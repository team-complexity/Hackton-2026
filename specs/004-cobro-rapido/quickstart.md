# Guía rápida de comprobación: Spec 004 — Cobro rápido

- **Spec**: [spec.md](spec.md)
- **Plan**: [plan.md](plan.md)
- **Contratos**: [crear-cobro-duracion.md](contracts/crear-cobro-duracion.md), [vistas-cobro-rapido.md](contracts/vistas-cobro-rapido.md), [calculadora-y-descarga.md](contracts/calculadora-y-descarga.md)

Esta guía permite comprobar de punta a punta el **Corte 1** y el **Corte 2** de la Spec 004 sin tocar pey real ni la base de datos de producción, salvo en el paso final de cobros reales de `$0.01` (que requiere autorización expresa de Hugo).

---

## 1. Prerrequisitos

Desde la raíz del repositorio (`/Users/hugoportillo/Hackton-2026-ci` o `/Users/hugoportillo/Hackton-2026`):

```bash
uv sync --directory backend --locked
```

Confirmar que el código pasa lint y formato:

```bash
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
```

---

## 2. Pruebas automáticas (sin pey real ni base de datos real)

### 2.1 Backend (duración del QR, validaciones, canal y conciliación)

```bash
uv run --directory backend pytest -q
```

**Qué comprueba:**
- Corte 1: duración por defecto de 10 min al omitir el campo (`CE-004`), rango 360..86 400 s, rechazo 422 para `< 360`, `> 86 400`, negativos, decimales, booleanos y `0` en C1 sin llamar a pey (`CE-003`), vencimiento a la hora elegida y ventana de escucha `expira_en + 10 min`.
- Corte 2: `duracion_segundos: 0` aceptado para monto fijo y monto libre, `expira_en: null`, nunca pasa a *vencido* ni emite evento `vencido`, canal cierra y concilia a las 24 h (`fin_ventana`), y un aviso firmado recibido a las 48 h registra el pago sin duplicar (`CE-010`).

### 2.2 Base de datos desechable (solo Corte 2 — migración `0004`)

Con un PostgreSQL 17 local desechable en `PRUEBAS_DATABASE_URL`:

```bash
PRUEBAS_DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/pago_facil_prueba" \
  uv run --directory backend pytest tests/test_migraciones_postgres.py tests/test_esquema_postgres.py -q
```

**Qué comprueba:**
- `python -m app.migraciones aplicar --entorno local` aplica `0001` a `0004` de forma idempotente (correrlo dos veces no cambia nada ni falla).
- `AlmacenPostgres` guarda y recupera cobros con `expira_en = None` (`duracion_segundos = 0`) y `cobros_con_estado` no marca esos cobros como `vencido`.

### 2.3 Web (calculadora, selector de duración, descarga PNG, tope de 20 min en anteriores largos y 320 px)

```bash
uv run --directory backend pytest ../web -q
```

**Qué comprueba:**
- Calculadora: `15 + 22.50 + 8 = $45.50`, `3 × 25 + 20 = $95.00`, `1.25 × 1.30 = $1.63`, `0 × 25` (Cobrar y Monto libre desactivados), operador final con total parcial, `25.` + `+`, tope de 20 operandos, desbordamiento > `$999,999.99`, borrado `⌫`, limpiar `C` y conservación de expresión ante rechazo del servidor.
- Selector de duración: opciones `6 min`, `10 min` (defecto), `30 min`, `1 h`, `24 h` (y `Sin vencimiento` en C2), cuenta regresiva `H:MM:SS` con reloj desfasado (`CE-005`), reinicio a `10 min` en Nuevo cobro / cancelar / recarga, conservación en error, y tope de 20 min para cobros anteriores > 1 h (`RF-044`).
- Descarga PNG: `Descargar QR` genera archivo `.png` válido con nombre descriptivo sin cerrar la vista QR ni detener la escucha (`CE-006`).
- Corte 2 en pantalla: etiqueta `"Sin vencimiento"`, aviso tras 24 h en vista QR ocultando `Cancelar cobro` y manteniendo `Descargar QR` y `Nuevo cobro`, y ocultado de `Mostrar QR otra vez` tras 24 h.
- Ancho de 320 px sin desplazamiento horizontal (`CE-008`) y nombres accesibles en español (`RF-048`).

---

## 3. Verificación manual en local (servidor + web sin pagos reales)

1. Arrancar el servidor entregando `web/`:
   ```bash
   CARPETA_WEB=../web uv run --directory backend uvicorn app.main:app --port 8000
   ```
2. Abrir `http://127.0.0.1:8000` en el navegador (y en modo responsive a `320 × 640 px`):
   - Verificar que no hay barra de desplazamiento horizontal.
   - Armar `3 × 25 + 20`, comprobar expresión arriba y `$95.00` abajo; probar `C`, `⌫` y operador colgando.
   - Cambiar la duración a `30 min` y comprobar que al pulsar *Nuevo cobro* vuelve a `10 min`.

---

## 4. Verificación con cobros reales de $0.01 MXN (solo con autorización de Hugo)

> **Regla (Principio V y VI):** solo con cuentas propias o CLABEs de prueba de pey, y con autorización explícita de Hugo en ese momento.

1. Encender la demo pública siguiendo `docs/operacion-demo.md` (en Corte 2, respaldar antes y aplicar la migración `0004`).
2. **Corte 1 — Duración personalizada (`CE-001`)**: seleccionar `6 min` (o `30 min`), teclear `$0.01`, generar el QR (verificar cuenta regresiva y tiempo ≤ 5 s, `CE-007`), pagar desde la app del banco en la opción CoDi y confirmar aviso visual y sonoro. Repetir una creación de `$0.01` con `24 h` para validar en vivo el límite superior en pey.
3. **Corte 1 — Calculadora (`CE-002`)**: armar `2 × 0.01 + 0.01 + 0.01` (`$0.04`), pulsar Cobrar, comprobar en la app del banco que el monto es `$0.04` y completar el pago.
4. **Corte 1 — Descarga (`CE-006`)**: pulsar **Descargar QR**, abrir el `.png` descargado y verificar que se escanea correctamente desde la app del banco en CoDi.
5. **Corte 2 — Sin vencimiento (`CE-009`)**: seleccionar `Sin vencimiento`, crear un cobro de `$0.01` (y otro de monto libre), verificar etiqueta `"Sin vencimiento"`, descargar el QR y pagar `$0.01` desde la app del banco confirmando "Pago recibido".
