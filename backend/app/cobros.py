"""Cobros del MVP, guardados en memoria. La base de datos definitiva llega en el issue #23."""

import logging
import secrets
from dataclasses import dataclass, field
from decimal import Decimal

from app.reloj import Reloj

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
    """Índices en memoria de cobros, transacciones y avisos (spec 001, data-model §5)."""

    def __init__(self, reloj: Reloj | None = None, gracia_segundos: int = 0) -> None:
        self._reloj = reloj or Reloj()
        self._gracia = gracia_segundos
        self._por_id: dict[str, Cobro] = {}
        self._por_codi_qr: dict[str, str] = {}
        self._transacciones: set[str] = set()
        self._avisos: set[str] = set()

    @property
    def vistas(self) -> set[str]:
        """Transacciones ya registradas, para no volver a contarlas (spec 001, RF-014)."""
        return self._transacciones

    def nuevo(self, monto: Decimal | None, concepto: str, expiracion: int, ahora: float) -> Cobro:
        """Crea un cobro con la hora del reloj (spec 001, RF-003, RF-006, RF-008, RF-022).

        `monto` None es un cobro de monto libre: no hay cantidad pedida.
        """
        creado_en = int(ahora)
        cobro = Cobro(
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
        self._por_id[cobro.id] = cobro
        return cobro

    def vincular_qr(self, cobro: Cobro, codi_qr_id: str, qr: str, qr_imagen: str | None) -> None:
        """Guarda el QR de pey y el índice para relacionar el aviso (spec 001, RF-012)."""
        cobro.codi_qr_id = codi_qr_id
        cobro.qr = qr
        cobro.qr_imagen = qr_imagen
        self._por_codi_qr[codi_qr_id] = cobro.id

    def descartar(self, cobro: Cobro) -> None:
        """Quita un cobro que pey no llegó a crear (spec 001, RF-009)."""
        self._por_id.pop(cobro.id, None)

    def obtener(self, cobro_id: str) -> Cobro | None:
        return self._por_id.get(cobro_id)

    def por_codi_qr(self, codi_qr_id: str) -> Cobro | None:
        return self._por_id.get(self._por_codi_qr.get(codi_qr_id, ""))

    def aviso_ya_visto(self, webhook_id: str) -> bool:
        """Primera barrera contra un aviso reenviado (spec 001, principio II)."""
        return webhook_id in self._avisos

    def marcar_aviso(self, webhook_id: str) -> None:
        """Recuerda el webhook-id. El prototipo lo marca antes de procesar, hasta F4."""
        self._avisos.add(webhook_id)

    def registrar_pago(
        self,
        cobro: Cobro,
        transaccion_id: str,
        monto_recibido: Decimal,
        monto_base: Decimal | None,
        pagado_en: int | None,
        fuente: str,
    ) -> Pago | None:
        """Agrega el pago o nada si esa transacción ya se vio (spec 001, RF-014 a RF-020)."""
        if transaccion_id in self._transacciones:
            return None
        hora = int(pagado_en if pagado_en is not None else self._reloj.ahora())
        pago = Pago(
            transaccion_id=transaccion_id,
            numero=len(cobro.pagos) + 1,
            monto_recibido=monto_recibido,
            monto_base=monto_base,
            pagado_en=hora,
            fuente=fuente,
            monto_del_cobro=cobro.monto,
        )
        cobro.pagos.append(pago)
        self._transacciones.add(transaccion_id)
        if pago.monto_distinto:
            comparado = pago.monto_base if pago.monto_base is not None else pago.monto_recibido
            registro.warning(
                "Cobro %s: se pidió %s y se recibió %s",
                cobro.id,
                cobro.monto,
                comparado,
            )
        return pago

    def cancelar(self, cobro: Cobro, ahora: float) -> None:
        """Guarda la cancelación solo si el cobro sigue pendiente (spec 001, RF-023, RF-024)."""
        if cobro.estado(ahora) != PENDIENTE:
            raise NoSePuedeCancelar
        cobro.cancelado_en = int(ahora)
