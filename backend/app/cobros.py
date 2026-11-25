"""Cobros y la caché en memoria sobre el almacén (spec 001, RF-008; spec 003, DP-7)."""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import TYPE_CHECKING

from app.reloj import Reloj

if TYPE_CHECKING:
    from app.almacen import Almacen

registro = logging.getLogger("pago_facil")

PENDIENTE = "pendiente"
PAGADO = "pagado"
VENCIDO = "vencido"
CANCELADO = "cancelado"


class NoSePuedeCancelar(Exception):
    """El cobro no está pendiente, así que no se cancela (spec 001, RF-024)."""


def _numero(monto: Decimal) -> float:
    return float(monto)


@dataclass
class Pago:
    """Un pago de un cobro (spec 001, RF-014, RF-016, RF-018, RF-019)."""

    transaccion_id: str
    numero: int
    monto_recibido: Decimal
    monto_base: Decimal | None
    pagado_en: int
    fuente: str
    monto_del_cobro: Decimal | None = field(repr=False)

    @property
    def monto_distinto(self) -> bool:
        """Monto fijo cuyo base, o el recibido si no hay base, no es el pedido (RF-019, RF-020)."""
        if self.monto_del_cobro is None:
            return False
        comparado = self.monto_base if self.monto_base is not None else self.monto_recibido
        return comparado != self.monto_del_cobro

    def publico(self) -> dict:
        """Lo que ve la web, sin el identificador de la transacción (spec 001, RF-018)."""
        return {
            "numero": self.numero,
            "monto_recibido": _numero(self.monto_recibido),
            "monto_distinto": self.monto_distinto,
            "pagado_en": self.pagado_en,
        }


@dataclass
class Cobro:
    """Cobro CoDi en memoria (spec 001, RF-008, RF-021, RF-032)."""

    id: str
    monto: Decimal | None
    concepto: str
    num_ref: str
    creado_en: int
    expira_en: int
    fin_ventana: int
    reloj: Reloj = field(repr=False)
    codi_qr_id: str = ""
    qr: str = ""
    qr_imagen: str | None = None
    cancelado_en: int | None = None
    pagos: list[Pago] = field(default_factory=list)
    ultima_consulta_pey: float = field(default=0.0, repr=False)

    @property
    def monto_libre(self) -> bool:
        """Verdadero cuando el cliente escribe la cantidad (spec 001, RF-003)."""
        return self.monto is None

    @property
    def numero_de_pagos(self) -> int:
        return len(self.pagos)

    @property
    def total_recibido(self) -> Decimal:
        return sum((pago.monto_recibido for pago in self.pagos), Decimal(0))

    @property
    def pagado_en(self) -> int | None:
        """Hora del último pago, o nada si todavía no hay (spec 001, RF-008)."""
        if not self.pagos:
            return None
        return self.pagos[-1].pagado_en

    def estado(self, ahora: float) -> str:
        """Pagos, luego cancelado, luego vencido, luego pendiente (spec 001, RF-017, RF-021)."""
        if self.pagos:
            return PAGADO
        if self.cancelado_en is not None:
            return CANCELADO
        if ahora >= self.expira_en:
            return VENCIDO
        return PENDIENTE

    def en_ventana(self, ahora: float) -> bool:
        """La escucha sigue mientras `ahora` sea anterior a fin_ventana (spec 001, RF-032)."""
        return ahora < self.fin_ventana

    def publico(self) -> dict:
        """Objeto cobro del contrato, sin datos de quien cobra (spec 001, RF-008).

        `hora_servidor` deja a la pantalla calcular su desfase con el servidor (C-2).
        """
        return {
            "id": self.id,
            "codi_qr_id": self.codi_qr_id,
            "monto": None if self.monto is None else _numero(self.monto),
            "monto_libre": self.monto_libre,
            "concepto": self.concepto,
            "estado": self.estado(self.reloj.ahora()),
            "qr": self.qr,
            "qr_imagen": self.qr_imagen,
            "creado_en": self.creado_en,
            "expira_en": self.expira_en,
            "fin_ventana": self.fin_ventana,
            "numero_de_pagos": self.numero_de_pagos,
            "total_recibido": _numero(self.total_recibido),
            "pagado_en": self.pagado_en,
            "pagos": [pago.publico() for pago in self.pagos],
            "hora_servidor": int(self.reloj.ahora()),
        }


class RepositorioCobros:
    """Caché de escritura directa: primero el almacén, después la memoria (spec 003, DP-7).

    Si el almacén falla, la memoria no cambia. ``ErrorDeAlmacen`` y ``ErrorDeDatos``
    salen hacia quien llama. La excepción es ``descartar``, que suelta el cobro igual.
    """

    def __init__(
        self,
        almacen: Almacen,
        reloj: Reloj | None = None,
        gracia_segundos: int = 0,
    ) -> None:
        self._almacen = almacen
        self._reloj = reloj or Reloj()
        self._gracia = gracia_segundos
        self._por_id: dict[str, Cobro] = {}
        self._por_codi_qr: dict[str, str] = {}
        self._avisos: set[str] = set()
        self._candados: dict[str, asyncio.Lock] = {}

    def nuevo(self, monto: Decimal | None, concepto: str, expiracion: int, ahora: float) -> Cobro:
        """Arma el cobro con la hora del reloj, sin guardarlo (spec 001, RF-008; spec 003, TK-16).

        ``monto`` None es un cobro de monto libre: no hay cantidad pedida.
        """
        creado_en = int(ahora)
        return Cobro(
            id=secrets.token_urlsafe(9),
            monto=monto,
            concepto=concepto,
            # Referencia numérica de hasta 7 dígitos, como pide CoDi.
            num_ref=str(secrets.randbelow(9_000_000) + 1_000_000),
            creado_en=creado_en,
            expira_en=creado_en + expiracion,
            fin_ventana=creado_en + expiracion + self._gracia,
            reloj=self._reloj,
        )

    async def guardar_nuevo(self, cobro: Cobro, espera: float = 2) -> None:
        """Escribe el cobro y, si respondió, lo deja en memoria (spec 003, RF-001, DP-35)."""
        await self._almacen.guardar_cobro(cobro, espera=espera)
        self._por_id[cobro.id] = cobro

    async def vincular_qr(
        self,
        cobro: Cobro,
        codi_qr_id: str,
        qr: str,
        qr_imagen: str | None,
        espera: float = 2,
    ) -> None:
        """Guarda una copia con el QR; el cobro original cambia solo si el almacén respondió.

        (spec 003, RF-010, DP-7, DP-35).
        """
        copia = replace(cobro, codi_qr_id=codi_qr_id, qr=qr, qr_imagen=qr_imagen)
        await self._almacen.guardar_qr(copia, espera=espera)
        anterior = cobro.codi_qr_id
        cobro.codi_qr_id = codi_qr_id
        cobro.qr = qr
        cobro.qr_imagen = qr_imagen
        if anterior and anterior != codi_qr_id and self._por_codi_qr.get(anterior) == cobro.id:
            self._por_codi_qr.pop(anterior, None)
        self._por_codi_qr[codi_qr_id] = cobro.id

    def olvidar(self, cobro: Cobro) -> None:
        """Quita el cobro de la memoria, sin tocar el almacén (spec 003, RF-013, TK-16)."""
        self._por_id.pop(cobro.id, None)
        if cobro.codi_qr_id and self._por_codi_qr.get(cobro.codi_qr_id) == cobro.id:
            self._por_codi_qr.pop(cobro.codi_qr_id, None)

    async def descartar(self, cobro: Cobro, espera: float = 2) -> None:
        """Borra el cobro del almacén y lo suelta de la memoria aunque el borrado falle.

        (spec 003, RF-052, DP-35). La excepción del almacén sigue hacia quien llama.
        """
        try:
            await self._almacen.borrar_cobro(cobro.id, espera=espera)
        finally:
            self.olvidar(cobro)

    async def obtener(self, cobro_id: str) -> Cobro | None:
        """El de memoria, o el del almacén: un solo objeto por id (spec 003, RF-005, DP-33)."""
        encontrado = self._por_id.get(cobro_id)
        if encontrado is not None:
            return encontrado
        cargado = await self._almacen.cargar_por_id(cobro_id)
        encontrado = self._por_id.get(cobro_id)
        if encontrado is not None:
            return encontrado
        if cargado is None:
            return None
        self._indexar(cargado)
        return cargado

    async def por_codi_qr(self, codi_qr_id: str) -> Cobro | None:
        """Busca por el id de pey: memoria y, si no está, el almacén (spec 003, RF-005, DP-33)."""
        cobro_id = self._por_codi_qr.get(codi_qr_id)
        if cobro_id is not None:
            return self._por_id.get(cobro_id)
        cargado = await self._almacen.cargar_por_codi_qr(codi_qr_id)
        if cargado is None:
            return None
        encontrado = self._por_id.get(cargado.id)
        if encontrado is not None:
            return encontrado
        self._indexar(cargado)
        return cargado

    async def aviso_ya_visto(self, webhook_id: str) -> bool:
        """Verdadero si el aviso está en memoria o en el almacén (spec 003, RF-003)."""
        if webhook_id in self._avisos:
            return True
        visto = await self._almacen.aviso_visto(webhook_id)
        if visto:
            self._avisos.add(webhook_id)
        return visto

    async def marcar_aviso(self, webhook_id: str, tipo: str) -> None:
        """Guarda el aviso en el almacén y después lo recuerda (spec 003, RF-003, DP-7)."""
        await self._almacen.guardar_aviso(webhook_id, tipo)
        self._avisos.add(webhook_id)

    async def registrar_pago(
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
        """Registra el pago una sola vez, con el candado del cobro (spec 003, RF-007, RF-008, DP-8).

        Si la transacción ya está en el cobro, no llama al almacén. El pago entra a la
        memoria solo cuando el almacén dice que es nuevo.
        """
        async with self._candado_de(cobro.id):
            if any(pago.transaccion_id == transaccion_id for pago in cobro.pagos):
                return None
            numero = len(cobro.pagos) + 1
            hora = int(self._reloj.ahora() if pagado_en is None else pagado_en)
            nuevo = await self._almacen.registrar_pago(
                cobro.id,
                transaccion_id=transaccion_id,
                numero=numero,
                monto_recibido=monto_recibido,
                monto_base=monto_base,
                pagado_en=hora,
                fuente=fuente,
                webhook_id=webhook_id,
                tipo_aviso=tipo_aviso,
            )
            if not nuevo:
                return None
            pago = Pago(
                transaccion_id=transaccion_id,
                numero=numero,
                monto_recibido=monto_recibido,
                monto_base=monto_base,
                pagado_en=hora,
                fuente=fuente,
                monto_del_cobro=cobro.monto,
            )
            cobro.pagos.append(pago)
            if pago.monto_distinto:
                comparado = pago.monto_base if pago.monto_base is not None else pago.monto_recibido
                registro.warning(
                    "Cobro %s: se pidió %s y se recibió %s",
                    cobro.id,
                    cobro.monto,
                    comparado,
                )
            return pago

    async def cancelar(self, cobro: Cobro, ahora: float) -> None:
        """Guarda la cancelación si el cobro sigue pendiente (spec 003, RF-004)."""
        if cobro.estado(ahora) != PENDIENTE:
            raise NoSePuedeCancelar
        hora = int(ahora)
        await self._almacen.cancelar(cobro.id, hora)
        cobro.cancelado_en = hora

    def _indexar(self, cobro: Cobro) -> None:
        """Lo deja en los dos índices, sin await entre medio (spec 003, DP-33)."""
        self._por_id[cobro.id] = cobro
        if cobro.codi_qr_id:
            self._por_codi_qr[cobro.codi_qr_id] = cobro.id

    def _candado_de(self, cobro_id: str) -> asyncio.Lock:
        """Un candado por cobro, creado sin await para que las dos peticiones compartan el mismo."""
        candado = self._candados.get(cobro_id)
        if candado is None:
            candado = asyncio.Lock()
            self._candados[cobro_id] = candado
        return candado
