"""Pagos avisados, sonido y pantalla encendida (spec 002, T012, T029)."""

from __future__ import annotations

import time

import pytest
from conftest import abrir, bloqueos, reloj, sonidos, tocar, vibraciones
from playwright.sync_api import Dialog, Page, expect
from servidor_simulado import ServidorSimulado


@pytest.mark.only_browser("chromium")
def test_avisados_devuelve_solo_los_pagos_con_numero_mayor_al_ultimo_avisado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """nuevos entrega cada pago una sola vez, en orden (spec 002, RF-029)."""
    abrir(pagina, servidor)
    numeros = pagina.evaluate(
        """async () => {
          const { Avisados } = await import("/js/avisados.js");
          const avisados = new Avisados();
          const cobro = {
            id: "CobroAvisos01",
            numero_de_pagos: 2,
            pagos: [
              { numero: 1, monto_recibido: 25.5 },
              { numero: 2, monto_recibido: 10 },
            ],
          };
          const primera = avisados.nuevos(cobro).map((pago) => pago.numero);
          cobro.pagos.push({ numero: 3, monto_recibido: 1 });
          cobro.numero_de_pagos = 3;
          const segunda = avisados.nuevos(cobro).map((pago) => pago.numero);
          const tercera = avisados.nuevos(cobro).map((pago) => pago.numero);
          return { primera, segunda, tercera };
        }"""
    )
    assert numeros == {"primera": [1, 2], "segunda": [3], "tercera": []}


@pytest.mark.only_browser("chromium")
def test_avisados_lleva_la_cuenta_por_cobro(pagina: Page, servidor: ServidorSimulado) -> None:
    """El pago 1 de otro cobro sigue siendo nuevo (spec 002, RF-029)."""
    abrir(pagina, servidor)
    numeros = pagina.evaluate(
        """async () => {
          const { Avisados } = await import("/js/avisados.js");
          const avisados = new Avisados();
          avisados.nuevos({
            id: "CobroAvisos01",
            numero_de_pagos: 1,
            pagos: [{ numero: 1, monto_recibido: 25.5 }],
          });
          return avisados
            .nuevos({
              id: "CobroAvisos02",
              numero_de_pagos: 1,
              pagos: [{ numero: 1, monto_recibido: 8 }],
            })
            .map((pago) => pago.numero);
        }"""
    )
    assert numeros == [1]


@pytest.mark.only_browser("chromium")
def test_marcar_todos_marca_sin_devolver_pagos(pagina: Page, servidor: ServidorSimulado) -> None:
    """marcar_todos fija el último avisado y nuevos no devuelve nada (spec 002, RF-053, RF-075)."""
    abrir(pagina, servidor)
    numeros = pagina.evaluate(
        """async () => {
          const { Avisados } = await import("/js/avisados.js");
          const avisados = new Avisados();
          const cobro = {
            id: "CobroAvisos01",
            numero_de_pagos: 2,
            pagos: [
              { numero: 1, monto_recibido: 25.5 },
              { numero: 2, monto_recibido: 10 },
            ],
          };
          const devuelto = avisados.marcar_todos(cobro);
          return {
            devuelto: devuelto === undefined ? null : devuelto,
            despues: avisados.nuevos(cobro).map((pago) => pago.numero),
          };
        }"""
    )
    assert numeros["devuelto"] is None
    assert numeros["despues"] == []


def test_el_sonido_se_desbloquea_con_un_toque_y_despues_suena_sin_otro(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """desbloquear suena en silencio; sonar ya no pide otro toque (spec 002, RF-022, RF-025)."""
    abrir(pagina, servidor)
    reproducciones = pagina.evaluate(
        """async () => {
          const { desbloquear, sonar } = await import("/js/sonido.js");
          desbloquear();
          const silencio = window.__sonidos.map((sonido) => ({
            volume: sonido.volume,
            muted: sonido.muted,
            src: sonido.src,
          }));
          sonar();
          return silencio;
        }"""
    )
    assert reproducciones
    assert all(sonido["volume"] == 0 for sonido in reproducciones)
    assert all(str(sonido["src"]).startswith("blob:") for sonido in reproducciones)
    assert sonidos(pagina) == 1


def test_vibrar_solo_si_el_celular_puede(
    pagina: Page, servidor: ServidorSimulado, browser_name: str
) -> None:
    """En Chromium vibra 200-100-200; en WebKit no lanza error (spec 002, RF-024)."""
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { vibrar } = await import("/js/sonido.js");
          vibrar();
        }"""
    )
    if browser_name == "chromium":
        assert vibraciones(pagina) == [[200, 100, 200]]


def test_mantener_encendida_pide_y_suelta_el_bloqueo(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Pedir dos veces cuenta un bloqueo; soltar lo libera (spec 002, RF-058, RF-059)."""
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { mantener_encendida } = await import("/js/pantalla.js");
          await mantener_encendida(true);
          await mantener_encendida(true);
          await mantener_encendida(false);
        }"""
    )
    assert bloqueos(pagina) == {"pedidos": 1, "soltados": 1}


def test_soltar_mientras_se_pide_el_bloqueo_no_lo_deja_pegado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si se suelta con el pedido en vuelo, el bloqueo que llega se libera (spec 002, RF-059)."""
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { mantener_encendida } = await import("/js/pantalla.js");
          const pedir = navigator.wakeLock.request.bind(navigator.wakeLock);
          navigator.wakeLock.request = (tipo) =>
            new Promise((resolver) => {
              setTimeout(() => resolver(pedir(tipo)), 50);
            });
          const pedido = mantener_encendida(true);
          await mantener_encendida(false);
          await pedido;
        }"""
    )
    assert bloqueos(pagina) == {"pedidos": 1, "soltados": 1}


def test_al_volver_a_la_pagina_se_vuelve_a_pedir_el_bloqueo(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Al volver a verse la página se pide otra vez el bloqueo (spec 002, RF-058)."""
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { mantener_encendida } = await import("/js/pantalla.js");
          await mantener_encendida(true);
          document.dispatchEvent(new Event("visibilitychange"));
          await new Promise((resolver) => {
            setTimeout(resolver, 0);
          });
        }"""
    )
    assert bloqueos(pagina)["pedidos"] == 2


def test_sin_wake_lock_no_falla(pagina: Page, servidor: ServidorSimulado) -> None:
    """Sin navigator.wakeLock, mantener la pantalla no lanza error (spec 002, RF-058)."""
    abrir(pagina, servidor)
    pagina.evaluate(
        """async () => {
          const { mantener_encendida } = await import("/js/pantalla.js");
          Object.defineProperty(navigator, "wakeLock", {
            configurable: true,
            value: undefined,
          });
          await mantener_encendida(true);
        }"""
    )


_HORA = 1_700_000_000


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def _ultimo_id(servidor: ServidorSimulado) -> str:
    ids = list(servidor.cobros)
    assert ids
    return str(ids[-1])


def _cobrar(pagina: Page, servidor: ServidorSimulado, concepto: str = "Tacos") -> str:
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill(concepto)
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    return _ultimo_id(servidor)


def _esperar_abierto(pagina: Page) -> None:
    pagina.wait_for_function(
        "() => window.__canales.some((canal) => canal.readyState === 1)",
        timeout=5_000,
    )


def _esperar_cerrado(pagina: Page, id_cobro: str) -> None:
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes(id) && canal.readyState === 2;
        })""",
        arg=id_cobro,
        timeout=8_000,
    )


def test_al_mostrar_el_qr_se_abre_el_canal_del_cobro(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """La vista QR abre el canal de ese cobro (spec 002, RF-020)."""
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    ruta = f"/api/cobros/{id_cobro}/eventos"
    canales_pedidos = [
        pedido
        for metodo, pedido, _cuerpo in servidor.peticiones
        if metodo == "GET" and pedido == ruta
    ]
    assert canales_pedidos


def test_un_pago_suena_vibra_y_pone_la_pantalla_verde_sin_tocar_nada_despues_de_cobrar(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un pago suena, vibra y muestra Pago recibido sin otro toque (spec 002, RF-022, CE-002)."""
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_hidden()
    inicio = time.perf_counter()
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    assert time.perf_counter() - inicio < 2
    expect(pagina.locator('[data-prueba="pagado"]')).to_have_text("Pago recibido")
    expect(pagina.locator('[data-prueba="pagado-monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="pagado-concepto"]')).to_have_text("Tacos")
    assert sonidos(pagina) == 1
    navegador = pagina.context.browser
    if navegador is not None and navegador.browser_type.name == "chromium":
        assert len(vibraciones(pagina)) == 1


def test_si_el_navegador_bloquea_el_sonido_avisa_y_reintenta_al_tocar(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un NotAllowedError conserva el aviso visual y permite reintentar (spec 002, C-5)."""
    reloj(pagina, _HORA)
    pagina.add_init_script("window.__rechazar_sonido = true;")
    mensajes: list[str] = []
    pagina.on("console", lambda mensaje: mensajes.append(mensaje.text))
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    aviso = pagina.locator('[data-prueba="activar-sonido"]')
    expect(aviso).to_have_text("Toca para activar el sonido", timeout=3_000)
    assert sonidos(pagina) == 1
    assert "sonido: aviso rechazado (NotAllowedError)" in mensajes
    aviso.click()
    expect(aviso).to_be_visible()
    assert sonidos(pagina) == 2
    pagina.evaluate("() => { window.__rechazar_sonido = false; }")
    aviso.click()
    expect(aviso).to_be_hidden()
    assert sonidos(pagina) == 3
    assert "sonido: aviso iniciado" in mensajes
    servidor.agregar_pago(id_cobro, 1)
    expect(pagina.locator('[data-prueba="pagado-numero"]')).to_have_text("Pago 2")
    assert sonidos(pagina) == 4


@pytest.mark.parametrize("regreso", ["visibilitychange", "pageshow"])
def test_al_volver_a_la_pagina_el_primer_toque_repite_el_desbloqueo(
    pagina: Page, servidor: ServidorSimulado, regreso: str
) -> None:
    """El regreso prepara un solo desbloqueo, que espera al toque (spec 002, C-5)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    _cobrar(pagina, servidor)
    cuenta = pagina.evaluate("() => window.__sonidos.length")
    pagina.evaluate(
        """(regreso) => {
          if (regreso === "pageshow") {
            window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
            return;
          }
          for (const estado of ["hidden", "visible"]) {
            Object.defineProperty(document, "visibilityState", {
              configurable: true, value: estado,
            });
            document.dispatchEvent(new Event("visibilitychange"));
          }
        }""",
        regreso,
    )
    assert pagina.evaluate("() => window.__sonidos.length") == cuenta
    monto = pagina.locator('[data-prueba="qr-monto"]')
    monto.click()
    assert pagina.evaluate("() => window.__sonidos.length") == cuenta + 1
    assert sonidos(pagina) == 0
    monto.click()
    assert pagina.evaluate("() => window.__sonidos.length") == cuenta + 1


@pytest.mark.parametrize(
    "sesion, tipo",
    [('({ type: "auto" })', "playback"), ("undefined", None), ("Object.freeze({})", None)],
    ids=["disponible", "ausente", "solo-lectura"],
)
def test_la_sesion_de_audio_configura_playback_si_puede(
    pagina: Page, servidor: ServidorSimulado, sesion: str, tipo: str | None
) -> None:
    """El uso opcional de audioSession no interrumpe el sonido (spec 002, C-5)."""
    reloj(pagina, _HORA)
    pagina.add_init_script(
        f'Object.defineProperty(navigator, "audioSession", {{ value: {sesion} }});'
    )
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    assert pagina.evaluate("() => navigator.audioSession?.type ?? null") == tipo
    assert sonidos(pagina) == 1


def test_pago_recibido_se_queda_varios_minutos(pagina: Page, servidor: ServidorSimulado) -> None:
    """La vista Pago recibido no cambia sola (spec 002, RF-026)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    pagina.clock.fast_forward(5 * 60_000)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="pagado"]')).to_have_text("Pago recibido")


def test_un_segundo_pago_al_mismo_qr_vuelve_a_sonar(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El segundo pago suena otra vez y muestra su monto (spec 002, RF-022, RF-029)."""
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="pagado-monto"]')).to_have_text("$25.50")
    servidor.agregar_pago(id_cobro, 10)
    expect(pagina.locator('[data-prueba="pagado-monto"]')).to_have_text("$10.00")
    assert sonidos(pagina) == 2


def test_un_monto_distinto_muestra_el_pedido_y_el_recibido(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si el pago trae monto distinto, se ven el pedido y el recibido (spec 002, RF-028)."""
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 20, monto_distinto=True)
    distinto = pagina.locator('[data-prueba="pagado-distinto"]')
    expect(distinto).to_be_visible()
    expect(distinto).to_contain_text("$25.50")
    expect(distinto).to_contain_text("$20.00")
    # Sin rótulos, "$25.50 $20.00" no dice cuál se pidió y cuál llegó (RF-028).
    expect(distinto).to_have_text("Pediste $25.50, recibiste $20.00")

    pagina.evaluate("() => localStorage.removeItem('pago_facil_escucha')")
    pagina.reload()
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5, monto_distinto=False)
    expect(pagina.locator('[data-prueba="pagado-distinto"]')).to_be_hidden()


def test_el_mismo_pago_por_canal_reconexion_y_consulta_suena_una_sola_vez(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El mismo pago por canal, consulta y reconexión suena una vez (spec 002, RF-029, CE-008)."""
    reloj(pagina, _HORA)
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    _esperar_cerrado(pagina, id_cobro)
    pagina.clock.run_for(3_000)
    servidor.permitir_canal(id_cobro)
    pagina.clock.run_for(15_000)
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes(id) && canal.readyState === 1;
        })""",
        arg=id_cobro,
        timeout=5_000,
    )
    assert sonidos(pagina) == 1


def test_la_pantalla_pide_no_apagarse_mientras_hay_un_cobro_en_escucha(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Con un cobro en escucha se pide mantener la pantalla (spec 002, RF-058)."""
    abrir(pagina, servidor)
    _cobrar(pagina, servidor)
    pagina.wait_for_function("() => window.__bloqueos_pedidos === 1", timeout=5_000)
    assert bloqueos(pagina)["pedidos"] == 1


def test_el_concepto_en_pago_recibido_se_muestra_como_texto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El concepto del pago se ve tal cual, sin ejecutarse (spec 002, RF-077, CE-015)."""
    dialogos: list[str] = []

    def guardar(dialogo: Dialog) -> None:
        dialogos.append(dialogo.message)
        dialogo.dismiss()

    pagina.on("dialog", guardar)
    abrir(pagina, servidor)
    concepto = "<script>alert(1)</script>"
    id_cobro = _cobrar(pagina, servidor, concepto)
    scripts = pagina.locator("#vistas script").count()
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="pagado-concepto"]')).to_have_text(concepto)
    assert pagina.locator("#vistas script").count() == scripts
    assert dialogos == []


def test_pago_recibido_cabe_en_320_px(pagina: Page, servidor: ServidorSimulado) -> None:
    """Pago recibido cabe en 320 px y la marca se ve (spec 002, RF-060, RF-061)."""
    alto = 640 if pagina.viewport_size is None else pagina.viewport_size["height"]
    pagina.set_viewport_size({"width": 320, "height": alto})
    abrir(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="marca"]')).to_be_visible()
    assert pagina.evaluate("() => document.documentElement.scrollWidth") <= 320
