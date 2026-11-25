"""Almacén de cobros: interfaz y copia en memoria (spec 003, DP-6).

La memoria no guarda los objetos ``Cobro``. Cada lectura arma uno nuevo con el
reloj del almacén, igual que hará la base de datos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import TypedDict

from app.cobros import Cobro, Pago
from app.reloj import Reloj


class ErrorDeAlmacen(Exception):
    """La base de datos no respondió (spec 003, RF-016, RF-021, DP-15).

    El texto lleva la operación y el nombre de la clase del error original,
    nunca el texto de ese error: el de psycopg puede traer el servidor y el usuario.
    """

    def __init__(self, operacion: str, clase: str) -> None:
        self.operacion = operacion
        self.clase = clase
        super().__init__(f"Base de datos sin respuesta al {operacion} ({clase})")


class ErrorDeDatos(Exception):
    """PostgreSQL rechazó el valor (spec 003, DP-34, RF-021).

    No es «sin respuesta»: el dato no va a pasar por reintentarlo igual.
    El texto tampoco incluye el error original.
    """

    def __init__(self, operacion: str, clase: str) -> None:
        self.operacion = operacion
        self.clase = clase
        super().__init__(f"La base de datos rechazó los datos al {operacion} ({clase})")


class _PagoPlano(TypedDict):
    transaccion_id: str
    numero: int
    monto_recibido: Decimal
    monto_base: Decimal | None
    pagado_en: int
    fuente: str


class _CobroPlano(TypedDict):
    id: str
    monto: Decimal | None
    concepto: str
    num_ref: str
    creado_en: int
    expira_en: int
    fin_ventana: int
    codi_qr_id: str
    qr: str
    qr_imagen: str | None
    cancelado_en: int | None
    pagos: list[_PagoPlano]


@dataclass
class _Datos:
    """Diccionarios compartidos para simular un reinicio (spec 003, RF-005, DP-6)."""

    cobros: dict[str, _CobroPlano]
    por_qr: dict[str, str]
    transacciones: set[str]
    avisos: dict[str, str]
    conciliado_hasta: float | None

    @classmethod
    def vacios(cls) -> "_Datos":
        """Un almacén recién creado, sin cobros (spec 003, RF-005)."""
        return cls(cobros={}, por_qr={}, transacciones=set(), avisos={}, conciliado_hasta=None)


class Almacen(ABC):
    """Operaciones para guardar cobros, pagos y avisos (spec 003, DP-6).

    Cada operación espera como máximo ``espera`` segundos (5; 2 en ``responde``, DP-31).
    """

    configurado: bool

    @abstractmethod
    async def abrir(self) -> None:
        """Prepara el almacén. En PostgreSQL abre el pool sin esperar (spec 003, RF-020)."""

    @abstractmethod
    async def cerrar(self) -> None:
        """Suelta lo que ``abrir`` haya tomado (spec 003, RF-020)."""

    @abstractmethod
    async def guardar_cobro(self, cobro: Cobro, espera: float = 5) -> None:
        """Inserta el cobro antes de llamar a pey (spec 003, RF-001, RF-012)."""

    @abstractmethod
    async def guardar_qr(self, cobro: Cobro, espera: float = 5) -> None:
        """Guarda el QR y su imagen en el cobro ya insertado (spec 003, RF-010, RF-011)."""

    @abstractmethod
    async def borrar_cobro(self, cobro_id: str, espera: float = 5) -> None:
        """Quita el cobro si pey no creó el QR (spec 003, RF-052)."""

    @abstractmethod
    async def cancelar(self, cobro_id: str, cancelado_en: int, espera: float = 5) -> None:
        """Guarda la cancelación solo si todavía no hay una (spec 003, RF-004)."""

    @abstractmethod
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
        """Guarda el pago y, si viene, su aviso juntos (spec 003, RF-002, RF-007, DP-9).

        Devuelve verdadero solo si el pago es nuevo.
        """

    @abstractmethod
    async def guardar_aviso(self, webhook_id: str, tipo: str, espera: float = 5) -> None:
        """Recuerda un aviso que no trajo un pago nuevo (spec 003, RF-003)."""

    @abstractmethod
    async def aviso_visto(self, webhook_id: str, espera: float = 5) -> bool:
        """Dice si ese ``webhook-id`` ya se guardó (spec 003, RF-003)."""

    @abstractmethod
    async def cargar_por_id(self, cobro_id: str, espera: float = 5) -> Cobro | None:
        """Arma el cobro y sus pagos, o nada si no está (spec 003, RF-005)."""

    @abstractmethod
    async def cargar_por_codi_qr(self, codi_qr_id: str, espera: float = 5) -> Cobro | None:
        """Arma el cobro a partir del id de pey (spec 003, RF-005)."""

    @abstractmethod
    async def cobros_con_ventana_terminada(
        self, desde: float, hasta: float, espera: float = 5
    ) -> list[Cobro]:
        """Cobros con QR cuya ``fin_ventana`` cae en (desde, hasta] (spec 003, RF-061)."""

    @abstractmethod
    async def leer_conciliado_hasta(self, espera: float = 5) -> float | None:
        """La marca del latido, o nada si todavía no hay fila (spec 003, RF-061)."""

    @abstractmethod
    async def guardar_conciliado_hasta(self, momento: float, espera: float = 5) -> None:
        """Deja la marca del latido en ``momento`` (spec 003, RF-061)."""

    @abstractmethod
    async def responde(self, espera: float = 2) -> bool:
        """Verdadero si un ``select 1`` cabe en ``espera`` segundos (spec 003, RF-023, DP-31)."""


class AlmacenEnMemoria(Almacen):
    """La misma interfaz con diccionarios (spec 003, DP-6, DP-16, CE-005).

    ``configurado`` es falso: sin ``DATABASE_URL`` la salud dice «sin configurar».
    ``espera`` está en la firma para quien llama; aquí no hay red que esperar.
    Un almacén nuevo con los mismos ``datos`` simula el reinicio.
    """

    def __init__(self, datos: _Datos | None = None, reloj: Reloj | None = None) -> None:
        self.datos = _Datos.vacios() if datos is None else datos
        self._reloj = reloj if reloj is not None else Reloj()
        self.configurado = False

    async def abrir(self) -> None:
        """No abre nada: los diccionarios ya están (spec 003, DP-6)."""

    async def cerrar(self) -> None:
        """No cierra nada: los diccionarios siguen para el siguiente almacén (spec 003, DP-6)."""

    async def guardar_cobro(self, cobro: Cobro, espera: float = 5) -> None:
        """Copia los campos del cobro, sin su lista de pagos (spec 003, RF-001)."""
        del espera
        if cobro.id in self.datos.cobros:
            raise ErrorDeDatos("guardar cobro", "UniqueViolation")
        self._ocupar_qr(cobro.id, cobro.codi_qr_id, "guardar cobro")
        self.datos.cobros[cobro.id] = _plano_de(cobro)

    async def guardar_qr(self, cobro: Cobro, espera: float = 5) -> None:
        """Actualiza el QR del cobro ya guardado (spec 003, RF-010, RF-011)."""
        del espera
        plano = self.datos.cobros.get(cobro.id)
        if plano is None:
            return
        if cobro.codi_qr_id != plano["codi_qr_id"]:
            # Primero el id nuevo: si ya es de otro cobro, el anterior sigue indexado.
            self._ocupar_qr(cobro.id, cobro.codi_qr_id, "guardar QR")
            self._soltar_qr(plano)
        plano["codi_qr_id"] = cobro.codi_qr_id
        plano["qr"] = cobro.qr
        plano["qr_imagen"] = cobro.qr_imagen

    async def borrar_cobro(self, cobro_id: str, espera: float = 5) -> None:
        """Quita el cobro y su QR; con pagos lo rechaza como la base (spec 003, RF-052, DP-34)."""
        del espera
        plano = self.datos.cobros.get(cobro_id)
        if plano is None:
            return
        if plano["pagos"]:
            # pagos.cobro_id no tiene on delete cascade (0001): PostgreSQL no deja borrarlo.
            raise ErrorDeDatos("borrar cobro", "ForeignKeyViolation")
        del self.datos.cobros[cobro_id]
        self._soltar_qr(plano)

    async def cancelar(self, cobro_id: str, cancelado_en: int, espera: float = 5) -> None:
        """Escribe la hora solo cuando ``cancelado_en`` está vacío (spec 003, RF-004)."""
        del espera
        plano = self.datos.cobros.get(cobro_id)
        if plano is not None and plano["cancelado_en"] is None:
            plano["cancelado_en"] = cancelado_en

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
        """Guarda el pago nuevo y, en el mismo paso, su aviso (spec 003, RF-007, DP-9)."""
        del espera
        plano = self.datos.cobros.get(cobro_id)
        if plano is None:
            raise ErrorDeDatos("registrar pago", "ForeignKeyViolation")
        nuevo = transaccion_id not in self.datos.transacciones
        if nuevo and any(pago["numero"] == numero for pago in plano["pagos"]):
            raise ErrorDeDatos("registrar pago", "UniqueViolation")
        if nuevo:
            plano["pagos"].append(
                {
                    "transaccion_id": transaccion_id,
                    "numero": numero,
                    "monto_recibido": monto_recibido,
                    "monto_base": monto_base,
                    "pagado_en": pagado_en,
                    "fuente": fuente,
                }
            )
            self.datos.transacciones.add(transaccion_id)
        if webhook_id:
            self.datos.avisos.setdefault(webhook_id, tipo_aviso)
        return nuevo

    async def guardar_aviso(self, webhook_id: str, tipo: str, espera: float = 5) -> None:
        """Guarda el aviso si ese ``webhook-id`` no estaba (spec 003, RF-003)."""
        del espera
        self.datos.avisos.setdefault(webhook_id, tipo)

    async def aviso_visto(self, webhook_id: str, espera: float = 5) -> bool:
        """Verdadero si el aviso ya está en los diccionarios (spec 003, RF-003)."""
        del espera
        return webhook_id in self.datos.avisos

    async def cargar_por_id(self, cobro_id: str, espera: float = 5) -> Cobro | None:
        """Arma un cobro nuevo con el reloj de este almacén (spec 003, RF-005)."""
        del espera
        plano = self.datos.cobros.get(cobro_id)
        if plano is None:
            return None
        return self._armar(plano)

    async def cargar_por_codi_qr(self, codi_qr_id: str, espera: float = 5) -> Cobro | None:
        """Busca por el id de pey y arma un cobro nuevo (spec 003, RF-005)."""
        del espera
        cobro_id = self.datos.por_qr.get(codi_qr_id)
        if cobro_id is None:
            return None
        return self._armar(self.datos.cobros[cobro_id])

    async def cobros_con_ventana_terminada(
        self, desde: float, hasta: float, espera: float = 5
    ) -> list[Cobro]:
        """(desde, hasta], solo con QR, en orden de ``fin_ventana`` (spec 003, RF-061)."""
        del espera
        planos = [
            plano
            for plano in self.datos.cobros.values()
            if plano["codi_qr_id"] and desde < plano["fin_ventana"] <= hasta
        ]
        planos.sort(key=lambda plano: plano["fin_ventana"])
        return [self._armar(plano) for plano in planos]

    async def leer_conciliado_hasta(self, espera: float = 5) -> float | None:
        """La marca guardada, o nada si el latido no ha corrido (spec 003, RF-061)."""
        del espera
        return self.datos.conciliado_hasta

    async def guardar_conciliado_hasta(self, momento: float, espera: float = 5) -> None:
        """Sustituye la marca del latido (spec 003, RF-061)."""
        del espera
        self.datos.conciliado_hasta = momento

    async def responde(self, espera: float = 2) -> bool:
        """La memoria siempre responde (spec 003, RF-023, DP-31)."""
        del espera
        return True

    def _armar(self, plano: _CobroPlano) -> Cobro:
        """Cobro nuevo con el reloj de este almacén (spec 003, RF-006, DP-12)."""
        monto = plano["monto"]
        pagos = [
            Pago(
                transaccion_id=pago["transaccion_id"],
                numero=pago["numero"],
                monto_recibido=pago["monto_recibido"],
                monto_base=pago["monto_base"],
                pagado_en=pago["pagado_en"],
                fuente=pago["fuente"],
                monto_del_cobro=monto,
            )
            for pago in sorted(plano["pagos"], key=lambda pago: pago["numero"])
        ]
        return Cobro(
            id=plano["id"],
            monto=monto,
            concepto=plano["concepto"],
            num_ref=plano["num_ref"],
            creado_en=plano["creado_en"],
            expira_en=plano["expira_en"],
            fin_ventana=plano["fin_ventana"],
            reloj=self._reloj,
            codi_qr_id=plano["codi_qr_id"] or "",
            qr=plano["qr"] or "",
            qr_imagen=plano["qr_imagen"],
            cancelado_en=plano["cancelado_en"],
            pagos=pagos,
        )

    def _ocupar_qr(self, cobro_id: str, codi_qr_id: str, operacion: str) -> None:
        """Reserva el id de pey. Vacío no se indexa: todavía no hay QR (spec 003, RF-012)."""
        if not codi_qr_id:
            return
        dueno = self.datos.por_qr.get(codi_qr_id)
        if dueno is not None and dueno != cobro_id:
            raise ErrorDeDatos(operacion, "UniqueViolation")
        self.datos.por_qr[codi_qr_id] = cobro_id

    def _soltar_qr(self, plano: _CobroPlano) -> None:
        """Quita el índice del QR anterior de este cobro (spec 003, RF-010)."""
        anterior = plano["codi_qr_id"]
        if anterior and self.datos.por_qr.get(anterior) == plano["id"]:
            self.datos.por_qr.pop(anterior, None)


def _plano_de(cobro: Cobro) -> _CobroPlano:
    """Copia los campos. Los pagos entran solo por ``registrar_pago`` (spec 003, RF-001, RF-002)."""
    return {
        "id": cobro.id,
        "monto": cobro.monto,
        "concepto": cobro.concepto,
        "num_ref": cobro.num_ref,
        "creado_en": cobro.creado_en,
        "expira_en": cobro.expira_en,
        "fin_ventana": cobro.fin_ventana,
        "codi_qr_id": cobro.codi_qr_id,
        "qr": cobro.qr,
        "qr_imagen": cobro.qr_imagen,
        "cancelado_en": cobro.cancelado_en,
        "pagos": [],
    }
