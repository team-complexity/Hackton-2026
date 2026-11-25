"""El pool solo se abre en el ciclo de vida, y la tarea de fondo arranca y se detiene.

(spec 003, T060, QT-8, CE-011, DP-16). Sin pey real, sin base real y sin tiempo real.
"""

import logging
import threading
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from psycopg_pool import AsyncConnectionPool
from pydantic import SecretStr

from app.almacen import AlmacenEnMemoria
from app.almacen_postgres import AlmacenPostgres
from app.main import crear_app
from app.pey import ClientePey
from tests.almacen_de_prueba import AlmacenQueFalla, RelojDetenido
from tests.conftest import BASE_PEY_DE_PRUEBA, LLAVE_FALSA, PeySimulado

URL_FALSA = "postgresql://usuario-falso:clave-falsa@127.0.0.1:1/no_existe"
AVISO = "Sin DATABASE_URL: los cobros se guardan en memoria"


def _cliente_pey(pey: PeySimulado) -> ClientePey:
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    return ClientePey(BASE_PEY_DE_PRUEBA, LLAVE_FALSA, http)


def test_sin_database_url_avisa_y_la_salud_dice_sin_configurar(
    configuracion, pey, reloj, caplog: pytest.LogCaptureFixture
) -> None:
    """Sin URL, un WARNING y la salud en «sin configurar» (spec 003, RF-023, DP-16)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    config = configuracion.model_copy(update={"database_url": SecretStr("")})
    # RelojFalso avanzaría solo si el bucle arrancara (armar_app hace lo mismo).
    app = crear_app(
        config,
        _cliente_pey(pey),
        reloj,
        tareas_en_segundo_plano=False,
    )
    assert any(
        registro.levelno == logging.WARNING and registro.getMessage() == AVISO
        for registro in caplog.records
        if registro.name == "pago_facil"
    )
    with TestClient(app) as cliente:
        assert cliente.get("/salud").json() == {
            "estado": "ok",
            "llave_pey": True,
            "secreto_aviso_pey": True,
            "base_de_datos": "sin configurar",
        }


def test_con_database_url_crear_app_no_abre_el_pool(
    configuracion, pey, reloj, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hay almacén de PostgreSQL, pero el pool no se abre al crear la app.

    (spec 003, QT-8, CE-011).
    """

    async def abrir_prohibido(self, *args, **kwargs) -> None:
        del self, args, kwargs
        raise AssertionError("crear_app no debe abrir el pool")

    monkeypatch.setattr(AsyncConnectionPool, "open", abrir_prohibido)
    config = configuracion.model_copy(update={"database_url": SecretStr(URL_FALSA)})
    app = crear_app(config, _cliente_pey(pey), reloj, tareas_en_segundo_plano=False)
    assert isinstance(app.state.almacen, AlmacenPostgres)
    assert app.state.almacen.configurado is True
    assert app.state.almacen._pool._opened is False
    assert app.state.almacen._pool.closed is True


def test_el_almacen_se_abre_al_entrar_al_cliente_y_se_cierra_al_salir(
    configuracion, pey, reloj
) -> None:
    """Entrar al cliente abre el almacén y salir lo cierra (spec 003, RF-020)."""

    class AlmacenAnotado(AlmacenQueFalla):
        def __init__(self) -> None:
            super().__init__(reloj=reloj)
            self.eventos: list[str] = []

        async def abrir(self) -> None:
            self.eventos.append("abrir")
            await super().abrir()

        async def cerrar(self) -> None:
            self.eventos.append("cerrar")
            await super().cerrar()

    almacen = AlmacenAnotado()
    app = crear_app(
        configuracion,
        _cliente_pey(pey),
        reloj,
        almacen=almacen,
        tareas_en_segundo_plano=False,
    )
    assert almacen.eventos == []
    with TestClient(app):
        assert almacen.eventos == ["abrir"]
    assert almacen.eventos == ["abrir", "cerrar"]


def test_la_tarea_de_fondo_registra_un_aviso_al_arrancar_y_se_cancela_al_salir(
    configuracion, pey
) -> None:
    """Al arrancar corre una vuelta; al salir la tarea se cancela y no se cuelga.

    (spec 003, RF-048).
    """

    class RelojQueAnuncia(RelojDetenido):
        """Avisa cuando ``dormir`` empieza, que es después de la primera ``una_vez``."""

        def __init__(self, inicio: float) -> None:
            super().__init__(inicio)
            self.en_dormir = threading.Event()

        async def dormir(self, segundos: float) -> None:
            self.en_dormir.set()
            await super().dormir(segundos)

    reloj = RelojQueAnuncia(1_794_700_000)
    almacen = AlmacenEnMemoria(reloj=reloj)
    app = crear_app(
        configuracion,
        _cliente_pey(pey),
        reloj,
        almacen=almacen,
        tareas_en_segundo_plano=True,
    )
    cobro = app.state.cobros.nuevo(Decimal("0.01"), "Tacos", 600, reloj.ahora())

    async def preparar() -> None:
        await app.state.cobros.guardar_nuevo(cobro)
        await app.state.cobros.vincular_qr(cobro, "qr-ciclo", "qr", None)

    import asyncio

    asyncio.run(preparar())
    app.state.reintentos.agregar(
        "msg_ciclo",
        codi_qr_id="qr-ciclo",
        transaccion_id="tx-ciclo",
        monto_recibido=Decimal("0.01"),
        pagado_en=100,
    )
    with TestClient(app):
        assert reloj.en_dormir.wait(2)
        assert "msg_ciclo" not in app.state.reintentos.avisos
        assert len(cobro.pagos) == 1
