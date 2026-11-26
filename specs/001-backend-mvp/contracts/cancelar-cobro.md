# Contrato: cancelar un cobro *(corte 2)*

## 1. Método, ruta y propósito

`POST /api/cobros/{id}/cancelar`: el negocio cancela un cobro que todavía no se paga. Es una cancelación local: el QR sigue pagable en el banco, porque pey no permite anularlo.

## 2. Requisitos

RF-023, RF-024, RF-030, RF-035, RF-039.

## 3. Petición

| Campo | Tipo | Obligatorio | Validación | Requisitos |
|---|---|---|---|---|
| `id` (en la ruta) | texto | Sí | Debe existir | RF-023 |

Sin cuerpo.

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | El cobro estaba *pendiente* y queda *cancelado* | [Objeto cobro](crear-cobro.md#objeto-cobro) con `estado: "cancelado"` |
| 403 | La petición trae `Origin` y no está en `WEB_ORIGIN` ni su host y puerto coinciden con el encabezado `Host`. No se consulta el almacén | `{"detail": "Origen no permitido"}` |
| 404 | No existe | `{"detail": "Ese cobro no existe"}` |
| 409 | El cobro está *pagado*, *vencido* o ya *cancelado* | `{"detail": "Solo se puede cancelar un cobro que todavía no se paga ni vence"}` |

Al cancelar, el canal emite `cancelado` en menos de 15 s (RF-030) y queda registro (RF-039). El canal sigue abierto hasta `fin_ventana`, por si llega un pago al QR cancelado (RF-017, RF-022).

## 5. Ejemplo

`POST /api/cobros/Xk3vQ9aZ1bNc/cancelar`, respuesta 200: el objeto cobro con `"estado": "cancelado"`.

## 6. Seguridad

- Sin autenticación: cualquiera con el `id` puede cancelar (supuesto aceptado, §7 de la spec). Cancelar no borra pagos ni impide registrarlos.
- Usa `POST`. CORS permite ese método, y además, si viene `Origin`, tiene que estar en `WEB_ORIGIN` o coincidir en host y puerto con el encabezado `Host` (no se compara el esquema). Si no, 403 sin cancelar. Sin `Origin` se acepta. `Origin: null` se rechaza (RF-035, C-11).
