"""Pruebas del aviso de pey (spec 001, RF-011 a RF-018, RF-037, RF-039)."""

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest

from tests.conftest import SECRETO_FALSO, enviar_aviso, firmar_aviso, pago


def test_webhook_marca_pagado_y_no_duplica(cliente) -> None:
    cobro = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).json()

    primero = enviar_aviso(cliente, pago())
    assert primero.status_code == 200
    assert primero.json() == {"recibido": True, "procesado": True}

    # Mismo aviso reenviado, y la misma transacción con otro webhook-id.
    assert enviar_aviso(cliente, pago()).json()["procesado"] is False
    assert enviar_aviso(cliente, pago(), webhook_id="msg_2").json()["procesado"] is False

    estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["estado"] == "pagado"
    assert estado["pagado_en"] == 1790724818


def test_webhook_sin_firma_valida_se_rechaza(cliente) -> None:
    cobro = cliente.post("/api/cobros", json={"monto": 0.01}).json()

    otro_secreto = "whsec_" + base64.b64encode(b"otro-secreto-distinto-al-bueno!!").decode()
    assert enviar_aviso(cliente, pago(), secreto=otro_secreto).status_code == 401
    assert cliente.post("/webhooks/pey", json=pago()).status_code == 401
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pendiente"


def test_webhook_de_cobro_desconocido_responde_200(cliente) -> None:
    respuesta = enviar_aviso(cliente, pago() | {"codiQrId": "no-existe"})
    assert respuesta.status_code == 200
    assert respuesta.json()["procesado"] is False


MENSAJE_FIRMA = "Firma no válida"
MENSAJE_AVISO = "Aviso con datos no válidos"


def _crear(cliente) -> dict:
    respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    assert respuesta.status_code == 201
    return respuesta.json()


@pytest.mark.parametrize("modo", ["sin_cabeceras", "otro_secreto", "fuera_de_tiempo"])
def test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada(cliente, modo) -> None:
    """Sin firma válida el cobro no cambia y el webhook-id no queda marcado (RF-011)."""
    cobro = _crear(cliente)
    identificador = "msg_firma"
    if modo == "sin_cabeceras":
        cuerpo = json.dumps(pago())
        respuesta = cliente.post(
            "/webhooks/pey",
            content=cuerpo,
            headers={"content-type": "application/json", "webhook-id": identificador},
        )
    elif modo == "otro_secreto":
        otro = "whsec_" + base64.b64encode(b"otro-secreto-distinto-al-bueno!!").decode()
        respuesta = enviar_aviso(cliente, pago(), webhook_id=identificador, secreto=otro)
    else:
        viejo = datetime.now(UTC) - timedelta(minutes=6)
        respuesta = enviar_aviso(cliente, pago(), webhook_id=identificador, momento=viejo)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == MENSAJE_FIRMA
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pendiente"
    reintento = enviar_aviso(cliente, pago(), webhook_id=identificador)
    assert reintento.status_code == 200
    assert reintento.json()["procesado"] is True


def test_un_aviso_valido_registra_el_pago_y_pasa_el_cobro_a_pagado(cliente) -> None:
    """Un aviso firmado deja el cobro pagado con el monto y la hora de pey (RF-012, RF-018)."""
    cobro = _crear(cliente)
    respuesta = enviar_aviso(cliente, pago())
    assert respuesta.status_code == 200
    assert respuesta.json() == {"recibido": True, "procesado": True}
    estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["estado"] == "pagado"
    assert estado["numero_de_pagos"] == 1
    assert estado["pagos"][0]["numero"] == 1
    assert estado["pagos"][0]["monto_recibido"] == 0.01
    assert estado["pagos"][0]["pagado_en"] == 1790724818


def test_un_aviso_de_otro_tipo_se_ignora(cliente) -> None:
    """Un evento que no es un pago no cambia el cobro (RF-013)."""
    cobro = _crear(cliente)
    respuesta = enviar_aviso(cliente, pago() | {"type": "otro.evento"})
    assert respuesta.status_code == 200
    assert respuesta.json()["procesado"] is False
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["numero_de_pagos"] == 0


def test_un_aviso_de_un_cobro_desconocido_responde_bien_y_se_ignora(cliente, caplog) -> None:
    """Un QR que no conocemos responde 200 y deja registro (RF-012, RF-039)."""
    caplog.set_level("WARNING", logger="pago_facil")
    _crear(cliente)
    respuesta = enviar_aviso(cliente, pago() | {"codiQrId": "qr-desconocido"})
    assert respuesta.status_code == 200
    assert respuesta.json()["procesado"] is False
    assert any("qr-desconocido" in registro.getMessage() for registro in caplog.records)


def test_un_aviso_reenviado_no_registra_el_pago_dos_veces(cliente) -> None:
    """El mismo envío y la misma transacción dejan un solo pago (RF-014)."""
    cobro = _crear(cliente)
    assert enviar_aviso(cliente, pago()).json()["procesado"] is True
    assert enviar_aviso(cliente, pago()).json()["procesado"] is False
    assert enviar_aviso(cliente, pago(), webhook_id="msg_2").json()["procesado"] is False
    estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["numero_de_pagos"] == 1


def test_un_qr_reutilizado_registra_y_numera_cada_pago(cliente) -> None:
    """Dos transacciones distintas al mismo QR quedan como pago 1 y 2 (C-1, RF-015)."""
    cobro = _crear(cliente)
    primero = enviar_aviso(cliente, pago("tx-1"), webhook_id="msg_a")
    segundo = enviar_aviso(cliente, pago("tx-2"), webhook_id="msg_b")
    assert primero.json()["procesado"] is True
    assert segundo.json()["procesado"] is True
    estado = cliente.get(f"/api/cobros/{cobro['id']}").json()
    assert estado["numero_de_pagos"] == 2
    assert estado["total_recibido"] == 0.02
    assert [pago_publico["numero"] for pago_publico in estado["pagos"]] == [1, 2]


def test_un_aviso_despues_de_la_ventana_registra_el_pago(cliente, reloj) -> None:
    """Un aviso posterior a la ventana igual registra el pago (RF-017, QT-5)."""
    cobro = _crear(cliente)
    reloj.avanzar(cobro["fin_ventana"] - reloj.ahora())
    respuesta = enviar_aviso(cliente, pago())
    assert respuesta.json()["procesado"] is True
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pagado"


def test_un_aviso_con_datos_no_validos_responde_400_y_se_acepta_en_el_reintento(cliente) -> None:
    """Un cuerpo que no es JSON responde 400 y el reintento con el mismo id se procesa (R-8)."""
    _crear(cliente)
    cuerpo = "esto no es json"
    cabeceras = firmar_aviso(cuerpo, SECRETO_FALSO, "msg_mal", datetime.now(UTC))
    cabeceras["content-type"] = "application/json"
    respuesta = cliente.post("/webhooks/pey", content=cuerpo, headers=cabeceras)
    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == MENSAJE_AVISO
    reintento = enviar_aviso(cliente, pago(), webhook_id="msg_mal")
    assert reintento.json()["procesado"] is True


@pytest.mark.parametrize("monto", ["NaN", "abc", True, None, float("nan"), float("inf")])
def test_un_aviso_con_monto_ilegible_responde_400_y_no_registra_el_pago(cliente, monto) -> None:
    """Un amount que no es un número finito responde 400 sin marcar el aviso (RF-018, R-8)."""
    cobro = _crear(cliente)
    respuesta = enviar_aviso(cliente, pago() | {"amount": monto}, webhook_id="msg_monto")
    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == MENSAJE_AVISO
    assert cliente.get(f"/api/cobros/{cobro['id']}").json()["pagos"] == []
    reintento = enviar_aviso(cliente, pago(), webhook_id="msg_monto")
    assert reintento.json()["procesado"] is True


def test_un_aviso_que_falla_al_procesarse_se_acepta_en_el_reintento(cliente) -> None:
    """Un amount ilegible responde 400 y no marca el webhook-id (R-8, DP-10)."""
    _crear(cliente)
    datos = pago() | {"amount": "no-es-numero"}
    respuesta = enviar_aviso(cliente, datos, webhook_id="msg_monto")
    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == MENSAJE_AVISO
    reintento = enviar_aviso(cliente, pago(), webhook_id="msg_monto")
    assert reintento.json()["procesado"] is True


def test_sin_secreto_configurado_todo_aviso_se_rechaza(configuracion, pey, reloj) -> None:
    """Sin secreto, cualquier aviso responde 503 (RF-037)."""
    import httpx
    from fastapi.testclient import TestClient
    from pydantic import SecretStr

    from app.main import crear_app
    from app.pey import ClientePey
    from tests.conftest import BASE_PEY_DE_PRUEBA, LLAVE_FALSA

    sin_secreto = configuracion.model_copy(update={"pey_webhook_secret": SecretStr("")})
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, LLAVE_FALSA, http)
    with TestClient(
        crear_app(sin_secreto, cliente_pey, reloj, tareas_en_segundo_plano=False)
    ) as cliente_http:
        cliente_http.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
        respuesta = cliente_http.post("/webhooks/pey", json=pago())
        assert respuesta.status_code == 503
        assert respuesta.json()["detail"] == "El aviso de pey todavía no está configurado"


def test_el_aviso_de_pey_no_hace_peticiones_a_pey(cliente, pey) -> None:
    """Registrar un aviso no consulta a pey (CE-010)."""
    _crear(cliente)
    hechas = len(pey.solicitudes)
    assert enviar_aviso(cliente, pago()).json()["procesado"] is True
    assert len(pey.solicitudes) == hechas
