"""Pruebas de cancelar un cobro (spec 001, RF-017, RF-023, RF-024, RF-039)."""

import logging

import pytest

from tests.conftest import enviar_aviso, pago

MENSAJE_NO_SE_PUEDE = "Solo se puede cancelar un cobro que todavía no se paga ni vence"
MENSAJE_NO_EXISTE = "Ese cobro no existe"


def _crear(cliente) -> dict:
    respuesta = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
    assert respuesta.status_code == 201
    return respuesta.json()


def test_cancelar_un_cobro_pendiente(cliente, caplog) -> None:
    """Un cobro pendiente queda cancelado y el registro lleva su id (RF-023, RF-039)."""
    caplog.set_level(logging.INFO, logger="pago_facil")
    cobro = _crear(cliente)
    respuesta = cliente.post(f"/api/cobros/{cobro['id']}/cancelar")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "cancelado"
    assert any(
        cobro["id"] in registro.getMessage() and "cancel" in registro.getMessage().lower()
        for registro in caplog.records
        if registro.name == "pago_facil"
    )


@pytest.mark.parametrize("caso", ["pagado", "vencido", "cancelado"])
def test_no_se_puede_cancelar_un_cobro_pagado_o_vencido(cliente, reloj, caso) -> None:
    """Pagado, vencido o ya cancelado responden 409 (RF-024)."""
    cobro = _crear(cliente)
    if caso == "pagado":
        assert enviar_aviso(cliente, pago()).json()["procesado"] is True
    elif caso == "vencido":
        reloj.avanzar(cobro["expira_en"] - reloj.ahora())
    else:
        assert cliente.post(f"/api/cobros/{cobro['id']}/cancelar").status_code == 200
    respuesta = cliente.post(f"/api/cobros/{cobro['id']}/cancelar")
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == MENSAJE_NO_SE_PUEDE


def test_un_cobro_cancelado_que_se_paga_pasa_a_pagado(cliente) -> None:
    """Un aviso después de cancelar registra el pago y el cobro queda pagado (RF-017)."""
    cobro = _crear(cliente)
    assert cliente.post(f"/api/cobros/{cobro['id']}/cancelar").status_code == 200
    respuesta = enviar_aviso(cliente, pago())
    assert respuesta.status_code == 200
    assert respuesta.json()["procesado"] is True
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pagado"


def test_cancelar_un_cobro_que_no_existe_da_404(cliente) -> None:
    """Un id desconocido responde que ese cobro no existe (RF-023)."""
    respuesta = cliente.post("/api/cobros/nada/cancelar")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == MENSAJE_NO_EXISTE


def test_cancelar_devuelve_la_hora_del_servidor(cliente, reloj) -> None:
    """La respuesta de cancelar trae hora_servidor (RF-008, C-2)."""
    cobro = _crear(cliente)
    reloj.avanzar(12)
    cancelado = cliente.post(f"/api/cobros/{cobro['id']}/cancelar").json()
    assert cancelado["hora_servidor"] == cobro["creado_en"] + 12
