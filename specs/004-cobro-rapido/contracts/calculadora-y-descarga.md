# Contrato: funciones puras de calculadora (`teclado.js`) y descarga PNG (`descarga.js`)

## 1. Propósito

Especifica la interfaz y los casos de frontera de las dos piezas puras de lógica del navegador que se prueban directamente con pruebas unitarias y de integración en `web/tests/`.

## 2. Requisitos

RF-025 a RF-041, RF-045 a RF-047; CE-002, CE-006.

## 3. Interfaz de `web/js/teclado.js`

| Función | Entrada | Salida | Requisitos |
|---|---|---|---|
| `aplicar_tecla(expresion, tecla)` | `expresion: string`, `tecla: "0".."9" \| "punto" \| "borrar" \| "mas" \| "por" \| "limpiar"` | `string` (nueva expresión canónica) | RF-028, RF-030, RF-033 a RF-036, RF-045, RF-046 |
| `evaluar_expresion(expresion)` | `expresion: string` | `{ tiene_operadores: boolean, incompleta: boolean, desbordado: boolean, total_centavos: bigint \| null, texto_total: string, monto_envio: number \| null }` | RF-029, RF-031, RF-032, RF-047 |
| `cobrar_activo(expresion)` | `expresion: string` | `boolean` | RF-037 |
| `monto_libre_activo(expresion)` | `expresion: string` | `boolean` | RF-038 |

### Tabla de casos exactos de `teclado.js`

| Secuencia / expresión | `evaluar_expresion` (`texto_total`, `monto_envio`, `incompleta`, `desbordado`) | `cobrar_activo` | `monto_libre_activo` |
|---|---|---|---|
| `""` | `""`, `null`, `false`, `false` | `false` | `true` |
| `"0"` | `"$0.00"`, `0`, `false`, `false` | `false` | `true` |
| `"0."` (sin operadores, `QP-1`) | `"$0.00"`, `0`, `false`, `false` | `false` | `true` |
| `"0.00"` (sin operadores, `QP-1`) | `"$0.00"`, `0`, `false`, `false` | `false` | `true` |
| `"25.50"` | `"$25.50"`, `25.5`, `false`, `false` | `true` | `false` |
| `"15 + 22.50 + 8"` | `"$45.50"`, `45.5`, `false`, `false` | `true` | `false` |
| `"3 × 25 + 20"` | `"$95.00"`, `95`, `false`, `false` | `true` | `false` |
| `"20 + 3 × 25"` | `"$95.00"`, `95`, `false`, `false` | `true` | `false` |
| `"1.25 × 1.25"` (`1.5625`) | `"$1.56"`, `1.56`, `false`, `false` | `true` | `false` |
| `"1.25 × 1.30"` (`1.625`) | `"$1.63"`, `1.63`, `false`, `false` | `true` | `false` |
| `"0.1 + 0.2"` | `"$0.30"`, `0.3`, `false`, `false` | `true` | `false` |
| `"25 + "` (operador final) | `"$25.00"`, `null`, `true`, `false` | `false` | `false` |
| `"3 × 25 + "` (operador final) | `"$75.00"`, `null`, `true`, `false` | `false` | `false` |
| `"25 + 0."` (punto colgante, `QP-5`) | `"$25.00"`, `25`, `false`, `false` | `true` | `false` |
| `"25 + 10."` (punto colgante, `QP-5`) | `"$35.00"`, `35`, `false`, `false` | `true` | `false` |
| `"0 × 25"` | `"$0.00"`, `0`, `false`, `false` | `false` | `false` |
| `"0 × 25 + 10"` | `"$10.00"`, `10`, `false`, `false` | `true` | `false` |
| `"99999 × 99"` (`9 899 901`) | `"El total es demasiado grande"`, `null`, `false`, `true` | `false` | `false` |

> **Nota (`QP-1`):** `monto_libre_activo` devuelve `true` solo cuando la entrada **no tiene operadores** y su valor numérico es `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`), manteniendo compatibilidad con `web/tests/test_teclado.py:97-116`, y `false` ante cualquier operador (`"0 × 25"`, `"0 + "`) o valor `> 0` (`RF-038`).

### Reglas de edición de `aplicar_tecla`

- `aplicar_tecla("", "mas")` → `""` y `aplicar_tecla("", "por")` → `""` (RF-033).
- `aplicar_tecla("25.", "mas")` → `"25 + "` (RF-045).
- `aplicar_tecla("25 + ", "punto")` → `"25 + 0."` (RF-030).
- `aplicar_tecla("25 + 0", "7")` → `"25 + 7"` (sustitución de `"0"` inicial por operando, RF-030, `QP-5`).
- `aplicar_tecla("25 + ", "por")` → `"25 × "` (RF-034).
- `aplicar_tecla("25 + ", "borrar")` → `"25"` (RF-035).
- `aplicar_tecla("3 × 25 + 20", "limpiar")` → `""` (RF-036).
- Con 20 operandos (`"1 + 1 + ... + 1"`), `aplicar_tecla(expr, "mas")` y `aplicar_tecla(expr, "por")` devuelven `expr` sin cambios (RF-046).
- **Punto colgante (`QP-5`):** un operando terminado en punto colgante (`"25."`, `"25 + 0."`, `"25 + 10."`) se evalúa con su valor numérico (`incompleta = false`) y mantiene `Cobrar` activo si el total es `> 0`, igual que `"25."` en `web/tests/test_teclado.py:111` (RF-037).

## 4. Interfaz de `web/js/descarga.js`

| Función | Entrada | Salida | Requisitos |
|---|---|---|---|
| `nombre_archivo_qr(cobro)` | `{ monto?: number \| null, concepto?: string }` | `string` terminado en `.png` | RF-026 |
| `descargar_qr(qr_imagen, cobro)` | `qr_imagen: string`, `cobro: object` | `{ ok: true, nombre: string } \| { ok: false, mensaje: string }` | RF-026, RF-027 |

### Ejemplos de `nombre_archivo_qr`

| `monto` | `concepto` | Resultado |
|---|---|---|
| `25.5` | `"Tacos al pastor"` | `"pago-facil-25-50-tacos-al-pastor.png"` |
| `null` | `"Propina / Café"` | `"pago-facil-monto-libre-propina-cafe.png"` |
| `0.01` | `""` | `"pago-facil-0-01.png"` |
| `null` | `"!!!"` | `"pago-facil-monto-libre.png"` |

> **Nota:** En pantalla el servidor rellena `"concepto": "Cobro"` cuando el concepto viene vacío (`backend/app/main.py:89`, por eso el ejemplo de `vistas-cobro-rapido.md` produce `"pago-facil-95-00-cobro.png"`), mientras que `nombre_archivo_qr` solo omite el sufijo cuando recibe `""` o un texto sin caracteres alfanuméricos.

## 5. Ejemplo de fallo en descarga

Si `qr_imagen` está vacío, no es base64 válido o `URL.createObjectURL` lanza una excepción:

```json
{ "ok": false, "mensaje": "No se pudo descargar el QR. Intenta de nuevo." }
```

## 6. Notas de seguridad

- `teclado.js` nunca usa `eval` ni `Function`: parsea solo dígitos, `.`, `+` y `×` sobre `BigInt`.
- `nombre_archivo_qr` elimina barras (`/` y `\`), puntos suspensivos (`..`), acentos y caracteres no ASCII para impedir nombres de archivo malformados.
