"""Pruebas de la consulta de respaldo (spec 001, RF-014, RF-025, RF-026, RF-027, RF-039)."""

import logging
from decimal import Decimal

import httpx
import pytest

from app.almacen import AlmacenEnMemoria
from app.cobros import RepositorioCobros
from app.eventos import Difusor
from app.pey import ClientePey, ErrorPey, PagoPey
from app.reloj import RelojFalso
from tests.conftest import BASE_PEY_DE_PRUEBA, PeySimulado


def test_sin_webhook_el_estado_se_confirma_consultando_a_pey(cliente, pey, reloj) -> None:
    cobro = cliente.post("/api/cobros", json={"monto": 0.01}).json()
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pendiente"

    pey.transacciones = [{"id": "01TX", "status": "PAID", "amount": 0.01, "datePaid": 1790724818}]
    reloj.avanzar(3)
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pagado"


def test_cobro_inexistente_da_404(cliente) -> None:
    assert cliente.get("/api/cobros/nada").status_code == 404
    assert cliente.get("/api/cobros/nada/eventos").status_code == 404


def _pagina(items: list[dict], token: str | None, request_id: str) -> dict:
    return {"items": items, "nextToken": token, "requestId": request_id}


def _pagada(identificador: str, monto: int, base: int | None, pagado_en: int) -> dict:
    transaccion: dict = {
        "id": identificador,
        "status": "PAID",
        "amount": monto,
        "datePaid": pagado_en,
    }
    if base is not None:
        transaccion["amountBreakdown"] = {"base": base, "tip": monto - base}
    return transaccion


async def _consultar(pey: PeySimulado, vistas: set[str]):
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente = ClientePey(BASE_PEY_DE_PRUEBA, "llave-falsa", http)
    try:
        return await cliente.pagos_del_qr("ab12cd34ef", vistas)
    finally:
        await cliente.cerrar()


# El nombre lo fija la tarea y no cabe en 100 caracteres.
# fmt: off
@pytest.mark.asyncio
async def test_la_consulta_sigue_las_paginas_solo_mientras_haya_pagos_nuevos_y_solo_cuenta_los_pagados() -> None:  # noqa: E501
# fmt: on
    """Tres páginas si hay pagos nuevos; para si la tercera ya se conocía; lo normal es una."""
    pey = PeySimulado()
    pey.paginas = [
        _pagina(
            [
                {"id": "pend", "status": "PENDING", "amount": 1},
                _pagada("a", 10, 10, 100),
            ],
            "t2",
            "req-1",
        ),
        _pagina([_pagada("b", 20, None, 200)], "t3", "req-2"),
        _pagina([_pagada("c", 30, 25, 300)], None, "req-3"),
    ]
    resultado = await _consultar(pey, set())
    assert resultado.pagos == [
        PagoPey(id="a", monto=Decimal("10"), monto_base=Decimal("10"), pagado_en=100),
        PagoPey(id="b", monto=Decimal("20"), monto_base=None, pagado_en=200),
        PagoPey(id="c", monto=Decimal("30"), monto_base=Decimal("25"), pagado_en=300),
    ]
    assert resultado.paginas == 3
    assert resultado.request_id == "req-3"
    assert len([s for s in pey.solicitudes if s.method == "GET"]) == 3

    pey = PeySimulado()
    pey.paginas = [
        _pagina([_pagada("a", 10, 10, 100)], "t2", "req-1"),
        _pagina([_pagada("b", 20, None, 200)], "t3", "req-2"),
        _pagina([_pagada("c", 30, 25, 300)], "t4", "req-3"),
        _pagina([_pagada("d", 40, None, 400)], None, "req-4"),
    ]
    await _consultar(pey, {"c"})
    assert len([s for s in pey.solicitudes if s.method == "GET"]) == 3

    pey = PeySimulado()
    pey.paginas = [_pagina([_pagada("a", 10, 10, 100)], None, "req-1")]
    await _consultar(pey, set())
    assert len([s for s in pey.solicitudes if s.method == "GET"]) == 1


@pytest.mark.asyncio
async def test_si_pey_tarda_mas_de_4_segundos_la_consulta_cuenta_como_sin_respuesta() -> None:
    """Un tiempo agotado es un error de conexión y la petición espera 4 s (QP-1, RF-027)."""
    pey = PeySimulado()
    pey.tiempo_agotado = True
    with pytest.raises(ErrorPey) as error:
        await _consultar(pey, set())
    assert error.value.tipo == "sin conexión"
    assert pey.solicitudes[0].extensions["timeout"]["read"] == 4.0


async def _armado():
    from app.respaldo import ConsultaDeRespaldo

    reloj = RelojFalso(inicio=1_794_700_000)
    repositorio = RepositorioCobros(AlmacenEnMemoria(reloj=reloj), reloj)
    difusor = Difusor()
    pey = PeySimulado()
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, "llave", http)
    consulta = ConsultaDeRespaldo(cliente_pey, repositorio, difusor, reloj)
    cobro = repositorio.nuevo(Decimal("0.01"), "Tacos", 600, ahora=reloj.ahora())
    await repositorio.guardar_nuevo(cobro)
    await repositorio.vincular_qr(cobro, "ab12cd34ef", "qr", None)
    return reloj, difusor, pey, cliente_pey, consulta, cobro


def _gets(pey: PeySimulado) -> int:
    return len([solicitud for solicitud in pey.solicitudes if solicitud.method == "GET"])


@pytest.mark.asyncio
async def test_la_consulta_respeta_el_intervalo_y_avisa_el_pago() -> None:
    """El intervalo de 3 s y 5 s es compartido, y un pago nuevo publica el evento (RF-029)."""
    reloj, difusor, pey, cliente_pey, consulta, cobro = await _armado()
    try:
        await consulta.consultar(cobro, 3)
        await consulta.consultar(cobro, 5)
        assert _gets(pey) == 1
        reloj.avanzar(3)
        await consulta.consultar(cobro, 3)
        await consulta.consultar(cobro, 5)
        assert _gets(pey) == 2
        reloj.avanzar(5)
        await consulta.consultar(cobro, 5)
        assert _gets(pey) == 3

        cola = difusor.suscribir(cobro.id)
        pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 0.01, "datePaid": 100}]
        reloj.avanzar(3)
        await consulta.consultar(cobro, 3)
        evento, datos = cola.get_nowait()
        assert evento == "pago"
        assert datos["pago"]["numero"] == 1
        assert datos["cobro"]["numero_de_pagos"] == 1
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_fuera_de_la_ventana_no_consulta_y_un_error_no_se_propaga(caplog) -> None:
    """Fuera de la ventana no hay petición. Si pey falla, queda un WARNING (RF-027)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    reloj, _difusor, pey, cliente_pey, consulta, cobro = await _armado()
    try:
        reloj.avanzar(600)
        await consulta.consultar(cobro, 3)
        assert _gets(pey) == 0
    finally:
        await cliente_pey.cerrar()
    _reloj, _difusor, pey, cliente_pey, consulta, cobro = await _armado()
    try:
        pey.estado_consulta = 500
        await consulta.consultar(cobro, 3)
        pey.estado_consulta = 200
        pey.tiempo_agotado = True
        _reloj.avanzar(3)
        await consulta.consultar(cobro, 3)
        assert cobro.numero_de_pagos == 0
        assert any(
            cobro.id in registro.getMessage() and registro.levelno == logging.WARNING
            for registro in caplog.records
        )
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_cada_consulta_a_pey_deja_una_linea_en_el_registro(caplog) -> None:
    """Cada consulta deja páginas, pagos nuevos y requestId, aunque no haya pagos (RF-039)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    _reloj, _difusor, pey, cliente_pey, consulta, cobro = await _armado()
    try:
        pey.request_id = "req-consulta"
        await consulta.consultar(cobro, 3)
        assert any(
            cobro.id in registro.getMessage()
            and "req-consulta" in registro.getMessage()
            and "paginas=1" in registro.getMessage()
            and "pagos_nuevos=0" in registro.getMessage()
            and registro.levelno == logging.INFO
            for registro in caplog.records
            if registro.name == "pago_facil"
        )
    finally:
        await cliente_pey.cerrar()


def test_despues_de_la_gracia_ya_no_se_consulta_a_pey(cliente, pey, reloj) -> None:
    """En expira_en + 600 ya no se pregunta a pey y el canal cierra (RF-025, RF-043)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    assert cobro["fin_ventana"] == cobro["expira_en"] + 600
    reloj.avanzar(cobro["fin_ventana"] - reloj.ahora())
    antes = _gets(pey)
    visto = cliente.get(f"/api/cobros/{cobro['id']}")
    assert visto.status_code == 200
    assert visto.json()["estado"] == "vencido"
    assert _gets(pey) == antes
    canal = cliente.get(f"/api/cobros/{cobro['id']}/eventos")
    assert canal.status_code == 200
    assert "event: estado" in canal.text
    assert "event: fin" in canal.text
    assert canal.text.index("event: estado") < canal.text.index("event: fin")
    assert _gets(pey) == antes


def test_ver_el_cobro_consulta_a_pey_como_maximo_cada_3_segundos(cliente, pey, reloj) -> None:
    """Tres lecturas seguidas hacen una sola consulta; a los 3 s, otra (RF-025)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    for _ in range(3):
        assert cliente.get(f"/api/cobros/{cobro['id']}").status_code == 200
    assert _gets(pey) == 1
    reloj.avanzar(3)
    cliente.get(f"/api/cobros/{cobro['id']}")
    assert _gets(pey) == 2


@pytest.mark.parametrize("fallo", ["error", "tiempo"])
def test_si_pey_no_responde_se_devuelve_el_ultimo_estado(cliente, pey, fallo) -> None:
    """Si pey falla o se agota el tiempo, ver el cobro responde 200 con lo último (RF-027)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    if fallo == "error":
        pey.estado_consulta = 500
    else:
        pey.tiempo_agotado = True
    respuesta = cliente.get(f"/api/cobros/{cobro['id']}")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "pendiente"


def test_el_mismo_pago_no_se_registra_dos_veces_por_aviso_ni_por_consulta() -> None:
    """Un pago llegado por aviso y luego por consulta queda una sola vez y se avisa una (CE-005)."""
    import asyncio

    async def escenario() -> None:
        _reloj, difusor, pey, cliente_pey, consulta, cobro = await _armado()
        try:
            cola = difusor.suscribir(cobro.id)
            await consulta.registrar_y_avisar(cobro, "tx-1", Decimal("0.01"), None, 100, "aviso")
            pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 0.01, "datePaid": 100}]
            await consulta.consultar(cobro, 3)
            assert cobro.numero_de_pagos == 1
            assert cola.qsize() == 1
        finally:
            await cliente_pey.cerrar()

    asyncio.run(escenario())


def test_un_cobro_que_no_existe_da_404(cliente) -> None:
    """Un id desconocido responde que ese cobro no existe (RF-008)."""
    respuesta = cliente.get("/api/cobros/nada")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Ese cobro no existe"


@pytest.mark.asyncio
async def test_si_el_almacen_falla_la_consulta_registra_la_falla_y_la_reintenta(caplog) -> None:
    """Un pago que no se guarda no se emite. La consulta sigue y la siguiente lo registra.

    (spec 003, RF-002, RF-016).
    """
    from app.respaldo import ConsultaDeRespaldo
    from tests.almacen_de_prueba import AlmacenQueFalla

    caplog.set_level(logging.WARNING, logger="pago_facil")
    reloj = RelojFalso(inicio=1_794_700_000)
    almacen = AlmacenQueFalla(reloj=reloj)
    repositorio = RepositorioCobros(almacen, reloj)
    difusor = Difusor()
    pey = PeySimulado()
    cliente_pey = ClientePey(
        BASE_PEY_DE_PRUEBA, "llave", httpx.AsyncClient(transport=httpx.MockTransport(pey))
    )
    consulta = ConsultaDeRespaldo(cliente_pey, repositorio, difusor, reloj)
    cobro = repositorio.nuevo(Decimal("0.01"), "Tacos", 600, ahora=reloj.ahora())
    await repositorio.guardar_nuevo(cobro)
    await repositorio.vincular_qr(cobro, "ab12cd34ef", "qr", None)
    cola = difusor.suscribir(cobro.id)
    pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 0.01, "datePaid": 100}]
    almacen.fallar("registrar_pago", veces=1)
    try:
        reloj.avanzar(3)
        await consulta.consultar(cobro, 3)
        assert cobro.pagos == []
        assert cola.empty()
        lineas = [
            registro.getMessage()
            for registro in caplog.records
            if registro.name == "pago_facil" and registro.levelno >= logging.WARNING
        ]
        assert any(
            "sin respuesta" in linea
            and "registrar pago" in linea
            and cobro.id in linea
            and "OperationalError" in linea
            for linea in lineas
        )
        reloj.avanzar(3)
        await consulta.consultar(cobro, 3)
        assert len(cobro.pagos) == 1
        assert cola.get_nowait()[0] == "pago"
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_si_el_almacen_rechaza_los_datos_la_consulta_lo_registra_como_rechazo(
    caplog,
) -> None:
    """Un dato rechazado no se dice «sin respuesta»: la línea lo distingue (spec 003, DP-34)."""
    from app.respaldo import ConsultaDeRespaldo
    from tests.almacen_de_prueba import CLASE_DE_DATOS, AlmacenQueFalla

    caplog.set_level(logging.WARNING, logger="pago_facil")
    reloj = RelojFalso(inicio=1_794_700_000)
    almacen = AlmacenQueFalla(reloj=reloj)
    repositorio = RepositorioCobros(almacen, reloj)
    pey = PeySimulado()
    cliente_pey = ClientePey(
        BASE_PEY_DE_PRUEBA, "llave", httpx.AsyncClient(transport=httpx.MockTransport(pey))
    )
    consulta = ConsultaDeRespaldo(cliente_pey, repositorio, Difusor(), reloj)
    cobro = repositorio.nuevo(Decimal("0.01"), "Tacos", 600, ahora=reloj.ahora())
    await repositorio.guardar_nuevo(cobro)
    await repositorio.vincular_qr(cobro, "ab12cd34ef", "qr", None)
    pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 0.01, "datePaid": 100}]
    almacen.fallar_datos("registrar_pago")
    try:
        reloj.avanzar(3)
        await consulta.consultar(cobro, 3)
    finally:
        await cliente_pey.cerrar()
    lineas = [r.getMessage() for r in caplog.records if r.name == "pago_facil"]
    assert any(
        "rechazó los datos" in linea
        and "registrar pago" in linea
        and cobro.id in linea
        and CLASE_DE_DATOS in linea
        for linea in lineas
    )
    assert not any("sin respuesta" in linea for linea in lineas)
