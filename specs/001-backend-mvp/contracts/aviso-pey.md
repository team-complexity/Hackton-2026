# Contrato: aviso de pago de pey (webhook recibido)

## 1. Método, ruta y propósito

`POST /webhooks/pey`: pey avisa que un QR recibió un pago. Es la vía principal para confirmar pagos; la consulta de respaldo cubre las fallas.

## 2. Requisitos

RF-011, RF-012, RF-013, RF-014, RF-017, RF-018, RF-020, RF-029, RF-037, RF-039, CE-004, CE-005, CE-010.

## 3. Petición

**Cabeceras** (Standard Webhooks):

| Cabecera | Validación | Requisitos |
|---|---|---|
| `webhook-id` | Identificador del envío; primera barrera contra reenvíos | RF-014 |
| `webhook-timestamp` | Dentro de ±5 minutos de la hora del servidor (tolerancia de `standardwebhooks`) | RF-011 |
| `webhook-signature` | Firma `v1,...` válida con `PEY_WEBHOOK_SECRET` sobre el cuerpo exacto | RF-011 |

**Cuerpo** (evento `codi.qr.payment_received`, según la documentación de pey):

| Campo | Tipo | Obligatorio | Validación | Requisitos |
|---|---|---|---|---|
| `type` | texto | Sí | Solo se procesa `codi.qr.payment_received`; otro tipo se ignora | RF-013 |
| `codiQrId` | texto | Sí | Busca el cobro; si no existe, se ignora y queda registro | RF-012, RF-039 |
| `transactionId` | texto (ULID) | Sí | Deduplicación definitiva | RF-014 |
| `amount` | número | Sí | Monto recibido del evento de pago. Si no se puede leer, o es 0 o negativo, 400 sin marcar el `webhook-id`. Otro tipo de evento se ignora aunque el `amount` sea 0 | RF-018 |
| `datePaid` | entero (Unix) | No | Hora del pago; si falta, la hora del servidor | RF-018 |
| `concept`, `numRef`, `metadata`, `apiKeyId`, `bankAccountId` | — | No | No se usan | — |

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Pago registrado | `{"recibido": true, "procesado": true}` |
| 200 | Ignorado a propósito: otro tipo de evento, cobro desconocido, `webhook-id` ya visto o transacción repetida | `{"recibido": true, "procesado": false}` |
| 400 | Firma válida, pero cuerpo no JSON, o el evento de pago (`codi.qr.payment_received`) trae un `amount` ilegible, de 0 o negativo. El `webhook-id` **no** se marca como visto, para que el reintento se procese (research R-8). Un evento de otro tipo se ignora y sí se marca, también con `amount` de 0 | `{"detail": "Aviso con datos no válidos"}` |
| 401 | Firma ausente, inválida o fuera de tiempo. Ningún cobro cambia | `{"detail": "Firma no válida"}` |
| 503 | `PEY_WEBHOOK_SECRET` vacío. No se procesa nada | `{"detail": "El aviso de pey todavía no está configurado"}` |

- Respuesta en menos de 1 s (CE-010): el manejador ya hace una llamada de red (guardar en la base de datos); la meta se mantiene.
- Si el cobro ya tenía pagos, una transacción nueva se registra como pago siguiente, con su número, y responde `procesado: true` (RF-015, RF-016; desde el corte M0 por C-1).

## 5. Ejemplo

Cuerpo (datos ficticios):

```json
{
  "type": "codi.qr.payment_received",
  "amount": 0.01,
  "codiQrId": "ab12cd34ef",
  "transactionId": "01M3QR8H0RH0XBCKYYD242YXNV",
  "datePaid": 1794700123,
  "concept": "Tacos",
  "numRef": "1234567"
}
```

Respuesta: `{"recibido": true, "procesado": true}`.

## 6. Seguridad

- La firma se verifica **antes** de leer el JSON; sin firma válida no se toca ningún dato (principio I).
- El secreto vive solo en `backend/.env` o en el hosting y nunca aparece en respuestas ni registros (RF-036).
- El registro guarda el `codiQrId`, el `transactionId` y el id del cobro; nunca las cabeceras ni el cuerpo completo.
- No se aplica CORS ni límite por IP: no lo llama un navegador.
