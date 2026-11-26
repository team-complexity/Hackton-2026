"""Conciliación por latido, sin pey real, sin base real y sin tiempo real.

(spec 003, T068, RF-061, CE-017). El reloj no avanza solo. Quien arma la app
con ``RelojFalso`` deja el bucle apagado; el bucle se prueba con
``RelojPorPasos`` o ``RelojDetenido``.
"""

import asyncio
import logging
import threading
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient

from app.almacen import AlmacenEnMemoria
from app.cobros import Cobro, RepositorioCobros
from app.eventos import Difusor
from app.main import crear_app
from app.pey import ClientePey
from app.reloj import RelojFalso
from app.respaldo import ConsultaDeRespaldo
from app.tareas import LatidoDeConciliacion, ReintentosDeAvisos, correr_tareas
from tests.almacen_de_prueba import (
    CLASE_DE_FALLA,
    AlmacenQueFalla,
    RelojDetenido,
    RelojPorPasos,
    armar_app,
    reiniciar,
)
from tests.conftest import BASE_PEY_DE_PRUEBA, PeySimulado

INICIO = 1_794_700_000
CLABE_FALSA = "CLABE-FALSA"
NOMBRE_FALSO = "Nombre Falso"


def _mundo(
    reloj: RelojFalso | None = None,
    almacen: AlmacenEnMemoria | AlmacenQueFalla | None = None,
) -> tuple:
    """Repositorio, pey simulado y latido. El cliente HTTP no sale de la prueba."""
    if reloj is None:
        reloj = RelojFalso(inicio=INICIO)
    if almacen is None:
        almacen = AlmacenEnMemoria(reloj=reloj)
    repositorio = RepositorioCobros(almacen, reloj, gracia_segundos=0)
    pey = PeySimulado()
    cliente = ClientePey(
        BASE_PEY_DE_PRUEBA,
        "llave",
        httpx.AsyncClient(transport=httpx.MockTransport(pey)),
    )
    latido = LatidoDeConciliacion(repositorio, cliente, reloj, almacen)
    return almacen, repositorio, pey, cliente, latido, reloj


async def _cobro(
    repositorio: RepositorioCobros, reloj: RelojFalso, qr: str, expiracion: int
) -> Cobro:
    """Cobro guardado con QR. ``fin_ventana`` queda en ahora + expiración (gracia 0)."""
    cobro = repositorio.nuevo(Decimal("0.01"), "Tacos", expiracion, reloj.ahora())
    await repositorio.guardar_nuevo(cobro)
    await repositorio.vincular_qr(cobro, qr, "qr", None)
    return cobro


def _tx(transaccion_id: str) -> dict:
    """Transacción pagada ficticia. La metadata no debe salir en el registro."""
    return {
        "id": transaccion_id,
        "status": "PAID",
        "amount": 0.01,
        "datePaid": INICIO + 50,
        "metadata": {"nombre": NOMBRE_FALSO, "clabe": CLABE_FALSA},
    }


def _gets(pey: PeySimulado, qr: str | None = None) -> list[httpx.Request]:
    return [
        solicitud
        for solicitud in pey.solicitudes
        if solicitud.method == "GET"
        and solicitud.url.path.startswith("/transaction/codi/qr/")
        and (qr is None or solicitud.url.path.endswith("/" + qr))
    ]


def _lineas(caplog: pytest.LogCaptureFixture, nivel: int = logging.INFO) -> list[str]:
    return [
        registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil" and registro.levelno >= nivel
    ]


@pytest.mark.asyncio
async def test_la_primera_vez_no_se_revisa_hacia_atras(caplog: pytest.LogCaptureFixture) -> None:
    """Sin fila, la marca es la hora del reloj y pey no se consulta (spec 003, RF-061)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        cobro = await _cobro(repositorio, reloj, "qr-atras", 100)
        reloj.avanzar(100)
        pey.para_el_qr("qr-atras", transacciones=[_tx("tx-atras")])
        await latido.una_vez()
        assert await almacen.leer_conciliado_hasta() == reloj.ahora()
        assert _gets(pey) == []
        assert cobro.pagos == []
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_al_arrancar_se_concilian_las_ventanas_que_terminaron_apagado(
    configuracion, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tras el apagado, el primer latido registra el pago una vez y no avisa.

    (spec 003, RF-061, CE-017).
    """
    publicados: list[tuple[str, str]] = []

    def publicar(self, cobro_id: str, evento: str, datos: dict) -> None:
        del self, datos
        publicados.append((cobro_id, evento))

    monkeypatch.setattr(Difusor, "publicar", publicar)
    reloj = RelojFalso(inicio=INICIO)
    pey = PeySimulado()
    almacen = AlmacenEnMemoria(reloj=reloj)
    app = armar_app(configuracion, pey, reloj, almacen)
    cobro = app.state.cobros.nuevo(Decimal("0.01"), "Tacos", 600, reloj.ahora())
    await app.state.cobros.guardar_nuevo(cobro)
    await app.state.cobros.vincular_qr(cobro, "qr-apagado", "qr", "aW1n")
    await app.state.latido.una_vez()
    assert await almacen.leer_conciliado_hasta() == reloj.ahora()
    reloj.avanzar(cobro.fin_ventana - reloj.ahora())
    pey.para_el_qr("qr-apagado", transacciones=[_tx("tx-apagado")])
    nueva = reiniciar(app)
    try:
        await nueva.state.latido.una_vez()
        guardado = await nueva.state.cobros.por_codi_qr("qr-apagado")
        assert guardado is not None
        assert len(guardado.pagos) == 1
        assert guardado.pagos[0].fuente == "consulta"
        assert guardado.pagos[0].transaccion_id == "tx-apagado"
        await nueva.state.latido.una_vez()
        assert len(guardado.pagos) == 1
        assert publicados == []
    finally:
        await app.state.latido._pey.cerrar()
        await nueva.state.latido._pey.cerrar()


@pytest.mark.asyncio
async def test_el_latido_registra_un_aviso_perdido_cuando_termina_la_ventana(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El pago que no llegó por el aviso se registra al terminar la ventana, sin canal.

    (spec 003, RF-061).
    """
    publicados: list[str] = []
    monkeypatch.setattr(Difusor, "publicar", lambda *args, **kwargs: publicados.append("pago"))
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        cobro = await _cobro(repositorio, reloj, "qr-perdido", 100)
        await almacen.guardar_conciliado_hasta(reloj.ahora())
        pey.para_el_qr("qr-perdido", transacciones=[_tx("tx-perdido")])
        reloj.avanzar(100)
        await latido.una_vez()
        assert len(cobro.pagos) == 1
        assert cobro.pagos[0].fuente == "consulta"
        assert cobro.pagos[0].transaccion_id == "tx-perdido"
        assert publicados == []
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_si_pey_falla_conciliado_hasta_no_avanza() -> None:
    """Una falla pasajera en el segundo cobro deja la marca en el primero (spec 003, RF-061)."""
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        primero = await _cobro(repositorio, reloj, "qr-uno", 100)
        segundo = await _cobro(repositorio, reloj, "qr-dos", 200)
        tercero = await _cobro(repositorio, reloj, "qr-tres", 300)
        await almacen.guardar_conciliado_hasta(reloj.ahora())
        reloj.avanzar(300)
        pey.para_el_qr("qr-dos", estado=500)
        await latido.una_vez()
        assert await almacen.leer_conciliado_hasta() == primero.fin_ventana
        assert _gets(pey, "qr-uno") != []
        assert _gets(pey, "qr-dos") != []
        assert _gets(pey, "qr-tres") == []
        pey.para_el_qr("qr-dos", transacciones=[_tx("tx-dos")])
        antes = len(_gets(pey, "qr-uno"))
        await latido.una_vez()
        assert len(_gets(pey, "qr-uno")) == antes
        assert len(segundo.pagos) == 1
        assert segundo.pagos[0].transaccion_id == "tx-dos"
        assert tercero.pagos == []
        assert await almacen.leer_conciliado_hasta() == reloj.ahora()
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_si_el_almacen_falla_a_medias_la_marca_queda_en_el_cobro_anterior() -> None:
    """Lo ya conciliado no se pierde: la marca avanza hasta el cobro anterior al que falló.

    (spec 003, RF-061, QP-13, TK-23).
    """
    reloj = RelojFalso(inicio=INICIO)
    almacen = AlmacenQueFalla(reloj=reloj)
    _almacen, repositorio, pey, cliente, latido, _reloj = _mundo(reloj, almacen)
    try:
        primero = await _cobro(repositorio, reloj, "qr-ya", 100)
        segundo = await _cobro(repositorio, reloj, "qr-falla", 200)
        await almacen.guardar_conciliado_hasta(INICIO)
        reloj.avanzar(200)
        pey.para_el_qr("qr-falla", transacciones=[_tx("tx-falla")])
        almacen.fallar("registrar_pago", veces=1)
        await latido.una_vez()
        assert await almacen.leer_conciliado_hasta() == primero.fin_ventana
        assert segundo.pagos == []
        await latido.una_vez()
        assert len(segundo.pagos) == 1
        assert await almacen.leer_conciliado_hasta() == reloj.ahora()
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_la_conciliacion_no_duplica_un_pago_ya_registrado() -> None:
    """La misma transacción, ya guardada, no se vuelve a registrar (spec 003, RF-007)."""
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        cobro = await _cobro(repositorio, reloj, "qr-dup", 100)
        await repositorio.registrar_pago(
            cobro, "tx-dup", Decimal("0.01"), None, INICIO + 50, "aviso"
        )
        await almacen.guardar_conciliado_hasta(reloj.ahora())
        pey.para_el_qr("qr-dup", transacciones=[_tx("tx-dup")])
        reloj.avanzar(100)
        await latido.una_vez()
        assert len(cobro.pagos) == 1
        assert cobro.pagos[0].fuente == "aviso"
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_un_qr_que_pey_no_conoce_no_bloquea_la_conciliacion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Un 404 se anota, el cobro se salta y la marca avanza (spec 003, RF-061, QP-13)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        cobro = await _cobro(repositorio, reloj, "qr-ajeno", 100)
        siguiente = await _cobro(repositorio, reloj, "qr-sigue", 200)
        await almacen.guardar_conciliado_hasta(reloj.ahora())
        reloj.avanzar(200)
        pey.para_el_qr("qr-ajeno", estado=404)
        pey.para_el_qr("qr-sigue", transacciones=[_tx("tx-sigue")])
        await latido.una_vez()
        assert any(
            "conciliar" in linea and cobro.id in linea and "requestId=r1" in linea
            for linea in _lineas(caplog)
        )
        assert len(siguiente.pagos) == 1
        assert await almacen.leer_conciliado_hasta() == reloj.ahora()
        pedidos = len(_gets(pey, "qr-ajeno"))
        await latido.una_vez()
        assert len(_gets(pey, "qr-ajeno")) == pedidos
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_tras_10_fallas_el_cobro_se_salta_con_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A la décima falla pasajera hay un ERROR, el cobro se salta y la marca avanza.

    (spec 003, RF-061, QP-13).
    """
    caplog.set_level(logging.INFO, logger="pago_facil")
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        cobro = await _cobro(repositorio, reloj, "qr-lento", 100)
        await almacen.guardar_conciliado_hasta(INICIO)
        reloj.avanzar(100)
        pey.para_el_qr("qr-lento", sin_conexion=True)
        for _ in range(9):
            await latido.una_vez()
            assert await almacen.leer_conciliado_hasta() == INICIO
        await latido.una_vez()
        assert any(
            registro.levelno == logging.ERROR and cobro.id in registro.getMessage()
            for registro in caplog.records
            if registro.name == "pago_facil"
        )
        assert await almacen.leer_conciliado_hasta() == reloj.ahora()
        pedidos = len(_gets(pey, "qr-lento"))
        await latido.una_vez()
        assert len(_gets(pey, "qr-lento")) == pedidos
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_el_latido_escribe_en_la_base_cada_minuto() -> None:
    """Los reintentos corren cada 15 s y la marca se escribe cada 60 s, sin cobros.

    (spec 003, RF-039, RF-048, QT-7).
    """
    reloj = RelojPorPasos(INICIO)
    almacen = AlmacenEnMemoria(reloj=reloj)
    repositorio = RepositorioCobros(almacen, reloj, gracia_segundos=0)
    pey = PeySimulado()
    cliente = ClientePey(
        BASE_PEY_DE_PRUEBA,
        "llave",
        httpx.AsyncClient(transport=httpx.MockTransport(pey)),
    )
    reintentos = ReintentosDeAvisos(
        repositorio, ConsultaDeRespaldo(cliente, repositorio, Difusor(), reloj)
    )
    latido = LatidoDeConciliacion(repositorio, cliente, reloj, almacen)
    tarea = asyncio.create_task(correr_tareas(reintentos, reloj, latido))
    try:
        for _ in range(50):
            if reloj.esperas == [15]:
                break
            await asyncio.sleep(0)
        assert reloj.esperas == [15]
        assert await almacen.leer_conciliado_hasta() == INICIO
        for paso in range(2, 6):
            reloj.soltar()
            for _ in range(50):
                if reloj.esperas == [15] * paso:
                    break
                await asyncio.sleep(0)
            assert reloj.esperas == [15] * paso
        assert await almacen.leer_conciliado_hasta() == INICIO + 60
        assert _gets(pey) == []
    finally:
        tarea.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarea
        await cliente.cerrar()


def test_al_arrancar_se_corre_el_primer_latido(configuracion) -> None:
    """Al entrar al cliente el latido corre una vez y se queda en ``dormir``.

    (spec 003, RF-061). ``RelojDetenido`` no deja otra vuelta.
    """

    class RelojQueAnuncia(RelojDetenido):
        """Avisa cuando empieza ``dormir``, que es después del primer latido."""

        def __init__(self, inicio: float) -> None:
            super().__init__(inicio)
            self.en_dormir = threading.Event()

        async def dormir(self, segundos: float) -> None:
            self.en_dormir.set()
            await super().dormir(segundos)

    reloj = RelojQueAnuncia(INICIO)
    pey = PeySimulado()
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente = ClientePey(BASE_PEY_DE_PRUEBA, configuracion.pey_api_key.get_secret_value(), http)
    almacen = AlmacenEnMemoria(reloj=reloj)
    app = crear_app(
        configuracion,
        cliente,
        reloj,
        almacen=almacen,
        tareas_en_segundo_plano=True,
    )
    with TestClient(app):
        assert reloj.en_dormir.wait(2)
        assert almacen.datos.conciliado_hasta == INICIO


@pytest.mark.asyncio
async def test_si_la_base_falla_en_el_latido_se_registra_y_se_reintenta(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Si no se pueden listar los cobros, la línea dice ``latido`` y la marca no cambia.

    (spec 003, RF-016).
    """
    caplog.set_level(logging.ERROR, logger="pago_facil")
    reloj = RelojFalso(inicio=INICIO)
    almacen = AlmacenQueFalla(reloj=reloj)
    _almacen, repositorio, pey, cliente, latido, _reloj = _mundo(reloj, almacen)
    try:
        cobro = await _cobro(repositorio, reloj, "qr-base", 100)
        await almacen.guardar_conciliado_hasta(INICIO)
        reloj.avanzar(100)
        pey.para_el_qr("qr-base", transacciones=[_tx("tx-base")])
        almacen.fallar("cobros_con_ventana_terminada")
        await latido.una_vez()
        assert await almacen.leer_conciliado_hasta() == INICIO
        assert cobro.pagos == []
        assert any(
            "latido" in registro.getMessage() and CLASE_DE_FALLA in registro.getMessage()
            for registro in caplog.records
            if registro.name == "pago_facil" and registro.levelno == logging.ERROR
        )
        almacen.quitar_falla("cobros_con_ventana_terminada")
        await latido.una_vez()
        assert len(cobro.pagos) == 1
        assert await almacen.leer_conciliado_hasta() == reloj.ahora()
    finally:
        await cliente.cerrar()


@pytest.mark.asyncio
async def test_cada_consulta_de_la_conciliacion_registra_el_requestid_de_pey(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """La línea de una respuesta y la de un 404 llevan el cobro y ``requestId=r1``.

    (spec 003, RF-009, principio X).
    """
    caplog.set_level(logging.INFO, logger="pago_facil")
    almacen, repositorio, pey, cliente, latido, reloj = _mundo()
    try:
        bueno = await _cobro(repositorio, reloj, "qr-ok", 100)
        ajeno = await _cobro(repositorio, reloj, "qr-404", 200)
        await almacen.guardar_conciliado_hasta(reloj.ahora())
        reloj.avanzar(200)
        pey.para_el_qr("qr-ok", transacciones=[_tx("tx-ok")])
        pey.para_el_qr("qr-404", estado=404)
        await latido.una_vez()
        lineas = _lineas(caplog)
        assert any(
            linea.startswith("Conciliación ")
            and f"cobro={bueno.id}" in linea
            and "paginas=" in linea
            and "pagos_nuevos=" in linea
            and "requestId=r1" in linea
            for linea in lineas
        )
        assert any(
            linea.startswith("No se pudo conciliar el cobro ")
            and ajeno.id in linea
            and "requestId=r1" in linea
            for linea in lineas
        )
        texto = "\n".join(lineas)
        assert CLABE_FALSA not in texto
        assert NOMBRE_FALSO not in texto
    finally:
        await cliente.cerrar()
