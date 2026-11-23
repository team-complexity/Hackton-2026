"""ver_cobro y el respaldo del canal (spec 002, T013, T030)."""

from __future__ import annotations

import json
import time
import urllib.request
from collections.abc import Callable

import pytest
from conftest import abrir, canales, reloj, sonidos, tocar
from playwright.sync_api import Page, Route, expect
from servidor_simulado import ServidorSimulado


def _guardar_cobro(servidor: ServidorSimulado) -> dict[str, object]:
    """Crea un cobro en el simulado sin pasar por el módulo de la web."""
    cuerpo = json.dumps({"monto": 25.5, "concepto": "Tacos"}).encode()
    peticion = urllib.request.Request(
        f"{servidor.origen}/api/cobros",
        data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(peticion) as respuesta:
        datos = json.load(respuesta)
    if not isinstance(datos, dict):
        raise AssertionError("el simulado no devolvió un cobro")
    return datos


def _abortar(ruta: Route) -> None:
    ruta.abort()


@pytest.mark.only_browser("chromium")
def test_ver_cobro_200_devuelve_el_cobro(pagina: Page, servidor: ServidorSimulado) -> None:
    """Un 200 devuelve el cobro guardado (spec 002, RF-030, RF-033)."""
    cobro = _guardar_cobro(servidor)
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async (id) => {
          const { ver_cobro } = await import("/js/servidor.js");
          return ver_cobro(id);
        }""",
        cobro["id"],
    )
    assert resultado["cobro"]["id"] == cobro["id"]
    assert resultado["cobro"]["monto"] == 25.5
    assert resultado["cobro"]["concepto"] == "Tacos"


@pytest.mark.only_browser("chromium")
def test_ver_cobro_404_dice_que_no_existe(pagina: Page, servidor: ServidorSimulado) -> None:
    """Un 404 se informa como cobro que no existe (spec 002, RF-056, RF-057)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { ver_cobro } = await import("/js/servidor.js");
          return ver_cobro("NoExiste123");
        }"""
    )
    assert resultado == {"no_existe": True}


@pytest.mark.only_browser("chromium")
def test_ver_cobro_con_fallo_de_red_dice_sin_conexion(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si la consulta se corta, ver_cobro informa sin conexión (spec 002, RF-030, RF-033)."""
    cobro = _guardar_cobro(servidor)
    abrir(pagina, servidor)
    pagina.route("**/api/cobros/**", _abortar)
    resultado = pagina.evaluate(
        """async (id) => {
          const { ver_cobro } = await import("/js/servidor.js");
          return ver_cobro(id);
        }""",
        cobro["id"],
    )
    assert resultado == {"sin_conexion": True}


_HORA = 1_700_000_000


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def _ultimo_id(servidor: ServidorSimulado) -> str:
    ids = list(servidor.cobros)
    assert ids
    return str(ids[-1])


def _cobrar(pagina: Page, servidor: ServidorSimulado) -> str:
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    return _ultimo_id(servidor)


def _consultas(servidor: ServidorSimulado, id_cobro: str) -> list[str]:
    ruta = f"/api/cobros/{id_cobro}"
    return [
        pedido
        for metodo, pedido, _cuerpo in servidor.peticiones
        if metodo == "GET" and pedido == ruta
    ]


def _esperar_cerrado(pagina: Page, id_cobro: str) -> None:
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes(id) && canal.readyState === 2;
        })""",
        arg=id_cobro,
        timeout=8_000,
    )


def _abortar_consulta(id_cobro: str) -> Callable[[Route], None]:
    """Corta solo la consulta del cobro. El canal de eventos sigue su camino."""

    def manejar(ruta: Route) -> None:
        camino = ruta.request.url.split("?", 1)[0].rstrip("/")
        if camino.endswith(f"/api/cobros/{id_cobro}"):
            ruta.abort()
            return
        ruta.fallback()

    return manejar


def test_con_el_canal_cortado_la_consulta_cada_3_segundos_avisa_el_pago(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Con el canal cortado, la consulta de los 3 s avisa el pago (spec 002, RF-030, CE-003)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_have_text("Reconectando…")
    inicio = time.perf_counter()
    servidor.agregar_pago(id_cobro, 25.5, avisar=False)
    pagina.clock.run_for(3_000)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    assert time.perf_counter() - inicio < 3
    assert sonidos(pagina) == 1


def test_mientras_el_canal_esta_cortado_se_ve_reconectando_sin_quitar_el_qr(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Reconectando no tapa el QR (spec 002, RF-032)."""
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_have_text("Reconectando…")
    expect(pagina.locator('[data-prueba="qr"]')).to_be_visible()


def test_al_volver_el_canal_se_deja_de_consultar_y_se_quita_reconectando(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Al abrirse de nuevo el canal se quita el aviso y la consulta (spec 002, RF-031)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    id_cobro = "CanalCortado"
    servidor.responder_crear(cuerpo=servidor.cobro_de_prueba(id=id_cobro))
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    assert _cobrar(pagina, servidor) == id_cobro
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    ruta_consulta = f"{servidor.origen}/api/cobros/{id_cobro}"
    with pagina.expect_request_finished(lambda peticion: peticion.url == ruta_consulta):
        pagina.clock.run_for(3_000)
    assert _consultas(servidor, id_cobro)
    _esperar_cerrado(pagina, id_cobro)
    servidor.permitir_canal(id_cobro)
    pagina.clock.run_for(15_000)
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes(id) && canal.readyState === 1;
        })""",
        arg=id_cobro,
        timeout=5_000,
    )
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_hidden()
    hechas = len(_consultas(servidor, id_cobro))
    pagina.clock.run_for(9_000)
    assert len(_consultas(servidor, id_cobro)) == hechas
    assert any(canal["estado"] == "OPEN" for canal in canales(pagina))


def test_si_el_servidor_rechaza_el_canal_se_sigue_con_la_consulta(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un canal rechazado se sigue por consulta y se reintenta a los 15 s (spec 002, RF-034)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    id_cobro = "CanalRechazado"
    servidor.responder_crear(cuerpo=servidor.cobro_de_prueba(id=id_cobro))
    servidor.cortar_canal(id_cobro, rechazar_con=429)
    assert _cobrar(pagina, servidor) == id_cobro
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    ruta_consulta = f"{servidor.origen}/api/cobros/{id_cobro}"
    for _ in range(2):
        with pagina.expect_request_finished(lambda peticion: peticion.url == ruta_consulta):
            pagina.clock.run_for(3_000)
    _esperar_cerrado(pagina, id_cobro)
    servidor.permitir_canal(id_cobro)
    with pagina.expect_response(f"{ruta_consulta}/eventos") as reabierto:
        pagina.clock.run_for(9_000)
    assert reabierto.value.status == 200


def test_si_la_consulta_falla_por_red_se_reintenta_en_3_segundos(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si la consulta se corta, Reconectando sigue y se reintenta a los 3 s (spec 002, RF-032)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    pedidas: list[str] = []
    pagina.on("request", lambda peticion: pedidas.append(peticion.url))
    pagina.route("**/api/cobros/**", _abortar_consulta(id_cobro))
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_have_text("Reconectando…")
    pagina.clock.run_for(3_000)
    pagina.clock.run_for(3_000)

    def es_consulta(url: str) -> bool:
        return url.split("?", 1)[0].rstrip("/").endswith(f"/api/cobros/{id_cobro}")

    assert sum(1 for url in pedidas if es_consulta(url)) >= 2
    expect(pagina.locator('[data-prueba="reconectando"]')).to_have_text("Reconectando…")
