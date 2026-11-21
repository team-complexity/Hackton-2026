# Contrato: canal de avisos de un cobro

## 1. Método, ruta y propósito

`GET /api/cobros/{id}/eventos`: un flujo de Server-Sent Events (`text/event-stream`) por el que la pantalla se entera, sin recargar, de los pagos y los cambios de estado de un cobro. Mientras haya un canal abierto, el servidor le pregunta a pey por su cuenta.

## 2. Requisitos

RF-028, RF-029, RF-030, RF-031, RF-032, RF-033, RF-040, RF-041, RF-043.

## 3. Petición

| Campo | Tipo | Obligatorio | Validación | Requisitos |
|---|---|---|---|---|
| `id` (en la ruta) | texto | Sí | Debe existir | RF-028 |

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | El cobro existe y la IP del cliente tiene menos de 10 canales abiertos | Flujo de eventos (abajo) |
| 404 | No existe | `{"detail": "Ese cobro no existe"}`. `EventSource` no se reconecta |
| 429 | La IP del cliente ya tiene 10 canales abiertos | `{"detail": "Tienes demasiadas pantallas abiertas. Cierra otras e intenta de nuevo."}` (RF-041). `EventSource` no se reconecta |

### Eventos

Cada evento lleva `event:` y `data:` (JSON). Primero se envía `retry: 3000`.

| Evento | Cuándo | `data` | Requisitos |
|---|---|---|---|
| `estado` | Siempre, nada más abrir el canal | [Objeto cobro](crear-cobro.md#objeto-cobro) | RF-031 |
| `pago` | Cada vez que se registra un pago (por aviso o por consulta) | `{"pago": <objeto pago>, "cobro": <objeto cobro>}` | RF-029 |
| `vencido` | El cobro pasa a *vencido*, en menos de 15 s | Objeto cobro | RF-030 |
| `cancelado` | El cobro se cancela, en menos de 15 s (corte 2) | Objeto cobro | RF-030 |
| `fin` | Termina la ventana de escucha, justo antes de cerrar | Objeto cobro | RF-032, RF-043 |
| (comentario) `: sigo conectado` | Después de 15 s sin enviar nada | — | RF-033 |

Cada objeto cobro de los eventos trae `hora_servidor` con la hora en que el servidor armó el evento (C-2). Los eventos `pago` y `cancelado` se arman al registrarse y se reenvían en el momento, así que la diferencia con la hora de envío es de milisegundos.

**Obligación para la web (#64)**: al recibir `fin`, la pantalla llama a `eventSource.close()`. Si no lo hace, el navegador se reconecta cada 3 s y recibe `estado` y `fin` en un ciclo sin fin.

### Ciclo del servidor

1. Al abrir: comprueba el límite de canales de la IP; emite `estado`.
2. Si `ahora ≥ fin_ventana`: emite `fin` y cierra (RF-043).
3. Si no, repite hasta `fin_ventana` o hasta que la pantalla se desconecte:
   - espera eventos con un tiempo límite igual al menor de: 5 s, lo que falta para `expira_en` y lo que falta para `fin_ventana`;
   - reenvía los eventos `pago` y `cancelado` publicados para ese cobro;
   - si el estado pasó a *vencido* desde la última vuelta, emite `vencido`;
   - si pasaron 5 s desde la última consulta a pey de ese cobro, consulta con `ConsultaDeRespaldo` (RF-040, QP-7), comparte el límite con la consulta al ver el cobro y avisa lo nuevo. La consulta espera como máximo 4 s (QP-1), así que una vuelta nunca dura más de unos 9 s;
   - si pasaron 15 s sin enviar nada, manda la señal de vida.
4. Al terminar la ventana: emite `fin` y cierra (RF-032). Si el cobro vence en el mismo instante en que termina la ventana (gracia 0, corte M0), emite primero `vencido` y después `fin` (QT-6).
5. Al desconectarse o terminar: libera el lugar del canal en el conteo de la IP.

## 5. Ejemplo

```text
retry: 3000

event: estado
data: {"id":"Xk3vQ9aZ1bNc","estado":"pendiente","numero_de_pagos":0,...}

: sigo conectado

event: pago
data: {"pago":{"numero":1,"monto_recibido":0.01,"monto_distinto":false,"pagado_en":1794700123},"cobro":{"id":"Xk3vQ9aZ1bNc","estado":"pagado","numero_de_pagos":1,"total_recibido":0.01,...}}

event: fin
data: {"id":"Xk3vQ9aZ1bNc","estado":"pagado",...}
```

## 6. Seguridad

- Máximo 10 canales abiertos por IP del cliente (RF-041), contados mientras están abiertos.
- Las consultas a pey que genera un canal comparten el límite por cobro: una cada 5 s, sin importar cuántas pantallas miren ese cobro.
- Cabeceras: `Cache-Control: no-cache` y `X-Accel-Buffering: no`, para que los proxies no retengan los eventos.
