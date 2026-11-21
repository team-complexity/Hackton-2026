"""Pey simulado, reloj falso y firmas de prueba (spec 001, principio V).

Ninguna prueba usa estas piezas para salir a api.pey.mx: el cliente HTTP
lleva un transporte simulado y una base que no es la de pey.
"""

import base64
import json
from collections.abc import Callable
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from standardwebhooks.webhooks import Webhook

from app.config import Configuracion
from app.main import crear_app
from app.pey import ClientePey
from app.reloj import RelojFalso

CODI_QR_ID = "ab12cd34ef"
LLAVE_FALSA = "llave-falsa-NO-DEBE-SALIR"
SECRETO_FALSO = "whsec_" + base64.b64encode(b"secreto-falso-NO-DEBE-SALIR").decode()
BASE_PEY_DE_PRUEBA = "https://pey.prueba"


class PeySimulado:
    """Transporte simulado de pey sobre httpx.MockTransport (spec 001, principio V)."""

    def __init__(self) -> None:
        self.solicitudes: list[httpx.Request] = []
        self.estado_crear = 201
        self.estado_consulta = 200
        self.id_qr = CODI_QR_ID
        self.qr_string = '{"IDC":"x"}'
        self.qr_imagen = "aW1n"
        self.transacciones: list[dict] = []
        # Cada página es el JSON de GET /transaction/codi/qr/{id}: items y nextToken.
        self.paginas: list[dict] | None = None
        self.request_id = "r1"
        self.sin_conexion = False
        self.tiempo_agotado = False
        # Se llama al responder POST /codi/qr; sirve para simular que pey tarda (C-2).
        self.al_crear: Callable[[], None] | None = None

    def __call__(self, solicitud: httpx.Request) -> httpx.Response:
        self.solicitudes.append(solicitud)
        if self.sin_conexion:
            raise httpx.ConnectError("sin conexión")
        if self.tiempo_agotado:
            raise httpx.ReadTimeout("tiempo agotado")
        if solicitud.method == "POST" and solicitud.url.path == "/codi/qr":
            return self._respuesta_crear()
        if solicitud.method == "GET" and solicitud.url.path.startswith("/transaction/codi/qr/"):
            return self._respuesta_consulta(solicitud)
        return self._error(404)

    def _respuesta_crear(self) -> httpx.Response:
        if self.al_crear is not None:
            self.al_crear()
        if self.estado_crear != 201:
            return self._error(self.estado_crear)
        return httpx.Response(
            201,
            json={
                "id": self.id_qr,
                "qrString": self.qr_string,
                "qrImage": self.qr_imagen,
                "requestId": self.request_id,
            },
        )

    def _respuesta_consulta(self, solicitud: httpx.Request) -> httpx.Response:
        if self.estado_consulta != 200:
            return self._error(self.estado_consulta)
        return httpx.Response(200, json=self._pagina(solicitud))

    def _pagina(self, solicitud: httpx.Request) -> dict:
        if not self.paginas:
            return {"items": self.transacciones, "nextToken": None, "requestId": self.request_id}
        token = solicitud.url.params.get("nextToken")
        if token is None:
            return self.paginas[0]
        for indice, pagina in enumerate(self.paginas[:-1]):
            if pagina.get("nextToken") == token:
                return self.paginas[indice + 1]
        return {"items": [], "nextToken": None}

    def _error(self, estado: int) -> httpx.Response:
        return httpx.Response(
            estado,
            json={
                "error": {
                    "message": "fallo",
                    "type": "X",
                    "requestId": self.request_id,
                }
            },
        )


def firmar_aviso(cuerpo: str, secreto: str, webhook_id: str, momento: datetime) -> dict[str, str]:
    """Firma el cuerpo como texto (spec 001, principio V, RF-011).

    `momento` puede ser una hora vieja para probar un aviso fuera de tiempo.
    """
    return {
        "webhook-id": webhook_id,
        "webhook-timestamp": str(int(momento.timestamp())),
        "webhook-signature": Webhook(secreto).sign(webhook_id, momento, cuerpo),
    }


def pago(transaccion_id: str = "01TX") -> dict:
    """Cuerpo mínimo de un aviso de pago, el mismo del prototipo."""
    return {
        "type": "codi.qr.payment_received",
        "amount": 0.01,
        "codiQrId": CODI_QR_ID,
        "concept": "Tacos",
        "datePaid": 1790724818,
        "numRef": "1",
        "transactionId": transaccion_id,
    }


def enviar_aviso(
    cliente: TestClient,
    datos: dict,
    webhook_id: str = "msg_1",
    secreto: str = SECRETO_FALSO,
    momento: datetime | None = None,
) -> httpx.Response:
    """Manda un aviso firmado. Si no hay momento, usa la hora actual."""
    cuerpo = json.dumps(datos)
    ahora = momento or datetime.now(UTC)
    cabeceras = firmar_aviso(cuerpo, secreto, webhook_id, ahora)
    cabeceras["content-type"] = "application/json"
    return cliente.post("/webhooks/pey", content=cuerpo, headers=cabeceras)


@pytest.fixture
def reloj() -> RelojFalso:
    """Reloj que no avanza solo (spec 001, principio V)."""
    return RelojFalso(inicio=1_794_700_000)


@pytest.fixture
def pey() -> PeySimulado:
    """pey simulado. No abre conexión con api.pey.mx."""
    return PeySimulado()


@pytest.fixture
def configuracion() -> Configuracion:
    """Llave y secreto falsos. El límite de 5 conserva la prueba repartida del prototipo."""
    return Configuracion(
        _env_file=None,
        pey_api_key=LLAVE_FALSA,
        pey_webhook_secret=SECRETO_FALSO,
        limite_cobros_por_minuto=5,
    )


@pytest.fixture
def app(configuracion: Configuracion, pey: PeySimulado, reloj: RelojFalso) -> FastAPI:
    """App de prueba con el transporte simulado y el reloj falso."""
    http = httpx.AsyncClient(transport=httpx.MockTransport(pey))
    cliente_pey = ClientePey(
        BASE_PEY_DE_PRUEBA,
        configuracion.pey_api_key.get_secret_value(),
        http,
    )
    return crear_app(configuracion, cliente_pey, reloj)


@pytest.fixture
def cliente(app: FastAPI):
    """Cliente HTTP contra la app de prueba."""
    with TestClient(app) as cliente_http:
        yield cliente_http
