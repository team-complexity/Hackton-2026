"""Monto libre, el número de pago y Mostrar QR otra vez (spec 002, T044, T045)."""

from __future__ import annotations

import time

from conftest import abrir, reloj, sonidos, tocar
from playwright.sync_api import Page, expect
from servidor_simulado import ServidorSimulado

_HORA = 1_700_000_000


def _teclear(pagina: Page, monto: str) -> None:
    nombres = ["tecla-punto" if caracter == "." else f"tecla-{caracter}" for caracter in monto]
    tocar(pagina, *nombres)


def _ultimo_id(servidor: ServidorSimulado) -> str:
    ids = list(servidor.cobros)
    assert ids
    return str(ids[-1])


def _esperar_abierto(pagina: Page) -> None:
    pagina.wait_for_function(
        "() => window.__canales.some((canal) => canal.readyState === 1)",
        timeout=5_000,
    )


def _posts(servidor: ServidorSimulado) -> list[tuple[str, str, object]]:
    return [item for item in servidor.peticiones if item[0] == "POST" and item[1] == "/api/cobros"]


def test_monto_libre_solo_esta_activo_sin_monto_y_crea_un_cobro_sin_monto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Monto libre solo actúa sin monto y el QR lo dice así (spec 002, RF-007, RF-008)."""
    abrir(pagina, servidor)
    libre = pagina.locator('[data-prueba="monto-libre"]')
    expect(libre).to_be_enabled()
    _teclear(pagina, "0.")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$0.")
    expect(libre).to_be_enabled()
    pagina.reload()
    _teclear(pagina, "25.50")
    expect(pagina.locator('[data-prueba="monto-libre"]')).to_be_disabled()
    pagina.reload()
    pagina.locator('[data-prueba="concepto"]').fill("Propina")
    tocar(pagina, "monto-libre")
    expect(pagina.locator('[data-prueba="qr-monto"]')).to_have_text("Monto libre")
    expect(pagina.locator('[data-prueba="qr-concepto"]')).to_have_text("Propina")
    assert ("POST", "/api/cobros", {"monto": None, "concepto": "Propina"}) in _posts(servidor)


def test_mientras_se_crea_un_monto_libre_se_ignoran_otros_toques(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Mientras se crea, otro toque no pide un segundo cobro (spec 002, RF-011)."""
    abrir(pagina, servidor)
    pagina.locator('[data-prueba="concepto"]').fill("Propina")
    servidor.responder_crear(demora=2)
    tocar(pagina, "monto-libre")
    expect(pagina.locator('[data-prueba="vista-generando"]')).to_be_visible()
    pagina.locator('[data-prueba="monto-libre"]').evaluate("nodo => nodo.click()")
    pagina.locator('[data-prueba="cobrar"]').evaluate("nodo => nodo.click()")
    limite = time.monotonic() + 5
    while time.monotonic() < limite and len(_posts(servidor)) < 1:
        time.sleep(0.05)
    assert len(_posts(servidor)) == 1
    time.sleep(0.3)
    assert len(_posts(servidor)) == 1


def test_un_monto_libre_vencido_muestra_monto_libre(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El QR vencido de un monto libre sigue diciendo Monto libre (spec 002, RF-037)."""
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)
    pagina.locator('[data-prueba="concepto"]').fill("Propina")
    tocar(pagina, "monto-libre")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.emitir(id_cobro, "vencido", dict(servidor.cobros[id_cobro]))
    expect(pagina.locator('[data-prueba="vencido-monto"]')).to_have_text("Monto libre")


def test_un_monto_libre_pagado_muestra_lo_que_pago_el_cliente_sin_monto_distinto(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un pago de monto libre muestra lo recibido, sin monto distinto (spec 002, RF-023)."""
    abrir(pagina, servidor)
    pagina.locator('[data-prueba="concepto"]').fill("Propina")
    tocar(pagina, "monto-libre")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 12)
    expect(pagina.locator('[data-prueba="pagado-monto"]')).to_have_text("$12.00")
    expect(pagina.locator('[data-prueba="pagado-distinto"]')).to_be_hidden()


def test_el_segundo_pago_muestra_pago_2_y_el_total(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Desde el segundo pago se ven el número y el total (spec 002, RF-027)."""
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="pagado-numero"]')).to_be_hidden()
    expect(pagina.locator('[data-prueba="pagado-total"]')).to_be_hidden()
    servidor.agregar_pago(id_cobro, 10)
    expect(pagina.locator('[data-prueba="pagado-numero"]')).to_have_text("Pago 2")
    expect(pagina.locator('[data-prueba="pagado-total"]')).to_contain_text("$35.50")
    # Sin rótulo, "$35.50" bajo "$10.00" no dice que es la suma de los dos pagos (RF-027).
    expect(pagina.locator('[data-prueba="pagado-total"]')).to_have_text("Total recibido: $35.50")


def test_mostrar_qr_otra_vez_vuelve_al_qr_mientras_siga_vigente(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Mostrar QR otra vez vuelve al QR y desaparece al vencer (spec 002, RF-069)."""
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    otra = pagina.locator('[data-prueba="mostrar-qr"]')
    expect(otra).to_be_visible()
    otra.click()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="cuenta"]')).to_be_visible()

    pagina.evaluate("() => localStorage.removeItem('pago_facil_escucha')")
    pagina.reload()
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="mostrar-qr"]')).to_be_visible()
    pagina.clock.fast_forward(600_000)
    expect(pagina.locator('[data-prueba="mostrar-qr"]')).to_be_hidden()
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()


def test_si_el_qr_que_se_volvio_a_mostrar_vence_vuelve_pago_recibido(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si el QR reabierto vence, vuelve Pago recibido y no QR vencido (spec 002, RF-071)."""
    reloj(pagina, _HORA)
    servidor.fijar_hora(_HORA)
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    pagina.locator('[data-prueba="mostrar-qr"]').click()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    pagina.clock.fast_forward(600_000)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-vencido"]')).to_be_hidden()


def test_un_pago_con_el_qr_reabierto_suena_y_vuelve_a_pago_recibido(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un pago con el QR reabierto suena y vuelve a Pago recibido (spec 002, RF-026, RF-071)."""
    abrir(pagina, servidor)
    _teclear(pagina, "25.50")
    pagina.locator('[data-prueba="concepto"]').fill("Tacos")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    id_cobro = _ultimo_id(servidor)
    _esperar_abierto(pagina)
    servidor.agregar_pago(id_cobro, 25.5)
    pagina.locator('[data-prueba="mostrar-qr"]').click()
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    servidor.agregar_pago(id_cobro, 10)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="pagado-numero"]')).to_have_text("Pago 2")
    assert sonidos(pagina) == 2
