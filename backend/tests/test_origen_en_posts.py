"""Origen en los POST de crear y cancelar (spec 001, RF-035, C-11)."""

import json
import logging
from datetime import UTC, datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from app.almacen import AlmacenEnMemoria
from tests.conftest import SECRETO_FALSO, firmar_aviso, pago

ORIGEN_AJENO = "https://otro.ejemplo"
MENSAJE = "Origen no permitido"
CUERPO = '{"monto": 1, "concepto": "Tacos"}'


def _post_texto(cliente: TestClient, origen: str) -> httpx.Response:
    """POST /api/cobros como text/plain, la petición simple del navegador (C-11)."""
    return cliente.post(
        "/api/cobros",
        content=CUERPO,
        headers={"Origin": origen, "Content-Type": "text/plain"},
    )


def _cobros(cliente: TestClient) -> dict[str, object]:
    """Cobros guardados en el almacén de la prueba."""
    almacen = cliente.app.state.almacen
    assert isinstance(almacen, AlmacenEnMemoria)
    return almacen.datos.cobros


def test_un_post_de_otro_origen_no_crea_cobros_ni_llama_a_pey(cliente, pey) -> None:
    """Un text/plain de otro origen no crea el cobro ni llama a pey (RF-035, C-11)."""
    respuesta = _post_texto(cliente, ORIGEN_AJENO)
    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": MENSAJE}
    assert pey.solicitudes == []
    assert _cobros(cliente) == {}


def test_un_post_de_otro_origen_no_cancela_un_cobro(cliente) -> None:
    """Cancelar desde otro origen responde 403 y el cobro sigue pendiente (RF-035, C-11)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    respuesta = cliente.post(
        f"/api/cobros/{cobro['id']}/cancelar",
        headers={"Origin": ORIGEN_AJENO},
    )
    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": MENSAJE}
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pendiente"


def test_un_post_con_el_origen_configurado_sigue_creando(cliente, configuracion) -> None:
    """El Origin de WEB_ORIGIN crea el cobro (RF-035, C-11)."""
    origen = configuracion.origenes_web[0]
    respuesta = cliente.post(
        "/api/cobros",
        json={"monto": 1, "concepto": "Tacos"},
        headers={"Origin": origen},
    )
    assert respuesta.status_code == 201


def test_un_post_del_mismo_origen_sigue_creando(cliente, configuracion) -> None:
    """El host de la petición crea el cobro aunque no esté en WEB_ORIGIN (RF-035, C-11)."""
    origen = "http://testserver"
    assert origen not in configuracion.origenes_web
    respuesta = cliente.post(
        "/api/cobros",
        json={"monto": 1, "concepto": "Tacos"},
        headers={"Origin": origen},
    )
    assert respuesta.status_code == 201


def test_un_post_sin_origen_sigue_funcionando(cliente) -> None:
    """Sin Origin, crear y cancelar siguen como hasta ahora (RF-035, C-11)."""
    creado = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
    assert creado.status_code == 201
    cancelado = cliente.post(f"/api/cobros/{creado.json()['id']}/cancelar")
    assert cancelado.status_code == 200


def test_el_origen_null_se_rechaza(cliente, pey) -> None:
    """Origin null (iframe con sandbox o file) no crea el cobro (RF-035, C-11)."""
    respuesta = cliente.post(
        "/api/cobros",
        content=CUERPO,
        headers={"Origin": "null", "Content-Type": "text/plain"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": MENSAJE}
    assert pey.solicitudes == []
    assert _cobros(cliente) == {}


def test_un_rechazo_por_origen_no_cuenta_para_el_limite_por_ip(cliente) -> None:
    """Varios 403 no gastan el límite: un POST válido después sigue pasando (RF-034, RF-035)."""
    for _ in range(6):
        assert _post_texto(cliente, ORIGEN_AJENO).status_code == 403
    valido = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
    assert valido.status_code == 201


def test_el_aviso_de_pey_no_depende_del_origen(cliente) -> None:
    """POST /webhooks/pey con Origin ajeno y firma válida se procesa (RF-011, C-11)."""
    cobro = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).json()
    cuerpo = json.dumps(pago())
    cabeceras = firmar_aviso(cuerpo, SECRETO_FALSO, "msg_origen", datetime.now(UTC))
    cabeceras["content-type"] = "application/json"
    cabeceras["origin"] = ORIGEN_AJENO
    respuesta = cliente.post("/webhooks/pey", content=cuerpo, headers=cabeceras)
    assert respuesta.status_code == 200
    assert respuesta.json() == {"recibido": True, "procesado": True}
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pagado"


def test_el_registro_no_copia_el_origen_ajeno(cliente, caplog: pytest.LogCaptureFixture) -> None:
    """El WARNING es una frase fija y no incluye el Origin (RF-035, RF-036, C-11)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    origen = "https://origen-ajeno.ejemplo"
    respuesta = _post_texto(cliente, origen)
    assert respuesta.status_code == 403
    avisos = [
        registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil" and registro.levelno == logging.WARNING
    ]
    assert avisos == ["Petición rechazada por origen"]
    assert origen not in caplog.text
