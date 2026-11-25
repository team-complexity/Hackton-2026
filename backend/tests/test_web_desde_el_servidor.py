"""La web servida por el mismo servidor (spec 003, RF-024, RF-029)."""

from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from app.config import Configuracion
from app.main import crear_app
from app.pey import ClientePey
from app.reloj import RelojFalso
from tests.conftest import BASE_PEY_DE_PRUEBA, LLAVE_FALSA, SECRETO_FALSO, PeySimulado


def _preparar_web(carpeta: Path) -> None:
    carpeta.joinpath("index.html").write_text("<h1>PAGO FÁCIL</h1>", encoding="utf-8")
    carpeta.joinpath("config.js").write_text(
        "window.PAGO_FACIL = { servidor: '' };", encoding="utf-8"
    )


def _cliente(reloj: RelojFalso, carpeta_web: str | None = None) -> TestClient:
    """App de prueba con pey simulado. `carpeta_web` vacía no entrega la web."""
    datos: dict[str, object] = {
        "_env_file": None,
        "pey_api_key": LLAVE_FALSA,
        "pey_webhook_secret": SECRETO_FALSO,
    }
    if carpeta_web is not None:
        datos["carpeta_web"] = carpeta_web
    config = Configuracion(**datos)
    http = httpx.AsyncClient(transport=httpx.MockTransport(PeySimulado()))
    cliente_pey = ClientePey(BASE_PEY_DE_PRUEBA, LLAVE_FALSA, http)
    return TestClient(crear_app(config, cliente_pey, reloj, tareas_en_segundo_plano=False))


def test_con_carpeta_web_el_servidor_entrega_la_web(tmp_path: Path) -> None:
    """Con carpeta_web, `/` y `/config.js` salen de esa carpeta (spec 003, RF-024)."""
    _preparar_web(tmp_path)
    reloj = RelojFalso(inicio=1_794_700_000)
    with _cliente(reloj, str(tmp_path)) as cliente:
        pagina = cliente.get("/")
        config = cliente.get("/config.js")
    assert pagina.status_code == 200
    assert pagina.headers["content-type"].startswith("text/html")
    assert "PAGO FÁCIL" in pagina.text
    assert config.status_code == 200


def test_las_rutas_del_api_mandan_sobre_la_web(tmp_path: Path) -> None:
    """La salud y el API siguen respondiendo aunque la web esté montada (spec 003, RF-029)."""
    _preparar_web(tmp_path)
    reloj = RelojFalso(inicio=1_794_700_000)
    with _cliente(reloj, str(tmp_path)) as cliente:
        salud = cliente.get("/salud")
        faltante = cliente.get("/api/cobros/noexiste")
    assert salud.status_code == 200
    assert salud.json()["estado"] == "ok"
    assert faltante.status_code == 404
    assert faltante.json() == {"detail": "Ese cobro no existe"}


def test_sin_carpeta_web_el_servidor_no_entrega_la_web() -> None:
    """Sin carpeta_web, `/` no es la web (spec 003, RF-024)."""
    reloj = RelojFalso(inicio=1_794_700_000)
    with _cliente(reloj) as cliente:
        respuesta = cliente.get("/")
    assert respuesta.status_code == 404


def test_carpeta_web_esta_vacia_por_defecto() -> None:
    """Las pruebas del servidor no entregan la web (spec 003, DP-21, R-12)."""
    assert Configuracion(_env_file=None).carpeta_web == ""
