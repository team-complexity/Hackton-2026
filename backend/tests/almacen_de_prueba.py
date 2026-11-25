"""Ayudas para probar el almacén sin pey real ni tiempo real (spec 003, T050, DP-6).

``AlmacenQueFalla``, ``reiniciar``, ``RelojDetenido`` y ``RelojPorPasos``.
La fixture ``app`` de ``conftest.py`` no cambia aquí: pasa al almacén en T057.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.main import crear_app
from app.pey import ClientePey
from app.reloj import Reloj, RelojFalso
from tests.conftest import BASE_PEY_DE_PRUEBA, PeySimulado

# La llamada se anota con el nombre del método. El texto del error usa la frase
# del contrato de fallas, que es la que debe quedar en el registro.
FRASES = {
    "guardar_cobro": "guardar cobro",
    "guardar_qr": "guardar QR",
    "borrar_cobro": "borrar cobro",
    "registrar_pago": "registrar pago",
    "guardar_aviso": "guardar aviso",
    "cancelar": "cancelar",
    "cargar_por_id": "cargar cobro",
    "cargar_por_codi_qr": "cargar cobro",
    "aviso_visto": "cargar cobro",
    "responde": "salud",
}
CLASE_DE_FALLA = "OperationalError"
CLASE_DE_DATOS = "DataError"


@dataclass(frozen=True)
class Llamada:
    """Una operación del almacén, con la espera que pidió quien llama (spec 003, DP-35)."""

    operacion: str
    espera: float
    args: tuple[object, ...] = ()


class AlmacenQueFalla:
    """Envuelve un almacén en memoria y falla la operación que la prueba elija (spec 003, DP-6).

    ``configurado`` es verdadero: la salud no lo trata como «sin configurar».
    Cada llamada queda en ``llamadas`` con su operación y su ``espera``.
    """

    def __init__(self, datos: object | None = None, reloj: Reloj | None = None) -> None:
        from app.almacen import AlmacenEnMemoria

        self._interno = AlmacenEnMemoria(datos=datos, reloj=reloj)
        self.datos = self._interno.datos
        self.configurado = True
        self.llamadas: list[Llamada] = []
        self.pagos_listos: list[str] = []
        self._fallos: dict[str, int | None] = {}
        self._fallos_datos: set[str] = set()
        self._pausas: dict[str, asyncio.Event] = {}
        self._sin_salud = False

    def fallar(self, operacion: str, veces: int | None = None) -> None:
        """Las próximas ``veces`` llamadas lanzan ``ErrorDeAlmacen`` (spec 003, RF-012).

        ``veces=None`` falla siempre, hasta ``quitar_falla``.
        """
        self._fallos[operacion] = veces

    def fallar_datos(self, operacion: str) -> None:
        """La operación lanza ``ErrorDeDatos`` (spec 003, DP-34)."""
        self._fallos_datos.add(operacion)

    def quitar_falla(self, operacion: str) -> None:
        """Vuelve a dejar pasar ``operacion`` (spec 003, RF-048)."""
        self._fallos.pop(operacion, None)
        self._fallos_datos.discard(operacion)

    def no_responde(self) -> None:
        """La salud va a ver que la base no responde (spec 003, RF-023)."""
        self._sin_salud = True

    def pausar(self, operacion: str) -> asyncio.Event:
        """La operación espera este evento, sin tiempo real (spec 003, DP-33).

        La prueba lo suelta con ``set`` cuando las dos peticiones ya llegaron.
        """
        evento = asyncio.Event()
        self._pausas[operacion] = evento
        return evento

    async def _antes(self, operacion: str, espera: float, args: tuple[object, ...]) -> None:
        self.llamadas.append(Llamada(operacion, espera, args))
        pausa = self._pausas.get(operacion)
        if pausa is not None and not pausa.is_set():
            await pausa.wait()
        from app.almacen import ErrorDeAlmacen, ErrorDeDatos

        if operacion in self._fallos_datos:
            raise ErrorDeDatos(FRASES.get(operacion, operacion), CLASE_DE_DATOS)
        if self._toca_fallar(operacion):
            raise ErrorDeAlmacen(FRASES.get(operacion, operacion), CLASE_DE_FALLA)

    def _toca_fallar(self, operacion: str) -> bool:
        if operacion not in self._fallos:
            return False
        veces = self._fallos[operacion]
        if veces is None:
            return True
        if veces <= 0:
            return False
        self._fallos[operacion] = veces - 1
        return True

    async def abrir(self) -> None:
        """Abre el almacén interno (spec 003, RF-020)."""
        await self._interno.abrir()

    async def cerrar(self) -> None:
        """Cierra el almacén interno (spec 003, RF-020)."""
        await self._interno.cerrar()

    async def guardar_cobro(self, cobro: object, espera: float = 5) -> None:
        """Delega ``guardar_cobro`` (spec 003, RF-001, RF-012)."""
        await self._antes("guardar_cobro", espera, (cobro,))
        await self._interno.guardar_cobro(cobro, espera=espera)

    async def guardar_qr(self, cobro: object, espera: float = 5) -> None:
        """Delega ``guardar_qr`` (spec 003, RF-010, RF-013)."""
        await self._antes("guardar_qr", espera, (cobro,))
        await self._interno.guardar_qr(cobro, espera=espera)

    async def borrar_cobro(self, cobro_id: str, espera: float = 5) -> None:
        """Delega ``borrar_cobro`` (spec 003, RF-052)."""
        await self._antes("borrar_cobro", espera, (cobro_id,))
        await self._interno.borrar_cobro(cobro_id, espera=espera)

    async def cancelar(self, cobro_id: str, cancelado_en: int, espera: float = 5) -> None:
        """Delega ``cancelar`` (spec 003, RF-004)."""
        await self._antes("cancelar", espera, (cobro_id, cancelado_en))
        await self._interno.cancelar(cobro_id, cancelado_en, espera=espera)

    async def registrar_pago(
        self,
        cobro_id: str,
        *,
        transaccion_id: str,
        numero: int,
        monto_recibido: object,
        monto_base: object,
        pagado_en: int,
        fuente: str,
        webhook_id: str | None = None,
        tipo_aviso: str = "",
        espera: float = 5,
    ) -> bool:
        """Delega ``registrar_pago`` y anota el id si el pago quedó guardado (spec 003, RF-002)."""
        await self._antes("registrar_pago", espera, (cobro_id, transaccion_id))
        nuevo = await self._interno.registrar_pago(
            cobro_id,
            transaccion_id=transaccion_id,
            numero=numero,
            monto_recibido=monto_recibido,
            monto_base=monto_base,
            pagado_en=pagado_en,
            fuente=fuente,
            webhook_id=webhook_id,
            tipo_aviso=tipo_aviso,
            espera=espera,
        )
        if nuevo:
            self.pagos_listos.append(transaccion_id)
        return nuevo

    async def guardar_aviso(self, webhook_id: str, tipo: str, espera: float = 5) -> None:
        """Delega ``guardar_aviso`` (spec 003, RF-003)."""
        await self._antes("guardar_aviso", espera, (webhook_id, tipo))
        await self._interno.guardar_aviso(webhook_id, tipo, espera=espera)

    async def aviso_visto(self, webhook_id: str, espera: float = 5) -> bool:
        """Delega ``aviso_visto`` (spec 003, RF-003)."""
        await self._antes("aviso_visto", espera, (webhook_id,))
        return await self._interno.aviso_visto(webhook_id, espera=espera)

    async def cargar_por_id(self, cobro_id: str, espera: float = 5) -> object | None:
        """Delega ``cargar_por_id`` (spec 003, RF-005)."""
        await self._antes("cargar_por_id", espera, (cobro_id,))
        return await self._interno.cargar_por_id(cobro_id, espera=espera)

    async def cargar_por_codi_qr(self, codi_qr_id: str, espera: float = 5) -> object | None:
        """Delega ``cargar_por_codi_qr`` (spec 003, RF-005)."""
        await self._antes("cargar_por_codi_qr", espera, (codi_qr_id,))
        return await self._interno.cargar_por_codi_qr(codi_qr_id, espera=espera)

    async def cobros_con_ventana_terminada(
        self, desde: float, hasta: float, espera: float = 5
    ) -> list[object]:
        """Delega la consulta de la conciliación (spec 003, RF-061)."""
        await self._antes("cobros_con_ventana_terminada", espera, (desde, hasta))
        return await self._interno.cobros_con_ventana_terminada(desde, hasta, espera=espera)

    async def leer_conciliado_hasta(self, espera: float = 5) -> float | None:
        """Delega la lectura de la marca (spec 003, RF-061)."""
        await self._antes("leer_conciliado_hasta", espera, ())
        return await self._interno.leer_conciliado_hasta(espera=espera)

    async def guardar_conciliado_hasta(self, momento: float, espera: float = 5) -> None:
        """Delega la escritura de la marca (spec 003, RF-061)."""
        await self._antes("guardar_conciliado_hasta", espera, (momento,))
        await self._interno.guardar_conciliado_hasta(momento, espera=espera)

    async def responde(self, espera: float = 5) -> bool:
        """Delega el ``select 1``, o falla si la prueba llamó ``no_responde`` (spec 003, RF-023)."""
        await self._antes("responde", espera, ())
        if self._sin_salud:
            from app.almacen import ErrorDeAlmacen

            raise ErrorDeAlmacen(FRASES["responde"], CLASE_DE_FALLA)
        return await self._interno.responde(espera=espera)


def armar_app(
    configuracion: Configuracion,
    pey: PeySimulado,
    reloj: Reloj,
    almacen: object,
) -> FastAPI:
    """Arma la app de prueba con el almacén inyectado (spec 003, T057, principio V).

    Deja en ``app.state`` el almacén, la configuración y el pey simulado para que
    ``reiniciar`` arme otra app sobre los mismos datos. Las tareas de fondo no
    arrancan: con ``RelojFalso`` el bucle avanzaría el reloj sin parar.
    """
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(
        BASE_PEY_DE_PRUEBA,
        configuracion.pey_api_key.get_secret_value(),
        http,
    )
    aplicacion = crear_app(
        configuracion,
        cliente_pey,
        reloj,
        almacen=almacen,
        tareas_en_segundo_plano=False,
    )
    aplicacion.state.almacen = almacen
    aplicacion.state.configuracion = configuracion
    aplicacion.state.pey_simulado = pey
    return aplicacion


def reiniciar(app: FastAPI, almacen: object | None = None) -> FastAPI:
    """Otra app con un almacén nuevo sobre los mismos datos (spec 003, plan §7, RF-005).

    Comparte el ``RelojFalso`` y el ``PeySimulado``. Si no se pasa almacén, usa
    uno en memoria. El objeto ``datos`` es el que sobrevive al reinicio.
    """
    datos = app.state.almacen.datos
    reloj = app.state.reloj
    if almacen is None:
        from app.almacen import AlmacenEnMemoria

        almacen = AlmacenEnMemoria(datos=datos, reloj=reloj)
    return armar_app(app.state.configuracion, app.state.pey_simulado, reloj, almacen)


@contextmanager
def cliente_de(app: FastAPI) -> Iterator[TestClient]:
    """Cliente HTTP contra la app. Cierra el ciclo de vida al salir (spec 003, principio V)."""
    with TestClient(app) as cliente:
        yield cliente


class RelojDetenido(RelojFalso):
    """``dormir`` no regresa: la tarea de fondo da una sola vuelta (spec 003, T050)."""

    async def dormir(self, segundos: float) -> None:
        """Espera para siempre, sin avanzar el reloj ni el tiempo real."""
        del segundos
        await asyncio.Event().wait()


class RelojPorPasos(RelojFalso):
    """``dormir`` anota la espera y se queda hasta que la prueba lo suelta (spec 003, QT-7).

    Así el bucle de ``correr_tareas`` se prueba vuelta por vuelta, sin tiempo real
    y sin que el reloj avance solo.
    """

    def __init__(self, inicio: float) -> None:
        super().__init__(inicio)
        self.esperas: list[float] = []
        self._paso: asyncio.Event | None = None

    async def dormir(self, segundos: float) -> None:
        """Anota ``segundos`` y espera ``soltar``, que avanza el reloj esa cantidad."""
        self.esperas.append(segundos)
        self._paso = asyncio.Event()
        await self._paso.wait()
        self.avanzar(segundos)

    def soltar(self) -> None:
        """Suelta el ``dormir`` en curso y, al despertar, el reloj avanza esa espera."""
        if self._paso is None:
            raise RuntimeError("nadie está esperando en dormir")
        self._paso.set()
