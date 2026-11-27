# Modelo de datos: Spec 004 — Cobro rápido

- **Fecha**: 2026-11-26
- **Spec**: [spec.md](spec.md)
- **Plan**: [plan.md](plan.md)

Este documento extiende [specs/001-backend-mvp/data-model.md](../001-backend-mvp/data-model.md), [specs/002-web-mvp/data-model.md](../002-web-mvp/data-model.md) y [specs/003-infraestructura-demo/data-model.md](../003-infraestructura-demo/data-model.md) únicamente en lo que agrega o ajusta la Spec 004.

---

## 1. Entidad `Cobro` (servidor y base de datos)

### 1.1 Campos que cambian o se agregan

| Campo | Tipo en Python | Tipo en PostgreSQL | Regla (Corte 1 `[C1]`) | Regla (Corte 2 `[C2]`) | Requisitos |
|---|---|---|---|---|---|
| `duracion_segundos` | `int` *(propiedad derivada)* | *(derivado: `0` si `expira_en is null`, si no `expira_en - creado_en`)* | Entero `360 <= v <= 86400`; `600` por defecto si se omite en la petición | Igual que C1 más `0` (sin vencimiento) | RF-001, RF-002, RF-007, RF-008 |
| `expira_en` | `int \| None` (Unix s) | `timestamptz` (`not null` en C1; **anulable** en C2 con migración `0004`) | `creado_en + duracion_segundos` (siempre `> creado_en`) | `creado_en + duracion_segundos` si finito; `None` / `NULL` si `duracion_segundos == 0` | RF-003, RF-007, RF-008 |
| `fin_ventana` | `int` (Unix s) | `timestamptz not null` *(sin cambios)* | `expira_en + gracia_segundos` (`+600 s`) | `expira_en + gracia_segundos` si finito; `creado_en + 86400` (24 h) si sin vencimiento | RF-005, RF-010, RF-011 |

Los demás campos de `Cobro` (`id`, `codi_qr_id`, `monto`, `monto_libre`, `concepto`, `num_ref`, `qr`, `qr_imagen`, `creado_en`, `cancelado_en`, `pagos`, `numero_de_pagos`, `total_recibido`, `pagado_en`, `hora_servidor`) y la entidad `Pago` no cambian.

### 1.2 Reglas de validación en el servidor (`validar_duracion`)

1. `valor is None` (o ausente en el JSON) → `config.expiracion_segundos` (`600` por defecto, RF-001).
2. `isinstance(valor, bool)` o `not isinstance(valor, int)` → rechazo HTTP 422 (RF-006).
3. En **Corte 1**: si `valor < 360` o `valor > 86400` → rechazo HTTP 422 `"Elige una duración entre 6 minutos y 24 horas"` (RF-002, RF-006).
4. En **Corte 2**: si `valor != 0` y (`valor < 360` o `valor > 86400`) → rechazo HTTP 422 `"Elige una duración entre 6 minutos y 24 horas, o sin vencimiento"` (RF-002, RF-006, RF-008).

### 1.3 Estados y transiciones de `Cobro`

```text
Cobro finito (expira_en != None):
  pendiente ──(primer pago)──────────────────► pagado
  pendiente ──(cancelar)─────────────────────► cancelado ──(pago posterior)──► pagado
  pendiente ──(ahora >= expira_en sin pagos)─► vencido   ──(pago tardío)────► pagado

Cobro sin vencimiento [C2] (expira_en == None):
  pendiente ──(primer pago, en cualquier momento, incluso > 24 h)─► pagado
  pendiente ──(cancelar)──────────────────────────────────────────► cancelado ──(pago posterior)──► pagado
  (NUNCA transiciona a vencido; RF-009)
```

- **Ventana de escucha en el servidor (`en_ventana(ahora)`)**: `ahora < fin_ventana` para ambos tipos.
- **Conciliación (`RF-061` de spec 003)**: al cumplirse `fin_ventana` (`expira_en + 10 min` en finitos; `creado_en + 24 h` en sin vencimiento), `LatidoDeConciliacion` consulta una vez a pey y registra cualquier pago faltante.
- **Avisos firmados posteriores a `fin_ventana`**: `POST /webhooks/pey` sigue registrando pagos nuevos sin duplicarlos en cualquier momento (`RF-012`).

### 1.4 Cambio de estructura de PostgreSQL (solo Corte 2, coordinado con `#119`)

Archivo nuevo: `supabase/migraciones/0004_cobros_sin_vencimiento.sql` (migración idempotente aplicada con `python -m app.migraciones aplicar`, `QP-6`):

1. Quitar `NOT NULL` de `cobros.expira_en`: `alter table cobros alter column expira_en drop not null;`.
2. Ejecutar un bloque `DO $$ ... $$` consultando `pg_constraint` sobre `'public.cobros'::regclass` (`contype = 'c'`) para eliminar de forma idempotente cualquier `CHECK` que referencie `expira_en` distinto a los 3 checks nuevos con nombre fijo.
3. Agregar los 3 checks con nombres fijos comprobando antes si ya existen:
   - `cobros_expira_mayor_creado`: `check (expira_en is null or expira_en > creado_en)`
   - `cobros_fin_ventana_mayor_creado`: `check (fin_ventana > creado_en)`
   - `cobros_fin_ventana_mayor_expira`: `check (expira_en is null or fin_ventana >= expira_en)`
4. Recrear la vista con `create or replace view cobros_con_estado with (security_invoker = true)` ajustando la condición de vencimiento a `when c.expira_en is not null and now() >= c.expira_en then 'vencido'`.
5. Reaplicar `revoke all on cobros_con_estado from anon, authenticated;`.
6. Verificar en `backend/tests/test_migraciones_postgres.py` que `_versiones == ["0001", "0002", "0003", "0004"]`, idempotencia al reaplicarse y permisos revocados para `anon` y `authenticated`.

*(En Corte 1 no se crea ni aplica ninguna migración: `0001` a `0003` cubren completamente las duraciones finitas de 360 a 86 400 s.)*

---

## 2. Estado transitorio de la calculadora en pantalla (solo cliente, Corte 1)

La calculadora no persiste nada en el servidor ni en `localStorage`. Vive únicamente en el estado de la vista Teclado (`web/js/app.js` + `web/js/teclado.js`).

### 2.1 Estructura de entrada y evaluación

| Concepto | Representación | Reglas | Requisitos |
|---|---|---|---|
| `expresion` | `string` (ej. `""`, `"25.50"`, `"3 × 25 + 20"`, `"25 + "`) | Secuencia de operandos separados por `" + "` o `" × "`. Máximo **20 operandos** | RF-028, RF-030, RF-046 |
| Operando individual | `string` (ej. `"0."`, `"25.5"`, `"12345"`) | Máx. 5 dígitos enteros, máx. 2 decimales, un solo `.`, `.` inicial → `"0."`, `"0"` + dígito → reemplaza `"0"`; `.` final antes de operador se quita (`"25."` → `"25"`) | RF-030, RF-045 |
| `ResultadoEvaluacion` | `{ tiene_operadores: boolean, incompleta: boolean, desbordado: boolean, total_centavos: bigint \| null, texto_total: string, monto_envio: number \| null }` | Precedencia `×` antes que `+`; aritmética exacta `BigInt`; redondeo `HALF_UP` a 2 decimales; si `incompleta`, calcula el total parcial del prefijo anterior al operador final; si `total_centavos > 99_999_999n`, `desbordado = true` | RF-029, RF-031, RF-032, RF-037, RF-047 |

### 2.2 Reglas de activación de botones en la vista Teclado

| Botón | Condición para estar activo | Requisitos |
|---|---|---|
| **Cobrar** | `expresion !== ""` y `!incompleta` y `!desbordado` y `total_centavos > 0n` | RF-037, RF-039 |
| **Monto libre** | Toda entrada **sin operadores** cuyo valor numérico sea `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`); desactivado ante cualquier operador (`"0 × 25"`, `"0 + "`) o valor `> 0` | RF-038, QA-1, QP-1 |

---

## 3. Estado de selección de duración y memoria de escuchas en la web

### 3.1 Estado en la vista Teclado (`web/js/app.js`)

| Campo | Tipo | Valor inicial | Reinicio / conservación | Requisitos |
|---|---|---|---|---|
| `duracion_segundos` | `number` | `600` (10 min) | Vuelve a `600` en *Nuevo cobro*, cancelación confirmada o recarga volviendo a Teclado; **se conserva** si falla `crear_cobro` o llega sin `qr_imagen` | RF-015, RF-017, RF-018 |

Opciones del selector:
- Corte 1: `360` ("6 min"), `600` ("10 min"), `1800` ("30 min"), `3600` ("1 h"), `86400` ("24 h").
- Corte 2: agrega `0` ("Sin vencimiento").

### 3.2 Registro en `localStorage` (`web/js/memoria.js`, clave `pago_facil_escucha`)

Extiende el objeto JSON de la spec 002 manteniendo compatibilidad con objetos existentes de 2 claves:

```json
{
  "en_pantalla": "Xk3vQ9aZ1bNc",
  "anteriores": ["Ab12Cd34Ef56"],
  "topes_anteriores": {
    "Ab12Cd34Ef56": 1794701200
  }
}
```

- `topes_anteriores` (opcional): mapa `{ [cobro_id]: entero_unix }` únicamente para cobros anteriores cuya duración es `> 3600` s o sin vencimiento (`RF-044`, `QA-4`). Indica el instante Unix del servidor en que termina su escucha acotada de 20 minutos en pantalla (`min(fin_ventana, ahora_servidor + 1200)`).
- **Omisión al guardar (`QP-3`)**: `web/js/memoria.js` omite la clave `"topes_anteriores"` al guardar en `localStorage` cuando esté vacía (solo la escribe si existe al menos un cobro anterior largo `> 1 h`), preservando el formato de 2 claves que validan las pruebas de `web/tests/test_recuperar.py`.
- **Cálculo diferido (`QP-4`)**: si `pasar_a_anterior()` ocurre mientras el cobro aún se recupera (`escucha.cobro === null`), el tope local se calcula y guarda al llegar la primera respuesta de recuperación cuando `es_anterior && tope_local === null` y el cobro recuperado dure `> 1 h` (`duracion_segundos === 0 || duracion_segundos > 3600`).
- Validación estricta al leer (`forma_valida` en `memoria.js`, `RF-077` de spec 002):
  - Solo se admiten las claves `en_pantalla`, `anteriores` y opcionalmente `topes_anteriores`.
  - Si `topes_anteriores` existe, debe ser un objeto plano donde cada clave cumple `ID_VALIDO` (`/^[A-Za-z0-9_-]{1,32}$/`), aparece en `anteriores` y su valor es un entero finito `> 0`. Si no cumple, el registro entero se descarta (`null`).
