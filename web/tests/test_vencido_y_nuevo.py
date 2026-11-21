"""QR vencido, fin de la escucha, Nuevo cobro y la vista Error (spec 002, T035, T036)."""

from __future__ import annotations

import pytest
from conftest import abrir, bloqueos, reloj, sonidos, tocar
from playwright.sync_api import Dialog, Locator, Page, expect
from servidor_simulado import ServidorSimulado

_HORA = 1_700_000_000
_MENSAJE_ERROR = (
    "Este cobro ya no se puede seguir. Revisa la app de tu banco para confirmar si llegó el pago."
)
_ESPERA = "Si el cliente ya pagó, aquí te avisamos"


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


def _visible(pagina: Page, nombre: str) -> Locator:
    return pagina.locator(f'[data-prueba="{nombre}"]').locator("visible=true")


def _consultas(servidor: ServidorSimulado, id_cobro: str) -> list[str]:
    ruta = f"/api/cobros/{id_cobro}"
    return [
        pedido
        for metodo, pedido, _cuerpo in servidor.peticiones
        if metodo == "GET" and pedido == ruta
    ]


def _rutas_del_cobro(servidor: ServidorSimulado, id_cobro: str) -> list[str]:
    return [pedido for _metodo, pedido, _cuerpo in servidor.peticiones if id_cobro in pedido]


def _assert_vencido(pagina: Page) -> None:
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vencido"]')).to_have_text("QR vencido")
    expect(pagina.locator('[data-prueba="qr"]')).to_be_hidden()
    expect(pagina.locator('[data-prueba="vencido-monto"]')).to_have_text("$25.50")
    expect(pagina.locator('[data-prueba="vencido-concepto"]')).to_have_text("Tacos")


def _preparar(pagina: Page, servidor: ServidorSimulado) -> None:
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)


def test_al_vencer_se_oculta_el_qr_y_se_ve_qr_vencido(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """A los 10 min, o con el aviso vencido, se oculta el QR (spec 002, RF-035, RF-036)."""
    _preparar(pagina, servidor)
    _cobrar(pagina, servidor)
    pagina.clock.fast_forward(600_000)
    _assert_vencido(pagina)

    servidor.fijar_hora(_HORA + 600)
    pagina.evaluate("() => localStorage.removeItem('pago_facil_escucha')")
    pagina.reload()
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    _assert_vencido(pagina)


def test_qr_vencido_dice_que_aun_se_avisa_el_pago(pagina: Page, servidor: ServidorSimulado) -> None:
    """Dentro de la ventana, el QR vencido avisa que el pago aún llega (spec 002, RF-038)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vencido-espera"]')).to_have_text(_ESPERA)


def test_un_pago_tardio_con_qr_vencido_suena_y_se_muestra(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cinco minutos después de vencer, el pago suena (spec 002, RF-039, CE-012)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    pagina.clock.fast_forward(600_000)
    _assert_vencido(pagina)
    pagina.clock.fast_forward(300_000)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    assert sonidos(pagina) == 1


def test_un_cobro_con_pagos_no_pasa_a_qr_vencido(pagina: Page, servidor: ServidorSimulado) -> None:
    """Si ya hubo un pago, al llegar a 0:00 se queda en Pago recibido (spec 002, RF-035)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    pagina.clock.fast_forward(600_000)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_hidden()


def test_al_recibir_fin_se_cierra_el_canal_y_no_se_reconecta(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """fin cierra el canal y no vuelve a pedir ese cobro (spec 002, RF-040)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "fin", dict(servidor.cobros[id_cobro]))
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes(id) && canal.readyState === 2;
        })""",
        arg=id_cobro,
        timeout=5_000,
    )
    hechas = len(_rutas_del_cobro(servidor, id_cobro))
    pagina.clock.run_for(20_000)
    assert len(_rutas_del_cobro(servidor, id_cobro)) == hechas


def test_al_terminar_la_ventana_desaparece_el_aviso_de_espera(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Tras fin, el aviso de que aún se puede pagar desaparece (spec 002, RF-038, RF-040)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vencido-espera"]')).to_be_visible()
    servidor.emitir(id_cobro, "fin", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vencido-espera"]')).to_be_hidden()


def test_si_la_consulta_muestra_que_paso_fin_ventana_termina_la_escucha(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si la consulta ya pasó fin_ventana, no se vuelve a consultar (spec 002, RF-040)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.cortar_canal(id_cobro, rechazar_con=503)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    servidor.fijar_hora(_HORA + 1_200)
    pagina.clock.run_for(3_000)
    hechas = len(_consultas(servidor, id_cobro))
    assert hechas >= 1
    pagina.clock.run_for(9_000)
    assert len(_consultas(servidor, id_cobro)) == hechas


def test_el_concepto_en_qr_vencido_se_muestra_como_texto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El concepto vencido se ve tal cual, sin ejecutarse (spec 002, RF-077)."""
    dialogos: list[str] = []

    def guardar(dialogo: Dialog) -> None:
        dialogos.append(dialogo.message)
        dialogo.dismiss()

    pagina.on("dialog", guardar)
    _preparar(pagina, servidor)
    concepto = "<script>alert(1)</script>"
    id_cobro = _cobrar(pagina, servidor, concepto)
    scripts = pagina.locator("#vistas script").count()
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vencido-concepto"]')).to_have_text(concepto)
    assert pagina.locator("#vistas script").count() == scripts
    assert dialogos == []


def test_qr_vencido_cabe_en_320_px(pagina: Page, servidor: ServidorSimulado) -> None:
    """QR vencido cabe en 320 px y la marca se ve (spec 002, RF-060, RF-061)."""
    alto = 640 if pagina.viewport_size is None else pagina.viewport_size["height"]
    pagina.set_viewport_size({"width": 320, "height": alto})
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="marca"]')).to_be_visible()
    assert pagina.evaluate("() => document.documentElement.scrollWidth") <= 320


@pytest.mark.parametrize("destino", ["qr", "vencido", "pagado", "error"])
def test_nuevo_cobro_vuelve_al_teclado_vacio_desde_cada_vista(
    pagina: Page, servidor: ServidorSimulado, destino: str
) -> None:
    """Nuevo cobro vuelve al teclado vacío desde cada vista (spec 002, RF-041, RF-042)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    if destino == "vencido":
        servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
        expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_visible()
    elif destino == "pagado":
        servidor.agregar_pago(id_cobro, 25.5)
        expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    elif destino == "error":
        servidor.olvidar(id_cobro)
        servidor.cortar_canal(id_cobro, rechazar_con=404)
        expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
        pagina.clock.run_for(3_000)
        expect(pagina.locator('[data-prueba="vista-error"]')).to_be_visible()
    _visible(pagina, "nuevo-cobro").click()
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("")


def test_si_el_servidor_ya_no_conoce_el_cobro_se_ve_la_vista_error(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un 404 del cobro en pantalla muestra la vista Error (spec 002, RF-057)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.olvidar(id_cobro)
    servidor.cortar_canal(id_cobro, rechazar_con=404)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    pagina.clock.run_for(3_000)
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="error"]')).to_have_text(_MENSAJE_ERROR)


def test_al_dejar_de_haber_cobros_en_escucha_se_suelta_la_pantalla(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Sin escuchas se suelta el bloqueo cuando llega fin (spec 002, RF-059)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    pagina.wait_for_function("() => window.__bloqueos_pedidos === 1")
    servidor.emitir(id_cobro, "fin", dict(servidor.cobros[id_cobro]))
    pagina.wait_for_function("() => window.__bloqueos_soltados === 1")
    assert bloqueos(pagina)["soltados"] == 1

    pagina.reload()
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    pagina.wait_for_function("() => window.__bloqueos_pedidos === 1")
    _visible(pagina, "nuevo-cobro").click()
    servidor.emitir(id_cobro, "fin", dict(servidor.cobros[id_cobro]))
    pagina.wait_for_function("() => window.__bloqueos_soltados === 1")
    assert bloqueos(pagina)["soltados"] == 1


def test_la_vista_error_cabe_en_320_px(pagina: Page, servidor: ServidorSimulado) -> None:
    """La vista Error cabe en 320 px y la marca se ve (spec 002, RF-060, RF-061)."""
    alto = 640 if pagina.viewport_size is None else pagina.viewport_size["height"]
    pagina.set_viewport_size({"width": 320, "height": alto})
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    servidor.olvidar(id_cobro)
    servidor.cortar_canal(id_cobro, rechazar_con=404)
    expect(pagina.locator('[data-prueba="reconectando"]')).to_be_visible()
    pagina.clock.run_for(3_000)
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="marca"]')).to_be_visible()
    assert pagina.evaluate("() => document.documentElement.scrollWidth") <= 320
