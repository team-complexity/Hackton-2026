# Tasks: Web del MVP: cobrar con el teclado y oír que me pagaron

- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-15, con el cambio C-3 aplicado (RF-078)
- **Plan**: [plan.md](plan.md), estado: Aprobado el 2026-11-15 (DP-1 a DP-17, QP-1 a QP-5)
- **Fecha**: 2026-11-15
- **Estado**: `FN terminada (Grok, 2026-11-15)`. F8 implementada por Grok y revisada por Codex (2026-11-15). Prueba CoDi real de F8 pendiente. F7 terminada el 2026-11-15. F1 terminada el 2026-11-15 (Hugo la revisó). El C-2 a la spec 001 (F0) quedó aplicado el 2026-11-15 con el campo `hora_servidor`. Pagos reales del quickstart §5 a §7 pendientes de autorización, celulares y #65.
- **Entrada**: los documentos de `specs/002-web-mvp/`: plan.md, spec.md, research.md, data-model.md, contracts/ y quickstart.md

> **Notas para los comandos de spec-kit.**
> - Cada tarea sigue el formato obligatorio `- [ ] T001 [P] [US1] Descripción con ruta del archivo`.
> - `/speckit-implement` la marca como `[X]` al terminarla.
> - Los detalles van como sub-puntos sangrados debajo de la tarea.
> - `[P]` = se puede hacer en paralelo (otros archivos, sin dependencias pendientes).
> - `[US1]` = historia de la spec a la que pertenece (H1 = US1 … H8 = US8).
> - Las casillas van siempre en listas, nunca en tablas (en las tablas no se ven).
> - Todas las rutas son relativas a la raíz del repositorio. Los comandos se corren desde la raíz.
> - Los textos entre comillas son los que exige la spec o los contratos; los nombres `data-prueba` son los de [contracts/vistas.md](contracts/vistas.md).

---

## Reglas de ejecución

1. **Las fases van en orden.** Una fase la hace una sola persona o agente. Al empezar lo anota en **Estado** ("F2 en curso (Claude)") y al cerrarla también ("F2 terminada (Claude, AAAA-MM-DD)").
2. **Pruebas primero.** En cada fase se escriben las pruebas, se ven fallar y después se implementa (principio V).
3. **Solo se hace la tarea pedida.** Nada de funciones sorpresa, retoques cosméticos ni refactorizaciones fuera de la tarea.
4. **Si el código obliga a cambiar algo**, se anota en el *Registro de implementación* del plan (§14) como TK-n. Si toca una spec aprobada, se presenta como un cambio `C-n`, que Hugo aprueba por separado.
5. **Una fase cierra con tres cosas:**
   - todo en verde:
     - backend: `uv run --directory backend pytest -q`, `uv run --directory backend ruff check .` y `uv run --directory backend ruff format --check .`;
     - web: `uv run --directory backend pytest ../web -q` (DP-15, QP-3);
     - estilo del Python de las pruebas de la web (AGENTS.md §5): `uv run --directory backend ruff check --config pyproject.toml ../web` y `uv run --directory backend ruff format --config pyproject.toml --check ../web`;
   - su sección en `specs/002-web-mvp/verification-guide.md`;
   - el mensaje de commit sugerido, con formato `tipo(002): descripción en español`.
   - El commit, el push y el pull request los hace Hugo.
6. **Ninguna prueba automática llama al pey real ni al servidor real, ni espera a que corra el reloj real.** Todas usan `ServidorSimulado` (R-2) y, donde hay temporizadores de JavaScript, el reloj de la página con la ayuda `reloj(pagina, hora)`, que lo instala y lo congela (QT-3). La reconexión del canal se prueba con el reintento propio de la pantalla, no con la reconexión automática del navegador (QT-2). Las pruebas con dinero real son de $0.01 y requieren la autorización de Hugo en ese momento.
7. **Secretos**: la web no tiene ninguno. Nadie lee, imprime ni cita `PEY_API_KEY` ni `PEY_WEBHOOK_SECRET`; para saber si el servidor los tiene, se usa `GET /salud`.
8. **Dos celulares**: las pruebas de pantalla corren en Chromium (`Pixel 7`) y en WebKit (`iPhone 13`). Las de lógica pura llevan `@pytest.mark.only_browser("chromium")` (plan §7).

## Reparto

| Fase | Quién la hace | Quién la revisa |
|---|---|---|
| F1 Preparación | Claude | Hugo |
| F2 Base | Claude | Hugo |
| F3 Historias 1 y 2 (C1) | Claude | Hugo |
| F4 Historias 3 y 4 (C1) | Claude | Hugo; prueba del silencio en el iPhone con Miguel o Beer17 |
| F5 Historias 5 y 6 (C1), cierre del corte 1 | Claude | Hugo (pagos reales de $0.01 en Android y iPhone) |
| F6 a F8 (C2) | Claude | Hugo |
| FN Pulido | Claude | Hugo |

Miguel o Beer17 revisan cada pull request y lo prueban en su iPhone o Android (DP-5).

## Dependencias externas

| Dependencia | Qué bloquea | Estado |
|---|---|---|
| C-2 aplicado en la spec 001 (`hora_servidor` en el objeto cobro y en los eventos), fase F0 del plan, trabajo del `tasks.md` de la 001 | El nombre definitivo del campo en T015 y T027, y el cierre del corte 1 (T043). Mientras no esté, las pruebas usan `hora_servidor`, el nombre propuesto | Listo: aplicado el 2026-11-15 con el nombre `hora_servidor` (F9 de la 001) |
| WebKit de Playwright en esta Mac (Darwin 27) | Las pruebas en `iPhone 13` desde F1 (QP-5) | Se comprueba en T002 |
| Web y servidor publicados con HTTPS, y el dominio de la web en `WEB_ORIGIN` (#65, Altairtm) | Los pagos reales y la pantalla encendida de T043 (CE-001, CE-011) y los cierres del corte 2 | Pendiente |
| CoDi activo en el banco con que se prueba (Hugo) | Los pagos reales de $0.01 de T043, T048, T053 y T057 | Se activa el 15 nov |
| Un Android con Chrome y un iPhone con Safari (equipo) | T034 (silencio del iPhone) y T043 | Por confirmar |
| Sonido de pago recibido | RF-022, RF-044 | Resuelto por R-7: la web genera su propio sonido, sin licencia que declarar (el final es de #33) |

## Formato de cada tarea

```text
- [ ] T000 [P] [US1] Descripción con la ruta exacta del archivo
  - **RF**: RF-001, RF-002
  - **Dep.**: T000 (o "ninguna")
  - **Hecho cuando**: criterio verificable (prueba que pasa, comando y salida esperada)
```

---

## Fase 1 (F1): Preparación (Setup) · 16 nov

**Propósito**: Playwright y sus navegadores, el servidor simulado, las páginas de los dos celulares y el esqueleto de la web, sin comportamiento todavía.

- [X] T001 Agregar `pytest-playwright` 0.10.0 y `playwright` 1.64.1 como dependencias de desarrollo en `backend/pyproject.toml` y `backend/uv.lock`
  - Comando: `cd backend && uv add --dev "pytest-playwright==0.10.0" "playwright==1.64.1"`. Las dos versiones tienen más de dos semanas (H-13). Sin `pip install`.
  - **RF**: — (DP-1, DP-15, principio V)
  - **Dep.**: ninguna
  - **Hecho cuando**: `uv run --directory backend pytest -q` sigue en `104 passed` y `uv run --directory backend python -c "import playwright, pytest_playwright"` no falla.
- [X] T002 Instalar Chromium y WebKit para el entorno de `backend/` y comprobar que arrancan en esta Mac (QP-5), sin dejar archivos en el repositorio
  - Comando: `uv run --directory backend playwright install chromium webkit`.
  - Prueba vacía: un script en el directorio temporal de la sesión (fuera del repositorio) que, con `sync_playwright`, abre cada navegador, carga `about:blank` y lo cierra.
  - Si WebKit no arranca: probar la versión más nueva de `playwright` con soporte para este macOS que tenga al menos dos semanas. Si no hay ninguna, WebKit queda solo para la integración continua en Linux (#35), en local se corre solo Chromium y se anota como TK en el plan §14.
  - **RF**: — (QP-5, CE-001)
  - **Dep.**: T001
  - **Hecho cuando**: los dos navegadores abren `about:blank`, o la alternativa está aplicada y anotada como TK.
- [X] T003 Crear `web/pytest.ini` (QP-3)
  - Contenido: `[pytest]`, `testpaths = tests`, `asyncio_default_fixture_loop_scope = function` y `addopts = --browser chromium --browser webkit` (los dos celulares de plan §7; si T002 aplicó la alternativa, solo `--browser chromium`).
  - **RF**: — (QP-3, DP-15)
  - **Dep.**: T002
  - **Hecho cuando**: `uv run --directory backend pytest ../web -q` informa `rootdir: …/web`, encuentra `testpaths` y no muestra `PytestDeprecationWarning` (todavía no hay pruebas: "no tests ran").
- [X] T004 [P] Escribir las pruebas de arranque en `web/tests/test_seguridad.py` (archivo nuevo)
  - `test_la_pagina_abre_y_muestra_pago_facil`: en los dos celulares, `[data-prueba="marca"]` dice "PAGO FÁCIL".
  - `test_la_pagina_carga_sin_errores_ni_bloqueos_de_la_politica`: ningún mensaje de consola de tipo `error` ni evento `securitypolicyviolation` al cargar (política de R-11 y QP-2).
  - **RF**: RF-060, RF-077 (política de seguridad de contenido)
  - **Dep.**: T003
  - **Hecho cuando**: las dos pruebas existen y fallan porque no hay servidor simulado ni página.
- [X] T005 [P] Crear el servidor simulado en `web/tests/servidor_simulado.py` (archivo nuevo, R-2)
  - App FastAPI que corre con uvicorn en un hilo, en `127.0.0.1` y un puerto libre. Sirve los archivos de `web/` (sin `tests/`) y las rutas de [contracts/uso-del-servidor.md](contracts/uso-del-servidor.md) en el mismo origen.
  - `cobro_de_prueba(id=None, monto=25.5, concepto="Tacos", creado_en=…, hora_servidor=…, pagos=[], qr_imagen=<PNG 1×1 en base64>)` arma un objeto cobro (con `id=None`, un id nuevo de 12 caracteres `[A-Za-z0-9]`) con los campos del [objeto cobro de la 001](../001-backend-mvp/contracts/crear-cobro.md#objeto-cobro) más `hora_servidor`: `expira_en = creado_en + 600`, `fin_ventana = expira_en + 600`, `monto_libre = monto is None`, `estado` calculado igual que el servidor y cada pago con `numero`, `monto_recibido`, `monto_distinto` y `pagado_en`.
  - Métodos que usan las pruebas (todos seguros entre hilos, con `loop.call_soon_threadsafe` para el canal):
    - `responder_crear(codigo=201, cuerpo=None, demora=0, sin_respuesta=False)`: programa la respuesta del siguiente `POST /api/cobros`. Por defecto crea un `cobro_de_prueba` con un id nuevo en cada `POST` (QT-3), el monto y el concepto recibidos, lo guarda y responde 201. Con otro código responde `{"detail": …}`.
    - `cobros`: diccionario `id → cobro` que leen `GET /api/cobros/{id}` (404 con `{"detail": "Ese cobro no existe"}` si falta) y el evento `estado` al abrir el canal.
    - `agregar_pago(id, monto_recibido, monto_distinto=False, avisar=True)`: suma el pago al cobro guardado y, si `avisar`, emite `pago` con `{"pago": …, "cobro": …}` en los canales abiertos de ese cobro.
    - `emitir(id, evento, datos)`: empuja `vencido`, `cancelado`, `fin` o `estado` a los canales abiertos.
    - `cortar_canal(id, rechazar_con=None)`: cierra los flujos abiertos de ese cobro; con `rechazar_con` (404, 429 o 503), los siguientes `GET …/eventos` responden ese código hasta `permitir_canal(id)`.
    - `olvidar(id)`: borra el cobro (simula un reinicio del servidor).
    - `fijar_hora(segundos)`: hora del servidor que se pone en `hora_servidor`.
    - `retry_ms`: valor de `retry:` del canal (3000, como `backend/app/canal.py:67`). Ninguna prueba depende de él: la reconexión se prueba con el reintento propio (QT-2).
    - `fijar_config(texto)`: reemplaza el contenido que sirve `/config.js` (por defecto `window.PAGO_FACIL = { servidor: "" };`).
    - `peticiones`: lista de `(método, ruta, cuerpo)` de todo lo recibido, incluidas las rutas que no existen; `reiniciar()` lo deja todo como al principio.
  - El canal manda `retry:`, el evento `estado` al abrir y después lo que se empuje, con `Cache-Control: no-cache`.
  - **RF**: — (R-2, DP-7, principio V)
  - **Dep.**: T003
  - **Hecho cuando**: `uv run --directory backend python -c "import sys; sys.path.insert(0, '../web/tests'); import servidor_simulado"` no falla.
- [X] T006 Crear `web/tests/conftest.py` con el servidor simulado y las páginas de los dos celulares
  - Fixture `servidor` (alcance de sesión arranca el hilo; por prueba llama a `reiniciar()`).
  - `browser_context_args` según `browser_name`: `playwright.devices["Pixel 7"]` en Chromium y `playwright.devices["iPhone 13"]` en WebKit, sin la clave `default_browser_type`.
  - Fixture `pagina`: la `page` de pytest-playwright con `add_init_script` que, antes de cargar la web:
    - reemplaza `HTMLMediaElement.prototype.play` por un contador `window.__sonidos` que guarda cada llamada con su `volume`, `muted` y `src`, y devuelve una promesa resuelta;
    - reemplaza `navigator.vibrate` por un contador `window.__vibraciones` (solo en Chromium; en WebKit no existe, como en Safari, R-8);
    - define `navigator.wakeLock.request("screen")` con contadores `window.__bloqueos_pedidos` y `window.__bloqueos_soltados`;
    - envuelve `window.EventSource` para guardar cada instancia en `window.__canales` (QT-3), y así poder ver su URL y su `readyState`.
  - Ayudas: `abrir(pagina, servidor)`, `tocar(pagina, "tecla-2", …)`, `sonidos(pagina)` (cuenta solo los `play` con volumen mayor a 0 y sin `muted`), `vibraciones(pagina)`, `bloqueos(pagina)`, `canales(pagina)` (lista de `{url, estado}` con `CONNECTING`, `OPEN` o `CLOSED`) y `reloj(pagina, hora)`, que hace `pagina.clock.install(time=hora)` y `pagina.clock.pause_at(hora)`, porque después de `install` el tiempo sigue corriendo solo (QT-3).
  - **RF**: — (plan §7)
  - **Dep.**: T005
  - **Hecho cuando**: las pruebas de T004 se ejecutan en los dos celulares y fallan solo porque no existe `web/index.html`.
- [X] T007 Crear el esqueleto de la web: `web/index.html`, `web/config.js`, `web/estilos.css` y `web/js/app.js` (archivos nuevos)
  - `index.html`: `lang="es"`, `meta viewport`, la marca `<h1 data-prueba="marca">PAGO FÁCIL</h1>`, un contenedor de vistas vacío, `config.js` antes de `<script type="module" src="js/app.js">`, y la política en `<meta http-equiv="Content-Security-Policy">` exactamente como R-11: `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; connect-src 'self' http://localhost:8000 https:`.
  - `config.js`: `window.PAGO_FACIL = { servidor: "" };` con un comentario que dice que la cadena vacía es el mismo origen (RF-064).
  - `estilos.css`: base desde 320 px (`box-sizing`, sin anchos fijos mayores a 320 px).
  - `js/app.js`: módulo vacío que lee `window.PAGO_FACIL.servidor`.
  - **RF**: RF-060, RF-064, RF-077
  - **Dep.**: T004, T006
  - **Hecho cuando**: las pruebas de T004 pasan en Chromium y en WebKit.
- [X] T008 [P] Agregar el comando de las pruebas de la web en `AGENTS.md` §6
  - La fila "Pruebas de la web" pasa a `uv run --directory backend pytest ../web -q`, con una nota: "la primera vez, `uv run --directory backend playwright install chromium webkit`".
  - Otra fila, "Lint y formato de las pruebas de la web": `uv run --directory backend ruff check --config pyproject.toml ../web` y `uv run --directory backend ruff format --config pyproject.toml --check ../web` (regla 5).
  - **RF**: — (DP-15, QP-3)
  - **Dep.**: T003
  - **Hecho cuando**: la fila ya no dice "Las define el plan de la primera spec de la web".
- [X] T009 Cierre de F1: pruebas en verde, sección F1 en `specs/002-web-mvp/verification-guide.md` (archivo nuevo) y commit sugerido
  - La guía dice cómo instalar los navegadores, cómo correr las pruebas de la web, qué versión de Playwright se fijó y qué pasó con WebKit en esta Mac (T002).
  - Commit sugerido: `test(002): preparar Playwright, servidor simulado y esqueleto de la web (F1)`.
  - **RF**: —
  - **Dep.**: T007, T008
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F1 existe.

---

## Fase 2 (F2): Base que bloquea (Foundational) · 16–17 nov

**Propósito**: lógica pura (teclado, cuenta regresiva y pagos avisados), uso del servidor para crear y ver, sonido, vibración, pantalla encendida y las vistas Teclado y Generando QR pintadas desde el estado.

**⚠️ Ninguna historia empieza antes de cerrar esta fase.**

- [X] T010 [P] Escribir las pruebas del teclado y de la pintura de las vistas Teclado y Generando QR en `web/tests/test_teclado.py` (archivo nuevo)
  - Lógica pura (`only_browser("chromium")`, con `import("/js/teclado.js")` dentro de `page.evaluate`):
    - `test_el_teclado_escribe_el_monto_con_dos_decimales_como_maximo`: `"25.50"` + `"1"` → `"25.50"`; `"25.5"` + `"punto"` → `"25.5"` (segundo punto); `"25.5"` + `"borrar"` → `"25."`; `""` + `"borrar"` → `""`.
    - `test_el_cero_inicial_se_reemplaza_y_el_punto_inicial_escribe_cero_punto`: `"0"` + `"7"` → `"7"`; `"0"` + `"0"` → `"0"`; `""` + `"punto"` → `"0."`; `"0"` + `"punto"` → `"0."`.
    - `test_no_se_aceptan_mas_de_5_digitos_enteros`: `"12345"` + `"6"` → `"12345"`; `"12345"` + `"punto"` → `"12345."`.
    - `test_cobrar_y_monto_libre_se_activan_segun_el_monto`: `cobrar_activo` es falso con `""`, `"0"`, `"0."` y `"0.00"`, y verdadero con `"0.01"` y `"25."`; `monto_libre_activo` es exactamente lo contrario.
  - Pintura (los dos celulares):
    - `test_la_vista_teclado_muestra_las_teclas_el_monto_y_el_concepto`: al abrir, `vista-teclado` visible con `tecla-0` a `tecla-9`, `tecla-punto`, `tecla-borrar`, `monto` = "$", `concepto` con `maxlength="40"` y `cobrar` desactivado.
    - `test_la_vista_generando_qr_muestra_su_texto`: llamar desde `page.evaluate` a la función de vistas que muestra Generando QR → `vista-generando` visible con "Generando QR…" y `vista-teclado` oculta.
    - `test_teclado_y_generando_caben_en_320_px` (QT-1): con `set_viewport_size({"width": 320, …})`, en las dos vistas `document.documentElement.scrollWidth <= 320` y `marca` visible.
  - **RF**: RF-001, RF-002, RF-003, RF-004, RF-005, RF-006, RF-010, RF-060, RF-061, RF-065, RF-066, RF-067, RF-068
  - **Dep.**: T009
  - **Hecho cuando**: las pruebas existen y fallan porque `web/js/teclado.js` y `web/js/vistas.js` no existen.
- [X] T011 [P] Escribir las pruebas de la cuenta regresiva y de `crear_cobro` en `web/tests/test_crear_y_mostrar_qr.py` (archivo nuevo)
  - Lógica pura de `cuenta.js` (`only_browser("chromium")`):
    - `test_la_cuenta_descuenta_el_desfase_con_el_servidor_en_la_funcion`: cobro con `expira_en = T + 600` y `hora_servidor = T`; con el celular en `T + 300`, `desfase` = −300 y `restante` = 600.
    - `test_si_crear_tardo_9_segundos_la_cuenta_arranca_en_9_51_en_la_funcion`: `creado_en = T`, `hora_servidor = T + 9` → `formato(restante(…))` = "9:51".
    - `test_el_formato_de_la_cuenta_es_minutos_y_segundos`: 600 → "10:00", 591.7 → "9:51" (se trunca), 59 → "0:59", 0 → "0:00", −5 → "0:00".
    - `test_sin_hora_del_servidor_se_usa_el_reloj_del_celular_y_se_avisa`: sin `hora_servidor`, `desfase` = 0 y queda un `console.warn`.
  - `crear_cobro` (`only_browser("chromium")`, contra el servidor simulado):
    - `test_crear_cobro_manda_el_monto_como_numero_y_el_concepto`: el cuerpo recibido es `{"monto": 25.5, "concepto": "Tacos"}` (DP-16) y la ruta es `servidor + "/api/cobros"`.
    - `test_crear_cobro_201_con_imagen_devuelve_el_cobro`.
    - `test_crear_cobro_201_sin_imagen_devuelve_el_mensaje_del_qr`: `qr_imagen: null` → "No se pudo mostrar el QR. Intenta de nuevo.".
    - `test_crear_cobro_rechazado_devuelve_el_detail` (parametrizada con 422, 429, 502 y 503): devuelve el `detail` tal cual.
    - `test_crear_cobro_sin_respuesta_en_15_segundos_devuelve_sin_conexion`: `responder_crear(sin_respuesta=True)`, `reloj(pagina, hora)` y `page.clock.run_for(15_000)` → "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo." ([uso-del-servidor](contracts/uso-del-servidor.md)); a los 14 s todavía no ha resuelto.
    - `test_crear_cobro_con_fallo_de_red_devuelve_sin_conexion`: `page.route("**/api/cobros", lambda r: r.abort())` → el mismo mensaje.
    - `test_la_direccion_del_servidor_sale_de_config_js` (QT-1): `fijar_config('window.PAGO_FACIL = { servidor: "/otro" };')`; `crear_cobro` llega como `POST /otro/api/cobros` en `peticiones`.
    - `test_crear_y_ver_solo_piden_cosas_al_servidor_configurado` (QT-1, CE-010): con `pagina.on("request")`, al crear y ver un cobro toda URL empieza por el origen del simulado.
  - **RF**: RF-009, RF-012, RF-013, RF-018, RF-019, RF-062, RF-063, RF-064, RF-078
  - **Dep.**: T009
  - **Hecho cuando**: las pruebas existen y fallan porque `web/js/cuenta.js` y `web/js/servidor.js` no existen.
- [X] T012 [P] Escribir las pruebas de pagos avisados, sonido y pantalla encendida en `web/tests/test_pago_recibido.py` (archivo nuevo)
  - `avisados.js` (`only_browser("chromium")`):
    - `test_avisados_devuelve_solo_los_pagos_con_numero_mayor_al_ultimo_avisado`: con pagos 1 y 2, `nuevos` devuelve los dos; otra llamada con 1, 2 y 3 devuelve solo el 3; otra igual no devuelve nada.
    - `test_avisados_lleva_la_cuenta_por_cobro`: el pago 1 de otro cobro sí es nuevo.
    - `test_marcar_todos_marca_sin_devolver_pagos`: después de `marcar_todos(cobro con 2 pagos)`, `nuevos` del mismo cobro no devuelve nada.
  - `sonido.js` (los dos celulares):
    - `test_el_sonido_se_desbloquea_con_un_toque_y_despues_suena_sin_otro`: `desbloquear()` reproduce con volumen 0 (no cuenta en `sonidos`); después `sonar()` suma 1 sin otro toque. La fuente del audio empieza por `blob:` (WAV propio, R-7).
    - `test_vibrar_solo_si_el_celular_puede`: en Chromium `vibrar()` llama a `navigator.vibrate` con `[200, 100, 200]`; en WebKit no lanza ningún error.
  - `pantalla.js` (los dos celulares):
    - `test_mantener_encendida_pide_y_suelta_el_bloqueo`: `mantener_encendida(true)` pide una vez aunque se llame dos veces; `mantener_encendida(false)` lo suelta.
    - `test_al_volver_a_la_pagina_se_vuelve_a_pedir_el_bloqueo`: con `mantener_encendida(true)`, un `visibilitychange` a visible vuelve a pedirlo.
    - `test_sin_wake_lock_no_falla`: con `navigator.wakeLock` borrado, no lanza ningún error.
  - **RF**: RF-022, RF-024, RF-025, RF-029, RF-053, RF-058, RF-059
  - **Dep.**: T009
  - **Hecho cuando**: las pruebas existen y fallan porque `web/js/avisados.js`, `web/js/sonido.js` y `web/js/pantalla.js` no existen.
- [X] T013 [P] Escribir las pruebas de `ver_cobro` en `web/tests/test_respaldo.py` (archivo nuevo) y las de `cancelar_cobro` en `web/tests/test_cobros_anteriores.py` (archivo nuevo)
  - Todo `servidor.js` se hace en F2, como dice el plan §8 (QT-4).
  - `ver_cobro`, `only_browser("chromium")`, contra el servidor simulado:
    - `test_ver_cobro_200_devuelve_el_cobro`.
    - `test_ver_cobro_404_dice_que_no_existe`.
    - `test_ver_cobro_con_fallo_de_red_dice_sin_conexion` (con `page.route(…).abort()`).
  - `cancelar_cobro`, `only_browser("chromium")`:
    - `test_cancelar_cobro_200_devuelve_el_cobro`: la petición es `POST servidor + "/api/cobros/{id}/cancelar"`.
    - `test_cancelar_cobro_rechazado_devuelve_el_detail` (parametrizada con 404 y 409).
    - `test_cancelar_cobro_con_fallo_de_red_dice_sin_conexion`: "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.".
  - **RF**: RF-030, RF-033, RF-047, RF-050, RF-056, RF-057
  - **Dep.**: T009
  - **Hecho cuando**: las pruebas existen y fallan porque `ver_cobro` y `cancelar_cobro` no existen.
- [X] T014 [P] Implementar `aplicar_tecla(texto, tecla)`, `cobrar_activo(texto)` y `monto_libre_activo(texto)` en `web/js/teclado.js` (archivo nuevo, puro)
  - Teclas: `"0"` a `"9"`, `"punto"` y `"borrar"`. Reglas: tercer decimal, segundo punto y sexto dígito entero se ignoran; `"0"` + dígito reemplaza el 0; punto con el monto vacío escribe `"0."` (R-13, DP-16). Sin DOM.
  - **RF**: RF-001, RF-003, RF-004, RF-006, RF-065, RF-066, RF-067, RF-068
  - **Dep.**: T010
  - **Hecho cuando**: las pruebas de lógica pura de T010 pasan.
- [X] T015 [P] Implementar `desfase(cobro, ahora)`, `restante(cobro, desfase, ahora)` y `formato(segundos)` en `web/js/cuenta.js` (archivo nuevo, puro)
  - `ahora` en segundos Unix (`Date.now() / 1000`). `desfase = hora_servidor − ahora`; sin `hora_servidor`, 0 y `console.warn` (R-6). `restante = expira_en − (ahora + desfase)`. `formato` trunca y nunca baja de "0:00".
  - **RF**: RF-018, RF-019
  - **Dep.**: T011
  - **Hecho cuando**: las pruebas de `cuenta.js` de T011 pasan.
- [X] T016 [P] Implementar `Avisados` en `web/js/avisados.js` (archivo nuevo, puro)
  - Por cobro, `ultimo_avisado` (0 al empezar). `nuevos(cobro)` devuelve los pagos con `numero` mayor, en orden, y sube `ultimo_avisado`; `marcar_todos(cobro)` lo fija en `numero_de_pagos` sin devolver nada (data-model §3).
  - **RF**: RF-029, RF-053, RF-075
  - **Dep.**: T012
  - **Hecho cuando**: las pruebas de `avisados.js` de T012 pasan.
- [X] T017 [P] Implementar `crear_cobro(monto, concepto)`, `ver_cobro(id)` y `cancelar_cobro(id)` en `web/js/servidor.js` (archivo nuevo)
  - Todas las rutas son `window.PAGO_FACIL.servidor + ruta` (RF-064). Sin cabeceras propias salvo `Content-Type: application/json` al crear.
  - `crear_cobro`: `fetch` con `AbortController` y un `setTimeout` de 15 s (QP-4, nunca `AbortSignal.timeout`). Resultado `{ cobro }` o `{ mensaje }`: 201 con `qr_imagen` → cobro; 201 sin imagen → "No se pudo mostrar el QR. Intenta de nuevo."; 422, 429, 502 o 503 → `detail`; fallo de red o 15 s → "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.". Otro código → el mismo mensaje de conexión.
  - `ver_cobro`: `{ cobro }`, `{ no_existe: true }` (404) o `{ sin_conexion: true }`.
  - `cancelar_cobro`: `POST servidor + "/api/cobros/" + id + "/cancelar"`: 200 → `{ cobro }`; 404 o 409 → `{ mensaje: detail }`; fallo de red u otro código → "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.". Se usa hasta F7 (QT-4).
  - Docstrings (JSDoc) en español con los requisitos.
  - **RF**: RF-009, RF-012, RF-013, RF-030, RF-033, RF-047, RF-050, RF-056, RF-057, RF-062, RF-063, RF-064, RF-078
  - **Dep.**: T011, T013
  - **Hecho cuando**: las pruebas de `crear_cobro` de T011 y todas las de T013 pasan.
- [X] T018 [P] Implementar el sonido y la vibración en `web/js/sonido.js` (archivo nuevo)
  - Al importar, arma en memoria un WAV PCM de unos 0.6 s con dos tonos y lo deja en un `HTMLAudioElement` con `URL.createObjectURL` (R-7, DP-10). `desbloquear()` lo reproduce con volumen 0 y lo detiene; `sonar()` lo reproduce desde el inicio con volumen 1; `vibrar()` llama a `navigator.vibrate([200, 100, 200])` solo si existe (R-8). Ningún error sale de estas funciones.
  - C-5: registrar y devolver el resultado de `play()`. Silenciar el desbloqueo y pausar después de que se inicie. Configurar una sesión `playback` donde esté disponible.
  - **RF**: RF-022, RF-024, RF-025
  - **Dep.**: T012
  - **Hecho cuando**: las pruebas de `sonido.js` de T012 pasan en los dos celulares.
- [X] T019 [P] Implementar `mantener_encendida(si_o_no)` en `web/js/pantalla.js` (archivo nuevo)
  - Pide `navigator.wakeLock.request("screen")` solo si existe y no hay un bloqueo vivo; lo suelta con `release()`; en `visibilitychange` a visible lo vuelve a pedir si debe estar encendida (R-9, DP-11). Errores atrapados y anotados en la consola.
  - **RF**: RF-058, RF-059
  - **Dep.**: T012
  - **Hecho cuando**: las pruebas de `pantalla.js` de T012 pasan en los dos celulares.
- [X] T020 Implementar las vistas Teclado y Generando QR en `web/js/vistas.js` (archivo nuevo) y mostrarlas desde `web/js/app.js`
  - Una función por vista que recibe el estado (data-model §1) y lo pinta solo con `textContent` y atributos fijos (DP-13). Una sola vista visible a la vez. Teclado: las teclas, `monto` como "$" + el texto tecleado, `concepto` con `maxlength="40"`, `cobrar` desactivado según `cobrar_activo` y `mensaje` vacío. Generando QR: "Generando QR…" con un indicador de carga hecho en CSS.
  - `app.js` crea el estado inicial y muestra la vista Teclado al cargar.
  - **RF**: RF-001, RF-002, RF-005, RF-006, RF-010, RF-060, RF-077
  - **Dep.**: T010, T014
  - **Hecho cuando**: las pruebas de pintura de T010 pasan en los dos celulares.
- [X] T021 Cierre de F2: pruebas en verde, sección F2 en `verification-guide.md` y commit sugerido
  - La guía dice cómo ver la vista Teclado en local (quickstart §3) y cómo comprobar en la consola del navegador que el sonido se genera sin archivo.
  - Commit sugerido: `feat(002): lógica pura, uso del servidor, sonido y vistas base de la web (F2)`.
  - **RF**: —
  - **Dep.**: T014 a T020
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F2 existe.

---

## Fase 3 (F3): Historias 1 y 2 — Teclear el monto, generar y enseñar el QR (P1) · Corte 1 🎯 MVP · 17 nov

**Objetivo**: el dueño teclea el monto, pulsa Cobrar y ve el QR con el monto, el concepto, la indicación de CoDi y una cuenta regresiva que sigue la hora del servidor; los errores vuelven al teclado sin perder lo escrito.

**Prueba independiente**: con el servidor simulado, teclear 25.50, escribir "Tacos", pulsar Cobrar y ver la vista QR con "$25.50", "Tacos", la indicación de CoDi y "10:00" en los dos celulares.

### Pruebas de las historias 1 y 2 (primero, deben fallar antes de implementar)

- [X] T022 [P] [US1] Escribir las pruebas del teclado en pantalla en `web/tests/test_teclado.py`
  - `test_teclear_25_50_muestra_el_monto_en_grande` (escenario 1): tocar 2, 5, punto, 5 y 0 → `monto` = "$25.50".
  - `test_el_teclado_en_pantalla_ignora_el_tercer_decimal_y_borra` (escenarios 2 y 3): otro dígito deja "$25.50"; desde "$25.5", borrar deja "$25.".
  - `test_el_teclado_en_pantalla_reemplaza_el_cero_y_escribe_cero_punto` (escenario 10): 0 y 7 → "$7"; punto como primera tecla → "$0.".
  - `test_el_teclado_en_pantalla_no_acepta_un_sexto_digito_entero` (escenario 11).
  - `test_el_concepto_acepta_como_maximo_40_caracteres`: al escribir 45 caracteres con `press_sequentially` (no con `fill`, que no se comporta como el teclado del celular) quedan 40.
  - `test_cobrar_esta_desactivado_sin_monto` (escenario 4): desactivado con "$" y con "$0."; activo con "$0.01".
  - **RF**: RF-001, RF-002, RF-003, RF-004, RF-005, RF-006, RF-066, RF-067, RF-068
  - **Dep.**: T021
  - **Hecho cuando**: las pruebas existen y fallan porque las teclas todavía no hacen nada.
- [X] T023 [P] [US1] Escribir las pruebas de crear el cobro en pantalla en `web/tests/test_crear_y_mostrar_qr.py`
  - `test_cobrar_pide_el_cobro_y_muestra_el_qr_con_monto_concepto_e_indicacion_codi`: el simulado recibe `{"monto": 25.5, "concepto": "Tacos"}`; vista QR con `qr` (`src` empieza por `data:image/png;base64,`), `qr-monto` = "$25.50", `qr-concepto` = "Tacos" e `indicacion-codi` = "Escanéalo desde la app de tu banco, en la opción CoDi".
  - `test_al_pulsar_cobrar_aparece_generando_qr_y_un_segundo_toque_no_crea_otro_cobro`: con `responder_crear(demora=2)`, `vista-generando` aparece en menos de 0.1 s después del toque, medido dentro de la página con `performance.now()` entre el `pointerdown` de `cobrar` y un `MutationObserver` sobre `vista-generando` (CE-005); un segundo toque no agrega otro `POST /api/cobros` a `peticiones`.
  - `test_si_el_servidor_rechaza_el_cobro_se_ve_su_mensaje_y_se_conserva_lo_escrito` (parametrizada con 422, 429, 502 y 503, cada una con su `detail` real de la 001, p. ej. "El monto máximo de la demo es $100"): vuelve `vista-teclado` con `mensaje` = el `detail`, sin el número del código, y `monto` y `concepto` como estaban.
  - `test_sin_conexion_se_pide_revisar_la_conexion_y_se_conserva_lo_escrito`: dos casos, el simulado sin respuesta con `page.clock.run_for(15_000)` y `page.route(…).abort()`; `mensaje` = "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.".
  - `test_si_el_qr_llega_sin_imagen_se_vuelve_al_teclado_con_mensaje` (escenario 12): `mensaje` = "No se pudo mostrar el QR. Intenta de nuevo.", lo escrito se conserva y no hay ningún `GET …/eventos` en `peticiones`.
  - `test_el_mensaje_de_error_se_borra_al_teclear`: tras un 422, tocar una tecla deja `mensaje` vacío ([vistas](contracts/vistas.md)).
  - `test_el_concepto_y_el_mensaje_del_servidor_se_muestran_como_texto` (QT-1, CE-015): concepto `<script>alert(1)</script>` en la vista QR y un 422 con `detail` `<img src=x onerror=alert(1)>` en el mensaje: se ven tal cual, no hay ningún `dialog` y no aparecen elementos `script` ni `img` nuevos dentro de las vistas.
  - `test_la_vista_qr_cabe_en_320_px` (QT-1, CE-007): con 320 px de ancho, `scrollWidth <= 320`, `marca` visible y el ancho de `qr` al menos el 70 % del de la página.
  - **RF**: RF-009, RF-010, RF-011, RF-012, RF-013, RF-014, RF-015, RF-016, RF-017, RF-060, RF-061, RF-062, RF-077, RF-078
  - **Dep.**: T021
  - **Hecho cuando**: las pruebas existen y fallan porque Cobrar todavía no pide nada.
- [X] T024 [US2] Escribir las pruebas de la cuenta regresiva en pantalla en `web/tests/test_crear_y_mostrar_qr.py`
  - `test_un_cobro_recien_creado_muestra_la_cuenta_en_10_00` (escenario 1): `hora_servidor = creado_en`, `cuenta` = "10:00".
  - `test_la_cuenta_regresiva_sigue_la_hora_del_servidor_aunque_el_celular_este_desfasado` (escenario 2, CE-009): `reloj(pagina, hora)` con el celular 5 minutos adelantado respecto a `hora_servidor`; `cuenta` empieza entre "10:00" y "9:58".
  - `test_si_crear_tardo_9_segundos_la_cuenta_arranca_en_9_51` (CE-016): `hora_servidor = creado_en + 9`; `cuenta` entre "9:51" y "9:49".
  - `test_la_cuenta_regresiva_baja_con_el_tiempo`: `page.clock.run_for(61_000)` → "8:59" (con 1 s de margen).
  - **RF**: RF-018, RF-019
  - **Dep.**: T023
  - **Hecho cuando**: las pruebas existen y fallan porque la vista QR no tiene cuenta regresiva.

### Implementación de las historias 1 y 2

- [X] T025 [US1] Conectar el teclado y el concepto en `web/js/app.js`
  - Cada `tecla-*` aplica `aplicar_tecla` al estado y vuelve a pintar; `concepto` guarda lo escrito; `cobrar` se activa con `cobrar_activo`. Tocar una tecla borra `mensaje`.
  - **RF**: RF-001, RF-002, RF-003, RF-004, RF-005, RF-006, RF-066, RF-067, RF-068
  - **Dep.**: T022
  - **Hecho cuando**: las pruebas de T022 pasan en los dos celulares.
- [X] T026 [US1] Implementar el toque a Cobrar en `web/js/app.js` y el mensaje de la vista Teclado en `web/js/vistas.js`
  - Al tocar `cobrar` con `accion_en_curso` vacía: `desbloquear()` del sonido (RF-025), `accion_en_curso = "creando"`, vista Generando QR en el mismo manejador (sin esperar nada) y `crear_cobro(Number(monto), concepto)`. Con `accion_en_curso` ocupada, el toque se ignora.
  - Con `{ cobro }`: guarda el cobro, `en_pantalla = cobro.id` y muestra la vista QR. Con `{ mensaje }`: vista Teclado con `mensaje`, `monto` y `concepto` intactos. En los dos casos `accion_en_curso` vuelve a vacía.
  - **RF**: RF-009, RF-010, RF-011, RF-012, RF-013, RF-014, RF-025, RF-062, RF-078
  - **Dep.**: T023, T025
  - **Hecho cuando**: las pruebas de T023 sobre Generando QR, doble toque, rechazos, conexión, imagen vacía y mensaje pasan.
- [X] T027 [US2] Implementar la vista QR en `web/js/vistas.js`, su cuenta regresiva en `web/js/app.js` y su diseño en `web/estilos.css`
  - Vista QR: `qr` con `src = "data:image/png;base64," + qr_imagen` (solo ese prefijo), `qr-monto` = "$" + `monto.toFixed(2)`, `qr-concepto` con `textContent`, `indicacion-codi` siempre visible y `cuenta`.
  - Cuenta: al recibir el cobro se calcula `desfase` y un `setInterval` de 250 ms pinta `formato(restante(…))` (DP-8).
  - `estilos.css`: `qr` con al menos el 70 % del ancho e `image-rendering: pixelated` (CE-007).
  - **RF**: RF-015, RF-016, RF-017, RF-018, RF-019, RF-077
  - **Dep.**: T024, T026
  - **Hecho cuando**: todas las pruebas de T023 y T024 pasan en los dos celulares.
- [X] T028 [US2] Cierre de F3: pruebas en verde, sección F3 en `verification-guide.md` y commit sugerido
  - La guía dice cómo crear un cobro de $0.01 en local contra el servidor real (quickstart §3) y comprobar el QR y la cuenta. Sin pagarlo todavía.
  - Commit sugerido: `feat(002): teclado, crear el cobro y mostrar el QR con cuenta regresiva (F3)`.
  - **RF**: —
  - **Dep.**: T025, T026, T027
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F3 existe.

**Punto de control**: las historias 1 y 2 funcionan solas: el QR se genera y se enseña.

---

## Fase 4 (F4): Historias 3 y 4 — Oír que me pagaron y no perder el aviso (P1) · Corte 1 · 17–18 nov

**Objetivo**: con la vista QR abierta, cada pago nuevo suena, vibra y pone la pantalla verde; si el canal se corta, la consulta cada 3 s lo descubre igual y se ve "Reconectando…".

**Prueba independiente**: el simulado emite un `pago` y en menos de 2 s se ve `vista-pagado` con un sonido; con el canal cortado, la consulta descubre el pago tras 3 s de reloj controlado.

### Pruebas de las historias 3 y 4 (primero, deben fallar antes de implementar)

- [X] T029 [P] [US3] Escribir las pruebas del aviso de pago en `web/tests/test_pago_recibido.py`
  - `test_al_mostrar_el_qr_se_abre_el_canal_del_cobro`: `GET /api/cobros/{id}/eventos` aparece en `peticiones` después de la vista QR.
  - `test_un_pago_suena_vibra_y_pone_la_pantalla_verde_sin_tocar_nada_despues_de_cobrar` (escenarios 1 y 2, CE-002): sin otro toque después de Cobrar, antes del evento no hay `vista-pagado`; `agregar_pago(id, 25.5)` → `vista-pagado` con `pagado` = "Pago recibido", `pagado-monto` = "$25.50" y `pagado-concepto` = "Tacos"; `sonidos` = 1; `vibraciones` = 1 en Chromium. El tiempo entre `agregar_pago` y la vista, medido con `time.perf_counter()` de Python, es menor a 2 s (QP-4).
  - `test_pago_recibido_se_queda_varios_minutos` (escenario 3): con `reloj(pagina, hora)`, `run_for(5 * 60_000)` y la vista sigue en Pago recibido.
  - `test_un_segundo_pago_al_mismo_qr_vuelve_a_sonar` (escenario 4): segundo `agregar_pago(id, 10)` → `sonidos` = 2 y `pagado-monto` = "$10.00".
  - `test_un_monto_distinto_muestra_el_pedido_y_el_recibido` (escenario 6): cobro de $25.50 y pago de $20.00 con `monto_distinto=True` → `pagado-distinto` muestra "$25.50" y "$20.00"; con `monto_distinto=False` no aparece.
  - `test_el_mismo_pago_por_canal_reconexion_y_consulta_suena_una_sola_vez` (escenario 7, CE-008; QT-2): con `reloj(pagina, hora)`, el pago 1 llega por `pago`; `cortar_canal(id, rechazar_con=503)` deja el canal `CLOSED`; `run_for(3_000)` y la consulta trae el mismo pago; `permitir_canal(id)` y `run_for(15_000)` abren otro canal cuyo `estado` lo trae otra vez → `sonidos` = 1. Pasa cuando existe el respaldo (T033).
  - `test_la_pantalla_pide_no_apagarse_mientras_hay_un_cobro_en_escucha` (escenario 8): `bloqueos_pedidos` = 1 tras la vista QR.
  - `test_el_concepto_en_pago_recibido_se_muestra_como_texto` (QT-1, CE-015): con el concepto `<script>alert(1)</script>`, `pagado-concepto` lo muestra tal cual, sin `dialog` ni elementos `script` nuevos.
  - `test_pago_recibido_cabe_en_320_px` (QT-1): con 320 px de ancho, `scrollWidth <= 320` y `marca` visible.
  - **RF**: RF-020, RF-021, RF-022, RF-023, RF-024, RF-025, RF-026, RF-028, RF-029, RF-058, RF-060, RF-061, RF-077
  - **Dep.**: T028
  - **Hecho cuando**: las pruebas existen y fallan porque no hay escucha.
- [X] T030 [P] [US4] Escribir las pruebas del respaldo en `web/tests/test_respaldo.py`
  - `test_con_el_canal_cortado_la_consulta_cada_3_segundos_avisa_el_pago` (escenario 1, CE-003): con `reloj(pagina, hora)`, `cortar_canal(id, rechazar_con=503)` y se ve `reconectando`; `agregar_pago(id, 25.5, avisar=False)`; `run_for(3_000)` → `vista-pagado` y `sonidos` = 1. El tiempo real desde el pago, medido con Python, es menor a 3 s, así que el total queda por debajo de 6 s.
  - `test_mientras_el_canal_esta_cortado_se_ve_reconectando_sin_quitar_el_qr` (escenario 3): `reconectando` = "Reconectando…" y `qr` sigue visible.
  - `test_al_volver_el_canal_se_consulta_a_los_8_segundos_y_se_quita_reconectando` (escenario 2, QT-2, C-4): después de la reapertura se quita «Reconectando…» y se pasa al intervalo de 8 s.
  - `test_si_el_servidor_rechaza_el_canal_se_sigue_con_la_consulta` (escenario 4): `cortar_canal(id, rechazar_con=429)`; las consultas siguen cada 3 s; `permitir_canal(id)` y `run_for(15_000)` → se pide `…/eventos` otra vez (reintento cada 15 s, R-5).
  - `test_si_la_consulta_falla_por_red_se_reintenta_en_3_segundos`: con el canal cortado y la consulta abortada, `reconectando` sigue y `run_for(3_000)` vuelve a consultar.
  - C-4: con un canal abierto y mudo, el GET de los 8 s muestra el pago y suena. Con el canal activo, el GET no vuelve a avisar el pago. Cubrir un GET pendiente al cortar y reabrir el canal, un evento atrasado y la última consulta de la ventana.
  - **RF**: RF-030, RF-031, RF-032, RF-033, RF-034
  - **Dep.**: T028
  - **Hecho cuando**: las pruebas existen y fallan porque no hay respaldo.

### Implementación de las historias 3 y 4

- [X] T031 [US3] Implementar `Escucha` (canal y eventos `estado` y `pago`) y `Escuchas` (cobro en pantalla) en `web/js/escucha.js` (archivo nuevo)
  - `Escucha(id, cobro, con_canal)`: abre `EventSource(servidor + "/api/cobros/" + id + "/eventos")`; en `estado` y `pago` actualiza `cobro` y `desfase` y lo entrega a `Escuchas`. Campos de data-model §2 (`canal` en `abriendo` o `abierto`).
  - `Escuchas`: guarda las escuchas y un `Avisados`. Con cada cobro recibido, `avisados.nuevos(cobro)`; por cada pago nuevo del cobro en pantalla, `sonar()`, `vibrar()` y vista Pago recibido con ese pago (solo lo que trae el servidor, RF-021). En el corte 1 solo existe la escucha del cobro en pantalla. Pide `mantener_encendida(true)` al empezar la primera escucha.
  - Deja en la consola los cambios de la escucha (abierto, cortado, consulta, `fin`) con el id del cobro y sin datos bancarios (principio X).
  - **RF**: RF-020, RF-021, RF-022, RF-023, RF-024, RF-029, RF-058
  - **Dep.**: T029
  - **Hecho cuando**: las pruebas de T029 sobre el canal, el pago, el segundo pago y la pantalla encendida pasan (la de CE-008 pasa con T033, porque usa el reintento).
- [X] T032 [US3] Implementar la vista Pago recibido en `web/js/vistas.js` y `web/estilos.css`, y empezar la escucha desde `web/js/app.js`
  - `vista-pagado` a pantalla completa en verde con `pagado`, `pagado-monto` (monto recibido del último pago), `pagado-concepto` y `pagado-distinto` solo si el pago trae `monto_distinto` (monto pedido y recibido). La vista solo cambia con Nuevo cobro (F5) o con otro pago.
  - `app.js`: al mostrar la vista QR empieza la escucha del cobro en pantalla.
  - **RF**: RF-020, RF-023, RF-026, RF-028, RF-077
  - **Dep.**: T031
  - **Hecho cuando**: todas las pruebas de T029 pasan en los dos celulares.
- [X] T033 [US4] Implementar el respaldo de `Escucha` en `web/js/escucha.js` y el aviso "Reconectando…" en `web/js/vistas.js`
  - En `error`: `canal = "cortado"`, consulta con `ver_cobro` cada 3 s (`setTimeout`), aviso `reconectando` si es el cobro en pantalla. Cada consulta con `{ cobro }` se trata igual que un evento (RF-033); con `{ sin_conexion }` se reintenta en 3 s.
  - En `open`: `canal = "abierto"`, se cambia al intervalo de 8 s y se quita el aviso. Una sola consulta en curso por cobro, incluso si cambia el estado del canal (C-4, RF-079).
  - Si el `EventSource` queda `CLOSED` y la consulta da 200, se intenta abrir otro cada 15 s (R-5, DP-9).
  - **RF**: RF-030, RF-031, RF-032, RF-033, RF-034
  - **Dep.**: T030, T032
  - **Hecho cuando**: todas las pruebas de T030 y de T029 pasan, incluida la de CE-008.
- [X] T034 [US4] Cierre de F4: pruebas en verde, sección F4 en `verification-guide.md`, prueba del silencio en el iPhone y commit sugerido
  - C-5: en `test_pago_recibido.py`, simular el rechazo de `play()`, comprobar el aviso y el reintento al tocar, el desbloqueo tras volver a la página y la sesión de audio opcional.
  - Reconexión automática del navegador (QT-2), a mano: con un cobro en la vista QR, activar y quitar el modo avión del celular; esperado: aparece y desaparece "Reconectando…" y un pago posterior se avisa.
  - Con la web servida en la red local (quickstart §3 con la IP de la Mac en lugar de `localhost`) y un cobro del servidor simulado o de $0.01 real con autorización de Hugo: poner el iPhone en silencio, provocar un pago y anotar si suena como TK en el plan §14 (riesgo R-7).
  - Commit sugerido: `feat(002): aviso de pago con sonido, vibración y respaldo del canal (F4)`.
  - **RF**: RF-022, RF-025, RF-031, RF-032
  - **Dep.**: T031, T032, T033
  - **Hecho cuando**: los comandos de la regla 5 dan verde, la sección F4 existe y el resultado del silencio está anotado como TK.

**Punto de control**: el momento del pago funciona solo, también con el canal cortado.

---

## Fase 5 (F5): Historias 5 y 6 — QR vencido, pagos tardíos y Nuevo cobro (P2) · Corte 1 · cierre del corte 1 · 18–19 nov

**Objetivo**: el QR vencido se oculta y los pagos tardíos se avisan; la escucha termina con `fin`; Nuevo cobro vuelve al teclado; un cobro que el servidor ya no conoce lleva a la vista Error; la web cabe en 320 px y solo habla con el servidor configurado.

**Prueba independiente**: con reloj controlado, dejar pasar 10 minutos, ver QR vencido y avisar un pago 5 minutos tarde; pulsar Nuevo cobro desde cada vista.

### Pruebas de las historias 5 y 6 (primero, deben fallar antes de implementar)

- [X] T035 [P] [US5] Escribir las pruebas del vencimiento y del fin de la escucha en `web/tests/test_vencido_y_nuevo.py` (archivo nuevo)
  - Todas con `reloj(pagina, hora)`.
  - `test_al_vencer_se_oculta_el_qr_y_se_ve_qr_vencido` (escenario 1, dos casos): la cuenta llega a "0:00" con `run_for(600_000)`, y el simulado emite `vencido`. En los dos: `vista-vencido` con `vencido` = "QR vencido", sin `qr`, `vencido-monto` = "$25.50" y `vencido-concepto` = "Tacos".
  - `test_qr_vencido_dice_que_aun_se_avisa_el_pago` (escenario 2): `vencido-espera` = "Si el cliente ya pagó, aquí te avisamos".
  - `test_un_pago_tardio_con_qr_vencido_suena_y_se_muestra` (escenario 3, CE-012): 5 minutos después del vencimiento (`run_for(300_000)`), `agregar_pago` → `vista-pagado` y `sonidos` = 1.
  - `test_un_cobro_con_pagos_no_pasa_a_qr_vencido`: con un pago, al llegar a "0:00" se queda en Pago recibido (RF-035 solo para cobros sin pagos).
  - `test_al_recibir_fin_se_cierra_el_canal_y_no_se_reconecta` (escenario 4): `emitir(id, "fin", cobro)` → `canales(pagina)` muestra ese canal `CLOSED` y, con `run_for(20_000)`, no hay más peticiones de ese cobro.
  - `test_al_terminar_la_ventana_desaparece_el_aviso_de_espera`: en QR vencido, tras `fin`, `vencido-espera` ya no se ve.
  - `test_si_la_consulta_muestra_que_paso_fin_ventana_termina_la_escucha`: con el canal cortado, la consulta trae `hora_servidor ≥ fin_ventana` → se deja de consultar.
  - `test_el_concepto_en_qr_vencido_se_muestra_como_texto` (QT-1): `vencido-concepto` muestra `<script>alert(1)</script>` tal cual.
  - `test_qr_vencido_cabe_en_320_px` (QT-1): con 320 px de ancho, `scrollWidth <= 320` y `marca` visible.
  - **RF**: RF-035, RF-036, RF-037, RF-038, RF-039, RF-040, RF-060, RF-061, RF-077
  - **Dep.**: T034
  - **Hecho cuando**: las pruebas existen y fallan porque no hay vista QR vencido ni fin de escucha.
- [X] T036 [US6] Escribir las pruebas de Nuevo cobro y de la vista Error en `web/tests/test_vencido_y_nuevo.py`
  - `test_nuevo_cobro_vuelve_al_teclado_vacio_desde_cada_vista` (parametrizada con QR, QR vencido, Pago recibido y Error; escenario 1): `nuevo-cobro` visible; al tocarlo, `vista-teclado` con `monto` = "$" y `concepto` vacío.
  - `test_en_el_corte_1_nuevo_cobro_deja_de_escuchar_el_cobro`: tras Nuevo cobro, `canales(pagina)` muestra el canal de ese cobro `CLOSED` y un `agregar_pago` no suena (comportamiento temporal de §1.2; T049 lo reemplaza).
  - `test_si_el_servidor_ya_no_conoce_el_cobro_se_ve_la_vista_error`: `olvidar(id)` y `cortar_canal(id, rechazar_con=404)`; la consulta da 404 → `vista-error` con `error` = "Este cobro ya no se puede seguir. Revisa la app de tu banco para confirmar si llegó el pago.".
  - `test_al_dejar_de_haber_cobros_en_escucha_se_suelta_la_pantalla`: tras `fin`, y en otra prueba tras Nuevo cobro, `bloqueos_soltados` = 1.
  - `test_la_vista_error_cabe_en_320_px` (QT-1): con 320 px de ancho, `scrollWidth <= 320` y `marca` visible.
  - **RF**: RF-040, RF-041, RF-042, RF-057, RF-059, RF-060, RF-061
  - **Dep.**: T035
  - **Hecho cuando**: las pruebas existen y fallan porque no hay Nuevo cobro ni vista Error.
- [X] T037 [US2] Escribir la revisión conjunta de 320 px en `web/tests/test_seguridad.py`
  - Cada vista ya se midió en su tarea de pruebas (QT-1); esta prueba recorre el flujo completo de una vez.
  - `test_todas_las_vistas_caben_en_320_px_y_muestran_pago_facil`: con `set_viewport_size({"width": 320, …})`, en cada vista (Teclado, Generando QR, QR, QR vencido, Pago recibido y Error) `document.documentElement.scrollWidth <= 320` y `marca` visible; en la vista QR, el ancho de `qr` es al menos el 70 % del ancho de la página (CE-007).
  - **RF**: RF-060, RF-061
  - **Dep.**: T036
  - **Hecho cuando**: la prueba existe y falla porque el flujo completo usa Nuevo cobro, que todavía no existe.
- [X] T038 [US1] Escribir la revisión conjunta de seguridad del corte 1 en `web/tests/test_seguridad.py`
  - La dirección de `config.js` y el texto del concepto y del `detail` ya se probaron en T011, T023, T029 y T035 (QT-1); esta prueba recorre el flujo completo de una vez.
  - `test_la_web_solo_pide_cosas_al_servidor_configurado` (CE-010): con `pagina.on("request")`, durante crear, pagar, cortar el canal, consultar, vencer, Nuevo cobro y la vista Error, toda URL empieza por el origen del simulado.
  - **RF**: RF-063
  - **Dep.**: T037
  - **Hecho cuando**: la prueba existe y falla porque el flujo completo usa Nuevo cobro, que todavía no existe.

### Implementación de las historias 5 y 6

- [X] T039 [US5] Implementar el vencimiento y el fin de la escucha en `web/js/escucha.js`, `web/js/vistas.js` y `web/js/app.js`
  - `Escucha`: en `vencido`, avisa a `Escuchas`; en `fin`, `close()`, detiene la consulta y el reintento, y termina; si una consulta trae `hora_servidor ≥ fin_ventana`, termina igual (RF-040); un 404 en la consulta del cobro en pantalla avisa a `Escuchas` para la vista Error (RF-057).
  - Vista QR vencido: `vencido`, `vencido-monto`, `vencido-concepto` y `vencido-espera` solo mientras la escucha siga viva; sin imagen del QR.
  - `app.js`: cuando la cuenta llega a 0 o llega `vencido`, si el cobro en pantalla no tiene pagos, vista QR vencido. Los pagos tardíos siguen el camino normal de `Escuchas` (RF-039).
  - **RF**: RF-035, RF-036, RF-037, RF-038, RF-039, RF-040, RF-057, RF-077
  - **Dep.**: T035
  - **Hecho cuando**: las pruebas de T035 pasan en los dos celulares.
- [X] T040 [US6] Implementar Nuevo cobro y la vista Error en `web/js/vistas.js`, `web/js/app.js` y `web/js/escucha.js`
  - `nuevo-cobro` en las vistas QR, QR vencido, Pago recibido y Error. Al tocarlo: termina la escucha del cobro en pantalla (corte 1), `en_pantalla = null`, `monto = ""`, `concepto = ""` y vista Teclado.
  - Vista Error con `error` y el texto de RF-057.
  - `Escuchas` llama a `mantener_encendida(false)` cuando no queda ninguna escucha.
  - **RF**: RF-041, RF-042, RF-057, RF-059
  - **Dep.**: T036, T039
  - **Hecho cuando**: las pruebas de T036 pasan en los dos celulares.
- [X] T041 [US2] Ajustar `web/estilos.css` (y lo que haga falta en `web/js/vistas.js`) para 320 px y para la seguridad del corte 1
  - Ningún elemento más ancho que la página; teclas y botones con al menos 44 px de alto (principio VII); textos largos del concepto con `overflow-wrap: anywhere`.
  - **RF**: RF-061, RF-063
  - **Dep.**: T037, T038, T040
  - **Hecho cuando**: las pruebas de T037 y T038 pasan en los dos celulares.
- [X] T042 [US1] Revisión de seguridad del corte 1 en la sección F5 de `verification-guide.md`
  - Secretos (CE-010): `git grep -nE "whsec_|Bearer |PEY_API_KEY|PEY_WEBHOOK_SECRET|pey\.mx" -- web`; esperado: nada.
  - Textos de fuera (RF-077): `git grep -n "innerHTML\|outerHTML\|insertAdjacentHTML\|document.write" -- web/js`; esperado: nada.
  - Política de seguridad de contenido: la de `web/index.html` es exactamente la de R-11.
  - Pagos solo del servidor (principio I, RF-021): ninguna ruta del código marca un pago sin un evento o un objeto cobro del servidor (revisión de `escucha.js` y `app.js`).
  - Abuso: Cobrar se bloquea mientras se crea y la web no reintenta crear un cobro sola (RF-011).
  - **RF**: RF-011, RF-021, RF-063, RF-077
  - **Dep.**: T041
  - **Hecho cuando**: cada punto tiene su resultado anotado.
- [X] T043 [US6] Cierre de F5 y del corte 1: pruebas en verde, sección F5 completa en `verification-guide.md`, pagos reales y commit sugerido
  - Requiere: C-2 aplicado en la 001 (si el nombre del campo cambió, ajustar `cuenta.js`, `servidor_simulado.py` y el contrato de uso del servidor antes de cerrar), la web publicada con HTTPS (#65) y CoDi activo.
  - Con autorización de Hugo en ese momento: quickstart §5 en un Android con Chrome y en un iPhone con Safari (CE-001, CE-004 y CE-006, con el tiempo del QR medido sin contar el primer cobro) y quickstart §6 en el Android (CE-011).
  - Si a las 23:59 del 19 nov falta #65 o CoDi, se anota en Estado y el corte 1 queda cerrado en código, con los pagos reales pendientes.
  - Commit sugerido: `feat(002): QR vencido, pagos tardíos, Nuevo cobro y seguridad; cierre del corte 1 (F5)`.
  - **RF**: RF-019, RF-025, RF-058; CE-001, CE-004, CE-006, CE-011
  - **Dep.**: T039, T040, T041, T042
  - **Hecho cuando**: los comandos de la regla 5 dan verde, la sección F5 tiene los resultados reales (o el motivo de que estén pendientes) y Hugo puede seguirla sin otra explicación.

**Punto de control**: el corte 1 está completo: monto → QR → pago desde el banco → sonido y "Pago recibido".

---

## Fase 6 (F6): Historias 1 y 3 — Monto libre, "Pago n" y Mostrar QR otra vez (P1) · Corte 2 · 20 nov

**Objetivo**: la tecla Monto libre crea un QR sin monto; desde el segundo pago se ven el número de pago y el total; mientras el QR siga vigente se puede volver a mostrar.

**Prueba independiente**: con el monto vacío, Monto libre crea un QR "Monto libre"; dos pagos muestran "Pago 2" y el total; Mostrar QR otra vez vuelve al QR y, al vencer, regresa a Pago recibido.

### Pruebas (primero, deben fallar antes de implementar)

- [X] T044 [US1] Escribir las pruebas de Monto libre en `web/tests/test_monto_libre_y_reuso.py` (archivo nuevo)
  - `test_monto_libre_solo_esta_activo_sin_monto_y_crea_un_cobro_sin_monto` (escenarios 8 y 9): `monto-libre` activo con "$" y "$0.", desactivado con "$25.50"; con el concepto "Propina", el simulado recibe `{"monto": null, "concepto": "Propina"}` y la vista QR muestra `qr-monto` = "Monto libre" y `qr-concepto` = "Propina".
  - `test_mientras_se_crea_un_monto_libre_se_ignoran_otros_toques`: con `demora=2`, un segundo toque a Monto libre o a Cobrar no agrega otro `POST`.
  - `test_un_monto_libre_vencido_muestra_monto_libre`: en QR vencido, `vencido-monto` = "Monto libre".
  - `test_un_monto_libre_pagado_muestra_lo_que_pago_el_cliente_sin_monto_distinto`: pago de $12.00 → `pagado-monto` = "$12.00" y no aparece `pagado-distinto`.
  - **RF**: RF-007, RF-008, RF-011, RF-016, RF-023, RF-037, RF-065
  - **Dep.**: T043
  - **Hecho cuando**: las pruebas existen y fallan porque no hay tecla Monto libre.
- [X] T045 [US3] Escribir las pruebas de "Pago n" y Mostrar QR otra vez en `web/tests/test_monto_libre_y_reuso.py`
  - `test_el_segundo_pago_muestra_pago_2_y_el_total` (escenario 5): con un pago no aparecen `pagado-numero` ni `pagado-total`; con el segundo, `pagado-numero` = "Pago 2" y `pagado-total` contiene "$35.50" (25.50 + 10).
  - `test_mostrar_qr_otra_vez_vuelve_al_qr_mientras_siga_vigente` (escenario 9): `mostrar-qr` visible dentro de la vigencia; al tocarlo, vista QR del mismo cobro con su `cuenta`; después de la vigencia, `mostrar-qr` no aparece.
  - `test_si_el_qr_que_se_volvio_a_mostrar_vence_vuelve_pago_recibido`: con `reloj(pagina, hora)` y el QR reabierto, `run_for` hasta "0:00" → `vista-pagado`, no `vista-vencido`.
  - `test_un_pago_con_el_qr_reabierto_suena_y_vuelve_a_pago_recibido`: con el QR reabierto, `agregar_pago` → `vista-pagado` con "Pago 2" y `sonidos` = 2.
  - **RF**: RF-026, RF-027, RF-069, RF-070, RF-071
  - **Dep.**: T044
  - **Hecho cuando**: las pruebas existen y fallan porque no hay número de pago ni botón.

### Implementación

- [X] T046 [US1] Implementar Monto libre en `web/js/vistas.js` y `web/js/app.js`
  - `monto-libre` en la vista Teclado, separado de Cobrar y activo según `monto_libre_activo`. Al tocarlo, el mismo camino que Cobrar con `crear_cobro(null, concepto)` y el mismo bloqueo de `accion_en_curso` (RF-011). En las vistas QR y QR vencido, `monto_libre: true` muestra "Monto libre".
  - **RF**: RF-007, RF-008, RF-011, RF-016, RF-037, RF-065
  - **Dep.**: T044
  - **Hecho cuando**: las pruebas de T044 pasan en los dos celulares.
- [X] T047 [US3] Implementar "Pago n", el total y Mostrar QR otra vez en `web/js/vistas.js` y `web/js/app.js`
  - Desde el segundo pago: `pagado-numero` = "Pago " + número y `pagado-total` con `total_recibido`.
  - `mostrar-qr` solo mientras `restante > 0`; al tocarlo, `qr_reabierto = true` y vista QR del mismo cobro. Si la cuenta llega a 0 con `qr_reabierto`, vuelve Pago recibido (data-model §1). Un pago nuevo vuelve a Pago recibido y pone `qr_reabierto = false`.
  - **RF**: RF-026, RF-027, RF-069, RF-070, RF-071
  - **Dep.**: T045, T046
  - **Hecho cuando**: las pruebas de T045 pasan y todas las anteriores siguen en verde.
- [X] T048 [US3] Cierre de F6: pruebas en verde, sección F6 en `verification-guide.md`, pago real de monto libre y commit sugerido
  - Con autorización de Hugo: quickstart §7, "Monto libre", con un pago real de $0.01; y un segundo pago de $0.01 al mismo QR para ver "Pago 2".
  - Commit sugerido: `feat(002): monto libre, número de pago y mostrar el QR otra vez (F6)`.
  - **RF**: RF-008, RF-027
  - **Dep.**: T046, T047
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F6 tiene el resultado real (o el motivo de que esté pendiente).

---

## Fase 7 (F7): Historias 6 y 7 — Cobros anteriores y Cancelar cobro (P2) · Corte 2 · 20 nov

**Objetivo**: Nuevo cobro y la cancelación dejan el cobro como anterior y se sigue escuchando hasta el fin de su ventana, con máximo 3 canales por pantalla; Cancelar cobro funciona con "Cancelando…", sus rechazos y el `cancelado` de otra pantalla.

**Prueba independiente**: crear un cobro, pulsar Nuevo cobro, teclear otro monto y pagar el anterior: suena y aparece su aviso sin borrar lo tecleado; crear otro, cancelarlo y pagarlo: suena y aparece su aviso.

### Pruebas (primero, deben fallar antes de implementar)

- [X] T049 [US6] Escribir las pruebas de cobros anteriores en `web/tests/test_cobros_anteriores.py` y quitar `test_en_el_corte_1_nuevo_cobro_deja_de_escuchar_el_cobro` de `web/tests/test_vencido_y_nuevo.py`
  - `test_un_pago_a_un_cobro_anterior_suena_y_avisa_sin_borrar_lo_tecleado` (escenario 2, CE-013): cobro de $30 "Refresco", Nuevo cobro, teclear "12"; `agregar_pago` al anterior → `sonidos` = 1, vibra en Chromium, `aviso-anterior` con "$30.00" y "Refresco", y `monto` sigue en "$12".
  - `test_el_aviso_de_un_cobro_anterior_se_cierra_al_tocarlo` (spec §7, [vistas](contracts/vistas.md)).
  - `test_un_cobro_anterior_deja_de_escucharse_al_terminar_su_ventana` (escenario 3): `fin` del anterior → `canales(pagina)` muestra su canal `CLOSED`.
  - `test_un_cobro_anterior_que_el_servidor_ya_no_conoce_deja_de_escucharse`: `olvidar` y canal rechazado con 404 → la consulta da 404 y no aparece la vista Error.
  - `test_con_mas_de_3_cobros_en_escucha_solo_3_usan_canal_y_el_resto_se_consulta` (QP-1): con `reloj(pagina, hora)` y 5 cobros en escucha (5 ids distintos, QT-3), `canales(pagina)` muestra 3 abiertos (el de pantalla y los dos anteriores más recientes) y los otros 2 se consultan cada 3 s; un pago a uno sin canal se avisa tras `run_for(3_000)`.
  - `test_con_muchos_cobros_en_escucha_se_puede_crear_otro_cobro` (QP-1): con 5 cobros en escucha, Cobrar llega a la vista QR.
  - `test_al_terminar_un_canal_pasa_al_anterior_mas_reciente` (QP-1): `fin` de un anterior con canal → `canales(pagina)` muestra que el siguiente más reciente abre el suyo.
  - `test_la_pantalla_sigue_encendida_mientras_haya_cobros_anteriores`: tras Nuevo cobro con el anterior en escucha, `bloqueos_soltados` = 0; tras su `fin`, 1.
  - **RF**: RF-024, RF-030, RF-040, RF-043, RF-044, RF-045, RF-056, RF-058, RF-059
  - **Dep.**: T048
  - **Hecho cuando**: las pruebas existen y fallan porque Nuevo cobro termina la escucha.
- [X] T050 [US7] Escribir las pruebas de Cancelar cobro en `web/tests/test_cobros_anteriores.py`
  - `test_cancelar_cobro_solo_aparece_con_el_cobro_pendiente`: visible en la vista QR de un cobro *pendiente*; no aparece con el QR reabierto de un cobro *pagado*.
  - `test_cancelar_un_cobro_pendiente_vuelve_al_teclado_y_lo_sigue_escuchando` (escenario 1): `POST /api/cobros/{id}/cancelar` en `peticiones`; vista Teclado vacía; el cobro sigue con canal.
  - `test_un_pago_a_un_cobro_cancelado_suena_y_avisa` (escenario 2): `agregar_pago` al cancelado → `sonidos` = 1 y `aviso-anterior`.
  - `test_si_el_servidor_rechaza_la_cancelacion_se_queda_el_cobro_con_su_mensaje` (escenario 3, parametrizada con 404, 409 y fallo de red): sigue la vista QR con `mensaje-cancelar` = el `detail` o el mensaje de conexión.
  - `test_mientras_se_cancela_se_ve_cancelando_y_se_ignora_otro_toque` (escenario 4): con demora en cancelar, `cancelar` dice "Cancelando…" y un segundo toque no agrega otro `POST …/cancelar`.
  - `test_un_cancelado_que_llega_por_el_canal_se_trata_como_propio` (escenario 5): `emitir(id, "cancelado", cobro)` → vista Teclado vacía y el cobro sigue en escucha como anterior.
  - **RF**: RF-046, RF-047, RF-048, RF-049, RF-050, RF-072, RF-073, RF-074
  - **Dep.**: T049
  - **Hecho cuando**: las pruebas existen y fallan porque no hay botón Cancelar cobro (`cancelar_cobro` ya existe desde T017).

### Implementación

- [X] T051 [US6] Implementar los cobros anteriores y el reparto de canales en `web/js/escucha.js`, el aviso de cobro anterior en `web/js/vistas.js` y Nuevo cobro del corte 2 en `web/js/app.js`
  - Nuevo cobro deja la escucha con `es_anterior = true` en lugar de terminarla (RF-043).
  - `Escuchas` reparte como máximo 3 canales: el del cobro en pantalla y los de los dos anteriores más recientes; los demás empiezan en `sin_canal` con la consulta cada 3 s; al terminar una escucha con canal, el siguiente más reciente pasa a `abriendo` (QP-1, data-model §2).
  - Un pago nuevo de un anterior: `sonar()`, `vibrar()` y `aviso-anterior` con el monto recibido y el concepto, encima de la vista actual y sin tocar el estado del teclado; se cierra al tocarlo.
  - Un 404 de un anterior termina su escucha sin vista Error (RF-056).
  - `mantener_encendida` sigue pedido mientras quede cualquier escucha.
  - **RF**: RF-024, RF-030, RF-040, RF-043, RF-044, RF-045, RF-056, RF-058, RF-059, RF-077
  - **Dep.**: T049
  - **Hecho cuando**: las pruebas de T049 pasan en los dos celulares.
- [X] T052 [US7] Implementar Cancelar cobro en `web/js/vistas.js` y `web/js/app.js`, y el evento `cancelado` en `web/js/escucha.js`
  - `cancelar` en la vista QR solo con el cobro *pendiente*. Al tocarlo con `accion_en_curso` vacía: `accion_en_curso = "cancelando"`, el botón dice "Cancelando…" y no responde; `cancelar_cobro`. Con `{ cobro }`: el cobro pasa a anterior y vista Teclado vacía. Con `{ mensaje }`: sigue la vista QR con `mensaje-cancelar`. `accion_en_curso` vuelve a vacía.
  - `Escucha`: un `cancelado` del cobro en pantalla, sin cancelación propia en curso, hace lo mismo que una cancelación propia confirmada (RF-074).
  - **RF**: RF-046, RF-047, RF-048, RF-049, RF-050, RF-072, RF-073, RF-074
  - **Dep.**: T050, T051
  - **Hecho cuando**: las pruebas de T050 pasan y todas las anteriores siguen en verde.
- [X] T053 [US7] Cierre de F7: pruebas en verde, sección F7 en `verification-guide.md`, pago real a un QR cancelado y commit sugerido
  - Con autorización de Hugo: quickstart §7, "Cobro anterior" y "Cancelar", con pagos reales de $0.01.
  - Commit sugerido: `feat(002): escuchar cobros anteriores y cancelar un cobro (F7)`.
  - **RF**: RF-044, RF-049
  - **Dep.**: T051, T052
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F7 tiene los resultados reales (o el motivo de que estén pendientes).

---

## Fase 8 (F8): Historia 8 — Recuperar los cobros al recargar (P2) · Corte 2 · 20 nov

**Objetivo**: al recargar, la pantalla recupera los cobros en escucha del mismo celular, muestra sin sonar lo que llegó con la página cerrada y pide un toque para volver a sonar.

**Prueba independiente**: crear un cobro, recargar la página, tocar la pantalla y pagar: suena y se ve "Pago recibido".

### Pruebas (primero, deben fallar antes de implementar)

- [X] T054 [US8] Escribir las pruebas de recuperar en `web/tests/test_recuperar.py` (archivo nuevo)
  - Lógica de `memoria.js` (`only_browser("chromium")`):
    - `test_memoria_guarda_y_lee_los_cobros_en_escucha`: `guardar("Xk3vQ9aZ1bNc", ["Ab12Cd34Ef56"])` y `leer()` devuelve lo mismo, con la clave `pago_facil_escucha`.
    - `test_lo_recordado_que_no_tiene_forma_valida_se_ignora` (RF-077): `leer()` devuelve nada con un texto que no es JSON, con claves de más o de menos, con `anteriores` que no es lista, con un id de 33 caracteres y con un id `<script>alert(1)</script>`.
    - `test_sin_almacenamiento_memoria_no_falla`: con `localStorage` que lanza al leer y al escribir, `guardar` y `leer` no lanzan.
  - Pantalla (los dos celulares):
    - `test_al_recargar_se_recuperan_los_cobros_en_escucha` (escenario 1, parametrizada con *pendiente* → QR, *vencido* → QR vencido y *pagado* → Pago recibido): tras `reload()`, la vista corresponde al estado y el cobro se sigue escuchando junto con un anterior.
    - `test_los_pagos_con_la_pagina_cerrada_se_muestran_sin_sonar` (escenarios 3 y 5): pagos agregados con `avisar=False` antes de recargar → el cobro en pantalla en Pago recibido con su número de pagos y su total, el anterior con su `aviso-anterior`, y `sonidos` = 0 y `vibraciones` = 0.
    - `test_tras_recargar_se_pide_un_toque_para_el_sonido` (escenarios 2 y 4, CE-014): `activar-sonido` = "Toca para activar el sonido"; un pago antes del toque se muestra sin sonar; después del toque, el aviso desaparece y el siguiente pago suena.
    - `test_sin_almacenamiento_la_recarga_vuelve_al_teclado` (escenario 6): con `localStorage` bloqueado por `add_init_script`, tras recargar se ve la vista Teclado vacía.
    - `test_un_cobro_recuperado_que_ya_termino_su_ventana_no_se_escucha`: si `ver_cobro` trae `hora_servidor ≥ fin_ventana`, no se abre canal y no se muestra.
    - `test_un_cobro_anterior_recuperado_que_el_servidor_no_conoce_deja_de_escucharse`: 404 al recuperarlo → no aparece en ninguna parte.
    - `test_un_cobro_en_pantalla_recuperado_que_el_servidor_no_conoce_muestra_error`: 404 → vista Error ([uso-del-servidor](contracts/uso-del-servidor.md)).
    - `test_lo_recordado_con_forma_de_codigo_no_se_ejecuta` (CE-015): `localStorage` con `<script>` en los ids → vista Teclado, sin `dialog` ni peticiones con ese texto.
  - **RF**: RF-051, RF-052, RF-053, RF-054, RF-055, RF-056, RF-057, RF-075, RF-076, RF-077
  - **Dep.**: T053
  - **Hecho cuando**: las pruebas existen y fallan porque `web/js/memoria.js` no existe.

### Implementación

- [X] T055 [US8] Implementar `guardar(en_pantalla, anteriores)` y `leer()` en `web/js/memoria.js` (archivo nuevo, puro)
  - Clave `pago_facil_escucha` con `{"en_pantalla": <id o null>, "anteriores": [<id>, …]}`. Al leer: JSON con exactamente esas dos claves, `en_pantalla` `null` o id, `anteriores` lista de ids, y cada id "de 1 a 32 caracteres `[A-Za-z0-9_-]`"; si algo no cumple, se ignora todo (data-model §4). Todo dentro de `try/catch`: si falla, se sigue sin recordar (RF-076).
  - **RF**: RF-051, RF-076, RF-077
  - **Dep.**: T054
  - **Hecho cuando**: las pruebas de lógica de T054 pasan.
- [X] T056 [US8] Implementar la recuperación en `web/js/app.js`, la escritura de lo recordado en `web/js/escucha.js` y el aviso "Toca para activar el sonido" en `web/js/vistas.js`
  - `Escuchas` llama a `memoria.guardar` en cada cambio: crear, Nuevo cobro, cancelar y terminar una escucha (R-10).
  - Al arrancar, `app.js` hace `memoria.leer()` y, por cada id, `ver_cobro`: 404 → el de pantalla va a la vista Error y un anterior se descarta; `hora_servidor ≥ fin_ventana` → se descarta; si no, se muestran sin sonido los pagos que ya tiene (el de pantalla en su vista y los anteriores con su aviso), se llama a `avisados.marcar_todos` y empieza su escucha.
  - Si se recuperó algo, `activar-sonido` hasta el primer toque en cualquier parte, que llama a `desbloquear()`; mientras tanto, los pagos nuevos se muestran sin `sonar()` ni `vibrar()` (RF-055).
  - C-5: usar el mismo aviso cuando se rechace el sonido de un pago nuevo y reintentarlo desde el primer toque. Preparar otro desbloqueo al recibir `pageshow` o volver a visible.
  - **RF**: RF-051, RF-052, RF-053, RF-054, RF-055, RF-056, RF-057, RF-075, RF-076
  - **Dep.**: T055
  - **Hecho cuando**: todas las pruebas de T054 pasan y las anteriores siguen en verde.
- [X] T057 [US8] Cierre de F8: pruebas en verde, sección F8 en `verification-guide.md`, prueba real de recargar y commit sugerido
  - Con autorización de Hugo: quickstart §7, "Recargar", con un pago real de $0.01 (CE-014).
  - Commit sugerido: `feat(002): recuperar los cobros en escucha al recargar la página (F8)`.
  - **RF**: CE-014
  - **Dep.**: T056
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F8 tiene el resultado real (o el motivo de que esté pendiente).

---

## Fase N (FN): Pulido y temas transversales · 20 nov

- [X] T058 [P] Actualizar `web/README.md` con una sección del MVP: cómo correr, probar, configurar y publicar la web
  - Se conserva la descripción general de la PWA, que sigue siendo la meta del proyecto (errata 2 de la QA).
  - Cómo servirla en local (quickstart §3), el comando de las pruebas, el valor de `config.js`, los dos cortes y lo que necesita #65 (quickstart §4, incluido el cambio de `https:` en la política).
  - **RF**: RF-064
  - **Dep.**: T057
  - **Hecho cuando**: cada comando del README funciona tal cual desde la raíz.
- [X] T059 [P] Corregir `backend/README.md:88`: con `qr_imagen` en `null`, la web muestra "No se pudo mostrar el QR. Intenta de nuevo." y no dibuja el QR (DP-17, H-9)
  - **RF**: RF-078
  - **Dep.**: T057
  - **Hecho cuando**: la línea ya no dice que la web dibuja el QR a partir de `qr`.
- [X] T060 [P] Repetir la revisión de seguridad para el corte 2 en la sección FN de `verification-guide.md`
  - La misma lista y los mismos `git grep` de T042, más lo recordado en el celular (solo ids validados, RF-077) y la ruta de cancelar (solo `POST`, desde el origen configurado).
  - **RF**: RF-063, RF-077
  - **Dep.**: T057
  - **Hecho cuando**: cada punto tiene su resultado anotado.
- [X] T061 Validar `specs/002-web-mvp/quickstart.md` de punta a punta y corregir lo que no coincida
  - **RF**: — (todas las historias)
  - **Dep.**: T058, T059, T060
  - **Hecho cuando**: los pasos 1 a 7 dan lo esperado; las diferencias se corrigen en el quickstart o se anotan como TK.
- [X] T062 Cierre de FN: pruebas en verde, sección FN completa en `verification-guide.md` y commit sugerido
  - Commit sugerido: `docs(002): pulido del corte 2, README de la web y quickstart validado (FN)`.
  - **RF**: —
  - **Dep.**: T061
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección FN existe.

---

## Dependencias y orden de ejecución

```text
(F0: C-2 en la 001, aparte)
         ╎
F1 → F2 → F3 (H1 y H2, MVP) → F4 (H3 y H4) → F5 (H5 y H6) ═ corte 1 (T043 necesita F0, #65 y CoDi)
                                                  │
                                                  └→ F6 (monto libre y reuso) → F7 (anteriores y cancelar) → F8 (recuperar) → FN ═ corte 2
```

- **Corte 1** (F1 a F5): en orden estricto. F3 necesita la base de F2; F4 necesita la vista QR de F3; F5 necesita la escucha de F4. El C-2 solo bloquea el cierre real (T043): las pruebas usan el nombre propuesto `hora_servidor`.
- **Corte 2**: F6, F7 y F8 tocan los mismos archivos (`app.js`, `vistas.js` y, F7 y F8, `escucha.js`), así que van **una después de la otra** y las hace el mismo agente. Lo que permite hacerlas en un día es que cada una es pequeña (plan §11, corregido con QT-4).
- **FN** cierra después de F8.

### Tareas en paralelo dentro de cada fase

- **F1**: T004 y T005 a la vez; T008 en cualquier momento después de T003.
- **F2**: T010, T011, T012 y T013 a la vez (cuatro archivos de pruebas); después T014 a T019 a la vez (seis módulos distintos). T020 espera a T014.
- **F3**: T022 y T023 a la vez. T024 va después de T023 (mismo archivo).
- **F4**: T029 y T030 a la vez. T031 a T033 en orden (mismo `escucha.js`).
- **F5**: T035 primero; T036 y T037/T038 tocan archivos distintos, pero se dejan en orden para no mezclar fallos. T039 a T041 en orden.
- **F6 a F8**: sin paralelo (mismos archivos).
- **FN**: T058, T059 y T060 a la vez.

## Estrategia

1. **MVP primero**: F1, F2 y F3, y se valida que el QR se genera y se enseña (historias 1 y 2) antes de seguir.
2. **El momento del pago** va después: F4 (sonido, verde y respaldo) y F5 (vencido, Nuevo cobro, 320 px y seguridad). El corte 1 se cierra con los pagos reales de $0.01 en Android y iPhone (T043).
3. **Entrega incremental del corte 2**: cada fase suma un comportamiento sin romper los anteriores. La única prueba temporal del corte 1 (Nuevo cobro deja de escuchar) se quita en la misma tarea que cambia la regla (T049).

## Trazabilidad

| Requisito | Tareas |
|---|---|
| RF-001 | T010, T014, T020, T022, T025 |
| RF-002 | T010, T020, T022, T025 |
| RF-003 | T010, T014, T022, T025 |
| RF-004 | T010, T014, T022, T025 |
| RF-005 | T010, T020, T022, T025 |
| RF-006 | T010, T014, T020, T022, T025 |
| RF-007 | T044, T046 |
| RF-008 | T044, T046, T048 |
| RF-009 | T011, T017, T023, T026 |
| RF-010 | T010, T020, T023, T026 |
| RF-011 | T023, T026, T042, T044, T046 |
| RF-012 | T011, T017, T023, T026 |
| RF-013 | T011, T017, T023, T026 |
| RF-014 | T023, T026 |
| RF-015 | T023, T027 |
| RF-016 | T023, T027, T044, T046 |
| RF-017 | T023, T027 |
| RF-018 | T011, T015, T024, T027 |
| RF-019 | T011, T015, T024, T027, T043 |
| RF-020 | T029, T031, T032 |
| RF-021 | T029, T031, T042 |
| RF-022 | T012, T018, T029, T031, T034 |
| RF-023 | T029, T031, T032, T044 |
| RF-024 | T012, T018, T029, T031, T049, T051 |
| RF-025 | T012, T018, T026, T029, T034, T043 |
| RF-026 | T029, T032, T045, T047 |
| RF-027 | T045, T047, T048 |
| RF-028 | T029, T032 |
| RF-029 | T012, T016, T029, T031 |
| RF-030 | T013, T017, T030, T033, T049, T051 |
| RF-031 | T030, T033, T034 |
| RF-032 | T030, T033, T034 |
| RF-033 | T013, T017, T030, T033 |
| RF-034 | T030, T033 |
| RF-035 | T035, T039 |
| RF-036 | T035, T039 |
| RF-037 | T035, T039, T044, T046 |
| RF-038 | T035, T039 |
| RF-039 | T035, T039 |
| RF-040 | T035, T036, T039, T049, T051 |
| RF-041 | T036, T040 |
| RF-042 | T036, T040 |
| RF-043 | T049, T051 |
| RF-044 | T049, T051, T053 |
| RF-045 | T049, T051 |
| RF-046 | T050, T052 |
| RF-047 | T013, T017, T050, T052 |
| RF-048 | T050, T052 |
| RF-049 | T050, T052, T053 |
| RF-050 | T013, T017, T050, T052 |
| RF-051 | T054, T055, T056 |
| RF-052 | T054, T056 |
| RF-053 | T012, T016, T054, T056 |
| RF-054 | T054, T056 |
| RF-055 | T054, T056 |
| RF-056 | T013, T017, T049, T051, T054, T056 |
| RF-057 | T013, T017, T036, T039, T040, T054, T056 |
| RF-058 | T012, T019, T029, T031, T043, T049, T051 |
| RF-059 | T012, T019, T036, T040, T049, T051 |
| RF-060 | T004, T007, T010, T020, T023, T029, T035, T036, T037 |
| RF-061 | T010, T023, T029, T035, T036, T037, T041 |
| RF-062 | T011, T017, T023, T026 |
| RF-063 | T011, T017, T038, T041, T042, T060 |
| RF-064 | T007, T011, T017, T058 |
| RF-065 | T010, T014, T044, T046 |
| RF-066 | T010, T014, T022, T025 |
| RF-067 | T010, T014, T022, T025 |
| RF-068 | T010, T014, T022, T025 |
| RF-069 | T045, T047 |
| RF-070 | T045, T047 |
| RF-071 | T045, T047 |
| RF-072 | T050, T052 |
| RF-073 | T050, T052 |
| RF-074 | T050, T052 |
| RF-075 | T016, T054, T056 |
| RF-076 | T054, T055, T056 |
| RF-077 | T004, T007, T020, T023, T027, T029, T032, T035, T039, T042, T051, T054, T055, T060 |
| RF-078 | T011, T017, T023, T026, T059 |
| CE-001 | T002, T043 |
| CE-002 | T029 |
| CE-003 | T030 |
| CE-004 | T043 |
| CE-005 | T023 |
| CE-006 | T043 |
| CE-007 | T023, T027, T037 |
| CE-008 | T029, T031, T033 |
| CE-009 | T024 |
| CE-010 | T011, T038, T042 |
| CE-011 | T043 |
| CE-012 | T035 |
| CE-013 | T049 |
| CE-014 | T054, T057 |
| CE-015 | T023, T029, T054 |
| CE-016 | T024 |

## Revisión QA de tasks

*2026-11-15, una sola pasada. Recoge los hallazgos de `/speckit-analyze` (D1, D2, U1, U2 e I1) más los de esta pasada. Los T### de las columnas "Hallazgo" y "Recomendación" y de las erratas son los del borrador; al aplicar QT-4 desapareció la antigua T051 y las tareas T052 a T063 pasaron a T051 a T062.*

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QT-1 | Contradicción | Constitución V: "cada comportamiento DEBE tener su prueba escrita y vista fallar **antes** de implementarse". Tres comportamientos se implementan antes de su prueba: la dirección de `config.js` y "solo habla con el servidor configurado" (T017, en F2) se prueban hasta T038 (F5); mostrar como texto el concepto y el `detail` (T020, T027 y T032) también se prueba hasta T038. T038 incluso avisa que esas pruebas "pueden pasar ya". Lo mismo pasa con 320 px: las vistas se construyen en T020, T027 y T032 y se miden hasta T037. | RF-061, RF-063, RF-064, RF-077 | Mover cada prueba a la tarea de pruebas donde aparece el comportamiento: `config.js` y el origen de las peticiones a T011 (antes de T017); el concepto y el `detail` como texto a T023 (vista QR y mensaje) y T029 (Pago recibido); y la medida de 320 px de cada vista a la tarea de pruebas de esa vista (T010, T023, T029, T035 y T036). T037 y T038 quedan como la revisión de todo junto al cierre del corte 1. | **Mover las pruebas** (Hugo, 2026-11-15), como se recomienda. Aplicada el 2026-11-15. |
| QT-2 | Contradicción | Constitución V: las pruebas automáticas "NUNCA … dependen del reloj real". Con QP-4, dos pruebas esperan en tiempo real a que el navegador reconecte el canal: la deduplicación "al reconectar" de T029 (CE-008) y "al volver el canal" de T030 (hasta 5 s reales, con `retry_ms` bajo). La reconexión automática de `EventSource` usa un temporizador interno que `page.clock` no controla. | RF-029, RF-031, RF-032, CE-008 | Provocar la reconexión con el reintento propio: el simulado rechaza el canal (queda `CLOSED`), la pantalla consulta, y con `permitir_canal` más `run_for(15_000)` abre otro `EventSource` que trae `estado` con el pago repetido. Todo con reloj controlado. La reconexión automática del navegador (modo avión) se comprueba a mano en la guía de F4. Las medidas de CE-002 y CE-003 con el reloj de Python se quedan: miden un máximo, no esperan a que pase el tiempo. | **Reintento propio con reloj controlado** (Hugo, 2026-11-15), como se recomienda; la reconexión automática del navegador se comprueba a mano en la guía de F4. Aplicada el 2026-11-15. |
| QT-3 | Construibilidad | Al servidor simulado y a `conftest.py` (T005 y T006) les faltan cuatro cosas que usan las tareas: (a) `page.clock.install()` deja que el tiempo siga corriendo (la guía de Playwright usa `pause_at` para congelarlo), así que las cuentas de T011, T024, T030 y T035 no serían deterministas; (b) T035, T036 y T049 revisan el `readyState` y cuántos `EventSource` hay abiertos, pero nada los expone; (c) T012 comprueba que el audio viene de `blob:`, pero el contador de `play` no guarda `src`; (d) `responder_crear` crea siempre el id `Xk3vQ9aZ1bNc`, y T049 necesita 5 cobros distintos. Comprobado: `browser_context_args` es de alcance de sesión en pytest-playwright 0.10.0 y `Pixel 7` e `iPhone 13` existen en playwright 1.64.1. | Principio V; RF-040, RF-043, QP-1 | Ampliar T005 y T006: ayuda `reloj(pagina, hora)` que hace `install` y `pause_at`; envoltura de `EventSource` en `add_init_script` (`window.__canales`, con URL y `readyState`) y ayuda `canales(pagina)`; el contador de `play` guarda `src`; cada `POST` por defecto crea un id nuevo. | **Ampliar T005 y T006** (Hugo, 2026-11-15), como se recomienda. Aplicada el 2026-11-15. |
| QT-4 | Inconsistencia | `tasks.md` se aparta del plan aprobado en dos cosas, sin dejarlo anotado: (a) `cancelar_cobro` se hace en F7 (T051) y no en F2, como dice el plan §8; (b) el riesgo del plan §11 dice "F6 y F7 tocan archivos distintos", pero F6, F7 y F8 tocan `app.js` y `vistas.js` y van en serie. Además, el plan §4 y `contracts/vistas.md` abrevian el mensaje de conexión como "Revisa tu conexión…", y el texto completo de `contracts/uso-del-servidor.md` es "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo.", el que usan las tareas. | RF-013, RF-047 | Anotar **TK-1** en el plan §14 (cancelar en F7 por ser del corte 2; F6 a F8 en serie), corregir la fila de riesgo del plan §11 y poner el texto completo del mensaje en el plan §4 y en `contracts/vistas.md`. Las tareas no cambian. | **Volver al plan** (Hugo, 2026-11-15; se aparta de la recomendación): `cancelar_cobro` vuelve a F2 con su prueba, como dice el plan §8, y solo se corrigen la fila de riesgo del plan §11 (F6 a F8 en serie) y el texto completo del mensaje de conexión en el plan §4 y en `contracts/vistas.md`. Aplicada el 2026-11-15. |

**Bloques de la pasada:**

1. **Coherencia interna**: 63 tareas con formato `- [ ] T### [P] [US#]`, ruta en la cabecera, RF, Dep. y "Hecho cuando" (comprobado con un script); numeración correlativa; ninguna dependencia hacia una tarea posterior; los 78 RF y los 16 CE en la trazabilidad; cada fase con su cierre. Las pruebas van antes que su implementación, salvo QT-1. Salen QT-1 y las erratas 1 y 2.
2. **Spec, plan, plan del hackathon, reglas e issues**: las fases y fechas siguen el plan §8 (corte 1 antes del 20 nov y corte 2 antes del 21 nov). El issue #64 pide sonido en menos de 2 s, Chrome de Android y Safari de iPhone, URL configurable y Nuevo cobro: los cubren T029 (CE-002), T043, T038 y T040; el logo es de #21 (spec §5). Cumple las reglas: cobro real con reacción visible (T043), la llave nunca en el cliente (T042). Constitución: salen QT-1 y QT-2. La tabla de la constitución dice "PWA", pero la spec ya dejó la instalación para #22 (§5) y no es una regla DEBE: sin hallazgo. El texto del principio II ("la única transición de *pendiente* a *pagado*") sigue pendiente de la enmienda TK-3 de la 001; la web avisa cada pago que informa el servidor, como la 001: sin hallazgo nuevo. Sale QT-4.
3. **Código (solo lectura)**: `uv run --directory backend pytest -q` → `104 passed` (el único aviso es de Starlette, ajeno a la web). `web/` solo tiene su README, que describe la PWA completa (errata 2). `backend/README.md:88` sigue diciendo que la web dibuja el QR, como prevé T060. `ruff check --config pyproject.toml ../web` funciona desde `backend/` ("No Python files found" por ahora).
4. **API de pey**: la web no la usa (RF-063). Sin hallazgos.
5. **Dependencias externas**: en una copia en el directorio temporal, `uv` resuelve `pytest-playwright==0.10.0` y `playwright==1.64.1` con `pytest 9.2.0` sin conflictos. WebKit en esta Mac sigue para T002 (QP-5). C-2, #65 y CoDi tienen dueño y estado en la tabla de dependencias. El sonido con licencia de la spec §7 ya lo resuelve R-7 (errata 4).
6. **Casos límite**: `fill` de Playwright no respeta `maxlength` como lo haría el teclado (errata 1); cinco cobros en escucha con el mismo id (QT-3); reloj que sigue corriendo (QT-3); `cancelado` que llega durante una cancelación propia (T053 lo cubre).
7. **Seguridad y rendimiento**: `git grep` de secretos y de `innerHTML` en T042 y T061; política de R-11 revisada en T004 y T042; CE-002, CE-003 y CE-005 con su forma de medir. Sale QT-1 (RF-063, RF-064, RF-077).
8. **Construibilidad y reparto**: el corte 2 (F6 a FN, 20 tareas) queda en un solo día y en serie (QT-4). Claude implementa y Hugo revisa (DP-5). Sale QT-3.

**Erratas** (sin efecto en el comportamiento; corregidas el 2026-11-15, a pedido de Hugo):

1. T022: el concepto se escribe con `press_sequentially` y no con `fill`, para que se aplique el `maxlength` como con el teclado del celular.
2. T059: "Actualizar `web/README.md`" agregando una sección del MVP, sin borrar la descripción general de la PWA, que sigue siendo la meta del proyecto.
3. T008: agregar también en `AGENTS.md` §6 el comando de `ruff` para el Python de `web/tests` (regla 5).
4. Spec §7, dependencia "Sonido de pago recibido con licencia": anotar que la resuelve R-7 (sonido propio, sin licencia).
