"""Comando para crear y actualizar la base de datos (spec 003, RF-017 a RF-019, RF-049, RF-054)."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import psycopg

from app.config import Configuracion

RAIZ = Path(__file__).resolve().parents[2]
CARPETA_MIGRACIONES = RAIZ / "supabase" / "migraciones"
PATRON_MIGRACION = re.compile(r"^(\d{4})_(.+)\.sql$")

MENSAJE_FALTA = "Falta DATABASE_URL en backend/.env."
MENSAJE_PRIMERA = "Es la primera vez en esta base: indica --entorno local o --entorno demo."
MENSAJE_SIN_REGISTRO = (
    "Esta base ya tiene el esquema del PR #97 sin registro. "
    "Revísalo y corre: aplicar --ya-aplicada 0001."
)
MENSAJE_DATOS = "Los datos de prueba solo se cargan en la base local."
MENSAJE_NADA = "No había nada que aplicar."

_SQL_CONTROL = """
create table if not exists cambios_de_estructura (
    version text primary key,
    nombre text not null,
    aplicado_en timestamptz not null
);
create table if not exists entorno_de_la_base (
    unico boolean primary key default true check (unico),
    nombre text not null check (nombre in ('local', 'demo')),
    definido_en timestamptz not null
);
alter table cambios_de_estructura enable row level security;
alter table entorno_de_la_base enable row level security;
revoke all on cambios_de_estructura from anon, authenticated;
revoke all on entorno_de_la_base from anon, authenticated;
"""


_SQL_ENTORNO = "insert into entorno_de_la_base (nombre, definido_en) values (%s, now())"
_SQL_VERSION = (
    "insert into cambios_de_estructura (version, nombre, aplicado_en) values (%s, %s, now())"
)

# Una sentencia (o un script) y sus parámetros; ``None`` si no lleva.
_Paso = tuple[str, tuple[str | None, ...] | None]


@dataclass(frozen=True)
class _Foto:
    """Lo que ya hay en la base, leído sin escribir."""

    cobros: bool
    entorno: str | None
    versiones: tuple[str, ...]


def ejecutar(
    url: str,
    carpeta: Path,
    accion: str,
    *,
    entorno: str | None = None,
    ya_aplicada: str | None = None,
    datos_de_prueba: bool = False,
) -> tuple[int, str]:
    """Aplica o consulta las migraciones y devuelve el código y el texto.

    No incluye la URL ni el texto de un error de PostgreSQL
    (spec 003, RF-017, RF-018, RF-019, RF-021, RF-049, RF-054).
    """
    if not carpeta.is_dir():
        return 1, "No se encontró la carpeta de migraciones."
    try:
        conexion = psycopg.connect(url, connect_timeout=5)
    except psycopg.Error as error:
        return 1, _mensaje_conexion(error)
    try:
        conexion.execute("set search_path to public")
        conexion.commit()
        return _con_conexion(
            conexion,
            carpeta,
            accion,
            entorno=entorno,
            ya_aplicada=ya_aplicada,
            datos_de_prueba=datos_de_prueba,
        )
    finally:
        conexion.close()


def main(argumentos: list[str] | None = None) -> int:
    """Punto de entrada de ``python -m app.migraciones`` (spec 003, RF-017, RF-021)."""
    args = _parser().parse_args(argumentos)
    url = Configuracion().database_url.get_secret_value().strip()
    if not url:
        print(MENSAJE_FALTA)
        return 1
    try:
        codigo, texto = ejecutar(
            url,
            CARPETA_MIGRACIONES,
            args.accion,
            entorno=args.entorno,
            ya_aplicada=args.ya_aplicada,
            datos_de_prueba=args.datos_de_prueba,
        )
    except Exception as error:
        print(_mensaje_conexion(error))
        return 1
    print(texto)
    return codigo


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.migraciones")
    parser.add_argument("accion", choices=("estado", "aplicar"))
    parser.add_argument("--entorno", choices=("local", "demo"))
    parser.add_argument("--ya-aplicada", dest="ya_aplicada")
    parser.add_argument("--datos-de-prueba", action="store_true", dest="datos_de_prueba")
    return parser


def _mensaje_conexion(error: BaseException) -> str:
    """Nombre de la clase, nunca el texto: puede traer la dirección (spec 003, RF-021, DP-15)."""
    return f"No se pudo conectar con la base de datos ({type(error).__name__})."


def _con_conexion(
    conexion: psycopg.Connection,
    carpeta: Path,
    accion: str,
    *,
    entorno: str | None,
    ya_aplicada: str | None,
    datos_de_prueba: bool,
) -> tuple[int, str]:
    foto = _leer(conexion)
    migraciones = _listar(carpeta)
    if accion == "estado":
        return 0, _texto_estado(foto, migraciones)
    if accion != "aplicar":
        return 1, "La acción tiene que ser estado o aplicar."
    # Rechazar antes de crear tablas. Si no, --ya-aplicada en una base vacía
    # dejaría cambios_de_estructura y entorno_de_la_base (T038, TK-12).
    rechazo = _rechazo(
        foto,
        entorno=entorno,
        ya_aplicada=ya_aplicada,
        datos_de_prueba=datos_de_prueba,
    )
    if rechazo is not None:
        return 1, rechazo
    try:
        return _aplicar(
            conexion,
            foto,
            carpeta,
            migraciones,
            entorno=entorno,
            ya_aplicada=ya_aplicada,
            datos_de_prueba=datos_de_prueba,
        )
    except psycopg.Error as error:
        conexion.rollback()
        return 1, _mensaje_conexion(error)


def _rechazo(
    foto: _Foto,
    *,
    entorno: str | None,
    ya_aplicada: str | None,
    datos_de_prueba: bool,
) -> str | None:
    if entorno is not None and entorno not in ("local", "demo"):
        return "El entorno tiene que ser local o demo."
    if foto.entorno and entorno and foto.entorno != entorno:
        return f"La base ya está marcada como {foto.entorno}. No se puede cambiar a {entorno}."
    destino = entorno or foto.entorno
    if datos_de_prueba and destino == "demo":
        return MENSAJE_DATOS
    if ya_aplicada is not None and ya_aplicada != "0001":
        return "Solo se acepta --ya-aplicada 0001."
    if ya_aplicada == "0001" and (not foto.cobros or "0001" in foto.versiones):
        return (
            "Solo se puede anotar --ya-aplicada 0001 si ya existe la tabla cobros "
            "y la versión 0001 no está anotada."
        )
    if foto.cobros and "0001" not in foto.versiones and ya_aplicada != "0001":
        return MENSAJE_SIN_REGISTRO
    if foto.entorno is None and entorno is None:
        return MENSAJE_PRIMERA
    return None


def _aplicar(
    conexion: psycopg.Connection,
    foto: _Foto,
    carpeta: Path,
    migraciones: list[tuple[str, str, Path]],
    *,
    entorno: str | None,
    ya_aplicada: str | None,
    datos_de_prueba: bool,
) -> tuple[int, str]:
    # Las tablas de control, la marca de entorno y la anotación de --ya-aplicada
    # viajan en la transacción de la primera migración pendiente: si esa falla,
    # la base queda como estaba y se puede reintentar (RF-019, RF-049, TK-13).
    previos: list[_Paso] = [(_SQL_CONTROL, None)]
    lineas_previas: list[str] = []
    if foto.entorno is None:
        previos.append((_SQL_ENTORNO, (entorno,)))
        lineas_previas.append(f"Base marcada como {entorno}.")
    anotadas = set(foto.versiones)
    anoto = False
    if ya_aplicada == "0001":
        nombre = _nombre(migraciones, "0001")
        previos.append((_SQL_VERSION, ("0001", nombre)))
        lineas_previas.append(f"Anotada 0001 {nombre} sin correrla.")
        anotadas.add("0001")
        anoto = True
    lineas: list[str] = []
    aplico = False
    for version, nombre, ruta in migraciones:
        if version in anotadas:
            continue
        pasos = [
            *previos,
            (ruta.read_text(encoding="utf-8"), None),
            (_SQL_VERSION, (version, nombre)),
        ]
        try:
            _correr(conexion, pasos)
        except psycopg.Error as error:
            return (
                1,
                f"La versión {version} falló y no se aplicó nada de ella ({type(error).__name__}).",
            )
        previos = []
        lineas.extend(lineas_previas)
        lineas_previas = []
        anotadas.add(version)
        aplico = True
        lineas.append(f"Aplicada {version} {nombre}.")
    if previos:
        # Sin migraciones pendientes (por ejemplo, solo marcar el entorno).
        try:
            _correr(conexion, previos)
        except psycopg.Error as error:
            return 1, f"No se pudo preparar la base ({type(error).__name__})."
        lineas.extend(lineas_previas)
    if datos_de_prueba:
        archivo = carpeta.parent / "datos_de_prueba.sql"
        if not archivo.is_file():
            return 1, "No se encontró supabase/datos_de_prueba.sql."
        try:
            _correr(conexion, [(archivo.read_text(encoding="utf-8"), None)])
        except psycopg.Error as error:
            clase = type(error).__name__
            return 1, f"No se pudieron cargar los datos de prueba ({clase})."
        lineas.append("Datos de prueba cargados.")
    if not aplico and not anoto and not datos_de_prueba and not lineas:
        return 0, MENSAJE_NADA
    if not aplico and not anoto and datos_de_prueba:
        lineas.insert(0, MENSAJE_NADA)
    return 0, "\n".join(lineas)


def _texto_estado(foto: _Foto, migraciones: list[tuple[str, str, Path]]) -> str:
    aplicadas = [version for version, _nombre, _ruta in migraciones if version in foto.versiones]
    pendientes = [
        version for version, _nombre, _ruta in migraciones if version not in foto.versiones
    ]
    # Versiones anotadas a mano (por ejemplo --ya-aplicada) que ya no tienen archivo.
    for version in foto.versiones:
        if version not in aplicadas:
            aplicadas.append(version)
    aplicadas.sort()
    entorno = foto.entorno or "sin marcar"
    texto_aplicadas = ", ".join(aplicadas) if aplicadas else "ninguna"
    texto_pendientes = ", ".join(pendientes) if pendientes else "ninguna"
    return f"Entorno: {entorno}.\nAplicadas: {texto_aplicadas}.\nPendientes: {texto_pendientes}."


def _leer(conexion: psycopg.Connection) -> _Foto:
    cobros = _existe(conexion, "cobros")
    versiones: tuple[str, ...] = ()
    if _existe(conexion, "cambios_de_estructura"):
        filas = conexion.execute(
            "select version from cambios_de_estructura order by version"
        ).fetchall()
        versiones = tuple(str(fila[0]) for fila in filas)
    entorno = None
    if _existe(conexion, "entorno_de_la_base"):
        fila = conexion.execute("select nombre from entorno_de_la_base").fetchone()
        if fila is not None:
            entorno = str(fila[0])
    conexion.rollback()
    return _Foto(cobros=cobros, entorno=entorno, versiones=versiones)


def _existe(conexion: psycopg.Connection, tabla: str) -> bool:
    fila = conexion.execute(
        """
        select 1
        from information_schema.tables
        where table_schema = 'public' and table_name = %s
        """,
        (tabla,),
    ).fetchone()
    return fila is not None


def _listar(carpeta: Path) -> list[tuple[str, str, Path]]:
    encontradas: list[tuple[str, str, Path]] = []
    for archivo in carpeta.iterdir():
        coincidencia = PATRON_MIGRACION.match(archivo.name)
        if coincidencia and archivo.is_file():
            encontradas.append((coincidencia.group(1), coincidencia.group(2), archivo))
    encontradas.sort(key=lambda item: item[0])
    return encontradas


def _nombre(migraciones: list[tuple[str, str, Path]], version: str) -> str:
    for encontrada, nombre, _ruta in migraciones:
        if encontrada == version:
            return nombre
    return "esquema_inicial"


def _correr(conexion: psycopg.Connection, pasos: list[_Paso]) -> None:
    """Corre los pasos en una sola transacción (spec 003, RF-019, DP-17).

    Un paso sin parámetros se manda entero a PostgreSQL, que entiende por sí solo
    ``$$``, ``E'…'`` y los comentarios: el comando no parte el SQL por su cuenta.
    """
    with conexion.transaction():
        for sentencia, parametros in pasos:
            conexion.execute(sentencia, parametros)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as error:
        print(_mensaje_conexion(error))
        raise SystemExit(1) from None
