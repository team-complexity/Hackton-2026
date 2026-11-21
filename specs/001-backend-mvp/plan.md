# Plan: Backend del MVP: cobrar con CoDi y saber que me pagaron

- **Rama**: `feature/18-backend-mvp`
- **Fecha**: 2026-11-14
- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-14
- **Estado del plan**: `Aprobado`. Hugo lo aprobó el 2026-11-14, después de decidir DP-1 a DP-3 y la QA (QP-1 a QP-7, aplicadas). Ajustado el 2026-11-14 por el cambio C-1 de la spec y la QA de tasks (QT-3, QT-4, QT-6; §14).
- **Entrada**: la spec de `specs/001-backend-mvp/spec.md`

> **Notas para los comandos de spec-kit.**
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
> - Los títulos marcados entre paréntesis (*Technical Context*, *Constitution Check*, *Project Structure*, *Complexity Tracking*) son las secciones que espera `/speckit-plan`.
> - El plan se escribe en español.
> - El plan dice **CÓMO**. Cada pieza cita los RF de la spec que cumple.

---

## 0. Resumen

El backend crea cobros CoDi con pey, registra cada pago una sola vez (por el aviso firmado de pey o por una consulta directa a pey) y lo avisa a la pantalla del negocio por Server-Sent Events.

El enfoque parte del prototipo que ya funcionó contra pey (DP-1) y lo reorganiza con pruebas primero en torno a tres piezas nuevas:

- un **reloj inyectable**, para probar vencimientos, ventanas y límites sin esperar;
- un **modelo de cobro con lista de pagos**, para el QR reutilizado y el monto distinto;
- un **canal de avisos** que, mientras está abierto, también le pregunta a pey por su cuenta, para que el pago se avise aunque el aviso de pey falle.

Se entrega en dos cortes: **M0**, para el kickoff del 15 nov a la 1:00 PM, y **corte 2**, antes del 21 nov (§1.2 de la spec).

### 0.1 Hechos del código y de las fuentes

| # | Hecho | Evidencia |
|---|---|---|
| H-1 | El cliente de pey ya creó un QR real con la llave de Hugo (codiQrId `35a61c5161`, 14 nov) | `backend/app/pey.py:71-95`, `backend/scripts/probar_pey.py` |
| H-2 | Las 15 pruebas del prototipo pasan con un pey simulado (`httpx.MockTransport`) | `uv run --directory backend pytest -q` → `15 passed` |
| H-3 | El cobro guarda un solo pago y rechaza el segundo | `backend/app/cobros.py:97` |
| H-4 | El estado se calcula con `time.time()` directo, sin reloj inyectable | `backend/app/cobros.py:34`, `backend/app/eventos.py:37` |
| H-5 | El canal se cierra con el primer pago y al vencer | `backend/app/main.py:172-179` |
| H-6 | La consulta de respaldo solo corre en *pendiente*, se detiene en la primera transacción y no pide más páginas | `backend/app/main.py:96-104,148`, `backend/app/pey.py:97-100` |
| H-7 | El `webhook-id` se marca como visto antes de procesar el aviso | `backend/app/main.py:210` |
| H-8 | El límite por IP usa la IP de la conexión | `backend/app/main.py:118` |
| H-9 | Los errores de validación salen en inglés (formato de pydantic) | Comportamiento de FastAPI 0.163; sin manejador propio en `main.py` |
| H-10 | No hay configuración de registros: los INFO no se ven | `backend/app/main.py:21` |
| H-11 | pey: 20 transacciones por página con `nextToken`; estados `PENDING` y `PAID`; `amountBreakdown` con `base`, `tip` y `fee` | `openapi.json`, `GET /transaction/codi/qr/{id}` |
| H-12 | pey: el aviso trae `amount`, `codiQrId`, `transactionId` (ULID) y `datePaid`, sin desglose | Página "CoDi QR Payment Received" de docs.pey.mx |
| H-13 | uvicorn 0.54 trae `ProxyHeadersMiddleware(app, trusted_hosts)` | `backend/uv.lock`, inspección del paquete instalado |
| H-14 | El cliente de pey espera hasta 20 s por respuesta | `backend/app/pey.py:31` |
| H-15 | pey advierte que `generateImage: true` hace más lenta la creación del QR | `openapi.json`, `POST /codi/qr` |

---

## 1. Contexto técnico (Technical Context)

- **Lenguaje y versión**: Python 3.11+ (el entorno local usa 3.14).
- **Dependencias principales**: FastAPI 0.163, uvicorn 0.54, httpx 0.28, pydantic-settings 2.16, standardwebhooks 1.1. **No se agrega ninguna dependencia de producción.**
- **Dependencias de desarrollo**: pytest 9.2, ruff 0.17 y **pytest-asyncio** (DP-2), que se agrega en F1 con `uv add --dev`, fijado a una versión publicada hace al menos dos semanas.
- **Almacenamiento**: en memoria, en un solo proceso (limitación aceptada hasta #23).
- **Pruebas**: pytest con pey simulado (`httpx.MockTransport`) y `RelojFalso`. `TestClient` para las rutas; pytest-asyncio para el canal de avisos.
- **Plataforma de destino**: un servidor con HTTPS en Render o Railway (#65, Altairtm), detrás del proxy del hosting.
- **Tipo de proyecto**: servicio web (API JSON y SSE) que consume la PWA de #64.
- **Metas de rendimiento**:
  - QR en menos de 3 s (CE-002);
  - aviso por el canal en menos de 2 s después del aviso de pey (CE-003);
  - respuesta a pey en menos de 1 s (CE-010);
  - pago avisado a más tardar 5 s después de que pey lo reporta, sin aviso de pey (CE-008);
  - *vencido* en menos de 15 s (RF-030).
  - Tiempos de espera de pey (QP-1): 4 s para la consulta de respaldo y 10 s para crear el QR.
- **Restricciones**: un solo proceso (los límites y el canal viven en memoria); la llave de pey y el secreto del aviso solo en el backend; nada de pey real en las pruebas automáticas.
- **Escala**: un negocio de demo, decenas de cobros por día y algunos jueces a la vez. Como mucho, 10 cobros por minuto y 10 canales por IP.

No quedan `[NECESITA ACLARACIÓN]`: las tres decisiones abiertas son de Hugo (§9.2), no de información.

---

## 2. Verificación de la constitución (Constitution Check)

*Revisada antes de la Fase 0 y otra vez después del diseño (Fase 1), el 2026-11-14.*

| Principio de la constitución | Cómo lo cumple este plan | Estado |
|---|---|---|
| I. El pago se confirma en el servidor | Solo el aviso con firma válida o la consulta del backend a pey registran pagos ([aviso-pey](contracts/aviso-pey.md), [ver-cobro](contracts/ver-cobro.md)). Ningún endpoint del navegador marca pagos | Cumple |
| II. Una orden nunca se ejecuta dos veces | Conjunto global de `transaccion_id` vistos y `webhook-id` como primera barrera, marcado después de procesar (R-8). El evento `pago` sale de una sola función de registro | Cumple |
| III. Los secretos nunca salen del backend | `SecretStr` en la configuración; `/salud` solo da booleanos; prueba que busca la llave y el secreto falsos en respuestas y registros (CE-009) | Cumple |
| IV. Spec primero y alcance anclado | Spec aprobada; cada pieza cita sus RF; los dos cortes vienen de QA-1 | Cumple |
| V. Pruebas primero, en todo | Cada tarea tiene su prueba antes; `RelojFalso` y pey simulado; nombres en español (§7) | Cumple |
| VI. CoDi real, reacción real | El cierre del corte M0 incluye el pago real de $0.01 con autorización de Hugo (quickstart, paso 4) | Cumple (depende de CoDi activo el 15 nov) |
| VII. Pensado para el mostrador | Todos los errores son `{"detail": "<mensaje en español para el dueño>"}`, incluidos los de validación (R-7). La interfaz es de #64 | Cumple |
| VIII. Un pago no prueba identidad ni entrega | Pagos tardíos, montos distintos, fallas de pey y devoluciones definidos en la spec §4; cada pago se registra y se avisa desde el corte M0 (C-1) | Cumple |
| IX. Lo más simple que gane la demo | Sin dependencias de producción nuevas; consulta a pey dentro del canal, sin tareas de fondo. La única herramienta nueva (pytest-asyncio, solo de desarrollo) pasó por comparativa y la eligió Hugo (DP-2, R-3) | Cumple |
| X. Si no se ve, no existe | Registro `pago_facil` configurado en INFO con id del cobro y `requestId` (R-9); `/salud` | Cumple |

No hay excepciones, así que §12 queda vacío.

---

## 3. Estructura del proyecto (Project Structure)

### 3.1 Documentación de esta funcionalidad

```text
specs/001-backend-mvp/
├── spec.md               # Qué y por qué (entrevista y QA incluidas)
├── plan.md               # Este archivo
├── research.md           # Fase 0: R-1 a R-12
├── data-model.md         # Fase 1: cobro, pago, estados y límites
├── contracts/            # Fase 1: crear-cobro, ver-cobro, cancelar-cobro, canal-avisos, aviso-pey, salud
├── quickstart.md         # Fase 1: comprobación de punta a punta
├── tasks.md              # /speckit-tasks
├── verification-guide.md # Al cerrar cada fase
└── checklists/requirements.md
```

### 3.2 Código fuente

```text
backend/
├── app/
│   ├── config.py      # (cambia) + proxies_confiables, gracia_segundos, canales_por_ip
│   ├── reloj.py       # (nuevo) Reloj y RelojFalso
│   ├── pey.py         # (cambia) consulta paginada, solo PAID, PagoPey con monto_base
│   ├── cobros.py      # (cambia) Cobro con lista de pagos, estados con reloj, RepositorioCobros
│   ├── eventos.py     # (cambia) Difusor, LimitePorIp con reloj, LimiteDeCanales (nuevo)
│   ├── respaldo.py    # (nuevo, QP-7) ConsultaDeRespaldo: consulta a pey, registrar y avisar
│   ├── canal.py       # (nuevo) generador del canal de avisos con consulta automática
│   └── main.py        # (cambia) rutas, errores en español, proxy, registros, cancelar (C2)
├── scripts/probar_pey.py   # sin cambios
└── tests/
    ├── conftest.py              # (nuevo) PeySimulado, RelojFalso, firmar_aviso, fixtures
    ├── test_crear_cobro.py      # (nuevo; recoge pruebas de test_api.py)
    ├── test_aviso_pey.py        # (nuevo)
    ├── test_respaldo.py         # (nuevo)
    ├── test_canal.py            # (nuevo, con pytest-asyncio)
    ├── test_proteccion.py       # (nuevo)
    ├── test_salud_y_registros.py # (nuevo)
    ├── test_modelo.py           # (nuevo) reloj, cobro, pagos y estados
    ├── test_cancelar_cobro.py   # (nuevo, corte 2) cancelación
    └── test_api.py              # (se reparte entre los anteriores y se borra con rm)
```

**Decisión de estructura**: se mantienen los módulos del prototipo y se agregan tres: `reloj.py` y `canal.py`, para separar las piezas que dependen del tiempo, y `respaldo.py`, para que el canal y la ruta de ver cobro compartan la consulta a pey y se puedan probar sin levantar la app (QP-7). Las pruebas se reparten por historia, para que cada fase de `tasks.md` toque sus propios archivos y las tareas `[P]` no choquen.

---

## 4. Módulos y piezas con comportamiento

| Pieza | Responsabilidad | Requisitos |
|---|---|---|
| `reloj.py` · `Reloj`, `RelojFalso` | `ahora()` en segundos Unix y `dormir(s)`. El falso avanza a mano y su `dormir` adelanta el tiempo sin esperar | Principio V; RF-021, RF-025, RF-030, RF-034, RF-040 |
| `config.py` · `Configuracion` | Variables de entorno; nuevas: `PROXIES_CONFIABLES` (por defecto `127.0.0.1`), `GRACIA_SEGUNDOS` (0 en M0, 600 en C2), `CANALES_POR_IP` (10) | RF-002, RF-022, RF-034, RF-041 |
| `pey.py` · `ClientePey.crear_qr` | `POST /codi/qr`: `amount` (0 si es monto libre), `concept`, `expiration: 600`, `numRef`, `generateImage: true` (QP-3: se mide en F3), `metadata.cobroId`. Espera como máximo 10 s (QP-1); si se pasa, es un error de conexión | RF-001, RF-003, RF-006, RF-007, CE-002 |
| `pey.py` · `ClientePey.pagos_del_qr` | `GET /transaction/codi/qr/{id}` siguiendo `nextToken` solo mientras la página traiga transacciones que no están en el conjunto de vistas (QP-2); devuelve solo `PAID` como `PagoPey(id, monto, monto_base, pagado_en)`. Espera como máximo 4 s por petición (QP-1) | RF-014, RF-015, RF-025, R-6 |
| `pey.py` · `ErrorPey` | Distingue sin llave, sin conexión, 401/403, 503 y otros, con `requestId` | RF-009, RF-010, RF-039 |
| `cobros.py` · `Cobro`, `Pago` | Datos del cobro, `estado(ahora)`, `en_ventana(ahora)`, totales y `publico()` según el [objeto cobro](contracts/crear-cobro.md#objeto-cobro) | RF-008, RF-017, RF-021, RF-022, data-model §1–3 |
| `cobros.py` · `RepositorioCobros.registrar_pago` | Única puerta para agregar pagos: deduplica por transacción, numera cada pago nuevo (C-1), calcula `monto_distinto` y devuelve el pago nuevo o nada | RF-014, RF-015, RF-016, RF-017, RF-018, RF-019, RF-020 |
| `cobros.py` · `RepositorioCobros.cancelar` | Solo desde *pendiente* (C2) | RF-023, RF-024 |
| `eventos.py` · `Difusor` | Colas por cobro; `publicar(cobro_id, evento, datos)` | RF-029, RF-030 |
| `eventos.py` · `LimitePorIp` | 10 cobros por minuto por IP del cliente, ventana deslizante con `Reloj` | RF-034 |
| `eventos.py` · `LimiteDeCanales` | Cuenta canales abiertos por IP; `ocupar` / `liberar` | RF-041 |
| `canal.py` · `flujo_de_avisos` | Generador asíncrono del [ciclo del servidor](contracts/canal-avisos.md#ciclo-del-servidor): `estado`, `pago`, `vencido`, `cancelado`, `fin`, señal de vida y consulta automática cada 5 s | RF-028 a RF-033, RF-040, RF-043 |
| `respaldo.py` · `ConsultaDeRespaldo` | Recibe cliente de pey, repositorio, difusor y reloj. `consultar(cobro, intervalo_minimo)`: respeta el intervalo por cobro (3 s al ver, 5 s desde el canal), tolera fallas y tiempos agotados de pey (RF-027), registra con `registrar_pago` y publica `pago`. `registrar_y_avisar(...)`: la misma puerta para el aviso de pey. `main.py` y `canal.py` la reciben ya creada (QP-7) | RF-025, RF-026, RF-027, RF-029, RF-040 |
| `main.py` · rutas | Las seis interfaces de §5 | Ver contratos |
| `main.py` · manejador de validación | Convierte `RequestValidationError` en `{"detail": "<mensaje en español>"}` | RF-004, RF-042, R-7 |
| `main.py` · `ProxyHeadersMiddleware` | IP real del cliente con `PROXIES_CONFIABLES` | RF-034, RF-041, R-5 |
| `main.py` · registros | Configura `pago_facil` en INFO; mensajes con id del cobro y `requestId`, nunca secretos | RF-036, RF-039, R-9 |

---

## 5. Contratos

| Contrato | Archivo | Requisitos | Corte |
|---|---|---|---|
| `POST /api/cobros` | [contracts/crear-cobro.md](contracts/crear-cobro.md) | RF-001 a RF-010, RF-034, RF-035, RF-042 | M0 (monto libre en C2) |
| `GET /api/cobros/{id}` | [contracts/ver-cobro.md](contracts/ver-cobro.md) | RF-008, RF-025 a RF-027 | M0 |
| `POST /api/cobros/{id}/cancelar` | [contracts/cancelar-cobro.md](contracts/cancelar-cobro.md) | RF-023, RF-024, RF-030 | C2 |
| `GET /api/cobros/{id}/eventos` (SSE) | [contracts/canal-avisos.md](contracts/canal-avisos.md) | RF-028 a RF-033, RF-040, RF-041, RF-043 | M0 (`cancelado` en C2) |
| `POST /webhooks/pey` | [contracts/aviso-pey.md](contracts/aviso-pey.md) | RF-011 a RF-014, RF-017, RF-018, RF-037, CE-010 | M0 |
| `GET /salud` | [contracts/salud.md](contracts/salud.md) | RF-036, RF-038 | M0 |

**Cambios de forma frente al prototipo** (la web todavía no existe, así que no rompen nada):

- campos en `snake_case` español (`codi_qr_id`, `qr_imagen`, `llave_pey`);
- objeto cobro con `pagos`, `numero_de_pagos`, `total_recibido`, `monto_libre` y `fin_ventana`;
- eventos del canal `estado`, `pago` y `fin` en lugar de `pagado`;
- errores de validación en español.

---

## 6. Modelo de datos

Detalle en [data-model.md](data-model.md). En resumen:

- **Cobro**, con monto fijo o libre, vigencia de 10 min, ventana de escucha (vencimiento + gracia) y una lista de pagos.
- **Pago**, con `transaccion_id` único, número, monto recibido, monto base opcional y hora.
- Estados *pendiente*, *pagado*, *vencido* y *cancelado*, calculados con el reloj. *Pagado* no se deshace.

---

## 7. Estrategia de pruebas

- **Pruebas primero**: cada tarea de implementación tiene antes su prueba, que se ve fallar y después pasa.
- **Pruebas automáticas**: nunca llaman al pey real (pey simulado con `httpx.MockTransport`) ni esperan tiempo real (`RelojFalso`).
- **Rutas**: con `TestClient`. **Canal de avisos**: probando `flujo_de_avisos` directamente con pytest-asyncio (`@pytest.mark.asyncio`) y `RelojFalso` (DP-2); solo el caso de "abrir después de la ventana" se prueba también por HTTP, porque termina solo.
- **Firmas**: `firmar_aviso(cuerpo, secreto_falso)` en `conftest.py`, con la librería `standardwebhooks`.
- **Pruebas reales**: solo con $0.01 y con autorización de Hugo (cierre del corte M0).
- **Nombres en español**, como el comportamiento.

| Requisito | Prueba | Tipo |
|---|---|---|
| RF-001, RF-006, RF-007 | `test_crear_cobro_pide_el_qr_a_pey_con_vigencia_de_10_minutos_y_el_id_del_cobro` | integración |
| RF-002, RF-004 | `test_montos_no_validos_se_rechazan_sin_llamar_a_pey` (negativo, 3 decimales, texto, mayor al máximo; en M0 también 0 y vacío) | integración |
| RF-003 (C2) | `test_monto_vacio_o_cero_crea_un_cobro_de_monto_libre` | integración |
| RF-005, RF-042 | `test_el_concepto_se_limpia_y_usa_cobro_por_defecto`, `test_un_concepto_con_caracteres_no_imprimibles_se_rechaza` | integración |
| RF-008 | `test_el_cobro_devuelve_todos_sus_campos` | integración |
| RF-009, RF-010 | `test_si_pey_falla_el_cobro_no_se_guarda_y_el_mensaje_dice_la_causa` (sin llave, 401, 503, 500, sin conexión) | integración |
| RF-011, CE-004 | `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada` (sin firma, otro secreto, fuera de tiempo) | integración |
| RF-012, RF-017 | `test_un_aviso_valido_registra_el_pago_y_pasa_el_cobro_a_pagado` | integración |
| RF-013 | `test_un_aviso_de_otro_tipo_se_ignora` | integración |
| RF-014, CE-005 | `test_el_mismo_pago_no_se_registra_dos_veces_por_aviso_ni_por_consulta` | integración |
| RF-015, RF-016, CE-006 | `test_un_qr_reutilizado_registra_y_numera_cada_pago`, `test_el_canal_avisa_cada_pago_con_su_numero_y_el_total` | unitaria, integración y async |
| RF-012, RF-032 (QT-5) | `test_un_aviso_despues_de_la_ventana_registra_el_pago` | integración |
| RF-018 | `test_el_pago_guarda_monto_recibido_base_hora_y_transaccion` | unitaria |
| RF-019, RF-020 | `test_un_monto_base_distinto_se_marca_y_deja_advertencia`, `test_una_propina_no_cuenta_como_monto_distinto` | unitaria |
| RF-021 | `test_un_cobro_sin_pagos_vence_a_los_10_minutos` | unitaria |
| RF-022, CE-007 (C2) | `test_un_pago_5_minutos_despues_de_vencer_se_avisa_por_el_canal` | async |
| RF-023, RF-024 (C2) | `test_cancelar_un_cobro_pendiente`, `test_no_se_puede_cancelar_un_cobro_pagado_o_vencido`, `test_un_cobro_cancelado_que_se_paga_pasa_a_pagado` | integración |
| RF-025, RF-026 | `test_ver_el_cobro_consulta_a_pey_como_maximo_cada_3_segundos` | integración |
| RF-025, QP-2 | `test_la_consulta_sigue_las_paginas_solo_mientras_haya_pagos_nuevos_y_solo_cuenta_los_pagados` (3 páginas; no pide la cuarta si la tercera ya era conocida) | unitaria |
| RF-027, QP-1 | `test_si_pey_tarda_mas_de_4_segundos_la_consulta_cuenta_como_sin_respuesta`, `test_si_pey_tarda_mas_de_10_segundos_al_crear_responde_intenta_de_nuevo` (pey simulado que lanza el tiempo agotado de httpx) | unitaria e integración |
| RF-027 | `test_si_pey_no_responde_se_devuelve_el_ultimo_estado` | integración |
| RF-028, RF-031 | `test_el_canal_emite_el_estado_al_abrirse` | async |
| RF-029, CE-003 | `test_el_canal_avisa_el_pago_en_cuanto_se_registra` | async |
| RF-030 | `test_el_canal_avisa_vencido_en_menos_de_15_segundos`, `test_con_gracia_0_el_canal_emite_vencido_y_luego_fin` (QT-6) | async |
| RF-032 | `test_el_canal_emite_fin_y_se_cierra_al_terminar_la_ventana` | async |
| RF-033 | `test_el_canal_manda_senal_de_vida_cada_15_segundos` | async |
| RF-040, CE-008 | `test_con_el_canal_abierto_el_servidor_pregunta_a_pey_cada_5_segundos`, `test_sin_secreto_el_canal_avisa_el_pago_por_la_consulta` (QT-5) | async |
| RF-041 | `test_una_ip_no_puede_abrir_mas_de_10_canales` | async e integración |
| RF-043 | `test_abrir_el_canal_despues_de_la_ventana_emite_estado_y_fin` | integración |
| RF-034 | `test_limite_de_cobros_por_ip`, `test_el_limite_usa_la_ip_real_detras_del_proxy` | integración |
| RF-035 | `test_cors_solo_permite_los_origenes_configurados` | integración |
| RF-036, CE-009 | `test_la_llave_y_el_secreto_no_aparecen_en_respuestas_ni_registros`, más un paso manual con `git grep` de patrones de llaves en los archivos versionados (QP-6) | integración y manual |
| RF-037 | `test_sin_secreto_configurado_todo_aviso_se_rechaza` | integración |
| RF-038 | `test_salud_dice_que_credenciales_faltan_sin_mostrarlas` | integración |
| RF-039 | `test_los_registros_dejan_cobro_error_de_pey_pago_y_aviso_ignorado`, `test_cada_consulta_a_pey_deja_una_linea_en_el_registro` (QT-4) | integración |
| CE-010 | `test_el_aviso_de_pey_no_hace_peticiones_a_pey` (prueba por estructura: el pey simulado no recibe nada durante el aviso), más una medición manual con `curl -w '%{time_total}'` en la guía de verificación (QP-6) | integración y manual |
| R-8 | `test_un_aviso_que_falla_al_procesarse_se_acepta_en_el_reintento` | integración |
| CE-001, CE-002 | Pago real de $0.01 desde la URL pública (quickstart, paso 4); en F3 se mide el tiempo de crear el QR con la imagen (QP-3) | manual |

---

## 8. Plan de implementación

| Fase | Fechas | Quién | Qué | Depende de |
|---|---|---|---|---|
| F1 Preparación | 14 nov, noche | Claude (revisa Hugo) | `reloj.py`, `conftest.py` (PeySimulado, RelojFalso, firmas), reparto de `test_api.py`, configuración nueva, agregar pytest-asyncio (DP-2) | Plan y tasks aprobados |
| F2 Base | 14–15 nov | Claude (revisa Hugo) | Modelo `Cobro`/`Pago` con reloj; `registrar_pago` con pagos numerados y monto distinto (C-1); cliente de pey paginado; errores en español; registros configurados | F1 |
| F3 Historia 1 (M0) | 15 nov, mañana | Claude (revisa Hugo) | Crear cobro de monto fijo: validaciones, concepto, errores de pey | F2 |
| F4 Historias 2 y 3 (M0) | 15 nov, mañana | Claude (revisa Hugo) | Aviso de pey (firma, deduplicación, R-8, QR reutilizado), ver cobro con respaldo, canal de avisos con consulta automática | F3 |
| F5 Historias 5 y 6 (M0) | 15 nov, antes de las 10:00 | Claude (revisa Hugo) | IP real, límite de canales, CORS, salud, secretos en registros, `backend/README.md` con el contrato nuevo (QP-4). Revisión de seguridad (QT-7). **Cierre del corte M0**, con el pago real de $0.01 y un segundo pago al mismo QR | F4, CoDi activo |
| F6 Ventana de gracia (C2) | 16–18 nov | Por repartir tras el kickoff | `GRACIA_SEGUNDOS = 600`, pagos tardíos por el canal; pago real (QT-2) | F5 |
| F7 Monto libre (C2) | 18–19 nov | Por repartir tras el kickoff | Monto vacío o 0 → `amount: 0` en pey; pago real (QT-2) | F5 |
| F8 Cancelación (C2) | 19–20 nov | Por repartir tras el kickoff | `POST /api/cobros/{id}/cancelar` y evento `cancelado`; pago real a un QR cancelado (QT-2) | F5 |
| FN Pulido | 21 nov | Por repartir tras el kickoff | `backend/README.md` con lo del corte 2, revisión de seguridad y quickstart completo | F6–F8 |

El QR reutilizado y el monto distinto, que eran la F6 del corte 2, pasaron a F2 y F4 con el cambio C-1.

El despliegue (#65) y la pantalla (#64) no son fases de este plan, pero el cierre de F5 depende de ellos para CE-001. Lo que necesita el despliegue está en la sección "Despliegue" del [quickstart](quickstart.md) (QP-5). Hugo avisa hoy al equipo de la web que el contrato está en [contracts/](contracts/) (QP-4).

---

## 9. Decisiones

### 9.1 Decisiones del plan

| # | Decisión | Por qué | Alternativas descartadas |
|---|---|---|---|
| DP-4 | Reloj propio inyectable (R-2) | Pruebas de tiempo sin esperar y sin librerías nuevas | `freezegun` o `time-machine`: librería nueva que no controla bien `asyncio.sleep` |
| DP-5 | Consulta automática a pey dentro del ciclo del canal, no en una tarea de fondo (R-4) | Solo consulta si alguien mira; sin tareas que limpiar; *vencido* en menos de 15 s | Una tarea por cobro: consulta aunque nadie mire |
| DP-6 | Evento `fin` antes de cerrar el canal, y la web obligada a llamar a `close()` (R-4) | Evita que `EventSource` reconecte en un ciclo sin fin | Cerrar sin aviso: el navegador reconecta cada 3 s |
| DP-7 | IP real con `ProxyHeadersMiddleware` dentro de la app y `PROXIES_CONFIABLES` (R-5) | Se prueba con `TestClient` y viene en uvicorn | `--proxy-headers` al arrancar: no se puede probar; leer la cabecera a mano: falsificable |
| DP-8 | La consulta a pey sigue las páginas solo mientras traigan transacciones nuevas y solo cuenta `PAID` (R-6, QP-2) | Pagos sin límite (E-4) y errata 1, con una sola petición en el caso normal | Solo la primera página: pierde pagos después del 20. Todas las páginas con tope de 50: demasiadas peticiones (QP-2) |
| DP-9 | Errores siempre como `{"detail": "<mensaje en español>"}`, con manejador de validación (R-7) | Principio VII | Traducir en la web |
| DP-10 | `webhook-id` marcado después de procesar (R-8) | Que un reintento de pey se procese si el primer intento falló | Marcar antes, como el prototipo |
| DP-11 | JSON en `snake_case` español, montos como número y monto libre como `null` (R-10) | Un solo estilo antes de que exista la web | Mantener la mezcla del prototipo |
| DP-12 | La gracia es la variable `GRACIA_SEGUNDOS`: 0 en el corte M0 y 600 desde el corte 2 | El corte 2 activa la gracia cambiando el valor por defecto, con su prueba, sin tocar la lógica | Dos versiones del código |
| DP-13 | Tiempos de espera de pey: 4 s para la consulta y 10 s para crear el QR (QP-1, R-11) | El canal no se queda mudo y se cumplen RF-030, RF-033 y CE-002 | Los 20 s del prototipo |
| DP-14 | Módulo `respaldo.py` con `ConsultaDeRespaldo` (QP-7) | El canal y la ruta de ver cobro comparten la misma lógica y se prueban por separado | Dejar la consulta dentro de `crear_app` |
| DP-15 | Se mantiene `generateImage: true` en el corte M0 y se mide en F3 (QP-3) | La web muestra el QR sin librerías; si pasa de 3 s, se anota un TK y la decisión pasa a #64 | Dibujar el QR en el navegador: exige una librería de QR en la web antes de mañana |

### 9.2 Decisiones de Hugo

| # | Pregunta | Recomendación | Decisión |
|---|---|---|---|
| DP-1 | ¿Partir del prototipo o reescribir? (R-1, P-1 de la spec) | Partir del prototipo y reorganizarlo con pruebas primero | **Partir del prototipo** (Hugo, 2026-11-14), como se recomienda. |
| DP-2 | ¿Qué herramienta para las pruebas asíncronas del canal? (R-3, comparativa) | Plugin de anyio, ya instalado | **pytest-asyncio** (Hugo, 2026-11-14). Se aparta de la recomendación; es solo de desarrollo y se agrega en F1. |
| DP-3 | ¿Quién hace cada fase y quién la revisa? | Claude implementa F1–F5 esta noche y mañana temprano; Hugo revisa cada cierre con la guía de verificación; Altairtm revisa la firma del aviso (#63) | **Claude implementa, Hugo revisa** (Hugo, 2026-11-14). Altairtm revisa la firma en el pull request. El corte 2 se reparte después del kickoff. |

### 9.3 Revisión QA del plan (2026-11-14, una sola pasada)

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QP-1 | Promesa imposible | El cliente de pey espera hasta **20 s** por respuesta (`backend/app/pey.py:31`). Dentro del ciclo del canal, una consulta lenta detiene la vuelta: no se emite *vencido* en menos de 15 s (RF-030) ni la señal de vida cada 15 s (RF-033), y ver un cobro puede tardar 20 s. Crear el cobro puede esperar 20 s frente a la meta de 3 s (CE-002). | RF-030, RF-033, RF-025, RF-040, CE-002 | Dos tiempos de espera: **4 s** para la consulta de respaldo (si se pasa, cuenta como "pey no responde", RF-027) y **10 s** para crear el QR (si se pasa, 502 "Intenta de nuevo"). Pruebas con un pey simulado que tarda. | **4 s para la consulta y 10 s para crear** (Hugo, 2026-11-14), como se recomienda. Aplicada. |
| QP-2 | API de pey | Recorrer **todas** las páginas en cada consulta (DP-8) multiplica las peticiones: un QR con 60 pagos haría 3 peticiones cada 5 s por cada cobro mirado, y el tope de 50 páginas permite 50 peticiones por consulta. pey ordena de la más nueva a la más vieja (`openapi.json`). | RF-025, RF-040, RF-015 | Pedir páginas solo mientras traigan transacciones nuevas: detenerse en la primera página donde todas las transacciones ya están vistas, sin tope de 50. La prueba usa 3 páginas y comprueba que no se pide la cuarta. | **Parar en la página conocida**, sin tope de 50. Reemplaza parte de DP-8. Aplicada. |
| QP-3 | API de pey | El plan pide `generateImage: true`. pey advierte que la imagen "can make the endpoint respond more slowly" y recomienda dibujar el QR en el cliente desde `qrString` (`openapi.json`, `POST /codi/qr`). Pone en riesgo CE-002 (QR en menos de 3 s). | CE-002, RF-008 | Mantener la imagen en el corte M0, porque la web la muestra sin librerías, y medir el tiempo en la verificación de F3. Si pasa de 3 s, se anota un TK y se pasa la decisión a la spec de la web (#64). | **Mantener la imagen y medir** en F3. Aplicada. |
| QP-4 | Construibilidad | El plan cambia la forma del API (campos en `snake_case`, eventos `estado`, `pago` y `fin`, objeto cobro con `pagos`), pero `backend/README.md` sigue con el contrato del prototipo (`codiQrId`, evento `pagado`, líneas 33-62) y solo se actualiza en FN (21 nov). Si alguien construye la web (#64) esta noche con ese README, se rompe al llegar el corte M0. | RF-008, RF-029, RF-031, RF-032 | Avisar hoy al equipo de la web que la fuente es `specs/001-backend-mvp/contracts/`, y actualizar `backend/README.md` en el cierre de F5 (corte M0), no en FN. | **Avisar hoy al equipo de la web y actualizar el README en el cierre de F5.** Aplicada. |
| QP-5 | Hueco | El plan exige un solo proceso, `PROXIES_CONFIABLES`, `WEB_ORIGIN`, `GRACIA_SEGUNDOS` y que el canal no se corte, pero no dice qué debe configurar el despliegue (#65). Con más de un *worker* de uvicorn, los cobros, los límites y los canales quedarían repartidos entre procesos y el aviso de pey podría llegar a un proceso que no conoce el cobro. | RF-034, RF-041, RF-032, restricción de §1 | Agregar al quickstart una sección "Despliegue" para Altairtm: un solo *worker*; variables `PEY_API_KEY`, `PEY_WEBHOOK_SECRET`, `WEB_ORIGIN`, `PROXIES_CONFIABLES`; la URL del aviso; y comprobar que el proxy no retiene los eventos SSE. | **Sección "Despliegue" en el quickstart.** Aplicada. |
| QP-6 | Contradicción | Dos comprobaciones de §7 chocan con el principio V o no son automáticas: (a) "menos de 1 segundo" (CE-010) mediría tiempo real; (b) CE-009 incluye "ningún archivo del repositorio", y la prueba solo revisa respuestas y registros. | CE-009, CE-010, principio V | (a) Comprobar CE-010 por estructura: durante el aviso, el pey simulado no recibe ninguna petición, más una medición manual con `curl -w` en la guía de verificación. (b) Un paso de la guía con `git grep` de patrones de llaves en los archivos versionados, sin leer el `.env`. | **Comprobación por estructura más pasos manuales** en la guía de verificación. Aplicada. |
| QP-7 | Hueco | `flujo_de_avisos` (en `canal.py`) necesita la consulta de respaldo, pero el plan la pone dentro de `crear_app` en `main.py` (§4), como en el prototipo (`main.py:85`). Así, el canal no se puede probar solo con pytest-asyncio sin levantar la app. | RF-040, RF-025, RF-026 | Llevar la consulta de respaldo y el "registrar y avisar" a un módulo nuevo, `respaldo.py` (`ConsultaDeRespaldo(cliente_pey, repositorio, difusor, reloj)`), que `main.py` y `canal.py` reciben ya creado. | **Módulo nuevo `respaldo.py`.** Aplicada. |

**Bloques de la pasada:**

1. **Coherencia interna**: cada RF y cada CE tiene pieza, contrato y prueba (comprobado con un script sobre §7: ningún RF-001 a RF-043 ni CE-001 a CE-010 sin prueba). La verificación de la constitución está completa y no quedan `[NECESITA ACLARACIÓN]`. DP-1 a DP-12 sin números repetidos. Salen QP-6 y QP-7, más la errata 1.
2. **Spec, plan del hackathon, reglas e issues**: el plan sigue los dos cortes de QA-1 y las fechas de M0. Del issue #18 se cumple "arranca con un solo comando" (quickstart, paso 2). No se pudo leer el issue #64 (`gh` agotó el tiempo); la coordinación con la web sale de README y contratos (QP-4).
3. **Código (solo lectura)**: tiempos de espera de 20 s (`pey.py:31`), consulta dentro de `crear_app` (`main.py:85`) y README con el contrato viejo. Salen QP-1, QP-4 y QP-7.
4. **API de pey**: `generateImage` más lento, orden de la más nueva a la más vieja con `nextToken`, `sign(msg_id, timestamp, data)` de `standardwebhooks` permite firmar con una hora vieja para probar "fuera de tiempo". Salen QP-2 y QP-3.
5. **Dependencias externas**: pytest-asyncio nuevo, solo de desarrollo, con versión de al menos dos semanas; CoDi el 15 nov; hosting y aviso en #65. Sale QP-5.
6. **Casos límite**: pey lento (QP-1), muchos pagos (QP-2), varias pantallas en un mismo cobro (el `Difusor` reparte a todas), reinicio con canales abiertos (404, y `EventSource` no reconecta), error de pey dentro del canal (se tolera, RF-027).
7. **Seguridad y rendimiento**: `PROXIES_CONFIABLES="*"` solo si el hosting no permite conexiones directas (riesgo en §11), firma antes de leer el JSON, registros sin secretos. Salen QP-1, QP-2 y QP-6.
8. **Construibilidad y reparto**: Claude hace F1 a F5 y Hugo revisa (DP-3); el riesgo de fecha está en §11. Sale QP-4.

**Erratas** (sin efecto en el comportamiento; corregidas al aprobar, el 2026-11-14):

1. *(Corregida)* H-13 mencionaba el plugin de anyio, que ya no se usa (DP-2); ahora dice solo lo de `ProxyHeadersMiddleware`.
2. *(Corregida en el contrato)* El contrato de crear cobro no decía que las peticiones rechazadas por validación (422) no cuentan para el límite de 10 por minuto; así funciona el prototipo y ya está escrito.

---

## 10. Seguridad

- **Secretos**:
  - `PEY_API_KEY` y `PEY_WEBHOOK_SECRET` como `SecretStr`, leídos de `backend/.env` (ignorado por git) o del hosting.
  - Solo `pey.py` usa la llave y solo la ruta del aviso usa el secreto.
  - La prueba de CE-009 usa valores falsos y distintivos y los busca en todas las respuestas y en los registros capturados.
- **Firma del aviso**:
  - `standardwebhooks.Webhook(secreto).verify(cuerpo, cabeceras)` sobre el cuerpo exacto, antes de leer el JSON.
  - Tolerancia de 5 minutos.
  - Si falla, 401 sin cambios; sin secreto, 503 (RF-011, RF-037).
- **Entradas**:
  - monto con `Decimal`, mayor a 0, 2 decimales y máximo $100 (monto libre en C2);
  - concepto de máximo 40 caracteres imprimibles;
  - `id` de cobro buscado en el diccionario, sin otro uso;
  - cuerpo del aviso leído solo después de la firma.
- **Demo pública**:
  - 10 cobros por minuto y 10 canales abiertos por IP real del cliente (DP-7);
  - CORS solo para `WEB_ORIGIN`, con `GET` y `POST`;
  - la consulta automática a pey, acotada a una cada 5 s por cobro, solo con canales abiertos y normalmente de una sola página (QP-2);
  - un solo *worker* de uvicorn en el hosting (quickstart, "Despliegue").
- **Registros**: id del cobro, `codiQrId`, `transactionId` y `requestId`; nunca cabeceras, cuerpos completos, llaves, secretos ni datos bancarios.

---

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| No terminar F1–F5 antes de la entrega (15 nov, 1:00 PM) | Sin app en vivo en el formulario | Orden de fases con lo más valioso primero (cobro, aviso, respaldo); si a las 10:00 no está F5, se despliega el último cierre en verde y se avisa en el formulario. El repo público es lo obligatorio |
| CoDi no se activa a tiempo en el banco de Hugo | No se puede demostrar CE-001 | Pedir a otra persona del equipo con CoDi activo que pague los $0.01 (con autorización de Hugo) |
| El aviso de pey no queda configurado en el despliegue | Sin CE-003 | La consulta automática (RF-040) avisa el pago igual, en a lo más 5 s |
| `PROXIES_CONFIABLES` mal configurado en el hosting | Límite por IP global o falsificable | Paso en la guía de verificación de F5: dos visitantes con distinta IP tienen límites separados; Altairtm confirma el proxy de Render o Railway |
| Límite de peticiones de pey desconocido | La consulta automática podría saturarlo | Tope por cobro (5 s), solo con canales abiertos y máximo 10 canales por IP; pregunta a pey en el kickoff |
| El hosting duerme el servidor sin uso | Se pierden los cobros y el primer QR tarda | Despertarlo antes de la demo (#65); limitación de memoria aceptada hasta #23 |
| La imagen del QR hace que crear el cobro pase de 3 s | No se cumple CE-002 | Medir en F3 (QP-3); si pasa, TK y decisión en #64 |
| La web se construye con el contrato viejo del prototipo | La pantalla se rompe al llegar el corte M0 | Hugo avisa hoy al equipo de la web; README actualizado en F5 (QP-4) |
| El hosting arranca varios *workers* | El aviso de pey llega a un proceso que no conoce el cobro | Un solo *worker*, en la sección "Despliegue" del quickstart (QP-5) |

---

## 12. Seguimiento de complejidad (Complexity Tracking)

Sin excepciones a la constitución.

---

## 13. Aprobación

- [x] Decisiones DP-1 a DP-3 tomadas por Hugo (2026-11-14).
- [x] Plan revisado con `/qa-spec 001 plan` y todos los hallazgos QP decididos y aplicados (QP-1 a QP-7, 2026-11-14).
- [x] Aprobado por Hugo el 2026-11-14. Aprobar no autoriza a empezar `tasks.md`: se espera a que Hugo lo pida.

---

## 14. Registro de implementación

| # | Fecha | Qué | Por qué | Afecta |
|---|---|---|---|---|
| TK-1 | 2026-11-14 | Cambio C-1: el QR reutilizado y el monto distinto pasan al corte M0. `registrar_pago` numera cada pago desde F2; se quita la regla temporal "solo el primer pago"; la antigua F6 se reparte entre F2 y F4 y las fases del corte 2 se renumeran (F6 gracia, F7 monto libre, F8 cancelación) | QT-3 de tasks: evitar el choque temporal con el principio VIII | spec §1.2, RF-015, RF-016, RF-019, RF-020, CE-006; data-model §1 y §4; contrato aviso-pey; §7 y §8 de este plan; tasks |
| TK-2 | 2026-11-14 | Una línea `INFO` por cada consulta a pey y por cada QR creado (QT-4); con gracia 0 el canal emite `vencido` y luego `fin` (QT-6) | Principio X; contrato del canal | research R-9; contrato canal-avisos; tasks T020, T023, T026, T029 |
| TK-3 | 2026-11-14 | Enmienda PATCH pendiente de la constitución II: "la única puerta que registra cada pago" (QT-1) | Avisar cada pago de un QR reutilizado | Constitución, cuando Hugo pida `/speckit-constitution` |
| TK-4 | 2026-11-14 | pytest-asyncio 1.4.1 (publicada el 2026-10-25) queda con `asyncio_default_fixture_loop_scope = "function"` en `backend/pyproject.toml` | Esa versión avisa en cada `pytest` si la opción no está fijada, y anuncia que el alcance del bucle va a pasar a `function` | Solo el arranque de pytest. No cambia la spec ni el prototipo |
| TK-5 | 2026-11-14 | Medición de F3 (QP-3, DP-15): crear un cobro real de $0.01 con `generateImage: true` tardó **9.09 s** con el servidor recién arrancado. Al repetirlo con otro arranque: **7.77 s** el primer cobro y **2.39 s** el segundo. El primer cobro después de arrancar no cumple CE-002 (menos de 3 s) y queda cerca del límite de 10 s que espera crear (QP-1): si pey tarda un poco más, responde 502. Los siguientes sí cumplen. No se cambió código | Lo que pide DP-15 cuando la medición pasa de 3 s | CE-002, QP-1; la decisión de la imagen pasa a #64 (spec de la web) |
| TK-6 | 2026-11-15 | Cambio C-2: `Cobro.publico()` agrega `hora_servidor` (entero, `int(reloj.ahora())`). Como todas las respuestas y los eventos usan `publico()`, el campo sale en crear, ver, cancelar y el canal sin tocar las rutas | Spec 002, RF-019 y CE-016: la cuenta regresiva no puede depender del reloj del celular ni de `creado_en`, que se fija antes de pedir el QR a pey | RF-008, `contracts/crear-cobro.md`, `contracts/canal-avisos.md`, `cobros.py`, tasks F9 |
