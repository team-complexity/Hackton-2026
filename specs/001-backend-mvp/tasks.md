# Tasks: Backend del MVP: cobrar con CoDi y saber que me pagaron

- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-14, con el cambio C-1 aplicado el mismo día, y el cambio C-2 aplicado el 2026-11-15
- **Plan**: [plan.md](plan.md), estado: Aprobado el 2026-11-14, ajustado por TK-1 y TK-2 (§14)
- **Fecha**: 2026-11-14
- **Estado**: `Aprobado`. Hugo lo aprobó el 2026-11-14, después de `/speckit-analyze` y de la QA (QT-1 a QT-7, aplicadas, con el cambio C-1 a la spec). F1 terminada (Grok, 2026-11-14). F2 terminada (Grok, 2026-11-14). F3 terminada (Grok, 2026-11-14). F4 terminada (Grok, 2026-11-14). F5 terminada en código (Grok, 2026-11-14). F4 y F5 revisadas por Claude el 2026-11-14, con una corrección (400 para un `amount` que no es un número finito): 95 passed y ruff limpio. Los dos pagos reales de $0.01 quedan pendientes de la autorización de Hugo y de CoDi (se activa el 15 nov). Si a las 10:00 del 15 nov no están hechos, se sigue el riesgo de §11 del plan: desplegar este cierre en verde y avisarlo en el formulario. F6 terminada en código (Grok, 2026-11-14): 97 passed y ruff limpio. El pago real tardío de $0.01 queda pendiente de la autorización de Hugo. Si el banco no deja pagar un QR vencido, se anota la pregunta abierta de la spec §8.5. F7 terminada en código (Grok, 2026-11-14): 96 passed y ruff limpio. El pago real de monto libre de $0.01 queda pendiente de la autorización de Hugo. F8 terminada en código (Grok, 2026-11-14). F6, F7 y F8 revisadas por Claude el 2026-11-14: 104 passed y ruff limpio. El pago real a un QR cancelado queda pendiente de la autorización de Hugo. FN terminada (Grok, 2026-11-15): 104 passed y ruff limpio. El README y el quickstart quedan al día con el corte 2. Los pagos reales de $0.01 siguen pendientes de la autorización de Hugo. F9 terminada (Claude, 2026-11-15): cambio C-2, `hora_servidor` en cada objeto cobro; 109 passed y ruff limpio.
- **Entrada**: los documentos de `specs/001-backend-mvp/`: plan.md, spec.md, research.md, data-model.md, contracts/ y quickstart.md

> **Notas para los comandos de spec-kit.**
> - Cada tarea sigue el formato obligatorio `- [ ] T001 [P] [US1] Descripción con ruta del archivo`.
> - `/speckit-implement` la marca como `[X]` al terminarla.
> - Los detalles van como sub-puntos sangrados debajo de la tarea.
> - `[P]` = se puede hacer en paralelo (otros archivos, sin dependencias pendientes).
> - `[US1]` = historia de la spec a la que pertenece (H1 = US1 … H6 = US6).
> - Las casillas van siempre en listas, nunca en tablas (en las tablas no se ven).
> - Todas las rutas son relativas a la raíz del repositorio. Los comandos de prueba se corren desde la raíz: `uv run --directory backend pytest -q`.

---

## Reglas de ejecución

1. **Las fases van en orden.** Una fase la hace una sola persona o agente. Al empezar lo anota en **Estado** ("F2 en curso (Claude)") y al cerrarla también ("F2 terminada (Claude, AAAA-MM-DD)").
2. **Pruebas primero.** En cada fase se escriben las pruebas, se ven fallar y después se implementa.
3. **Solo se hace la tarea pedida.** Nada de funciones sorpresa, retoques cosméticos ni refactorizaciones fuera de la tarea.
4. **Si el código obliga a cambiar algo**, se anota en el *Registro de implementación* del plan (§14) como TK-n. Si toca una spec aprobada, se presenta como un cambio `C-n`, que Hugo aprueba por separado.
5. **Una fase cierra con tres cosas:**
   - todas las pruebas en verde: `uv run --directory backend pytest -q`, `uv run --directory backend ruff check .` y `uv run --directory backend ruff format --check .` (esta spec no tiene web; la web es #64);
   - su sección en `specs/001-backend-mvp/verification-guide.md`;
   - el mensaje de commit sugerido, con formato `tipo(001): descripción en español`.
   - El commit, el push y el pull request los hace Hugo.
6. **Ninguna prueba automática llama al pey real ni espera tiempo real.** pey simulado con `httpx.MockTransport` y `RelojFalso`. Las pruebas con dinero real son de $0.01 y requieren la autorización de Hugo en ese momento.
7. **Secretos**: la llave de pey y el secreto del aviso nunca se leen, imprimen ni citan. Las pruebas usan valores falsos y distintivos.

## Reparto

| Fase | Quién la hace | Quién la revisa |
|---|---|---|
| F1 Preparación | Claude | Hugo |
| F2 Base | Claude | Hugo |
| F3 Historia 1 (M0) | Claude | Hugo |
| F4 Historias 2 y 3 (M0) | Claude | Hugo; Altairtm revisa la firma del aviso en el pull request |
| F5 Historias 5 y 6 (M0) | Claude | Hugo (cierre del corte M0, con los pagos reales de $0.01) |
| F6 a F8 (corte 2) | Por repartir tras el kickoff | Por repartir |
| FN Pulido | Por repartir tras el kickoff | Hugo |

## Dependencias externas

| Dependencia | Qué bloquea | Estado |
|---|---|---|
| CoDi activado en el banco de Hugo (15 nov) | Los pagos reales de $0.01 de T038 (CE-001, CE-006 y CE-008 reales) y de los cierres del corte 2 | Pendiente |
| Llave de pey en `backend/.env` | La medición del QR con imagen de T021 (CE-002) y T038 | Listo (H-1) |
| Hosting con HTTPS y aviso dado de alta en el portal de pey (#65, Altairtm) | CE-001 desde la URL pública y CE-003 con el aviso real (T038) | Pendiente |
| Pantalla de la web (#64) | CE-001 desde la URL pública | Pendiente |
| Aviso de Hugo al equipo de la web: el contrato está en `contracts/` y la pantalla llama a `close()` al recibir `fin` (QP-4) | Que #64 no se construya con el contrato viejo | Pendiente (Hugo, 14 nov) |

## Formato de cada tarea

```text
- [ ] T000 [P] [US1] Descripción con la ruta exacta del archivo
  - **RF**: RF-001, RF-002
  - **Dep.**: T000 (o "ninguna")
  - **Hecho cuando**: criterio verificable (prueba que pasa, comando y salida esperada)
```

---

## Fase 1 (F1): Preparación (Setup) · 14 nov, noche

**Propósito**: reloj inyectable, pey simulado compartido, firmas de prueba, configuración nueva y pytest-asyncio, sin cambiar el comportamiento del prototipo.

- [X] T001 Agregar pytest-asyncio 1.4.1 como dependencia de desarrollo en `backend/pyproject.toml` y `backend/uv.lock`
  - Comando: `cd backend && uv add --dev "pytest-asyncio==1.4.1"`. Es la versión más nueva publicada el 2026-10-31 o antes (salió el 2026-10-25; `1.4.1.post1` y `1.5.0` tienen menos de dos semanas, DP-2). Sin `pip install`.
  - **RF**: — (DP-2, principio V)
  - **Dep.**: ninguna
  - **Hecho cuando**: `uv run --directory backend pytest -q` sigue en `15 passed` y la versión, con su fecha de publicación, queda anotada para la sección F1 de la guía de verificación.
- [X] T002 [P] Escribir las pruebas del reloj en `backend/tests/test_modelo.py` (archivo nuevo)
  - `test_el_reloj_falso_avanza_solo_cuando_se_le_pide`: `RelojFalso(inicio=1_794_700_000)`; `ahora()` no cambia hasta `avanzar(10)`.
  - `test_dormir_con_el_reloj_falso_adelanta_el_tiempo_sin_esperar` (`@pytest.mark.asyncio`): `await reloj.dormir(5)` adelanta `ahora()` 5 s y la prueba tarda menos de 0.5 s reales.
  - **RF**: — (principio V; base de RF-021, RF-030, RF-034, RF-040)
  - **Dep.**: T001
  - **Hecho cuando**: las dos pruebas existen y fallan porque `app.reloj` no existe.
- [X] T003 [P] Escribir la prueba de la configuración nueva en `backend/tests/test_salud_y_registros.py` (archivo nuevo)
  - `test_la_configuracion_tiene_los_valores_por_defecto_del_plan`: `proxies_confiables == "127.0.0.1"`, `gracia_segundos == 0`, `canales_por_ip == 10`, sin leer `backend/.env` (se construye `Configuracion(_env_file=None)`).
  - **RF**: RF-022, RF-034, RF-041
  - **Dep.**: ninguna
  - **Hecho cuando**: la prueba existe y falla porque faltan los campos.
- [X] T004 Implementar `Reloj` y `RelojFalso` en `backend/app/reloj.py` (archivo nuevo)
  - `Reloj.ahora() -> float` (segundos Unix, `time.time()`) y `async Reloj.dormir(segundos: float) -> None` (`asyncio.sleep`).
  - `RelojFalso(inicio: float)`: `ahora()`, `avanzar(segundos)` y `async dormir(segundos)`, que adelanta el tiempo y cede el control con `await asyncio.sleep(0)`, sin esperar.
  - Docstrings en español con los requisitos (spec 001, principio V).
  - **RF**: — (DP-4, R-2)
  - **Dep.**: T002
  - **Hecho cuando**: las pruebas de T002 pasan.
- [X] T005 [P] Agregar `proxies_confiables`, `gracia_segundos` y `canales_por_ip` en `backend/app/config.py` y documentarlos en `backend/.env.example`
  - Variables `PROXIES_CONFIABLES` (por defecto `127.0.0.1`), `GRACIA_SEGUNDOS` (por defecto `0` en el corte M0) y `CANALES_POR_IP` (por defecto `10`). En `.env.example`, solo los nombres y valores por defecto; nunca valores de secretos.
  - **RF**: RF-022, RF-034, RF-041
  - **Dep.**: T003
  - **Hecho cuando**: la prueba de T003 pasa.
- [X] T006 Crear `backend/tests/conftest.py` con el pey simulado, el reloj falso y las firmas, y agregar el parámetro `reloj` a `crear_app` en `backend/app/main.py`
  - `PeySimulado` (sobre `httpx.MockTransport`): guarda cada petición recibida; respuestas configurables para `POST /codi/qr` (éxito con `id`, `qrString`, `qrImage`), `GET /transaction/codi/qr/{id}` (lista de páginas con `nextToken`), errores 401, 403, 503 y 500 con `requestId`, sin conexión (`httpx.ConnectError`) y tiempo agotado (`httpx.ReadTimeout`).
  - Fixtures: `reloj` (`RelojFalso`), `pey`, `configuracion` (llave y secreto falsos y distintivos, p. ej. `llave-falsa-NO-DEBE-SALIR` y `whsec_` + base64 de `secreto-falso-NO-DEBE-SALIR`), `app` y `cliente` (`TestClient`).
  - `firmar_aviso(cuerpo: str, secreto: str, webhook_id: str, momento: datetime) -> dict` con `standardwebhooks.Webhook(secreto).sign(webhook_id, momento, cuerpo)`, que recibe el cuerpo como **texto** (`data: str`); devuelve las cabeceras `webhook-id`, `webhook-timestamp` y `webhook-signature`. Permite firmar con una hora vieja para probar "fuera de tiempo".
  - `crear_app(configuracion, cliente_pey=None, reloj=None)`: guarda `reloj or Reloj()` en `app.state.reloj`, sin usarlo todavía en la lógica.
  - **RF**: — (principio V; base de RF-011 y de todas las pruebas)
  - **Dep.**: T004, T005
  - **Hecho cuando**: `uv run --directory backend pytest -q` sigue en verde y ninguna petición sale a `api.pey.mx`.
- [X] T007 Repartir las 11 pruebas de `backend/tests/test_api.py` entre los archivos nuevos y borrar `test_api.py` con `rm`
  - Destinos: `test_salud` → `test_salud_y_registros.py`; `test_crear_cobro_llama_a_pey_y_devuelve_el_qr`, `test_montos_invalidos_se_rechazan_sin_llamar_a_pey` y `test_error_de_pey_da_mensaje_claro_y_no_guarda_el_cobro` → `test_crear_cobro.py`; `test_limite_de_cobros_por_ip` → `test_proteccion.py`; `test_webhook_marca_pagado_y_no_duplica`, `test_webhook_sin_firma_valida_se_rechaza` y `test_webhook_de_cobro_desconocido_responde_200` → `test_aviso_pey.py`; `test_sin_webhook_el_estado_se_confirma_consultando_a_pey` y `test_cobro_inexistente_da_404` → `test_respaldo.py`; `test_eventos_emite_pagado_si_el_cobro_ya_se_pago` → `test_canal.py`.
  - Mismas aserciones; solo cambian a las fixtures de `conftest.py`. Las fases siguientes las reescriben al contrato nuevo.
  - **RF**: —
  - **Dep.**: T006
  - **Hecho cuando**: `backend/tests/test_api.py` ya no existe y `uv run --directory backend pytest -q` da `15 passed` más las 3 pruebas nuevas de F1 (18 en total).
- [X] T008 Cierre de F1: pruebas en verde, sección F1 en `specs/001-backend-mvp/verification-guide.md` (archivo nuevo) y commit sugerido
  - La guía dice cómo comprobar que el reloj falso no espera, que el pey simulado no sale a la red y qué versión de pytest-asyncio se fijó.
  - Commit sugerido: `test(001): preparar reloj inyectable, pey simulado y pytest-asyncio (F1)`.

---

## Fase 2 (F2): Base que bloquea (Foundational) · 14–15 nov

**Propósito**: modelo `Cobro`/`Pago` con reloj, una sola puerta para registrar pagos (numerados, sin límite y con monto distinto, por C-1), cliente de pey paginado con tiempos de espera, errores en español y registros visibles.

**⚠️ Ninguna historia empieza antes de cerrar esta fase.**

- [X] T009 [P] Escribir las pruebas del modelo de cobro y pago en `backend/tests/test_modelo.py`
  - `test_un_cobro_sin_pagos_vence_a_los_10_minutos`: `expira_en == creado_en + 600`; *pendiente* en `creado_en + 599`, *vencido* en `creado_en + 600`.
  - `test_el_estado_sigue_el_orden_pagos_cancelado_vencido_pendiente`: "si hay pagos → pagado; si no, si cancelado_en → cancelado; si no, si ahora ≥ expira_en → vencido; si no → pendiente".
  - `test_la_ventana_de_escucha_termina_al_vencer_mas_la_gracia`: `fin_ventana == expira_en + gracia`; `en_ventana(ahora)` es `ahora < fin_ventana` (con gracia 0 y con gracia 600).
  - `test_el_pago_guarda_monto_recibido_base_hora_y_transaccion`: campos `transaccion_id`, `numero`, `monto_recibido`, `monto_base` (vacío si llegó por aviso), `pagado_en` (la hora del `Reloj` si falta `datePaid`) y `fuente` (`aviso` o `consulta`).
  - `test_monto_distinto_compara_el_monto_base_o_el_recibido_con_el_pedido`: "el cobro es de monto fijo y (`monto_base` si existe, o si no `monto_recibido`) ≠ `monto` del cobro".
  - `test_el_objeto_publico_del_cobro_tiene_los_campos_del_contrato`: exactamente `id`, `codi_qr_id`, `monto`, `monto_libre`, `concepto`, `estado`, `qr`, `qr_imagen`, `creado_en`, `expira_en`, `fin_ventana`, `numero_de_pagos`, `total_recibido`, `pagado_en`, `pagos`; cada pago con `numero`, `monto_recibido`, `monto_distinto`, `pagado_en` y **sin** `transaccion_id`.
  - **RF**: RF-008, RF-018, RF-019, RF-021, RF-032
  - **Dep.**: T008
  - **Hecho cuando**: las pruebas existen y fallan contra el `cobros.py` del prototipo.
- [X] T010 Escribir las pruebas de `registrar_pago` en `backend/tests/test_modelo.py`
  - `test_el_primer_pago_pasa_a_pagado_desde_pendiente_vencido_o_cancelado`.
  - `test_una_transaccion_ya_vista_no_se_registra_otra_vez`: el mismo `transaccion_id` devuelve "nada" aunque venga de otra fuente o de otro cobro (conjunto global).
  - `test_un_qr_reutilizado_registra_y_numera_cada_pago` (parte unitaria): tres transacciones distintas → pagos 1, 2 y 3; `total_recibido` es la suma; `pagado_en` es la hora del último; el estado sigue *pagado* (C-1).
  - `test_un_monto_base_distinto_se_marca_y_deja_advertencia`: cobro de $50 y pago con `monto_base` 40 → `monto_distinto: true` y un `WARNING` en el registro `pago_facil` con el id del cobro, el monto pedido y el recibido (`caplog`).
  - `test_una_propina_no_cuenta_como_monto_distinto`: `monto_base` 50 y `monto_recibido` 55 → `monto_distinto: false`, sin advertencia.
  - **RF**: RF-014, RF-015, RF-016, RF-017, RF-019, RF-020; CE-006
  - **Dep.**: T009 (mismo archivo)
  - **Hecho cuando**: las pruebas existen y fallan contra el prototipo.
- [X] T011 [P] Escribir las pruebas del cliente de pey para la consulta en `backend/tests/test_respaldo.py`
  - `test_la_consulta_sigue_las_paginas_solo_mientras_haya_pagos_nuevos_y_solo_cuenta_los_pagados`: 3 páginas en el pey simulado (la primera con una `PENDING`); con todas desconocidas pide las 3 y devuelve solo las `PAID` como `PagoPey(id, monto, monto_base, pagado_en)`; con la tercera ya conocida, no pide una cuarta; en el caso normal hace una sola petición.
  - `test_si_pey_tarda_mas_de_4_segundos_la_consulta_cuenta_como_sin_respuesta`: el pey simulado lanza `httpx.ReadTimeout`; `pagos_del_qr` lanza `ErrorPey` de tipo "sin conexión", y el cliente se construye con un tiempo de espera de 4 s para la consulta (se comprueba en el `httpx.Timeout` de la petición).
  - **RF**: RF-025, RF-027, RF-015 (QP-1, QP-2, DP-8)
  - **Dep.**: T008
  - **Hecho cuando**: las pruebas existen y fallan contra el `pey.py` del prototipo.
- [X] T012 Actualizar las pruebas repartidas al objeto cobro nuevo y escribir la prueba de errores en español en `backend/tests/test_crear_cobro.py`
  - En los archivos de pruebas repartidos en T007, cambiar las aserciones de nombres de campos del cobro al [objeto cobro](contracts/crear-cobro.md#objeto-cobro) (`codiQrId` → `codi_qr_id`, `qrImagen` → `qr_imagen`, etc.). Las pruebas de salud y del canal se reescriben en F4 y F5, no aquí.
  - `test_los_errores_de_validacion_salen_en_espanol`: `POST /api/cobros` con `{"monto": "abc"}` responde 422 con `{"detail": <texto>}`, donde `detail` es una cadena en español, no la lista de pydantic.
  - **RF**: RF-004, RF-008 (DP-9, R-7)
  - **Dep.**: T010, T011
  - **Hecho cuando**: las pruebas fallan por los nombres de campos y por el formato de error.
- [X] T013 [P] Escribir la prueba de registros visibles en `backend/tests/test_salud_y_registros.py`
  - `test_los_registros_de_pago_facil_se_ven_en_info`: al crear la app, el registro `pago_facil` queda en nivel `INFO` con un manejador que escribe en la consola.
  - **RF**: RF-039 (R-9, H-10)
  - **Dep.**: T008
  - **Hecho cuando**: la prueba existe y falla.
- [X] T014 Implementar `Cobro`, `Pago` y `RepositorioCobros` con reloj en `backend/app/cobros.py`
  - `Cobro`: campos del [modelo de datos §1](data-model.md); `estado(ahora)`, `en_ventana(ahora)`, `numero_de_pagos`, `total_recibido`, `pagado_en` y `publico()`.
  - `Pago`: campos del [modelo de datos §2](data-model.md) y `monto_distinto` calculado.
  - `RepositorioCobros`: índices `id → Cobro`, `codi_qr_id → id`, conjunto de transacciones vistas y conjunto de `webhook-id` vistos (data-model §5). `nuevo(...)` recibe `ahora` del reloj; `registrar_pago(cobro, transaccion_id, monto_recibido, monto_base, pagado_en, fuente) -> Pago | None` con las reglas de data-model §4: transacción ya vista → nada; si no, agrega con `numero = len(pagos) + 1`, sin límite; si `monto_distinto`, deja un `WARNING`.
  - **RF**: RF-008, RF-014, RF-015, RF-016, RF-017, RF-018, RF-019, RF-020, RF-021
  - **Dep.**: T004, T010
  - **Hecho cuando**: las pruebas de T009 y T010 pasan.
- [X] T015 [P] Implementar la consulta paginada, `PagoPey`, los tiempos de espera y los tipos de `ErrorPey` en `backend/app/pey.py`
  - `pagos_del_qr(codi_qr_id, vistas: set[str]) -> list[PagoPey]`: sigue `nextToken` solo mientras la página traiga alguna transacción que no esté en `vistas` (QP-2); devuelve solo `PAID`; `monto_base` = `amountBreakdown.base` si viene. Devuelve también cuántas páginas pidió y el `requestId` de la última respuesta, si pey lo manda, para el registro de T026.
  - Tiempos de espera: 4 s por petición de consulta y 10 s para `crear_qr` (QP-1, DP-13). Un tiempo agotado se trata como error de conexión.
  - `ErrorPey` distingue: sin llave, sin conexión, llave rechazada (401/403), mantenimiento (503) y error general, y guarda el `requestId` cuando pey lo manda.
  - **RF**: RF-010, RF-025, RF-027, RF-039
  - **Dep.**: T011
  - **Hecho cuando**: las pruebas de T011 pasan.
- [X] T016 Conectar `backend/app/main.py` al modelo nuevo, con errores en español y registros configurados
  - Usar `app.state.reloj` para crear cobros y calcular estados; responder con `Cobro.publico()`.
  - El manejador del aviso y la consulta de respaldo del prototipo (`backend/app/main.py:79,85,149`) pasan de `marcar_pagado` a `RepositorioCobros.registrar_pago`, y de la consulta vieja a `pagos_del_qr(codi_qr_id, vistas)`, con el mismo comportamiento que hoy, hasta que T027 y T028 los reemplacen.
  - Manejador de `RequestValidationError` que responde `{"detail": "<mensaje en español>"}` (los mensajes específicos de monto y concepto llegan en F3).
  - Configurar el registro `pago_facil` en `INFO` con un manejador de consola al crear la app; nunca registrar cabeceras, cuerpos completos ni secretos.
  - **RF**: RF-004, RF-008, RF-039 (DP-9, R-7, R-9)
  - **Dep.**: T012, T013, T014, T015
  - **Hecho cuando**: `uv run --directory backend pytest -q` está todo en verde, con `ruff check` y `ruff format --check` limpios.
- [X] T017 Cierre de F2: pruebas en verde, sección F2 en `verification-guide.md` y commit sugerido
  - La guía dice cómo leer en las pruebas el orden de estados, la numeración de pagos y el monto distinto, y cómo ver un registro `INFO` al arrancar el servidor.
  - Commit sugerido: `refactor(001): modelo de cobro con pagos numerados, reloj y cliente de pey paginado (F2)`.

---

## Fase 3 (F3): Historia 1 — Cobrar con un QR (P1) · Corte M0 🎯 MVP · 15 nov, mañana

**Objetivo**: el negocio pide un cobro de monto fijo y recibe su QR CoDi creado con pey, con validaciones y errores claros en español.

**Prueba independiente**: crear un cobro de $0.01 y escanear el QR desde la app de un banco con CoDi; la app muestra el monto y el concepto.

### Pruebas de la historia 1 (primero, deben fallar antes de implementar)

- [X] T018 [US1] Escribir las pruebas de creación y validación en `backend/tests/test_crear_cobro.py` según [crear-cobro](contracts/crear-cobro.md)
  - `test_crear_cobro_pide_el_qr_a_pey_con_vigencia_de_10_minutos_y_el_id_del_cobro`: la petición a pey lleva `amount: 0.01`, `concept: "Tacos"`, `expiration: 600`, `numRef` que cumple `^[0-9]{1,7}$`, `generateImage: true` y `metadata: {"cobroId": <id>}`; la respuesta es 201 y nunca incluye `metadata`.
  - `test_el_cobro_devuelve_todos_sus_campos`: los 15 campos del objeto cobro; `id` de 12 caracteres URL-safe; `estado: "pendiente"`; `expira_en == creado_en + 600`; `fin_ventana == expira_en` (gracia 0 en M0); `numero_de_pagos: 0`, `total_recibido: 0`, `pagado_en: null`, `pagos: []`.
  - `test_montos_no_validos_se_rechazan_sin_llamar_a_pey` (parametrizada): negativo, `0.001`, `"abc"`, `100.01` y, **en el corte M0**, `0`, `null` y ausente. 422 con "Escribe un monto mayor a $0 con máximo 2 decimales" o "El monto máximo de la demo es $100"; el pey simulado no recibe nada.
  - `test_el_concepto_se_limpia_y_usa_cobro_por_defecto`: `"  Tacos  "` → `"Tacos"`; ausente, `""` o solo espacios → `"Cobro"`; 41 caracteres → 422 "El concepto puede tener máximo 40 letras".
  - `test_un_concepto_con_caracteres_no_imprimibles_se_rechaza`: `"Tacos\n"` y `"Ta\x00cos"` → 422 "El concepto tiene caracteres no válidos", sin llamar a pey.
  - `test_crear_un_cobro_deja_una_linea_en_el_registro`: una línea `INFO` con el id del cobro, el `codi_qr_id` y el `requestId` si pey lo mandó (QT-4).
  - **RF**: RF-001, RF-002, RF-004, RF-005, RF-006, RF-007, RF-008, RF-039, RF-042
  - **Dep.**: T017
  - **Hecho cuando**: las pruebas existen y fallan por la razón esperada (mensajes, campos, validaciones o registro que faltan).
- [X] T019 [US1] Escribir las pruebas de fallas de pey al crear en `backend/tests/test_crear_cobro.py`
  - `test_si_pey_falla_el_cobro_no_se_guarda_y_el_mensaje_dice_la_causa` (parametrizada): sin llave → 503 "El servidor no tiene configurada la llave de pey"; 401 y 403 → 502 "pey rechazó la llave del servidor"; 503 → 503 "pey está en mantenimiento. Intenta de nuevo en unos minutos."; 500 y sin conexión → 502 "No se pudo crear el cobro con pey. Intenta de nuevo.". En todos, `GET /api/cobros/{id}` del cobro intentado no existe (RF-009).
  - `test_si_pey_tarda_mas_de_10_segundos_al_crear_responde_intenta_de_nuevo`: el pey simulado lanza `httpx.ReadTimeout` → 502 "No se pudo crear el cobro con pey. Intenta de nuevo.".
  - **RF**: RF-009, RF-010 (QP-1)
  - **Dep.**: T018 (mismo archivo)
  - **Hecho cuando**: las pruebas existen y fallan por la razón esperada.

### Implementación de la historia 1

- [X] T020 [US1] Implementar `POST /api/cobros` según el contrato en `backend/app/main.py`
  - Validación con `Decimal`: monto fijo `0 < monto ≤ MONTO_MAXIMO` con máximo 2 decimales; en el corte M0, `0`, `null` o ausente se rechazan con el mismo mensaje. Concepto: espacios sobrantes quitados, "Cobro" si falta o queda vacío, "1 a 40 caracteres imprimibles". Mensajes exactos del contrato.
  - Las peticiones rechazadas con 422 no cuentan para el límite de 10 por minuto: el límite se aplica después de validar y antes de llamar a pey.
  - `id = secrets.token_urlsafe(9)` (12 caracteres); `num_ref` de 7 dígitos aleatorios; petición a pey con `amount`, `concept`, `expiration: 600`, `numRef`, `generateImage: true` y `metadata: {"cobroId": id}`.
  - Errores de pey traducidos a 502/503 con los mensajes del contrato; el cobro solo se guarda si pey respondió bien.
  - Registro (QT-4): una línea `INFO` por cada QR creado (id del cobro, `codi_qr_id` y `requestId` si pey lo mandó) y una por cada error de pey con su `requestId`.
  - **RF**: RF-001, RF-002, RF-004, RF-005, RF-006, RF-007, RF-008, RF-009, RF-010, RF-039, RF-042
  - **Dep.**: T016, T018, T019
  - **Hecho cuando**: las pruebas de T018 y T019 pasan y todo `pytest -q` sigue en verde.
- [X] T021 [US1] Cierre de F3: pruebas en verde, sección F3 en `verification-guide.md` (con la medición del QR con imagen) y commit sugerido
  - Paso manual para Hugo: crear un cobro **real** de $0.01 con `curl -s -w '\n%{time_total}\n' -X POST http://localhost:8000/api/cobros -H 'Content-Type: application/json' -d '{"monto": 0.01, "concepto": "Prueba"}'` y anotar el tiempo. Crearlo no mueve dinero. Si pasa de 3 s, se anota un TK en §14 del plan y la decisión pasa a #64 (QP-3, DP-15).
  - **RF**: CE-002
  - Commit sugerido: `feat(001): crear cobro CoDi de monto fijo con pey (F3)`.

**Punto de control**: la historia 1 funciona y se puede demostrar sola.

---

## Fase 4 (F4): Historias 2 y 3 — Saber que me pagaron y no perder un pago (P1) · Corte M0 · 15 nov, mañana

**Objetivo**: cada pago se registra una sola vez, por el aviso firmado de pey o por la consulta de respaldo, se numera si el QR se reutiliza (C-1) y llega a la pantalla por el canal de avisos, incluso sin aviso de pey (consulta automática cada 5 s).

**Prueba independiente**: con el canal abierto y sin aviso de pey, el pago aparece en el canal sin que la pantalla consulte nada; con un aviso firmado, aparece de inmediato; un segundo pago al mismo QR llega como pago 2.

### Pruebas de las historias 2 y 3 (primero, deben fallar antes de implementar)

- [X] T022 [P] [US2] Escribir las pruebas del aviso de pey en `backend/tests/test_aviso_pey.py` según [aviso-pey](contracts/aviso-pey.md)
  - `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada` (parametrizada): sin cabeceras, firmado con otro secreto y firmado con una hora de hace 6 minutos → 401 "Firma no válida"; el cobro sigue *pendiente* y el `webhook-id` no queda marcado.
  - `test_un_aviso_valido_registra_el_pago_y_pasa_el_cobro_a_pagado`: 200 `{"recibido": true, "procesado": true}`; el cobro queda *pagado* con un pago `numero: 1`, `monto_recibido` = `amount`, `pagado_en` = `datePaid`.
  - `test_un_aviso_de_otro_tipo_se_ignora`: 200 `procesado: false`, sin cambios.
  - `test_un_aviso_de_un_cobro_desconocido_responde_bien_y_se_ignora`: 200 `procesado: false` y queda registro.
  - `test_un_aviso_reenviado_no_registra_el_pago_dos_veces`: mismo `webhook-id`, y también otro `webhook-id` con el mismo `transactionId` → `procesado: false`; un solo pago.
  - `test_un_qr_reutilizado_registra_y_numera_cada_pago` (parte de integración, C-1): dos avisos con `transactionId` distintos al mismo QR → los dos `procesado: true`; `GET /api/cobros/{id}` con `numero_de_pagos: 2` y el total correcto.
  - `test_un_aviso_despues_de_la_ventana_registra_el_pago` (QT-5): con el reloj después de `fin_ventana`, un aviso válido → `procesado: true` y el cobro queda *pagado*, aunque ya no haya canal ni consulta.
  - `test_un_aviso_con_datos_no_validos_responde_400_y_se_acepta_en_el_reintento` y `test_un_aviso_que_falla_al_procesarse_se_acepta_en_el_reintento`: cuerpo no JSON o `amount` ilegible → 400 "Aviso con datos no válidos" sin marcar el `webhook-id`; el reintento válido con el mismo `webhook-id` se procesa (R-8, DP-10).
  - `test_sin_secreto_configurado_todo_aviso_se_rechaza`: con `PEY_WEBHOOK_SECRET` vacío → 503 "El aviso de pey todavía no está configurado".
  - `test_el_aviso_de_pey_no_hace_peticiones_a_pey`: durante un aviso válido, el pey simulado no recibe ninguna petición (CE-010 por estructura, QP-6).
  - **RF**: RF-011, RF-012, RF-013, RF-014, RF-015, RF-016, RF-017, RF-018, RF-032, RF-037, RF-039; CE-004, CE-005, CE-006, CE-010
  - **Dep.**: T021
  - **Hecho cuando**: las pruebas existen y fallan por la razón esperada (formato de respuesta, 400, R-8 o QR reutilizado).
- [X] T023 [P] [US3] Escribir las pruebas de la consulta de respaldo y de ver un cobro en `backend/tests/test_respaldo.py` según [ver-cobro](contracts/ver-cobro.md)
  - Unitarias de `ConsultaDeRespaldo(cliente_pey, repositorio, difusor, reloj)`: respeta el intervalo mínimo por cobro (3 s y 5 s, compartido entre llamadas); registra con `registrar_pago` y publica el evento `pago` con `{"pago": ..., "cobro": ...}`; fuera de la ventana de escucha no consulta; si pey lanza `ErrorPey` o se agota el tiempo, no lanza nada y deja un `WARNING`.
  - `test_cada_consulta_a_pey_deja_una_linea_en_el_registro` (QT-4): cada consulta, aunque no traiga pagos nuevos, deja una línea `INFO` con el id del cobro, las páginas pedidas, los pagos nuevos y el `requestId` si pey lo mandó.
  - `test_ver_el_cobro_consulta_a_pey_como_maximo_cada_3_segundos`: tres `GET /api/cobros/{id}` seguidos hacen una sola consulta; tras `reloj.avanzar(3)`, otra.
  - `test_si_pey_no_responde_se_devuelve_el_ultimo_estado`: pey con error 500 o tiempo agotado → 200 con el estado anterior, nunca 5xx.
  - `test_el_mismo_pago_no_se_registra_dos_veces_por_aviso_ni_por_consulta`: un pago llegado por aviso y luego encontrado en la consulta queda una sola vez, y el evento `pago` se publica una sola vez.
  - `test_un_cobro_que_no_existe_da_404`: "Ese cobro no existe".
  - **RF**: RF-014, RF-025, RF-026, RF-027, RF-029, RF-039; CE-005
  - **Dep.**: T021
  - **Hecho cuando**: las pruebas existen y fallan porque `app.respaldo` no existe o la ruta no se comporta así.
- [X] T024 [P] [US2] Escribir las pruebas del canal de avisos en `backend/tests/test_canal.py` según [canal-avisos](contracts/canal-avisos.md)
  - Pruebas `@pytest.mark.asyncio` sobre `flujo_de_avisos` con `RelojFalso` y pey simulado (DP-2):
    - `test_el_canal_emite_el_estado_al_abrirse`: primero `retry: 3000` y luego `event: estado` con el objeto cobro; con un cobro que ya tiene pagos, `numero_de_pagos` y `total_recibido` correctos.
    - `test_el_canal_avisa_el_pago_en_cuanto_se_registra`: al publicar un pago en el `Difusor`, el siguiente evento es `pago` con `{"pago": {"numero": 1, ...}, "cobro": {...}}`, sin avanzar el reloj (CE-003).
    - `test_el_canal_avisa_cada_pago_con_su_numero_y_el_total` (C-1): dos pagos al mismo QR → dos eventos `pago` con `numero` 1 y 2 y el `total_recibido` correcto (CE-006).
    - `test_el_canal_avisa_vencido_en_menos_de_15_segundos`: con gracia 600, el evento `vencido` sale con el reloj en `expira_en` + menos de 15 s.
    - `test_con_gracia_0_el_canal_emite_vencido_y_luego_fin` (QT-6): con `expira_en == fin_ventana`, los dos últimos eventos son `vencido` y `fin`, en ese orden, y el generador termina.
    - `test_el_canal_emite_fin_y_se_cierra_al_terminar_la_ventana`: en `fin_ventana` sale `event: fin` y el generador termina.
    - `test_el_canal_manda_senal_de_vida_cada_15_segundos`: `: sigo conectado` tras 15 s sin otros eventos.
  - Por HTTP: `test_abrir_el_canal_despues_de_la_ventana_emite_estado_y_fin` con `TestClient` (`GET /api/cobros/{id}/eventos` termina solo); 404 "Ese cobro no existe"; cabeceras `Cache-Control: no-cache` y `X-Accel-Buffering: no`.
  - La prueba repartida `test_eventos_emite_pagado_si_el_cobro_ya_se_pago` se reemplaza por estas (el evento `pagado` ya no existe).
  - **RF**: RF-015, RF-016, RF-028, RF-029, RF-030, RF-031, RF-032, RF-033, RF-043; CE-003, CE-006
  - **Dep.**: T021
  - **Hecho cuando**: las pruebas existen y fallan porque `app.canal` no existe.
- [X] T025 [US3] Escribir las pruebas de la consulta automática del canal en `backend/tests/test_canal.py`
  - `test_con_el_canal_abierto_el_servidor_pregunta_a_pey_cada_5_segundos`: sin aviso de pey, el pey simulado empieza a reportar un `PAID` en `t`; el canal emite `pago` con el reloj en `t + 5` o antes, sin ninguna consulta de la pantalla (CE-008). Dos canales del mismo cobro comparten el límite: una consulta cada 5 s, no dos.
  - `test_sin_secreto_el_canal_avisa_el_pago_por_la_consulta` (QT-5): con `PEY_WEBHOOK_SECRET` vacío, el canal abierto emite `pago` gracias a la consulta automática.
  - `test_una_consulta_lenta_no_deja_mudo_el_canal`: con la consulta agotando su tiempo de 4 s, la señal de vida y `vencido` siguen saliendo dentro de sus plazos (QP-1).
  - **RF**: RF-027, RF-030, RF-033, RF-037, RF-040; CE-008
  - **Dep.**: T024 (mismo archivo)
  - **Hecho cuando**: las pruebas existen y fallan.

### Implementación de las historias 2 y 3

- [X] T026 [US3] Implementar `ConsultaDeRespaldo` en `backend/app/respaldo.py` (archivo nuevo)
  - `ConsultaDeRespaldo(cliente_pey, repositorio, difusor, reloj)`.
  - `async consultar(cobro, intervalo_minimo: float) -> None`: si `cobro.en_ventana(ahora)` y pasaron `intervalo_minimo` segundos desde `ultima_consulta_pey`, actualiza esa hora, llama a `pagos_del_qr(codi_qr_id, vistas)` y pasa cada `PagoPey` nuevo por `registrar_y_avisar`; deja una línea `INFO` por consulta con el id del cobro, las páginas pedidas, los pagos nuevos y el `requestId` si pey lo mandó (QT-4); ante `ErrorPey`, deja un `WARNING` con el id del cobro y el `requestId`, sin lanzar (RF-027).
  - `registrar_y_avisar(cobro, transaccion_id, monto_recibido, monto_base, pagado_en, fuente) -> Pago | None`: llama a `registrar_pago`; si hay pago nuevo, deja un `INFO` y publica `pago` con `{"pago": pago.publico(), "cobro": cobro.publico()}`.
  - **RF**: RF-014, RF-025, RF-026, RF-027, RF-029, RF-039, RF-040 (QP-7, DP-14)
  - **Dep.**: T016, T023
  - **Hecho cuando**: las pruebas unitarias de `ConsultaDeRespaldo` y la de registro de T023 pasan.
- [X] T027 [US2] Implementar `POST /webhooks/pey` según el contrato en `backend/app/main.py`
  - Orden: sin secreto → 503; `standardwebhooks.Webhook(secreto).verify(cuerpo_exacto, cabeceras)` antes de leer el JSON → 401; `webhook-id` ya visto → 200 `procesado: false`; tipo distinto de `codi.qr.payment_received` → 200 `procesado: false`; cuerpo ilegible o `amount` no numérico → 400 sin marcar el `webhook-id`; `codiQrId` desconocido → 200 `procesado: false` con registro; si no, `registrar_y_avisar(..., fuente="aviso")`, también fuera de la ventana de escucha y también si el cobro ya tenía pagos (pago siguiente, C-1).
  - El `webhook-id` se marca como visto **después** de procesar (DP-10). Sin llamadas de red.
  - **RF**: RF-011, RF-012, RF-013, RF-014, RF-015, RF-016, RF-017, RF-018, RF-037, RF-039; CE-010
  - **Dep.**: T022, T026
  - **Hecho cuando**: las pruebas de T022 pasan.
- [X] T028 [US3] Usar `ConsultaDeRespaldo` en `GET /api/cobros/{id}` en `backend/app/main.py`
  - Antes de responder, `await consulta.consultar(cobro, intervalo_minimo=3)`; 404 "Ese cobro no existe"; nunca 5xx por la consulta. Se quita la consulta que el prototipo tenía dentro de `crear_app`.
  - **RF**: RF-025, RF-026, RF-027
  - **Dep.**: T023, T026, T027 (mismo archivo)
  - **Hecho cuando**: todas las pruebas de T023 pasan.
- [X] T029 [US2] Implementar `flujo_de_avisos` en `backend/app/canal.py` (archivo nuevo)
  - Generador asíncrono que sigue el [ciclo del servidor](contracts/canal-avisos.md#ciclo-del-servidor): `retry: 3000`; `estado`; si `ahora ≥ fin_ventana`, `fin` y termina (RF-043); si no, en cada vuelta espera eventos del `Difusor` con un tiempo límite igual al menor de 5 s, lo que falta para `expira_en` y lo que falta para `fin_ventana`; reenvía cada `pago`; emite `vencido` una vez al pasar a ese estado; si pasaron 5 s, `consulta.consultar(cobro, intervalo_minimo=5)`; tras 15 s sin enviar nada, `: sigo conectado`; al terminar la ventana, `fin`.
  - Si el cobro vence en el mismo instante en que termina la ventana (gracia 0), emite primero `vencido` y después `fin` (QT-6).
  - Recibe el cobro, el difusor, la consulta y el reloj ya creados; cancela su suscripción al `Difusor` al terminar o desconectarse (`finally`).
  - **RF**: RF-028, RF-029, RF-030, RF-031, RF-032, RF-033, RF-040, RF-043 (DP-5, DP-6)
  - **Dep.**: T024, T025, T026
  - **Hecho cuando**: las pruebas asíncronas de T024 y T025 pasan.
- [X] T030 [US2] Servir el canal en `GET /api/cobros/{id}/eventos` en `backend/app/main.py`
  - `StreamingResponse(flujo_de_avisos(...), media_type="text/event-stream")` con `Cache-Control: no-cache` y `X-Accel-Buffering: no`; 404 "Ese cobro no existe"; se detiene al desconectarse la pantalla.
  - **RF**: RF-028, RF-032, RF-043
  - **Dep.**: T028, T029
  - **Hecho cuando**: todas las pruebas de T022 a T025 pasan y todo `pytest -q` sigue en verde.
- [X] T031 [US2] Cierre de F4: pruebas en verde, sección F4 en `verification-guide.md` y commit sugerido
  - La guía incluye: abrir el canal con `curl -N` sobre un cobro de prueba y ver `estado`, la señal de vida, `vencido` y `fin`; dónde se lee en las pruebas que un aviso sin firma no cambia nada (para la revisión de Altairtm).
  - Commit sugerido: `feat(001): aviso de pey firmado, QR reutilizado, consulta de respaldo y canal de avisos (F4)`.

**Punto de control**: las historias 1, 2 y 3 del corte M0 funcionan juntas.

---

## Fase 5 (F5): Historias 5 y 6 — Demo protegida y salud (P2, P3) · Corte M0 · 15 nov, antes de las 10:00

**Objetivo**: la demo pública no se puede abusar (IP real, 10 cobros por minuto, 10 canales, CORS), `/salud` dice qué falta sin mostrar secretos, los registros cuentan lo que pasa y el README tiene el contrato nuevo. **Cierra el corte M0** con la revisión de seguridad y los pagos reales de $0.01.

**Prueba independiente**: 11 cobros seguidos desde una IP → el 11.º se rechaza sin llamar a pey; `/salud` sin el secreto dice `secreto_aviso_pey: false`.

### Pruebas de las historias 5 y 6 (primero, deben fallar antes de implementar)

- [X] T032 [P] [US5] Escribir las pruebas de protección en `backend/tests/test_proteccion.py`
  - `test_limite_de_cobros_por_ip`: 10 cobros válidos pasan; el 11.º → 429 "Demasiados cobros seguidos. Espera un minuto." sin llamar a pey; tras `reloj.avanzar(60)`, vuelve a pasar; los 422 no cuentan.
  - `test_el_limite_usa_la_ip_real_detras_del_proxy`: con `proxies_confiables="testclient"` (la dirección con la que se conecta `TestClient`; el valor por defecto `127.0.0.1` no la incluye), dos valores distintos de `X-Forwarded-For` tienen límites separados; con el valor por defecto, la cabecera se ignora.
  - `test_una_ip_no_puede_abrir_mas_de_10_canales`: con 10 lugares ocupados en `LimiteDeCanales` para una IP, `GET /api/cobros/{id}/eventos` → 429 "Tienes demasiadas pantallas abiertas. Cierra otras e intenta de nuevo."; al liberar uno, se abre; prueba unitaria de `ocupar` y `liberar`.
  - `test_cors_solo_permite_los_origenes_configurados`: un `Origin` de `WEB_ORIGIN` recibe `Access-Control-Allow-Origin`; otro no; métodos permitidos solo `GET` y `POST`.
  - **RF**: RF-034, RF-035, RF-041 (DP-7, R-5)
  - **Dep.**: T031
  - **Hecho cuando**: las pruebas existen y fallan (IP real, límite de canales o reloj en el límite).
- [X] T033 [P] [US6] Escribir las pruebas de salud, secretos y registros en `backend/tests/test_salud_y_registros.py` según [salud](contracts/salud.md)
  - `test_salud_dice_que_credenciales_faltan_sin_mostrarlas`: con llave y sin secreto → `{"estado": "ok", "llave_pey": true, "secreto_aviso_pey": false}`; reemplaza la prueba repartida `test_salud`.
  - `test_la_llave_y_el_secreto_no_aparecen_en_respuestas_ni_registros`: recorre todas las rutas, incluidos los errores (pey 401, aviso con firma mala, validación), y busca los valores falsos de `conftest.py` en cada cuerpo, cabecera y en todo `caplog`; no aparecen.
  - `test_los_registros_dejan_cobro_error_de_pey_pago_y_aviso_ignorado`: hay una línea por cobro creado (id, `codi_qr_id` y `requestId` si vino), por consulta a pey (QT-4), por error de pey (con `requestId`), por pago registrado (id, `transactionId`, número y fuente) y por aviso ignorado o rechazado.
  - **RF**: RF-036, RF-038, RF-039; CE-009
  - **Dep.**: T031
  - **Hecho cuando**: las pruebas existen y fallan (nombres de `/salud` o registros que faltan).

### Implementación de las historias 5 y 6

- [X] T034 [US5] Agregar `LimiteDeCanales` y el reloj a `LimitePorIp` en `backend/app/eventos.py`
  - `LimitePorIp(maximo_por_minuto, reloj)`: ventana deslizante de 60 s con `reloj.ahora()`.
  - `LimiteDeCanales(maximo)`: `ocupar(ip) -> bool` y `liberar(ip)`, contados mientras el canal está abierto.
  - **RF**: RF-034, RF-041
  - **Dep.**: T032
  - **Hecho cuando**: las pruebas unitarias de T032 pasan.
- [X] T035 [US5] Agregar IP real, CORS y límite de canales en `backend/app/main.py`
  - `ProxyHeadersMiddleware(app, trusted_hosts=configuracion.proxies_confiables)` de uvicorn; la IP del cliente sale de `request.client.host` ya corregida.
  - `CORSMiddleware` con los orígenes de `WEB_ORIGIN` y métodos `GET` y `POST`.
  - En la ruta del canal: `ocupar` antes de abrir (429 si no hay lugar) y `liberar` en un `finally` al terminar o desconectarse.
  - **RF**: RF-034, RF-035, RF-041
  - **Dep.**: T030, T034
  - **Hecho cuando**: todas las pruebas de T032 pasan.
- [X] T036 [US6] Ajustar `/salud` y completar los registros en `backend/app/main.py`
  - `/salud` → `{"estado": "ok", "llave_pey": bool, "secreto_aviso_pey": bool}`, sin valores.
  - Registros que faltan según T033; nunca cabeceras, cuerpos completos, llaves, secretos ni datos bancarios.
  - **RF**: RF-036, RF-038, RF-039
  - **Dep.**: T033, T035 (mismo archivo)
  - **Hecho cuando**: todas las pruebas de T033 pasan y todo `pytest -q` sigue en verde.
- [X] T037 [P] [US5] Reescribir `backend/README.md` con el contrato nuevo (QP-4)
  - Enlace a `specs/001-backend-mvp/contracts/` como fuente; objeto cobro en `snake_case` con `pagos` numerados; eventos `estado`, `pago`, `vencido` y `fin` (la web llama a `close()` al recibir `fin`); arranque con un solo comando; variables de entorno (sin valores de secretos); un solo *worker*. Sin `codiQrId` ni el evento `pagado`.
  - **RF**: RF-008, RF-015, RF-029, RF-031, RF-032
  - **Dep.**: T030
  - **Hecho cuando**: `grep -n "codiQrId\|pagado\b" backend/README.md` no encuentra el contrato viejo (solo los nombres que impone pey, si se citan como tales).
- [X] T038 [US5] Escribir la sección F5 de `verification-guide.md` con la revisión de seguridad y las comprobaciones manuales del corte M0
  - **Revisión de seguridad del corte M0** (QT-7), con su resultado anotado: secretos solo en `backend/.env` o el hosting; firma del aviso verificada antes de leer el JSON; entradas validadas en el servidor; CORS solo para `WEB_ORIGIN`; 10 cobros por minuto y 10 canales por IP real; `PROXIES_CONFIABLES` en el hosting distinto de `*`, salvo que el hosting no permita conexiones directas; un solo *worker* (quickstart §7).
  - CE-009: `git grep -nE "whsec_[A-Za-z0-9+/=]{16,}|Bearer [A-Za-z0-9._-]{16,}" -- ':!backend/tests'` sin abrir `backend/.env`; esperado: nada. Además, comprobar que `backend/tests/` solo contiene los valores falsos de `conftest.py`.
  - CE-010: `curl -s -o /dev/null -w '%{time_total}'` a `POST /webhooks/pey` con un aviso sin firma; esperado: menos de 1 s.
  - CE-008, CE-006 y CE-001 (local), con autorización de Hugo en ese momento: crear un cobro real de $0.01, abrir el canal con `curl -N` y pagarlo desde la app del banco en la opción CoDi; esperado: `event: pago` con `numero: 1` en menos de 5 s después de que pey lo registra, sin aviso de pey configurado. Pagar **otra vez el mismo QR** ($0.01 más); esperado: `event: pago` con `numero: 2` y `total_recibido: 0.02` (C-1, QT-2). Cuando estén #65 y #64, repetir desde la URL pública (CE-001) y con el aviso real (CE-003, menos de 2 s).
  - IP real en el despliegue: dos redes distintas tienen límites separados (quickstart §7, paso 5).
  - **RF**: RF-011, RF-015, RF-034, RF-035, RF-036, RF-041; CE-001, CE-003, CE-006, CE-008, CE-009, CE-010
  - **Dep.**: T036, T037
  - **Hecho cuando**: la sección existe, cada punto de seguridad tiene su resultado y Hugo puede seguirla sin otra explicación.
- [X] T039 [US5] Cierre de F5 y del corte M0: pruebas en verde, sección F5 completa en `verification-guide.md` y commit sugerido
  - Hugo hace los dos pagos reales de $0.01 (T038) cuando CoDi esté activo; si no lo está a las 10:00, se anota en Estado y se sigue el riesgo de §11 del plan.
  - **RF**: CE-001
  - Commit sugerido: `feat(001): proteger la demo, salud y registros; cierre del corte M0 (F5)`.

**Punto de control**: el corte M0 está completo y listo para desplegarse (#65).

---

## Fase 6 (F6): Historia 3 — Ventana de gracia para pagos tardíos (P1) · Corte 2 · 16–18 nov

**Objetivo**: durante los 10 minutos posteriores al vencimiento, el sistema sigue detectando y avisando pagos.

**Prueba independiente**: un pago que llega 5 minutos después del vencimiento se avisa por el canal, que sigue abierto (CE-007).

- [X] T040 [US3] Escribir las pruebas de la gracia en `backend/tests/test_canal.py`, `backend/tests/test_respaldo.py` y `backend/tests/test_salud_y_registros.py`
  - `test_un_pago_5_minutos_despues_de_vencer_se_avisa_por_el_canal` (`test_canal.py`): con la gracia por defecto, el canal emite `vencido`, sigue abierto y en `expira_en + 300` emite `pago`; el cobro pasa a *pagado*.
  - `test_despues_de_la_gracia_ya_no_se_consulta_a_pey` (`test_respaldo.py`): en `expira_en + 600` ver el cobro no consulta a pey; abrir el canal emite `estado` y `fin` y cierra.
  - En `test_la_configuracion_tiene_los_valores_por_defecto_del_plan`, `gracia_segundos == 600`.
  - **RF**: RF-022, RF-025, RF-032, RF-043; CE-007
  - **Dep.**: T039
  - **Hecho cuando**: las pruebas fallan con la gracia en 0.
- [X] T041 [US3] Cambiar el valor por defecto de `GRACIA_SEGUNDOS` a 600 en `backend/app/config.py` y `backend/.env.example`
  - Sin cambios de lógica (DP-12).
  - **RF**: RF-022
  - **Dep.**: T040
  - **Hecho cuando**: las pruebas de T040 pasan y todo `pytest -q` sigue en verde.
- [X] T042 [US3] Cierre de F6: pruebas en verde, sección F6 en `verification-guide.md` con un pago real y commit sugerido
  - Pago real (QT-2), con autorización de Hugo en ese momento: crear un cobro de $0.01, dejarlo vencer, abrir el canal y pagarlo unos 5 minutos después del vencimiento; esperado: `event: pago` con el cobro *pagado*. Si el banco no deja pagar un QR vencido, se anota (pregunta abierta para pey, §8.5 de la spec).
  - **RF**: RF-022; CE-007
  - Commit sugerido: `feat(001): ventana de gracia de 10 minutos para pagos tardíos (F6)`.

---

## Fase 7 (F7): Historia 1 — Monto libre (P1) · Corte 2 · 18–19 nov

**Objetivo**: un cobro sin monto o con monto 0 crea un QR en el que el cliente escribe la cantidad.

**Prueba independiente**: crear un cobro sin monto y escanearlo; el banco pide escribir la cantidad.

- [X] T043 [US1] Escribir la prueba de monto libre en `backend/tests/test_crear_cobro.py`
  - `test_monto_vacio_o_cero_crea_un_cobro_de_monto_libre` (parametrizada: ausente, `null`, `0`): 201 con `monto: null` y `monto_libre: true`; la petición a pey lleva `amount: 0`; un pago de cualquier monto tiene `monto_distinto: false`.
  - Se quitan `0`, `null` y ausente de los casos de `test_montos_no_validos_se_rechazan_sin_llamar_a_pey`.
  - **RF**: RF-003, RF-019
  - **Dep.**: T039
  - **Hecho cuando**: la prueba falla con 422.
- [X] T044 [US1] Aceptar el monto libre en `backend/app/main.py` y `backend/app/cobros.py`
  - `monto` vacío o 0 → cobro con `monto = None`; `amount: 0` en la petición a pey.
  - **RF**: RF-003
  - **Dep.**: T043
  - **Hecho cuando**: la prueba de T043 pasa y todo `pytest -q` sigue en verde.
- [X] T045 [US1] Cierre de F7: pruebas en verde, sección F7 en `verification-guide.md` con un pago real y commit sugerido
  - Pago real (QT-2), con autorización de Hugo en ese momento: crear un cobro libre, escanearlo y escribir $0.01 en el banco; esperado: `event: pago` con `monto_recibido: 0.01` y el cobro con `monto_libre: true`.
  - **RF**: RF-003
  - Commit sugerido: `feat(001): cobro de monto libre (F7)`.

---

## Fase 8 (F8): Historia 4 — Cancelar un cobro equivocado (P2) · Corte 2 · 19–20 nov

**Objetivo**: el negocio cancela un cobro *pendiente*; si después se paga, el pago se registra y se avisa igual.

**Prueba independiente**: crear, cancelar y comprobar *cancelado*; luego un aviso de pago lo pasa a *pagado*.

- [X] T046 [P] [US4] Escribir las pruebas de cancelación en `backend/tests/test_cancelar_cobro.py` (archivo nuevo) según [cancelar-cobro](contracts/cancelar-cobro.md)
  - `test_cancelar_un_cobro_pendiente`: 200 con `estado: "cancelado"` y una línea de registro con el id del cobro.
  - `test_no_se_puede_cancelar_un_cobro_pagado_o_vencido` (parametrizada: *pagado*, *vencido* y ya *cancelado*): 409 "Solo se puede cancelar un cobro que todavía no se paga ni vence".
  - `test_un_cobro_cancelado_que_se_paga_pasa_a_pagado`: aviso válido después de cancelar → *pagado* y `procesado: true`.
  - `test_cancelar_un_cobro_que_no_existe_da_404`: "Ese cobro no existe".
  - Archivo ya listado en el plan §3.2 (errata 5 de la QA de tasks).
  - **RF**: RF-017, RF-023, RF-024, RF-039
  - **Dep.**: T039
  - **Hecho cuando**: las pruebas fallan con 404 o 405.
- [X] T047 [P] [US4] Escribir la prueba del evento `cancelado` en `backend/tests/test_canal.py`
  - `test_el_canal_avisa_cancelado_en_menos_de_15_segundos`: al publicar la cancelación, el canal emite `cancelado` con el objeto cobro antes de avanzar 15 s.
  - **RF**: RF-030
  - **Dep.**: T039
  - **Hecho cuando**: la prueba falla.
- [X] T048 [US4] Implementar la cancelación en `backend/app/cobros.py` y `POST /api/cobros/{id}/cancelar` en `backend/app/main.py`
  - `RepositorioCobros.cancelar(cobro, ahora)`: solo si `estado(ahora) == "pendiente"`, guarda `cancelado_en`; si no, error que la ruta traduce a 409. La ruta publica `cancelado` en el `Difusor` y deja una línea de registro.
  - **RF**: RF-023, RF-024, RF-039
  - **Dep.**: T046
  - **Hecho cuando**: las pruebas de T046 pasan.
- [X] T049 [US4] Reenviar el evento `cancelado` en `backend/app/canal.py`
  - **RF**: RF-030
  - **Dep.**: T047, T048
  - **Hecho cuando**: la prueba de T047 pasa y todo `pytest -q` sigue en verde.
- [X] T050 [US4] Cierre de F8: pruebas en verde, sección F8 en `verification-guide.md` con un pago real y commit sugerido
  - Pago real (QT-2), con autorización de Hugo en ese momento: crear un cobro de $0.01, cancelarlo y después pagarlo desde el banco; esperado: el canal emite `cancelado` y luego `pago`, y el cobro queda *pagado*.
  - **RF**: RF-017, RF-023
  - Commit sugerido: `feat(001): cancelar un cobro pendiente (F8)`.

---

## Fase N (FN): Pulido y temas transversales · 21 nov

- [X] T051 [P] Actualizar `backend/README.md` con el corte 2: monto libre, cancelación, evento `cancelado` y `GRACIA_SEGUNDOS = 600`
  - **RF**: RF-003, RF-022, RF-023
  - **Dep.**: T042, T045, T050
  - **Hecho cuando**: cada ruta y evento de `contracts/` aparece en el README.
- [X] T052 [P] Repetir la revisión de seguridad para el corte 2 en la sección FN de `verification-guide.md`
  - La misma lista y el mismo `git grep` de T038, más la ruta de cancelar (solo `POST`, 404 y 409 sin datos de más).
  - **RF**: RF-011, RF-024, RF-034, RF-035, RF-036, RF-041; CE-009
  - **Dep.**: T042, T045, T050
  - **Hecho cuando**: cada punto tiene su resultado anotado.
- [X] T053 Validar `specs/001-backend-mvp/quickstart.md` de punta a punta y corregir lo que no coincida
  - **RF**: — (todas las historias)
  - **Dep.**: T051, T052
  - **Hecho cuando**: los pasos 1 a 7 del quickstart dan lo esperado; las diferencias se corrigen en el quickstart o se anotan como TK.
- [X] T054 Cierre de FN: pruebas en verde, sección FN completa en `verification-guide.md` y commit sugerido
  - Commit sugerido: `docs(001): pulido del corte 2 y quickstart validado (FN)`.

---

## Fase 9 (F9): Cambio C-2 — Hora actual del servidor en cada cobro · 15 nov

**Objetivo**: cada objeto cobro (crear, ver, cancelar y los eventos del canal) trae `hora_servidor`, para que la pantalla de la spec 002 calcule la cuenta regresiva sin depender del reloj del celular (spec 002, RF-019 y CE-016). Es la fase F0 del plan de la 002.

**Prueba independiente**: con el reloj falso, un cobro cuya creación tardó 9 s devuelve `creado_en = T` y `hora_servidor = T + 9`.

- [X] T055 [P] Escribir las pruebas de `hora_servidor` en `backend/tests/test_modelo.py`, `backend/tests/test_crear_cobro.py`, `backend/tests/test_canal.py` y `backend/tests/test_cancelar_cobro.py`
  - `test_modelo.py`: `CAMPOS_COBRO` suma `hora_servidor` (16 campos) en `test_el_objeto_publico_del_cobro_tiene_los_campos_del_contrato`; nueva `test_el_objeto_publico_trae_la_hora_actual_del_servidor_como_entero`: con `RelojFalso(1_794_700_009)`, `hora_servidor == 1_794_700_009`; tras `avanzar(5.7)`, `1_794_700_014`.
  - `test_crear_cobro.py`: `CAMPOS_COBRO` suma `hora_servidor`; nueva `test_crear_cobro_descuenta_lo_que_tardo_pey_en_la_hora_del_servidor`: el `PeySimulado` adelanta el reloj 9 s al responder `POST /codi/qr` (nuevo atributo `al_crear` en `backend/tests/conftest.py`) → `creado_en = T` y `hora_servidor = T + 9`; nueva `test_ver_cobro_trae_la_hora_actual_del_servidor`: tras `reloj.avanzar(30)`, `GET /api/cobros/{id}` trae `hora_servidor = T + 30`.
  - `test_canal.py`: nueva `test_los_eventos_del_canal_traen_la_hora_del_servidor`: el `estado` al abrir y el `fin` traen `hora_servidor` igual a la hora del reloj al emitirlos.
  - `test_cancelar_cobro.py`: nueva `test_cancelar_devuelve_la_hora_del_servidor`.
  - **RF**: RF-008 (C-2)
  - **Dep.**: T054
  - **Hecho cuando**: las pruebas existen y fallan porque el objeto cobro no trae `hora_servidor`.
- [X] T056 Agregar `hora_servidor` a `Cobro.publico()` en `backend/app/cobros.py` y al ejemplo del objeto cobro en `backend/README.md`
  - `"hora_servidor": int(self.reloj.ahora())`, con el docstring citando el C-2. Las rutas y el canal no cambian: todos usan `publico()` (TK-6 del plan).
  - **RF**: RF-008 (C-2)
  - **Dep.**: T055
  - **Hecho cuando**: las pruebas de T055 pasan y `uv run --directory backend pytest -q` queda en verde.
- [X] T057 Cierre de F9: pruebas en verde, sección F9 en `verification-guide.md` y commit sugerido
  - La guía dice cómo ver `hora_servidor` con `curl` en `POST /api/cobros`, `GET /api/cobros/{id}` y el canal, sin crear cobros reales (servidor en local sin llave, o con el pey simulado de las pruebas).
  - Commit sugerido: `feat(001): hora actual del servidor en cada cobro (C-2, F9)`.
  - **RF**: RF-008
  - **Dep.**: T056
  - **Hecho cuando**: los comandos de la regla 5 dan verde y la sección F9 existe.

---

## Dependencias y orden de ejecución

```text
F1 → F2 → F3 (H1, MVP) → F4 (H2 y H3) → F5 (H5 y H6) ═ corte M0
                                           │
                                           ├→ F6 (H3: gracia) ──────┐
                                           ├→ F7 (H1: monto libre) ─┼→ FN
                                           └→ F8 (H4: cancelar) ────┘
```

- **Corte M0** (F1 a F5): en orden estricto. F4 depende del cobro de F3; F5 depende del canal de F4. El QR reutilizado y el monto distinto ya no son una fase aparte: van en F2 (modelo) y F4 (aviso y canal), por el cambio C-1.
- **Corte 2**: F6, F7 y F8 dependen solo de F5. F7 y F8 tocan `main.py` y `cobros.py`, y F6 y F8 tocan `test_canal.py`: si las hacen personas distintas a la vez, se integran una después de la otra, en el orden F6 → F7 → F8.
- **FN** cierra después de F6 a F8.

### Tareas en paralelo dentro de cada fase

- **F1**: T002 y T003 (archivos de pruebas distintos); después T004 y T005.
- **F2**: T009, T011 y T013 a la vez; después T014 y T015 a la vez.
- **F3**: sin paralelo (un archivo de pruebas y `main.py`).
- **F4**: T022, T023 y T024 a la vez (tres archivos de pruebas). T026 y T029 tocan archivos distintos, pero T029 usa `ConsultaDeRespaldo`: primero T026.
- **F5**: T032 y T033 a la vez; T037 (README) en paralelo con T034 a T036.
- **F8**: T046 y T047 a la vez. **FN**: T051 y T052 a la vez.

## Estrategia

1. **MVP primero**: F1, F2 y F3, y se valida la historia 1 sola (crear un QR real de $0.01) antes de seguir.
2. **Lo que gana la demo del kickoff** va después: F4 (aviso, QR reutilizado, respaldo y canal) y F5 (protección, salud y seguridad). Si a las 10:00 del 15 nov F5 no está cerrada, se despliega el último cierre en verde y se avisa en el formulario (§11 del plan).
3. **Entrega incremental**: cada fase del corte 2 suma un comportamiento sin romper los anteriores; las pruebas temporales del corte M0 se reemplazan en la misma fase que cambia la regla (T040 para la gracia, T043 para el monto libre).

## Trazabilidad

| Requisito | Tareas |
|---|---|
| RF-001 | T018, T020 |
| RF-002 | T018, T020 |
| RF-003 | T043, T044, T045, T051 |
| RF-004 | T012, T016, T018, T020 |
| RF-005 | T018, T020 |
| RF-006 | T018, T020 |
| RF-007 | T018, T020 |
| RF-008 | T009, T012, T014, T016, T018, T020, T037, T055, T056, T057 |
| RF-009 | T019, T020 |
| RF-010 | T015, T019, T020 |
| RF-011 | T006, T022, T027, T038, T052 |
| RF-012 | T022, T027 |
| RF-013 | T022, T027 |
| RF-014 | T010, T014, T022, T023, T026, T027 |
| RF-015 | T010, T011, T014, T022, T024, T027, T037, T038 |
| RF-016 | T010, T014, T022, T024, T027 |
| RF-017 | T010, T014, T022, T027, T046, T050 |
| RF-018 | T009, T014, T022, T027 |
| RF-019 | T009, T010, T014, T043 |
| RF-020 | T010, T014 |
| RF-021 | T002, T009, T014 |
| RF-022 | T003, T005, T040, T041, T042, T051 |
| RF-023 | T046, T048, T050, T051 |
| RF-024 | T046, T048, T052 |
| RF-025 | T011, T015, T023, T026, T028, T040 |
| RF-026 | T023, T026, T028 |
| RF-027 | T011, T015, T023, T025, T026, T028 |
| RF-028 | T024, T029, T030 |
| RF-029 | T023, T024, T026, T029, T037 |
| RF-030 | T002, T024, T025, T029, T047, T049 |
| RF-031 | T024, T029, T037 |
| RF-032 | T009, T022, T024, T029, T030, T037, T040 |
| RF-033 | T024, T025, T029 |
| RF-034 | T002, T003, T005, T032, T034, T035, T038, T052 |
| RF-035 | T032, T035, T038, T052 |
| RF-036 | T033, T036, T038, T052 |
| RF-037 | T022, T025, T027 |
| RF-038 | T033, T036 |
| RF-039 | T013, T015, T016, T018, T020, T022, T023, T026, T027, T033, T036, T046, T048 |
| RF-040 | T002, T025, T026, T029 |
| RF-041 | T003, T005, T032, T034, T035, T038, T052 |
| RF-042 | T018, T020 |
| RF-043 | T024, T029, T030, T040 |
| CE-001 | T038, T039 |
| CE-002 | T021 |
| CE-003 | T024, T038 |
| CE-004 | T022 |
| CE-005 | T022, T023 |
| CE-006 | T010, T022, T024, T038 |
| CE-007 | T040, T042 |
| CE-008 | T025, T038 |
| CE-009 | T033, T038, T052 |
| CE-010 | T022, T027, T038 |

## Revisión QA de tasks

*2026-11-14, una sola pasada. Recoge los hallazgos de `/speckit-analyze` (D1–D4, G1, G2, A1, C1, U1, I1) más los de esta pasada. Los T### de las columnas "Hallazgo" y "Recomendación" son los del borrador; al aplicar C-1 las tareas se renumeraron, y la columna "Decisión" cita los números nuevos.*

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QT-1 | Contradicción | Constitución II: "Toda acción que dispare un pago (sonido, aviso…) DEBE colgar de esa única transición de *pendiente* a *pagado*". La spec avisa **cada** pago de un QR reutilizado (RF-015, RF-016, RF-029) y pasa a *pagado* también desde *vencido* y *cancelado* (RF-017). El plan lo resuelve con "una sola función de registro" (§2), pero el texto de la constitución no dice eso. | RF-015, RF-016, RF-017, RF-029 | Enmienda PATCH de la constitución, aparte y cuando Hugo la pida (`/speckit-constitution`): "DEBE colgar de la única puerta que registra cada pago". Las tareas no cambian. | **Enmienda PATCH de la constitución** (Hugo, 2026-11-14), como se recomienda: v1.0.1 con "la única puerta que registra cada pago", aparte y cuando Hugo pida `/speckit-constitution` (TK-3 del plan). Sin cambios en las tareas. |
| QT-2 | Contradicción | Constitución VI: "Toda funcionalidad de cobro DEBE demostrarse con un cobro CoDi real". Los cierres T043 (QR reutilizado), T046 (pago tardío) y T054 (pagar un cobro cancelado) no tienen pago real, y en T049 (monto libre) es opcional. | RF-003, RF-015, RF-022, RF-023; CE-006, CE-007 | Agregar a cada cierre del corte 2 un paso de pago real de $0.01, con la autorización de Hugo en ese momento. | **Pago real de $0.01 en cada cierre del corte 2** (Hugo, 2026-11-14), como se recomienda. Aplicada: segundo pago al mismo QR en T038 (el QR reutilizado pasó a M0 con C-1), pago tardío en T042, monto libre en T045 y QR cancelado en T050. |
| QT-3 | Contradicción | Constitución VIII: "si llega dinero de un cobro conocido, se registra… y se avisa". En el corte M0, el segundo pago a un QR solo quedaba como advertencia, sin aviso (spec §1.2, aceptado en QA-1). El plan decía "Sin excepciones a la constitución" (`plan.md:366`). | §1.2 de la spec; RF-015 | Registrar en el plan §12 la excepción temporal a VIII: la justifica QA-1, dura hasta F6 y la resuelve T042. | **Avisar todos los pagos desde el corte M0** (Hugo, 2026-11-14). Se aparta de la recomendación. Cambio **C-1** a la spec aprobado y aplicado por Hugo el 2026-11-14 (spec §8.2; plan TK-1): RF-015, RF-016, RF-019, RF-020 y CE-006 pasan a [M0]. La antigua F6 se reparte entre T010, T014 (F2) y T022, T024, T027 (F4); el corte 2 queda en F6 gracia, F7 monto libre y F8 cancelación. |
| QT-4 | Hueco | Constitución X: "Cada interacción con pey… DEBE dejar un registro con el identificador del cobro y el `requestId`". La consulta solo se registraba cuando fallaba o traía un pago nuevo: una consulta sin novedades (cada 5 s con un canal abierto) no dejaba rastro. El `requestId` solo se registraba en errores; el `openapi.json` de pey no lo documenta en las respuestas buenas. | RF-039 | Una línea `INFO` por cada consulta a pey (id del cobro, páginas pedidas, pagos nuevos) y por cada QR creado (id y `codi_qr_id`), con `requestId` cuando pey lo mande. | **Una línea `INFO` por cada consulta a pey y por cada QR creado** (Hugo, 2026-11-14), como se recomienda. Aplicada en T015, T018, T020, T023, T026 y T033; research R-9 y plan TK-2. |
| QT-5 | Caso límite | Dos casos de la spec §4 sin prueba: (a) "Pago después de la ventana de escucha": un aviso que llega después de `fin_ventana` se registra aunque el canal esté cerrado; (b) "Secreto del aviso sin configurar… el respaldo sigue detectando pagos" se probaba por partes, nunca junto. | RF-012, RF-032, RF-037, RF-040 | Agregar `test_un_aviso_despues_de_la_ventana_registra_el_pago` y `test_sin_secreto_el_canal_avisa_el_pago_por_la_consulta`. | **Agregar las dos pruebas** (Hugo, 2026-11-14), como se recomienda. Aplicada en T022 y T025; plan §7. |
| QT-6 | Caso límite | En el corte M0 la gracia es 0, así que `expira_en == fin_ventana`: el cobro vence y la ventana termina en el mismo instante. No se decía si el canal emite `vencido` y luego `fin`, o solo `fin`. La web (#64) cuenta con `vencido` para mostrar el QR como vencido. | RF-030, RF-032 | El canal emite `vencido` y después `fin` cuando coinciden. | **`vencido` y luego `fin`** (Hugo, 2026-11-14), como se recomienda. Aplicada en T024 y T029; contrato canal-avisos (paso 4 del ciclo) y plan TK-2. |
| QT-7 | Seguridad | La revisión de seguridad completa (firma, entradas, CORS, límites, `PROXIES_CONFIABLES`, un solo *worker*) estaba solo en FN (21 nov), pero la demo pública sale con el corte M0 el 15 nov. Además, el `git grep` de CE-009 usaba `<patrones…>` sin definirlos, y las pruebas sí contienen secretos falsos con `whsec_`, que darían falsos positivos. | RF-011, RF-034, RF-035, RF-036, RF-041; CE-009 | Copiar la lista de seguridad al cierre de M0 y fijar el comando de búsqueda, excluyendo `backend/tests` y revisando aparte que solo tenga los valores falsos de `conftest.py`. | **Revisión de seguridad también en el cierre del corte M0**, con el comando fijado (Hugo, 2026-11-14), como se recomienda. Aplicada en T038; FN la repite en T052. |

**Bloques de la pasada:**

1. **Coherencia interna**: tareas con formato `- [ ] T### [P] [US#]`, ruta, RF, Dep. y "Hecho cuando" (comprobado con un script); trazabilidad completa de RF-001 a RF-043 y CE-001 a CE-010; pruebas antes de su implementación en cada fase; cada fase con su cierre. Salen QT-6 y las erratas 4 y 5.
2. **Spec, plan del hackathon, reglas e issues**: el issue #18 pide "arranca con un solo comando", "GET /salud responde 200" y "no hay valores reales en el código": cubiertos por T037, T033 y T038 (`DATABASE_URL` del issue queda fuera de alcance, #19 y #23). Fechas de M0 coherentes con el ensayo de las 10:00 y el formulario de las 12:00 del 15 nov. Constitución: salen QT-1 a QT-4.
3. **Código (solo lectura)**: `pytest -q` → `15 passed` (11 funciones, con parametrización). `backend/app/main.py:79,85,149` usa `marcar_pagado` y la consulta vieja que T014 y T015 cambian (errata 4). El prototipo ya usa `qrImage`, `whsec_` y `monto_maximo`, como dicen las tareas.
4. **API de pey**: `Webhook.sign(msg_id, timestamp, data: str)` recibe texto, no bytes (errata 2). El `openapi.json` solo documenta `requestId` en errores (QT-4). El `llms.txt` de pey menciona un ambiente de pruebas (`api.dev.pey.mx`), pero la página vigente "Create an API Key" dice que está "coming soon" y la del simulador da 404: se mantiene "solo producción" y queda como pregunta para pey (§8.5 de la spec), sin decisión.
5. **Dependencias externas**: pytest-asyncio: la versión más nueva publicada el 2026-10-31 o antes es **1.4.1** (2026-10-25); `1.4.1.post1` es del 2026-11-01 y `1.5.0` del 2026-11-12, ambas con menos de dos semanas (errata 1). CoDi el 15 nov, #65 y #64 en la tabla de dependencias.
6. **Casos límite**: salen QT-5 y QT-6. Varias pantallas en un cobro (T025), consulta lenta (T025), pagos simultáneos por aviso y consulta (un solo proceso con `asyncio`; `registrar_pago` es síncrono, así que no hay carrera) y reinicio (404, sin tarea: limitación aceptada).
7. **Seguridad y rendimiento**: sale QT-7. `ProxyHeadersMiddleware` con el valor por defecto `127.0.0.1` no confía en el cliente `testclient` de `TestClient` (comprobado con `_TrustedHosts` de uvicorn 0.54): errata 3.
8. **Construibilidad y reparto**: con C-1, el corte M0 queda en 39 tareas (T001 a T039) entre esta noche y las 10:00 del 15 nov; la F6 vieja se integró en tareas que ya existían, sin fases nuevas. El riesgo y su salida están en §11 del plan y en la Estrategia.

**Erratas** (sin efecto en el comportamiento; corregidas el 2026-11-14):

1. *(Corregida en T001)* Se fija `pytest-asyncio==1.4.1` en lugar de `<versión>`.
2. *(Corregida en T006)* `firmar_aviso` firma el cuerpo como texto (`str`), porque `Webhook.sign` recibe `data: str`.
3. *(Corregida en T032)* En la prueba de IP real, `proxies_confiables="testclient"`, que es la dirección con la que se conecta `TestClient`.
4. *(Corregida en T016)* El manejador del aviso y la consulta del prototipo (`main.py:79,85,149`) pasan a `registrar_pago` y `pagos_del_qr(…, vistas)` con el mismo comportamiento, hasta que T027 y T028 los reemplacen.
5. *(Corregida en el plan)* `plan.md` dice "R-1 a R-12" y lista `test_cancelar_cobro.py` en §3.2.
