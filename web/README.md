# Web — PAGO FÁCIL

Web del negocio como **PWA** (HTML, CSS, JavaScript). Se instala desde el navegador en Android, iPhone y computadora, sin pasar por tiendas de apps.

## Pantallas

- Registro e inicio de sesión del negocio.
- **Cobrar:** monto + concepto → QR CoDi en grande.
- **Pago recibido:** sonido + aviso visual a pantalla completa.
- Historial de cobros y corte del día.
- Cupones y plan Premium.

## Reglas

- La web **nunca** llama directamente a pey ni guarda la API key: todo pasa por el backend.
- Debe verse bien primero en celular, porque es donde la usará el negocio.

## MVP

El MVP es la pantalla que ya está en esta carpeta: teclado, QR y aviso de pago. La PWA instalable, el registro, el historial, los cupones y Premium siguen siendo la meta del proyecto; no forman parte de este MVP.

Hay dos cortes:

- **Corte 1.** Teclado con monto fijo, QR con cuenta regresiva, sonido y "Pago recibido", respaldo si se corta el canal, QR vencido, Nuevo cobro y pantalla encendida mientras hay un cobro en escucha.
- **Corte 2.** Monto libre, "Pago n" y el total, Mostrar QR otra vez, cobros anteriores, Cancelar cobro y recuperar los cobros al recargar.

Los comandos de abajo se corren desde la raíz del repositorio. El recorrido completo está en [specs/002-web-mvp/quickstart.md](../specs/002-web-mvp/quickstart.md).

### Configurar

`web/config.js` tiene un solo valor, `servidor`:

- `""` — el mismo origen. Es el valor del repositorio. Sirve para las pruebas y para cuando el propio backend entregue la web.
- `"http://localhost:8000"` — la pantalla en esta computadora, contra el servidor local.
- `"https://<dominio del servidor>"` — sitio estático publicado aparte.

### Correr en local

Con el servidor en el puerto 8000, como dice el quickstart de la spec 001, y `WEB_ORIGIN=http://localhost:5173` en `backend/.env`:

```bash
uv run --directory backend python -m http.server 5173 --directory ../web
```

Abre `http://localhost:5173`. Se ve "PAGO FÁCIL", el teclado y Cobrar desactivado. No abras el enlace `http://[::]:5173` que imprime el comando: el servidor lo rechaza por CORS (`WEB_ORIGIN`) y la pantalla dice que no hay conexión.

En `http://localhost` el celular no mantiene la pantalla encendida: el navegador solo lo permite con HTTPS, o en `localhost` de la propia máquina.

### Probar

La primera vez, instala los navegadores de las pruebas:

```bash
uv run --directory backend playwright install chromium webkit
```

```bash
uv run --directory backend pytest ../web -q
uv run --directory backend ruff check --config pyproject.toml ../web
uv run --directory backend ruff format --config pyproject.toml --check ../web
```

Esas pruebas usan un servidor simulado. No llaman a pey ni al servidor real.

### Publicar

Lo publica el issue #65. Se suben los archivos de `web/` sin `tests/` ni este `README.md`. Hay dos formas:

| Forma | `web/config.js` | En el servidor |
|---|---|---|
| Sitio estático aparte, con HTTPS | `servidor: "https://<dominio del servidor>"` | Agregar el dominio de la web a `WEB_ORIGIN` |
| Servida por el backend | `servidor: ""` | Antes hay que proponer un cambio `C-n` a la spec 001 |

Antes de publicar, en `web/index.html`, cambia `https:` de `connect-src` (la política de seguridad de contenido) por el dominio exacto del servidor. Si la web la sirve el backend, basta `'self'`.

Después de publicar hay que comprobar tres cosas: la web abre con HTTPS, el navegador no muestra errores de CORS al crear un cobro, y el canal de avisos se mantiene abierto porque el proxy no retiene los eventos.
