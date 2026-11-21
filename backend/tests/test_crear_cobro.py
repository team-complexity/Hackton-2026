"""Pruebas de crear un cobro (spec 001, RF-001 a RF-010, RF-042)."""

import json
import logging
import re

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import crear_app
from app.pey import ClientePey
from tests.conftest import BASE_PEY_DE_PRUEBA, CODI_QR_ID, LLAVE_FALSA, enviar_aviso, pago

MENSAJE_MONTO = "Escribe un monto mayor a $0 con máximo 2 decimales"
MENSAJE_MAXIMO = "El monto máximo de la demo es $100"
MENSAJE_CONCEPTO_LARGO = "El concepto puede tener máximo 40 letras"
MENSAJE_CONCEPTO_RARO = "El concepto tiene caracteres no válidos"
MENSAJE_SIN_LLAVE = "El servidor no tiene configurada la llave de pey"
MENSAJE_LLAVE_RECHAZADA = "pey rechazó la llave del servidor"
MENSAJE_MANTENIMIENTO = "pey está en mantenimiento. Intenta de nuevo en unos minutos."
MENSAJE_REINTENTAR = "No se pudo crear el cobro con pey. Intenta de nuevo."
CAMPOS_COBRO = {
    "id",
    "codi_qr_id",
    "monto",
    "monto_libre",
    "concepto",
    "estado",
    "qr",
    "qr_imagen",
    "creado_en",
    "expira_en",
    "fin_ventana",
    "numero_de_pagos",
    "total_recibido",
    "pagado_en",
    "pagos",
    "hora_servidor",
}


def test_crear_cobro_llama_a_pey_y_devuelve_el_qr(cliente, pey) -> None:
    respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "  Tacos  "})
    assert respuesta.status_code == 201
    cobro = respuesta.json()
    assert cobro["codi_qr_id"] == CODI_QR_ID
    assert cobro["qr"] == '{"IDC":"x"}'
    assert cobro["qr_imagen"] == "aW1n"
    assert cobro["estado"] == "pendiente"
    assert cobro["concepto"] == "Tacos"

    enviada = pey.solicitudes[0]
    assert enviada.headers["authorization"] == f"Bearer {LLAVE_FALSA}"
    cuerpo = json.loads(enviada.content)
    assert cuerpo["amount"] == 0.01
    assert cuerpo["expiration"] >= 360
    assert cuerpo["numRef"].isdigit() and len(cuerpo["numRef"]) <= 7
    assert cuerpo["metadata"] == {"cobroId": cobro["id"]}


@pytest.mark.parametrize("monto", [-5, 100.01, 1.234, "abc"])
def test_montos_invalidos_se_rechazan_sin_llamar_a_pey(cliente, pey, monto) -> None:
    respuesta = cliente.post("/api/cobros", json={"monto": monto, "concepto": "x"})
    assert respuesta.status_code == 422
    assert pey.solicitudes == []


def test_los_errores_de_validacion_salen_en_espanol(cliente) -> None:
    """Un monto ilegible responde 422 con un texto en español, no la lista de pydantic (RF-004)."""
    respuesta = cliente.post("/api/cobros", json={"monto": "abc"})
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == MENSAJE_MONTO


def test_error_de_pey_da_mensaje_claro_y_no_guarda_el_cobro(cliente, pey) -> None:
    pey.estado_crear = 503
    respuesta = cliente.post("/api/cobros", json={"monto": 1})
    assert respuesta.status_code == 503
    assert "mantenimiento" in respuesta.json()["detail"]


def test_crear_cobro_pide_el_qr_a_pey_con_vigencia_de_10_minutos_y_el_id_del_cobro(
    cliente, pey
) -> None:
    """La petición a pey lleva vigencia de 10 minutos y el id del cobro (RF-001, RF-006, RF-007)."""
    respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    assert respuesta.status_code == 201
    cobro = respuesta.json()
    assert "metadata" not in cobro
    enviada = pey.solicitudes[0]
    cuerpo = json.loads(enviada.content)
    assert cuerpo["amount"] == 0.01
    assert cuerpo["concept"] == "Tacos"
    assert cuerpo["expiration"] == 600
    assert re.fullmatch(r"[0-9]{1,7}", cuerpo["numRef"])
    assert cuerpo["generateImage"] is True
    assert cuerpo["metadata"] == {"cobroId": cobro["id"]}


def test_el_cobro_devuelve_todos_sus_campos(cliente) -> None:
    """La respuesta trae los 16 campos del objeto cobro (RF-008, RF-022, C-2)."""
    cobro = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).json()
    assert set(cobro) == CAMPOS_COBRO
    assert re.fullmatch(r"[A-Za-z0-9_-]{12}", cobro["id"])
    assert cobro["estado"] == "pendiente"
    assert cobro["expira_en"] == cobro["creado_en"] + 600
    assert cobro["fin_ventana"] == cobro["expira_en"] + 600
    assert cobro["numero_de_pagos"] == 0
    assert cobro["total_recibido"] == 0
    assert cobro["pagado_en"] is None
    assert cobro["pagos"] == []


@pytest.mark.parametrize(
    ("cuerpo", "mensaje"),
    [
        ({"monto": -5, "concepto": "x"}, MENSAJE_MONTO),
        ({"monto": 0.001, "concepto": "x"}, MENSAJE_MONTO),
        ({"monto": "abc", "concepto": "x"}, MENSAJE_MONTO),
        ({"monto": 100.01, "concepto": "x"}, MENSAJE_MAXIMO),
    ],
)
def test_montos_no_validos_se_rechazan_sin_llamar_a_pey(cliente, pey, cuerpo, mensaje) -> None:
    """Negativo, decimales de más, texto y el tope siguen en 422 (RF-002, RF-004)."""
    respuesta = cliente.post("/api/cobros", json=cuerpo)
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == mensaje
    assert pey.solicitudes == []


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"concepto": "Tacos"},
        {"monto": None, "concepto": "Tacos"},
        {"monto": 0, "concepto": "Tacos"},
    ],
    ids=["ausente", "null", "cero"],
)
def test_monto_vacio_o_cero_crea_un_cobro_de_monto_libre(cliente, pey, cuerpo) -> None:
    """Sin monto, null o 0 el QR es de monto libre y el pago no es distinto (RF-003, RF-019)."""
    respuesta = cliente.post("/api/cobros", json=cuerpo)
    assert respuesta.status_code == 201
    cobro = respuesta.json()
    assert cobro["monto"] is None
    assert cobro["monto_libre"] is True
    enviada = json.loads(pey.solicitudes[-1].content)
    assert enviada["amount"] == 0
    aviso = enviar_aviso(cliente, pago("tx-libre") | {"amount": 7.5}, webhook_id="msg_libre")
    assert aviso.status_code == 200
    assert aviso.json()["procesado"] is True
    estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["monto_libre"] is True
    assert estado["pagos"][0]["monto_recibido"] == 7.5
    assert estado["pagos"][0]["monto_distinto"] is False


def test_el_concepto_se_limpia_y_usa_cobro_por_defecto(cliente, pey) -> None:
    """Se quitan espacios sobrantes y, si falta, el concepto es Cobro (RF-005, RF-042)."""
    con_espacios = cliente.post("/api/cobros", json={"monto": 1, "concepto": "  Tacos  "})
    assert con_espacios.status_code == 201
    assert con_espacios.json()["concepto"] == "Tacos"
    for cuerpo in ({"monto": 1}, {"monto": 1, "concepto": ""}, {"monto": 1, "concepto": "   "}):
        respuesta = cliente.post("/api/cobros", json=cuerpo)
        assert respuesta.status_code == 201
        assert respuesta.json()["concepto"] == "Cobro"
    largo = cliente.post("/api/cobros", json={"monto": 1, "concepto": "a" * 41})
    assert largo.status_code == 422
    assert largo.json()["detail"] == MENSAJE_CONCEPTO_LARGO
    assert all(json.loads(s.content).get("concept") != "a" * 41 for s in pey.solicitudes)


@pytest.mark.parametrize("concepto", ["Tacos\n", "Ta\x00cos"])
def test_un_concepto_con_caracteres_no_imprimibles_se_rechaza(cliente, pey, concepto) -> None:
    """Un concepto con caracteres no imprimibles no llega a pey (RF-042)."""
    respuesta = cliente.post("/api/cobros", json={"monto": 1, "concepto": concepto})
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == MENSAJE_CONCEPTO_RARO
    assert pey.solicitudes == []


def test_crear_un_cobro_deja_una_linea_en_el_registro(cliente, pey, caplog) -> None:
    """Cada QR creado deja el id, el codi_qr_id y el requestId si pey lo mandó (RF-039)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    pey.request_id = "req-crear-1"
    cobro = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).json()
    assert any(
        cobro["id"] in registro.getMessage()
        and cobro["codi_qr_id"] in registro.getMessage()
        and "req-crear-1" in registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil" and registro.levelno == logging.INFO
    )


def _cliente_sin_llave(configuracion, pey, reloj) -> TestClient:
    sin_llave = configuracion.model_copy(update={"pey_api_key": ""})
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, "", http)
    return TestClient(crear_app(sin_llave, cliente_pey, reloj))


def _id_intentado(cliente_http, pey, caplog) -> str:
    if pey.solicitudes:
        return json.loads(pey.solicitudes[0].content)["metadata"]["cobroId"]
    for registro in caplog.records:
        hallado = re.search(r"cobro ([A-Za-z0-9_-]{12})", registro.getMessage())
        if hallado:
            return hallado.group(1)
    consulta = cliente_http.get("/api/cobros/no-se-guardo")
    assert consulta.status_code == 404
    raise AssertionError("el cobro intentado no quedó identificable")


@pytest.mark.parametrize(
    ("caso", "estado_http", "mensaje"),
    [
        ("sin_llave", 503, MENSAJE_SIN_LLAVE),
        (401, 502, MENSAJE_LLAVE_RECHAZADA),
        (403, 502, MENSAJE_LLAVE_RECHAZADA),
        (503, 503, MENSAJE_MANTENIMIENTO),
        (500, 502, MENSAJE_REINTENTAR),
        ("sin_conexion", 502, MENSAJE_REINTENTAR),
    ],
)
def test_si_pey_falla_el_cobro_no_se_guarda_y_el_mensaje_dice_la_causa(
    cliente, pey, configuracion, reloj, caplog, caso, estado_http, mensaje
) -> None:
    """Si pey falla, el cobro no queda guardado y el mensaje dice la causa (RF-009, RF-010)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    if caso == "sin_llave":
        with _cliente_sin_llave(configuracion, pey, reloj) as cliente_http:
            respuesta = cliente_http.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
            assert respuesta.status_code == estado_http
            assert respuesta.json()["detail"] == mensaje
            cobro_id = _id_intentado(cliente_http, pey, caplog)
            assert cliente_http.get(f"/api/cobros/{cobro_id}").status_code == 404
        return
    if caso == "sin_conexion":
        pey.sin_conexion = True
    else:
        pey.estado_crear = caso
    respuesta = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
    assert respuesta.status_code == estado_http
    assert respuesta.json()["detail"] == mensaje
    cobro_id = _id_intentado(cliente, pey, caplog)
    assert cliente.get(f"/api/cobros/{cobro_id}").status_code == 404


def test_si_pey_tarda_mas_de_10_segundos_al_crear_responde_intenta_de_nuevo(cliente, pey) -> None:
    """Un tiempo agotado al crear responde que se intente de nuevo (QP-1, RF-010)."""
    pey.tiempo_agotado = True
    respuesta = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
    assert respuesta.status_code == 502
    assert respuesta.json()["detail"] == MENSAJE_REINTENTAR
    assert pey.solicitudes[0].extensions["timeout"]["read"] == 10.0


def test_crear_cobro_descuenta_lo_que_tardo_pey_en_la_hora_del_servidor(
    cliente, pey, reloj
) -> None:
    """Si pey tarda 9 s, creado_en queda antes y hora_servidor después (RF-008, C-2)."""
    inicio = int(reloj.ahora())
    pey.al_crear = lambda: reloj.avanzar(9)
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    assert cobro["creado_en"] == inicio
    assert cobro["hora_servidor"] == inicio + 9


def test_ver_cobro_trae_la_hora_actual_del_servidor(cliente, reloj) -> None:
    """Al ver un cobro, hora_servidor es la hora de la consulta (RF-008, C-2)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    reloj.avanzar(30)
    visto = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert visto["hora_servidor"] == cobro["creado_en"] + 30
