# Plan: Cobro rápido — calculadora, duración del QR y descarga del código

- **Rama**: `feature/132-spec-004-cobro-rapido`
- **Fecha**: 2026-11-27 (borrador inicial 2026-11-26; actualizado y aprobado el 2026-11-27)
- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-26 (entrevista `E-1`–`E-9` y QA `QA-1`–`QA-8` aplicadas; ajuste puntual de `RF-038` por `QP-1` el 2026-11-27; cambios `C-12`, `C-13` y `C-14` aprobados y pendientes de aplicar)
- **Estado del plan**: `Aprobado` (2026-11-27; QA `QP-1`–`QP-7` y erratas aplicadas; esperando solicitud de Hugo para `/speckit-tasks`)
- **Entrada**: la spec de `specs/004-cobro-rapido/spec.md`

> **Notas para los comandos de spec-kit.**
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
> - Los títulos marcados entre paréntesis (*Technical Context*, *Constitution Check*, *Project Structure*, *Complexity Tracking*) son las secciones que espera `/speckit-plan`.
> - El plan se escribe en español.
> - El plan dice **CÓMO**. Cada pieza cita los RF de la spec que cumple.

---

## 0. Resumen

Esta spec extiende el backend FastAPI y la web PWA sin framework para incorporar: (1) **duración configurable del QR** en `POST /api/cobros` (de 6 min a 24 h en el Corte 1 sin migrar base de datos, y opción **Sin vencimiento** con duración `0` y ventana de escucha de 24 h en el Corte 2 con la migración `0004` coordinada con `#119`); (2) **calculadora exacta en el teclado de cobro** (`+`, `×` con precedencia estándar y redondeo mitad hacia arriba a 2 decimales usando `BigInt`, `⌫`, `C`, expresión secundaria y total grande); (3) **descarga local de la imagen PNG del QR** sin librerías ni endpoints nuevos; y (4) **tope de 20 minutos en cobros anteriores mayores a 1 hora** para proteger la cuota de pey, los 10 canales por IP y la pantalla encendida del celular. No agrega ninguna librería ni servicio externo nuevo (principio IX).

### 0.1 Hechos del código y de las fuentes

| # | Hecho | Evidencia |
|---|---|---|
| H-1 | Hoy `POST /api/cobros` solo lee `monto` y `concepto`, y pasa siempre `config.expiracion_segundos` (`600`) a `cobros.nuevo(...)` y a `pey.crear_qr(...)`. | `backend/app/main.py:95-105`, `:286-312`; `backend/app/config.py:34` |
| H-2 | `ClientePey.crear_qr` ya acepta `expiracion: int` y lo envía como `"expiration"` en `POST /codi/qr`. | `backend/app/pey.py:95-113` |
| H-3 | `docs.pey.mx/openapi.json` (versión `2026-10-20`, consultada el 2026-11-26) define `expiration` como `integer`, `minimum: 0`, `default: 0`, mínimo `360` cuando se fija vencimiento, sin máximo documentado; también documenta `429 CALL_LIMIT_REACHED`. | `https://docs.pey.mx/openapi.json` (`/codi/qr`) |
| H-4 | En PostgreSQL (`0001_esquema_inicial.sql`), `cobros.expira_en` es `timestamptz not null` con `check (expira_en > creado_en)` y `check (fin_ventana >= expira_en)`, y la vista `cobros_con_estado` compara `now() >= c.expira_en`. Para duraciones finitas (`360..86400`, Corte 1) no hace falta migrar nada porque `duracion_segundos == expira_en - creado_en`; para `Sin vencimiento` (`expira_en = NULL`, Corte 2) sí hace falta migración (`0004`, `#119`). | `supabase/migraciones/0001_esquema_inicial.sql:66-73`, `:116-138` (`:127`); `backend/app/almacen_postgres.py:398` |
| H-5 | `LatidoDeConciliacion` busca cobros únicamente por `fin_ventana > desde and fin_ventana <= hasta` (nunca lee `expira_en`). Manteniendo `fin_ventana` obligatorio (`creado_en + 86400` en cobros sin vencimiento), la conciliación de la spec 003 (`RF-061`) funciona sin cambios en `tareas.py`. | `backend/app/almacen_postgres.py:81-90`; `backend/app/tareas.py:124-131` |
| H-6 | `Cobro.estado(ahora)` y `canal.py:_espera` comparan `ahora` con `cobro.expira_en` asumiendo que es `int` no nulo; en Corte 2 deberán comprobar `expira_en is not None`. | `backend/app/cobros.py:102-110`; `backend/app/canal.py:22-23` |
| H-7 | `web/js/teclado.js` implementa solo `0`–`9`, `punto` y `borrar` sobre una cadena única; `web/js/cuenta.js` solo formatea `m:ss` y resta `cobro.expira_en - (ahora + desfase)`. | `web/js/teclado.js:11-66`; `web/js/cuenta.js:26-43` |
| H-8 | `web/js/vistas.js` ya pinta el QR como `data:image/png;base64,${qr_imagen}` y `web/index.html` tiene CSP `img-src 'self' data:`; `web/js/escucha.js` mantiene hasta 3 canales SSE + polling cada 3 s para cobros anteriores sin tope propio. | `web/js/vistas.js:364`; `web/index.html:9`; `web/js/escucha.js:306-441` |
| H-9 | `web/js/memoria.js` valida estrictamente las claves de `localStorage` (`en_pantalla` y `anteriores`, `RF-077` de la 002), rechazando cualquier forma inválida. | `web/js/memoria.js:59-82` |
| H-10 | El rediseño UX/UI en la rama remota `origin/feature/web-ux-landing-login-dashboard` (`2d7652e`, `#118`) usa exactamente los mismos módulos JS sin framework (`teclado.js`, `cuenta.js`, `escucha.js`) y los mismos `data-prueba` de las 6 vistas de cobro. | Inspección de solo lectura de `2d7652e` (2026-11-26) |

---

## 1. Contexto técnico (Technical Context)

- **Lenguaje y versión**: Python 3.11+ (backend), JavaScript ES Modules nativo + HTML5 + CSS3 (web), SQL PostgreSQL 17 (migración Corte 2).
- **Dependencias principales**: las ya instaladas — FastAPI, `httpx`, `pydantic-settings`, `standardwebhooks`, `psycopg[binary]`, `psycopg-pool` en backend; **cero dependencias** en la web. Sin librerías nuevas (principio IX).
- **Almacenamiento**: Supabase (PostgreSQL) con `AlmacenPostgres` y `AlmacenEnMemoria` para pruebas; `localStorage` del navegador para cobros en escucha y topes de 20 min de anteriores largos.
- **Pruebas**: `pytest` + `pytest-asyncio` con `PeySimulado`, `RelojFalso` y PostgreSQL desechable (`PRUEBAS_DATABASE_URL`) en backend; `pytest` + Playwright (Chromium y WebKit) contra `servidor_simulado.py` en la web; `ruff check` y `ruff format --check`.
- **Plataforma de destino**: servidor local en la computadora de la demo expuesto por Tailscale Funnel con HTTPS (spec 003); navegador móvil (Android Chrome, iPhone Safari) desde 320 px de ancho.
- **Tipo de proyecto**: API web (FastAPI) + PWA sin framework (`web/`) + migraciones SQL (`supabase/migraciones/`).
- **Metas de rendimiento**: QR visible en `<= 5 s` en 9 de cada 10 intentos desde la demo pública (`CE-007`, alineado con `spec 003 C-10`); cuenta regresiva con error máximo de `2 s` respecto al servidor (`CE-005`); actualización instantánea de expresión y total en cada toque de la calculadora.
- **Restricciones**: un solo proceso del servidor; API key y secretos nunca salen del backend; CSP estricta sin `eval` ni scripts inline; sin dependencias nuevas; Corte 1 sin migración de base de datos para desbloquear la puerta S2 (29 nov).
- **Escala**: un negocio de demo y negocios piloto; límite de 10 cobros/minuto y 10 canales abiertos por IP; tope de 20 min en cobros anteriores > 1 h para proteger cuota de pey y Wake Lock.

---

## 2. Verificación de la constitución (Constitution Check)

*Revisada antes de la Fase 0 y reconfirmada después del diseño de la Fase 1 (contratos y modelo de datos).*

| Principio de la constitución | Cómo lo cumple este plan | Estado |
|---|---|---|
| **I. El pago se confirma en el servidor** | La calculadora solo calcula el monto previo; ni la web ni el botón Descargar QR ni el selector de duración pueden marcar un cobro como pagado. En QR sin vencimiento, los pagos siguen confirmándose únicamente por webhook firmado o consulta del backend (`RF-010`, `RF-012`). | Cumple |
| **II. Una orden nunca se ejecuta dos veces** | La deduplicación por `webhook-id` y `transactionId` (`Almacen.registrar_pago`) y el registro de pagos avisados en pantalla (`Avisados`) no cambian; funciona igual tras 24 h o 48 h en QR sin vencimiento (`RF-012`, `CE-010`). | Cumple |
| **III. Los secretos nunca salen del backend** | No se agregan credenciales nuevas; la web sigue hablando exclusivamente con el backend de PAGO FÁCIL (`RF-043`). | Cumple |
| **IV. Alcance anclado y trabajo documentado** | Solo construye los RF aprobados de la Spec 004 (`#132`, `#120`, `#100`, `#121` y migración `#119` en C2); mantiene `#118` y `#115` fuera de alcance; `C-12`, `C-13` y `C-14` están aprobados y trazados. | Cumple |
| **V. Pruebas primero, en todo** | Todas las tareas de backend, migración y web siguen pruebas primero con `PeySimulado`, `RelojFalso`, `servidor_simulado.py` y PostgreSQL desechable, con nombres en español. Los cobros reales de `$0.01` quedan solo en validación manual con autorización de Hugo. | Cumple |
| **VI. CoDi real, reacción real** | `quickstart.md` y la estrategia de pruebas incluyen cobros reales de `$0.01` para duración distinta a 10 min (`CE-001`), 24 h, cuenta de 3+ términos en calculadora (`CE-002`) y Sin vencimiento (`CE-009`). | Cumple |
| **VII. Pensado para el mostrador** | Atajos de un toque (6 min, 10 min, 30 min, 1 h, 24 h, Sin vencimiento), teclas táctiles ≥ 44×71 px en 320 px sin scroll horizontal (`RF-042`, `CE-008`), nombres accesibles en español (`RF-048`) y mensajes de error para el dueño (`RF-043`). | Cumple |
| **VIII. Un pago no prueba identidad ni entrega** | Pago tardío cubierto en cobros finitos (+10 min de gracia + webhook siempre) y en cobros sin vencimiento (24 h de escucha + conciliación + webhook siempre, `RF-011`, `RF-012`); monto distinto, fallas de pey y devoluciones mantienen las reglas de la 001. | Cumple |
| **IX. Lo más simple que gane la demo** | Cero librerías ni servicios nuevos; Corte 1 evita bloquearse en migraciones de BD; `BigInt` nativo para la calculadora; `Blob` nativo para descargar el PNG que ya tiene la pantalla. | Cumple |
| **X. Si no se ve, no existe** | Cada cobro creado registra su `duracion_segundos` junto con `cobro` y `codi_qr_id` (sin secretos ni datos bancarios) y los errores de pey siguen anotando `requestId`. | Cumple |

---

## 3. Estructura del proyecto (Project Structure)

### 3.1 Documentación de esta funcionalidad

```text
specs/004-cobro-rapido/
├── spec.md                              # Aprobada (2026-11-26, E-1..E-9, QA-1..QA-8; RF-038 ajustado por QP-1 el 2026-11-27)
├── checklists/
│   └── requirements.md                  # Calidad de la spec validada
├── plan.md                              # Este archivo (/speckit-plan)
├── research.md                          # Fase 0: decisiones R-1 a R-9
├── data-model.md                        # Fase 1: entidades, estados, migración 0004 y localStorage
├── contracts/
│   ├── crear-cobro-duracion.md          # Contrato POST /api/cobros, objeto cobro y canal SSE
│   ├── vistas-cobro-rapido.md           # Contrato DOM, data-prueba y accesibilidad
│   └── calculadora-y-descarga.md        # Contrato de teclado.js y descarga.js
├── quickstart.md                        # Fase 1: guía de comprobación de punta a punta
├── tasks.md                             # Pendiente (/speckit-tasks, cuando Hugo lo pida)
└── verification-guide.md                # Verificación manual de cada fase (durante implementación)
```

### 3.2 Código fuente (raíz del repositorio)

```text
backend/
├── app/
│   ├── main.py               # [MODIFICAR] validar_duracion, leer_solicitud, crear_cobro, log de duración
│   ├── cobros.py             # [MODIFICAR] Cobro.expira_en int|None, propiedad duracion_segundos, estado() y publico()
│   ├── canal.py              # [MODIFICAR en C2] _espera tolera expira_en = None
│   ├── almacen.py            # [MODIFICAR en C2] _CobroPlano.expira_en int|None
│   └── almacen_postgres.py   # [MODIFICAR en C2] _instante_o_nada / _unix_o_nada para expira_en anulable
└── tests/
    ├── test_crear_cobro.py            # [MODIFICAR] actualizar CAMPOS_COBRO (16→17 claves con duracion_segundos, C-12, QP-3); pruebas de duración finita, defecto y rechazos 422 (C1) y 0 (C2)
    ├── test_modelo.py                 # [MODIFICAR] pruebas de Cobro.duracion_segundos y expira_en = None (C1/C2)
    ├── test_canal.py                  # [MODIFICAR] pruebas de ventana larga y sin vencimiento sin evento vencido (C1/C2)
    ├── test_conciliacion.py           # [MODIFICAR en C2] conciliación a las 24 h y webhook a las 48 h (CE-010)
    ├── test_migraciones_postgres.py   # [MODIFICAR en C2] actualizar _versiones a 0001..0004 (C-14, QP-3); validar idempotencia y permisos revocados en cobros_con_estado tras 0004 (QP-6)
    └── test_esquema_postgres.py       # [MODIFICAR en C2] pruebas de expira_en NULL y vista cobros_con_estado

supabase/
└── migraciones/
    └── 0004_cobros_sin_vencimiento.sql  # [NUEVO en C2, #119] expira_en anulable, checks idempotentes, vista cobros_con_estado (security_invoker) y revoke all (QP-6)

web/
├── estilos.css               # [MODIFICAR] .teclas en 4 columnas, .expresion, .selector-duracion, 320 px
├── js/
│   ├── teclado.js            # [MODIFICAR] motor calculadora BigInt (+, ×, ⌫, C, precedencia, redondeo, tope 20 y $999,999.99)
│   ├── cuenta.js             # [MODIFICAR] formato H:MM:SS y M:SS, es_sin_vencimiento, restante_ventana, puede_reabrir_qr (QP-4)
│   ├── descarga.js           # [NUEVO] nombre_archivo_qr y descargar_qr (PNG vía Blob)
│   ├── servidor.js           # [MODIFICAR] enviar duracion_segundos en crear_cobro (parámetro opcional; omite clave si undefined, QP-2)
│   ├── escucha.js            # [MODIFICAR] tope de 20 min para cobros anteriores > 1 h (RF-044, cálculo diferido de tope_local, QP-4) y fin en sin vencimiento
│   ├── memoria.js            # [MODIFICAR] topes_anteriores opcional validado estrictamente (RF-077); omite clave cuando esté vacía (QP-3)
│   ├── vistas.js             # [MODIFICAR] expresión, teclas +, ×, C, selector de duración, Descargar QR, aviso 24 h, aria-label
│   └── app.js                # [MODIFICAR] estado de expresión/duración, reinicio a 10 min, descarga, puede_reabrir_qr y manejo de C2 (QP-4)
└── tests/
    ├── servidor_simulado.py          # [MODIFICAR] aceptar y validar duracion_segundos, registrar última petición
    ├── test_teclado.py               # [MODIFICAR] pruebas de calculadora completa y bordes (C1)
    ├── test_crear_y_mostrar_qr.py    # [MODIFICAR en F3] actualizar aserto de pantalla :313 para esperar duracion_segundos: 600 (C-13, QP-2), manteniendo intacta la unitaria :128
    ├── test_monto_libre_y_reuso.py   # [MODIFICAR en F3] actualizar aserto de pantalla :54 para esperar duracion_segundos: 600 (C-13, QP-2)
    ├── test_duracion_y_descarga.py   # [NUEVO] selector de duración, H:MM:SS, descarga PNG, tope 20 min y C2 Sin vencimiento
    └── test_seguridad.py             # [MODIFICAR] XSS en expresión, saneamiento de nombre PNG y topes_anteriores malformados
```

**Decisión de estructura**: se amplían los módulos existentes para mantener una sola base de código coherente con las specs 001–003 y compatible con el rediseño `#118`. Solo se agregan dos archivos nuevos de producción: `web/js/descarga.js` (para aislar la lógica de descarga PNG y saneamiento de nombres) y `supabase/migraciones/0004_cobros_sin_vencimiento.sql` (exclusivamente en Corte 2).

---

## 4. Módulos y piezas con comportamiento

| Pieza | Responsabilidad | Requisitos |
|---|---|---|
| `backend/app/main.py` (`validar_duracion`, `leer_solicitud`, `crear_cobro`) | Valida `duracion_segundos` (defecto 600 s, rango 360..86 400 s en C1, más `0` en C2; rechaza `bool`, `float`, texto y fuera de rango con 422 antes del límite por IP y de pey) y pasa `expiracion` a pey registrando la duración en el log. | RF-001, RF-002, RF-003, RF-006, RF-008, RF-012, RF-043 |
| `backend/app/cobros.py` (`Cobro`, `RepositorioCobros.nuevo`) | Calcula `expira_en` (`creado_en + duracion` o `None` si `0`), `fin_ventana` (`expira_en + gracia` o `creado_en + 86 400` si `0`), propiedad `duracion_segundos`, evita pasar a `vencido` si `expira_en is None` y expone `duracion_segundos` en `publico()`. | RF-003, RF-004, RF-005, RF-007, RF-008, RF-009, RF-010, RF-011 |
| `backend/app/canal.py` (`_espera`, `flujo_de_avisos`) | Mantiene el canal abierto durante `fin_ventana`, omite comprobación de `expira_en` cuando es `None` (nunca emite `vencido`) y emite `fin` al cumplirse 24 h. | RF-005, RF-009, RF-010, RF-011 |
| `backend/app/almacen.py` y `backend/app/almacen_postgres.py` + `supabase/migraciones/0004_cobros_sin_vencimiento.sql` | Persiste y recupera `expira_en` anulable en Corte 2 manteniendo `fin_ventana not null` para `LatidoDeConciliacion`, con migración `0004` idempotente sobre `pg_constraint`, vista `cobros_con_estado` (`security_invoker = true`) y `revoke all` a `anon`/`authenticated` (`QP-6`). | RF-007, RF-008, RF-009, RF-011, RF-012 |
| `web/js/teclado.js` | Aplica teclas (`0`–`9`, `.`, `⌫`, `+`, `×`, `C`), normaliza punto final/inicial, limita a 20 operandos y evalúa con `BigInt` exacto (`×` antes de `+`, redondeo mitad hacia arriba a 2 decimales, total parcial con operador final, tope `$999,999.99`, reglas de `Cobrar` y `Monto libre` bajo `QP-1` y bordes de `QP-5`). | RF-028 a RF-041, RF-045, RF-046, RF-047 |
| `web/js/cuenta.js` | Formatea `H:MM:SS` (`>= 3600 s`) y `M:SS` (`< 3600 s`) con desfase del servidor; detecta cobros sin vencimiento, calcula `restante_ventana` para la ventana de 24 h y expone `puede_reabrir_qr(cobro, desfase, ahora)` (`QP-4`). | RF-019, RF-020, RF-021, RF-022 |
| `web/js/descarga.js` | Sanea y construye el nombre `.png` descriptivo y descarga el PNG base64 vía `Blob` + `URL.createObjectURL` manejando errores sin alterar la vista ni la escucha. | RF-025, RF-026, RF-027 |
| `web/js/servidor.js` | Acepta `duracion_segundos` como 3.er parámetro opcional en `crear_cobro` (omite la clave del JSON si es `undefined` para compatibilidad unitaria; `app.js` siempre la envía desde Cobrar y Monto libre, `QP-2`). | RF-016, RF-039, RF-043 |
| `web/js/escucha.js` y `web/js/memoria.js` | Conserva duración y condición sin vencimiento al recuperar tras recargar; acota a 20 min la escucha de cobros anteriores > 1 h (`24 h` y `Sin vencimiento`) con cálculo diferido de `tope_local` en la primera respuesta de recuperación si `pasar_a_anterior()` ocurrió con `cobro === null` (`QP-4`), guardando `topes_anteriores` validado estrictamente y omitiendo esa clave en `localStorage` cuando esté vacía (`QP-3`). | RF-024, RF-044 |
| `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css` | Renderiza expresión secundaria, total grande, teclado 4 columnas (`⌫` en `tecla-borrar`), selector de duración con reinicio a `10 min` y conservación en error, botón **Descargar QR**, etiqueta `"Sin vencimiento"`, usa `puede_reabrir_qr()` en los 4 sitios de `app.js` (`:88`, `:314`, `:380-399`, `:424`) y dispara la transición idempotente de fin de 24 h (`RF-023`, ocultando `Cancelar cobro` / `Mostrar QR otra vez`) tanto por `escuchas.fin` como por `empezar_cuenta` cuando `restante_ventana < 1` (`QP-4`), con layout 320 px sin scroll horizontal y nombres accesibles `aria-label` / `role`. | RF-013 a RF-027, RF-031, RF-032, RF-037 a RF-043, RF-047, RF-048 |

---

## 5. Contratos

Cada interfaz pública o de pruebas tiene su contrato en `contracts/`:

| Contrato | Archivo | Requisitos |
|---|---|---|
| `POST /api/cobros` con `duracion_segundos`, objeto cobro ampliado y canal SSE en C2 | [contracts/crear-cobro-duracion.md](contracts/crear-cobro-duracion.md) | RF-001 a RF-012, RF-043 |
| Vistas ampliadas (`vista-teclado`, `vista-qr`, `vista-pagado`), `data-prueba` y accesibilidad | [contracts/vistas-cobro-rapido.md](contracts/vistas-cobro-rapido.md) | RF-013 a RF-042, RF-044 a RF-048 |
| Funciones puras de calculadora (`teclado.js`) y descarga PNG (`descarga.js`) | [contracts/calculadora-y-descarga.md](contracts/calculadora-y-descarga.md) | RF-025 a RF-041, RF-045 a RF-047 |

Al cerrar el Corte 1 y el Corte 2 (fase FN), se reflejarán los cambios ya aprobados `C-12`, `C-13` y `C-14` en las specs y contratos de `001-backend-mvp`, `002-web-mvp` y `003-infraestructura-demo`.

---

## 6. Modelo de datos

El detalle completo está en [data-model.md](data-model.md):

- **Corte 1**: no requiere migraciones de base de datos; `Cobro` deriva `duracion_segundos = expira_en - creado_en` sobre el esquema existente (`0001`–`0003`) y la calculadora vive como estado transitorio en el navegador.
- **Corte 2**: agrega `supabase/migraciones/0004_cobros_sin_vencimiento.sql` (`expira_en` anulable, checks actualizados y vista `cobros_con_estado` sin marcar `NULL` como vencido) manteniendo `fin_ventana not null` (`creado_en + 86 400`) para que la conciliación `RF-061` funcione sin cambios.
- **`localStorage`**: agrega el mapa opcional `topes_anteriores` (validado estrictamente por `RF-077`) para recordar el límite de 20 min de los cobros anteriores > 1 h tras una recarga.

---

## 7. Estrategia de pruebas

- **Pruebas primero (principio V)**: cada historia y tarea de implementación escribe primero sus pruebas, las ve fallar por la razón esperada y después implementa.
- **Pruebas automáticas aisladas**: nunca llaman al pey real ni a Supabase real; usan `PeySimulado`, `RelojFalso`, `AlmacenEnMemoria`, PostgreSQL 17 desechable (`PRUEBAS_DATABASE_URL`) y `servidor_simulado.py`.
- **Pruebas reales ($0.01 MXN)**: solo en la verificación manual de cierre de Corte 1 y Corte 2 con autorización explícita de Hugo (`CE-001`, `CE-002`, `CE-006`, `CE-007`, `CE-009`).
- **Nombres en español**: todas las pruebas nuevas se nombran en español describiendo el comportamiento.
- **Compatibilidad y asertos existentes (`QP-1`–`QP-3`, `QP-6`)**:
  - Se actualizan de forma explícita: `CAMPOS_COBRO` (16→17 claves con `duracion_segundos`) en `backend/tests/test_crear_cobro.py` en **F1** (`C-12`, `QP-3`); los 2 asertos de pantalla `web/tests/test_crear_y_mostrar_qr.py:313` y `web/tests/test_monto_libre_y_reuso.py:54` en **F3** para esperar `duracion_segundos: 600` (`C-13`, `QP-2`); y `_versiones` (`0001`..`0004`) junto con la validación de idempotencia y permisos revocados de `cobros_con_estado` en `backend/tests/test_migraciones_postgres.py` en **F6** (`C-14`, `QP-3`, `QP-6`).
  - Se conservan intactas y en verde sin modificarlas: `web/tests/test_crear_y_mostrar_qr.py:128` (`QP-2`), `web/tests/test_teclado.py:97-116` (`QP-1`), `web/tests/test_monto_libre_y_reuso.py:43-45` (`QP-1`) y `web/tests/test_recuperar.py` (`QP-3`).

| Requisitos | Pruebas (archivo y casos clave) | Tipo |
|---|---|---|
| RF-001, RF-002, RF-003, RF-006, RF-007, RF-043, CE-003, CE-004 | `backend/tests/test_crear_cobro.py`: actualizar `CAMPOS_COBRO` a 17 claves con `duracion_segundos` en F1 (`C-12`, `QP-3`); `test_sin_duracion_usa_diez_minutos_por_defecto`, `test_duracion_finita_valida_se_envia_a_pey_y_fija_vencimiento` (360, 1800, 86400), `test_duracion_invalida_se_rechaza_sin_llamar_a_pey` (<360, >86400, negativo, decimal, booleano, texto, y 0 en C1) | Integración (FastAPI + `PeySimulado`) |
| RF-004, RF-005, RF-007 | `backend/tests/test_modelo.py` y `backend/tests/test_canal.py`: `test_cobro_con_duracion_elegida_vence_a_su_hora_y_mantiene_diez_minutos_de_gracia`, `test_canal_cierra_al_terminar_ventana_de_duracion_elegida` | Unitaria / asíncrona (`RelojFalso`) |
| RF-008, RF-009, RF-010, RF-011, RF-012, CE-010 | `backend/tests/test_crear_cobro.py`, `test_canal.py`, `test_conciliacion.py`: `test_cobro_sin_vencimiento_envia_cero_a_pey_y_no_tiene_expira_en`, `test_cobro_sin_vencimiento_nunca_vence_ni_emite_vencido`, `test_cobro_sin_vencimiento_cierra_canal_y_concilia_a_las_24_horas`, `test_aviso_firmado_a_las_48_horas_registra_pago_en_cobro_sin_vencimiento` | Integración / asíncrona (`RelojFalso`) |
| RF-008, RF-009 (persistencia C2) | `backend/tests/test_migraciones_postgres.py` y `test_esquema_postgres.py`: actualizar `_versiones` a `0001..0004` en F6 (`C-14`, `QP-3`), `test_migracion_0004_es_idempotente_y_admite_cobro_sin_vencimiento`, validación de permisos revocados a `anon`/`authenticated` en `cobros_con_estado` tras `0004` (`QP-6`), y `test_vista_cobros_con_estado_no_vence_cobro_sin_expira_en` | Integración (PostgreSQL desechable) |
| RF-028 a RF-041, RF-045 a RF-047, CE-002 | `web/tests/test_teclado.py`: pruebas de `+`, `×` con precedencia, `1.25 × 1.30 = 1.63`, `0.1 + 0.2 = 0.30`, expresión secundaria vs monto simple, operador final con total parcial y Cobrar/Monto libre desactivados, `0 × 25`, `25.` + `+`, `25 + .5`, `25 + 0.`, `25 + 10.`, `25 + 0` + `7` (`QP-5`), tope 20 operandos, desbordamiento > `$999,999.99`, `⌫`, `C`, envío de total único con concepto independiente y conservación de expresión en error del servidor; conserva en verde `test_teclado.py:97-116` y `test_monto_libre_y_reuso.py:43-45` (`QP-1`) | Integración web (Playwright) |
| RF-013 a RF-024, RF-044, CE-005 | `web/tests/test_duracion_y_descarga.py` + actualización en F3 de `test_crear_y_mostrar_qr.py:313` y `test_monto_libre_y_reuso.py:54` (`duracion_segundos: 600`, `C-13`, `QP-2`; intactas `test_crear_y_mostrar_qr.py:128` y `test_recuperar.py`, `QP-2`/`QP-3`): atajos `6 min`–`24 h` (y `Sin vencimiento` en C2), defecto `10 min`, reinicio en Nuevo cobro/cancelar/recarga, conservación en error, cuenta `H:MM:SS` con reloj desfasado 5 min (`CE-005`), recuperación tras recarga (incluido `tope_local` diferido si `cobro === null`, `QP-4`), tope de 20 min en cobro anterior de 24 h / Sin vencimiento (`RF-044`), aviso de fin de 24 h por `escuchas.fin` y por reloj local en `empezar_cuenta` ocultando `Cancelar cobro` y `Mostrar QR otra vez` (`RF-022`, `RF-023`, `QP-4`) | Integración web (Playwright) |
| RF-025, RF-026, RF-027, CE-006 | `web/tests/test_duracion_y_descarga.py`: `test_descargar_qr_guarda_png_con_nombre_descriptivo_sin_salir_ni_cortar_escucha`, `test_descargar_qr_disponible_tras_recargar_y_mostrar_qr_otra_vez`, `test_error_al_descargar_qr_muestra_mensaje_sin_ocultar_qr` | Integración web (Playwright `expect_download`) |
| RF-042, RF-043, RF-048, CE-008 | `web/tests/test_duracion_y_descarga.py` y `web/tests/test_seguridad.py`: ancho 320 px sin scroll horizontal con expresión larga y selector, `aria-label`/`role` en español, sin XSS en expresión ni nombres de archivo PNG, `topes_anteriores` malformados descartados en `localStorage` | Integración web (Playwright) |
| CE-001, CE-002, CE-006, CE-007, CE-009 | Verificación manual con `$0.01` en demo pública (Android + iPhone) siguiendo `quickstart.md` §4 con autorización de Hugo | Manual |

---

## 8. Plan de implementación

> **Prerequisito de entorno antes de empezar TDD en F1 (`QP-7`)**: ejecutar `uv sync --directory backend --locked` para sincronizar `backend/.venv` (incluyendo `psycopg` de la spec 003) antes de correr `pytest`.

| Fase | Corte | Fecha meta | Quién | Qué | Depende de |
|---|---|---|---|---|---|
| **F1** | C1 | 27 nov | Hugo (`#120`) | Backend de duración finita (`360..86400` s, defecto `600`), `duracion_segundos` en `Cobro.publico()`, validación 422, actualización de `CAMPOS_COBRO` (`C-12`, `QP-3`) y pruebas con `RelojFalso` y `PeySimulado`. | Plan y `tasks.md` aprobados + `uv sync --directory backend --locked` |
| **F2** | C1 | 27 nov | Leonel (`#100`) | Calculadora exacta `BigInt` en `web/js/teclado.js`, vista Teclado 4 columnas (`expresion`, `+`, `×`, `⌫`, `C`, accesibilidad, 320 px) y pruebas en `web/tests/test_teclado.py`. | Plan y `tasks.md` aprobados (en paralelo con F1) |
| **F3** | C1 | 28 nov | Leonel (`#121`) | Selector de duración (`6 min`–`24 h`), envío en `servidor.js` (`duracion_segundos` opcional, `QP-2`), cuenta `H:MM:SS` y `puede_reabrir_qr` en `cuenta.js` (`QP-4`), reinicio a `10 min`, tope de 20 min en cobros anteriores > 1 h (`escucha.js`, `memoria.js`), `servidor_simulado.py`, actualización de los 2 asertos de pantalla (`C-13`) y pruebas Playwright. | F1 y F2 (ramificada tras `#100`) |
| **F4** | C1 | 28 nov | Leonel (`#121`) | Módulo `web/js/descarga.js`, botón **Descargar QR** y manejo de error en `vistas.js`/`app.js`, pruebas de descarga y seguridad. | F3 |
| **F5** | C1 | dom 29 nov (puerta S2) | Hugo y Leonel | Cierre del Corte 1: `pytest` (servidor y web), `ruff`, prueba en 320 px y cobros reales de `$0.01` (duración distinta a 10 min, 24 h, calculadora 3+ términos y descarga PNG). | F1–F4 |
| **F6** | C2 | 29–30 nov | Juan (`#119`) y Hugo (`#120`) | Migración `0004_cobros_sin_vencimiento.sql` idempotente con `revoke all` (`QP-6`), `expira_en: int \| None` en `cobros.py`, `canal.py`, `almacen.py`, `almacen_postgres.py`, habilitar `duracion_segundos = 0` en `main.py`, actualización de `_versiones` (`C-14`, `QP-3`), pruebas con PostgreSQL desechable, conciliación a 24 h y webhook a 48 h. | F5 y `#119` |
| **F7** | C2 | 30 nov – 1 dic | Leonel (`#121`) | Opción **Sin vencimiento** (`duracion-0`), etiqueta `"Sin vencimiento"`, transición idempotente de fin de 24 h en vista QR (oculta `Cancelar cobro`) por `escuchas.fin` y reloj local (`QP-4`), ocultado de `Mostrar QR otra vez`, recuperación tras recarga y pruebas Playwright. | F6 |
| **FN** | C1+C2 | 1 dic | Hugo y Leonel | Aplicar textos de `C-12`, `C-13` y `C-14` en specs 001–003, revisión de seguridad, validación completa de `quickstart.md`, cobro real `$0.01` Sin vencimiento (`CE-009`) y guía de verificación final. | F7 |

### 8.1 Estrategia de ramas y PRs por issue (`QP-7`)

Para cumplir la forma de trabajar de la constitución (una rama y un PR por issue, revisados y unidos a `main`) y evitar conflictos entre tareas de la web:

| Issue | Fases | Rama / PR | Base y orden |
|---|---|---|---|
| `#132` | Spec, plan y `tasks.md` | `feature/132-spec-004-cobro-rapido` | Sale de `main` y se une primero (documentación). |
| `#120` | **F1** (backend duración finita) | Rama propia del issue `#120` (Corte 1) | Sale de `main`; corre en paralelo con `#100`. |
| `#100` | **F2** (calculadora en web) | Rama propia del issue `#100` | Sale de `main`; corre en paralelo con `#120`. |
| `#121` | **F3–F4** (selector duración, cuenta `H:MM:SS`, tope 20 min y Descargar QR) | Rama propia del issue `#121` (Corte 1) | Sale **tras unir `#100`** (o sobre su rama base) para evitar choques en `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css`. |
| `#119` + `#120` | **F6** (migración `0004` + backend Sin vencimiento) | PR de `#119` (migración `0004`, Juan) seguido de PR de `#120` Corte 2 (backend, Hugo) | Tras cierre de Corte 1 (`F5`); `#120` Corte 2 integra la migración de `#119`. |
| `#121` | **F7** (web Sin vencimiento) y cierre `FN` | Rama propia del issue `#121` (Corte 2) | Sale tras unir F6 (`#119` + `#120` Corte 2). |

---

## 9. Decisiones

### 9.1 Decisiones del plan

| # | Decisión | Por qué | Alternativas descartadas |
|---|---|---|---|
| DP-1 | Campo JSON `duracion_segundos` (entero opcional, defecto `600`, validado antes del límite por IP y de pey; `360..86400` en C1 y más `0` en C2). | Idioma español en código y contratos (constitución); 100 % retrocompatible con specs 001 y 002; coherente con `openapi.json` de pey (`R-1`). | `expiration` en inglés; duración en minutos; lista cerrada en servidor (descartada en E-1). |
| DP-2 | Derivar `duracion_segundos` de `expira_en - creado_en` (o `0` si `expira_en is None`) y mantener `fin_ventana not null` (`creado_en + 86 400` en sin vencimiento), con migración `0004` solo en Corte 2. | Desbloquea Corte 1 sin esperar `#119`; evita columnas duplicadas y mantiene `LatidoDeConciliacion` sin cambios (`R-2`). | Columna redundante `duracion_segundos` en BD; fecha centinela año 9999. |
| DP-3 | En Corte 2, `Cobro.estado()` y `canal.py:_espera()` tratan `expira_en is None` como "nunca vence"; webhooks posteriores a 24 h siguen registrando sin cambio en `POST /webhooks/pey`. | Cambio mínimo de 2 guardas sobre lógica ya probada (`R-3`). | Canal SSE separado para QR sin vencimiento. |
| DP-4 | Motor de calculadora en `web/js/teclado.js` usando cadena canónica y aritmética decimal exacta sobre `BigInt` (`×` antes que `+`, redondeo `HALF_UP`, tope 20 operandos y `$999,999.99`). | Cero dependencias nuevas, sin errores binarios IEEE-754 ni `eval()`, y 100 % reutilizable con `#118` (`R-4`). | `decimal.js`/`big.js` (nueva dependencia); `Number` flotante; `eval()`. |
| DP-5 | `cuenta.js` formatea `H:MM:SS` desde 3600 s y `M:SS` debajo de 3600 s; `restante()` devuelve `null` en sin vencimiento, `restante_ventana()` controla las 24 h en UI y `puede_reabrir_qr()` unifica los 4 cheques de vigencia/ventana en `app.js` (`QP-4`). | Conserva compatibilidad total con pruebas de spec 002 (`"10:00"`) y evita falsos `qr_vencido` (`R-5`). | Formato `0:10:00` siempre. |
| DP-6 | Descarga PNG en `web/js/descarga.js` con `Blob` + `URL.createObjectURL` + `<a download>` y saneamiento estricto del nombre `.png`. | Sin peticiones extra al servidor ni cambios de CSP; determinista en Playwright `expect_download` (`R-6`). | `data:` URL directa en `<a>`; endpoint nuevo en backend. |
| DP-7 | Tope local de 20 min en `escucha.js` para cobros anteriores > 1 h (`24 h` y `Sin vencimiento`, con cálculo diferido si `cobro === null`, `QP-4`), persistido en `memoria.js` con `topes_anteriores` validado estrictamente (`RF-077`) y omitido cuando esté vacío (`QP-3`). | Protege cuota de pey (`429`), límite de 10 canales por IP y Wake Lock de 24 h, sin recortar las 24 h mientras el cobro sigue en pantalla ni romper `test_recuperar.py` (`R-7`). | Recortar `fin_ventana` en servidor; no persistir el tope al recargar. |
| DP-8 | Teclado en cuadrícula de 4 columnas manteniendo el orden numérico `1–9` de la spec 002 (`+`, `×`, `⌫`, `C` en la 4.ª columna / fila inferior) y selector de duración `radiogroup` con `flex-wrap`. | Teclas ≥ 44×71 px en 320 px sin scroll horizontal y nombres accesibles en español (`R-8`). | `<select>` nativo (2 toques); reordenar dígitos a `7-8-9`. |
| DP-9 | Ampliar `web/tests/servidor_simulado.py` para aceptar/validar `duracion_segundos` y registrar la última petición recibida. | Mantiene la suite web rápida e independiente de pey y PostgreSQL en CI (`R-9`). | Levantar FastAPI completo dentro de Playwright. |

### 9.2 Decisiones de Hugo

- **2026-11-26 (Entrevista `E-1` a `E-9`)**: atajos 6 min–24 h en pantalla y rango 360–86 400 s en servidor; inclusión de Sin vencimiento; ventanas de escucha (`+10 min` en finitos, `24 h` en sin vencimiento + registro permanente por webhook); reinicio siempre a 10 min; botón sencillo Descargar QR; calculadora con `+`, `×`, `⌫` y `C`, expresión secundaria y total grande, operador final desactivando Cobrar; entrega en dos cortes (C1 y C2).
- **2026-11-26 (QA de spec `QA-1` a `QA-8`)**: *Monto libre* solo con entrada vacía o `"0"` simple; total parcial con operador final; `CE-007` alineado a 5 s en 9/10 intentos (`C-10`); `C-12`, `C-13` y `C-14` aprobados; tope de 20 min en cobros anteriores > 1 h; normalización de `.` + tope de 20 operandos + desbordamiento > `$999,999.99`; descarga en toda vista QR con nombre descriptivo; fin de 24 h en vista QR ocultando *Cancelar cobro* y nombres accesibles en español; verificación de `openapi.json` v`2026-10-20` y fecha meta C1 antes del 29 nov.
- **2026-11-27 (QA del plan `QP-1` a `QP-7` y aprobación)**: Hugo aprobó las 7 recomendaciones (`QP-1`–`QP-7`) y las 2 erratas, autorizó el ajuste puntual de `spec.md RF-038` (`QP-1`: *Monto libre* activo en cualquier entrada sin operadores con valor `0`, incluyendo `"0."`, `"0.0"`, `"0.00"`), y aprobó el plan (quedando en espera de su solicitud explícita para `/speckit-tasks`).

### 9.3 Revisión QA del plan

*Pasada única ejecutada el 2026-11-27 (`/qa-spec 004 plan`); todas las decisiones (`QP-1` a `QP-7`) y las 2 erratas fueron aprobadas por Hugo y aplicadas el 2026-11-27.*

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QP-1 | Contradicción | `data-model.md §2.2` y `contracts/calculadora-y-descarga.md` (siguiendo `RF-038`) activan `Monto libre` solo para `""` o `"0"`, pero `web/tests/test_teclado.py:97-116` y `web/tests/test_monto_libre_y_reuso.py:43-45` exigen que siga activo en `"0."` y `"0.00"`. | RF-038, QA-1, spec 002 RF-060 | Activar `monto_libre_activo` para toda entrada sin operadores cuyo valor numérico sea `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`), desactivándolo con cualquier operador (`"0 × 25"`, `"0 + "`) o valor `> 0`; ajuste puntual en `spec.md RF-038` aprobado aparte. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27 *(ajuste en `spec.md RF-038` autorizado y aplicado el 2026-11-27)*. |
| QP-2 | Contradicción | `contracts/vistas-cobro-rapido.md` exige enviar `duracion_segundos` en `POST /api/cobros`, pero tres pruebas existentes comparan igualdad exacta sin esa clave (`web/tests/test_crear_y_mostrar_qr.py:128`, `:313` y `web/tests/test_monto_libre_y_reuso.py:54`). | RF-016, C-13 | Dejar el 3.er parámetro `duracion_segundos` opcional en `servidor.js` (omitir clave si es `undefined`, manteniendo `:128` intacta), enviarlo siempre desde `app.js` y actualizar los 2 asertos de pantalla (`:313` y `:54`) en F3 bajo `C-13`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QP-3 | Contradicción | Tres suites tienen asertos cerrados de claves: `backend/tests/test_crear_cobro.py:23-40` (`CAMPOS_COBRO` de 16 claves), `backend/tests/test_migraciones_postgres.py:194,271,307` (`["0001","0002","0003"]`) y `web/tests/test_recuperar.py:109-112,314` (`{"en_pantalla","anteriores"}` exacto). | RF-007, RF-008, RF-044, C-12, C-14 | Explicitar en `plan.md §3.2` y `§7` la actualización de `CAMPOS_COBRO` en F1 (`C-12`) y `_versiones` en F6 (`C-14`); en `memoria.js`, omitir `"topes_anteriores"` al guardar cuando esté vacía para mantener verde `test_recuperar.py`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QP-4 | Hueco | En `research.md` (`R-5`, `R-7`) frente a `web/js/app.js` y `escucha.js`: (1) `restante() === null` en Sin vencimiento rompe 4 comparaciones `>= 1` / `< 1` en `app.js` (`:88`, `:314`, `:380-399`, `:424`); (2) si el SSE está caído a las 24 h en vista QR (con o sin `qr_reabierto`), falta respaldo por reloj local; (3) si `pasar_a_anterior()` ocurre mientras `cobro === null` (`test_recuperar.py:299-318`), falta diferir el cálculo de `tope_local`. | RF-022, RF-023, RF-044 | Agregar en `R-5`, `R-7` y `plan.md §4`: (1) helper `puede_reabrir_qr()` usado en los 4 sitios de `app.js`; (2) transición idempotente de fin de 24 h desde `escuchas.fin` y desde `empezar_cuenta` si `restante_ventana < 1`; (3) cálculo diferido de `tope_local` al recuperar la primera respuesta si `es_anterior && tope_local === null`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QP-5 | Ambigüedad | En `contracts/calculadora-y-descarga.md` faltaban dos bordes (`"25 + 0."` / `"25 + 10."` con `Cobrar` activo, y `"25 + 0"` + `"7"` → `"25 + 7"`), y en `contracts/vistas-cobro-rapido.md` explicitar que `tecla-borrar` cambia su texto visible de `"Borrar"` (`vistas.js:77`) a `"⌫"` conservando `data-prueba="tecla-borrar"`. | RF-028, RF-030, RF-037, RF-045, RF-048 | Documentar explícitamente los 3 puntos en `contracts/calculadora-y-descarga.md` y `contracts/vistas-cobro-rapido.md`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QP-6 | Hueco | En `supabase/migraciones/0001_esquema_inicial.sql:71-72` los `check` sobre `expira_en` son anónimos y `:151-152` revoca permisos de `cobros_con_estado` a `anon`/`authenticated` (`test_migraciones_postgres.py:331-349`); `data-model.md §1.4` no fijaba la técnica idempotente ni la prueba de permisos. | RF-008, RF-009, C-14, Principio III | Fijar en `data-model.md §1.4` y `research.md R-2` que `0004` usa `DO $$ ... $$` sobre `pg_constraint` para quitar los `CHECK` viejos sobre `expira_en`, agrega 3 checks con nombres fijos si no existen, usa `create or replace view cobros_con_estado with (security_invoker = true)`, reaplica `revoke all ... from anon, authenticated` y lo verifica en `test_migraciones_postgres.py`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QP-7 | Construibilidad | Al 2026-11-27 `plan.md §8` mantenía F1 en `26–27 nov`, no detallaba el mapa de ramas/PRs por issue ni evitaba choques entre `#100` (F2) y `#121` (F3–F4), y `backend/.venv` necesita `uv sync --directory backend --locked` (falta `psycopg` de la 003) antes de `pytest`. | Constitución (forma de trabajar, Principio V), `plan.md §8` | Reajustar `§8` desde el 27 nov (`F1`+`F2` 27 nov, `F3`+`F4` 28 nov, `F5` dom 29 nov), agregar mapa de ramas/PRs por issue (`#132`, `#120`, `#100`, `#121` saliendo tras `#100`, `#119`) y marcar `uv sync --directory backend --locked` como prerequisito de F1. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |

**Bloques de la pasada comprobados (8 de 8):**
1. *Coherencia interna*: 48/48 RF y 10/10 CE trazados en `plan.md`, `research.md`, `data-model.md`, contratos y `quickstart.md`; `Constitution Check` completo sin excepciones y 0 `[NECESITA ACLARACIÓN]` (`QP-5` y 2 erratas).
2. *Otras specs, plan del hackathon y reglas*: contrastado contra `C-12`, `C-13`, `C-14`, issues `#132`, `#120`, `#100`, `#121`, `#119` (y exclusión de `#118`/`#115`), sin PRs ni comentarios nuevos al 2026-11-27, y las 4 reglas del hackathon (`QP-1`, `QP-2`, `QP-3`).
3. *Código (solo lectura)*: contrastado contra `backend/app/`, `supabase/migraciones/0001_esquema_inicial.sql`, `web/js/`, `backend/tests/` y `web/tests/`; `ruff check` y `ruff format --check` limpios (`39 files already formatted`); `pytest` pendiente de `uv sync --directory backend --locked` (`QP-1` a `QP-7`).
4. *API de pey*: `https://docs.pey.mx/openapi.json` (v`2026-10-20`) confirmado (`expiration` entero `minimum: 0`, mínimo `360` cuando finito, sin máximo documentado, `429 CALL_LIMIT_REACHED`); riesgo de tope real cubierto en `§11` con prueba `$0.01`.
5. *Fuentes y dependencias externas*: dueños y cortes verificados (`#119` solo C2; compatibilidad con `#118`); fallos de pey y falta de webhook cubiertos por respaldo y conciliación `RF-061`.
6. *Ambigüedades y casos límite*: vacíos, cero, 20 operandos, `$999,999.99`, punto colgante, operador final, pago tardío 48 h, corte SSE a 24 h, recarga en recuperación, 320 px, lector de pantalla y aviso CoDi (`QP-4`, `QP-5`).
7. *Seguridad y rendimiento*: sin secretos nuevos, Standard Webhooks intacto, validación previa al límite por IP, `web/tests/test_seguridad.py:203-205` ya permite `blob:{origen}/` sin relajar CSP, permisos de vista en `0004` (`QP-6`), metas `CE-005` y `CE-007`.
8. *Construibilidad y reparto*: fechas frente a Puerta S2 (dom 29 nov) y cierre (12 dic), reparto Hugo/Leonel/Juan y estrategia de ramas por issue (`QP-7`).

**Erratas menores registradas (corregidas el 2026-11-27):**
1. *(Corregida el 2026-11-27)* En `§0.1 H-4`, se corrigió la cita de `supabase/migraciones/0001_esquema_inicial.sql` de `:67-73, :126-131` a `:66-73, :116-138` (`:127` para la condición de vencimiento).
2. *(Corregida el 2026-11-27)* En `contracts/calculadora-y-descarga.md §4`, se añadió una nota de 1 línea aclarando que el servidor rellena `"Cobro"` si el concepto se dejó vacío (`backend/app/main.py:89`), mientras que `nombre_archivo_qr` solo omite el sufijo cuando recibe `""` o sin caracteres alfanuméricos.

---

## 10. Seguridad

- **Secretos**: sin secretos nuevos; `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` y `DATABASE_URL` siguen exclusivamente en `backend/.env` / `.env.demo`. Ninguna respuesta, log ni archivo descargado incluye credenciales.
- **Firma de webhooks**: `POST /webhooks/pey` no cambia su verificación Standard Webhooks ni su deduplicación por `webhook-id` y `transactionId` (incluso 48 h después en cobros sin vencimiento).
- **Validación de entradas**:
  - Servidor: `duracion_segundos` validado estrictamente (rechaza `bool`, `float`, texto, negativos y fuera de rango con 422 antes de contar límite por IP y de llamar a pey).
  - Cliente: calculadora sin `eval`/`Function` (parseo estricto + `BigInt`), renderizado exclusivo con `textContent`, nombre de archivo PNG saneado a `[a-z0-9-]` y validación estricta de `topes_anteriores` en `localStorage` (`RF-077`).
- **Abuso de la demo pública**: se mantienen CORS, `OrigenEnPosts` (`C-11`), límite de cobros por minuto por IP y máximo 10 canales por IP; además `RF-044` acota a 20 min la escucha de cobros anteriores > 1 h para evitar tormentas de polling hacia pey (`429 CALL_LIMIT_REACHED`).

---

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Tiempo ajustado hasta la Puerta S2 (domingo 29 nov) | Atraso si se depende de la migración `#119` | Corte 1 (`F1`–`F5`) no requiere ninguna migración de BD y `F1` (Hugo) + `F2` (Leonel) se construyen en paralelo. |
| pey imponga en producción un límite máximo no documentado para `expiration` (p. ej. < 24 h) | Falla al crear QR de 24 h en demo real | `openapi.json` v`2026-10-20` no documenta tope; se comprueba con un cobro real de `$0.01` de 24 h en `F5` (y uno de `0` en `FN`). Si pey rechaza un valor, se ajusta el tope en el registro de implementación (`TK-n`). |
| Tailscale Funnel corte un canal SSE de larga duración (> 25 min) | Interrupción momentánea del canal en QR de 1 h / 24 h | `escucha.js` ya activa consulta cada 3 s y reconecta automáticamente el SSE (`spec 002 RF-030`, `RF-031`, `RF-079`); ningún pago se pierde. |
| Comportamiento de `<a download>` con `Blob` en iPhone Safari | El navegador podría abrir la imagen en lugar de guardarla directo o fallar | Se prueba en WebKit (Playwright) y en iPhone real en `F5`; `descargar_qr` captura cualquier excepción y muestra mensaje claro sin ocultar el QR (`RF-027`). |
| Conflictos al unir el rediseño UX/UI (`#118`) con la Spec 004 | Retrabajo visual en `web/js/vistas.js` y `estilos.css` | La lógica pura vive en `teclado.js`, `cuenta.js`, `descarga.js`, `escucha.js` y `servidor.js`, idénticos en estructura a `#118`, y las vistas conservan todos los `data-prueba`. |

---

## 12. Seguimiento de complejidad (Complexity Tracking)

*No aplica: la verificación de la constitución (§2) no tiene ninguna excepción.*

---

## 13. Aprobación

- [x] Plan revisado con `/qa-spec 004 plan` y todos los hallazgos QP (`QP-1` a `QP-7`) y erratas decididos y aplicados el 2026-11-27.
- [x] Aprobado por Hugo el 2026-11-27. Aprobar no autoriza a empezar `tasks.md`: se espera a que Hugo lo pida.

---

## 14. Registro de implementación

*Se llenará durante `/speckit-implement`.*
