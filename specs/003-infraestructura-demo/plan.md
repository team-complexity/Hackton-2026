# Plan: Infraestructura de la demo: guardar los cobros, abrir la demo local por un túnel y probar cada cambio

- **Rama**: `feature/90-infraestructura-demo` (F1 va en su propio PR, `feature/35-ci`, DP-28)
- **Fecha**: 2026-11-20
- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-20 (QA-12 a QA-20)
- **Estado del plan**: `Aprobado` el 2026-11-21 por Hugo, con la QA del 2026-11-20 (QP-10 a QP-14, §9.3) decidida y aplicada y los PR #72 y #96 unidos a `main` ese mismo día (C-8 cumplido; `main` con la constitución 3.0.1, `f01f732`). Estado anterior: `En QA`. Lo redactó Claude el 2026-11-20 con `/speckit-plan`, como permite C-8: contra la constitución 3.0.0 del PR #96 (`a962dc5`), que la QA-19 lleva a 3.0.1, y contra el código de esta rama (`5db47ed`). Sustituye al plan de la versión con AWS (en el historial de git, commit `5db47ed`), del que se conservan las decisiones del guardado, las migraciones y el CI con su mismo número. Hugo decidió DP-38 el mismo día: Tailscale Funnel (§9.2).
- **Entrada**: la spec de `specs/003-infraestructura-demo/spec.md`

> **Notas para los comandos de spec-kit.**
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
> - Los títulos marcados entre paréntesis (*Technical Context*, *Constitution Check*, *Project Structure*, *Complexity Tracking*) son las secciones que espera `/speckit-plan`.
> - El plan se escribe en español.
> - El plan dice **CÓMO**. Cada pieza cita los RF de la spec que cumple.

---

## 0. Resumen

La spec pide tres cosas sin cambiar lo que el dueño ve y oye: un CI en cada pull request, una demo pública con HTTPS que sale por un túnel desde la computadora de Hugo, y que los cobros sobrevivan a un reinicio sin perder nunca un pago. Va en dos cortes (QA-12).

**Corte 1 (≤ domingo 22 nov), sin base de datos:**

- **CI**: GitHub Actions sin secretos, con un trabajo para el servidor y otro para la web (DP-27, DP-28).
- **Demo por el túnel**: el servidor de la 001 entrega también la web, en el mismo origen y solo en `127.0.0.1`. **Tailscale Funnel** (DP-38, decidido por Hugo) le da una dirección fija con HTTPS que termina en la propia computadora. La IP real del celular llega por `X-Forwarded-For` sin código nuevo (DP-40). Una guía enciende y apaga la demo (DP-42, DP-43).
- **Pago real** de $0.01 desde la dirección del túnel, en Android y en iPhone.

**Corte 2 (≤ miércoles 25 nov), con Supabase:**

- **Migraciones**: un comando propio aplica en orden los archivos de `supabase/migraciones/`, anota cada uno y separa los datos de prueba con una marca de entorno (DP-3, DP-17 a DP-20).
- **Guardar**: la memoria pasa a ser una caché de escritura directa sobre un *almacén* de PostgreSQL. Cada escritura va primero a la base de datos, un cobro se carga al pedirlo después de un reinicio y los pagos se registran con un candado por cobro (DP-6 a DP-13, DP-33).
- **Conciliación**: una tarea de fondo revisa en pey, una vez, cada cobro cuya ventana terminó, también las que terminaron con el servidor apagado. Así no se pierde ningún pago (RF-061, DP-39).

### 0.1 Hechos del código y de las fuentes

| # | Hecho | Evidencia |
|---|---|---|
| H-1 | Todo el estado vive en `RepositorioCobros`, en memoria y con métodos síncronos: índices por id, por `codi_qr_id`, transacciones vistas y `webhook-id` vistos | `backend/app/cobros.py:134-233` |
| H-2 | El canal y la consulta de respaldo guardan y modifican el objeto `Cobro` en memoria (`cobro.pagos`, `ultima_consulta_pey`) | `backend/app/canal.py:58-103`, `backend/app/respaldo.py:58-65` |
| H-3 | `crear_cobro` crea el cobro en memoria, llama a pey y lo descarta si pey falla | `backend/app/main.py:173-223` |
| H-4 | El webhook marca el `webhook-id` después de procesar y responde 200 a lo que ignora | `backend/app/main.py:268-325` |
| H-5 | `pagos_del_qr` recibe el conjunto **global** de transacciones vistas para saber cuándo parar de paginar | `backend/app/pey.py:140-172`, `respaldo.py:67` |
| H-6 | La configuración no lee `DATABASE_URL`, aunque `.env.example` la tiene | `backend/app/config.py`, `backend/.env.example:9` |
| H-7 | `/salud` devuelve solo `estado`, `llave_pey` y `secreto_aviso_pey` | `backend/app/main.py:155-161` |
| H-8 | La IP de los límites sale de `ProxyHeadersMiddleware` con `PROXIES_CONFIABLES` (por defecto `127.0.0.1`): un agente de túnel en la misma computadora que mande `X-Forwarded-For` ya da la IP real | `backend/app/main.py:139-140`, `config.py:35`; research R-2 |
| H-9 | La web ya admite el mismo origen (`config.js` vale `""`), pero su CSP permite `connect-src … http://localhost:8000 https:` | `web/config.js:2`, `web/index.html:8` |
| H-10 | La web trata cualquier error que no sea 404 al consultar un cobro como "sin conexión" y reintenta; al crear, espera 15 s | `web/js/servidor.js` |
| H-11 | El esquema del PR #97 se corre a mano, una sola vez, con `begin`/`commit` propios; no tiene `qr_imagen`; pone `default now()` en las horas; tiene RLS encendido en las 5 tablas, sin políticas | `supabase/001_esquema_inicial.sql:66`, `:93`, `:109`, `:146-150` (en `main`) |
| H-12 | El PR #97 ya se corrió, con sus datos de prueba, en el proyecto de Supabase de la demo | Descripción del PR #97 |
| H-13 | No hay `.github/workflows/`: no existe ningún CI | `ls .github` |
| H-14 | uvicorn escucha en `127.0.0.1` si no se le da `--host` | `backend/README.md:12` |
| H-15 | El canal manda una señal de vida cada 15 s | `backend/app/canal.py:91` |
| H-16 | El túnel rápido de Cloudflare no admite SSE; ngrok gratis pone una página de advertencia; Tailscale Funnel termina el HTTPS en la computadora | Research R-1 |
| H-17 | pey: un solo aviso por llave, que solo se cambia en el portal; sin reintentos documentados; su ambiente de pruebas está "coming soon"; una llave nueva se liga en el portal a una cuenta CoDi ya creada | QA de la spec, QA-15; [set-up-webhooks](https://docs.pey.mx/en/docs/tutorials/getting-started/set-up-webhooks), [create-an-api-key](https://docs.pey.mx/en/docs/tutorials/getting-started/create-an-api-key) |
| H-18 | El backend tiene 109 pruebas en verde y `ruff` limpio | `uv run --directory backend pytest -q` (2026-11-20) |
| H-19 | Esta rama sale de `feature/64-web-mvp` y no tiene el esquema del PR #97 ni la constitución 3.0.0 | `git merge-base` (2026-11-20) |

---

## 1. Contexto técnico (Technical Context)

- **Lenguaje y versión**: Python 3.11 o superior (3.12 en el CI).
- **Dependencias principales**: FastAPI, httpx, pydantic-settings, standardwebhooks y uvicorn, como hoy. **Nuevas en el corte 2** (DP-2): `psycopg[binary]` 3 y `psycopg-pool`, fijadas a versiones publicadas hace al menos dos semanas.
- **Almacenamiento**: memoria en el corte 1 (como la 001). En el corte 2, PostgreSQL de Supabase, plan gratuito: un proyecto para la demo y otro para desarrollo (RF-049), por el *pooler* en modo sesión (research R-9).
- **Pruebas**: pytest con pey simulado (`httpx.MockTransport`), `RelojFalso`, almacén en memoria y almacén que falla a propósito. Las pruebas del almacén de PostgreSQL y de las migraciones corren contra un PostgreSQL 17 desechable (research R-10). Playwright para la web, como hoy.
- **Plataforma de destino**: la Mac de Hugo con el servidor (uvicorn, un proceso, solo `127.0.0.1`, entrega también la web) y el túnel (Tailscale Funnel, DP-38) hacia el puerto 8000. CI en GitHub Actions.
- **Tipo de proyecto**: servicio web con PWA, como en las specs 001 y 002.
- **Metas de rendimiento**: QR en 5 s o menos en 9 de cada 10 intentos (CE-003, C-10); "Pago recibido" en menos de 2 s después del aviso de pey (CE-002); canal durante toda la ventana sin cortes (RF-026, CE-004 con 20 min); aviso de pey respondido en menos de 1 s (CE-010 de la 001, C-6 f). Cada escritura en la base de datos agrega la ida y vuelta de la computadora de Hugo a Supabase (se mide en F3 y F6).
- **Restricciones**: un solo proceso (QP-5 de la 001); credenciales solo en `backend/.env` (desarrollo) y `backend/.env.demo` (demo) de cada computadora (principio III, QP-14); ninguna prueba automática con pey real ni con la base de datos real (principio V, CE-011); servidor solo en `127.0.0.1` (RF-056); sin costo (spec §7).
- **Escala**: una demo, decenas de cobros al día, unos pocos celulares a la vez; los jueces del 12 al 14 de diciembre. Supabase gratuito: 500 MB, sobrado para la imagen del QR.

---

## 2. Verificación de la constitución (Constitution Check)

*Puerta de paso: se revisa antes de la investigación (Fase 0) y otra vez después del diseño (Fase 1). Contra la constitución 3.0.0 del PR #96, con el parche 3.0.1 de QA-19 (C-8).*

| Principio de la constitución | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. El pago se confirma en el servidor | No cambia: solo el aviso firmado, la consulta de respaldo y la conciliación (que también es una consulta del backend a pey) registran pagos. La base de datos no se puede leer ni escribir desde fuera del servidor (RLS sin políticas del PR #97, RF-022) | Cumple |
| II. Una orden nunca se ejecuta dos veces | `transaccion_id` único con `on conflict do nothing`, candado por cobro y `webhook-id` guardado en la misma transacción que su pago. La conciliación entra por la misma función. El evento `pago` sale solo si el `insert` devolvió fila (DP-8, DP-9, DP-39) | Cumple |
| III. Los secretos nunca salen del backend | `DATABASE_URL` y las llaves de pey solo en `backend/.env` de cada computadora. En la demo, la Mac de Hugo es el hosting y `backend/.env.demo` son sus variables (QP-14, DP-44; QT-9 de las tareas), así que se cumple sin cambiar la constitución. La sesión del túnel vive en la app de Tailscale de la computadora de la demo (RF-059). Los registros nunca llevan el texto de un error de conexión (DP-15). La web y las apps nunca hablan con Supabase. Con Funnel, el HTTPS termina en la computadora y nadie en medio ve los avisos (R-1) | Cumple |
| IV. Alcance anclado y trabajo documentado | Solo lo que pide la spec. Cada PR con la plantilla, `Closes` de sus issues y enlace a esta carpeta, sin notas aparte (3.0.0). C-6 y C-7 se aprueban antes de las tareas y se aplican en la fase que cambia ese comportamiento: C-7 en F2 y C-6 en F5 (QP-11) | Cumple |
| V. Pruebas primero, en todo | Cada pieza tiene su prueba antes (§7). El almacén en memoria y el que falla a propósito sustituyen a la base de datos en las pruebas de la API; el SQL se prueba contra un PostgreSQL desechable (R-10). Reloj controlado también en la tarea de fondo (DP-14) | Cumple |
| VI. CoDi real, reacción real | F3: pago real de $0.01 desde la dirección del túnel, en Android y en iPhone (CE-002). F6: pago real después de un reinicio (CE-001). Con autorización de Hugo | Cumple |
| VII. Pensado para el mostrador | Mensajes de falla para el dueño (DP-32). QR en 5 s o menos (C-10) y aviso en menos de 3 s (la spec pide 2 s) | Cumple |
| VIII. Un pago no prueba identidad ni entrega | Pago tardío, monto distinto y falla de pey: sin cambios respecto a la 001. Falla de la base de datos: reintentos en memoria (RF-048). Demo apagada o aviso perdido: conciliación (RF-061). Devoluciones: fuera de alcance | Cumple |
| IX. Lo más simple que gane la demo | Piezas nuevas justificadas por la spec (base de datos, túnel, CI). Cada herramienta nueva con comparativa y decisión de Hugo: DP-2 y DP-3 (decididas), DP-38 (pendiente); las comparativas van en la descripción del PR. Tabla de restricciones: Hosting y la imagen del QR, con el parche 3.0.1 (QA-19). Una tarea de fondo, justificada en §12 | Cumple, con excepción justificada en §12 |
| X. Si no se ve, no existe | `/salud` agrega `base_de_datos` sin valores ([contrato](contracts/salud.md)). Cada falla de la base de datos y cada conciliación dejan su línea con el id del cobro (RF-016) | Cumple |

**Después del diseño (Fase 1)**: sin cambios con los contratos y el modelo de datos escritos. No quedan `[NECESITA ACLARACIÓN]`. El PR #96 se unió el 2026-11-21 con el parche 3.0.1, así que "Hosting" ya dice túnel y no hace falta excepción en §12.

---

## 3. Estructura del proyecto (Project Structure)

### 3.1 Documentación de esta funcionalidad

```text
specs/003-infraestructura-demo/
├── spec.md               # Qué y por qué (aprobada el 2026-11-20)
├── plan.md               # Este archivo
├── research.md           # R-1 a R-12
├── data-model.md         # Qué se guarda, traducción, conciliación, migraciones
├── contracts/
│   ├── salud.md
│   ├── fallas-base-de-datos.md
│   ├── comando-migraciones.md
│   └── ci.md
├── quickstart.md         # Comprobación de punta a punta
├── tasks.md              # /speckit-tasks (después de aprobar el plan)
└── verification-guide.md # Al cerrar cada fase
```

### 3.2 Código fuente (raíz del repositorio)

```text
.github/workflows/
└── ci.yml                    # F1 (DP-27, DP-28); trabajo base-de-datos en F4
backend/
├── app/
│   ├── main.py               # F2: web desde el servidor. F5: fallas 503, salud, ciclo de vida
│   ├── config.py             # F2: CARPETA_WEB. F5: DATABASE_URL
│   ├── almacen.py            # F5, nuevo: interfaz Almacen, AlmacenEnMemoria, ErrorDeAlmacen
│   ├── almacen_postgres.py   # F5, nuevo: AlmacenPostgres con psycopg
│   ├── migraciones.py        # F4, nuevo: comando
│   ├── tareas.py             # F5 y F6, nuevo: reintentos de avisos y latido de conciliación
│   ├── cobros.py             # F5: el repositorio usa el almacén, métodos async, candado por cobro
│   ├── respaldo.py           # F5: await al registrar; transacciones del cobro
│   └── canal.py              # F5: solo si hace falta un await nuevo
├── tests/                    # Pruebas nuevas por pieza (§7)
└── pyproject.toml            # F4: psycopg y psycopg-pool (DP-2)
supabase/
├── migraciones/
│   ├── 0001_esquema_inicial.sql      # El 001 del PR #97, sin begin/commit
│   ├── 0002_imagen_del_qr.sql
│   └── 0003_estado_del_servidor.sql
├── datos_de_prueba.sql               # Bloques A y B del 002 del PR #97
└── consultas_de_verificacion.sql     # Bloques C a F del 002 del PR #97
docs/
└── operacion-demo.md         # F2 (encender, apagar, túnel); F6 (Supabase, copia, migraciones)
web/
├── index.html                # F2: CSP connect-src 'self' (RF-029)
└── README.md                 # Con C-7: abrir la web desde el servidor
README.md                     # F3: enlace de la demo y cuándo está encendida (#66)
```

**Decisión de estructura**: el código nuevo de la base de datos vive en módulos propios (`almacen*.py`, `migraciones.py`, `tareas.py`) para probar cada uno por separado; `cobros.py` conserva el modelo de la 001. La rama se pone al día sobre `main` antes de F2 (H-19, QP-10), así que en F4 los archivos del PR #97 ya están para moverlos a `supabase/migraciones/`. No hay carpeta `infra/`: la demo es una computadora y su guía.

---

## 4. Módulos y piezas con comportamiento

| Pieza | Responsabilidad | Requisitos |
|---|---|---|
| `main.py` · web (F2) | Con `CARPETA_WEB`, monta `web/` en `/` después de las rutas del API | RF-024, RF-029 |
| `web/index.html` (F2) | CSP `connect-src 'self'` | RF-029 |
| `config.py` (F2 y F5) | `carpeta_web`; `database_url` (`SecretStr`, F5); `WEB_ORIGIN` con la dirección del túnel en la demo. La demo carga `backend/.env.demo` con `--env-file`, sin código nuevo (QP-14) | RF-020, RF-027, RF-049, RF-053 |
| Túnel (F2, sin código) | Tailscale Funnel hacia `127.0.0.1:8000`, con su nombre fijo `*.ts.net` (DP-38) | RF-024 a RF-026, RF-030, RF-057, RF-059 |
| IP real (F2, sin código) | `ProxyHeadersMiddleware` con `PROXIES_CONFIABLES=127.0.0.1`; si el túnel no manda la IP, límites de 60 en la demo (DP-40) | RF-028 |
| `docs/operacion-demo.md` (F2 y F6) | Encender y apagar (R-4), comprobar desde fuera, dar de alta el aviso de pey, calendario de encendido (al menos cada 5 días y del 12 al 14 dic), reactivar Supabase, copia antes de migrar, aplicar migraciones | RF-050, RF-051, RF-058, RF-060 |
| `.github/workflows/ci.yml` (F1 y F4) | Contrato [ci](contracts/ci.md) | RF-036 a RF-038 |
| `migraciones.py` (F4) | Comando `estado` y `aplicar` (contrato [comando-migraciones](contracts/comando-migraciones.md)) | RF-017 a RF-019, RF-049, RF-054 |
| `supabase/migraciones/0002`, `0003` (F4) | Columna `qr_imagen`; tabla `estado_del_servidor` | RF-010, RF-018, RF-061 |
| `almacen.py` · `Almacen` (F5) | Operaciones asíncronas: `guardar_cobro`, `guardar_qr`, `borrar_cobro`, `cancelar`, `registrar_pago` (devuelve si el pago es nuevo; guarda el `webhook-id` en la misma transacción), `guardar_aviso`, `aviso_visto`, `cargar_por_id`, `cargar_por_codi_qr`, `cobros_con_ventana_terminada`, `leer_conciliado_hasta`, `guardar_conciliado_hasta`, `responde` | RF-001 a RF-005, RF-007, RF-061 |
| `almacen.py` · `AlmacenEnMemoria` (F5) | La misma interfaz con diccionarios. Para las pruebas de la API y para un servidor sin `DATABASE_URL` (DP-16). Un almacén nuevo sobre los mismos diccionarios simula un reinicio | RF-005, CE-005 |
| `almacen.py` · `ErrorDeAlmacen` (F5) | La única excepción que ve el resto del código cuando la base de datos no responde; lleva la operación y el nombre de la clase del error original, nunca su texto | RF-016, RF-021 |
| `almacen_postgres.py` · `AlmacenPostgres` (F5) | El SQL de data-model §3 con psycopg y un *pool* de 1 a 3 conexiones; traduce Unix ↔ `timestamptz` y `""` ↔ `null`; escribe todas las horas con el `Reloj` (DP-10); espera 5 s como máximo por operación (2 s al crear, DP-35); convierte cualquier error de conexión o de servidor en `ErrorDeAlmacen` | RF-001 a RF-009, RF-020, RF-022 |
| `cobros.py` · `RepositorioCobros` (F5) | Caché de escritura directa (DP-7); carga al pedir lo que no está (RF-005) con un solo objeto por cobro (DP-33); `registrar_pago` dentro del candado del cobro (DP-8); calcula el estado con el `Reloj` (DP-11) | RF-002, RF-005 a RF-008 |
| `respaldo.py` · `ConsultaDeRespaldo` (F5) | Igual que en la 001, con `await` al registrar; pasa a pey las transacciones **del cobro** (DP-13); si el almacén falla, registra y sigue | RF-005, RF-007, RF-016 |
| `main.py` · `crear_cobro` (F5) | Guarda el cobro (si falla, 503 sin llamar a pey); llama a pey; si pey falla, borra el cobro; guarda el QR (si falla, 503 sin QR). Cada escritura espera como máximo 2 s (DP-35) | RF-001, RF-012, RF-013, RF-052 |
| `main.py` · `ver_cobro`, `eventos_cobro`, `cancelar_cobro` (F5) | Cargan del almacén si hace falta; 503 si no responde, nunca 404 por una falla | RF-004, RF-005, RF-015 |
| `main.py` · `webhook_pey` (F5) | Rechaza con 400 un `amount` de 0 o negativo, sin marcar el `webhook-id` (DP-34); busca el cobro (memoria, luego almacén); registra el pago y el `webhook-id` en una transacción; si la base de datos no responde, 503 a pey y el aviso entra a la lista de reintentos; un error de datos responde 400 y nunca entra a la lista (DP-34) | RF-003, RF-007, RF-009, RF-014 |
| `tareas.py` · `ReintentosDeAvisos` (F5) | Lista en memoria por `webhook_id` (data-model §4); cada 15 s intenta registrar y, al lograrlo, emite por el canal | RF-014, RF-048 |
| `tareas.py` · `LatidoDeConciliacion` (F6) | Cada 60 s: concilia con pey los cobros cuya ventana terminó desde `conciliado_hasta` y mueve la marca; salta un cobro con 4xx de pey o con 10 fallas pasajeras seguidas (data-model §4.1, DP-39, QP-13). Su escritura cumple el uso diario de RF-039 | RF-039, RF-061 |
| `main.py` · ciclo de vida (F5 y F6) | Abre y cierra el *pool*; arranca y detiene la tarea de fondo con el `Reloj` inyectado; el primer latido corre al arrancar | RF-039, RF-048, RF-061 |
| `main.py` · `/salud` (F5) | Agrega `base_de_datos` (consulta con 2 s, guardada 10 s, DP-31) | RF-023 |
| `README.md` (F3) | Enlace de la demo, cuándo está encendida y cómo probarla (#66) | RF-024, RF-060 |

---

## 5. Contratos

Las rutas de la 001 no cambian de forma; solo se agregan respuestas de falla.

| Contrato | Archivo | Requisitos |
|---|---|---|
| `GET /salud` (amplía el de la 001) | [contracts/salud.md](contracts/salud.md) | RF-023, RF-050 |
| Respuestas 503 por falla de la base de datos en las rutas de la 001 | [contracts/fallas-base-de-datos.md](contracts/fallas-base-de-datos.md) | RF-012 a RF-016, RF-048, RF-052, RF-061 |
| Comando `python -m app.migraciones` | [contracts/comando-migraciones.md](contracts/comando-migraciones.md) | RF-017 a RF-019, RF-049, RF-051, RF-054 |
| `ci.yml` | [contracts/ci.md](contracts/ci.md) | RF-036 a RF-038 |

Los contratos de la 001 `crear-cobro.md`, `ver-cobro.md`, `cancelar-cobro.md`, `canal-avisos.md` y `aviso-pey.md` siguen valiendo; C-6 (e), (f) y (g) les quita las menciones a "se perdió al reiniciar" y "no hace llamadas de red" y agrega el 400 del `amount` ≤ 0. El túnel no es una interfaz nueva: expone las mismas rutas en la dirección pública.

---

## 6. Modelo de datos

El detalle va en [data-model.md](data-model.md). En resumen:

- El modelo de la 001 no cambia; se guarda en las tablas del PR #97, más la columna `qr_imagen` (migración 0002) y la tabla `estado_del_servidor` (migración 0003).
- Todas las horas se escriben con el `Reloj` del servidor, y el estado se calcula en Python (RF-006, QA-11, QA-18).
- El comando de migraciones crea `cambios_de_estructura` y `entorno_de_la_base`, con RLS y sin acceso para `anon` ni `authenticated`.
- La lista de reintentos de avisos, los límites por IP, los canales y `ultima_consulta_pey` viven solo en memoria.

---

## 7. Estrategia de pruebas

- **Pruebas primero**: cada tarea de implementación tiene antes su prueba, que se ve fallar y después pasa.
- **Pruebas automáticas**: nunca llaman al pey real ni a la base de datos real. La API se prueba con el almacén en memoria y con `AlmacenQueFalla` (un almacén cuyas operaciones se pueden hacer fallar una por una). El SQL se prueba contra un PostgreSQL desechable (R-10).
- **"Reinicio" en las pruebas**: se crea una app nueva con un almacén nuevo sobre los mismos datos y se comprueba que todo sigue igual. "Apagado": se avanza el `RelojFalso` sin app corriendo y después se arranca otra.
- **Pruebas reales**: solo con $0.01 y con autorización de Hugo (F3 y F6).
- **Nombres de las pruebas** en español, como la spec que comprueban.
- **Las 109 pruebas de hoy** se mantienen; se ajustan solo donde una función pasa a ser asíncrona.

| Requisito | Prueba | Tipo |
|---|---|---|
| RF-001, RF-010 | `test_un_cobro_creado_queda_guardado_con_su_imagen_del_qr` | integración |
| RF-002 | `test_el_pago_se_guarda_antes_de_emitirse_por_el_canal` | integración |
| RF-003 | `test_el_webhook_id_procesado_queda_guardado` | integración |
| RF-004 | `test_la_cancelacion_queda_guardada_con_su_hora` | integración |
| RF-005 | `test_dos_cargas_a_la_vez_del_mismo_cobro_dan_el_mismo_objeto` (DP-33); `test_tras_un_reinicio_se_puede_ver_cancelar_y_escuchar_un_cobro_guardado`; `test_tras_un_reinicio_el_aviso_de_pey_registra_el_pago`; `test_tras_un_reinicio_la_consulta_de_respaldo_encuentra_el_pago` | integración |
| RF-006 | `test_el_estado_tras_un_reinicio_se_calcula_con_el_reloj_del_servidor`; `test_las_horas_guardadas_son_las_del_reloj_del_servidor` (PostgreSQL) | integración |
| RF-007, CE-005 | `test_un_aviso_reenviado_no_duplica_el_pago`; `test_el_aviso_y_la_consulta_a_la_vez_registran_un_solo_pago`; `test_el_mismo_pago_antes_y_despues_de_un_reinicio_se_registra_una_vez`; `test_on_conflict_no_duplica_la_transaccion` (PostgreSQL) | integración |
| RF-008 | `test_tras_un_reinicio_el_siguiente_pago_es_el_numero_3`; `test_dos_pagos_distintos_a_la_vez_quedan_con_numeros_1_y_2` | integración |
| RF-009 | `test_los_datos_de_quien_paga_no_se_guardan_ni_se_registran` (aviso con `metadata` completa) | integración |
| RF-011 | `test_sin_imagen_de_pey_el_cobro_guardado_vuelve_sin_imagen` | integración |
| RF-012 | `test_si_la_base_no_responde_al_crear_no_se_llama_a_pey` | integración |
| RF-052 | `test_si_pey_falla_el_cobro_guardado_se_borra` | integración |
| RF-013 | `test_si_la_base_falla_al_guardar_el_qr_no_se_devuelve_el_qr`; `test_al_crear_cada_escritura_espera_como_maximo_2_segundos` (DP-35) | integración |
| RF-014 | `test_si_la_base_falla_con_un_aviso_se_responde_503_y_no_se_emite`; `test_un_aviso_con_monto_cero_o_negativo_se_rechaza_con_400`; `test_un_error_de_datos_responde_400_y_no_entra_a_los_reintentos` (DP-34) | integración |
| RF-048 | `test_el_aviso_pendiente_se_registra_y_se_emite_cuando_la_base_vuelve` (`RelojFalso`, avanza 15 s); `test_un_aviso_reenviado_mientras_esta_pendiente_no_se_duplica` | integración |
| RF-015 | `test_si_la_base_no_responde_al_ver_un_cobro_se_responde_503_y_no_404` | integración |
| RF-016, RF-021 | `test_cada_falla_de_la_base_deja_registro_sin_datos_de_conexion` | integración |
| RF-017, RF-018, CE-007 | `test_aplicar_en_una_base_vacia_crea_el_esquema_la_imagen_y_el_estado`; trabajo `base-de-datos` del CI (dos veces seguidas) | integración (PostgreSQL) |
| RF-019 | `test_aplicar_dos_veces_no_cambia_nada`; `test_una_migracion_que_falla_no_deja_nada_a_medias` | integración (PostgreSQL) |
| Historia 6, esc. 3 | `test_una_base_con_el_esquema_sin_registro_pide_ya_aplicada`; `test_ya_aplicada_solo_agrega_lo_que_falta` | integración (PostgreSQL) |
| RF-049, RF-054 | `test_los_datos_de_prueba_se_rechazan_en_una_base_demo`; `test_la_marca_de_entorno_no_se_puede_cambiar` | integración (PostgreSQL) |
| RF-051 | Paso de la guía revisado en F6 | manual |
| RF-020 | `test_database_url_se_lee_de_la_configuracion` | unitaria |
| RF-022 | `test_anon_y_authenticated_no_pueden_leer_ni_escribir` (PostgreSQL con los roles creados), también en `estado_del_servidor` | integración |
| RF-023 | `test_la_salud_dice_si_la_base_responde_sin_mostrar_valores` (tres casos) | integración |
| RF-039 | `test_el_latido_escribe_en_la_base_cada_minuto` (`RelojFalso`) | integración |
| RF-061, CE-017 | `test_al_arrancar_se_concilian_las_ventanas_que_terminaron_apagado`; `test_el_latido_registra_un_aviso_perdido_cuando_termina_la_ventana`; `test_si_pey_falla_conciliado_hasta_no_avanza`; `test_la_primera_vez_no_se_revisa_hacia_atras`; `test_la_conciliacion_no_duplica_un_pago_ya_registrado`; `test_un_qr_que_pey_no_conoce_no_bloquea_la_conciliacion`; `test_tras_10_fallas_el_cobro_se_salta_con_error` (QP-13) | integración |
| RF-050 | Revisión de `docs/operacion-demo.md` (reactivar Supabase y comprobar con la salud) | manual |
| RF-024, RF-029 | `test_con_carpeta_web_el_servidor_entrega_la_web`; prueba de la web: la CSP tiene `connect-src 'self'` y nada más; quickstart §3 (abrir con datos móviles) | integración y manual |
| RF-056, CE-015 | Quickstart §3.6: desde otro equipo de la misma red, `curl` a la IP de la computadora, puerto 8000, no responde; la guía nunca usa `--host 0.0.0.0` | manual |
| RF-025 | Quickstart §4.1 (aviso dado de alta y firma válida en el registro) | manual |
| RF-026, RF-057, CE-004 | F0 con `curl` (quickstart §3.0, QP-12), después quickstart §3.2 con la web y §4.3 (pago después del minuto 15) | manual |
| RF-027 | `test_cors_solo_permite_los_origenes_configurados` (ya existe en la 001) y quickstart §3.5 | integración y manual |
| RF-028 | Quickstart §3.3 (dos celulares en redes distintas, dos IP en el registro) | manual |
| RF-030 | Quickstart §3.4 (misma dirección después de reiniciar el servidor, el túnel y la computadora) | manual |
| RF-058 | Hugo enciende la demo con la computadora recién prendida siguiendo solo la guía (CE-016) | manual |
| RF-059 | `git grep` de la sesión del túnel y revisión: Tailscale guarda su sesión en la app, fuera del repositorio | manual |
| RF-060 | Revisión de la guía (calendario de encendido) y de las instrucciones de prueba de la entrega | manual |
| RF-036, RF-037, CE-006 | Quickstart §2 | manual |
| RF-038, CE-011 | El CI corre sin secretos; revisión del flujo | manual |
| RF-049, RF-053 | Revisión de que `backend/.env` (desarrollo) y `backend/.env.demo` (demo) tienen distinta llave y distinta base, sin leer valores, con la salud de cada servidor (QP-14) | manual |
| CE-001 | Quickstart §6 (reinicio y pago de $0.01) | manual (dinero real) |
| CE-002, CE-003 | Quickstart §4 | manual (dinero real) |
| CE-010 | Prueba de registros (RF-016) y `git grep` de llaves en el repositorio | integración y manual |
| CE-016 | Quickstart §5 | manual |

---

## 8. Plan de implementación

| Fase | Fechas | Quién | Qué | Depende de |
|---|---|---|---|---|
| F0 Prueba del túnel | Ya, antes de las tareas | Hugo, con Claude | Sin código de producto ni la web (QP-12): cuenta de Tailscale, HTTPS, MagicDNS y permiso `funnel`; Funnel hacia el servidor actual; un cobro de $0.01 con `curl` (QR real sin pagar); `curl -N` al canal desde otra red durante 25 minutos (RF-026, RF-057); dos redes para la IP real (R-2); reinicio de la computadora y misma dirección (RF-030). Pasos en el quickstart §3.0. El resultado se anota como TK. Si falla, Hugo decide B (R-1) antes de seguir | DP-38 |
| F1 CI | 21 nov | Grok (revisa Claude) | `ci.yml` con los trabajos `servidor` y `web`, en su propio PR desde `main` (`feature/35-ci`, DP-28), que cierra #35. La protección de `main` exige los dos trabajos y deja de exigir aprobación | Plan y tasks aprobados, es decir, PR #72 y #96 unidos (C-8) |
| F2 Demo por el túnel | 21–22 nov | Código, Grok (revisa Claude); túnel y guía, Hugo | `CARPETA_WEB` y CSP; C-7 aplicado a la 002 (QP-11); `docs/operacion-demo.md` (encender y apagar con `backend/.env.demo`, túnel, aviso de pey, calendario; QP-14); límites de la demo (DP-36 o DP-40). Hugo da de alta el aviso de la llave de la demo con la dirección del túnel. Su PR cierra #65 | F1; F0 en verde; rama al día sobre `main` (QP-10); C-7 aprobado |
| F3 Pago real | 22 nov | Hugo, con los dos celulares | CE-002, CE-003, CE-004 y reenvío del aviso; README con el enlace (#66). Leonel prueba desde fuera de la red (N-17). Después del pago, el PR del README cierra #66, #27 y #64 (o se cierran a mano) | F2 |
| **Fin del corte 1** | **dom 22 nov** | | | |
| F4 Migraciones | 23 nov | Grok (revisa Claude) | Mover los archivos del #97; `0002` y `0003`; `migraciones.py` con sus pruebas; trabajo `base-de-datos` del CI. Hugo aplica en desarrollo con `--entorno local --datos-de-prueba` | F3; proyecto de Supabase de desarrollo (Juan, RF-049) |
| F5 Guardar | 23–24 nov | Grok (revisa Claude) | `almacen.py`, `almacen_postgres.py`, `RepositorioCobros` asíncrono con candado, fallas 503, lista de reintentos, `/salud`, configuración; C-6 aplicado a la 001 (QP-11) | F4; C-6 aprobado |
| F6 Conciliación y demo con base de datos | 24–25 nov | Código, Grok (revisa Claude); demo, Hugo | `LatidoDeConciliacion` y `estado_del_servidor`; guía de Supabase (reactivar, copia, migraciones). Hugo exporta una copia de la base de la demo, borra los datos de prueba del #97 (H-12), la marca con `--entorno demo --ya-aplicada 0001` y aplica 0002 y 0003; CE-001 y CE-016 con dinero real | F5 |
| FN Cierre | 25 nov | Hugo y Claude | Comprobar que C-6 y C-7 están aplicados (QP-11); revisión de seguridad (constitución, flujo 6); `verification-guide.md` completo; PR con la plantilla y `Closes #90, #19, #94` | F6 |
| **Fin del corte 2** | **mié 25 nov** | | | |

---

## 9. Decisiones

### 9.1 Decisiones del plan

Las que vienen de la versión con AWS conservan su número. Se retiraron con D-4: DP-1, DP-4, DP-22 a DP-26, DP-29, DP-30 y DP-37.

| # | Decisión | Por qué | Alternativas descartadas |
|---|---|---|---|
| DP-6 | Interfaz `Almacen` con dos implementaciones: memoria y PostgreSQL | Las pruebas de la API no necesitan PostgreSQL (principio V) y se puede simular un reinicio | Llamar a psycopg desde `main.py`: no se puede probar sin base de datos |
| DP-7 | La memoria es una caché de escritura directa: primero la base de datos, después la memoria y el canal (R-8) | Un solo proceso: la memoria nunca queda desactualizada; el canal y la consulta de respaldo no cambian | Leer siempre de la base de datos: una consulta cada 3 a 5 s por pantalla abierta |
| DP-8 | Candado por cobro (`asyncio.Lock`) al registrar pagos; `unique (cobro_id, numero)` como red | El aviso, la consulta y la conciliación no calculan el mismo número a la vez (RF-008) | Reintentar al chocar con `unique` |
| DP-9 | El pago y su `webhook-id` se guardan en la misma transacción | Si falla una, falla la otra: un reintento de pey se procesa completo | Dos escrituras separadas |
| DP-10 | Todas las horas se escriben con el `Reloj` del servidor; nunca con `default now()` | RF-006 (QA-18) y las pruebas con `RelojFalso` | Dejar que la base de datos ponga `creado_en`: dos relojes |
| DP-11 | El estado se calcula en Python; la columna `estado` de la vista no se usa (QA-11) | Reloj controlado y ventana de escucha, que la vista no conoce | Leer la vista |
| DP-12 | `ultima_consulta_pey` solo en memoria | Escribirla sería una escritura cada 3 a 5 s por cobro mirado | Guardarla |
| DP-13 | La consulta de respaldo y la conciliación pasan a pey las transacciones del cobro, no un conjunto global | Tras un reinicio no hay conjunto global; las transacciones de un QR solo pueden ser de ese cobro | Cargar todas las transacciones al arrancar |
| DP-14 | Una tarea de fondo en el ciclo de vida, con el `Reloj` inyectado: reintentos de avisos cada 15 s y latido de conciliación cada 60 s | RF-048 y RF-061 piden trabajo aunque nadie mire (excepción a DP-5 de la 001, §12) | Un cron externo: otra pieza fuera de las pruebas |
| DP-15 | Los registros de fallas llevan solo el nombre de la clase del error | El texto de psycopg puede traer servidor y usuario (RF-021) | Registrar el error completo |
| DP-16 | Sin `DATABASE_URL`, el servidor usa la memoria, avisa en el registro y la salud dice `"sin configurar"`. La guía de la demo exige `"responde"` desde el corte 2 | Juan, Miguel y Leonel pueden correr el servidor sin Supabase; la demo no puede quedar en memoria sin que se note | Negarse a arrancar sin base de datos |
| DP-17 | Los archivos de migración no llevan `begin`/`commit`; el comando corre cada uno en una transacción junto con su registro | Una migración queda completa o no queda (RF-019) | Dejar el `begin`/`commit` del PR #97 |
| DP-18 | Marca de entorno (`local`/`demo`) en la base, puesta la primera vez; los datos de prueba solo en `local` | RF-054 con una comprobación en la base | Confiar en una variable de la computadora |
| DP-19 | La base de la demo (creada a mano con el PR #97) se registra con `--ya-aplicada 0001` después de revisarla | Historia 6, escenario 3, sin que el comando adivine | Detectarlo solo |
| DP-20 | La migración 0002 no recrea la vista `cobros_con_estado` | El servidor no la usa (DP-11); el historial (#38) la recrea si la necesita | Recrearla ahora |
| DP-21 | El servidor entrega la web en el mismo origen; CSP `connect-src 'self'` (R-12) | Un solo túnel y un solo origen; RF-027 y RF-029 | Dos túneles |
| DP-27 | CI con `pull_request` y `push` a `main`, `permissions: contents: read` y sin secretos; trabajos `servidor` y `web` en F1 y `base-de-datos` en F4 (R-11) | RF-036 a RF-038 | `pull_request_target`: expone secretos a los forks |
| DP-28 | F1 se entrega en su propio PR desde `main` (`feature/35-ci`), antes que el resto del código de la 003 | Entra pronto a `main` y prueba los PR siguientes | Entregarlo junto con el resto |
| DP-31 | La salud consulta la base de datos con `select 1` y 2 s de espera, y guarda el resultado 10 s | Rápida y sin cargar la base de datos | Consultar en cada petición |
| DP-32 | Mensajes de falla para el dueño, como en el [contrato](contracts/fallas-base-de-datos.md) | Principio VII; la web ya los muestra o reconecta | Mensajes técnicos |
| DP-33 | Un solo objeto `Cobro` por id: después de cargar de la base de datos, se usa el que ya esté en memoria si otra petición lo cargó antes, sin `await` entre comprobar y guardar | El canal y el aviso comparten el mismo objeto | Un candado por id al cargar |
| DP-34 | Un aviso con `amount` ≤ 0 responde 400 sin marcar el `webhook-id`; uno sin `type` se guarda con `tipo` vacío; un error de datos de PostgreSQL se registra, responde 400 y nunca entra a la lista de reintentos | El esquema del PR #97 rechaza esos datos; sin esto, un aviso se reintentaría para siempre | Quitar las restricciones del esquema |
| DP-35 | Al crear un cobro, cada escritura en la base de datos espera como máximo 2 s; las demás operaciones, 5 s | 2 + 10 (pey) + 2 = 14 s, por debajo de los 15 s de la web (H-10) | Subir la espera de la web: cambio a la 002 |
| DP-36 | En la demo, `LIMITE_COBROS_POR_MINUTO` y `CANALES_POR_IP` valen 30, en `backend/.env.demo` | Jueces en el mismo wifi o con la misma compañía comparten IP pública; son configurables desde la 001 | Dejar 10 |
| DP-39 | Conciliación por latido: `estado_del_servidor.conciliado_hasta` y una revisión cada 60 s de los cobros cuya ventana terminó desde esa marca (R-5, data-model §4.1) | Una sola pieza cubre la demo apagada y los avisos perdidos en un reinicio; una consulta a pey por cobro; su escritura cumple RF-039. Un 4xx de pey salta el cobro, y una falla pasajera lo salta después de 10 latidos, para que nada la atore (QP-13) | Revisar 7 días al arrancar; columna por cobro |
| DP-40 | La IP real llega con `X-Forwarded-For` del agente del túnel, sin código nuevo; si F0 muestra que no llega, los límites de la demo suben a 60 y se anota como TK (R-2) | El servidor ya confía en `127.0.0.1` (H-8) | Código propio por cada túnel |
| DP-41 | El corte 1 sale con los cobros en memoria (el código de la 001); el almacén llega en el corte 2 | QA-12: el corte 1 no depende de Supabase ni de las migraciones | Esperar al almacén para abrir la demo |
| DP-42 | La demo corre en la Mac de Hugo: uvicorn con `--workers 1`, sin `--host` (solo `127.0.0.1`), `--env-file backend/.env.demo` (QP-14), `CARPETA_WEB`, y `caffeinate` mientras está encendida, conectada a la corriente (R-4). Si a la vez corre un servidor de desarrollo, usa el puerto 8001 | RF-056, RF-060 y un solo proceso, sin herramientas nuevas | Un servicio de `launchd`: más piezas para encender en momentos acordados |
| DP-43 | Una sola guía, `docs/operacion-demo.md`, con encender y apagar, `backend/.env.demo`, aviso de pey, calendario (cada 5 días y del 12 al 14 dic), Supabase y migraciones contra la demo con `uv run --env-file backend/.env.demo` | RF-050, RF-051, RF-058 y RF-060 en un solo lugar | Repartirlo en varios README |
| DP-44 | `backend/.env.demo` declara todas las variables de la demo, con `DATABASE_URL=` vacía hasta F6 (T071). Salió de `/speckit-analyze` del 2026-11-21 (U1) | `Configuracion` siempre lee también `backend/.env` y pydantic-settings completa con él lo que falta; una variable vacía en el archivo de `--env-file` manda sobre `backend/.env` (comprobado con valores falsos). Sin esto, la demo usaría la base de desarrollo desde T045 (RF-049) | Cambiar `config.py` para no leer `backend/.env` con `--env-file`: código nuevo para un problema que resuelve una línea |

### 9.2 Decisiones de Hugo

| # | Duda | Recomendación | Decisión |
|---|---|---|---|
| DP-2 | ¿Qué librería de PostgreSQL? (R-6) | psycopg 3 | **psycopg 3** (Hugo, 2026-11-17). Sigue vigente |
| DP-3 | ¿Qué herramienta de migraciones? (R-7) | Comando propio | **Comando propio** (Hugo, 2026-11-17). Sigue vigente |
| DP-5 | ¿Quién implementa cada fase y quién revisa? | Grok implementa el código de F1, F2, F4, F5 y F6; Claude revisa cada fase; Hugo hace F0, el túnel, el aviso de pey, los pagos reales y la demo con la base de datos, y aprueba cada cierre con la guía de verificación | **Grok implementa, Claude revisa** (Hugo, 2026-11-17). Sigue vigente con las fases nuevas |
| DP-38 | ¿Qué túnel? (R-1) | **Tailscale Funnel**: el único que cumple los 7 criterios sin pagar ni dominio, con el HTTPS en la computadora. Si falla F0, Cloudflare Tunnel con un dominio barato | **Tailscale Funnel** (Hugo, 2026-11-20), como se recomienda. Si F0 falla, se vuelve a decidir con la opción B |

### 9.3 Revisión QA del plan

QA del 2026-11-20, en una sola pasada, contra la spec aprobada, la constitución 3.0.0 del PR #96 y el código de esta rama. Según C-8, la QA no aprueba el plan hasta que los PR #72 y #96 estén unidos.

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QP-10 | Hueco | El plan pone "Rama sobre `main`" recién en F4, pero F2 ya escribe código en `feature/90-infraestructura-demo`, que sale de `feature/64-web-mvp` en una versión vieja: no tiene `1a15c14` (arreglo de WebKit del #72), ni la constitución 3.0.0, ni el esquema del #97 (H-19). El PR de F2 traería commits de la 002 ya unidos y una rama que el CI de F1 no ha probado. | §8 (F2, F4), DP-28 | En cuanto se unan #72 y #96, y antes de empezar F2, Hugo rebasa `feature/90-infraestructura-demo` sobre `main`, o la rehace desde `main` con los commits de `specs/003-*`. F4 deja de tener ese paso. | Aceptada por Hugo el 2026-11-20: la rama se pone al día sobre `main` antes de F2. Aplicada el 2026-11-20 |
| QP-11 | Contradicción | El plan deja C-6 y C-7 para FN ("si Hugo los aprueba"), pero el código los necesita antes. (a) F2 cambia la CSP a `connect-src 'self'`, y eso rompe el flujo de desarrollo de la 002 (web en el puerto 5173 con `config.js` en `http://localhost:8000`: `specs/002-web-mvp/quickstart.md:32-40`, `web/README.md:34-45`), que C-7 (b) y (c) corrige. (b) F5 responde 400 a un `amount` ≤ 0 y agrega `base_de_datos` a la salud, y eso contradice los contratos de la 001 hasta que se aplique C-6 (c) y (g). Entre la fase y FN, las specs aprobadas quedarían diciendo lo contrario del código. | C-6, C-7, F2, F5, FN | Hugo aprueba C-6 y C-7 antes de las tareas. C-7 se aplica en F2 y C-6 en F5, cada uno en la fase que cambia ese comportamiento. FN solo comprueba que estén aplicados. | Aceptada por Hugo el 2026-11-20: C-6 y C-7 se aprueban antes de las tareas; C-7 se aplica en F2 y C-6 en F5. Aplicada el 2026-11-20 |
| QP-12 | Hueco | F0 dice "sobre el servidor actual", pero ese servidor todavía no entrega la web (`CARPETA_WEB` llega en F2), y un túnel solo expone un puerto. Además, el quickstart §3.2 crea el cobro "desde el celular", algo que en F0 no se puede. Faltan los requisitos de Funnel: cuenta de Tailscale, HTTPS y MagicDNS activados y el permiso `funnel` en la política del tailnet ([funnel](https://tailscale.com/kb/1223/funnel)). | F0, quickstart §3, RF-026, RF-028, RF-030, RF-057 | F0 sin la web, con el servidor actual: (1) requisitos de Funnel; (2) `POST /api/cobros` de $0.01 por la dirección del túnel con `curl`, que crea un QR real sin pagarlo; (3) `curl -N` al canal de eventos de ese cobro **desde otra red** (celular con datos como punto de acceso, o Leonel), anotando la hora de cada evento durante 25 minutos; (4) dos peticiones desde redes distintas para ver las dos IP en el registro; (5) reiniciar la computadora y comprobar la misma dirección. El quickstart §3 queda como comprobación de F2, con la web. | Aceptada por Hugo el 2026-11-20: F0 con `curl`, sin la web, con los requisitos de Funnel. Aplicada el 2026-11-20 |
| QP-13 | Caso límite | La conciliación "no avanza" si pey falla con un cobro (data-model §4.1), pero no distingue una falla pasajera de una permanente. Un cobro que pey no conoce la bloquearía **para siempre**. Ya pasa con los datos de prueba: `prueba-pendiente` y `prueba-cancelado` tienen `codi_qr_id` ficticios (`qr-prueba-1`, `qr-prueba-4`) y su ventana termina 15 y 20 minutos después de cargarlos (`supabase/002_datos_de_prueba.sql`, bloque A). A los 20 minutos, la conciliación de desarrollo se atoraría. | RF-061, DP-39, data-model §4.1 | Una respuesta 4xx de pey (por ejemplo, 404: QR inexistente) se registra y ese cobro se salta. Una falla pasajera (sin conexión, tiempo agotado, 5xx) se reintenta en cada latido hasta 10 veces (unos 10 minutos); después se registra como `ERROR` y se salta. `conciliado_hasta` avanza en los dos casos. Pruebas: `test_un_qr_que_pey_no_conoce_no_bloquea_la_conciliacion` y `test_tras_10_fallas_el_cobro_se_salta_con_error`. | Aceptada por Hugo el 2026-11-20: 4xx se salta; las fallas pasajeras, después de 10 latidos. Aplicada el 2026-11-20 |
| QP-14 | Hueco | La computadora de la demo también es la de desarrollo de Hugo, y las dos usarían el mismo `backend/.env`. RF-049 y RF-053 piden otra base y otra llave en desarrollo. Cambiar a mano el mismo archivo antes de cada demo es fácil de equivocar: pruebas de desarrollo en la base de la demo, o la llave de desarrollo en la demo. Lo mismo pasa con el comando de migraciones, que lee `DATABASE_URL`. | RF-049, RF-053, RF-054, RF-058, DP-42 | La demo usa su propio archivo, `backend/.env.demo` (ya lo ignora git: `.env.*` en `.gitignore`), cargado con `--env-file` de uvicorn y de `uv run`, sin código nuevo: las variables de entorno mandan sobre `backend/.env` en pydantic-settings. `backend/.env` queda para desarrollo. Si las dos corren a la vez, la de desarrollo usa el puerto 8001. La guía (DP-43) lo dice, también para correr las migraciones contra la demo. | Aceptada por Hugo el 2026-11-20: `backend/.env.demo` con `--env-file`; desarrollo en el puerto 8001 si las dos corren. Aplicada el 2026-11-20 |

**Bloques de la pasada:**

1. **Coherencia interna:** cada RF (RF-001 a RF-030, RF-036 a RF-039 y RF-048 a RF-061) y cada CE (CE-001 a CE-007, CE-010, CE-011 y CE-015 a CE-017) tiene prueba o paso manual en §7, comprobado con un script. DP citadas en research, data-model y contratos: todas existen; ninguna referencia a las DP retiradas. Verificación de la constitución completa y sin `[NECESITA ACLARACIÓN]`. Siguiente C-n libre: **C-10**. Salen QP-10, QP-13 y la errata 1.
2. **Otras specs, plan, reglas e issues:** contratos de la 001 (salud y aviso) frente a C-6; flujo de desarrollo de la 002 frente a C-7; constitución 3.0.0 (IV sin notas, V, IX con el parche 3.0.1 de QA-19, unión por el autor); `docs/plan-hackathon.md` (demo por enlace, producción de pey, 12 al 14 dic); issues #35, #65, #66, #27, #64, #90, #19 (PR #99 sigue abierto) y #94. Las reglas del hackathon (cobro real, producción, llave fuera del cliente, sin reventa) siguen cubiertas. Salen QP-11 y la errata 1.
3. **Código:** H-1 a H-19 comprobados. `ProxyHeadersMiddleware` de uvicorn recorre `X-Forwarded-For` de derecha a izquierda y toma la primera IP que no es de confianza (`uvicorn/middleware/proxy_headers.py:169-186`), como dice R-2. Las pruebas de la web sirven la página y el servidor simulado en el mismo origen (`web/tests/servidor_simulado.py:467-490`), así que `connect-src 'self'` no las rompe. El #97 hace `revoke … from anon, authenticated` (`supabase/001_esquema_inicial.sql:152-153`), así que el CI necesita crear esos roles (R-10). FastAPI deja `/docs` abierto por el túnel, como en la 001; no expone nada que la web no permita ya. Backend: 109 pruebas en verde. Salen QP-12, QP-13 y QP-14.
4. **API de pey:** la conciliación usa `GET /transaction/codi/qr/{id}`, ya usado por la consulta de respaldo (`pey.py:140-172`). El aviso solo se cambia en el portal, un solo aviso por llave, sin reintentos documentados y ambiente de pruebas "coming soon" (H-17). Qué responde pey a un QR inexistente no está documentado: QP-13 trata cualquier 4xx igual. Sale QP-13.
5. **Fuentes y dependencias externas:** cuenta de Tailscale y permisos de Funnel (QP-12), proyecto de Supabase de desarrollo (Juan, antes de F4), aviso de pey con la dirección del túnel (Hugo, F2), segunda llave (Hugo), protección de `main` (administrador), Leonel para N-17, celulares. Sale QP-12.
6. **Ambigüedades y casos límite:** reinicio y apagado (conciliación), datos de prueba con QR ficticios, la misma computadora para la demo y para desarrollo, canal largo, IP compartida, base de datos pausada. No hay pantallas nuevas. Salen QP-13 y QP-14.
7. **Seguridad y rendimiento:** secretos por archivo y por entorno (QP-14), HTTPS que termina en la computadora, `127.0.0.1`, RLS y `revoke`, límites por IP real, CORS y CSP; tiempos medibles (CE-002 a CE-004). Sale QP-14.
8. **Construibilidad y reparto:** corte 1 en 2 días con F0 adelantado, dependencias de C-8, rama desfasada (QP-10), Grok implementa y Claude revisa, Juan con Supabase de desarrollo antes del 23 nov. Salen QP-10 y QP-11.

**Errata** (sin efecto en el comportamiento; corregida el 2026-11-20 junto con las decisiones):

1. §8: #35 se cierra con el PR de F1 (`feature/35-ci`), no en F3. #27 y #64 se cierran después del pago real de F3, con el PR de F3 (README, `Closes #66`) o a mano, y #65 con el PR de F2.

La QA de la versión con AWS (QP-1 a QP-9) está en el historial, commit `5db47ed`. Lo que sigue vigente ya está en este plan: QP-1 (C-8 sin cambios), QP-2 (DP-33), QP-3 (DP-34 y C-6 g), QP-5 (DP-35), QP-6 (DP-36) y QP-8 (C-7 b y c).

---

## 10. Seguridad

- **Secretos**: `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` y `DATABASE_URL` solo en `backend/.env` (desarrollo) y en `backend/.env.demo` (demo, solo en la computadora de Hugo), los dos ignorados por git (QP-14). `DATABASE_URL` es `SecretStr` y nunca se imprime (RF-021). Se comprueba con `git grep` y con la prueba de registros (CE-010).
- **Túnel**: la sesión de Tailscale vive en su app, en la computadora de la demo (RF-059). El HTTPS termina en la computadora, así que el servicio del túnel no ve los avisos de pey (R-1, criterio 7). El túnel solo apunta al puerto 8000.
- **Red local**: el servidor solo escucha en `127.0.0.1` (RF-056, DP-42); otro equipo de la misma red no recibe respuesta (quickstart §3.6).
- **Base de datos**: RLS encendido y sin acceso para `anon` ni `authenticated` en todas las tablas, también en las del comando y en `estado_del_servidor` (RF-022). Solo el servidor tiene la cadena de conexión.
- **Firma de webhooks**: sin cambios; un aviso sin firma válida se rechaza antes de tocar la base de datos.
- **Entradas**: sin cambios en la validación de la 001. Todo el SQL usa parámetros de psycopg, nunca texto pegado.
- **Abuso de la demo pública**: límites por IP real (DP-36, DP-40); CORS solo con la dirección del túnel (RF-027); CSP `connect-src 'self'` (RF-029).
- **Datos de quien paga**: no se leen ni se guardan (RF-009), tampoco en la conciliación.
- **Llaves de pey**: la de la demo solo en la computadora de Hugo; la segunda llave de producción (RF-053) solo con quien Hugo la comparta. Si alguna se filtra, se rota y se avisa a pey en menos de 24 h (principio III).

---

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Tailscale Funnel corta el canal, retiene eventos o cambia de nombre tras reiniciar (no documentado, R-1) | Incumple RF-026, RF-057 o RF-030 | F0 lo prueba antes de escribir código; si falla, Hugo decide B (Cloudflare Tunnel con dominio) |
| El túnel no manda la IP real (R-2) | Los límites por IP cuentan a todos como una sola IP | DP-40: límites de 60 en la demo y TK escrito |
| Funnel está en beta y el plan Personal es "no comercial" | Cambios del servicio sin aviso | El video y las instrucciones de prueba muestran el flujo completo; plan B listo (R-1) |
| La computadora de la demo se suspende, se apaga o pierde internet, sobre todo del 12 al 14 dic (72 horas) | La demo no responde a los jueces | `caffeinate`, corriente conectada, actualizaciones automáticas de macOS en pausa esos días (guía), Leonel prueba cada día (N-17) y avisa en el momento; RF-061 registra los pagos de ese rato |
| La red de casa de Hugo se cae | La demo no responde | La guía dice cómo volver a encender; la dirección no cambia (RF-030) |
| Los PR #72 y #96 tardan en unirse | El plan no se aprueba (C-8) y F1 no empieza | Hugo los une él mismo (constitución 3.0.0), después de atender los 4 cambios que pidió Juan en el #72 y de agregar el parche 3.0.1 al #96; después pone al día la rama de la 003 (QP-10) |
| Las pruebas de WebKit fallan en Linux | El trabajo `web` del CI sale en rojo | Arreglo del #72 (`1a15c14`); si falla alguna, TK con `skip` y motivo escrito, o arreglo |
| La base de la demo tiene los datos de prueba del PR #97 (H-12) | Incumple RF-054 | En F6, antes de marcarla `demo`, Hugo corre los borrados del bloque F |
| Supabase pausa el proyecto entre momentos acordados | La demo no guarda | Guía: encender al menos cada 5 días (RF-050); salud `"no responde"`; reactivación |
| La ida y vuelta a Supabase desde casa hace lentos el QR o el aviso | Incumple CE-003 o la respuesta en menos de 1 s al aviso | Se mide en F6; si no se cumple, se elige la región del proyecto o se decide con un TK |
| Pedir la imagen del QR a pey es lento (de 2.39 s a 9.09 s en TK-5 del plan 001) | Incumple CE-003 | Se mide en F3. Si no se cumple, Hugo decide con un C-n a la 003 y a la 002 si el QR se dibuja desde `qr` (D-2) |
| Falla el borrado de un cobro cuando pey no creó su QR (RF-052) | Queda un cobro sin QR en la base de datos | Se registra (RF-016); el historial (#38) puede filtrar `codi_qr_id is null`. Limitación aceptada |
| 2 días para el corte 1 y 3 para el corte 2 | Algún corte no llega | F0 se adelanta; el corte 1 no depende de Supabase (DP-41); lo que no llegue del corte 2 se anota y se pasa a S2 |

---

## 12. Seguimiento de complejidad (Complexity Tracking)

| Excepción | Por qué hace falta | Alternativa más simple descartada y por qué |
|---|---|---|
| Una tarea de fondo en el servidor (DP-14), cuando el plan de la 001 (DP-5) evitó las tareas de fondo | RF-048 exige reintentar avisos aunque nadie tenga la pantalla abierta, y RF-061 exige conciliar las ventanas que terminan aunque nadie mire | Reintentar o conciliar solo cuando alguien abre el cobro: un pago podría no registrarse nunca (principio VIII). Un cron en la computadora: otra pieza fuera de las pruebas |

---

## 13. Aprobación

- [x] DP-2, DP-3 y DP-5 decididas por Hugo (2026-11-17), vigentes.
- [x] DP-38 decidida por Hugo (2026-11-20): Tailscale Funnel.
- [x] PR #72 y PR #96 unidos a `main` (C-8), el 2026-11-21; la rama de la 003 quedó rebasada sobre `main` (QP-10).
- [x] Plan revisado con `/qa-spec 003 plan` y todos los hallazgos QP decididos (2026-11-20).
- [x] Decisiones de la QA aplicadas (QP-10 a QP-14 y la errata), el 2026-11-20.
- [x] C-6 y C-7 aprobados por Hugo, ampliados, el 2026-11-20 (QP-11). Se aplican en F5 y F2.
- [x] Aprobado por Hugo el 2026-11-21. Aprobar no autoriza a empezar `tasks.md`: se espera a que Hugo lo pida.

---

## 14. Registro de implementación

| # | Fecha | Qué | Por qué | Afecta |
|---|---|---|---|---|
| TK-1 | 2026-11-21 | **Dirección de la demo (F0, T001): `https://pago-facil.tail8d44cb.ts.net`.** Tailscale la arma como `<nombre de la máquina en el tailnet>.<nombre del tailnet>.ts.net`. (1) El nombre de la máquina se cambió en la consola (*Machines → Edit machine name*, sin «Auto-generate from OS hostname») de `macbook-air-de-hugo` a `pago-facil`, para no publicar el nombre del dueño. El nombre de la Mac en macOS sigue siendo «MacBook Air de Hugo» y no afecta la dirección. (2) La parte `tail8d44cb` es el nombre DNS del tailnet (consola, página *DNS*): lo asigna Tailscale y no acepta un nombre libre como `pago-facil`; Hugo intentó renombrarlo y se queda así. (3) MagicDNS y los certificados HTTPS quedaron activos; el certificado es para `pago-facil.tail8d44cb.ts.net`. | La dirección va en el README, en la entrega del hackathon y en el aviso de pey, y no debe cambiar (RF-030). Por eso ni el nombre de la máquina ni el del tailnet se vuelven a tocar. Si alguien cambia cualquiera de los dos, cambia la dirección: hay que actualizar `WEB_ORIGIN` en `backend/.env.demo`, el aviso de pey y el README | RF-024, RF-025, RF-030; T002, T025, T032 |
| TK-2 | 2026-11-21 | `backend/.env.demo` creado (T002) con la llave de pey que ya estaba en `backend/.env` (la segunda llave, para desarrollo, llega en T048). `PEY_WEBHOOK_SECRET` queda vacía: esa llave todavía no tiene aviso dado de alta, así que no hay secreto. La comprobación `"secreto_aviso_pey": true` pasa de T002 a T025. Decisión de Hugo | F0 crea un QR sin pagarlo y no necesita el aviso. Darlo de alta antes de T006 arriesga cambiar la dirección si F0 falla y se pasa al plan B | RF-025; T002, T025 |
| TK-3 | 2026-11-21 | T022 agrega a `docs/operacion-demo.md` una tabla con cada variable de `backend/.env.demo`: los valores que no son secretos, tal cual; los secretos, como "del portal de pey (o de Supabase), solo en la Mac de la demo". Así el equipo revisa la configuración sin recibir el archivo; con la demo encendida, `GET /salud` dice si cada credencial está puesta. Decisión de Hugo | Hugo pidió que el equipo pueda revisarla. El archivo nunca se comparte (principio III); una plantilla `.env.demo.example` pedía una excepción en `.gitignore` | Principio III, RF-020; T022 |
| TK-4 | 2026-11-21 | **Sustituye a TK-3.** Se sube `backend/.env.demo.example`: las mismas variables que `backend/.env.demo`, con los valores que no son secretos (`WEB_ORIGIN`, límites, `DATABASE_URL` vacía) y las llaves de pey vacías. `.gitignore` agrega `!.env.demo.example`; el `backend/.env.demo` real sigue ignorado por `.env.*` (comprobado con `git check-ignore -v`). T022 enlaza la plantilla en lugar de repetir la tabla. Decisión de Hugo | Hugo pidió que el equipo pueda correrlo. Sacar el `.env.demo` real del ignore subiría la llave de pey a un repositorio público (principio III). El equipo no puede encender la demo de Hugo (el túnel vive en su Mac y cada llave admite un solo aviso): la plantilla sirve para entenderla o armar la suya | Principio III, RF-020, DP-44; T022 |
| TK-5 | 2026-11-21 | **Resultado de F0: Tailscale Funnel cumple; no hace falta el plan B (R-1).** Dirección `https://pago-facil.tail8d44cb.ts.net` (TK-1). (a) HTTPS válido desde un celular con datos (T003). (b) Canal de un QR real de $0.01 sin pagar, abierto 17:28:12 → `vencido` 17:37:56 → `fin` del servidor 17:47:56, con 73 señales de vida cada 16–17 s (una a 21 s) llegando en el momento: sin retención (RF-057) ni cortes (RF-026) (T004). (c) La IP pública de cada cliente llega por `X-Forwarded-For` desde dos redes distintas, nunca `127.0.0.1`: no se aplica DP-40 y los límites se quedan en 30 (T005); un iPhone con iCloud Private Relay llega con la IP del relay. (d) Misma dirección tras reiniciar servidor, túnel y computadora; tras el reinicio hay que abrir la app de Tailscale y Funnel vuelve solo por `--bg` (T006). Detalle en la guía de verificación, F0 | QP-12 pedía probar el túnel antes que todo lo demás de la demo. Dos hallazgos para las fases siguientes: crear un cobro tardó 9.8 s, casi todo pey (riesgo de CE-003 del plan §11, se mide en T029); y en cuanto se activó HTTPS llegaron escáneres automáticos (todo 404), lo que refuerza apagar la demo fuera de los momentos acordados (RF-060). Para probar el túnel desde la propia Mac se fuerza la IP pública del relay con `curl --resolve`, porque si no la petición va por dentro del tailnet | RF-024, RF-026, RF-028, RF-030, RF-057; DP-38, DP-40; T003 a T006, T022, T029 |
| TK-6 | 2026-11-21 | En T014, la prueba que falla a propósito usa `assert 1 + 1 == 3` en lugar de `assert False`. Resultado en el PR #103: `servidor` en rojo solo en `pytest -q` (`1 failed, 112 passed`), `web` en verde y `gh pr merge` sin `--admin` rechazado por la protección de `main`; el PR se cerró sin unir y se borró la rama | Ruff rechaza `assert False` (B011), y `servidor` habría fallado en el lint antes de llegar a pytest, sin probar lo que pide CE-006. No se intentó `--admin`: `enforce_admins` ya está en `true` (T013) y, si funcionara, metería una prueba rota en `main` | RF-036, RF-037, CE-006; T014 |
| TK-7 | 2026-11-22 | En T030 los dos primeros pagos se hicieron con el servidor arrancado una sola vez con `EXPIRACION_SEGUNDOS=1200` (y registro con hora por una tubería), no solo el pago tardío como pedía la tarea. El pago que prueba CE-004 se hizo a los 20 min 11 s, con el QR ya vencido en la web, dentro de la gracia. Después se hicieron otros tres pagos (cobros 3 a 5), con la pantalla en el Android y en el iPhone | Evitar un segundo reinicio y poder medir las horas con el mismo reloj de la Mac. El primer pago no depende de la vigencia. El caso extremo salió del propio pago de Hugo | T030, CE-002, CE-004; guía de verificación F3 |
| TK-8 | 2026-11-22 | En T031 el portal de pey no ofrece reenviar un aviso (tampoco la documentación ni el API: solo existe «Webhook Logs» para ver las entregas). El reenvío se sustituyó por una repetición del aviso hecha con un script que lo firma con el secreto leído dentro de su proceso: mismo cobro y misma transacción, primero con otro `webhook-id` y luego con el mismo. Respuesta `200`, `procesado: false` las dos veces y el cobro siguió con un solo pago | pey no tiene reenvío, y el servidor firmaba igual que lo haría un reintento de pey, así que prueba el mismo código (RF-007). Lo decidió Hugo el 2026-11-22 | T031, RF-007 |
| TK-9 | 2026-11-22 | La prueba de Leonel de T031 (abrir con HTTPS y QR en menos de 3 s desde su red y sus celulares, N-17) se saca de la tarea y pasa al issue #105, asignado a Leonel. T031 se marca hecha en lo demás (reenvío, TK-8) | Hugo dijo que Leonel no podrá probar ese día ni esa noche, y T033 y el cierre del corte 1 no deben esperar. Leonel no necesita `.env`: solo el enlace y que Hugo encienda la demo (`docs/operacion-demo.md` §10) | T031, T033, N-17 |
| TK-10 | 2026-11-22 | **C-10 aplicado.** CE-003 y la historia 2 (escenario 2) pasan de "menos de 3 segundos" a "5 segundos o menos" en 9 de cada 10 intentos. Se cambiaron la spec, el plan (metas y principio VII), el quickstart §4 paso 2, las tareas (objetivo de F3, T029, T031 y T073) y `docs/operacion-demo.md` §10. T029 queda hecha | La medición de T029 (3 a 5 s) no cumplía los 3 s; pey por sí sola gasta unos 2.3 s. Hugo lo aprobó el 2026-11-22. No se cambia CE-006 de la 002 | CE-003, T029, T031, T073 |
| TK-11 | 2026-11-22 | **`database_url` se adelanta de F5 a F4.** El plan §4 deja `database_url` (`SecretStr`) en `config.py` para F5. T036 ya lo prueba y T039 lo agrega, porque el comando de migraciones lee `DATABASE_URL` con `Configuracion` (T041). El servidor sigue sin usarlo hasta F5. | El comando no puede leer la conexión si el campo no existe, y las pruebas van antes que el código (principio V). | RF-020, RF-021; T036, T039, T041; plan §4 |
| TK-12 | 2026-11-22 | **Opción (a): el comando valida antes de crear las tablas de control.** `test_ya_aplicada_se_rechaza_si_no_existe_cobros` exige que un rechazo no deje tablas nuevas. El data-model §5.1 pide crear `cambios_de_estructura` y `entorno_de_la_base` antes de migrar. Se comprueban primero la primera vez sin `--entorno`, la marca distinta, `cobros` sin registro, `--ya-aplicada` inválida y los datos de prueba en una base `demo`; solo si se va a seguir se crean las tablas. `estado` solo lee. | Crear las tablas y rechazar después dejaba dos tablas de más y rompía la prueba de T038. No se cambió la prueba ni el data-model. | T038, T041; data-model §5.1; RF-019 |
| TK-13 | 2026-11-22 | **El comando no parte el SQL y la primera migración lleva la preparación.** (1) `app/migraciones.py` ya no separa el script por `;`: manda cada archivo entero a PostgreSQL, que entiende `$$`, `E'…'` y los comentarios, así que una migración futura con funciones no se rompe. (2) Las tablas de control, la marca de entorno y la anotación de `--ya-aplicada` se guardan en la misma transacción que la primera migración pendiente: si esa falla, la base queda como estaba y se puede reintentar (antes quedaban guardadas). Cada migración sigue en su propia transacción con su fila. Se agregaron dos pruebas a T038 (`test_una_migracion_con_funciones_y_textos_con_punto_y_coma_se_aplica` y `test_si_la_primera_migracion_falla_no_queda_ni_la_marca_de_entorno`); las doce anteriores no cambiaron | Detalles de la revisión de T041: el separador propio fallaba con funciones y una marca de entorno huérfana obligaba a repetir `--entorno` tras un fallo. No cambian el contrato §4 ni el data-model §5.2 (regla 1) | T038, T041; RF-019, RF-049; contrato comando-migraciones §4 |
