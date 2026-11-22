# Guía rápida (Fase 1): comprobar la spec 003 de punta a punta

- **Fecha**: 2026-11-20 (versión con túnel; la versión con AWS está en el commit `5db47ed`)
- **Plan**: [plan.md](plan.md)
- **Para quién**: Hugo (todo), Juan (CI y migraciones) y Leonel (prueba desde fuera, N-17). Cada sección dice qué comprueba y qué se espera ver. Los detalles están en los [contratos](contracts/) y en el [modelo de datos](data-model.md); los pasos para encender la demo, en `docs/operacion-demo.md`, que se escribe en F2.

> Ningún paso imprime ni pega en un chat `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` ni `DATABASE_URL`. Para saber si están puestos se usa `GET /salud`.

---

## 0. Requisitos previos

- `uv` instalado y el repositorio al día.
- Para la demo: la computadora de Hugo con Tailscale (DP-38) instalado, con sesión iniciada y con HTTPS, MagicDNS y el permiso `funnel` activados en el tailnet, y `backend/.env.demo` con la llave de la demo, `WEB_ORIGIN` (la dirección del túnel), `CARPETA_WEB=../web` y los límites de la demo (DP-36, QP-14). `backend/.env` queda para desarrollo.
- Corte 2: un proyecto de Supabase de desarrollo (RF-049) y su URL del *pooler* en modo sesión como `DATABASE_URL` en `backend/.env`.
- Para las pruebas del almacén en una computadora (opcional): un PostgreSQL 17 vacío y su URL en `PRUEBAS_DATABASE_URL`. Sin ella, esas pruebas se saltan con el motivo escrito; en el CI siempre corren.
- Dos celulares (un Android y un iPhone) y la autorización de Hugo para los pagos de $0.01.

## 1. Pruebas automáticas (CE-005, CE-010, CE-011, CE-017)

```text
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
uv run --directory backend pytest ../web -q
```

**Se espera**: todo en verde, sin conexión a pey ni a Supabase. En el corte 2, también las pruebas de deduplicación (aviso reenviado, aviso y consulta a la vez, antes y después de un reinicio simulado) y las de conciliación.

## 2. CI (CE-006) — F1

1. Abre un pull request hacia `main` con un `assert False` en una prueba.
2. **Se espera**: el trabajo `servidor` sale en rojo y GitHub no deja unir.
3. Quita el `assert False`. **Se espera**: los trabajos en verde, y GitHub deja unir sin pedir aprobación.
4. Revisa el flujo: `permissions: contents: read` y ningún `secrets.` ([contrato](contracts/ci.md)).

## 3.0 Prueba del túnel sin la web — F0 (QP-12)

Con el servidor actual (que todavía no entrega la web) y la configuración de la demo:

1. Arranca el servidor solo en `127.0.0.1:8000` con `--env-file .env.demo`, y Funnel hacia el puerto 8000. Anota la dirección `https://<nombre>.<tailnet>.ts.net`.
2. Desde **otra red** (un celular con datos como punto de acceso, o Leonel), pide `curl https://<dirección>/salud`. **Se espera**: `"estado": "ok"` con HTTPS válido.
3. Crea un cobro de $0.01 con `curl -X POST https://<dirección>/api/cobros` y el cuerpo de la [spec 001](../001-backend-mvp/contracts/crear-cobro.md). Esto crea un QR real en pey; **no se paga**.
4. Desde la otra red, `curl -N https://<dirección>/api/cobros/<id>/eventos` durante 25 minutos, anotando la hora de cada evento. **Se espera**: una señal de vida cada ~15 s en el momento en que sale (no todas juntas al final), *vencido* al minuto 10 y el cierre del servidor al minuto 20 (RF-026, RF-057).
5. Pide `/salud` desde dos redes distintas y mira el registro del servidor. **Se espera**: dos IP distintas y ninguna `127.0.0.1` (R-2). Si no, DP-40.
6. Reinicia la computadora, vuelve a encender el servidor y Funnel. **Se espera**: la misma dirección (RF-030).
7. Anota el resultado como TK en el plan. Si falla el paso 4 o el 6, se para y Hugo decide el plan B (research R-1).

## 3. Demo por el túnel con la web — F2

1. **Encender** con la guía: servidor solo en `127.0.0.1` y túnel hacia el puerto 8000. Pide `/salud` por la dirección del túnel desde un celular con datos móviles. **Se espera**: HTTPS sin advertencias ni páginas intermedias, y `"estado": "ok"` (RF-024).
2. **Canal de 25 minutos con la web (RF-026, RF-057; ya probado sin la web en §3.0)**: crea un cobro desde el celular por la dirección del túnel, deja la pantalla abierta 25 minutos y mira el registro del servidor y la pantalla. **Se espera**: las señales de vida y los cambios de estado (*vencido* al minuto 10) llegan en el momento, y el canal solo se cierra cuando el servidor lo cierra al terminar la ventana (minuto 20). Si se corta antes o los eventos llegan juntos al final, se para y Hugo decide el plan B (research R-1).
3. **IP real con la web (RF-028)**: abre la demo desde dos celulares en redes distintas (wifi y datos). **Se espera**: el registro cuenta dos IP distintas, ninguna `127.0.0.1`. Si no, se aplica DP-40 y se anota el TK.
4. **Misma dirección (RF-030)**: reinicia el servidor, después el túnel y después la computadora, y vuelve a encender con la guía. **Se espera**: la misma dirección cada vez.
5. **CORS (RF-027)**: desde una página de otro dominio, intenta un `fetch` a `/api/cobros`. **Se espera**: el navegador lo bloquea.
6. **Red local (RF-056, CE-015)**: desde otro equipo en la misma red que la computadora de la demo, pide `http://<IP de la computadora>:8000/salud`. **Se espera**: sin respuesta (conexión rechazada).

## 4. Pago real desde la dirección del túnel (CE-002, CE-003, CE-004) — F3

1. **Aviso de pey (RF-025)**: en el portal de pey, el aviso de la llave de la demo apunta a `https://<dirección del túnel>/webhooks/pey`. **Se espera**: después del primer pago, el registro muestra el aviso con firma válida.
2. **QR en menos de 3 s (CE-003)**: crea 10 cobros desde el celular con datos móviles y mide de "Cobrar" al QR. **Se espera**: 9 de 10 en menos de 3 s. Anota los tiempos en la guía de verificación.
3. **Pago de $0.01** con autorización de Hugo, en un Android y en un iPhone, pagando desde otro celular con la app del banco. **Se espera**: suena y muestra "Pago recibido" en menos de 2 s después de que pey entrega el aviso (hora del aviso en el registro frente a la hora en pantalla). En uno de los dos, paga después del minuto 15 del canal (CE-004).
4. **Reenvío**: en el portal de pey, reenvía el aviso. **Se espera**: la pantalla no vuelve a sonar y el cobro sigue con un pago.
5. **Leonel (N-17)**: abre el enlace desde su red y sus celulares y repite 3.1 y 4.2. Avisa a Hugo si algo falla.

## 5. Encender la demo con la guía (CE-016) — F6

Con la computadora recién prendida, Hugo sigue solo `docs/operacion-demo.md` y pide `/salud` por la dirección del túnel desde un celular con datos móviles. **Se espera**: `"llave_pey": true`, `"secreto_aviso_pey": true` y `"base_de_datos": "responde"`.

## 6. Migraciones, guardado y conciliación — F4 a F6

1. **Migraciones en desarrollo (CE-007, RF-054)**:

   ```text
   uv run --directory backend python -m app.migraciones aplicar --entorno local --datos-de-prueba
   uv run --directory backend python -m app.migraciones aplicar
   ```

   **Se espera**: la primera aplica 0001, 0002 y 0003 y carga los datos de prueba; la segunda dice "No había nada que aplicar."
2. **Base de la demo (historia 6, escenario 3; RF-051)**: Hugo exporta una copia, borra los datos de prueba del PR #97 y corre `aplicar --entorno demo --ya-aplicada 0001`. **Se espera**: aplica solo 0002 y 0003, sin borrar nada. El comando lleva `uv run --env-file backend/.env.demo` (QP-14).
3. **Reinicio con un pago (CE-001)**: crea un cobro en la demo, detén el servidor, vuelve a arrancarlo, recarga la pantalla y paga $0.01. **Se espera**: vuelve el mismo QR con su tiempo restante, y suena "Pago recibido".
4. **Pago con la demo apagada (RF-061)**: crea un cobro de $0.01, apaga el servidor, paga, espera a que termine la ventana (20 minutos) y vuelve a encender. **Se espera**: en el primer minuto, el registro muestra la conciliación de ese cobro y `GET /api/cobros/{id}` lo devuelve *pagado*, con un solo pago.
5. **Base de datos caída (RF-012, RF-015)**: con `DATABASE_URL` apuntando a una dirección que no responde, crea un cobro. **Se espera**: un mensaje para el dueño, y el registro dice que no se llamó a pey.
