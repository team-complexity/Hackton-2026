"""Lista de reintentos y el bucle de fondo, sin tiempo real (spec 003, T059, TK-18).

T050 a T054 no cubren ``agregar``, el cobro que ya no está, el error de datos
ni el bucle de ``correr_tareas``. Pey es simulado y el reloj no espera.
"""

import logging
from decimal import Decimal

import httpx
import pytest

from app.cobros import RepositorioCobros
from app.eventos import Difusor
from app.pey import ClientePey
from app.reloj import RelojFalso
from app.respaldo import ConsultaDeRespaldo
from app.tareas import EVENTO_QR_PAGADO, ReintentosDeAvisos, correr_tareas
from tests.almacen_de_prueba import CLASE_DE_DATOS, CLASE_DE_FALLA, AlmacenQueFalla, RelojPorPasos
from tests.conftest import BASE_PEY_DE_PRUEBA, PeySimulado


def _armado(almacen=None):
    """Repositorio, consulta y lista sobre un almacén que no sale a la red."""
    reloj = RelojFalso(inicio=1_794_700_000)
    if almacen is None:
        from app.almacen import AlmacenEnMemoria

        almacen = AlmacenEnMemoria(reloj=reloj)
    repositorio = RepositorioCobros(almacen, reloj)
    pey = PeySimulado()
    cliente_pey = ClientePey(
        BASE_PEY_DE_PRUEBA,
        "llave",
        httpx.AsyncClient(transport=httpx.MockTransport(pey)),
    )
    consulta = ConsultaDeRespaldo(cliente_pey, repositorio, Difusor(), reloj)
    return almacen, repositorio, consulta, cliente_pey, ReintentosDeAvisos(repositorio, consulta)


def _agregar(reintentos: ReintentosDeAvisos, webhook_id: str, codi_qr_id: str = "qr-1") -> None:
    reintentos.agregar(
        webhook_id,
        codi_qr_id=codi_qr_id,
        transaccion_id="tx-1",
        monto_recibido=Decimal("0.01"),
        pagado_en=100,
    )


def test_agregar_no_duplica_un_webhook_id() -> None:
    """El mismo aviso, dos veces, deja una sola entrada y nada de quien paga.

    (spec 003, RF-048, RF-009).
    """
    _almacen, _repositorio, _consulta, cliente_pey, reintentos = _armado()
    try:
        _agregar(reintentos, "msg_una")
        _agregar(reintentos, "msg_una")
        reintentos.agregar(
            "msg_una",
            codi_qr_id="otro",
            transaccion_id="tx-otra",
            monto_recibido=Decimal("9"),
            pagado_en=200,
        )
    finally:
        import asyncio

        asyncio.run(cliente_pey.cerrar())
    assert list(reintentos.avisos) == ["msg_una"]
    aviso = reintentos.avisos["msg_una"]
    assert aviso["codi_qr_id"] == "qr-1"
    assert aviso["transaccion_id"] == "tx-1"
    assert aviso["monto_recibido"] == Decimal("0.01")
    assert aviso["pagado_en"] == 100
    assert aviso["intentos"] == 0
    assert "metadata" not in aviso


@pytest.mark.asyncio
async def test_una_vez_con_un_cobro_que_no_existe_lo_guarda_como_ignorado_y_lo_quita() -> None:
    """Si el cobro no está, el aviso se marca ignorado y sale de la lista (spec 003, RF-048)."""
    almacen, repositorio, _consulta, cliente_pey, reintentos = _armado()
    try:
        _agregar(reintentos, "msg_no", codi_qr_id="qr-no-existe")
        await reintentos.una_vez()
        assert "msg_no" not in reintentos.avisos
        assert await repositorio.aviso_ya_visto("msg_no") is True
        assert almacen.datos.avisos["msg_no"] == EVENTO_QR_PAGADO
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_una_vez_con_el_almacen_caido_suma_un_intento_y_conserva_el_aviso(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Si la base no responde, suma un intento, deja la línea y el aviso sigue.

    (spec 003, RF-048).
    """
    caplog.set_level(logging.ERROR, logger="pago_facil")
    reloj = RelojFalso(inicio=1_794_700_000)
    almacen = AlmacenQueFalla(reloj=reloj)
    _almacen, repositorio, _consulta, cliente_pey, reintentos = _armado(almacen)
    cobro = repositorio.nuevo(Decimal("0.01"), "Tacos", 600, reloj.ahora())
    try:
        await repositorio.guardar_nuevo(cobro)
        await repositorio.vincular_qr(cobro, "qr-caido", "qr", None)
        almacen.fallar("registrar_pago")
        _agregar(reintentos, "msg_caido", codi_qr_id="qr-caido")
        await reintentos.una_vez()
    finally:
        await cliente_pey.cerrar()
    assert reintentos.avisos["msg_caido"]["intentos"] == 1
    assert "msg_caido" in reintentos.avisos
    assert any(
        registro.levelno == logging.ERROR
        and "Base de datos sin respuesta al registrar pago" in registro.getMessage()
        and cobro.id in registro.getMessage()
        and CLASE_DE_FALLA in registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil"
    )


@pytest.mark.asyncio
async def test_una_vez_con_error_de_datos_quita_el_aviso_y_lo_registra(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Un dato rechazado se anota y el aviso sale de la lista (spec 003, RF-048, DP-34)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    reloj = RelojFalso(inicio=1_794_700_000)
    almacen = AlmacenQueFalla(reloj=reloj)
    _almacen, repositorio, _consulta, cliente_pey, reintentos = _armado(almacen)
    cobro = repositorio.nuevo(Decimal("0.01"), "Tacos", 600, reloj.ahora())
    try:
        await repositorio.guardar_nuevo(cobro)
        await repositorio.vincular_qr(cobro, "qr-datos", "qr", None)
        almacen.fallar_datos("registrar_pago")
        _agregar(reintentos, "msg_datos", codi_qr_id="qr-datos")
        await reintentos.una_vez()
    finally:
        await cliente_pey.cerrar()
    assert "msg_datos" not in reintentos.avisos
    assert any(
        registro.levelno == logging.WARNING
        and "La base de datos rechazó los datos" in registro.getMessage()
        and "registrar pago" in registro.getMessage()
        and cobro.id in registro.getMessage()
        and CLASE_DE_DATOS in registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil"
    )


@pytest.mark.asyncio
async def test_correr_tareas_llama_una_vez_y_duerme_15_segundos_cada_vuelta() -> None:
    """Soltar el reloj vuelta por vuelta llama a una_vez y duerme 15 s, sin tiempo real.

    (spec 003, RF-048, DP-14).
    """
    import asyncio

    reloj = RelojPorPasos(1_794_700_000)
    veces = 0

    class _Cuenta:
        async def una_vez(self) -> None:
            nonlocal veces
            veces += 1

    tarea = asyncio.create_task(correr_tareas(_Cuenta(), reloj))
    try:
        for _ in range(20):
            if veces >= 1 and reloj.esperas == [15]:
                break
            await asyncio.sleep(0)
        assert veces == 1
        assert reloj.esperas == [15]
        reloj.soltar()
        for _ in range(20):
            if veces >= 2 and reloj.esperas == [15, 15]:
                break
            await asyncio.sleep(0)
        assert veces == 2
        assert reloj.esperas == [15, 15]
        assert reloj.ahora() == 1_794_700_000 + 15
    finally:
        tarea.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tarea
