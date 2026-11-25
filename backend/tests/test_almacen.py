"""Contrato del almacén, en memoria y en PostgreSQL (spec 003, T051).

La de postgres aplica las migraciones con ``ejecutar`` (la función del comando,
no el proceso) y se salta sin ``PRUEBAS_DATABASE_URL``.
"""

import secrets
from collections.abc import AsyncIterator, Coroutine
from datetime import UTC, datetime
from decimal import Decimal

import psycopg
import pytest
import pytest_asyncio
from pydantic import SecretStr

from app.almacen import AlmacenEnMemoria, ErrorDeAlmacen, ErrorDeDatos
from app.almacen_postgres import AlmacenPostgres
from app.cobros import Cobro
from app.migraciones import CARPETA_MIGRACIONES, ejecutar
from app.reloj import RelojFalso

URL_CERRADA = "postgresql://usuario-falso:clave-falsa@127.0.0.1:1/prueba"
# 2020-06-15 12:00:00 UTC. No es la hora de la base.
INICIO_2020 = datetime(2020, 6, 15, 12, 0, tzinfo=UTC).timestamp()


def _nuevo(
    reloj: RelojFalso,
    monto: Decimal | None = Decimal("12.50"),
    concepto: str = "Tacos",
) -> Cobro:
    """Arma el cobro directo: T057 cambia el constructor de ``RepositorioCobros``."""
    creado_en = int(reloj.ahora())
    return Cobro(
        id=secrets.token_urlsafe(9),
        monto=monto,
        concepto=concepto,
        num_ref=str(secrets.randbelow(9_000_000) + 1_000_000),
        creado_en=creado_en,
        expira_en=creado_en + 600,
        fin_ventana=creado_en + 600,
        reloj=reloj,
    )


@pytest_asyncio.fixture(params=["memoria", "postgres"])
async def almacen(request: pytest.FixtureRequest, reloj: RelojFalso) -> AsyncIterator[object]:
    """Almacén en memoria, o PostgreSQL vacío con las migraciones aplicadas (spec 003, T051)."""
    if request.param == "memoria":
        objeto = AlmacenEnMemoria(reloj=reloj)
    else:
        url = request.getfixturevalue("base_vacia")
        codigo, texto = ejecutar(url, CARPETA_MIGRACIONES, "aplicar", entorno="local")
        assert codigo == 0, texto
        objeto = AlmacenPostgres(SecretStr(url), reloj)
    await objeto.abrir()
    try:
        yield objeto
    finally:
        await objeto.cerrar()


@pytest.mark.asyncio
async def test_un_cobro_guardado_se_carga_igual(almacen, request: pytest.FixtureRequest) -> None:
    """El cobro vuelve con los mismos campos; el vacío es "" y en la base es null.

    (spec 003, RF-001).
    """
    reloj = RelojFalso(inicio=1_794_700_000)
    fijo = _nuevo(reloj, Decimal("12.50"))
    libre = _nuevo(reloj, None, "Libre")
    await almacen.guardar_cobro(fijo)
    await almacen.guardar_cobro(libre)

    cargado = await almacen.cargar_por_id(fijo.id)
    assert cargado is not None
    assert cargado.monto == Decimal("12.50")
    assert cargado.monto_libre is False
    assert cargado.concepto == fijo.concepto
    assert cargado.num_ref == fijo.num_ref
    assert cargado.creado_en == fijo.creado_en
    assert cargado.expira_en == fijo.expira_en
    assert cargado.fin_ventana == fijo.fin_ventana
    assert cargado.codi_qr_id == ""
    assert cargado.qr == ""
    assert cargado.qr_imagen is None
    assert cargado.cancelado_en is None
    assert cargado.pagos == []

    sin_monto = await almacen.cargar_por_id(libre.id)
    assert sin_monto is not None
    assert sin_monto.monto is None
    assert sin_monto.monto_libre is True

    if type(almacen).__name__ == "AlmacenPostgres":
        filas = _filas(
            request.getfixturevalue("base_vacia"),
            "select codi_qr_id, qr from cobros where id = %s",
            (fijo.id,),
        )
        assert filas == [(None, None)]


@pytest.mark.asyncio
async def test_el_qr_guardado_se_carga_por_codi_qr_id_con_su_imagen(almacen) -> None:
    """El QR y su imagen se cargan por codi_qr_id; sin imagen, vuelve None.

    (spec 003, RF-010, RF-011).
    """
    reloj = RelojFalso(inicio=1_794_700_000)
    con_imagen = _nuevo(reloj)
    await almacen.guardar_cobro(con_imagen)
    con_imagen.codi_qr_id = "qr-con-imagen"
    con_imagen.qr = '{"IDC":"con"}'
    con_imagen.qr_imagen = "aW1n"
    await almacen.guardar_qr(con_imagen)

    cargado = await almacen.cargar_por_codi_qr("qr-con-imagen")
    assert cargado is not None
    assert cargado.id == con_imagen.id
    assert cargado.qr == '{"IDC":"con"}'
    assert cargado.qr_imagen == "aW1n"

    sin_imagen = _nuevo(reloj, Decimal("1"))
    await almacen.guardar_cobro(sin_imagen)
    sin_imagen.codi_qr_id = "qr-sin-imagen"
    sin_imagen.qr = '{"IDC":"sin"}'
    sin_imagen.qr_imagen = None
    await almacen.guardar_qr(sin_imagen)
    vacio = await almacen.cargar_por_codi_qr("qr-sin-imagen")
    assert vacio is not None
    assert vacio.qr_imagen is None


@pytest.mark.asyncio
async def test_un_cobro_borrado_ya_no_se_carga(almacen) -> None:
    """Borrar el cobro lo quita del almacén (spec 003, RF-052)."""
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    await almacen.borrar_cobro(cobro.id)
    assert await almacen.cargar_por_id(cobro.id) is None


@pytest.mark.asyncio
async def test_la_cancelacion_se_guarda_una_sola_vez(almacen) -> None:
    """La segunda cancelación no pisa la hora (spec 003, RF-004)."""
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    await almacen.cancelar(cobro.id, 1_794_700_100)
    await almacen.cancelar(cobro.id, 1_794_700_500)
    cargado = await almacen.cargar_por_id(cobro.id)
    assert cargado is not None
    assert cargado.cancelado_en == 1_794_700_100


@pytest.mark.asyncio
async def test_on_conflict_no_duplica_la_transaccion(almacen) -> None:
    """La misma transacción la primera vez es nueva y la segunda no (spec 003, RF-007)."""
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    pago = _pago()
    assert await almacen.registrar_pago(cobro.id, **pago) is True
    assert await almacen.registrar_pago(cobro.id, **pago) is False
    cargado = await almacen.cargar_por_id(cobro.id)
    assert cargado is not None
    assert len(cargado.pagos) == 1


@pytest.mark.asyncio
async def test_el_pago_y_su_webhook_id_se_guardan_juntos(almacen) -> None:
    """Registrar el pago con webhook_id deja el aviso visto (spec 003, DP-9, RF-003)."""
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    await almacen.registrar_pago(cobro.id, **_pago(webhook_id="msg_1"))
    assert await almacen.aviso_visto("msg_1") is True
    assert await almacen.aviso_visto("msg_otro") is False


@pytest.mark.asyncio
async def test_los_pagos_se_cargan_en_orden_de_numero(almacen) -> None:
    """Aunque se guarden al revés, al cargar vienen 1 y después 2 (spec 003, RF-008)."""
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    await almacen.registrar_pago(cobro.id, **_pago(transaccion_id="tx-2", numero=2))
    await almacen.registrar_pago(cobro.id, **_pago(transaccion_id="tx-1", numero=1))
    cargado = await almacen.cargar_por_id(cobro.id)
    assert cargado is not None
    assert [pago.numero for pago in cargado.pagos] == [1, 2]


@pytest.mark.asyncio
async def test_cobros_con_ventana_terminada_respeta_el_rango(almacen) -> None:
    """(desde, hasta], solo con codi_qr_id, en orden de fin_ventana (spec 003, RF-061)."""
    reloj = RelojFalso(inicio=1_000)
    incluidos = []
    for fin, qr in ((300, "qr-300"), (400, "qr-400")):
        cobro = _con_ventana(reloj, fin, qr)
        await almacen.guardar_cobro(cobro)
        await almacen.guardar_qr(cobro)
        incluidos.append(cobro.id)
    for fin, qr in ((200, "qr-200"), (500, "qr-500"), (350, "")):
        cobro = _con_ventana(reloj, fin, qr)
        await almacen.guardar_cobro(cobro)
        if qr:
            await almacen.guardar_qr(cobro)

    hallados = await almacen.cobros_con_ventana_terminada(200, 400)
    assert [cobro.id for cobro in hallados] == incluidos
    assert [cobro.fin_ventana for cobro in hallados] == [300, 400]


@pytest.mark.asyncio
async def test_conciliado_hasta_empieza_vacio_y_se_guarda(almacen) -> None:
    """Sin fila la marca está vacía; después se lee la hora guardada (spec 003, RF-061)."""
    assert await almacen.leer_conciliado_hasta() is None
    await almacen.guardar_conciliado_hasta(1_794_700_000)
    assert await almacen.leer_conciliado_hasta() == 1_794_700_000


async def _rechazo(operacion: Coroutine[object, object, object]) -> ErrorDeDatos:
    """Espera la operación y devuelve el ``ErrorDeDatos`` que lanza."""
    with pytest.raises(ErrorDeDatos) as error:
        await operacion
    return error.value


@pytest.mark.asyncio
async def test_guardar_el_mismo_cobro_dos_veces_lanza_error_de_datos(almacen) -> None:
    """Un id repetido lo rechaza la llave primaria, en memoria igual que en la base.

    (spec 003, DP-34, RF-021).
    """
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    error = await _rechazo(almacen.guardar_cobro(cobro))
    assert (error.operacion, error.clase) == ("guardar cobro", "UniqueViolation")


@pytest.mark.asyncio
async def test_un_codi_qr_id_de_otro_cobro_lanza_error_de_datos(almacen) -> None:
    """El id de pey es único: el segundo cobro con el mismo se rechaza (spec 003, DP-34)."""
    reloj = RelojFalso(inicio=1_794_700_000)
    uno, otro = _nuevo(reloj), _nuevo(reloj)
    await almacen.guardar_cobro(uno)
    await almacen.guardar_cobro(otro)
    uno.codi_qr_id = otro.codi_qr_id = "qr-repetido"
    uno.qr = otro.qr = "{}"
    await almacen.guardar_qr(uno)
    error = await _rechazo(almacen.guardar_qr(otro))
    assert (error.operacion, error.clase) == ("guardar QR", "UniqueViolation")


@pytest.mark.asyncio
async def test_un_numero_de_pago_repetido_lanza_error_de_datos(almacen) -> None:
    """Dos transacciones distintas no pueden llevar el mismo número (spec 003, DP-8, DP-34)."""
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    await almacen.registrar_pago(cobro.id, **_pago(transaccion_id="tx-1", numero=1))
    error = await _rechazo(
        almacen.registrar_pago(cobro.id, **_pago(transaccion_id="tx-2", numero=1))
    )
    assert (error.operacion, error.clase) == ("registrar pago", "UniqueViolation")


@pytest.mark.asyncio
async def test_un_pago_de_un_cobro_que_no_existe_lanza_error_de_datos(almacen) -> None:
    """Un pago sin cobro se rechaza, como la llave ajena de la base (spec 003, DP-34)."""
    error = await _rechazo(almacen.registrar_pago("no-existe-00", **_pago()))
    assert (error.operacion, error.clase) == ("registrar pago", "ForeignKeyViolation")


@pytest.mark.asyncio
async def test_un_cobro_con_pagos_no_se_borra(almacen) -> None:
    """Borrar un cobro con pagos se rechaza y el cobro conserva sus pagos.

    (spec 003, RF-052, DP-34).
    """
    cobro = _nuevo(RelojFalso(inicio=1_794_700_000))
    await almacen.guardar_cobro(cobro)
    await almacen.registrar_pago(cobro.id, **_pago())
    error = await _rechazo(almacen.borrar_cobro(cobro.id))
    assert (error.operacion, error.clase) == ("borrar cobro", "ForeignKeyViolation")
    cargado = await almacen.cargar_por_id(cobro.id)
    assert cargado is not None
    assert len(cargado.pagos) == 1


@pytest.mark.asyncio
async def test_los_registros_del_pool_no_traen_el_usuario_ni_el_host(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """psycopg_pool registra usuario, host y puerto al fallar la conexión.

    El almacén los calla: la URL no puede salir en los registros (spec 003, RF-021, CE-010).
    """
    caplog.set_level("DEBUG")
    reloj = RelojFalso(inicio=INICIO_2020)
    cerrado = AlmacenPostgres(SecretStr(URL_CERRADA), reloj)
    await cerrado.abrir()
    try:
        with pytest.raises(ErrorDeAlmacen):
            await cerrado.guardar_cobro(_nuevo(reloj), espera=0.5)
    finally:
        await cerrado.cerrar()
    for fragmento in ("usuario-falso", "clave-falsa", "127.0.0.1"):
        assert fragmento not in caplog.text


@pytest.mark.asyncio
async def test_las_horas_guardadas_son_las_del_reloj_del_servidor(base_vacia: str) -> None:
    """creado_en, registrado_en y recibido_en son la hora del reloj, no la de la base.

    (spec 003, RF-006).
    """
    reloj = RelojFalso(inicio=INICIO_2020)
    codigo, texto = ejecutar(base_vacia, CARPETA_MIGRACIONES, "aplicar", entorno="local")
    assert codigo == 0, texto
    postgres = AlmacenPostgres(SecretStr(base_vacia), reloj)
    await postgres.abrir()
    try:
        cobro = _nuevo(reloj, Decimal("0.01"))
        await postgres.guardar_cobro(cobro)
        await postgres.registrar_pago(
            cobro.id,
            **_pago(pagado_en=1_500_000_000, webhook_id="msg_hora"),
        )
        creados = _filas(base_vacia, "select creado_en from cobros where id = %s", (cobro.id,))
        registrados = _filas(
            base_vacia,
            "select registrado_en from pagos where transaccion_id = %s",
            ("tx-1",),
        )
        recibidos = _filas(
            base_vacia,
            "select recibido_en from avisos_webhook where webhook_id = %s",
            ("msg_hora",),
        )
    finally:
        await postgres.cerrar()
    hora = datetime.fromtimestamp(INICIO_2020, UTC)
    assert _en_utc(creados[0][0]) == hora
    assert _en_utc(registrados[0][0]) == hora
    assert _en_utc(recibidos[0][0]) == hora
    assert hora.year == 2020


@pytest.mark.asyncio
async def test_sin_respuesta_lanza_error_de_almacen_sin_datos_de_conexion() -> None:
    """Una base cerrada lanza ErrorDeAlmacen sin la URL (spec 003, RF-021, DP-15)."""
    reloj = RelojFalso(inicio=INICIO_2020)
    cerrado = AlmacenPostgres(SecretStr(URL_CERRADA), reloj)
    await cerrado.abrir()
    cobro = _nuevo(reloj)
    try:
        with pytest.raises(ErrorDeAlmacen) as error:
            # El puerto 1 rechaza la conexión. El tope evita un cuelgue si no la rechazara.
            await cerrado.guardar_cobro(cobro, espera=1)
    finally:
        await cerrado.cerrar()
    texto = str(error.value)
    assert error.value.operacion in texto
    assert error.value.clase in texto
    assert "guardar cobro" in texto
    for fragmento in ("usuario-falso", "clave-falsa", "127.0.0.1"):
        assert fragmento not in texto


def _pago(
    *,
    transaccion_id: str = "tx-1",
    numero: int = 1,
    webhook_id: str | None = None,
    pagado_en: int = 1_794_700_050,
) -> dict[str, object]:
    return {
        "transaccion_id": transaccion_id,
        "numero": numero,
        "monto_recibido": Decimal("12.50"),
        "monto_base": None,
        "pagado_en": pagado_en,
        "fuente": "aviso",
        "webhook_id": webhook_id,
        "tipo_aviso": "codi.qr.payment_received" if webhook_id else "",
    }


def _con_ventana(reloj: RelojFalso, fin: int, codi_qr_id: str) -> Cobro:
    cobro = _nuevo(reloj, Decimal("1"), f"v{fin}")
    cobro.creado_en = 1
    cobro.expira_en = fin
    cobro.fin_ventana = fin
    if codi_qr_id:
        cobro.codi_qr_id = codi_qr_id
        cobro.qr = codi_qr_id
    return cobro


def _filas(url: str, sentencia: str, parametros: tuple[object, ...]) -> list[tuple]:
    """Lee la base de la prueba. Si falla, el error no incluye la URL."""
    try:
        with psycopg.connect(url, connect_timeout=5) as conexion:
            return list(conexion.execute(sentencia, parametros).fetchall())
    except psycopg.Error as error:
        raise AssertionError(
            f"No se pudo leer la base de la prueba ({type(error).__name__})."
        ) from None


def _en_utc(momento: datetime) -> datetime:
    return momento.astimezone(UTC).replace(microsecond=0)
