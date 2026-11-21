# Contrato: uso del servidor de la spec 001

## 1. Propósito

Qué rutas del servidor de PAGO FÁCIL usa la pantalla, cómo interpreta cada respuesta y qué espera del cambio C-2. La fuente de verdad del servidor sigue siendo [specs/001-backend-mvp/contracts/](../../001-backend-mvp/contracts/). Este archivo solo fija lo que la pantalla hace con cada respuesta.

## 2. Requisitos

RF-009 a RF-014, RF-019, RF-020, RF-030 a RF-034, RF-040, RF-047, RF-050, RF-056, RF-057, RF-063, RF-064, RF-078.

## 3. Configuración

`web/config.js` (RF-064):

```js
window.PAGO_FACIL = { servidor: "https://api.ejemplo.mx" }; // "" = el mismo origen que la web
```

Todas las rutas se arman como `servidor + ruta`. Es el único lugar con la dirección (DP-4, R-4).

## 4. Rutas y respuestas

### Crear un cobro: `POST /api/cobros` ([contrato 001](../../001-backend-mvp/contracts/crear-cobro.md))

| Petición | Cuándo | Requisitos |
|---|---|---|
| `{"monto": 25.5, "concepto": "Tacos"}` | Cobrar | RF-009 |
| `{"monto": null, "concepto": "Propina"}` | Monto libre (C2) | RF-008 |

| Respuesta | Qué hace la pantalla | Requisitos |
|---|---|---|
| 201 con `qr_imagen` | Vista QR; abre la escucha | RF-015, RF-020 |
| 201 con `qr_imagen` en `null` | Vista Teclado con "No se pudo mostrar el QR. Intenta de nuevo."; conserva lo escrito; no escucha | RF-078, RF-014 |
| 422, 429, 502, 503 | Vista Teclado con el `detail` del servidor; conserva lo escrito | RF-012, RF-014 |
| Sin respuesta en 15 s o fallo de red | Vista Teclado con "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo."; conserva lo escrito | RF-013, RF-014 |

- **Por qué 10 s**: es el tiempo máximo que el servidor espera a pey al crear (DP-13 del plan 001). Pasado ese tiempo, el servidor ya habría respondido 502.
- **Prudencia**: la pantalla espera 15 s antes de declarar "sin conexión", para no adelantarse al 502 del servidor.

### Ver un cobro: `GET /api/cobros/{id}` ([contrato 001](../../001-backend-mvp/contracts/ver-cobro.md))

La pantalla consulta cada 8 s con el canal abierto (RF-079), cada 3 s con el canal cortado o sin canal asignado (RF-030, QP-1) y al recuperar (RF-051). Empieza el intervalo al abrirse el canal o al terminar una consulta. Hay como máximo una consulta en curso por cobro. La consulta pide el estado sin reutilizar la caché del navegador.

| Respuesta | Qué hace la pantalla | Requisitos |
|---|---|---|
| 200 | Actualiza el cobro y el desfase y avisa los pagos nuevos. Si la hora del servidor alcanza `fin_ventana`, avisa los pagos de la última respuesta del cobro en escucha y cierra el canal. En la consulta inicial de recuperación descarta los cobros fuera de ventana. | RF-029, RF-033, RF-040, RF-051, RF-079 |
| 404 | Cobro en pantalla: vista Error. Cobro anterior: deja de escucharlo | RF-057, RF-056 |
| Fallo de red | Reintenta en 8 s si el canal sigue abierto y en 3 s si está cortado o el cobro no tiene canal. «Reconectando…» sigue el estado del canal. | RF-030, RF-032, RF-079 |

### Cancelar un cobro (C2): `POST /api/cobros/{id}/cancelar` ([contrato 001](../../001-backend-mvp/contracts/cancelar-cobro.md))

| Respuesta | Qué hace la pantalla | Requisitos |
|---|---|---|
| 200 | Vista Teclado vacía; el cobro pasa a anterior y se sigue escuchando | RF-048, RF-049 |
| 404, 409 | Se queda en la vista QR con el `detail` | RF-050 |
| Fallo de red | Se queda en la vista QR con "No hay conexión con el servidor…" | RF-050 |

### Canal de avisos: `GET /api/cobros/{id}/eventos` ([contrato 001](../../001-backend-mvp/contracts/canal-avisos.md))

La pantalla abre como máximo **3 canales a la vez**: el del cobro en pantalla y los de los dos cobros anteriores más recientes. Los demás cobros en escucha se siguen con la consulta del estado cada 3 s (QP-1, porque el navegador solo abre 6 conexiones por origen).

| Evento | Qué hace la pantalla | Requisitos |
|---|---|---|
| `open` (del navegador) | Quita «Reconectando…» y pasa a la consulta cada 8 s. Si ya hay una consulta en curso, espera su resultado. | RF-031, RF-032, RF-079 |
| `estado` | Actualiza el cobro y avisa los pagos nuevos (al reconectar puede traer pagos que llegaron durante el corte) | RF-029, RF-033 |
| `pago` | Avisa el pago si es nuevo, con el cobro que viene en el evento | RF-022, RF-023, RF-029, RF-044, RF-045 |
| `vencido` | Vista QR vencido si es el cobro en pantalla y no tiene pagos | RF-035 |
| `cancelado` | Si es el cobro en pantalla y esta pantalla no lo canceló, actúa como una cancelación propia confirmada | RF-074 |
| `fin` | `close()` y termina la escucha | RF-040 |
| `error` (del navegador) | Empieza la consulta cada 3 s y muestra "Reconectando…". Si el canal queda `CLOSED` y la consulta da 200, reintenta abrirlo cada 15 s | RF-030, RF-031, RF-034 |

## 5. Campo que agrega el C-2

| Campo | Tipo | Dónde | Uso | Requisitos |
|---|---|---|---|---|
| `hora_servidor` | entero (Unix) | En cada objeto cobro (crear, ver, cancelar y eventos del canal) | `desfase = hora_servidor − ahora_del_celular` (R-6) | RF-019, CE-009, CE-016 |

- Nombre fijado al aplicar el C-2 en la spec 001 (2026-11-15): `hora_servidor`, entero Unix truncado de la hora del servidor al armar el objeto.
- Si no viene, la pantalla usa el reloj del celular y deja una advertencia en la consola.

## 6. Ejemplo

Respuesta 201 que la pantalla espera tras el C-2 (campos de la 001 abreviados):

```json
{
  "id": "Xk3vQ9aZ1bNc",
  "monto": 25.5,
  "monto_libre": false,
  "concepto": "Tacos",
  "estado": "pendiente",
  "qr_imagen": "iVBORw0KGgo...",
  "creado_en": 1794700000,
  "expira_en": 1794700600,
  "fin_ventana": 1794701200,
  "hora_servidor": 1794700009,
  "numero_de_pagos": 0,
  "pagos": []
}
```

Con este ejemplo, la cuenta regresiva arranca en 9:51 (CE-016).

## 7. Seguridad

- La pantalla nunca llama a pey ni guarda llaves (RF-063). En las pruebas, toda petición se compara con el origen del servidor simulado (CE-010).
- El `detail` del servidor se muestra solo como texto (RF-077).
- No se mandan cabeceras propias: el `Content-Type: application/json` de crear es lo único fuera de lo simple, y CORS ya lo admite (`backend/app/main.py:137`).
