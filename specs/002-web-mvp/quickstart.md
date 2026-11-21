# Quickstart: Web del MVP

Guía para comprobar la pantalla de punta a punta. Los detalles están en [contracts/](contracts/) y en [data-model.md](data-model.md). El servidor se arranca con el [quickstart de la 001](../001-backend-mvp/quickstart.md).

## 1. Requisitos previos

- uv instalado y `uv sync` hecho en `backend/` (ver el quickstart de la 001).
- Las herramientas de prueba de la web, después de F1:

```bash
uv run --directory backend playwright install chromium webkit
```

- Si WebKit no arranca en esta Mac (macOS muy nuevo), se sigue la alternativa de QP-5 del plan.

- Para las pruebas reales: un Android con Chrome, un iPhone con Safari, CoDi activo en la app del banco y la autorización de Hugo para pagar $0.01.

## 2. Pruebas automáticas (sin pey ni servidor real)

```bash
uv run --directory backend pytest ../web -q
```

**Esperado**: todo en verde, en Chromium (`Pixel 7`) y en WebKit (`iPhone 13`), con el servidor simulado y el reloj controlado. La configuración de pytest está en `web/pytest.ini` (QP-3). Las del backend se siguen corriendo aparte:

```bash
uv run --directory backend pytest -q
```

## 3. La pantalla en local, contra el servidor real en local

1. En `backend/.env`, agrega `WEB_ORIGIN=http://localhost:5173` (sin tocar las demás variables) y arranca el servidor como dice el quickstart de la 001 (puerto 8000).
2. En `web/config.js`, pon `servidor: "http://localhost:8000"`.
3. Sirve la carpeta `web/`:

```bash
uv run --directory backend python -m http.server 5173 --directory ../web
```

4. Abre `http://localhost:5173` en el navegador de la computadora, en modo celular (herramientas de desarrollo, 320 px de ancho).

**Esperado**: la vista Teclado con "PAGO FÁCIL", el teclado y Cobrar desactivado. Con la llave de pey configurada, un cobro de $0.01 muestra el QR real con su cuenta regresiva.

En `http://localhost` no hay pantalla encendida en el celular: el navegador solo la permite con HTTPS o en `localhost` de la propia máquina.

## 4. Despliegue (para #65)

La web son archivos estáticos: `web/` sin `tests/` ni `README.md`. Puede publicarse de dos formas (DP-4, lo decide #65):

| Forma | `web/config.js` | En el servidor |
|---|---|---|
| Sitio estático aparte, con HTTPS | `servidor: "https://<dominio del servidor>"` | Agregar el dominio de la web a `WEB_ORIGIN` |
| Servida por el backend | `servidor: ""` | Es un cambio al servidor: antes hay que proponer un `C-n` a la spec 001 |

Antes de publicar, en `web/index.html`, cambiar `https:` de `connect-src` (política de seguridad de contenido) por el dominio exacto del servidor (QP-2). Si se sirve desde el backend, basta `'self'`.

Comprobar después de publicar:

- la web abre con HTTPS;
- el navegador no muestra errores de CORS al crear un cobro;
- el canal de avisos se mantiene abierto: el proxy no retiene los eventos (ver "Despliegue" en el quickstart de la 001).

## 5. Cierre del corte 1: pago real (con autorización de Hugo)

En el Android y después en el iPhone, con la web publicada:

1. Teclea 0, punto, 0, 1 → se ve "$0.01". Pulsa Cobrar.
2. **Esperado**: Generando QR al instante; el QR con "$0.01", la indicación de CoDi y la cuenta regresiva.
3. Paga desde la app del banco, en la opción CoDi.
4. **Esperado**: suena, vibra (solo en Android) y la pantalla se pone verde con "Pago recibido", "$0.01" y el concepto (CE-001, CE-002).
5. Pulsa Nuevo cobro, crea otro cobro y mide el tiempo hasta ver el QR: menos de 3 s (CE-006, sin contar el primer cobro después de arrancar el servidor).
6. Teclea 2, 5, punto, 5, 0 y comprueba que basta un sexto toque (Cobrar) para pedir el cobro (CE-004).
7. Pon el iPhone en silencio y repite el pago: anota si suena (riesgo R-7) en el registro de implementación del plan.

## 6. Pantalla encendida (CE-011)

En el Android, con la web publicada en HTTPS, crea un cobro y no toques el celular durante 10 minutos.

**Esperado**: la pantalla sigue encendida hasta que termina la escucha.

## 7. Corte 2 (cuando se entregue)

- **Monto libre**: con el monto vacío, Monto libre crea un QR que muestra "Monto libre", y el banco pide escribir la cantidad. Con un monto escrito, la tecla está desactivada.
- **Cobro anterior**: crea un cobro, pulsa Nuevo cobro y paga el QR anterior. **Esperado**: suena y aparece su aviso sin borrar lo tecleado (CE-013).
- **Cancelar**: crea un cobro, pulsa Cancelar cobro y paga ese QR. **Esperado**: vuelve el teclado, y al pagar suena y aparece el aviso.
- **Recargar**: crea un cobro, recarga la página y toca la pantalla. **Esperado**: vuelve el cobro; al pagarlo, suena (CE-014).
