# Contrato: ver un cobro

## 1. Método, ruta y propósito

`GET /api/cobros/{id}`: devuelve el estado actual de un cobro. Mientras el cobro está dentro de su ventana de escucha, aprovecha para preguntarle a pey por sus pagos (consulta de respaldo).

## 2. Requisitos

RF-008, RF-014, RF-025, RF-026, RF-027.

## 3. Petición

| Campo | Tipo | Obligatorio | Validación | Requisitos |
|---|---|---|---|---|
| `id` (en la ruta) | texto | Sí | Debe existir | RF-008 |

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | El cobro existe | [Objeto cobro](crear-cobro.md#objeto-cobro) |
| 404 | No existe | `{"detail": "Ese cobro no existe"}` |

**Consulta de respaldo:**

- Si `ahora < fin_ventana` y pasaron al menos 3 s desde la última consulta a pey de ese cobro, el servidor consulta `GET /transaction/codi/qr/{codi_qr_id}` **antes** de responder. Sigue las páginas solo mientras traigan transacciones nuevas (QP-2) y espera como máximo 4 s por petición (QP-1).
- Registra los pagos `PAID` nuevos y los avisa por el canal (RF-026).
- Si pey falla o no responde en 4 s, responde 200 con el último estado conocido y deja una advertencia en el registro (RF-027). Nunca responde 5xx por culpa de la consulta.

## 5. Ejemplo

`GET /api/cobros/Xk3vQ9aZ1bNc`, respuesta 200 con un pago:

```json
{
  "id": "Xk3vQ9aZ1bNc",
  "codi_qr_id": "ab12cd34ef",
  "monto": 0.01,
  "monto_libre": false,
  "concepto": "Tacos",
  "estado": "pagado",
  "qr": "...",
  "qr_imagen": null,
  "creado_en": 1794700000,
  "expira_en": 1794700600,
  "fin_ventana": 1794700600,
  "numero_de_pagos": 1,
  "total_recibido": 0.01,
  "pagado_en": 1794700123,
  "pagos": [
    { "numero": 1, "monto_recibido": 0.01, "monto_distinto": false, "pagado_en": 1794700123 }
  ]
}
```

## 6. Seguridad

- Cualquiera que conozca el `id` ve el cobro (supuesto aceptado, §7 de la spec). El `id` no se puede adivinar.
- No se aplica límite por IP: la consulta a pey ya está acotada a una cada 3 s por cobro.
