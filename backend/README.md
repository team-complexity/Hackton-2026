# Backend — PAGO FÁCIL

API en **Python (FastAPI)**. Es la única parte que habla con pey y la única que conoce la llave.

La fuente del contrato con la web es [`specs/001-backend-mvp/contracts/`](../specs/001-backend-mvp/contracts/). Este archivo resume el corte 2: ventana de gracia, monto libre y cancelación. Si algo no coincide, manda el contrato.

## Arranque

Un solo comando, un solo proceso (sin `--workers`):

```bash
cd backend && uv run uvicorn app.main:app --port 8000
```

Antes, una vez: [uv](https://docs.astral.sh/uv/) instalado, `uv sync` y un `backend/.env` copiado de `.env.example`. Los secretos se rellenan ahí, en la máquina, y `.env` no se sube a Git.

`GET http://localhost:8000/salud` responde sin mostrar credenciales:

```json
{ "estado": "ok", "llave_pey": true, "secreto_aviso_pey": false }
```

`llave_pey` y `secreto_aviso_pey` son booleanos: dicen si el valor está configurado, no cuál es.

## Variables de entorno

Sin valores de secretos. Los nombres y los valores por defecto del corte 2:

| Variable | Para qué | Por defecto |
|---|---|---|
| `PEY_API_KEY` | Llave de pey. Solo en `.env` o en el hosting | vacío |
| `PEY_WEBHOOK_SECRET` | Secreto con el que se firma el aviso de pey | vacío |
| `WEB_ORIGIN` | Orígenes CORS, separados por coma | `http://localhost:5173` |
| `PROXIES_CONFIABLES` | De quién se acepta `X-Forwarded-For` | `127.0.0.1` |
| `LIMITE_COBROS_POR_MINUTO` | Cobros por IP | `10` |
| `CANALES_POR_IP` | Canales de avisos abiertos a la vez por IP | `10` |
| `MONTO_MAXIMO` | Tope del monto en la demo | `100` |
| `EXPIRACION_SEGUNDOS` | Vigencia del QR | `600` |
| `GRACIA_SEGUNDOS` | Escucha después del vencimiento (corte 2, F6). Con `0` el canal cierra al vencer, como en el corte M0 | `600` |

En el hosting, `PROXIES_CONFIABLES` es la IP del proxy, o `*` solo si el hosting no deja conexiones directas al proceso. El arranque no usa varios workers: los cobros, los límites y los canales viven en memoria.

## Probar la conexión con pey

Crea un cobro CoDi **real** de $0.01 y guarda el QR en `.tmp/qr-prueba.png`:

```bash
uv run python scripts/probar_pey.py --esperar
```

Escanea la imagen con la app del banco, en la opción CoDi. Con `--esperar`, el script consulta a pey hasta ver el pago. El dinero enviado a la CLABE de prueba de pey no se devuelve: usa solo $0.01 y solo con autorización de Hugo.

## Contrato con la web

| Método y ruta | Qué hace |
|---|---|
| `POST /api/cobros` | Cuerpo `{"monto": 0.01, "concepto": "Tacos"}`. Crea el cobro en pey y responde `201` con el objeto cobro. Sin `monto`, con `null` o con `0`, el cobro es de **monto libre**: `"monto": null`, `"monto_libre": true`, y el cliente escribe la cantidad en su banco. |
| `GET /api/cobros/{id}` | El mismo objeto. Si sigue en ventana, pregunta a pey como respaldo del aviso. |
| `POST /api/cobros/{id}/cancelar` | Sin cuerpo. Cancela un cobro pendiente y responde el objeto con `estado: "cancelado"`. El QR sigue pagable en el banco. 404 si no existe; 409 si ya está pagado, vencido o cancelado. |
| `GET /api/cobros/{id}/eventos` | Server-Sent Events. Ver eventos abajo. |
| `POST /webhooks/pey` | Solo para pey. Verifica la firma antes de leer el JSON. |
| `GET /salud` | Comprobación de vida, sin valores de credenciales. |

Un cobro se ve así (nombres en `snake_case`; los pagos van numerados):

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
  "fin_ventana": 1794701200,
  "numero_de_pagos": 0,
  "total_recibido": 0,
  "pagado_en": null,
  "pagos": [],
  "hora_servidor": 1794700009
}
```

Cada elemento de `pagos` trae `numero` (1, 2, 3…), `monto_recibido`, `monto_distinto` y `pagado_en`. `hora_servidor` es la hora del servidor al armar la respuesta o el evento, para que la web no dependa del reloj del celular (C-2). `estado` vale `pendiente`, `pagado`, `vencido` o `cancelado`.

- `qr_imagen`: PNG en base64 (`<img src="data:image/png;base64,...">`). Puede ser `null`; en ese caso la web muestra "No se pudo mostrar el QR. Intenta de nuevo." y no dibuja el QR.
- Errores: `422` monto o concepto inválido, `404` cobro inexistente, `409` no se puede cancelar, `429` demasiados cobros o demasiados canales desde la misma IP, `502`/`503` pey falló. El campo `detail` trae un mensaje para mostrar.

En la web, al recibir `fin` hay que cerrar el canal. Si no, el navegador se reconecta:

```js
const eventos = new EventSource(`${API}/api/cobros/${cobro.id}/eventos`);
eventos.addEventListener("estado", (e) => mostrar(JSON.parse(e.data)));
eventos.addEventListener("pago", (e) => mostrarPago(JSON.parse(e.data)));
eventos.addEventListener("vencido", (e) => mostrar(JSON.parse(e.data)));
eventos.addEventListener("cancelado", (e) => mostrar(JSON.parse(e.data)));
eventos.addEventListener("fin", () => eventos.close());
```

`pago` trae `{"pago": {"numero": 1, ...}, "cobro": { ... }}`. `estado`, `vencido`, `cancelado` y `fin` traen el objeto cobro. Cada 15 s sin otro evento manda el comentario `: sigo conectado`.

Con `GRACIA_SEGUNDOS` en 600, `vencido` no cierra el canal: sigue abierto hasta `fin_ventana` (10 minutos después de vencer) y un pago tardío llega como `pago`. `cancelado` tampoco lo cierra. Solo `fin` cierra. El contrato completo está en [canal-avisos](../specs/001-backend-mvp/contracts/canal-avisos.md).

## Reglas que cumple

- La llave y el secreto solo se leen de las variables de entorno. No aparecen en el código, en respuestas ni en registros.
- Un aviso sin firma válida se rechaza con `401` y no cambia ningún cobro.
- El mismo pago no se registra dos veces (por `transactionId`).
- Monto fijo mayor a 0, con máximo 2 decimales y tope de `MONTO_MAXIMO`; vacío o 0 es monto libre. En un cobro de monto libre no aplica «monto distinto».
- CORS limitado a `WEB_ORIGIN`, con métodos `GET` y `POST`.
- Como máximo 10 cobros por minuto y 10 canales abiertos por IP del cliente.

## Límites

- Los cobros viven **en memoria**: se pierden al reiniciar el servidor.
- Un solo negocio de demo, sin inicio de sesión.
- Un solo proceso. No arrancar con `--workers`.

## Calidad

Desde la raíz del repositorio:

```bash
uv run --directory backend pytest
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Las pruebas usan un pey simulado. No llaman a pey ni usan la llave real.
