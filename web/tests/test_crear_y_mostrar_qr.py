"""Cuenta regresiva y crear_cobro contra el servidor simulado (spec 002, T011)."""

from __future__ import annotations

import re
import time

import pytest
from conftest import abrir, reloj, tocar
from playwright.sync_api import Dialog, Page, Route, expect
from servidor_simulado import ServidorSimulado

_MENSAJE_SIN_CONEXION = "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo."
_MENSAJE_SIN_QR = "No se pudo mostrar el QR. Intenta de nuevo."
_HORA = 1_700_000_000


def _abortar(ruta: Route) -> None:
    ruta.abort()


@pytest.mark.only_browser("chromium")
def test_la_cuenta_descuenta_el_desfase_con_el_servidor_en_la_funcion(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Con el celular adelantado, el restante sigue la vigencia del servidor (spec 002, RF-019)."""
    abrir(pagina, servidor)
    instante = _HORA
    resultado = pagina.evaluate(
        """async (instante) => {
          const { desfase, restante } = await import("/js/cuenta.js");
          const cobro = { expira_en: instante + 600, hora_servidor: instante };
          const ahora = instante + 300;
          const diferencia = desfase(cobro, ahora);
          return { desfase: diferencia, restante: restante(cobro, diferencia, ahora) };
        }""",
        instante,
    )
    assert resultado == {"desfase": -300, "restante": 600}


@pytest.mark.only_browser("chromium")
def test_si_crear_tardo_9_segundos_la_cuenta_arranca_en_9_51_en_la_funcion(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si el cobro tardó 9 s, al recibirlo quedan 9:51 (spec 002, RF-019)."""
    abrir(pagina, servidor)
    instante = _HORA
    texto = pagina.evaluate(
        """async (instante) => {
          const { desfase, restante, formato } = await import("/js/cuenta.js");
          const cobro = {
            creado_en: instante,
            expira_en: instante + 600,
            hora_servidor: instante + 9,
          };
          const ahora = instante + 9;
          const diferencia = desfase(cobro, ahora);
          return formato(restante(cobro, diferencia, ahora));
        }""",
        instante,
    )
    assert texto == "9:51"


@pytest.mark.only_browser("chromium")
def test_el_formato_de_la_cuenta_es_minutos_y_segundos(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El formato es m:ss, trunca y no baja de 0:00 (spec 002, RF-018)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { formato } = await import("/js/cuenta.js");
          return {
            diez: formato(600),
            truncado: formato(591.7),
            menos_de_un_minuto: formato(59),
            cero: formato(0),
            negativo: formato(-5),
          };
        }"""
    )
    assert resultado == {
        "diez": "10:00",
        "truncado": "9:51",
        "menos_de_un_minuto": "0:59",
        "cero": "0:00",
        "negativo": "0:00",
    }


@pytest.mark.only_browser("chromium")
def test_sin_hora_del_servidor_se_usa_el_reloj_del_celular_y_se_avisa(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Sin hora_servidor el desfase es 0 y queda un aviso en consola (spec 002, RF-019)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const avisos = [];
          const avisar = console.warn.bind(console);
          console.warn = (...partes) => {
            avisos.push(partes.join(" "));
            avisar(...partes);
          };
          const { desfase } = await import("/js/cuenta.js");
          return { desfase: desfase({ expira_en: 1000 }, 1000), avisos };
        }"""
    )
    assert resultado["desfase"] == 0
    assert any("hora_servidor" in texto for texto in resultado["avisos"])


@pytest.mark.only_browser("chromium")
def test_crear_cobro_manda_el_monto_como_numero_y_el_concepto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El cuerpo es monto numérico y concepto, en /api/cobros (spec 002, RF-009)."""
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { crear_cobro } = await import("/js/servidor.js");
          return crear_cobro(25.5, "Tacos");
        }"""
    )
    posts = [item for item in servidor.peticiones if item[0] == "POST"]
    assert ("POST", "/api/cobros", {"monto": 25.5, "concepto": "Tacos"}) in posts


@pytest.mark.only_browser("chromium")
def test_crear_cobro_201_con_imagen_devuelve_el_cobro(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un 201 con imagen devuelve el cobro (spec 002, RF-009, RF-015)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { crear_cobro } = await import("/js/servidor.js");
          return crear_cobro(25.5, "Tacos");
        }"""
    )
    assert "mensaje" not in resultado
    cobro = resultado["cobro"]
    assert cobro["monto"] == 25.5
    assert cobro["concepto"] == "Tacos"
    assert isinstance(cobro["qr_imagen"], str) and cobro["qr_imagen"]
    assert isinstance(cobro["id"], str) and len(cobro["id"]) == 12


@pytest.mark.only_browser("chromium")
def test_crear_cobro_201_sin_imagen_devuelve_el_mensaje_del_qr(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un 201 con qr_imagen null devuelve el mensaje del QR (spec 002, RF-078)."""
    servidor.responder_crear(cuerpo={"monto": 25.5, "concepto": "Tacos", "qr_imagen": None})
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { crear_cobro } = await import("/js/servidor.js");
          return crear_cobro(25.5, "Tacos");
        }"""
    )
    assert resultado == {"mensaje": _MENSAJE_SIN_QR}


@pytest.mark.only_browser("chromium")
@pytest.mark.parametrize("codigo", [422, 429, 502, 503])
def test_crear_cobro_rechazado_devuelve_el_detail(
    pagina: Page, servidor: ServidorSimulado, codigo: int
) -> None:
    """422, 429, 502 y 503 devuelven el detail tal cual (spec 002, RF-012)."""
    detalle = f"detalle {codigo}"
    servidor.responder_crear(codigo=codigo, cuerpo={"detail": detalle})
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { crear_cobro } = await import("/js/servidor.js");
          return crear_cobro(25.5, "Tacos");
        }"""
    )
    assert resultado == {"mensaje": detalle}


@pytest.mark.only_browser("chromium")
def test_crear_cobro_sin_respuesta_en_15_segundos_devuelve_sin_conexion(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """A los 14 s sigue esperando; a los 15 s avisa sin conexión (spec 002, RF-013)."""
    abrir(pagina, servidor)
    reloj(pagina, _HORA)
    servidor.responder_crear(sin_respuesta=True)
    pagina.evaluate(
        """() => {
          window.__listo = false;
          window.__resultado = null;
          return import("/js/servidor.js").then(({ crear_cobro }) => {
            crear_cobro(25.5, "Tacos").then((resultado) => {
              window.__resultado = resultado;
              window.__listo = true;
            });
          });
        }"""
    )
    pagina.clock.run_for(14_000)
    assert pagina.evaluate("() => window.__listo") is False
    pagina.clock.run_for(1_000)
    pagina.wait_for_function("() => window.__listo === true", timeout=5_000)
    assert pagina.evaluate("() => window.__resultado") == {"mensaje": _MENSAJE_SIN_CONEXION}


@pytest.mark.only_browser("chromium")
def test_crear_cobro_con_fallo_de_red_devuelve_sin_conexion(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si la petición se corta, el mensaje pide revisar la conexión (spec 002, RF-013)."""
    abrir(pagina, servidor)
    pagina.route("**/api/cobros", _abortar)
    resultado = pagina.evaluate(
        """async () => {
          const { crear_cobro } = await import("/js/servidor.js");
          return crear_cobro(25.5, "Tacos");
        }"""
    )
    assert resultado == {"mensaje": _MENSAJE_SIN_CONEXION}


@pytest.mark.only_browser("chromium")
def test_la_direccion_del_servidor_sale_de_config_js(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """crear_cobro usa la dirección de config.js (spec 002, RF-064)."""
    servidor.fijar_config('window.PAGO_FACIL = { servidor: "/otro" };')
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { crear_cobro } = await import("/js/servidor.js");
          return crear_cobro(25.5, "Tacos");
        }"""
    )
    assert any(
        metodo == "POST" and ruta == "/otro/api/cobros"
        for metodo, ruta, _cuerpo in servidor.peticiones
    )


@pytest.mark.only_browser("chromium")
def test_crear_y_ver_solo_piden_cosas_al_servidor_configurado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Crear y ver un cobro solo hablan con el origen del simulado (spec 002, RF-063)."""
    abrir(pagina, servidor)
    vistas: list[str] = []
    pagina.on("request", lambda peticion: vistas.append(peticion.url))
    pagina.evaluate(
        """async () => {
          const { crear_cobro, ver_cobro } = await import("/js/servidor.js");
          const creado = await crear_cobro(25.5, "Tacos");
          return ver_cobro(creado.cobro.id);
        }"""
    )
    assert vistas
    assert all(url.startswith(servidor.origen) for url in vistas)


_INDICACION = "Escanéalo desde la app de tu banco, en la opción CoDi"
_RECHAZOS = (
    (422, "El monto máximo de la demo es $100"),
    (429, "Demasiados cobros seguidos. Espera un minuto."),
    (502, "No se pudo crear el cobro con pey. Intenta de nuevo."),
    (503, "pey está en mantenimiento. Intenta de nuevo en unos minutos."),
)


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def _escribir_y_cobrar(pagina: Page, concepto: str = "Tacos", monto: str = "25.50") -> None:
    _teclear(pagina, monto)
    pagina.locator('[data-prueba="concepto"]').fill(concepto)
    tocar(pagina, "cobrar")


def _posts(servidor: ServidorSimulado) -> list[tuple[str, str, object]]:
    return [item for item in servidor.peticiones if item[0] == "POST" and item[1] == "/api/cobros"]


def _posts_uno(servidor: ServidorSimulado) -> None:
    """Espera el POST del cobro y comprueba que no sale otro (spec 002, RF-011)."""
    limite = time.monotonic() + 5
    while time.monotonic() < limite and len(_posts(servidor)) < 1:
        time.sleep(0.05)
    assert len(_posts(servidor)) == 1
    time.sleep(0.3)
    assert len(_posts(servidor)) == 1


def test_cobrar_pide_el_cobro_y_muestra_el_qr_con_monto_concepto_e_indicacion_codi(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cobrar manda el monto numérico y muestra el QR (spec 002, RF-009, RF-015, RF-016, RF-017)."""
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="qr"]')).to_have_attribute(
        "src", re.compile(r"^data:image/png;base64,")
    )
    expect(pagina.locator('[data-prueba="qr-monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="qr-concepto"]')).to_have_text("Tacos")
    expect(pagina.locator('[data-prueba="indicacion-codi"]')).to_have_text(_INDICACION)
    assert ("POST", "/api/cobros", {"monto": 25.5, "concepto": "Tacos"}) in _posts(servidor)


def test_al_pulsar_cobrar_aparece_generando_qr_y_un_segundo_toque_no_crea_otro_cobro(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Generando QR sale al instante y el segundo toque no crea otro cobro
    (spec 002, RF-010, RF-011).
    """
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    pagina.evaluate(
        """() => {
          window.__generando_ms = null;
          const vista = document.querySelector('[data-prueba="vista-generando"]');
          const cobrar = document.querySelector('[data-prueba="cobrar"]');
          let inicio = 0;
          cobrar.addEventListener("pointerdown", () => {
            inicio = performance.now();
          });
          const observador = new MutationObserver(() => {
            if (!vista.hidden && window.__generando_ms === null && inicio > 0) {
              window.__generando_ms = performance.now() - inicio;
            }
          });
          observador.observe(vista, { attributes: true, attributeFilter: ["hidden"] });
        }"""
    )
    servidor.responder_crear(demora=2)
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-generando"]')).to_be_visible()
    pagina.locator('[data-prueba="cobrar"]').evaluate("nodo => nodo.click()")
    pagina.wait_for_function("() => window.__generando_ms !== null")
    assert pagina.evaluate("() => window.__generando_ms") < 100
    _posts_uno(servidor)


@pytest.mark.parametrize(("codigo", "detalle"), _RECHAZOS)
def test_si_el_servidor_rechaza_el_cobro_se_ve_su_mensaje_y_se_conserva_lo_escrito(
    pagina: Page, servidor: ServidorSimulado, codigo: int, detalle: str
) -> None:
    """El rechazo muestra el detail sin el código y conserva lo escrito (spec 002, RF-012)."""
    servidor.responder_crear(codigo=codigo, cuerpo={"detail": detalle})
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    mensaje = pagina.locator('[data-prueba="mensaje"]')
    expect(mensaje).to_have_text(detalle)
    expect(mensaje).not_to_contain_text(str(codigo))
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("Tacos")


def test_sin_conexion_se_pide_revisar_la_conexion_y_se_conserva_lo_escrito(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Sin respuesta a los 15 s, o con la red cortada, se conserva lo escrito (spec 002, RF-013)."""
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    reloj(pagina, _HORA)
    servidor.responder_crear(sin_respuesta=True)
    tocar(pagina, "cobrar")
    pagina.clock.run_for(15_000)
    mensaje = pagina.locator('[data-prueba="mensaje"]')
    expect(mensaje).to_have_text(_MENSAJE_SIN_CONEXION)
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("Tacos")

    pagina.route("**/api/cobros", _abortar)
    tocar(pagina, "cobrar")
    expect(mensaje).to_have_text(_MENSAJE_SIN_CONEXION)
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("Tacos")


def test_si_el_qr_llega_sin_imagen_se_vuelve_al_teclado_con_mensaje(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Sin imagen vuelve al teclado y no abre el canal (spec 002, RF-078)."""
    servidor.responder_crear(cuerpo={"monto": 25.5, "concepto": "Tacos", "qr_imagen": None})
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="mensaje"]')).to_have_text(_MENSAJE_SIN_QR)
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("Tacos")
    eventos = [
        ruta
        for metodo, ruta, _cuerpo in servidor.peticiones
        if metodo == "GET" and "/eventos" in ruta
    ]
    assert eventos == []


def test_el_mensaje_de_error_se_borra_al_teclear(pagina: Page, servidor: ServidorSimulado) -> None:
    """Tras un 422, tocar una tecla deja el mensaje vacío (spec 002, RF-012)."""
    servidor.responder_crear(codigo=422, cuerpo={"detail": _RECHAZOS[0][1]})
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="mensaje"]')).to_have_text(_RECHAZOS[0][1])
    tocar(pagina, "tecla-0")
    expect(pagina.locator('[data-prueba="mensaje"]')).to_have_text("")


def test_el_concepto_y_el_mensaje_del_servidor_se_muestran_como_texto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El concepto y el detail se ven tal cual, sin ejecutarse (spec 002, RF-077, CE-015)."""
    dialogos: list[str] = []

    def guardar(dialogo: Dialog) -> None:
        dialogos.append(dialogo.message)
        dialogo.dismiss()

    pagina.on("dialog", guardar)
    detalle = "<img src=x onerror=alert(1)>"
    servidor.responder_crear(codigo=422, cuerpo={"detail": detalle})
    abrir(pagina, servidor)
    imagenes = pagina.locator("#vistas img").count()
    scripts = pagina.locator("#vistas script").count()
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="mensaje"]')).to_have_text(detalle)
    assert pagina.locator("#vistas script").count() == scripts
    assert pagina.locator("#vistas img").count() == imagenes
    assert pagina.locator('#vistas img:not([data-prueba="qr"])').count() == 0
    assert dialogos == []

    concepto = "<script>alert(1)</script>"
    pagina.locator('[data-prueba="concepto"]').fill(concepto)
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="qr-concepto"]')).to_have_text(concepto)
    assert pagina.locator("#vistas script").count() == scripts
    assert pagina.locator("#vistas img").count() == imagenes
    assert pagina.locator('#vistas img:not([data-prueba="qr"])').count() == 0
    assert dialogos == []


def test_la_vista_qr_cabe_en_320_px(pagina: Page, servidor: ServidorSimulado) -> None:
    """El QR cabe en 320 px y ocupa al menos el 70 % del ancho (spec 002, RF-061, CE-007)."""
    alto = 640 if pagina.viewport_size is None else pagina.viewport_size["height"]
    pagina.set_viewport_size({"width": 320, "height": alto})
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="marca"]')).to_be_visible()
    ancho_pagina = pagina.evaluate("() => document.documentElement.clientWidth")
    assert pagina.evaluate("() => document.documentElement.scrollWidth") <= 320
    caja = pagina.locator('[data-prueba="qr"]').bounding_box()
    assert caja is not None
    assert caja["width"] >= ancho_pagina * 0.7


def test_un_cobro_recien_creado_muestra_la_cuenta_en_10_00(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Con hora_servidor igual a creado_en, la cuenta empieza en 10:00 (spec 002, RF-018)."""
    servidor.fijar_hora(_HORA)
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="cuenta"]')).to_have_text("10:00")


def test_la_cuenta_regresiva_sigue_la_hora_del_servidor_aunque_el_celular_este_desfasado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un celular 5 minutos adelantado sigue entre 10:00 y 9:58 (spec 002, RF-019, CE-009)."""
    servidor.fijar_hora(_HORA)
    reloj(pagina, _HORA + 300)
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="cuenta"]')).to_have_text(
        re.compile(r"^(10:00|9:59|9:58)$")
    )


def test_si_crear_tardo_9_segundos_la_cuenta_arranca_en_9_51(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si hora_servidor es creado_en + 9, la cuenta queda entre 9:51 y 9:49 (spec 002, CE-016)."""
    servidor.fijar_hora(_HORA + 9)
    servidor.responder_crear(cuerpo={"monto": 25.5, "concepto": "Tacos", "creado_en": _HORA})
    reloj(pagina, _HORA + 9)
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="cuenta"]')).to_have_text(re.compile(r"^(9:51|9:50|9:49)$"))


def test_la_cuenta_regresiva_baja_con_el_tiempo(pagina: Page, servidor: ServidorSimulado) -> None:
    """61 s de reloj dejan la cuenta en 8:59, con 1 s de margen (spec 002, RF-018)."""
    servidor.fijar_hora(_HORA)
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    _escribir_y_cobrar(pagina)
    expect(pagina.locator('[data-prueba="cuenta"]')).to_have_text("10:00")
    pagina.clock.run_for(61_000)
    expect(pagina.locator('[data-prueba="cuenta"]')).to_have_text(re.compile(r"^(9:00|8:59|8:58)$"))
