"""Consulta de respaldo y la puerta que registra un pago y lo avisa (spec 001, QP-7)."""

import logging
from decimal import Decimal

from app.almacen import ErrorDeAlmacen, ErrorDeDatos
from app.cobros import Cobro, Pago, RepositorioCobros
from app.eventos import Difusor
from app.pey import ClientePey, ErrorPey
from app.reloj import Reloj

registro = logging.getLogger("pago_facil")


class ConsultaDeRespaldo:
    """Pregunta a pey por los pagos de un cobro y avisa los nuevos (spec 001, RF-025, RF-040)."""

    def __init__(
        self,
        cliente_pey: ClientePey,
        repositorio: RepositorioCobros,
        difusor: Difusor,
        reloj: Reloj,
    ) -> None:
        self._pey = cliente_pey
        self._repositorio = repositorio
        self._difusor = difusor
        self._reloj = reloj

    async def registrar_y_avisar(
        self,
        cobro: Cobro,
        transaccion_id: str,
        monto_recibido: Decimal,
        monto_base: Decimal | None,
        pagado_en: int | None,
        fuente: str,
        webhook_id: str | None = None,
        tipo_aviso: str = "",
    ) -> Pago | None:
        """Si el pago es nuevo y ya quedó guardado, publica el evento (spec 003, RF-002).

        ``ErrorDeAlmacen`` y ``ErrorDeDatos`` salen hacia quien llama (TK-16).
        """
        pago = await self._repositorio.registrar_pago(
            cobro,
            transaccion_id,
            monto_recibido,
            monto_base,
            pagado_en,
            fuente,
            webhook_id=webhook_id,
            tipo_aviso=tipo_aviso,
        )
        if pago is None:
            return None
        registro.info(
            "Pago cobro=%s transaccion=%s numero=%s fuente=%s",
            cobro.id,
            transaccion_id,
            pago.numero,
            fuente,
        )
        self._difusor.publicar(
            cobro.id,
            "pago",
            {"pago": pago.publico(), "cobro": cobro.publico()},
        )
        return pago

    async def consultar(self, cobro: Cobro, intervalo_minimo: float) -> None:
        """Consulta a pey si toca. Si el almacén falla, se registra y sigue (spec 003, RF-016)."""
        ahora = self._reloj.ahora()
        if not cobro.en_ventana(ahora):
            return
        if ahora - cobro.ultima_consulta_pey < intervalo_minimo:
            return
        cobro.ultima_consulta_pey = ahora
        try:
            # Las transacciones son las de este cobro: tras un reinicio no hay un conjunto global.
            transacciones = {pago.transaccion_id for pago in cobro.pagos}
            resultado = await self._pey.pagos_del_qr(cobro.codi_qr_id, transacciones)
        except ErrorPey as error:
            registro.warning(
                "No se pudo consultar el cobro %s en pey (requestId=%s)",
                cobro.id,
                error.request_id,
            )
            return
        nuevos = 0
        for pago_pey in resultado.pagos:
            try:
                quedo = await self.registrar_y_avisar(
                    cobro,
                    pago_pey.id,
                    pago_pey.monto,
                    pago_pey.monto_base,
                    pago_pey.pagado_en,
                    "consulta",
                )
            except (ErrorDeAlmacen, ErrorDeDatos) as error:
                # Solo el nombre de la clase y la operación: nunca el texto original (RF-021).
                frase = (
                    "Base de datos sin respuesta"
                    if isinstance(error, ErrorDeAlmacen)
                    else "La base de datos rechazó los datos"
                )
                registro.error(
                    "%s al %s cobro=%s (%s)", frase, error.operacion, cobro.id, error.clase
                )
                continue
            if quedo:
                nuevos += 1
        if resultado.request_id:
            registro.info(
                "Consulta cobro=%s paginas=%s pagos_nuevos=%s requestId=%s",
                cobro.id,
                resultado.paginas,
                nuevos,
                resultado.request_id,
            )
        else:
            registro.info(
                "Consulta cobro=%s paginas=%s pagos_nuevos=%s",
                cobro.id,
                resultado.paginas,
                nuevos,
            )
