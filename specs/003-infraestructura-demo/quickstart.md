# Guía rápida (Fase 1): comprobar la spec 003 de punta a punta

> **Sustituido.** El 2026-11-17 la spec cambió de rumbo (D-4): ya no hay AWS, dominio, presupuesto ni publicación, y la demo sale por un túnel desde una computadora del equipo. Este documento queda como historia de la versión con AWS y se rehace con el plan nuevo.

- **Fecha**: 2026-11-17
- **Plan**: [plan.md](plan.md)
- **Para quién**: Hugo (todo) y Juan (CI y migraciones). Cada sección dice qué comprueba y qué se espera ver. Los detalles están en los [contratos](contracts/) y en el [modelo de datos](data-model.md); los pasos de AWS, en `docs/operacion-demo.md`, que se escribe en F4.

> Ningún paso imprime ni pega en un chat `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` ni `DATABASE_URL`. Para saber si están puestos se usa `GET /salud`.

---

## 0. Requisitos previos

- `uv` instalado, y el repositorio en la rama de la spec.
- Un proyecto de Supabase **local** (el segundo proyecto, RF-049) y su URL del *pooler* en modo sesión en `backend/.env` como `DATABASE_URL`.
- Para las pruebas del almacén en tu computadora (opcional): un PostgreSQL 17 vacío y su URL en `PRUEBAS_DATABASE_URL`. Sin ella, esas pruebas se saltan con el motivo escrito; en el CI siempre corren.

## 1. Pruebas automáticas (CE-005, CE-010, CE-011)

```text
uv run --directory backend pytest -q
uv run --directory backend ruff check .
uv run --directory backend ruff format --check .
uv run --directory backend pytest ../web -q
```

**Se espera**: todo en verde, sin conexión a pey ni a Supabase. Las pruebas de deduplicación (aviso reenviado, aviso y consulta a la vez, antes y después de un "reinicio" simulado con un almacén nuevo sobre los mismos datos) pasan.

## 2. CI (CE-006) — F1

1. Abre un pull request hacia `main` con un `assert False` en una prueba.
2. **Se espera**: el trabajo `servidor` sale en rojo y GitHub no deja unir.
3. Quita el `assert False`. **Se espera**: los trabajos en verde.
4. Revisa el flujo: `permissions: contents: read` y ningún `secrets.` ([contrato](contracts/ci.md)).

## 3. Migraciones (CE-007, RF-054) — F2

```text
uv run --directory backend python -m app.migraciones aplicar --entorno local --datos-de-prueba
uv run --directory backend python -m app.migraciones aplicar
uv run --directory backend python -m app.migraciones estado
```

**Se espera**: la primera aplica 0001 y 0002 y carga los datos de prueba; la segunda dice "No había nada que aplicar."; `estado` muestra `local` y las dos versiones. En el CI, el trabajo `base-de-datos` hace lo mismo sobre un PostgreSQL vacío.

**Datos de prueba en la demo (RF-054)**: con una base marcada `demo`, `aplicar --datos-de-prueba` debe responder "Los datos de prueba solo se cargan en la base local." y no cargar nada.

## 4. El cobro sobrevive a un reinicio (historia 1, CE-001 en local) — F3

1. Arranca el servidor: `uv run --directory backend uvicorn app.main:app --port 8000` (con `CARPETA_WEB=../web` en `backend/.env`).
2. Abre `http://localhost:8000`, crea un cobro de monto fijo y deja el QR en pantalla.
3. Detén el servidor (Ctrl+C) y vuelve a arrancarlo.
4. **Se espera**: la pantalla dice "Reconectando…" y vuelve sola al mismo QR, con el mismo monto, concepto y tiempo.
5. `GET /api/cobros/<id>` devuelve el cobro con `qr_imagen` (RF-010).
6. `GET /salud` devuelve `base_de_datos: "responde"` (RF-023).

## 5. Falla de la base de datos (RF-012, RF-015) — F3

1. Con el servidor arrancado, cambia `DATABASE_URL` por una dirección que no exista (por ejemplo, otro puerto) y reinicia.
2. Toca Cobrar. **Se espera**: "No se pudo guardar el cobro. Intenta de nuevo en un momento." y, en el log, ninguna llamada a pey ni ningún dato de la conexión.
3. `GET /salud` → `base_de_datos: "no responde"`.
4. Vuelve a poner la `DATABASE_URL` buena.

## 6. Demo pública (historias 2 y 4) — F4

Hugo, con `docs/operacion-demo.md`:

1. **Primero el presupuesto** (CE-008): créalo, baja un momento el umbral del 50 % por debajo del gasto actual y comprueba que llega el correo a los tres integrantes. Regrésalo al 50 %.
2. Configura el dominio en Route 53, crea la instancia, la IP elástica, el grupo de seguridad, los dos certificados y CloudFront; escribe `/etc/pago-facil/entorno` (con los límites de la demo en 30, DP-36); publica con `publicar.sh` (contrato de [publicación](contracts/publicacion.md)).
3. Desde un celular **con datos móviles**, abre `https://<dominio>`. **Se espera**: la pantalla de cobro con HTTPS y sin advertencias (RF-024).
4. Crea 10 cobros y anota cuánto tarda cada QR. **Se espera**: 9 de 10 en menos de 3 s (CE-003).
5. **Canal de 20 minutos** (CE-004): crea un cobro, no lo pagues y deja la pantalla abierta. **Se espera**: a los 10 min "vencido"; el canal sigue hasta el min 20 y termina con `fin`, sin "Reconectando…" antes. *Se hace al principio de F4 (research R-3).*
6. **CORS** (RF-027): desde la consola del navegador en otra página (por ejemplo `https://example.com`), `fetch("https://<dominio>/api/cobros", {method: "POST"})`. **Se espera**: lo bloquea el navegador.
7. **IP real** (RF-028): crea 31 cobros en un minuto desde el mismo celular (el límite de la demo es 30, DP-36). **Se espera**: el 31.º dice "Demasiados cobros seguidos". Con otro celular **en otra red** (wifi frente a datos; dos celulares de la misma compañía pueden compartir IP pública), sí deja crear.
8. Revisa que el costo estimado quede anotado en el plan (CE-009, research R-6).
9. **Cifrado hasta el servidor** (RF-056, CE-015): desde tu computadora, `curl -m 5 http://<ip-elástica>/` y `curl -m 5 https://origen.<dominio>/salud` no reciben respuesta (el grupo de seguridad solo deja entrar a CloudFront); en CloudFront, el origen dice "solo HTTPS".

## 7. Pago real (historia 3, CE-001, CE-002) — F5, con autorización de Hugo

1. Da de alta en el portal de pey el aviso `https://<dominio>/webhooks/pey` con su secreto (RF-025).
2. En un **Android** con datos móviles, cobra $0.01; paga desde otro celular con la app del banco, en CoDi.
3. Mide desde la hora del aviso en el portal de pey hasta que suena "Pago recibido". **Se espera**: menos de 2 s (CE-002). Repite en un **iPhone**.
4. Pide a pey reenviar el aviso desde su portal. **Se espera**: la pantalla no vuelve a sonar y el cobro sigue con un pago (historia 3, escenario 3).
5. **Reinicio** (CE-001): crea un cobro, reinicia el servicio (`sudo systemctl restart pago-facil` en Session Manager), recarga la pantalla y paga $0.01. **Se espera**: el mismo QR y "Pago recibido".
6. **Tres publicaciones seguidas** (CE-014): con un cobro abierto, publica tres veces. **Se espera**: cada corte dura menos de 1 min y la pantalla se reconecta sola, sin perder sus pagos.

## 8. Corte 2 — F6 y F7

- **Publicación automática** (CE-013): une un pull request pequeño a `main`. **Se espera**: el flujo `publicar` en verde y la versión nueva en la demo, sin que nadie haga nada. Busca en el repositorio y en la configuración de GitHub: ninguna llave de AWS, solo la variable `AWS_ROL_PUBLICACION`.
- **Demo apagada** (RF-045): con la instancia detenida, el flujo `publicar` sale en rojo con "La demo está apagada; solo Hugo la enciende" y la instancia sigue detenida.
- **Estructura pendiente** (RF-047): publica una versión con una migración nueva sin aplicarla. **Se espera**: `GET /salud` → `estructura: "pendiente"` y Cobrar muestra "La demo se está actualizando…". Aplica la migración (con copia previa, RF-051) y comprueba que vuelve a `al dia`.
- **8 días sin pausa** (CE-012): durante 8 días sin cobros, `journalctl -u pago-facil | grep "Consulta de vida"` muestra al menos una línea por día, y el proyecto de Supabase sigue activo. No bloquea el cierre.
