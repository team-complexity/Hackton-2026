# Contrato: respuestas cuando la base de datos falla

> **Pendiente de revisar con el plan nuevo.** El 2026-11-17 la spec cambió de rumbo (D-4): ya no hay AWS, dominio, presupuesto ni publicación, y la demo sale por un túnel desde una computadora del equipo. Lo de este documento sobre el guardado, las migraciones y el CI sigue sirviendo de punto de partida; lo que menciona AWS, CloudFront, el dominio o la publicación ya no aplica.

## 1. Propósito

Las rutas de la spec 001 no cambian de forma: mismas peticiones, mismos cuerpos y mismos códigos de éxito. Este contrato agrega **solo** las respuestas nuevas para cuando la base de datos no responde o la estructura está pendiente. Todas siguen la forma de error de la 001: `{"detail": "<mensaje para el dueño>"}` (DP-9 de la 001).

"No responde" incluye: no se puede conectar, la operación tarda más de lo permitido (2 s en cada escritura de crear un cobro, DP-35; 5 s en las demás) o la base de datos devuelve un error que no es de los datos. Un **error de datos** (PostgreSQL rechaza el valor) no es "no responde": ver §3.1.

## 2. Requisitos

RF-012, RF-013, RF-014, RF-015, RF-016, RF-047 (corte 2), RF-048, RF-052, RF-021. Decisiones del plan DP-34 y DP-35.

## 3. Respuestas nuevas por ruta

| Ruta | Momento | Código | `detail` | Qué pasa además | Requisitos |
|---|---|---|---|---|---|
| `POST /api/cobros` | Estructura pendiente (corte 2) | 503 | "La demo se está actualizando. Intenta de nuevo en unos minutos." | No se guarda nada ni se llama a pey | RF-047 |
| `POST /api/cobros` | Al guardar el cobro, antes de pey | 503 | "No se pudo guardar el cobro. Intenta de nuevo en un momento." | No se llama a pey | RF-012 |
| `POST /api/cobros` | pey falló y se borra el cobro | Lo que diga la 001 para la falla de pey (502 o 503) | Igual que la 001 | Si el borrado también falla, se registra y la respuesta no cambia | RF-052, RF-016 |
| `POST /api/cobros` | Al guardar el QR que pey ya creó | 503 | "No se pudo guardar el cobro. Intenta de nuevo en un momento." | La respuesta no trae el QR; el cobro sale de la memoria | RF-013 |
| `GET /api/cobros/{id}` | Al cargar un cobro que no está en memoria | 503 | "No se pudo consultar el cobro. Intenta de nuevo." | Nunca 404: un 404 solo significa que el cobro no existe | RF-015 |
| `GET /api/cobros/{id}/eventos` | Al cargar el cobro | 503 | "No se pudo consultar el cobro. Intenta de nuevo." | La web reconecta (spec 002, historia 4) | RF-015 |
| `POST /api/cobros/{id}/cancelar` | Al cargar o al guardar la cancelación | 503 | "No se pudo cancelar el cobro. Intenta de nuevo." | El cobro no cambia ni se avisa por el canal | RF-004 |
| `POST /webhooks/pey` | Al revisar si el `webhook-id` ya se vio, al buscar el cobro, al registrar el pago o al guardar el `webhook-id` | 503 | "No se pudo registrar el aviso. Se reintentará." | Si el aviso trae un pago válido, entra en la lista de reintentos (data-model §4); no se emite nada por el canal | RF-014, RF-048 |

### 3.1 Datos que el esquema no acepta (DP-34)

| Ruta | Caso | Código | `detail` | Qué pasa además |
|---|---|---|---|---|
| `POST /webhooks/pey` | `amount` de 0 o negativo (firma válida) | 400 | "Aviso con datos no válidos" | Se valida antes de la base de datos; el `webhook-id` no se marca, como con un `amount` ilegible (C-6 g) |
| `POST /webhooks/pey` | Aviso sin `type` | 200, como cualquier aviso ignorado | — | Se guarda con `tipo` vacío |
| `POST /webhooks/pey` | Cualquier otro error de datos de PostgreSQL | 400 | "Aviso con datos no válidos" | Se registra con el nombre de la clase del error; **nunca** entra a la lista de reintentos |

- La consulta de respaldo (dentro de ver cobro y del canal) no responde nada a nadie: si no puede guardar un pago, lo registra en el log y lo intenta en la próxima consulta (RF-016). Ver cobro sigue respondiendo con lo que hay en memoria.
- Un 503 de `GET /api/cobros/{id}` ya lo trata la web como "sin conexión" y reintenta (`web/js/servidor.js`; QA de la spec, bloque 3), así que la web no cambia.

## 4. Registros

Cada falla deja una línea `WARNING` o `ERROR` en el registro `pago_facil` con:

- la operación (`guardar cobro`, `guardar QR`, `borrar cobro`, `registrar pago`, `guardar aviso`, `cancelar`, `cargar cobro`, `consulta de vida`);
- el id del cobro cuando lo hay;
- **solo el nombre de la clase** del error (por ejemplo `OperationalError`), nunca su texto, porque el texto de psycopg puede traer el servidor y el usuario de la conexión (DP-15, RF-021).

Ejemplo: `ERROR pago_facil: Base de datos sin respuesta al guardar cobro cobro=Xy12ab34Cd56 (OperationalError)`.

## 5. Seguridad

- Ningún cuerpo de respuesta incluye datos de la conexión ni textos de PostgreSQL (RF-021).
- Una prueba automática provoca cada falla con un almacén que falla a propósito y comprueba el código, el mensaje y que el registro no contiene el valor de `DATABASE_URL` (CE-010).
