# Guía de verificación: 003 Infraestructura de la demo

## F0 Prueba del túnel, sin la web

Fecha: 2026-11-21. Hecha por Hugo con Claude, sin código de producto ni la web (QP-12). La dirección de la demo es **`https://pago-facil.tail8d44cb.ts.net`**: Tailscale Funnel (DP-38) hacia el servidor actual en `127.0.0.1:8000`. En esta guía no se anotan IP, llaves ni datos de la cuenta de Tailscale.

### T001 · Tailscale

- La app **Standalone** de Tailscale para macOS: la de la App Store no admite Funnel. Hugo inició sesión y se instaló el CLI (*Settings → CLI integration*).
- En la consola, la máquina se renombró de `macbook-air-de-hugo` a `pago-facil`, para no publicar el nombre del dueño. El nombre DNS del tailnet (`tail8d44cb`) lo asigna Tailscale y no se puede cambiar por uno libre (TK-1).
- Quedaron activos MagicDNS, los certificados HTTPS (para `pago-facil.tail8d44cb.ts.net`) y el permiso `funnel`: la primera vez, `tailscale funnel --bg 8000` pidió aprobarlo en el navegador.

```bash
tailscale status
```

```bash
tailscale funnel status
```

### T002 · `backend/.env.demo`

Creado por Hugo con la llave de pey que ya estaba en `backend/.env` (la segunda llave, para desarrollo, llega en T048). Comprobado sin ver valores:

- `git check-ignore -v backend/.env.demo` → lo ignora `.gitignore:3:.env.*`; permisos `-rw-------`.
- Tienen valor `WEB_ORIGIN`, `LIMITE_COBROS_POR_MINUTO`, `CANALES_POR_IP` y `PEY_API_KEY`. `DATABASE_URL` está vacía a propósito (DP-44).
- `PEY_WEBHOOK_SECRET` está vacía: esa llave todavía no tiene aviso dado de alta. Se pone en T025 (TK-2).
- Para el equipo se subió la plantilla `backend/.env.demo.example`, sin valores secretos (TK-4).

### T003 · Servidor y Funnel

```bash
cd ~/Hackton-2026/backend && uv run uvicorn app.main:app --env-file .env.demo --workers 1 --port 8000
```

```bash
tailscale funnel --bg 8000
```

- `lsof` muestra el servidor solo en `127.0.0.1:8000` (RF-056). `tailscale funnel status`: `https://pago-facil.tail8d44cb.ts.net (Funnel on)` → `http://127.0.0.1:8000`.
- Desde el celular de Hugo con datos móviles: `/salud` respondió `200` con HTTPS válido, sin advertencias.
- Respuesta: `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}` (`false` por TK-2).
- **Probar desde la Mac de la demo por el relay público.** Desde la propia Mac, el nombre se resuelve a su IP del tailnet y la petición no pasa por Funnel. Para que salga a internet y entre por Funnel, como la de un celular, se fuerza una IP pública del relay (las da `dig +short @1.1.1.1 pago-facil.tail8d44cb.ts.net`):

```bash
curl --resolve pago-facil.tail8d44cb.ts.net:443:<IP pública del relay> https://pago-facil.tail8d44cb.ts.net/salud
```

- **Escáneres.** En cuanto se activó HTTPS, el nombre quedó en el registro público de certificados y llegaron bots pidiendo `/.env`, `/.git/config`, `/.ssh/id_rsa`, `/backup.sql`, WordPress, etc. Todo respondió 404. Por eso la demo se apaga fuera de los momentos acordados (RF-060).

### T004 · Canal de 25 minutos

Con la autorización de Hugo, un QR real de $0.01 **sin pagar**, creado y escuchado desde la Mac por el relay público:

- Cobro `_XAvDuVhbubs` (`codi_qr_id` `354a2b81da`), creado a las 17:27:56. `POST /api/cobros` tardó **9.8 s**, casi todo esperando a pey: es el riesgo de CE-003 del plan §11, que se mide en T029.
- `curl -N` al canal desde las 17:28:12, anotando la hora de cada línea:

| Hora | Evento |
|---|---|
| 17:28:13 | `estado` (*pendiente*), un segundo después de abrir |
| 17:28:29 → 17:47:51 | 73 señales de vida (`: sigo conectado`): 66 a 16 s, 5 a 17 s y una a 21 s |
| 17:37:56 | `vencido`, a los 10 min exactos de crear el QR |
| 17:47:56 | `fin`: el servidor cerró el canal a los 20 min y `curl` terminó con código 0 |

- **Resultado**: cada evento llegó en el momento en que salió, sin retención (RF-057), y el canal duró toda la ventana sin cortes hasta que lo cerró el servidor (RF-026).

### T005 · IP real

En el registro del servidor, las peticiones llegan con la IP pública de quien las hace, nunca `127.0.0.1`: Funnel manda `X-Forwarded-For` y el servidor confía en `127.0.0.1` (`PROXIES_CONFIABLES`, H-8). Hubo dos redes de Hugo con IP distintas: su casa (cobro y canal) y su celular con datos (`/salud`).

- El iPhone salió con una IP de **iCloud Private Relay**, no la de su compañía. Para el servidor es la IP del cliente, y los límites por IP se aplican a ella.
- **Resultado**: no hace falta DP-40; los límites de la demo se quedan en 30 (DP-36).

### T006 · Misma dirección después de reiniciar

Hugo paró el servidor con `Ctrl+C` y reinició la Mac (arrancó a las 17:52).

- Al volver, Tailscale estaba detenido hasta abrir la app (`open -a Tailscale`). La configuración de Funnel se había guardado (`--bg`) y volvió sola: `https://pago-facil.tail8d44cb.ts.net (Funnel on)` → `http://127.0.0.1:8000`. **Al encender la demo después de un reinicio, primero se abre Tailscale** (lo recoge la guía de T022).
- Servidor arrancado otra vez con el mismo comando de T003 (nuevo proceso, solo en `127.0.0.1:8000`).
- Desde el celular con datos: `/salud` → `200`. Por el relay público: `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}` con certificado válido.
- **Resultado**: la dirección es exactamente la misma después de reiniciar el servidor, el túnel y la computadora (RF-030).

### Resultado de F0

Tailscale Funnel cumple lo que el plan da por hecho (QP-12, research R-1 y R-2): HTTPS válido, canal de toda la ventana sin retener ni cortar eventos, IP real y dirección fija. No hace falta el plan B. Anotado como TK-5 en el plan.

- Hugo dijo "seguimos" con Tailscale Funnel el 2026-11-21.
- Demo apagada al terminar: servidor parado por su PID exacto y `tailscale funnel reset` (`tailscale funnel status` → `No serve config`). Para encenderla otra vez: abrir Tailscale, arrancar el servidor y `tailscale funnel --bg 8000`.
- Commit sugerido: `docs(003): prueba del túnel con Tailscale Funnel (F0)`.

## F1 CI en GitHub Actions

Rama `feature/35-ci` (worktree aparte de `feature/90`). Grok escribió `.github/workflows/ci.yml` y `backend/tests/test_ci.py` (T008 y T009); Claude los revisó antes del commit.

### T008 y T009 · Pruebas primero y flujo

- Las 3 pruebas de `test_ci.py` fallan sin `ci.yml` y pasan con él.
- En local: 112 pruebas del backend en verde, `ruff check` y `ruff format --check` limpios, también en `web/tests`.
- Versiones: `actions/checkout@v7` y `astral-sh/setup-uv@v7`, las dos con Node 24. Desde la v8, setup-uv no publica etiqueta `@vN`, así que `@v7` es la mayor más reciente que la tiene.

### T010 · PR y los dos trabajos en GitHub

PR [#102](https://github.com/team-complexity/Hackton-2026/pull/102), `Closes #35`, un solo commit `feat(003): CI con los trabajos servidor y web (F1)`.

| Trabajo | Resultado | Tiempo |
|---|---|---|
| `servidor` | 112 pruebas en verde, lint y formato limpios | 17 s |
| `web` | 265 pruebas en verde y 32 saltadas, lint y formato limpios | 3 min 18 s |

- Las 32 saltadas son las pruebas marcadas `only_browser("chromium")`, que en la pasada de WebKit se saltan a propósito. Ninguna prueba de WebKit falló en Linux, así que no hizo falta ningún `skip` nuevo ni TK.
- Cada trabajo muestra un aviso de pytest por dependencias (`PytestRemovedIn10Warning` en `web`, `StarletteDeprecationWarning` en `servidor`). No son errores.

### T011 · El flujo no ve secretos ni escribe

```bash
git grep -n "secrets\.\|pull_request_target\|permissions" .github/workflows/ci.yml
```

- Única coincidencia: `permissions:` con `contents: read` (línea 19). No usa `secrets.` ni `pull_request_target` (RF-038).
- Revisado por Claude el 2026-11-21.

### T012 · PR unido a `main`

- Hugo unió el PR #102 con *merge commit* (`be5adc3`) el 2026-11-21; #35 se cerró solo. La rama `feature/35-ci` se conserva por el worktree.
- El push a `main` disparó el CI otra vez, ya con `ci.yml` en `main`.

### T013 · Checks obligatorios y `enforce_admins`

- En *Settings → Branches → main*, Hugo marcó *Require status checks to pass* con `servidor` y `web`, los dos de GitHub Actions. *Require branches to be up to date* queda desactivado: un PR no tiene que actualizarse con `main` para unirse.
- `gh api -X POST repos/team-complexity/Hackton-2026/branches/main/protection/enforce_admins` → `"enabled": true`.
- Comprobado con la API: `required_status_checks .contexts` → `["servidor","web"]` y `enforce_admins .enabled` → `true`. El resto de la regla no cambió: 0 aprobaciones, sin force push y sin borrar `main`.
- El CI de `main` después del merge (`be5adc3`) salió en verde.
- Hugo avisó a Juan, Miguel y Leonel que traigan `main` a sus ramas. Al momento de activarlo había tres PR abiertos sin `ci.yml`: #101, #99 y #98.

### T014 · Prueba del error a propósito

Desde la rama `prueba/ci-assert-false`, creada de `main` en el worktree, el archivo `backend/tests/test_prueba_ci.py` con una prueba que siempre falla. Se usó `assert 1 + 1 == 3` y no `assert False`: ruff rechaza `assert False` (B011), y el CI habría fallado en el lint en vez de en pytest (TK-6).

PR [#103](https://github.com/team-complexity/Hackton-2026/pull/103) `[NO UNIR]`, abierto como PR normal (un borrador nunca se puede unir y no se sabría qué lo bloquea):

| Comprobación | Resultado |
|---|---|
| `servidor` | ❌ en 12 s. `ruff check` y `ruff format` en verde, falló `pytest -q`: `1 failed, 112 passed`, solo `test_el_ci_bloquea_un_pr_con_una_prueba_que_falla` |
| `web` | ✅ `265 passed, 32 skipped` en 3 min 24 s |
| Estado del PR | `BLOCKED` |
| `gh pr merge 103 --merge` (Hugo, administrador) | Rechazado: *the base branch policy prohibits the merge* |

- No se intentó `--admin`: `enforce_admins` está en `true` (T013), y si funcionara metería una prueba rota en `main`.
- Sin la prueba rota, los dos trabajos salieron en verde en el PR #102 y en `main` (`be5adc3`).
- El PR #103 se cerró **sin unir** (`mergedAt: null`) y se borró la rama en GitHub.

### Resultado de F1

`main` solo acepta PR con `servidor` y `web` en verde, también para los administradores (RF-036, RF-037, RF-038, CE-006). El flujo solo lee el repositorio y no usa secretos.

- Commit sugerido: `docs(003): CI obligatorio en main y prueba del error (F1)`.

## F2 Demo por el túnel, con la web desde el servidor

Fecha: 2026-11-21. En curso (Grok). Quedaron el código, C-7 y el borrador de `docs/operacion-demo.md`. Faltan las comprobaciones de Hugo: límites y `CARPETA_WEB` en `backend/.env.demo` (T023 y T024), el aviso de pey (T025) y la demo por el túnel (T026 y T027).

### T015 a T018 · Pruebas primero

- `backend/tests/test_web_desde_el_servidor.py`: las pruebas que piden la web y `carpeta_web` fallaron antes de implementarlo (`GET /` en 404 y `Configuracion` sin el atributo). Las dos que ya pasaban comprueban que, sin la carpeta, `/` sigue en 404 y que el API no cambia.
- `web/tests/test_seguridad.py`: `test_la_politica_solo_permite_conectarse_al_mismo_origen` falló porque `connect-src` incluía `http://localhost:8000 https:`.
- Después del código: 113 pruebas del backend en verde. Web: 266 passed y 32 skipped, en Chromium y WebKit. `ruff check` y `ruff format --check` limpios en el backend y en las pruebas de la web.

### T020 · Web servida en local

Servidor de desarrollo **sin llave de pey**, en `127.0.0.1:8001`, con `CARPETA_WEB=../web`. El proceso del servidor fue el PID 19297. Se paró con `kill 19297`.

- `http://127.0.0.1:8001/` muestra «PAGO FÁCIL», el teclado (0 a 9, punto y Borrar), el concepto y Cobrar desactivado con el monto en «$».
- Pulsar 2 deja el monto en «$2» y activa Cobrar. En Chromium, 2 y 5 dejan «$25».
- La consola no escribió errores y no hubo violaciones de la política. Un `fetch` a `/salud` en el mismo origen respondió `{"estado": "ok", "llave_pey": false, "secreto_aviso_pey": false}`: el proceso se arrancó sin llave, a propósito.

### T021 · C-7 aplicado

La fila C-7 de `specs/003-infraestructura-demo/spec.md` dice «aplicado el 2026-11-21». `git grep -n "5173" specs/002-web-mvp web/README.md` solo encuentra el puerto en la guía de verificación de la 002 (secciones con fecha) y en la fila histórica QP-2 de `specs/002-web-mvp/plan.md`.

### T022 · Borrador de la guía

`docs/operacion-demo.md` tiene las 10 secciones del corte 1. `git grep -n "0.0.0.0" docs/operacion-demo.md` no encuentra nada. Hugo la valida al seguirla en T026.

La plantilla `backend/.env.demo.example` ya tiene `CARPETA_WEB=../web` (parte de T024 que hace Grok). La misma línea se agregó a `backend/.env.demo` el 2026-11-21 (sin leer el archivo).

### T023 · Límites

`backend/.env.demo` tiene `LIMITE_COBROS_POR_MINUTO=30` y `CANALES_POR_IP=30`, como dice el TK-5 de F0 (la IP real llegó). Coincide.

### T026 · Demo con la web por el túnel (en curso, 2026-11-21)

Demo encendida con `docs/operacion-demo.md`, con una excepción: se omitió `git switch main` y `git pull` de la sección 2, porque el código de F2 solo está en `feature/90-infraestructura-demo` y AGENTS.md prohíbe cambiar de rama al agente. Se corrió `uv sync --locked`.

- **Paso 1 (celular con datos móviles):** `/salud` y la pantalla abren con HTTPS válido y sin páginas intermedias. Al abrir se lee «$» y Cobrar está desactivado.
- **Paso 2 (cobro de $0.01 sin pagar):**
  - Intento 1, **descartado**: el celular se bloqueaba solo y la web reconectaba (reaperturas del canal a los 4, 7 y 9 minutos). No fue el túnel. Hallazgo: en ese celular la web no mantuvo la pantalla encendida (RF-058).
  - Intento 2, con el bloqueo automático desactivado: QR en el minuto 0 (22:46:53), vencido a la vista en el minuto 10 (22:57:00) y un solo canal abierto, sin cortes ni reaperturas, hasta el cierre por el servidor en el minuto 20 (hacia las 23:07, observado en el celular). El registro de uvicorn no escribe las señales de vida ni el cierre; las señales se comprobaron con `curl` en F0 (T004).
  - Se crearon además dos QR de $0.01 que se cancelaron enseguida. Ninguno se pagó.
- **Paso 3 (dos redes):** el registro muestra las IP de dos celulares en redes distintas y de la Mac; ninguna petición que entró por el túnel llegó como `127.0.0.1`. Los límites se quedan en 30 (DP-40 no hace falta). No se anotan los valores de las IP.
- **Paso 4 (reinicios):** servidor reiniciado por su PID exacto y túnel con `tailscale funnel reset` y `--bg`: la misma dirección responde `"estado": "ok"` en los dos casos. Falta reiniciar la computadora.
- **Extra A (wifi de la Mac apagado un minuto con un cobro en pantalla):** el celular reabrió el canal del cobro a los ~80 s (23:13:40) y la pantalla volvió continua al QR con la cuenta regresiva del tiempo restante. En el celular no se llegó a ver «Reconectando…»: la reconexión fue tan rápida que no se notó. El resultado cumple: vuelve sola al cobro, sin recargar.
- **Extra B (demo apagada, sección 7 de la guía):** con `tailscale funnel reset` y el servidor parado, `tailscale funnel status` dice `No serve config` y el enlace, abierto en una pestaña nueva del celular con datos móviles, no carga: no aparece ninguna página propia. Una pestaña que ya estaba abierta con un cobro en pantalla sí mostró «Reconectando…», que es la página ya cargada intentando reconectar su canal, no una página servida por la demo.
- **Paso 4, reinicio de la computadora (2026-11-21):** tras reiniciar la Mac, Hugo siguió la guía (secciones 3 y 4) desde su terminal: `open -a Tailscale`, el servidor sin `--host` (escucha solo en `127.0.0.1:8000`), `tailscale funnel --bg 8000` y `caffeinate -is -w <PID>`. `/salud` por internet respondió `"estado": "ok"` y `GET /` entregó la web con HTTPS válido, en **la misma dirección** de F0 (RF-030).
- **Observación sobre la guía:** `caffeinate -is -w <PID>` se queda en primer plano mientras el servidor viva, y bloquea esa terminal. Falta aclararlo en `docs/operacion-demo.md` sección 3.
- **T026 completa**, a falta de que Hugo la apruebe.
- **Nota de operación:** a las 23:15 el servidor se detuvo solo porque terminó la sesión del agente que lo había arrancado. Para las pruebas de T026 la demo debe arrancarse desde la terminal de Hugo (guía, sección 3), no desde una sesión del agente.

### T027 · CORS y red local (2026-11-22)

- **Paso 5 (CORS):** desde la consola de Safari en `https://example.com`, `fetch("https://pago-facil.tail8d44cb.ts.net/api/cobros", {method: "POST"})` quedó bloqueado: «Origin https://example.com is not allowed by Access-Control-Allow-Origin», `bloqueado: "Load failed"`. Con `curl` y un origen ajeno, el servidor contesta `400 Disallowed CORS origin` al preflight y no manda `access-control-allow-origin`; con el origen de la demo contesta `200` y lo permite (RF-027). Cumple.
- **Observación del paso 5, sin resolver:** el navegador bloquea que la página **lea** la respuesta, pero la petición sí salió. El servidor la recibió, respondió `201` y creó un QR de monto libre en pey (sin pagar, vence solo). Un `POST` sin cabeceras especiales no lleva preflight, y un cobro sin monto es válido (RF-003). Queda acotado por el límite de 30 cobros por minuto por IP. Si el equipo quiere cerrarlo (por ejemplo, exigir `Content-Type: application/json` o validar `Origin` en los `POST`), sería un cambio `C-n` a la spec 001; no se toca aquí. La prueba del quickstart §3 paso 5 crea ese QR cada vez que se corre.
- **Paso 6 (red local):** uvicorn escucha solo en `127.0.0.1:8000`. Desde la propia Mac, `curl` a la IP de la red local sale con código 7 (conexión rechazada). Desde un celular en la misma wifi, con los datos móviles apagados, `http://<IP local de la Mac>:8000/salud` no se pudo conectar (RF-056). Cumple. No se anota la IP.
- **T027 completa**, a falta de que Hugo la apruebe.

### T025 · Aviso de pey (2026-11-22)

Hugo dio de alta el aviso de la llave de la demo en el portal de pey, con la dirección del túnel y `/webhooks/pey`, y puso el secreto en `backend/.env.demo` sin que pasara por el chat. Reinició el servidor por su terminal. `GET /salud`, tanto en local como por internet (con `curl --resolve` al relay), responde `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":true}`. Cumple. La firma válida se comprueba con el primer pago real (T030).

- **Observación sobre el túnel:** tras el reinicio del servidor, `tailscale funnel status` decía `No serve config` y la dirección pública no respondía. No se encontró qué quitó la configuración. Hugo la reabrió con `tailscale funnel --bg 8000` y volvió a responder. Si se repite, conviene comprobar `tailscale funnel status` después de cada reinicio del servidor y anotarlo en la sección 8 de `docs/operacion-demo.md`.
- **T025 completa**, a falta de que Hugo la apruebe.

### Resultado de F2 (2026-11-22)

| Qué | Resultado |
|---|---|
| Pruebas del backend | 113 pasan |
| Pruebas de la web | 266 pasan y 32 se omiten (son marcadas solo para un navegador distinto, `skipped for this browser: webkit`) |
| `ruff check` y `ruff format --check` (backend y web) | Sin avisos, todo formateado |
| T015 a T018, T020 a T022 | Hechas por Grok y revisadas (arriba) |
| T023, T024 | Límites y `CARPETA_WEB` comprobados |
| T025 | Aviso de pey dado de alta y `secreto_aviso_pey: true` |
| T026 | Pasos 1 a 4 y extras A y B comprobados con la demo por el túnel |
| T027 | CORS bloquea el origen ajeno; la red local rechaza la conexión |

- **Qué queda para Hugo:** aprobar el cierre de F2. La firma válida del aviso de pey se comprueba con el primer pago real (T030).
- **Hallazgos abiertos, sin resolver en F2:**
  - RF-058 (pantalla encendida): la web no mantuvo la pantalla encendida en el celular de Hugo con el bloqueo automático activo (T026, paso 2). Falta saber modelo y navegador.
  - Un `POST /api/cobros` de otra página sí llega al servidor y crea un QR de monto libre, aunque CORS bloquea la lectura (T027). Está acotado por el límite por IP. Cerrarlo sería un cambio `C-n`.
  - El túnel desapareció una vez tras reiniciar el servidor (T025).
- **Commit sugerido:** `feat(003): demo por el túnel con la web desde el servidor y C-7 (F2)`.

## F3 Pago real desde la dirección del túnel

### T029 · QR en menos de 3 s (2026-11-22, en curso)

- **Medición de Hugo** (celular con datos móviles, 10 cobros de $0.01 sin pagar, de «Cobrar» al QR en pantalla): los 10 tiempos quedaron **entre 3 y 5 s**. Hugo dio el rango, no los 10 valores. **No cumple CE-003** (9 de 10 en menos de 3 s).
- **Diagnóstico del servidor** (con la autorización de Hugo, 5 cobros de $0.01 desde la Mac contra el servidor local, sin pasar por el túnel, cancelados al terminar): crear el cobro tarda **2.24 a 2.35 s** en cada uno, y casi todo es la llamada a pey (`crear_qr`), que el servidor espera antes de contestar a la web.
- **Costo del túnel** (`GET /salud` por internet, vía el relay, desde la Mac): ~0.6 s por petición, contra ~0.001 s en local. Desde un celular con datos móviles es más.
- **Lectura:** pey por sí sola ya gasta unos 2.3 s de los 3 s de la meta, así que el túnel y la red del celular la rebasan. Coincide con la 001, TK-5 (2.39 a 9.09 s con `generateImage: true`). Es una lectura de estas muestras, no una medición del tramo del celular.
- **Decisión (2026-11-22):** Hugo eligió relajar la meta y aprobó **C-10**: CE-003 pasa a "5 segundos o menos en 9 de cada 10" (antes, menos de 3 s), aplicado en la spec, el plan, el quickstart y las tareas (TK-10). Con esa meta, los 10 cobros de Hugo (de 3 a 5 s) cumplen. **T029 completa.** Queda el riesgo de los picos de 8 y 9 s de pey vistos en T030: la meta tolera uno de cada diez. No se cambió D-2 (la imagen del QR sigue siendo la de pey).

### T030 · Pagos reales de $0.01 (2026-11-22, en curso)

El servidor se arrancó con registro con hora y con la vigencia de 20 minutos para los dos pagos (`PYTHONUNBUFFERED=1 EXPIRACION_SEGUNDOS=1200`), una sola vez, como desviación de lo que dice T030 (que solo el pago tardío la usa). El primer pago no depende de la vigencia. Pagos de $0.01 de Hugo, con su cuenta y por CoDi, cada uno autorizado por él en ese momento. La hora del canal se midió con una escucha desde la Mac por internet (vía el relay) con el mismo reloj del registro, que solo marca segundos.

- **Observación sobre la lentitud (T029 y T030):** el tiempo que el servidor tarda en registrar el QR (desde que empieza la petición hasta el registro, con precisión de segundos) fue de 2.2 a 2.6 s en 11 cobros hechos desde la Mac, en local y por el túnel, y de 2 a 3 s en 3 cobros hechos desde el otro celular (IP distinta de la del Android que mostraba los cobros 1 y 2). En cambio, **los dos primeros cobros hechos desde el celular durante T030 tardaron 8 y 9 s** en el servidor (el primero tras arrancar con la vigencia de 20 minutos). No se encontró una causa: una pausa de 20 s antes de crear no los reproduce, la vigencia de 20 minutos no cambia los cobros siguientes, y el túnel solo suma ~0.6 s. Queda como pico de la llamada a pey, que coincide con la 001, TK-5 (primer cobro tras arrancar de 7.77 a 9.09 s). Es un riesgo para CE-003 que la guía registra sin resolver.

- **Pago 1** (cobro `4MkQZ8yecB7x`, pantalla en el **Android**, paga el **iPhone**):
  - Pago en pey (`datePaid`) 08:36:31. Aviso (`POST /webhooks/pey`, `200`) 08:36:35. «pago» en el canal 08:36:35.101. Del aviso al canal: menos de 1 s (CE-002).
  - **Firma del aviso válida** (RF-025): `200`, sin «Aviso rechazado».
  - El pago lo registró la consulta de respaldo (`fuente=consulta`) en el mismo segundo del aviso; el aviso llegó entonces como repetido. No afecta CE-002.
  - Hugo: «Pago recibido» apareció en A y sonó de inmediato. Falta anotar el tiempo exacto en pantalla, que el rango del registro no da.
- **Pago 2** (cobro `9i4oMre8Hncv`, pantalla en el **Android**, paga el **iPhone**; Hugo confirmó que ese fue su pago de $0.01 con su cuenta. Los celulares **no se invirtieron**, como se había propuesto: el registro muestra la misma IP creando y consultando los dos cobros):
  - Cobro creado a las 08:38:34 con vigencia de 1200 s (comprobada en `expira_en`). QR vencido en la web a las 08:58:34. Hugo pagó **a los 20 min 11 s del canal**: pey dio `datePaid` 08:58:45, la consulta de respaldo lo registró a las 08:58:49, y el aviso (`POST /webhooks/pey`, `200`, sin «Aviso rechazado», firma válida) llegó en el mismo segundo. «pago» en el canal a las 08:58:49.107: del aviso al canal, menos de 1 s (CE-002).
  - **Caso extremo (CE-004):** el pago llegó después del minuto 15 del canal y **después del vencimiento** del QR, dentro de la gracia del servidor. El canal seguía abierto, el servidor registró el pago y la pantalla lo mostró. Hugo: «Pago recibido» apareció y **sonó**, aunque el QR ya estaba oculto. Se queda como caso documentado que funciona como debe. El plan pedía pagar en el minuto 16; el pago real se hizo al final de la ventana, que es el caso más difícil. A las 08:54:43 (minuto 16) se avisó a Hugo y el pago no se hizo en ese momento sino al final de la ventana.
  - La hora exacta de «Pago recibido» en pantalla no se midió: se anota lo que Hugo vio y oyó.
- **Corrección sobre los celulares:** al arrancar T030 se llamó «A» y «B» a los celulares y se propuso invertirlos en el pago 2. Hugo aclaró después que el Android es el de cobro y el iPhone el de pago. Por eso **el iPhone aún no ha mostrado «Pago recibido»**: T030 pide que suene y se muestre en los dos celulares (Android y iPhone), y solo el Android lo ha hecho. Falta un pago con la pantalla en el iPhone.
- **Pagos 3 y 4** (cobros `ysPw7dIBQaC5` y `Sr3aDh4EWCTW`; la pantalla con el QR fue otra vez el **Android**, y pagó un iPhone con $0.01 de Hugo; no se anota ningún dato de la cuenta). Primero se anotó el pago 3 como «pantalla en el iPhone», y era un error: Hugo aclaró después que el Android tenía el QR.
  - **Pago 3** (`ysPw7dIBQaC5`): creado 09:08:13. Pago en pey (`datePaid`) 09:10:51, registrado por la consulta de respaldo en el mismo segundo; el aviso (`POST /webhooks/pey`, `200`, firma válida) llegó a las 09:10:55, 4 s después, y ya no encontró nada nuevo. En el Android «Pago recibido» apareció y sonó de inmediato, sin tocar la pantalla.
  - **Pago 4** (`Sr3aDh4EWCTW`): creado 09:11:30, pagado por Hugo otra vez. El pago lo registró **el aviso** de pey a las 09:12:04 (`fuente=aviso`, `POST /webhooks/pey` `200`), no la consulta. Es la primera vez en T030 que el aviso, y no la consulta de respaldo, procesa el pago (RF-025 con firma válida y procesado). No se midió la hora de la pantalla (no había escucha del canal armada).
  - La diferencia de «las 9:12» que Hugo recordó era por este segundo pago, no un error de reloj.
  - **Otro iPhone con PAGO FÁCIL abierto no sonó.** Es lo esperado: el canal de un cobro solo lo abre el celular que lo creó, y recuperar los cobros en otro celular o navegador es del issue #24, que requiere cuentas (spec 002). En el registro solo hay un canal abierto por cada cobro, el del Android.
- **Pago 5** (cobro `_YvkqhViwF6g`, pantalla en un **iPhone**, paga el otro iPhone con $0.01 de Hugo; no se anota ningún dato de la cuenta):
  - Cobro creado 09:16:49. Pago en pey (`datePaid`) 09:17:19, registrado por la consulta de respaldo a las 09:17:20 (`fuente=consulta`). «pago» llegó al canal, medido desde la Mac por internet, a las **09:17:20.785**, unos 1.8 s después del `datePaid` y unos 2 s **antes** que el aviso (`POST /webhooks/pey`, `200`, firma válida, 09:17:23). El celular que cobró consultó el cobro a las 09:17:22.
  - Hugo: en el iPhone «Pago recibido» apareció y **sonó de inmediato**. No dijo si hizo falta tocar la pantalla antes.
- **Estado de T030:** pagos reales de $0.01 con la pantalla en el **Android** (cobros 1, 2, 3 y 4) y en el **iPhone** (cobro 5). En todos el aviso de pey llegó con firma válida y «Pago recibido» apareció y sonó de inmediato en el celular que cobró. Casos cubiertos: pago tardío a los 20 min 11 s con el QR ya vencido (pago 2), pago procesado por el aviso (pago 4) y pago registrado antes por la consulta de respaldo (pagos 1, 2, 3 y 5). Tiempos medidos: en los pagos 1, 2 y 5, con la escucha armada, el evento «pago» llegó al canal en el mismo segundo del registro del pago y antes de que llegara el aviso o con él (menos de 1 s a 3 s según el caso; CE-002 mide desde el aviso, y la pantalla se actualizó antes). En el pago 4, que sí procesó el aviso, **no había escucha armada**: no hay hora medida del canal, solo lo que Hugo vio y oyó («inmediato»). T030 queda completa, a falta de que Hugo la apruebe.

### T031 · Reenvío del aviso (2026-11-22, en curso)

- **El portal de pey no ofrece reenviar un aviso** (Hugo lo comprobó en el portal). La documentación de pey tampoco describe un reenvío ni un endpoint para eso; solo hay «Webhook Logs» en Desarrollador para ver cada entrega, su payload y la respuesta. Se registró como TK-8 del plan.
- **Repetición del aviso hecha por Claude, con la aprobación de Hugo:** un script lee el secreto de `backend/.env.demo` dentro de su proceso (sin imprimirlo ni guardarlo), arma un aviso igual al del cobro `_YvkqhViwF6g` (mismo `codiQrId` y misma transacción), lo firma con Standard Webhooks y lo manda al servidor de la demo, en local.
  - Con otro `webhook-id` y la misma transacción: `200`, `{"recibido": true, "procesado": false}`. El cobro siguió con **1 pago**.
  - El mismo aviso otra vez, con el mismo `webhook-id`: `200`, `procesado: false`. Seguía con **1 pago**.
  - El registro muestra los dos `POST /webhooks/pey` con `200`, sin «Aviso rechazado» y sin una línea nueva de pago. La firma se verificó. Se cubren las dos defensas de RF-007: por `webhook-id` y por transacción.
  - Hugo: en el iPhone que cobró **no volvió a sonar** ni mostró otro pago.
- **Prueba de Leonel (N-17):** Hugo dijo que Leonel no podrá probar ese día ni esa noche. Pasa al [issue #105](https://github.com/team-complexity/Hackton-2026/issues/105), asignado a él (TK-9), con los pasos y sin necesidad de `.env`: solo el enlace y la demo encendida por Hugo. Falta su resultado, que Hugo anotará aquí. T031 queda completa en lo demás, a falta de que Hugo la apruebe.

### T032 · README

Se agregaron a `README.md` las secciones «La demo», «Correr en local» y «Equipo y tecnologías», con el enlace `https://pago-facil.tail8d44cb.ts.net`.

### Resultado de F3 (2026-11-22)

| Qué | Resultado |
|---|---|
| Pruebas del backend | 116 pasan |
| Pruebas de la web | 266 pasan y 32 se omiten (solo marcadas para webkit) |
| `ruff check` y `ruff format --check` (backend y web) | Sin avisos, todo formateado |
| T029 QR en 5 s o menos (CE-003) | 10 cobros de 3 a 5 s; la meta pasó de 3 s a 5 s con **C-10** (TK-10) |
| T030 pagos reales de $0.01 (CE-002, CE-004) | 5 pagos con aviso de firma válida; pantalla en Android (cobros 1 a 4) y en iPhone (cobro 5); caso tardío a los 20 min 11 s |
| T031 reenvío del aviso (RF-007) | Sin reenvío en el portal de pey (TK-8): repetición del aviso por script, `200` y un solo pago |
| T031 prueba de Leonel (N-17) | Pasa al [issue #105](https://github.com/team-complexity/Hackton-2026/issues/105), asignado a él (TK-9) |
| T032 README (#66) | Secciones «La demo», «Correr en local» y «Equipo y tecnologías», revisadas por Claude |

- **Qué queda para Hugo:** aprobar el cierre de F3 y del corte 1, y cerrar #66, #27 y #64 con el PR o con un comentario que cite los tiempos de T030.
- **Lo que sigue abierto, sin resolver en F3:**
  - Picos de 8 y 9 s de pey al crear el QR (T030); la meta de CE-003 tolera uno de cada diez.
  - RF-058: la pantalla del celular de Hugo no se mantuvo encendida con el bloqueo automático activo (F2).
  - Un `POST /api/cobros` desde otra página crea un QR de monto libre aunque CORS bloquee la lectura (F2); cerrarlo sería un cambio `C-n` a la 001.
  - La prueba de Leonel desde su red (#105).
- **Commit sugerido:** `docs(003): enlace de la demo y pago real desde el túnel (F3)`.

## F4 Migraciones con un comando

### T045 a T047 · Base de desarrollo en Supabase (2026-11-24)

La base es el proyecto de Supabase de desarrollo de Juan, con la `DATABASE_URL` del *pooler* en modo sesión en `backend/.env` de Hugo. Hugo confirmó que es la de desarrollo y no la de la demo. La contraseña no se anota aquí.

- **`estado` antes de aplicar** (T045): `Entorno: sin marcar.`, `Aplicadas: ninguna.`, `Pendientes: 0001, 0002, 0003.`
- **Hallazgo:** la base ya tenía el esquema del PR #97 creado a mano, con sus cinco tablas y los mismos datos de prueba de `supabase/datos_de_prueba.sql` (1 negocio, 1 cupón, 4 cobros, 1 pago; se comprobó por ids y por el código del cupón, en solo lectura). Por eso `aplicar --entorno local --datos-de-prueba` se negó, como pide la spec: «Esta base ya tiene el esquema del PR #97 sin registro. Revísalo y corre: aplicar --ya-aplicada 0001.» Es el caso de la demo creada a mano (DP-3, R-7), probado por primera vez contra Supabase.
- **T046**, tras revisar el esquema:

  ```text
  aplicar --ya-aplicada 0001 --entorno local --datos-de-prueba
  Base marcada como local.
  Anotada 0001 esquema_inicial sin correrla.
  Aplicada 0002 imagen_del_qr.
  Aplicada 0003 estado_del_servidor.
  Datos de prueba cargados.

  aplicar
  No había nada que aplicar.
  ```

- **T047**: `estado` dice `Entorno: local.`, `Aplicadas: 0001, 0002, 0003.`, `Pendientes: ninguna.`
- **Primera prueba real de 0002 y 0003 en Supabase:** corrieron sin errores. La 0001 no se corrió ahí: ya estaba hecha a mano y solo se anotó.
- **Para Juan:** la contraseña de la base pasó por el chat del equipo mientras se resolvía la conexión; conviene cambiarla.

### T048 · Segunda llave de pey (2026-11-24)

- La comparación de `PEY_API_KEY` entre `backend/.env` y `backend/.env.demo` dice `DISTINTAS`. No se anota ningún valor.
- `GET /salud` del servidor de desarrollo: `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}`. `secreto_aviso_pey` queda en `false` porque quien prueba sin túnel no da de alta aviso y usa la consulta de respaldo.

### Resultado de F4 (2026-11-24)

| Qué | Resultado |
|---|---|
| Pruebas del backend | 134 pasan con un PostgreSQL 17 desechable; 119 pasan y 14 se saltan sin él |
| `ruff check` y `ruff format --check` | Sin avisos, todo formateado |
| CI del PR #107 | `servidor`, `web` y `base-de-datos` en verde |
| T044 protección de `main` | `servidor`, `web` y `base-de-datos` obligatorios |
| T045 a T047 base de desarrollo | 0001 anotada, 0002 y 0003 aplicadas; segunda corrida sin cambios; `Entorno: local.` |
| T048 segunda llave de pey | `DISTINTAS` y `llave_pey: true` |

- **Qué queda para Hugo:** revisar el diff, unir el PR #107 y avisar a Juan de que cambie la contraseña de la base.
- **Lo que sigue abierto, sin resolver en F4:** el servidor todavía no usa la base (F5) y la base de la demo se crea en F6.
- **Commit sugerido:** `feat(003): comando de migraciones y trabajo base-de-datos del CI (F4)`.
