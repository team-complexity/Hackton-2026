"""Pruebas de configuración, salud y registros (spec 001, RF-022, RF-034, RF-036, RF-039)."""

import logging
import sys

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Configuracion
from app.main import crear_app
from app.pey import ClientePey
from tests.conftest import (
    BASE_PEY_DE_PRUEBA,
    LLAVE_FALSA,
    SECRETO_FALSO,
    enviar_aviso,
    pago,
)


def test_database_url_se_lee_de_la_configuracion(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL se lee como secreto y no aparece en repr (spec 003, RF-020, RF-021)."""
    valor = "postgresql://usuario-falso:clave-falsa@base.prueba/x"
    monkeypatch.setenv("DATABASE_URL", valor)
    configuracion = Configuracion(_env_file=None)
    assert configuracion.database_url.get_secret_value() == valor
    assert valor not in repr(configuracion)


def test_la_configuracion_tiene_los_valores_por_defecto_del_plan() -> None:
    """Los valores nuevos salen del plan, sin leer backend/.env."""
    configuracion = Configuracion(_env_file=None)
    assert configuracion.proxies_confiables == "127.0.0.1"
    assert configuracion.gracia_segundos == 600
    assert configuracion.canales_por_ip == 10


def test_los_registros_de_pago_facil_se_ven_en_info(cliente) -> None:
    """Al crear la app, pago_facil queda en INFO y escribe en la consola (RF-039)."""
    registro = logging.getLogger("pago_facil")
    assert registro.level == logging.INFO
    consolas = [
        manejador
        for manejador in registro.handlers
        if isinstance(manejador, logging.StreamHandler)
        and not isinstance(manejador, logging.FileHandler)
        and manejador.stream in (sys.stdout, sys.stderr)
    ]
    assert consolas


def _textos_de(respuesta) -> str:
    cabeceras = "\n".join(f"{nombre}: {valor}" for nombre, valor in respuesta.headers.items())
    return f"{respuesta.text}\n{cabeceras}"


def test_salud_dice_que_credenciales_faltan_sin_mostrarlas(configuracion, pey, reloj) -> None:
    """Con llave y sin secreto, /salud solo dice booleanos (RF-036, RF-038)."""
    sin_secreto = configuracion.model_copy(update={"pey_webhook_secret": SecretStr("")})
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, LLAVE_FALSA, http)
    with TestClient(crear_app(sin_secreto, cliente_pey, reloj)) as cliente_http:
        respuesta = cliente_http.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "estado": "ok",
        "llave_pey": True,
        "secreto_aviso_pey": False,
    }
    assert LLAVE_FALSA not in respuesta.text
    assert SECRETO_FALSO not in respuesta.text


def test_la_llave_y_el_secreto_no_aparecen_en_respuestas_ni_registros(cliente, pey, caplog) -> None:
    """Ninguna ruta, ni sus errores, devuelve o registra las credenciales (RF-036, CE-009)."""
    caplog.set_level(logging.DEBUG)
    cobro = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    invalido = cliente.post("/api/cobros", json={"monto": -1})
    visto = cliente.get(f"/api/cobros/{cobro.json()['id']}")
    faltante = cliente.get("/api/cobros/no-existe")
    canal = cliente.get(f"/api/cobros/{cobro.json()['id']}/eventos")
    firma_mala = cliente.post(
        "/webhooks/pey",
        content=b"{}",
        headers={"content-type": "application/json"},
    )
    pey.estado_crear = 401
    pey_rechaza = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
    salud = cliente.get("/salud")
    textos = [
        _textos_de(respuesta)
        for respuesta in (salud, cobro, invalido, visto, faltante, canal, firma_mala, pey_rechaza)
    ]
    textos.append(caplog.text)
    unido = "\n".join(textos)
    assert LLAVE_FALSA not in unido
    assert SECRETO_FALSO not in unido


def test_los_registros_dejan_cobro_error_de_pey_pago_y_aviso_ignorado(cliente, pey, caplog) -> None:
    """Cada cobro, consulta, error, pago y aviso deja una línea (RF-039, QT-4)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    pey.request_id = "req-crear"
    cobro = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).json()
    pey.estado_crear = 401
    pey.request_id = "req-error"
    assert cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).status_code == 502
    pey.estado_crear = 201
    pey.request_id = "req-consulta"
    assert cliente.get(f"/api/cobros/{cobro['id']}").status_code == 200
    assert enviar_aviso(cliente, pago("tx-log")).json()["procesado"] is True
    rechazado = cliente.post(
        "/webhooks/pey",
        content=b"{}",
        headers={"content-type": "application/json"},
    )
    assert rechazado.status_code == 401
    ignorado = enviar_aviso(
        cliente, pago("tx-otra") | {"codiQrId": "qr-no"}, webhook_id="msg_ignorado"
    )
    assert ignorado.json()["procesado"] is False

    lineas = [
        (registro.levelno, registro.getMessage())
        for registro in caplog.records
        if registro.name == "pago_facil"
    ]
    assert any(
        nivel == logging.INFO
        and cobro["id"] in mensaje
        and cobro["codi_qr_id"] in mensaje
        and "req-crear" in mensaje
        for nivel, mensaje in lineas
    )
    assert any(
        nivel == logging.INFO and cobro["id"] in mensaje and "req-consulta" in mensaje
        for nivel, mensaje in lineas
    )
    assert any(nivel >= logging.WARNING and "req-error" in mensaje for nivel, mensaje in lineas)
    assert any(
        nivel == logging.INFO
        and cobro["id"] in mensaje
        and "tx-log" in mensaje
        and "numero=1" in mensaje
        and "fuente=aviso" in mensaje
        for nivel, mensaje in lineas
    )
    assert any("qr-no" in mensaje for _, mensaje in lineas)
    assert any("rechaz" in mensaje.lower() for _, mensaje in lineas)
