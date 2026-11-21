"""Servidor de pruebas: la web y las rutas de la spec 001, sin pey (spec 002, R-2)."""

from __future__ import annotations

import asyncio
import json
import secrets
import socket
import string
import threading
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_WEB = Path(__file__).resolve().parent.parent
_ALFABETO = string.ascii_letters + string.digits
_EXPIRACION = 600
_GRACIA = 600
_PNG_1X1 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
_CONFIG_POR_DEFECTO = 'window.PAGO_FACIL = { servidor: "" };\n'
_DETALLE_NO_EXISTE = "Ese cobro no existe"
_DETALLE_NO_CANCELA = "Solo se puede cancelar un cobro que todavía no se paga ni vence"
_DETALLE_CREAR = {
    422: "Los datos del cobro no son válidos.",
    429: "Demasiados cobros seguidos. Espera un minuto.",
    502: "No se pudo crear el cobro con pey. Intenta de nuevo.",
    503: "El servidor no tiene configurada la llave de pey",
}
_DETALLE_GENERICO = "No se pudo crear el cobro."
_DETALLE_CANAL = {
    404: _DETALLE_NO_EXISTE,
    429: "Tienes demasiadas pantallas abiertas. Cierra otras e intenta de nuevo.",
    503: "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.",
}
_TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}

_Mensaje = tuple[str, dict[str, object]] | None


@dataclass
class _Cobro:
    """Cobro guardado por el simulado. El estado se calcula al armar la respuesta."""

    id: str
    monto: object
    concepto: str
    creado_en: int
    qr_imagen: str | None
    pagos: list[dict[str, object]] = field(default_factory=list)
    cancelado: bool = False
    codi_qr_id: str = ""
    qr: str = "qr-de-prueba"


@dataclass
class _Programa:
    """La respuesta del próximo POST /api/cobros. Se consume una sola vez."""

    codigo: int
    cuerpo: dict[str, object] | None
    demora: float
    sin_respuesta: bool


def _evento(nombre: str, datos: dict[str, object]) -> str:
    """Un evento SSE con el mismo formato que el canal real (spec 001)."""
    return f"event: {nombre}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


def _estado(cobro: _Cobro, hora: int) -> str:
    """Pagos, luego cancelado, luego vencido, luego pendiente (spec 001, RF-017)."""
    if cobro.pagos:
        return "pagado"
    if cobro.cancelado:
        return "cancelado"
    if hora >= cobro.creado_en + _EXPIRACION:
        return "vencido"
    return "pendiente"


def _normalizar_pago(pago: dict[str, object], numero: int, hora: int) -> dict[str, object]:
    """Deja un pago con los cuatro campos que ve la pantalla (spec 001, RF-018)."""
    return {
        "numero": int(pago.get("numero", numero)),
        "monto_recibido": pago.get("monto_recibido", 0),
        "monto_distinto": bool(pago.get("monto_distinto", False)),
        "pagado_en": int(pago.get("pagado_en", hora)),
    }


class _RegistrarPeticiones:
    """Anota método, ruta y cuerpo sin retener el flujo del canal."""

    def __init__(self, app: ASGIApp, servidor: ServidorSimulado) -> None:
        self._app = app
        self._servidor = servidor

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        partes: list[bytes] = []
        anotada = False

        def anotar() -> None:
            nonlocal anotada
            if anotada:
                return
            anotada = True
            self._servidor._anotar(str(scope.get("method", "")), str(scope.get("path", "")), partes)

        async def recibir() -> Message:
            mensaje = await receive()
            if mensaje["type"] == "http.request":
                partes.append(mensaje.get("body", b""))
                if not mensaje.get("more_body", False):
                    anotar()
            return mensaje

        async def enviar(mensaje: Message) -> None:
            if mensaje["type"] == "http.response.start":
                anotar()
            await send(mensaje)

        await self._app(scope, recibir, enviar)


class ServidorSimulado:
    """FastAPI en un hilo, en el mismo origen que la web (spec 002, R-2, DP-7)."""

    def __init__(self) -> None:
        self.puerto = 0
        self.origen = ""
        self.retry_ms = 3000
        self.peticiones: list[tuple[str, str, object]] = []
        self._hora = int(time.time())
        self._guardados: dict[str, _Cobro] = {}
        self._programa: _Programa | None = None
        self._demora_cancelar = 0.0
        self._config_js: str | None = None
        self._rechazos: dict[str, int] = {}
        self._canales_mudos: set[str] = set()
        self._suscriptores: dict[str, list[asyncio.Queue[_Mensaje]]] = {}
        self._candado = threading.Lock()
        self._bucle: asyncio.AbstractEventLoop | None = None
        self._uvicorn: uvicorn.Server | None = None
        self._hilo: threading.Thread | None = None
        self._conector: socket.socket | None = None
        self._asgi = _RegistrarPeticiones(self._crear_api(), self)

    def arrancar(self) -> None:
        """Abre un puerto libre y sirve en un hilo propio (spec 002, R-2)."""
        if self._hilo is not None:
            return
        conector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conector.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        conector.bind(("127.0.0.1", 0))
        conector.listen(128)
        conector.setblocking(False)
        self._conector = conector
        self.puerto = int(conector.getsockname()[1])
        self.origen = f"http://127.0.0.1:{self.puerto}"
        config = uvicorn.Config(
            self._asgi,
            host="127.0.0.1",
            port=self.puerto,
            log_level="warning",
            access_log=False,
            timeout_graceful_shutdown=1,
        )
        self._uvicorn = uvicorn.Server(config)
        self._hilo = threading.Thread(
            target=self._uvicorn.run,
            kwargs={"sockets": [conector]},
            name="servidor-simulado",
            daemon=True,
        )
        self._hilo.start()
        limite = time.monotonic() + 10
        while not self._uvicorn.started:
            if not self._hilo.is_alive():
                raise RuntimeError("El servidor simulado se detuvo al arrancar")
            if time.monotonic() > limite:
                raise RuntimeError("El servidor simulado no arrancó a tiempo")
            time.sleep(0.02)

    def detener(self) -> None:
        """Pide el cierre del hilo y espera a que suelte el puerto (spec 002, R-2)."""
        servidor = self._uvicorn
        hilo = self._hilo
        if servidor is None or hilo is None:
            return
        servidor.should_exit = True
        hilo.join(timeout=5)
        if hilo.is_alive() and self._conector is not None:
            self._conector.close()
            hilo.join(timeout=2)

    def reiniciar(self) -> None:
        """Deja cobros, peticiones, hora y canales como al arrancar (spec 002, R-2)."""
        with self._candado:
            self._guardados.clear()
            self.peticiones.clear()
            self._programa = None
            self._demora_cancelar = 0.0
            self._config_js = None
            self._rechazos.clear()
            self._canales_mudos.clear()
            self._hora = int(time.time())
            self.retry_ms = 3000
        self._en_bucle(self._cerrar_todos)

    @property
    def cobros(self) -> dict[str, dict[str, object]]:
        """Copia de los cobros guardados, con el estado calculado a la hora actual."""
        with self._candado:
            return {clave: self._publico(cobro) for clave, cobro in self._guardados.items()}

    def cobro_de_prueba(
        self,
        id: str | None = None,
        monto: float | int | None = 25.5,
        concepto: str = "Tacos",
        creado_en: int | None = None,
        hora_servidor: int | None = None,
        pagos: list[dict[str, object]] | None = None,
        qr_imagen: str | None = _PNG_1X1,
    ) -> dict[str, object]:
        """Arma un objeto cobro de la spec 001 más hora_servidor (spec 002, R-2).

        No lo guarda. `expira_en` es `creado_en + 600` y `fin_ventana` suma otros 600.
        """
        datos: dict[str, object] = {
            "id": id,
            "monto": monto,
            "concepto": concepto,
            "qr_imagen": qr_imagen,
            "pagos": list(pagos or []),
        }
        if creado_en is not None:
            datos["creado_en"] = creado_en
        if hora_servidor is not None:
            datos["hora_servidor"] = hora_servidor
        with self._candado:
            cobro = self._desde_dict(datos)
            return self._publico(cobro, None if hora_servidor is None else int(hora_servidor))

    def demorar_cancelar(self, segundos: float) -> None:
        """El próximo POST …/cancelar espera antes de responder (spec 002, T050)."""
        with self._candado:
            self._demora_cancelar = float(segundos)

    def responder_crear(
        self,
        codigo: int = 201,
        cuerpo: dict[str, object] | None = None,
        demora: float = 0,
        sin_respuesta: bool = False,
    ) -> None:
        """Programa la respuesta del siguiente POST /api/cobros (spec 002, R-2)."""
        with self._candado:
            self._programa = _Programa(codigo, cuerpo, demora, sin_respuesta)

    def agregar_pago(
        self,
        id_cobro: str,
        monto_recibido: float,
        monto_distinto: bool = False,
        avisar: bool = True,
    ) -> None:
        """Suma un pago y, si `avisar`, emite `pago` en los canales de ese cobro."""
        with self._candado:
            cobro = self._guardados[id_cobro]
            pago = {
                "numero": len(cobro.pagos) + 1,
                "monto_recibido": monto_recibido,
                "monto_distinto": monto_distinto,
                "pagado_en": self._hora,
            }
            cobro.pagos.append(pago)
            publico = self._publico(cobro)
        if avisar:
            self.emitir(id_cobro, "pago", {"pago": pago, "cobro": publico})

    def emitir(self, id_cobro: str, evento: str, datos: dict[str, object]) -> None:
        """Empuja `vencido`, `cancelado`, `fin`, `estado` u otro evento ya armado."""
        self._en_bucle(self._poner, id_cobro, evento, datos)

    def cortar_canal(self, id_cobro: str, rechazar_con: int | None = None) -> None:
        """Cierra los flujos de ese cobro. Con código, los siguientes GET responden eso."""
        if rechazar_con is not None:
            with self._candado:
                self._rechazos[id_cobro] = rechazar_con
        self._en_bucle(self._cerrar_id, id_cobro)

    def permitir_canal(self, id_cobro: str) -> None:
        """Quita el rechazo de `cortar_canal` para que el canal vuelva a abrirse."""
        with self._candado:
            self._rechazos.pop(id_cobro, None)

    def dejar_canal_mudo(self, id_cobro: str) -> None:
        """Abre el SSE con retry y retiene todos los eventos del cobro (spec 002, C-4)."""
        with self._candado:
            self._canales_mudos.add(id_cobro)

    def canales_abiertos(self, id_cobro: str) -> int:
        """Cuenta las suscripciones SSE vigentes del cobro (spec 002, R-2, C-4)."""
        total = 0

        def contar() -> None:
            nonlocal total
            total = len(self._suscriptores.get(id_cobro, ()))

        self._en_bucle(contar)
        return total

    def olvidar(self, id_cobro: str) -> None:
        """Borra el cobro, como si el servidor se hubiera reiniciado (spec 002, R-2)."""
        with self._candado:
            self._guardados.pop(id_cobro, None)

    def fijar_hora(self, segundos: int) -> None:
        """Fija la hora que se escribe en `hora_servidor` y usa el estado (spec 002, R-6)."""
        with self._candado:
            self._hora = int(segundos)

    def fijar_config(self, texto: str) -> None:
        """Reemplaza el `config.js` que se sirve, hasta el próximo reinicio (spec 002, RF-064)."""
        with self._candado:
            self._config_js = texto

    def _anotar(self, metodo: str, ruta: str, partes: list[bytes]) -> None:
        bruto = b"".join(partes)
        cuerpo: object = None
        if bruto:
            try:
                cuerpo = json.loads(bruto)
            except json.JSONDecodeError:
                cuerpo = bruto.decode("utf-8", errors="replace")
        with self._candado:
            self.peticiones.append((metodo, ruta, cuerpo))

    def _crear_api(self) -> FastAPI:
        @asynccontextmanager
        async def vida(_app: FastAPI) -> AsyncIterator[None]:
            self._bucle = asyncio.get_running_loop()
            yield

        api = FastAPI(lifespan=vida)

        @api.post("/api/cobros")
        async def crear_cobro(request: Request) -> Response:
            """Crea un cobro de prueba o responde lo programado (spec 002, R-2)."""
            await request.body()
            programa = self._tomar_programa()
            if programa is not None and programa.demora > 0:
                sigue = await self._seguir_conectado(request, programa.demora)
                if not sigue:
                    return Response(status_code=499)
            if programa is not None and programa.sin_respuesta:
                while not await request.is_disconnected():
                    await asyncio.sleep(0.05)
                return Response(status_code=204)
            if programa is not None and programa.codigo != 201:
                cuerpo = programa.cuerpo
                if cuerpo is None:
                    texto = _DETALLE_CREAR.get(programa.codigo, _DETALLE_GENERICO)
                    cuerpo = {"detail": texto}
                return JSONResponse(cuerpo, status_code=programa.codigo)
            if programa is not None and programa.cuerpo is not None:
                with self._candado:
                    cobro = self._desde_dict(programa.cuerpo)
                    self._guardados[cobro.id] = cobro
                    return JSONResponse(self._publico(cobro), status_code=201)
            datos = await self._leer_json(request)
            if datos is None:
                return JSONResponse({"detail": _DETALLE_CREAR[422]}, status_code=422)
            monto = datos["monto"] if "monto" in datos else None
            concepto = datos.get("concepto", "")
            with self._candado:
                cobro = self._desde_dict({"monto": monto, "concepto": str(concepto)})
                self._guardados[cobro.id] = cobro
                return JSONResponse(self._publico(cobro), status_code=201)

        @api.get("/api/cobros/{cobro_id}")
        async def ver_cobro(cobro_id: str) -> JSONResponse:
            """Devuelve el cobro guardado, o 404 si no está (spec 002, R-2)."""
            with self._candado:
                cobro = self._guardados.get(cobro_id)
                if cobro is None:
                    return JSONResponse({"detail": _DETALLE_NO_EXISTE}, status_code=404)
                return JSONResponse(self._publico(cobro))

        @api.post("/api/cobros/{cobro_id}/cancelar")
        async def cancelar_cobro(cobro_id: str, request: Request) -> Response:
            """Cancela un cobro pendiente y avisa por el canal (spec 001, RF-023)."""
            await request.body()
            with self._candado:
                demora = self._demora_cancelar
                self._demora_cancelar = 0.0
            if demora > 0 and not await self._seguir_conectado(request, demora):
                return Response(status_code=499)
            with self._candado:
                cobro = self._guardados.get(cobro_id)
                if cobro is None:
                    return JSONResponse({"detail": _DETALLE_NO_EXISTE}, status_code=404)
                if _estado(cobro, self._hora) != "pendiente":
                    return JSONResponse({"detail": _DETALLE_NO_CANCELA}, status_code=409)
                cobro.cancelado = True
                publico = self._publico(cobro)
            self._poner(cobro_id, "cancelado", publico)
            return JSONResponse(publico)

        @api.get("/api/cobros/{cobro_id}/eventos")
        async def eventos_cobro(cobro_id: str) -> Response:
            """Abre el canal: retry, estado y después lo que se empuje (spec 002, R-2)."""
            with self._candado:
                rechazo = self._rechazos.get(cobro_id)
                cobro = self._guardados.get(cobro_id)
                mudo = cobro_id in self._canales_mudos
            if rechazo is not None:
                detalle = _DETALLE_CANAL.get(rechazo, "El canal no está disponible")
                return JSONResponse({"detail": detalle}, status_code=rechazo)
            if cobro is None:
                return JSONResponse({"detail": _DETALLE_NO_EXISTE}, status_code=404)
            retry = self.retry_ms
            cola: asyncio.Queue[_Mensaje] = asyncio.Queue()
            self._suscriptores.setdefault(cobro_id, []).append(cola)
            with self._candado:
                estado = self._publico(self._guardados[cobro_id])

            async def flujo() -> AsyncIterator[str]:
                try:
                    # Envía bytes iniciales para separar la apertura del flujo de sus eventos.
                    yield f"retry: {retry}\n\n"
                    if not mudo:
                        yield _evento("estado", estado)
                    while True:
                        mensaje = await cola.get()
                        if mensaje is None:
                            return
                        if not mudo:
                            yield _evento(mensaje[0], mensaje[1])
                finally:
                    colas = self._suscriptores.get(cobro_id, [])
                    if cola in colas:
                        colas.remove(cola)
                    if not colas:
                        self._suscriptores.pop(cobro_id, None)

            # El proxy no debe acumular el flujo, igual que el canal real.
            return StreamingResponse(
                flujo(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        @api.get("/")
        async def raiz() -> Response:
            """Sirve la página de la web (spec 002, R-2)."""
            return self._archivo("index.html")

        @api.get("/{ruta:path}")
        async def estatico(ruta: str) -> Response:
            """Sirve un archivo de web/, nunca los de tests/ (spec 002, R-2)."""
            return self._archivo(ruta)

        return api

    def _archivo(self, ruta: str) -> Response:
        if ruta in ("", "/"):
            ruta = "index.html"
        limpio = ruta.lstrip("/")
        if limpio == "favicon.ico":
            # Chromium pide el icono solo. Un 404 se vería como error de consola (RF-077).
            return Response(status_code=204)
        with self._candado:
            config = self._config_js
        if limpio == "config.js":
            if config is None:
                config = _CONFIG_POR_DEFECTO
            return Response(config, media_type="text/javascript; charset=utf-8")
        destino = (_WEB / limpio).resolve()
        if _WEB not in destino.parents:
            raise HTTPException(status_code=404, detail="No encontrado")
        # Se mira la ruta ya resuelta: "js/../tests/x" también cae en tests/.
        if destino.relative_to(_WEB).parts[0] == "tests":
            raise HTTPException(status_code=404, detail="No encontrado")
        if not destino.is_file():
            raise HTTPException(status_code=404, detail="No encontrado")
        return FileResponse(destino, media_type=_TIPOS.get(destino.suffix))

    def _tomar_programa(self) -> _Programa | None:
        with self._candado:
            programa = self._programa
            self._programa = None
            return programa

    async def _leer_json(self, request: Request) -> dict[str, object] | None:
        bruto = await request.body()
        if not bruto:
            return None
        try:
            datos = json.loads(bruto)
        except json.JSONDecodeError:
            return None
        if not isinstance(datos, dict):
            return None
        return datos

    async def _seguir_conectado(self, request: Request, segundos: float) -> bool:
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            if await request.is_disconnected():
                return False
            restante = limite - time.monotonic()
            await asyncio.sleep(min(0.05, max(restante, 0)))
        return not await request.is_disconnected()

    def _desde_dict(self, datos: dict[str, object]) -> _Cobro:
        hora = int(datos["hora_servidor"]) if "hora_servidor" in datos else self._hora
        creado = int(datos["creado_en"]) if "creado_en" in datos else hora
        crudos = datos.get("pagos") or []
        pagos = [
            _normalizar_pago(pago, indice, hora)
            for indice, pago in enumerate(crudos, start=1)
            if isinstance(pago, dict)
        ]
        if "qr_imagen" in datos:
            valor = datos["qr_imagen"]
            imagen = None if valor is None else str(valor)
        else:
            imagen = _PNG_1X1
        identificador = datos.get("id")
        return _Cobro(
            id=str(identificador) if identificador else self._nuevo_id(),
            monto=datos.get("monto", 25.5),
            concepto=str(datos.get("concepto", "Tacos")),
            creado_en=creado,
            qr_imagen=imagen,
            pagos=pagos,
            cancelado=datos.get("estado") == "cancelado",
            codi_qr_id=str(datos.get("codi_qr_id") or _codigo(10)),
            qr=str(datos.get("qr") or "qr-de-prueba"),
        )

    def _publico(self, cobro: _Cobro, hora: int | None = None) -> dict[str, object]:
        momento = self._hora if hora is None else hora
        total = 0
        for pago in cobro.pagos:
            total += pago["monto_recibido"]
        return {
            "id": cobro.id,
            "codi_qr_id": cobro.codi_qr_id,
            "monto": cobro.monto,
            "monto_libre": cobro.monto is None,
            "concepto": cobro.concepto,
            "estado": _estado(cobro, momento),
            "qr": cobro.qr,
            "qr_imagen": cobro.qr_imagen,
            "creado_en": cobro.creado_en,
            "expira_en": cobro.creado_en + _EXPIRACION,
            "fin_ventana": cobro.creado_en + _EXPIRACION + _GRACIA,
            "numero_de_pagos": len(cobro.pagos),
            "total_recibido": total,
            "pagado_en": None if not cobro.pagos else cobro.pagos[-1]["pagado_en"],
            "pagos": list(cobro.pagos),
            "hora_servidor": momento,
        }

    def _nuevo_id(self) -> str:
        ocupados = set(self._guardados)
        while True:
            candidato = _codigo(12)
            if candidato not in ocupados:
                return candidato

    def _poner(self, id_cobro: str, evento: str, datos: dict[str, object]) -> None:
        for cola in list(self._suscriptores.get(id_cobro, ())):
            cola.put_nowait((evento, datos))

    def _cerrar_id(self, id_cobro: str) -> None:
        for cola in list(self._suscriptores.get(id_cobro, ())):
            cola.put_nowait(None)
        self._suscriptores.pop(id_cobro, None)

    def _cerrar_todos(self) -> None:
        for colas in self._suscriptores.values():
            for cola in colas:
                cola.put_nowait(None)
        self._suscriptores.clear()

    def _en_bucle(self, funcion: Callable[..., None], *argumentos: object) -> None:
        """Corre `funcion` en el hilo del servidor. El canal no es seguro entre hilos."""
        bucle = self._bucle
        if bucle is None or not bucle.is_running():
            funcion(*argumentos)
            return
        try:
            if asyncio.get_running_loop() is bucle:
                funcion(*argumentos)
                return
        except RuntimeError:
            pass
        hecho = threading.Event()
        error: list[Exception] = []

        def correr() -> None:
            try:
                funcion(*argumentos)
            except Exception as excepcion:
                error.append(excepcion)
            finally:
                hecho.set()

        bucle.call_soon_threadsafe(correr)
        if not hecho.wait(timeout=2):
            raise TimeoutError("El servidor simulado no aplicó el cambio a tiempo")
        if error:
            raise error[0]


def _codigo(largo: int) -> str:
    return "".join(secrets.choice(_ALFABETO) for _ in range(largo))
