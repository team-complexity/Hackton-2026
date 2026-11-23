"""Pruebas del comando contra un PostgreSQL desechable (spec 003, T038).

Llaman a ``app.migraciones.ejecutar``, que todavía no existe (principio V)::

    ejecutar(
        url, carpeta, accion, *,
        entorno=None, ya_aplicada=None, datos_de_prueba=False,
    ) -> tuple[int, str]

``accion`` es ``"estado"`` o ``"aplicar"``. ``texto`` es lo que el comando
escribe. Con ``datos_de_prueba=True`` carga ``carpeta.parent / "datos_de_prueba.sql"``.
Sin ``PRUEBAS_DATABASE_URL`` se saltan (R-10). No imprimen la URL.
"""

import importlib
from decimal import Decimal
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

CARPETA_MIGRACIONES = Path(__file__).resolve().parents[2] / "supabase" / "migraciones"
IDS_DE_PRUEBA = (
    "prueba-cancelado",
    "prueba-pagado",
    "prueba-pendiente",
    "prueba-vencido",
)
MENSAJE_SIN_ENTORNO = "Es la primera vez en esta base: indica --entorno local o --entorno demo."
MENSAJE_SIN_REGISTRO = (
    "Esta base ya tiene el esquema del PR #97 sin registro. "
    "Revísalo y corre: aplicar --ya-aplicada 0001."
)
MENSAJE_FALLO = "La versión 0002 falló y no se aplicó nada de ella (UndefinedTable)."
MENSAJE_NADA = "No había nada que aplicar."
MENSAJE_DATOS = "Los datos de prueba solo se cargan en la base local."


def _exigir_comando() -> None:
    """Falla en la prueba si ``app.migraciones`` todavía no existe."""
    importlib.import_module("app.migraciones")


def _conectar(url: str) -> psycopg.Connection:
    """Abre la base desechable. Si falla, el error no incluye la URL."""
    try:
        return psycopg.connect(url, connect_timeout=5)
    except psycopg.Error as error:
        raise AssertionError(
            f"No se pudo conectar con la base desechable ({type(error).__name__})."
        ) from None


def _consulta(url: str, sentencia: str, parametros: tuple | None = None) -> list[tuple]:
    """Corre una sentencia y devuelve sus filas, o ``[]`` si no produce ninguna.

    Sin parámetros no se pasa ``()``: psycopg tomaría el ``%`` de un ``like`` como marcador.
    """
    with _conectar(url) as conexion:
        cursor = conexion.execute(sentencia, parametros)
        filas = list(cursor.fetchall()) if cursor.description is not None else []
        conexion.commit()
        return filas


def _tablas(url: str) -> set[str]:
    filas = _consulta(
        url,
        """
        select table_name
        from information_schema.tables
        where table_schema = 'public' and table_type = 'BASE TABLE'
        """,
    )
    return {str(fila[0]) for fila in filas}


def _vistas(url: str) -> set[str]:
    filas = _consulta(
        url,
        """
        select table_name
        from information_schema.views
        where table_schema = 'public'
        """,
    )
    return {str(fila[0]) for fila in filas}


def _columnas(url: str, tabla: str) -> set[str]:
    filas = _consulta(
        url,
        """
        select column_name
        from information_schema.columns
        where table_schema = 'public' and table_name = %s
        """,
        (tabla,),
    )
    return {str(fila[0]) for fila in filas}


def _versiones(url: str) -> list[str]:
    filas = _consulta(url, "select version from cambios_de_estructura order by version")
    return [str(fila[0]) for fila in filas]


def _entorno(url: str) -> str | None:
    filas = _consulta(url, "select nombre from entorno_de_la_base")
    if not filas:
        return None
    return str(filas[0][0])


def _ejecutar(
    url: str,
    accion: str,
    *,
    carpeta: Path | None = None,
    entorno: str | None = None,
    ya_aplicada: str | None = None,
    datos_de_prueba: bool = False,
) -> tuple[int, str]:
    """Llama a ``ejecutar`` y rechaza una salida que incluya la URL."""
    _exigir_comando()
    from app.migraciones import ejecutar

    try:
        codigo, texto = ejecutar(
            url,
            carpeta or CARPETA_MIGRACIONES,
            accion,
            entorno=entorno,
            ya_aplicada=ya_aplicada,
            datos_de_prueba=datos_de_prueba,
        )
    except Exception as error:
        if url in str(error):
            raise AssertionError(
                f"ejecutar falló con {type(error).__name__} y el texto incluye la URL."
            ) from None
        raise
    if not isinstance(codigo, int) or not isinstance(texto, str):
        raise AssertionError("ejecutar debe devolver (codigo: int, texto: str).")
    if url in texto:
        raise AssertionError("La salida del comando incluye la URL de la base.")
    return codigo, texto


def _correr_script(url: str, script: str) -> None:
    """Corre el SQL de una migración a mano, sentencia por sentencia.

    psycopg ejecuta una sentencia a la vez. Se quitan los comentarios ``--``
    porque el esquema trae ``;`` dentro de comentarios que no deben correr.
    """
    lineas = [linea.split("--", 1)[0] for linea in script.splitlines()]
    with _conectar(url) as conexion:
        for sentencia in "\n".join(lineas).split(";"):
            if sentencia.strip():
                conexion.execute(sentencia)
        conexion.commit()


def _sql_de(nombre: str) -> str:
    return (CARPETA_MIGRACIONES / nombre).read_text(encoding="utf-8")


def _exige_sin_permiso(url: str, rol: str, tabla: str, orden: str) -> None:
    with _conectar(url) as conexion:
        conexion.execute(sql.SQL("set role {}").format(sql.Identifier(rol)))
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conexion.execute(sql.SQL(orden).format(sql.Identifier(tabla)))


def test_aplicar_en_una_base_vacia_crea_el_esquema_la_imagen_y_el_estado(
    base_vacia: str,
) -> None:
    """Aplicar con --entorno local deja el esquema, la imagen y el estado (spec 003, RF-018)."""
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="local")
    assert codigo == 0
    assert {
        "negocios",
        "cupones",
        "cobros",
        "pagos",
        "avisos_webhook",
        "estado_del_servidor",
        "cambios_de_estructura",
        "entorno_de_la_base",
    } <= _tablas(base_vacia)
    assert "cobros_con_estado" in _vistas(base_vacia)
    assert "qr_imagen" in _columnas(base_vacia, "cobros")
    assert _versiones(base_vacia) == ["0001", "0002", "0003"]
    assert _entorno(base_vacia) == "local"


def test_aplicar_dos_veces_no_cambia_nada(base_vacia: str) -> None:
    """La segunda vez no cambia nada y conserva una fila puesta entre medias (spec 003, RF-019)."""
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="local")
    assert codigo == 0
    _consulta(
        base_vacia,
        "insert into avisos_webhook (webhook_id, tipo) values (%s, %s)",
        ("msg-entre-medias", "codi.qr.payment_received"),
    )
    codigo, texto = _ejecutar(base_vacia, "aplicar")
    assert codigo == 0
    assert MENSAJE_NADA in texto
    filas = _consulta(
        base_vacia,
        "select webhook_id from avisos_webhook where webhook_id = %s",
        ("msg-entre-medias",),
    )
    assert filas == [("msg-entre-medias",)]


def test_una_migracion_que_falla_no_deja_nada_a_medias(base_vacia: str, tmp_path: Path) -> None:
    """Si 0002 falla, no queda su tabla ni su registro, y 0001 sí (spec 003, RF-019)."""
    (tmp_path / "0001_base.sql").write_text(
        "create table queda (id int primary key);\n",
        encoding="utf-8",
    )
    (tmp_path / "0002_falla.sql").write_text(
        "create table no_queda (id int primary key);\nselect * from tabla_que_no_existe;\n",
        encoding="utf-8",
    )
    codigo, texto = _ejecutar(base_vacia, "aplicar", carpeta=tmp_path, entorno="local")
    assert codigo == 1
    assert MENSAJE_FALLO in texto
    assert "queda" in _tablas(base_vacia)
    assert "no_queda" not in _tablas(base_vacia)
    assert _versiones(base_vacia) == ["0001"]


def test_la_primera_vez_sin_entorno_se_detiene(base_vacia: str) -> None:
    """La primera vez sin --entorno se detiene (spec 003, RF-049)."""
    codigo, texto = _ejecutar(base_vacia, "aplicar")
    assert codigo == 1
    assert MENSAJE_SIN_ENTORNO in texto


def test_una_base_con_el_esquema_sin_registro_pide_ya_aplicada(base_vacia: str) -> None:
    """Con el SQL de 0001 ya corrido, aplicar pide --ya-aplicada 0001 (spec 003, DP-19)."""
    _exigir_comando()
    _correr_script(base_vacia, _sql_de("0001_esquema_inicial.sql"))
    codigo, texto = _ejecutar(base_vacia, "aplicar", entorno="demo")
    assert codigo == 1
    assert MENSAJE_SIN_REGISTRO in texto


def test_ya_aplicada_solo_agrega_lo_que_falta(base_vacia: str) -> None:
    """--ya-aplicada 0001 anota 0001 sin correrla y deja el cobro (spec 003, historia 6)."""
    _exigir_comando()
    _correr_script(base_vacia, _sql_de("0001_esquema_inicial.sql"))
    _consulta(
        base_vacia,
        """
        insert into cobros (id, monto, concepto, num_ref, creado_en, expira_en, fin_ventana)
        values (%s, %s, %s, %s, now(), now() + interval '10 min', now() + interval '20 min')
        """,
        ("cobrodemo1", Decimal("10.00"), "Tacos", "1234567"),
    )
    codigo, _texto = _ejecutar(
        base_vacia,
        "aplicar",
        entorno="demo",
        ya_aplicada="0001",
    )
    assert codigo == 0
    assert _versiones(base_vacia) == ["0001", "0002", "0003"]
    assert "qr_imagen" in _columnas(base_vacia, "cobros")
    assert "estado_del_servidor" in _tablas(base_vacia)
    assert _entorno(base_vacia) == "demo"
    filas = _consulta(base_vacia, "select id from cobros where id = %s", ("cobrodemo1",))
    assert filas == [("cobrodemo1",)]


def test_ya_aplicada_se_rechaza_si_no_existe_cobros(base_vacia: str) -> None:
    """--ya-aplicada 0001 en una base vacía sale con 1 y no deja nada (spec 003, DP-19).

    También se pasa ``--entorno local``: sin eso, el rechazo podría ser el de
    la primera vez y esta prueba no comprobaría la regla de DP-19.
    """
    antes = _tablas(base_vacia)
    codigo, _texto = _ejecutar(
        base_vacia,
        "aplicar",
        entorno="local",
        ya_aplicada="0001",
    )
    assert codigo == 1
    assert _tablas(base_vacia) == antes
    assert _vistas(base_vacia) == set()


def test_los_datos_de_prueba_se_rechazan_en_una_base_demo(base_vacia: str) -> None:
    """Los datos de prueba no se cargan si la base es demo (spec 003, RF-054)."""
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="demo")
    assert codigo == 0
    codigo, texto = _ejecutar(base_vacia, "aplicar", datos_de_prueba=True)
    assert codigo == 1
    assert MENSAJE_DATOS in texto
    filas = _consulta(base_vacia, "select id from cobros where id like 'prueba-%'")
    assert filas == []
    assert _entorno(base_vacia) == "demo"
    assert _versiones(base_vacia) == ["0001", "0002", "0003"]


def test_los_datos_de_prueba_se_cargan_en_local_y_se_pueden_repetir(base_vacia: str) -> None:
    """--datos-de-prueba en local deja cada cobro prueba-* una sola vez (spec 003, RF-054)."""
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="local", datos_de_prueba=True)
    assert codigo == 0
    codigo, _texto = _ejecutar(base_vacia, "aplicar", datos_de_prueba=True)
    assert codigo == 0
    filas = _consulta(base_vacia, "select id from cobros where id like 'prueba-%' order by id")
    assert [fila[0] for fila in filas] == list(IDS_DE_PRUEBA)


def test_la_marca_de_entorno_no_se_puede_cambiar(base_vacia: str) -> None:
    """Una base local no pasa a demo (spec 003, RF-049, RF-054)."""
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="local")
    assert codigo == 0
    versiones = _versiones(base_vacia)
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="demo")
    assert codigo == 1
    assert _entorno(base_vacia) == "local"
    assert _versiones(base_vacia) == versiones


def test_anon_y_authenticated_no_pueden_leer_ni_escribir(base_vacia: str) -> None:
    """anon y authenticated no leen ni escriben ninguna tabla (spec 003, RF-022)."""
    codigo, _texto = _ejecutar(base_vacia, "aplicar", entorno="local")
    assert codigo == 0
    tablas = (
        "negocios",
        "cupones",
        "cobros",
        "pagos",
        "avisos_webhook",
        "cambios_de_estructura",
        "entorno_de_la_base",
        "estado_del_servidor",
    )
    for rol in ("anon", "authenticated"):
        for tabla in tablas:
            _exige_sin_permiso(base_vacia, rol, tabla, "select * from {}")
            _exige_sin_permiso(base_vacia, rol, tabla, "insert into {} default values")


def test_estado_muestra_entorno_aplicadas_y_pendientes(base_vacia: str, tmp_path: Path) -> None:
    """estado muestra entorno, aplicadas y pendientes, y no cambia nada (spec 003, RF-017)."""
    (tmp_path / "0001_uno.sql").write_text(
        "create table solo_para_estado (id int primary key);\n",
        encoding="utf-8",
    )
    codigo, _texto = _ejecutar(base_vacia, "aplicar", carpeta=tmp_path, entorno="local")
    assert codigo == 0
    (tmp_path / "0002_dos.sql").write_text(
        "create table todavia_no (id int primary key);\n",
        encoding="utf-8",
    )
    _consulta(base_vacia, "insert into solo_para_estado (id) values (%s)", (1,))
    tablas_antes = _tablas(base_vacia)
    versiones_antes = _versiones(base_vacia)
    codigo, texto = _ejecutar(base_vacia, "estado", carpeta=tmp_path)
    assert codigo == 0
    assert "local" in texto
    assert "0001" in texto
    assert "0002" in texto
    assert _tablas(base_vacia) == tablas_antes
    assert "todavia_no" not in _tablas(base_vacia)
    assert _versiones(base_vacia) == versiones_antes
    assert _consulta(base_vacia, "select id from solo_para_estado") == [(1,)]


def test_una_migracion_con_funciones_y_textos_con_punto_y_coma_se_aplica(
    base_vacia: str, tmp_path: Path
) -> None:
    """Una migración con ``$$``, ``E'…'`` y ``;`` en textos se aplica entera (spec 003, DP-17).

    El comando no parte el SQL por su cuenta: lo corre PostgreSQL, que sí entiende estas formas.
    """
    (tmp_path / "0001_funciones.sql").write_text(
        "/* un comentario de bloque; con punto y coma */\n"
        "create table notas (id int primary key, texto text);\n"
        "insert into notas values (1, E'it\\'s; ok -- no es un comentario');\n"
        "insert into notas values (2, 'otro; texto -- tampoco');\n"
        "create function siempre_uno() returns int language plpgsql as $$\n"
        "begin\n"
        "  -- este comentario tiene un ; adentro\n"
        "  return 1;\n"
        "end;\n"
        "$$;\n"
        "create function con_etiqueta() returns text language sql as $f$ select 'a;b'; $f$;\n",
        encoding="utf-8",
    )
    codigo, _texto = _ejecutar(base_vacia, "aplicar", carpeta=tmp_path, entorno="local")
    assert codigo == 0
    assert _versiones(base_vacia) == ["0001"]
    assert _consulta(base_vacia, "select siempre_uno()") == [(1,)]
    assert _consulta(base_vacia, "select con_etiqueta()") == [("a;b",)]
    assert _consulta(base_vacia, "select texto from notas order by id") == [
        ("it's; ok -- no es un comentario",),
        ("otro; texto -- tampoco",),
    ]


def test_si_la_primera_migracion_falla_no_queda_ni_la_marca_de_entorno(
    base_vacia: str, tmp_path: Path
) -> None:
    """Si falla la primera versión, la base queda como estaba y se reintenta (RF-019, RF-049).

    La marca de entorno y las tablas de control se guardan junto con la primera
    migración: si esta falla, no se guardan.
    """
    antes = _tablas(base_vacia)
    (tmp_path / "0001_falla.sql").write_text(
        "create table no_queda (id int primary key);\nselect * from tabla_que_no_existe;\n",
        encoding="utf-8",
    )
    codigo, texto = _ejecutar(base_vacia, "aplicar", carpeta=tmp_path, entorno="local")
    assert codigo == 1
    assert "La versión 0001 falló y no se aplicó nada de ella (UndefinedTable)." in texto
    assert _tablas(base_vacia) == antes
    (tmp_path / "0001_falla.sql").write_text(
        "create table queda (id int primary key);\n",
        encoding="utf-8",
    )
    codigo, _texto = _ejecutar(base_vacia, "aplicar", carpeta=tmp_path, entorno="demo")
    assert codigo == 0
    assert _entorno(base_vacia) == "demo"
    assert _versiones(base_vacia) == ["0001"]
