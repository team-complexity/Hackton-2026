# Contrato: vistas ampliadas de la pantalla (Cobro rápido)

> Amplía [specs/002-web-mvp/contracts/vistas.md](../../002-web-mvp/contracts/vistas.md) (cambio aprobado `C-13`, sin aplicar todavía en la spec 002). Conserva todos los `data-prueba` existentes para compatibilidad con las pruebas de la spec 002 y con el rediseño `#118`.

## 1. Propósito

Fija los elementos, atributos `data-prueba`, nombres accesibles (`aria-label` / `role`) y textos observables de las vistas afectadas por la Spec 004: **Teclado**, **QR** y **Pago recibido**.

## 2. Requisitos

RF-013 a RF-042, RF-044 a RF-048; CE-001, CE-002, CE-005, CE-006, CE-008, CE-009.

## 3. Vista Teclado (`data-prueba="vista-teclado"`)

| Elemento | `data-prueba` | Accesibilidad (`aria` / `role`) | Comportamiento | Requisitos |
|---|---|---|---|---|
| Expresión en curso (secundaria, encima del total) | `expresion` | — | Oculta (`hidden`) cuando no hay operadores (`+` o `×`). Visible con texto canónico (ej. `"3 × 25 + 20"` o `"25 +"`) en cuanto existe un operador. Se renderiza solo con `textContent` | RF-031, RF-032 |
| Monto / total en grande | `monto` | — | Sin operadores: muestra el texto escrito (`"$25."`, `"$0."`, `"$"`). Con operadores: muestra el total calculado o parcial (`"$95.00"`, `"$25.00"`). Si hay desbordamiento (`> $999,999.99`): muestra `"El total es demasiado grande"` (nunca notación científica) | RF-029, RF-031, RF-032, RF-047 |
| Teclas numéricas y punto | `tecla-0`…`tecla-9`, `tecla-punto` | Botones nativos | Reglas por operando (máx. 5 enteros, 2 decimales, un `.`, `.` inicial → `0.`) | RF-028, RF-030 |
| Tecla suma (`+`) | `tecla-mas` | `aria-label="Sumar"` | Agrega `+`, normaliza punto sobrante, reemplaza operador final, ignora si vacío o si ya hay 20 operandos | RF-028, RF-033, RF-034, RF-045, RF-046, RF-048 |
| Tecla multiplicación (`×`) | `tecla-por` | `aria-label="Multiplicar"` | Igual que `+` con operador `×` | RF-028, RF-033, RF-034, RF-045, RF-046, RF-048 |
| Tecla borrar un carácter (`⌫`) | `tecla-borrar` | `aria-label="Borrar último carácter"` | Su texto visible cambia de `"Borrar"` (`web/js/vistas.js`, spec 002) a `"⌫"` con `aria-label="Borrar último carácter"`, conservando `data-prueba="tecla-borrar"` para compatibilidad con las pruebas existentes de la spec 002 (`QP-5`). Quita el último carácter del operando o el operador final | RF-028, RF-035, RF-048 |
| Tecla limpiar todo (`C`) | `tecla-limpiar` | `aria-label="Limpiar todo"` | Vacía toda la expresión y el total | RF-028, RF-036, RF-048 |
| Selector de duración | `selector-duracion` | `role="radiogroup"`, `aria-label="Duración del QR"` | Contenedor flexible que no desborda en 320 px | RF-013, RF-042, RF-048 |
| Opciones de duración `[C1]` | `duracion-360`, `duracion-600`, `duracion-1800`, `duracion-3600`, `duracion-86400` | `role="radio"`, `aria-checked="true\|false"` | Etiquetas: `"6 min"`, `"10 min"`, `"30 min"`, `"1 h"`, `"24 h"`. `"10 min"` activa al iniciar, al pulsar Nuevo cobro, al cancelar y al recargar en Teclado; conservada ante error al crear | RF-013, RF-015, RF-016, RF-017, RF-018, RF-048 |
| Opción sin vencimiento `[C2]` | `duracion-0` | `role="radio"`, `aria-checked="true\|false"` | Etiqueta: `"Sin vencimiento"`. Visible solo desde Corte 2 | RF-014, RF-016, RF-048 |
| Botón "Cobrar" | `cobrar` | — | Desactivado si vacío, termina en operador final, total = `$0.00` o total desbordado (`> $999,999.99`). Envía `{ monto: total_calculado, concepto, duracion_segundos }` | RF-016, RF-037, RF-039, RF-047 |
| Botón "Monto libre" | `monto-libre` | — | Activo **solo** cuando la entrada **no tiene operadores** y su valor numérico es `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`); desactivado ante cualquier operador (`"0 × 25"`, `"0 + "`) o valor `> 0` (`RF-038`, `QP-1`). Envía `{ monto: null, concepto, duracion_segundos }` | RF-016, RF-038 |
| Mensaje de error | `mensaje` | — | Igual que spec 002; al volver por error conserva la expresión completa, el concepto y la duración elegida | RF-018, RF-040 |

> **Nota (`QP-2`, envío de `duracion_segundos`):** `web/js/app.js` siempre envía `duracion_segundos` en `POST /api/cobros` (`RF-016`), mientras que en `web/js/servidor.js` el 3.er parámetro `duracion_segundos` es opcional y omite la clave del JSON cuando es `undefined` (manteniendo intacta `web/tests/test_crear_y_mostrar_qr.py:128`); los 2 asertos de pantalla (`web/tests/test_crear_y_mostrar_qr.py:313` y `web/tests/test_monto_libre_y_reuso.py:54`) se actualizan en F3 bajo `C-13`.

## 4. Vista QR (`data-prueba="vista-qr"`) y Pago recibido (`data-prueba="vista-pagado"`)

| Vista / Elemento | `data-prueba` | Accesibilidad | Comportamiento | Requisitos |
|---|---|---|---|---|
| Vista QR — Cuenta / vigencia | `cuenta` | — | Cobro finito `>= 3600 s`: `H:MM:SS` (ej. `24:00:00`). Cobro finito `< 3600 s`: `M:SS` (ej. `30:00`, `6:00`, `0:05`). Cobro sin vencimiento `[C2]`: `"Sin vencimiento"` | RF-019, RF-020, RF-021 |
| Vista QR — Botón "Descargar QR" | `descargar-qr` | `aria-label="Descargar imagen del QR"` | Visible siempre que la vista QR tenga `qr_imagen` (recién creado, recuperado o reabierto con *Mostrar QR otra vez*). Descarga PNG sin cambiar vista ni detener escucha | RF-025, RF-026, RF-048 |
| Vista QR — Mensaje de descarga | `mensaje-descarga` | — | Oculto salvo error de descarga (`"No se pudo descargar el QR. Intenta de nuevo."`). Se limpia al cambiar de cobro | RF-027 |
| Vista QR — Aviso fin de escucha 24 h `[C2]` | `aviso-fin-escucha` | — | Oculto por defecto. Al cumplirse las 24 h en pantalla de un cobro sin vencimiento (con o sin pagos): visible con `"Este QR sigue vigente, pero ya terminaron las 24 horas de avisos en vivo en esta pantalla."`; se oculta `cancelar`; permanecen visibles el QR, `descargar-qr` y `nuevo-cobro` | RF-023 |
| Vista Pago recibido — "Mostrar QR otra vez" | `mostrar-qr` | — | En cobros finitos: visible mientras `restante >= 1`. En cobros sin vencimiento `[C2]`: visible mientras `ahora < fin_ventana` (24 h); oculto al terminar las 24 h | RF-022 |

## 5. Ejemplo de interacción

```text
1. Vista Teclado inicial → duracion-600 tiene aria-checked="true", expresion oculta, monto = "$"
2. Tocar duracion-1800 → duracion-1800 tiene aria-checked="true" ("30 min")
3. Tocar tecla-3, tecla-por, tecla-2, tecla-5, tecla-mas, tecla-2, tecla-0
   → expresion = "3 × 25 + 20", monto = "$95.00", cobrar activo, monto-libre desactivado
4. Tocar cobrar → POST /api/cobros { monto: 95, concepto: "", duracion_segundos: 1800 }
5. Respuesta 201 → vista-qr visible, qr-monto = "$95.00", cuenta = "30:00", descargar-qr visible
6. Tocar descargar-qr → descarga "pago-facil-95-00-cobro.png"; vista-qr sigue abierta y escuchando
7. Tocar nuevo-cobro → vista-teclado vacía, duracion-600 vuelve a aria-checked="true"
```

## 6. Notas de seguridad

- Toda cadena dinámica (`expresion`, `monto`, `mensaje`, `mensaje-descarga`, `aviso-fin-escucha`) se asigna exclusivamente con `textContent`, nunca `innerHTML` (spec 002 RF-077).
- El nombre del archivo descargado se sanea quitando cualquier carácter fuera de `[a-z0-9-]` antes de asignarlo al atributo `download`.
- La política de seguridad de contenido de `web/index.html` permanece cerrada (`default-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'`).
