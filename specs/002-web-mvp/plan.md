# Plan: Web del MVP: cobrar con el teclado y oír que me pagaron

- **Rama**: `feature/64-web-mvp`
- **Fecha**: 2026-11-15
- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-15
- **Estado del plan**: `Aprobado`. Hugo lo aprobó el 2026-11-15, después de decidir DP-1 a DP-5 (§9.2) y la QA del plan (QP-1 a QP-5 y sus 3 erratas, aplicadas). El cambio C-3 a la spec, que salió del plan, está aprobado y aplicado (RF-078). El C-2 a la spec 001 (F0) quedó aplicado el 2026-11-15 con el campo `hora_servidor`.
- **Entrada**: la spec de `specs/002-web-mvp/spec.md`

> **Notas para los comandos de spec-kit.**
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
> - Los títulos marcados entre paréntesis (*Technical Context*, *Constitution Check*, *Project Structure*, *Complexity Tracking*) son las secciones que espera `/speckit-plan`.
> - El plan se escribe en español.
> - El plan dice **CÓMO**. Cada pieza cita los RF de la spec que cumple.

---

## 0. Resumen

La pantalla del negocio es una página web sin framework ni compilación (HTML, CSS y módulos de JavaScript). Se apoya en tres ideas:

- **Lógica pura aparte del DOM**: el teclado, la cuenta regresiva, los pagos avisados y la lectura de lo recordado se prueban solos.
- **Una escucha por cobro**. El canal del servidor entrega los avisos en vivo. La pantalla consulta el estado cada 8 s con canal abierto o cada 3 s con el canal cortado o sin canal asignado. Abre como máximo 3 canales (QP-1) y registra los pagos ya avisados por cobro.
- **Vistas que solo pintan texto**: cada vista es una función que recibe el estado y lo muestra con `textContent`.

El QR es la imagen que genera pey (DP-2). La cuenta regresiva usa la hora del servidor que agrega el C-2 a la spec 001. El sonido lo genera la propia web.

Se prueba con Playwright para Python en Chromium y WebKit, contra un servidor simulado y con el reloj de la página controlado (DP-1). Se entrega en dos cortes: el **corte 1** antes del 20 nov y el **corte 2** antes del 21 nov (spec §1.2).

### 0.1 Hechos del código y de las fuentes

| # | Hecho | Evidencia |
|---|---|---|
| H-1 | `web/` solo tiene su README; no hay código de la pantalla | `ls web/` |
| H-2 | El backend tiene 104 pruebas en verde | `uv run --directory backend pytest -q` → `104 passed` (2026-11-15) |
| H-3 | CORS acepta `GET` y `POST` con `Content-Type` desde `WEB_ORIGIN`: alcanza para crear, ver, cancelar y abrir el canal | `backend/app/main.py:134-137`, `backend/app/config.py:41` |
| H-4 | El servidor fija `creado_en` **antes** de pedirle el QR a pey | `backend/app/main.py:181-185`, `backend/app/cobros.py:151` |
| H-5 | El objeto cobro no trae la hora actual del servidor (lo agrega el C-2) | `specs/001-backend-mvp/contracts/crear-cobro.md`, "Objeto cobro" |
| H-6 | El canal manda `retry: 3000`, eventos con nombre y `: sigo conectado` | `backend/app/canal.py:15,67,92` |
| H-7 | La imagen del QR se pide siempre a pey (`generateImage`) y puede llegar vacía | `backend/app/pey.py:29,106,118,127` |
| H-8 | Cancelar responde 200, 404 o 409 con `detail` en español | `specs/001-backend-mvp/contracts/cancelar-cobro.md` §4 |
| H-9 | `backend/README.md` dice que, con `qr_imagen` en `null`, "la web dibuja el QR a partir de `qr`" | `backend/README.md:88` |
| H-10 | Máximo 10 canales y 10 cobros por minuto por IP | `backend/app/config.py:32,38` |
| H-11 | El primer cobro después de arrancar el servidor tardó de 7 a 9 s; los siguientes, unos 2.4 s | TK-5 del plan 001 |
| H-12 | Node 24 y npm 11 están instalados, pero el repositorio no los usa | `node -v`, `npm -v` |
| H-13 | `playwright` 1.64.1 (22 oct 2026) y `pytest-playwright` 0.10.0 (8 oct 2026) cumplen la espera mínima de dos semanas | PyPI, consultado el 2026-11-15 |

---

## 1. Contexto técnico (Technical Context)

- **Lenguaje y versión**: HTML5, CSS y JavaScript con módulos nativos (ES2020+), sin compilación. Las pruebas se escriben en Python 3.11+.
- **Dependencias principales**: **ninguna de producción**. Ni framework, ni librería de QR (DP-2), ni archivo de sonido (R-7).
- **Dependencias de desarrollo**: `pytest-playwright` 0.10.0 y `playwright` 1.64.1 en el grupo de desarrollo del backend (DP-1), más los navegadores Chromium y WebKit (`playwright install chromium webkit`).
- **Almacenamiento**: en memoria de la página. Desde el corte 2, además, `localStorage` con los identificadores de los cobros en escucha (R-10).
- **Pruebas**: pytest + Playwright, contra `ServidorSimulado` (R-2), con `page.clock` para los temporizadores de JavaScript (QP-4) y emulación de `Pixel 7` (Chromium) y `iPhone 13` (WebKit). Configuración en `web/pytest.ini` (QP-3). Si WebKit no arranca en esta Mac, se aplica la alternativa de QP-5.
- **Plataforma de destino**: Chrome de Android y Safari de iPhone, con HTTPS. El hosting lo decide #65 (DP-4).
- **Tipo de proyecto**: página web que consume el API y el canal SSE de la spec 001.
- **Metas de rendimiento** (spec §6):
  - aviso y sonido en menos de 2 s después del evento del servidor (CE-002);
  - con el canal cortado, aviso en menos de 6 s (CE-003);
  - vista Generando QR en menos de 0.1 s (CE-005);
  - QR en menos de 3 s, sin contar el primer cobro (CE-006);
  - cuenta regresiva con menos de 2 s de error (CE-009).
- **Restricciones**:
  - la web solo habla con el servidor de PAGO FÁCIL;
  - nada de secretos;
  - desde 320 px de ancho;
  - textos de fuera solo como texto;
  - el corte 1 requiere el C-2 aplicado en la 001.
- **Escala**: un celular por negocio. Desde el corte 2, hasta unos 20 cobros en escucha a la vez (10 por minuto durante sus 20 minutos de ventana). La pantalla abre como máximo 3 canales a la vez, porque Chrome y Safari solo abren 6 conexiones HTTP/1.1 por origen y hay que dejar libres las de crear, ver y cancelar (QP-1). El resto de los cobros en escucha se consulta cada 3 s. Más de 10 canales por IP en el servidor sigue siendo la limitación aceptada QA-3.

No quedan `[NECESITA ACLARACIÓN]`.

---

## 2. Verificación de la constitución (Constitution Check)

*Revisada antes de la Fase 0 y otra vez después del diseño (Fase 1), el 2026-11-15.*

| Principio de la constitución | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. El pago se confirma en el servidor | La pantalla solo muestra un pago como recibido cuando llega en un evento `pago` o en el objeto cobro del servidor (RF-021). No existe ninguna acción del navegador que marque pagos | Cumple |
| II. Una orden nunca se ejecuta dos veces | `Avisados` deduplica por número de pago dentro de cada cobro: un pago suena una sola vez aunque llegue por el canal, al reconectar y por la consulta (RF-029, CE-008). Cobrar se bloquea mientras se crea (RF-011) | Cumple |
| III. Los secretos nunca salen del backend | La web no tiene llaves ni habla con pey (RF-063). Una prueba revisa que todas las peticiones vayan al servidor configurado (CE-010), y en el cierre se buscan patrones de llaves en `web/` | Cumple |
| IV. Spec primero y alcance anclado | Spec aprobada. Cada pieza cita sus RF. El caso de la imagen vacía, que la spec no cubría, entró con el cambio C-3 (RF-078), aprobado y aplicado | Cumple |
| V. Pruebas primero, en todo | Cada tarea lleva antes su prueba de Playwright, con servidor simulado y `page.clock` (§7). Nombres en español | Cumple |
| VI. CoDi real, reacción real | El cierre del corte 1 incluye un pago real de $0.01 desde un Android y un iPhone con la web publicada (quickstart, paso 5), con autorización de Hugo | Cumple (depende de #65 y de CoDi activo) |
| VII. Pensado para el mostrador | Monto y QR grandes; indicación de CoDi; estados de carga, error y éxito en todo lo que se toca; 320 px; mensajes del servidor en español | Cumple |
| VIII. Un pago no prueba identidad ni entrega | Pagos tardíos, monto distinto, QR reutilizado y fallas definidos en la spec §4 y cubiertos por `Escucha` (§4) | Cumple |
| IX. Lo más simple que gane la demo | Sin framework, sin compilación y sin dependencias de producción. La única herramienta nueva, Playwright (solo de desarrollo), pasó por comparativa y la eligió Hugo (DP-1, R-1) | Cumple |
| X. Si no se ve, no existe | La web deja en la consola los cambios de la escucha (abierto, cortado, consulta, `fin`), sin datos bancarios. Los registros del servidor ya los define la 001 | Cumple |

No hay excepciones, así que §12 queda vacío.

---

## 3. Estructura del proyecto (Project Structure)

### 3.1 Documentación de esta funcionalidad

```text
specs/002-web-mvp/
├── spec.md               # Qué y por qué (entrevista y QA incluidas)
├── plan.md               # Este archivo
├── research.md           # Fase 0: R-1 a R-14
├── data-model.md         # Fase 1: estado de la pantalla, escuchas, vistas y transiciones
├── contracts/            # Fase 1: vistas (contrato de pantalla) y uso del servidor
├── quickstart.md         # Fase 1: comprobación de punta a punta
├── tasks.md              # /speckit-tasks
├── verification-guide.md # Al cerrar cada fase
└── checklists/requirements.md
```

### 3.2 Código fuente

```text
web/
├── index.html            # (nuevo) una sola página; política de seguridad de contenido en <meta>
├── config.js             # (nuevo) dirección del servidor: un solo valor (RF-064)
├── estilos.css           # (nuevo) desde 320 px; verde de Pago recibido; QR ≥ 70 % del ancho
├── js/
│   ├── app.js            # (nuevo) arranque: une piezas y maneja los toques
│   ├── teclado.js        # (nuevo, puro) aplicar_tecla, cobrar_activo, monto_libre_activo
│   ├── cuenta.js         # (nuevo, puro) desfase y tiempo restante con la hora del servidor
│   ├── avisados.js       # (nuevo, puro) pagos ya avisados por cobro
│   ├── servidor.js       # (nuevo) crear, ver y cancelar; errores → mensajes
│   ├── escucha.js        # (nuevo) canal + consulta de respaldo por cobro; Escuchas
│   ├── vistas.js         # (nuevo) pinta cada vista con textContent
│   ├── sonido.js         # (nuevo) WAV propio, desbloqueo y vibración
│   ├── pantalla.js       # (nuevo) pantalla encendida (Wake Lock)
│   └── memoria.js        # (nuevo, corte 2) recordar y leer cobros en escucha
├── README.md             # (cambia en FN) cómo correr, probar y configurar
├── pytest.ini            # (nuevo, QP-3) testpaths = tests y opción de pytest-asyncio
└── tests/
    ├── conftest.py               # (nuevo) ServidorSimulado en un hilo, páginas Pixel 7 e iPhone 13, data-prueba
    ├── servidor_simulado.py      # (nuevo) app FastAPI de pruebas (R-2)
    ├── test_teclado.py           # (nuevo) H1
    ├── test_crear_y_mostrar_qr.py # (nuevo) H1, H2
    ├── test_pago_recibido.py     # (nuevo) H3
    ├── test_respaldo.py          # (nuevo) H4
    ├── test_vencido_y_nuevo.py   # (nuevo) H5, H6 (corte 1)
    ├── test_seguridad.py         # (nuevo) RF-063, RF-077, CE-010, CE-015
    ├── test_monto_libre_y_reuso.py # (nuevo, corte 2) RF-007/008/065, RF-027, RF-069 a RF-071
    ├── test_cobros_anteriores.py # (nuevo, corte 2) H6 y H7
    └── test_recuperar.py         # (nuevo, corte 2) H8
backend/
├── pyproject.toml        # (cambia en F1) + pytest-playwright y playwright en el grupo dev
└── README.md             # (cambia en FN) la línea de qr_imagen null (H-9, DP-17)
AGENTS.md                 # (cambia en F1) comando de las pruebas de la web en §6
```

**Decisión de estructura**:

- Los módulos puros (`teclado`, `cuenta`, `avisados`, `memoria`) no tocan el DOM, para probarlos rápido con `page.evaluate`.
- `escucha.js` concentra todo lo del tiempo real, para que el respaldo y la deduplicación vivan en un solo lugar.
- Las pruebas se reparten por historia, para que las tareas `[P]` de `tasks.md` no choquen.
- Las pruebas de la web usan el entorno de uv del backend (DP-15), para no crear un segundo proyecto de Python.

---

## 4. Módulos y piezas con comportamiento

| Pieza | Responsabilidad | Requisitos |
|---|---|---|
| `config.js` | `window.PAGO_FACIL = { servidor: "" }`. La cadena vacía significa el mismo origen (R-4). Es la única dirección a la que habla la web | RF-063, RF-064 |
| `teclado.js` · `aplicar_tecla(texto, tecla)` | Dígitos, punto y borrar. Ignora el tercer decimal, el segundo punto y el sexto dígito entero; reemplaza el 0 inicial; el punto inicial escribe "0." | RF-001, RF-003, RF-004, RF-066, RF-067, RF-068 |
| `teclado.js` · `cobrar_activo(texto)`, `monto_libre_activo(texto)` | Cobrar si el monto vale más de 0; Monto libre si está vacío o vale 0 | RF-006, RF-065 |
| `cuenta.js` · `desfase(cobro, ahora)`, `restante(cobro, desfase, ahora)`, `formato(s)` | Segundos que le quedan al QR según la hora del servidor (C-2), y `m:ss`. Sin `hora_servidor`, desfase 0 y advertencia (R-6) | RF-018, RF-019, CE-009, CE-016 |
| `avisados.js` · `Avisados` | Por cobro, el número de pago más alto ya avisado. `nuevos(cobro)` devuelve los pagos con número mayor y los marca. `marcar_todos(cobro)` marca sin avisar (recuperación) | RF-029, RF-053, RF-075, CE-008 |
| `servidor.js` · `crear_cobro(monto, concepto)` | `POST /api/cobros` con `monto` número o `null` (Monto libre). 201 con imagen → cobro; 201 sin imagen → "No se pudo mostrar el QR. Intenta de nuevo." (RF-078); 422, 429, 502 o 503 → mensaje `detail`; fallo de red o 15 s sin respuesta → "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo." (el servidor espera a pey 10 s; ver [uso-del-servidor](contracts/uso-del-servidor.md)). Los 15 s se cuentan con `setTimeout` y `AbortController`, para que `page.clock` los controle en las pruebas (QP-4). Solo pide cosas a la dirección de `config.js`; los mensajes propios están en español | RF-008, RF-009, RF-012, RF-013, RF-062, RF-063, RF-078 |
| `servidor.js` · `ver_cobro(id)` | `GET /api/cobros/{id}` → cobro, "no existe" (404) o "sin conexión" | RF-030, RF-033, RF-056, RF-057 |
| `servidor.js` · `cancelar_cobro(id)` | `POST /api/cobros/{id}/cancelar` → cobro, o el mensaje de 404 o 409, o "sin conexión" | RF-047, RF-050 |
| `escucha.js` · `Escucha` | Un cobro en escucha. Si `Escuchas` le asigna canal, abre el `EventSource` y consulta cada 8 s desde `open`. Con el canal cortado o sin canal asignado, consulta cada 3 s. Mantiene un solo GET en curso. Ante `error`, muestra el aviso de corte y reintenta el canal cada 15 s si quedó `CLOSED` (R-5). Termina con `fin` o al pasar `fin_ventana`. Entrega el estado vigente a `Escuchas`. | RF-020, RF-030, RF-031, RF-032, RF-033, RF-034, RF-039, RF-040, RF-056, RF-057, RF-074, RF-079 |
| `escucha.js` · `Escuchas` | Conjunto de escuchas, con el cobro en pantalla y los anteriores. Reparte **como máximo 3 canales**: siempre uno para el cobro en pantalla y los otros para los dos anteriores más recientes. Al terminar o liberarse uno, pasa el canal al siguiente más reciente (QP-1). Solo avisa lo que trae el servidor. Usa `Avisados` para decidir qué es nuevo. Llama a `sonido`, a `vistas` y a `pantalla`. En el corte 1 solo hay el cobro en pantalla; en el corte 2 conserva los anteriores | RF-021, RF-022, RF-023, RF-027, RF-029, RF-043, RF-044, RF-045, RF-049, RF-058, RF-059 |
| `vistas.js` | Una función por vista (Teclado, Generando QR, QR, QR vencido, Pago recibido y Error), más el aviso de cobro anterior, "Reconectando…" y "Toca para activar el sonido". Solo `textContent` y atributos fijos. Contrato en [contracts/vistas.md](contracts/vistas.md) | RF-002, RF-005, RF-010, RF-015, RF-016, RF-017, RF-023, RF-026, RF-028, RF-035 a RF-038, RF-041, RF-046, RF-054, RF-060, RF-061, RF-062, RF-069, RF-072, RF-077 |
| `sonido.js` | Arma el WAV de dos tonos y usa la sesión `playback` cuando está disponible. `desbloquear()` y `sonar()` devuelven y registran el resultado de `play()`. `app.js` coordina el aviso, el primer toque y la vuelta al primer plano. `vibrar()` actúa donde existe. | RF-022, RF-024, RF-025, RF-044, RF-054, RF-055 |
| `pantalla.js` | `mantener_encendida(sí/no)` con Wake Lock; vuelve a pedirlo en `visibilitychange` | RF-058, RF-059, CE-011 |
| `memoria.js` (C2) | `guardar(en_pantalla, anteriores)` y `leer()` con validación estricta y `try/catch` | RF-051, RF-056, RF-076, RF-077 |
| `app.js` | Arranque: lee la configuración, recupera lo recordado (C2), conecta los toques (teclas, Cobrar, Monto libre, Nuevo cobro, Cancelar cobro, Mostrar QR otra vez) con las piezas y con el bloqueo de doble toque | RF-007, RF-009, RF-011, RF-014, RF-042, RF-047, RF-048, RF-052, RF-070, RF-071, RF-073 |
| `index.html` | Una página con la marca PAGO FÁCIL, el contenedor de vistas y la política de seguridad de contenido (R-11) | RF-060, RF-077 |
| `estilos.css` | Diseño desde 320 px, QR ≥ 70 % del ancho con `image-rendering: pixelated`, verde a pantalla completa en Pago recibido | RF-023, RF-061, CE-007 |

---

## 5. Contratos

La web no expone ninguna interfaz a otros sistemas. Sus contratos son la pantalla misma (lo que ve y toca el dueño, y lo que buscan las pruebas) y el uso que hace del servidor de la 001.

| Contrato | Archivo | Requisitos | Corte |
|---|---|---|---|
| Vistas, elementos, `data-prueba` y transiciones | [contracts/vistas.md](contracts/vistas.md) | RF-001 a RF-078 | C1 y C2 |
| Uso del servidor de la 001: rutas, códigos, mensajes, canal, `hora_servidor` (C-2) y configuración | [contracts/uso-del-servidor.md](contracts/uso-del-servidor.md) | RF-009 a RF-014, RF-019, RF-020, RF-030 a RF-034, RF-040, RF-047, RF-050, RF-057, RF-063, RF-064 | C1 y C2 |

---

## 6. Modelo de datos

Detalle en [data-model.md](data-model.md). En resumen:

- **Estado de la pantalla**: la vista actual, el texto del monto, el concepto, el cobro en pantalla, si el sonido está desbloqueado y si hay una acción en curso (crear o cancelar).
- **Escucha**: una por cobro en escucha, con su último cobro conocido, su desfase con el servidor, el estado del canal y si es el cobro en pantalla o uno anterior.
- **Avisados**: el número de pago más alto ya avisado de cada cobro.
- **Lo recordado** (C2): los identificadores del cobro en pantalla y de los anteriores.

---

## 7. Estrategia de pruebas

- **Pruebas primero**: cada tarea de implementación tiene antes su prueba, que se ve fallar y después pasa.
- **Sin pey ni servidor real**: todas las pruebas usan `ServidorSimulado` (R-2). Cada prueba programa sus respuestas y empuja eventos del canal cuando quiere.
- **Reloj controlado** (QP-4):
  - `page.clock.install()` con una hora fija, seguido de `page.clock.pause_at(…)` para congelarlo (QT-3 de tasks), y `page.clock.run_for(…)` recorren lo que depende de temporizadores de JavaScript: la cuenta regresiva, la vigencia, la consulta cada 3 s, el reintento cada 15 s y el tiempo de espera de 15 s al crear.
  - Lo que el navegador maneja por dentro no lo controla: la reconexión automática del `EventSource`. Por eso las pruebas no la esperan: el servidor simulado rechaza el canal, la pantalla queda en la consulta cada 3 s y la reconexión se hace con su reintento de 15 s, todo con reloj controlado. La reconexión automática del navegador se comprueba a mano (modo avión) en la guía de F4 (TK-1).
  - CE-002 y CE-003 se miden con el reloj de Python alrededor de la espera, no con `Date`.
  - La hora del servidor simulado se fija desde la prueba.
- **Dos celulares**: las pruebas de pantalla corren en Chromium con `Pixel 7` y en WebKit con `iPhone 13`. La lógica pura corre solo en Chromium, porque no depende del motor.
- **Sonido y vibración**: antes de cargar la página se reemplazan `HTMLMediaElement.prototype.play` y `navigator.vibrate` con contadores (`page.add_init_script`), para comprobar cuántas veces sonó y vibró.
- **Pantalla encendida**: `navigator.wakeLock` simulado con un contador en `add_init_script`. CE-011 se comprueba a mano en el Android.
- **Pruebas reales**: solo con $0.01 y con autorización de Hugo, en el cierre del corte 1 (Android e iPhone) y de cada fase del corte 2.
- **Nombres en español**, como el comportamiento.

| Requisito | Prueba | Tipo |
|---|---|---|
| RF-001 a RF-004, RF-066 a RF-068 | `test_el_teclado_escribe_el_monto_con_dos_decimales_como_maximo`, `test_el_cero_inicial_se_reemplaza_y_el_punto_inicial_escribe_cero_punto`, `test_no_se_aceptan_mas_de_5_digitos_enteros` (función pura y pantalla) | unitaria y pantalla |
| RF-005 | `test_el_concepto_acepta_como_maximo_40_caracteres` | pantalla |
| RF-006 | `test_cobrar_esta_desactivado_sin_monto` | pantalla |
| RF-009, RF-015, RF-016, RF-017 | `test_cobrar_pide_el_cobro_y_muestra_el_qr_con_monto_concepto_e_indicacion_codi` | pantalla |
| RF-010, RF-011, CE-005 | `test_al_pulsar_cobrar_aparece_generando_qr_y_un_segundo_toque_no_crea_otro_cobro` (el servidor simulado tarda; se cuentan las peticiones) | pantalla |
| RF-012, RF-014 | `test_si_el_servidor_rechaza_el_cobro_se_ve_su_mensaje_y_se_conserva_lo_escrito` (422, 429, 502, 503) | pantalla |
| RF-013, RF-014 | `test_sin_conexion_se_pide_revisar_la_conexion_y_se_conserva_lo_escrito` (servidor que no responde, con el reloj adelantado 15 s) | pantalla |
| RF-078 (C-3) | `test_si_el_qr_llega_sin_imagen_se_vuelve_al_teclado_con_mensaje` | pantalla |
| RF-018, RF-019, CE-009, CE-016 | `test_la_cuenta_regresiva_sigue_la_hora_del_servidor_aunque_el_celular_este_desfasado`, `test_si_crear_tardo_9_segundos_la_cuenta_arranca_en_9_51` (función pura y pantalla) | unitaria y pantalla |
| RF-020 a RF-025, CE-002 | `test_un_pago_suena_vibra_y_pone_la_pantalla_verde_sin_tocar_nada_despues_de_cobrar` (se mide con el reloj de Python el tiempo entre el evento y la vista, QP-4) | pantalla |
| RF-026 | `test_pago_recibido_se_queda_hasta_nuevo_cobro` | pantalla |
| RF-022, RF-023 (C1, segundo pago) | `test_un_segundo_pago_al_mismo_qr_vuelve_a_sonar` | pantalla |
| RF-028 | `test_un_monto_distinto_muestra_el_pedido_y_el_recibido` | pantalla |
| RF-029, CE-008 | `test_el_mismo_pago_por_canal_reconexion_y_consulta_suena_una_sola_vez` | pantalla |
| RF-030 a RF-033, CE-003 | `test_con_el_canal_cortado_la_consulta_cada_3_segundos_avisa_el_pago`, `test_al_volver_el_canal_se_consulta_a_los_8_segundos_y_se_quita_reconectando` (reintento propio y reloj controlado, TK-1) | pantalla |
| RF-079, CE-017 | `test_con_el_canal_abierto_y_mudo_la_consulta_avisa_y_suena` y casos de deduplicación, consulta pendiente, evento retrasado y fin de ventana en `test_respaldo.py` | pantalla |
| RF-054, CE-018 | Casos de rechazo, reintento con un toque, vuelta al primer plano y `audioSession` en `test_pago_recibido.py` | pantalla |
| RF-034 | `test_si_el_servidor_rechaza_el_canal_se_sigue_con_la_consulta` (el simulado responde 429 al canal) | pantalla |
| RF-035 a RF-039, CE-012 | `test_al_vencer_se_oculta_el_qr_y_se_ve_qr_vencido`, `test_un_pago_tardio_con_qr_vencido_suena_y_se_muestra` | pantalla |
| RF-040 | `test_al_recibir_fin_se_cierra_el_canal_y_no_se_reconecta` | pantalla |
| RF-041, RF-042 | `test_nuevo_cobro_vuelve_al_teclado_vacio_desde_cada_vista` | pantalla |
| RF-057 | `test_si_el_servidor_ya_no_conoce_el_cobro_se_ve_la_vista_error` | pantalla |
| RF-058, RF-059 | `test_la_pantalla_pide_no_apagarse_mientras_hay_un_cobro_en_escucha` (Wake Lock simulado), más un paso manual en Android (CE-011) | pantalla y manual |
| RF-060 a RF-062 | `test_todas_las_vistas_caben_en_320_px_y_muestran_pago_facil` (ancho de la página ≤ 320 px y QR ≥ 70 %, CE-007) | pantalla |
| RF-063, CE-010 | `test_la_web_solo_pide_cosas_al_servidor_configurado`, más `git grep` de patrones de llaves en `web/` en el cierre | pantalla y manual |
| RF-064 | `test_la_direccion_del_servidor_sale_de_config_js` | pantalla |
| RF-077, CE-015 | `test_un_concepto_con_forma_de_codigo_se_muestra_como_texto` (`<script>alert(1)</script>` en el concepto, en un `detail` y en lo recordado) | pantalla |
| RF-007, RF-008, RF-065 (C2) | `test_monto_libre_solo_esta_activo_sin_monto_y_crea_un_cobro_sin_monto` | pantalla |
| RF-027 (C2) | `test_el_segundo_pago_muestra_pago_2_y_el_total` | pantalla |
| RF-069 a RF-071 (C2) | `test_mostrar_qr_otra_vez_vuelve_al_qr_mientras_siga_vigente`, `test_si_el_qr_que_se_volvio_a_mostrar_vence_vuelve_pago_recibido` | pantalla |
| RF-043 a RF-045, CE-013 (C2) | `test_un_pago_a_un_cobro_anterior_suena_y_avisa_sin_borrar_lo_tecleado` | pantalla |
| QP-1 (C2) | `test_con_mas_de_3_cobros_en_escucha_solo_3_usan_canal_y_el_resto_se_consulta`, `test_con_muchos_cobros_en_escucha_se_puede_crear_otro_cobro`, `test_al_terminar_un_canal_pasa_al_anterior_mas_reciente` | pantalla |
| RF-046 a RF-050, RF-072 a RF-074 (C2) | `test_cancelar_un_cobro_pendiente_vuelve_al_teclado_y_lo_sigue_escuchando`, `test_mientras_se_cancela_se_ve_cancelando_y_se_ignora_otro_toque`, `test_si_el_servidor_rechaza_la_cancelacion_se_queda_el_cobro_con_su_mensaje`, `test_un_cancelado_que_llega_por_el_canal_se_trata_como_propio` | pantalla |
| RF-051 a RF-056, RF-075, RF-076, CE-014 (C2) | `test_al_recargar_se_recuperan_los_cobros_en_escucha`, `test_los_pagos_con_la_pagina_cerrada_se_muestran_sin_sonar`, `test_tras_recargar_se_pide_un_toque_para_el_sonido`, `test_sin_almacenamiento_la_recarga_vuelve_al_teclado`, `test_lo_recordado_que_no_tiene_forma_valida_se_ignora` | pantalla |
| CE-001, CE-004, CE-006 | Pago real de $0.01 desde un Android y un iPhone con la web publicada; 6 toques para $25.50; tiempo del QR medido sin contar el primero (quickstart, paso 5) | manual |
| CE-011 | Android sin tocar 10 minutos con un cobro en escucha (quickstart, paso 6) | manual |

---

## 8. Plan de implementación

| Fase | Fechas | Quién | Qué | Depende de |
|---|---|---|---|---|
| F0 C-2 en la spec 001 | 16 nov | Claude (revisa Hugo), cuando Hugo pida aplicar el C-2 | `hora_servidor` en el objeto cobro y en los eventos, con prueba primero; contratos y registro del plan 001. Es trabajo de la 001 (su `tasks.md`), no de esta spec | Hugo pide aplicar el C-2 |
| F1 Preparación | 16 nov | Claude (revisa Hugo) | **Primero** instalar Chromium y WebKit y correr una prueba vacía en cada uno; si WebKit no arranca, aplicar la alternativa de QP-5. Después: Playwright en el grupo dev (DP-1); `web/pytest.ini` (QP-3); `web/tests/conftest.py` y `servidor_simulado.py`; esqueleto de `index.html`, `config.js`, `estilos.css` y `app.js`; comando de pruebas en `AGENTS.md` §6 | Plan y tasks aprobados |
| F2 Base | 16–17 nov | Claude (revisa Hugo) | Módulos puros `teclado`, `cuenta` y `avisados`; `servidor.js`; `vistas.js` con Teclado y Generando QR; `sonido.js` y `pantalla.js` con su detección | F1 |
| F3 Historias 1 y 2 (C1) | 17 nov | Claude (revisa Hugo) | Teclado → Cobrar → QR con cuenta regresiva; errores y conexión; imagen vacía (RF-078) | F2, F0 (para la cuenta regresiva) |
| F4 Historias 3 y 4 (C1) | 17–18 nov | Claude (revisa Hugo) | `Escucha` y `Escuchas` con el cobro en pantalla: Pago recibido, sonido, vibración, segundo pago, monto distinto, deduplicación, respaldo cada 3 s, "Reconectando…", rechazo del canal y pantalla encendida. Prueba del silencio en el iPhone (R-7) | F3 |
| F5 Historias 5 y 6 (C1) · cierre del corte 1 | 18–19 nov | Claude (revisa Hugo) | QR vencido con pagos tardíos, `fin`, Nuevo cobro, vista Error, 320 px y seguridad (RF-063, RF-077). Revisión de seguridad. **Cierre del corte 1**: pago real de $0.01 en Android y iPhone con la web publicada | F4, #65, CoDi activo |
| F6 Monto libre y reuso (C2) | 20 nov | Claude (revisa Hugo) | Tecla Monto libre, "Pago n" y total, Mostrar QR otra vez; pago real de monto libre | F5 |
| F7 Cobros anteriores y cancelar (C2) | 20 nov | Claude (revisa Hugo) | Escuchas con anteriores, aviso de cobro anterior, Cancelar cobro con "Cancelando…" y `cancelado` de fuera; pago real a un QR cancelado | F5 |
| F8 Recuperar al recargar (C2) | 20 nov | Claude (revisa Hugo) | `memoria.js`, recuperación, avisos sin sonido y "Toca para activar el sonido" | F7 |
| FN Pulido | 20 nov | Claude (revisa Hugo) | `web/README.md`, la línea de `qr_imagen` en `backend/README.md` (DP-17), quickstart completo y revisión de seguridad del corte 2 | F6–F8 |

- **Revisión del equipo**: Miguel o Beer17 revisan cada pull request y prueban en su iPhone o Android (DP-5).
- **Despliegue**: el despliegue de la web (#65) no es una fase de este plan, pero el cierre de F5 depende de él. Lo que necesita #65 está en la sección "Despliegue" del [quickstart](quickstart.md).

---

## 9. Decisiones

### 9.1 Decisiones del plan

| # | Decisión | Por qué | Alternativas descartadas |
|---|---|---|---|
| DP-6 | Módulos nativos sin compilación; lógica pura separada del DOM (R-12) | Constitución ("sin framework"); se despliega como archivos sueltos y la lógica se prueba sola | Empaquetador: herramienta nueva sin necesidad |
| DP-7 | `ServidorSimulado` en Python para las pruebas, en el mismo origen que la web (R-2) | Control de cada respuesta y de cada evento del canal; sin pey ni reloj real | El backend real con `RelojFalso` (el canal correría al fin de la ventana en un instante); `page.route` (no sirve para SSE) |
| DP-8 | Cuenta regresiva con el desfase respecto a `hora_servidor`, recalculada cada 250 ms (R-6) | RF-019 y CE-016, sin depender del reloj del celular ni de que los temporizadores sean puntuales | Cabecera `Date` (CORS no la deja leer); arrancar en 10:00 |
| DP-9 | Un `EventSource` por cobro en escucha, con **máximo 3 canales por pantalla** (QP-1). Consulta cada 8 s con canal abierto y cada 3 s con el canal cortado o sin canal asignado. Reintento cada 15 s si queda `CLOSED` y `close()` en `fin` (R-5). | Reconexión del navegador y respaldo para cortes o eventos retenidos, con un solo GET por cobro en curso. | Leer el flujo con `fetch`: reimplementar la reconexión y el formato SSE |
| DP-10 | Sonido generado por la propia web (WAV en memoria) y `HTMLAudioElement`. Cuando la API está disponible se intenta usar una sesión `playback` (R-7). | Sin licencia ni componente de terceros. El resultado de `play()` permite pedir otro toque cuando el navegador lo rechaza. | Archivo con licencia; oscilador de Web Audio |
| DP-11 | Screen Wake Lock con detección y nueva petición en `visibilitychange` (R-9) | RF-058 y RF-059 con la API estándar | Video invisible en bucle |
| DP-12 | `localStorage` con forma y identificadores validados, y `try/catch` (R-10) | RF-051, RF-076 y RF-077 | `sessionStorage` (se pierde al cerrar); IndexedDB (demasiado) |
| DP-13 | Solo `textContent` para textos de fuera y política de seguridad de contenido en `<meta>`, que permite el sonido en `blob:` y el servidor local (R-11, QP-2) | RF-077 en dos capas | Una librería para limpiar HTML |
| DP-14 | Atributo `data-prueba` en todo lo que tocan las pruebas (R-14) | Pruebas estables y nombres en español | Buscar por texto visible |
| DP-15 | Las pruebas de la web corren con el entorno de uv del backend y su propio `web/pytest.ini`: `uv run --directory backend pytest ../web -q` (QP-3) | Un solo entorno de Python y la misma versión de FastAPI para el servidor simulado | Un segundo `pyproject.toml` en `web/` |
| DP-16 | El monto se maneja como texto en el teclado y se manda como número JSON (R-13) | Respeta lo tecleado ("$25.") y el servidor ya convierte con `Decimal(str(...))` | Centavos enteros: no representan lo que se va tecleando |
| DP-17 | En FN se corrige `backend/README.md:88`: con `qr_imagen` en `null`, la web muestra un error, no dibuja el QR (H-9) | Que la documentación no contradiga DP-2 y DP-3 | Dejarlo hasta la migración |

### 9.2 Decisiones de Hugo

| # | Pregunta | Recomendación | Decisión |
|---|---|---|---|
| DP-1 | ¿Con qué se prueba la pantalla? (R-1, comparativa) | Playwright para Python | **Playwright para Python** (Hugo, 2026-11-15), como se recomienda. Solo de desarrollo; se agrega en F1. |
| DP-2 | ¿Cómo se dibuja el QR? (R-3, comparativa) | Dibujarlo con `qrcode-generator` | **Usar la imagen de pey** (Hugo, 2026-11-15). Se aparta de la recomendación; sin librerías. |
| DP-3 | ¿Qué hace la pantalla si la imagen del QR llega vacía? | Tratarlo como error | **Tratarlo como error** (Hugo, 2026-11-15): vuelve al Teclado con "No se pudo mostrar el QR. Intenta de nuevo." y conserva lo escrito. Es un comportamiento nuevo para la spec: cambio **C-3** (abajo), ya aplicado como RF-078. |
| DP-4 | ¿Desde dónde se sirve la web? | Sitio estático aparte | **Lo decide #65** (Hugo, 2026-11-15). La web funciona de las dos formas (R-4). Si #65 elige servirla desde el backend, se propone entonces un `C-n` a la 001. |
| DP-5 | ¿Quién implementa y quién revisa? | Claude implementa, Hugo revisa | **Claude implementa, Hugo revisa** (Hugo, 2026-11-15), como se recomienda. Miguel o Beer17 revisan el pull request y prueban en su celular. |

**Cambios a la spec que salen del plan**

| # | Spec | Cambio propuesto | Origen | Estado |
|---|---|---|---|---|
| C-3 | 002 | Nuevo RF (No deseado) [C1]: SI el cobro creado llega sin imagen del QR, ENTONCES EL SISTEMA mostrará en la vista Teclado "No se pudo mostrar el QR. Intenta de nuevo." y conservará el monto y el concepto. Más su fila en §4 y que RF-015 lo excluya | DP-2, DP-3 | Aprobado y aplicado por Hugo el 2026-11-15 (RF-078) |

### 9.3 Revisión QA del plan (2026-11-15, una sola pasada)

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QP-1 | Promesa imposible | DP-9 abre un `EventSource` por cada cobro en escucha, y en el corte 2 puede haber unos 20 (§1, "Escala"). Pero Chrome y Safari abren como máximo **6 conexiones HTTP/1.1 por origen**, y cada canal ocupa una todo el tiempo. Con 6 canales abiertos, crear un cobro, ver o cancelar se quedan esperando: la pantalla deja de cobrar. En local siempre es HTTP/1.1 (uvicorn no tiene HTTP/2), y en producción depende del proxy de #65. | RF-009, RF-043, RF-030, RF-034 | Máximo **3 canales abiertos por pantalla**. El cobro en pantalla siempre tiene el suyo y los dos cobros anteriores más recientes usan los otros dos. El resto se sigue con la consulta del estado cada 3 s, igual que con RF-034. Quedan 3 conexiones libres para crear, ver y cancelar. No cambia la spec: "escuchar" incluye la consulta (glosario). | **Máximo 3 canales por pantalla** (Hugo, 2026-11-15), como se recomienda. Aplicada. |
| QP-2 | Contradicción | La política de seguridad de contenido de R-11 rompe dos cosas del propio plan: (a) el sonido es un WAV en un `blob:` (R-7) y `default-src 'self'` también aplica a `media-src`, así que no sonaría; (b) el quickstart (paso 3) conecta `http://localhost:5173` con `http://localhost:8000`, que `connect-src 'self' https:` bloquea. Además, `https:` permite conectar con cualquier sitio HTTPS. | RF-022, RF-077, RF-064 | Agregar `media-src 'self' blob:` y `http://localhost:8000` a `connect-src`. En el despliegue, #65 cambia `https:` por el dominio del servidor (quickstart, "Despliegue"). | **Ajustar la política** (Hugo, 2026-11-15): `media-src 'self' blob:`, `http://localhost:8000` en `connect-src`, y #65 cambia `https:` por el dominio del servidor. Como se recomienda. Aplicada. |
| QP-3 | Construibilidad | DP-15 corre `uv run --directory backend pytest ../web/tests -q`, pero pytest busca su configuración hacia arriba desde las pruebas, no desde `backend/`. Comprobado con una prueba de sonda en una carpeta aparte: el `rootdir` pasa a ser la carpeta de las pruebas, no se usa `backend/pyproject.toml` y pytest-asyncio avisa `PytestDeprecationWarning: … "asyncio_default_fixture_loop_scope" is unset`. | Principio V, DP-15 | Crear `web/pytest.ini` con `testpaths = tests` y `asyncio_default_fixture_loop_scope = function`, y correr `uv run --directory backend pytest ../web -q`. Se ajustan DP-15, el quickstart y la fila de `AGENTS.md` §6. | **`web/pytest.ini` propio** (Hugo, 2026-11-15) y el comando `uv run --directory backend pytest ../web -q`. Como se recomienda. Aplicada. |
| QP-4 | Construibilidad | `page.clock` solo controla los temporizadores de JavaScript (`Date`, `setTimeout`, `setInterval`). No controla los internos del navegador: el tiempo de espera de `AbortSignal.timeout()` ni la reconexión de `EventSource` (`retry: 3000`). §7 da por hecho que se controlan: "servidor que no responde, con el reloj adelantado 15 s" y las pruebas de reconexión. Además, con el reloj falso, CE-002 (menos de 2 s) no se puede medir con `Date`. | RF-013, RF-030, RF-031, CE-002, CE-003 | El tiempo de espera de 15 s se hace con `setTimeout` y `AbortController`, que sí controla `page.clock`. La reconexión se provoca desde el servidor simulado (cerrar el flujo o rechazarlo) y se espera en tiempo real, con un máximo de 5 s. CE-002 y CE-003 se miden con el reloj de Python alrededor de la espera. | **Ajustar diseño y pruebas** (Hugo, 2026-11-15): `setTimeout` con `AbortController`, reconexión provocada desde el servidor simulado y CE-002 y CE-003 medidos con el reloj de Python. Como se recomienda. Aplicada. |
| QP-5 | Construibilidad | Esta Mac corre Darwin 27, un macOS muy nuevo. Playwright publica sus navegadores por versión de macOS, y cuando sale una versión nueva a veces no hay WebKit para ella durante un tiempo. El plan da por hecho que WebKit (el motor de Safari) corre aquí con playwright 1.64.1. No se instaló para comprobarlo, porque son cientos de MB. | DP-1, CE-001 | La primera tarea de F1 instala los dos navegadores y corre una prueba vacía en cada uno. Si WebKit no arranca: se usa la versión más nueva de Playwright con soporte que tenga al menos dos semanas; si no hay ninguna, WebKit corre solo en la integración continua en Linux (#35) y en local solo Chromium, y se anota como TK. | **Comprobar en F1, con alternativa** (Hugo, 2026-11-15), como se recomienda. Aplicada. |

**Bloques de la pasada:**

1. **Coherencia interna**:
   - Los 78 RF tienen prueba en §7 y los 16 CE también.
   - RF-005, RF-021, RF-062 y RF-063 no tienen pieza en §4 (errata 1).
   - Los tiempos de espera de 15 s coinciden entre §4, §7 y el contrato de uso del servidor.
   - DP-1 a DP-17, C-2, C-3 y R-1 a R-14 existen y se citan bien.
   - La verificación de la constitución está completa y no quedan `[NECESITA ACLARACIÓN]`.
   - De aquí salen QP-2 y QP-3.
2. **Spec, otras specs, plan del hackathon, reglas e issues**:
   - Las fechas de los cortes y de las fases siguen §1.2 de la spec.
   - El C-2 está como F0, trabajo de la 001.
   - Las rutas y los códigos de la 001 que se citan existen en sus contratos (crear, ver, cancelar y canal).
   - Cumple las reglas: no hay llave en el cliente, hay cobro real y reacción visible.
   - El issue #64 sigue cubierto.
3. **Código (solo lectura)**:
   - H-1 a H-13 se comprobaron con su archivo y línea.
   - Las 104 pruebas del backend pasan.
   - El comportamiento de pytest se probó con una sonda en el directorio temporal (QP-3).
   - No hay un `pyproject.toml` en la raíz.
4. **API de pey**: la web no la usa directamente. Solo depende de que `qr_imagen` pueda llegar vacía, y eso ya lo cubren el C-3 y RF-078.
5. **Dependencias externas**:
   - #65 decide el hosting (DP-4) y aparece en el quickstart.
   - La disponibilidad de WebKit en esta Mac sale en QP-5.
   - El C-2 es un requisito previo con dueño (Hugo).
6. **Casos límite**: varios canales a la vez (QP-1), sonido bloqueado o en silencio (R-7), almacenamiento bloqueado (R-10), reloj desfasado (R-6), imagen vacía (RF-078) y tiempos internos del navegador (QP-4).
7. **Seguridad y rendimiento**:
   - La política de seguridad de contenido sale en QP-2.
   - `textContent` y la validación de lo recordado están cubiertos.
   - No hay secretos en la web.
   - CE-002 y CE-003 son medibles con QP-4.
8. **Construibilidad y reparto**:
   - El corte 2 queda en un día (§11).
   - Claude implementa y Hugo revisa (DP-5).
   - De aquí salen QP-3, QP-4 y QP-5.

**Erratas** (sin efecto en el comportamiento; aplicadas el 2026-11-15, a pedido de Hugo):

1. §4: agregar RF-005 (campo concepto en `vistas.js`), RF-021 (`Escuchas` solo avisa lo que trae el servidor), RF-062 (mensajes de `servidor.js` y `vistas.js`) y RF-063 (`servidor.js` y `config.js`).
2. §11: agregar el riesgo "la migración del backend a JavaScript deja sin entorno las pruebas de la web", con la mitigación "pasar entonces `web/` a su propio `pyproject.toml`".
3. §1, "Escala": mencionar el límite de canales del navegador (QP-1).

---

## 10. Seguridad

- **Secretos**: la web no tiene ninguno. `config.js` solo lleva la dirección pública del servidor. En el cierre de cada corte se corre `git grep` con patrones de llaves sobre `web/` (CE-010).
- **Firma de webhooks**: no aplica a la web; la verifica el servidor (spec 001).
- **Entradas**:
  - el teclado limita el monto (RF-003, RF-004, RF-068) y el campo, el concepto (RF-005), pero **el servidor sigue siendo quien valida** (spec 001, RF-002, RF-005, RF-042);
  - lo que llega del servidor o del almacenamiento se trata como texto (RF-077, DP-13), y lo recordado se valida antes de usarlo (DP-12).
- **Política de seguridad de contenido** (R-11, QP-2): scripts y estilos solo del propio sitio; imágenes del propio sitio y `data:` (para el QR); sonido del propio sitio y `blob:`; conexiones al propio sitio, a `http://localhost:8000` (pruebas en local) y a HTTPS. Al desplegar, #65 cambia `https:` por el dominio exacto del servidor.
- **Abuso de la demo pública**: los límites por IP y CORS son del servidor (spec 001). La web no reintenta crear un cobro por su cuenta, y Cobrar se bloquea mientras se crea (RF-011).
- **Lo recordado en el celular** (C2): solo identificadores de cobros. Quien tenga el celular podría verlos o cancelarlos, un supuesto ya aceptado en la spec 001 (§7).

---

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El C-2 no está aplicado al llegar F3 | La cuenta regresiva no cumple RF-019 ni CE-016 | F0 va primero; sin `hora_servidor` la pantalla usa el reloj del celular y avisa en consola, y el corte 1 no se cierra sin el C-2 |
| El primer cobro tarda de 7 a 9 s (H-11) | La demo arranca lenta | Vista Generando QR desde el primer instante (RF-010); en el ensayo, crear un cobro de calentamiento. Si molesta, decidir en un TK si se apaga la imagen de pey (DP-2 se reabre como TK) |
| La imagen del QR llega vacía | No hay QR que mostrar | RF-078 (error con mensaje, C-3); si pasa en pruebas reales, TK y reconsiderar dibujar el QR |
| El interruptor de silencio del iPhone calla el sonido | No suena en iPhone | `<audio>` en lugar de Web Audio (DP-10); la vista verde sigue avisando; se comprueba en F4 y se anota |
| Muchos cobros en escucha (corte 2) | Sin límite, los canales agotarían las 6 conexiones del navegador; además, las consultas cada 3 s multiplican las peticiones a pey | Máximo 3 canales por pantalla (QP-1); el resto, consulta cada 3 s. Limitación aceptada para las consultas (QA-3), que se observa en las pruebas reales |
| Corte 2 en un solo día (20 nov) | No llega antes del 21 nov | Empezar F6 en cuanto cierre F5. F6, F7 y F8 tocan los mismos archivos (`app.js`, `vistas.js`, `escucha.js`), así que van en serie; cada una es pequeña (QT-4 de tasks) |
| #65 no publica la web con HTTPS a tiempo | Sin Wake Lock y sin cierre del corte 1 en celulares | La sección "Despliegue" del quickstart lista lo que necesita #65; las pruebas automáticas no dependen del despliegue |
| Playwright tarda o falla al descargar navegadores, o WebKit no tiene versión para este macOS (QP-5) | Pruebas lentas, rotas o sin el motor de Safari | Primera tarea de F1 con prueba vacía en cada navegador; si WebKit no arranca, versión más nueva con soporte o WebKit solo en la integración continua en Linux (#35), y TK |
| El backend migra a JavaScript (decisión de Hugo del 14 nov, para después del MVP) | Las pruebas de la web se quedan sin el entorno de Python del backend | Pasar entonces `web/` a su propio `pyproject.toml` con uv (errata 2 de la QA del plan) |

---

## 12. Seguimiento de complejidad (Complexity Tracking)

> Se llena **solo** si la verificación de la constitución tiene excepciones que hay que justificar.

No hay excepciones.

---

## 13. Aprobación

- [x] Plan revisado con `/qa-spec 002 plan` y todos los hallazgos QP decididos (QP-1 a QP-5, aplicados).
- [x] C-3 decidido por Hugo: aprobado y aplicado el 2026-11-15.
- [x] Aprobado por Hugo el 2026-11-15. Aprobar no autoriza a empezar `tasks.md`: se espera a que Hugo lo pida.

---

## 14. Registro de implementación

| # | Fecha | Qué | Por qué | Afecta |
|---|---|---|---|---|
| TK-1 | 2026-11-15 | Las pruebas de reconexión ya no esperan en tiempo real a que el navegador reconecte el `EventSource`: el simulado rechaza el canal y la reconexión se hace con el reintento propio de 15 s, con reloj controlado. La reconexión automática del navegador se comprueba a mano en la guía de F4 | QT-2 de tasks: la constitución (principio V) prohíbe que las pruebas dependan del reloj real | §7, R-1 (QP-4), T029, T030 y T034 de tasks |
| TK-2 | 2026-11-15 | El silencio del iPhone (R-7) no se pudo comprobar en esta sesión: hace falta el iPhone de Hugo, con la web en la red local y un pago provocado. No queda anotado si suena o no. Los pasos están en la guía de F4 | T034 pide el resultado y aquí no hay un iPhone | R-7, T034, guía F4 |
| TK-3 | 2026-11-15 | Las pruebas que saltan 5 o 10 minutos de reloj usan `page.clock.fast_forward` en lugar de `run_for` (T035, T045 y la de Pago recibido de T029). `run_for(600_000)` dispara el `setInterval` de 250 ms unas 2400 veces y cada prueba tardaba 11 s en Chromium y 19 s en WebKit: la suite tardaba 267 s. `fast_forward` dispara los temporizadores una sola vez y la cuenta se recalcula con `Date.now()`, igual que cuando el celular se duerme | Principio V (rapidez de las pruebas); la suite bajó a unos 100 s con las mismas 176 pruebas | T029, T035 y T045 de tasks |
| TK-4 | 2026-11-15 | La recuperación registra primero los identificadores únicos y consulta cada cobro por separado. Si falla la consulta, conserva el identificador y reintenta a los 3 s. Durante la consulta inicial del cobro en pantalla se muestra «Reconectando…» | Una consulta lenta de un cobro anterior bloqueaba al de pantalla. Un fallo de red podía descartar un cobro vigente y el teclado podía permitir otro cobro mientras se recuperaba el de pantalla | R-10, RF-051, RF-052 y T056 |
| TK-5 | 2026-11-16 | Con SSE abierto, cada cobro en escucha consulta a los 8 s. Se serializan los GET, se descartan los estados anteriores y se usa `Avisados` para ambas fuentes. | En Android e iPhone, el túnel rápido de Cloudflare entregó las cabeceras y retuvo los eventos hasta cerrar la conexión. | C-4, RF-079, R-5, DP-9, T030 y T033. Verificación manual pendiente. |
| TK-6 | 2026-11-16 | El resultado de `play()` activa el aviso y el reintento si falla un sonido. Se prepara otro desbloqueo al volver a la página y se intenta usar la sesión `playback`. | La reproducción podía ser rechazada sin indicación en pantalla. | C-5, RF-054, R-7, DP-10, T018 y T056. Verificación manual pendiente. |
