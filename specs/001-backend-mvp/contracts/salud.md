# Contrato: salud del servidor

## 1. Método, ruta y propósito

`GET /salud`: comprobar en segundos que el servidor responde, que tiene sus credenciales y que la base de datos está configurada y responde, sin mostrar ningún valor (spec 003, RF-023).

## 2. Requisitos

RF-036, RF-038, y RF-023 de la spec 003.

## 3. Petición

Sin parámetros.

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Siempre que el servidor responde | Tabla de abajo |

| Campo | Tipo | Requisitos |
|---|---|---|
| `estado` | `"ok"` | RF-038 |
| `llave_pey` | booleano: `true` si la llave de pey no está vacía | RF-038 |
| `secreto_aviso_pey` | booleano: `true` si el secreto del aviso no está vacío | RF-038 |
| `base_de_datos` | `"responde"`, `"no responde"` o `"sin configurar"` (sin `DATABASE_URL`: el servidor guarda en memoria) | RF-023 de la spec 003 |

## 5. Ejemplo

```json
{ "estado": "ok", "llave_pey": true, "secreto_aviso_pey": false, "base_de_datos": "responde" }
```

## 6. Seguridad

- Solo devuelve booleanos y palabras fijas; nunca los valores, ni la dirección, el usuario ni la contraseña de la base de datos (RF-036, spec 003 RF-021).
- No llama a pey: que la llave exista no prueba que pey la acepte. Eso se comprueba con `scripts/probar_pey.py` (quickstart).
- El prototipo devuelve `pey_api_key` y `pey_webhook_secret`; se renombran a español (research R-10).
