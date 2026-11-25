# Modelo de datos (Fase 1): Spec 001 — Backend del MVP

- **Fecha**: 2026-11-14
- **Plan**: [plan.md](plan.md)
- **Almacenamiento**: los cobros, pagos y avisos se guardan en la base de datos (spec 003). Los límites por IP y los canales siguen en memoria, en un solo proceso.

---

## 1. Cobro

| Campo | Tipo | Regla | Requisitos |
|---|---|---|---|
| `id` | texto | Aleatorio, no adivinable (12 caracteres URL-safe) | RF-008, supuesto de §7 |
| `monto` | decimal o vacío | Vacío = monto libre. Monto fijo: `0 < monto ≤ MONTO_MAXIMO`, máximo 2 decimales | RF-002, RF-003 |
| `concepto` | texto | 1 a 40 caracteres imprimibles, espacios sobrantes quitados, "Cobro" si falta | RF-005, RF-042 |
| `num_ref` | texto | 7 dígitos aleatorios, como pide pey (`^[0-9]{1,7}$`) | RF-007 |
| `codi_qr_id` | texto | El `id` que devuelve pey al crear el QR; con él llegan los avisos | RF-012 |
| `qr` | texto | `qrString` de pey | RF-008 |
| `qr_imagen` | texto o vacío | PNG en base64 si pey lo entrega | RF-008 |
| `creado_en` | entero (Unix) | Según el `Reloj` | RF-008 |
| `expira_en` | entero (Unix) | `creado_en + 600` | RF-006, RF-021 |
| `fin_ventana` | entero (Unix) | `expira_en + GRACIA` (0 en el corte M0, 600 desde el corte 2) | RF-022, RF-032 |
| `cancelado_en` | entero o vacío | Hora de la cancelación (corte 2) | RF-023 |
| `pagos` | lista de Pago | En orden de registro, sin límite (desde el corte M0, C-1) | RF-015, RF-016 |
| `ultima_consulta_pey` | número | Hora de la última consulta de respaldo; no se publica | RF-025, RF-040 |

**Calculados** (no se guardan):

- `monto_libre` = `monto` vacío.
- `numero_de_pagos` = cantidad de pagos.
- `total_recibido` = suma de `monto_recibido` de los pagos.
- `pagado_en` = hora del último pago.
- `estado`: ver §3.
- `en_ventana(ahora)` = `ahora < fin_ventana`.

## 2. Pago

| Campo | Tipo | Regla | Requisitos |
|---|---|---|---|
| `transaccion_id` | texto | `transactionId` del aviso o `id` de la consulta (los dos son el mismo ULID). Único en todo el sistema | RF-014 |
| `numero` | entero | 1, 2, 3… dentro de su cobro | RF-016 |
| `monto_recibido` | decimal | `amount` de pey (total) | RF-018 |
| `monto_base` | decimal o vacío | `amountBreakdown.base` si viene en la consulta; vacío si llegó por el aviso | RF-018, RF-019 |
| `pagado_en` | entero (Unix) | `datePaid` de pey, o la hora del `Reloj` si falta | RF-018 |
| `fuente` | `aviso` o `consulta` | De dónde se supo; solo para los registros | RF-039 |

**Calculado**: `monto_distinto` = el cobro es de monto fijo y (`monto_base` si existe, o si no `monto_recibido`) ≠ `monto` del cobro (RF-019, RF-020).

## 3. Estados y transiciones

El estado se calcula con la hora del `Reloj` (`ahora`):

```text
si hay pagos                         → pagado
si no, si cancelado_en               → cancelado
si no, si ahora ≥ expira_en          → vencido
si no                                → pendiente
```

```text
            primer pago                       primer pago
pendiente ─────────────→ pagado ←───────────── vencido
    │  └──── 10 min ─────────────────────────────↑
    │                       ↑ primer pago
    └── cancelar (C2) ──→ cancelado
```

| Desde | Hacia | Disparador | Requisitos |
|---|---|---|---|
| *pendiente* | *pagado* | Primer pago, por aviso o por consulta | RF-017 |
| *pendiente* | *vencido* | `ahora ≥ expira_en` | RF-021 |
| *pendiente* | *cancelado* | El negocio cancela (corte 2) | RF-023 |
| *vencido* | *pagado* | Primer pago (pago tardío) | RF-017, RF-022 |
| *cancelado* | *pagado* | Primer pago al QR cancelado | RF-017 |
| *pagado* | *pagado* | Pago siguiente: se agrega a `pagos` sin cambiar de estado | RF-015 |

- No hay transición de *pagado* a ningún otro estado.
- Cancelar un cobro que no está *pendiente* se rechaza (RF-024).
- La ventana de escucha no es un estado: decide si se sigue consultando a pey y si el canal sigue abierto (RF-025, RF-032, RF-040).

## 4. Registro de pagos (reglas)

1. Un `transaccion_id` ya visto se ignora, venga del aviso o de la consulta (RF-014).
2. Si no, se agrega con `numero = len(pagos) + 1` (RF-015, RF-016), desde el corte M0 (C-1).
3. Si `monto_distinto`, se deja una advertencia (RF-020) y se publica en el pago (RF-019).
4. Cada pago agregado publica el evento `pago` en el canal del cobro (RF-029).

## 5. Repositorio

Los cobros, pagos y avisos se guardan en la base de datos (spec 003). El proceso guarda además esta copia en memoria:

| Índice | Para qué |
|---|---|
| `id → Cobro` | Ver, cancelar y abrir el canal |
| `codi_qr_id → id` | Relacionar el aviso de pey con su cobro (RF-012) |
| `transacciones vistas` (conjunto) | Deduplicar (RF-014) |
| `webhook-id vistos` (conjunto) | Primera barrera contra reenvíos (principio II) |

## 6. Límites de la demo (en memoria)

Los límites por IP y los canales siguen en memoria. Los cobros, pagos y avisos se guardan en la base de datos (spec 003).

| Límite | Ventana | Valor | Requisitos |
|---|---|---|---|
| Cobros por IP del cliente | 60 s deslizantes | 10 (configurable) | RF-034 |
| Canales abiertos por IP del cliente | Mientras estén abiertos | 10 | RF-041 |
| Consultas de respaldo por cobro | — | Una cada 3 s al ver el cobro; una cada 5 s desde el canal | RF-025, RF-040 |
