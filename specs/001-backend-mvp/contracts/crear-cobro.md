# Contrato: crear un cobro

## 1. Método, ruta y propósito

`POST /api/cobros`: el negocio pide un cobro y recibe su QR CoDi creado con pey.

## 2. Requisitos

RF-001, RF-002, RF-003 (C2), RF-004, RF-005, RF-006, RF-007, RF-008, RF-009, RF-010, RF-034, RF-035, RF-036, RF-042.

## 3. Petición

Cuerpo JSON:

| Campo | Tipo | Obligatorio | Validación | Requisitos |
|---|---|---|---|---|
| `monto` | número o `null` | No | Monto fijo: mayor a 0, máximo 2 decimales, ≤ `MONTO_MAXIMO` ($100 por defecto). `null`, ausente o `0` = monto libre (corte 2; en el corte M0 se rechaza con 422). Negativo, texto o más de 2 decimales: 422 | RF-002, RF-003, RF-004 |
| `concepto` | texto | No | Máximo 40 caracteres imprimibles; espacios sobrantes quitados; "Cobro" si falta o queda vacío | RF-005, RF-042 |

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 201 | Cobro creado | [Objeto cobro](#objeto-cobro) |
| 422 | Monto o concepto no válidos. No se llama a pey | `{"detail": "<mensaje>"}`. Mensajes: "Escribe un monto mayor a $0 con máximo 2 decimales", "El monto máximo de la demo es $100", "El concepto tiene caracteres no válidos", "El concepto puede tener máximo 40 letras" |
| 429 | La IP del cliente ya pidió el máximo de cobros del minuto. No se llama a pey | `{"detail": "Demasiados cobros seguidos. Espera un minuto."}` |
| 502 | pey rechazó la llave (401/403) o falló con un error general | `{"detail": "pey rechazó la llave del servidor"}` o `{"detail": "No se pudo crear el cobro con pey. Intenta de nuevo."}` |
| 503 | Falta la llave de pey, o pey está en mantenimiento (503) | `{"detail": "El servidor no tiene configurada la llave de pey"}` o `{"detail": "pey está en mantenimiento. Intenta de nuevo en unos minutos."}` |

Con 422, 429, 502 y 503 el cobro **no** queda guardado (RF-009).

- Si pey no responde en **10 s**, se responde 502 "No se pudo crear el cobro con pey. Intenta de nuevo." (QP-1).
- Las peticiones rechazadas con 422 no cuentan para el límite de 10 por minuto: solo cuentan las que llegan a pedirle el QR a pey.

<a id="objeto-cobro"></a>
### Objeto cobro

Es el mismo en todas las respuestas que devuelven un cobro y en los eventos del canal.

| Campo | Tipo | Requisitos |
|---|---|---|
| `id` | texto | RF-008 |
| `codi_qr_id` | texto | RF-008 |
| `monto` | número o `null` | RF-008 |
| `monto_libre` | booleano | RF-008 |
| `concepto` | texto | RF-008 |
| `estado` | `pendiente`, `pagado`, `vencido` o `cancelado` | RF-008 |
| `qr` | texto (contenido del QR) | RF-008 |
| `qr_imagen` | texto (PNG en base64) o `null` | RF-008 |
| `creado_en` | entero (Unix) | RF-008 |
| `expira_en` | entero (Unix) | RF-008 |
| `fin_ventana` | entero (Unix) | RF-032 |
| `numero_de_pagos` | entero | RF-008 |
| `total_recibido` | número | RF-008 |
| `pagado_en` | entero (Unix) o `null`: hora del último pago | RF-008 |
| `pagos` | lista de [objeto pago](#objeto-pago) | RF-018, RF-019 |
| `hora_servidor` | entero (Unix): la hora actual del servidor al armar este objeto, para que la pantalla calcule su desfase (C-2) | RF-008 |

<a id="objeto-pago"></a>
### Objeto pago

| Campo | Tipo | Requisitos |
|---|---|---|
| `numero` | entero | RF-016 |
| `monto_recibido` | número | RF-018 |
| `monto_distinto` | booleano | RF-019 |
| `pagado_en` | entero (Unix) | RF-018 |

El objeto pago no expone el `transaccion_id` de pey ni ningún dato bancario del pagador.

## 5. Ejemplo

Petición:

```json
{ "monto": 0.01, "concepto": "Tacos" }
```

Respuesta 201:

```json
{
  "id": "Xk3vQ9aZ1bNc",
  "codi_qr_id": "ab12cd34ef",
  "monto": 0.01,
  "monto_libre": false,
  "concepto": "Tacos",
  "estado": "pendiente",
  "qr": "{\"TYP\":19,\"v\":{\"DEV\":\"...\"}}",
  "qr_imagen": "iVBORw0KGgo...",
  "creado_en": 1794700000,
  "expira_en": 1794700600,
  "fin_ventana": 1794700600,
  "numero_de_pagos": 0,
  "total_recibido": 0,
  "pagado_en": null,
  "pagos": []
}
```

## 6. Seguridad

- No requiere autenticación: hay un solo negocio de demo (#24).
- El límite es por **IP del cliente**, obtenida detrás del proxy del hosting (RF-034, research R-5).
- CORS: solo los orígenes de `WEB_ORIGIN`, con los métodos `GET` y `POST` (RF-035).
- La petición a pey lleva `metadata: {"cobroId": <id>}` (RF-007) y nunca la devuelve.
- Nunca se devuelve la llave de pey, ni en los errores (RF-036). Los errores de pey quedan en el registro con su `requestId` (RF-039).
