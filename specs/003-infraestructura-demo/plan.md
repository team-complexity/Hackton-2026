# Plan: Infraestructura de la demo pública: guardar los cobros, publicar con HTTPS y probar cada cambio

- **Rama**: `feature/90-infraestructura-demo`
- **Fecha**: 2026-11-17
- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-17 (con el cambio C-8 del mismo día)
- **Estado del plan**: `Borrador`. Lo redactó Claude el 2026-11-17 con `/speckit-plan`, antes de que se unan los PR #72 y #96, como permite C-8: se revisa contra la constitución 2.0.0 del PR #96 (commit `aa187d7`) y el código de esta rama. Hugo decidió DP-1 a DP-5 el mismo día, todas como se recomendaba (§9.2). Falta la QA (`/qa-spec 003 plan`), que no lo aprueba hasta que los dos PR estén en `main`.
- **Entrada**: la spec de `specs/003-infraestructura-demo/spec.md`

> **Notas para los comandos de spec-kit.**
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
> - Los títulos marcados entre paréntesis (*Technical Context*, *Constitution Check*, *Project Structure*, *Complexity Tracking*) son las secciones que espera `/speckit-plan`.
> - El plan se escribe en español.
> - El plan dice **CÓMO**. Cada pieza cita los RF de la spec que cumple.

---

## 0. Resumen

La spec pide tres cosas sin cambiar lo que el dueño ve y oye: que los cobros sobrevivan a un reinicio, una demo pública con HTTPS y un CI en cada pull request, todo dentro de 200 dólares de AWS hasta el 31 de enero.

El enfoque:

- **Guardar**: el servidor de la 001 sigue trabajando con sus objetos en memoria, pero la memoria pasa a ser una caché de escritura directa sobre un *almacén* de PostgreSQL (Supabase, esquema del PR #97). Cada escritura va primero a la base de datos. Después de un reinicio, un cobro se carga al pedirlo. Los pagos se registran con un candado por cobro (DP-6 a DP-14).
- **Migraciones**: un comando propio aplica en orden los archivos de `supabase/migraciones/`, anota cada uno y separa los datos de prueba con una marca de entorno (DP-3, DP-17 a DP-20).
- **Demo pública**: una instancia EC2 pequeña, con IP elástica, detrás de CloudFront, que pone el HTTPS en `*.cloudfront.net`. El servidor entrega también la web, en el mismo origen. El presupuesto detiene la instancia con la acción nativa de AWS Budgets (DP-1, DP-21 a DP-26).
- **CI**: GitHub Actions, sin secretos, con trabajos para el servidor, la web y un PostgreSQL desechable. La publicación automática del corte 2 usa OIDC (DP-27 a DP-29).

### 0.1 Hechos del código y de las fuentes

| # | Hecho | Evidencia |
|---|---|---|
| H-1 | Todo el estado vive en `RepositorioCobros`, en memoria y con métodos síncronos: índices por id, por `codi_qr_id`, transacciones vistas y `webhook-id` vistos | `backend/app/cobros.py:134-233` |
| H-2 | El canal y la consulta de respaldo guardan y modifican el objeto `Cobro` en memoria (`cobro.pagos`, `ultima_consulta_pey`) | `backend/app/canal.py:58-103`, `backend/app/respaldo.py:58-65` |
| H-3 | `crear_cobro` crea el cobro en memoria, llama a pey y lo descarta si pey falla | `backend/app/main.py:173-223` |
| H-4 | El webhook marca el `webhook-id` después de procesar y responde 200 a lo que ignora | `backend/app/main.py:268-325` |
| H-5 | `pagos_del_qr` recibe el conjunto **global** de transacciones vistas para saber cuándo parar de paginar | `backend/app/pey.py:140-172`, `respaldo.py:67` |
| H-6 | La configuración no lee `DATABASE_URL`, aunque `.env.example` la tiene | `backend/app/config.py:13-38`, `backend/.env.example` |
| H-7 | `/salud` devuelve solo `estado`, `llave_pey` y `secreto_aviso_pey` | `backend/app/main.py:155-161` |
| H-8 | La IP de los límites sale de `ProxyHeadersMiddleware` con `PROXIES_CONFIABLES` (por defecto `127.0.0.1`) | `backend/app/main.py:139-140`, `config.py:35` |
| H-9 | La web ya admite el mismo origen (`config.js` vale `""`), pero su CSP permite `connect-src … http://localhost:8000 https:` | `web/config.js:2`, `web/index.html:8` |
| H-10 | La web trata cualquier error que no sea 404 al consultar un cobro como "sin conexión" y reintenta | `web/js/servidor.js` (QA de la spec, bloque 3) |
| H-11 | El esquema del PR #97 se corre a mano, una sola vez, con `begin`/`commit` propios; no tiene `qr_imagen`; usa los roles `anon` y `authenticated` de Supabase | `supabase/001_esquema_inicial.sql` (PR #97, `891960d`) |
| H-12 | El PR #97 ya se corrió, con sus datos de prueba, en el único proyecto de Supabase que existe | Descripción del PR #97 |
| H-13 | No hay `.github/`: no existe ningún CI | `ls .github` |
| H-14 | App Runner corta toda petición a los 120 s | [App Runner, develop](https://docs.aws.amazon.com/apprunner/latest/dg/develop.html) (research R-1) |
| H-15 | CloudFront espera hasta su tiempo de respuesta (30 s por defecto) entre un dato y el siguiente; el canal manda una señal de vida cada 15 s | Research R-3; `canal.py:91` |
| H-16 | CloudFront agrega la IP del celular al final de `X-Forwarded-For` sin quitar lo que mandó el celular; `CloudFront-Viewer-Address` trae un solo valor | Research R-4 |
| H-17 | AWS Budgets puede detener instancias EC2 por sí mismo | Research R-5 |
| H-18 | El backend tiene 109 pruebas en verde | Revisión del PR #72 (Juan, 2026-11-17) |

---

## 1. Contexto técnico (Technical Context)

- **Lenguaje y versión**: Python 3.11 o superior (3.12 en el CI y en la instancia).
- **Dependencias principales**: FastAPI, httpx, pydantic-settings, standardwebhooks y uvicorn, como hoy. **Nuevas** (DP-2): `psycopg[binary]` 3 y `psycopg-pool`, fijadas a versiones publicadas hace al menos dos semanas.
- **Almacenamiento**: PostgreSQL de Supabase, plan gratuito: un proyecto para la demo y otro para local (RF-049). Conexión por el *pooler* en modo sesión (research R-11). En las pruebas de la API, almacén en memoria.
- **Pruebas**: pytest con pey simulado (`httpx.MockTransport`), `RelojFalso`, almacén en memoria y almacén que falla a propósito. Las pruebas del almacén de PostgreSQL y de las migraciones corren contra un PostgreSQL 17 desechable (research R-12). Playwright para la web, como hoy.
- **Plataforma de destino**: AWS (DP-1), creada con la guía en la consola (DP-4): una instancia EC2 `t4g.micro` con Ubuntu 24.04, IP elástica, systemd y uvicorn en el puerto 8000; CloudFront delante, con HTTPS en `*.cloudfront.net`. La web, en el mismo servidor. CI y publicación automática en GitHub Actions.
- **Tipo de proyecto**: servicio web con PWA, como en las specs 001 y 002.
- **Metas de rendimiento**: QR en menos de 3 s en 9 de cada 10 intentos (CE-003); "Pago recibido" en menos de 2 s después del aviso de pey (CE-002); canal de 20 minutos sin cortes (CE-004); de vuelta en menos de 1 minuto después de publicar (RF-055); aviso de pey respondido en menos de 1 s (CE-010 de la 001, que se mantiene, C-6 f). Cada escritura en la base de datos agrega unos milisegundos si la instancia está en la región de Supabase (DP-24).
- **Restricciones**: un solo proceso (QP-5 de la 001); credenciales solo en `backend/.env` o en `/etc/pago-facil/entorno` (principio III); ninguna prueba automática con pey real ni con la base de datos real (principio V, CE-011); sin llaves de AWS en GitHub (RF-043); costo ≤ 150 dólares hasta el 31 de enero (RF-035).
- **Escala**: una demo, decenas de cobros al día, unos pocos celulares a la vez. Supabase gratuito: 500 MB, sobrado para la imagen del QR (unos KB por cobro).

---

## 2. Verificación de la constitución (Constitution Check)

*Puerta de paso: se revisa antes de la investigación (Fase 0) y otra vez después del diseño (Fase 1). Contra la constitución 2.0.0 del PR #96 (C-8).*

| Principio de la constitución | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. El pago se confirma en el servidor | No cambia: solo el aviso firmado y la consulta de respaldo registran pagos. La base de datos no se puede escribir desde fuera del servidor (RLS y `revoke` del PR #97, grupo de seguridad, RF-022) | Cumple |
| II. Una orden nunca se ejecuta dos veces | `transaccion_id` único con `on conflict do nothing`, candado por cobro, `webhook-id` guardado en la misma transacción que su pago. El evento `pago` sigue saliendo de una sola función, y solo si el `insert` devolvió fila (DP-8, DP-9) | Cumple |
| III. Los secretos nunca salen del backend | `DATABASE_URL` y las llaves de pey solo en `backend/.env` o en `/etc/pago-facil/entorno` (DP-26). Los registros nunca llevan el texto de un error de conexión (DP-15). Sin llaves de AWS en GitHub: OIDC (DP-29). La web y las apps nunca hablan con Supabase | Cumple |
| IV. Alcance anclado y trabajo documentado | Solo lo que pide la spec. Una nota de implementación por cada issue (#90, #19, #34, #65, #35, #94) en FN. C-6 y C-7 se aplican solo cuando Hugo lo pida | Cumple |
| V. Pruebas primero, en todo | Cada pieza tiene su prueba antes (§7). El almacén en memoria y el que falla a propósito sustituyen a la base de datos en las pruebas de la API; el SQL se prueba contra un PostgreSQL desechable, que no es la base de datos real (research R-12). Reloj controlado también en la tarea de fondo (DP-14) | Cumple |
| VI. CoDi real, reacción real | F5: pago real de $0.01 desde la demo pública, en Android y en iPhone, con autorización de Hugo (CE-001, CE-002) | Cumple |
| VII. Pensado para el mostrador | Mensajes de falla para el dueño (DP-32). QR en menos de 3 s y aviso en menos de 3 s (en la spec, menos de 2 s) | Cumple |
| VIII. Un pago no prueba identidad ni entrega | Pago tardío, monto distinto y falla de pey: sin cambios respecto a la 001. Falla de la base de datos: reintentos en memoria (RF-048) y consulta de respaldo. Devoluciones: fuera de alcance | Cumple |
| IX. Lo más simple que gane la demo | Piezas nuevas justificadas por la spec (base de datos, hosting, CI). Cada herramienta nueva con comparativa y decisión de Hugo: DP-1 a DP-4 (research R-1, R-8, R-9, R-14). Las comparativas se copian a las notas de implementación. Una sola tarea de fondo, justificada en §12 | Cumple, con excepción justificada en §12 |
| X. Si no se ve, no existe | `/salud` agrega `base_de_datos` y `estructura` sin valores (contrato de [salud](contracts/salud.md)). Cada falla de la base de datos y cada consulta de vida dejan su línea en el registro (RF-016, RF-039) | Cumple |

**Después del diseño (Fase 1)**: sin cambios; la tabla sigue igual con los contratos y el modelo de datos escritos, y con las decisiones DP-1 a DP-5 de Hugo. No quedan `[NECESITA ACLARACIÓN]`.

---

## 3. Estructura del proyecto (Project Structure)

### 3.1 Documentación de esta funcionalidad

```text
specs/003-infraestructura-demo/
├── spec.md               # Qué y por qué (aclaraciones, QA, entrevista y C-8)
├── plan.md               # Este archivo
├── research.md           # R-1 a R-18
├── data-model.md         # Qué se guarda, traducción, migraciones
├── contracts/
│   ├── salud.md
│   ├── fallas-base-de-datos.md
│   ├── comando-migraciones.md
│   ├── publicacion.md
│   └── ci.md
├── quickstart.md         # Comprobación de punta a punta
├── tasks.md              # /speckit-tasks (después de aprobar el plan)
└── verification-guide.md # Al cerrar cada fase
```

### 3.2 Código fuente (raíz del repositorio)

```text
.github/workflows/
├── ci.yml                    # F1 (DP-27, DP-28)
└── publicar.yml              # F6, corte 2 (DP-29)
backend/
├── app/
│   ├── almacen.py            # Nuevo: interfaz Almacen, AlmacenEnMemoria, ErrorDeAlmacen
│   ├── almacen_postgres.py   # Nuevo: AlmacenPostgres con psycopg
│   ├── migraciones.py        # Nuevo: comando y versión esperada (RF-047)
│   ├── tareas.py             # Nuevo: reintentos de avisos y consulta de vida
│   ├── cobros.py             # Cambia: el repositorio usa el almacén, métodos async, candado por cobro
│   ├── respaldo.py           # Cambia: await al registrar; transacciones del cobro
│   ├── canal.py              # Cambia solo si hace falta un await nuevo
│   ├── config.py             # Cambia: DATABASE_URL, CARPETA_WEB, CABECERA_IP_REAL
│   └── main.py               # Cambia: fallas 503, salud, IP real, web, ciclo de vida
├── tests/                    # Pruebas nuevas por pieza (§7)
└── pyproject.toml            # psycopg y psycopg-pool (DP-2)
supabase/
├── migraciones/
│   ├── 0001_esquema_inicial.sql   # El 001 del PR #97, sin begin/commit
│   └── 0002_imagen_del_qr.sql
├── datos_de_prueba.sql            # Bloques A y B del 002 del PR #97
└── consultas_de_verificacion.sql  # Bloques C a F del 002 del PR #97
infra/servidor/
├── pago-facil.service        # Unidad de systemd
├── preparar.sh               # Preparación única de la instancia
└── publicar.sh               # Publicar un commit (contrato de publicación)
infra/aws/
└── rol-publicacion.json      # Permisos del rol de OIDC (corte 2)
docs/
└── operacion-demo.md         # Guía de Hugo: AWS, presupuesto, reencendido, Supabase (RF-041, RF-050, RF-051)
web/
├── index.html                # CSP: connect-src 'self' (RF-029)
└── README.md                 # Cómo abrir la web desde el servidor local
```

**Decisión de estructura**: el código nuevo de la base de datos vive en módulos propios (`almacen*.py`, `migraciones.py`, `tareas.py`) para probar cada uno por separado; `cobros.py` conserva el modelo de la 001. Los archivos del PR #97 se mueven a `supabase/migraciones/` cuando se una el #97 (F2), y la infraestructura que no es código de Python va en `infra/`.

---

## 4. Módulos y piezas con comportamiento

| Pieza | Responsabilidad | Requisitos |
|---|---|---|
| `almacen.py` · `Almacen` (protocolo) | Operaciones asíncronas: `guardar_cobro`, `guardar_qr`, `borrar_cobro`, `cancelar`, `registrar_pago` (devuelve si el pago es nuevo; guarda el `webhook-id` en la misma transacción), `guardar_aviso`, `aviso_visto`, `cargar_por_id`, `cargar_por_codi_qr`, `consulta_de_vida`, `version_registrada` | RF-001 a RF-005, RF-007 |
| `almacen.py` · `AlmacenEnMemoria` | La misma interfaz con diccionarios. Para las pruebas de la API y para un servidor sin `DATABASE_URL` (DP-16). Un almacén nuevo sobre los mismos diccionarios simula un reinicio | RF-005, CE-005 |
| `almacen.py` · `ErrorDeAlmacen` | La única excepción que ve el resto del código cuando la base de datos no responde; lleva la operación y el nombre de la clase del error original, nunca su texto | RF-016, RF-021 |
| `almacen_postgres.py` · `AlmacenPostgres` | El SQL de data-model §3 con psycopg y un *pool* de 1 a 3 conexiones; traduce Unix ↔ `timestamptz` y `""` ↔ `null`; espera 5 s como máximo por operación; convierte cualquier error de conexión o de servidor en `ErrorDeAlmacen` | RF-001 a RF-009, RF-020, RF-022 |
| `cobros.py` · `RepositorioCobros` | Caché de escritura directa: escribe en el almacén y después cambia la memoria (DP-7); carga al pedir lo que no está (RF-005); `registrar_pago` dentro del candado del cobro (DP-8); calcula el estado con el `Reloj` (DP-11) | RF-002, RF-005 a RF-008 |
| `respaldo.py` · `ConsultaDeRespaldo` | Igual que en la 001, con `await` al registrar; pasa a pey las transacciones **del cobro** (DP-13); si el almacén falla, registra y sigue | RF-005, RF-007, RF-016 |
| `main.py` · `crear_cobro` | Guarda el cobro (si falla, 503 sin llamar a pey); llama a pey; si pey falla, borra el cobro; guarda el QR (si falla, 503 sin QR); con el corte 2, rechaza si la estructura está pendiente | RF-001, RF-012, RF-013, RF-047, RF-052 |
| `main.py` · `ver_cobro`, `eventos_cobro`, `cancelar_cobro` | Cargan del almacén si hace falta; 503 si no responde, nunca 404 por una falla | RF-004, RF-005, RF-015 |
| `main.py` · `webhook_pey` | Busca el cobro (memoria, luego almacén); registra el pago y el `webhook-id` en una transacción; si falla, 503 a pey y el aviso entra a la lista de reintentos | RF-003, RF-007, RF-014 |
| `tareas.py` · `ReintentosDeAvisos` | Lista en memoria por `webhook_id` (data-model §4); cada 15 s intenta registrar y, al lograrlo, emite por el canal | RF-014, RF-048 |
| `tareas.py` · consulta de vida | Cada 6 h, `select 1` y la línea "Consulta de vida de la base de datos: responde" (o la falla) | RF-039, CE-012 |
| `main.py` · ciclo de vida | Abre y cierra el *pool*; arranca y detiene la tarea de fondo con el `Reloj` inyectado | RF-039, RF-048 |
| `main.py` · `/salud` | Agrega `base_de_datos` (consulta con 2 s, guardada 10 s) y, en el corte 2, `estructura` | RF-023, RF-047 |
| `main.py` · `ip_del_cliente` | Con `CABECERA_IP_REAL`, la IP de `CloudFront-Viewer-Address` (sin el puerto; IPv6 sin corchetes); si no, `request.client.host` con `ProxyHeadersMiddleware` como hoy | RF-028 |
| `main.py` · web | Con `CARPETA_WEB`, monta `web/` en `/` después de las rutas del API | RF-024, RF-029 |
| `config.py` | `database_url` (`SecretStr`), `carpeta_web`, `cabecera_ip_real`; `WEB_ORIGIN` con la dirección de CloudFront en la demo | RF-020, RF-027 |
| `migraciones.py` | Comando `estado` y `aplicar` (contrato [comando-migraciones](contracts/comando-migraciones.md)); `version_esperada()` para RF-047 | RF-017 a RF-019, RF-046, RF-047, RF-049, RF-054 |
| `supabase/migraciones/0002_imagen_del_qr.sql` | Columna `qr_imagen` | RF-010, RF-018 |
| `web/index.html` | CSP `connect-src 'self'` | RF-029 |
| `.github/workflows/ci.yml` | Contrato [ci](contracts/ci.md) | RF-036 a RF-038 |
| `infra/servidor/*` | systemd con un solo proceso de uvicorn (`--workers 1`) y `EnvironmentFile`; preparación de la instancia; publicación con vuelta atrás | RF-024, RF-030, RF-044, RF-046, RF-055 |
| `.github/workflows/publicar.yml` | Contrato [publicación](contracts/publicacion.md), corte 2 | RF-042 a RF-045 |
| `docs/operacion-demo.md` | Presupuesto (primero), EC2, IP elástica, grupo de seguridad, CloudFront, secretos, publicar, reencender después del presupuesto, reactivar Supabase, copia antes de migrar, rol de OIDC | RF-031 a RF-035, RF-040, RF-041, RF-050, RF-051 |

---

## 5. Contratos

Cada contrato tiene el formato de la plantilla. Las rutas de la 001 no cambian de forma; solo se agregan respuestas de falla.

| Contrato | Archivo | Requisitos |
|---|---|---|
| `GET /salud` (amplía el de la 001) | [contracts/salud.md](contracts/salud.md) | RF-023, RF-047 |
| Respuestas 503 por falla de la base de datos en las rutas de la 001 | [contracts/fallas-base-de-datos.md](contracts/fallas-base-de-datos.md) | RF-012 a RF-016, RF-047, RF-048, RF-052 |
| Comando `python -m app.migraciones` | [contracts/comando-migraciones.md](contracts/comando-migraciones.md) | RF-017 a RF-019, RF-046, RF-049, RF-051, RF-054 |
| `publicar.sh` y `publicar.yml` | [contracts/publicacion.md](contracts/publicacion.md) | RF-024, RF-030, RF-042 a RF-046, RF-055 |
| `ci.yml` | [contracts/ci.md](contracts/ci.md) | RF-036 a RF-038 |

Los contratos de la 001 `crear-cobro.md`, `ver-cobro.md`, `cancelar-cobro.md`, `canal-avisos.md` y `aviso-pey.md` siguen valiendo; C-6 (e) y (f) les quita las menciones a "se perdió al reiniciar" y "no hace llamadas de red".

---

## 6. Modelo de datos

El detalle va en [data-model.md](data-model.md). En resumen:

- El modelo de la 001 no cambia; se guarda en las tablas del PR #97 más la columna `qr_imagen` (migración 0002).
- Todas las horas se escriben con el `Reloj` del servidor, y el estado se calcula en Python (RF-006, QA-11).
- El comando de migraciones crea `cambios_de_estructura` y `entorno_de_la_base`, con RLS y sin acceso para `anon` ni `authenticated`.
- La lista de reintentos de avisos, los límites por IP, los canales y `ultima_consulta_pey` viven solo en memoria.

---

## 7. Estrategia de pruebas

- **Pruebas primero**: cada tarea de implementación tiene antes su prueba, que se ve fallar y después pasa.
- **Pruebas automáticas**: nunca llaman al pey real ni a la base de datos real. La API se prueba con el almacén en memoria y con `AlmacenQueFalla` (un almacén cuyas operaciones se pueden hacer fallar una por una). El SQL se prueba contra un PostgreSQL desechable (research R-12).
- **"Reinicio" en las pruebas**: se crea una app nueva con un almacén nuevo sobre los mismos datos (memoria compartida o la misma base desechable) y se comprueba que todo sigue igual.
- **Pruebas reales**: solo con $0.01 y con autorización de Hugo (F5).
- **Nombres de las pruebas** en español, como la spec que comprueban.
- **Las 109 pruebas de hoy** se mantienen; se ajustan solo donde una función pasa a ser asíncrona.

| Requisito | Prueba | Tipo |
|---|---|---|
| RF-001, RF-010 | `test_un_cobro_creado_queda_guardado_con_su_imagen_del_qr` | integración |
| RF-002 | `test_el_pago_se_guarda_antes_de_emitirse_por_el_canal` | integración |
| RF-003 | `test_el_webhook_id_procesado_queda_guardado` | integración |
| RF-004 | `test_la_cancelacion_queda_guardada_con_su_hora` | integración |
| RF-005 | `test_tras_un_reinicio_se_puede_ver_cancelar_y_escuchar_un_cobro_guardado`; `test_tras_un_reinicio_el_aviso_de_pey_registra_el_pago`; `test_tras_un_reinicio_la_consulta_de_respaldo_encuentra_el_pago` | integración |
| RF-006 | `test_el_estado_tras_un_reinicio_se_calcula_con_el_reloj_del_servidor`; `test_las_horas_guardadas_son_las_del_reloj_del_servidor` (almacén de PostgreSQL) | integración |
| RF-007, CE-005 | `test_un_aviso_reenviado_no_duplica_el_pago`; `test_el_aviso_y_la_consulta_a_la_vez_registran_un_solo_pago`; `test_el_mismo_pago_antes_y_despues_de_un_reinicio_se_registra_una_vez`; `test_on_conflict_no_duplica_la_transaccion` (PostgreSQL) | integración |
| RF-008 | `test_tras_un_reinicio_el_siguiente_pago_es_el_numero_3`; `test_dos_pagos_distintos_a_la_vez_quedan_con_numeros_1_y_2` | integración |
| RF-009 | `test_los_datos_de_quien_paga_no_se_guardan_ni_se_registran` (aviso con `metadata` completa) | integración |
| RF-011 | `test_sin_imagen_de_pey_el_cobro_guardado_vuelve_sin_imagen` | integración |
| RF-012 | `test_si_la_base_no_responde_al_crear_no_se_llama_a_pey` | integración |
| RF-052 | `test_si_pey_falla_el_cobro_guardado_se_borra` | integración |
| RF-013 | `test_si_la_base_falla_al_guardar_el_qr_no_se_devuelve_el_qr` | integración |
| RF-014 | `test_si_la_base_falla_con_un_aviso_se_responde_503_y_no_se_emite` | integración |
| RF-048 | `test_el_aviso_pendiente_se_registra_y_se_emite_cuando_la_base_vuelve` (con `RelojFalso`, avanza 15 s); `test_un_aviso_reenviado_mientras_esta_pendiente_no_se_duplica` | integración |
| RF-015 | `test_si_la_base_no_responde_al_ver_un_cobro_se_responde_503_y_no_404` | integración |
| RF-016, RF-021 | `test_cada_falla_de_la_base_deja_registro_sin_datos_de_conexion` | integración |
| RF-017, RF-018, CE-007 | `test_aplicar_en_una_base_vacia_crea_el_esquema_y_la_imagen_del_qr`; trabajo `base-de-datos` del CI (dos veces seguidas) | integración (PostgreSQL) |
| RF-019 | `test_aplicar_dos_veces_no_cambia_nada`; `test_una_migracion_que_falla_no_deja_nada_a_medias` | integración (PostgreSQL) |
| Historia 6, esc. 3 | `test_una_base_con_el_esquema_sin_registro_pide_ya_aplicada`; `test_ya_aplicada_solo_agrega_lo_que_falta` | integración (PostgreSQL) |
| RF-049, RF-054 | `test_los_datos_de_prueba_se_rechazan_en_una_base_demo`; `test_la_marca_de_entorno_no_se_puede_cambiar` | integración (PostgreSQL) |
| RF-046 | Revisión: `publicar.sh` y `publicar.yml` no llaman a `app.migraciones` | manual (QA) |
| RF-047 | `test_con_la_estructura_pendiente_la_salud_lo_dice_y_se_rechazan_cobros` | integración |
| RF-051 | Paso de la guía revisado en F4 | manual |
| RF-020 | `test_database_url_se_lee_de_la_configuracion` | unitaria |
| RF-022 | `test_anon_y_authenticated_no_pueden_leer_ni_escribir` (PostgreSQL con los roles creados) | integración |
| RF-023 | `test_la_salud_dice_si_la_base_responde_sin_mostrar_valores` (tres casos) | integración |
| RF-039, CE-012 | `test_la_consulta_de_vida_corre_cada_6_horas` (`RelojFalso`); 8 días en la demo (F7) | integración y manual |
| RF-024 | Quickstart §6.3 | manual |
| RF-025 | Quickstart §7.1 | manual |
| RF-026, CE-004 | Quickstart §6.5 (20 minutos) | manual |
| RF-027 | `test_cors_solo_acepta_el_origen_configurado` (ya existe en la 001; se repite con la dirección real) y quickstart §6.6 | integración y manual |
| RF-028 | `test_con_cabecera_ip_real_el_limite_usa_la_ip_de_cloudfront`; `test_sin_cabecera_ip_real_se_ignora_cloudfront_viewer_address`; quickstart §6.7 | integración y manual |
| RF-029 | Prueba de la web: la CSP tiene `connect-src 'self'` y nada más en `connect-src` | integración (web) |
| RF-030 | Quickstart §8 (misma dirección después de publicar) y §7.5 | manual |
| RF-055, CE-014 | Quickstart §7.6 | manual |
| RF-031 a RF-034, CE-008 | Quickstart §6.1 y revisión de la configuración del presupuesto | manual |
| RF-035, CE-009 | Research R-6, recalculado en F4 | manual |
| RF-040, RF-041, RF-050 | Revisión de `docs/operacion-demo.md` y de los permisos del rol de OIDC | manual |
| RF-036, RF-037, CE-006 | Quickstart §2 | manual |
| RF-038, CE-011 | El CI corre sin secretos; revisión del flujo | manual |
| RF-042 a RF-045, CE-013 | Quickstart §8 | manual |
| RF-053 | Revisión de `backend/.env` local (otra llave y su aviso) sin leer valores | manual |
| CE-001, CE-002, CE-003 | Quickstart §7 y §6.4 | manual (dinero real) |
| CE-010 | Prueba de registros (RF-016) y `git grep` de llaves en el repositorio | integración y manual |

---

## 8. Plan de implementación

| Fase | Fechas | Quién | Qué | Depende de |
|---|---|---|---|---|
| F1 CI | 18 nov | Grok (revisa Claude) | `ci.yml` con los trabajos `servidor` y `web`, en su propio PR desde `main` (DP-28). Juan lo hace obligatorio en `main` | Plan y tasks aprobados |
| F2 Migraciones | 18–19 nov | Grok (revisa Claude) | Mover los archivos del PR #97; `0002`; `migraciones.py` con sus pruebas; trabajo `base-de-datos` del CI. Hugo aplica en local con `--entorno local --datos-de-prueba` | F1; PR #97 unido |
| F3 Guardar | 19–20 nov | Grok (revisa Claude) | `almacen.py`, `almacen_postgres.py`, `RepositorioCobros` asíncrono con candado, fallas 503, lista de reintentos, consulta de vida, `/salud`, configuración | F2 |
| F4 Demo pública | 20–21 nov | Código, Grok (revisa Claude); AWS, Hugo | IP real, web desde el servidor y CSP, `infra/servidor/*`, `docs/operacion-demo.md`. Hugo: tipo de cuenta (R-7), **presupuesto primero**, instancia, CloudFront, secretos y primera publicación. **Prueba de 20 minutos al principio** (R-3). Hugo marca la base de la demo con `--entorno demo --ya-aplicada 0001` y aplica 0002, después de exportar una copia y de limpiar los datos de prueba que dejó el PR #97 (H-12) | F3; PR #72 unido (para publicar la web desde `main`) |
| F5 Pago real | 21–22 nov | Hugo, con los dos celulares | Aviso de pey dado de alta; CE-001, CE-002, CE-003 y CE-014; reenvío del aviso. Cierra #27 y #64 | F4 |
| **Fin del corte 1** | **22 nov** | | | |
| F6 Publicación automática | 24–27 nov | Grok (revisa Claude); rol de OIDC, Hugo; variable del repositorio, Juan | `publicar.yml`, `infra/aws/rol-publicacion.json` y su guía | F5 |
| F7 Estructura pendiente | 24–26 nov | Grok (revisa Claude) | `version_esperada`, `estructura` en la salud, rechazo de cobros (RF-047). CE-012 empieza a contar con la primera publicación de F4 y se revisa el 29 nov o después, sin bloquear | F5 |
| FN Cierre | 28–29 nov | Hugo y Claude | C-6 y C-7 (si Hugo los aprueba), notas de implementación de #90, #19, #34, #65, #35 y #94, revisión de seguridad (constitución, flujo 6), `verification-guide.md` completo | F6, F7 |
| **Fin del corte 2** | **29 nov** | | | |

---

## 9. Decisiones

### 9.1 Decisiones del plan

| # | Decisión | Por qué | Alternativas descartadas |
|---|---|---|---|
| DP-6 | Interfaz `Almacen` con dos implementaciones: memoria y PostgreSQL | Las pruebas de la API no necesitan PostgreSQL (principio V) y se puede simular un reinicio | Llamar a psycopg desde `main.py`: no se puede probar sin base de datos |
| DP-7 | La memoria es una caché de escritura directa: primero la base de datos, después la memoria y el canal (R-10) | Un solo proceso: la memoria nunca queda desactualizada; el canal y la consulta de respaldo no cambian | Leer siempre de la base de datos: una consulta cada 3 a 5 s por cada pantalla abierta |
| DP-8 | Candado por cobro (`asyncio.Lock`) al registrar pagos; `unique (cobro_id, numero)` como red | El aviso y la consulta no calculan el mismo número a la vez (RF-008) | Reintentar al chocar con `unique`: más código para el mismo resultado |
| DP-9 | El pago y su `webhook-id` se guardan en la misma transacción | Si falla una, falla la otra: un reintento de pey se procesa completo (DP-10 de la 001) | Dos escrituras separadas: el `webhook-id` podría quedar sin su pago |
| DP-10 | Todas las horas se escriben con el `Reloj` del servidor; nunca con `default now()` | RF-006 y las pruebas con `RelojFalso` | Dejar que la base de datos ponga `creado_en`: dos relojes |
| DP-11 | El estado se calcula en Python; la columna `estado` de la vista no se usa (QA-11) | Reloj controlado en las pruebas y la ventana de escucha, que la vista no conoce | Leer la vista |
| DP-12 | `ultima_consulta_pey` solo en memoria | Escribirla sería una escritura cada 3 a 5 s por cobro mirado; tras un reinicio, empezar de cero solo adelanta una consulta | Guardarla |
| DP-13 | La consulta de respaldo pasa a pey las transacciones del cobro, no un conjunto global | Tras un reinicio no hay conjunto global en memoria; las transacciones de un QR solo pueden ser de ese cobro | Cargar todas las transacciones al arrancar |
| DP-14 | Una tarea de fondo en el ciclo de vida, con el `Reloj` inyectado: reintentos cada 15 s y consulta de vida cada 6 h | RF-048 y RF-039 piden trabajo aunque nadie mire (excepción a DP-5 de la 001, §12) | Un cron externo: otra pieza en la instancia |
| DP-15 | Los registros de fallas llevan solo el nombre de la clase del error | El texto de psycopg puede traer servidor y usuario (RF-021) | Registrar el error completo |
| DP-16 | Sin `DATABASE_URL`, el servidor usa la memoria, avisa en el registro y la salud dice `"sin configurar"`; `publicar.sh` exige `"responde"` | Juan y Miguel pueden correr el servidor sin Supabase; la demo no puede quedar en memoria sin que se note | Negarse a arrancar sin base de datos: obliga a todos a tener un proyecto |
| DP-17 | Los archivos de migración no llevan `begin`/`commit`; el comando corre cada uno en una transacción junto con su registro | Una migración queda completa o no queda (RF-019) | Dejar el `begin`/`commit` del PR #97: el registro quedaría fuera de la transacción |
| DP-18 | Marca de entorno (`local`/`demo`) en la base, puesta la primera vez; los datos de prueba solo en `local` | RF-054 con una comprobación en la base, no en la memoria de quien corre el comando | Confiar en una variable de entorno de la computadora |
| DP-19 | La base de la demo (creada a mano con el PR #97) se registra con `--ya-aplicada 0001` después de revisarla | Historia 6, escenario 3, sin que el comando adivine | Detectarlo solo: un esquema parecido pero distinto pasaría por bueno |
| DP-20 | La migración 0002 no recrea la vista `cobros_con_estado` | El servidor no la usa (DP-11); `c.*` no verá `qr_imagen`, y el historial (#38) la recrea si la necesita | Recrearla ahora: trabajo que nadie usa |
| DP-21 | El servidor entrega la web en el mismo origen; CSP `connect-src 'self'` (R-18) | RF-027, RF-029 y una sola publicación | S3 aparte |
| DP-22 | IP real con `CloudFront-Viewer-Address` cuando `CABECERA_IP_REAL` está puesta; el grupo de seguridad solo deja entrar a CloudFront (R-4) | `X-Forwarded-For` con todas las IP en confianza es falsificable (RF-028) | `PROXIES_CONFIABLES=*` |
| DP-23 | CloudFront: un comportamiento sin caché, todos los métodos, política de origen `AllViewerAndCloudFrontHeaders-2022-06`, origen HTTP al puerto 8000, tiempo de respuesta de 30 s y sin tiempo de respuesta completa (R-3) | Canal de 20 minutos y avisos de pey sin cambios | Caché para la web: obliga a invalidar en cada publicación |
| DP-24 | EC2 `t4g.micro` en la región del proyecto de Supabase de la demo, con IP elástica, IMDSv2, Session Manager (sin SSH ni puerto 22) y rol de instancia `AmazonSSMManagedInstanceCore` | Costo (R-6), latencia (R-11), misma dirección de origen tras un apagado (RF-030) | `t4g.small`: no hace falta para un proceso; se sube si la memoria no alcanza |
| DP-25 | Publicación por carpetas de versión con vuelta atrás si la salud no responde (R-15) | RF-044 y RF-055 con un solo script para los dos cortes | `git pull` en la misma carpeta |
| DP-26 | Secretos del servidor en `/etc/pago-facil/entorno` (de root, `0640`), cargado por systemd (R-17) | Principio III, sin otra pieza | Parameter Store |
| DP-27 | CI con tres trabajos, `pull_request`, `permissions: contents: read` y sin secretos; el trabajo `web` solo si existe `web/tests/` (R-13) | RF-036 a RF-038 | `pull_request_target`: expone secretos a los forks |
| DP-28 | F1 se entrega en su propio PR desde `main` (rama `feature/35-ci`) | Juan quiere ver las pruebas del #72 en GitHub antes de unirlo; esta rama sale de la del #72 | Entregar el CI junto con el resto de la spec: llega después del #72 |
| DP-29 | Publicación automática con OIDC y un rol que solo puede consultar la instancia y mandar el comando; el ARN como variable del repositorio (R-16) | RF-043 y RF-045 | Llaves de IAM como secretos de GitHub |
| DP-30 | RF-047: versión esperada = mayor versión de los archivos; se compara al arrancar y cada 60 s | Sin llamadas a la base de datos en cada petición | Comparar en cada cobro |
| DP-31 | La salud consulta la base de datos con `select 1` y 2 s de espera, y guarda el resultado 10 s | Rápida y sin cargar la base de datos aunque la pidan muchas veces | Consultar en cada petición |
| DP-32 | Mensajes de falla para el dueño, como en el [contrato](contracts/fallas-base-de-datos.md) | Principio VII; la web ya los muestra o reconecta | Mensajes técnicos |

### 9.2 Decisiones de Hugo

Cada una tiene su comparativa en research.md (principio IX); se copian a las notas de implementación en FN.

| # | Duda | Recomendación | Decisión |
|---|---|---|---|
| DP-1 | ¿Qué servicio de AWS? (R-1) | **EC2 `t4g.micro` + CloudFront**: único que cumple el canal de 20 min, el HTTPS sin dominio y el apagado nativo por presupuesto; unos 25 dólares | **EC2 + CloudFront** (Hugo, 2026-11-17), como se recomienda |
| DP-2 | ¿Qué librería de PostgreSQL? (R-8) | **psycopg 3**: una sola librería para el servidor y para las migraciones, SQL a mano, funciona con el *pooler* | **psycopg 3** (Hugo, 2026-11-17), como se recomienda |
| DP-3 | ¿Qué herramienta de migraciones? (R-9) | **Comando propio** (`python -m app.migraciones`): sin herramientas nuevas, misma tabla para RF-047, marca de entorno para RF-054 | **Comando propio** (Hugo, 2026-11-17), como se recomienda |
| DP-4 | ¿Cómo se crea la infraestructura? (R-14) | **Guía paso a paso en la consola** (`docs/operacion-demo.md`): cabe en el corte 1; CloudFormation queda para después | **Guía en la consola** (Hugo, 2026-11-17), como se recomienda |
| DP-5 | ¿Quién implementa cada fase y quién revisa? | **Grok implementa F1 a F3, F4 (código), F6 y F7; Claude revisa cada fase; Hugo hace todo lo de AWS, el pago real y aprueba cada cierre con la guía de verificación**; Juan revisa los PR y configura `main` | **Grok implementa, Claude revisa** (Hugo, 2026-11-17), como se recomienda |

### 9.3 Revisión QA del plan

Se llena con `/qa-spec 003 plan`. Según C-8, la QA no aprueba el plan hasta que los PR #72 y #96 estén unidos; si al unirse cambian algo que el plan usa, el ajuste sale como hallazgo QP-n.

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|

**Bloques de la pasada:** pendiente.

---

## 10. Seguridad

- **Secretos**: `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` y `DATABASE_URL` solo en `backend/.env` (local) y en `/etc/pago-facil/entorno` (demo, DP-26). `DATABASE_URL` es `SecretStr` y nunca se imprime (RF-021). Ninguna llave de AWS en GitHub (DP-29). Se comprueba con `git grep` y con la prueba de registros (CE-010).
- **Base de datos**: RLS encendido y sin acceso para `anon` ni `authenticated` en todas las tablas, también en las del comando (RF-022). Solo el servidor tiene la cadena de conexión. Prueba con los roles creados en el PostgreSQL desechable.
- **Firma de webhooks**: sin cambios; un aviso sin firma válida se rechaza antes de tocar la base de datos.
- **Entradas**: sin cambios en la validación de la 001. Todo el SQL usa parámetros de psycopg, nunca texto pegado.
- **Abuso de la demo pública**: límites por IP real (DP-22); CORS solo con la dirección de CloudFront (RF-027); el origen solo acepta conexiones de CloudFront; sin SSH (DP-24).
- **Datos de quien paga**: no se leen ni se guardan (RF-009).
- **Instancia**: IMDSv2 obligatorio, actualizaciones automáticas de seguridad de Ubuntu (`unattended-upgrades`), servicio con un usuario sin privilegios.

---

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| CloudFront corta el canal antes de 20 min (R-3) | Incumple RF-026 y CE-004 | Prueba de 20 minutos al principio de F4; si falla, cambiar a la opción B de R-1 antes de seguir |
| La cuenta de AWS es del plan gratuito y bloquea algo, o vence antes del 31 ene (R-7) | La demo no se puede crear o se apaga | Hugo confirma el plan y la fecha antes de F4 |
| Las 6 pruebas de WebKit fallan en Linux (revisión del PR #72) | El trabajo `web` del CI sale en rojo | Se resuelven en el PR #72 (otra sesión); si no, se decide ahí `skip` o `xfail` con su TK |
| El PR #97 o el #72 tardan en unirse | F2 o F4 no pueden empezar | F1 no depende de ellos; F3 se puede escribir sobre una copia del esquema mientras tanto, y se ajusta al unirse |
| La base de la demo tiene los datos de prueba del PR #97 (H-12) | Incumple RF-054 | En F4, antes de marcarla `demo`, Hugo corre los borrados del bloque F (o se usa ese proyecto como el local y se crea otro para la demo) |
| Falla el borrado de un cobro cuando pey no creó su QR (RF-052) | Queda un cobro sin QR en la base de datos | Se registra (RF-016); el historial (#38) puede filtrar `codi_qr_id is null`. Limitación aceptada |
| Supabase pausa el proyecto aunque haya consulta de vida | La demo no guarda | Salud `"no responde"`, guía de reactivación (RF-050) |
| 5 días para el corte 1 con piezas nuevas | El corte 1 no llega | Orden por lo que más desbloquea (§1.2 de la spec); el corte 2 absorbe lo que no llegue |
| Una escritura en la base de datos hace más lento el aviso de pey | El aviso tarda más de 1 s (CE-010 de la 001) | Instancia en la región de Supabase (DP-24); se mide en F5 |

---

## 12. Seguimiento de complejidad (Complexity Tracking)

| Excepción | Por qué hace falta | Alternativa más simple descartada y por qué |
|---|---|---|
| Una tarea de fondo en el servidor (DP-14), cuando el plan de la 001 (DP-5) evitó las tareas de fondo | RF-048 exige reintentar avisos aunque nadie tenga la pantalla abierta, y RF-039 exige consultar la base de datos aunque nadie cree cobros | Reintentar solo cuando alguien abre el cobro: un pago podría no registrarse nunca (principio VIII). Un cron en la instancia: otra pieza fuera de las pruebas |

---

## 13. Aprobación

- [x] Decisiones DP-1 a DP-5 tomadas por Hugo (2026-11-17).
- [ ] PR #72 y PR #96 unidos a `main` (C-8).
- [ ] Plan revisado con `/qa-spec 003 plan` y todos los hallazgos QP decididos.
- [ ] Aprobado por Hugo el [AAAA-MM-DD]. Aprobar no autoriza a empezar `tasks.md`: se espera a que Hugo lo pida.

---

## 14. Registro de implementación

| # | Fecha | Qué | Por qué | Afecta |
|---|---|---|---|---|
