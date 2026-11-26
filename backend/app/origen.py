"""Rechazo de un Origin ajeno al crear o cancelar un cobro."""

import logging
from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

registro = logging.getLogger("pago_facil")

_DETALLE = "Origen no permitido"


def _host_y_puerto(texto: str) -> tuple[str, int | None] | None:
    """Host y puerto tal como vienen escritos.

    El puerto ausente queda en None. No se rellena con 80 o 443: la comparación
    no usa el esquema (spec 001, C-11).
    """
    try:
        partes = urlsplit(texto)
        puerto = partes.port
    except ValueError:
        return None
    if partes.hostname is None:
        return None
    return partes.hostname, puerto


def _es_post_de_cobro(method: str, path: str) -> bool:
    """POST /api/cobros o POST /api/cobros/{id}/cancelar."""
    if method != "POST":
        return False
    if path == "/api/cobros":
        return True
    resto = path.removeprefix("/api/cobros/")
    identificador, separador, accion = resto.partition("/")
    return bool(separador) and bool(identificador) and accion == "cancelar"


class OrigenEnPosts:
    """403 si crear o cancelar trae un Origin que no es de esta web.

    (spec 001, RF-035, C-11). Sin el encabezado la petición sigue, como curl,
    las apps y las pruebas. ``null`` se rechaza. No lee el cuerpo: el rechazo
    ocurre antes de la ruta, así que no cuenta para el límite por IP ni llama
    a pey o al almacén. OPTIONS, GET y el aviso de pey siguen de largo.
    """

    def __init__(self, app: ASGIApp, origenes: list[str]) -> None:
        self.app = app
        self._origenes = origenes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and _es_post_de_cobro(scope["method"], scope["path"]):
            cabeceras = Headers(scope=scope)
            origin = cabeceras.get("origin")
            if origin is not None and not self._permitido(origin, cabeceras.get("host")):
                registro.warning("Petición rechazada por origen")
                await JSONResponse(status_code=403, content={"detail": _DETALLE})(
                    scope, receive, send
                )
                return
        await self.app(scope, receive, send)

    def _permitido(self, origin: str, host: str | None) -> bool:
        """El Origin está configurado, o su host y puerto son los del encabezado Host."""
        if origin == "null":
            return False
        if origin in self._origenes:
            return True
        if host is None:
            return False
        propio = _host_y_puerto(f"//{host}")
        pedido = _host_y_puerto(origin)
        if propio is None or pedido is None:
            return False
        return pedido == propio
