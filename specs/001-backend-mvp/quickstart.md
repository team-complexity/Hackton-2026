# Quickstart: comprobar el backend del MVP de punta a punta

- **Plan**: [plan.md](plan.md)
- **Contratos**: [contracts/](contracts/)

Esta guía demuestra que la spec 001 funciona. No sustituye a `verification-guide.md`, que tiene los pasos de cada fase.

## 0. Requisitos previos

- `uv` instalado y Python 3.11 o superior.
- `backend/.env` con `PEY_API_KEY`. `PEY_WEBHOOK_SECRET` solo hace falta para la prueba del aviso (paso 5). Nunca pegues sus valores en el chat.
- Para el paso 4: un banco con **CoDi activado** y su app en el celular. La cámara normal no sirve.

## 1. Pruebas automáticas (sin pey real)

Desde la raíz del repositorio:

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

**Esperado**: todo en verde, sin llamadas a pey y en pocos segundos (el reloj es falso).

## 2. Arrancar el servidor

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

En otra terminal:

```bash
curl -s http://localhost:8000/salud
```

**Esperado**: `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":...}`, sin valores de credenciales ([contrato](contracts/salud.md)).

## 3. Crear un cobro y abrir su canal

```bash
curl -s -X POST http://localhost:8000/api/cobros -H 'Content-Type: application/json' -d '{"monto": 0.01, "concepto": "Prueba"}'
```

**Esperado**: 201 con el [objeto cobro](contracts/crear-cobro.md#objeto-cobro) en estado `pendiente`. Esto crea un QR **real** en pey de $0.01. Crearlo no mueve dinero: solo se cobra si alguien lo paga.

Abre el canal con el `id` recibido:

```bash
curl -N http://localhost:8000/api/cobros/<id>/eventos
```

**Esperado**: `event: estado` de inmediato y una señal de vida cada 15 s ([contrato](contracts/canal-avisos.md)).

## 4. Pago real de $0.01 (con autorización de Hugo)

1. Guarda la imagen del QR (`qr_imagen`) o usa `cd backend && uv run python scripts/probar_pey.py --esperar --minutos 20`.
2. Paga desde la app del banco, en la opción CoDi.
3. **Esperado, sin aviso de pey configurado**: en menos de 5 s después de que pey registra el pago, el canal emite `event: pago` con `numero: 1` gracias a la consulta automática (RF-040, CE-008).
4. **Esperado, con aviso de pey configurado** (servidor desplegado, #65): el canal emite `pago` en menos de 2 s después de que pey entrega el aviso (CE-003).
5. A los 10 minutos el canal emite `event: vencido` y sigue abierto. `fin_ventana` es el vencimiento más `GRACIA_SEGUNDOS` (600 por defecto): a los 20 minutos emite `event: fin` y se cierra. Un pago durante esos 10 minutos de gracia también llega como `event: pago`.

## 5. Aviso de pey firmado (local, sin dinero)

Las pruebas automáticas ya firman avisos con un secreto falso. Para probarlo a mano contra el servidor local hace falta firmar con el secreto real, lo que solo debe hacer Hugo en su máquina. Lo cubre la prueba `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada` y su paso en `verification-guide.md`.

## 6. Protección de la demo

```bash
for i in $(seq 1 11); do curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:8000/api/cobros -H 'Content-Type: application/json' -d '{"monto": 150}'; done
```

**Esperado**: 422 en todos (monto mayor al máximo) sin llamar a pey. El límite de 10 por minuto se comprueba en las pruebas automáticas, para no crear 11 QR reales.

## 7. Despliegue (para #65, QP-5)

Lo que el hosting necesita para que el backend cumpla la spec:

1. **Un solo proceso**: arranca con `uvicorn app.main:app --port $PORT`, **sin** `--workers`. El servidor solo escucha en `127.0.0.1` (spec 003, RF-056). Los cobros, pagos y avisos se guardan en la base de datos; los límites por IP y los canales siguen en memoria.
2. **Variables de entorno** (en el panel del hosting, nunca en el repo):

   | Variable | Valor |
   |---|---|
   | `PEY_API_KEY` | La llave de pey (la pone Hugo) |
   | `PEY_WEBHOOK_SECRET` | El secreto que muestra pey al crear el aviso (una sola vez) |
   | `WEB_ORIGIN` | La URL pública de la web (#64), por ejemplo `https://pago-facil.ejemplo.app` |
   | `PROXIES_CONFIABLES` | La IP del proxy del hosting, o `*` solo si el hosting no permite conexiones directas al servidor |
   | `GRACIA_SEGUNDOS` | No hace falta definirla: el valor por defecto del código es 600. Poner 0 cierra el canal al vencer, como en el corte M0 |

3. **Aviso de pey**: en el portal de pey, el webhook apunta a `https://<backend>/webhooks/pey`. Se comprueba con `GET /salud` que `secreto_aviso_pey` sea `true`.
4. **El canal no se corta ni se retiene**: abre `curl -N https://<backend>/api/cobros/<id>/eventos` y comprueba que `event: estado` llega de inmediato y la señal de vida cada 15 s. Si los eventos llegan juntos al final, el proxy está reteniendo la respuesta.
5. **IP real**: desde dos redes distintas (por ejemplo, wifi y datos del celular), cada una tiene su propio límite de 10 cobros por minuto.
6. **Despertar el servidor** antes de la demo, si el plan gratuito lo duerme.

