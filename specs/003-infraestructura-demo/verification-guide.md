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

## F5 — Guardar los cobros en la base de datos

### T050 a T060 · Código y pruebas

- **T050 a T054.** Pruebas primero: ayudas del almacén, contrato del almacén, guardado y reinicio por la API, fallas de la base y la salud con `base_de_datos`.
- **T055 y T056.** Interfaz, almacén en memoria y almacén de PostgreSQL. El *pool* no se abre al crear la app.
- **T057 y T058.** El repositorio escribe primero en el almacén y la consulta de respaldo pasa a `await`.
- **T059 y T060.** Lista de reintentos, respuestas cuando la base falla, salud con la base y ciclo de vida.

### Cómo se comprueba

Desde la raíz:

```bash
uv run --directory backend pytest -q
```

178 pasan y 29 se saltan: son las de PostgreSQL, porque no hay `PRUEBAS_DATABASE_URL`.

Con el PostgreSQL local de pruebas (puerto 5434) la misma orden, con esa variable en el entorno del comando: 207 pasan. La URL no se anota aquí.

```bash
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Sin avisos, todo formateado. Esta revisión no tocó `backend/app` ni `backend/tests`.

### T061 · Diff de las pruebas que ya existían (2026-11-24)

Rango pedido: `git diff cfaedc3~1 HEAD -- backend/tests` (de T055 y T056 a T059 y T060). También se miró el diff desde antes de F5 (`ead45ed`). En los archivos que ya existían, lo único fuera de ese rango es el alta de dos pruebas en `test_salud_y_registros.py` (T054).

| Archivo | Qué cambió |
|---|---|
| `test_crear_cobro.py`, `test_aviso_pey.py`, `test_cancelar_cobro.py`, `test_web_desde_el_servidor.py`, `test_ci.py`, `test_migraciones.py`, `test_migraciones_postgres.py`, `postgres_desechable.py` | Sin diff. No hay `test_ver_cobro.py`: ver un cobro vive en esos archivos y no se tocó |
| `test_modelo.py`, `test_canal.py` | `await`, `async`, almacén en memoria y `guardar_nuevo` antes de vincular o registrar. Ninguna aserción cambia |
| `test_respaldo.py` | Lo mismo, más dos pruebas nuevas (TK-17). Las aserciones de las pruebas viejas no cambian |
| `conftest.py` | Fixture del almacén, `tareas_en_segundo_plano=False`, y el id distinto de `PeySimulado` ya anotado en TK-17. Ninguna aserción |
| `test_proteccion.py` | Solo el flag `tareas_en_segundo_plano=False` (TK-19) |
| `test_salud_y_registros.py` | La aserción conocida de TK-19: el cuerpo de la salud incluye `base_de_datos: "sin configurar"`. T054 agregó dos pruebas; no cambió las demás aserciones |
| `test_fallas_base_de_datos.py` | Archivo de F5. El cambio de aserción es el de TK-18: la línea de «guardar aviso» ya no exige el id del cobro |

Nombres `test_` de antes de F5: 110. Ninguno falta en HEAD. Entre `cfaedc3~1` (158) y HEAD (169) tampoco se quitó ninguno. El único `pytest.skip` sigue en `postgres_desechable.py`, igual que antes de F5. No hay `xfail` nuevo. Sin `PRUEBAS_DATABASE_URL` se saltan las pruebas de PostgreSQL, no las de la 001 ni la 002.

No hay hallazgo nuevo. Los cambios de aserción son los de TK-17, TK-18 y TK-19.

### T062 · `DATABASE_URL`

Fila en la tabla de `backend/README.md` y comentario en `backend/.env.example`, con «nunca en el repositorio». La línea queda `DATABASE_URL=` sin valor.

### T063 · Datos de quien paga (2026-11-24)

`git grep -n "metadata" backend/app`:

- `main.py:140`: el docstring de `_pago_para_reintento` dice que no lleva metadata.
- `main.py:305`: al crear el QR se envía `{"cobroId": ...}`.
- `pey.py:105` y `pey.py:119`: ese mismo cuerpo de salida. `_pago_de` lee `id`, `status`, `amount`, `amountBreakdown.base` y `datePaid`. El aviso lee `type`, `amount`, `codiQrId`, `transactionId` y `datePaid`. No se lee la metadata que trae pey.

`AvisoPendiente` guarda `codi_qr_id`, `transaccion_id`, `monto_recibido`, `pagado_en` e `intentos`. Nada de metadata.

Un `git grep` de CLABE, teléfono, banco o nombre de quien paga en `backend/app` no encuentra nada.

`git grep -nE "str(error)|%s.*error)" backend/app` no encuentra `str(error)`. La única línea es `tareas.py:98`: `registro.error("%s", type(error).__name__)`, el nombre de la clase. `registrar_falla` y `_clasificar` usan `error.clase` o `type(error).__name__`.

### T064 · C-6 aplicado

La spec 001 quedó con el cambio y la fila C-6 de esta spec dice «aplicado el 2026-11-24». El detalle, archivo por archivo, está en TK-21 del plan. El ejemplo JSON de `GET /salud` en `backend/README.md` no estaba en C-6; Claude le agregó `base_de_datos` en la revisión.

### T065 · Credenciales (2026-11-24)

`git grep -nE "postgres(ql)?://[^ ]+:[^ ]+@" -- ':!backend/tests'` no sale vacío. Lo que encuentra son valores falsos. No hay usuario ni contraseña del *pooler*:

- `.github/workflows/ci.yml`, líneas 81, 82, 84 y 90: usuario `postgres`, contraseña `prueba`, host local. Es la base desechable del CI.
- `specs/003-infraestructura-demo/tasks.md`, líneas 410 y 417: `usuario-falso` y `clave-falsa`.

En `backend/tests` hay cinco líneas (`test_almacen.py:23`, `test_ciclo_de_vida.py:23`, `test_fallas_base_de_datos.py:29`, `test_migraciones.py:15`, `test_salud_y_registros.py:25`), todas con `usuario-falso` y `clave-falsa`. El mismo patrón en `docs/` no encuentra nada. `git grep -nE "pooler\.supabase\.com"` no encuentra nada.

`git status --short` no muestra `backend/.env` ni `backend/.env.demo`. Están ignorados. No se leyeron.

### T066 · Reinicio en desarrollo (2026-11-25)

Hugo, con `backend/.env` (base de desarrollo y segunda llave), en el puerto 8001:

1. `GET /salud` dice `"base_de_datos": "responde"`.
2. Crear un cobro de $0.01. QR real, sin pagar, con su autorización en ese momento.
3. Parar el servidor por su PID.
4. Arrancarlo otra vez.
5. `GET /api/cobros/<id>` vuelve con su QR, su imagen y su tiempo restante.

Resultado: **pasó**.

- `GET /salud` dijo `"base_de_datos": "responde"`.
- Cobro de $0.01 creado sin pagar (`0mlfQTGx-EhQ`, QR real de pey): 201.
- Servidor parado por su PID (76471) y arrancado otra vez (PID nuevo, 77632).
- `GET /api/cobros/0mlfQTGx-EhQ` volvió con el mismo `id`, `codi_qr_id`, `qr`, `qr_imagen`, `creado_en` y `expira_en`, en `pendiente`, con 290 s de vida. El servidor nuevo consultó a pey una vez (`pagos_nuevos=0`).
- Antes de la prueba la base dijo `no responde`: la contraseña de la base de desarrollo había cambiado y `DATABASE_URL` guardaba la vieja. El error era `password authentication failed`. Se restableció la contraseña en Supabase, se actualizó `backend/.env` y se reinició el servidor. Si `/salud` dice `no responde`, `uv run --directory backend python -m app.migraciones estado` da el motivo sin mostrar la URL.

### Resultado de F5 (2026-11-24)

| Qué | Resultado |
|---|---|
| Pruebas del backend | 178 pasan y 29 se saltan sin PostgreSQL; 207 pasan con el PostgreSQL local |
| `ruff check` y `ruff format --check` | Sin avisos, todo formateado |
| T061 diff de pruebas previas | Sin hallazgo nuevo (TK-17, TK-18 y TK-19) |
| T062 `DATABASE_URL` | README y `.env.example`, sin valor |
| T063 datos de quien paga | No se leen ni se registran |
| T064 C-6 | Aplicado el 2026-11-24 |
| T065 credenciales | Solo valores falsos; el host del *pooler* no aparece |
| T066 reinicio en desarrollo | Pasó: el cobro volvió con QR, imagen y tiempo restante |
| T067 cierre de F5 | Cerrada el 2026-11-25: PR #142 con el CI en verde (`base-de-datos`, `servidor` y `web`) y aprobación de Hugo |

- **Qué queda para Hugo:** unir el PR #142 con `main`.
- **Lo que sigue abierto:** F6 (conciliación y demo con base de datos).
- **Commit sugerido:** `docs(003): revisión de pruebas, DATABASE_URL, revisión de credenciales y cambio C-6 aplicado (F5, T061 a T065)`.

## F6 — Conciliación de pagos y demo con base de datos

### T068 a T070 · Código, pruebas y guía (2026-11-25)

Grok escribió las pruebas, el latido y la guía; Claude las revisó (TK-23). Sin PostgreSQL pasan 190 y se saltan 32; con PostgreSQL local, las 222. `ruff check` y `ruff format --check` salen limpios. No se quitó ninguna aserción anterior.

Lo que se comprueba en `backend/tests/test_conciliacion.py` (12 pruebas):

- El primer latido solo crea la marca con la hora del reloj y no consulta a pey.
- Un pago de una ventana que terminó con el servidor apagado se registra una vez, con `fuente = consulta` y sin publicar en el canal.
- Un 4xx se anota y se salta; una falla pasajera se reintenta; a la décima hay un `ERROR` y se salta.
- Si el almacén falla a medias, la marca queda en el cobro anterior (TK-23).
- Cada consulta registra el `requestId` de pey y ningún dato de quien paga.

### T071 · `DATABASE_URL` de la demo (2026-11-25)

La comparación de `DATABASE_URL` entre `backend/.env` y `backend/.env.demo` dice `DISTINTAS`. No se anota ningún valor.

### T072 · Base de la demo (2026-11-25)

La base es un proyecto nuevo y vacío (TK-25). `aplicar --entorno demo` marcó la base como `demo` y aplicó 0001, 0002 y 0003. `estado` dice `Entorno: demo`, `Aplicadas: 0001, 0002, 0003` y `Pendientes: ninguna`.

Al probar el comando salió un fallo de la guía: `--env-file` va como `.env.demo`, porque `uv` aplica `--directory backend` antes (TK-24).

### T073, paso 3 · El cobro sobrevive a un reinicio (2026-11-25)

Pago real de $0.01, con la autorización de Hugo, en la demo por el túnel y con la base de datos de la demo.

- Primera corrida: el cobro `fglECvUuPaJx` volvió a cargarse con el servidor nuevo (leído de la base), pero Hugo pagó un cobro creado después. No cuenta para CE-001. Ese pago entró por aviso, una sola vez, y quedó guardado.
- Segunda corrida: se creó `Q5yPSGb8vJKd`, se paró y arrancó el servidor, la pantalla recargó y mostró el mismo QR con menos tiempo, y Hugo pagó ese QR. Pasó a *pagado*.
- La base tiene un pago de $0.01 en ese cobro. El registro dice `Pago … numero=1 fuente=consulta` y, después, un `POST /webhooks/pey` con ese mismo pago que respondió 200 sin crear otra fila (RF-007).

CE-001: cumplido. No se anota ningún dato de quien paga.

### T073, paso 4 · Conciliación de un pago con el servidor apagado (2026-11-25)

Pago real de $0.01, con la autorización de Hugo.

- Se creó `_mQZ0YVbvhXN` (00:41:43 UTC, `fin_ventana` 01:01:43), se paró el servidor, se pagó y se esperó a que la ventana terminara. La base seguía con 0 pagos y `conciliado_hasta` en 00:41:43.
- Se encendió el servidor a las 01:06:45 UTC. En el primer latido el registro mostró `Conciliación cobro=… pagos_nuevos=…` para los cobros cuya ventana terminó apagado: tres con `pagos_nuevos=0` y `_mQZ0YVbvhXN` con `pagos_nuevos=1`.
- La base tiene un pago de $0.01 en ese cobro, número 1 y `fuente = consulta`, registrado 3 segundos después del arranque. `GET /api/cobros/_mQZ0YVbvhXN` dice `pagado`, `numero_de_pagos: 1` y `total_recibido: 0.01`. `conciliado_hasta` avanzó a 01:06:45.
- El pago no entró por el aviso de pey, así que la prueba sí ejercitó la conciliación (RF-061). Ningún dato de quien paga se anota.

RF-061: cumplido.

### T073, paso 5 · Base de datos caída (2026-11-25)

Servidor de desarrollo en el puerto 8001 con `DATABASE_URL=postgresql://nadie@127.0.0.1:1/x` en la línea de comando (valor falso, no un secreto). Sin dinero.

- `POST /api/cobros` respondió **503** con `"No se pudo guardar el cobro. Intenta de nuevo en un momento."`, sin QR.
- El registro tiene `ERROR … Base de datos sin respuesta al guardar cobro cobro=<id> (TimeoutError)` y otra del latido. No hay línea de QR creado ni de pey: no se llamó a pey (RF-012). La URL falsa no aparece en el registro.

RF-012 y RF-015: cumplidos para el cobro. (El 503 de `GET` ya lo cubren las pruebas automáticas de F5.)

### T073, medición de CE-003 con la base de datos (2026-11-25)

Celular con datos móviles, por el túnel, 10 cobros de $0.01 sin pagar, de «Cobrar» al QR en pantalla. Hugo dio el rango, no los 10 valores: **nueve entre 3 y 5 s** y el primero tardó hasta unos 10 s.

- Criterio (CE-003 con C-10): 9 de 10 en 5 s o menos. Se cumple, justo (9 de 10).
- En F3, sin base de datos, los 10 estuvieron entre 3 y 5 s. El primer cobro lento es de un servidor recién reiniciado. Si se repite en una demo real, la acción sería la región del proyecto de Supabase (plan §11).

### T074 · Encender la demo con la guía (2026-11-25)

La demo se encendió con `docs/operacion-demo.md` desde la rama de F6, con acompañamiento. La dirección del túnel responde `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":true,"base_de_datos":"responde"}`, comprobado desde el celular con datos móviles y por la IP del relay.

Lo que faltó o confundió se corrigió en la guía (TK-26): el `<PID>` como marcador, el `cd backend` que dejaba la terminal en `backend` y el `caffeinate` tras un reinicio.

### Resultado de F6 (2026-11-25)

| Tarea | Resultado |
|---|---|
| T068 a T070 | 12 pruebas de la conciliación y la guía de operación con la base; revisadas por Claude (TK-23) |
| T071 | `DATABASE_URL` de la demo distinta de la de desarrollo |
| T072 | Base nueva marcada `demo`, 0001 a 0003 aplicadas (TK-25) |
| T073 | Cobro que sobrevive al reinicio y se paga una sola vez (CE-001); pago recuperado por la conciliación con el servidor apagado (RF-061); base caída con 503 y sin llamar a pey (RF-012, RF-015); medición de CE-003 con 9 de 10 en 5 s o menos |
| T074 | Demo encendida con la guía; `/salud` desde el celular con `llave_pey`, `secreto_aviso_pey` y `base_de_datos: "responde"` (TK-26) |
| T075 cierre de F6 | Cerrada el 2026-11-25: 190 pruebas pasan y 32 se saltan sin PostgreSQL; 222 con PostgreSQL local; `ruff` limpio |

- **Qué queda para Hugo:** unir el PR #143 con `main` cuando el CI esté en verde.
- **Lo que sigue abierto:** FN (T076 a T079, el PR final con `Closes #90, #19, #94`).
- **Commit sugerido:** `docs(003): cierre de F6, resultados de T073 a T075 (F6, TK-26)`.

## FN — Cierre

Fecha: 2026-11-25. Grok. No se cambió código de `backend/` ni de `web/`. No se encendió la demo ni el túnel, y ninguna prueba llamó a pey. No se leyeron `backend/.env` ni `backend/.env.demo`.

### T076 · C-6 y C-7 siguen aplicados

Las dos filas de `specs/003-infraestructura-demo/spec.md` §8.2 dicen aplicado:

- C-6, línea 429: «aplicado el 2026-11-24» (F5).
- C-7, línea 430: «aplicado el 2026-11-21» (F2).

Búsqueda de T021, ejecutada tal cual (`git grep -n "5173" specs/002-web-mvp web/README.md`). Salida:

| Archivo | Líneas |
|---|---|
| `specs/002-web-mvp/plan.md` | 323 (fila histórica QP-2) |
| `specs/002-web-mvp/verification-guide.md` | 81, 84, 85 (F2, con la nota de flujo anterior); 157, 162, 165, 167, 195, 197 (F3, 2026-11-15, con la nota de flujo anterior); 483, 486 (FN de la 002, 2026-11-15); 520 (revisión del 2026-11-16); 537 (pruebas reales, 2026-11-16); 584 (C-4 y C-5, fecha 2026-11-16) |

`web/README.md` no aparece. Cada coincidencia está en una sección con fecha de esa guía o en la fila histórica QP-2. Cumple el «hecho cuando» de T021.

Búsqueda de T064, ejecutada tal cual (`git grep -n "se perdió al reiniciar\|0.0.0.0" specs/001-backend-mvp backend/README.md`). No escribió ninguna línea (código de salida 1). Nada vigente. Cumple.

### T077 · Revisión de seguridad

Cada punto se marcó leyendo el archivo citado o ejecutando el comando. Ninguno dejó un hallazgo nuevo que haya que corregir.

**Secretos (CE-010, RF-038).** Ejecuté `git grep -nE "(PEY_API_KEY|PEY_WEBHOOK_SECRET|DATABASE_URL)=.+"`. Solo hay textos de la spec, de las tareas y de esta guía: `DATABASE_URL=` vacía a propósito (plan.md:320, tasks.md:97 y :756, verification-guide.md:407) o una URL falsa de las pruebas (tasks.md:417 y :772, verification-guide.md:521). No hay un valor real. `git grep -n "secrets\." -- .github/workflows/ci.yml` no encontró nada (código de salida 1). El flujo declara `permissions: contents: read` (`.github/workflows/ci.yml:19-20`). La contraseña `prueba` de las líneas 65 y 84 es la del PostgreSQL desechable del CI, no un `secrets.` de GitHub. Cumple.

**Túnel (RF-059, RF-056).** `git ls-files` no tiene archivos de Tailscale, de llave ni de sesión. `git grep` de `tskey-`, `TS_AUTHKEY`, `tailscale login`, `authkey` y `TAILSCALE_AUTH` no encontró nada. La dirección pública `*.ts.net` está en la documentación (TK-1); no es una llave ni una sesión. Cumple.

`git grep -n "0.0.0.0" -- docs backend specs/003-infraestructura-demo`, tal como lo escribe T077, también acierta en líneas que no son esa dirección, porque en `git grep` el punto es cualquier carácter (`backend/app/cobros.py:173`, `backend/tests/test_almacen.py:39` y `:326`, `backend/tests/test_guardar_cobros.py:23` y `:25`, `backend/uv.lock:1097`). Con la cadena fija (`git grep -nF "0.0.0.0"` sobre las mismas carpetas) solo quedan textos que dicen no usarla: plan.md:247, research.md:49, spec.md:429 (C-6 h), tasks.md:278, :288, :680, :685 y :802, y verification-guide.md:182. `docs/operacion-demo.md` no aparece. Cumple RF-056.

**Base de datos (RF-022).** Leí `supabase/migraciones/` y el SQL del comando.

| Tabla | RLS | `revoke all … from anon, authenticated` |
|---|---|---|
| `negocios`, `cupones`, `cobros`, `pagos`, `avisos_webhook` | `0001_esquema_inicial.sql:145-149` | `:151-152` (también la vista `cobros_con_estado`, que además es `security_invoker`, `:117`) |
| `estado_del_servidor` | `0003_estado_del_servidor.sql:6` | `:8` |
| `cambios_de_estructura`, `entorno_de_la_base` | `backend/app/migraciones.py:36-37` | `:38-39` |

`0002_imagen_del_qr.sql` solo agrega `cobros.qr_imagen` a una tabla que ya tiene RLS. Cumple.

**Aviso (DP-34).** Leí `backend/app/main.py`. `Webhook(secreto).verify` está en las líneas 404-408. La primera llamada al almacén es `cobros.aviso_ya_visto` en la línea 433, después de la firma. Un `amount` ilegible, de 0 o negativo en el evento de pago responde 400 en las líneas 425-427, también antes de tocar la base. Cumple.

**Demo pública.** Los límites usan `request.client.host` después de `ProxyHeadersMiddleware` (`main.py:228-229`, `:231-232`, `:285-286`). La plantilla `backend/.env.demo.example:16-17` deja 30 y 30 (DP-36). F0 (T005) ya vio la IP real, así que no se aplicó DP-40. CORS sale de `WEB_ORIGIN` (`config.py:31` y `:48-50`, `main.py:222-226`); en la plantilla es la dirección del túnel (`backend/.env.demo.example:13`) y T027 lo comprobó. La CSP de `web/index.html:8` tiene `connect-src 'self'` y nada más. Cumple. Sigue abierto, ya anotado en F2 (T027) y sin cambio aquí: un `POST` simple desde otro origen puede crear un cobro aunque el navegador no lea la respuesta. Cerrarlo sería un `C-n` a la spec 001.

**Datos de quien paga (RF-009).** Los `insert` de `backend/app/almacen_postgres.py:29-33` y `:50-54` no tienen columnas de quien paga. `_pago_de` (`backend/app/pey.py:183-194`) no lee `metadata`. La conciliación registra cobro, páginas, pagos nuevos y `requestId` (`backend/app/tareas.py:233-248`) y el aviso pendiente solo guarda id del QR, transacción, monto y hora (`tareas.py:24-31`). Las pruebas `test_los_datos_de_quien_paga_no_se_guardan_ni_se_registran` (`backend/tests/test_guardar_cobros.py:366`) y la de la conciliación (`backend/tests/test_conciliacion.py:461-462`) lo comprueban. Cumple.

### T078 · Quickstart de punta a punta

Cada sección queda enlazada a lo que ya está en esta guía. Lo que no coincidía con lo hecho se corrigió en `quickstart.md` y quedó como TK-27.

| Sección | Resultado | Dónde |
|---|---|---|
| §1 Pruebas automáticas | En verde, sin pey ni Supabase. Con PostgreSQL local también (abajo, T079). Deduplicación en F5 y conciliación en F6 | F5 (T050 a T060), F6 (T068 a T070), T079 |
| §2 CI | `servidor` en rojo con una prueba que falla y el PR no se puede unir; sin `secrets.` | F1 (T010 a T014, TK-6). El quickstart ya no dice `assert False` |
| §3.0 Túnel sin la web | HTTPS, canal de toda la ventana, IP real, misma dirección. Sin plan B | F0 (T001 a T006, TK-5) |
| §3 Demo con la web | Pantalla por el túnel, canal de 20 min, dos redes, misma dirección, CORS y red local | F2 (T026 y T027) |
| §4 Pago real | QR en 5 s o menos (C-10), pagos de $0.01 en Android y en iPhone, firma válida | F3 (T029 a T031) |
| §4 paso 4, reenvío | El portal no reenvía. Se repitió el aviso firmado: un solo pago y no volvió a sonar | F3 (T031, TK-8). Corregido en el quickstart |
| §4 paso 5, Leonel | No se hizo. Sigue en el issue #105 | F3 (T031, TK-9). El quickstart lo deja pendiente |
| §5 Encender con la guía | `/salud` por el túnel, desde el celular, con llave, secreto y base que responde | F6 (T074, TK-26) |
| §6.1 Migraciones en desarrollo | Base vacía: el CI aplica dos veces. Base de desarrollo: el esquema ya estaba a mano y se anotó 0001 | F4 (T045 a T047) y el trabajo `base-de-datos` (F4) |
| §6.2 Base de la demo | Proyecto nuevo y vacío: `aplicar --entorno demo` aplicó 0001, 0002 y 0003. El comando es `uv run --directory backend --env-file .env.demo` | F6 (T071 y T072, TK-24 y TK-25). Corregido en el quickstart |
| §6.3 Reinicio con un pago | El mismo QR volvió y se pagó una sola vez | F6 (T073, paso 3) |
| §6.4 Pago con la demo apagada | La conciliación lo registró al encender, un solo pago | F6 (T073, paso 4) |
| §6.5 Base caída | 503 para el dueño y el registro dice que no se llamó a pey | F6 (T073, paso 5) |

### T079 · Cierre

Ejecuté, desde la raíz:

| Comando | Resultado |
|---|---|
| `uv run --directory backend pytest -q` | 190 passed, 32 skipped, 1 warning (`StarletteDeprecationWarning`) |
| `uv run --directory backend ruff check .` | All checks passed |
| `uv run --directory backend ruff format --check .` | 37 files already formatted |
| `uv run --directory backend ruff check --config pyproject.toml ../web` | All checks passed |
| `uv run --directory backend ruff format --config pyproject.toml --check ../web` | 12 files already formatted |
| `uv run --directory backend pytest ../web -q` | 266 passed, 32 skipped, 1 warning (`PytestRemovedIn10Warning`) |
| Lo mismo del backend con `PRUEBAS_DATABASE_URL` al PostgreSQL local del puerto 5434 (`pg_isready` dijo `accepting connections`) | 222 passed, 1 warning |

La primera corrida de la web, dentro del entorno del agente, falló al arrancar el navegador: Playwright buscaba los binarios en una caché vacía. La repetí apuntando a los navegadores que ya estaban instalados en la máquina. No instalé navegadores ni cambié pruebas.

T076 a T079 quedaron marcadas en `tasks.md`. El estado de ese archivo dice FN terminada el 2026-11-25. La descripción del PR final y el mensaje de commit van en el chat, no en el repositorio: el PR lo abre Hugo.

### Resultado de FN (2026-11-25)

| Tarea | Resultado |
|---|---|
| T076 | C-6 y C-7 dicen aplicado; las búsquedas de T021 y T064 siguen limpias |
| T077 | Los seis puntos de la revisión cumplen. Sin hallazgo nuevo. Sigue el `POST` simple de F2 (T027) |
| T078 | §1 a §6 enlazadas. Quickstart corregido en §2, §4 y §6 (TK-27) |
| T079 | Backend 190/32 y 222 con PostgreSQL local; web 266/32; ruff limpio |

- **Qué queda para Hugo:** el commit, el push y el PR con `Closes #90, #19, #94`. La prueba de Leonel sigue en #105.
- **Commit sugerido:** `docs(003): cierre de la spec 003 y guía de verificación completa (FN)`.
