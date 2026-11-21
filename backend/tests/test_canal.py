"""Pruebas del canal de avisos (spec 001, RF-028 a RF-033, RF-040, RF-043)."""

import json
import time
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient

from app.cobros import RepositorioCobros
from app.eventos import Difusor
from app.pey import ClientePey
from app.reloj import RelojFalso
from tests.conftest import BASE_PEY_DE_PRUEBA, LLAVE_FALSA, PeySimulado, pago


def _flujo():
    from app.canal import flujo_de_avisos

    return flujo_de_avisos


def _consulta():
    from app.respaldo import ConsultaDeRespaldo

    return ConsultaDeRespaldo


def _mundo(gracia: int = 0, inicio: float = 1_794_700_000):
    reloj = RelojFalso(inicio=inicio)
    repositorio = RepositorioCobros(reloj, gracia_segundos=gracia)
    difusor = Difusor()
    simulado = PeySimulado()
    http = httpx.AsyncClient(transport=httpx.MockTransport(simulado))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, "llave", http)
    consulta = _consulta()(cliente_pey, repositorio, difusor, reloj)
    cobro = repositorio.nuevo(Decimal("10"), "Tacos", 600, ahora=reloj.ahora())
    repositorio.vincular_qr(cobro, "ab12cd34ef", "qr", None)
    return reloj, repositorio, difusor, simulado, cliente_pey, consulta, cobro


def _datos(trozo: str) -> dict:
    for linea in trozo.splitlines():
        if linea.startswith("data:"):
            return json.loads(linea.split(":", 1)[1].strip())
    raise AssertionError(trozo)


async def _hasta(gen, texto: str, maximo: int = 400) -> list[str]:
    vistos: list[str] = []
    for _ in range(maximo):
        vistos.append(await anext(gen))
        if texto in vistos[-1]:
            return vistos
    raise AssertionError(vistos[-3:])


@pytest.mark.asyncio
async def test_el_canal_emite_el_estado_al_abrirse() -> None:
    """Al abrir sale retry y el estado, con los pagos que el cobro ya tiene (RF-031)."""
    _reloj, repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo()
    try:
        repo.registrar_pago(cobro, "tx-1", Decimal("4"), None, 100, "aviso")
        repo.registrar_pago(cobro, "tx-2", Decimal("6"), None, 200, "aviso")
        gen = _flujo()(cobro, difusor, consulta, _reloj)
        assert (await anext(gen)).startswith("retry: 3000")
        estado = _datos(await anext(gen))
        assert estado["numero_de_pagos"] == 2
        assert estado["total_recibido"] == 10
        assert estado["estado"] == "pagado"
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_el_canal_avisa_el_pago_en_cuanto_se_registra() -> None:
    """Un pago publicado llega en el siguiente evento, sin mover el reloj (CE-003)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo()
    marca = reloj.ahora()
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        consulta.registrar_y_avisar(cobro, "tx-1", Decimal("10"), None, 100, "aviso")
        aviso = _datos(await anext(gen))
        assert aviso["pago"]["numero"] == 1
        assert aviso["cobro"]["estado"] == "pagado"
        assert reloj.ahora() == marca
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_el_canal_avisa_cancelado_en_menos_de_15_segundos() -> None:
    """Al publicar la cancelación, el canal emite el cobro antes de 15 s (RF-030)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo()
    inicio = reloj.ahora()
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        cobro.cancelado_en = int(reloj.ahora())
        difusor.publicar(cobro.id, "cancelado", cobro.publico())
        trozo = await anext(gen)
        assert "event: cancelado" in trozo
        aviso = _datos(trozo)
        assert aviso["id"] == cobro.id
        assert aviso["estado"] == "cancelado"
        assert reloj.ahora() - inicio < 15
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_el_canal_avisa_cada_pago_con_su_numero_y_el_total() -> None:
    """Dos pagos al mismo QR salen con su número y el total acumulado (C-1, CE-006)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo()
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        consulta.registrar_y_avisar(cobro, "tx-1", Decimal("4"), None, 100, "aviso")
        primero = _datos(await anext(gen))
        consulta.registrar_y_avisar(cobro, "tx-2", Decimal("6"), None, 200, "aviso")
        segundo = _datos(await anext(gen))
        assert primero["pago"]["numero"] == 1
        assert primero["cobro"]["total_recibido"] == 4
        assert segundo["pago"]["numero"] == 2
        assert segundo["cobro"]["total_recibido"] == 10
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_el_canal_avisa_vencido_en_menos_de_15_segundos() -> None:
    """Con gracia, vencido sale antes de 15 s después de expira_en (RF-030)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo(gracia=600)
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        await _hasta(gen, "event: vencido")
        assert cobro.expira_en <= reloj.ahora() < cobro.expira_en + 15
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_con_gracia_0_el_canal_emite_vencido_y_luego_fin() -> None:
    """Si vence y cierra a la vez, los dos últimos eventos son vencido y fin (QT-6)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo()
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        vistos: list[str] = []
        for _ in range(400):
            try:
                vistos.append(await anext(gen))
            except StopAsyncIteration:
                break
        assert "event: vencido" in vistos[-2]
        assert "event: fin" in vistos[-1]
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_el_canal_emite_fin_y_se_cierra_al_terminar_la_ventana() -> None:
    """Al llegar a fin_ventana el canal emite fin y el generador termina (RF-032)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo(gracia=600)
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        ultimo = ""
        for _ in range(800):
            try:
                ultimo = await anext(gen)
            except StopAsyncIteration:
                break
        assert "event: fin" in ultimo
        assert reloj.ahora() >= cobro.fin_ventana
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_el_canal_manda_senal_de_vida_cada_15_segundos() -> None:
    """Sin otros eventos, a los 15 s sale la señal de vida (RF-033)."""
    reloj, _repo, difusor, _pey, cliente_pey, consulta, cobro = _mundo(gracia=600)
    inicio = reloj.ahora()
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        await _hasta(gen, ": sigo conectado")
        assert reloj.ahora() - inicio <= 15
    finally:
        await cliente_pey.cerrar()


def test_abrir_el_canal_despues_de_la_ventana_emite_estado_y_fin(cliente, reloj) -> None:
    """Pasada la ventana, el canal emite estado y fin, y cierra (RF-043)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    reloj.avanzar(cobro["fin_ventana"] - reloj.ahora())
    respuesta = cliente.get(f"/api/cobros/{cobro['id']}/eventos")
    assert respuesta.status_code == 200
    assert respuesta.headers["cache-control"] == "no-cache"
    assert respuesta.headers["x-accel-buffering"] == "no"
    assert "event: estado" in respuesta.text
    assert "event: fin" in respuesta.text
    assert respuesta.text.index("event: estado") < respuesta.text.index("event: fin")
    faltante = cliente.get("/api/cobros/nada/eventos")
    assert faltante.status_code == 404
    assert faltante.json()["detail"] == "Ese cobro no existe"


@pytest.mark.asyncio
async def test_con_el_canal_abierto_el_servidor_pregunta_a_pey_cada_5_segundos() -> None:
    """Sin aviso, el pago aparece por la consulta, y dos canales comparten el límite (CE-008)."""
    reloj, _repo, difusor, pey, cliente_pey, consulta, cobro = _mundo(gracia=600)
    try:
        primero = _flujo()(cobro, difusor, consulta, reloj)
        segundo = _flujo()(cobro, difusor, consulta, reloj)
        await anext(primero)
        await anext(primero)
        await anext(segundo)
        await anext(segundo)
        marca = reloj.ahora()
        pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 10, "datePaid": 100}]
        aviso = _datos(await anext(primero))
        assert aviso["pago"]["numero"] == 1
        assert reloj.ahora() <= marca + 5
        otro = _datos(await anext(segundo))
        assert otro["pago"]["numero"] == 1
        assert len([s for s in pey.solicitudes if s.method == "GET"]) == 1
    finally:
        await cliente_pey.cerrar()


def test_sin_secreto_el_canal_avisa_el_pago_por_la_consulta(configuracion, pey, reloj) -> None:
    """Sin secreto de aviso, el canal igual avisa el pago que encuentra en pey (QT-5)."""
    from pydantic import SecretStr

    from app.main import crear_app

    sin_secreto = configuracion.model_copy(update={"pey_webhook_secret": SecretStr("")})
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, LLAVE_FALSA, http)
    with TestClient(crear_app(sin_secreto, cliente_pey, reloj)) as cliente_http:
        cobro = cliente_http.post("/api/cobros", json={"monto": 0.01, "concepto": "Tacos"}).json()
        rechazo = cliente_http.post("/webhooks/pey", json=pago())
        assert rechazo.status_code == 503
        pey.transacciones = [{"id": "tx-1", "status": "PAID", "amount": 0.01, "datePaid": 100}]
        respuesta = cliente_http.get(f"/api/cobros/{cobro['id']}/eventos")
        assert "event: pago" in respuesta.text


@pytest.mark.asyncio
async def test_un_pago_5_minutos_despues_de_vencer_se_avisa_por_el_canal() -> None:
    """Con la gracia por defecto, a los 5 minutos de vencer el canal sigue y avisa (CE-007)."""
    from app.config import Configuracion

    gracia = Configuracion(_env_file=None).gracia_segundos
    reloj, _repo, difusor, pey, cliente_pey, consulta, cobro = _mundo(gracia=gracia)
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        await _hasta(gen, "event: vencido")
        assert reloj.ahora() < cobro.fin_ventana
        while reloj.ahora() < cobro.expira_en + 300:
            await anext(gen)
            assert reloj.ahora() < cobro.fin_ventana
        pey.transacciones = [
            {"id": "tx-tarde", "status": "PAID", "amount": 10, "datePaid": int(reloj.ahora())}
        ]
        aviso = _datos((await _hasta(gen, "event: pago"))[-1])
        assert aviso["pago"]["numero"] == 1
        assert aviso["cobro"]["estado"] == "pagado"
        assert cobro.expira_en + 300 <= reloj.ahora() <= cobro.expira_en + 305
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_un_cobro_cancelado_sigue_escuchando_y_avisa_el_pago() -> None:
    """Tras cancelar, el canal sigue abierto, no emite vencido y avisa el pago (RF-017, RF-022)."""
    reloj, repositorio, difusor, pey, cliente_pey, consulta, cobro = _mundo(gracia=600)
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        repositorio.cancelar(cobro, reloj.ahora())
        difusor.publicar(cobro.id, "cancelado", cobro.publico())
        assert "event: cancelado" in await anext(gen)
        vistos = []
        while reloj.ahora() < cobro.expira_en + 300:
            vistos.append(await anext(gen))
        assert not any("event: vencido" in trozo for trozo in vistos)
        assert not any("event: fin" in trozo for trozo in vistos)
        pey.transacciones = [
            {"id": "tx-cancelado", "status": "PAID", "amount": 1, "datePaid": int(reloj.ahora())}
        ]
        aviso = _datos((await _hasta(gen, "event: pago"))[-1])
        assert aviso["pago"]["numero"] == 1
        assert aviso["cobro"]["estado"] == "pagado"
        assert reloj.ahora() < cobro.fin_ventana
    finally:
        await cliente_pey.cerrar()


@pytest.mark.asyncio
async def test_una_consulta_lenta_no_deja_mudo_el_canal() -> None:
    """Aunque la consulta se agote, la señal de vida y vencido salen a tiempo (QP-1)."""
    reloj, _repo, difusor, pey, cliente_pey, consulta, cobro = _mundo(gracia=600)
    pey.tiempo_agotado = True
    inicio = reloj.ahora()
    arranque = time.perf_counter()
    try:
        gen = _flujo()(cobro, difusor, consulta, reloj)
        await anext(gen)
        await anext(gen)
        await _hasta(gen, ": sigo conectado")
        assert reloj.ahora() - inicio <= 15
        await _hasta(gen, "event: vencido")
        assert reloj.ahora() < cobro.expira_en + 15
        assert time.perf_counter() - arranque < 2
    finally:
        await cliente_pey.cerrar()


def test_los_eventos_del_canal_traen_la_hora_del_servidor(cliente, reloj) -> None:
    """El estado y el fin traen la hora del servidor al emitirse (RF-008, C-2)."""
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    reloj.avanzar(cobro["fin_ventana"] + 5 - reloj.ahora())
    texto = cliente.get(f"/api/cobros/{cobro['id']}/eventos").text
    eventos = [trozo for trozo in texto.split("\n\n") if trozo.startswith("event:")]
    assert [trozo.splitlines()[0] for trozo in eventos] == ["event: estado", "event: fin"]
    for trozo in eventos:
        assert _datos(trozo)["hora_servidor"] == cobro["fin_ventana"] + 5
