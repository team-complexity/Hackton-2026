"""Pruebas del comando de migraciones sin PostgreSQL (spec 003, RF-017, RF-021).

El módulo ``app.migraciones`` todavía no existe: estas pruebas tienen que
fallar antes de implementarlo (principio V).
"""

import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parents[1]
MENSAJE_FALTA = "Falta DATABASE_URL en backend/.env."
URL_FALSA = "postgresql://usuario-falso:clave-falsa@127.0.0.1:1/x"
# El comando conecta con espera de 5 s (T041). Este tope solo evita un cuelgue.
ESPERA_MAXIMA_SEGUNDOS = 15


def _correr(argumentos: list[str], database_url: str) -> tuple[int, str]:
    """Corre ``python -m app.migraciones`` y devuelve el código y la salida.

    ``database_url`` vacía pisa ``backend/.env``: pydantic-settings da
    prioridad a la variable de entorno, y así la prueba no toca una base
    real (spec 003, CE-011). No imprime la URL.
    """
    entorno = os.environ.copy()
    entorno["DATABASE_URL"] = database_url
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "app.migraciones", *argumentos],
            cwd=RAIZ_BACKEND,
            env=entorno,
            capture_output=True,
            text=True,
            check=False,
            timeout=ESPERA_MAXIMA_SEGUNDOS,
        )
    except subprocess.TimeoutExpired:
        raise AssertionError("El comando no terminó a tiempo.") from None
    return resultado.returncode, resultado.stdout + resultado.stderr


def test_sin_database_url_el_comando_avisa_y_sale_con_1() -> None:
    """Sin DATABASE_URL el comando avisa y sale con 1 (spec 003, RF-017)."""
    codigo, salida = _correr(["estado"], "")
    assert codigo == 1
    assert MENSAJE_FALTA in salida


def test_si_no_se_puede_conectar_no_muestra_la_direccion() -> None:
    """Si no hay conexión, el mensaje lleva la clase y no la dirección (spec 003, RF-021)."""
    codigo, salida = _correr(["estado"], URL_FALSA)
    assert codigo == 1
    assert re.search(
        r"No se pudo conectar con la base de datos \([A-Za-z][A-Za-z0-9]*\)\.",
        salida,
    )
    assert "usuario-falso" not in salida
    assert "clave-falsa" not in salida
    assert "127.0.0.1:1" not in salida
