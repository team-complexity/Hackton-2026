"""Páginas de Pixel 7 e iPhone 13, y el servidor simulado (spec 002, plan §7)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from playwright.sync_api import Page, Playwright
from servidor_simulado import ServidorSimulado

# Se inyecta antes de la página. Cuenta sonido, vibración, bloqueo y canales (plan §7, QT-3).
_ARRANQUE = """
(() => {
  window.__sonidos = [];
  window.__vibraciones = [];
  window.__bloqueos_pedidos = 0;
  window.__bloqueos_soltados = 0;
  window.__canales = [];

  HTMLMediaElement.prototype.play = function () {
    window.__sonidos.push({
      volume: this.volume,
      muted: this.muted,
      src: this.src,
    });
    if (this.volume > 0 && !this.muted && window.__rechazar_sonido) {
      return Promise.reject(new DOMException("Reproducción bloqueada", "NotAllowedError"));
    }
    return Promise.resolve();
  };

  if (typeof navigator.vibrate === "function") {
    navigator.vibrate = (patron) => {
      window.__vibraciones.push(patron);
      return true;
    };
  }

  const sentinela = {
    release() {
      window.__bloqueos_soltados += 1;
      return Promise.resolve();
    },
  };
  try {
    Object.defineProperty(navigator, "wakeLock", {
      configurable: true,
      value: {
        request() {
          window.__bloqueos_pedidos += 1;
          return Promise.resolve(sentinela);
        },
      },
    });
  } catch (_error) {
    // Algunos motores no dejan reemplazar wakeLock.
  }

  const Original = window.EventSource;
  function EventSourceEnvuelto(url, opciones) {
    const canal = new Original(url, opciones);
    window.__canales.push(canal);
    return canal;
  }
  EventSourceEnvuelto.prototype = Original.prototype;
  EventSourceEnvuelto.CONNECTING = Original.CONNECTING;
  EventSourceEnvuelto.OPEN = Original.OPEN;
  EventSourceEnvuelto.CLOSED = Original.CLOSED;
  window.EventSource = EventSourceEnvuelto;
})();
"""


@pytest.fixture(scope="session")
def browser_context_args(
    browser_context_args: dict[str, Any],
    browser_name: str,
    playwright: Playwright,
) -> dict[str, Any]:
    """Pixel 7 en Chromium e iPhone 13 en WebKit (spec 002, plan §7).

    `default_browser_type` no se pasa: el navegador ya lo eligió pytest-playwright.
    El alcance es de sesión porque así está fijada la fixture del plugin (QT-3).
    """
    dispositivos = {"chromium": "Pixel 7", "webkit": "iPhone 13"}
    argumentos = {**browser_context_args, **playwright.devices[dispositivos[browser_name]]}
    argumentos.pop("default_browser_type", None)
    return argumentos


@pytest.fixture(scope="session")
def _servidor_arrancado() -> Iterator[ServidorSimulado]:
    """Arranca el hilo del simulado una vez por sesión (spec 002, R-2)."""
    servidor = ServidorSimulado()
    servidor.arrancar()
    yield servidor
    servidor.detener()


@pytest.fixture
def servidor(_servidor_arrancado: ServidorSimulado) -> ServidorSimulado:
    """Deja el simulado como al principio antes de cada prueba (spec 002, R-2)."""
    _servidor_arrancado.reiniciar()
    return _servidor_arrancado


@pytest.fixture
def pagina(page: Page) -> Page:
    """La página del celular con los contadores ya instalados (spec 002, plan §7)."""
    page.add_init_script(_ARRANQUE)
    return page


def abrir(pagina: Page, servidor: ServidorSimulado) -> None:
    """Abre la web servida por el simulado, en su mismo origen (spec 002, R-2)."""
    pagina.goto(f"{servidor.origen}/")


def tocar(pagina: Page, *nombres: str) -> None:
    """Pulsa cada control por su `data-prueba`, en el orden recibido (spec 002, plan §7)."""
    for nombre in nombres:
        pagina.locator(f'[data-prueba="{nombre}"]').click()


def sonidos(pagina: Page) -> int:
    """Cuenta play con volumen mayor a 0 y sin muted (spec 002, plan §7)."""
    return int(
        pagina.evaluate(
            """() => window.__sonidos.filter((sonido) => {
              return sonido.volume > 0 && !sonido.muted;
            }).length"""
        )
    )


def vibraciones(pagina: Page) -> list[object]:
    """Devuelve cada patrón pasado a navigator.vibrate (spec 002, plan §7)."""
    return list(pagina.evaluate("() => window.__vibraciones"))


def bloqueos(pagina: Page) -> dict[str, int]:
    """Cuenta pedidos y sueltas del bloqueo de pantalla (spec 002, plan §7)."""
    return dict(
        pagina.evaluate(
            """() => ({
              pedidos: window.__bloqueos_pedidos,
              soltados: window.__bloqueos_soltados,
            })"""
        )
    )


def canales(pagina: Page) -> list[dict[str, str]]:
    """Lista los EventSource con su URL y CONNECTING, OPEN o CLOSED (spec 002, QT-3)."""
    return list(
        pagina.evaluate(
            """() => {
              const nombres = {0: "CONNECTING", 1: "OPEN", 2: "CLOSED"};
              return window.__canales.map((canal) => ({
                url: canal.url,
                estado: nombres[canal.readyState],
              }));
            }"""
        )
    )


def reloj(pagina: Page, hora: float | str | int) -> None:
    """Congela el reloj de la página. Tras install el tiempo seguiría solo (QT-3).

    Un número es en segundos Unix (Playwright de Python lo multiplica por 1000), igual que
    `creado_en` y `hora_servidor`; no son milisegundos como en JavaScript.
    """
    pagina.clock.install(time=hora)
    pagina.clock.pause_at(hora)
