# Contrato: CI de los pull requests

## 1. Flujo y propósito

`.github/workflows/ci.yml`: corre las pruebas y el lint del servidor, de la web y de la base de datos en cada pull request hacia `main`, y muestra el resultado en el pull request.

## 2. Requisitos

RF-036, RF-037, RF-038, CE-006, CE-007, CE-011.

## 3. Disparadores y permisos

| Campo | Valor |
|---|---|
| `on` | `pull_request` hacia `main` (abrir, subir cambios, reabrir) y `push` a `main` |
| `permissions` | `contents: read` |
| Secretos | Ninguno; tampoco variables de pey ni de la base de datos real |

## 4. Trabajos (los nombres son los que Juan marca como obligatorios en la protección de `main`)

| Trabajo | Pasos | Cuándo corre | Requisitos |
|---|---|---|---|
| `servidor` | `uv sync --locked`; `ruff check .`; `ruff format --check .`; `pytest -q` (en `backend/`) | Siempre | RF-036 |
| `web` | Lo anterior más `playwright install --with-deps chromium webkit`; `ruff check` y `ruff format --check` de `../web` con la configuración del backend; `pytest ../web -q` | Siempre (el CI llega después de unir el #72, QP-1) | RF-036 |
| `base-de-datos` | Servicio PostgreSQL 17; crea los roles `anon` y `authenticated`; corre `python -m app.migraciones aplicar --entorno local` **dos veces** (la segunda debe decir que no había nada que aplicar); corre las pruebas del almacén con `PRUEBAS_DATABASE_URL` apuntando al servicio | Desde F2 | RF-036, CE-007 |

- Python 3.12 en `ubuntu-latest`, con `astral-sh/setup-uv` y su caché.
- Si cualquier paso falla, el trabajo sale en rojo y, con la protección de `main`, no se puede unir (RF-037, CE-006).
- La contraseña del PostgreSQL del servicio es fija y de prueba (`prueba`): ese servidor solo existe mientras corre el trabajo y no es la base de datos real (RF-038).

## 5. Prueba del contrato (CE-006)

Un pull request de prueba con un `assert False` debe salir en rojo y no poder unirse; al quitarlo, en verde. Lo hace Hugo en F1 y lo anota en la guía de verificación.
