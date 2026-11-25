"""Contrato del CI (spec 003, RF-036, RF-038)."""

from pathlib import Path

RUTA_CI = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _bloque(texto: str, clave: str) -> str:
    """Devuelve el cuerpo indentado de una clave, sin leer el YAML con otra librería."""
    for indice, linea in enumerate(texto.splitlines()):
        desnuda = linea.split("#", 1)[0].rstrip()
        if desnuda.strip() != f"{clave}:":
            continue
        sangria = len(linea) - len(linea.lstrip(" "))
        cuerpo: list[str] = []
        for siguiente in texto.splitlines()[indice + 1 :]:
            if not siguiente.strip() or siguiente.lstrip().startswith("#"):
                cuerpo.append(siguiente)
                continue
            sangria_siguiente = len(siguiente) - len(siguiente.lstrip(" "))
            if sangria_siguiente <= sangria:
                break
            cuerpo.append(siguiente)
        return "\n".join(cuerpo)
    return ""


def _flujo() -> str:
    return RUTA_CI.read_text(encoding="utf-8")


def test_el_ci_corre_en_cada_pull_request_hacia_main() -> None:
    """El archivo existe y corre en cada pull request hacia main y en cada push a main (RF-036)."""
    texto = _flujo()
    assert RUTA_CI.is_file()
    disparadores = _bloque(texto, "on")
    assert "pull_request:" in disparadores
    assert "push:" in disparadores
    assert "main" in _bloque(disparadores, "pull_request")
    assert "main" in _bloque(disparadores, "push")


def test_el_ci_solo_lee_el_repositorio_y_no_usa_secretos() -> None:
    """El flujo solo pide lectura del repositorio y no usa secretos (RF-038)."""
    texto = _flujo()
    assert "contents: read" in _bloque(texto, "permissions")
    assert "secrets." not in texto
    assert "pull_request_target" not in texto


def test_el_ci_tiene_los_trabajos_servidor_y_web() -> None:
    """Hay trabajos servidor y web con los comandos del contrato (RF-036)."""
    texto = _flujo()
    assert "servidor:" in texto
    assert "web:" in texto
    for comando in (
        "uv sync --locked",
        "ruff check",
        "ruff format --check",
        "pytest -q",
        "playwright install --with-deps chromium webkit",
        "pytest ../web -q",
    ):
        assert comando in texto


def test_el_ci_prueba_las_migraciones_contra_un_postgresql_desechable() -> None:
    """base-de-datos prueba las migraciones en un PostgreSQL 17 (spec 003, RF-036, RF-038)."""
    trabajos = _bloque(_flujo(), "jobs")
    assert "base-de-datos:" in trabajos
    cuerpo = _bloque(trabajos, "base-de-datos")
    assert "postgres:17" in cuerpo
    assert "PRUEBAS_DATABASE_URL" in cuerpo
    assert cuerpo.count("python -m app.migraciones aplicar --entorno local") == 2
    assert "pytest -q" in cuerpo
    assert "uv sync --locked" in cuerpo
