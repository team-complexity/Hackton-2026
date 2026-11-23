"""Pruebas de protección de la demo (spec 001, RF-034, RF-035, RF-041)."""

import httpx
from fastapi.testclient import TestClient

from app.main import crear_app
from app.pey import ClientePey
from tests.conftest import BASE_PEY_DE_PRUEBA

MENSAJE_LIMITE = "Demasiados cobros seguidos. Espera un minuto."
MENSAJE_CANALES = "Tienes demasiadas pantallas abiertas. Cierra otras e intenta de nuevo."


def _cliente(configuracion, pey, reloj, **cambios) -> TestClient:
    """App de prueba con el límite o los proxies que pide el caso."""
    config = configuracion.model_copy(update=cambios) if cambios else configuracion
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(
        BASE_PEY_DE_PRUEBA,
        config.pey_api_key.get_secret_value(),
        http,
    )
    return TestClient(crear_app(config, cliente_pey, reloj))


def test_limite_de_cobros_por_ip(configuracion, pey, reloj) -> None:
    """Diez cobros pasan; el 11.º no llama a pey. A los 60 s vuelve a pasar (RF-034)."""
    with _cliente(configuracion, pey, reloj, limite_cobros_por_minuto=10) as cliente:
        invalido = cliente.post("/api/cobros", json={"monto": -1})
        assert invalido.status_code == 422
        estados = [
            cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).status_code
            for _ in range(10)
        ]
        assert estados == [201] * 10
        llamadas = len(pey.solicitudes)
        exceso = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
        assert exceso.status_code == 429
        assert exceso.json()["detail"] == MENSAJE_LIMITE
        assert len(pey.solicitudes) == llamadas
        reloj.avanzar(60)
        otra_vez = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"})
        assert otra_vez.status_code == 201


def test_el_limite_usa_la_ip_real_detras_del_proxy(configuracion, pey, reloj) -> None:
    """X-Forwarded-For solo cuenta si el proxy es de confianza (RF-034, R-5)."""
    cabecera_a = {"X-Forwarded-For": "203.0.113.1"}
    cabecera_b = {"X-Forwarded-For": "203.0.113.2"}
    cuerpo = {"monto": 1, "concepto": "Tacos"}
    with _cliente(configuracion, pey, reloj, limite_cobros_por_minuto=1) as cliente:
        primera = cliente.post("/api/cobros", json=cuerpo, headers=cabecera_a)
        segunda = cliente.post("/api/cobros", json=cuerpo, headers=cabecera_b)
        assert primera.status_code == 201
        assert segunda.status_code == 429

    with _cliente(
        configuracion,
        pey,
        reloj,
        limite_cobros_por_minuto=1,
        proxies_confiables="testclient",
    ) as cliente:
        una = cliente.post("/api/cobros", json=cuerpo, headers=cabecera_a)
        otra = cliente.post("/api/cobros", json=cuerpo, headers=cabecera_b)
        repeticion = cliente.post("/api/cobros", json=cuerpo, headers=cabecera_a)
        assert una.status_code == 201
        assert otra.status_code == 201
        assert repeticion.status_code == 429
        assert repeticion.json()["detail"] == MENSAJE_LIMITE


def test_una_ip_no_puede_abrir_mas_de_10_canales(cliente) -> None:
    """Diez canales por IP; el siguiente se rechaza y liberar abre lugar (RF-041)."""
    from app.eventos import LimiteDeCanales

    limite = LimiteDeCanales(10)
    assert all(limite.ocupar("203.0.113.9") for _ in range(10))
    assert limite.ocupar("203.0.113.9") is False
    assert limite.ocupar("203.0.113.10") is True
    limite.liberar("203.0.113.9")
    assert limite.ocupar("203.0.113.9") is True

    canales = cliente.app.state.limite_canales
    for _ in range(10):
        assert canales.ocupar("testclient")
    cobro = cliente.post("/api/cobros", json={"monto": 1, "concepto": "Tacos"}).json()
    rechazo = cliente.get(f"/api/cobros/{cobro['id']}/eventos")
    assert rechazo.status_code == 429
    assert rechazo.json()["detail"] == MENSAJE_CANALES
    canales.liberar("testclient")
    abierto = cliente.get(f"/api/cobros/{cobro['id']}/eventos")
    assert abierto.status_code == 200


def test_cors_solo_permite_los_origenes_configurados(cliente, configuracion) -> None:
    """Solo WEB_ORIGIN, y solo los métodos GET, POST y DELETE necesarios para la web."""
    origen = configuracion.origenes_web[0]
    permitido = cliente.options(
        "/salud",
        headers={"Origin": origen, "Access-Control-Request-Method": "GET"},
    )
    assert permitido.headers["access-control-allow-origin"] == origen
    metodos = {
        parte.strip() for parte in permitido.headers["access-control-allow-methods"].split(",")
    }
    assert metodos == {"GET", "POST", "DELETE"}

    ajeno = cliente.options(
        "/salud",
        headers={
            "Origin": "https://otro.ejemplo",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in ajeno.headers

    lectura = cliente.get("/salud", headers={"Origin": origen})
    assert lectura.headers["access-control-allow-origin"] == origen
    ajena = cliente.get("/salud", headers={"Origin": "https://otro.ejemplo"})
    assert "access-control-allow-origin" not in ajena.headers
