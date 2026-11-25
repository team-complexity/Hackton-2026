"""Reintentos de avisos que la base no pudo guardar (spec 003, RF-048, DP-14).

La lista vive solo en memoria. El latido de conciliación llega en F6.
"""

import logging
from decimal import Decimal
from typing import TypedDict

from app.almacen import ErrorDeAlmacen, ErrorDeDatos, registrar_falla
from app.cobros import RepositorioCobros
from app.reloj import Reloj
from app.respaldo import ConsultaDeRespaldo

registro = logging.getLogger("pago_facil")

EVENTO_QR_PAGADO = "codi.qr.payment_received"
ESPERA_REINTENTO_SEGUNDOS = 15


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


async def correr_tareas(reintentos: ReintentosDeAvisos, reloj: Reloj) -> None:
    """Llama a ``una_vez`` y espera 15 s del reloj, una y otra vez (spec 003, RF-048, DP-14).

    Una falla que no sea del almacén se anota solo con el nombre de su clase y el bucle sigue.
    """
    while True:
        try:
            await reintentos.una_vez()
        except Exception as error:
            registro.error("%s", type(error).__name__)
        await reloj.dormir(ESPERA_REINTENTO_SEGUNDOS)
