# Contrato: salud del servidor (amplía el de la spec 001)

## 1. Método, ruta y propósito

`GET /salud`: comprobar en segundos que el servidor responde, que tiene sus credenciales y que la base de datos responde, sin mostrar ningún valor. Lo usan Hugo al encender la demo (RF-058, CE-016), la guía de reactivación de Supabase (RF-050) y las pruebas de Leonel desde fuera de la red (N-17).

Sustituye al [contrato de la 001](../../001-backend-mvp/contracts/salud.md) cuando se aplique el cambio C-6 (c).

## 2. Requisitos

RF-023 (amplía RF-038 de la 001), RF-021, RF-050, CE-010, CE-016.

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

- `base_de_datos` sale de un `select 1` con 2 s de espera. El resultado se guarda 10 s, para que pedir la salud muchas veces no cargue la base de datos (DP-31).
- `base_de_datos` llega con F5 (corte 2); en el corte 1 la salud es la de la 001. La salud no avisa de una estructura pendiente (RF-047 se retiró con D-4); la guía pide aplicar las migraciones antes de arrancar.

## 5. Ejemplos

```json
{ "estado": "ok", "llave_pey": true, "secreto_aviso_pey": true, "base_de_datos": "responde" }
```

```json
{ "estado": "ok", "llave_pey": true, "secreto_aviso_pey": true, "base_de_datos": "no responde" }
```

## 6. Seguridad

- Solo devuelve booleanos y palabras fijas: nunca la dirección, el usuario ni la contraseña de la base de datos, ni el texto de un error de conexión (RF-021, DP-15).
- No llama a pey.
- Es público, como en la 001. Lo que revela (si la base de datos responde) no ayuda a un atacante más que intentar crear un cobro.
