"""Guardar cobros y sobrevivir a un reinicio, por la API (spec 003, T052).

Usa el almacén en memoria y ``reiniciar``: otra app sobre los mismos datos,
el mismo reloj falso y el mismo pey simulado.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

from app.eventos import Difusor
from app.reloj import RelojFalso
from tests.almacen_de_prueba import AlmacenQueFalla, armar_app, cliente_de, reiniciar
from tests.conftest import SECRETO_FALSO, PeySimulado, enviar_aviso, firmar_aviso, pago

DATOS_DE_QUIEN_PAGA = {
    "nombre": "Persona Falsa",
    "clabe": "000000000000000000",
    "banco": "Banco Falso",
    "telefono": "5500000000",
    "claveDeRastreo": "rastreo-falso",
}


def _app(configuracion, pey: PeySimulado, reloj: RelojFalso, almacen: object | None = None):
    if almacen is None:
        from app.almacen import AlmacenEnMemoria

        almacen = AlmacenEnMemoria(reloj=reloj)
    return armar_app(configuracion, pey, reloj, almacen), almacen


def _crear(cliente, pey: PeySimulado, qr_id: str) -> dict:
    pey.id_qr = qr_id
    respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    assert respuesta.status_code == 201
    return respuesta.json()


def _cuerpo(qr_id: str, transaccion: str) -> dict:
    return pago(transaccion) | {"codiQrId": qr_id}


@asynccontextmanager
async def _asgi(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente concurrente. El ciclo de vida deja ``app.state.pey`` listo.

    (spec 003, principio V).
    """
    async with app.router.lifespan_context(app):
        transporte = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://test") as cliente:
            yield cliente


async def _enviar(cliente: httpx.AsyncClient, datos: dict, webhook_id: str) -> httpx.Response:
    import json
    from datetime import UTC, datetime

    cuerpo = json.dumps(datos)
    cabeceras = firmar_aviso(cuerpo, SECRETO_FALSO, webhook_id, datetime.now(UTC))
    cabeceras["content-type"] = "application/json"
    return await cliente.post("/webhooks/pey", content=cuerpo, headers=cabeceras)


async def _ya_pausadas(almacen: AlmacenQueFalla, operacion: str, cuantas: int) -> None:
    for _ in range(1000):
        if sum(llamada.operacion == operacion for llamada in almacen.llamadas) >= cuantas:
            return
        await asyncio.sleep(0)
    raise AssertionError("la operación no llegó a pausarse")


async def _con_la_otra_esperando(almacen: AlmacenQueFalla) -> None:
    """Deja una petición dentro del almacén y a la otra esperando el candado del cobro (DP-8).

    Con un candado por cobro solo una llega a ``registrar_pago``; las vueltas extra dejan
    a la otra esperando antes de soltar la pausa. Sin ellas el evento se suelta antes de que
    haya dos peticiones y la prueba pasaría aunque no hubiera candado.
    """
    await _ya_pausadas(almacen, "registrar_pago", 1)
    for _ in range(20):
        await asyncio.sleep(0)


def test_un_cobro_creado_queda_guardado_con_su_imagen_del_qr(configuracion, pey, reloj) -> None:
    """Tras reiniciar, el cobro vuelve con la imagen del QR (spec 003, RF-001, RF-010)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-imagen")
    with cliente_de(reiniciar(app)) as cliente:
        visto = cliente.get(f"/api/cobros/{cobro['id']}")
    assert visto.status_code == 200
    cuerpo = visto.json()
    assert cuerpo["id"] == cobro["id"]
    assert cuerpo["qr"] == cobro["qr"]
    assert cuerpo["qr_imagen"] == "aW1n"
    assert cuerpo["monto"] == 0.01
    assert cuerpo["concepto"] == "Tacos"


def test_el_pago_se_guarda_antes_de_emitirse_por_el_canal(
    configuracion, pey, reloj, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si registrar el pago falla no se emite; si no, al emitir ya está guardado.

    (spec 003, RF-002).
    """
    almacen = AlmacenQueFalla(reloj=reloj)
    app, _ = _app(configuracion, pey, reloj, almacen)
    emitidos: list[str] = []
    original = Difusor.publicar

    def publicar(self: Difusor, cobro_id: str, evento: str, datos: dict) -> None:
        if evento == "pago":
            assert almacen.pagos_listos
        emitidos.append(evento)
        original(self, cobro_id, evento, datos)

    monkeypatch.setattr(Difusor, "publicar", publicar)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-orden")
        almacen.fallar("registrar_pago")
        fallo = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-falla"), webhook_id="msg_falla"
        )
        assert fallo.status_code == 503
        assert "pago" not in emitidos
        almacen.quitar_falla("registrar_pago")
        bien = enviar_aviso(cliente, _cuerpo(cobro["codi_qr_id"], "tx-bien"), webhook_id="msg_bien")
        assert bien.status_code == 200
        assert bien.json()["procesado"] is True
    assert "pago" in emitidos
    assert "tx-bien" in almacen.pagos_listos


def test_el_webhook_id_procesado_queda_guardado(configuracion, pey, reloj) -> None:
    """El mismo aviso, después de reiniciar, ya no se procesa (spec 003, RF-003)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-aviso")
        primero = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_visto"
        )
        assert primero.json()["procesado"] is True
    with cliente_de(reiniciar(app)) as cliente:
        repetido = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_visto"
        )
        assert repetido.status_code == 200
        assert repetido.json()["procesado"] is False
        assert cliente.get(f"/api/cobros/{cobro['id']}").json()["numero_de_pagos"] == 1


def test_la_cancelacion_queda_guardada_con_su_hora(configuracion, pey, reloj) -> None:
    """La hora de la cancelación sigue ahí después de reiniciar (spec 003, RF-004)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-cancel")
        hora = int(reloj.ahora())
        respuesta = cliente.post(f"/api/cobros/{cobro['id']}/cancelar")
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == "cancelado"
    app2 = reiniciar(app)
    with cliente_de(app2) as cliente:
        assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "cancelado"
    cargado = asyncio.run(app2.state.almacen.cargar_por_id(cobro["id"]))
    assert cargado is not None
    assert cargado.cancelado_en == hora


def test_dos_cargas_a_la_vez_del_mismo_cobro_dan_el_mismo_objeto(configuracion, pey, reloj) -> None:
    """Dos ``obtener`` con la carga en pausa devuelven el mismo objeto (spec 003, RF-005, DP-33)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-mismo")
    pausable = AlmacenQueFalla(datos=app.state.almacen.datos, reloj=reloj)
    app2 = armar_app(configuracion, pey, reloj, pausable)
    evento = pausable.pausar("cargar_por_id")

    async def escenario() -> None:
        repo = app2.state.cobros
        una = asyncio.create_task(repo.obtener(cobro["id"]))
        otra = asyncio.create_task(repo.obtener(cobro["id"]))
        await _ya_pausadas(pausable, "cargar_por_id", 2)
        evento.set()
        primero, segundo = await asyncio.gather(una, otra)
        assert primero is segundo
        assert primero is not None
        assert primero.id == cobro["id"]

    asyncio.run(escenario())


def test_tras_un_reinicio_se_puede_ver_cancelar_y_escuchar_un_cobro_guardado(
    configuracion, pey, reloj
) -> None:
    """Ver, cancelar y abrir el canal siguen funcionando (spec 003, RF-005, historia 1)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-vivo")
    with cliente_de(reiniciar(app)) as cliente:
        visto = cliente.get(f"/api/cobros/{cobro['id']}")
        assert visto.status_code == 200
        assert visto.json()["qr"] == cobro["qr"]
        assert visto.json()["monto"] == cobro["monto"]
        cancelado = cliente.post(f"/api/cobros/{cobro['id']}/cancelar")
        assert cancelado.status_code == 200
        assert cancelado.json()["estado"] == "cancelado"
        canal = cliente.get(f"/api/cobros/{cobro['id']}/eventos")
        assert canal.status_code == 200
        assert "event: estado" in canal.text


def test_tras_un_reinicio_el_aviso_de_pey_registra_el_pago(configuracion, pey, reloj) -> None:
    """Un aviso que llega después del reinicio registra el pago (spec 003, RF-005)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-pago")
    with cliente_de(reiniciar(app)) as cliente:
        aviso = enviar_aviso(cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_1")
        assert aviso.json()["procesado"] is True
        estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["estado"] == "pagado"
    assert estado["numero_de_pagos"] == 1
    assert estado["pagos"][0]["numero"] == 1


def test_tras_un_reinicio_la_consulta_de_respaldo_encuentra_el_pago(
    configuracion, pey, reloj
) -> None:
    """Sin aviso, la consulta de respaldo encuentra el pago guardado el cobro (spec 003, RF-005)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-respaldo")
    pey.transacciones = [{"id": "tx-respaldo", "status": "PAID", "amount": 0.01, "datePaid": 100}]
    with cliente_de(reiniciar(app)) as cliente:
        estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["estado"] == "pagado"
    assert estado["numero_de_pagos"] == 1
    assert estado["pagos"][0]["numero"] == 1


def test_el_estado_tras_un_reinicio_se_calcula_con_el_reloj_del_servidor(
    configuracion, pey, reloj
) -> None:
    """Cancelado y vencido se conservan, y un pago tardío dentro de la ventana entra.

    (spec 003, RF-006).
    """
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cancelado = _crear(cliente, pey, "qr-cancelado")
        vencido = _crear(cliente, pey, "qr-vencido")
        assert cliente.post(f"/api/cobros/{cancelado['id']}/cancelar").status_code == 200
        reloj.avanzar(cancelado["expira_en"] - reloj.ahora())
    with cliente_de(reiniciar(app)) as cliente:
        assert cliente.get(f"/api/cobros/{cancelado['id']}").json()["estado"] == "cancelado"
        assert cliente.get(f"/api/cobros/{vencido['id']}").json()["estado"] == "vencido"
        aviso = enviar_aviso(
            cliente, _cuerpo(vencido["codi_qr_id"], "tx-tarde"), webhook_id="msg_tarde"
        )
        assert aviso.json()["procesado"] is True
        assert cliente.get(f"/api/cobros/{vencido['id']}").json()["estado"] == "pagado"
        assert cliente.get(f"/api/cobros/{cancelado['id']}").json()["estado"] == "cancelado"


def test_un_aviso_reenviado_no_duplica_el_pago(configuracion, pey, reloj) -> None:
    """Reenviar el aviso, u otra vez la misma transacción, deja un solo pago (spec 003, RF-007)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-reenvio")
        cuerpo = _cuerpo(cobro["codi_qr_id"], "tx-1")
        assert enviar_aviso(cliente, cuerpo, webhook_id="msg_1").json()["procesado"] is True
        assert enviar_aviso(cliente, cuerpo, webhook_id="msg_1").json()["procesado"] is False
        assert enviar_aviso(cliente, cuerpo, webhook_id="msg_2").json()["procesado"] is False
        assert cliente.get(f"/api/cobros/{cobro['id']}").json()["numero_de_pagos"] == 1


@pytest.mark.asyncio
async def test_el_aviso_y_la_consulta_a_la_vez_registran_un_solo_pago(
    configuracion, pey, reloj
) -> None:
    """Aviso y consulta de la misma transacción, a la vez, dejan un pago (spec 003, RF-007)."""
    almacen = AlmacenQueFalla(reloj=reloj)
    app, _ = _app(configuracion, pey, reloj, almacen)
    pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 0.01, "datePaid": 100}]
    evento = almacen.pausar("registrar_pago")
    async with _asgi(app) as cliente:
        pey.id_qr = "qr-a-la-vez"
        creacion = await cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
        assert creacion.status_code == 201
        cobro = creacion.json()
        consulta = asyncio.create_task(cliente.get(f"/api/cobros/{cobro['id']}"))
        aviso = asyncio.create_task(
            _enviar(cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), "msg_a_la_vez")
        )
        await _con_la_otra_esperando(almacen)
        evento.set()
        _consulta, respuesta = await asyncio.gather(consulta, aviso)
        estado = await cliente.get(f"/api/cobros/{cobro['id']}")
    assert respuesta.status_code == 200
    assert estado.json()["numero_de_pagos"] == 1
    assert [pago_visto["numero"] for pago_visto in estado.json()["pagos"]] == [1]


def test_el_mismo_pago_antes_y_despues_de_un_reinicio_se_registra_una_vez(
    configuracion, pey, reloj
) -> None:
    """La misma transacción, con otro aviso después de reiniciar, no se duplica.

    (spec 003, RF-007).
    """
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-una-vez")
        cuerpo = _cuerpo(cobro["codi_qr_id"], "tx-1")
        assert enviar_aviso(cliente, cuerpo, webhook_id="msg_antes").json()["procesado"] is True
    with cliente_de(reiniciar(app)) as cliente:
        despues = enviar_aviso(cliente, cuerpo, webhook_id="msg_despues")
        assert despues.json()["procesado"] is False
        assert cliente.get(f"/api/cobros/{cobro['id']}").json()["numero_de_pagos"] == 1


def test_tras_un_reinicio_el_siguiente_pago_es_el_numero_3(configuracion, pey, reloj) -> None:
    """Dos pagos guardados siguen siendo 1 y 2, y el siguiente es 3 (spec 003, RF-008)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-numeros")
        enviar_aviso(cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_1")
        enviar_aviso(cliente, _cuerpo(cobro["codi_qr_id"], "tx-2"), webhook_id="msg_2")
    with cliente_de(reiniciar(app)) as cliente:
        tercero = enviar_aviso(cliente, _cuerpo(cobro["codi_qr_id"], "tx-3"), webhook_id="msg_3")
        assert tercero.json()["procesado"] is True
        numeros = [p["numero"] for p in cliente.get(f"/api/cobros/{cobro['id']}").json()["pagos"]]
    assert numeros == [1, 2, 3]


@pytest.mark.asyncio
async def test_dos_pagos_distintos_a_la_vez_quedan_con_numeros_1_y_2(
    configuracion, pey, reloj
) -> None:
    """Dos pagos distintos a la vez quedan numerados 1 y 2 (spec 003, RF-008, DP-8)."""
    almacen = AlmacenQueFalla(reloj=reloj)
    app, _ = _app(configuracion, pey, reloj, almacen)
    evento = almacen.pausar("registrar_pago")
    async with _asgi(app) as cliente:
        pey.id_qr = "qr-paralelo"
        creacion = await cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
        assert creacion.status_code == 201
        cobro = creacion.json()
        uno = asyncio.create_task(_enviar(cliente, _cuerpo(cobro["codi_qr_id"], "tx-a"), "msg_a"))
        dos = asyncio.create_task(_enviar(cliente, _cuerpo(cobro["codi_qr_id"], "tx-b"), "msg_b"))
        await _con_la_otra_esperando(almacen)
        evento.set()
        await asyncio.gather(uno, dos)
        estado = await cliente.get(f"/api/cobros/{cobro['id']}")
    assert {p["numero"] for p in estado.json()["pagos"]} == {1, 2}


def test_los_datos_de_quien_paga_no_se_guardan_ni_se_registran(
    configuracion, pey, reloj, caplog: pytest.LogCaptureFixture
) -> None:
    """Nombre, CLABE, banco, teléfono y clave de rastreo no se guardan ni se registran.

    (spec 003, RF-009).
    """
    caplog.set_level(logging.DEBUG)
    app, _almacen = _app(configuracion, pey, reloj)
    cuerpo = _cuerpo("qr-privado", "tx-privado")
    cuerpo["metadata"] = DATOS_DE_QUIEN_PAGA
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-privado")
        aviso = enviar_aviso(cliente, cuerpo, webhook_id="msg_privado")
        visto = cliente.get(f"/api/cobros/{cobro['id']}")
    assert aviso.status_code == 200
    cargado = asyncio.run(app.state.almacen.cargar_por_id(cobro["id"]))
    texto = "\n".join(
        (
            aviso.text,
            visto.text,
            caplog.text,
            repr(cargado),
            repr(app.state.almacen.datos),
        )
    )
    for valor in DATOS_DE_QUIEN_PAGA.values():
        assert valor not in texto


def test_sin_imagen_de_pey_el_cobro_guardado_vuelve_sin_imagen(configuracion, pey, reloj) -> None:
    """Si pey no mandó imagen, después de reiniciar el cobro vuelve sin ella (spec 003, RF-011)."""
    pey.qr_imagen = None
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-sin-imagen")
        assert cobro["qr_imagen"] is None
    with cliente_de(reiniciar(app)) as cliente:
        visto = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert visto["qr"] == cobro["qr"]
    assert visto["qr_imagen"] is None
