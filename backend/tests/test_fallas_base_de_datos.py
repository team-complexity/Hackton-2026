"""Fallas de la base de datos por la API (spec 003, T053).

Los textos son los del contrato de fallas. El almacén que falla evita pey real
y el reloj falso evita esperar los 15 s del reintento.
"""

import asyncio
import logging

import pytest
from pydantic import SecretStr

from app.eventos import Difusor
from tests.almacen_de_prueba import (
    CLASE_DE_DATOS,
    CLASE_DE_FALLA,
    AlmacenQueFalla,
    armar_app,
    cliente_de,
)
from tests.conftest import PeySimulado, enviar_aviso

MENSAJE_GUARDAR = "No se pudo guardar el cobro. Intenta de nuevo en un momento."
MENSAJE_AVISO = "No se pudo registrar el aviso. Se reintentará."
MENSAJE_CONSULTAR = "No se pudo consultar el cobro. Intenta de nuevo."
MENSAJE_CANCELAR = "No se pudo cancelar el cobro. Intenta de nuevo."
MENSAJE_DATOS = "Aviso con datos no válidos"
MENSAJE_PEY = "No se pudo crear el cobro con pey. Intenta de nuevo."
URL_FALSA = "postgresql://usuario-falso:clave-falsa@base.prueba/x"
FRAGMENTOS_URL = ("usuario-falso", "clave-falsa", "base.prueba")


def _app(configuracion, pey: PeySimulado, reloj, almacen: AlmacenQueFalla | None = None):
    if almacen is None:
        almacen = AlmacenQueFalla(reloj=reloj)
    return armar_app(configuracion, pey, reloj, almacen), almacen


def _crear(cliente, pey: PeySimulado, qr_id: str) -> dict:
    pey.id_qr = qr_id
    pey.estado_crear = 201
    respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


def _cuerpo(qr_id: str, transaccion: str, monto: float = 0.01) -> dict:
    from tests.conftest import pago

    return pago(transaccion) | {"codiQrId": qr_id, "amount": monto}


def _ultimo_id(almacen: AlmacenQueFalla, operacion: str) -> str:
    for llamada in reversed(almacen.llamadas):
        if llamada.operacion == operacion and llamada.args:
            objetivo = llamada.args[0]
            return objetivo if isinstance(objetivo, str) else objetivo.id
    raise AssertionError(f"no hubo llamada a {operacion}")


def _esperas(almacen: AlmacenQueFalla, operacion: str) -> list[float]:
    return [llamada.espera for llamada in almacen.llamadas if llamada.operacion == operacion]


def test_si_la_base_no_responde_al_crear_no_se_llama_a_pey(configuracion, pey, reloj) -> None:
    """Si no se puede guardar el cobro, no se llama a pey (spec 003, RF-012)."""
    app, almacen = _app(configuracion, pey, reloj)
    almacen.fallar("guardar_cobro")
    with cliente_de(app) as cliente:
        respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == MENSAJE_GUARDAR
    assert pey.solicitudes == []


def test_si_pey_falla_el_cobro_guardado_se_borra(configuracion, pey, reloj, caplog) -> None:
    """Si pey no crea el QR se borra el cobro; si el borrado falla, la respuesta no cambia.

    (spec 003, RF-052).
    """
    caplog.set_level(logging.WARNING, logger="pago_facil")
    app, almacen = _app(configuracion, pey, reloj)
    pey.estado_crear = 500
    with cliente_de(app) as cliente:
        respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
        assert respuesta.status_code == 502
        assert respuesta.json()["detail"] == MENSAJE_PEY
        cobro_id = _ultimo_id(almacen, "guardar_cobro")
        almacen.fallar("borrar_cobro")
        otra = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
        assert otra.status_code == 502
        assert otra.json()["detail"] == MENSAJE_PEY
    assert asyncio.run(almacen.cargar_por_id(cobro_id)) is None
    assert any(
        "borrar cobro" in registro.getMessage() and CLASE_DE_FALLA in registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil" and registro.levelno >= logging.WARNING
    )


def test_si_la_base_falla_al_guardar_el_qr_no_se_devuelve_el_qr(configuracion, pey, reloj) -> None:
    """Si el QR no se guarda, la respuesta no lo trae y el cobro sale de la memoria.

    (spec 003, RF-013).
    """
    app, almacen = _app(configuracion, pey, reloj)
    almacen.fallar("guardar_qr")
    with cliente_de(app) as cliente:
        respuesta = cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == MENSAJE_GUARDAR
    assert "qr" not in respuesta.json()
    assert pey.qr_string not in respuesta.text
    cobro_id = _ultimo_id(almacen, "guardar_cobro")
    # T057 conserva la caché en ``_por_id``: si el guardado del QR falla, el cobro se quita.
    assert cobro_id not in app.state.cobros._por_id
    cargado = asyncio.run(almacen.cargar_por_id(cobro_id))
    assert cargado is not None
    assert cargado.qr == ""
    assert cargado.qr_imagen is None


def test_al_crear_cada_escritura_espera_como_maximo_2_segundos(configuracion, pey, reloj) -> None:
    """Guardar el cobro y el QR piden 2 s de espera (spec 003, DP-35)."""
    app, almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        assert _crear(cliente, pey, "qr-espera")["qr_imagen"] == "aW1n"
    assert _esperas(almacen, "guardar_cobro") == [2]
    assert _esperas(almacen, "guardar_qr") == [2]


def test_si_la_base_falla_con_un_aviso_se_responde_503_y_no_se_emite(
    configuracion, pey, reloj, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un aviso que no se puede guardar responde 503, no se emite y queda para reintentar.

    (spec 003, RF-014).
    """
    app, almacen = _app(configuracion, pey, reloj)
    emitidos: list[str] = []
    _espiar(monkeypatch, emitidos)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-aviso-falla")
        almacen.fallar("registrar_pago")
        respuesta = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_falla"
        )
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == MENSAJE_AVISO
    assert "pago" not in emitidos
    assert "msg_falla" in app.state.reintentos.avisos


def test_un_aviso_con_monto_cero_o_negativo_se_rechaza_con_400(configuracion, pey, reloj) -> None:
    """Un amount de 0 o negativo es 400 y no marca el webhook-id (spec 003, DP-34)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-monto")
        for monto, identificador in ((0, "msg_cero"), (-1, "msg_neg")):
            respuesta = enviar_aviso(
                cliente,
                _cuerpo(cobro["codi_qr_id"], "tx-malo", monto),
                webhook_id=identificador,
            )
            assert respuesta.status_code == 400
            assert respuesta.json()["detail"] == MENSAJE_DATOS
        reintento = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-bueno"), webhook_id="msg_cero"
        )
        assert reintento.status_code == 200
        assert reintento.json()["procesado"] is True


def test_un_error_de_datos_responde_400_y_no_entra_a_los_reintentos(
    configuracion, pey, reloj, caplog: pytest.LogCaptureFixture
) -> None:
    """Un error de datos es 400 y no se reintenta (spec 003, DP-34)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    app, almacen = _app(configuracion, pey, reloj)
    almacen.fallar_datos("registrar_pago")
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-datos")
        respuesta = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-datos"), webhook_id="msg_datos"
        )
    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == MENSAJE_DATOS
    assert "msg_datos" not in app.state.reintentos.avisos
    assert any(CLASE_DE_DATOS in registro.getMessage() for registro in caplog.records)


def test_el_aviso_pendiente_se_registra_y_se_emite_cuando_la_base_vuelve(
    configuracion, pey, reloj, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A los 15 s, una vuelta de los reintentos registra el pago y lo emite (spec 003, RF-048)."""
    app, almacen = _app(configuracion, pey, reloj)
    emitidos: list[str] = []
    _espiar(monkeypatch, emitidos)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-reintento")
        almacen.fallar("registrar_pago")
        fallo = enviar_aviso(
            cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_reintento"
        )
        assert fallo.status_code == 503
        assert "pago" not in emitidos
    assert "msg_reintento" in app.state.reintentos.avisos
    almacen.quitar_falla("registrar_pago")
    reloj.avanzar(15)
    asyncio.run(app.state.reintentos.una_vez())
    assert "msg_reintento" not in app.state.reintentos.avisos
    assert "pago" in emitidos
    cargado = asyncio.run(app.state.almacen.cargar_por_id(cobro["id"]))
    assert cargado is not None
    assert len(cargado.pagos) == 1


def test_un_aviso_reenviado_mientras_esta_pendiente_no_se_duplica(
    configuracion, pey, reloj
) -> None:
    """El mismo aviso, mientras sigue pendiente, no entra dos veces a la lista.

    (spec 003, RF-048).
    """
    app, almacen = _app(configuracion, pey, reloj)
    almacen.fallar("registrar_pago")
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-pendiente")
        cuerpo = _cuerpo(cobro["codi_qr_id"], "tx-1")
        assert enviar_aviso(cliente, cuerpo, webhook_id="msg_pendiente").status_code == 503
        enviar_aviso(cliente, cuerpo, webhook_id="msg_pendiente")
    assert list(app.state.reintentos.avisos) == ["msg_pendiente"]


def test_si_la_base_no_responde_al_ver_un_cobro_se_responde_503_y_no_404(
    configuracion, pey, reloj
) -> None:
    """Un cobro fuera de la memoria, si no se puede cargar, es 503 y no 404 (spec 003, RF-015)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-ver")
    fallido = AlmacenQueFalla(datos=app.state.almacen.datos, reloj=reloj)
    fallido.fallar("cargar_por_id")
    app2 = armar_app(configuracion, pey, reloj, fallido)
    with cliente_de(app2) as cliente:
        respuesta = cliente.get(f"/api/cobros/{cobro['id']}")
    assert respuesta.status_code == 503
    assert respuesta.status_code != 404
    assert respuesta.json()["detail"] == MENSAJE_CONSULTAR


def test_si_la_base_no_responde_al_abrir_el_canal_se_responde_503(
    configuracion, pey, reloj
) -> None:
    """Abrir el canal tampoco responde 404 si la base no carga el cobro (spec 003, RF-015)."""
    app, _almacen = _app(configuracion, pey, reloj)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-canal")
    fallido = AlmacenQueFalla(datos=app.state.almacen.datos, reloj=reloj)
    fallido.fallar("cargar_por_id")
    app2 = armar_app(configuracion, pey, reloj, fallido)
    with cliente_de(app2) as cliente:
        respuesta = cliente.get(f"/api/cobros/{cobro['id']}/eventos")
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == MENSAJE_CONSULTAR


def test_si_la_base_falla_al_cancelar_el_cobro_no_cambia(
    configuracion, pey, reloj, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Si cancelar no se guarda, el cobro sigue pendiente y no se avisa (spec 003, RF-004)."""
    app, almacen = _app(configuracion, pey, reloj)
    emitidos: list[str] = []
    _espiar(monkeypatch, emitidos)
    with cliente_de(app) as cliente:
        cobro = _crear(cliente, pey, "qr-no-cancela")
        almacen.fallar("cancelar")
        respuesta = cliente.post(f"/api/cobros/{cobro['id']}/cancelar")
        assert respuesta.status_code == 503
        assert respuesta.json()["detail"] == MENSAJE_CANCELAR
        assert cliente.get(f"/api/cobros/{cobro['id']}").json()["estado"] == "pendiente"
    assert "cancelado" not in emitidos


def test_cada_falla_de_la_base_deja_registro_sin_datos_de_conexion(
    configuracion, pey, reloj, caplog: pytest.LogCaptureFixture
) -> None:
    """Cada falla deja operación, id y clase, y ni el registro ni la respuesta traen la URL.

    (spec 003, RF-016).
    """
    caplog.set_level(logging.DEBUG)
    config = configuracion.model_copy(update={"database_url": SecretStr(URL_FALSA)})
    app, almacen = _app(config, pey, reloj)
    textos: list[str] = []
    with cliente_de(app) as cliente:
        almacen.fallar("guardar_cobro")
        textos.append(_post(cliente).text)
        id_guardar = _ultimo_id(almacen, "guardar_cobro")
        almacen.quitar_falla("guardar_cobro")

        almacen.fallar("guardar_qr")
        textos.append(_post(cliente).text)
        id_qr = _ultimo_id(almacen, "guardar_cobro")
        almacen.quitar_falla("guardar_qr")

        almacen.fallar("borrar_cobro")
        pey.estado_crear = 500
        textos.append(_post(cliente).text)
        id_borrar = _ultimo_id(almacen, "guardar_cobro")
        pey.estado_crear = 201
        almacen.quitar_falla("borrar_cobro")

        cobro = _crear(cliente, pey, "qr-registro")
        almacen.fallar("registrar_pago")
        aviso = enviar_aviso(cliente, _cuerpo(cobro["codi_qr_id"], "tx-1"), webhook_id="msg_r")
        textos.append(aviso.text)
        almacen.quitar_falla("registrar_pago")

        almacen.fallar("guardar_aviso")
        ignorado = _cuerpo(cobro["codi_qr_id"], "tx-2") | {"type": "otro.evento"}
        textos.append(enviar_aviso(cliente, ignorado, webhook_id="msg_ignorado").text)
        almacen.quitar_falla("guardar_aviso")

        almacen.fallar("cancelar")
        textos.append(cliente.post(f"/api/cobros/{cobro['id']}/cancelar").text)
        almacen.quitar_falla("cancelar")

    fallido = AlmacenQueFalla(datos=app.state.almacen.datos, reloj=reloj)
    fallido.fallar("cargar_por_id")
    app2 = armar_app(config, pey, reloj, fallido)
    with cliente_de(app2) as cliente:
        textos.append(cliente.get(f"/api/cobros/{cobro['id']}").text)

    esperados = {
        "guardar cobro": id_guardar,
        "guardar QR": id_qr,
        "borrar cobro": id_borrar,
        "registrar pago": cobro["id"],
        # Un aviso ignorado no trae cobro: no hay id que anotar (contrato §4, «cuando lo hay»).
        "guardar aviso": None,
        "cancelar": cobro["id"],
        "cargar cobro": cobro["id"],
    }
    lineas = [
        registro.getMessage()
        for registro in caplog.records
        if registro.name == "pago_facil" and registro.levelno >= logging.WARNING
    ]
    for frase, cobro_id in esperados.items():
        assert any(
            frase in linea and (cobro_id is None or cobro_id in linea) and CLASE_DE_FALLA in linea
            for linea in lineas
        )
    unido = "\n".join([*textos, caplog.text])
    for fragmento in FRAGMENTOS_URL:
        assert fragmento not in unido


def _post(cliente):
    return cliente.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"})


def _espiar(monkeypatch: pytest.MonkeyPatch, emitidos: list[str]) -> None:
    original = Difusor.publicar

    def publicar(self: Difusor, cobro_id: str, evento: str, datos: dict) -> None:
        emitidos.append(evento)
        original(self, cobro_id, evento, datos)

    monkeypatch.setattr(Difusor, "publicar", publicar)
