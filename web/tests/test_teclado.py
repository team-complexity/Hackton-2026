"""Teclado del monto y pintura de Teclado y Generando QR (spec 002, T010)."""

from __future__ import annotations

import pytest
from conftest import abrir, tocar
from playwright.sync_api import Page, expect
from servidor_simulado import ServidorSimulado

_ESTADO = {
    "vista": "generando",
    "monto": "",
    "concepto": "",
    "mensaje": "",
    "en_pantalla": None,
    "accion_en_curso": None,
    "sonido_desbloqueado": False,
    "qr_reabierto": False,
}


@pytest.mark.only_browser("chromium")
def test_el_teclado_escribe_el_monto_con_dos_decimales_como_maximo(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Ignora el tercer decimal, el segundo punto y borrar quita uno (spec 002, RF-003, RF-004)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { aplicar_tecla } = await import("/js/teclado.js");
          return {
            tercer_decimal: aplicar_tecla("25.50", "1"),
            segundo_punto: aplicar_tecla("25.5", "punto"),
            borrar: aplicar_tecla("25.5", "borrar"),
            borrar_vacio: aplicar_tecla("", "borrar"),
          };
        }"""
    )
    assert resultado == {
        "tercer_decimal": "25.50",
        "segundo_punto": "25.5",
        "borrar": "25.",
        "borrar_vacio": "",
    }


@pytest.mark.only_browser("chromium")
def test_el_cero_inicial_se_reemplaza_y_el_punto_inicial_escribe_cero_punto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El 0 inicial se reemplaza y el punto inicial escribe 0. (spec 002, RF-066, RF-067)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { aplicar_tecla } = await import("/js/teclado.js");
          return {
            reemplaza: aplicar_tecla("0", "7"),
            cero: aplicar_tecla("0", "0"),
            punto_vacio: aplicar_tecla("", "punto"),
            punto_cero: aplicar_tecla("0", "punto"),
          };
        }"""
    )
    assert resultado == {
        "reemplaza": "7",
        "cero": "0",
        "punto_vacio": "0.",
        "punto_cero": "0.",
    }


@pytest.mark.only_browser("chromium")
def test_no_se_aceptan_mas_de_5_digitos_enteros(pagina: Page, servidor: ServidorSimulado) -> None:
    """El sexto dígito entero se ignora; el punto después de cinco sí entra (spec 002, RF-068)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { aplicar_tecla } = await import("/js/teclado.js");
          return {
            sexto: aplicar_tecla("12345", "6"),
            punto: aplicar_tecla("12345", "punto"),
          };
        }"""
    )
    assert resultado == {"sexto": "12345", "punto": "12345."}


@pytest.mark.only_browser("chromium")
def test_cobrar_y_monto_libre_se_activan_segun_el_monto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cobrar exige un monto mayor a 0; Monto libre es lo contrario (spec 002, RF-006, RF-065)."""
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async () => {
          const { cobrar_activo, monto_libre_activo } = await import("/js/teclado.js");
          const textos = ["", "0", "0.", "0.00", "0.01", "25."];
          return textos.map((texto) => ({
            texto,
            cobrar: cobrar_activo(texto),
            libre: monto_libre_activo(texto),
          }));
        }"""
    )
    esperados = {
        "": False,
        "0": False,
        "0.": False,
        "0.00": False,
        "0.01": True,
        "25.": True,
    }
    assert [fila["texto"] for fila in resultado] == list(esperados)
    for fila in resultado:
        assert fila["cobrar"] is esperados[fila["texto"]]
        assert fila["libre"] is not fila["cobrar"]


def test_la_vista_teclado_muestra_las_teclas_el_monto_y_el_concepto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Al abrir: teclado, $ y Cobrar apagado (spec 002, RF-001, RF-002, RF-005, RF-006)."""
    abrir(pagina, servidor)
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    for digito in range(10):
        expect(pagina.locator(f'[data-prueba="tecla-{digito}"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="tecla-punto"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="tecla-borrar"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_attribute("maxlength", "40")
    expect(pagina.locator('[data-prueba="cobrar"]')).to_be_disabled()


def test_la_vista_generando_qr_muestra_su_texto(pagina: Page, servidor: ServidorSimulado) -> None:
    """mostrar_generando deja Generando QR y oculta el teclado (spec 002, RF-010)."""
    abrir(pagina, servidor)
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    pagina.evaluate(
        """async (estado) => {
          const { mostrar_generando } = await import("/js/vistas.js");
          mostrar_generando(estado);
        }""",
        _ESTADO,
    )
    expect(pagina.locator('[data-prueba="vista-generando"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="generando"]')).to_have_text("Generando QR…")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_hidden()


def test_teclado_y_generando_caben_en_320_px(pagina: Page, servidor: ServidorSimulado) -> None:
    """Teclado y Generando QR caben en 320 px y la marca se ve (spec 002, RF-060, RF-061)."""
    abrir(pagina, servidor)
    alto = 640 if pagina.viewport_size is None else pagina.viewport_size["height"]
    pagina.set_viewport_size({"width": 320, "height": alto})

    def cabe() -> None:
        expect(pagina.locator('[data-prueba="marca"]')).to_be_visible()
        ancho = pagina.evaluate("() => document.documentElement.scrollWidth")
        assert ancho <= 320

    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    cabe()
    pagina.evaluate(
        """async (estado) => {
          const { mostrar_generando } = await import("/js/vistas.js");
          mostrar_generando(estado);
        }""",
        _ESTADO,
    )
    expect(pagina.locator('[data-prueba="vista-generando"]')).to_be_visible()
    cabe()


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def test_teclear_25_50_muestra_el_monto_en_grande(pagina: Page, servidor: ServidorSimulado) -> None:
    """2, 5, punto, 5 y 0 dejan $25.50 (spec 002, RF-001, RF-002)."""
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.50")


def test_el_teclado_en_pantalla_ignora_el_tercer_decimal_y_borra(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El tercer decimal no entra y borrar quita un carácter (spec 002, RF-003, RF-004)."""
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    tocar(pagina, "tecla-1")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.50")
    pagina.reload()
    _teclear(pagina, "25.5")
    tocar(pagina, "tecla-borrar")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$25.")


def test_el_teclado_en_pantalla_reemplaza_el_cero_y_escribe_cero_punto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """0 y 7 queda en $7; el punto inicial escribe $0. (spec 002, RF-066, RF-067)."""
    abrir(pagina, servidor)
    _teclear(pagina, "07")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$7")
    pagina.reload()
    tocar(pagina, "tecla-punto")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$0.")


def test_el_teclado_en_pantalla_no_acepta_un_sexto_digito_entero(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El sexto dígito entero se ignora (spec 002, RF-068)."""
    abrir(pagina, servidor)
    _teclear(pagina, "123456")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$12345")


def test_el_concepto_acepta_como_maximo_40_caracteres(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El teclado del celular no deja pasar de 40 caracteres (spec 002, RF-005)."""
    abrir(pagina, servidor)
    pagina.locator('[data-prueba="concepto"]').press_sequentially("a" * 45, delay=0)
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("a" * 40)


def test_cobrar_esta_desactivado_sin_monto(pagina: Page, servidor: ServidorSimulado) -> None:
    """Cobrar sigue apagado en $ y en $0., y se prende en $0.01 (spec 002, RF-006)."""
    abrir(pagina, servidor)
    monto = pagina.locator('[data-prueba="monto"]')
    cobrar = pagina.locator('[data-prueba="cobrar"]')
    expect(monto).to_have_text("$")
    expect(cobrar).to_be_disabled()
    _teclear(pagina, "0.")
    expect(monto).to_have_text("$0.")
    expect(cobrar).to_be_disabled()
    _teclear(pagina, "01")
    expect(monto).to_have_text("$0.01")
    expect(cobrar).to_be_enabled()
