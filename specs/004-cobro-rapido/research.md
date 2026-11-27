# Investigación (Fase 0): Spec 004 — Cobro rápido

- **Fecha**: 2026-11-26
- **Plan**: [plan.md](plan.md)
- **Spec**: [spec.md](spec.md) (aprobada el 2026-11-26, cortes C1 y C2)
- **Fuentes**: `backend/app/` y `web/js/` en `main` (`3867106`), `supabase/migraciones/0001_esquema_inicial.sql` a `0003`, `https://docs.pey.mx/openapi.json` (versión `2026-10-20`, consultada el 2026-11-26), y rama remota `origin/feature/web-ux-landing-login-dashboard` (`2d7652e`, revisada en solo lectura).

Cada sección sigue el formato de spec-kit: **Decisión**, **Por qué** y **Alternativas consideradas**. Ninguna decisión agrega librerías ni servicios externos nuevos (principio IX).

---

## R-1. Campo y validación de duración en `POST /api/cobros` (DP-1)

- **Decisión**:
  - Agregar el campo opcional `duracion_segundos` (entero) al cuerpo JSON de `POST /api/cobros`, en español y `snake_case` (coherente con `expiracion_segundos`, `gracia_segundos` y `hora_servidor` de la spec 001, R-10).
  - Si el campo falta o es `null`, usar `config.expiracion_segundos` (`600` segundos = 10 minutos, RF-001).
  - Validar en `validar_duracion(valor, *, permitir_sin_vencimiento)` dentro de `leer_solicitud` (`backend/app/main.py:95`), **antes** del límite por IP y de llamar a pey:
    - Rechazar `bool` (`isinstance(valor, bool)`), `float`, `Decimal`, cadenas no enteras, listas u objetos con HTTP 422 (RF-006).
    - En **Corte 1** (`permitir_sin_vencimiento=False`): aceptar únicamente enteros `360 <= valor <= 86400`; cualquier otro entero (incluido `0`) responde 422 `"Elige una duración entre 6 minutos y 24 horas"`.
    - En **Corte 2** (`permitir_sin_vencimiento=True`): aceptar `valor == 0` o `360 <= valor <= 86400`; cualquier otro valor responde 422 `"Elige una duración entre 6 minutos y 24 horas, o sin vencimiento"`.
  - Enviar `expiracion=duracion` a `ClientePey.crear_qr(...)` (`backend/app/pey.py:95`), que ya pasa `"expiration": expiracion` a `POST /codi/qr`.
  - En el cliente web (`web/js/servidor.js`), el 3.er parámetro `duracion_segundos` es opcional y omite la clave del JSON cuando es `undefined` (conservando intacta la prueba unitaria `web/tests/test_crear_y_mostrar_qr.py:128`), mientras que `web/js/app.js` siempre envía `estado.duracion_segundos` (`RF-016`) y en F3 se actualizan los 2 asertos de pantalla (`web/tests/test_crear_y_mostrar_qr.py:313` y `web/tests/test_monto_libre_y_reuso.py:54`) bajo `C-13` (`QP-2`).
- **Por qué**:
  - `docs.pey.mx/openapi.json` (v`2026-10-20`) define `expiration` como entero con `minimum: 0`, `0` para sin vencimiento y mínimo `360` cuando se fija vencimiento, sin máximo documentado.
  - En Python `bool` hereda de `int` (`isinstance(True, int) == True`); rechazarlo explícitamente replica el patrón de `validar_monto` (`backend/app/main.py:52`).
  - Omitir `duracion_segundos` mantiene compatibilidad total con las pruebas y clientes de las specs 001 y 002 (CE-004).
- **Alternativas consideradas**:
  - **Nombrar el campo `expiration` o `duracion_minutos`**: `expiration` rompe la regla de idioma del código en español (constitución); minutos impediría alinear 1:1 con segundos en `expira_en`, `fin_ventana` y `config.expiracion_segundos`.
  - **Validar contra lista cerrada `{360, 600, 1800, 3600, 86400}`**: descartada por E-1; Hugo eligió rango acotado `360..86400` en el servidor y atajos predefinidos en pantalla.

---

## R-2. Persistencia de duración y `expira_en` anulable en Corte 1 vs Corte 2 (DP-2)

- **Decisión**:
  - **En el objeto `Cobro` y en el JSON público (`RF-007`)**:
    - `Cobro.expira_en` pasa a `int | None` (`int` en cobros finitos; `None` en cobros sin vencimiento en Corte 2).
    - `Cobro.duracion_segundos` es una propiedad derivada: `0 if self.expira_en is None else self.expira_en - self.creado_en`, expuesta en `Cobro.publico()` junto con `expira_en` (`int | None`) y `fin_ventana` (`int`, siempre obligatorio).
    - `Cobro.fin_ventana`: `creado_en + duracion + gracia_segundos` en cobros finitos (`RF-005`); `creado_en + 86400` (24 horas) en cobros sin vencimiento (`RF-010`, `RF-011`).
  - **En Corte 1**: **cero migraciones de base de datos**. `supabase/migraciones/0001_esquema_inicial.sql` ya guarda `creado_en`, `expira_en` (`check (expira_en > creado_en)`) y `fin_ventana` (`check (fin_ventana >= expira_en)`). Como todo cobro de Corte 1 tiene `360 <= duracion <= 86400`, el esquema actual persiste y recupera `duracion_segundos = expira_en - creado_en` sin pérdida tras un reinicio.
  - **En Corte 2** (coordinado con `#119` de Juan): nueva migración idempotente `supabase/migraciones/0004_cobros_sin_vencimiento.sql` (`QP-6`, `QP-3`) que:
    1. Hace `cobros.expira_en` anulable: `alter table cobros alter column expira_en drop not null;`.
    2. Ejecuta un bloque `DO $$ ... $$` consultando `pg_constraint` sobre `'public.cobros'::regclass` (`contype = 'c'`) para eliminar de forma idempotente cualquier `CHECK` que referencie `expira_en` distinto a los 3 checks nuevos con nombre fijo.
    3. Agrega los 3 checks con nombres fijos comprobando antes si ya existen:
       - `cobros_expira_mayor_creado`: `check (expira_en is null or expira_en > creado_en)`
       - `cobros_fin_ventana_mayor_creado`: `check (fin_ventana > creado_en)`
       - `cobros_fin_ventana_mayor_expira`: `check (expira_en is null or fin_ventana >= expira_en)`
    4. Recrea la vista con `create or replace view cobros_con_estado with (security_invoker = true)` ajustando la condición de vencimiento a `when c.expira_en is not null and now() >= c.expira_en then 'vencido'`.
    5. Reaplica `revoke all on cobros_con_estado from anon, authenticated;`.
    6. Se verifica en `backend/tests/test_migraciones_postgres.py` (`_versiones == ["0001", "0002", "0003", "0004"]`, idempotencia y permisos revocados).
    - Mantiene `fin_ventana not null`, por lo que `_SQL_VENTANA` (`backend/app/almacen_postgres.py:81`) y `LatidoDeConciliacion` (`backend/app/tareas.py:92`) concilian automáticamente los QR sin vencimiento a las 24 h sin cambios en `tareas.py`.
- **Por qué**:
  - Permite entregar Corte 1 antes de la puerta S2 (29 nov) sin bloquearse en `#119` (E-9).
  - Derivar `duracion_segundos` de `expira_en` evita duplicar columnas que podrían desincronizarse y mantiene retrocompatibilidad con cobros ya guardados en la base de la demo (todos tienen `expira_en - creado_en = 600`).
  - Mantener `fin_ventana not null` evita rediseñar la conciliación de la spec 003 (`RF-061`).
- **Alternativas consideradas**:
  - **Agregar una columna redundante `duracion_segundos` en `cobros`**: requiere migración incluso para Corte 1 y obliga a rellenar filas existentes y mantener una restricción adicional de coherencia con `expira_en - creado_en`.
  - **Usar una fecha centinela (ej. año 9999) para `expira_en`**: contamina consultas SQL, el JSON público y la vista de estado; `NULL` es el estándar relacional limpio en PostgreSQL.

---

## R-3. Canal de avisos (`canal.py`) y estado del cobro sin vencimiento (DP-3)

- **Decisión**:
  - En `Cobro.estado(ahora)` (`backend/app/cobros.py:102`): comprobar `if self.expira_en is not None and ahora >= self.expira_en: return VENCIDO`. Así un cobro sin vencimiento nunca pasa a *vencido* (`RF-009`).
  - En `canal.py:_espera(cobro, reloj)` (`backend/app/canal.py:18`): comprobar `if cobro.expira_en is not None and ahora < cobro.expira_en:` antes de calcular `cobro.expira_en - ahora`.
  - Al llegar a `fin_ventana` (24 h), `flujo_de_avisos` emite `fin` y cierra sin emitir `vencido` (`RF-009`, `RF-011`).
  - Los avisos firmados de pey (`POST /webhooks/pey`) ya no comprueban `fin_ventana` ni `expira_en` al registrar un pago (`backend/app/main.py:445-460`), así que un pago recibido días después sobre un QR sin vencimiento se registra y actualiza estado/total automáticamente (`RF-012`).
- **Por qué**: cambios mínimos y localizados en 2 funciones ya cubiertas por pruebas con `RelojFalso`.
- **Alternativas consideradas**: crear un flujo SSE separado para cobros sin vencimiento (duplicación innecesaria).

---

## R-4. Motor de calculadora con aritmética decimal exacta en JavaScript (DP-4)

- **Decisión**:
  - Extender `web/js/teclado.js` (funciones puras sin DOM ni librerías externas) para manejar una **expresión de cobro** como lista estructurada de tokens o cadena normalizada con espacios alrededor de operadores (`"3 × 25 + 20"`).
  - Representar la entrada como texto canónico con separadores simples (`" + "`, `" × "`), que además coincide 1:1 con lo que se muestra en `[data-prueba="expresion"]` (cero doble fuente de verdad):
    - Teclas: `"0"`–`"9"`, `"punto"`, `"borrar"`, `"mas"`, `"por"`, `"limpiar"`.
    - Reglas por operando (`RF-030`): máximo 5 dígitos enteros, máximo 2 decimales, un solo `.`, `.` inicial → `"0."`, `"0"` + dígito → reemplaza el `"0"`.
    - Al pulsar `"mas"` o `"por"`:
      - Si está vacía → ignorar (`RF-033`).
      - Si ya termina en operador → reemplazar ese operador (`RF-034`).
      - Si ya hay 20 operandos → ignorar (`RF-046`).
      - Si el operando actual termina en `.` → quitar el `.` sobrante (`RF-045`).
      - Agregar `" + "` o `" × "`.
    - Al pulsar `"borrar"`: si termina en `" + "` o `" × "` elimina los 3 caracteres del operador; si no, elimina 1 carácter del operando actual (`RF-035`).
    - Al pulsar `"limpiar"`: devuelve `""` (`RF-036`).
  - **Evaluación exacta sin coma flotante (`BigInt`)** (`RF-029`, `RF-047`):
    - Parsear cada operando a `{ entero: BigInt, escala: number }` (donde `escala` es 0, 1 o 2).
    - Si la expresión termina en operador final, evaluar el prefijo completo anterior al operador final para obtener el **total parcial** (`QA-1`, `RF-031`), marcando `incompleta: true`.
    - Evaluar productos `×` primero (precedencia estándar): multiplicar `enteroA * enteroB` y sumar `escalaA + escalaB` (exacto, sin pérdida intermedia).
    - Sumar los términos resultantes llevando todos a la escala máxima `S` de la expresión (`BigInt`).
    - Redondear de escala `S` a escala `2` (centavos) con **redondeo mitad hacia arriba** (`HALF_UP`): si `S > 2`, dividir por `10^(S-2)` sumando `1` cuando el residuo es `>= 5 * 10^(S-3)` (`1.5625 → 156` centavos = `$1.56`; `1.625 → 163` centavos = `$1.63`).
    - Comprobar tope de desbordamiento (`RF-047`): si `centavos > 99_999_999n` (`$999,999.99`), devolver `{ desbordado: true, total_centavos: null, monto_envio: null }` → nunca formatear en notación científica.
  - `cobrar_activo(expresion)`: `true` solo si no está vacía, no es `incompleta`, no es `desbordado` y `centavos > 0n` (`RF-037`).
  - `monto_libre_activo(expresion)`: `true` en toda entrada **sin operadores** cuyo valor numérico sea `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`), y `false` con cualquier operador (`"0 × 25"`, `"0 + "`) o valor `> 0` (`RF-038`, `QA-1`, `QP-1`; conserva en verde `web/tests/test_teclado.py:97-116` y `web/tests/test_monto_libre_y_reuso.py:43-45`).
- **Por qué**:
  - `Number` de JavaScript falla en casos cotidianos de centavos (`0.1 + 0.2 = 0.30000000000000004`, `1.005 * 100 = 100.49999999999999`) y pierde precisión entera arriba de `2^53`. `BigInt` es nativo en todos los navegadores modernos (Chromium y WebKit de Playwright, Android Chrome, iOS Safari 14+), pesa cero dependencias y garantiza exactitud matemática en centavos.
  - Al seguir siendo funciones puras en `web/js/teclado.js`, es 100 % reutilizable cuando se integre el rediseño `#118` (que usa el mismo `teclado.js`).
- **Alternativas consideradas**:
  - **Librería `decimal.js` o `big.js`**: requiere comparativa y gestión de dependencias en una web sin bundler (principio IX).
  - **`Number` con `Math.round(x * 100) / 100`**: falla con `1.25 * 1.30 = 1.625` o `1.005` por representación binaria IEEE-754.
  - **`eval()`**: prohibido por seguridad y CSP (`script-src 'self'`, sin `unsafe-eval`).

---

## R-5. Cuenta regresiva `H:MM:SS` y manejo de QR sin vencimiento en la web (DP-5)

- **Decisión**:
  - Extender `web/js/cuenta.js`:
    - `es_sin_vencimiento(cobro)`: devuelve `cobro.expira_en == null || cobro.duracion_segundos === 0`.
    - `restante(cobro, desfase, ahora)`: en cobros finitos calcula `cobro.expira_en - (ahora + desfase)`; en cobros sin vencimiento devuelve `null` (nunca un número negativo que dispare `qr_vencido`).
    - `restante_ventana(cobro, desfase, ahora)`: calcula `cobro.fin_ventana - (ahora + desfase)` para controlar la visibilidad de `Mostrar QR otra vez` y el fin de escucha en QR sin vencimiento (`RF-022`, `RF-023`).
    - `puede_reabrir_qr(cobro, desfase, ahora)` (`QP-4`): `es_sin_vencimiento(cobro) ? restante_ventana(cobro, desfase, ahora) >= 1 : restante(cobro, desfase, ahora) >= 1`, usado en los 4 sitios de `web/js/app.js` (`pagado()` :88, `al_mostrar_qr()` :314, `empezar_cuenta()` :380-399 y `mostrar_cobro_recuperado()` :424) para evitar los fallos de JS cuando `restante()` devuelve `null` (`null >= 1` es `false` y `null < 1` es `true`).
    - `formato(segundos)`:
      - Si `segundos >= 3600`: `H:MM:SS` (ej. `1:00:00`, `24:00:00`, con minutos y segundos en 2 dígitos, `RF-019`).
      - Si `segundos < 3600`: `M:SS` (ej. `59:59`, `10:00`, `6:00`, `0:00`, conservando 100 % de compatibilidad con las pruebas de spec 002, `RF-020`).
  - En `web/js/app.js`:
    - En la vista QR de un cobro sin vencimiento, `cuenta` muestra `"Sin vencimiento"` (`RF-021`).
    - En `empezar_cuenta(cobro)`: cuando `es_sin_vencimiento(actual)` nunca transiciona a `qr_vencido`; usa `puede_reabrir_qr` / `restante_ventana` para saber si sigue dentro de las 24 h (para `Mostrar QR otra vez` en `vista-pagado`, `RF-022`), y cuando `restante_ventana(...) < 1` dispara la misma transición idempotente de fin de 24 h (`RF-023`, `QP-4`: permanecer en `vista-qr` incluso si `qr_reabierto` es `true`, ocultar `cancelar`, mostrar `[data-prueba="aviso-fin-escucha"]`, detener el reloj y cerrar la escucha; nunca pasar a `qr_vencido` ni volver a `pago_recibido`), respaldando el caso en que el SSE esté cortado justo a las 24 h.
    - Al recibir el evento `fin` de `escuchas` para el cobro en pantalla (`RF-023`, `QA-7`):
      - Si el cobro es sin vencimiento y la vista actual es `"qr"`: permanece en `vista-qr` (incluso si `qr_reabierto` es `true`), oculta `cancelar`, muestra `[data-prueba="aviso-fin-escucha"]` con `"Este QR sigue vigente, pero ya terminaron las 24 horas de avisos en vivo en esta pantalla."`, detiene el reloj, cierra la escucha y deja activos `descargar-qr` y `nuevo-cobro`.
      - Si el cobro es sin vencimiento y la vista actual es `"pago_recibido"`: oculta `mostrar-qr` y mantiene `nuevo-cobro`.
      - Si es un cobro finito: mantiene el comportamiento actual (`ocultar_espera()`).
- **Por qué**: evita cualquier falso paso a `qr_vencido` cuando `expira_en` es `null` y mantiene intactas todas las pruebas existentes de `cuenta.js` y `test_vencido_y_nuevo.py`.
- **Alternativas consideradas**: mostrar siempre `0:10:00` con horas incluso en cobros de 10 min (rompería pruebas existentes de spec 002 que verifican `"10:00"` y añade ruido visual en mostrador).

---

## R-6. Descarga de la imagen PNG del QR (`web/js/descarga.js`, DP-6)

- **Decisión**:
  - Crear un módulo pequeño y enfocado `web/js/descarga.js` con dos funciones:
    1. `nombre_archivo_qr(cobro)`: arma `pago-facil-<monto-o-libre>-<concepto>.png` en minúsculas, normalizando acentos (`NFD` sin diacríticos), reemplazando caracteres no alfanuméricos por `-`, colapsando guiones repetidos y acotando el concepto a 30 caracteres (ej. `pago-facil-25-50-tacos.png`, `pago-facil-monto-libre-propina.png`, `pago-facil-qr.png` si faltan datos, `RF-026`, `QA-6`).
    2. `descargar_qr(qr_imagen_base64, cobro)`: decodifica base64 con `atob` → `Uint8Array` → `new Blob([bytes], { type: "image/png" })` → `URL.createObjectURL(blob)` → `<a download="...">` → `click()` → `setTimeout(() => URL.revokeObjectURL(url), 1000)` envuelto en `try/catch`. Si `qr_imagen_base64` está vacío, mal formado o falla alguna API del navegador, devuelve `{ ok: false, mensaje: "No se pudo descargar el QR. Intenta de nuevo." }` (`RF-027`).
  - No requiere cambios en la CSP de `web/index.html` (`a.click()` con `download` y `blob:` no viola `default-src 'self'`; en caso de cualquier restricción del entorno, el `try/catch` muestra el mensaje en español).
- **Por qué**:
  - Usar `Blob` + `URL.createObjectURL` evita límites de longitud de `data:` URLs en navegadores móviles y funciona de forma determinista con `page.expect_download()` en Playwright (Chromium y WebKit).
  - Separar la lógica en `descarga.js` permite probar el saneamiento de nombres y el manejo de errores de forma aislada.
- **Alternativas consideradas**:
  - **`href="data:image/png;base64,..."` directo**: más corto, pero algunos navegadores bloquean o truncan descargas `data:` en pestañas móviles y es menos fiable que `Blob`.
  - **Endpoint nuevo en backend `GET /api/cobros/{id}/qr.png`**: innecesario porque la pantalla ya tiene `qr_imagen` en memoria (principio IX) y obligaría a una petición extra que podría fallar sin red.

---

## R-7. Tope de 20 minutos para cobros anteriores > 1 hora (`escucha.js` y `memoria.js`, DP-7)

- **Decisión**:
  - En `web/js/escucha.js`:
    - Constante `TOPE_ANTERIOR_LARGO_SEGUNDOS = 1200` (20 minutos) y umbral `UMBRAL_COBRO_LARGO_SEGUNDOS = 3600` (1 hora).
    - Un cobro se considera *largo* si `cobro.duracion_segundos === 0 || cobro.duracion_segundos > 3600 || cobro.expira_en == null || (cobro.expira_en - cobro.creado_en) > 3600`.
    - Al pasar un cobro largo a **anterior** (`pasar_a_anterior()`), se calcula su tope local: `hasta = Math.min(cobro.fin_ventana, ahora_servidor_estimado + 1200)` (en segundos Unix del servidor).
    - Si `pasar_a_anterior()` ocurre mientras el cobro aún se recupera (`escucha.cobro === null`, como en `web/tests/test_recuperar.py:299-318`), se difiere el cálculo de `tope_local` a la primera respuesta de recuperación cuando `es_anterior && tope_local === null` y el cobro recuperado dure `> 1 h` (`duracion_segundos === 0 || duracion_segundos > 3600`) (`QP-4`).
    - Cada `Escucha` guarda `this.tope_local` (`number | null`). Mientras exista `tope_local`:
      - Se programa un temporizador exacto (revisado también al recibir cualquier evento o respuesta de `_consultar`) que cierra esa escucha (`this._al_recibir({ tipo: "fin", escucha: this })` y `this.terminar()`) en cuanto `ahora_servidor_estimado >= tope_local`, liberando su canal SSE, deteniendo el polling y permitiendo soltar Wake Lock cuando no queden escuchas (`RF-044`, `QA-4`).
  - En `web/js/memoria.js`:
    - Mantener el formato `{ en_pantalla, anteriores }` retrocompatible y admitir una clave opcional `topes_anteriores` (objeto `{ [cobro_id]: entero_unix }`, validado estrictamente en `forma_valida` por `RF-077` de la spec 002: cada clave debe pasar `es_id` y cada valor debe ser entero finito positivo). Si `localStorage` trae el formato anterior de 2 claves, sigue cargando sin errores.
    - Al guardar en `localStorage`, omitir la clave `"topes_anteriores"` cuando esté vacía (solo escribirla si existe al menos un cobro anterior largo `> 1 h`), conservando intactas las pruebas de `web/tests/test_recuperar.py:109-112,314` (`QP-3`).
    - Al recargar la página, si `ahora_servidor >= tope_local` para un cobro anterior, se descarta de inmediato sin reabrir canal (`RF-024`, `RF-044`).
- **Por qué**:
  - Protege la cuota de pey (`429 CALL_LIMIT_REACHED`), el límite de 10 canales por IP (`RF-041`) y la batería/pantalla del celular (Wake Lock `RF-058` de la 002) sin cambiar el comportamiento del servidor (el servidor sigue registrando webhooks y conciliando a las 24 h).
  - La validación estricta de `topes_anteriores` conserva intacta la seguridad de `memoria.js` (`RF-077`).
- **Alternativas consideradas**:
  - **Acortar `fin_ventana` en el servidor**: impediría al dueño que deja un QR de 24 h **en pantalla** recibir avisos más allá de 20 min, violando E-3.
  - **No persistir `topes_anteriores` en `localStorage`**: recargar la página reiniciaría el reloj de 20 min cada vez o lo perdería.

---

## R-8. Diseño del selector de duración, teclado en 320 px y accesibilidad (DP-8)

- **Decisión**:
  - **Teclado (`.teclas`)**: cambiar de cuadrícula de 3 columnas a **4 columnas** (`grid-template-columns: repeat(4, minmax(0, 1fr))`) con botones táctiles de al menos `44px` de alto (`web/estilos.css:33`):
    - Fila 1: `7`, `8`, `9`, `×` (`aria-label="Multiplicar"`)
    - Fila 2: `4`, `5`, `6`, `+` (`aria-label="Sumar"`)
    - Fila 3: `1`, `2`, `3`, `⌫` (`aria-label="Borrar último carácter"`)
    - Fila 4: `C` (`aria-label="Limpiar todo"`), `0`, `.`, *(o disposición 1–9 arriba como hoy: `1 2 3 +` / `4 5 6 ×` / `7 8 9 ⌫` / `. 0 C` con `0` o `C` ocupando 2 espacios — mantener el orden `1 2 3` arriba preserva la memoria muscular del teclado telefónico actual de la spec 002!)*.
    - **Elección concreta**: mantener el orden numérico `1–9` de la spec 002 para no sorprender a quien ya probó la web:
      - Fila 1: `1`, `2`, `3`, `+` (`tecla-mas`, `aria-label="Sumar"`)
      - Fila 2: `4`, `5`, `6`, `×` (`tecla-por`, `aria-label="Multiplicar"`)
      - Fila 3: `7`, `8`, `9`, `⌫` (`tecla-borrar`, `aria-label="Borrar último carácter"`)
      - Fila 4: `.` (`tecla-punto`), `0` (`tecla-0`), `C` (`tecla-limpiar`, `aria-label="Limpiar todo"`, `grid-column: span 2`)
    - En 320 px con padding `0.75rem` (24 px) y 3 gaps de `0.25rem` (12 px), cada tecla tiene `(320 - 24 - 12) / 4 = 71 px` de ancho y `>= 44 px` de alto: amplio para el pulgar y cero scroll horizontal (`RF-042`, `CE-008`).
  - **Expresión y total**: `[data-prueba="expresion"]` con `overflow-wrap: anywhere` (o `overflow-x: auto` interno al contenedor sin ensanchar la página) encima de `[data-prueba="monto"]` en grande (`RF-031`, `RF-042`).
  - **Selector de duración**: grupo accesible `role="radiogroup"` con `aria-label="Duración del QR"` y botones `role="radio"` con `aria-checked="true|false"` en flujo flexible (`display: flex; flex-wrap: wrap; gap: 0.25rem`), garantizando `min-height: 44px` y cero scroll horizontal en 320 px (`RF-013`, `RF-014`, `RF-042`, `RF-048`).
  - **Compatibilidad con `#118`**: toda la interacción se basa en atributos `data-prueba` estables y módulos puros (`teclado.js`, `cuenta.js`, `descarga.js`), igual que en `origin/feature/web-ux-landing-login-dashboard`.
- **Por qué**: mantiene el orden numérico de la spec 002, garantiza zonas táctiles ≥ 44×71 px en 320 px y cumple accesibilidad semántica básica (`RF-048`).
- **Alternativas consideradas**: usar un `<select>` nativo para duración (oculta las opciones y requiere 2 toques; los chips en una fila/wrap son de un solo toque en mostrador).

---

## R-9. Compatibilidad del servidor simulado de pruebas web (`web/tests/servidor_simulado.py`) (DP-9)

- **Decisión**:
  - Actualizar `web/tests/servidor_simulado.py` para que `POST /api/cobros`:
    - Acepte el campo opcional `duracion_segundos` (por defecto `600`), valide el mismo rango que el backend real (`360..86400` en C1; más `0` en C2) y devuelva `duracion_segundos`, `expira_en` (`int | None`) y `fin_ventana` (`creado_en + duracion + 600` o `creado_en + 86400` para `0`).
    - Guarde la última petición recibida para que las pruebas Playwright puedan verificar exactamente qué `monto` (total calculado) y qué `duracion_segundos` mandó la pantalla sin depender de pey real (principio V).
  - En `web/js/servidor.js`, el 3.er parámetro `duracion_segundos` es opcional y omite la clave del JSON cuando es `undefined` (conservando intacta la prueba unitaria `web/tests/test_crear_y_mostrar_qr.py:128`), mientras que `web/js/app.js` siempre envía `estado.duracion_segundos` (`RF-016`) y en F3 se actualizan los 2 asertos de pantalla (`web/tests/test_crear_y_mostrar_qr.py:313` y `web/tests/test_monto_libre_y_reuso.py:54`) bajo `C-13` (`QP-2`).
- **Por qué**: las pruebas de la web (`uv run --directory backend pytest ../web -q`) corren contra `servidor_simulado.py` en el CI sin base de datos ni pey real.
- **Alternativas consideradas**: levantar la app FastAPI real en las pruebas Playwright (más lento y acopla las pruebas de interfaz a la configuración del backend).
