"""Arranque de la web: la marca y la política de seguridad (spec 002, RF-060, RF-077)."""

import http.client

from conftest import abrir, reloj, tocar
from playwright.sync_api import ConsoleMessage, Page, expect
from servidor_simulado import ServidorSimulado


def test_la_pagina_abre_y_muestra_pago_facil(pagina: Page, servidor: ServidorSimulado) -> None:
    """La marca se lee PAGO FÁCIL al abrir la página (spec 002, RF-060)."""
    abrir(pagina, servidor)
    expect(pagina.locator('[data-prueba="marca"]')).to_have_text("PAGO FÁCIL")


def test_la_pagina_carga_sin_errores_ni_bloqueos_de_la_politica(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """La carga no escribe errores ni dispara securitypolicyviolation (spec 002, RF-077)."""
    errores: list[str] = []

    def anotar(mensaje: ConsoleMessage) -> None:
        if mensaje.type == "error":
            errores.append(mensaje.text)

    pagina.on("console", anotar)
    pagina.add_init_script(
        """
        window.__violaciones = [];
        document.addEventListener("securitypolicyviolation", (evento) => {
          window.__violaciones.push(evento.violatedDirective || "");
        });
        """
    )
    abrir(pagina, servidor)
    violaciones = pagina.evaluate("() => window.__violaciones")
    assert errores == []
    assert violaciones == []


def test_el_servidor_simulado_no_sirve_los_archivos_de_las_pruebas(
    servidor: ServidorSimulado,
) -> None:
    """Ninguna ruta, ni con puntos, deja leer web/tests/ desde el simulado (spec 002, T005)."""
    rutas = (
        "/tests/conftest.py",
        "/js/../tests/conftest.py",
        "/./tests/conftest.py",
        "/js/%2e%2e/tests/conftest.py",
    )
    for ruta in rutas:
        conexion = http.client.HTTPConnection("127.0.0.1", servidor.puerto)
        try:
            conexion.request("GET", ruta)
            assert conexion.getresponse().status == 404, ruta
        finally:
            conexion.close()


_HORA = 1_700_000_000


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def _cabe(pagina: Page) -> None:
    expect(pagina.locator('[data-prueba="marca"]')).to_be_visible()
    assert pagina.evaluate("() => document.documentElement.scrollWidth") <= 320


def _cobrar(pagina: Page, servidor: ServidorSimulado) -> str:
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    ids = list(servidor.cobros)
    assert ids
    return str(ids[-1])


def _esperar_abierto(pagina: Page) -> None:
    pagina.wait_for_function(
        "() => window.__canales.some((canal) => canal.readyState === 1)",
        timeout=5_000,
    )


def test_todas_las_vistas_caben_en_320_px_y_muestran_pago_facil(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cada vista cabe en 320 px y muestra la marca (spec 002, RF-060, RF-061, CE-007)."""
    alto = 640 if pagina.viewport_size is None else pagina.viewport_size["height"]
    pagina.set_viewport_size({"width": 320, "height": alto})
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)
    _cabe(pagina)

    servidor.responder_crear(demora=1)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-generando"]')).to_be_visible()
    _cabe(pagina)
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    _cabe(pagina)
    caja = pagina.locator('[data-prueba="qr"]').bounding_box()
    ancho = pagina.evaluate("() => document.documentElement.clientWidth")
    assert caja is not None
    assert caja["width"] >= ancho * 0.7 - 1

    id_cobro = str(list(servidor.cobros)[-1])
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    _cabe(pagina)

    pagina.evaluate("() => localStorage.removeItem('pago_facil_escucha')")
    pagina.reload()
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_visible()
    _cabe(pagina)

    pagina.evaluate("() => localStorage.removeItem('pago_facil_escucha')")
    pagina.reload()
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.olvidar(id_cobro)
    servidor.cortar_canal(id_cobro, rechazar_con=404)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    pagina.clock.run_for(3_000)
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_visible()
    _cabe(pagina)


def test_la_web_solo_pide_cosas_al_servidor_configurado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Crear, pagar, consultar, vencer y el error solo hablan con el simulado (spec 002, RF-063)."""
    urls: list[str] = []
    pagina.on("request", lambda peticion: urls.append(peticion.url))
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    pagina.locator('[data-prueba="nuevo-cobro"]').locator("visible=true").click()
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_visible()
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    pagina.clock.run_for(3_000)
    servidor.olvidar(id_cobro)
    pagina.clock.run_for(3_000)
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_visible()

    # El sonido es un blob: de esta misma página (R-7), no una llamada a otro servidor.
    def propia(url: str) -> bool:
        return url.startswith(servidor.origen) or url.startswith(f"blob:{servidor.origen}/")

    ajenas = [url for url in urls if not propia(url)]
    assert ajenas == []
