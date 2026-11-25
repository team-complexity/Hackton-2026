# Operación de la demo

Guía para encender y apagar la demo de PAGO FÁCIL en la Mac de Hugo (spec 003, RF-058). La dirección pública, fija desde F0 (TK-1), es:

`https://pago-facil.tail8d44cb.ts.net`

Esta parte cubre el corte 1: el servidor y el túnel. La base de datos se agrega en F6.

## 1. Cuándo está encendida

La demo solo está encendida en los momentos que el equipo acordó (RF-060): pruebas, grabación del video, demos con negocios piloto y las pruebas de Leonel antes de cada puerta. Desde la entrega del 12 de diciembre hasta el anuncio del 14 de diciembre no se apaga.

Fuera de esos momentos se apaga. En cuanto la dirección tuvo HTTPS, llegaron escáneres automáticos (F0).

Además, se enciende y se comprueba la salud al menos una vez cada 5 días, y el día antes de cada momento acordado (RF-050). La parte de reactivar Supabase llega en F6. Esos días la Mac va con la corriente conectada y con las actualizaciones automáticas de macOS en pausa.

## 2. Antes de encender

En la raíz del repositorio, con `main` al día:

```bash
git switch main
git pull
cd backend && uv sync --locked
```

## 3. Encender

Si la Mac se acaba de prender, primero abre la app de Tailscale. Funnel no vuelve hasta que la app está abierta; la configuración guardada con `--bg` sí vuelve sola (TK-5).

```bash
open -a Tailscale
```

Después el servidor, en `backend/`, con un solo proceso y **sin `--host`**. uvicorn se queda en `127.0.0.1` (RF-056):

```bash
cd backend && uv run uvicorn app.main:app --env-file .env.demo --workers 1 --port 8000
```

Anota el PID de ese proceso. En otra terminal:

```bash
tailscale funnel --bg 8000
caffeinate -is -w <PID del servidor>
```

`caffeinate` mantiene la Mac despierta mientras ese PID siga vivo. Se queda en primer plano y ocupa esa terminal; para dejarla libre, ábrelo en su propia terminal o agrégale `&` al final.

El PID del servidor lo da `lsof -nP -iTCP:8000 -sTCP:LISTEN -t`.

## 4. Comprobar desde fuera

Desde un celular con datos móviles (no desde la wifi de la Mac), abre:

`https://pago-facil.tail8d44cb.ts.net/salud`

Se espera HTTPS sin advertencias y sin páginas intermedias, y un JSON con `"estado": "ok"`. `llave_pey` y `secreto_aviso_pey` son booleanos: dicen si el valor está puesto, no cuál es. Con la demo lista, los dos valen `true`.

La pantalla de cobro es la misma dirección, en `/`: se lee «PAGO FÁCIL» y se ve el teclado.

Desde la propia Mac el nombre se resuelve por dentro del tailnet y no pasa por Funnel. Para salir a internet y entrar como un celular, usa la IP pública del relay que da `dig +short @1.1.1.1 pago-facil.tail8d44cb.ts.net`:

```bash
curl --resolve pago-facil.tail8d44cb.ts.net:443:<IP pública del relay> https://pago-facil.tail8d44cb.ts.net/salud
```

## 5. Aviso de pey

El aviso de la llave de la demo se da de alta **una sola vez** en el portal de pey, en:

`https://pago-facil.tail8d44cb.ts.net/webhooks/pey`

El secreto que entrega el portal va solo a `backend/.env.demo`. La dirección no cambia al reiniciar el servidor, el túnel o la Mac (RF-030). Si cambiara el nombre de la máquina o el del tailnet, cambiaría la dirección: habría que actualizar `WEB_ORIGIN`, este aviso y esta guía (TK-1).

## 6. Desarrollo a la vez

El servidor de desarrollo usa `backend/.env` (la segunda llave y, desde F5, la base de desarrollo) y el puerto **8001**, para no chocar con la demo en el 8000 (QP-14).

## 7. Apagar

```bash
tailscale funnel reset
```

Para el servidor con su PID exacto (`kill <PID>`). No uses `pkill` ni `killall`. `caffeinate` termina solo porque se arrancó con `-w`.

Comprueba que no quedó túnel: `tailscale funnel status` dice `No serve config`.

## 8. Si algo falla

- **Sin internet, o la Mac se suspendió.** Vuelve a encender con la sección 3. La dirección no cambia.
- **El túnel no responde.** `tailscale funnel status`. Si la Mac se reinició, abre antes la app de Tailscale (sección 3).
- **Límites por IP.** F0 mostró la IP real del celular, así que se quedan en 30 cobros por minuto y 30 canales por IP (DP-36, TK-5). Si una comprobación viera `127.0.0.1` en el registro, pasarían a 60 (DP-40).
- **El canal de un cobro se corta antes de tiempo, o los eventos llegan todos juntos al final.** Se para y Hugo decide el plan B (research R-1). En F0 no pasó.

## 9. Secretos

`backend/.env.demo` no se comparte ni se sube. La sesión de Tailscale vive en su app, fuera del repositorio (RF-059).

Cada variable que la demo necesita va en `backend/.env.demo`, aunque el valor esté vacío: lo que falta se toma de `backend/.env`, que es el de desarrollo (DP-44). La plantilla, sin secretos, es [`backend/.env.demo.example`](../backend/.env.demo.example) (TK-4). Se actualiza cuando se agrega una variable. Con la demo encendida, `GET /salud` dice si cada credencial está puesta.

## 10. Pruebas de Leonel

Leonel abre `https://pago-facil.tail8d44cb.ts.net` desde su red y sus celulares (N-17). Si algo falla, se lo dice a Hugo.

Leonel **no necesita** `backend/.env` ni `backend/.env.demo` para esto: solo el enlace. Esos archivos, y las llaves de pey que guardan, solo viven en la Mac de Hugo (sección 9). Quien quiera correr el proyecto en local usa `backend/.env.example` y `docs/` según [backend/README.md](../backend/README.md).

La demo solo está encendida cuando Hugo la enciende (sección 1), así que Leonel le avisa cuándo quiere probar, y Hugo la enciende y se la deja lista. La prueba, sin pagar nada:

1. **Abre el enlace con HTTPS.** Desde su red (wifi) y desde datos móviles. Debe cargar la pantalla de cobro, con «PAGO FÁCIL» y el teclado, sin advertencias del navegador ni páginas intermedias.
2. **Crea un cobro de `0.01`** y mide de «Cobrar» a que se ve el QR. La meta es 5 segundos o menos (C-10). Hazlo 10 veces, anota los tiempos y no pagues ninguno.
3. **Reporta** en el [issue #105](https://github.com/team-complexity/Hackton-2026/issues/105): sistema y navegador de cada celular, los tiempos y lo que falle.

La medición de Hugo del 22 de nov dio entre 3 y 5 segundos (spec 003, guía de verificación, T029), y es lo que llevó a poner la meta en 5 segundos. Esta prueba da un dato de otra red y de otros celulares.
