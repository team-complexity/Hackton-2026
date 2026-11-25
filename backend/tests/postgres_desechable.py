"""PostgreSQL desechable para las pruebas del SQL (spec 003, R-10, RF-038, CE-011).

El usuario de ``PRUEBAS_DATABASE_URL`` tiene que poder crear roles y bases
(en el CI es el superusuario del servicio). Esta ayuda no imprime la URL.
"""

import os
import secrets
from collections.abc import Iterator
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest
from psycopg import sql

MOTIVO_SIN_PRUEBAS = "Sin PRUEBAS_DATABASE_URL: las pruebas de PostgreSQL corren en el CI (R-10)"


def base_desechable() -> Iterator[str]:
    """Crea una base vacía y la borra al salir (spec 003, R-10, CE-011).

    Si ``PRUEBAS_DATABASE_URL`` no está, la prueba se salta. Crea los roles
    ``anon`` y ``authenticated`` si no existen: el ``revoke`` del PR #97 los
    necesita. No imprime la URL.
    """
    url = os.environ.get("PRUEBAS_DATABASE_URL", "").strip()
    if not url:
        pytest.skip(MOTIVO_SIN_PRUEBAS)
    _asegurar_roles(url)
    nombre = "prueba_" + secrets.token_hex(8)
    with _conectar(url, autocommit=True) as conexion:
        conexion.execute(sql.SQL("create database {}").format(sql.Identifier(nombre)))
    try:
        yield _url_con_base(url, nombre)
    finally:
        with _conectar(url, autocommit=True) as conexion:
            # WITH (FORCE) cierra conexiones que la prueba haya dejado abiertas.
            conexion.execute(
                sql.SQL("drop database {} with (force)").format(sql.Identifier(nombre))
            )


def _conectar(url: str, *, autocommit: bool) -> psycopg.Connection:
    """Abre una conexión. Si falla, el error no incluye la URL."""
    try:
        return psycopg.connect(url, autocommit=autocommit, connect_timeout=5)
    except psycopg.Error as error:
        raise RuntimeError(
            f"No se pudo usar el PostgreSQL de pruebas ({type(error).__name__})."
        ) from None


def _asegurar_roles(url: str) -> None:
    """Crea ``anon`` y ``authenticated`` si no existen (spec 003, R-10)."""
    with _conectar(url, autocommit=True) as conexion:
        for rol in ("anon", "authenticated"):
            existe = conexion.execute(
                "select 1 from pg_roles where rolname = %s",
                (rol,),
            ).fetchone()
            if existe is None:
                conexion.execute(sql.SQL("create role {}").format(sql.Identifier(rol)))


def _url_con_base(url: str, nombre: str) -> str:
    """Devuelve la misma URL apuntando a ``nombre``, sin registrar el valor."""
    partes = urlsplit(url)
    return urlunsplit((partes.scheme, partes.netloc, f"/{nombre}", partes.query, partes.fragment))
