"""Pruebas del reloj, del cobro y de los pagos (spec 001, principio V, RF-008, RF-014 a RF-021)."""

import logging
import time
from decimal import Decimal

import pytest

from app.cobros import RepositorioCobros
from app.reloj import RelojFalso

CAMPOS_COBRO = {
    "id",
    "codi_qr_id",
    "monto",
    "monto_libre",
    "concepto",
    "estado",
    "qr",
    "qr_imagen",
    "creado_en",
    "expira_en",
    "fin_ventana",
    "numero_de_pagos",
    "total_recibido",
    "pagado_en",
    "pagos",
    "hora_servidor",
}
CAMPOS_PAGO = {"numero", "monto_recibido", "monto_distinto", "pagado_en"}


def _repositorio(inicio: float, gracia: int = 0) -> tuple[RelojFalso, RepositorioCobros]:
    reloj = RelojFalso(inicio=inicio)
    return reloj, RepositorioCobros(reloj, gracia_segundos=gracia)


def test_el_reloj_falso_avanza_solo_cuando_se_le_pide() -> None:
    """El reloj falso no se mueve hasta que la prueba llama a avanzar."""
    reloj = RelojFalso(inicio=1_794_700_000)
    assert reloj.ahora() == 1_794_700_000
    reloj.avanzar(10)
    assert reloj.ahora() == 1_794_700_010


@pytest.mark.asyncio
async def test_dormir_con_el_reloj_falso_adelanta_el_tiempo_sin_esperar() -> None:
    """dormir adelanta el reloj y no espera los segundos pedidos."""
    reloj = RelojFalso(inicio=1_794_700_000)
    inicio_real = time.perf_counter()
    await reloj.dormir(5)
    assert reloj.ahora() == 1_794_700_005
    assert time.perf_counter() - inicio_real < 0.5


def test_un_cobro_sin_pagos_vence_a_los_10_minutos() -> None:
    """expira_en es creado_en + 600; a los 599 s sigue pendiente y a los 600 vence (RF-021)."""
    _reloj, repo = _repositorio(1_794_700_000)
    cobro = repo.nuevo(Decimal("50"), "Tacos", 600, ahora=1_794_700_000)
    assert cobro.expira_en == cobro.creado_en + 600
    assert cobro.estado(cobro.creado_en + 599) == "pendiente"
    assert cobro.estado(cobro.creado_en + 600) == "vencido"


def test_el_estado_sigue_el_orden_pagos_cancelado_vencido_pendiente() -> None:
    """Pagos, luego cancelado, luego vencido, luego pendiente (spec 001, data-model §3)."""
    _reloj, repo = _repositorio(1_000)
    cobro = repo.nuevo(Decimal("50"), "Tacos", 600, ahora=1_000)
    assert cobro.estado(1_000) == "pendiente"
    assert cobro.estado(cobro.expira_en) == "vencido"
    cobro.cancelado_en = 1_000
    assert cobro.estado(cobro.expira_en) == "cancelado"
    repo.registrar_pago(cobro, "tx-1", Decimal("50"), None, 1_100, "aviso")
    assert cobro.estado(cobro.expira_en) == "pagado"


def test_la_ventana_de_escucha_termina_al_vencer_mas_la_gracia() -> None:
    """fin_ventana es expira_en + gracia, y en_ventana es ahora < fin_ventana (RF-032)."""
    for gracia in (0, 600):
        _reloj, repo = _repositorio(1_000, gracia)
        cobro = repo.nuevo(Decimal("10"), "Tacos", 600, ahora=1_000)
        assert cobro.fin_ventana == cobro.expira_en + gracia
        assert cobro.en_ventana(cobro.fin_ventana - 1) is True
        assert cobro.en_ventana(cobro.fin_ventana) is False


def test_el_pago_guarda_monto_recibido_base_hora_y_transaccion() -> None:
    """El aviso no trae monto_base; si falta datePaid, la hora es la del reloj (RF-018)."""
    reloj, repo = _repositorio(5_000)
    cobro = repo.nuevo(Decimal("50"), "Tacos", 600, ahora=reloj.ahora())
    por_aviso = repo.registrar_pago(cobro, "tx-aviso", Decimal("50"), None, None, "aviso")
    assert por_aviso is not None
    assert por_aviso.transaccion_id == "tx-aviso"
    assert por_aviso.numero == 1
    assert por_aviso.monto_recibido == Decimal("50")
    assert por_aviso.monto_base is None
    assert por_aviso.pagado_en == 5_000
    assert por_aviso.fuente == "aviso"

    por_consulta = repo.registrar_pago(
        cobro, "tx-consulta", Decimal("55"), Decimal("50"), 5_100, "consulta"
    )
    assert por_consulta is not None
    assert por_consulta.numero == 2
    assert por_consulta.monto_base == Decimal("50")
    assert por_consulta.pagado_en == 5_100
    assert por_consulta.fuente == "consulta"


def test_monto_distinto_compara_el_monto_base_o_el_recibido_con_el_pedido() -> None:
    """Con monto fijo, manda el base si existe; si no, el recibido (RF-019, RF-020)."""
    _reloj, repo = _repositorio(1_000)
    cobro = repo.nuevo(Decimal("50"), "Tacos", 600, ahora=1_000)
    recibido_distinto = repo.registrar_pago(cobro, "a", Decimal("40"), None, 1_000, "aviso")
    recibido_igual = repo.registrar_pago(cobro, "b", Decimal("50"), None, 1_000, "aviso")
    base_distinta = repo.registrar_pago(cobro, "c", Decimal("55"), Decimal("40"), 1_000, "consulta")
    base_igual = repo.registrar_pago(cobro, "d", Decimal("55"), Decimal("50"), 1_000, "consulta")
    assert recibido_distinto is not None and recibido_distinto.monto_distinto is True
    assert recibido_igual is not None and recibido_igual.monto_distinto is False
    assert base_distinta is not None and base_distinta.monto_distinto is True
    assert base_igual is not None and base_igual.monto_distinto is False

    libre = repo.nuevo(None, "Libre", 600, ahora=1_000)
    propina_libre = repo.registrar_pago(libre, "e", Decimal("12"), Decimal("12"), 1_000, "consulta")
    assert propina_libre is not None and propina_libre.monto_distinto is False


def test_el_objeto_publico_del_cobro_tiene_los_campos_del_contrato() -> None:
    """El JSON público tiene los 16 campos y el pago no lleva transaccion_id (RF-008, C-2)."""
    _reloj, repo = _repositorio(1_794_700_000)
    cobro = repo.nuevo(Decimal("0.01"), "Tacos", 600, ahora=1_794_700_000)
    repo.vincular_qr(cobro, "ab12cd34ef", '{"IDC":"x"}', "aW1n")
    repo.registrar_pago(cobro, "tx", Decimal("0.02"), None, 1_794_700_010, "aviso")
    publico = cobro.publico()
    assert set(publico) == CAMPOS_COBRO
    assert publico["codi_qr_id"] == "ab12cd34ef"
    assert publico["qr_imagen"] == "aW1n"
    assert publico["monto"] == 0.01
    assert publico["monto_libre"] is False
    assert publico["estado"] == "pagado"
    assert publico["numero_de_pagos"] == 1
    assert publico["total_recibido"] == 0.02
    assert publico["pagado_en"] == 1_794_700_010
    assert publico["fin_ventana"] == publico["expira_en"]
    pago_publico = publico["pagos"][0]
    assert set(pago_publico) == CAMPOS_PAGO
    assert pago_publico["numero"] == 1
    assert pago_publico["monto_distinto"] is True


def test_el_primer_pago_pasa_a_pagado_desde_pendiente_vencido_o_cancelado() -> None:
    """El primer pago deja el cobro pagado desde pendiente, vencido o cancelado (RF-017)."""
    for origen in ("pendiente", "vencido", "cancelado"):
        _reloj, repo = _repositorio(1_000)
        cobro = repo.nuevo(Decimal("10"), "Tacos", 600, ahora=1_000)
        if origen == "vencido":
            assert cobro.estado(cobro.expira_en) == "vencido"
        elif origen == "cancelado":
            cobro.cancelado_en = 1_000
            assert cobro.estado(1_000) == "cancelado"
        else:
            assert cobro.estado(1_000) == "pendiente"
        pago = repo.registrar_pago(cobro, f"tx-{origen}", Decimal("10"), None, 1_200, "aviso")
        assert pago is not None
        assert cobro.estado(cobro.expira_en + 10) == "pagado"


def test_una_transaccion_ya_vista_no_se_registra_otra_vez() -> None:
    """El mismo transaccion_id no se registra ni en otro cobro ni por otra fuente (RF-014)."""
    _reloj, repo = _repositorio(1_000)
    uno = repo.nuevo(Decimal("10"), "Uno", 600, ahora=1_000)
    otro = repo.nuevo(Decimal("10"), "Otro", 600, ahora=1_000)
    assert repo.registrar_pago(uno, "tx", Decimal("10"), None, 1_000, "aviso") is not None
    assert repo.registrar_pago(uno, "tx", Decimal("10"), None, 1_001, "consulta") is None
    assert repo.registrar_pago(otro, "tx", Decimal("10"), None, 1_002, "aviso") is None
    assert uno.numero_de_pagos == 1
    assert otro.numero_de_pagos == 0


def test_un_qr_reutilizado_registra_y_numera_cada_pago() -> None:
    """Tres transacciones distintas quedan como pagos 1, 2 y 3 y el cobro sigue pagado (C-1)."""
    _reloj, repo = _repositorio(1_000)
    cobro = repo.nuevo(Decimal("10"), "Tacos", 600, ahora=1_000)
    montos = (Decimal("10"), Decimal("4"), Decimal("1"))
    horas = (1_100, 1_200, 1_300)
    for numero, monto, hora in zip((1, 2, 3), montos, horas, strict=True):
        pago = repo.registrar_pago(cobro, f"tx-{numero}", monto, None, hora, "aviso")
        assert pago is not None
        assert pago.numero == numero
    assert cobro.numero_de_pagos == 3
    assert cobro.total_recibido == Decimal("15")
    assert cobro.pagado_en == 1_300
    assert cobro.estado(2_000) == "pagado"


def test_un_monto_base_distinto_se_marca_y_deja_advertencia(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Base distinta del pedido marca el pago y deja un WARNING (RF-019, RF-020)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    _reloj, repo = _repositorio(1_000)
    cobro = repo.nuevo(Decimal("50"), "Tacos", 600, ahora=1_000)
    pago = repo.registrar_pago(cobro, "tx", Decimal("40"), Decimal("40"), 1_000, "consulta")
    assert pago is not None and pago.monto_distinto is True
    advertencias = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any(
        cobro.id in mensaje and "50" in mensaje and "40" in mensaje for mensaje in advertencias
    )


def test_una_propina_no_cuenta_como_monto_distinto(caplog: pytest.LogCaptureFixture) -> None:
    """Si el base coincide, la propina no es monto distinto ni deja advertencia (RF-020)."""
    caplog.set_level(logging.WARNING, logger="pago_facil")
    _reloj, repo = _repositorio(1_000)
    cobro = repo.nuevo(Decimal("50"), "Tacos", 600, ahora=1_000)
    pago = repo.registrar_pago(cobro, "tx", Decimal("55"), Decimal("50"), 1_000, "consulta")
    assert pago is not None and pago.monto_distinto is False
    assert [
        r for r in caplog.records if r.name == "pago_facil" and r.levelno >= logging.WARNING
    ] == []


def test_el_objeto_publico_trae_la_hora_actual_del_servidor_como_entero() -> None:
    """hora_servidor es la hora del reloj al armar el objeto, en segundos enteros (RF-008, C-2)."""
    reloj, repo = _repositorio(1_794_700_009)
    cobro = repo.nuevo(Decimal("1"), "Tacos", 600, ahora=1_794_700_000)
    assert cobro.publico()["hora_servidor"] == 1_794_700_009
    reloj.avanzar(5.7)
    assert cobro.publico()["hora_servidor"] == 1_794_700_014
