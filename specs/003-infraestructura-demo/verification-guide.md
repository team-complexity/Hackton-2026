# Guía de verificación: 003 Infraestructura de la demo

## F0 Prueba del túnel, sin la web

Fecha: 2026-11-21. Hecha por Hugo con Claude, sin código de producto ni la web (QP-12). La dirección de la demo es **`https://pago-facil.tail8d44cb.ts.net`**: Tailscale Funnel (DP-38) hacia el servidor actual en `127.0.0.1:8000`. En esta guía no se anotan IP, llaves ni datos de la cuenta de Tailscale.

### T001 · Tailscale

- La app **Standalone** de Tailscale para macOS: la de la App Store no admite Funnel. Hugo inició sesión y se instaló el CLI (*Settings → CLI integration*).
- En la consola, la máquina se renombró de `macbook-air-de-hugo` a `pago-facil`, para no publicar el nombre del dueño. El nombre DNS del tailnet (`tail8d44cb`) lo asigna Tailscale y no se puede cambiar por uno libre (TK-1).
- Quedaron activos MagicDNS, los certificados HTTPS (para `pago-facil.tail8d44cb.ts.net`) y el permiso `funnel`: la primera vez, `tailscale funnel --bg 8000` pidió aprobarlo en el navegador.

```bash
tailscale status
```

```bash
tailscale funnel status
```

### T002 · `backend/.env.demo`

Creado por Hugo con la llave de pey que ya estaba en `backend/.env` (la segunda llave, para desarrollo, llega en T048). Comprobado sin ver valores:

- `git check-ignore -v backend/.env.demo` → lo ignora `.gitignore:3:.env.*`; permisos `-rw-------`.
- Tienen valor `WEB_ORIGIN`, `LIMITE_COBROS_POR_MINUTO`, `CANALES_POR_IP` y `PEY_API_KEY`. `DATABASE_URL` está vacía a propósito (DP-44).
- `PEY_WEBHOOK_SECRET` está vacía: esa llave todavía no tiene aviso dado de alta. Se pone en T025 (TK-2).
- Para el equipo se subió la plantilla `backend/.env.demo.example`, sin valores secretos (TK-4).

### T003 · Servidor y Funnel

```bash
cd ~/Hackton-2026/backend && uv run uvicorn app.main:app --env-file .env.demo --workers 1 --port 8000
```

```bash
tailscale funnel --bg 8000
```

- `lsof` muestra el servidor solo en `127.0.0.1:8000` (RF-056). `tailscale funnel status`: `https://pago-facil.tail8d44cb.ts.net (Funnel on)` → `http://127.0.0.1:8000`.
- Desde el celular de Hugo con datos móviles: `/salud` respondió `200` con HTTPS válido, sin advertencias.
- Respuesta: `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}` (`false` por TK-2).
- **Probar desde la Mac de la demo por el relay público.** Desde la propia Mac, el nombre se resuelve a su IP del tailnet y la petición no pasa por Funnel. Para que salga a internet y entre por Funnel, como la de un celular, se fuerza una IP pública del relay (las da `dig +short @1.1.1.1 pago-facil.tail8d44cb.ts.net`):

```bash
curl --resolve pago-facil.tail8d44cb.ts.net:443:<IP pública del relay> https://pago-facil.tail8d44cb.ts.net/salud
```

- **Escáneres.** En cuanto se activó HTTPS, el nombre quedó en el registro público de certificados y llegaron bots pidiendo `/.env`, `/.git/config`, `/.ssh/id_rsa`, `/backup.sql`, WordPress, etc. Todo respondió 404. Por eso la demo se apaga fuera de los momentos acordados (RF-060).

### T004 · Canal de 25 minutos

Con la autorización de Hugo, un QR real de $0.01 **sin pagar**, creado y escuchado desde la Mac por el relay público:

- Cobro `_XAvDuVhbubs` (`codi_qr_id` `354a2b81da`), creado a las 17:27:56. `POST /api/cobros` tardó **9.8 s**, casi todo esperando a pey: es el riesgo de CE-003 del plan §11, que se mide en T029.
- `curl -N` al canal desde las 17:28:12, anotando la hora de cada línea:

| Hora | Evento |
|---|---|
| 17:28:13 | `estado` (*pendiente*), un segundo después de abrir |
| 17:28:29 → 17:47:51 | 73 señales de vida (`: sigo conectado`): 66 a 16 s, 5 a 17 s y una a 21 s |
| 17:37:56 | `vencido`, a los 10 min exactos de crear el QR |
| 17:47:56 | `fin`: el servidor cerró el canal a los 20 min y `curl` terminó con código 0 |

- **Resultado**: cada evento llegó en el momento en que salió, sin retención (RF-057), y el canal duró toda la ventana sin cortes hasta que lo cerró el servidor (RF-026).

### T005 · IP real

En el registro del servidor, las peticiones llegan con la IP pública de quien las hace, nunca `127.0.0.1`: Funnel manda `X-Forwarded-For` y el servidor confía en `127.0.0.1` (`PROXIES_CONFIABLES`, H-8). Hubo dos redes de Hugo con IP distintas: su casa (cobro y canal) y su celular con datos (`/salud`).

- El iPhone salió con una IP de **iCloud Private Relay**, no la de su compañía. Para el servidor es la IP del cliente, y los límites por IP se aplican a ella.
- **Resultado**: no hace falta DP-40; los límites de la demo se quedan en 30 (DP-36).

### T006 · Misma dirección después de reiniciar

Hugo paró el servidor con `Ctrl+C` y reinició la Mac (arrancó a las 17:52).

- Al volver, Tailscale estaba detenido hasta abrir la app (`open -a Tailscale`). La configuración de Funnel se había guardado (`--bg`) y volvió sola: `https://pago-facil.tail8d44cb.ts.net (Funnel on)` → `http://127.0.0.1:8000`. **Al encender la demo después de un reinicio, primero se abre Tailscale** (lo recoge la guía de T022).
- Servidor arrancado otra vez con el mismo comando de T003 (nuevo proceso, solo en `127.0.0.1:8000`).
- Desde el celular con datos: `/salud` → `200`. Por el relay público: `{"estado":"ok","llave_pey":true,"secreto_aviso_pey":false}` con certificado válido.
- **Resultado**: la dirección es exactamente la misma después de reiniciar el servidor, el túnel y la computadora (RF-030).

### Resultado de F0

Tailscale Funnel cumple lo que el plan da por hecho (QP-12, research R-1 y R-2): HTTPS válido, canal de toda la ventana sin retener ni cortar eventos, IP real y dirección fija. No hace falta el plan B. Anotado como TK-5 en el plan.

- Hugo dijo "seguimos" con Tailscale Funnel el 2026-11-21.
- Demo apagada al terminar: servidor parado por su PID exacto y `tailscale funnel reset` (`tailscale funnel status` → `No serve config`). Para encenderla otra vez: abrir Tailscale, arrancar el servidor y `tailscale funnel --bg 8000`.
- Commit sugerido: `docs(003): prueba del túnel con Tailscale Funnel (F0)`.
