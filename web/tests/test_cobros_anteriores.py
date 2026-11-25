"""cancelar_cobro, cobros anteriores y Cancelar cobro (spec 002, T013, T049, T050)."""

from __future__ import annotations

import json
import time
import urllib.request

import pytest
from conftest import abrir, bloqueos, canales, reloj, sonidos, tocar, vibraciones
from playwright.sync_api import Locator, Page, Route, expect
from servidor_simulado import ServidorSimulado

_MENSAJE_SIN_CONEXION = "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo."
_DETALLE_NO_EXISTE = "Ese cobro no existe"
_DETALLE_NO_CANCELA = "Solo se puede cancelar un cobro que todavía no se paga ni vence"


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
def test_cancelar_cobro_200_devuelve_el_cobro(pagina: Page, servidor: ServidorSimulado) -> None:
    """Cancelar pide POST …/cancelar y devuelve el cobro (spec 002, RF-047)."""
    cobro = _guardar_cobro(servidor)
    identificador = str(cobro["id"])
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async (id) => {
          const { cancelar_cobro } = await import("/js/servidor.js");
          return cancelar_cobro(id);
        }""",
        identificador,
    )
    ruta = f"/api/cobros/{identificador}/cancelar"
    assert ("POST", ruta, None) in servidor.peticiones
    assert resultado["cobro"]["id"] == identificador
    assert resultado["cobro"]["estado"] == "cancelado"


@pytest.mark.only_browser("chromium")
@pytest.mark.parametrize(
    ("codigo", "detalle"),
    [
        (404, _DETALLE_NO_EXISTE),
        (409, _DETALLE_NO_CANCELA),
    ],
)
def test_cancelar_cobro_rechazado_devuelve_el_detail(
    pagina: Page, servidor: ServidorSimulado, codigo: int, detalle: str
) -> None:
    """404 y 409 devuelven el detail del servidor (spec 002, RF-050)."""
    if codigo == 404:
        identificador = "NoExiste123"
    else:
        cobro = _guardar_cobro(servidor)
        identificador = str(cobro["id"])
        servidor.agregar_pago(identificador, 10)
    abrir(pagina, servidor)
    resultado = pagina.evaluate(
        """async (id) => {
          const { cancelar_cobro } = await import("/js/servidor.js");
          return cancelar_cobro(id);
        }""",
        identificador,
    )
    assert resultado == {"mensaje": detalle}


@pytest.mark.only_browser("chromium")
def test_cancelar_cobro_con_fallo_de_red_dice_sin_conexion(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Si cancelar se corta, el mensaje pide revisar la conexión (spec 002, RF-050)."""
    cobro = _guardar_cobro(servidor)
    abrir(pagina, servidor)
    pagina.route("**/api/cobros/**", _abortar)
    resultado = pagina.evaluate(
        """async (id) => {
          const { cancelar_cobro } = await import("/js/servidor.js");
          return cancelar_cobro(id);
        }""",
        cobro["id"],
    )
    assert resultado == {"mensaje": _MENSAJE_SIN_CONEXION}


_HORA = 1_700_000_000


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


def _consultas(servidor: ServidorSimulado, id_cobro: str) -> int:
    ruta = f"/api/cobros/{id_cobro}"
    return sum(
        1 for metodo, pedido, _cuerpo in servidor.peticiones if metodo == "GET" and pedido == ruta
    )


def _cancelaciones(servidor: ServidorSimulado, id_cobro: str) -> int:
    ruta = f"/api/cobros/{id_cobro}/cancelar"
    return sum(
        1 for metodo, pedido, _cuerpo in servidor.peticiones if metodo == "POST" and pedido == ruta
    )


def _esperar_consultas(servidor: ServidorSimulado, id_cobro: str, minimo: int) -> None:
    limite = time.monotonic() + 5
    while time.monotonic() < limite and _consultas(servidor, id_cobro) < minimo:
        time.sleep(0.05)
    assert _consultas(servidor, id_cobro) >= minimo


def _cobros_en_escucha(
    pagina: Page, servidor: ServidorSimulado, cantidad: int, dejar_en_pantalla: bool
) -> list[str]:
    ids: list[str] = []
    for indice in range(cantidad):
        ids.append(_cobrar(pagina, servidor, monto=str(indice + 1), concepto=f"Cobro {indice + 1}"))
        _esperar_abierto(pagina)
        if indice < cantidad - 1 or not dejar_en_pantalla:
            _nuevo(pagina)
    return ids


def test_un_pago_a_un_cobro_anterior_suena_y_avisa_sin_borrar_lo_tecleado(
    pagina: Page, servidor: ServidorSimulado, browser_name: str
) -> None:
    """Un pago anterior suena y avisa sin borrar el monto (spec 002, RF-044, RF-045, CE-013)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor, monto="30", concepto="Refresco")
    _esperar_abierto(pagina)
    _nuevo(pagina)
    _teclear(pagina, "12")
    servidor.agregar_pago(id_cobro, 30)
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_be_visible()
    expect(aviso).to_contain_text("$30.00")
    expect(aviso).to_contain_text("Refresco")
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$12")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    assert sonidos(pagina) == 1
    if browser_name == "chromium":
        assert vibraciones(pagina) == [[200, 100, 200]]


def test_el_aviso_de_un_cobro_anterior_se_cierra_al_tocarlo(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El aviso de un cobro anterior se cierra al tocarlo (spec 002, RF-045)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor, monto="30", concepto="Refresco")
    _esperar_abierto(pagina)
    _nuevo(pagina)
    _teclear(pagina, "12")
    servidor.agregar_pago(id_cobro, 30)
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_be_visible()
    aviso.click()
    expect(aviso).to_be_hidden()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$12")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()


def test_el_aviso_de_un_cobro_anterior_se_ve_sin_desplazar_la_pantalla_y_dice_que_es(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """El aviso queda a la vista y dice qué es (spec 002, RF-045, RF-061)."""
    _preparar(pagina, servidor)
    pagina.set_viewport_size({"width": 320, "height": 568})
    id_anterior = _cobrar(pagina, servidor, monto="30", concepto="Refresco")
    _esperar_abierto(pagina)
    _nuevo(pagina)
    id_actual = _cobrar(pagina, servidor, monto="12", concepto="Tacos")
    _esperar_canales(pagina, [id_anterior, id_actual])
    servidor.agregar_pago(id_actual, 12)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    servidor.agregar_pago(id_anterior, 30)
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_be_visible()
    # Sin rótulo, "$30.00 Refresco" no dice que es el pago de otro cobro (RF-045).
    expect(aviso).to_have_text("Pago de un cobro anterior: $30.00 Refresco")
    caja = aviso.bounding_box()
    assert caja is not None
    assert caja["y"] >= 0
    assert caja["y"] + caja["height"] <= 568
    assert pagina.evaluate("() => document.documentElement.scrollWidth") <= 320


def test_un_cobro_anterior_deja_de_escucharse_al_terminar_su_ventana(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Al llegar fin, el canal del cobro anterior queda cerrado (spec 002, RF-040)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    _nuevo(pagina)
    assert _canal_abierto(pagina, id_cobro)
    servidor.emitir(id_cobro, "fin", dict(servidor.cobros[id_cobro]))
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes("/" + id + "/eventos") && canal.readyState === 2;
        })""",
        arg=id_cobro,
        timeout=10_000,
    )
    assert not _canal_abierto(pagina, id_cobro)


def test_un_cobro_anterior_que_el_servidor_ya_no_conoce_deja_de_escucharse(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un 404 de un cobro anterior cierra su escucha sin la vista Error (spec 002, RF-056)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    _nuevo(pagina)
    assert _canal_abierto(pagina, id_cobro)
    servidor.olvidar(id_cobro)
    servidor.cortar_canal(id_cobro, rechazar_con=404)
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes("/" + id + "/eventos") && canal.readyState === 2;
        })""",
        arg=id_cobro,
        timeout=10_000,
    )
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_hidden()
    pagina.clock.run_for(3_000)
    _esperar_consultas(servidor, id_cobro, 1)
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="vista-error"]')).to_be_hidden()
    pagina.wait_for_function(
        """(id) => window.__canales.some((canal) => {
          return canal.url.includes("/" + id + "/eventos") && canal.readyState === 2;
        })""",
        arg=id_cobro,
        timeout=10_000,
    )


def test_con_mas_de_3_cobros_en_escucha_solo_3_usan_canal_y_el_resto_se_consulta(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Solo el cobro en pantalla y dos anteriores tienen canal (spec 002, QP-1, RF-030)."""
    _preparar(pagina, servidor)
    ids = _cobros_en_escucha(pagina, servidor, 5, dejar_en_pantalla=True)
    pantalla, reciente, siguiente = ids[4], ids[3], ids[2]
    sin_canal = (ids[1], ids[0])
    _esperar_canales(pagina, [pantalla, reciente, siguiente])
    assert _consultas(servidor, sin_canal[0]) == 0
    assert _consultas(servidor, sin_canal[1]) == 0
    servidor.agregar_pago(sin_canal[0], 1)
    pagina.clock.run_for(3_000)
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_be_visible()
    expect(aviso).to_contain_text("$1.00")
    assert sonidos(pagina) == 1
    _esperar_consultas(servidor, sin_canal[0], 1)
    _esperar_consultas(servidor, sin_canal[1], 1)
    assert _consultas(servidor, pantalla) == 0
    base = _consultas(servidor, sin_canal[1])
    pagina.clock.run_for(3_000)
    _esperar_consultas(servidor, sin_canal[1], base + 1)


def test_con_muchos_cobros_en_escucha_se_puede_crear_otro_cobro(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Con cinco cobros en escucha, Cobrar sigue llegando al QR (spec 002, QP-1, RF-009)."""
    _preparar(pagina, servidor)
    _cobros_en_escucha(pagina, servidor, 5, dejar_en_pantalla=False)
    _teclear(pagina, "10")
    tocar(pagina, "cobrar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()


def test_al_terminar_un_canal_pasa_al_anterior_mas_reciente(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Al cerrarse un canal, lo toma el anterior más reciente que no lo tenía (spec 002, QP-1)."""
    _preparar(pagina, servidor)
    ids = _cobros_en_escucha(pagina, servidor, 5, dejar_en_pantalla=True)
    _esperar_canales(pagina, [ids[4], ids[3], ids[2]])
    servidor.emitir(ids[3], "fin", dict(servidor.cobros[ids[3]]))
    _esperar_canales(pagina, [ids[4], ids[2], ids[1]])


def test_la_pantalla_sigue_encendida_mientras_haya_cobros_anteriores(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Nuevo cobro no suelta la pantalla; fin, sí (spec 002, RF-058, RF-059)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    pagina.wait_for_function("() => window.__bloqueos_pedidos === 1")
    _nuevo(pagina)
    assert bloqueos(pagina)["soltados"] == 0
    assert _canal_abierto(pagina, id_cobro)
    servidor.emitir(id_cobro, "fin", dict(servidor.cobros[id_cobro]))
    pagina.wait_for_function("() => window.__bloqueos_soltados === 1", timeout=10_000)
    assert bloqueos(pagina)["soltados"] == 1


def test_cancelar_cobro_solo_aparece_con_el_cobro_pendiente(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cancelar cobro se ve en el QR pendiente y no al reabrir uno pagado (spec 002, RF-046)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    expect(pagina.locator('[data-prueba="cancelar"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="cancelar"]')).to_have_text("Cancelar cobro")
    servidor.agregar_pago(id_cobro, 25.5)
    expect(pagina.locator('[data-prueba="vista-pagado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="mostrar-qr"]')).to_be_visible()
    tocar(pagina, "mostrar-qr")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="cancelar"]')).to_be_hidden()


def test_cancelar_un_cobro_pendiente_vuelve_al_teclado_y_lo_sigue_escuchando(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Cancelar confirmado vacía el teclado y deja el canal (spec 002, RF-047, RF-048, RF-049)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    expect(pagina.locator('[data-prueba="cancelar"]')).to_be_visible()
    tocar(pagina, "cancelar")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("")
    assert _cancelaciones(servidor, id_cobro) == 1
    assert _canal_abierto(pagina, id_cobro)


def test_un_pago_a_un_cobro_cancelado_suena_y_avisa(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un pago al QR cancelado suena y muestra el aviso (spec 002, RF-044, RF-049)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor, monto="30", concepto="Refresco")
    _esperar_abierto(pagina)
    expect(pagina.locator('[data-prueba="cancelar"]')).to_be_visible()
    tocar(pagina, "cancelar")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    servidor.agregar_pago(id_cobro, 30)
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_be_visible()
    expect(aviso).to_contain_text("$30.00")
    expect(aviso).to_contain_text("Refresco")
    assert sonidos(pagina) == 1


@pytest.mark.parametrize("caso", ["404", "409", "red"])
def test_si_el_servidor_rechaza_la_cancelacion_se_queda_el_cobro_con_su_mensaje(
    pagina: Page, servidor: ServidorSimulado, caso: str
) -> None:
    """Si cancelar falla, el QR sigue con el mensaje (spec 002, RF-050)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor)
    _esperar_abierto(pagina)
    if caso == "404":
        servidor.olvidar(id_cobro)
        esperado = _DETALLE_NO_EXISTE
    elif caso == "409":
        servidor.agregar_pago(id_cobro, 10, avisar=False)
        esperado = _DETALLE_NO_CANCELA
    else:
        pagina.route("**/api/cobros/*/cancelar", _abortar)
        esperado = _MENSAJE_SIN_CONEXION
    expect(pagina.locator('[data-prueba="cancelar"]')).to_be_visible()
    tocar(pagina, "cancelar")
    expect(pagina.locator('[data-prueba="vista-qr"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="mensaje-cancelar"]')).to_have_text(esperado)


def test_mientras_se_cancela_se_ve_cancelando_y_se_ignora_otro_toque(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Se ve Cancelando… y un segundo toque no se repite (spec 002, RF-072, RF-073)."""
    abrir(pagina, servidor)
    servidor.demorar_cancelar(2)
    id_cobro = _cobrar(pagina, servidor)
    expect(pagina.locator('[data-prueba="cancelar"]')).to_be_visible()
    tocar(pagina, "cancelar")
    expect(pagina.locator('[data-prueba="cancelar"]')).to_have_text("Cancelando…")
    pagina.locator('[data-prueba="cancelar"]').evaluate("nodo => nodo.click()")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible(timeout=8_000)
    assert _cancelaciones(servidor, id_cobro) == 1


def test_un_cancelado_que_llega_por_el_canal_se_trata_como_propio(
    pagina: Page, servidor: ServidorSimulado
) -> None:
    """Un cancelado del canal vacía el teclado y sigue la escucha (spec 002, RF-074)."""
    _preparar(pagina, servidor)
    id_cobro = _cobrar(pagina, servidor, monto="30", concepto="Refresco")
    _esperar_abierto(pagina)
    cobro = dict(servidor.cobros[id_cobro])
    cobro["estado"] = "cancelado"
    servidor.emitir(id_cobro, "cancelado", cobro)
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
    expect(pagina.locator('[data-prueba="monto"]')).to_have_text("$")
    expect(pagina.locator('[data-prueba="concepto"]')).to_have_value("")
    assert _canal_abierto(pagina, id_cobro)
    servidor.agregar_pago(id_cobro, 30)
    aviso = pagina.locator('[data-prueba="aviso-anterior"]')
    expect(aviso).to_be_visible()
    expect(aviso).to_contain_text("Refresco")
    expect(pagina.locator('[data-prueba="vista-teclado"]')).to_be_visible()
