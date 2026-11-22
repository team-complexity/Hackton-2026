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
