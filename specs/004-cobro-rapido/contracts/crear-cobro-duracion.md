# Contrato: crear cobro con duración configurable (y objeto cobro ampliado)

> Amplía [specs/001-backend-mvp/contracts/crear-cobro.md](../../001-backend-mvp/contracts/crear-cobro.md) y [canal-avisos.md](../../001-backend-mvp/contracts/canal-avisos.md) (cambio aprobado `C-12`, sin aplicar todavía en la spec 001).

## 1. Método, ruta y propósito

`POST /api/cobros`: el negocio pide un cobro CoDi indicando opcionalmente cuántos segundos dura el QR (`duracion_segundos`), desde 6 minutos hasta 24 horas en el corte 1, y también `0` (sin vencimiento) en el corte 2. El objeto cobro ampliado es el mismo que devuelven `GET /api/cobros/{id}`, `POST /api/cobros/{id}/cancelar` y los eventos de `GET /api/cobros/{id}/eventos`.

## 2. Requisitos

RF-001 a RF-012, RF-043; CE-001, CE-003, CE-004, CE-009, CE-010.

## 3. Petición

Cuerpo JSON de `POST /api/cobros`:

| Campo | Tipo | Obligatorio | Validación | Requisitos |
|---|---|---|---|---|
| `monto` | número o `null` | No | Igual que spec 001: monto fijo `> 0`, máx. 2 decimales, `<= MONTO_MAXIMO`; `null`, ausente o `0` = monto libre | Spec 001 RF-002 a RF-004 |
| `concepto` | texto o `null` | No | Igual que spec 001: máx. 40 caracteres imprimibles; `"Cobro"` si falta o queda vacío | Spec 001 RF-005, RF-042 |
| `duracion_segundos` | entero o `null` | No | Ausente o `null` → `600` (10 min). **Corte 1**: entero `360 <= valor <= 86400` (rechaza `0`, negativos, decimales, booleanos y texto). **Corte 2**: `0` (sin vencimiento) o entero `360 <= valor <= 86400` | RF-001, RF-002, RF-006, RF-008 |

## 4. Respuestas por código

| Código | Cuándo | Cuerpo |
|---|---|---|
| 201 | Cobro creado con éxito | [Objeto cobro ampliado](#objeto-cobro-ampliado) |
| 403 | `Origin` no permitido (`C-11`, antes de leer cuerpo y de llamar a pey) | `{"detail": "Origen no permitido"}` |
| 422 | `monto`, `concepto` o `duracion_segundos` no válidos. No cuenta para el límite por IP, no guarda nada y no llama a pey | `{"detail": "<mensaje>"}`. Mensajes nuevos de duración: en **Corte 1** `"Elige una duración entre 6 minutos y 24 horas"`; en **Corte 2** `"Elige una duración entre 6 minutos y 24 horas, o sin vencimiento"` |
| 429 | Límite de cobros por minuto alcanzado | `{"detail": "Demasiados cobros seguidos. Espera un minuto."}` |
| 502 | pey rechazó la llave o falló al crear el QR | Igual que spec 001 |
| 503 | Falta llave de pey, pey en mantenimiento o falla del almacén | Igual que spec 001 y spec 003 |

<a id="objeto-cobro-ampliado"></a>
### Objeto cobro ampliado

Mantiene todos los campos de la spec 001 y agrega/ajusta los siguientes:

| Campo | Tipo | Requisitos |
|---|---|---|
| `duracion_segundos` | entero (`360..86400`, o `0` en Corte 2 si es sin vencimiento) | RF-007 |
| `expira_en` | entero (Unix) en cobros finitos; `null` en cobros sin vencimiento (`[C2]`) | RF-003, RF-007, RF-008 |
| `fin_ventana` | entero (Unix), siempre presente: `expira_en + 600` en finitos; `creado_en + 86400` en sin vencimiento (`[C2]`) | RF-005, RF-007, RF-010, RF-011 |

### Comportamiento del canal `GET /api/cobros/{id}/eventos` para cobros sin vencimiento (`[C2]`)

- Mientras `ahora < fin_ventana` (24 horas desde `creado_en`), el canal emite `estado`, `pago`, `cancelado` y la señal de vida `: sigo conectado` cada 15 s, y consulta a pey cada 5 s.
- **Nunca** emite el evento `vencido` (RF-009).
- Al alcanzarse `fin_ventana` (24 horas), emite `fin` con el objeto cobro actualizado y cierra la conexión (RF-011).
- Un aviso firmado posterior en `POST /webhooks/pey` (días después) sigue registrando el pago una sola vez y actualizando `estado` a `"pagado"`, `numero_de_pagos` y `total_recibido` (RF-012).

## 5. Ejemplos

### Corte 1 — Cobro finito de 30 minutos

Petición:

```json
{
  "monto": 95.0,
  "concepto": "Tacos y refresco",
  "duracion_segundos": 1800
}
```

Respuesta `201`:

```json
{
  "id": "Xk3vQ9aZ1bNc",
  "codi_qr_id": "ab12cd34ef",
  "monto": 95.0,
  "monto_libre": false,
  "concepto": "Tacos y refresco",
  "estado": "pendiente",
  "qr": "{\"TYP\":19,\"v\":{\"DEV\":\"...\"}}",
  "qr_imagen": "iVBORw0KGgo...",
  "creado_en": 1794700000,
  "duracion_segundos": 1800,
  "expira_en": 1794701800,
  "fin_ventana": 1794702400,
  "numero_de_pagos": 0,
  "total_recibido": 0,
  "pagado_en": null,
  "pagos": [],
  "hora_servidor": 1794700001
}
```

### Corte 2 — Cobro sin vencimiento de monto libre

Petición:

```json
{
  "monto": null,
  "concepto": "Mostrador",
  "duracion_segundos": 0
}
```

Respuesta `201`:

```json
{
  "id": "Lm8nP2qR4sTu",
  "codi_qr_id": "cd56ef78gh",
  "monto": null,
  "monto_libre": true,
  "concepto": "Mostrador",
  "estado": "pendiente",
  "qr": "{\"TYP\":19,\"v\":{\"DEV\":\"...\"}}",
  "qr_imagen": "iVBORw0KGgo...",
  "creado_en": 1794700000,
  "duracion_segundos": 0,
  "expira_en": null,
  "fin_ventana": 1794786400,
  "numero_de_pagos": 0,
  "total_recibido": 0,
  "pagado_en": null,
  "pagos": [],
  "hora_servidor": 1794700001
}
```

### Error 422 — Duración fuera de rango (Corte 1)

Petición:

```json
{ "monto": 10.0, "duracion_segundos": 300 }
```

Respuesta `422`:

```json
{ "detail": "Elige una duración entre 6 minutos y 24 horas" }
```

## 6. Notas de seguridad

- `duracion_segundos` se valida en el servidor antes de consumir el límite por IP y antes de hablar con pey (RF-006); los valores booleanos (`true`/`false`), decimales o fuera de rango se rechazan con 422.
- El valor enviado a pey en `POST /codi/qr` es únicamente el entero validado `duracion_segundos`; las credenciales de pey nunca salen del backend (RF-043, principio III).
- Se conservan intactos CORS, la verificación de `Origin` (`C-11`), el límite de cobros por minuto por IP y el límite de 10 canales por IP (`spec 001 RF-034`, `RF-035`, `RF-041`).
