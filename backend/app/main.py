"""API de PAGO FÁCIL: crea cobros CoDi con pey y avisa a la web cuando se pagan."""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from standardwebhooks.webhooks import Webhook, WebhookVerificationError
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.almacen import Almacen, AlmacenEnMemoria
from app.canal import flujo_de_avisos
from app.cobros import Cobro, NoSePuedeCancelar, RepositorioCobros
from app.config import RAIZ_BACKEND, Configuracion, obtener_configuracion
from app.eventos import Difusor, LimiteDeCanales, LimitePorIp
from app.pey import ClientePey, ErrorPey
from app.reloj import Reloj
from app.respaldo import ConsultaDeRespaldo

registro = logging.getLogger("pago_facil")
_registro_listo = False

EVENTO_QR_PAGADO = "codi.qr.payment_received"


MENSAJE_MONTO = "Escribe un monto mayor a $0 con máximo 2 decimales"
MENSAJE_CONCEPTO_LARGO = "El concepto puede tener máximo 40 letras"
MENSAJE_CONCEPTO_RARO = "El concepto tiene caracteres no válidos"


def validar_monto(valor: object, maximo: Decimal) -> Decimal | None:
    """Monto fijo, o None si el cobro es de monto libre (spec 001, RF-002, RF-003, RF-004).

    None, ausente y 0 dejan que el cliente escriba la cantidad. Negativo, texto
    y más de 2 decimales se rechazan.
    """
    if isinstance(valor, bool):
        raise HTTPException(422, MENSAJE_MONTO)
    if valor is None:
        return None
    if isinstance(valor, str):
        try:
            monto = Decimal(valor)
        except InvalidOperation:
            raise HTTPException(422, MENSAJE_MONTO) from None
    elif isinstance(valor, Decimal):
        monto = valor
    elif isinstance(valor, int):
        monto = Decimal(valor)
    elif isinstance(valor, float):
        monto = Decimal(str(valor))
    else:
        raise HTTPException(422, MENSAJE_MONTO)
    exponente = monto.as_tuple().exponent
    if isinstance(exponente, str) or exponente < -2 or not monto.is_finite():
        raise HTTPException(422, MENSAJE_MONTO)
    if monto == 0:
        return None
    if monto > maximo:
        raise HTTPException(422, f"El monto máximo de la demo es ${maximo}")
    if monto < 0:
        raise HTTPException(422, MENSAJE_MONTO)
    return monto


def validar_concepto(valor: object) -> str:
    """Limpia el concepto o usa Cobro. Rechaza lo no imprimible y lo de más de 40."""
    if valor is None:
        return "Cobro"
    if not isinstance(valor, str) or any(not caracter.isprintable() for caracter in valor):
        raise HTTPException(422, MENSAJE_CONCEPTO_RARO)
    limpio = " ".join(valor.split())
    if not limpio:
        return "Cobro"
    if len(limpio) > 40:
        raise HTTPException(422, MENSAJE_CONCEPTO_LARGO)
    return limpio


async def leer_solicitud(request: Request, monto_maximo: Decimal) -> tuple[Decimal | None, str]:
    """Lee el JSON y valida monto y concepto antes del límite por IP (spec 001, RF-004, RF-034)."""
    try:
        bruto = await request.body()
        cuerpo = json.loads(bruto or b"{}", parse_float=Decimal)
    except json.JSONDecodeError:
        raise HTTPException(422, MENSAJE_MONTO) from None
    if not isinstance(cuerpo, dict):
        raise HTTPException(422, MENSAJE_MONTO)
    monto = validar_monto(cuerpo.get("monto"), monto_maximo)
    return monto, validar_concepto(cuerpo.get("concepto"))


def configurar_registros() -> None:
    """Deja `pago_facil` en INFO con un manejador de consola (spec 001, RF-039)."""
    global _registro_listo
    registro.setLevel(logging.INFO)
    if _registro_listo:
        return
    consola = logging.StreamHandler()
    consola.setLevel(logging.INFO)
    consola.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    registro.addHandler(consola)
    _registro_listo = True
    registro.info("Registros de pago_facil activos")


def crear_app(
    config: Configuracion | None = None,
    cliente_pey: ClientePey | None = None,
    reloj: Reloj | None = None,
    almacen: Almacen | None = None,
    tareas_en_segundo_plano: bool = True,
) -> FastAPI:
    """Crea la API con reloj, registros y el almacén de cobros (spec 001, RF-008; spec 003, DP-6).

    Si `carpeta_web` tiene valor, entrega esa carpeta en `/` después de las rutas
    del API (spec 003, RF-024, RF-029). Sin `almacen`, los cobros se guardan en memoria.
    `tareas_en_segundo_plano` se acepta para T060, que arrancará el trabajo de fondo.
    """
    del tareas_en_segundo_plano
    config = config or obtener_configuracion()
    configurar_registros()
    reloj_de_la_app = reloj or Reloj()

    cliente_final = cliente_pey or ClientePey(
        config.pey_api_base_url, config.pey_api_key.get_secret_value()
    )

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI):
        app.state.pey = cliente_final
        yield
        await cliente_final.cerrar()

    app = FastAPI(title="PAGO FÁCIL", version="0.1.0", lifespan=ciclo_de_vida)
    app.state.reloj = reloj_de_la_app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origenes_web,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    # La IP del límite es la del cliente, no la del proxy del hosting (RF-034, R-5).
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=config.proxies_confiables)

    almacen_de_la_app = almacen or AlmacenEnMemoria(reloj=reloj_de_la_app)
    cobros = RepositorioCobros(almacen_de_la_app, reloj_de_la_app, config.gracia_segundos)
    app.state.almacen = almacen_de_la_app
    app.state.cobros = cobros
    difusor = Difusor()
    consulta = ConsultaDeRespaldo(cliente_final, cobros, difusor, reloj_de_la_app)
    limite = LimitePorIp(config.limite_cobros_por_minuto, reloj_de_la_app)
    limite_canales = LimiteDeCanales(config.canales_por_ip)
    app.state.limite_canales = limite_canales

    async def buscar(cobro_id: str) -> Cobro:
        cobro = await cobros.obtener(cobro_id)
        if cobro is None:
            raise HTTPException(404, "Ese cobro no existe")
        return cobro

    @app.get("/salud")
    async def salud() -> dict:
        return {
            "estado": "ok",
            "llave_pey": bool(config.pey_api_key.get_secret_value()),
            "secreto_aviso_pey": bool(config.pey_webhook_secret.get_secret_value()),
        }

    @app.exception_handler(RequestValidationError)
    async def errores_de_validacion(
        _solicitud: Request, _error: RequestValidationError
    ) -> JSONResponse:
        """Un texto en español en lugar de la lista de pydantic (spec 001, RF-004)."""
        return JSONResponse(
            status_code=422,
            content={"detail": "Los datos del cobro no son válidos."},
        )

    @app.post("/api/cobros", status_code=201)
    async def crear_cobro(request: Request) -> dict:
        """Crea un cobro y su QR en pey (spec 001, RF-001, RF-003, RF-006, RF-009, RF-010)."""
        monto, concepto = await leer_solicitud(request, config.monto_maximo)
        ip = request.client.host if request.client else "desconocida"
        if not limite.permitir(ip):
            raise HTTPException(429, "Demasiados cobros seguidos. Espera un minuto.")

        cobro = cobros.nuevo(
            monto,
            concepto,
            config.expiracion_segundos,
            ahora=app.state.reloj.ahora(),
        )
        await cobros.guardar_nuevo(cobro)
        try:
            # pey usa amount 0 cuando el cliente escribe la cantidad (RF-003).
            qr = await app.state.pey.crear_qr(
                monto=cobro.monto if cobro.monto is not None else Decimal(0),
                concepto=cobro.concepto,
                expiracion=config.expiracion_segundos,
                num_ref=cobro.num_ref,
                metadata={"cobroId": cobro.id},
            )
        except ErrorPey as error:
            await cobros.descartar(cobro)
            registro.error(
                "pey no creó el cobro %s (requestId=%s)",
                cobro.id,
                error.request_id,
            )
            if error.tipo == "sin llave":
                raise HTTPException(503, "El servidor no tiene configurada la llave de pey")
            if error.estado in (401, 403):
                raise HTTPException(502, "pey rechazó la llave del servidor")
            if error.estado == 503:
                raise HTTPException(
                    503, "pey está en mantenimiento. Intenta de nuevo en unos minutos."
                )
            raise HTTPException(502, "No se pudo crear el cobro con pey. Intenta de nuevo.")

        await cobros.vincular_qr(cobro, qr.id, qr.qr_string, qr.qr_image)
        if qr.request_id:
            registro.info(
                "QR creado cobro=%s codi_qr_id=%s requestId=%s",
                cobro.id,
                qr.id,
                qr.request_id,
            )
        else:
            registro.info("QR creado cobro=%s codi_qr_id=%s", cobro.id, qr.id)
        return cobro.publico()

    @app.get("/api/cobros/{cobro_id}")
    async def ver_cobro(cobro_id: str) -> dict:
        cobro = await buscar(cobro_id)
        await consulta.consultar(cobro, intervalo_minimo=3)
        return cobro.publico()

    @app.post("/api/cobros/{cobro_id}/cancelar")
    async def cancelar_cobro(cobro_id: str) -> dict:
        """Cancela un cobro pendiente y avisa por el canal (spec 001, RF-023, RF-024, RF-030)."""
        cobro = await buscar(cobro_id)
        try:
            await cobros.cancelar(cobro, app.state.reloj.ahora())
        except NoSePuedeCancelar:
            raise HTTPException(
                409, "Solo se puede cancelar un cobro que todavía no se paga ni vence"
            )
        registro.info("Cobro cancelado cobro=%s", cobro.id)
        difusor.publicar(cobro.id, "cancelado", cobro.publico())
        return cobro.publico()

    @app.get("/api/cobros/{cobro_id}/eventos")
    async def eventos_cobro(cobro_id: str, request: Request) -> StreamingResponse:
        """Sirve el canal si la IP todavía tiene lugar (spec 001, RF-028, RF-041)."""
        cobro = await buscar(cobro_id)
        ip = request.client.host if request.client else "desconocida"
        if not limite_canales.ocupar(ip):
            raise HTTPException(
                429, "Tienes demasiadas pantallas abiertas. Cierra otras e intenta de nuevo."
            )

        async def flujo() -> AsyncIterator[str]:
            try:
                async for trozo in flujo_de_avisos(cobro, difusor, consulta, reloj_de_la_app):
                    yield trozo
            finally:
                limite_canales.liberar(ip)

        return StreamingResponse(
            flujo(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/webhooks/pey")
    async def webhook_pey(request: Request) -> dict:
        """Recibe un aviso firmado y registra el pago sin llamar a pey (RF-011)."""
        secreto = config.pey_webhook_secret.get_secret_value()
        if not secreto:
            registro.warning("Aviso rechazado")
            raise HTTPException(503, "El aviso de pey todavía no está configurado")
        cuerpo = await request.body()
        try:
            Webhook(secreto).verify(cuerpo, dict(request.headers))
        except WebhookVerificationError:
            registro.warning("Aviso rechazado")
            raise HTTPException(401, "Firma no válida")
        except json.JSONDecodeError:
            registro.warning("Aviso rechazado")
            raise HTTPException(400, "Aviso con datos no válidos")

        webhook_id = request.headers.get("webhook-id", "")
        if await cobros.aviso_ya_visto(webhook_id):
            return {"recibido": True, "procesado": False}
        try:
            datos = json.loads(cuerpo)
        except ValueError:
            registro.warning("Aviso rechazado")
            raise HTTPException(400, "Aviso con datos no válidos")
        if not isinstance(datos, dict):
            registro.warning("Aviso rechazado")
            raise HTTPException(400, "Aviso con datos no válidos")
        tipo = str(datos.get("type") or "")
        if datos.get("type") != EVENTO_QR_PAGADO:
            registro.info("Aviso ignorado")
            await cobros.marcar_aviso(webhook_id, tipo)
            return {"recibido": True, "procesado": False}
        try:
            monto = Decimal(str(datos["amount"]))
        except (KeyError, InvalidOperation):
            monto = None
        # NaN e Infinity se leen como Decimal, pero no son un monto (contrato aviso-pey).
        if monto is None or not monto.is_finite():
            registro.warning("Aviso rechazado")
            raise HTTPException(400, "Aviso con datos no válidos")

        codi_qr_id = str(datos.get("codiQrId", ""))
        transaccion_id = datos.get("transactionId")
        cobro = await cobros.por_codi_qr(codi_qr_id)
        if cobro is None or not transaccion_id:
            registro.warning("Aviso ignorado codi_qr_id=%s", codi_qr_id)
            await cobros.marcar_aviso(webhook_id, tipo)
            return {"recibido": True, "procesado": False}
        pago = await consulta.registrar_y_avisar(
            cobro,
            str(transaccion_id),
            monto,
            None,
            datos.get("datePaid"),
            "aviso",
            webhook_id=webhook_id,
            tipo_aviso=tipo,
        )
        await cobros.marcar_aviso(webhook_id, tipo)
        return {"recibido": True, "procesado": pago is not None}

    if config.carpeta_web:
        # Relativa a backend/, no a la carpeta desde la que arrancó uvicorn (DP-21).
        ruta_web = Path(config.carpeta_web)
        if not ruta_web.is_absolute():
            ruta_web = RAIZ_BACKEND / ruta_web
        app.mount("/", StaticFiles(directory=ruta_web, html=True), name="web")

    return app


app = crear_app()
