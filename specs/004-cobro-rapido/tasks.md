# Tasks: Cobro rápido — calculadora, duración del QR y descarga del código

- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-26 (`E-1`–`E-9`, `QA-1`–`QA-8`; ajuste puntual de `RF-038` por `QP-1` el 2026-11-27; cambios `C-12`, `C-13` —ampliado el 2026-11-27 por `QT-5` con `RF-046`, `RF-049`, `RF-070` de spec 002; sigue `Aprobado · sin aplicar`— y `C-14` aprobados y pendientes de aplicar)
- **Plan**: [plan.md](plan.md), estado: Aprobado el 2026-11-27 (`DP-1`–`DP-9`, `QP-1`–`QP-7`)
- **Fecha**: 2026-11-27
- **Estado**: `Aprobado` (2026-11-27 por Hugo; QA en una sola pasada `/qa-spec 004 tasks` con `QT-1`–`QT-7` y 4 erratas aplicadas el 2026-11-27. Aprobar no autoriza empezar F1: se espera a que Hugo pida `/speckit-implement`.)
- **Entrada**: los documentos de `specs/004-cobro-rapido/`: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/` y `quickstart.md`

> **Notas para los comandos de spec-kit.**
> - Cada tarea sigue el formato obligatorio `- [ ] T001 [P] [US1] Descripción con ruta del archivo`.
> - `/speckit-implement` la marca como `[X]` al terminarla.
> - Los detalles van como sub-puntos sangrados debajo de la tarea.
> - `[P]` = se puede hacer en paralelo (otros archivos, sin dependencias pendientes).
> - `[US1]` … `[US5]` = historia de la spec a la que pertenece (`Historia 1` = `US1` … `Historia 5` = `US5`).
> - Las casillas van siempre en listas, nunca en tablas (en las tablas no se ven).
> - Todas las rutas son relativas a la raíz del repositorio. Los comandos se corren desde la raíz, salvo que la tarea diga otra cosa.
> - Las fases siguen el plan (`plan.md §8`): `F1`–`F5` corresponden al **Corte 1** (meta Puerta S2, dom 29 nov, sin migración de BD) y `F6`–`FN` corresponden al **Corte 2** (tras `#119`, opción **Sin vencimiento** y cierre).

---

## Reglas de ejecución

1. **Las fases van en orden según el grafo de dependencias.** Cada fase la hace una sola persona o agente; en fases compartidas por dos personas (`F5`, `F6` con PR `#119` de Juan y PR `#120` Corte 2 de Hugo, y `FN`), cada PR o sub-bloque lo ejecuta una sola persona. Al empezar lo anota en **Estado** (`"F1 en curso (nombre)"`) y al cerrarla también (`"F1 terminada (nombre, AAAA-MM-DD)"`).
2. **Pruebas primero (principio V).** En cada historia y fase de código se escriben las pruebas, se ven fallar por la razón esperada y después se implementa.
3. **Solo se hace la tarea pedida.** Nada de funciones sorpresa, retoques cosméticos ni refactorizaciones fuera de la tarea (`#118` y `#115` siguen fuera de alcance).
4. **Si el código obliga a cambiar algo**, se anota en el *Registro de implementación* del plan (`plan.md §14`) como `TK-n`. Si toca una spec aprobada, se presenta como un cambio `C-n` (**el siguiente libre es `C-15`**, pues `C-12`, `C-13` y `C-14` ya están aprobados y pendientes de aplicar en FN), que Hugo aprueba por separado.
5. **Una fase cierra con tres cosas:**
   - todo en verde:
     - backend: `uv run --directory backend pytest -q`, `uv run --directory backend ruff check .` y `uv run --directory backend ruff format --check .`;
     - web: `uv run --directory backend pytest ../web -q`;
     - estilo del Python de las pruebas de la web: `uv run --directory backend ruff check --config pyproject.toml ../web` y `uv run --directory backend ruff format --config pyproject.toml --check ../web`;
     - PostgreSQL desechable (en `F6` y `FN`, o en CI, `QT-3`): `PRUEBAS_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/pago_facil_prueba" uv run --directory backend pytest tests/test_migraciones_postgres.py tests/test_esquema_postgres.py tests/test_almacen.py -q`;
   - su sección en `specs/004-cobro-rapido/verification-guide.md`;
   - el mensaje de commit sugerido, con formato `tipo(004): descripción en español`.
   - El commit, el push, las ramas y el pull request los hace Hugo (o el dueño de la rama en su entorno; los agentes trabajan Git en **solo lectura**). Cada PR usa `.github/pull_request_template.md`.
   - **Guía QA en `docs/qa/` (`QT-6`)**: siguiendo la constitución (equipo/QA) y `.github/pull_request_template.md:30`, entregar `specs/004-cobro-rapido/quickstart.md` y `specs/004-cobro-rapido/verification-guide.md` a Miguel (`#87`) en los cierres de Corte 1 (`T027`) y Corte 2 (`T041`) para mantener la guía QA en `docs/qa/`; mientras `docs/qa/` no exista o esté pendiente, anotar explícitamente su estado en «Qué quedó pendiente» de cada PR con pantalla (`F2`, `F3`–`F4`, `F7`).
6. **Ninguna prueba automática llama al pey real, a la base de datos real ni espera tiempo real.** Usan `PeySimulado`, `RelojFalso`, `AlmacenEnMemoria`, PostgreSQL desechable (`PRUEBAS_DATABASE_URL`) y `web/tests/servidor_simulado.py`. Las pruebas de pantalla corren en Chromium (`Pixel 7`) y WebKit (`iPhone 13`); las de lógica pura llevan `@pytest.mark.only_browser("chromium")`.
7. **Dinero real**: solo cobros de `$0.01` MXN, solo con cuentas propias o CLABEs de prueba de pey, y únicamente en `F5` (`T026`) y `FN` (`T039`) con la autorización expresa de Hugo en ese momento.
8. **Secretos**: nadie lee, imprime, cita ni pega `PEY_API_KEY`, `PEY_WEBHOOK_SECRET`, `DATABASE_URL` ni el contenido de `backend/.env` o `backend/.env.demo`. Para saber si están configurados se usa `GET /salud`.

---

## Reparto

| Fase | Issue / Corte | Quién la hace | Quién la revisa |
|---|---|---|---|
| F1 Backend duración finita | `#120` (Corte 1) | Hugo | Leonel y Juan (al unir PR) |
| F2 Calculadora en teclado | `#100` (Corte 1) | Leonel | Hugo; Juan (después de unir) |
| F3 Selector duración, `H:MM:SS` y tope 20 min | `#121` (Corte 1) | Leonel | Hugo; Juan (después de unir) |
| F4 Descarga PNG del QR | `#121` (Corte 1) | Leonel | Hugo; Juan (después de unir) |
| F5 Cierre Corte 1 (Puerta S2) | `#120`, `#100`, `#121` (Corte 1) | Hugo y Leonel | Hugo (pagos reales `$0.01`) |
| F6 Migración `0004` + backend Sin vencimiento | `#119` y `#120` (Corte 2) | Juan (`#119`) y Hugo (`#120`) | Leonel y Hugo |
| F7 Opción Sin vencimiento en web | `#121` (Corte 2) | Leonel | Hugo y Juan |
| FN Cierre, `C-12`–`C-14`, seguridad y `$0.01` C2 | cierre 004 (C1+C2) | Hugo y Leonel | Hugo; Juan y Leonel |

**Estrategia de ramas, PRs y etiquetas por issue (`plan.md §8.1`, `QP-7`, `QT-6`):**

| Issue | Fases | Rama / PR | Etiqueta en el PR | Base y orden |
|---|---|---|---|---|
| `#132` | Spec, plan y `tasks.md` | `feature/132-spec-004-cobro-rapido` | `Closes #132` *(solo aquí)* | Sale de `main` y se une primero (documentación). |
| `#120` | **F1** (backend duración finita) | Rama propia del issue `#120` (Corte 1) | `Refs #120` (`T006`) | Sale de `main`; corre en paralelo con `#100`. |
| `#100` | **F2** (calculadora en web) | Rama propia del issue `#100` | `Closes #100` (`T011`) | Sale de `main`; corre en paralelo con `#120`. |
| `#121` | **F3–F4** (selector, `H:MM:SS`, tope 20 min y Descargar QR) | Rama propia del issue `#121` (Corte 1) | `Refs #121` (`T024`) | Sale **tras unir `#100`** (o sobre su rama base) para evitar colisiones en `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css`. |
| `#119` + `#120` | **F6** (migración `0004` + backend Sin vencimiento) | PR de `#119` (Juan) seguido de PR de `#120` Corte 2 (Hugo) | `Closes #119` (Juan, `T030`/`T032`) · `Closes #120` (Hugo, `T032`) | Tras cierre de Corte 1 (`F5`); `#120` Corte 2 integra la migración de `#119`. |
| `#121` | **F7** (web Sin vencimiento) y cierre `FN` | Rama propia del issue `#121` (Corte 2) + cierre `004` | `Closes #121` (`T036`) · cierre `004` en `FN` sin re-cerrar `#132` | Sale tras unir F6 (`#119` + `#120` Corte 2). |

*Política de etiquetas (`QT-6`): `Closes #132` se usa únicamente en el PR inicial de documentación (`feature/132-spec-004-cobro-rapido`); los PRs de Corte 1 de issues divididos usan `Refs #120` (`T006`) y `Refs #121` (`T024`), y cierran en Corte 2 con `Closes #120` (`T032`) y `Closes #121` (`T036`); `#100` cierra en `T011` (`Closes #100`) y `#119` en el PR de migración `0004` de Juan (`Closes #119`, `T030`/`T032`).*

---

## Dependencias externas

| Dependencia | Dueño | Qué bloquea | Estado |
|---|---|---|---|
| Sincronizar `backend/.venv` con `uv sync --directory backend --locked` (`psycopg` de spec 003, `QP-7`) | Hugo y Leonel | Ejecución de `pytest` en local en `F1` (Hugo) y `F2` (Leonel) en adelante | Pendiente en la copia local de cada autor antes de empezar `F1` y `F2` |
| Base de datos y demo pública funcionando (spec 003, PR `#144` unido a `main`) | Hugo | `F1`–`FN`, pruebas reales de `F5` y `FN` | Listo |
| Actualización de persistencia `#119` (migración `0004`) | Juan (`Altairtm`) | Únicamente **Corte 2** (`F6`–`FN`); no bloquea Corte 1 (`F1`–`F5`) | Pendiente |
| CoDi activo en banco propio + Android e iPhone + autorización expresa de Hugo para `$0.01` | Hugo | Verificaciones reales de `T026` (`F5`) y `T039` (`FN`) | CoDi activo; autorización al ejecutar |
| PostgreSQL 17 desechable en local (`PRUEBAS_DATABASE_URL`) | Hugo / Juan / Leonel | Correr pruebas SQL y de almacén de `F6` y `FN` en local (sin él se saltan en local; en CI siempre corren) | Opcional en local; siempre en CI |

---

## Formato de cada tarea

```text
- [ ] T001 [P] [US1] Descripción con la ruta exacta del archivo
  - **RF**: RF-001, RF-002
  - **Dep.**: T000 (o "ninguna")
  - **Hecho cuando**: criterio verificable (prueba que pasa, comando y salida esperada)
```

---

## Fase 1 (F1): Backend de duración finita del QR (`#120`, Corte 1 · 27 nov · 🎯 MVP servidor · Historia 1 y validación de Historia 5)

**Objetivo**: aceptar y validar `duracion_segundos` en `POST /api/cobros` (defecto `600` s para compatibilidad, rango finito `360..86400` s, rechazos `422` sin llamar a pey), exponer `duracion_segundos` en el objeto cobro y mantener la ventana de escucha `+10 min` tras vencer sin tocar la base de datos (`Corte 1`).

**Prueba independiente**: enviar a `POST /api/cobros` una duración omitida (`600` s), duraciones finitas (`360`, `1800`, `86400` s) y duraciones inválidas (`0` en C1, `359`, `86401`, `-600`, `600.5`, `true`, `"600"`), comprobando con `PeySimulado` y `RelojFalso` que las válidas fijan `expira_en` y `fin_ventana` exactos y las inválidas devuelven `422` en español con cero llamadas a pey.

- [ ] T001 Sincronizar el entorno virtual del backend con `uv sync --directory backend --locked` desde `backend/pyproject.toml` y `backend/uv.lock` (preparación local previa a `F1` y `F2`, `QP-7`, `QT-3`)
  - Preparación/setup de entorno local que cada autor corre en su propia copia local (Hugo antes de `F1` en `#120` y Leonel antes de `F2` en `#100`) para comprobar la línea base antes de modificar código.
  - **RF**: — (prerrequisito de entorno para TDD, principio V, `QP-7`, `QT-3`)
  - **Dep.**: ninguna
  - **Hecho cuando**: `uv run --directory backend pytest -q`, `uv run --directory backend ruff check .` y `uv run --directory backend ruff format --check .` pasan en verde sin errores de importación de `psycopg`.

### Pruebas de F1 (primero, deben fallar antes de implementar)

- [ ] T002 [P] [US1] Actualizar `CAMPOS_COBRO` (16 → 17 claves con `"duracion_segundos"`, `C-12`, `QP-3`) y agregar pruebas de duración por defecto, finita válida y rechazos 422 en `backend/tests/test_crear_cobro.py`
  - Actualizar `CAMPOS_COBRO` en `backend/tests/test_crear_cobro.py:23-40` agregando `"duracion_segundos"`.
  - `test_sin_duracion_usa_diez_minutos_por_defecto`: omitir o mandar `null` envía `"expiration": 600` a pey y devuelve `duracion_segundos: 600` (`CE-004`).
  - `test_duracion_finita_valida_se_envia_a_pey_y_fija_vencimiento`: probar `360`, `1800` y `86400` (tanto monto fijo como monto libre), verificando `"expiration": duracion` en `PeySimulado`, `expira_en == creado_en + duracion`, `fin_ventana == expira_en + 600`, `duracion_segundos == duracion` y registro en log con `duracion_segundos` (sin secretos ni datos bancarios, Principio X).
  - `test_duracion_invalida_se_rechaza_sin_llamar_a_pey`: probar `0` (en C1), `359`, `86401`, `-600`, `600.5`, `True`, `False`, `"600"`, `[]`, `{}` → HTTP `422` con `{"detail": "Elige una duración entre 6 minutos y 24 horas"}`, cero solicitudes en `pey.solicitudes`, sin guardar cobro y sin consumir el límite por IP (`CE-003`).
  - **RF**: RF-001, RF-002, RF-003, RF-006, RF-007, RF-043 (CE-003, CE-004)
  - **Dep.**: T001
  - **Hecho cuando**: las pruebas nuevas y el aserto actualizado de `CAMPOS_COBRO` existen en `backend/tests/test_crear_cobro.py` y fallan porque el servidor aún ignora `duracion_segundos` y no lo incluye en `publico()`.
- [ ] T003 [P] [US1] Actualizar `CAMPOS_COBRO` (16 → 17 claves con `"duracion_segundos"`, `C-12`, `QP-3`, `QT-1`) y agregar pruebas unitarias de `Cobro.duracion_segundos`, vencimiento con duración elegida y ventana de escucha en `backend/tests/test_modelo.py` y `backend/tests/test_canal.py`
  - En `backend/tests/test_modelo.py`: actualizar `CAMPOS_COBRO` en `backend/tests/test_modelo.py:13-30` (16 → 17 claves añadiendo `"duracion_segundos"`, y actualizar el docstring en `:144`, `QT-1`) para que `test_el_objeto_publico_del_cobro_tiene_los_campos_del_contrato` quede alineado al completar `T004`; agregar `test_cobro_con_duracion_elegida_vence_a_su_hora_y_mantiene_diez_minutos_de_gracia` (`creado_en + 1800` para `expira_en`, `expira_en + 600` para `fin_ventana`, `duracion_segundos == 1800`, transición a `vencido` al cumplir los 1800 s con `RelojFalso` y pago tardío dentro de gracia pasa a `pagado`).
  - En `backend/tests/test_canal.py`: `test_canal_cierra_al_terminar_ventana_de_duracion_elegida` (emite `vencido` al cumplirse `expira_en` y `fin` al cumplirse `expira_en + 600`).
  - **RF**: RF-003, RF-004, RF-005, RF-007
  - **Dep.**: T001
  - **Hecho cuando**: el aserto actualizado de `CAMPOS_COBRO` y ambas pruebas existen y fallan por la razón esperada (falta la propiedad `duracion_segundos` en `Cobro` y en `publico()`).

### Implementación de F1

- [ ] T004 [US1] Agregar la propiedad derivada `duracion_segundos` y exponerla en `Cobro.publico()` en `backend/app/cobros.py`
  - Definir propiedad `duracion_segundos -> int`: `0 if self.expira_en is None else self.expira_en - self.creado_en` (`data-model.md §1.1`).
  - Incluir `"duracion_segundos": self.duracion_segundos` en `Cobro.publico()` manteniendo `expira_en = creado_en + expiracion` y `fin_ventana = creado_en + expiracion + self._gracia` en `RepositorioCobros.nuevo`.
  - **RF**: RF-003, RF-004, RF-005, RF-007
  - **Dep.**: T003
  - **Hecho cuando**: las pruebas de T003 pasan en verde.
- [ ] T005 [US1] Implementar `validar_duracion`, leer `duracion_segundos` antes del límite por IP, pasarlo a `cobros.nuevo` y `pey.crear_qr`, y registrarlo en el log en `backend/app/main.py`
  - Reglas literales (`data-model.md §1.2`, `contracts/crear-cobro-duracion.md`):
    - Si `valor is None` o falta la clave → `config.expiracion_segundos` (`600`).
    - Si `isinstance(valor, bool)` o `not isinstance(valor, int)` → HTTP `422` con `"Elige una duración entre 6 minutos y 24 horas"`.
    - En Corte 1 (`permitir_sin_vencimiento=False`): si `valor < 360 or valor > 86400` (incluido `0`) → HTTP `422` con `"Elige una duración entre 6 minutos y 24 horas"`.
  - Ejecutar `validar_duracion` dentro de `leer_solicitud` antes de `limite.permitir(ip)` y antes de llamar a `pey.crear_qr`.
  - Pasar `duracion` tanto a `cobros.nuevo(...)` como a `pey.crear_qr(..., expiracion=duracion)` y agregar `duracion_segundos=%s` al `registro.info("QR creado ...")` (sin secretos ni datos bancarios).
  - **RF**: RF-001, RF-002, RF-003, RF-006, RF-007, RF-043 (CE-003, CE-004)
  - **Dep.**: T002, T004
  - **Hecho cuando**: T002 y toda la suite `uv run --directory backend pytest -q` pasan en verde.
- [ ] T006 [US1] Cierre de F1: pruebas y ruff en verde, crear `specs/004-cobro-rapido/verification-guide.md` con la sección F1 y commit sugerido
  - Commit sugerido (PR del issue `#120`, Corte 1 — usar `Refs #120` en el PR y **no** `Closes #120`, porque `#120` cierra en `F6`/`T032`, `QT-6`): `feat(004): duración configurable del QR de 6 min a 24 h en el servidor (F1)`.
  - **RF**: RF-001, RF-002, RF-003, RF-004, RF-005, RF-006, RF-007, RF-043
  - **Dep.**: T005
  - **Hecho cuando**: los comandos de backend y web de la regla 5 dan verde, existe `specs/004-cobro-rapido/verification-guide.md` con la sección F1 y el estado de este archivo registra F1 terminada.

**Punto de control**: `POST /api/cobros` admite duraciones de `360` a `86400` s (defecto `600`), rechaza entradas inválidas con `422` sin tocar pey y pasa toda la suite existente sin migrar la base de datos.

---

## Fase 2 (F2): Calculadora exacta en el teclado de cobro (`#100`, Corte 1 · 27 nov · en paralelo con F1 · Historia 2)

**Objetivo**: permitir armar sumas y multiplicaciones en el teclado (`+`, `×`, `⌫`, `C`) con precedencia `×` antes que `+`, aritmética exacta `BigInt` con redondeo mitad hacia arriba a 2 decimales, expresión secundaria encima del total grande, total parcial en operador final, tope de 20 operandos, protección contra desbordamiento > `$999,999.99`, accesibilidad en español y diseño responsive desde 320 px.

**Prueba independiente**: en Chromium y WebKit contra `servidor_simulado.py`, teclear `3 × 25 + 20`, comprobar expresión `"3 × 25 + 20"` arriba y `"$95.00"` abajo, probar `25 +` (total parcial `"$25.00"` y `Cobrar`/`Monto libre` desactivados), `1.25 × 1.30 = $1.63`, `0 × 25`, `25.` + `+`, `C`, `⌫`, tope de 20 operandos, desbordamiento `> $999,999.99`, conservación de expresión en error del servidor, envío del monto único `$95.00` con concepto independiente y 0 px de desplazamiento horizontal a `320 × 640 px`.

### Pruebas de F2 (primero, deben fallar antes de implementar)

- [ ] T007 [P] [US2] Agregar pruebas unitarias del motor de calculadora (`@pytest.mark.only_browser("chromium")`) y pruebas de pantalla (Chromium y WebKit) en `web/tests/test_teclado.py`
  - Conservar intactas las pruebas existentes `web/tests/test_teclado.py:97-116` y `web/tests/test_monto_libre_y_reuso.py:43-45` (`QP-1`).
  - Pruebas unitarias de `web/js/teclado.js`: cubrir la tabla completa de `contracts/calculadora-y-descarga.md §3` (`""`, `"0"`, `"0."`, `"0.00"`, `"25.50"`, `"15 + 22.50 + 8"` → `$45.50`, `"3 × 25 + 20"` → `$95.00`, `"20 + 3 × 25"` → `$95.00`, `"1.25 × 1.25"` → `$1.56`, `"1.25 × 1.30"` → `$1.63`, `"0.1 + 0.2"` → `$0.30`, `"25 + "` → parcial `$25.00` y `incompleta: true`, `"3 × 25 + "` → parcial `$75.00`, `"25 + 0."` → `$25.00` `cobrar_activo: true` [`QP-5`], `"25 + 10."` → `$35.00` `cobrar_activo: true` [`QP-5`], `"25 + 0"` + `"7"` → `"25 + 7"` [`QP-5`], `"0 × 25"` → `$0.00` ambos desactivados, `"0 × 25 + 10"` → `$10.00` `cobrar_activo: true`, `"99999 × 99"` → `"El total es demasiado grande"` con `desbordado: true` y sin notación científica), `aplicar_tecla("", "mas"|"por") === ""`, `"25."` + `"mas"` → `"25 + "`, `"25 + "` + `"punto"` → `"25 + 0."`, `"25 + "` + `"por"` → `"25 × "`, `borrar` en operador y dígito, `limpiar` → `""` y tope de 20 operandos ignorando `"mas"`/`"por"`.
  - Pruebas de pantalla: `[data-prueba="expresion"]` oculto para monto simple (`25.50`) y visible con operadores (`3 × 25 + 20`); botones `tecla-mas` (`aria-label="Sumar"`), `tecla-por` (`aria-label="Multiplicar"`), `tecla-borrar` (texto visible `"⌫"` conservando `data-prueba="tecla-borrar"` y `aria-label="Borrar último carácter"`, `QP-5`) y `tecla-limpiar` (`aria-label="Limpiar todo"`); `Cobrar` envía únicamente el total calculado y conserva el campo concepto independiente; doble toque a `Cobrar` crea 1 solo cobro; error `422` o falta de conexión conserva `"60 + 50"` en Teclado; `Nuevo cobro` y cancelación confirmada limpian expresión y concepto; a `320 × 640 px` con `6` o más importes no hay scroll horizontal (`document.documentElement.scrollWidth <= window.innerWidth`, `CE-008`).
  - **RF**: RF-028 a RF-042, RF-045 a RF-048 (CE-002, CE-008)
  - **Dep.**: ninguna (rama propia de `#100` desde `main`, con `uv sync --directory backend --locked` corrido en local, `QT-3`)
  - **Hecho cuando**: las pruebas nuevas existen en `web/tests/test_teclado.py` y fallan porque `evaluar_expresion`, las teclas nuevas y la vista de 4 columnas aún no existen.
- [ ] T008 [P] [US2] Agregar prueba de renderizado seguro (`textContent` y cero violaciones de CSP / `eval`) para la expresión de calculadora en `web/tests/test_seguridad.py`
  - Comprobar que ni `[data-prueba="expresion"]` ni `[data-prueba="monto"]` ejecutan HTML ni disparan `securitypolicyviolation` o `eval`.
  - **RF**: RF-031, RF-043
  - **Dep.**: ninguna (rama propia de `#100` desde `main`, con `uv sync --directory backend --locked` corrido en local, `QT-3`)
  - **Hecho cuando**: la prueba existe en `web/tests/test_seguridad.py` y falla porque `[data-prueba="expresion"]` aún no existe.

### Implementación de F2

- [ ] T009 [US2] Implementar el motor de calculadora exacta con `BigInt` en `web/js/teclado.js`
  - Exportar `aplicar_tecla(expresion, tecla)`, `evaluar_expresion(expresion)`, `cobrar_activo(expresion)` y `monto_libre_activo(expresion)` cumpliendo `contracts/calculadora-y-descarga.md §3` y `data-model.md §2`:
    - Operando individual: máx. `5` dígitos enteros, máx. `2` decimales, un solo `.`, `.` inicial → `"0."`, `"0"` + dígito → reemplaza `"0"` (incluido tras operador: `"25 + 0"` + `"7"` → `"25 + 7"`, `QP-5`).
    - Operadores `" + "` y `" × "`: máximo `20` operandos (ignorar `+`/`×` al llegar a 20); quitar `.` final al pulsar operador (`"25."` + `"mas"` → `"25 + "`); operador sobre expresión vacía se ignora; operador sobre operador final lo reemplaza; `"borrar"` quita `" + "` / `" × "` (3 chars) o último carácter del operando; `"limpiar"` → `""`.
    - Evaluación exacta `BigInt` sin `Number` ni `eval`: precedencia `×` antes que `+`, suma en escala máxima `S`, redondeo `HALF_UP` a escala 2; si termina en operador final, calcula total parcial del prefijo anterior con `incompleta: true` y `monto_envio: null`; si el último operando termina en punto colgante (`"25."`, `"25 + 0."`, `"25 + 10."`), se evalúa como completo (`incompleta: false`, `QP-5`); si `total_centavos > 99_999_999n` (`$999,999.99`), devolver `{ desbordado: true, total_centavos: null, texto_total: "El total es demasiado grande", monto_envio: null }` (nunca notación científica).
    - `cobrar_activo`: `expresion !== "" && !incompleta && !desbordado && total_centavos > 0n`.
    - `monto_libre_activo`: `true` únicamente para entradas sin operadores cuyo valor numérico sea `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`), y `false` ante cualquier operador (`"0 × 25"`, `"0 + "`) o valor `> 0` (`RF-038`, `QP-1`).
  - **RF**: RF-028, RF-029, RF-030, RF-033, RF-034, RF-035, RF-036, RF-037, RF-038, RF-045, RF-046, RF-047
  - **Dep.**: T007
  - **Hecho cuando**: todas las pruebas unitarias de `teclado.js` en T007 pasan y `web/tests/test_teclado.py:97-116` sigue en verde sin haberse modificado.
- [ ] T010 [US2] Actualizar la vista Teclado (4 columnas, expresión secundaria, `aria-label`, limpieza y conservación en error) en `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css`
  - `web/js/vistas.js`: agregar `<div data-prueba="expresion" class="expresion" hidden>` encima de `[data-prueba="monto"]` (asignado solo por `textContent`); cuadrícula de 4 columnas manteniendo orden `1–9` (`1 2 3 +`, `4 5 6 ×`, `7 8 9 ⌫`, `. 0 C` con `C` en 2 columnas); cambiar texto visible de `tecla-borrar` de `"Borrar"` a `"⌫"` conservando `data-prueba="tecla-borrar"` (`QP-5`); agregar `aria-label` en español (`"Sumar"`, `"Multiplicar"`, `"Borrar último carácter"`, `"Limpiar todo"`, `RF-048`). **Regla de pintado de `[data-prueba="monto"]` (`QT-2`)**: cuando `!evaluacion.tiene_operadores`, seguir pintando el texto crudo `` `$${expresion}` `` (`"$"`, `"$0."`, `"$7"`, `"$25."`, exigido por 10+ pruebas existentes y `contracts/vistas-cobro-rapido.md:18`); usar `evaluacion.texto_total` únicamente cuando haya operadores o desbordamiento (`"El total es demasiado grande"`, sin anteponer un segundo `$`).
  - `web/js/app.js`: manejar `expresion` en el estado de Teclado; en `al_cobrar()` añadir la guarda explícita `if (!cobrar_activo(expresion) || monto_envio === null) return;` (`QT-2`) para impedir invocar `pedir_cobro(null)` (Monto libre accidental, `web/js/app.js:167`), enviar `evaluar_expresion(expresion).monto_envio` manteniendo `concepto` independiente (`RF-039`); si falla `crear_cobro` o llega sin `qr_imagen`, volver a Teclado conservando la expresión completa (`RF-040`); limpiar expresión y concepto en `Nuevo cobro` y cancelación confirmada (`RF-041`).
  - `web/estilos.css`: `.teclas` en `grid-template-columns: repeat(4, minmax(0, 1fr))` con `min-height: 44px`, `.tecla-limpiar { grid-column: span 2; }`, y `.expresion` con `overflow-wrap: anywhere` / `overflow-x: auto` sin provocar desplazamiento horizontal en `320 px` (`RF-042`, `CE-008`).
  - **RF**: RF-028, RF-031, RF-032, RF-035 a RF-042, RF-047, RF-048 (CE-008)
  - **Dep.**: T007, T008, T009
  - **Hecho cuando**: T007, T008 y toda la suite web en Chromium y WebKit pasan en verde.
- [ ] T011 [US2] Cierre de F2: pruebas y ruff en verde, sección F2 en `specs/004-cobro-rapido/verification-guide.md` y commit sugerido
  - Commit sugerido (PR del issue `#100` — usar `Closes #100` en el PR y anotar el estado de `docs/qa/` en «Qué quedó pendiente» de `.github/pull_request_template.md`, `QT-6`): `feat(004): calculadora exacta con suma y multiplicación en el teclado de cobro (F2)`.
  - **RF**: RF-028 a RF-042, RF-045 a RF-048
  - **Dep.**: T010
  - **Hecho cuando**: todos los comandos de la regla 5 dan verde, existe la sección F2 en `specs/004-cobro-rapido/verification-guide.md` y el estado registra F2 terminada.

**Punto de control**: la calculadora funciona completa en Chromium y WebKit desde `320 px` de ancho, de forma independiente al selector de duración y sin cambios en el servidor.

---

## Fase 3 (F3): Selector de duración, cuenta `H:MM:SS` y tope de 20 min en anteriores largos (`#121`, Corte 1 · 28 nov · Historia 1 web y recuperación de Historia 5)

**Objetivo**: ofrecer en la vista Teclado el selector de duración C1 (`6 min`, `10 min` por defecto, `30 min`, `1 h`, `24 h`), enviarlo en `Cobrar` y `Monto libre`, reiniciar a `10 min` (salvo en error), formatear la cuenta regresiva como `H:MM:SS` desde 60 min con error `< 2 s` frente al servidor, recuperar cobros tras recargar y acotar a 20 min la escucha de cobros anteriores `> 1 h` (`RF-044`). Rama propia del issue `#121` (Corte 1) saliendo **tras unir `#100`** (`plan.md §8.1`, `QP-7`).

**Prueba independiente**: en Playwright (Chromium y WebKit) contra `servidor_simulado.py`, elegir `24 h`, generar cobro y ver `24:00:00` incluso con reloj del navegador desfasado 5 min (`CE-005`), comprobar reinicio a `10 min` en `Nuevo cobro`/cancelación/recarga y conservación tras error `422`, recargar recuperando un cobro de `30 min` y validar que al pasar un cobro de `24 h` a anterior su canal y polling se detienen a los 20 min (incluso tras recarga y con recuperación diferida).

### Pruebas de F3 (primero, deben fallar antes de implementar)

- [ ] T012 [US1] Ampliar `web/tests/servidor_simulado.py` para aceptar y validar `duracion_segundos` (defecto `600`, rango `360..86400` en C1), calcular `expira_en`/`fin_ventana` por cobro y registrar las peticiones (`R-9`, `QT-3`)
  - Aceptar parámetro configurable `permitir_sin_vencimiento: bool = False` (en F3 en `False`; en F7 pasará a `True`) y exponer el método `fijar_sin_vencimiento(activo: bool)`, restableciendo `permitir_sin_vencimiento` a su valor por defecto dentro de `reiniciar()` (instancia única de alcance de sesión en `web/tests/conftest.py:92-105`, `QT-3`).
  - Si `duracion_segundos` falta o es `None` → `600`; rechazar con `422` (`"Elige una duración entre 6 minutos y 24 horas"`) booleanos, decimales, texto, `< 360`, `> 86400` y `0` en modo C1.
  - Actualizar `_Cobro`, `_desde_dict()` (con defecto `600` cuando un dict parcial de `responder_crear(cuerpo=...)` omita `duracion_segundos`, `QT-3`) y `_estado` para leer `cobro.expira_en` (permitiendo `int | None` para F7) en lugar de una constante fija de 600 s; incluir `"duracion_segundos"` en el objeto cobro devuelto.
  - **RF**: RF-016, RF-019, RF-020, RF-024 (R-9)
  - **Dep.**: T011 (rama propia de `#121` basada tras unir `#100`; independiente de F1 backend al probar contra `servidor_simulado.py`, `QT-3`)
  - **Hecho cuando**: todas las pruebas existentes de `web/tests/` siguen pasando contra el simulado actualizado y éste valida y registra `duracion_segundos`.
- [ ] T013 [P] [US1] Actualizar los 2 asertos de pantalla existentes (`web/tests/test_crear_y_mostrar_qr.py:313` y `web/tests/test_monto_libre_y_reuso.py:54` esperando `"duracion_segundos": 600`, `C-13`, `QP-2`) y crear `web/tests/test_duracion_y_descarga.py` con las pruebas C1 de selector, cuenta `H:MM:SS`, helpers de `cuenta.js`, recuperación y tope de 20 min
  - Conservar intactas la prueba unitaria `web/tests/test_crear_y_mostrar_qr.py:128` (`QP-2`) y toda la suite `web/tests/test_recuperar.py` (`QP-3`).
  - Casos en `web/tests/test_duracion_y_descarga.py`:
    - `test_selector_de_duracion_muestra_atajos_c1_con_diez_minutos_por_defecto`: `role="radiogroup"` + `aria-label="Duración del QR"`, opciones `duracion-360`, `duracion-600` (`aria-checked="true"`), `duracion-1800`, `duracion-3600`, `duracion-86400`; `duracion-0` ausente en C1.
    - `test_crear_cobro_y_monto_libre_envian_duracion_elegida`: enviar `1800` con `Cobrar` y `360` con `Monto libre`.
    - `test_duracion_se_reinicia_a_diez_minutos_en_nuevo_cobro_cancelacion_y_recarga_pero_se_conserva_en_error`: comprobar `RF-017` y `RF-018` (422, 502 y falta de `qr_imagen`).
    - `test_cuenta_regresiva_muestra_h_mm_ss_desde_una_hora_y_m_ss_debajo_con_reloj_desfasado_cinco_minutos` (unitaria en Chromium + pantalla): `24:00:00`, `1:00:00`, `59:59`, `6:00`, y margen `< 2 s` con el reloj del navegador adelantado/atrasado 5 min respecto a `hora_servidor` (`CE-005`).
    - `test_helpers_de_cuenta_para_finitos_y_sin_vencimiento` (`@pytest.mark.only_browser("chromium")`, `QT-4`): pruebas unitarias para las 4 funciones/ramas nuevas de `web/js/cuenta.js`: `es_sin_vencimiento` (`expira_en === null` o `duracion_segundos === 0` vs finito), `restante` devolviendo `null` en sin vencimiento, `restante_ventana` y `puede_reabrir_qr` en cobros finitos y sin vencimiento (dentro y fuera de su ventana, `RF-021`, `RF-022`, `QP-4`).
    - `test_recarga_recupera_cobro_con_duracion_elegida_y_tiempo_restante_real`: `30 min` en pantalla y `1 h` en anterior recuperan su restante real (`RF-024`).
    - `test_cobro_anterior_de_24_horas_acota_escucha_a_20_minutos_incluso_tras_recargar_y_en_recuperacion_diferida`: comprueba `RF-044` (cierre de canal/polling a los 20 min con reloj simulado, persistencia de `topes_anteriores` y su omisión cuando solo hay cobros `<= 1 h` [`QP-3`], y cálculo diferido de `tope_local` cuando `pasar_a_anterior()` ocurre con `cobro === null` [`QP-4`]).
    - `test_selector_y_cuenta_sin_desplazamiento_horizontal_en_320px`: en `320 × 640 px` (`CE-008`, `RF-042`, `RF-048`).
  - **RF**: RF-013, RF-015, RF-016, RF-017, RF-018, RF-019, RF-020, RF-021, RF-022, RF-024, RF-042, RF-044, RF-048 (CE-005, CE-008)
  - **Dep.**: T012
  - **Hecho cuando**: los 2 asertos actualizados y las pruebas nuevas de `web/tests/test_duracion_y_descarga.py` fallan por la razón esperada antes de implementar.
- [ ] T014 [P] [US5] Agregar pruebas de validación estricta y descarte de `topes_anteriores` malformados en `localStorage` dentro de `web/tests/test_seguridad.py`
  - Probar claves extrañas en `pago_facil_escucha`, IDs inválidos según `/^[A-Za-z0-9_-]{1,32}$/`, IDs que no figuran en `anteriores`, topes `<= 0`, negativos, flotantes, booleanos o texto, así como rechazo de claves reservadas (`"__proto__"`, `"constructor"`, `"prototype"`) y prototipos no planos en `topes_anteriores` (`QT-7`) → el registro entero devuelve `null` al leer (`RF-077` spec 002, `data-model.md §3.2`).
  - **RF**: RF-024, RF-043, RF-044
  - **Dep.**: T012
  - **Hecho cuando**: las pruebas existen en `web/tests/test_seguridad.py` y fallan porque `memoria.js` aún rechaza o ignora `topes_anteriores`.

### Implementación de F3

- [ ] T015 [P] [US1] Actualizar `web/js/cuenta.js` con formato `H:MM:SS` / `M:SS`, `es_sin_vencimiento`, `restante_ventana` y `puede_reabrir_qr` (`DP-5`, `QP-4`)
  - `formato(segundos)`: devuelve `H:MM:SS` si `segundos >= 3600` (minutos y segundos de 2 dígitos) y `M:SS` si `segundos < 3600`.
  - `es_sin_vencimiento(cobro)`: `cobro.expira_en == null || cobro.duracion_segundos === 0`.
  - `restante(cobro, desfase, ahora)`: devuelve `null` si `es_sin_vencimiento(cobro)`, o `cobro.expira_en - (ahora + desfase)` en finitos.
  - `restante_ventana(cobro, desfase, ahora)`: `cobro.fin_ventana - (ahora + desfase)`.
  - `puede_reabrir_qr(cobro, desfase, ahora)` (`QP-4`): `es_sin_vencimiento(cobro) ? restante_ventana(cobro, desfase, ahora) >= 1 : restante(cobro, desfase, ahora) >= 1`.
  - **RF**: RF-019, RF-020, RF-021, RF-022
  - **Dep.**: T013
  - **Hecho cuando**: las pruebas unitarias de `cuenta.js` en T013 y las pruebas existentes de `test_vencido_y_nuevo.py` pasan en verde.
- [ ] T016 [P] [US1] Ampliar `crear_cobro(monto, concepto, duracion_segundos)` en `web/js/servidor.js` dejando `duracion_segundos` opcional (`QP-2`)
  - Construir el cuerpo `{ monto, concepto }` y asignar `cuerpo.duracion_segundos = duracion_segundos` únicamente cuando `duracion_segundos !== undefined` (conservando intacta `web/tests/test_crear_y_mostrar_qr.py:128`).
  - **RF**: RF-016, RF-043
  - **Dep.**: T013
  - **Hecho cuando**: `crear_cobro` incluye `duracion_segundos` cuando se pasa y omite la clave cuando es `undefined`, pasando `test_crear_y_mostrar_qr.py:128`.
- [ ] T017 [P] [US5] Implementar `topes_anteriores` validado estrictamente en `web/js/memoria.js`, el tope local de 20 min (con cálculo diferido) y `cerrar_en_pantalla()` en `web/js/escucha.js` (`DP-7`, `QP-3`, `QP-4`, `QT-1`, `QT-2`, `QT-7`)
  - En `web/js/memoria.js`: aceptar `topes_anteriores` opcional en `forma_valida` con endurecimiento (`QT-7`): validar `Object.getPrototypeOf(topes) === Object.prototype`, rechazar claves reservadas (`"__proto__"`, `"constructor"`, `"prototype"`) o construir el mapa con `Object.create(null)`, comprobar que cada clave pasa `ID_VALIDO` (`/^[A-Za-z0-9_-]{1,32}$/`) y existe en `anteriores`, y exigir `typeof v === "number" && Number.isSafeInteger(v) && v > 0`; tanto `guardar()` como `leer()` omiten la clave `"topes_anteriores"` cuando está ausente o vacía (`web/tests/test_recuperar.py:109-112,314`, `QP-3`, `QT-1`), manteniendo intacto `web/tests/test_recuperar.py`.
  - En `web/js/escucha.js`: constantes `TOPE_ANTERIOR_LARGO_SEGUNDOS = 1200` y `UMBRAL_COBRO_LARGO_SEGUNDOS = 3600`; definir `es_cobro_largo(cobro)` (`duracion_segundos === 0 || duracion_segundos > 3600 || expira_en == null || (expira_en - creado_en) > 3600`); al llamar a `pasar_a_anterior()` sobre cobro largo, fijar `this.tope_local = Math.min(fin_ventana, ahora_servidor_estimado + 1200)`; si `this.cobro === null` al pasar a anterior, diferir el cálculo de `this.tope_local` a la primera respuesta de recuperación si `es_anterior && tope_local === null` (`QP-4`); cerrar la escucha con `{ tipo: "fin", escucha: this }` y `this.terminar()` cuando `ahora_servidor_estimado >= this.tope_local`, y descartar en recarga los anteriores cuyo `tope_local` ya venció. Además, exponer el método público `cerrar_en_pantalla()` en `Escuchas` (`QT-2`, delegando a `_cerrar(this._en_pantalla, "fin")` para cerrar `EventSource`, detener polling, soltar Wake Lock y limpiar `en_pantalla` en `localStorage`) para que `empezar_cuenta` en `T035` pueda invocarlo limpiamente.
  - **RF**: RF-023, RF-024, RF-043, RF-044
  - **Dep.**: T013, T014
  - **Hecho cuando**: T014 y las pruebas de recuperación y tope de 20 min pasan sin romper `web/tests/test_recuperar.py`.
- [ ] T018 [US1] Integrar el selector de duración C1, el reinicio/conservación en error y `puede_reabrir_qr()` en los 4 sitios de vigencia/reapertura de `web/js/app.js`, junto con `web/js/vistas.js` y `web/estilos.css` (`DP-8`, `QP-2`, `QP-4`, `QT-2`)
  - `web/js/vistas.js`: agregar `[data-prueba="selector-duracion"]` (`role="radiogroup"`, `aria-label="Duración del QR"`) con los 5 chips C1: `duracion-360` ("6 min"), `duracion-600` ("10 min"), `duracion-1800` ("30 min"), `duracion-3600` ("1 h"), `duracion-86400` ("24 h"), cada uno con `role="radio"` y `aria-checked="true|false"`.
  - `web/js/app.js`: estado inicial `duracion_segundos = 600`; enviarlo siempre en `Cobrar` y `Monto libre` (`QP-2`); reiniciar a `600` en `Nuevo cobro`, cancelación confirmada y recarga volviendo a Teclado (`RF-017`); conservarlo ante rechazo, falta de red o llegada sin `qr_imagen` (`RF-018`); reemplazar con `puede_reabrir_qr()` exactamente los 4 chequeos de vigencia/reapertura (`web/js/app.js:88-89`, `:314-315`, `:398` y `:424-425`, `QP-4`, `QT-2`), dejando las guardas de vencimiento de `empezar_cuenta` (`web/js/app.js:382` y `:388`) protegidas bajo `!es_sin_vencimiento(actual)` (evitando que `null < 1 === true` en JS rompa QR sin vencimiento en C2, `QT-2`); persistir y restaurar `topes_anteriores` vía `memoria.js` y `escucha.js`.
  - `web/estilos.css`: `.selector-duracion` con `display: flex; flex-wrap: wrap; gap: 0.25rem; min-height: 44px`, sin desplazamiento horizontal en `320 px` (`RF-042`, `CE-008`).
  - **RF**: RF-013, RF-015, RF-016, RF-017, RF-018, RF-019, RF-020, RF-024, RF-042, RF-044, RF-048 (CE-005, CE-008)
  - **Dep.**: T015, T016, T017
  - **Hecho cuando**: T013, T014 y toda la suite web en Chromium y WebKit pasan en verde.
- [ ] T019 [US1] Cierre de F3: pruebas y ruff en verde, sección F3 en `specs/004-cobro-rapido/verification-guide.md` y commit sugerido
  - Commit sugerido (en la rama del issue `#121`, Corte 1): `feat(004): selector de duración, cuenta H:MM:SS y tope de 20 min en anteriores largos (F3)`.
  - **RF**: RF-013, RF-015, RF-016, RF-017, RF-018, RF-019, RF-020, RF-024, RF-042, RF-044, RF-048
  - **Dep.**: T018
  - **Hecho cuando**: todos los comandos de la regla 5 dan verde y la sección F3 está anotada en `specs/004-cobro-rapido/verification-guide.md`.

**Punto de control**: el selector C1, las duraciones enviadas a `POST /api/cobros`, el formato `H:MM:SS` con desfase y el tope de 20 min para anteriores `> 1 h` funcionan y están cubiertos en verde.

---

## Fase 4 (F4): Descargar imagen PNG del QR (`#121`, Corte 1 · 28 nov · Historia 3)

**Objetivo**: mostrar el botón **Descargar QR** en toda vista QR que tenga imagen (recién creado, recuperado tras recargar o reabierto con *Mostrar QR otra vez*), descargar un `.png` válido con nombre descriptivo saneado sin salir de la vista ni cortar la escucha de pagos, y mostrar un mensaje claro en español si el navegador falla al guardar. Continúa en la rama de `#121` (Corte 1).

**Prueba independiente**: generar un cobro (y probar también tras recarga y tras *Mostrar QR otra vez*), pulsar **Descargar QR**, verificar con `expect_download` de Playwright un archivo `.png` válido con el nombre esperado (`pago-facil-<monto-o-libre>-<concepto>.png`), comprobar que el canal sigue abierto y recibe un pago posterior, y forzar un fallo de descarga verificando el mensaje en español sin ocultar el QR.

### Pruebas de F4 (primero, deben fallar antes de implementar)

- [ ] T020 [P] [US3] Agregar pruebas unitarias de `nombre_archivo_qr` (`only_browser("chromium")`) y pruebas Playwright `expect_download` de **Descargar QR** en `web/tests/test_duracion_y_descarga.py`
  - Unitarias (`contracts/calculadora-y-descarga.md §4`): `25.5` + `"Tacos al pastor"` → `"pago-facil-25-50-tacos-al-pastor.png"`; `null` + `"Propina / Café"` → `"pago-facil-monto-libre-propina-cafe.png"`; `0.01` + `""` → `"pago-facil-0-01.png"`; `null` + `"!!!"` → `"pago-facil-monto-libre.png"`.
  - Pantalla (Chromium y WebKit):
    - `test_descargar_qr_guarda_png_con_nombre_descriptivo_sin_salir_ni_cortar_escucha`: `descargar-qr` tiene `aria-label="Descargar imagen del QR"`, el archivo descargado empieza con cabecera PNG `\x89PNG\r\n\x1a\n`, `vista-qr` sigue visible, el `EventSource` sigue `OPEN` y un pago posterior pasa a `vista-pagado` (`CE-006`).
    - `test_descargar_qr_disponible_tras_recargar_y_mostrar_qr_otra_vez`: comprobar `RF-025` en ambos flujos y sin desplazamiento horizontal en `320 px` (`CE-008`).
    - `test_error_al_descargar_qr_muestra_mensaje_sin_ocultar_qr`: al fallar `URL.createObjectURL` o llegar sin base64 válido, `[data-prueba="mensaje-descarga"]` muestra `"No se pudo descargar el QR. Intenta de nuevo."`, `[data-prueba="qr"]` sigue visible y la escucha continúa (`RF-027`).
  - **RF**: RF-025, RF-026, RF-027, RF-042, RF-048 (CE-006, CE-008)
  - **Dep.**: T019
  - **Hecho cuando**: las pruebas existen en `web/tests/test_duracion_y_descarga.py` y fallan porque aún no existen `web/js/descarga.js` ni el botón `descargar-qr`.
- [ ] T021 [P] [US3] Agregar pruebas de saneamiento de nombres PNG maliciosos y compatibilidad de `blob:` con la CSP en `web/tests/test_seguridad.py`
  - Conceptos con `../`, `\`, `<script>`, caracteres Unicode acentuados y símbolos producen nombres restringidos a `[a-z0-9-]` terminados en `.png`; descargar un QR no dispara ningún evento `securitypolicyviolation`.
  - **RF**: RF-026, RF-043
  - **Dep.**: T019
  - **Hecho cuando**: las pruebas existen en `web/tests/test_seguridad.py` y fallan porque `web/js/descarga.js` aún no existe.

### Implementación de F4

- [ ] T022 [US3] Crear `web/js/descarga.js` con `nombre_archivo_qr` y `descargar_qr` vía `Blob` y `URL.createObjectURL` (`DP-6`)
  - `nombre_archivo_qr(cobro)`: construir `pago-facil-<monto-o-libre>-<concepto>.png` en minúsculas, normalizando `NFD` sin diacríticos, reemplazando todo lo fuera de `[a-z0-9]` por `-`, colapsando guiones repetidos, recortando bordes `-` y acotando el concepto a `30` caracteres (si faltan monto y concepto, `"pago-facil-qr.png"`).
  - `descargar_qr(qr_imagen, cobro)`: validar base64 no vacío, decodificar con `atob` → `Uint8Array` → `new Blob([bytes], { type: "image/png" })` → `URL.createObjectURL(blob)` → `<a download="...">` → `click()` → `setTimeout(() => URL.revokeObjectURL(url), 1000)` dentro de `try/catch`; ante excepción devolver `{ ok: false, mensaje: "No se pudo descargar el QR. Intenta de nuevo." }`.
  - **RF**: RF-026, RF-027, RF-043
  - **Dep.**: T020, T021
  - **Hecho cuando**: las pruebas unitarias de T020 y las de saneamiento de T021 pasan en verde.
- [ ] T023 [US3] Agregar el botón **Descargar QR** y `mensaje-descarga` en `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css`
  - `web/js/vistas.js`: botón `[data-prueba="descargar-qr"]` (`aria-label="Descargar imagen del QR"`) visible siempre que `vista-qr` tenga `qr_imagen`; elemento `[data-prueba="mensaje-descarga"]` oculto por defecto y escrito solo con `textContent`.
  - `web/js/app.js`: invocar `descargar_qr(actual.qr_imagen, actual)` sin cambiar de vista ni detener escuchas; mostrar `mensaje-descarga` cuando `!resultado.ok` y limpiarlo al cambiar o reiniciar el cobro.
  - `web/estilos.css`: estilo táctil `min-height: 44px` del botón y aviso sin desbordar en `320 px`.
  - **RF**: RF-025, RF-026, RF-027, RF-042, RF-048 (CE-006, CE-008)
  - **Dep.**: T022
  - **Hecho cuando**: T020, T021 y toda la suite web en Chromium y WebKit pasan en verde.
- [ ] T024 [US3] Cierre de F4: pruebas y ruff en verde, sección F4 en `specs/004-cobro-rapido/verification-guide.md` y commit sugerido
  - Commit sugerido (PR del issue `#121`, Corte 1 completo F3+F4 — usar `Refs #121` en el PR y **no** `Closes #121`, porque `#121` cierra en `F7`/`T036`, y anotar el estado de `docs/qa/` en «Qué quedó pendiente» de `.github/pull_request_template.md`, `QT-6`): `feat(004): descarga local de la imagen PNG del QR con nombre descriptivo (F4)`.
  - **RF**: RF-025, RF-026, RF-027, RF-042, RF-043, RF-048
  - **Dep.**: T023
  - **Hecho cuando**: todos los comandos de la regla 5 dan verde y la sección F4 existe en `specs/004-cobro-rapido/verification-guide.md`.

**Punto de control**: todo el alcance funcional del Corte 1 (`F1`–`F4`) está implementado y probado en automático de forma independiente a `#119`.

---

## Fase 5 (F5): Verificación integral y cierre del Corte 1 (Puerta S2 · dom 29 nov · Hugo y Leonel)

**Objetivo**: validar de punta a punta el **Corte 1** integrado (`#120` C1 + `#100` + `#121` C1) en local y en la demo pública con cobros reales de `$0.01`, cumpliendo la Puerta S2 sin esperar a `#119`.

- [ ] T025 Ejecutar las suites completas del Corte 1 y comprobar manualmente `http://127.0.0.1:8000` a `320 × 640 px` siguiendo `specs/004-cobro-rapido/quickstart.md` §2 y §3
  - Correr `uv run --directory backend ruff check .`, `uv run --directory backend ruff format --check .`, `uv run --directory backend pytest -q`, `uv run --directory backend ruff check --config pyproject.toml ../web`, `uv run --directory backend ruff format --config pyproject.toml --check ../web` y `uv run --directory backend pytest ../web -q`.
  - Comprobar en navegador local a `320 × 640 px` cero desplazamiento horizontal, calculadora `3 × 25 + 20 = $95.00`, `C`, `⌫`, selector `30 min` y reinicio a `10 min`.
  - **RF**: RF-001 a RF-007, RF-013, RF-015 a RF-020, RF-024 a RF-048 (CE-003, CE-004, CE-005, CE-008)
  - **Dep.**: T006, T011, T024
  - **Hecho cuando**: todos los comandos están en verde y la inspección visual local queda anotada en `specs/004-cobro-rapido/verification-guide.md`.
- [ ] T026 Ejecutar los cobros reales de `$0.01` MXN del Corte 1 en la demo pública (Android e iPhone, únicamente con autorización expresa de Hugo) siguiendo `specs/004-cobro-rapido/quickstart.md` §4 pasos 1 a 4
  - Comprobar: (a) cobro de `$0.01` a `6 min` o `30 min` pagado desde la app del banco (`CE-001`) y tiempo de aparición del QR `<= 5 s` en 9 de 10 intentos (`CE-007`); (b) creación de `$0.01` con `24 h` verificando que pey acepta `expiration: 86400` en producción (si pey impone un tope menor, registrarlo como `TK-n` en `plan.md §14`); (c) cuenta `2 × 0.01 + 0.01 + 0.01 = $0.04` pagada y avisada (`CE-002`); (d) archivo `.png` descargado con **Descargar QR** escaneable en la app del banco (`CE-006`).
  - **RF**: RF-003, RF-016, RF-019, RF-020, RF-026, RF-029, RF-039 (CE-001, CE-002, CE-006, CE-007)
  - **Dep.**: T025 (y autorización explícita de Hugo en ese momento)
  - **Hecho cuando**: los cuatro comprobantes reales se cumplen y sus resultados (sin secretos ni datos bancarios) quedan registrados en `specs/004-cobro-rapido/verification-guide.md`.
- [ ] T027 Cierre de F5 (Fin del Corte 1 / Puerta S2): documentar sección F5 en `specs/004-cobro-rapido/verification-guide.md`, entregar insumos QA a Miguel (`#87`), anotar cualquier `TK-n` en `plan.md §14` y commit sugerido
  - Entregar `specs/004-cobro-rapido/quickstart.md` y `specs/004-cobro-rapido/verification-guide.md` (secciones `F1`–`F5`) a Miguel (`#87`) para la guía QA de Corte 1 en `docs/qa/` (`QT-6`).
  - Commit sugerido: `docs(004): verificación integral y cierre del Corte 1 para Puerta S2 (F5)`.
  - **RF**: RF-001 a RF-007, RF-013, RF-015 a RF-020, RF-024 a RF-048 (CE-001 a CE-008)
  - **Dep.**: T026
  - **Hecho cuando**: las pruebas están en verde, F5 está documentada, Miguel (`#87`) recibe los insumos para `docs/qa/` y el Corte 1 queda entregado para la Puerta S2 (dom 29 nov).

**Punto de control (Fin del Corte 1)**: duración configurable `6 min`–`24 h`, calculadora exacta y **Descargar QR** entregados y verificados con `$0.01` real.

---

## Fase 6 (F6): Migración `0004` y backend de QR sin vencimiento (`#119` Juan y `#120` Hugo · Corte 2 · 29–30 nov · Historia 4 servidor y validación de Historia 5)

**Objetivo**: habilitar `duracion_segundos: 0` (QR sin vencimiento, `expira_en = None / NULL`), con migración idempotente `0004` coordinada con `#119`, manteniendo `fin_ventana = creado_en + 86400`, cero transiciones a `vencido`, cierre de canal y conciliación a las 24 h y registro permanente de avisos firmados a las 48 h+.

**Prueba independiente**: aplicar `0004_cobros_sin_vencimiento.sql` dos veces contra PostgreSQL desechable (`PRUEBAS_DATABASE_URL`), confirmar permisos revocados en `cobros_con_estado` para `anon`/`authenticated`, crear cobros con `duracion_segundos: 0` (monto fijo y libre) y comprobar con `RelojFalso` que no vencen tras 24 h/48 h, cierran canal y concilian exactamente a las 24 h y registran un pago firmado a las 48 h sin duplicar (`CE-010`).

### Pruebas de F6 (primero, deben fallar antes de implementar)

- [ ] T028 [P] [US4] Actualizar `_versiones` a `["0001", "0002", "0003", "0004"]` (`C-14`, `QP-3`) y agregar pruebas SQL puras de idempotencia, permisos revocados en `cobros_con_estado` (`QP-6`) y `expira_en NULL` en `backend/tests/test_migraciones_postgres.py` y `backend/tests/test_esquema_postgres.py` (`#119`, Juan, `QT-3`)
  - En `backend/tests/test_migraciones_postgres.py`: actualizar las tres aserciones de `_versiones` (`:194`, `:271`, `:307`) a `["0001", "0002", "0003", "0004"]`; probar `test_migracion_0004_es_idempotente_y_admite_cobro_sin_vencimiento` ejecutando `0004` entero con `conexion.execute(sql)` dos veces sin fallar (**no** usar `_correr_script`, que divide el SQL por `;` y rompería `DO $$ ... $$`, `QT-3`), insertar cobro con `expira_en = NULL` y `fin_ventana > creado_en`, comprobar que `cobros_expira_mayor_creado`, `cobros_fin_ventana_mayor_creado` y `cobros_fin_ventana_mayor_expira` rechazan violaciones; verificar que `anon` y `authenticated` siguen sin permisos (`SELECT`) sobre `cobros_con_estado` tras `0004` (`QP-6`).
  - En `backend/tests/test_esquema_postgres.py`: `test_vista_cobros_con_estado_no_vence_cobro_sin_expira_en` (un cobro con `expira_en = NULL` creado hace 48 h sigue `'pendiente'` en `cobros_con_estado`). *(La prueba de guardado/carga en `AlmacenPostgres` con `expira_en = None` va en `T029` dentro de `backend/tests/test_almacen.py`, `QT-3`.)*
  - **RF**: RF-008, RF-009
  - **Dep.**: T027
  - **Hecho cuando**: las pruebas SQL nuevas existen y fallan porque todavía no existe `supabase/migraciones/0004_cobros_sin_vencimiento.sql`.
- [ ] T029 [P] [US4] Agregar pruebas de `duracion_segundos = 0`, persistencia en almacén (`AlmacenEnMemoria`/`AlmacenPostgres`), no vencimiento, cancelación pendiente, cierre/conciliación a 24 h y aviso firmado a 48 h en `backend/tests/test_crear_cobro.py`, `backend/tests/test_modelo.py`, `backend/tests/test_canal.py`, `backend/tests/test_conciliacion.py` y `backend/tests/test_almacen.py` (`QT-1`, `QT-3`, `QT-4`)
  - En `backend/tests/test_almacen.py`: prueba parametrizada (`AlmacenEnMemoria` y `AlmacenPostgres`, `QT-3`) de guardado y carga de un cobro con `expira_en = None` y `duracion_segundos == 0`.
  - `test_cobro_sin_vencimiento_envia_cero_a_pey_y_no_tiene_expira_en`: en `test_crear_cobro.py`, probar `duracion_segundos: 0` (monto fijo y monto libre → `expiration: 0` enviado a pey, `duracion_segundos == 0`, `expira_en is None`, `fin_ventana == creado_en + 86400`), retirar explícitamente `0` de los casos inválidos de `test_duracion_invalida_se_rechaza_sin_llamar_a_pey` creados en `T002` (`QT-1`) y actualizar las aserciones de mensaje 422 por duración inválida a `"Elige una duración entre 6 minutos y 24 horas, o sin vencimiento"` (`contracts/crear-cobro-duracion.md §4`).
  - `test_cobro_sin_vencimiento_nunca_vence_ni_emite_vencido`: en `test_modelo.py` y `test_canal.py` con `RelojFalso`, avanzar `> 600 s`, `> 86400 s` y `> 172800 s` verificando que `estado()` sigue `pendiente` y el canal nunca emite `vencido`.
  - `test_cobro_sin_vencimiento_cierra_canal_y_concilia_a_las_24_horas`: al alcanzar `creado_en + 86400`, el canal emite `fin` y cierra, y `LatidoDeConciliacion` ejecuta una sola conciliación.
  - `test_aviso_firmado_a_las_48_horas_registra_pago_en_cobro_sin_vencimiento`: en `test_conciliacion.py` (o `test_aviso_pey.py`), enviar aviso Standard Webhooks válido 48 h después y verificar registro sin duplicado (`estado == "pagado"`, `numero_de_pagos == 1`, `total_recibido`, `CE-010`).
  - `test_cancelar_cobro_sin_vencimiento_pendiente_registra_pago_si_llega_aviso_firmado` (`spec.md §4:241`, `QT-4`): cancelar un QR **Sin vencimiento** pendiente (incluso tras `> 10 min`) y comprobar que un aviso firmado posterior de pey pasa el cobro a `pagado` sin duplicar.
  - **RF**: RF-006, RF-007, RF-008, RF-009, RF-010, RF-011, RF-012, RF-043 (CE-010)
  - **Dep.**: T027
  - **Hecho cuando**: las pruebas nuevas existen y fallan porque `validar_duracion` aún rechaza `0` y `Cobro`/`canal.py`/`AlmacenPostgres` aún esperan `expira_en` no nulo.

### Implementación de F6

- [ ] T030 [US4] Crear la migración idempotente `supabase/migraciones/0004_cobros_sin_vencimiento.sql` (`#119`, Juan, `DP-2`, `QP-6`)
  - Seguir exactamente `data-model.md §1.4`:
    1. `alter table cobros alter column expira_en drop not null;`
    2. Bloque `DO $$ ... $$` sobre `pg_constraint` en `'public.cobros'::regclass` (`contype = 'c'`) para eliminar de forma idempotente cualquier `CHECK` existente que referencie `expira_en` distinto a los 3 checks nuevos.
    3. Crear si no existen los 3 checks con nombre fijo: `cobros_expira_mayor_creado` (`check (expira_en is null or expira_en > creado_en)`), `cobros_fin_ventana_mayor_creado` (`check (fin_ventana > creado_en)`) y `cobros_fin_ventana_mayor_expira` (`check (expira_en is null or fin_ventana >= expira_en)`).
    4. `create or replace view cobros_con_estado with (security_invoker = true)` con `when c.expira_en is not null and now() >= c.expira_en then 'vencido'`.
    5. `revoke all on cobros_con_estado from anon, authenticated;`
  - El PR de migración `0004` de Juan usa `Closes #119` (`QT-6`).
  - **RF**: RF-008, RF-009
  - **Dep.**: T028
  - **Hecho cuando**: las pruebas de migración y esquema SQL en T028 pasan contra PostgreSQL desechable (y el PR de `#119` con `Closes #119` queda listo).
- [ ] T031 [US4] Habilitar `expira_en: int | None` y `duracion_segundos = 0` en `backend/app/cobros.py`, `backend/app/canal.py`, `backend/app/almacen.py`, `backend/app/almacen_postgres.py` y `backend/app/main.py` (`#120` Corte 2, Hugo, `DP-2`, `DP-3`)
  - `backend/app/cobros.py`: `Cobro.expira_en: int | None`; en `RepositorioCobros.nuevo`, cuando `expiracion == 0`, fijar `expira_en = None` y `fin_ventana = creado_en + 86400`; en `Cobro.estado(ahora)`, comprobar `if self.expira_en is not None and ahora >= self.expira_en: return VENCIDO`.
  - `backend/app/canal.py`: en `_espera`, comprobar `if cobro.expira_en is not None and ahora < cobro.expira_en:`.
  - `backend/app/almacen.py`: `_CobroPlano.expira_en: int | None`.
  - `backend/app/almacen_postgres.py`: en `_cobro` (`:398`), usar `expira_en=_unix_o_nada(fila["expira_en"])` (`_instante` en `:450` ya acepta `None`).
  - `backend/app/main.py`: llamar a `validar_duracion(..., permitir_sin_vencimiento=True)` aceptando `0` y devolviendo 422 `"Elige una duración entre 6 minutos y 24 horas, o sin vencimiento"` para otros valores fuera de rango.
  - **RF**: RF-006, RF-007, RF-008, RF-009, RF-010, RF-011, RF-012, RF-043 (CE-010)
  - **Dep.**: T029, T030
  - **Hecho cuando**: T028, T029 y toda la suite del backend (incluida `PRUEBAS_DATABASE_URL` con `tests/test_almacen.py`) pasan en verde.
- [ ] T032 [US4] Cierre de F6: pruebas de backend, PostgreSQL y ruff en verde, sección F6 en `specs/004-cobro-rapido/verification-guide.md` y commits sugeridos
  - Commits sugeridos (`QT-6`): `feat(004): migración 0004 para cobros sin vencimiento (#119)` (PR de Juan con `Closes #119`) y `feat(004): soporte de cobros sin vencimiento en el servidor y almacén (F6)` (PR de Hugo Corte 2 con `Closes #120`).
  - **RF**: RF-006, RF-007, RF-008, RF-009, RF-010, RF-011, RF-012, RF-043 (CE-010)
  - **Dep.**: T031
  - **Hecho cuando**: todos los comandos de la regla 5 (incluido PostgreSQL con `tests/test_almacen.py` en local o CI) dan verde y la sección F6 está documentada en `specs/004-cobro-rapido/verification-guide.md`.

**Punto de control**: el servidor y PostgreSQL soportan `duracion_segundos: 0` (`expira_en = NULL`), nunca marcan vencido un QR sin vencimiento, concilian a las 24 h y registran webhooks días después.

---

## Fase 7 (F7): Opción "Sin vencimiento" en la web (`#121` Corte 2 · 30 nov – 1 dic · Leonel · Historia 4 web y recuperación de Historia 5)

**Objetivo**: mostrar la opción **Sin vencimiento** (`duracion-0`) en el selector de duración, mostrar `"Sin vencimiento"` en lugar de la cuenta regresiva, aplicar la transición idempotente de fin de 24 h en vista QR (por evento `fin` o por reloj local si el SSE cayó, ocultando `Cancelar cobro` y conservando `Descargar QR` y `Nuevo cobro`) y en *Pago recibido* (ocultando `Mostrar QR otra vez`), recuperar tras recarga y acotar a 20 min cuando pase a cobro anterior.

**Prueba independiente**: en Chromium y WebKit contra `servidor_simulado.py`, seleccionar **Sin vencimiento**, generar un cobro (monto fijo y monto libre), comprobar `"Sin vencimiento"` y `Descargar QR`, comprobar que tras 10 min no vence, simular las 24 h tanto por SSE `fin` como por reloj congelado con SSE cortado (con y sin *Mostrar QR otra vez*), recargar dentro de 24 h y comprobar el tope de 20 min al pasar a anterior.

### Pruebas de F7 (primero, deben fallar antes de implementar)

- [ ] T033 [US4] Habilitar `duracion_segundos = 0` (modo C2) por defecto en `web/tests/servidor_simulado.py` (`QT-3`)
  - Cambiar el valor por defecto del simulado a `permitir_sin_vencimiento = True` y asegurar que `reiniciar()` restablece `permitir_sin_vencimiento = True` por defecto en modo C2 (conservando `fijar_sin_vencimiento(False)` para pruebas específicas si hiciera falta, `QT-3`): si `duracion_segundos == 0`, crear `_Cobro` con `expira_en = None` y `fin_ventana = creado_en + 86400`; `_estado` nunca devuelve `"vencido"` si `expira_en is None`; rechazar otros inválidos con `422` `"Elige una duración entre 6 minutos y 24 horas, o sin vencimiento"`.
  - **RF**: RF-014, RF-016, RF-021, RF-024
  - **Dep.**: T032
  - **Hecho cuando**: el servidor simulado acepta `duracion_segundos: 0` devolviendo `expira_en: None`, `reiniciar()` restaura modo C2 y las pruebas previas de `web/tests/` siguen en verde.
- [ ] T034 [US4] Actualizar el aserto C1 del selector (`T013`, `QT-1`) y agregar pruebas Playwright de **Sin vencimiento** en `web/tests/test_duracion_y_descarga.py` (`QT-1`, `QT-4`)
  - Actualizar `test_selector_de_duracion_muestra_atajos_c1_con_diez_minutos_por_defecto` (creada en `T013`) para esperar en C2 las 6 opciones incluida `duracion-0` (`QT-1`).
  - `test_selector_incluye_sin_vencimiento_y_crea_cobro_con_etiqueta_sin_vencimiento`: `duracion-0` visible con etiqueta `"Sin vencimiento"`, monto fijo y monto libre envían `duracion_segundos: 0`, `[data-prueba="cuenta"]` muestra `"Sin vencimiento"`, `descargar-qr` visible y al avanzar > 10 min nunca pasa a `vista-vencido`.
  - `test_sin_vencimiento_al_terminar_24_horas_en_vista_qr_oculta_cancelar_y_muestra_aviso`: probar ambos disparadores (`QP-4`: evento SSE `fin` y respaldo por reloj local en `empezar_cuenta` con SSE cortado, tanto recién creado como con `qr_reabierto = true`), comprobando que permanece en `vista-qr`, muestra `[data-prueba="aviso-fin-escucha"]` con `"Este QR sigue vigente, pero ya terminaron las 24 horas de avisos en vivo en esta pantalla."`, oculta `[data-prueba="cancelar"]` y mantiene `qr`, `descargar-qr` y `nuevo-cobro`.
  - `test_sin_vencimiento_en_pago_recibido_oculta_mostrar_qr_al_cumplir_24_horas`: dentro de 24 h `mostrar-qr` visible; al cumplirse 24 h se oculta manteniendo `nuevo-cobro` (`RF-022`).
  - `test_cancelar_qr_sin_vencimiento_pendiente_reinicia_selector_y_acota_escucha_a_20_min` (`spec.md §4:241`, `QT-4`): cancelar un QR **Sin vencimiento** pendiente reinicia el selector a `10 min` (`RF-017`) y acota la escucha del cobro cancelado como anterior a `20 min` (`RF-044`).
  - `test_error_al_crear_cobro_sin_vencimiento_conserva_duracion_cero_seleccionada` (`RF-018`, `QT-4`): ante fallo `502` o `422` al crear con `duracion-0`, al volver a Teclado sigue seleccionada `duracion-0`.
  - `test_sin_vencimiento_recupera_tras_recarga_y_acota_a_20_min_como_anterior`: recuperación con `"Sin vencimiento"` (`RF-024`) y tope de 20 min como anterior (`RF-044`).
  - `test_selector_con_sin_vencimiento_sin_desplazamiento_horizontal_en_320px`: las 6 opciones visibles en `320 × 640 px` sin scroll horizontal (`RF-042`, `CE-008`, `RF-048`).
  - **RF**: RF-013, RF-014, RF-016, RF-017, RF-018, RF-021, RF-022, RF-023, RF-024, RF-042, RF-044, RF-048 (CE-008)
  - **Dep.**: T033
  - **Hecho cuando**: el aserto actualizado y las pruebas nuevas existen en `web/tests/test_duracion_y_descarga.py` y fallan por la razón esperada antes de implementar.

### Implementación de F7

- [ ] T035 [US4] Implementar la opción **Sin vencimiento**, la etiqueta `"Sin vencimiento"` y la transición idempotente de fin de 24 h en `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css` (`DP-5`, `QP-4`, `QT-2`)
  - `web/js/vistas.js`: agregar botón `duracion-0` (`role="radio"`, texto `"Sin vencimiento"`) dentro de `selector-duracion`, y `[data-prueba="aviso-fin-escucha"]` (`hidden` por defecto, escrito solo con `textContent`) en `vista-qr`.
  - `web/js/app.js`: en `pintar_qr_actual()` (`web/js/app.js:344-349`, `QT-2`), devolver `"Sin vencimiento"` en `[data-prueba="cuenta"]` cuando `es_sin_vencimiento(actual)` sin llamar a `formato(null)` (`RF-021`); conservar `duracion_segundos = 0` si falla al crear (`RF-018`) y recuperar como `"Sin vencimiento"` tras recarga (`RF-024`); bifurcar `es_sin_vencimiento(actual)` al principio de `empezar_cuenta` antes de `web/js/app.js:382` y `:388` (`QT-2`, dejando `:382`/`:388` solo para `!es_sin_vencimiento(actual)`), disparando la transición idempotente de fin de 24 h llamada tanto desde `escuchas.fin` como desde `empezar_cuenta` cuando `restante_ventana(...) < 1` (`QP-4`):
    - si vista actual es `"qr"` (incluso cuando `qr_reabierto` es `true`), permanecer en `vista-qr` sin volver a `pago_recibido` ni pasar a `qr_vencido`, ocultar `cancelar`, mostrar `aviso-fin-escucha` con `"Este QR sigue vigente, pero ya terminaron las 24 horas de avisos en vivo en esta pantalla."`, detener el reloj y cerrar la escucha invocando `escuchas.cerrar_en_pantalla()` (`web/js/escucha.js`, expuesto en `T017`, `QT-2`), manteniendo `descargar-qr` y `nuevo-cobro`;
    - si vista actual es `"pago_recibido"`, ocultar `mostrar-qr` manteniendo `nuevo-cobro` (`RF-022`).
  - `web/estilos.css`: asegurar ajuste de las 6 opciones de duración y de `aviso-fin-escucha` sin scroll horizontal en `320 px` (`RF-042`, `CE-008`).
  - **RF**: RF-014, RF-016, RF-018, RF-021, RF-022, RF-023, RF-024, RF-042, RF-044, RF-048 (CE-008)
  - **Dep.**: T034
  - **Hecho cuando**: T034 y toda la suite web en Chromium y WebKit pasan en verde.
- [ ] T036 [US4] Cierre de F7: pruebas y ruff en verde, sección F7 en `specs/004-cobro-rapido/verification-guide.md` y commit sugerido
  - Commit sugerido (PR del issue `#121`, Corte 2 — usar `Closes #121` en el PR y anotar el estado de `docs/qa/` en «Qué quedó pendiente» de `.github/pull_request_template.md`, `QT-6`): `feat(004): opción Sin vencimiento y aviso de fin de escucha de 24 h en la web (F7)`.
  - **RF**: RF-014, RF-016, RF-018, RF-021, RF-022, RF-023, RF-024, RF-042, RF-044, RF-048
  - **Dep.**: T035
  - **Hecho cuando**: todos los comandos de la regla 5 dan verde y la sección F7 existe en `specs/004-cobro-rapido/verification-guide.md`.

**Punto de control (Fin del Corte 2 implementado)**: toda la web y el servidor cumplen **Sin vencimiento** (`RF-008` a `RF-012`, `RF-014`, `RF-021` a `RF-024`) en pruebas automáticas.

---

## Fase N (FN): Pulido, aplicación de `C-12`–`C-14`, seguridad y validación final (`1 dic` · Hugo y Leonel)

**Propósito**: alinear las specs previas (`C-12`, `C-13`, `C-14`), ejecutar la revisión de seguridad de punta a punta, comprobar el cobro real de `$0.01` Sin vencimiento (`CE-009`) y cerrar `quickstart.md` y `verification-guide.md`.

- [ ] T037 [P] Aplicar los cambios aprobados `C-12`, `C-13` (ampliado por `QT-5` con `RF-046`, `RF-049`, `RF-070` de spec 002) y `C-14` en `specs/001-backend-mvp/spec.md`, `specs/001-backend-mvp/data-model.md`, `specs/001-backend-mvp/contracts/crear-cobro.md`, `specs/001-backend-mvp/contracts/canal-avisos.md`, `specs/002-web-mvp/spec.md`, `specs/002-web-mvp/data-model.md`, `specs/002-web-mvp/contracts/vistas.md`, `specs/002-web-mvp/contracts/uso-del-servidor.md`, `specs/003-infraestructura-demo/spec.md`, `specs/003-infraestructura-demo/data-model.md`, `specs/003-infraestructura-demo/contracts/comando-migraciones.md`, `backend/README.md` y `web/README.md`, y marcar `Aplicado` en `specs/004-cobro-rapido/spec.md` §8.2 (`QT-5`)
  - Reflejar en `specs/002-web-mvp/spec.md` el alcance ampliado de `C-13` (`QT-5`): `RF-046` (ocultar *Cancelar cobro* a las 24 h en QR sin vencimiento), `RF-049` (acotar a 20 min la escucha como anterior en cobros cancelados `> 1 h`) y `RF-070` (al pulsar *Mostrar QR otra vez*, mostrar `"Sin vencimiento"` en Corte 2), además de los RF ya listados de spec 002.
  - **RF**: RF-001 a RF-048 (`C-12`, `C-13`, `C-14`)
  - **Dep.**: T036
  - **Hecho cuando**: las tres specs previas, sus contratos, sus modelos de datos y `backend/README.md` / `web/README.md` reflejan `duracion_segundos`, la calculadora, **Descargar QR** y **Sin vencimiento** (incluido `C-13` ampliado por `QT-5`), y la tabla §8.2 de `specs/004-cobro-rapido/spec.md` marca `C-12`, `C-13` y `C-14` como `Aplicado`.
- [ ] T038 [P] Ejecutar la revisión de seguridad de la Spec 004 (`plan.md §10`, Constitución flujo 6) y documentarla en `specs/004-cobro-rapido/verification-guide.md`
  - Comprobar con `git grep`: cero secretos en código, pruebas o documentos; cero `eval(` o `new Function(` en `web/js/`; cero asignaciones nuevas a `innerHTML` en `web/js/`; política CSP cerrada en `web/index.html`; validación estricta de `duracion_segundos` antes del límite por IP y de pey; verificación Standard Webhooks y deduplicación intactas en `POST /webhooks/pey`; `revoke all on cobros_con_estado from anon, authenticated` vigente tras `0004`; saneamiento de nombres PNG y validación de `topes_anteriores` en `memoria.js`.
  - **RF**: RF-006, RF-012, RF-026, RF-043, RF-044 (CE-003)
  - **Dep.**: T036
  - **Hecho cuando**: cada punto de seguridad queda verificado y anotado en la sección FN de `specs/004-cobro-rapido/verification-guide.md`.
- [ ] T039 Ejecutar el cobro real de `$0.01` MXN con **Sin vencimiento** (y otro de monto libre) en la demo pública (únicamente con autorización expresa de Hugo) siguiendo `specs/004-cobro-rapido/quickstart.md` §4 paso 5
  - Respaldar la base de la demo antes de aplicar `0004` (`docs/operacion-demo.md`), aplicar `0004`, generar un cobro `$0.01` con **Sin vencimiento** (y otro de monto libre), confirmar `"Sin vencimiento"`, descargar el QR PNG y pagarlo desde la app del banco verificando aviso visual y sonoro (`CE-009`).
  - **RF**: RF-008, RF-014, RF-021, RF-026 (CE-009)
  - **Dep.**: T038 (y autorización expresa de Hugo en ese momento; escritura secuencial tras `T038` en `specs/004-cobro-rapido/verification-guide.md`)
  - **Hecho cuando**: el pago real **Sin vencimiento** se completa y avisa `"Pago recibido"` de punta a punta, y la evidencia (sin secretos ni datos bancarios) queda en la sección FN de `specs/004-cobro-rapido/verification-guide.md`.
- [ ] T040 Validar `specs/004-cobro-rapido/quickstart.md` de punta a punta (§1 a §4) y marcar los criterios de finalización cumplidos en `specs/004-cobro-rapido/spec.md` §9
  - **RF**: RF-001 a RF-048 (CE-001 a CE-010)
  - **Dep.**: T037, T038, T039
  - **Hecho cuando**: cada sección de `quickstart.md` (§1 a §4) está enlazada a su resultado verificado en `verification-guide.md` y todas las casillas de `spec.md §9` quedan completadas.
- [ ] T041 Cierre de FN: suites completas en verde, `specs/004-cobro-rapido/verification-guide.md` completa, entrega final a Miguel (`#87`), estado final en `tasks.md` y commit sugerido
  - Entregar la versión final de `specs/004-cobro-rapido/quickstart.md` y `specs/004-cobro-rapido/verification-guide.md` (secciones `F1`–`FN`) a Miguel (`#87`) para la guía QA completa en `docs/qa/` (`QT-6`).
  - Commit sugerido (cierre `004` sin re-cerrar `#132`, ya cerrado en el PR inicial de documentación, `QT-6`): `docs(004): cierre de la spec 004, aplicación de C-12 a C-14 y guía de verificación final (FN)`.
  - **RF**: RF-001 a RF-048 (CE-001 a CE-010)
  - **Dep.**: T040
  - **Hecho cuando**: todos los comandos de la regla 5 (incluidas las pruebas PostgreSQL con `PRUEBAS_DATABASE_URL` y `tests/test_almacen.py`) pasan en verde, Miguel (`#87`) recibe la entrega final para `docs/qa/`, el estado de este archivo marca `FN terminada` y Hugo aprueba el cierre de la Spec 004.

---

## Dependencias y orden de ejecución

```text
Corte 1 (meta dom 29 nov · Puerta S2 · sin migración de BD):
  F1 (#120, Hugo: T001..T006) ───────────────────────────────────────────────────────────────────┐
                                                                                                 ├→ F5 (Puerta S2: T025..T027)
  F2 (#100, Leonel: T007..T011) → F3 (#121, Leonel: T012..T019) → F4 (#121, Leonel: T020..T024) ─┘

Corte 2 (tras #119):
  F5 → F6 (#119 Juan: T028, T030 → #120 C2 Hugo: T029, T031, T032) → F7 (#121 C2 Leonel: T033..T036) → FN (T037..T041)
```

- **Historias independientes y paralelismo entre ramas**:
  - **F1 (`#120` C1)** corre completamente en paralelo con toda la cadena web del Corte 1 (**F2 `#100` → F3 `#121` → F4 `#121`**) porque F1 solo toca `backend/` y la web se valida contra `web/tests/servidor_simulado.py`, convergiendo ambas ramas en **F5 (`T025`)** (`QT-3`).
  - **F3 (`#121` C1)** sale **después de unir F2 (`#100`)** (`Dep.: T011` en `T012`, sin depender de `T006`) para evitar conflictos en `web/js/vistas.js`, `web/js/app.js` y `web/estilos.css`, y continúa con **F4 (`#121` C1)** antes de integrarse con **F1 (`#120` C1)** en **F5**.
  - **F6 (`#119` + `#120` C2)** depende de cerrar **F5** (`Dep.: T027` en `T028` y `T029`) y de la migración `0004` de Juan; desbloquea **F7 (`#121` C2)** y el cierre **FN**.
- **Tareas `[P]` paralelizables dentro de cada fase**:
  - **F1**: `T002` (`test_crear_cobro.py`) y `T003` (`test_modelo.py` / `test_canal.py`).
  - **F2**: `T007` (`test_teclado.py`) y `T008` (`test_seguridad.py`).
  - **F3**: primero `T013` (`test_duracion_y_descarga.py` + 2 asertos) y `T014` (`test_seguridad.py`); después `T015` (`cuenta.js`), `T016` (`servidor.js`) y `T017` (`memoria.js` + `escucha.js`) en paralelo antes de `T018`.
  - **F4**: `T020` (`test_duracion_y_descarga.py`) y `T021` (`test_seguridad.py`).
  - **F6**: `T028` (pruebas SQL puras de migración `0004`) y `T029` (pruebas de almacén, modelo, canal y conciliación).
  - **FN**: `T037` (aplicar `C-12`–`C-14` y actualizar contratos/READMEs) y `T038` (revisión de seguridad); `T039` corre tras `T038` para escribir secuencialmente en `verification-guide.md`.

## Estrategia

1. **MVP primero (Corte 1: `F1` ‖ `(F2 → F3 → F4)` → `F5`)**: entrega valor inmediato en mostrador (duraciones finitas `6 min`–`24 h`, calculadora completa y **Descargar QR**) antes de la Puerta S2 (domingo 29 nov) sin bloquearse en la migración de base de datos (`#119`).
2. **Entrega incremental (Corte 2: `F6` → `F7` → `FN`)**: agrega **Sin vencimiento** (`duracion_segundos: 0`) de punta a punta en cuanto entra `#119`, conservando 100 % compatible lo entregado en el Corte 1.
3. **Verificación continua**: cada fase cierra con todas las pruebas en verde (sin pey real), su sección en `specs/004-cobro-rapido/verification-guide.md` y su mensaje de commit sugerido; los cobros reales de `$0.01` se concentran exclusivamente al validar `F5` y `FN`.

---

## Trazabilidad

| Requisito | Tareas |
|---|---|
| RF-001 | T002, T005, T006, T025, T027, T037, T040, T041 |
| RF-002 | T002, T005, T006, T025, T027, T037, T040, T041 |
| RF-003 | T002, T003, T004, T005, T006, T025, T026, T027, T037, T040, T041 |
| RF-004 | T003, T004, T006, T025, T027, T037, T040, T041 |
| RF-005 | T003, T004, T006, T025, T027, T037, T040, T041 |
| RF-006 | T002, T005, T006, T025, T027, T029, T031, T032, T037, T038, T040, T041 |
| RF-007 | T002, T003, T004, T005, T006, T025, T027, T029, T031, T032, T037, T040, T041 |
| RF-008 | T028, T029, T030, T031, T032, T037, T039, T040, T041 |
| RF-009 | T028, T029, T030, T031, T032, T037, T040, T041 |
| RF-010 | T029, T031, T032, T037, T040, T041 |
| RF-011 | T029, T031, T032, T037, T040, T041 |
| RF-012 | T029, T031, T032, T037, T038, T040, T041 |
| RF-013 | T013, T018, T019, T025, T027, T034, T037, T040, T041 |
| RF-014 | T033, T034, T035, T036, T037, T039, T040, T041 |
| RF-015 | T013, T018, T019, T025, T027, T037, T040, T041 |
| RF-016 | T012, T013, T016, T018, T019, T025, T026, T027, T033, T034, T035, T036, T037, T040, T041 |
| RF-017 | T013, T018, T019, T025, T027, T034, T037, T040, T041 |
| RF-018 | T013, T018, T019, T025, T027, T034, T035, T036, T037, T040, T041 |
| RF-019 | T012, T013, T015, T018, T019, T025, T026, T027, T037, T040, T041 |
| RF-020 | T012, T013, T015, T018, T019, T025, T026, T027, T037, T040, T041 |
| RF-021 | T013, T015, T033, T034, T035, T036, T037, T039, T040, T041 |
| RF-022 | T013, T015, T034, T035, T036, T037, T040, T041 |
| RF-023 | T017, T034, T035, T036, T037, T040, T041 |
| RF-024 | T012, T013, T014, T017, T018, T019, T025, T027, T033, T034, T035, T036, T037, T040, T041 |
| RF-025 | T020, T023, T024, T025, T027, T037, T040, T041 |
| RF-026 | T020, T021, T022, T023, T024, T025, T026, T027, T037, T038, T039, T040, T041 |
| RF-027 | T020, T022, T023, T024, T025, T027, T037, T040, T041 |
| RF-028 | T007, T009, T010, T011, T025, T027, T037, T040, T041 |
| RF-029 | T007, T009, T011, T025, T026, T027, T037, T040, T041 |
| RF-030 | T007, T009, T011, T025, T027, T037, T040, T041 |
| RF-031 | T007, T008, T010, T011, T025, T027, T037, T040, T041 |
| RF-032 | T007, T010, T011, T025, T027, T037, T040, T041 |
| RF-033 | T007, T009, T011, T025, T027, T037, T040, T041 |
| RF-034 | T007, T009, T011, T025, T027, T037, T040, T041 |
| RF-035 | T007, T009, T010, T011, T025, T027, T037, T040, T041 |
| RF-036 | T007, T009, T010, T011, T025, T027, T037, T040, T041 |
| RF-037 | T007, T009, T010, T011, T025, T027, T037, T040, T041 |
| RF-038 | T007, T009, T010, T011, T025, T027, T037, T040, T041 |
| RF-039 | T007, T010, T011, T025, T026, T027, T037, T040, T041 |
| RF-040 | T007, T010, T011, T025, T027, T037, T040, T041 |
| RF-041 | T007, T010, T011, T025, T027, T037, T040, T041 |
| RF-042 | T007, T010, T011, T013, T018, T019, T020, T023, T024, T025, T027, T034, T035, T036, T037, T040, T041 |
| RF-043 | T002, T005, T006, T008, T014, T016, T017, T021, T022, T024, T025, T027, T029, T031, T032, T037, T038, T040, T041 |
| RF-044 | T013, T014, T017, T018, T019, T025, T027, T034, T035, T036, T037, T038, T040, T041 |
| RF-045 | T007, T009, T011, T025, T027, T037, T040, T041 |
| RF-046 | T007, T009, T011, T025, T027, T037, T040, T041 |
| RF-047 | T007, T009, T010, T011, T025, T027, T037, T040, T041 |
| RF-048 | T007, T010, T011, T013, T018, T019, T020, T023, T024, T025, T027, T034, T035, T036, T037, T040, T041 |
| CE-001 | T026, T027, T040, T041 |
| CE-002 | T007, T026, T027, T040, T041 |
| CE-003 | T002, T005, T025, T027, T038, T040, T041 |
| CE-004 | T002, T005, T025, T027, T040, T041 |
| CE-005 | T013, T018, T025, T027, T040, T041 |
| CE-006 | T020, T023, T026, T027, T040, T041 |
| CE-007 | T026, T027, T040, T041 |
| CE-008 | T007, T010, T013, T018, T020, T023, T025, T027, T034, T035, T040, T041 |
| CE-009 | T039, T040, T041 |
| CE-010 | T029, T031, T032, T040, T041 |

## Revisión QA de tasks

*Pasada única ejecutada el 2026-11-27 (`/qa-spec 004 tasks`, 8 de 8 bloques); todos los hallazgos (`QT-1` a `QT-7`) y las 4 erratas fueron aprobados por Hugo y aplicados el 2026-11-27.*

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QT-1 | Contradicción | Asertos cerrados y convivencia C1→C2 omitidos: `CAMPOS_COBRO` duplicado en `backend/tests/test_modelo.py:13-30` (omiso en `T003`), `leer()` de `web/js/memoria.js` frente a `web/tests/test_recuperar.py:109-112` (`T017` solo cubría `guardar()`), `0` seguía como inválido en `T002` sin retirarse en `T029`, y `test_selector_de_duracion_muestra_atajos_c1_con_diez_minutos_por_defecto` (`T013`) exigía `duracion-0` ausente sin actualizarse en `T034`. | RF-007, RF-008, RF-013, RF-014, RF-024, RF-044, C-12, QP-3 | Actualizar `CAMPOS_COBRO` (`:13-30` y docstring `:144`) en `T003`, omitir `"topes_anteriores"` vacío tanto en `guardar()` como en `leer()` en `T017`, retirar `0` de los casos inválidos en `T029` y actualizar en `T034` la prueba del selector de `T013` para esperar las 6 opciones incluida `duracion-0`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QT-2 | Hueco / Contradicción | Faltaban guardas críticas en UI y escucha: (1) `T010` omitía pintar texto crudo `` `$${expresion}` `` sin operadores en `[data-prueba="monto"]` y la guarda en `al_cobrar()` contra `pedir_cobro(null)` (`web/js/app.js:167`); (2) `T018`/`T035` no bifurcaban el 5.º uso de `restante()` en `pintar_qr_actual()` (`app.js:344-349`) ni protegían `:382`/`:388` bajo `!es_sin_vencimiento(actual)` (evitando `null < 1 === true`); (3) `Escuchas` (`web/js/escucha.js`) carecía de método público para cerrar la escucha en pantalla desde `empezar_cuenta` (`T035`). | RF-021, RF-022, RF-023, RF-031, RF-032, RF-037, RF-038, RF-039, RF-047, QP-4 | Explicitar en `T010` el pintado crudo sin operadores y la guarda `if (!cobrar_activo(expresion) || monto_envio === null) return;`; exponer `cerrar_en_pantalla()` en `Escuchas` (`T017`) e invocarlo en `T035`; precisar en `T018` los 4 sitios exactos de `puede_reabrir_qr()` (`:88-89`, `:314-315`, `:398`, `:424-425`) + guarda `!es_sin_vencimiento(actual)` en `:382`/`:388`, y en `T035` citar `app.js:344-349` y la bifurcación previa a `:382`/`:388`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QT-3 | Construibilidad | Acoplamientos indebidos entre ramas y detalles de infraestructura de pruebas: `T001` llevaba `[US1]` y bloqueaba `T007`/`T008` (F2); `T012` (F3 web) dependía de `T006` (F1 backend) y omitía `fijar_sin_vencimiento()`, reset en `reiniciar()` y defecto `600` en `_desde_dict()`; `T028` (`#119`, Juan) mezclaba prueba de `AlmacenPostgres` (implementada en `T031`, `#120` Hugo) sin advertir que `_correr_script` rompe `DO $$ ... $$`; Regla 5 omitía `tests/test_almacen.py` en el comando PostgreSQL. | RF-008, RF-009, RF-016, RF-019, RF-020, RF-024, R-9, QP-7 | Quitar `[US1]` de `T001` y desacoplar `T007`/`T008` (`Dep.: ninguna`) y `T012` (`Dep.: T011` + `fijar_sin_vencimiento()`/`reiniciar()`/`_desde_dict()`; modo C2 en `T033`); dejar en `T028` solo pruebas SQL puras usando `conexion.execute(sql)` entero, mover la prueba de `AlmacenPostgres` a `T029` (`tests/test_almacen.py`), sumar `tests/test_almacen.py` a Regla 5 y actualizar el diagrama de dependencias (`F1` ‖ `F2 → F3 → F4` → `F5`). | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QT-4 | Hueco / Caso límite | Faltaban pruebas previas y casos límite de `spec.md §4`: pruebas unitarias en `T013` para las 4 funciones/ramas nuevas de `web/js/cuenta.js` (`es_sin_vencimiento`, `restante` → `null`, `restante_ventana`, `puede_reabrir_qr`, Principio V); cancelación de un QR Sin vencimiento pendiente en backend (`T029`, + aviso firmado posterior → `pagado`) y en web (`T034`, reinicio a `10 min` + tope de 20 min como anterior); conservación de `duracion-0` ante fallo `502`/`422` en `T034` (`RF-018`). | RF-010, RF-012, RF-017, RF-018, RF-021, RF-022, RF-044, Principio V | Añadir en `T013` unitarias (`only_browser("chromium")`) para las 4 funciones de `cuenta.js` (y sincronizar `RF-021`, `RF-022`), añadir en `T029` y `T034` el caso de cancelación de QR sin vencimiento pendiente, y en `T034` el caso de `RF-018` con `duracion-0`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QT-5 | Hueco / Contradicción | `T037` omitía 4 contratos/modelos de datos de 001–003 (`specs/001-backend-mvp/data-model.md`, `specs/002-web-mvp/contracts/uso-del-servidor.md`, `specs/002-web-mvp/data-model.md`, `specs/003-infraestructura-demo/contracts/comando-migraciones.md`) y 2 guías operativas (`backend/README.md`, `web/README.md`); además `C-13` en `spec.md §8.2` omitía `RF-046`, `RF-049` y `RF-070` de `specs/002-web-mvp/spec.md`. | RF-001 a RF-048, C-12, C-13, C-14 (spec 002 RF-046, RF-049, RF-070) | Ampliar `T037` con los 4 documentos de 001–003 más `backend/README.md` y `web/README.md`, y ampliar `C-13` en `spec.md §8.2` con `RF-046`, `RF-049` y `RF-070` (manteniéndolo `Aprobado · sin aplicar` hasta FN). | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27 *(ampliación de `C-13` en `spec.md §8.2` autorizada y aplicada el 2026-11-27; sigue `Aprobado · sin aplicar` hasta FN)*. |
| QT-6 | Hueco | Faltaba política explícita de etiquetas `Refs #` vs `Closes #` en PRs divididos (`#120`, `#121`) y `#132` aparecía repetido en `FN` (`Reparto`); además faltaba coordinar la guía QA en `docs/qa/` con Miguel (`#87`) en los cierres y documentar su estado en la plantilla de PRs con pantalla (`.github/pull_request_template.md:30`). | Constitución (Principio IV, Equipo/QA, flujo 1), `Reparto`, `T006`, `T011`, `T024`, `T027`, `T030`, `T032`, `T036`, `T041` | Quitar `#132` de `FN`, fijar `Closes #132` solo en el PR de docs, `Refs #120`/`Closes #120`, `Closes #100`, `Refs #121`/`Closes #121` y `Closes #119`; añadir en Regla 5, `T027` y `T041` la entrega de `quickstart.md` y `verification-guide.md` a Miguel (`#87`) y anotar el estado de `docs/qa/` en «Qué quedó pendiente» de cada PR con pantalla. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |
| QT-7 | Seguridad | `ID_VALIDO` en `web/js/memoria.js:2` (`/^[A-Za-z0-9_-]{1,32}$/`) permite claves reservadas (`"__proto__"`, `"constructor"`, `"prototype"`) en `topes_anteriores`, lo que podría contaminar un objeto plano ante un `localStorage` manipulado. | RF-043, RF-044 (spec 002 RF-077) | Endurecer `memoria.js` en `T017` exigiendo `Object.getPrototypeOf(topes) === Object.prototype`, rechazando `"__proto__"`, `"constructor"` y `"prototype"` (o usando `Object.create(null)`) y validando `typeof v === "number" && Number.isSafeInteger(v) && v > 0`, con prueba de seguridad en `T014`. | **Aceptada (recomendada) y aplicada** — Hugo, 2026-11-27. |

**Bloques de la pasada comprobados (8 de 8):**
1. *Coherencia interna*: trazabilidad bidireccional 100 % exacta (48/48 RF y 10/10 CE), glosario limpio, todas las rutas/referencias válidas y siguiente `C-n` libre confirmado (`C-15` tras `C-14`), corregidos formato de `T001`, TDD en `T013`/`T015`, frontera `T028` vs `T030`/`T031` y guardas de `T010` (`QT-2`, `QT-3`, `QT-4` y 4 erratas).
2. *Otras specs, plan del hackathon, reglas e issues*: comprobados los archivos de `T037`, `C-12`–`C-14`, fechas de Puerta S2/cierre, constitución y `.github/pull_request_template.md` (`gh issue view` restringido por sandbox; contrastado con los documentos del repo), resueltos los documentos omitidos en `T037`, la ampliación de `C-13`, la política `Refs #`/`Closes #` y la coordinación de `docs/qa/` (`QT-5`, `QT-6`).
3. *Código (solo lectura)*: verificadas las 46 rutas y líneas citadas en `backend/`, `web/` y `supabase/` y linters `ruff` limpios en backend (39) y web (12) con `pytest` pendiente de `T001` (`psycopg`); resueltos `CAMPOS_COBRO` en `test_modelo.py`, `app.js:344-349` y `:382`/`:388`, `cerrar_en_pantalla()` en `Escuchas`, `leer()` de `memoria.js`, convivencia C1→C2, texto crudo en `monto` y detalles de `servidor_simulado.py`/`_correr_script`/`test_almacen.py` (`QT-1`, `QT-2`, `QT-3`).
4. *API de pey*: contrastado contra `docs.pey.mx`, `backend/app/pey.py`, `backend/app/main.py` y citas de `openapi.json` v`2026-10-20` (`POST /codi/qr`, `GET /transaction/codi/qr/{id}`, webhooks `codi.qr.payment_received` y `429 CALL_LIMIT_REACHED`); sin contradicciones ni promesas fuera de API, con verificación real de `86400` (`T026`) y `0` (`T039`).
5. *Dependencias externas*: dueños y cortes verificados (`#119` solo Corte 2; fallos de pey/webhook/red cubiertos); añadidos dueños explícitos en las 5 filas de `## Dependencias externas` (`uv sync` también para Leonel en F2) y el caso `RF-018` con `duracion-0` en `T034` (`QT-4`, Errata 2).
6. *Ambigüedades y casos límite*: contrastadas todas las filas de `spec.md §4` más 320 px, lector de pantalla y aviso CoDi; cubiertos los casos de cancelación de QR sin vencimiento pendiente (`T029`, `T034`) y las guardas de `al_cobrar()` y `[data-prueba="monto"]` en `T010` (`QT-2`, `QT-4`).
7. *Seguridad y rendimiento*: secretos, Standard Webhooks, deduplicación, validación previa al límite por IP, CSP frente a `Blob`/`a.download`, `textContent`, saneamiento PNG, `revoke all` en `0004` y metas `CE-005`/`CE-007` verificados; aplicado el endurecimiento contra claves reservadas en `topes_anteriores` (`QT-7`).
8. *Construibilidad y reparto*: fechas (27 nov → Puerta S2 dom 29 nov → C2 1 dic, con margen al 10/12 dic) y reparto Hugo/Leonel/Juan viables tras eliminar los acoplamientos de ramas/pruebas entre F1, F2, F3 y F6 (`QT-1`, `QT-3`, Erratas 1, 3 y 4).

**Erratas menores registradas (corregidas el 2026-11-27):**
1. *(Corregida el 2026-11-27)* En **Regla 1**, se aclaró que en fases compartidas por dos personas (`F5`, `F6` con PR `#119` de Juan y PR `#120` Corte 2 de Hugo, y `FN`), cada PR o sub-bloque lo ejecuta una sola persona.
2. *(Corregida el 2026-11-27)* En **`## Dependencias externas`**, se añadió la columna `Dueño` con responsables explícitos en las 5 filas, aclarando que `uv sync --directory backend --locked` también aplica a Leonel en `F2`.
3. *(Corregida el 2026-11-27)* En **`T039`**, se cambió `Dep.: T036` a `Dep.: T038` para asegurar escritura secuencial en `specs/004-cobro-rapido/verification-guide.md` sin concurrencia con `T038 [P]`.
4. *(Corregida el 2026-11-27)* En **`## Dependencias y orden de ejecución`**, se alineó que `F6` depende de cerrar `F5` (`Dep.: T027` en `T028` y `T029`), retirando la nota discordante «o de `main` tras F1».
