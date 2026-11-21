# Investigación (Fase 0): Web del MVP

- **Spec**: [spec.md](spec.md) (aprobada el 2026-11-15)
- **Plan**: [plan.md](plan.md)
- **Fecha**: 2026-11-15

Cada punto tiene el formato de spec-kit: **Decisión**, **Por qué** y **Alternativas consideradas**. Las decisiones que tomó Hugo llevan su `DP-n` de §9.2 del plan.

---

## R-1. Herramienta de pruebas de la pantalla (DP-1, Hugo)

- **Decisión**: **Playwright para Python**: `pytest-playwright` 0.10.0 (8 oct 2026) y `playwright` 1.64.1 (22 oct 2026), las dos publicadas hace más de dos semanas. Se agregan al grupo de desarrollo del backend con `uv add --dev`, y las pruebas viven en `web/tests/`. Se corren con el entorno de uv del backend y su propio `web/pytest.ini` (QP-3): `uv run --directory backend pytest ../web -q`. Se usan dos navegadores: Chromium con la emulación de un Android (`Pixel 7`) y WebKit con la de un iPhone (`iPhone 13`).
- **Por qué**:
  - Navegadores reales, incluido el motor de Safari, con el canal de avisos, el audio y el almacenamiento de verdad.
  - Reloj de la página controlado con `page.clock` (principio V).
  - La misma herramienta del backend: uv y pytest, sin meter npm al repositorio.
- **Alternativas consideradas**:
  - `node:test`: no tiene dependencias, pero solo prueba lógica pura y mete Node al repositorio.
  - Vitest con happy-dom: dependencias de npm, y su DOM simulado no trae canal SSE, audio ni pantalla encendida.
- **Costo aceptado**: descargar Chromium y WebKit (`playwright install chromium webkit`), con cientos de MB, y pruebas de segundos cada una.
- **WebKit en esta Mac (QP-5)**: la Mac corre un macOS muy nuevo (Darwin 27). La primera tarea de F1 comprueba que WebKit arranca. Si no, se usa la versión más nueva de Playwright con soporte que tenga al menos dos semanas; si no hay ninguna, WebKit corre solo en la integración continua en Linux (#35), en local solo Chromium, y se anota como TK.
- **Lo que `page.clock` no controla (QP-4)**: solo maneja los temporizadores de JavaScript. La reconexión interna de `EventSource` y `AbortSignal.timeout()` corren en tiempo real. Por eso los tiempos de espera se hacen con `setTimeout` y `AbortController`, y las pruebas de reconexión esperan en tiempo real (5 s como máximo). *Cambiado por TK-1 del plan (QT-2 de tasks): la reconexión se prueba con el reintento propio de la pantalla y reloj controlado, y la reconexión automática del navegador se comprueba a mano.*

## R-2. Servidor simulado para las pruebas

- **Decisión**: `web/tests/servidor_simulado.py` es una app FastAPI pequeña, solo para pruebas, que corre con uvicorn en un hilo y en un puerto libre.
  - Sirve los archivos de `web/` y las rutas de la spec 001 que consume la pantalla ([contracts/uso-del-servidor.md](contracts/uso-del-servidor.md)), en el mismo origen. Así las pruebas no dependen de CORS, que ya se prueba en la 001.
  - Cada prueba programa sus respuestas: el cobro creado, los errores, la imagen vacía, la hora del servidor, y los eventos del canal, que empuja por una cola cuando la prueba lo pide.
  - También puede cerrar el flujo de un canal o rechazarlo (404 o 429), para provocar cortes y reconexiones (QP-4).
  - Registra cada petición, para comprobar que la pantalla no pide nada a otro origen (CE-010) y que no repite cobros (RF-011).
- **Por qué**: control total de cada caso, sin pey ni reloj real (principio V). FastAPI y uvicorn ya están en el entorno del backend.
- **Alternativas consideradas**:
  - El backend real con su `PeySimulado` y su `RelojFalso`: el `dormir` del reloj falso adelanta el tiempo sin esperar, y dentro del ciclo del canal correría hasta el fin de la ventana en un instante. Además, volvería a probar la 001.
  - `page.route` de Playwright: entrega el cuerpo de una vez y no sirve para un flujo SSE que emite eventos a lo largo del tiempo.

## R-3. Cómo se dibuja el QR (DP-2 y DP-3, Hugo)

- **Decisión**: se muestra la imagen PNG que manda el servidor (`qr_imagen`, generada por pey) en un `<img>` con `data:image/png;base64,…`, sin librerías. Se escala con `image-rendering: pixelated` para que los módulos no se vean borrosos, y ocupa al menos el 70 % del ancho (CE-007).
- **Si `qr_imagen` llega vacía** (DP-3): la pantalla vuelve a la vista Teclado con "No se pudo mostrar el QR. Intenta de nuevo." y conserva el monto y el concepto. Nadie vio ese QR, así que no se escucha. La spec no cubría este caso: entró con el cambio **C-3**, aprobado y aplicado como RF-078.
- **Por qué**: lo más simple (principio IX), sin componente de terceros.
- **Alternativas consideradas**:
  - Dibujarlo con `qrcode-generator` 2.0.4 (MIT, sin dependencias): siempre habría QR y nítido, pero es una librería que copiar y declarar.
  - `lean-qr` 2.7.4: igual, con menos años de uso.
- **Consecuencia**: `backend/README.md:88` dice que, con `qr_imagen` en `null`, "la web dibuja el QR a partir de `qr`". Ya no es cierto: se corrige en FN (DP-17).

## R-4. Desde dónde se sirve la web (DP-4, Hugo)

- **Decisión**: lo decide el despliegue (#65). La web funciona de las dos formas:
  - **Sitio estático aparte**: `web/config.js` lleva la dirección completa del servidor, y el dominio de la web se agrega a `WEB_ORIGIN` del servidor (`backend/app/config.py:41`).
  - **Servida por el backend**: `servidor` queda vacío, lo que significa "el mismo origen". Esto sí es un cambio al servidor: si #65 lo elige, se propone entonces un `C-n` a la spec 001.
- **Por qué**: no bloquear la web por una decisión del despliegue que Altairtm todavía no toma.
- **Alternativas consideradas**: fijar ahora el sitio estático (recomendado en la pregunta) o el backend (exigía un C-n ya).

## R-5. Canal de avisos en el navegador

- **Decisión**: un `EventSource` por cada cobro en escucha que tenga canal asignado, abierto a `GET /api/cobros/{id}/eventos` (contrato de la 001).
  - **Máximo 3 canales por pantalla (QP-1)**: Chrome y Safari abren como máximo 6 conexiones HTTP/1.1 por origen, y cada canal ocupa una todo el tiempo. El cobro en pantalla siempre tiene canal; los otros dos van a los dos cobros anteriores más recientes. Los demás se siguen con la consulta del estado cada 3 s desde el inicio. Al terminar un canal, pasa al siguiente cobro anterior más reciente. Así quedan 3 conexiones libres para crear, ver y cancelar.
  - Se escuchan `estado`, `pago`, `vencido`, `cancelado` y `fin`. Al recibir `fin` se llama a `close()`, como obliga el contrato de la 001.
  - **Error de red**: el navegador reconecta solo (estado `CONNECTING`, con el `retry: 3000` que manda el servidor, `backend/app/canal.py:67`).
  - **Respuesta que no es 200** (404 o 429): el navegador cierra el canal (estado `CLOSED`) y no dice el código.
  - **Respaldo**: en cuanto llega `error`, empieza la consulta del estado con `GET /api/cobros/{id}` cada 3 s (RF-030). Esa consulta también aclara qué pasó:
    - 404: el servidor ya no conoce el cobro (RF-057, RF-056).
    - 200 con el canal `CLOSED`: lo más probable es el límite de canales (RF-034). Se sigue consultando y se intenta reabrir el canal cada 15 s (RF-031).
  - Al llegar `open`, se quita «Reconectando…» y la consulta pasa a 8 s (RF-079). Así también llegan los pagos cuando un proxy entrega las cabeceras y retiene los eventos. Se programa el siguiente GET al terminar el actual y se reaprovecha su resultado si cambia el estado del canal.
  - Los eventos del canal y las respuestas del GET comparten `Avisados`. Un estado anterior se descarta para que un evento retenido no tape un pago ya mostrado.
  - La escucha termina con `fin`, o cuando la hora del servidor alcanza `fin_ventana` en la consulta (RF-040).
- **Por qué**: `EventSource` viene en los navegadores de CE-001 y el servidor ya está hecho para él. La consulta cada 3 s coincide con el límite del servidor, que le pregunta a pey como mucho una vez cada 3 s por cobro.
- **Costo con canal abierto (C-4)**. Hasta 7.5 GET por minuto en promedio por cobro con respuestas rápidas, o 22.5 por pantalla con sus tres canales abiertos. El GET y el canal comparten la última consulta a pey por cobro. El GET puede activar una consulta a pey al pasar 3 s y el canal al pasar 5 s. Por eso el número adicional de consultas a pey depende de cuándo coincidan.
- **Alternativas consideradas**: leer el flujo con `fetch`. Daría el código de error, pero obliga a reimplementar la reconexión y el formato SSE.
- **Limitación aceptada (QA-3 de la spec)**: el servidor admite 10 canales por IP. Con el máximo de 3 por pantalla (QP-1), solo se llega ahí con varias pantallas detrás de la misma IP; en ese caso, los canales rechazados quedan con la consulta cada 3 s. Las consultas a pey que generan esas consultas siguen siendo la limitación aceptada.

## R-6. Hora del servidor y cuenta regresiva (C-2)

- **Decisión**: con el C-2 aplicado, cada cobro trae `hora_servidor`, un entero Unix como los demás tiempos (nombre fijado al aplicar el C-2 el 2026-11-15).
  - Al recibir cada cobro, la pantalla calcula `desfase = hora_servidor − ahora_del_celular` y lo guarda por cobro.
  - El tiempo restante es `expira_en − (ahora_del_celular + desfase)`, recalculado cada 250 ms y mostrado como `m:ss`, para que la cuenta no se atrase si el navegador retrasa un temporizador.
  - Así, el primer cobro que tardó 9 s en crearse arranca en 9:51 (CE-016), porque `creado_en` se fijó antes de llamar a pey (`backend/app/main.py:181-185`).
  - El error máximo es el redondeo del entero (menos de 1 s) más lo que tarda la respuesta en llegar: dentro de los 2 s de RF-019.
- **Si un cobro llega sin `hora_servidor`** (el C-2 todavía no está aplicado): se usa el reloj del celular y queda una advertencia en la consola. El corte 1 no se cierra sin el C-2 (plan, §8).
- **Alternativas consideradas**:
  - La cabecera `Date` de la respuesta: con CORS no se puede leer sin exponerla, y tampoco llega en los eventos del canal.
  - Arrancar siempre en 10:00: no cumple RF-019 (QA-2).

## R-7. Sonido de pago recibido

- **Decisión**: el sonido lo genera la propia web.
  - Al cargar la página se arma en memoria un WAV corto (dos tonos de unos 0.6 s) y se reproduce con un `HTMLAudioElement`.
  - **Desbloqueo**. El toque del dueño inicia el WAV silenciado y lo detiene una vez que se resuelve `play()`. Al volver a visible o recibir `pageshow`, se prepara un desbloqueo para el siguiente toque (RF-054).
  - **Rechazo de reproducción (C-5)**. El resultado de `play()` se devuelve a la app y se registra con `console.info`. Si falla el aviso de un pago nuevo, se muestra «Toca para activar el sonido» y se reintenta desde el gesto. Al recuperar, los pagos siguen mostrándose en silencio hasta el primer toque.
  - Si `navigator.audioSession` existe, se intenta fijar `type = "playback"` dentro de `try/catch`. El efecto del silenciador se verifica físicamente en el iPhone (TK-2). [Audio Session](https://www.w3.org/TR/audio-session/)
  - Es un sonido propio, así que no es componente de terceros. El sonido final es de #33.
- **Por qué**: no hay licencia que declarar ni archivo que descargar.
- **Riesgo a comprobar en F4**: el interruptor de silencio del iPhone. Según lo publicado, calla el audio generado con Web Audio, pero no siempre el de un elemento `<audio>`. Se comprueba en el iPhone de prueba y el resultado se anota como TK (spec §7).
- **Alternativas consideradas**:
  - Un archivo con licencia libre: hay que declararlo y servirlo.
  - Un oscilador de Web Audio: más fácil de generar, pero el silencio del iPhone lo calla.

## R-8. Vibración

- **Decisión**: `navigator.vibrate([200, 100, 200])` solo si existe (RF-024). En Safari de iPhone no existe y no se hace nada.
- **Alternativas consideradas**: ninguna; es la única forma estándar.

## R-9. Pantalla encendida (RF-058, RF-059)

- **Decisión**: Screen Wake Lock (`navigator.wakeLock.request("screen")`), solo si existe y el sitio está en HTTPS.
  - Se pide al haber al menos un cobro en escucha y se suelta al no quedar ninguno.
  - El navegador lo suelta solo al ocultar la página, así que se vuelve a pedir en `visibilitychange` cuando la página se ve otra vez y sigue habiendo cobros en escucha.
- **Alternativas consideradas**: reproducir un video invisible en bucle. Es un truco frágil, gasta batería y no hace falta en Chrome de Android (CE-011).

## R-10. Recordar los cobros para la recarga (corte 2)

- **Decisión**: `localStorage`, clave `pago_facil_escucha`, con `{"en_pantalla": "<id o null>", "anteriores": ["<id>", …]}`.
  - Se escribe al crear, cancelar, pulsar Nuevo cobro y terminar cada escucha.
  - Al leerlo, todo se trata como dato no confiable (RF-077):
    - si no es JSON o no tiene esa forma, se ignora;
    - solo se aceptan identificadores de 1 a 32 caracteres `[A-Za-z0-9_-]`;
    - cada uno se vuelve a pedir al servidor.
  - Si leer o escribir lanza un error (modo privado o almacenamiento bloqueado), se sigue sin recordar nada (RF-076).
- **Alternativas consideradas**:
  - `sessionStorage`: se pierde al cerrar la pestaña, y E-8 habla de recargar o cerrar el navegador.
  - IndexedDB: demasiado para una lista de identificadores.

## R-11. Mostrar textos de forma segura (RF-077)

- **Decisión**:
  - Todo texto que viene de fuera (concepto, `detail` del servidor y datos recordados) se pone con `textContent`, nunca con `innerHTML`.
  - La página lleva una política de seguridad de contenido en `<meta>` (QP-2): `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self' http://localhost:8000 https:`.
    - `media-src blob:` deja sonar el WAV que arma la página (R-7).
    - `http://localhost:8000` permite la prueba en local del quickstart.
    - Al desplegar, #65 cambia `https:` por el dominio exacto del servidor, para no permitir conexiones a cualquier sitio HTTPS.
- **Por qué**: aunque se colara un texto con forma de código, no se ejecuta. Es la defensa en dos capas.
- **Alternativas consideradas**: limpiar el HTML con una librería. Es otra dependencia y no hace falta si nunca se interpreta.

## R-12. Estructura sin framework ni compilación

- **Decisión**: HTML, CSS y JavaScript con módulos nativos (`<script type="module">`), sin empaquetador ni paso de compilación. Chrome de Android y Safari de iPhone los cargan directamente.
  - La lógica pura vive en módulos sin DOM: teclado, cuenta regresiva, avisados y lectura de lo recordado.
  - Las pruebas importan esos módulos dentro del navegador con `page.evaluate(() => import(...))`.
- **Por qué**: lo dice la constitución ("sin framework") y es lo más simple de desplegar como sitio estático.
- **Alternativas consideradas**: un empaquetador (Vite o esbuild): una herramienta nueva sin una necesidad que la justifique (principio IX).

## R-13. Montos en el teclado

- **Decisión**:
  - El teclado trabaja con el **texto** del monto ("25.5"), no con un número, para respetar exactamente lo tecleado ("$25." mientras se escribe).
  - Las reglas de RF-003, RF-004 y RF-066 a RF-068 son una función pura: `aplicar_tecla(texto, tecla) → texto`.
  - Se manda al servidor como número JSON (`25.5`), que el servidor convierte con `Decimal(str(...))` (contrato de la 001).
  - Cobrar se activa cuando el texto vale más de 0. Monto libre se activa cuando el texto está vacío o vale 0 (RF-006, RF-065).
- **Alternativas consideradas**: guardar centavos enteros. No representa "$25." mientras se escribe.

## R-14. Selectores estables para las pruebas

- **Decisión**: cada elemento que las pruebas tocan lleva el atributo `data-prueba` (por ejemplo `data-prueba="cobrar"`), configurado en Playwright con `selectors.set_test_id_attribute("data-prueba")`. La lista está en [contracts/vistas.md](contracts/vistas.md).
- **Por qué**: las pruebas no se rompen al cambiar textos o estilos, y el nombre queda en español.
- **Alternativas consideradas**: buscar por texto visible. Se rompe con cada cambio de redacción.
