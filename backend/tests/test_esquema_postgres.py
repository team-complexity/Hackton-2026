"""Pruebas del esquema contra un PostgreSQL desechable (issue #110).

Convierten en pruebas automáticas las secciones C y D de
``supabase/consultas_de_verificacion.sql``: el estado de los cobros y que un
pago no se cuente dos veces (principio II).

Aplican las migraciones con ``app.migraciones`` en entorno local y cargan
``supabase/datos_de_prueba.sql``. Sin ``PRUEBAS_DATABASE_URL`` se saltan y no
imprimen la URL.
"""

from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

from app.migraciones import ejecutar

CARPETA_MIGRACIONES = Path(__file__).resolve().parents[2] / "supabase" / "migraciones"
TRANSACCION_EXISTENTE = "01PRUEBATRANSACCION0000001"

INSERTAR_PAGO = """
    insert into pagos (cobro_id, transaccion_id, numero, monto_recibido, pagado_en, fuente)
    values ('prueba-pagado', %s, 2, 80.00, now(), 'consulta')
"""


@pytest.fixture
def base_con_datos(base_vacia: str) -> str:
    """Base desechable con las migraciones y los datos de prueba (entorno local)."""
    codigo, _texto = ejecutar(
        base_vacia,
        CARPETA_MIGRACIONES,
        "aplicar",
        entorno="local",
        datos_de_prueba=True,
    )
    assert codigo == 0, "No se pudieron aplicar las migraciones con los datos de prueba."
    return base_vacia


@pytest.fixture
def conexion(base_con_datos: str) -> Iterator[psycopg.Connection]:
    """Conexión a la base con datos. Si falla, el error no incluye la URL."""
    try:
        abierta = psycopg.connect(base_con_datos, connect_timeout=5)
    except psycopg.Error as error:
        raise AssertionError(
            f"No se pudo conectar con la base desechable ({type(error).__name__})."
        ) from None
    with abierta:
        yield abierta


def _pagos_del_cobro(conexion: psycopg.Connection, cobro_id: str) -> tuple[int, object]:
    """Devuelve cuántos pagos tiene el cobro y su ``total_recibido`` según la vista."""
    fila = conexion.execute(
        "select numero_de_pagos, total_recibido from cobros_con_estado where id = %s",
        (cobro_id,),
    ).fetchone()
    assert fila is not None
    return int(fila[0]), fila[1]


def test_la_vista_devuelve_el_estado_de_cada_cobro_de_prueba(
    conexion: psycopg.Connection,
) -> None:
    """cobros_con_estado marca pendiente, pagado, vencido y cancelado (consultas, sección D)."""
    filas = conexion.execute(
        "select id, estado from cobros_con_estado where id like 'prueba-%' order by id"
    ).fetchall()
    assert dict(filas) == {
        "prueba-pendiente": "pendiente",
        "prueba-pagado": "pagado",
        "prueba-vencido": "vencido",
        "prueba-cancelado": "cancelado",
    }


def test_un_pago_repetido_con_on_conflict_no_se_cuenta_dos_veces(
    conexion: psycopg.Connection,
) -> None:
    """Repetir un transaccion_id con on conflict no agrega filas (principio II, sección C)."""
    antes = _pagos_del_cobro(conexion, "prueba-pagado")
    assert antes[0] == 1

    cursor = conexion.execute(
        INSERTAR_PAGO + " on conflict (transaccion_id) do nothing",
        (TRANSACCION_EXISTENTE,),
    )
    conexion.commit()

    assert cursor.rowcount == 0
    assert _pagos_del_cobro(conexion, "prueba-pagado") == antes


def test_un_transaccion_id_repetido_sin_on_conflict_lo_rechaza_la_base(
    conexion: psycopg.Connection,
) -> None:
    """Sin on conflict, la base lanza UniqueViolation y el pago no cambia (principio II)."""
    antes = _pagos_del_cobro(conexion, "prueba-pagado")

    with pytest.raises(psycopg.errors.UniqueViolation):
        conexion.execute(INSERTAR_PAGO, (TRANSACCION_EXISTENTE,))
    conexion.rollback()

    assert _pagos_del_cobro(conexion, "prueba-pagado") == antes
