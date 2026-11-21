# Guía de verificación: 001 Backend del MVP

## F1 Preparación

Fecha: 2026-11-14. El prototipo responde igual. Lo nuevo es el reloj inyectable, el pey simulado compartido, la configuración nueva y pytest-asyncio.

### Reloj falso

`RelojFalso.dormir(5)` adelanta el reloj 5 segundos y cede el control. La prueba no espera esos 5 segundos: exige que el tiempo real sea menor a 0.5 s.

```bash
uv run --directory backend pytest -q tests/test_modelo.py::test_dormir_con_el_reloj_falso_adelanta_el_tiempo_sin_esperar
```

Tiene que terminar enseguida y pasar. La otra prueba del mismo archivo comprueba que `ahora()` se queda quieto hasta `avanzar(10)`.

`crear_app` guarda el reloj en `app.state.reloj`. Desde F2, crear un cobro y calcular su estado usan ese reloj.

### Pey simulado, sin salir a la red

Las pruebas arman el cliente con `httpx.MockTransport` y la base `https://pey.prueba` (`backend/tests/conftest.py`). El transporte responde dentro del proceso: crear QR, páginas con `nextToken`, errores 401, 403, 503 y 500 con `requestId`, `httpx.ConnectError` y `httpx.ReadTimeout`. El host de cada petición guardada es `pey.prueba`.

```bash
uv run --directory backend pytest -q
```

Esperado: `18 passed`.

La fixture `configuracion` usa la llave falsa `llave-falsa-NO-DEBE-SALIR` y el secreto falso `whsec_` + base64 de `secreto-falso-NO-DEBE-SALIR`. El límite de la fixture sigue en 5 cobros por minuto, que es el del prototipo, para que la prueba repartida siga esperando el 429 en el sexto cobro. El valor por defecto del servidor sigue en 10.

### pytest-asyncio

Versión fijada: **1.4.1**, publicada el **2026-10-25** (la más nueva con al menos dos semanas al 2026-10-31; ver DP-2). Está solo en el grupo `dev`.

En `backend/pyproject.toml` quedó `asyncio_default_fixture_loop_scope = "function"` (TK-4 del plan): sin esa línea, pytest-asyncio 1.4.1 avisa en cada corrida de que el alcance del bucle va a cambiar.

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Los tres tienen que salir limpios. `pytest` puede mostrar el aviso ya existente de Starlette sobre `TestClient` y httpx; no viene de F1.

Commit sugerido:

```text
test(001): preparar reloj inyectable, pey simulado y pytest-asyncio (F1)
```

## F2 Base

Fecha: 2026-11-14. El cobro guarda una lista de pagos numerados, el estado sale del reloj y la consulta a pey recorre páginas. El aviso sigue firmándose como el prototipo y el canal sigue emitiendo `pagado`. Cada transacción nueva entra por `registrar_pago`.

### Orden de estados

En `tests/test_modelo.py`, `test_el_estado_sigue_el_orden_pagos_cancelado_vencido_pendiente` deja el orden por escrito:

1. Si hay pagos, el estado es `pagado` (también si estaba vencido o cancelado).
2. Si no hay pagos y hay `cancelado_en`, el estado es `cancelado`.
3. Si `ahora` es mayor o igual que `expira_en`, el estado es `vencido`.
4. En cualquier otro caso, el estado es `pendiente`.

`test_un_cobro_sin_pagos_vence_a_los_10_minutos` fija el corte: a los 599 s sigue pendiente y a los 600 ya venció. `test_la_ventana_de_escucha_termina_al_vencer_mas_la_gracia` comprueba gracia 0 y gracia 600: la ventana sigue abierta un segundo antes de `fin_ventana` y se cierra en ese instante.

```bash
uv run --directory backend pytest -q tests/test_modelo.py -k "estado or ventana or vence"
```

### Pagos numerados y monto distinto

`test_un_qr_reutilizado_registra_y_numera_cada_pago` registra tres transacciones en el mismo cobro. Los números quedan 1, 2 y 3, `total_recibido` es la suma, `pagado_en` es la hora del último y el estado sigue `pagado`.

`test_una_transaccion_ya_vista_no_se_registra_otra_vez` usa el mismo identificador en otro cobro y por la otra fuente: las dos veces devuelve nada.

`test_un_monto_base_distinto_se_marca_y_deja_advertencia` pide $50 y registra un base de $40. El pago queda con `monto_distinto` y el registro `pago_facil` deja un `WARNING` con el id del cobro, 50 y 40. `test_una_propina_no_cuenta_como_monto_distinto` usa base $50 y recibido $55: no hay marca ni advertencia.

```bash
uv run --directory backend pytest -q tests/test_modelo.py -k "numera or transaccion or monto"
```

### Registro INFO al arrancar

Al crear la app, `pago_facil` queda en INFO y escribe en la consola. Esta línea sale al importar el servidor:

```text
INFO pago_facil: Registros de pago_facil activos
```

```bash
uv run --directory backend python -c "import app.main"
```

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de F2: `33 passed`, y ruff limpio.

Commit sugerido:

```text
refactor(001): modelo de cobro con pagos numerados, reloj y cliente de pey paginado (F2)
```

## F3 Historia 1: cobrar con un QR

Fecha: 2026-11-14. Un cobro de monto fijo se valida en el servidor y, si pey responde bien, devuelve el QR. El monto libre sigue fuera de este corte: `0`, `null` y un monto ausente se rechazan.

### Qué comprueban las pruebas

`test_crear_cobro_pide_el_qr_a_pey_con_vigencia_de_10_minutos_y_el_id_del_cobro` mira la petición a pey: monto `0.01`, concepto, vigencia `600`, `numRef` de hasta 7 dígitos, imagen pedida y `metadata.cobroId`. La respuesta no devuelve `metadata`.

`test_el_cobro_devuelve_todos_sus_campos` exige los 15 campos del contrato, un `id` de 12 caracteres, estado `pendiente`, vencimiento a los 600 s y ventana igual al vencimiento (gracia 0).

`test_montos_no_validos_se_rechazan_sin_llamar_a_pey` cubre negativo, tres decimales, texto, más de $100 y, en este corte, `0`, `null` y ausente. El mensaje es «Escribe un monto mayor a $0 con máximo 2 decimales» o «El monto máximo de la demo es $100», y pey no recibe la petición.

`test_el_concepto_se_limpia_y_usa_cobro_por_defecto` y `test_un_concepto_con_caracteres_no_imprimibles_se_rechaza` cubren espacios, el texto «Cobro», el máximo de 40 letras y los caracteres no imprimibles.

`test_si_pey_falla_el_cobro_no_se_guarda_y_el_mensaje_dice_la_causa` cubre llave ausente, 401, 403, mantenimiento, error 500 y sin conexión. En todos, el cobro intentado responde 404. Si crear tarda demasiado, la respuesta es 502 «No se pudo crear el cobro con pey. Intenta de nuevo.»

`test_crear_un_cobro_deja_una_linea_en_el_registro` busca una línea `INFO` con el id del cobro, el `codi_qr_id` y el `requestId`.

```bash
uv run --directory backend pytest -q tests/test_crear_cobro.py
```

### Medición del QR con imagen (CE-002)

La haces tú, con el servidor local y la llave real. Crear el cobro no mueve dinero.

1. Arranca el backend: `uv run --directory backend uvicorn app.main:app --port 8000`.
2. En otra terminal:

```bash
curl -s -w '\n%{time_total}\n' -X POST http://localhost:8000/api/cobros \
  -H 'Content-Type: application/json' \
  -d '{"monto": 0.01, "concepto": "Prueba"}'
```

3. Anota aquí el `time_total`: ____ s.

Si pasa de 3 s, se anota un TK en el §14 del plan y la decisión de la imagen pasa al issue #64.

**Medición del 2026-11-14 (Hugo):** 201, cobro real de $0.01 con imagen, `time_total` de **9.09 s**, con el servidor recién arrancado. Se repitió con otro arranque y dos cobros seguidos: **7.77 s** y **2.39 s**. El primer cobro después de arrancar pasa de 3 s y los siguientes no. Queda como TK-5 en el §14 del plan y la decisión pasa a #64. La respuesta de crear no trajo `requestId`, así que la línea `INFO` salió sin él, como estaba previsto.

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de F3: `53 passed`, y ruff limpio.

Commit sugerido:

```text
feat(001): crear cobro CoDi de monto fijo con pey (F3)
```

## F4 Historias 2 y 3: aviso, respaldo y canal

Fecha: 2026-11-14. Un pago se registra una sola vez, por el aviso firmado o por la consulta a pey, y el canal lo avisa sin que la pantalla pregunte.

### Aviso sin firma

Para la revisión de la firma: `tests/test_aviso_pey.py`, `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada`. Cubre tres casos: sin cabeceras, firmado con otro secreto y firmado con una hora de hace 6 minutos. Los tres responden 401 «Firma no válida», el cobro sigue pendiente y el `webhook-id` no queda marcado: el reintento válido con el mismo id se procesa.

### Canal con curl

Con el servidor local y un cobro de prueba (crearlo no mueve dinero):

```bash
curl -s -X POST http://localhost:8000/api/cobros \
  -H 'Content-Type: application/json' \
  -d '{"monto": 0.01, "concepto": "Prueba"}'
```

Con el `id` de la respuesta:

```bash
curl -N http://localhost:8000/api/cobros/<id>/eventos
```

Se ve `retry: 3000`, luego `event: estado`. A los 15 s, `: sigo conectado`. A los 10 minutos, `event: vencido` y enseguida `event: fin`, y curl termina. El reloj de las pruebas recorre esos plazos sin esperar; este curl usa el reloj real.

> Desde F6, con `GRACIA_SEGUNDOS` en 600 por defecto: a los 10 minutos llega `event: vencido` y el canal sigue abierto. `event: fin` llega a los 20 minutos, en `fin_ventana`. Para ver el comportamiento de F4, arranca con `GRACIA_SEGUNDOS=0`.

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

Esperado: `84 passed`, y ruff limpio. F4 y F5 se entregan en un solo commit (comparten `main.py` y `eventos.py`), así que la cifra que vale es la del cierre de F5.

Commit sugerido:

```text
feat(001): aviso de pey firmado, QR reutilizado, consulta de respaldo y canal de avisos (F4)
```

## F5 Historias 5 y 6: demo protegida y salud

Fecha: 2026-11-14. La demo limita cobros y canales por la IP del cliente, `/salud` dice qué credencial falta sin mostrarla, y el README usa el contrato del corte M0.

La prueba repartida que esperaba el 429 en el sexto cobro quedó reemplazada por `test_limite_de_cobros_por_ip`, con límite de 10. La fixture general sigue en 5.

### Protección

```bash
uv run --directory backend pytest -q tests/test_proteccion.py tests/test_salud_y_registros.py
```

Qué tiene que pasar:

- `test_limite_de_cobros_por_ip`: un 422 no cuenta; 10 cobros válidos pasan; el 11.º responde 429 «Demasiados cobros seguidos. Espera un minuto.» y no llama a pey; tras `reloj.avanzar(60)` vuelve a pasar.
- `test_el_limite_usa_la_ip_real_detras_del_proxy`: con el valor por defecto `127.0.0.1`, `X-Forwarded-For` se ignora. Con `proxies_confiables="testclient"`, dos IPs de documentación (`203.0.113.1` y `203.0.113.2`) tienen límites separados.
- `test_una_ip_no_puede_abrir_mas_de_10_canales`: `ocupar` diez veces y el canal responde 429 «Tienes demasiadas pantallas abiertas. Cierra otras e intenta de nuevo.»; `liberar` abre un lugar.
- `test_cors_solo_permite_los_origenes_configurados`: el origen de `WEB_ORIGIN` recibe `Access-Control-Allow-Origin`; otro no. Los métodos permitidos son solo `GET` y `POST`.
- `test_salud_dice_que_credenciales_faltan_sin_mostrarlas`: con llave y sin secreto, `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}`.
- `test_la_llave_y_el_secreto_no_aparecen_en_respuestas_ni_registros`: la llave falsa y el secreto falso de `conftest.py` no salen en cuerpos, cabeceras ni en `caplog`.
- `test_los_registros_dejan_cobro_error_de_pey_pago_y_aviso_ignorado`: hay línea de cobro creado, de consulta, de error de pey con `requestId`, de pago (`numero` y `fuente`) y de aviso ignorado o rechazado. El aviso rechazado no guarda cabeceras ni el cuerpo.

### Revisión de seguridad del corte M0

Revisado el 2026-11-14 sobre el código de este cierre.

| Punto | Resultado |
|---|---|
| Secretos solo en `backend/.env` o en el hosting | Cumple en el repo. El `git grep` de abajo no encontró nada. `.env` no se abre ni se cita. |
| Firma del aviso antes de leer el JSON | Cumple. `POST /webhooks/pey` llama a `Webhook.verify` y solo después hace `json.loads`. Lo cubre `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada`. |
| Entradas validadas en el servidor | Cumple. Monto y concepto se rechazan antes de llamar a pey (`test_montos_no_validos_se_rechazan_sin_llamar_a_pey` y las de concepto). |
| CORS solo para `WEB_ORIGIN` | Cumple. Métodos `GET` y `POST`. Prueba de arriba. |
| 10 cobros por minuto y 10 canales por IP real | Cumple en las pruebas automáticas. El límite usa `request.client.host` después de `ProxyHeadersMiddleware`. |
| `PROXIES_CONFIABLES` distinto de `*` | El valor por defecto del código es `127.0.0.1`, no `*`. En el hosting (#65) tiene que ser la IP del proxy, o `*` solo si el hosting no permite conexiones directas. Eso lo confirma Altairtm al desplegar. |
| Un solo worker | Cumple en la documentación de arranque: `uvicorn app.main:app` sin `--workers` (`backend/README.md` y quickstart §7). Este cierre no desplegó. |

CE-009. Desde la raíz, sin abrir `backend/.env`:

```bash
git grep -nE "whsec_[A-Za-z0-9+/=]{16,}|Bearer [A-Za-z0-9._-]{16,}" -- ':!backend/tests'
```

Resultado del 2026-11-14: salida vacía (el comando termina en 1, que es «no hay coincidencias»).

En `backend/tests/` no hay credenciales reales. El secreto de prueba se arma en `conftest.py` (`whsec_` + base64 de `secreto-falso-NO-DEBE-SALIR`) y la llave falsa es `llave-falsa-NO-DEBE-SALIR`. `test_aviso_pey.py` arma otro secreto falso, distinto, solo para firmar mal (`otro-secreto-distinto-al-bueno!!`). No son valores de pey.

CE-010. Con el servidor local, un aviso sin firma:

```bash
cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8765
```

En otra terminal:

```bash
curl -s -o /dev/null -w '%{http_code} %{time_total}\n' -X POST http://127.0.0.1:8765/webhooks/pey \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Con secreto configurado responde **401**; sin secreto, **503** («El aviso de pey todavía no está configurado»). Tu `backend/.env` todavía no tiene el secreto, así que en local verás 503.

Resultado del 2026-11-14 (revisión de Claude, servidor local real, con un secreto falso puesto en la variable de entorno para no tocar `.env`): **401 en 0.002 s** con secreto y **503 en 0.001 s** sin secreto. Los dos están por debajo de 1 s. La medición anterior no imprimía el código HTTP y coincidió con un servidor de prueba en el mismo puerto, así que se repitió. Cuando termines, para ese proceso por su PID. La prueba `test_el_aviso_de_pey_no_hace_peticiones_a_pey` comprueba, además, que ese camino no llama a pey.

### Pagos reales de $0.01 (los haces tú)

Pendiente. Hace falta tu autorización en el momento y CoDi activo en el banco (la spec lo deja para el 15 nov). Son dos pagos de $0.01, con cuenta propia o la CLABE de prueba de pey. Si a las 10:00 del 15 nov no están hechos, se despliega este cierre en verde y se avisa en el formulario (riesgo de §11 del plan).

1. Arranca el backend: `cd backend && uv run uvicorn app.main:app --port 8000`. Un solo proceso, sin `--workers`.
2. Crea el cobro (no mueve dinero hasta que alguien lo pague):

```bash
curl -s -X POST http://localhost:8000/api/cobros \
  -H 'Content-Type: application/json' \
  -d '{"monto": 0.01, "concepto": "Prueba"}'
```

3. Abre el canal con el `id` de la respuesta: `curl -N http://localhost:8000/api/cobros/<id>/eventos`.
4. Paga $0.01 desde la app del banco, en la opción CoDi. **Esperado, sin aviso de pey configurado** (CE-008, local): `event: pago` con `numero: 1` en menos de 5 s después de que pey lo registra.
5. Paga **otra vez el mismo QR**, otros $0.01 (CE-006, C-1). **Esperado**: `event: pago` con `numero: 2` y `total_recibido: 0.02`.
6. Cuando existan la URL pública (#65) y la pantalla (#64), repetir desde esa URL (CE-001). Con el aviso real configurado, el `pago` tiene que llegar en menos de 2 s después del aviso (CE-003).
7. IP real en el despliegue (quickstart §7, paso 5): desde dos redes distintas, por ejemplo wifi y datos del celular, cada una tiene su propio límite de 10 cobros por minuto. Pendiente de #65.

Anota aquí los tiempos cuando los hagas:

- Pago 1, `numero: 1`: ____ s después de que pey lo registra.
- Pago 2, `numero: 2`, `total_recibido: 0.02`: ____ s.
- Desde la URL pública: ____.
- Con aviso real: ____ s.

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de F5: `95 passed`, y ruff limpio. Las 6 pruebas nuevas son de la revisión de Claude: un aviso firmado con `amount` en `NaN`, `Infinity`, texto, `true` o `null` responde 400 «Aviso con datos no válidos», no registra el pago y el reintento con el mismo `webhook-id` sí se procesa (`test_un_aviso_con_monto_ilegible_responde_400_y_no_registra_el_pago`). El corte M0 queda listo en código. Los dos pagos reales y el despliegue siguen pendientes, como dice la sección de arriba.

`grep -n "codiQrId\|pagado\b" backend/README.md` no encuentra el contrato viejo.

> Desde F6 ese `grep` encuentra la palabra *pagado*, que es el estado del cobro y no el evento viejo. Para comprobar el contrato viejo usa `grep -nE 'codiQrId|"pagado"|event: pagado' backend/README.md`, que tiene que salir vacío. El 2026-11-15 salió vacío.

Commit sugerido, uno solo para F4 y F5:

```text
feat(001): aviso, respaldo y canal (F4); demo protegida, salud y cierre del corte M0 (F5)
```

## F6 Historia 3: ventana de gracia

Fecha: 2026-11-14. Durante los 10 minutos posteriores al vencimiento el canal sigue abierto y un pago tardío se avisa. El cambio es el valor por defecto de `GRACIA_SEGUNDOS`: pasa de 0 a 600. La lógica del canal no cambia.

`test_el_cobro_devuelve_todos_sus_campos` ahora exige `fin_ventana == expira_en + 600`. Las pruebas que abrían el canal o mandaban un aviso «al terminar la ventana» avanzan el reloj hasta `fin_ventana` del cobro, que ahora es 20 minutos después de crearlo.

### Qué comprueban las pruebas

```bash
uv run --directory backend pytest -q \
  tests/test_canal.py::test_un_pago_5_minutos_despues_de_vencer_se_avisa_por_el_canal \
  tests/test_respaldo.py::test_despues_de_la_gracia_ya_no_se_consulta_a_pey \
  tests/test_salud_y_registros.py::test_la_configuracion_tiene_los_valores_por_defecto_del_plan
```

- Con la gracia por defecto, el canal emite `vencido`, sigue abierto y, al llegar un pago en `expira_en + 300`, emite `pago`. El cobro queda *pagado*.
- En `fin_ventana` (`expira_en + 600`) ver el cobro no consulta a pey. Abrir el canal emite `estado` y `fin`, y cierra.
- `Configuracion(_env_file=None).gracia_segundos` es 600. `backend/.env.example` trae `GRACIA_SEGUNDOS=600`.

### Pago real tardío (lo haces tú)

Pendiente. Hace falta tu autorización en el momento. Es un cobro de $0.01, con cuenta propia o la CLABE de prueba de pey. Si el banco no deja pagar un QR ya vencido, anótalo aquí: es la pregunta abierta de la spec §8.5.

1. Arranca el backend: `cd backend && uv run uvicorn app.main:app --port 8000`. Un solo proceso, sin `--workers`. No definas `GRACIA_SEGUNDOS` si quieres los 600 del corte 2.
2. Crea el cobro:

```bash
curl -s -X POST http://localhost:8000/api/cobros \
  -H 'Content-Type: application/json' \
  -d '{"monto": 0.01, "concepto": "Prueba"}'
```

3. Espera a que venza (10 minutos). El canal, abierto con `curl -N http://localhost:8000/api/cobros/<id>/eventos`, tiene que emitir `event: vencido` y seguir conectado.
4. Unos 5 minutos después del vencimiento, paga $0.01 desde la app del banco, en la opción CoDi.
5. **Esperado**: `event: pago` y el cobro *pagado*.

Anota el resultado: ____

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de F6: `97 passed`, y ruff limpio.

Revisión de Claude (2026-11-14):
- Con `GRACIA_SEGUNDOS=0 uv run --directory backend pytest -q` fallan justo las 4 pruebas de la gracia. Así se cumple el «Hecho cuando» de T040.
- `backend/README.md` seguía diciendo que la gracia «queda en 0». Ahora dice 600 por defecto, el ejemplo trae `fin_ventana` 10 minutos después de `expira_en` y explica que `vencido` no cierra el canal: solo `fin`.

Commit sugerido:

```text
feat(001): ventana de gracia de 10 minutos para pagos tardíos (F6)
```

## F7 Historia 1: monto libre

Fecha: 2026-11-14. Un cobro sin monto, con `null` o con `0` crea un QR en el que el cliente escribe la cantidad. Pey recibe `amount: 0`. El cobro guarda `monto: null` y `monto_libre: true`. Un pago de cualquier cantidad no queda como monto distinto.

`0`, `null` y el monto ausente salieron de `test_montos_no_validos_se_rechazan_sin_llamar_a_pey`. Negativo, más de dos decimales, texto y más de $100 siguen en 422.

### Qué comprueba la prueba

```bash
uv run --directory backend pytest -q \
  tests/test_crear_cobro.py::test_monto_vacio_o_cero_crea_un_cobro_de_monto_libre
```

Tres casos: cuerpo sin `monto`, `"monto": null` y `"monto": 0`. En los tres la respuesta es 201, la petición a pey lleva `amount: 0` y un aviso de $7.50 queda con `monto_distinto: false`.

### Pago real (lo haces tú)

Pendiente. Hace falta tu autorización en el momento. Es $0.01, con cuenta propia o la CLABE de prueba de pey.

1. Arranca el backend: `cd backend && uv run uvicorn app.main:app --port 8000`.
2. Crea el cobro libre (no mueve dinero hasta que alguien lo pague):

```bash
curl -s -X POST http://localhost:8000/api/cobros \
  -H 'Content-Type: application/json' \
  -d '{"concepto": "Prueba"}'
```

**Esperado**: 201 con `monto: null` y `monto_libre: true`.

3. Abre el canal: `curl -N http://localhost:8000/api/cobros/<id>/eventos`.
4. Escanea el QR en la app del banco, en la opción CoDi, y escribe $0.01.
5. **Esperado**: `event: pago` con `monto_recibido: 0.01` y el cobro con `monto_libre: true`.

Anota el resultado: ____

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de F7: `96 passed`, y ruff limpio.

Revisión de Claude (2026-11-14):
- Casos borde probados aparte: `0.00`, `-0`, `"0"` y un cuerpo vacío también crean un cobro de monto libre. `-0.01` y `0.001` siguen en 422.
- Un pago de $150 a un QR libre se registra sin «monto distinto». El tope de `MONTO_MAXIMO` solo limita lo que el negocio pide, no lo que el cliente escribe en su banco.
- `backend/README.md` no mencionaba el monto libre. Ahora lo explica en la fila de `POST /api/cobros` y en las reglas.

Commit sugerido:

```text
feat(001): cobro de monto libre (F7)
```

## F8 Historia 4: cancelar un cobro

Fecha: 2026-11-14. El negocio cancela un cobro pendiente. El QR sigue pagable en el banco. Si después llega un pago, se registra y el cobro queda pagado. El canal emite `cancelado` y sigue abierto hasta `fin_ventana`.

### Qué comprueban las pruebas

```bash
uv run --directory backend pytest -q tests/test_cancelar_cobro.py \
  tests/test_canal.py::test_el_canal_avisa_cancelado_en_menos_de_15_segundos
```

- `POST /api/cobros/{id}/cancelar` sobre un pendiente responde 200 con `estado: "cancelado"` y deja una línea de registro con el id.
- Pagado, vencido o ya cancelado responden 409 «Solo se puede cancelar un cobro que todavía no se paga ni vence».
- Un aviso válido después de cancelar responde `procesado: true` y el cobro queda pagado.
- Un id que no existe responde 404 «Ese cobro no existe».
- Al publicar la cancelación, el canal emite `event: cancelado` con el objeto cobro antes de que el reloj avance 15 s.

### Pago real a un QR cancelado (lo haces tú)

Pendiente. Hace falta tu autorización en el momento. Es $0.01, con cuenta propia o la CLABE de prueba de pey. Cancelar no llama a pey: el banco sigue pudiendo cobrar el QR.

1. Arranca el backend: `cd backend && uv run uvicorn app.main:app --port 8000`.
2. Crea el cobro:

```bash
curl -s -X POST http://localhost:8000/api/cobros \
  -H 'Content-Type: application/json' \
  -d '{"monto": 0.01, "concepto": "Prueba"}'
```

3. Abre el canal: `curl -N http://localhost:8000/api/cobros/<id>/eventos`.
4. Cancélalo: `curl -s -X POST http://localhost:8000/api/cobros/<id>/cancelar`. **Esperado**: `estado: "cancelado"` y, en el canal, `event: cancelado`.
5. Paga $0.01 desde la app del banco, en la opción CoDi.
6. **Esperado**: el canal emite `pago` y el cobro queda pagado.

Anota el resultado: ____

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de F8: `104 passed`, y ruff limpio.

Revisión de Claude (2026-11-14):
- Ruta, mensajes y códigos coinciden con [cancelar-cobro](contracts/cancelar-cobro.md).
- Faltaba una prueba de lo que espera el pago real de T050. La agregué: `test_un_cobro_cancelado_sigue_escuchando_y_avisa_el_pago` (`test_canal.py`). Con la gracia de 600 s, el canal emite `cancelado`, sigue abierto pasado el vencimiento sin emitir `vencido` ni `fin`, y a los 5 minutos de vencer avisa el `pago` con el cobro *pagado*. Pasó a la primera: el código ya se comportaba así.
- El README todavía no menciona la ruta de cancelar ni el evento `cancelado`. Eso le toca a T051 (FN).

Commit sugerido:

```text
feat(001): cancelar un cobro pendiente (F8)
```

## FN Pulido del corte 2

Fecha: 2026-11-15. El README cuenta la gracia, el monto libre, la cancelación y el evento `cancelado`. El quickstart ya describe la ventana de 20 minutos. La revisión de seguridad del corte M0 se repitió con la ruta de cancelar.

### README

`backend/README.md` enlaza `specs/001-backend-mvp/contracts/` y nombra cada ruta y cada evento:

- `POST /api/cobros`, `GET /api/cobros/{id}`, `POST /api/cobros/{id}/cancelar`, `GET /api/cobros/{id}/eventos`, `POST /webhooks/pey`, `GET /salud`.
- Eventos `estado`, `pago`, `vencido`, `cancelado` y `fin`, más el comentario `: sigo conectado`.
- `GRACIA_SEGUNDOS` por defecto 600.
- Un `monto` ausente, `null` o `0` crea un cobro de monto libre.

### Revisión de seguridad del corte 2

Revisado el 2026-11-15. La lista es la del corte M0, más la cancelación.

| Punto | Resultado |
|---|---|
| Secretos solo en `backend/.env` o en el hosting | Cumple en el repo. El `git grep` de abajo no encontró nada. `.env` no se abre ni se cita. |
| Firma del aviso antes de leer el JSON | Cumple. `Webhook.verify` sigue antes de `json.loads`. Lo cubre `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada`. |
| Entradas validadas en el servidor | Cumple. Monto, concepto y la cancelación se deciden en el servidor. |
| CORS solo para `WEB_ORIGIN` | Cumple. Métodos `GET` y `POST`, que es el método de cancelar. |
| 10 cobros por minuto y 10 canales por IP real | Cumple en `tests/test_proteccion.py`. |
| `PROXIES_CONFIABLES` distinto de `*` | El valor por defecto sigue en `127.0.0.1`. En el hosting (#65) es la IP del proxy, o `*` solo si no hay conexiones directas. |
| Un solo worker | Sigue documentado en el README y en el quickstart §7, sin `--workers`. |
| Cancelar | Solo `POST /api/cobros/{id}/cancelar`. 404 «Ese cobro no existe» y 409 «Solo se puede cancelar un cobro que todavía no se paga ni vence». El cuerpo es el objeto cobro o `{"detail": "..."}`, sin llave, secreto ni datos bancarios. Lo cubren `tests/test_cancelar_cobro.py`. |

CE-009, otra vez, sin abrir `backend/.env`:

```bash
git grep -nE "whsec_[A-Za-z0-9+/=]{16,}|Bearer [A-Za-z0-9._-]{16,}" -- ':!backend/tests'
```

Resultado del 2026-11-15: salida vacía (el comando termina en 1). En `backend/tests/` siguen solo los secretos falsos de `conftest.py` y el otro falso de `test_aviso_pey.py`.

Un aviso sin firma, en el servidor local del quickstart (puerto 8766, sin imprimir `.env`): **503 en 0.0008 s**, porque el secreto del aviso no está configurado. Está por debajo de 1 s y no llama a pey.

### Quickstart, pasos 1 a 7

| Paso | Resultado del 2026-11-15 |
|---|---|
| 1. Pruebas y ruff | `104 passed`. `ruff check` y `ruff format --check` limpios. |
| 2. Arranque y `/salud` | Servidor local en `127.0.0.1:8766`. `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}`. Solo esos tres campos. |
| 3. Crear un cobro real y abrir el canal | No se creó un QR real en esta pasada. Crearlo llama a pey. El objeto y `event: estado` los cubren las pruebas. Lo haces tú con el paso 3 del quickstart cuando autorices el cobro. |
| 4. Pago real de $0.01 | Pendiente de tu autorización, igual que en F5, F6, F7 y F8. El texto del quickstart ahora dice que `vencido` llega a los 10 minutos y `fin` a los 20. |
| 5. Aviso firmado a mano | No se firmó con el secreto real. Lo cubre `test_un_aviso_sin_firma_valida_se_rechaza_sin_cambiar_nada`. |
| 6. Once cobros de $150 | Los 11 respondieron **422**. No se llama a pey. |
| 7. Despliegue | Revisado contra el código. No hay despliegue (#65). `GRACIA_SEGUNDOS` queda documentada como 600 por defecto. |

No hizo falta un TK: lo que no coincidía con la gracia de 600 se corrigió en el quickstart.

### Cierre

```bash
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

En el cierre de FN: `104 passed`, y ruff limpio. Con esto terminan las tareas de la spec 001. Los pagos reales de $0.01 siguen pendientes de tu autorización.

Commit sugerido:

```text
docs(001): pulido del corte 2 y quickstart validado (FN)
```

## F9 Cambio C-2: hora actual del servidor en cada cobro

Fecha: 2026-11-15. Cada objeto cobro trae `hora_servidor` (entero Unix): la hora del servidor al armar la respuesta o el evento. Lo pidió la spec 002 para que la cuenta regresiva no dependa del reloj del celular (RF-019, CE-016). El cambio vive en `Cobro.publico()` (`backend/app/cobros.py`), así que sale en crear, ver, cancelar y en todos los eventos del canal sin tocar las rutas (TK-6 del plan).

### Por qué un campo y no `creado_en`

`creado_en` se fija **antes** de pedirle el QR a pey. Si pey tarda 9 s, un cobro recién creado ya lleva 9 s de vida. Con `hora_servidor`, la pantalla calcula `expira_en − hora_servidor` y arranca en 9:51, no en 10:00.

### Pruebas automáticas

```bash
uv run --directory backend pytest -q -k "del_servidor or campos"
```

Esperado: `7 passed`:

| Prueba | Qué comprueba |
|---|---|
| `test_el_objeto_publico_del_cobro_tiene_los_campos_del_contrato` y `test_el_cobro_devuelve_todos_sus_campos` | El objeto cobro tiene 16 campos, con `hora_servidor` |
| `test_el_objeto_publico_trae_la_hora_actual_del_servidor_como_entero` | Es la hora del reloj, en segundos enteros (5.7 s de más se truncan) |
| `test_crear_cobro_descuenta_lo_que_tardo_pey_en_la_hora_del_servidor` | Si pey tarda 9 s: `creado_en = T` y `hora_servidor = T + 9` |
| `test_ver_cobro_trae_la_hora_actual_del_servidor` | Al ver el cobro 30 s después, `hora_servidor = creado_en + 30` |
| `test_cancelar_devuelve_la_hora_del_servidor` | La respuesta de cancelar también la trae |
| `test_los_eventos_del_canal_traen_la_hora_del_servidor` | `estado` y `fin` la traen, con la hora en que se emitieron |

Resultado del 2026-11-15: suite completa `109 passed`; `ruff check` y `ruff format --check` limpios.

### Comprobación a mano (opcional, con tu autorización)

Crear un QR llama a pey, aunque no mueve dinero. Si lo autorizas, con el servidor del quickstart (paso 2):

1. `curl -s -X POST http://localhost:8000/api/cobros -H 'Content-Type: application/json' -d '{"monto": 0.01, "concepto": "Prueba"}'` y, en otra terminal, `date +%s`.
2. **Esperado**: `hora_servidor` es igual o 1 s menor que `date +%s`, y mayor o igual que `creado_en` (la diferencia es lo que tardó pey).
3. `curl -N http://localhost:8000/api/cobros/<id>/eventos`: el `event: estado` trae `hora_servidor` con la hora de apertura.

No hace falta pagar el QR.
