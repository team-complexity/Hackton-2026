# Investigación (Fase 0): Spec 003 — Infraestructura de la demo por el túnel

- **Fecha**: 2026-11-20 (versión con túnel). La versión con AWS (R-1 a R-19 del 2026-11-17) está en el historial de git, en el commit `5db47ed`.
- **Plan**: [plan.md](plan.md)
- **Base**: el código de la rama `feature/90-infraestructura-demo` (`5db47ed`), la constitución 3.0.0 del PR #96 (`a962dc5`), el esquema del PR #97 (`supabase/001_esquema_inicial.sql`, en `main`), la spec aprobada el 2026-11-20 y la documentación citada en cada punto, leída el 2026-11-20.

Cada punto sigue el formato **Decisión / Por qué / Alternativas**. Los puntos con comparativa (R-1, R-6 y R-7) llevan una recomendación: decide Hugo (principio IX), y su decisión queda en el plan (§9.2). R-6 y R-7 ya los decidió Hugo el 2026-11-17 y siguen igual.

---

## R-1. Servicio de túnel (comparativa, DP-38)

Se compara contra los 7 criterios del túnel de la spec (§7, QA-16). "No documentado" quiere decir que la documentación oficial leída no lo dice; esos puntos se comprueban en la primera prueba de F2.

| Criterio (spec §7) | A. Tailscale Funnel (recomendada) | B. Cloudflare Tunnel con nombre + dominio propio | C. ngrok gratuito | D. Túnel rápido de Cloudflare / `localhost.run` |
|---|---|---|---|---|
| 1. HTTPS sin advertencias | Certificados válidos automáticos ("Tailscale automatically creates valid HTTPS certificates", [funnel](https://tailscale.com/kb/1223/funnel)); no documenta páginas intermedias | Sí, con el dominio en Cloudflare | **No**: "ngrok shows an interstitial page in front of all HTML browser traffic on the free tier" ([free-plan-limits](https://ngrok.com/docs/pricing-limits/free-plan-limits/)) | Sí |
| 2. Canal sin retención | El HTTPS termina en la computadora y el relevo solo pasa bytes cifrados, así que no puede retener eventos HTTP. Sin tiempos de corte documentados | No documentado para túneles con nombre; el rápido sí falla (columna D) | No documentado | **No**: "Quick Tunnels do not support Server-Sent Events (SSE)" ([quick-tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)), lo mismo que se vio en la 002 |
| 3. Canal durante toda la ventana | No documentado; se prueba primero (20 minutos) | No documentado; se prueba primero | No documentado | `localhost.run` se cortó cada ~16 min (002) |
| 4. Dirección fija | Sí, sin dominio propio: "Funnel can only use DNS names in your tailnet's domain (`tailnet-name.ts.net`)" | Sí, pero "A domain on Cloudflare (required to publish applications)" ([tunnel](https://developers.cloudflare.com/tunnel/get-started/)) | Sí: un dominio de desarrollo que "doesn't change when you restart the agent" | **No**: "The hostname changes each time you create a Quick Tunnel" |
| 5. IP real del celular | No documentado. Funnel no agrega cabeceras de identidad ([serve](https://tailscale.com/kb/1312/serve)); si tampoco manda `X-Forwarded-For`, todas las peticiones llegan como `127.0.0.1` (R-2) | Cloudflare manda la IP del visitante en sus cabeceras (no se leyó en esta pasada; se comprueba en F2 si se elige B) | No documentado | — |
| 6. Gratis | Sí: plan Personal, "$0 Free forever", y Funnel "available for all plans" ([pricing](https://tailscale.com/pricing)). Ojo: el plan Personal dice "only suitable for non-commercial use", y Funnel está en beta | El túnel es gratis; el dominio cuesta (un `.xyz`, unos pocos dólares al año) | Sí, pero con 1 GB al mes y 20 000 peticiones HTTP al mes. La consulta de respaldo de una pantalla abierta pide cada 3 a 5 s, así que tres días de evaluación pasan de ese límite | Sí |
| 7. HTTPS termina en la computadora | **Sí**: "The Tailscale server running on your device … terminates the TLS connection" | No: termina en Cloudflare, así que Cloudflare ve los avisos de pey sin cifrar (limitación aceptada, spec §4) | No (termina en ngrok) | No |
| Curva de aprendizaje | Baja: instalar Tailscale, iniciar sesión, activar HTTPS y Funnel, y `tailscale funnel 8000` | Media: comprar el dominio, pasarlo a Cloudflare, `cloudflared` y su configuración | Baja | Baja |

**Decisión**: **A, Tailscale Funnel** (Hugo, 2026-11-20), como se recomendaba. Es la única que cumple los 7 criterios sin pagar ni comprar un dominio. Además, el HTTPS termina en la computadora de la demo, así que nadie más ve los datos de quien paga. Lo que no está documentado (canal largo, IP real y si el nombre sobrevive al reinicio de la computadora) se prueba **antes que todo lo demás de F2**, en este orden: canal de 25 minutos con eventos, IP real (R-2) y reinicio de la computadora.
**Si A falla en esa prueba**: **B**, con un dominio barato. Comprar el dominio es una decisión nueva de Hugo (spec §7: "Si solo hay opción de pago, es una decisión nueva de Hugo"), y Cloudflare viendo los avisos queda como limitación aceptada (spec §4).
**Descartadas**: C, por la página de advertencia (criterio 1) y por el límite de peticiones. D, por los criterios 2, 3 y 4.
**Riesgos de A**: (a) beta y plan "no comercial": la demo del hackathon y las pruebas con pilotos no venden nada, pero si el proyecto sigue después, se cambia de túnel; (b) límites de ancho de banda sin número, de sobra para unos KB por cobro.

## R-2. La IP real del celular a través del túnel

**Decisión**: no se agrega código. El servidor ya usa `ProxyHeadersMiddleware` con `PROXIES_CONFIABLES=127.0.0.1` (`backend/app/main.py:140`, `config.py:35`). El agente del túnel (`tailscaled` o `cloudflared`) se conecta al servidor desde `127.0.0.1`, así que si manda `X-Forwarded-For`, el límite ya usa la IP del celular (RF-028). uvicorn toma de `X-Forwarded-For` la primera IP de derecha a izquierda que no está en la lista de confianza, así que un celular que mande su propio `X-Forwarded-For` falso no puede cambiar la IP que cuenta.
**Comprobación (F2, paso 2)**: abrir la demo desde dos celulares en redes distintas y ver en el registro del servidor que cuenta dos IP distintas, y que ninguna es `127.0.0.1`.
**Si el túnel no manda la IP**: todas las peticiones cuentan como una sola IP, y el límite por IP se vuelve un límite para toda la demo. Entonces, en la demo, `LIMITE_COBROS_POR_MINUTO` y `CANALES_POR_IP` suben a 60. Queda como limitación escrita (TK en el registro de implementación) y no cambia ningún RF: RF-028 queda incumplido solo para la demo, y se anota.
**Alternativas**: una cabecera propia del túnel (como la de Cloudflare). Solo si se elige B en R-1.

## R-3. El canal de avisos a través del túnel

**Decisión**: el canal no cambia. Ya manda una señal de vida cada 15 s (`backend/app/canal.py:91`), así que ninguna conexión pasa más de 15 a 20 s sin datos. La prueba de 25 minutos de F2 comprueba RF-026, RF-057 y CE-004 antes de construir lo demás.
**Por qué**: con A (R-1), el HTTPS termina en la computadora y nadie en medio puede retener eventos. Con B, Cloudflare suele cortar una respuesta que pasa unos 100 s sin datos (no se leyó en esta pasada); la señal de vida cada 15 s queda muy por debajo.

## R-4. Encender la demo en la Mac de Hugo

**Decisión**: la demo es la computadora de Hugo con dos procesos y un tercero que la mantiene despierta. La guía `docs/operacion-demo.md` (RF-058) lleva los pasos:

1. Poner al día la rama `main` y las dependencias (`uv sync --locked`).
2. En el corte 2: exportar una copia de la base de la demo y aplicar las migraciones pendientes (RF-017, RF-051).
3. Arrancar el servidor **solo en `127.0.0.1`** (el valor por defecto de uvicorn; la guía nunca usa `--host 0.0.0.0`), con `--workers 1` y con `CARPETA_WEB` (RF-056, R-6 de la 001).
4. Arrancar el túnel hacia el puerto 8000.
5. Mantener la computadora despierta con `caffeinate` mientras la demo está encendida, conectada a la corriente (supuesto de la spec §7).
6. Pedir `/salud` desde un celular con datos móviles (CE-016).

**Por qué**: RF-058 pide una sola guía, y RF-060 pide que la demo no se suspenda en los momentos acordados. `caffeinate` viene con macOS: no es una herramienta nueva.
**Configuración de la demo** (en `backend/.env.demo` de la computadora de Hugo, que git ignora por `.env.*`; nunca en el repositorio): `PEY_API_KEY` y `PEY_WEBHOOK_SECRET` de la llave de la demo, `DATABASE_URL` (corte 2), `WEB_ORIGIN` con la dirección del túnel, `CARPETA_WEB=../web` y los límites de la demo (DP-36). El servidor la carga con `uvicorn … --env-file .env.demo`, y el comando de migraciones con `uv run --env-file backend/.env.demo`. En pydantic-settings las variables de entorno mandan sobre `backend/.env`, así que no hace falta código nuevo (QP-14).
**Desarrollo en la misma computadora**: `backend/.env`, con la segunda llave y la base de desarrollo. Si la demo está encendida, el servidor de desarrollo usa el puerto 8001.
**Servidor de desarrollo**: el mismo arranque, con la segunda llave de producción (RF-053) y la base de desarrollo (RF-049). Si quien prueba quiere avisos de pey, levanta su propio túnel y lo da de alta en el aviso de esa llave; si no, usa la consulta de respaldo.

## R-5. Conciliación al arrancar (RF-061)

**Decisión**: un **latido de conciliación** guardado en la base de datos (DP-39):

- Una tabla de una sola fila, `estado_del_servidor`, guarda `conciliado_hasta`: la última hora hasta la que el servidor revisó las ventanas que terminaron.
- La tarea de fondo (DP-14), cada 60 s del `Reloj`, busca los cobros cuya `fin_ventana` cae entre `conciliado_hasta` y ahora, consulta en pey sus transacciones (`GET /transaction/codi/qr/{id}`, la misma consulta de la consulta de respaldo) y registra las que falten, con `fuente = consulta`. Después mueve `conciliado_hasta` a ahora.
- La primera vez (sin fila), la crea con la hora actual y no revisa nada hacia atrás.
- Si pey responde 4xx con un cobro (por ejemplo, un QR que no conoce, como los ficticios de los datos de prueba), se registra y ese cobro se salta. Si la falla es pasajera (sin conexión, tiempo agotado, 5xx), `conciliado_hasta` solo avanza hasta antes de ese cobro y el siguiente latido lo vuelve a intentar, hasta 10 veces; después se registra como `ERROR` y se salta (QP-13).

**Por qué**: así se cubren los dos huecos de §4 de la spec con una sola pieza: las ventanas que terminaron con el servidor apagado (al arrancar, `conciliado_hasta` es la hora del último latido antes de apagarse) y los avisos que se perdieron de la memoria en un reinicio (la ventana de su cobro termina después, con el servidor encendido, y el latido la revisa). Cuesta una consulta a pey por cobro, una sola vez. La escritura de cada minuto también cumple RF-039 (uso diario de la base de datos), así que la consulta de vida cada 6 h de la versión con AWS ya no hace falta.
**Sin sonido**: cuando termina la ventana, el canal ya está cerrado (RF-032 de la 001), así que nadie recibe el pago en ese momento; queda guardado para el historial (#38).
**Alternativas**: (a) revisar al arrancar todos los cobros de los últimos 7 días: muchas consultas a pey en cada arranque, y no cubre los avisos perdidos de cobros que siguen abiertos; (b) una columna `conciliado_en` por cobro: una escritura por cobro y una consulta más compleja para el mismo resultado.

## R-6. Librería para conectarse a PostgreSQL (comparativa, DP-2; decidida)

| | A. psycopg 3 (`psycopg[binary]` + `psycopg-pool`) (decidida) | B. asyncpg | C. SQLAlchemy 2 asíncrono + un controlador |
|---|---|---|---|
| Asíncrono | Sí, y también síncrono (sirve para el comando de migraciones) | Sí, solo asíncrono | Sí |
| SQL | SQL escrito a mano con parámetros `%s` | SQL a mano con `$1` | ORM o SQL; una capa más |
| Con el *pooler* de Supabase | Funciona en modo sesión y en modo transacción (`prepare_threshold=None`) | En modo transacción hay que apagar las sentencias preparadas | Según el controlador |
| Dependencias nuevas | 2 | 1 | 2 o más |
| Curva de aprendizaje | Baja: el mismo SQL del PR #97 | Baja | Media o alta: el ORM no hace falta |

**Decisión**: **A** (Hugo, 2026-11-17). Una sola librería para el servidor y para el comando de migraciones, con el mismo SQL del PR #97, sin ORM. Se fija a versiones publicadas hace al menos dos semanas.

## R-7. Herramienta para los cambios de estructura (comparativa, DP-3; decidida)

| | A. Comando propio con psycopg (decidida) | B. CLI de Supabase (`supabase db push`) | C. dbmate |
|---|---|---|---|
| Qué es | `python -m app.migraciones`: aplica en orden los `.sql` de `supabase/migraciones/` y anota cada uno en una tabla | Herramienta oficial; migraciones en `supabase/migrations/` | Un ejecutable de Go con SQL plano |
| Herramienta nueva | Ninguna (usa R-6) | Un ejecutable en cada computadora y en el CI | Un ejecutable |
| Idempotente (RF-019) | Sí: salta lo ya anotado | Sí | Sí |
| Base de la demo creada a mano (historia 6, escenario 3) | Opción `--ya-aplicada 0001` después de revisar | `supabase migration repair` | Insertar la fila a mano |
| Datos de prueba solo en desarrollo (RF-054) | Marca de entorno en la base (DP-18) | `seed.sql` solo en su entorno local con Docker | No tiene |

**Decisión**: **A** (Hugo, 2026-11-17). Corre igual en desarrollo, en el CI y desde la computadora de Hugo contra la demo (RF-017), y se prueba en el CI contra un PostgreSQL desechable (R-10, CE-007).

## R-8. Cómo guardar sin cambiar el comportamiento de la 001

**Decisión**: el servidor sigue trabajando con los objetos `Cobro` en memoria (el canal y la consulta de respaldo no cambian), pero la memoria pasa a ser una **caché de escritura directa** sobre un *almacén*:

1. Toda escritura va **primero** a la base de datos; solo si se guardó se cambia la memoria y se emite por el canal (RF-002).
2. Un cobro que no está en memoria (después de un reinicio) se carga de la base de datos al pedirlo por su id o por su `codi_qr_id` (RF-005), y nunca quedan dos objetos del mismo cobro (DP-33).
3. Registrar un pago va dentro de un candado por cobro (`asyncio.Lock`): el número se calcula dentro del candado, y `insert … on conflict (transaccion_id) do nothing returning` dice si el pago es nuevo (RF-007, RF-008).

**Por qué**: hay un solo proceso, así que la memoria no puede quedar desactualizada. El candado evita que el aviso, la consulta de respaldo y la conciliación calculen el mismo número a la vez; `unique (cobro_id, numero)` del PR #97 queda como red.
**Alternativas**: leer siempre de la base de datos (una consulta cada 3 a 5 s por pantalla abierta); cargar todos los cobros al arrancar (innecesario).

## R-9. Conexión con Supabase desde la computadora de la demo

**Decisión**: `DATABASE_URL` apunta al *pooler* de Supabase en **modo sesión** (puerto 5432), con un *pool* de 1 a 3 conexiones y 5 s de espera para conectar.
**Por qué**: la conexión directa de Supabase es solo por IPv6 (QA de la spec, versión con AWS, bloque 5), y no todas las redes de casa o de un evento dan IPv6. El *pooler* funciona por IPv4. El modo sesión admite todo PostgreSQL. Con un solo proceso, 3 conexiones sobran.
**Latencia**: cada escritura viaja de la computadora de Hugo a la región del proyecto de Supabase. Se mide en F3 contra CE-003 (QR en menos de 3 s) y contra la respuesta al aviso de pey en menos de 1 s (CE-010 de la 001).

## R-10. Probar el almacén sin la base de datos real

**Decisión**: dos niveles:

- **Las pruebas de la API** (todas las de hoy y las nuevas de fallas y conciliación) usan el almacén en memoria y un almacén que falla a propósito. No necesitan PostgreSQL.
- **Las pruebas del almacén de PostgreSQL y del comando de migraciones** corren contra un **PostgreSQL 17 desechable**: en el CI, un contenedor de servicio de GitHub Actions; en una computadora, solo si se define `PRUEBAS_DATABASE_URL` (si no, se saltan con el motivo escrito). Antes de migrar, la prueba crea los roles `anon` y `authenticated`, que el PR #97 usa en su `revoke` y que solo existen en Supabase.

**Por qué**: CE-011 y RF-038 prohíben la base de datos **real**, no un PostgreSQL vacío que se crea y se destruye en cada corrida.

## R-11. CI en GitHub Actions

**Decisión**: `.github/workflows/ci.yml`, con `pull_request` hacia `main` y `push` a `main`, `permissions: contents: read`, sin secretos, y tres trabajos en `ubuntu-latest` ([contrato](contracts/ci.md)):

1. **`servidor`** (F1): `uv sync --locked`, `ruff check`, `ruff format --check` y `pytest -q`.
2. **`web`** (F1): lo mismo para `../web`, más `playwright install --with-deps chromium webkit`.
3. **`base-de-datos`** (F4, corte 2): PostgreSQL 17 como servicio; corre el comando de migraciones dos veces (CE-007) y las pruebas del almacén.

**Por qué**: RF-036 a RF-038. `pull_request` (no `pull_request_target`) no expone secretos a los forks. La protección de `main` exige los trabajos y ya no exige aprobación (constitución 3.0.0; dependencia de §7 de la spec).
**Riesgo**: las pruebas de WebKit en Linux. El PR #72 trae su arreglo (`1a15c14`); si alguna falla en el CI, se decide en ese momento con un TK (`skip` con motivo escrito o arreglo).

## R-12. La web, desde el mismo servidor

**Decisión**: el servidor entrega la carpeta `web/` en `/` cuando `CARPETA_WEB` está definida (en la demo y en desarrollo; vacía en las pruebas del servidor). La CSP de `web/index.html` queda en `connect-src 'self'` (DP-21).
**Por qué**: con un solo túnel hacia un solo puerto, la web y el servidor quedan en el mismo origen. `web/config.js` ya vale `""` para ese caso (spec 002, RF-064). La web solo puede conectarse a su propio servidor (RF-029), y CORS solo deja pasar la dirección del túnel (RF-027).
**Consecuencia en desarrollo**: la web se abre en `http://localhost:8000` en lugar del puerto 5173. Se quita esa forma del `web/README.md` y de los documentos de la 002 con el cambio C-7 (b) y (c).
**Alternativas**: dos túneles (uno para la web y otro para el servidor): dos direcciones fijas, CORS entre ellas y una CSP más abierta.
