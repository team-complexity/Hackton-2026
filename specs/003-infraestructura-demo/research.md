# Investigación (Fase 0): Spec 003 — Infraestructura de la demo pública

- **Fecha**: 2026-11-17
- **Plan**: [plan.md](plan.md)
- **Base**: el código de la rama `feature/90-infraestructura-demo`, la constitución 2.0.0 del PR #96 (commit `aa187d7`), el esquema del PR #97 (`supabase/001_esquema_inicial.sql`, commit `891960d`) y la documentación citada en cada punto.

Cada punto sigue el formato **Decisión / Por qué / Alternativas**. Los puntos con comparativa (R-1, R-8, R-9 y R-14) llevan una recomendación: decide Hugo (principio IX), y su decisión queda en el plan (§9.2).

---

## R-1. Servicio de AWS para el servidor y la web (comparativa, DP-1)

**Lo que se necesita** (spec 003): un solo proceso (RF-055, QP-5 de la 001); un canal de avisos de 20 minutos sin cortes (RF-026); HTTPS en la dirección que asigna AWS, sin dominio propio (RF-024); que el presupuesto pueda apagarlo solo (RF-034); costo ≤ 150 dólares hasta el 31 de enero de 2027 (RF-035); y la misma dirección después de cada publicación y de cada apagado (RF-030).

| | A. EC2 + CloudFront (recomendada) | B. Lightsail, servicio de contenedores | C. App Runner | D. ECS Fargate + balanceador + CloudFront |
|---|---|---|---|---|
| HTTPS sin dominio | Sí: `*.cloudfront.net` trae su certificado | Sí: dirección propia del servicio | Sí | Solo con CloudFront delante: el balanceador no da HTTPS sin dominio |
| Canal de 20 min | Sí, si llega un dato cada menos de 30 s (R-3); el canal manda señal de vida cada 15 s | Sin confirmar: no se pudo leer su tiempo de inactividad (QA de la spec, bloque 7) | **No**: corta toda petición a los 120 s ([App Runner, develop](https://docs.aws.amazon.com/apprunner/latest/dg/develop.html); [re:Post sobre SSE](https://repost.aws/questions/QUHFHBKsCYQlueDcXywdZ5jw/apprunner-timeout-for-sse-connection)) | Sí (balanceador hasta 4000 s) |
| Apagado por el presupuesto | **Nativo**: la acción "detener instancias EC2" de AWS Budgets ([budgets-controls](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)) | Hace falta una función propia (aviso → Lambda) | Hace falta una función propia | Hace falta una función propia |
| Un solo proceso | Sí (systemd) | Sí | Sí | Sí |
| Costo hasta el 31 ene | ≈ 25 dólares (R-6) | ≈ 18 dólares (7 dólares al mes) | — | ≈ 60 dólares o más (el balanceador solo cuesta unos 16 al mes) |
| Trabajo de Hugo | Preparar un servidor Linux una vez (guía) | Escribir una imagen de contenedor y subirla | — | Lo más largo de configurar |
| Curva de aprendizaje | Media: EC2, CloudFront y grupos de seguridad | Media: contenedores | — | Alta |

**Decisión recomendada**: **A**, una instancia EC2 `t4g.micro` con IP elástica y CloudFront delante.
**Por qué**: es la única opción que cumple a la vez el canal de 20 minutos, el HTTPS sin dominio y el apagado nativo por presupuesto, y además es de las más baratas. CloudFront entra en su capa siempre gratuita (1 TB y 10 millones de peticiones al mes).
**Alternativas**: B, si Hugo prefiere no administrar un servidor, a cambio de escribir una función de apagado y de medir antes su corte del canal. C queda descartada por el límite de 120 s. D cuesta más y tarda más.

## R-2. HTTPS en la dirección que asigna AWS

**Decisión**: el HTTPS lo pone CloudFront, con su dirección `https://<id>.cloudfront.net`. Entre CloudFront y la instancia se usa HTTP al puerto 8000, y el grupo de seguridad solo deja entrar a CloudFront (R-4).
**Por qué**: la aclaración del 2026-11-17 pide la dirección que asigna AWS, sin dominio propio (RF-024). El balanceador de AWS no da HTTPS sin dominio, y un certificado dentro del servidor obligaría a tener un dominio.
**Alternativas**: dominio propio con su certificado (fuera de alcance, §5 de la spec); balanceador con dominio (cuesta más y también necesita dominio).

## R-3. El canal de avisos a través de CloudFront

**Decisión**: tiempo de respuesta del origen de 30 s (el valor por defecto), **sin** tiempo de respuesta completa, sin caché y sin compresión en el comportamiento del servidor. Se comprueba al principio de F4 con un canal real de 20 minutos (CE-004).
**Por qué**: CloudFront espera el primer dato y **cada dato siguiente** hasta ese tiempo, y lo reinicia con cada dato que llega ([anuncio de julio de 2025](https://aws.amazon.com/about-aws/whats-new/2025/07/amazon-cloudfront-origin-response-timeout-controls)). El canal de la 001 manda `retry` en cuanto se abre y una señal de vida cada 15 s (`canal.py:91`), así que nunca pasan 30 s sin datos. El "tiempo de respuesta completa" sí cortaría el canal, por eso no se configura. Ver cobro y crear cobro esperan a pey como máximo 4 y 10 s (DP-13 de la 001), por debajo de 30 s.
**Alternativas**: subir el tiempo a 60 s o más (no hace falta y alarga la espera cuando el servidor está caído).
**Riesgo**: la guía para desarrolladores que describe el comportamiento con respuestas que van llegando por partes no se pudo leer completa. Por eso la prueba de 20 minutos va al principio de F4: si CloudFront corta el canal, se cambia a B (R-1) antes de seguir.

## R-4. La IP real del celular detrás de CloudFront

**Decisión**: en la demo, la IP de los límites sale de la cabecera `CloudFront-Viewer-Address` (`<ip>:<puerto>`), que CloudFront agrega cuando el comportamiento usa la política de origen administrada `AllViewerAndCloudFrontHeaders-2022-06`. El grupo de seguridad de la instancia solo acepta el puerto 8000 desde la lista de prefijos administrada `com.amazonaws.global.cloudfront.origin-facing`, así que esa cabecera no la puede mandar nadie más.
**Por qué**: CloudFront **agrega** la IP del celular al final de `X-Forwarded-For` y deja lo que mandó el celular ([políticas de origen administradas](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-managed-origin-request-policies.html)). Con `PROXIES_CONFIABLES=*`, uvicorn tomaría la primera dirección de la lista, que la escribe el atacante, y cualquiera se saltaría el límite por IP (RF-028). Listar las IP de CloudFront en `PROXIES_CONFIABLES` es una lista larga que cambia. `CloudFront-Viewer-Address` trae un solo valor puesto por CloudFront ([re:Post](https://repost.aws/articles/AR-VvhzdKVRgOIYl4SJMTcHg/how-to-identify-the-real-client-ip-on-alb-when-using-cloudfront-as-a-front-end)).
**Alternativas**: tomar la última dirección de `X-Forwarded-For` (sirve, pero depende de que nadie más agregue saltos); `ProxyHeadersMiddleware` con todas las IP de CloudFront (frágil).
**Cómo**: variable `CABECERA_IP_REAL`. Vacía en local y en las pruebas: se sigue usando `ProxyHeadersMiddleware` con `PROXIES_CONFIABLES`, como en la 001 (DP-7). En la demo vale `CloudFront-Viewer-Address`. Si falta la cabecera, se usa la IP de la conexión.

## R-5. Apagado por el presupuesto y quién reenciende

**Decisión**: un presupuesto mensual de costo de 200 dólares que **no** descuenta créditos ("Unblended costs", sin la opción de restar créditos), con avisos por correo al 50, 80 y 100 % del gasto real y al 100 % del pronóstico, y una acción al 90 % del gasto real que **detiene la instancia EC2** de la demo, de ejecución automática. La acción usa un rol de IAM propio con permiso solo para detener esa instancia.
**Por qué**: RF-031 a RF-034 y QA-2. Es la acción nativa de AWS Budgets para EC2. Solo Hugo tiene acceso a la cuenta (supuesto de §7), y el rol de la publicación automática no tiene permiso de encender instancias (DP-29), así que solo Hugo reenciende (RF-040, RF-045).
**Limitaciones aceptadas** (ya en la spec): el gasto se actualiza hasta tres veces al día y el pronóstico necesita unas 5 semanas de datos.

## R-6. Costo estimado hasta el 31 de enero de 2027 (CE-009)

Precios de `us-east-1`; en otras regiones de Estados Unidos son parecidos. Periodo: del 21 de noviembre al 31 de enero, 72 días.

| Pieza | Cálculo | Dólares |
|---|---|---|
| EC2 `t4g.micro` (2 vCPU, 1 GB) | 0.0084 × 24 × 72 | 14.52 |
| IP elástica (IPv4 pública) | 0.005 × 24 × 72 | 8.64 |
| Disco gp3 de 8 GB | 0.08 × 8 × 2.37 meses | 1.52 |
| CloudFront | Capa siempre gratuita (1 TB y 10 millones de peticiones al mes) | 0 |
| Datos de EC2 a CloudFront | Sin costo | 0 |
| Session Manager (SSM), AWS Budgets (dos presupuestos con acciones) | Sin costo | 0 |
| **Total** | | **≈ 24.7** (12 % del presupuesto) |

Con `t4g.small` (2 GB), el total sube a unos 39 dólares (20 %). Los dos quedan muy por debajo de 150 (RF-035). El cálculo se repite en F4 con los precios de la región elegida (DP-24).

## R-7. Tipo de cuenta de AWS (por confirmar)

**Hallazgo**: desde julio de 2025, las cuentas nuevas de AWS reciben hasta 200 dólares de crédito y eligen entre el **plan gratuito**, que dura hasta 6 meses o hasta acabar el crédito, nunca cobra y bloquea algunos servicios, y el **plan de pago** ([anuncio](https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan); [FAQ](https://aws.amazon.com/free/faqs/)). Si la cuenta de Hugo está en el plan gratuito, al acabar el crédito o los 6 meses AWS deja de servir y, sin cambiar de plan en 90 días, borra la cuenta.
**Decisión**: Hugo confirma en F4, antes de crear nada, el plan de la cuenta y su fecha de alta. Con el plan gratuito, los 6 meses deben pasar del 31 de enero, y se comprueba que EC2 `t4g.micro` y CloudFront estén permitidos. El presupuesto se configura igual (RF-031).
**Por qué**: cambia qué pasa al acabar el crédito, pero no el diseño.

## R-8. Librería para conectarse a PostgreSQL (comparativa, DP-2)

| | A. psycopg 3 (`psycopg[binary]` + `psycopg-pool`) (recomendada) | B. asyncpg | C. SQLAlchemy 2 asíncrono + un controlador |
|---|---|---|---|
| Asíncrono | Sí, y también síncrono (sirve para el comando de migraciones) | Sí, solo asíncrono | Sí |
| SQL | SQL escrito a mano con parámetros `%s` | SQL a mano con `$1` | ORM o SQL; una capa más |
| Con el *pooler* de Supabase | Funciona en modo sesión y en modo transacción (`prepare_threshold=None`) | En modo transacción hay que apagar las sentencias preparadas | Según el controlador |
| Dependencias nuevas | 2 | 1 | 2 o más |
| Curva de aprendizaje | Baja: el mismo SQL del PR #97 | Baja | Media o alta: el ORM no hace falta |
| Rendimiento | De sobra para decenas de cobros al día | El más rápido | El más lento |

**Decisión recomendada**: **A**. Una sola librería sirve para el servidor y para el comando de migraciones (R-9), con el mismo SQL del PR #97, sin ORM.
**Alternativas**: B, si se prefiere una sola dependencia (el comando de migraciones también puede ser asíncrono). C añade un ORM que no hace falta (principio IX).

## R-9. Herramienta para los cambios de estructura (comparativa, DP-3)

| | A. Comando propio con psycopg (recomendada) | B. CLI de Supabase (`supabase db push`) | C. dbmate |
|---|---|---|---|
| Qué es | `python -m app.migraciones` (unas 100 líneas): aplica en orden los `.sql` de `supabase/migraciones/` y anota cada uno en una tabla | Herramienta oficial; migraciones en `supabase/migrations/` y datos en `seed.sql` | Un ejecutable de Go con SQL plano |
| Herramienta nueva | Ninguna (usa R-8) | Un ejecutable (npm o Homebrew) en cada computadora y en el CI | Un ejecutable |
| Idempotente (RF-019) | Sí: salta lo ya anotado | Sí | Sí |
| Base de la demo ya creada a mano (historia 6, escenario 3) | Opción `--ya-aplicada 0001` después de revisar | `supabase migration repair --status applied` | Insertar la fila a mano |
| Datos de prueba solo en local (RF-054) | Marca de entorno en la base (DP-18) | `seed.sql` solo lo carga su entorno local con Docker; con un segundo proyecto en la nube hay que cargarlo a mano | No tiene datos de prueba |
| Lo que lee el servidor para RF-047 | Su propia tabla | La tabla interna de la CLI | Su tabla `schema_migrations` |
| Curva de aprendizaje | Ninguna, pero es código que se prueba | Media | Baja |

**Decisión recomendada**: **A**. No agrega herramientas, corre igual en local, en el CI y desde la computadora de Hugo contra la demo (RF-017), y el servidor lee la misma tabla para RF-047. Se prueba en el CI contra un PostgreSQL desechable (R-12, CE-007).
**Alternativas**: B, si el equipo quiere la herramienta oficial, a cambio de instalarla en el CI y en cada computadora. C, si se prefiere una herramienta probada sin datos de prueba.

## R-10. Cómo guardar sin cambiar el comportamiento de la 001

**Decisión**: el servidor sigue trabajando con los objetos `Cobro` en memoria (el canal y la consulta de respaldo no cambian), pero la memoria pasa a ser una **caché de escritura directa** sobre un *almacén*:

1. Toda escritura va **primero** a la base de datos; solo si se guardó se cambia la memoria y se emite por el canal (RF-002).
2. Un cobro que no está en memoria (después de un reinicio) se carga de la base de datos al pedirlo por su id o por su `codi_qr_id` (RF-005).
3. Registrar un pago va dentro de un candado por cobro (`asyncio.Lock`): el número del pago se calcula dentro del candado, y el `insert … on conflict (transaccion_id) do nothing returning` dice si el pago es nuevo (RF-007, RF-008).

**Por qué**: hay un solo proceso (supuesto de la spec), así que la memoria no puede quedar desactualizada respecto a la base de datos. El candado evita que el aviso y la consulta de respaldo calculen el mismo número a la vez; la restricción `unique (cobro_id, numero)` del PR #97 queda como red.
**Alternativas**: leer siempre de la base de datos (cambia el canal y la consulta, que hoy guardan el objeto en memoria, y multiplica las consultas: una cada 3 a 5 s por cada pantalla abierta); cargar todos los cobros al arrancar (innecesario: se cargan al pedirlos).

## R-11. Conexión con Supabase desde AWS

**Decisión**: `DATABASE_URL` apunta al *pooler* de Supabase en **modo sesión** (puerto 5432, IPv4), con un *pool* de 1 a 3 conexiones y 5 s de espera para conectar.
**Por qué**: la conexión directa de Supabase es solo IPv6, y la VPC por defecto de EC2 no tiene IPv6 (QA de la spec, bloque 5). El modo sesión admite todo PostgreSQL. Con un solo proceso, 3 conexiones sobran.
**Región**: la instancia EC2 va en la misma región que el proyecto de Supabase de la demo (DP-24), para que cada consulta tarde milisegundos.

## R-12. Probar el almacén sin la base de datos real

**Decisión**: dos niveles:

- **Las pruebas de la API** (todas las de hoy y las nuevas de fallas) usan el almacén en memoria y un almacén que falla a propósito. No necesitan PostgreSQL.
- **Las pruebas del almacén de PostgreSQL y del comando de migraciones** corren contra un **PostgreSQL 17 desechable**: en el CI, un contenedor de servicio de GitHub Actions; en una computadora, solo si se define `PRUEBAS_DATABASE_URL` (si no, se saltan con el motivo escrito). Antes de migrar, la prueba crea los roles `anon` y `authenticated`, que el PR #97 usa en su `revoke` y que solo existen en Supabase.

**Por qué**: CE-011 y RF-038 prohíben la base de datos **real**, no un PostgreSQL vacío que se crea y se destruye en cada corrida. Sin esa prueba, el SQL solo se probaría en la demo.
**Alternativas**: probar el SQL solo a mano en el proyecto local de Supabase (frágil); simular psycopg (no prueba el SQL).

## R-13. CI en GitHub Actions

**Decisión**: un flujo `.github/workflows/ci.yml` que corre con `pull_request` hacia `main` (y en `push` a `main`), con `permissions: contents: read` y tres trabajos en `ubuntu-latest`:

1. **Servidor**: `uv sync --locked`, `ruff check`, `ruff format --check` y `pytest -q`.
2. **Web**: lo mismo para `../web`, más `playwright install --with-deps chromium webkit`. Solo corre si existe `web/tests/` (todavía no está en `main` hasta que se una el #72).
3. **Base de datos** (desde F2): PostgreSQL 17 como servicio; corre el comando de migraciones dos veces (CE-007) y las pruebas del almacén.

**Por qué**: RF-036 a RF-038. `pull_request` (no `pull_request_target`) no expone secretos a los forks, y el flujo no usa ninguno. Juan hace obligatorios los tres trabajos en la protección de `main` (RF-037, dependencia de §7).
**Riesgo**: las 6 pruebas de WebKit que fallan fuera de Mac (revisión del PR #72) pueden fallar también en Linux. Se resuelven en el PR #72; si no, el trabajo de la web sale en rojo.

## R-14. Cómo se crea la infraestructura (comparativa, DP-4)

| | A. Guía paso a paso en la consola de AWS (recomendada) | B. Plantilla de CloudFormation |
|---|---|---|
| Herramienta nueva | Ninguna | Ninguna fuera de AWS, pero hay que aprender su formato |
| Tiempo para el corte 1 | 1 a 2 horas de Hugo con la guía | Escribir y depurar la plantilla: medio día o más |
| Repetible | Con la guía; a mano | Sí, con un comando |
| Revisable en un PR | La guía, sí; lo creado, no | Sí |

**Decisión recomendada**: **A** para esta spec. Es una sola instancia, una distribución y un presupuesto, y la demo vive hasta el 31 de enero. La guía `docs/operacion-demo.md` deja cada valor escrito (RF-041).
**Alternativas**: B, si el equipo quiere volver a crear la demo desde cero con un comando; se puede hacer después sin cambiar el código.

## R-15. Publicar una versión nueva

**Decisión**: un solo script en la instancia, `infra/servidor/publicar.sh <commit>`, que usan Hugo a mano (corte 1) y el flujo automático (corte 2):

1. Descarga ese commit en una carpeta nueva `releases/<commit>` (el repositorio es público: no hacen falta credenciales).
2. Corre `uv sync --locked --no-dev`. Si falla, se detiene, y sigue la versión anterior (RF-044).
3. Cambia el enlace `actual` a la carpeta nueva y reinicia el servicio de systemd: es el corte de RF-055.
4. Espera hasta 45 s a que `GET /salud` responda con la base de datos en `responde`. Si no responde, devuelve el enlace a la versión anterior, reinicia y sale con error (RF-044).
5. Deja las 3 versiones más recientes y borra las demás.

**A mano** (corte 1): Hugo lo corre con `aws ssm send-command` desde su computadora, o en una sesión de Session Manager. **Automático** (corte 2): el flujo `publicar.yml` hace lo mismo con OIDC (R-16).
**Por qué**: un solo camino para las dos formas; la carpeta por versión permite volver atrás sin descargar nada.
**Alternativas**: `git pull` sobre la misma carpeta (sin vuelta atrás limpia); imágenes de contenedor (exigen un registro y Docker en la instancia).

## R-16. Publicación automática sin credenciales guardadas (corte 2)

**Decisión**: GitHub Actions obtiene credenciales temporales con **OIDC** (`aws-actions/configure-aws-credentials` con `role-to-assume`). El rol solo confía en `repo:Altairtm/Hackton-2026:ref:refs/heads/main` y solo puede:

- `ec2:DescribeInstances`, para comprobar que la instancia está encendida;
- `ssm:SendCommand` sobre esa instancia y el documento `AWS-RunShellScript`;
- `ssm:GetCommandInvocation`.

No puede encender instancias (RF-045). El ARN del rol va como **variable** del repositorio (no es una credencial).
**Por qué**: RF-042 a RF-045 y el principio III: ninguna llave de AWS vive en GitHub. Si la instancia está detenida (presupuesto o Hugo), el flujo falla con el mensaje "La demo está apagada; solo Hugo la enciende" y no la enciende.
**Alternativas**: llaves de acceso de IAM como secretos de GitHub (prohibido por RF-043).

## R-17. Dónde viven los secretos del servidor

**Decisión**: en la instancia, un archivo `/etc/pago-facil/entorno`, de `root` y con permisos `0640` (grupo del servicio), que systemd carga con `EnvironmentFile`. Tiene `PEY_API_KEY`, `PEY_WEBHOOK_SECRET`, `DATABASE_URL`, `WEB_ORIGIN`, `CABECERA_IP_REAL` y `PROXIES_CONFIABLES`. Hugo lo escribe en una sesión de Session Manager; nunca pasa por el repositorio ni por GitHub.
**Por qué**: son las "variables del hosting" del principio III. pydantic-settings ya lee variables de entorno (`config.py`).
**Alternativas**: AWS Systems Manager Parameter Store (más piezas para el mismo resultado con una sola instancia).

## R-18. La web, desde el mismo servidor

**Decisión**: el servidor entrega la carpeta `web/` en `/` cuando `CARPETA_WEB` está definida (en la demo y en local; vacía en las pruebas del servidor). La CSP de `web/index.html` queda en `connect-src 'self'`.
**Por qué**: la web y el servidor quedan en el mismo origen. `web/config.js` ya vale `""` para ese caso (spec 002, RF-064; `web/README.md:33`). CORS no hace falta para la propia web, y `WEB_ORIGIN` solo deja pasar su dominio (RF-027). La web solo puede conectarse a su propio servidor (RF-029). Una sola publicación sube servidor y web (RF-042).
**Alternativas**: S3 con su propio comportamiento en CloudFront (otra pieza y otra publicación); dejar `connect-src https:` (incumple RF-029).
**Consecuencia en local**: la web se abre en `http://localhost:8000` (el servidor la entrega) en lugar del puerto 5173. La forma con `config.js` en `http://localhost:8000` deja de pasar la CSP; se quita del `web/README.md`.
