# Contrato: salud del servidor (amplía el de la spec 001)

## 1. Método, ruta y propósito

`GET /salud`: comprobar en segundos que el servidor responde, que tiene sus credenciales y que la base de datos responde, sin mostrar ningún valor. Lo usan Hugo, el script de publicación (`publicar.sh`, DP-25) y la guía de reactivación de Supabase (RF-050).

Sustituye al [contrato de la 001](../../001-backend-mvp/contracts/salud.md) cuando se aplique el cambio C-6 (c).

## 2. Requisitos

RF-023 (amplía RF-038 de la 001), RF-021, RF-047 (corte 2), RF-050, CE-010.

## 3. Petición

Sin parámetros.

## 4. Respuestas

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Siempre que el servidor responde, aunque la base de datos no responda | Tabla de abajo |

| Campo | Tipo | Requisitos |
|---|---|---|
| `estado` | `"ok"` | RF-038 de la 001 |
| `llave_pey` | booleano | RF-038 de la 001 |
| `secreto_aviso_pey` | booleano | RF-038 de la 001 |
| `base_de_datos` | `"responde"`, `"no responde"` o `"sin configurar"` (sin `DATABASE_URL`: el servidor guarda en memoria, DP-16) | RF-023 |
| `estructura` | `"al dia"`, `"pendiente"` o `"desconocida"` (la base de datos no responde o no está configurada). **Corte 2** | RF-047 |

- `base_de_datos` sale de un `select 1` con 2 s de espera. El resultado se guarda 10 s, para que pedir la salud muchas veces no cargue la base de datos (DP-31).
- `estructura` compara la versión esperada con la registrada (data-model §5.2, regla 5). Se recalcula cada 60 s (DP-30).

## 5. Ejemplos

```json
{ "estado": "ok", "llave_pey": true, "secreto_aviso_pey": true, "base_de_datos": "responde", "estructura": "al dia" }
```

```json
{ "estado": "ok", "llave_pey": true, "secreto_aviso_pey": true, "base_de_datos": "no responde", "estructura": "desconocida" }
```

## 6. Seguridad

- Solo devuelve booleanos y palabras fijas: nunca la dirección, el usuario ni la contraseña de la base de datos, ni el texto de un error de conexión (RF-021, DP-15).
- No llama a pey.
- Es público, como en la 001. Lo que revela (si la base de datos responde) no ayuda a un atacante más que intentar crear un cobro.
