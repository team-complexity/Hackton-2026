# Modelo de datos (Fase 1): Spec 003 — Infraestructura de la demo pública

- **Fecha**: 2026-11-17
- **Plan**: [plan.md](plan.md)
- **Parte de**: el modelo de la [spec 001](../001-backend-mvp/data-model.md) (cobro, pago, estados y reglas de registro), que **no cambia**, y del esquema del PR #97 (`supabase/001_esquema_inicial.sql`). Aquí solo va lo que se guarda, cómo se traduce y lo que se agrega.

---

## 1. Qué se guarda y dónde

| Entidad de la 001 | Tabla del PR #97 | Qué cambia | Requisitos |
|---|---|---|---|
| Cobro | `cobros` | Columna nueva `qr_imagen` (migración 0002) | RF-001, RF-010, RF-011, RF-018 |
| Pago | `pagos` | Nada | RF-002, RF-007, RF-008, RF-009 |
| `webhook-id` vistos | `avisos_webhook` | Nada | RF-003 |
| — | `cambios_de_estructura` (nueva, la crea el comando) | Registro de migraciones aplicadas | RF-017, RF-019, RF-047 |
| — | `entorno_de_la_base` (nueva, la crea el comando) | Marca `local` o `demo` | RF-049, RF-054 |

Las tablas `negocios` y `cupones` del PR #97 no se usan en esta spec (#24 y #37). Los límites por IP, los canales abiertos y `ultima_consulta_pey` siguen solo en memoria (DP-12, §3.2 de la spec).

## 2. Traducción entre la memoria y la base de datos

### 2.1 Cobro → `cobros`

| Campo de la 001 | Columna | Traducción | Regla de esta spec |
|---|---|---|---|
| `id` | `id` | Igual (12 caracteres; la columna admite 8 a 32) | — |
| `monto` | `monto` | `Decimal` ↔ `numeric(12,2)`; `None` ↔ `null` (monto libre) | — |
| `concepto` | `concepto` | Igual (ya validado a 1–40 caracteres, RF-005 de la 001) | — |
| `num_ref` | `num_ref` | Igual | — |
| `codi_qr_id` | `codi_qr_id` | `""` en memoria ↔ `null` hasta que pey crea el QR | Se guarda el cobro antes de llamar a pey (RF-012) |
| `qr` | `qr` | `""` ↔ `null` hasta que pey crea el QR | — |
| `qr_imagen` | `qr_imagen` (nueva) | `None` ↔ `null` si pey no la manda | RF-010, RF-011 |
| `creado_en`, `expira_en`, `fin_ventana`, `cancelado_en` | mismas columnas | Entero Unix ↔ `timestamptz` en UTC | **Siempre** con la hora del `Reloj` del servidor; nunca con el `default now()` de la base de datos (DP-10, RF-006) |
| `pagos` | tabla `pagos` | Se cargan con el cobro, ordenados por `numero` | RF-005, RF-008 |
| `ultima_consulta_pey` | `ultima_consulta_pey` | **No se escribe**: queda `null` y la hora vive en memoria | DP-12 |

**Calculados** (como en la 001, no se guardan ni se leen de la vista): `monto_libre`, `numero_de_pagos`, `total_recibido`, `pagado_en`, `estado` y `en_ventana`. El servidor los calcula con su reloj (RF-006, QA-11). La vista `cobros_con_estado` queda para consultas a mano y para el historial (#38).

### 2.2 Pago → `pagos`

| Campo de la 001 | Columna | Traducción |
|---|---|---|
| `transaccion_id` | `transaccion_id` (`unique`) | Igual |
| `numero` | `numero` (`unique (cobro_id, numero)`) | Calculado dentro del candado del cobro (DP-8) |
| `monto_recibido` | `monto_recibido` | `Decimal` ↔ `numeric(12,2)` |
| `monto_base` | `monto_base` | `None` ↔ `null` |
| `pagado_en` | `pagado_en` | Entero Unix ↔ `timestamptz`; `datePaid` de pey, o la hora del `Reloj` si falta |
| `fuente` | `fuente` | `aviso` o `consulta` |
| — | `registrado_en` | Hora del `Reloj` del servidor (DP-10) |

**Nunca se guardan** los datos de quien paga que pey manda en `metadata` (nombre, CLABE o cuenta, banco, teléfono, clave de rastreo): el código no los lee (`pey.py:183`) y no hay columna para ellos (RF-009).

### 2.3 Aviso → `avisos_webhook`

| Dato | Columna | Regla |
|---|---|---|
| Cabecera `webhook-id` | `webhook_id` (llave primaria) | Se guarda **en la misma transacción** que el pago que trae, o sola si el aviso se ignora (DP-9) |
| `type` del aviso | `tipo` | Igual |
| — | `recibido_en` | Hora del `Reloj` del servidor |

## 3. Reglas de escritura

Todas las escrituras van primero a la base de datos y después a la memoria y al canal (DP-7).

| Operación | SQL (resumen) | Si la base de datos falla | Requisitos |
|---|---|---|---|
| Crear cobro | `insert into cobros (…) values (…)` sin QR, **antes** de llamar a pey; espera como máximo 2 s (DP-35) | 503 y no se llama a pey | RF-001, RF-012 |
| pey no creó el QR | `delete from cobros where id = …` | Se registra la falla; el cobro queda sin QR en la base de datos (limitación, §11 del plan) | RF-052, RF-016 |
| pey creó el QR | `update cobros set codi_qr_id, qr, qr_imagen where id = …`; espera como máximo 2 s (DP-35) | 503 sin QR; el cobro sale de la memoria | RF-001, RF-013 |
| Registrar pago | Dentro del candado del cobro, en una transacción: `insert into pagos … on conflict (transaccion_id) do nothing returning id` y, si viene de un aviso, `insert into avisos_webhook … on conflict do nothing` | Aviso: 503 a pey y el aviso queda en la lista de reintentos (RF-014, RF-048). Consulta: se registra la falla y se reintenta en la próxima consulta | RF-002, RF-003, RF-007, RF-008 |
| Aviso ignorado (otro tipo, QR desconocido) | `insert into avisos_webhook … on conflict do nothing` | 503 a pey | RF-003 |
| Cancelar | `update cobros set cancelado_en = … where id = … and cancelado_en is null` | 503 | RF-004 |
| Consulta de vida | `select 1` cada 6 h (y en la salud, DP-31) | Se registra la falla | RF-039, RF-023 |

**Lecturas**: un cobro se carga por `id` (ver, cancelar, canal) o por `codi_qr_id` (aviso), con sus pagos, solo si no está ya en memoria (RF-005). Si dos peticiones lo cargan a la vez, se queda el primer objeto que entró a la memoria y las dos usan ese mismo (DP-33).

**Datos que el esquema no acepta**: un `amount` de 0 o negativo se rechaza antes de llegar a la base de datos, y un aviso sin `type` se guarda con `tipo` vacío (DP-34). Para saber si un `webhook-id` ya se vio, se mira primero la memoria y después la tabla.

## 4. Lista de reintentos de avisos (solo en memoria)

| Campo | Tipo | Regla | Requisitos |
|---|---|---|---|
| `webhook_id` | texto | El del aviso | RF-014 |
| `codi_qr_id`, `transaccion_id`, `monto_recibido`, `pagado_en` | como en el aviso | Lo necesario para registrar el pago, nada de `metadata` | RF-009, RF-014 |
| `intentos` | entero | Solo para el registro | RF-016 |

- Cada 15 s, la tarea de fondo intenta registrar cada aviso de la lista; al lograrlo, emite el pago por el canal y lo quita (RF-048).
- Si el mismo aviso vuelve a llegar de pey mientras está en la lista, no se duplica: se identifica por `webhook_id`.
- Se pierde si el servidor se reinicia (limitación aceptada en §4 de la spec).

## 5. Migraciones

| Versión | Archivo | Contenido |
|---|---|---|
| 0001 | `supabase/migraciones/0001_esquema_inicial.sql` | El esquema del PR #97, sin `begin` ni `commit` (los pone el comando, DP-17) |
| 0002 | `supabase/migraciones/0002_imagen_del_qr.sql` | `alter table cobros add column qr_imagen text;` y el comentario de `cobros.qr` al día ("la imagen es la que manda pey") |

Fuera de las migraciones:

- `supabase/datos_de_prueba.sql`: los bloques A y B del `002_datos_de_prueba.sql` del PR #97, con `on conflict do nothing` para poder repetirlo. Solo se carga con `--datos-de-prueba` en una base marcada `local` (DP-18, RF-054).
- `supabase/consultas_de_verificacion.sql`: los bloques C a F del mismo archivo, para correrlos a mano.

### 5.1 Tablas del comando

```text
cambios_de_estructura
  version      text  primary key        -- "0001", "0002"…
  nombre       text  not null           -- "esquema_inicial"
  aplicado_en  timestamptz not null

entorno_de_la_base
  unico        boolean primary key default true check (unico)  -- una sola fila
  nombre       text not null check (nombre in ('local', 'demo'))
  definido_en  timestamptz not null
```

El comando las crea con `if not exists` antes de cualquier migración, les enciende RLS y les quita el acceso a `anon` y `authenticated`, igual que el PR #97 (RF-022).

### 5.2 Reglas

1. Las migraciones se aplican en orden de versión. Cada una corre en **una transacción junto con su fila** en `cambios_de_estructura`: o queda todo, o nada (RF-019).
2. Una versión ya anotada no se vuelve a correr (RF-019, CE-007).
3. Si `cambios_de_estructura` está vacía pero ya existe la tabla `cobros` (la base de la demo, creada a mano con el PR #97), el comando se detiene y pide `--ya-aplicada 0001` (DP-19). No lo decide solo.
4. Toda tabla nueva de una migración futura enciende RLS y quita el acceso a `anon` y `authenticated`: Supabase les da permisos por defecto sobre las tablas nuevas del esquema `public`.
5. **Versión esperada** (RF-047, corte 2): la mayor versión de los archivos de `supabase/migraciones/` que trae la versión publicada. Si es mayor que la mayor de `cambios_de_estructura`, la estructura está **pendiente**.

## 6. Límites (sin cambios)

Siguen los de la 001 (`data-model.md` §6), en memoria. La IP con la que se cuentan sale de `CloudFront-Viewer-Address` en la demo (DP-22, RF-028).
