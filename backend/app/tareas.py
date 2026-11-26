"""Reintentos de avisos y conciliación de ventanas terminadas (spec 003, RF-048, RF-061).

La lista de reintentos y el contador de fallas del latido viven solo en memoria.
"""

import logging
from decimal import Decimal
from typing import TypedDict

from app.almacen import Almacen, ErrorDeAlmacen, ErrorDeDatos, registrar_falla
from app.cobros import Cobro, RepositorioCobros
from app.pey import ClientePey, ErrorPey, ResultadoConsulta
from app.reloj import Reloj
from app.respaldo import ConsultaDeRespaldo

registro = logging.getLogger("pago_facil")

EVENTO_QR_PAGADO = "codi.qr.payment_received"
ESPERA_REINTENTO_SEGUNDOS = 15
ESPERA_LATIDO_SEGUNDOS = 60
FALLAS_PARA_SALTAR = 10


class AvisoPendiente(TypedDict):
    """Lo justo para registrar el pago otra vez, sin datos de quien paga (spec 003, RF-009)."""

    codi_qr_id: str
    transaccion_id: str
    monto_recibido: Decimal
    pagado_en: int | None
    intentos: int


class ReintentosDeAvisos:
    """Avisos de pago pendientes, uno por ``webhook_id`` (spec 003, RF-014, RF-048)."""

    def __init__(self, repositorio: RepositorioCobros, consulta: ConsultaDeRespaldo) -> None:
        self._repositorio = repositorio
        self._consulta = consulta
        self.avisos: dict[str, AvisoPendiente] = {}

    def agregar(
        self,
        webhook_id: str,
        *,
        codi_qr_id: str,
        transaccion_id: str,
        monto_recibido: Decimal,
        pagado_en: int | None,
    ) -> None:
        """Deja el aviso si ese ``webhook_id`` no estaba ya (spec 003, RF-048, RF-009)."""
        if webhook_id in self.avisos:
            return
        self.avisos[webhook_id] = {
            "codi_qr_id": codi_qr_id,
            "transaccion_id": transaccion_id,
            "monto_recibido": monto_recibido,
            "pagado_en": pagado_en,
            "intentos": 0,
        }

    async def una_vez(self) -> None:
        """Intenta cada aviso una vez. Un error del almacén no sale de aquí (spec 003, RF-048)."""
        for webhook_id, aviso in list(self.avisos.items()):
            cobro_id: str | None = None
            try:
                cobro = await self._repositorio.por_codi_qr(aviso["codi_qr_id"])
                if cobro is None:
                    await self._repositorio.marcar_aviso(webhook_id, EVENTO_QR_PAGADO)
                    self.avisos.pop(webhook_id, None)
                    continue
                cobro_id = cobro.id
                await self._consulta.registrar_y_avisar(
                    cobro,
                    aviso["transaccion_id"],
                    aviso["monto_recibido"],
                    None,
                    aviso["pagado_en"],
                    "aviso",
                    webhook_id=webhook_id,
                    tipo_aviso=EVENTO_QR_PAGADO,
                )
                self.avisos.pop(webhook_id, None)
            except ErrorDeAlmacen as error:
                aviso["intentos"] += 1
                registrar_falla(error, cobro_id)
            except ErrorDeDatos as error:
                registrar_falla(error, cobro_id)
                self.avisos.pop(webhook_id, None)


class LatidoDeConciliacion:
    """Revisa en pey, una vez, cada cobro cuya ventana ya terminó (spec 003, RF-061, DP-39).

    No publica en el canal: nadie está escuchando. El contador de fallas pasajeras
    vive en memoria y se pierde al reiniciar (QP-13).
    """

    def __init__(
        self,
        repositorio: RepositorioCobros,
        pey: ClientePey,
        reloj: Reloj,
        almacen: Almacen,
    ) -> None:
        self._repositorio = repositorio
        self._pey = pey
        self._reloj = reloj
        self._almacen = almacen
        self._fallas: dict[str, int] = {}

    async def una_vez(self) -> None:
        """Una pasada. Una falla del almacén no sale de aquí (spec 003, RF-039, RF-061)."""
        try:
            marca = await self._almacen.leer_conciliado_hasta()
        except (ErrorDeAlmacen, ErrorDeDatos) as error:
            _fallo_de_almacen(error, None)
            return
        ahora = self._reloj.ahora()
        if marca is None:
            try:
                await self._almacen.guardar_conciliado_hasta(ahora)
            except (ErrorDeAlmacen, ErrorDeDatos) as error:
                _fallo_de_almacen(error, None)
            return
        try:
            candidatos = await self._almacen.cobros_con_ventana_terminada(marca, ahora)
        except (ErrorDeAlmacen, ErrorDeDatos) as error:
            _fallo_de_almacen(error, None)
            return

        destino = ahora
        anterior = marca
        for candidato in candidatos:
            try:
                cobro = await self._repositorio.obtener(candidato.id)
            except (ErrorDeAlmacen, ErrorDeDatos) as error:
                if not self._cuenta_falla_de_almacen(error, candidato.id):
                    destino = anterior
                    break
                anterior = candidato.fin_ventana
                continue
            if cobro is None:
                anterior = candidato.fin_ventana
                continue
            try:
                fin = await self._conciliar(cobro)
            except (ErrorDeAlmacen, ErrorDeDatos) as error:
                if not self._cuenta_falla_de_almacen(error, cobro.id):
                    destino = anterior
                    break
                anterior = cobro.fin_ventana
                continue
            if fin is None:
                destino = anterior
                break
            anterior = fin
        try:
            await self._almacen.guardar_conciliado_hasta(destino)
        except (ErrorDeAlmacen, ErrorDeDatos) as error:
            _fallo_de_almacen(error, None)

    async def _conciliar(self, cobro: Cobro) -> float | None:
        """Concilia un cobro y devuelve su ``fin_ventana`` si se sigue con el próximo.

        (spec 003, RF-061, DP-13, QP-13). ``None`` pide detenerse en la marca anterior.
        """
        try:
            vistas = {pago.transaccion_id for pago in cobro.pagos}
            resultado = await self._pey.pagos_del_qr(cobro.codi_qr_id, vistas)
        except ErrorPey as error:
            return self._pey_fallo(cobro, error)
        nuevos = 0
        for pago in resultado.pagos:
            quedo = await self._repositorio.registrar_pago(
                cobro,
                pago.id,
                pago.monto,
                pago.monto_base,
                pago.pagado_en,
                "consulta",
            )
            if quedo is not None:
                nuevos += 1
        _anotar_consulta(cobro.id, resultado, nuevos)
        self._fallas.pop(cobro.id, None)
        return cobro.fin_ventana

    def _pey_fallo(self, cobro: Cobro, error: ErrorPey) -> float | None:
        """4xx se salta. Una falla pasajera se reintenta; a la décima también se salta."""
        if 400 <= error.estado < 500:
            _anotar_pey(cobro.id, error.request_id, logging.WARNING)
            self._fallas.pop(cobro.id, None)
            return cobro.fin_ventana
        veces = self._fallas.get(cobro.id, 0) + 1
        self._fallas[cobro.id] = veces
        nivel = logging.ERROR if veces >= FALLAS_PARA_SALTAR else logging.WARNING
        _anotar_pey(cobro.id, error.request_id, nivel)
        if veces >= FALLAS_PARA_SALTAR:
            self._fallas.pop(cobro.id, None)
            return cobro.fin_ventana
        return None

    def _cuenta_falla_de_almacen(self, error: ErrorDeAlmacen | ErrorDeDatos, cobro_id: str) -> bool:
        """A la décima el cobro se salta; antes, el latido se detiene (spec 003, QP-13)."""
        _fallo_de_almacen(error, cobro_id)
        veces = self._fallas.get(cobro_id, 0) + 1
        self._fallas[cobro_id] = veces
        if veces >= FALLAS_PARA_SALTAR:
            self._fallas.pop(cobro_id, None)
            return True
        return False


def _fallo_de_almacen(error: ErrorDeAlmacen | ErrorDeDatos, cobro_id: str | None) -> None:
    """La línea dice ``latido``, no el texto ni la operación interna (spec 003, RF-016)."""
    registrar_falla(type(error)("latido", error.clase), cobro_id)


def _anotar_pey(cobro_id: str, request_id: str | None, nivel: int) -> None:
    """4xx o falla pasajera de pey, sin datos de quien paga (spec 003, RF-009, RF-061)."""
    if request_id:
        registro.log(
            nivel,
            "No se pudo conciliar el cobro %s en pey (requestId=%s)",
            cobro_id,
            request_id,
        )
        return
    registro.log(nivel, "No se pudo conciliar el cobro %s en pey", cobro_id)


def _anotar_consulta(cobro_id: str, resultado: ResultadoConsulta, nuevos: int) -> None:
    """Misma forma que la consulta de respaldo, con otro prefijo (spec 003, RF-061)."""
    if resultado.request_id:
        registro.info(
            "Conciliación cobro=%s paginas=%s pagos_nuevos=%s requestId=%s",
            cobro_id,
            resultado.paginas,
            nuevos,
            resultado.request_id,
        )
        return
    registro.info(
        "Conciliación cobro=%s paginas=%s pagos_nuevos=%s",
        cobro_id,
        resultado.paginas,
        nuevos,
    )


async def correr_tareas(
    reintentos: ReintentosDeAvisos,
    reloj: Reloj,
    latido: LatidoDeConciliacion | None = None,
) -> None:
    """Reintentos cada 15 s. Con latido, también al empezar y cada 60 s (spec 003, RF-048, RF-061).

    Una falla que no sea del almacén se anota solo con el nombre de su clase y el bucle sigue.
    """
    hasta_latido = ESPERA_LATIDO_SEGUNDOS
    while True:
        try:
            await reintentos.una_vez()
            if latido is not None and hasta_latido >= ESPERA_LATIDO_SEGUNDOS:
                await latido.una_vez()
                hasta_latido = 0
        except Exception as error:
            registro.error("%s", type(error).__name__)
        await reloj.dormir(ESPERA_REINTENTO_SEGUNDOS)
        if latido is not None:
            hasta_latido += ESPERA_REINTENTO_SEGUNDOS
