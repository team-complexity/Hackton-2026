# Contrato: publicar una versión en la demo

## 1. Propósito

Subir una versión de `main` (servidor y web) a la instancia de la demo, a mano (corte 1) o sola al unir un pull request (corte 2), con un solo script y con vuelta atrás si algo falla. Supone DP-1 (EC2 + CloudFront).

## 2. Requisitos

RF-024, RF-030, RF-042, RF-043, RF-044, RF-045, RF-046, RF-055, CE-013, CE-014.

## 3. Script en la instancia: `infra/servidor/publicar.sh <commit>`

| Entrada | Validación |
|---|---|
| `<commit>` | 40 caracteres hexadecimales; debe existir en `main` del repositorio público |

Pasos (research R-15):

1. Descarga el commit en `/opt/pago-facil/releases/<commit>`.
2. `uv sync --locked --no-dev` en esa carpeta. Si falla → sale con código 1 y la versión anterior sigue atendiendo (RF-044).
3. Cambia el enlace `/opt/pago-facil/actual` y reinicia `pago-facil.service` (corte de RF-055).
4. Espera hasta 45 s a que `http://127.0.0.1:8000/salud` responda con `base_de_datos: "responde"`. Si no → devuelve el enlace a la versión anterior, reinicia y sale con código 2 (RF-044).
5. Borra las versiones más viejas y deja las 3 más recientes.

**No** aplica migraciones (RF-046) y **no** toca `/etc/pago-facil/entorno`.

| Código de salida | Significado |
|---|---|
| 0 | Publicada; la salud responde |
| 1 | No se pudo preparar; sigue la versión anterior, sin corte |
| 2 | La versión nueva no respondió; se volvió a la anterior |

## 4. Publicación a mano (corte 1)

Hugo, desde su computadora, con su perfil de AWS:

```text
aws ssm send-command --instance-ids <id> --document-name AWS-RunShellScript \
  --parameters 'commands=["/opt/pago-facil/actual/infra/servidor/publicar.sh <commit>"]'
```

o en una sesión de Session Manager. Los pasos completos están en `docs/operacion-demo.md`.

## 5. Publicación automática (corte 2): `.github/workflows/publicar.yml`

| Disparador | `push` a `main` (es decir, al unir un pull request) |
|---|---|
| Trabajo 1 | Las mismas pruebas del CI (RF-042: solo publica si pasan) |
| Trabajo 2 | Credenciales temporales por OIDC con el rol de la variable `AWS_ROL_PUBLICACION` (RF-043) |
| | Si la instancia no está `running` → falla con "La demo está apagada; solo Hugo la enciende" y no la enciende (RF-045) |
| | `ssm send-command` con `publicar.sh ${{ github.sha }}` y espera el resultado |
| | Después, `GET https://<demo>/salud` debe responder 200 (RF-030, RF-055) |
| Resultado | Verde si todo salió bien; rojo con el mensaje del script si no (RF-044) |
| `permissions` | `id-token: write`, `contents: read` |
| `concurrency` | Un solo `publicar` a la vez; uno nuevo espera al anterior |

## 6. Seguridad

- Ninguna llave de AWS en el repositorio ni en los secretos de GitHub: solo el ARN del rol, como variable (RF-043, CE-013).
- El rol solo confía en `main` de `Altairtm/Hackton-2026` y no puede encender instancias (R-16).
- El script corre como el usuario del servicio, no lee el archivo de secretos y no imprime variables de entorno.
