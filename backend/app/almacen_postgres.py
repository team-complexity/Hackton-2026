"""Almacén sobre PostgreSQL (spec 003, RF-001 a RF-009, RF-020, RF-021).

El constructor no abre conexiones: las pruebas importan la app y, si lo hiciera,
con ``DATABASE_URL`` en el entorno tocarían la base real (QT-8, CE-011).
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypeVar

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import SecretStr

from app.almacen import Almacen, ErrorDeAlmacen, ErrorDeDatos
from app.cobros import Cobro, Pago
from app.reloj import Reloj

_T = TypeVar("_T")
_Fila = dict[str, object]

# Horas del Reloj, nunca now() (DP-10). ultima_consulta_pey no se escribe (DP-12).
# Parámetros %s: el SQL no se arma con los datos.
_SQL_INSERTAR_COBRO = """
insert into cobros (
    id, monto, concepto, num_ref, codi_qr_id, qr, qr_imagen,
    creado_en, expira_en, fin_ventana, cancelado_en
) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_SQL_GUARDAR_QR = """
update cobros
set codi_qr_id = %s, qr = %s, qr_imagen = %s
where id = %s
"""

_SQL_BORRAR = "delete from cobros where id = %s"

_SQL_CANCELAR = """
update cobros
set cancelado_en = %s
where id = %s and cancelado_en is null
"""

_SQL_PAGO = """
insert into pagos (
    cobro_id, transaccion_id, numero, monto_recibido, monto_base,
    pagado_en, fuente, registrado_en
) values (%s, %s, %s, %s, %s, %s, %s, %s)
on conflict (transaccion_id) do nothing
returning id
"""

_SQL_AVISO = """
insert into avisos_webhook (webhook_id, tipo, recibido_en)
values (%s, %s, %s)
on conflict (webhook_id) do nothing
"""

_SQL_AVISO_VISTO = "select 1 from avisos_webhook where webhook_id = %s"

_SQL_POR_ID = """
select id, monto, concepto, num_ref, codi_qr_id, qr, qr_imagen,
       creado_en, expira_en, fin_ventana, cancelado_en
from cobros
where id = %s
"""

_SQL_POR_QR = """
select id, monto, concepto, num_ref, codi_qr_id, qr, qr_imagen,
       creado_en, expira_en, fin_ventana, cancelado_en
from cobros
where codi_qr_id = %s
"""

_SQL_VENTANA = """
select id, monto, concepto, num_ref, codi_qr_id, qr, qr_imagen,
       creado_en, expira_en, fin_ventana, cancelado_en
from cobros
where fin_ventana > %s
  and fin_ventana <= %s
  and codi_qr_id is not null
  and codi_qr_id <> ''
order by fin_ventana
"""

_SQL_PAGOS = """
select cobro_id, transaccion_id, numero, monto_recibido, monto_base,
       pagado_en, fuente
from pagos
where cobro_id = any(%s)
order by numero
"""

_SQL_LEER_MARCA = "select conciliado_hasta from estado_del_servidor where unico"

_SQL_GUARDAR_MARCA = """
insert into estado_del_servidor (unico, conciliado_hasta)
values (true, %s)
on conflict (unico) do update
set conciliado_hasta = excluded.conciliado_hasta
"""

_SQL_RESPONDE = "select 1"


class _SinRegistrosDelPool(logging.Filter):
    """Descarta lo que registra psycopg_pool al fallar una conexión.

    Ese texto trae el usuario, el host y el puerto de la URL (RF-021, CE-010). Quien
    llama ya deja su línea con la operación y la clase del error.
    """

    def filter(self, registro: logging.LogRecord) -> bool:
        """Nada del pool llega a los registros (spec 003, RF-021)."""
        del registro
        return False


def _callar_al_pool() -> None:
    """Pone el filtro una sola vez, aunque se abran varios almacenes (spec 003, RF-021)."""
    registro = logging.getLogger("psycopg.pool")
    if not any(isinstance(filtro, _SinRegistrosDelPool) for filtro in registro.filters):
        registro.addFilter(_SinRegistrosDelPool())


class AlmacenPostgres(Almacen):
    """Pool de 1 a 3 conexiones y el SQL del modelo (spec 003, RF-020, RF-006, DP-10).

    ``configurado`` es verdadero: hay URL, aunque la base todavía no responda.
    """

    def __init__(self, url: SecretStr, reloj: Reloj) -> None:
        self._reloj = reloj
        self.configurado = True
        # open=False y nada de connect aquí (QT-8, CE-011). El nombre no es la URL (RF-021).
        self._pool = AsyncConnectionPool(
            url.get_secret_value(),
            min_size=1,
            max_size=3,
            open=False,
            name="almacen",
            kwargs={"connect_timeout": 5},
        )

    async def abrir(self) -> None:
        """Abre el pool sin esperar a que la base conteste (spec 003, RF-020, RF-021)."""
        _callar_al_pool()
        await self._pool.open(wait=False)

    async def cerrar(self) -> None:
        """Cierra el pool (spec 003, RF-020)."""
        await self._pool.close()

    async def guardar_cobro(self, cobro: Cobro, espera: float = 5) -> None:
        """Inserta el cobro con la hora del reloj (spec 003, RF-001, DP-12).

        No escribe ``ultima_consulta_pey``: esa hora se queda en memoria.
        """

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(_SQL_INSERTAR_COBRO, _parametros_cobro(cobro))

        await self._correr("guardar cobro", espera, trabajo)

    async def guardar_qr(self, cobro: Cobro, espera: float = 5) -> None:
        """Guarda el id de pey, el texto del QR y la imagen (spec 003, RF-010, RF-011)."""

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(
                    _SQL_GUARDAR_QR,
                    (
                        _vacio_a_null(cobro.codi_qr_id),
                        _vacio_a_null(cobro.qr),
                        cobro.qr_imagen,
                        cobro.id,
                    ),
                )

        await self._correr("guardar QR", espera, trabajo)

    async def borrar_cobro(self, cobro_id: str, espera: float = 5) -> None:
        """Borra la fila del cobro (spec 003, RF-052)."""

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(_SQL_BORRAR, (cobro_id,))

        await self._correr("borrar cobro", espera, trabajo)

    async def cancelar(self, cobro_id: str, cancelado_en: int, espera: float = 5) -> None:
        """Escribe la hora solo si ``cancelado_en`` sigue vacío (spec 003, RF-004)."""

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(
                    _SQL_CANCELAR,
                    (_instante(cancelado_en), cobro_id),
                )

        await self._correr("cancelar", espera, trabajo)

    async def registrar_pago(
        self,
        cobro_id: str,
        *,
        transaccion_id: str,
        numero: int,
        monto_recibido: Decimal,
        monto_base: Decimal | None,
        pagado_en: int,
        fuente: str,
        webhook_id: str | None = None,
        tipo_aviso: str = "",
        espera: float = 5,
    ) -> bool:
        """Inserta el pago y, si viene, el aviso, en una transacción (spec 003, RF-007, DP-9).

        Devuelve verdadero solo si el ``insert`` del pago devolvió fila.
        No guarda datos de quien paga: no hay columna para ellos (RF-009).
        """

        async def trabajo() -> bool:
            ahora = _instante(self._reloj.ahora())
            async with self._conexion(espera) as conexion, conexion.transaction():
                cursor = await conexion.execute(
                    _SQL_PAGO,
                    (
                        cobro_id,
                        transaccion_id,
                        numero,
                        monto_recibido,
                        monto_base,
                        _instante(pagado_en),
                        fuente,
                        ahora,
                    ),
                )
                fila = await cursor.fetchone()
                if webhook_id:
                    await conexion.execute(_SQL_AVISO, (webhook_id, tipo_aviso, ahora))
                return fila is not None

        return await self._correr("registrar pago", espera, trabajo)

    async def guardar_aviso(self, webhook_id: str, tipo: str, espera: float = 5) -> None:
        """Guarda el aviso ignorado, con ``tipo`` vacío si no vino (spec 003, RF-003, DP-34)."""

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(
                    _SQL_AVISO,
                    (webhook_id, tipo, _instante(self._reloj.ahora())),
                )

        await self._correr("guardar aviso", espera, trabajo)

    async def aviso_visto(self, webhook_id: str, espera: float = 5) -> bool:
        """Verdadero si ese ``webhook-id`` ya está guardado (spec 003, RF-003)."""

        async def trabajo() -> bool:
            async with self._conexion(espera) as conexion:
                cursor = await conexion.execute(_SQL_AVISO_VISTO, (webhook_id,))
                return await cursor.fetchone() is not None

        return await self._correr("cargar cobro", espera, trabajo)

    async def cargar_por_id(self, cobro_id: str, espera: float = 5) -> Cobro | None:
        """Arma el cobro y sus pagos ordenados por número (spec 003, RF-005, RF-008)."""

        async def trabajo() -> Cobro | None:
            async with self._conexion(espera) as conexion:
                cursor = await conexion.execute(_SQL_POR_ID, (cobro_id,))
                fila = await cursor.fetchone()
                if fila is None:
                    return None
                return (await self._armar_varios(conexion, [fila]))[0]

        return await self._correr("cargar cobro", espera, trabajo)

    async def cargar_por_codi_qr(self, codi_qr_id: str, espera: float = 5) -> Cobro | None:
        """Arma el cobro a partir del id de pey (spec 003, RF-005)."""

        async def trabajo() -> Cobro | None:
            async with self._conexion(espera) as conexion:
                cursor = await conexion.execute(_SQL_POR_QR, (codi_qr_id,))
                fila = await cursor.fetchone()
                if fila is None:
                    return None
                return (await self._armar_varios(conexion, [fila]))[0]

        return await self._correr("cargar cobro", espera, trabajo)

    async def cobros_con_ventana_terminada(
        self, desde: float, hasta: float, espera: float = 5
    ) -> list[Cobro]:
        """(desde, hasta], solo con QR, en orden de ``fin_ventana`` (spec 003, RF-061)."""

        async def trabajo() -> list[Cobro]:
            async with self._conexion(espera) as conexion:
                cursor = await conexion.execute(
                    _SQL_VENTANA,
                    (_instante(desde), _instante(hasta)),
                )
                filas = await cursor.fetchall()
                return await self._armar_varios(conexion, list(filas))

        return await self._correr("conciliar", espera, trabajo)

    async def leer_conciliado_hasta(self, espera: float = 5) -> float | None:
        """La marca, o nada si la tabla sigue vacía (spec 003, RF-061)."""

        async def trabajo() -> float | None:
            async with self._conexion(espera) as conexion:
                cursor = await conexion.execute(_SQL_LEER_MARCA)
                fila = await cursor.fetchone()
                if fila is None:
                    return None
                momento = fila["conciliado_hasta"]
                if not isinstance(momento, datetime):
                    raise ErrorDeDatos("latido", "DataError")
                return _unix_marca(momento)

        return await self._correr("latido", espera, trabajo)

    async def guardar_conciliado_hasta(self, momento: float, espera: float = 5) -> None:
        """Crea o sustituye la única fila de la marca (spec 003, RF-061, DP-10)."""

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(_SQL_GUARDAR_MARCA, (_instante(momento),))

        await self._correr("latido", espera, trabajo)

    async def responde(self, espera: float = 2) -> bool:
        """``select 1``. Por defecto espera 2 s (spec 003, RF-023, DP-31)."""

        async def trabajo() -> None:
            async with self._conexion(espera) as conexion:
                await conexion.execute(_SQL_RESPONDE)

        await self._correr("salud", espera, trabajo)
        return True

    @asynccontextmanager
    async def _conexion(self, espera: float) -> AsyncIterator[psycopg.AsyncConnection]:
        """Saca una conexión del pool y lee las filas como diccionarios."""
        async with self._pool.connection(timeout=espera) as conexion:
            conexion.row_factory = dict_row
            yield conexion

    async def _correr(
        self,
        operacion: str,
        espera: float,
        trabajo: Callable[[], Awaitable[_T]],
    ) -> _T:
        """Corta a ``espera`` segundos, sin el texto de psycopg (spec 003, RF-021, DP-15)."""
        try:
            return await asyncio.wait_for(trabajo(), espera)
        except TimeoutError:
            raise ErrorDeAlmacen(operacion, TimeoutError.__name__) from None
        except psycopg.Error as error:
            raise _clasificar(error, operacion) from None

    async def _armar_varios(
        self,
        conexion: psycopg.AsyncConnection,
        filas: list[_Fila],
    ) -> list[Cobro]:
        """Carga los pagos de esas filas, ordenados por ``numero`` (spec 003, RF-008)."""
        if not filas:
            return []
        ids = [str(fila["id"]) for fila in filas]
        cursor = await conexion.execute(_SQL_PAGOS, (ids,))
        por_cobro: dict[str, list[_Fila]] = {cobro_id: [] for cobro_id in ids}
        for pago in await cursor.fetchall():
            por_cobro[str(pago["cobro_id"])].append(pago)
        return [self._cobro(fila, por_cobro[str(fila["id"])]) for fila in filas]

    def _cobro(self, fila: _Fila, pagos: list[_Fila]) -> Cobro:
        """Cobro nuevo con el reloj del servidor. Null vuelve como ``""`` (spec 003, RF-006)."""
        monto = _decimal_o_nada(fila["monto"])
        ordenados = sorted(pagos, key=lambda pago: int(str(pago["numero"])))
        return Cobro(
            id=str(fila["id"]),
            monto=monto,
            concepto=str(fila["concepto"]),
            num_ref=str(fila["num_ref"]),
            creado_en=_unix_entero(_fecha(fila["creado_en"])),
            expira_en=_unix_entero(_fecha(fila["expira_en"])),
            fin_ventana=_unix_entero(_fecha(fila["fin_ventana"])),
            reloj=self._reloj,
            codi_qr_id=_null_a_vacio(fila["codi_qr_id"]),
            qr=_null_a_vacio(fila["qr"]),
            qr_imagen=_texto_o_nada(fila["qr_imagen"]),
            cancelado_en=_unix_o_nada(fila["cancelado_en"]),
            pagos=[_pago(pago, monto) for pago in ordenados],
        )


def _clasificar(error: psycopg.Error, operacion: str) -> ErrorDeAlmacen | ErrorDeDatos:
    """Un dato rechazado es ``ErrorDeDatos``; el resto, sin respuesta (spec 003, DP-34).

    ``on conflict do nothing`` no llega aquí. Solo se usa el nombre de la clase (RF-021).
    """
    clase = type(error).__name__
    if isinstance(error, (psycopg.DataError, psycopg.IntegrityError)):
        return ErrorDeDatos(operacion, clase)
    return ErrorDeAlmacen(operacion, clase)


def _parametros_cobro(cobro: Cobro) -> tuple[object, ...]:
    """Columnas del insert. ``""`` se va como null; la hora es la del cobro (spec 003, DP-10)."""
    return (
        cobro.id,
        cobro.monto,
        cobro.concepto,
        cobro.num_ref,
        _vacio_a_null(cobro.codi_qr_id),
        _vacio_a_null(cobro.qr),
        cobro.qr_imagen,
        _instante(cobro.creado_en),
        _instante(cobro.expira_en),
        _instante(cobro.fin_ventana),
        _instante(cobro.cancelado_en),
    )


def _pago(fila: _Fila, monto_del_cobro: Decimal | None) -> Pago:
    """Arma el pago con el monto del cobro, que la tabla de pagos no guarda (spec 001, RF-019)."""
    return Pago(
        transaccion_id=str(fila["transaccion_id"]),
        numero=int(str(fila["numero"])),
        monto_recibido=_decimal(fila["monto_recibido"]),
        monto_base=_decimal_o_nada(fila["monto_base"]),
        pagado_en=_unix_entero(_fecha(fila["pagado_en"])),
        fuente=str(fila["fuente"]),
        monto_del_cobro=monto_del_cobro,
    )


def _instante(momento: float | None) -> datetime | None:
    """Unix a ``timestamptz`` en UTC. Nada sigue siendo nada (spec 003, DP-10)."""
    if momento is None:
        return None
    return datetime.fromtimestamp(momento, UTC)


def _fecha(valor: object) -> datetime:
    """La columna de hora que devolvió psycopg (spec 003, RF-006)."""
    if isinstance(valor, datetime):
        if valor.tzinfo is None:
            return valor.replace(tzinfo=UTC)
        return valor
    raise ErrorDeDatos("cargar cobro", "DataError")


def _unix_entero(momento: datetime) -> int:
    """Vuelve a segundos enteros, como los guarda el cobro en memoria (spec 003, RF-006)."""
    return int(momento.timestamp())


def _unix_o_nada(valor: object) -> int | None:
    """``null`` de la base a ``None`` (spec 003, RF-004)."""
    if valor is None:
        return None
    return _unix_entero(_fecha(valor))


def _unix_marca(momento: datetime) -> float:
    """La marca del latido. Si cayó en un segundo exacto, ese entero (spec 003, RF-061)."""
    segundos = momento.timestamp()
    if segundos.is_integer():
        return int(segundos)
    return segundos


def _vacio_a_null(texto: str) -> str | None:
    """``""`` en memoria es null en la base (spec 003, data-model §2.1)."""
    return texto or None


def _null_a_vacio(valor: object) -> str:
    """Null en la base vuelve como ``""`` (spec 003, data-model §2.1)."""
    if valor is None:
        return ""
    return str(valor)


def _texto_o_nada(valor: object) -> str | None:
    """La imagen vacía de la base es ``None``, no una cadena (spec 003, RF-011)."""
    if valor is None:
        return None
    return str(valor)


def _decimal(valor: object) -> Decimal:
    """``numeric`` de la base a ``Decimal`` (spec 003, RF-001)."""
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def _decimal_o_nada(valor: object) -> Decimal | None:
    """``numeric`` nulo a ``None`` (spec 003, RF-001)."""
    if valor is None:
        return None
    return _decimal(valor)
