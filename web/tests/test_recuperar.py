"""Recuperar los cobros en escucha al recargar (spec 002, T054)."""

from __future__ import annotations

from urllib.parse import unquote

import pytest
from conftest import abrir, canales, reloj, sonidos, tocar, vibraciones
from playwright.sync_api import Dialog, Locator, Page, Route, expect
from servidor_simulado import ServidorSimulado

_HORA = 1_700_000_000
_MENSAJE_ERROR = (
    "Este cobro ya no se puede seguir. Revisa la app de tu banco para confirmar si llegó el pago."
)
_TEXTO_SONIDO = "Toca para activar el sonido"
_VISTAS = {
    "pendiente": "vista-qr",
    "vencido": "vista-vencido",
    "pagado": "vista-pagado",
}


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def _ultimo_id(servidor: ServidorSimulado) -> str:
    ids = list(servidor.cobros)
    assert ids
    return str(ids[-1])


def _preparar(pagina: Page, servidor: ServidorSimulado) -> None:
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)


def _visible(pagina: Page, nombre: str) -> Locator:
    return pagina.locator(f'[data-prueba="{nombre}"]').locator("visible=true")


def _cobrar(
    pagina: Page,
    servidor: ServidorSimulado,
    monto: str = "25.50",
    concepto: str = "Tacos",
) -> str:
    _teclear(pagina, monto)
    pagina.locator('[data-prueba="concepto"]').fill(concepto)
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    return _ultimo_id(servidor)


def _nuevo(pagina: Page) -> None:
    _visible(pagina, "nuevo-cobro").click()
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()


def _esperar_abierto(pagina: Page) -> None:
    pagina.wait_for_function(
        "() => window.__canales.some((canal) => canal.readyState === 1)",
        timeout=10_000,
    )


def _esperar_canales(pagina: Page, ids: list[str]) -> None:
    pagina.wait_for_function(
        """(esperados) => {
          const abiertos = window.__canales.filter((canal) => canal.readyState === 1);
          if (abiertos.length !== esperados.length) {
            return false;
          }
          return esperados.every((id) => {
            return abiertos.some((canal) => canal.url.includes("/" + id + "/eventos"));
          });
        }""",
        arg=ids,
        timeout=10_000,
    )


def _canal_abierto(pagina: Page, id_cobro: str) -> bool:
    sufijo = f"/{id_cobro}/eventos"
    return any(
        canal["estado"] == "OPEN" and canal["url"].endswith(sufijo) for canal in canales(pagina)
    )


@pytest.mark.only_browser("chromium")
def test_memoria_guarda_y_lee_los_cobros_en_escucha(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """guardar y leer usan la clave pago_facil_escucha (spec 002, RF-051)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { guardar, leer } = await import("/js/memoria.js");
          guardar("Xk3vQ9aZ1bNc", ["Ab12Cd34Ef56"]);
          return {
            leido: leer(),
            crudo: localStorage.getItem("pago_facil_escucha"),
          };
        }"""
    )
    assert resultado["leido"] == {
        "en_pantalla": "Xk3vQ9aZ1bNc",
        "anteriores": ["Ab12Cd34Ef56"],
    }
    assert resultado["crudo"] is not None
    assert "pago_facil_escucha" in pagina.evaluate("() => Object.keys(localStorage)")


@pytest.mark.only_browser("chromium")
def test_lo_recordado_que_no_tiene_forma_valida_se_ignora(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un recuerdo inválido se ignora entero (spec 002, RF-077)."""
    abrir(pagina, servidor)
    id_largo = "a" * 33
    lecturas = pagina.evaluate(
        """async (idLargo) => {
          const { leer } = await import("/js/memoria.js");
          const casos = [
            "no-es-json",
            JSON.stringify({ en_pantalla: "Abc", anteriores: [], sobra: 1 }),
            JSON.stringify({ en_pantalla: "Abc" }),
            JSON.stringify({ en_pantalla: null, anteriores: "Abc" }),
            JSON.stringify({ en_pantalla: idLargo, anteriores: [] }),
            JSON.stringify({
              en_pantalla: "<script>alert(1)</script>",
              anteriores: [],
            }),
          ];
          return casos.map((texto) => {
            localStorage.setItem("pago_facil_escucha", texto);
            return leer();
          });
        }""",
        id_largo,
    )
    assert lecturas == [None, None, None, None, None, None]


@pytest.mark.only_browser("chromium")
def test_sin_almacenamiento_memoria_no_falla(pagina: Page, servidor: ServidorSimulado) -> None:
    """Si localStorage lanza, guardar y leer no lanzan (spec 002, RF-076)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const fallo = () => {
            throw new Error("bloqueado");
          };
          Storage.prototype.getItem = fallo;
          Storage.prototype.setItem = fallo;
          const { guardar, leer } = await import("/js/memoria.js");
          let guardar_lanzo = false;
          let leer_lanzo = false;
          try {
            guardar("Xk3vQ9aZ1bNc", []);
          } catch (_error) {
            guardar_lanzo = true;
          }
          try {
            leer();
          } catch (_error) {
            leer_lanzo = true;
          }
          return { guardar_lanzo, leer_lanzo, leido: null };
        }"""
    )
    assert resultado == {"guardar_lanzo": False, "leer_lanzo": False, "leido": None}


@pytest.mark.parametrize("estado", ["pendiente", "vencido", "pagado"])
def test_al_recargar_se_recuperan_los_cobros_en_escucha(
    pagina: Page, servidor: ServidorSimulado, estado: str
) -> None:
    """Tras recargar, la vista sigue al estado y se escucha (spec 002, RF-051, RF-052)."""
    _preparar(pagina, servidor)
    id_anterior = _cobrar(pagina, servidor, monto="10", concepto="Agua")
    _esperar_abierto(pagina)
    _nuevo(pagina)
    id_pantalla = _cobrar(pagina, servidor, monto="20", concepto="Tacos")
    _esperar_abierto(pagina)
    if estado == "vencido":
        servidor.fijar_hora(_HORA + 600)
    elif estado == "pagado":
        servidor.agregar_pago(id_pantalla, 20, avisar=False)
    pagina.reload()
    expect(pagina.locator(f'[data-prueba="{_VISTAS[estado]}"]')).to_be_visible()
    _esperar_canales(pagina, [id_pantalla, id_anterior])


def test_los_pagos_con_la_pagina_cerrada_se_muestran_sin_sonar(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Lo pagado con la página cerrada se muestra sin sonar (spec 002, RF-053, RF-075)."""
    _preparar(pagina, servidor)
    id_anterior = _cobrar(pagina, servidor, monto="30", concepto="Refresco")
    _esperar_abierto(pagina)
    _nuevo(pagina)
    id_pantalla = _cobrar(pagina, servidor, monto="25", concepto="Tacos")
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_pantalla, 10, avisar=False)
    servidor.agregar_pago(id_pantalla, 5, avisar=False)
    servidor.agregar_pago(id_anterior, 30, avisar=False)
    servidor.agregar_pago(id_anterior, 5, avisar=False)
    pagina.reload()
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="pagado-numero"]')).to_have_text("Pago 2")
    expect(pagina.locator('[data-prueba="pagado-total"]')).to_contain_text("$15.00")
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_have_text(
        ["Pago de un cobro anterior: $30.00 Refresco", "Pago de un cobro anterior: $5.00 Refresco"]
    )
    assert sonidos(pagina) == 0
    assert vibraciones(pagina) == []


def test_tras_recargar_se_pide_un_toque_para_el_sonido(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Hasta el primer toque no suena; después, el pago nuevo sí (spec 002, RF-054, RF-055)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor, monto="25.50", concepto="Tacos")
    _esperar_abierto(pagina)
    pagina.reload()
    aviso = pagina.locator('[data-prueba="activar-sonido"]')
    expect(aviso).to_have_text(_TEXTO_SONIDO)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    assert sonidos(pagina) == 0
    assert vibraciones(pagina) == []
    aviso.click()
    expect(aviso).to_be_hidden()
    servidor.agregar_pago(id_cobro, 1)
    expect(pagina.locator('[data-prueba="pagado-numero"]')).to_have_text("Pago 2")
    assert sonidos(pagina) == 1


def test_al_recargar_un_cobro_pagado_el_qr_reabierto_conserva_su_cuenta(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El QR reabierto tras recuperar un pago sigue contando hasta vencer (RF-070, RF-071)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    servidor.fijar_hora(_HORA + 594)
    servidor.agregar_pago(id_cobro, 25.5, avisar=False)
    pagina.reload()
    tocar(pagina, "mostrar-qr")
    cuenta = pagina.locator('[data-prueba="cuenta"]')
    expect(cuenta).to_have_text("0:06")
    pagina.clock.fast_forward(2_000)
    expect(cuenta).to_have_text("0:04")
    pagina.clock.fast_forward(4_000)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="mostrar-qr"]')).to_be_hidden()


def test_al_recargar_un_cobro_cancelado_pasa_a_anterior(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un cobro cancelado fuera de la página sigue en escucha desde el teclado (RF-048, RF-049)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    pagina.evaluate("() => window.__canales.forEach((canal) => canal.close())")
    respuesta = pagina.request.post(f"{servidor.origen}/api/cobros/{id_cobro}/cancelar")
    assert respuesta.ok
    pagina.reload()
    _esperar_canales(pagina, [id_cobro])
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_hidden()
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="aviso-anterior"]')).to_contain_text("$25.50 Tacos")


def test_al_recargar_se_reintenta_la_consulta_sin_perder_el_cobro(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un fallo transitorio del GET durante recuperación conserva el cobro (RF-030, RF-051)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    ruta = f"{servidor.origen}/api/cobros/{id_cobro}"
    pagina.route(ruta, lambda consulta: consulta.abort(), times=1)
    with pagina.expect_event("requestfailed", predicate=lambda peticion: peticion.url == ruta):
        pagina.reload()
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_hidden()
    pagina.clock.run_for(3_000)
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    _esperar_canales(pagina, [id_cobro])
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_hidden()


def test_un_anterior_con_consulta_pendiente_no_impide_recuperar_el_cobro_en_pantalla(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cada consulta de recuperación puede avanzar aunque otra siga pendiente (RF-051, RF-052)."""
    _preparar(pagina, servidor)
    anterior = _cobrar(pagina, servidor)
    _nuevo(pagina)
    pantalla = _cobrar(pagina, servidor, monto="12")
    pendientes: list[Route] = []
    pagina.route(f"**/api/cobros/{anterior}", lambda ruta: pendientes.append(ruta), times=1)
    pagina.reload()
    expect(pagina.locator('[data-prueba="qr-monto"]')).to_have_text("$12.00")
    assert len(pendientes) == 1
    _nuevo(pagina)
    guardado = pagina.evaluate("() => JSON.parse(localStorage.getItem('pago_facil_escucha'))")
    assert guardado == {"en_pantalla": None, "anteriores": [anterior, pantalla]}
    pendientes[0].continue_()
    _esperar_canales(pagina, [anterior, pantalla])
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()


def test_al_recargar_los_identificadores_repetidos_solo_abren_un_canal(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un recuerdo repetido conserva un solo canal por cobro (RF-029, RF-051, QP-1)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    pagina.evaluate(
        """async (id) => {
          const { guardar } = await import("/js/memoria.js");
          guardar(id, [id, id]);
        }""",
        id_cobro,
    )
    with pagina.expect_response(f"**/api/cobros/{id_cobro}/eventos"):
        pagina.reload()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    assert len(canales(pagina)) == 1


def test_sin_almacenamiento_la_recarga_vuelve_al_teclado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Sin poder guardar, recargar vuelve al teclado vacío (spec 002, RF-076)."""
    pagina.add_init_script(
        """
        (() => {
          const fallo = () => {
            throw new Error("bloqueado");
          };
          Storage.prototype.getItem = fallo;
          Storage.prototype.setItem = fallo;
        })();
        """
    )
    _preparar(pagina, servidor)
    _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    pagina.reload()
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("")


def test_si_falla_la_escritura_se_descarta_el_recuerdo_desactualizado(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Con almacenamiento lleno, la recarga no revive un cobro que ya salió de pantalla (RF-076)."""
    _preparar(pagina, servidor)
    _cobrar(pagina, servidor)
    pagina.evaluate(
        """() => {
          Storage.prototype.setItem = () => { throw new Error("sin espacio"); };
        }"""
    )
    _nuevo(pagina)
    pagina.reload()
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")


def test_un_cobro_recuperado_que_ya_termino_su_ventana_no_se_escucha(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Pasada la ventana, el cobro no se muestra ni abre canal (spec 002, RF-051)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.fijar_hora(_HORA + 1_200)
    pagina.reload()
    pagina.wait_for_load_state("networkidle")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_hidden()
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_hidden()
    assert not _canal_abierto(pagina, id_cobro)


def test_un_cobro_anterior_recuperado_que_el_servidor_no_conoce_deja_de_escucharse(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un anterior que ya no existe no aparece (spec 002, RF-056)."""
    _preparar(pagina, servidor)
    id_anterior = _cobrar(pagina, servidor, monto="10", concepto="Agua")
    _esperar_abierto(pagina)
    _nuevo(pagina)
    id_pantalla = _cobrar(pagina, servidor, monto="20", concepto="Tacos")
    _esperar_abierto(pagina)
    servidor.olvidar(id_anterior)
    pagina.reload()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_hidden()
    _esperar_canales(pagina, [id_pantalla])
    assert not _canal_abierto(pagina, id_anterior)


def test_un_cobro_en_pantalla_recuperado_que_el_servidor_no_conoce_muestra_error(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si el cobro en pantalla ya no existe, se ve la vista Error (spec 002, RF-057)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.olvidar(id_cobro)
    pagina.reload()
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="error"]')).to_have_text(_MENSAJE_ERROR)


def test_lo_recordado_con_forma_de_codigo_no_se_ejecuta(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un id con forma de código no se ejecuta ni se pide (spec 002, RF-077, CE-015)."""
    dialogos: list[str] = []

    def guardar(dialogo: Dialog) -> None:
        dialogos.append(dialogo.message)
        dialogo.dismiss()

    pagina.on("dialog", guardar)
    pedidos: list[str] = []
    pagina.on("request", lambda peticion: pedidos.append(peticion.url))
    _preparar(pagina, servidor)
    pagina.evaluate(
        """() => {
          localStorage.setItem(
            "pago_facil_escucha",
            JSON.stringify({
              en_pantalla: "<script>alert(1)</script>",
              anteriores: ["<script>alert(1)</script>"],
            }),
          );
        }"""
    )
    pagina.reload()
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")
    assert dialogos == []
    assert all("<script>" not in unquote(url) for url in pedidos)
