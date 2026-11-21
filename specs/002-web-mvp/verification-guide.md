# Guía de verificación: 002 Web del MVP

## F1 Preparación

Fecha: 2026-11-15. Quedaron Playwright, el servidor simulado, las páginas de los dos celulares y el esqueleto de la web. Todavía no hay teclado, cobro ni canal en la pantalla.

### Navegadores

En `backend/pyproject.toml`, grupo `dev`:

- `pytest-playwright` **0.10.0**
- `playwright` **1.64.1**

En esta Mac (Darwin 27) los dos abrieron `about:blank`. WebKit se descargó como la compilación para macOS 26 (`webkit-mac-26`, revisión 2370) y arrancó. No hizo falta la alternativa de QP-5 y no hay TK nuevo. Los navegadores quedaron en la caché de Playwright, fuera del repositorio.

```bash
uv run --directory backend playwright install chromium webkit
```

### La página

`web/index.html` trae `lang="es"`, el viewport, la marca `PAGO FÁCIL` y la política de R-11 tal cual. `config.js` deja `servidor` en cadena vacía: el mismo origen. `estilos.css` usa `box-sizing` y no fija anchos. `js/app.js` solo lee esa dirección.

La primera corrida de las pruebas de arranque falló con 404, porque `index.html` todavía no existía. Después del esqueleto pasan.

### Comandos

```bash
uv run --directory backend pytest ../web -q
```

Esperado: `5 passed`. Son las dos pruebas de arranque, cada una en Chromium (Pixel 7) y en WebKit (iPhone 13), más una prueba sin navegador que comprueba que el servidor simulado no sirve nada de `web/tests/`. El `rootdir` es `web` (`web/pytest.ini`). No sale el `PytestDeprecationWarning` de pytest-asyncio.

### Revisión de Claude (2026-11-15)

Claude revisó lo que implementó Grok y comprobó los ayudantes de `conftest.py` con una sonda temporal, ya borrada: `reloj`, `sonidos`, `vibraciones`, `bloqueos`, `canales`, el canal del simulado (`estado`, `pago`, `cortar_canal` con 503) y que la política detecta una violación. Todo funcionaba salvo un fallo, que se corrigió:

- **El simulado servía `web/tests/`** con rutas como `/js/../tests/conftest.py`, porque comprobaba el texto de la ruta y no la ya resuelta. Ahora responde 404 (prueba `test_el_servidor_simulado_no_sirve_los_archivos_de_las_pruebas`, vista fallar antes del arreglo).
- Nombres en inglés (`_lock`, `_loop`, `sock`, `args`) pasados a español, por `AGENTS.md` §4.
- La prueba de la consola usa el tipo `ConsoleMessage` en lugar de `getattr`.
- `reloj(pagina, hora)` recibe **segundos Unix** (Playwright de Python multiplica por 1000), igual que `creado_en` y `hora_servidor`. Quedó dicho en su docstring para F2 en adelante.

pytest-playwright 0.10.0, con pytest 9.2, avisa una vez `PytestRemovedIn10Warning` por su fixture `base_url`. No viene de esta fase. El comando igual sale en 0.

```bash
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Los cinco salen limpios. El backend da **109 passed**. T001 hablaba de 104, el conteo del día en que se escribieron las tareas; no se agregaron ni se quitaron pruebas del backend.

El aviso de Starlette sobre `TestClient` y httpx sigue ahí, igual que en la 001. No viene de F1.

### Cierre

Commit sugerido:

```text
test(002): preparar Playwright, servidor simulado y esqueleto de la web (F1)
```

## F2 Base

Fecha: 2026-11-15. Quedaron la lógica del teclado, la cuenta regresiva y los pagos avisados; crear, ver y cancelar contra el servidor; el sonido propio; el bloqueo de pantalla; y las vistas Teclado y Generando QR. Las teclas se ven y se pueden pulsar, pero todavía no cambian el monto: conectarlas es F3. Cobrar sigue desactivado con el monto vacío.

Las pruebas de esta fase se escribieron antes del código y fallaron porque faltaban los módulos (`teclado.js`, `cuenta.js`, `avisados.js`, `servidor.js`, `vistas.js`). Después de implementarlas pasan.

### Ver el teclado en local

Sigue el quickstart §3 para servir la carpeta. En F2 no hace falta el servidor real ni la llave de pey: la vista Teclado no pide un cobro.

1. Deja `web/config.js` con `servidor: ""` (el mismo origen).
2. Sirve la web:

```bash
uv run --directory backend python -m http.server 5173 --directory ../web
```

3. Abre `http://localhost:5173` en el navegador, en modo celular, a 320 px de ancho.
4. Al terminar, para ese proceso por su PID exacto (`lsof -ti tcp:5173` lo muestra y `kill <PID>` lo para). No uses `pkill`.

**Esperado**: "PAGO FÁCIL", el monto en "$", las teclas 0 a 9, el punto y Borrar, el concepto (como máximo 40 caracteres) y Cobrar desactivado. La página no se desplaza hacia los lados. Pulsar un número deja el monto en "$": el teclado de la pantalla se conecta en F3.

### Sonido sin archivo

La página no importa el sonido al abrir. En la consola de esa misma página, antes de cualquier otro `import` de `js/sonido.js`:

```javascript
const urls = [];
const Original = window.Audio;
window.Audio = function (src) {
  urls.push(String(src));
  return new Original(src);
};
window.Audio.prototype = Original.prototype;
const { desbloquear, sonar } = await import("./js/sonido.js");
desbloquear();
sonar();
console.log(urls[0]);
```

**Esperado**: la dirección empieza por `blob:`. En la pestaña Red no aparece un `.wav` ni un `.mp3`. En `web/` no hay archivo de sonido: el WAV de dos tonos se arma en memoria al importar `js/sonido.js`.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

**Esperado en la web**: `52 passed, 29 skipped`. Las 29 saltadas son las pruebas de lógica pura en WebKit: llevan `only_browser("chromium")` porque no dependen del motor. En Chromium sí corren. Entran las 5 de F1. El aviso `PytestRemovedIn10Warning` de pytest-playwright sigue igual que en F1.

**Esperado en el backend**: `109 passed`. F2 no tocó el backend. Sigue el aviso de Starlette sobre `TestClient` y httpx.

Ruff de la web y del backend queda limpio. F2 no cambió `.gitignore`: no hacía falta ningún patrón nuevo.

### Revisión de Claude de F2 (2026-11-15)

Claude revisó lo que implementó Grok: las 5 pruebas nuevas, los 7 módulos de `web/js/`, y siguió esta guía a mano en el navegador integrado (320 px). Ninguna prueba fallaba. La suite es estable (3 corridas seguidas, 52 passed y 29 skipped).

- **Corregido: la pantalla podía quedarse encendida para siempre.** Si se pedía soltar el bloqueo mientras el navegador todavía contestaba el pedido, el bloqueo llegaba después y nadie lo soltaba (RF-059). Prueba nueva `test_soltar_mientras_se_pide_el_bloqueo_no_lo_deja_pegado`, vista fallar (`soltados: 0`) antes del arreglo en `web/js/pantalla.js`.
- **Corregido, sin cambio de comportamiento:** el JSDoc de `volumen` estaba colgado de `rebobinar` en `web/js/sonido.js`, y `_abortar` en tres archivos de pruebas usaba `# type: ignore` en lugar del tipo `Route`.
- **Comprobado con el `Audio` real, sin simulacro** (las pruebas simulan `play`): el WAV que arma la página dura 0.6 s, no da error en Chromium ni en WebKit y la política de seguridad no registra ninguna violación. `fetch` sobre el `blob:` sí lo bloquea `connect-src`, como debe ser.
- **Comprobado a mano con esta guía:** la vista Teclado no desborda a 320 px, las teclas van en orden de celular, Cobrar está apagado, pulsar un número deja el monto en "$" (las teclas se conectan en F3) y el fragmento del sonido da una dirección `blob:` sin ningún `.wav` en la red. La consola no muestra errores.

Pendiente para F3, a la vista en el navegador: el campo del concepto es una caja vacía, sin texto de ayuda, y el estilo es el del navegador sin tocar. Es esperado en F2; el diseño real llega con la vista QR (T027).

### Cierre

Commit sugerido:

```text
feat(002): lógica pura, uso del servidor, sonido y vistas base de la web (F2)
```

## F3 Teclado, cobro y QR

Fecha: 2026-11-15. El teclado de la pantalla ya escribe el monto. Cobrar pide el cobro, muestra "Generando QR…" al instante y, si el servidor responde con imagen, enseña el QR con el monto, el concepto, la indicación de CoDi y una cuenta regresiva que sigue `hora_servidor`. Si el servidor rechaza, no hay conexión o el QR llega sin imagen, vuelve el teclado con el mensaje y lo escrito se conserva.

Las pruebas de pantalla se escribieron antes del código. Fallaron porque pulsar un número dejaba el monto en "$" y Cobrar seguía desactivado. La de 40 caracteres en el concepto ya pasaba: el `maxlength` venía de F2.

### Cobro de $0.01 en local, sin pagarlo

Sigue el quickstart §3. Hace falta el servidor real de la 001 en el puerto 8000. No pagues el QR: esta fase solo comprueba que se genera y que la cuenta corre.

1. En `backend/.env`, agrega `WEB_ORIGIN=http://localhost:5173` sin tocar las demás variables, y arranca el servidor como dice el quickstart de la 001.
2. En `web/config.js`, pon `servidor: "http://localhost:8000"`. Al terminar, déjalo otra vez en `""` para no guardar esa dirección.
3. Sirve la web:

```bash
uv run --directory backend python -m http.server 5173 --directory ../web
```

4. Abre `http://localhost:5173` en el navegador, en modo celular, a 320 px de ancho.
5. Teclea 0, punto, 0 y 1. El monto queda en "$0.01" y Cobrar se activa. Escribe un concepto, por ejemplo "Tacos", y pulsa Cobrar.
6. Al terminar, para el `http.server` por su PID exacto (`lsof -ti tcp:5173` y `kill <PID>`). No uses `pkill`.

**Esperado**: "Generando QR…" sale enseguida. Después se ve el QR grande, "$0.01", "Tacos", "Escanéalo desde la app de tu banco, en la opción CoDi" y una cuenta que empieza cerca de 10:00 y baja. La página no se desplaza hacia los lados. Si no hay llave de pey, el teclado vuelve con el mensaje del servidor y "$0.01" sigue escrito.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

**Esperado en la web**: `94 passed, 29 skipped`. Las 29 saltadas siguen siendo la lógica pura en WebKit. Entran las de F1 y F2. El aviso `PytestRemovedIn10Warning` de pytest-playwright sigue igual.

**Esperado en el backend**: `109 passed`. F3 no tocó el backend. Sigue el aviso de Starlette sobre `TestClient` y httpx.

Ruff de la web y del backend queda limpio.

### Revisión de Claude de F3 (2026-11-15)

Claude revisó lo que implementó Grok: las pruebas nuevas (`test_teclado.py`, `test_crear_y_mostrar_qr.py`), `app.js`, `vistas.js` y `estilos.css`. Ninguna prueba fallaba y no hizo falta corregir código. La suite es estable: 3 corridas seguidas dieron `94 passed, 29 skipped`; el backend da `109 passed` y ruff queda limpio en la web y en el backend.

- **Contra el servidor simulado, en el navegador integrado a 320 px, siguiendo los pasos de arriba:** teclear 0, punto, 0, 1 deja "$0.01" y activa Cobrar; con "Tacos" sale "Generando QR…" y después el QR (224 px de 320, el 70 %), "$0.01", "Tacos", la indicación de CoDi y una cuenta que arranca en 9:59 y baja. La página no se desplaza hacia los lados (`scrollWidth` 320) y la consola no muestra errores.
- **Los `detail` de las pruebas de rechazo (422, 429, 502 y 503) son los textos reales de `backend/app/main.py`.** El backend siempre responde `detail` como texto, así que `crear_cobro` no necesita cubrir el caso de una lista.
- **No se probó contra el servidor real:** hacerlo llama a pey. Queda para Hugo, con la llave en `backend/.env`, sin pagar el QR.
- **Paso 1 de la guía:** `WEB_ORIGIN` ya vale `http://localhost:5173` por defecto en `backend/app/config.py`. Solo hace falta agregarla si la web se sirve desde otro puerto.

**Probado por Hugo contra el servidor real (2026-11-15):** con su llave de pey, el cobro de $0.01 con "Tacos" mostró el QR. Un primer intento falló porque abrió `http://[::]:5173` (el enlace que imprime `http.server`): el backend solo permite el origen `http://localhost:5173` y rechaza el resto con `400 Disallowed CORS origin`, que la web muestra como falta de conexión. Hay que abrir `http://localhost:5173` a mano.

**Tema anotado para después:** el teclado de la computadora no escribe el monto; solo funcionan las teclas de la pantalla. La spec no pide teclado físico (ni en la spec, ni en el plan, ni en las tareas), así que agregarlo es un cambio `C-n` a la spec 002, que Hugo aprueba por separado. Para un celular no hace falta.

Pendiente para F4, a la vista en el navegador: la cuenta repinta la vista QR cada 250 ms, así que al llegar un pago (T030 en adelante) hay que parar ese intervalo antes de mostrar Pago recibido. El QR mide el 70 % del ancho (`70vw`), correcto en un celular de pie y demasiado alto en horizontal; el diseño real llega más adelante.

### Cierre

Commit sugerido:

```text
feat(002): teclado, crear el cobro y mostrar el QR con cuenta regresiva (F3)
```

## F4 Aviso de pago y respaldo del canal

Fecha: 2026-11-15. Con el QR en pantalla, un pago nuevo suena, vibra en Android y deja la vista verde "Pago recibido". Si el canal se corta, se ve "Reconectando…" sin quitar el QR, y la consulta cada 3 s descubre el pago igual. Al volver el canal se quita el aviso. El mismo pago no suena dos veces.

Las pruebas se escribieron antes del código y fallaban porque no había escucha. La de WebKit del canal rechazado además esperaba "Reconectando…" antes de adelantar el reloj: si no, la consulta todavía no estaba programada.

### Modo avión (reconexión del navegador)

Con un cobro ya en la vista QR, en el celular:

1. Activa el modo avión. **Esperado**: aparece "Reconectando…" y el QR sigue.
2. Quita el modo avión. **Esperado**: desaparece "Reconectando…".
3. Provoca un pago después. **Esperado**: suena y se ve "Pago recibido".

Esto no lo cubre la suite: el reloj de las pruebas no controla la reconexión automática del navegador (TK-1).

### Silencio del iPhone (R-7)

Pendiente, anotado como TK-2 en el plan §14. Hace falta el iPhone de Hugo. No queda dicho si suena o no.

1. Sirve la web en la red local, como el quickstart §3, pero con la IP de la Mac en lugar de `localhost` (en `config.js` y en `WEB_ORIGIN`).
2. Abre esa dirección en el iPhone, crea un cobro y pon el teléfono en silencio.
3. Provoca un pago (simulado, o $0.01 real si Hugo lo autoriza en ese momento).
4. Anota en TK-2 si se oyó el sonido.

Al terminar, deja `web/config.js` con `servidor: ""`.

### Comprobado en el navegador, contra el simulado

A 320 px: teclear 25.50 y "Tacos", pulsar Cobrar, y al llegar el pago se ve la pantalla verde con "Pago recibido", "$25.50" y "Tacos". El QR se oculta. `scrollWidth` queda en 320 y la marca sigue visible. El modo avión y el silencio del iPhone no se probaron aquí.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

**Esperado en la web**: `122 passed, 29 skipped`. Las 29 saltadas siguen siendo la lógica pura en WebKit. El aviso `PytestRemovedIn10Warning` de pytest-playwright sigue igual.

**Esperado en el backend**: `109 passed`. F4 no tocó el backend. Sigue el aviso de Starlette sobre `TestClient` y httpx.

Ruff de la web y del backend queda limpio.

### Revisión de Claude de F4 (2026-11-15)

Claude revisó lo que implementó Grok: `web/js/escucha.js`, `vistas.js`, `app.js`, `estilos.css` y las pruebas de `test_pago_recibido.py` y `test_respaldo.py`. Ninguna prueba fallaba. La suite es estable: 5 corridas seguidas dieron `122 passed, 29 skipped`; el backend da `109 passed` y ruff queda limpio en la web y en el backend.

- **Corregido: monto distinto sin rótulos.** La vista mostraba `$25.50 $20.00`, sin decir cuál se pidió y cuál llegó (RF-028). Ahora dice `Pediste $25.50, recibiste $20.00`. La prueba `test_un_monto_distinto_muestra_el_pedido_y_el_recibido` ganó esa comprobación y se vio fallar (`Actual value: $25.50 $20.00`) antes del arreglo en `web/js/vistas.js`.
- **Corregido, sin cambio de comportamiento:** `_abortar_consulta` en `test_respaldo.py` no tenía tipo de retorno (`AGENTS.md` §5).
- **Los eventos del simulado coinciden con los del backend real** (`backend/app/canal.py` y `respaldo.py`): `estado` trae el cobro y `pago` trae `{pago, cobro}`, que es lo que lee `escucha.js`.
- **Comprobado a mano, contra el simulado, a 320 px, siguiendo esta guía:** con el QR en pantalla se cortó el canal y salió «Reconectando…» sin quitar el QR. Un pago sin aviso por el canal lo descubrió la consulta de 3 s y la pantalla se puso verde con "Pago recibido", "$25.50" y "Tacos"; el QR se oculta y la cuenta se detiene. Al restaurar el canal desapareció «Reconectando…», y un segundo pago de $20.00 con monto distinto mostró el rótulo nuevo. `scrollWidth` quedó en 320. La consola solo mostró el `503` que provoqué al cortar el canal y el aviso de Chrome de que bloquea `vibrate` si no hubo un toque real: las pruebas hicieron los toques por código, en un celular real sí vibra.

Pendiente, a la vista en el navegador:

- El texto blanco de "Pago recibido" sobre el verde `#128a3e` tiene un contraste de unos 4.4:1, justo debajo del 4.5:1 recomendado para texto pequeño. El monto grande sí pasa. El diseño real llega más adelante.
- `estilos.css` pinta el fondo con `body:has(...)`, que necesita iOS 15.4 o más. Si el iPhone de la prueba del silencio es más viejo, la pantalla no se verá verde.
- El silencio del iPhone y el modo avión siguen sin probarse (TK-2 y TK-1): necesitan el celular de Hugo.

### Cierre

Commit sugerido:

```text
feat(002): aviso de pago con sonido, vibración y respaldo del canal (F4)
```

## F5 QR vencido, Nuevo cobro y vista Error

Fecha: 2026-11-15. Si el QR cumple 10 minutos sin un pago, se oculta y queda "QR vencido", con el aviso de que un pago tardío todavía se avisa. Con un pago ya recibido, al llegar a 0:00 la pantalla se queda en verde. `fin`, o una consulta con la hora del servidor ya pasada de `fin_ventana`, cierra el canal y no vuelve a preguntar. Si el servidor ya no conoce el cobro, se ve la vista Error. Nuevo cobro, desde QR, QR vencido, Pago recibido o Error, vuelve al teclado vacío y deja de escuchar ese cobro. Las teclas y los botones miden al menos 44 px de alto.

### Verlo en local, sin pagar

Sirve la web como en F2 (`servidor: ""`) o contra el simulado. Con el servidor real, un cobro de $0.01 sigue el quickstart §5; no lo pagues si solo quieres ver el vencimiento.

1. Teclea un monto, escribe un concepto y pulsa Cobrar.
2. Pulsa Nuevo cobro. **Esperado**: el teclado vuelve vacío. Un pago de ese QR ya no cambia la pantalla.
3. Crea otro cobro y espera 10 minutos sin pagarlo. **Esperado**: desaparece el QR y se lee "QR vencido", el monto, el concepto y "Si el cliente ya pagó, aquí te avisamos".
4. Si ese cobro se pagara dentro de los siguientes 10 minutos, sonaría y se vería "Pago recibido".

Los pagos reales del corte 1 (quickstart §5 y §6) quedan pendientes: hace falta tu autorización y la web en HTTPS. No se hicieron en esta sesión.

### Revisión de seguridad del corte 1

- Secretos: `git grep -nE "whsec_|Bearer |PEY_API_KEY|PEY_WEBHOOK_SECRET|pey\\.mx" -- web` no encontró nada.
- Textos de fuera: `git grep -n "innerHTML\\|outerHTML\\|insertAdjacentHTML\\|document.write" -- web/js` no encontró nada. El concepto, los mensajes y los montos se pintan con `textContent`.
- La política de `web/index.html` es la de R-11: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self' http://localhost:8000 https:`.
- Un pago solo se anuncia en `escucha.js` cuando el servidor trae un pago nuevo en el cobro (`sonar` y `vibrar` dentro de ese recorrido). La pantalla no marca un pago por su cuenta.
- Cobrar y Monto libre se ignoran mientras `accion_en_curso` está ocupada. La web no reintenta crear un cobro sola.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

**Esperado en la web**: `176 passed, 29 skipped`. Las 29 saltadas siguen siendo la lógica pura en WebKit.

**Esperado en el backend**: `109 passed`. F5 no tocó el backend.

### Revisión de Claude de F5 (2026-11-15)

Claude revisó `escucha.js`, `vistas.js`, `app.js`, `estilos.css`, `test_vencido_y_nuevo.py` y `test_seguridad.py`. Ninguna prueba fallaba y el comportamiento es el de la spec. La suite es estable: 7 corridas seguidas dieron `176 passed, 29 skipped`.

- **Corregido: la suite tardaba 4.5 minutos** (F4 tardaba 1). Seis pruebas saltaban 5 o 10 minutos con `clock.run_for`, que dispara el intervalo de la cuenta unas 2400 veces: 11 s en Chromium y 19 s en WebKit cada una. Pasaron a `clock.fast_forward`, que dispara los temporizadores una vez; la cuenta se recalcula con `Date.now()`, igual que cuando el celular se duerme. Las mismas 176 pruebas pasan en unos 100 s. Anotado como TK-3 en el plan.
- **Corregido, sin cambio de comportamiento:** `_visible` en `test_vencido_y_nuevo.py` no tenía tipo de retorno, y el JSDoc de `empezar_cuenta` estaba colgado encima de `tiene_pagos`, en `app.js`.
- **Revisión de seguridad (T042), repetida por Claude:** los dos `git grep` salen vacíos (secretos y HTML inyectado), la política de `web/index.html` es la de R-11 con los ajustes de QP-2, `crear_cobro` solo se llama desde `pedir_cobro` y un pago solo se anuncia desde `escucha.js` con un cobro del servidor.
- **Comprobado a mano, contra el simulado, a 320 px:** con el QR en pantalla, el evento `vencido` oculta el QR y deja "QR vencido", "$25.50", "Tacos" y "Si el cliente ya pagó, aquí te avisamos". Un pago tardío con el QR vencido muestra "Pago recibido". Con el cobro olvidado y el canal rechazado con 404, la consulta lleva a la vista Error con el texto de RF-057. Nuevo cobro, desde QR, Pago recibido y Error, deja el teclado en "$" y sin concepto. La página no se desplaza hacia los lados y los botones visibles miden 44 px.
- **No se probó:** los pagos reales (quickstart §5 y §6), el silencio del iPhone y el modo avión. Esperan a CoDi y a tu celular.

### Cierre

Commit sugerido:

```text
feat(002): QR vencido, Nuevo cobro y vista de error (F5)
```

## F6 Monto libre, número de pago y Mostrar QR otra vez

Fecha: 2026-11-15. Con el monto vacío o en cero, Monto libre pide un cobro sin monto y el QR dice "Monto libre". Con un monto mayor a cero, la tecla está apagada. Desde el segundo pago se ven "Pago 2" y el total. Mientras el QR siga vigente, "Mostrar QR otra vez" vuelve a enseñarlo; si ese QR llega a 0:00, regresa a Pago recibido y no a QR vencido. Un pago nuevo con el QR reabierto suena y vuelve a la pantalla verde.

### Verlo en local

1. Deja el concepto, por ejemplo "Propina", y pulsa Monto libre sin teclear un monto. **Esperado**: "Generando QR…" y después el QR con "Monto libre" y "Propina". Cobrar sigue apagado.
2. Teclea 25.50. **Esperado**: Monto libre se apaga y Cobrar se prende.
3. Cobra $25.50. Cuando llegue un pago, se ve "Pago recibido" sin "Pago 1". Un segundo pago al mismo QR muestra "Pago 2" y el total.
4. Antes de que pasen 10 minutos, pulsa "Mostrar QR otra vez". **Esperado**: vuelve el QR y su cuenta. Si se acaba el tiempo, vuelve "Pago recibido".

El pago real de monto libre y el segundo pago de $0.01 (quickstart §7) quedan pendientes: hace falta tu autorización. No se hicieron en esta sesión.

### Revisión de Claude de F6 (2026-11-15)

Claude revisó `test_monto_libre_y_reuso.py`, y `vistas.js` y `app.js` en lo de Monto libre, "Pago n" y Mostrar QR otra vez. Ninguna prueba fallaba. Los campos que usa (`monto: null`, `fin_ventana`, `total_recibido`, `pagos[].numero`) existen en `backend/app/cobros.py`, y el backend acepta `monto: null` como monto libre (`validar_monto`).

- **Corregido: el total sin rótulo.** Desde el segundo pago la vista mostraba "Pago 2" y "$35.50" sin decir que era la suma, bajo un monto grande que es el del último pago. Ahora dice `Total recibido: $35.50` (igual que el rótulo de monto distinto de F4). La prueba `test_el_segundo_pago_muestra_pago_2_y_el_total` ganó esa comprobación y se vio fallar (`Actual value: $35.50`) antes del arreglo en `web/js/vistas.js`.
- **Corregido, sin cambio de comportamiento:** una asignación sin uso de `id_cobro` en `test_mostrar_qr_otra_vez_vuelve_al_qr_mientras_siga_vigente`.
- **Comprobado a mano, contra el simulado, a 320 px:** sin teclear monto, Monto libre crea el QR con "Monto libre" y "Propina"; con 25 tecleado se apaga y Cobrar se prende. Dos pagos (12 y 5) dejaron "Pago 2" y "Total recibido: $17.00", sin "monto distinto". "Mostrar QR otra vez" volvió al QR con su cuenta (9:35) y "Monto libre".
- **No se probó:** los pagos reales de $0.01 (quickstart §7).

### Cierre

Commit sugerido, si F5 y F6 van juntas:

```text
feat(002): QR vencido, monto libre, número de pago y mostrar el QR otra vez (F5 y F6)
```

Si se separan, el de F6 es:

```text
feat(002): monto libre, número de pago y mostrar el QR otra vez (F6)
```

## F7 Cobros anteriores y Cancelar cobro

Fecha: 2026-11-15. Nuevo cobro deja el cobro como anterior y lo sigue escuchando hasta el fin de su ventana. Un pago a ese cobro suena, vibra en Chromium y muestra un aviso con el monto y el concepto, sin borrar lo que se está tecleando; el aviso se cierra al tocarlo. Hay como máximo 3 canales: el cobro en pantalla y los dos anteriores más recientes. El resto se consulta cada 3 segundos, y al cerrarse un canal el siguiente más reciente abre el suyo. La pantalla sigue encendida mientras quede cualquier escucha.

Cancelar cobro aparece en el QR de un cobro pendiente. Mientras el servidor responde, el botón dice "Cancelando…" y un segundo toque no repite el pedido. Si el servidor confirma, vuelve el teclado vacío y el cobro se sigue escuchando: un pago posterior suena y muestra el aviso. Si rechaza (404, 409 o sin conexión), el QR se queda con el mensaje. Un `cancelado` que llega por el canal, sin que esta pantalla lo haya pedido, hace lo mismo que una cancelación confirmada.

Se quitó `test_en_el_corte_1_nuevo_cobro_deja_de_escuchar_el_cobro`: en el corte 2 Nuevo cobro ya no corta la escucha. La prueba de soltar la pantalla, tras Nuevo cobro, espera el `fin` del cobro anterior.

### Verlo en local

Hace falta el servidor simulado o el servidor real. Con el simulado, las pruebas de `web/tests/test_cobros_anteriores.py` recorren los dos flujos. A mano, con la web y el servidor en marcha:

1. Crea un cobro, por ejemplo $30 "Refresco", pulsa Nuevo cobro y teclea otro monto. Paga el QR anterior. **Esperado**: suena, aparece el aviso de $30.00 y "Refresco", y el monto tecleado sigue ahí. Al tocar el aviso, se cierra.
2. Crea otro cobro y pulsa Cancelar cobro. **Esperado**: un momento "Cancelando…" y después el teclado vacío. El QR sigue pagable: al pagarlo, suena y aparece el aviso.

Los pagos reales de $0.01 (quickstart §7, "Cobro anterior" y "Cancelar") quedan pendientes: hace falta tu autorización. No se hicieron en esta sesión.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

La web: **206 passed, 29 skipped**. El backend: **109 passed**. Ruff, en los dos, limpio. Los 29 saltos son las pruebas marcadas `only_browser("chromium")` cuando les toca WebKit. El aviso de pytest-playwright sobre `base_url` sigue igual que en F1, y el de Starlette sobre `TestClient` igual que en la 001.

### Revisión de Claude de F7 (2026-11-15)

Claude revisó el diff de `escucha.js` (`tomar_canal`, `soltar_canal`, `_repartir`, `cancelado`), `app.js` (`al_cancelar`, `volver_al_teclado`, `pintar_qr_actual`), `vistas.js`, el simulado y las pruebas de `test_cobros_anteriores.py`. El reparto de 3 canales coincide con QP-1 y con data-model §2, y las 14 pruebas nuevas cubren los escenarios de T049 y T050. Ninguna fallaba.

- **Corregido: el aviso del cobro anterior quedaba fuera de la pantalla.** Se anexaba al final de la página sin estilo. A 320×568, en la vista verde «Pago recibido», su borde superior caía en 584 px, con la pantalla en 568: el dueño no lo veía sin desplazarse. Ahora es una franja fija arriba, encima de cualquier vista (`web/estilos.css`). La prueba `test_el_aviso_de_un_cobro_anterior_se_ve_sin_desplazar_la_pantalla_y_dice_que_es` se vio fallar antes del arreglo.
- **Corregido: el aviso sin rótulo.** Decía solo «$30.00 Refresco». Ahora dice `Pago de un cobro anterior: $30.00 Refresco` (mismo tipo de fallo que el rótulo de monto distinto de F4 y el del total de F6). Cambio en `web/js/vistas.js`.
- **Comprobado a mano, contra el simulado, a 320 px:** con el teclado, un pago al cobro anterior deja el aviso arriba sin borrar el "$12" tecleado; en la vista QR y en «Pago recibido» el aviso queda a la vista; un concepto de 40 caracteres se envuelve en dos líneas.
- **Pendiente para F8:** si dos cobros anteriores se pagan seguidos, el segundo aviso reemplaza al primero (un solo elemento `aviso-anterior`). Los dos suenan, pero solo queda visible el último. RF-075 pide un aviso por cada pago recuperado, así que F8 tendrá que acumularlos; conviene decidirlo entonces.
- **Resultados:** web **208 passed, 29 skipped** (107 s); backend **109 passed**; `ruff check` y `ruff format --check` limpios en web y backend.
- **No se probó:** los pagos reales de $0.01 (quickstart §7, «Cobro anterior» y «Cancelar»).

### Cierre

Commit sugerido:

```text
feat(002): escuchar cobros anteriores y cancelar un cobro (F7)
```

## F8 Recuperar los cobros al recargar

Fecha: 2026-11-15. Al recargar en el mismo celular, la pantalla recupera los cobros que seguían en escucha. El que estaba en pantalla vuelve en la vista de su estado (QR, QR vencido o Pago recibido) y los anteriores se siguen escuchando. Lo que se pagó con la página cerrada se muestra sin sonar ni vibrar: el de pantalla con su número de pago y su total, y cada pago de un cobro anterior con su aviso. Hasta el primer toque se lee "Toca para activar el sonido"; un pago anterior a ese toque se ve sin sonar, y el siguiente ya suena.

Lo guardado es solo identificadores, en `localStorage` con la clave `pago_facil_escucha`. Si el texto no tiene la forma pedida, o un id no es válido, se ignora todo y vuelve el teclado. Si el celular no deja leer ni escribir, la recarga también vuelve al teclado vacío. Un cobro cuya ventana ya terminó no se muestra ni abre canal. Si el servidor ya no conoce al de pantalla, se ve la vista Error; si es un anterior, desaparece sin esa vista.

Cada pago de un cobro anterior deja su propio aviso, uno debajo del otro. Las pruebas que recargan para empezar otro cobro desde el teclado borran antes `pago_facil_escucha`: si no, F8 les devolvería el cobro anterior.

### Revisión de Codex de F8 (2026-11-15)

- Un cobro cancelado que estaba en pantalla vuelve al teclado y sigue en escucha como anterior. Si llega un pago, se muestra el aviso de cobro anterior.
- Al recuperar un cobro pagado, «Mostrar QR otra vez» conserva la cuenta regresiva. Al terminar, vuelve a «Pago recibido».
- Las consultas de recuperación avanzan por separado. Si falla una, se conserva el identificador y se reintenta a los 3 segundos. Si falta confirmar el cobro en pantalla, se ve «Reconectando…» antes de poder iniciar otro cobro. Cada identificador abre como máximo un canal.
- Si falla la escritura en `localStorage`, se intenta borrar el recuerdo desactualizado para que la recarga vuelva al teclado vacío. Un toque en la pantalla habilita el audio, y los pagos recuperados se muestran en silencio.
- La primera corrida completa falló en WebKit en `test_si_el_servidor_rechaza_el_canal_se_sigue_con_la_consulta`. Las pruebas de reconexión con 429 y 503 esperan ahora las peticiones del navegador antes de avanzar el reloj.

### Verlo en local

Con la web y el servidor en marcha (quickstart §7, "Recargar"):

1. Crea un cobro y recarga la página. **Esperado**: vuelve ese cobro y, abajo, "Toca para activar el sonido".
2. Sin tocar, provoca un pago. **Esperado**: se ve "Pago recibido" y no suena.
3. Toca la pantalla y provoca otro pago. **Esperado**: el aviso desaparece y este sí suena.

La verificación con un pago CoDi real de $0.01 sigue pendiente de autorización específica de Hugo.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Resultado de la revisión. Web con Chromium y WebKit, **243 pruebas aprobadas y 32 omitidas** por la marca `only_browser("chromium")`. Backend, **109 pruebas aprobadas**. Ruff pasó la revisión de lint y formato en ambos. Se mantienen los avisos de obsolescencia de pytest-playwright sobre `base_url` y de Starlette sobre `TestClient`.

### Cierre

Commit sugerido:

```text
feat(002): recuperar los cobros en escucha al recargar la página (F8)
```

## FN Pulido del corte 2

Fecha: 2026-11-15. Quedó el README del MVP en `web/README.md`, con la descripción de la PWA que sigue siendo la meta del proyecto. La línea de `qr_imagen` en `backend/README.md` ya dice que, si llega en `null`, la web muestra "No se pudo mostrar el QR. Intenta de nuevo." y no dibuja el QR. El quickstart se recorrió y no hizo falta cambiarlo.

### Quickstart

Los comandos se corrieron desde la raíz.

1. **Requisitos.** `uv run --directory backend playwright install chromium webkit` terminó en 0. Chromium 1248 y WebKit 2370 ya estaban en la caché de Playwright. No hizo falta la alternativa de QP-5.
2. **Pruebas.** `uv run --directory backend pytest ../web -q` dio **243 passed, 32 skipped** en 117 s. Los 32 saltos son las pruebas de lógica pura cuando les toca WebKit. El aviso de pytest-playwright sobre `base_url` sigue igual que en F1. El backend dio **109 passed**, con el aviso de Starlette sobre `TestClient`, igual que en la 001.
3. **Pantalla en local.** Este comando sirve `web/`:

```bash
uv run --directory backend python -m http.server 5173 --directory ../web
```

En `http://localhost:5173`, a 320×568, se ve "PAGO FÁCIL", el teclado y Cobrar desactivado. Monto libre está activo, que es el corte 2. Al teclear 0, punto, 0, 1 se lee "$0.01", Cobrar se activa y Monto libre se apaga. La página no se desplaza hacia los lados (`scrollWidth` 320) y las teclas miden 44 px de alto. `config.js` se dejó con `servidor: ""`. No había servidor en el puerto 8000 y esta sesión no tenía autorización para un cobro real, así que no se pidió el QR de $0.01.
4. **Despliegue.** El texto coincide con el código: `config.js` publica la única dirección, y la política de `web/index.html` sigue trayendo `https:` en `connect-src` para que #65 lo cambie por el dominio del servidor. La web no está publicada.
5. **Pago real del corte 1**, **pantalla encendida** y **corte 2.** No se hicieron. Siguen pendientes la autorización de Hugo, un Android y un iPhone, y la web en HTTPS (#65). Los pasos escritos coinciden con la pantalla: "$0.01" sale en seis toques contando Cobrar, y con un monto escrito Monto libre queda apagado. Al recargar, el quickstart pide tocar la pantalla y después pagar; la spec, en ese momento, muestra "Toca para activar el sonido". No se contradicen. No hay TK nuevo.

### Revisión de seguridad del corte 2

- Secretos: `git grep -nE "whsec_|Bearer |PEY_API_KEY|PEY_WEBHOOK_SECRET|pey\.mx" -- web` no encontró nada.
- Textos de fuera: `git grep -n "innerHTML\|outerHTML\|insertAdjacentHTML\|document.write" -- web/js` no encontró nada. El concepto, los mensajes y los montos se pintan con `textContent`.
- La política de `web/index.html` es la de R-11 con los ajustes de QP-2: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self' http://localhost:8000 https:`.
- Un pago solo se anuncia en `escucha.js` cuando el cobro llega del servidor (`estado`, `pago`, `vencido` o la consulta) y trae un pago nuevo. La pantalla no marca un pago por su cuenta.
- Cobrar y Monto libre se ignoran mientras `accion_en_curso` está ocupada. La web no reintenta crear un cobro sola.
- Lo recordado en el celular sale solo de `memoria.js`. `leer()` exige las dos claves `en_pantalla` y `anteriores`, y cada id tiene de 1 a 32 caracteres `[A-Za-z0-9_-]`. Si el texto no cumple, devuelve `null` y no se usa. En `web/js`, `localStorage` no aparece en otro archivo.
- Cancelar va solo por `POST` a `window.PAGO_FACIL.servidor + /api/cobros/${id}/cancelar`. En `servidor.js` el otro `POST` es el de crear un cobro; ver un cobro y el canal usan la misma dirección configurada.

### Comandos

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

La web: **243 passed, 32 skipped**. El backend: **109 passed**. Ruff, en los dos, limpio. FN no cambió código de la pantalla ni del servidor.

### Revisión de Claude de F8 y FN (2026-11-16)

Claude revisó `memoria.js`, la recuperación en `escucha.js` y `app.js`, el aviso «Toca para activar el sonido», los avisos apilados, `test_recuperar.py` y lo que Codex ya había corregido, además del README de la web y la sección FN. Ninguna prueba fallaba y no hizo falta cambiar código de la pantalla.

- **Resultados repetidos por Claude:** web **243 passed, 32 skipped** (119 s); backend **109 passed**; `ruff check` y `ruff format --check` limpios en web y backend. Coinciden con los de Grok.
- **Seguridad, repetida con `grep -rn` y no con `git grep`:** `git grep` solo mira archivos que git conoce, y `memoria.js` y `test_recuperar.py` aún no estaban confirmados, así que se le habrían escapado. Sin secretos, sin `innerHTML`, `eval` ni `new Function`; `localStorage` solo aparece en `memoria.js`; los dos únicos `POST` son crear y cancelar.
- **Comprobado a mano, contra el simulado, a 320 px:** al recargar vuelve el QR con su cuenta (9:57) y «Toca para activar el sonido» abajo; un pago antes del toque da «Pago recibido» sin sonar (el aviso sigue ahí); tras el toque, el aviso desaparece y el siguiente pago suena una vez y deja «Pago 2» y «Total recibido: $17.00»; la página no se desplaza hacia los lados.
- **README de la web:** el comando de «Correr en local» sirve la web (`index.html`, `js/memoria.js` y `config.js` dan 200) y paré el servidor por sus PID exactos. Agregué una línea: no abrir el enlace `http://[::]:5173` que imprime el comando, porque el servidor lo rechaza por CORS y la pantalla dice que no hay conexión (nos pasó en F3).
- **Observaciones, sin cambio:**
  - Los avisos de cobros anteriores se apilan arriba sin tope de alto. Con unos 8 o más seguidos taparían el botón Nuevo cobro hasta que se toquen uno por uno. Es raro (hacen falta muchos pagos a cobros anteriores con la página cerrada); si molesta, basta `max-height` y `overflow-y: auto` en `avisos-anteriores`.
  - Un cobro en pantalla que otra pantalla canceló y que recibió un pago con la página cerrada vuelve al teclado sin el aviso de ese pago. Es un caso raro; los demás flujos de cancelación sí avisan.
  - Un cobro que el servidor ya no conoce lleva a la vista Error al recargar, como pide la spec. Si el servidor se reinicia, el dueño la verá una vez.
- **No se probó:** el pago real de $0.01 de F8 (CE-014), los de F5 a F7, el iPhone (TK-2) y el modo avión (TK-1).

### Cierre

Commit sugerido:

```text
docs(002): pulido del corte 2, README de la web y quickstart validado (FN)
```

## Pruebas reales con CoDi (2026-11-16)

Hugo hizo las pruebas con pey real, pagos de $0.01 desde su banco, en `http://localhost:5173` contra el backend local (`http://localhost:8000`, con `config.js` apuntando ahí; se dejó otra vez en `servidor: ""`). `/salud` dio `llave_pey: true` y `secreto_aviso_pey: false`: en local no hay webhook, así que cada pago se detectó por la consulta de respaldo del backend (`fuente=consulta` en el log).

### Resultado

Hugo reportó que todas las pruebas funcionaron:

- Cobro de $0.01: suena y sale el aviso del pago.
- Cobro anterior (Nuevo cobro y luego pago del QR anterior): suena y sale «Pago de un cobro anterior: $0.01 Cobro».
- Cancelar cobro y pagar ese QR, Recargar y tocar la pantalla, y Monto libre.

El log del backend lo corrobora en lo que se alcanzó a ver: al menos tres pagos registrados (`numero=1`, `fuente=consulta`) y siete cobros en escucha a la vez. Solo tres tenían canal (`/eventos`) y el resto se consultaba con `GET /api/cobros/{id}` cada 3 segundos, como pide QP-1.

### Observaciones

- **El primer pago tardó más de 30 s en aparecer.** El backend hizo unas 11 consultas seguidas con `pagos_nuevos=0` antes de que pey reportara el `PAID`. Es de pey y del respaldo sin webhook, no de la web. El tiempo «menos de 2 s» (CE-001) solo se puede medir con el webhook en el despliegue de #65.
- **Un falso «no sonó».** Al principio Hugo creyó que no sonó. Fue un error al confirmar el pitido, no de la web: se comprobó que `sonar()` reproduce (`play ok`, volumen 1, sin silencio).
- **El navegador integrado de la app no es un celular.** Las pruebas se hicieron en computadora.

### Sigue pendiente

- Android y iPhone con la web en HTTPS: sonido y vibración reales, el iPhone en silencio (TK-2) y el modo avión (TK-1).
- Pantalla encendida 10 minutos (CE-011, quickstart §6).
- Tiempos de CE-001 y CE-006 con el webhook activo.

## C-4 y C-5 · Consulta con SSE abierto y recuperación del sonido

Fecha de implementación 2026-11-16. Mientras el canal está abierto, la web consulta el cobro cada 8 s. Si el canal se corta o el cobro se queda sin canal asignado, consulta cada 3 s. Hay un solo GET en curso por cobro. SSE y GET comparten `Avisados`, incluso si el proxy entrega luego los eventos acumulados.

Si el navegador rechaza el sonido de un pago, la pantalla muestra «Toca para activar el sonido» y lo reintenta al tocar. Al volver a la página, el primer toque vuelve a desbloquear el audio. Cada intento registra su resultado en la consola. Se sigue usando el WAV con `HTMLAudioElement` y se pide la sesión `playback` donde esté disponible. Los pagos recuperados y los que se avisan antes del primer toque de F8 se muestran en silencio.

### Resultados automáticos

Las pruebas nuevas se ejecutaron antes de implementar. Se reprodujeron el canal abierto que no descubre el pago y el rechazo de audio sin aviso, en Chromium y WebKit. Con el cambio pasan los casos de canal mudo, pago duplicado por SSE y GET, consulta pendiente al reconectar, evento vencido atrasado, última consulta de la ventana, rechazo y reintento de audio, vuelta a la página, sesión de audio opcional y recuperación de F8.

- `uv run --directory backend pytest ../web -q` → **265 passed, 32 skipped** por selección de motor. Playwright usó Chromium y WebKit, el reloj controlado y el servidor simulado.
- `uv run --directory backend ruff check --config pyproject.toml ../web` → pasó.
- `uv run --directory backend ruff format --config pyproject.toml --check ../web` → 12 archivos con formato correcto.
- `uv run --directory backend pytest -q` → **109 passed** en una copia temporal del backend sin `.env`, con el transporte de pey simulado.
- `uv run --directory backend ruff check .` → pasó.
- `uv run --directory backend ruff format --check .` → 20 archivos con formato correcto.

### Prueba pendiente con dos celulares

1. Expón la web y el backend mediante HTTPS con un túnel que entregue SSE en vivo. Por ejemplo, con los puertos locales del [quickstart](quickstart.md), abre cada reenvío en una terminal y conserva las dos URL HTTPS que imprime el servicio. [Documentación de localhost.run](https://localhost.run/docs/http-tunnels) · [Acceso gratuito con `nokey`](https://localhost.run/docs/faq#i-dont-want-to-use-an-ssh-key)

   ```bash
   ssh -R 80:127.0.0.1:8000 nokey@localhost.run
   ssh -R 80:127.0.0.1:5173 nokey@localhost.run
   ```

2. Arranca el backend con `WEB_ORIGIN` igual al origen HTTPS de la web. Sirve `web/` como indica el quickstart y apunta `servidor` de `web/config.js` al origen HTTPS del backend durante la prueba.
3. En el celular del negocio, abre la URL de la web, crea un cobro de **$0.01 MXN** con autorización vigente de Hugo y deja el QR en pantalla. Desde la computadora puedes verificar el túnel con este comando, reemplazando el dominio y el id por los del cobro. `event: estado` debe llegar mientras la conexión sigue abierta. En la prueba de Hugo, el túnel rápido de Cloudflare retuvo los eventos hasta el cierre. Para esta comprobación usa un túnel que entregue el evento antes de cerrar.

   ```bash
   curl -NsS --max-time 18 'https://DOMINIO_API/api/cobros/ID/eventos'
   ```

4. En el segundo celular, paga con una cuenta propia desde la opción CoDi de la app del banco. En el celular del negocio, mantén la página abierta en el QR. Al registrarse el pago en el backend, verifica que aparece «Pago recibido» con $0.01 y que el sonido se oye una sola vez. Si aparece «Toca para activar el sonido», toca y confirma que el sonido se reintenta y el aviso se quita.
5. Repite con Android y iPhone como pantalla del negocio. En iPhone, comprueba con el silenciador activado y anota si el sonido se oye. Para probar el regreso, vuelve al navegador desde otra app antes de un pago nuevo, toca una vez y confirma que el siguiente aviso suena. Para probar F8, recarga después de un pago y comprueba que el pago recuperado se ve en silencio, incluso al tocar para activar el sonido.

Commit sugerido

```text
fix(002): consultar el cobro aunque el canal esté mudo y avisar si el navegador bloquea el sonido
```

### Revisión de Claude de C-4 y C-5 (2026-11-16)

Claude revisó el diff de `escucha.js` (consulta cada 8 s con canal abierto, un solo GET en curso, descarte de estados viejos), `app.js` y `sonido.js` (intento de sonido con resultado, reintento con un toque, desbloqueo al volver a la página, `audioSession`), el simulado (`dejar_canal_mudo`) y las pruebas nuevas. No hizo falta cambiar código.

- **Resultados repetidos por Claude:** web **265 passed, 32 skipped** (135 s); backend **109 passed**; `ruff check` y `ruff format --check` limpios en web y backend. Coinciden con los de Codex.
- **Seguridad:** sin `innerHTML`, `eval` ni `new Function` en `web/js`; sin secretos; `localStorage` solo en `memoria.js`; `audioSession` solo en `sonido.js`, dentro de `try/catch`.
- **Las pruebas no dependen de `web/config.js`.** Con `config.js` apuntando a un túnel (como estaba durante la prueba real), la suite pasó igual: el simulado ahora siempre sirve su propio `config.js`.
- **Causa de lo que se vio en Android e iPhone:** el túnel rápido de Cloudflare retiene el canal de eventos hasta que se cierra (8 eventos de 1 por segundo llegaron juntos a los 8.3 s; con `localhost.run` llegaron uno por segundo). La consulta de seguridad de C-4 cubre ese caso, y también el de un proxy con búfer en producción (#65).
- **Costo en el backend:** cada consulta de la web (`GET /api/cobros/{id}`) pide a pey los pagos como mucho cada 3 s por cobro (`intervalo_minimo=3`). Con tres canales abiertos son tres consultas más cada 8 s; no cambia el límite hacia pey.
- **Estado de C-4 y C-5:** aprobados por Hugo el 2026-11-16 (así lo marca el documento y Hugo lo confirmó).

### Resultado de la prueba con celulares (2026-11-16)

Con el celular del negocio en el QR, sin salir de la página, y el pago desde otro dispositivo:

- **Antes de C-4 y C-5:** con un túnel rápido de Cloudflare el pago se registró en el backend, pero la pantalla se quedó en el QR y el aviso solo apareció al salir de la página, sin sonido. El túnel retenía el canal de eventos hasta cerrarse (8 eventos de 1 por segundo llegaron juntos a los 8.3 s).
- **iPhone (Safari), backend por `localhost.run` (canal en vivo):** Hugo reportó que funciona: aparece «Pago recibido» y suena.
- **Android (Chrome), backend por un túnel rápido de Cloudflare (canal retenido):** Hugo reportó que funciona. Como el túnel retiene los eventos, el aviso llega por la consulta de seguridad de C-4, hasta unos 8 s después de registrarse el pago, y suena con la pantalla en primer plano.

### Sigue pendiente

- **No se midió «menos de 2 s»** (CE-001, CE-002, #64): hace falta el webhook y un canal en vivo, en el despliegue de #65.
- Vibración en Android, iPhone en silencio con el interruptor activado (TK-2), modo avión (TK-1) y pantalla encendida 10 minutos (CE-011).

Los túneles gratuitos sirvieron para las pruebas pero son frágiles: el de `localhost.run` se cortó cada ~16 minutos, y el rápido de Cloudflare no transmite eventos. Para repetir estas pruebas conviene el despliegue real de #65.

### Repetición de las pruebas de C-4 y C-5 en Windows (2026-11-17)

Juan reportó seis fallos en WebKit en Windows 11 con el commit `9795e74`. En macOS los seis casos originales pasan. La sonda local con Playwright 1.64.1 registró `touchstart`, `touchend` y un `click` confiable al usar `tap()` en WebKit 27.2 con el perfil iPhone 13. El `EventSource` emitió `open` con solo las cabeceras y sin bytes de cuerpo. La causa de los fallos en Windows sigue por confirmar.

- **Sonido.** Las pruebas usan `locator.click()` para entregar el evento que escucha la web. WebKit conserva el perfil iPhone 13. Se siguen comprobando el reintento tras el rechazo del audio, el desbloqueo único al regresar y la reactivación al recuperar un cobro.
- **Canal mudo.** El simulado envía la línea de protocolo `retry:` al abrir el flujo y retiene los eventos del cobro. Las pruebas se sincronizan con la respuesta del servidor y con el registro de apertura de la web antes de adelantar el reloj. Comprueban el GET de los 8 s, el aviso, el sonido y que el SSE siga conectado al servidor en la primera prueba. La segunda comprueba el aviso del último GET y el cierre del canal.

En una copia temporal, se desactivó la programación de la consulta al abrir el SSE. En ambos motores, el primer caso falló al esperar el GET y el segundo al esperar «Pago recibido». Con la consulta activa, omitir que se aplique el resultado del último GET también hizo fallar el segundo caso.

Juan puede volver a correr los seis casos en Windows desde la raíz del repositorio. El selector los ejecuta en Chromium y WebKit, según la configuración de la suite.

```bash
uv run --directory backend pytest ../web -q -k "bloquea_el_sonido or primer_toque_repite or pide_un_toque or canal_abierto_y_mudo or cierra_el_canal_mudo"
```
