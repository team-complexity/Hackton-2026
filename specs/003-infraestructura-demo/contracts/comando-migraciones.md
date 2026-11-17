# Contrato: comando de cambios de estructura

## 1. Comando y propósito

```text
uv run --directory backend python -m app.migraciones <acción> [opciones]
```

Crea y actualiza la estructura de una base de datos con los archivos de `supabase/migraciones/`, igual en local, en el CI y contra la demo (desde la computadora de Hugo). Lee la conexión de `DATABASE_URL` (variable de entorno o `backend/.env`). Supone la decisión DP-3 (comando propio); si Hugo elige otra herramienta, este contrato se reescribe.

## 2. Requisitos

RF-017, RF-018, RF-019, RF-046, RF-049, RF-051, RF-054, CE-007.

## 3. Acciones y opciones

| Acción | Qué hace | Requisitos |
|---|---|---|
| `estado` | Muestra el entorno de la base, las versiones aplicadas y las pendientes. No cambia nada | RF-017 |
| `aplicar` | Aplica en orden las versiones pendientes (data-model §5.2) | RF-017, RF-018, RF-019 |

| Opción | Con | Qué hace | Requisitos |
|---|---|---|---|
| `--entorno local\|demo` | `aplicar` | **Obligatoria la primera vez** que se aplica en una base. Guarda la marca en `entorno_de_la_base`. Si la base ya tiene otra marca, el comando se detiene | RF-049, RF-054 |
| `--ya-aplicada 0001` | `aplicar` | Anota la versión 0001 sin correrla. Solo se acepta si ya existe la tabla `cobros` y la 0001 no está anotada (base de la demo creada a mano, DP-19) | Historia 6, escenario 3 |
| `--datos-de-prueba` | `aplicar` | Después de migrar, carga `supabase/datos_de_prueba.sql`. Se rechaza si la base no está marcada `local` | RF-054 |

## 4. Salidas

| Código de salida | Cuándo | Mensaje (español, para Hugo o Juan) |
|---|---|---|
| 0 | Todo aplicado, o ya estaba al día | "Base de datos local al día: 0001, 0002." / "No había nada que aplicar." |
| 1 | Falta `DATABASE_URL` | "Falta DATABASE_URL en backend/.env." |
| 1 | No se puede conectar | "No se pudo conectar con la base de datos (OperationalError)." Sin la dirección ni el usuario |
| 1 | Primera vez sin `--entorno` | "Es la primera vez en esta base: indica --entorno local o --entorno demo." |
| 1 | `cobros` existe sin registro | "Esta base ya tiene el esquema del PR #97 sin registro. Revísalo y corre: aplicar --ya-aplicada 0001." |
| 1 | `--datos-de-prueba` en una base `demo` | "Los datos de prueba solo se cargan en la base local." |
| 1 | Una migración falla | "La versión 0002 falló y no se aplicó nada de ella (UndefinedTable)." Las anteriores quedan aplicadas |

## 5. Ejemplos

```text
$ uv run --directory backend python -m app.migraciones aplicar --entorno local --datos-de-prueba
Base marcada como local.
Aplicada 0001 esquema_inicial.
Aplicada 0002 imagen_del_qr.
Datos de prueba cargados.

$ uv run --directory backend python -m app.migraciones aplicar
No había nada que aplicar.
```

## 6. Seguridad y reglas

- Nunca imprime `DATABASE_URL` ni el texto de un error de conexión (RF-021).
- La publicación (manual o automática) **no** corre este comando (RF-046). Contra la demo lo corre solo Hugo, desde su computadora, después de exportar una copia de la base (RF-051; pasos en `docs/operacion-demo.md`).
- Conviene aplicar una migración en la demo **antes** de unir el pull request que la usa (§4 de la spec); si no, la salud dice `estructura: "pendiente"` y los cobros nuevos se rechazan (RF-047).
