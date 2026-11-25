# Modelo de datos: Web del MVP

- **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

La pantalla no crea datos de negocio: el cobro y el pago son los de la spec 001 ([objeto cobro](../001-backend-mvp/contracts/crear-cobro.md#objeto-cobro)). Aquí está el estado propio de la página, que vive en memoria y, desde el corte 2, parcialmente en el celular.

---

## 1. Estado de la pantalla

| Campo | Qué guarda | Valores | Requisitos |
|---|---|---|---|
| `vista` | La vista actual | `teclado`, `generando`, `qr`, `qr_vencido`, `pago_recibido`, `error` | Glosario de la spec |
| `monto` | El texto tecleado | `""`, `"0."`, `"25.5"`… Como máximo 5 dígitos enteros y 2 decimales | RF-001 a RF-004, RF-066 a RF-068 |
| `concepto` | Lo escrito en el campo | Hasta 40 caracteres | RF-005 |
| `mensaje` | El mensaje de error en la vista Teclado, o nada | Texto del servidor o de la pantalla | RF-012, RF-013, RF-078 |
| `en_pantalla` | El identificador del cobro en pantalla, o nada | Identificador o `null` | Glosario |
| `accion_en_curso` | Si se está creando o cancelando | `null`, `creando`, `cancelando` | RF-011, RF-073 |
| `sonido_desbloqueado` | Si el dueño ya hizo un gesto para iniciar la reproducción | `true` / `false` | RF-025, RF-054 |
| `qr_reabierto` | Si la vista QR se volvió a mostrar tras un pago (C2) | `true` / `false` | RF-070, RF-071 |

## 2. Escucha (una por cobro en escucha)

| Campo | Qué guarda | Requisitos |
|---|---|---|
| `id` | Identificador del cobro | — |
| `cobro` | Objeto vigente recibido del servidor. Se descartan los datos con menos pagos o, a igualdad de pagos, con hora del servidor anterior | RF-016, RF-023, RF-079 |
| `desfase` | `hora_servidor − ahora_del_celular` del último cobro recibido (0 si no vino `hora_servidor`) | RF-019 |
| `canal` | `sin_canal` (solo consulta cada 3 s, QP-1), `abriendo`, `abierto`, `cortado` o `cerrado` | RF-030 a RF-032 |
| `_consulta`, `_consulta_en_curso` | Temporizador de 8 s con el canal abierto o de 3 s sin él, y bandera de GET en curso | RF-030, RF-079 |
| `es_anterior` | `false` para el cobro en pantalla, `true` para un cobro anterior (C2) | RF-043 a RF-045 |

**Ciclo de una escucha**:

```text
abriendo ──open──▶ abierto ──error──▶ cortado (consulta cada 3 s)
   ▲                  ▲                 │
   │                  └──────open───────┤
   │                                    │ CLOSED y la consulta da 200
   └────────── reintento cada 15 s ─────┘
cualquiera ──fin, hora del servidor ≥ fin_ventana, 404 o Nuevo cobro (C1)──▶ terminada
```

- **Reparto de canales (QP-1)**: como máximo 3 escuchas tienen canal a la vez: siempre la del cobro en pantalla y las de los dos cobros anteriores más recientes. Las demás empiezan en `sin_canal`, y al terminar una escucha con canal, la siguiente más reciente pasa a `abriendo`.
- Termina con `fin` (RF-040), cuando la consulta muestra que la hora del servidor ya pasó `fin_ventana` (RF-040), o con un 404 (RF-056, RF-057).
- En el corte 1 termina también con Nuevo cobro. En el corte 2, Nuevo cobro y la cancelación confirmada solo la pasan a `es_anterior = true` (RF-043, RF-049).

## 3. Avisados

- Por cobro, `ultimo_avisado`: el número de pago más alto ya mostrado. Un pago es **nuevo** si su `numero` es mayor (RF-029).
- Al crear un cobro vale 0. Al recuperar un cobro (C2) se fija en su `numero_de_pagos` actual, después de mostrar esos pagos sin sonido (RF-053, RF-075).
- Como el servidor numera los pagos 1, 2, 3… en orden de registro (spec 001, RF-016), comparar números basta para deduplicar.

## 4. Lo recordado en el celular (corte 2)

Clave `pago_facil_escucha` en `localStorage`:

```json
{ "en_pantalla": "Xk3vQ9aZ1bNc", "anteriores": ["Ab12Cd34Ef56", "Zz98Yy76Xx54"] }
```

- **Validación al leer** (RF-077):
  - JSON con esas dos claves;
  - `en_pantalla` es `null` o un identificador;
  - `anteriores` es una lista de identificadores;
  - cada identificador tiene de 1 a 32 caracteres `[A-Za-z0-9_-]`.
  - Si algo no cumple, se ignora todo.
- **Si leer o escribir falla**, se sigue sin recordar (RF-076).
- Se reescribe en cada cambio de las escuchas.

## 5. Vistas y transiciones

```text
Teclado ──Cobrar / Monto libre──▶ Generando QR ──201 con imagen──▶ QR
   ▲                                  │
   │◀──error, sin conexión o sin imagen (RF-078), con lo escrito conservado
   │
QR ──pago nuevo──▶ Pago recibido ──pago nuevo──▶ Pago recibido (suena otra vez)
QR ──vigencia termina sin pagos──▶ QR vencido ──pago tardío──▶ Pago recibido
QR ──Cancelar cobro (C2) y confirmado, o `cancelado` de fuera──▶ Teclado (el cobro pasa a anterior)
Pago recibido ──Mostrar QR otra vez (C2, QR vigente)──▶ QR ──vence──▶ Pago recibido
QR / QR vencido / Pago recibido ──404 del servidor──▶ Error
QR / QR vencido / Pago recibido / Error ──Nuevo cobro──▶ Teclado vacío
```

Encima de cualquier vista pueden aparecer tres avisos que no la cambian:

- el aviso de pago de un cobro anterior (C2, RF-045);
- "Reconectando…" (RF-032), en las vistas del cobro en pantalla;
- «Toca para activar el sonido» al recuperar cobros o si el navegador rechaza el sonido de un pago (RF-054).
