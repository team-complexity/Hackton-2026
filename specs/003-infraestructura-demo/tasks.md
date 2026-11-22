# Tasks: Infraestructura de la demo: guardar los cobros, abrir la demo local por un túnel y probar cada cambio

- **Spec**: [spec.md](spec.md), estado: Aprobada el 2026-11-20 (QA-12 a QA-20)
- **Plan**: [plan.md](plan.md), estado: Aprobado el 2026-11-21 (DP-38 Tailscale Funnel, QP-10 a QP-14, C-8 cumplido)
- **Fecha**: 2026-11-21
- **Estado**: `Aprobado` el 2026-11-21 por Hugo, con `/speckit-analyze` y la QA de tareas (QT-1 a QT-9) decididos y aplicados (ver «Revisión QA de tasks»). Estado anterior: `En QA`. Lo redactó Claude el 2026-11-21 con `/speckit-tasks`. Aprobar no autoriza empezar F1: se espera a que Hugo lo pida (F0 es suya y puede empezar cuando quiera). **F0 terminada (Hugo, con Claude, 2026-11-21): Tailscale Funnel cumple, sin plan B (TK-5).** **F1 terminada (2026-11-21): CI en `main` con `servidor` y `web` obligatorios, también para administradores (PR #102; prueba del error en el PR #103, TK-6).**
- **Entrada**: los documentos de `specs/003-infraestructura-demo/`: plan.md, spec.md, research.md, data-model.md, contracts/ y quickstart.md

> **Notas para los comandos de spec-kit.**
> - Cada tarea sigue el formato obligatorio `- [ ] T001 [P] [US1] Descripción con ruta del archivo`.
> - `/speckit-implement` la marca como `[X]` al terminarla.
> - Los detalles van como sub-puntos sangrados debajo de la tarea.
> - `[P]` = se puede hacer en paralelo (otros archivos, sin dependencias pendientes).
> - `[US1]` … `[US6]` = historia de la spec a la que pertenece (Historia 1 = US1 … Historia 6 = US6).
> - Las casillas van siempre en listas, nunca en tablas (en las tablas no se ven).
> - Todas las rutas son relativas a la raíz del repositorio. Los comandos se corren desde la raíz, salvo que la tarea diga otra cosa.
> - Los textos entre comillas son los que exigen la spec o los contratos.
> - Las fases son las del plan (§8), no las de la plantilla: F0 a F3 son el corte 1 (≤ dom 22 nov) y F4 a FN el corte 2 (≤ mié 25 nov).

---

## Reglas de ejecución

1. **Las fases van en orden.** Una fase la hace una sola persona o agente. Al empezar lo anota en **Estado** ("F2 en curso (Grok)") y al cerrarla también ("F2 terminada (Grok, AAAA-MM-DD)").
2. **Pruebas primero.** En cada fase se escriben las pruebas, se ven fallar y después se implementa (principio V).
3. **Solo se hace la tarea pedida.** Nada de funciones sorpresa, retoques cosméticos ni refactorizaciones fuera de la tarea.
4. **Si el código obliga a cambiar algo**, se anota en el *Registro de implementación* del plan (§14) como TK-n. Si toca una spec aprobada, se presenta como un cambio `C-n` (el siguiente libre es **C-10**), que Hugo aprueba por separado.
5. **Una fase cierra con tres cosas:**
   - todo en verde:
     - backend: `uv run --directory backend pytest -q`, `uv run --directory backend ruff check .` y `uv run --directory backend ruff format --check .`;
     - web: `uv run --directory backend pytest ../web -q`;
     - estilo del Python de las pruebas de la web: `uv run --directory backend ruff check --config pyproject.toml ../web` y `uv run --directory backend ruff format --config pyproject.toml --check ../web`;
   - su sección en `specs/003-infraestructura-demo/verification-guide.md`;
   - el mensaje de commit sugerido, con formato `tipo(003): descripción en español`.
   - El commit, el push, las ramas y el pull request los hace Hugo. Cada PR usa `.github/pull_request_template.md` y lo une su autor con el CI en verde (constitución 3.0.0).
6. **Ninguna prueba automática llama al pey real, a la base de datos real ni espera tiempo real.** pey simulado (`PeySimulado` sobre `httpx.MockTransport`), `RelojFalso`, almacén en memoria o almacén que falla a propósito. Las pruebas del SQL corren contra un PostgreSQL 17 desechable (`PRUEBAS_DATABASE_URL`, R-10): si no está definida, se saltan con el motivo escrito; en el CI siempre corren.
7. **Dinero real**: solo cobros de $0.01, solo con cuentas propias y con la autorización de Hugo en ese momento (F0 crea un QR real sin pagarlo; F3 y F6 pagan).
8. **Secretos**: nadie lee, imprime, cita ni pega `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` ni `DATABASE_URL`, ni el contenido de `backend/.env` o `backend/.env.demo`. Para saber si están puestos se usa `GET /salud`. Para comparar dos archivos sin ver los valores se usa la comparación de T048.
9. **Procesos**: el servidor y `caffeinate` se paran por su PID exacto, nunca con `pkill` ni `killall`.

## Reparto

| Fase | Quién la hace | Quién la revisa |
|---|---|---|
| F0 Prueba del túnel | Hugo, con Claude | Hugo decide si se sigue o se pasa al plan B (R-1) |
| F1 CI | Grok (código); Hugo (rama, protección de `main` y PR de prueba) | Claude |
| F2 Demo por el túnel | Grok (código, C-7 y borrador de la guía); Hugo (`backend/.env.demo`, túnel, aviso de pey y comprobaciones) | Claude; Hugo con la guía de verificación |
| F3 Pago real | Hugo, con los dos celulares; Leonel desde fuera (N-17); Grok (README) | Hugo |
| F4 Migraciones | Grok (código); Juan (proyecto de Supabase de desarrollo); Hugo (aplica en desarrollo) | Claude |
| F5 Guardar | Grok (código y C-6); Hugo (comprobación en desarrollo) | Claude |
| F6 Conciliación y demo con base de datos | Grok (código y guía); Hugo (base de la demo y pagos reales) | Claude; Hugo con la guía de verificación |
| FN Cierre | Claude y Hugo | Hugo; Juan y Leonel revisan después de unir |

## Dependencias externas

| Dependencia | Qué bloquea | Estado |
|---|---|---|
| PR #72 y PR #96 unidos a `main` (C-8) y rama de la 003 rebasada sobre `main` (QP-10) | F1 y F2 | Listo el 2026-11-21 (`f01f732`; rama en `2d73373` y después `17bdbf0`) |
| C-6 y C-7 aprobados (QP-11) | T021 (C-7, F2) y T064 (C-6, F5) | Aprobados el 2026-11-20 · sin aplicar |
| Cuenta de Tailscale de Hugo con HTTPS, MagicDNS y el permiso `funnel` (DP-38) | F0 y todo lo demás de la demo | Pendiente (T001) |
| Llave de pey de la demo y su secreto en `backend/.env.demo` (Hugo) | F0, F2, F3 y F6 | Pendiente (T002) |
| Aviso de pey de la llave de la demo con la dirección del túnel (Hugo, en el portal) | El pago real de F3 (RF-025) | Pendiente (T025) |
| Protección de `main` con los trabajos del CI como obligatorios (Hugo, administrador) | RF-037 y CE-006 (T013, T014, T044) | Aprobación obligatoria quitada el 2026-11-21; faltan los trabajos y `enforce_admins` (QT-3) |
| CoDi activo en el banco de Hugo, un Android y un iPhone, y otro celular para pagar | F3 y F6 | CoDi activo desde el 15 nov; celulares por confirmar |
| Leonel con su red y sus celulares (N-17) | T031 | Por confirmar |
| Proyecto de Supabase de desarrollo y su URL del *pooler* en modo sesión (Juan, RF-049) | T046 y la comprobación de F5 (T066) | Pendiente, antes del 23 nov |
| Segunda llave de producción de pey para desarrollo (Hugo, RF-053) | T048 y la comprobación de F5 (T066) | Pendiente; Hugo la liga en el portal a su cuenta CoDi |
| PostgreSQL 17 desechable en la computadora (opcional) | Correr en local las pruebas del SQL; sin él se saltan y corren en el CI | Opcional |
| Proyecto de Supabase de la demo, con el PR #97 corrido a mano y sus datos de prueba (H-12) | T071 y T072 (F6) | Existe; falta limpiarlo y marcarlo |

## Formato de cada tarea

```text
- [ ] T000 [P] [US1] Descripción con la ruta exacta del archivo
  - **RF**: RF-001, RF-002
  - **Dep.**: T000 (o "ninguna")
  - **Hecho cuando**: criterio verificable (prueba que pasa, comando y salida esperada)
```

---

## Fase 0 (F0): Prueba del túnel, sin la web · 21 nov · corte 1

**Propósito**: comprobar con `curl`, antes de escribir código, que Tailscale Funnel cumple lo que el plan da por hecho: HTTPS válido, canal de 25 minutos sin cortes ni eventos retenidos, IP real y misma dirección tras reiniciar (QP-12, research R-1 y R-2). Si falla el canal o la dirección, se para y Hugo decide el plan B.

**Prueba independiente**: el quickstart §3.0, pasos 1 a 7.

- [X] T001 [US2] Preparar Tailscale en la Mac de Hugo (quickstart §0)
  - **Quién**: Hugo.
  - Crear la cuenta, instalar la app de Tailscale y entrar. En la consola del tailnet: activar HTTPS y MagicDNS, y dar el permiso `funnel` en la política del tailnet ([funnel](https://tailscale.com/kb/1223/funnel)).
  - La sesión de Tailscale vive en su app, fuera del repositorio (RF-059). No se copia ninguna llave de Tailscale a ningún archivo del repositorio.
  - **RF**: RF-024, RF-059
  - **Dep.**: ninguna
  - **Hecho cuando**: `tailscale status` muestra la Mac conectada y `tailscale funnel status` responde sin error de permisos.
- [X] T002 [US2] Crear `backend/.env.demo` en la Mac de Hugo (QP-14, DP-36)
  - **Quién**: Hugo. Nadie más lo abre ni lo lee.
  - Variables: `PEY_API_KEY` y `PEY_WEBHOOK_SECRET` de la llave de la demo, `WEB_ORIGIN=https://<nombre>.<tailnet>.ts.net`, `LIMITE_COBROS_POR_MINUTO=30`, `CANALES_POR_IP=30` y `DATABASE_URL=` **vacía a propósito** hasta T071. `CARPETA_WEB` llega en F2 (T024).
  - Por qué la línea vacía (DP-44): `Configuracion` también lee `backend/.env`, y lo que falta en `backend/.env.demo` se toma de ahí. Sin esa línea, desde T045 la demo usaría la base de desarrollo; vacía, el servidor guarda en memoria y la salud dice `"sin configurar"` (una variable vacía manda sobre `backend/.env`). Lo mismo vale para cualquier variable de la demo.
  - **RF**: RF-020, RF-027, RF-049, RF-053
  - **Dep.**: T001
  - **Hecho cuando**: `git check-ignore -v backend/.env.demo` dice que lo ignora la regla `.env.*`; `grep -c '^DATABASE_URL=$' backend/.env.demo` dice `1` (cuenta la línea sin mostrar valores); y `/salud` del servidor arrancado con ese archivo (T003) dice `"llave_pey": true` y `"secreto_aviso_pey": true`.
- [X] T003 [US2] Arrancar el servidor actual solo en `127.0.0.1` y abrir Funnel hacia el puerto 8000 (quickstart §3.0, paso 1)
  - **Quién**: Hugo.
  - Servidor: `cd backend && uv run uvicorn app.main:app --env-file .env.demo --workers 1 --port 8000`, **sin `--host`** (RF-056, DP-42). Túnel: `tailscale funnel --bg 8000`. Anotar la dirección `https://<nombre>.<tailnet>.ts.net`.
  - Desde **otra red** (celular con datos móviles como punto de acceso, o Leonel): `curl https://<dirección>/salud`.
  - **RF**: RF-024, RF-056
  - **Dep.**: T002
  - **Hecho cuando**: la respuesta trae `"estado": "ok"` y `curl` no se queja del certificado (HTTPS válido).
- [X] T004 [US2] Canal de 25 minutos con `curl` desde otra red (quickstart §3.0, pasos 3 y 4)
  - **Quién**: Hugo, con su autorización para crear un QR real de $0.01 **sin pagarlo**.
  - `curl -X POST https://<dirección>/api/cobros -H 'Content-Type: application/json' -d '{"monto": 0.01, "concepto": "Prueba túnel"}'` (cuerpo de [crear-cobro](../001-backend-mvp/contracts/crear-cobro.md)). Anotar el `id`.
  - Desde la otra red: `curl -N https://<dirección>/api/cobros/<id>/eventos` durante 25 minutos, anotando la hora a la que aparece cada línea (por ejemplo, con `| while IFS= read -r l; do echo "$(date +%T) $l"; done`).
  - **RF**: RF-026, RF-057
  - **Dep.**: T003
  - **Hecho cuando**: hay una señal de vida cada ~15 s en el momento en que sale (no todas juntas al final), `vencido` cerca del minuto 10, y el servidor cierra el canal con `fin` cerca del minuto 20, sin cortes antes. Si falla, se para la fase (T007).
- [X] T005 [US2] IP real del celular por `X-Forwarded-For` (quickstart §3.0, paso 5; research R-2)
  - **Quién**: Hugo.
  - Pedir `/salud` y crear un cobro desde dos redes distintas (wifi de otra casa o datos de dos compañías), y mirar en el registro del servidor la IP de cada petición.
  - **RF**: RF-028
  - **Dep.**: T003
  - **Hecho cuando**: el registro muestra dos IP distintas y ninguna es `127.0.0.1`. Si no, se aplica DP-40 (límites de 60 en `backend/.env.demo`) y se anota en T007.
- [X] T006 [US2] Misma dirección después de reiniciar (quickstart §3.0, paso 6)
  - **Quién**: Hugo.
  - Reiniciar la computadora, volver a arrancar el servidor y Funnel como en T003, y pedir `/salud` desde la otra red.
  - **RF**: RF-030
  - **Dep.**: T004, T005
  - **Hecho cuando**: la dirección es exactamente la anotada en T003. Si cambia, se para la fase (T007).
- [X] T007 Cierre de F0: resultado como TK y decisión de seguir
  - Anotar en el plan §14 un TK con: la dirección (sin datos de la cuenta), las horas de los eventos de T004, las IP de T005 (solo si son distintas, no los valores) y el resultado de T006.
  - Crear `specs/003-infraestructura-demo/verification-guide.md` con su sección F0 (pasos y resultado).
  - Si fallaron T004 o T006: no se sigue con F2; Hugo decide el plan B (Cloudflare Tunnel con dominio, research R-1) y se replanea con un TK.
  - Para el servidor por su PID exacto y `tailscale funnel reset`.
  - Commit sugerido: `docs(003): prueba del túnel con Tailscale Funnel (F0)`.
  - **RF**: RF-024, RF-026, RF-028, RF-030, RF-057
  - **Dep.**: T004, T005, T006
  - **Hecho cuando**: el TK está en el plan, la sección F0 en la guía y Hugo dijo "seguimos" (o eligió el plan B).

**Punto de control**: el túnel cumple los criterios del canal, la IP y la dirección fija, o hay plan B decidido.

---

## Fase 1 (F1): CI en cada pull request · 21 nov · corte 1 · PR propio desde `main`

**Objetivo**: cada pull request hacia `main` muestra si las pruebas y el lint del servidor y de la web pasan, sin secretos, y no se puede unir si fallan (historia 5).

**Prueba independiente**: un PR con un `assert False` sale en rojo y no se puede unir; al quitarlo, en verde (quickstart §2, CE-006).

> F1 va en su propia rama, `feature/35-ci`, que Hugo crea desde `main` (DP-28). Las casillas de este archivo se marcan en `feature/90-infraestructura-demo`.

### Pruebas de F1 (primero, deben fallar antes de implementar)

- [X] T008 [US5] Prueba del contrato del CI en `backend/tests/test_ci.py` (archivo nuevo)
  - Lee `.github/workflows/ci.yml` como texto (ruta: `Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"`), sin dependencias nuevas.
  - `test_el_ci_corre_en_cada_pull_request_hacia_main`: el archivo existe y tiene `pull_request:` y `push:` con la rama `main`.
  - `test_el_ci_solo_lee_el_repositorio_y_no_usa_secretos`: tiene `contents: read` bajo `permissions:`, y no contiene `secrets.` ni `pull_request_target`.
  - `test_el_ci_tiene_los_trabajos_servidor_y_web`: tiene los trabajos `servidor:` y `web:`, y los comandos `uv sync --locked`, `ruff check`, `ruff format --check`, `pytest -q`, `playwright install --with-deps chromium webkit` y `pytest ../web -q` (contrato [ci](contracts/ci.md) §4).
  - **RF**: RF-036, RF-038
  - **Dep.**: ninguna (rama `feature/35-ci` creada por Hugo)
  - **Hecho cuando**: las tres pruebas existen y fallan porque no existe `ci.yml`.

### Implementación de F1

- [X] T009 [US5] Escribir `.github/workflows/ci.yml` según el [contrato](contracts/ci.md)
  - `on`: `pull_request` hacia `main` (`opened`, `synchronize`, `reopened`) y `push` a `main`. `permissions: contents: read`. Sin secretos ni variables de pey o de la base de datos (RF-038, DP-27).
  - Trabajo `servidor` en `ubuntu-latest`: `actions/checkout` y `astral-sh/setup-uv` con caché y Python 3.12; en `backend/`: `uv sync --locked`, `uv run ruff check .`, `uv run ruff format --check .` y `uv run pytest -q`.
  - Trabajo `web`: lo mismo hasta `uv sync --locked`, y después `uv run playwright install --with-deps chromium webkit`, `uv run ruff check --config pyproject.toml ../web`, `uv run ruff format --config pyproject.toml --check ../web` y `uv run pytest ../web -q`.
  - Cada acción con su versión mayor fijada (`@vN`), la más reciente publicada hace al menos dos semanas; anotar cuáles en la descripción del PR.
  - **RF**: RF-036, RF-037, RF-038
  - **Dep.**: T008
  - **Hecho cuando**: T008 pasa y todo lo demás sigue en verde en local.
- [X] T010 [US5] Abrir el PR de `feature/35-ci` y comprobar los dos trabajos en GitHub
  - **Quién**: Hugo (commit, push y PR); Grok arregla lo que falle.
  - Commit sugerido: `feat(003): CI con los trabajos servidor y web (F1)`. PR con la plantilla y `Closes #35`.
  - Si una prueba de WebKit falla solo en Linux: se arregla o se marca con `skip` y su motivo escrito, y se anota como TK en el plan §14 (research R-11, riesgo del plan §11).
  - **RF**: RF-036
  - **Dep.**: T009
  - **Hecho cuando**: el PR muestra `servidor` y `web` en verde.
- [X] T011 [US5] Revisar que el flujo no puede ver secretos ni escribir en el repositorio (quickstart §2, paso 4)
  - **Quién**: Claude, al revisar el PR.
  - `git grep -n "secrets\.\|pull_request_target\|permissions" .github/workflows/ci.yml`: solo `permissions` con `contents: read`.
  - **RF**: RF-038
  - **Dep.**: T010
  - **Hecho cuando**: la revisión queda anotada en la sección F1 de la guía de verificación.
- [X] T012 [US5] Unir el PR de `feature/35-ci` a `main` con el CI en verde (QT-1)
  - **Quién**: Hugo. Se une **antes** de marcar los trabajos como obligatorios: si se marcan antes, los PR abiertos del equipo sin `ci.yml` quedan esperando unos trabajos que nunca corren.
  - **RF**: RF-036, RF-038
  - **Dep.**: T011
  - **Hecho cuando**: el PR está unido a `main` y #35 se cerró.
- [X] T013 [US5] Marcar `servidor` y `web` como obligatorios, activar `enforce_admins` y avisar al equipo (QT-1, QT-3)
  - **Quién**: Hugo (administrador).
  - En *Settings → Branches → main*, *Require status checks to pass*, con `servidor` y `web`. La aprobación obligatoria ya se quitó el 2026-11-21 (constitución 3.0.0).
  - `gh api -X POST repos/team-complexity/Hackton-2026/branches/main/protection/enforce_admins`: la regla del CI también vale para los administradores (CE-006). Desde la 3.0.0 ya no hace falta `--admin` para unir.
  - Avisar a Juan, Miguel y Leonel que traigan `main` a sus ramas abiertas, para que su PR tenga `ci.yml`.
  - **RF**: RF-037
  - **Dep.**: T012 (GitHub solo ofrece los trabajos que ya corrieron)
  - **Hecho cuando**: `gh api repos/team-complexity/Hackton-2026/branches/main/protection/required_status_checks -q .contexts` muestra `servidor` y `web`, y `gh api repos/team-complexity/Hackton-2026/branches/main/protection/enforce_admins -q .enabled` dice `true`.
- [X] T014 [US5] Prueba del error a propósito y cierre de F1 (quickstart §2, CE-006)
  - **Quién**: Hugo.
  - Desde una rama nueva de `main`, un `assert False` en una prueba del backend y su PR hacia `main`. Después de verlo, se cierra **sin unir** y se borra la rama.
  - Sección F1 de la guía de verificación con los resultados de T010 a T014.
  - **RF**: RF-036, RF-037, RF-038
  - **Dep.**: T013
  - **Hecho cuando**: con el `assert False`, `servidor` sale en rojo y GitHub dice que no se puede unir, también para Hugo; sin él, los dos trabajos en verde; y la sección F1 de la guía está escrita.

**Punto de control**: `main` solo acepta PR con `servidor` y `web` en verde.

---

## Fase 2 (F2): Demo por el túnel, con la web desde el servidor · 21–22 nov · corte 1

**Objetivo**: el servidor entrega también la web en el mismo origen, la web solo se conecta a su servidor, y Hugo enciende y apaga la demo con una guía (historias 2 y 4). Su PR cierra #65.

**Prueba independiente**: el quickstart §3 (abrir la demo con datos móviles, canal de 25 minutos con la web, IP real, misma dirección, CORS y red local).

> Antes de empezar: F1 unida, F0 en verde y la rama de la 003 al día con `main` (`git rebase origin/main`, lo hace Hugo).

### Pruebas de F2 (primero, deben fallar antes de implementar)

- [ ] T015 [P] [US2] Pruebas de la web servida por el servidor en `backend/tests/test_web_desde_el_servidor.py` (archivo nuevo)
  - Cada prueba arma su app con `crear_app(Configuracion(_env_file=None, pey_api_key=…, pey_webhook_secret=…, carpeta_web=…), cliente_pey, reloj)` y una carpeta temporal (`tmp_path`) con `index.html` (`<h1>PAGO FÁCIL</h1>`) y `config.js`.
  - `test_con_carpeta_web_el_servidor_entrega_la_web`: `GET /` responde 200, `text/html`, con "PAGO FÁCIL"; `GET /config.js` responde 200.
  - `test_las_rutas_del_api_mandan_sobre_la_web`: con `carpeta_web`, `GET /salud` sigue respondiendo el JSON de la salud y `GET /api/cobros/noexiste` responde 404 con `{"detail": "Ese cobro no existe"}`.
  - `test_sin_carpeta_web_el_servidor_no_entrega_la_web`: con la configuración por defecto, `GET /` responde 404.
  - `test_carpeta_web_esta_vacia_por_defecto`: `Configuracion(_env_file=None).carpeta_web == ""`.
  - **RF**: RF-024, RF-029
  - **Dep.**: T014
  - **Hecho cuando**: las cuatro pruebas existen y fallan porque `carpeta_web` no existe.
- [ ] T016 [P] [US2] Prueba de la política de seguridad de contenido en `web/tests/test_seguridad.py`
  - `test_la_politica_solo_permite_conectarse_al_mismo_origen`: lee `web/index.html` (sin abrir página), saca el `content` del `<meta http-equiv="Content-Security-Policy">` y comprueba que la directiva `connect-src` vale exactamente `'self'`, y que las demás no cambian: `default-src 'self'`, `script-src 'self'`, `style-src 'self'`, `img-src 'self' data:` y `media-src 'self' blob:`.
  - **RF**: RF-029
  - **Dep.**: T014
  - **Hecho cuando**: la prueba existe y falla porque hoy `connect-src` incluye `http://localhost:8000 https:`.

### Implementación de F2

- [ ] T017 [US2] Agregar `carpeta_web` a `backend/app/config.py` y montar la web en `backend/app/main.py`
  - `config.py`: `carpeta_web: str = ""`, con su comentario (DP-21, R-12). Vacía en las pruebas del servidor.
  - `main.py`: al final de `crear_app`, **después de todas las rutas**, si `config.carpeta_web` no está vacía, `app.mount("/", StaticFiles(directory=<ruta>, html=True), name="web")`. Una ruta relativa se resuelve desde `RAIZ_BACKEND` (`CARPETA_WEB=../web` funciona aunque uvicorn arranque en otra carpeta). Si la carpeta no existe, el servidor no arranca (comportamiento de `StaticFiles`), y así se nota.
  - Docstring de `crear_app` con `(spec 003, RF-024, RF-029)`.
  - Limitación aceptada (QT-4): `StaticFiles` también entrega `web/tests/`, `web/pytest.ini` y los archivos ocultos de `web/`. Hugo lo aceptó el 2026-11-21 porque el repositorio es público y no hay secretos; no se filtra nada.
  - **RF**: RF-024, RF-029
  - **Dep.**: T015
  - **Hecho cuando**: T015 pasa y las demás pruebas del backend siguen en verde.
- [ ] T018 [US2] Cambiar la política de `web/index.html` a `connect-src 'self'`
  - Solo se cambia la directiva `connect-src`; el resto del `content` queda igual.
  - **RF**: RF-029
  - **Dep.**: T016
  - **Hecho cuando**: T016 pasa y todas las pruebas de la web siguen en verde en Chromium y WebKit (el servidor simulado sirve la página y las rutas en el mismo origen).
- [ ] T019 [P] [US4] Documentar `CARPETA_WEB` en `backend/.env.example` y en la tabla de variables de `backend/README.md`
  - `.env.example`: `CARPETA_WEB=` con el comentario "Carpeta de la web que entrega el servidor (en la demo, ../web). Vacía: no entrega la web."
  - `backend/README.md`: fila `CARPETA_WEB` · "Carpeta de la web que entrega el servidor en `/`" · vacío.
  - **RF**: RF-024
  - **Dep.**: T017
  - **Hecho cuando**: las dos líneas están y no se tocó nada más de esos archivos.
- [ ] T020 [US2] Comprobar en local la web servida por el servidor
  - **Quién**: Grok, con un servidor de desarrollo sin llave de pey (no crea cobros).
  - `cd backend && CARPETA_WEB=../web uv run uvicorn app.main:app --port 8001` y abrir `http://localhost:8001` en el navegador: se ve "PAGO FÁCIL" y el teclado, sin errores de la política en la consola. Parar por su PID exacto.
  - **RF**: RF-024, RF-029
  - **Dep.**: T017, T018
  - **Hecho cuando**: la página carga sin errores en la consola y se anota en la sección F2 de la guía.
- [ ] T021 [US2] Aplicar el cambio C-7 a la spec 002 (QP-11)
  - Las líneas citadas en C-7 (spec 003 §8.2) pudieron moverse con la unión del #72: se busca el texto.
  - (a) `specs/002-web-mvp/spec.md`, RF-057: quitar "(por ejemplo, porque se reinició)".
  - (b) Flujo local con la web desde el servidor en `http://localhost:8000` (con `CARPETA_WEB=../web`), en lugar del puerto 5173: `specs/002-web-mvp/quickstart.md` (pasos de arranque) y `web/README.md` («Correr en local»).
  - (c) `connect-src 'self'` en `specs/002-web-mvp/research.md` (política de R-11) y `specs/002-web-mvp/plan.md` (fila que la cita).
  - (d) `specs/002-web-mvp/spec.md` §4, filas "Reinicio del servidor con un cobro en pantalla" y "Reinicio del servidor con cobros anteriores en escucha": con la spec 003 el cobro sigue guardado (corte 2) y la pantalla reconecta y lo sigue escuchando.
  - (e) `specs/002-web-mvp/quickstart.md` §4: la web la sirve el backend (spec 003, DP-21), sin C-n a la 001.
  - `specs/002-web-mvp/verification-guide.md`: **no se tocan** las secciones con fecha; solo se agrega una nota con el flujo nuevo junto a los pasos con el puerto 5173 (hoy líneas 79-82 y 153-163).
  - En `specs/003-infraestructura-demo/spec.md` §8.2, la fila C-7 pasa a "Aprobado por Hugo el 2026-11-20, ampliado con (d) y (e) · **aplicado el AAAA-MM-DD** (F2)".
  - **RF**: RF-029 (C-7)
  - **Dep.**: T018
  - **Hecho cuando**: `git grep -n "5173" specs/002-web-mvp web/README.md` solo encuentra el puerto en secciones con fecha de la guía de verificación de la 002 (y en sus notas nuevas, que lo dan como flujo anterior) y en la fila histórica QP-2 de `specs/002-web-mvp/plan.md`, y la fila C-7 dice "aplicado".
- [ ] T022 [US4] Escribir la guía `docs/operacion-demo.md`, parte del corte 1 (DP-42, DP-43, research R-4)
  - **Quién**: borrador de Grok; la valida Hugo al seguirla en T026.
  - Secciones, en español y para Hugo:
    1. **Cuándo está encendida** (RF-060): solo en los momentos acordados (pruebas, video, negocios piloto y las pruebas de Leonel antes de cada puerta) y sin parar desde la entrega del 12 dic hasta el anuncio del 14 dic. Al menos una vez cada 5 días (RF-050; la parte de Supabase llega en F6). Esos días: corriente conectada y actualizaciones automáticas de macOS en pausa.
    2. **Antes de encender**: `main` al día y `uv sync --locked` en `backend/`.
    3. **Encender**: si la Mac se acaba de prender, primero abrir la app de Tailscale (`open -a Tailscale`; Funnel vuelve solo por `--bg`, TK-5). Después `cd backend && uv run uvicorn app.main:app --env-file .env.demo --workers 1 --port 8000`, **nunca con `--host 0.0.0.0`** (solo `127.0.0.1`, RF-056); `tailscale funnel --bg 8000`; `caffeinate -is -w <PID del servidor>`.
    4. **Comprobar desde fuera**: `https://<dirección>/salud` desde un celular con datos móviles; qué debe decir.
    5. **Aviso de pey**: la dirección `https://<dirección>/webhooks/pey`, dada de alta una sola vez en el portal para la llave de la demo (RF-025). No cambia al reiniciar (RF-030).
    6. **Desarrollo a la vez**: el servidor de desarrollo usa `backend/.env` y el puerto 8001 (QP-14).
    7. **Apagar**: `tailscale funnel reset` y parar el servidor por su PID exacto; `caffeinate` termina solo con `-w`.
    8. **Si algo falla**: sin internet o suspendida (volver a encender; la dirección no cambia), el túnel no responde (`tailscale funnel status`), límites por IP (DP-36 y, si F0 lo pidió, DP-40).
    9. **Secretos**: `backend/.env.demo` nunca se comparte ni se sube; la sesión de Tailscale vive en su app (RF-059). Cada variable que la demo necesita va en `backend/.env.demo`, aunque sea vacía: lo que falta se toma de `backend/.env` (desarrollo) (DP-44). Para que el equipo vea la configuración sin recibir el archivo, la guía enlaza la plantilla `backend/.env.demo.example` (TK-4, sustituye a la tabla de TK-3), que se mantiene al día cuando se agregue una variable (`CARPETA_WEB` en T024); con la demo encendida, `GET /salud` dice si cada credencial está puesta.
    10. **Pruebas de Leonel** (N-17): abrir el enlace desde su red y avisar si algo falla.
  - **RF**: RF-050, RF-056, RF-058, RF-059, RF-060
  - **Dep.**: T017
  - **Hecho cuando**: la guía tiene las 10 secciones y `git grep -n "0.0.0.0" docs/operacion-demo.md` no encuentra nada.

### Encender la demo con la web (Hugo)

- [ ] T023 [US4] Revisar los límites de la demo en `backend/.env.demo` con el resultado de F0
  - **Quién**: Hugo.
  - 30 si T005 mostró la IP real (DP-36); 60 si no (DP-40).
  - **RF**: RF-028
  - **Dep.**: T007
  - **Hecho cuando**: el valor coincide con el TK de F0.
- [ ] T024 [US4] Agregar `CARPETA_WEB=../web` a `backend/.env.demo`
  - **Quién**: Hugo. Grok agrega la misma línea, `CARPETA_WEB=../web`, a la plantilla `backend/.env.demo.example` (TK-4).
  - **RF**: RF-024
  - **Dep.**: T017
  - **Hecho cuando**: al encender con la guía, `https://<dirección>/` abre la pantalla de cobro.
- [ ] T025 [US2] Dar de alta el aviso de pey de la llave de la demo con la dirección del túnel
  - **Quién**: Hugo, en el portal de pey: `https://<dirección>/webhooks/pey`. El secreto que entrega el portal va solo a `backend/.env.demo`.
  - **RF**: RF-025, RF-030
  - **Dep.**: T006
  - **Hecho cuando**: el portal muestra la dirección del túnel en el aviso de esa llave, y `/salud` del servidor arrancado con `backend/.env.demo` dice `"secreto_aviso_pey": true` (pasó de T002, TK-2). La firma válida se comprueba con el primer pago (T030).
- [ ] T026 [US2] Comprobar la demo con la web por el túnel (quickstart §3, pasos 1 a 4)
  - **Quién**: Hugo, siguiendo **solo** `docs/operacion-demo.md`.
  - Paso 1: `/salud` y la pantalla desde un celular con datos móviles, con HTTPS y sin páginas intermedias.
  - Paso 2: cobro desde el celular y pantalla abierta 25 minutos; las señales de vida y *vencido* llegan en el momento, y el canal solo lo cierra el servidor al minuto 20.
  - Paso 3: dos celulares en redes distintas; dos IP en el registro, ninguna `127.0.0.1`.
  - Paso 4: reiniciar el servidor, después el túnel y después la computadora; la misma dirección cada vez.
  - Paso extra A (historia 4, escenario 3; QT-6): con un cobro en pantalla, quitar el wifi de la Mac un minuto y volver a ponerlo; la pantalla muestra "Reconectando…" y vuelve sola al cobro.
  - Paso extra B (historia 4, escenario 4; QT-6): con la demo apagada (guía, sección 7), abrir el enlace desde el celular; se ve el error del túnel o del navegador, sin página propia.
  - Si el paso 2 falla, se para y Hugo decide el plan B (research R-1).
  - **RF**: RF-024, RF-026, RF-028, RF-030, RF-057, RF-060
  - **Dep.**: T020, T022, T023, T024
  - **Hecho cuando**: los cuatro pasos y los dos extra salen como dicen el quickstart y la historia 4, y quedan anotados en la sección F2 de la guía de verificación. Lo que falte de la guía se corrige en `docs/operacion-demo.md`.
- [ ] T027 [US2] Comprobar CORS y la red local (quickstart §3, pasos 5 y 6)
  - **Quién**: Hugo.
  - Paso 5: desde la consola de una página de otro dominio, `fetch("https://<dirección>/api/cobros", {method: "POST"})`; el navegador lo bloquea por CORS.
  - Paso 6: desde otro equipo en la misma red, `curl --max-time 5 http://<IP local de la Mac>:8000/salud`; conexión rechazada o sin respuesta.
  - **RF**: RF-027, RF-056
  - **Dep.**: T026
  - **Hecho cuando**: los dos resultados quedan anotados en la sección F2 de la guía de verificación (CE-015).
- [ ] T028 Cierre de F2: todo en verde, sección F2 en la guía de verificación y commit sugerido
  - Commit sugerido: `feat(003): demo por el túnel con la web desde el servidor y C-7 (F2)`.
  - PR con la plantilla, `Closes #65` y el enlace a `specs/003-infraestructura-demo/`. Menciona que C-7 quedó aplicado y la comparativa del túnel (research R-1, DP-38).
  - `docs/plan-hackathon.md` §7: la línea "Base de datos y hosting: Supabase y AWS (15 nov)" pasa a "Base de datos y hosting: Supabase y la Mac de Hugo por Tailscale Funnel (21 nov, spec 003, DP-38)", como pide #65 (QT-5). No se toca nada más del archivo.
  - **RF**: RF-024 a RF-030, RF-056 a RF-060
  - **Dep.**: T019, T021, T025, T026, T027
  - **Hecho cuando**: todo en verde (regla 5), la guía de verificación tiene la sección F2 y Hugo aprobó el cierre.

**Punto de control**: cualquier celular abre la demo por HTTPS, crea un cobro y escucha su canal durante toda la ventana.

---

## Fase 3 (F3): Pago real desde la dirección del túnel · 22 nov · cierre del corte 1

**Objetivo**: medir la promesa de PAGO FÁCIL desde la demo pública: QR en menos de 3 s y "Pago recibido" en menos de 2 s después del aviso, en Android y en iPhone (historia 3). Después se cierran #66, #27 y #64.

**Prueba independiente**: el quickstart §4.

- [ ] T029 [US3] QR en menos de 3 s (quickstart §4, paso 2; CE-003)
  - **Quién**: Hugo, con un celular con datos móviles.
  - Crear 10 cobros y medir de "Cobrar" al QR en pantalla. No se pagan.
  - Si no se cumple, Hugo decide con un C-n a la 003 y a la 002 si el QR se dibuja desde `qr` (riesgo del plan §11, D-2).
  - **RF**: RF-024
  - **Dep.**: T028
  - **Hecho cuando**: 9 de 10 en menos de 3 s, con los 10 tiempos anotados en la sección F3 de la guía de verificación.
- [ ] T030 [US3] Pagos reales de $0.01 en Android y en iPhone (quickstart §4, pasos 1 y 3; CE-002, CE-004)
  - **Quién**: Hugo, con su autorización en ese momento. Se paga desde otro celular con la app del banco.
  - Por cada celular: hora del aviso en el registro del servidor frente a la hora en que la pantalla muestra "Pago recibido" (con sonido).
  - En uno de los dos, pagar después del minuto 15 del canal (CE-004). Con la vigencia normal el QR vence en el minuto 10 y la web lo oculta, así que **solo para ese pago** (QT-2) la demo se arranca con la vigencia en la línea de comando, que manda sobre `backend/.env.demo`: `cd backend && EXPIRACION_SEGUNDOS=1200 uv run uvicorn app.main:app --env-file .env.demo --workers 1 --port 8000`. Se paga en el minuto 16 y después se para el servidor por su PID y se vuelve a arrancar normal (pey no tiene máximo para `expiration`; mínimo 360). Se anota en la guía de verificación.
  - El primer pago comprueba el aviso: el registro muestra el aviso con firma válida (RF-025).
  - **RF**: RF-025, RF-026, RF-057
  - **Dep.**: T025, T029
  - **Hecho cuando**: en los dos celulares suena y muestra "Pago recibido" en menos de 2 s después del aviso, y los tiempos quedan anotados.
- [ ] T031 [US3] Reenvío del aviso y prueba de Leonel (quickstart §4, pasos 4 y 5)
  - **Quién**: Hugo (reenvío desde el portal de pey) y Leonel (desde su red y sus celulares, N-17).
  - Reenvío: la pantalla no vuelve a sonar y `GET /api/cobros/<id>` sigue con un solo pago.
  - Leonel repite el paso 3.1 (abrir con HTTPS) y el 4.2 (QR en menos de 3 s) y avisa a Hugo si algo falla.
  - **RF**: RF-007, RF-024
  - **Dep.**: T030
  - **Hecho cuando**: los dos resultados quedan anotados en la sección F3 de la guía de verificación.
- [ ] T032 [P] [US3] Agregar la sección de la demo a `README.md` (#66)
  - Enlace `https://<dirección>`, cuándo está encendida (los momentos acordados y del 12 al 14 dic, RF-060) y cómo probarla: abrir en el celular, cobrar y pagar con la app del banco (CoDi), no con la cámara.
  - Lo demás que pide #66 (QT-5), en secciones cortas: «Correr en local», con enlaces a `backend/README.md` y `web/README.md` (sin repetir sus pasos), y «Equipo y tecnologías»: Hugo, Juan, Miguel y Leonel con los usuarios de GitHub que dé Hugo, y Python con FastAPI, la web PWA, Supabase y el API de pey. El aviso de que no es un producto oficial ya está.
  - **RF**: RF-024, RF-060
  - **Dep.**: T028
  - **Hecho cuando**: las tres secciones existen y el enlace abre la demo cuando está encendida.
- [ ] T033 Cierre de F3 y del corte 1: sección F3 en la guía de verificación y commit sugerido
  - Commit sugerido: `docs(003): enlace de la demo y pago real desde el túnel (F3)`.
  - PR del README con la plantilla y `Closes #66`. Después del pago real, Hugo cierra #27 y #64 con un comentario que cita los tiempos de T030 (o los cierra el mismo PR).
  - **RF**: RF-024, RF-025, RF-060
  - **Dep.**: T029, T030, T031, T032
  - **Hecho cuando**: la sección F3 de la guía tiene los tiempos, y #66, #27 y #64 están cerrados.

**Punto de control (fin del corte 1)**: demo pública con CI, enlace en el README y pago real medido.

---

## Fase 4 (F4): Migraciones con un comando · 23 nov · corte 2

**Objetivo**: crear y actualizar la estructura de la base de datos con un solo comando, igual en desarrollo, en el CI y en la demo (historia 6).

**Prueba independiente**: aplicar el comando dos veces seguidas en una base vacía: la primera crea todo y la segunda dice "No había nada que aplicar." (CE-007).

### Preparación de F4

- [ ] T034 [US6] Agregar `psycopg[binary]` 3 y `psycopg-pool` a `backend/pyproject.toml` y `backend/uv.lock` (DP-2, research R-6)
  - `cd backend && uv add "psycopg[binary]==<versión>" "psycopg-pool==<versión>"`, cada una publicada hace al menos dos semanas (se comprueba la fecha en PyPI y se anota en la descripción del PR). Sin `pip install`.
  - **RF**: RF-017
  - **Dep.**: T033
  - **Hecho cuando**: `uv run --directory backend python -c "import psycopg, psycopg_pool"` no falla y las pruebas siguen en verde.
- [ ] T035 [P] [US6] Ayuda del PostgreSQL desechable en `backend/tests/postgres_desechable.py` (archivo nuevo) y la fixture `base_vacia` en `backend/tests/conftest.py` (research R-10)
  - Lee `PRUEBAS_DATABASE_URL`. Si no está, `pytest.skip("Sin PRUEBAS_DATABASE_URL: las pruebas de PostgreSQL corren en el CI (R-10)")`.
  - Crea los roles `anon` y `authenticated` si no existen (el `revoke` del PR #97 los necesita), crea una base `prueba_<hex aleatorio>`, entrega su URL y al terminar la borra con `drop database … with (force)`.
  - Nunca imprime la URL.
  - **RF**: RF-038 (CE-011)
  - **Dep.**: T034
  - **Hecho cuando**: sin `PRUEBAS_DATABASE_URL`, una prueba que pide `base_vacia` sale como *skipped* con ese motivo.

### Pruebas de F4 (primero, deben fallar antes de implementar)

- [ ] T036 [P] [US6] Prueba de `DATABASE_URL` en la configuración, en `backend/tests/test_salud_y_registros.py`
  - `test_database_url_se_lee_de_la_configuracion`: con `monkeypatch.setenv("DATABASE_URL", "postgresql://usuario-falso:clave-falsa@base.prueba/x")`, `Configuracion(_env_file=None).database_url.get_secret_value()` es ese valor, y `repr()` de la configuración no lo contiene.
  - El plan pone `database_url` en F5 (§4); se adelanta aquí porque el comando de migraciones la lee. Se anota como TK en el plan §14.
  - **RF**: RF-020, RF-021
  - **Dep.**: T034
  - **Hecho cuando**: la prueba existe y falla porque el campo no existe.
- [ ] T037 [P] [US6] Pruebas del comando sin PostgreSQL en `backend/tests/test_migraciones.py` (archivo nuevo)
  - `test_sin_database_url_el_comando_avisa_y_sale_con_1`: sale con 1 y escribe "Falta DATABASE_URL en backend/.env.".
  - `test_si_no_se_puede_conectar_no_muestra_la_direccion`: con `DATABASE_URL=postgresql://usuario-falso:clave-falsa@127.0.0.1:1/x`, sale con 1, escribe "No se pudo conectar con la base de datos (" seguido del nombre de una clase, y la salida no contiene `usuario-falso`, `clave-falsa` ni `127.0.0.1:1`.
  - Mensajes del [contrato](contracts/comando-migraciones.md) §4.
  - **RF**: RF-017, RF-021
  - **Dep.**: T034
  - **Hecho cuando**: las dos pruebas existen y fallan porque no existe `app.migraciones`.
- [ ] T038 [US6] Pruebas del comando con PostgreSQL en `backend/tests/test_migraciones_postgres.py` (archivo nuevo)
  - Todas usan `base_vacia` (T035) y una función interna del comando que recibe la URL y la carpeta de migraciones.
  - `test_aplicar_en_una_base_vacia_crea_el_esquema_la_imagen_y_el_estado`: con `--entorno local`, existen `negocios`, `cupones`, `cobros`, `pagos`, `avisos_webhook`, la vista `cobros_con_estado`, la columna `cobros.qr_imagen` y `estado_del_servidor`; `cambios_de_estructura` tiene 0001, 0002 y 0003, y `entorno_de_la_base` dice `local`.
  - `test_aplicar_dos_veces_no_cambia_nada`: la segunda vez sale con 0, dice "No había nada que aplicar." y una fila insertada entre las dos sigue ahí (RF-019, CE-007).
  - `test_una_migracion_que_falla_no_deja_nada_a_medias`: con una carpeta temporal donde 0002 crea una tabla y después falla, la tabla de 0002 no existe, 0002 no queda anotada, 0001 sí, y el mensaje es "La versión 0002 falló y no se aplicó nada de ella (<Clase>)." con código 1.
  - `test_la_primera_vez_sin_entorno_se_detiene`: "Es la primera vez en esta base: indica --entorno local o --entorno demo." y código 1.
  - `test_una_base_con_el_esquema_sin_registro_pide_ya_aplicada`: con el SQL de 0001 corrido a mano, `aplicar --entorno demo` sale con 1 y dice "Esta base ya tiene el esquema del PR #97 sin registro. Revísalo y corre: aplicar --ya-aplicada 0001."
  - `test_ya_aplicada_solo_agrega_lo_que_falta`: lo mismo, con un cobro guardado; `aplicar --entorno demo --ya-aplicada 0001` anota 0001 sin correrla, aplica 0002 y 0003, y el cobro sigue ahí (historia 6, escenario 3).
  - `test_ya_aplicada_se_rechaza_si_no_existe_cobros`: en una base vacía, `--ya-aplicada 0001` sale con 1 sin cambiar nada (DP-19).
  - `test_los_datos_de_prueba_se_rechazan_en_una_base_demo`: "Los datos de prueba solo se cargan en la base local." y código 1 (RF-054).
  - `test_los_datos_de_prueba_se_cargan_en_local_y_se_pueden_repetir`: con `--datos-de-prueba` dos veces, los cobros `prueba-*` quedan una sola vez.
  - `test_la_marca_de_entorno_no_se_puede_cambiar`: una base `local` con `--entorno demo` se detiene con código 1 (RF-049, RF-054).
  - `test_anon_y_authenticated_no_pueden_leer_ni_escribir`: con `set role anon` y después `set role authenticated`, leer o escribir en cada tabla (también `cambios_de_estructura`, `entorno_de_la_base` y `estado_del_servidor`) da error de permisos (RF-022).
  - `test_estado_muestra_entorno_aplicadas_y_pendientes`: `estado` no cambia nada y muestra el entorno, las versiones aplicadas y las pendientes.
  - **RF**: RF-017, RF-018, RF-019, RF-022, RF-049, RF-054
  - **Dep.**: T035
  - **Hecho cuando**: las pruebas existen y fallan (con `PRUEBAS_DATABASE_URL`) o se saltan con su motivo (sin ella).

### Implementación de F4

- [ ] T039 [US6] Agregar `database_url: SecretStr = SecretStr("")` a `backend/app/config.py`
  - Con su comentario: URL del *pooler* de Supabase en modo sesión (R-9), solo en `backend/.env` o `backend/.env.demo` (RF-020).
  - **RF**: RF-020, RF-021
  - **Dep.**: T036
  - **Hecho cuando**: T036 pasa.
- [ ] T040 [US6] Crear los archivos de `supabase/migraciones/` y los de datos (data-model §5)
  - `supabase/migraciones/0001_esquema_inicial.sql`: el contenido de `supabase/001_esquema_inicial.sql` **sin** `begin;` ni `commit;` (DP-17); el resto igual.
  - `supabase/migraciones/0002_imagen_del_qr.sql`: `alter table cobros add column qr_imagen text;` y el comentario de `cobros.qr` al día ("la imagen es la que manda pey"). No recrea la vista (DP-20).
  - `supabase/migraciones/0003_estado_del_servidor.sql`: `estado_del_servidor` con `unico boolean primary key default true check (unico)` y `conciliado_hasta timestamptz not null`; `enable row level security`; `revoke all … from anon, authenticated`.
  - `supabase/datos_de_prueba.sql`: los bloques A y B de `supabase/002_datos_de_prueba.sql`, con `on conflict do nothing` en cada `insert`.
  - `supabase/consultas_de_verificacion.sql`: los bloques C a F del mismo archivo, con la cabecera "para correrlas a mano".
  - Borrar `supabase/001_esquema_inicial.sql` y `supabase/002_datos_de_prueba.sql` con `rm` (no con `git rm`; el índice lo maneja Hugo).
  - **RF**: RF-018, RF-022, RF-054, RF-061
  - **Dep.**: T038
  - **Hecho cuando**: `git grep -n "001_esquema_inicial\|002_datos_de_prueba" -- ':!specs'` no encuentra referencias rotas y los archivos nuevos existen.
- [ ] T041 [US6] Implementar el comando en `backend/app/migraciones.py` (archivo nuevo, DP-3, DP-17 a DP-19)
  - `python -m app.migraciones estado|aplicar [--entorno local|demo] [--ya-aplicada 0001] [--datos-de-prueba]`, con `argparse` y mensajes del [contrato](contracts/comando-migraciones.md) §4 y §5.
  - Lee `DATABASE_URL` con `Configuracion` (variable de entorno o `backend/.env`; con `uv run --env-file …` manda el archivo indicado). Conexión síncrona de psycopg con `connect_timeout=5`.
  - Antes de migrar crea, con `if not exists`, `cambios_de_estructura` y `entorno_de_la_base` (data-model §5.1), con RLS y sin acceso para `anon` ni `authenticated`.
  - Cada migración pendiente corre **en una transacción junto con su fila** en `cambios_de_estructura` (RF-019). Orden por versión.
  - Reglas de data-model §5.2: primera vez exige `--entorno`; marca distinta se detiene; `cobros` sin registro pide `--ya-aplicada 0001`; `--ya-aplicada` solo con `cobros` existente y 0001 sin anotar; datos de prueba solo en `local`.
  - Errores: solo el nombre de la clase, nunca su texto ni la URL (RF-021, DP-15). Código 0 o 1.
  - Una función interna que recibe la URL, la carpeta de migraciones y las opciones, para las pruebas.
  - Docstrings con `(spec 003, RF-017 …)`.
  - **RF**: RF-017, RF-018, RF-019, RF-021, RF-049, RF-054
  - **Dep.**: T037, T039, T040
  - **Hecho cuando**: T037 pasa en local, y T038 pasa con `PRUEBAS_DATABASE_URL` (en el CI con T043).
- [ ] T042 [US6] Agregar el trabajo `base-de-datos` a la prueba del CI en `backend/tests/test_ci.py`
  - `test_el_ci_prueba_las_migraciones_contra_un_postgresql_desechable`: hay un trabajo `base-de-datos:` con el servicio `postgres:17`, `PRUEBAS_DATABASE_URL`, y `python -m app.migraciones aplicar --entorno local` dos veces.
  - **RF**: RF-036, RF-038
  - **Dep.**: T041
  - **Hecho cuando**: la prueba existe y falla porque el trabajo no está en `ci.yml`.
- [ ] T043 [US6] Agregar el trabajo `base-de-datos` a `.github/workflows/ci.yml` (contrato [ci](contracts/ci.md) §4)
  - Servicio `postgres:17` con `POSTGRES_PASSWORD: prueba` (contraseña fija de prueba, no un secreto) y su comprobación de salud.
  - Pasos: `uv sync --locked`; crear los roles `anon` y `authenticated`; `DATABASE_URL=<servicio> uv run python -m app.migraciones aplicar --entorno local` dos veces, comprobando que la segunda dice "No había nada que aplicar."; `PRUEBAS_DATABASE_URL=<servicio> uv run pytest -q`.
  - **RF**: RF-036, RF-038
  - **Dep.**: T042
  - **Hecho cuando**: T042 pasa y, en el PR, `base-de-datos` sale en verde sin pruebas saltadas por falta de `PRUEBAS_DATABASE_URL`.
- [ ] T044 [US6] Marcar `base-de-datos` como obligatorio en la protección de `main`
  - **Quién**: Hugo, cuando el trabajo ya corrió en un PR (como T013).
  - **RF**: RF-037
  - **Dep.**: T043
  - **Hecho cuando**: `gh api repos/team-complexity/Hackton-2026/branches/main/protection/required_status_checks -q .contexts` muestra `servidor`, `web` y `base-de-datos`.

### Base de desarrollo (Hugo y Juan)

- [ ] T045 [US6] Recibir el proyecto de Supabase de desarrollo y poner su `DATABASE_URL` en `backend/.env`
  - **Quién**: Juan crea el proyecto (RF-049) y comparte el acceso con Hugo; Hugo pone la URL del *pooler* en modo sesión en su `backend/.env` (desarrollo). Nadie la pega en un chat.
  - **RF**: RF-020, RF-049
  - **Dep.**: ninguna (puede hacerse antes de F4)
  - **Hecho cuando**: `uv run --directory backend python -m app.migraciones estado` conecta y muestra que la base no tiene entorno.
- [ ] T046 [US6] Aplicar las migraciones en la base de desarrollo (quickstart §6, paso 1; CE-007)
  - **Quién**: Hugo.
  - `uv run --directory backend python -m app.migraciones aplicar --entorno local --datos-de-prueba` y después `uv run --directory backend python -m app.migraciones aplicar`.
  - **RF**: RF-017, RF-018, RF-019, RF-054
  - **Dep.**: T041, T045
  - **Hecho cuando**: la primera aplica 0001, 0002 y 0003 y carga los datos de prueba; la segunda dice "No había nada que aplicar."
- [ ] T047 [US6] Comprobar que la base de desarrollo no es la de la demo
  - **Quién**: Hugo. El comando `estado` en la base de desarrollo dice `local`. La de la demo se marca `demo` en F6 (T072).
  - **RF**: RF-049
  - **Dep.**: T046
  - **Hecho cuando**: `estado` sin `--env-file` dice `local`.
- [ ] T048 [US6] Poner la segunda llave de producción en `backend/.env` y comprobar que es distinta de la de la demo (RF-053, QP-14)
  - **Quién**: Hugo crea la segunda llave en el portal de pey y la liga a su cuenta CoDi; quien prueba sin túnel no da de alta aviso (usa la consulta de respaldo).
  - Comparación sin ver los valores: `diff -q <(grep '^PEY_API_KEY=' backend/.env) <(grep '^PEY_API_KEY=' backend/.env.demo) >/dev/null && echo IGUALES || echo DISTINTAS`, y lo mismo con `DATABASE_URL` cuando la demo la tenga (F6).
  - **RF**: RF-049, RF-053
  - **Dep.**: T045
  - **Hecho cuando**: el comando dice `DISTINTAS` y `/salud` del servidor de desarrollo dice `"llave_pey": true`.
- [ ] T049 Cierre de F4: todo en verde, sección F4 en la guía de verificación y commit sugerido
  - Commit sugerido: `feat(003): comando de migraciones y trabajo base-de-datos del CI (F4)`.
  - **RF**: RF-017 a RF-019, RF-022, RF-049, RF-053, RF-054
  - **Dep.**: T043, T044, T046, T047, T048
  - **Hecho cuando**: todo en verde (regla 5) con el trabajo `base-de-datos` en el CI, y la sección F4 tiene las salidas de T046.

**Punto de control**: la base de desarrollo y la del CI se crean con el mismo comando, y la segunda vez no cambia nada.

---

## Fase 5 (F5): Guardar los cobros en la base de datos · 23–24 nov · corte 2

**Objetivo**: la memoria pasa a ser una caché de escritura directa sobre un almacén de PostgreSQL; los cobros, pagos y avisos sobreviven a un reinicio, cada pago se registra una sola vez y una falla de la base de datos responde con un mensaje para el dueño (historia 1).

**Prueba independiente**: pruebas automáticas de reinicio, deduplicación y fallas con el almacén en memoria (CE-005); comprobación en desarrollo (T066).

### Pruebas de F5 (primero, deben fallar antes de implementar)

- [ ] T050 [P] [US1] Ayudas de prueba del almacén en `backend/tests/almacen_de_prueba.py` (archivo nuevo) y en `backend/tests/conftest.py`
  - `AlmacenQueFalla`: envuelve un `AlmacenEnMemoria`, dice `configurado = True` y permite `fallar(operacion, veces=None)` (lanza `ErrorDeAlmacen`), `fallar_datos(operacion)` (lanza `ErrorDeDatos`), `no_responde()` (la salud) y `pausar(operacion)` (un `asyncio.Event` que la prueba suelta, para simular dos peticiones a la vez sin tiempo real). Guarda cada llamada con su operación y su `espera`.
  - `reiniciar(app)`: una app nueva con un almacén nuevo sobre los **mismos** datos en memoria, el mismo `RelojFalso` y el mismo `PeySimulado` (plan §7).
  - `RelojDetenido`: `RelojFalso` cuyo `dormir` espera para siempre (para arrancar la tarea de fondo una sola vuelta en T060).
  - `RelojPorPasos` (QT-7): `RelojFalso` cuyo `dormir(segundos)` anota la espera pedida y se queda esperando hasta que la prueba lo suelta con un método que avanza el reloj esos segundos. Así se prueba el bucle de `correr_tareas` vuelta por vuelta, sin tiempo real y sin que el reloj avance solo.
  - `backend/tests/conftest.py` todavía no cambia: la fixture `app` pasa al almacén en T057. Así `almacen_de_prueba.py` solo lo importan los archivos de prueba nuevos y las pruebas de la 001 se siguen recogiendo.
  - **RF**: — (principio V, DP-6)
  - **Dep.**: T049
  - **Hecho cuando**: el archivo existe; las pruebas nuevas que lo usan fallan porque `app.almacen` no existe, y las de la 001 siguen en verde.
- [ ] T051 [P] [US1] Pruebas del contrato del almacén en `backend/tests/test_almacen.py` (archivo nuevo)
  - Una fixture `almacen` parametrizada: `memoria` siempre, y `postgres` con `base_vacia` (T035), las migraciones aplicadas con la función interna del comando y `AlmacenPostgres` con un `RelojFalso` (se salta sin `PRUEBAS_DATABASE_URL`).
  - Pruebas para los dos:
    - `test_un_cobro_guardado_se_carga_igual`: `guardar_cobro` y `cargar_por_id` devuelven los mismos campos; monto `Decimal`, monto libre `None`, `codi_qr_id` y `qr` vacíos (`""` en memoria, `null` en la base), sin pagos.
    - `test_el_qr_guardado_se_carga_por_codi_qr_id_con_su_imagen`, y `qr_imagen` `None` cuando pey no la mandó (RF-010, RF-011).
    - `test_un_cobro_borrado_ya_no_se_carga` (RF-052).
    - `test_la_cancelacion_se_guarda_una_sola_vez`: `cancelar` solo escribe si `cancelado_en` está vacío (RF-004).
    - `test_on_conflict_no_duplica_la_transaccion`: el mismo `transaccion_id` dos veces; la primera devuelve `True` y la segunda `False` (RF-007).
    - `test_el_pago_y_su_webhook_id_se_guardan_juntos`: después de `registrar_pago` con `webhook_id`, `aviso_visto` dice `True` (DP-9, RF-003).
    - `test_los_pagos_se_cargan_en_orden_de_numero` (RF-008).
    - `test_cobros_con_ventana_terminada_respeta_el_rango`: `fin_ventana` en (desde, hasta], solo con `codi_qr_id`, en orden de `fin_ventana` (RF-061).
    - `test_conciliado_hasta_empieza_vacio_y_se_guarda` (RF-061).
  - Solo para PostgreSQL:
    - `test_las_horas_guardadas_son_las_del_reloj_del_servidor`: con el `RelojFalso` en una fecha de 2020, `creado_en`, `registrado_en` y `recibido_en` son esa fecha, no la de la base de datos (RF-006, DP-10).
    - `test_sin_respuesta_lanza_error_de_almacen_sin_datos_de_conexion`: con una URL a `127.0.0.1:1`, la operación lanza `ErrorDeAlmacen` cuyo texto tiene la operación y el nombre de la clase, y no la URL (RF-021, DP-15).
  - **RF**: RF-001 a RF-008, RF-010, RF-011, RF-021, RF-052, RF-061
  - **Dep.**: T050
  - **Hecho cuando**: las pruebas existen y fallan porque no existe `app.almacen`.
- [ ] T052 [P] [US1] Pruebas de guardar y de reinicio por la API en `backend/tests/test_guardar_cobros.py` (archivo nuevo)
  - Nombres del plan §7, con el almacén en memoria y `reiniciar(app)`:
    - `test_un_cobro_creado_queda_guardado_con_su_imagen_del_qr` (RF-001, RF-010).
    - `test_el_pago_se_guarda_antes_de_emitirse_por_el_canal`: con `registrar_pago` en falla no se emite nada; sin falla, cuando llega el evento `pago` el almacén ya lo tiene (RF-002).
    - `test_el_webhook_id_procesado_queda_guardado` (RF-003).
    - `test_la_cancelacion_queda_guardada_con_su_hora` (RF-004).
    - `test_dos_cargas_a_la_vez_del_mismo_cobro_dan_el_mismo_objeto`: dos `obtener` a la vez con `cargar_por_id` en pausa devuelven el mismo objeto (`is`) (RF-005, DP-33).
    - `test_tras_un_reinicio_se_puede_ver_cancelar_y_escuchar_un_cobro_guardado` (RF-005, historia 1, escenario 1).
    - `test_tras_un_reinicio_el_aviso_de_pey_registra_el_pago` (RF-005, escenario 2).
    - `test_tras_un_reinicio_la_consulta_de_respaldo_encuentra_el_pago` (RF-005, escenario 3).
    - `test_el_estado_tras_un_reinicio_se_calcula_con_el_reloj_del_servidor`: un cobro *cancelado* y uno *vencido* conservan su estado, y un pago tardío dentro de la ventana se registra (RF-006, escenario 5).
    - `test_un_aviso_reenviado_no_duplica_el_pago`, `test_el_aviso_y_la_consulta_a_la_vez_registran_un_solo_pago` y `test_el_mismo_pago_antes_y_despues_de_un_reinicio_se_registra_una_vez` (RF-007, CE-005).
    - `test_tras_un_reinicio_el_siguiente_pago_es_el_numero_3` y `test_dos_pagos_distintos_a_la_vez_quedan_con_numeros_1_y_2` (RF-008, escenario 4, DP-8).
    - `test_los_datos_de_quien_paga_no_se_guardan_ni_se_registran`: aviso con `metadata` completa (nombre, CLABE, banco, teléfono, clave de rastreo); nada de eso en el almacén ni en `caplog` (RF-009).
    - `test_sin_imagen_de_pey_el_cobro_guardado_vuelve_sin_imagen` (RF-011, escenario 6).
  - **RF**: RF-001 a RF-011
  - **Dep.**: T050
  - **Hecho cuando**: las pruebas existen y fallan por la razón esperada.
- [ ] T053 [P] [US1] Pruebas de fallas de la base de datos en `backend/tests/test_fallas_base_de_datos.py` (archivo nuevo)
  - Con `AlmacenQueFalla`; códigos y textos `detail` del [contrato de fallas](contracts/fallas-base-de-datos.md):
    - `test_si_la_base_no_responde_al_crear_no_se_llama_a_pey`: 503 "No se pudo guardar el cobro. Intenta de nuevo en un momento." y `pey.solicitudes` vacío (RF-012, escenario 7).
    - `test_si_pey_falla_el_cobro_guardado_se_borra`: con `pey.estado_crear = 500`, el almacén ya no tiene el cobro y la respuesta es la de la 001; si el borrado también falla, se registra y la respuesta no cambia (RF-052, RF-016).
    - `test_si_la_base_falla_al_guardar_el_qr_no_se_devuelve_el_qr`: 503, el cuerpo no trae `qr` y el cobro salió de la memoria (RF-013).
    - `test_al_crear_cada_escritura_espera_como_maximo_2_segundos`: las llamadas `guardar_cobro` y `guardar_qr` llevan `espera=2` (DP-35).
    - `test_si_la_base_falla_con_un_aviso_se_responde_503_y_no_se_emite`: 503 "No se pudo registrar el aviso. Se reintentará.", ningún evento en el canal y el aviso en la lista de reintentos (RF-014).
    - `test_un_aviso_con_monto_cero_o_negativo_se_rechaza_con_400`: `amount` 0 y -1 con firma válida dan 400 "Aviso con datos no válidos" y el `webhook-id` no queda marcado (DP-34, C-6 g).
    - `test_un_error_de_datos_responde_400_y_no_entra_a_los_reintentos` (DP-34).
    - `test_el_aviso_pendiente_se_registra_y_se_emite_cuando_la_base_vuelve`: después de la falla, se quita la falla, se avanza el `RelojFalso` 15 s y una vuelta de `ReintentosDeAvisos` registra el pago y lo emite (RF-048).
    - `test_un_aviso_reenviado_mientras_esta_pendiente_no_se_duplica` (RF-048).
    - `test_si_la_base_no_responde_al_ver_un_cobro_se_responde_503_y_no_404`: un cobro que no está en memoria con `cargar_por_id` en falla; 503 "No se pudo consultar el cobro. Intenta de nuevo." (RF-015).
    - `test_si_la_base_no_responde_al_abrir_el_canal_se_responde_503` (RF-015).
    - `test_si_la_base_falla_al_cancelar_el_cobro_no_cambia`: 503 "No se pudo cancelar el cobro. Intenta de nuevo.", el cobro sigue *pendiente* y no se avisa por el canal (RF-004).
    - `test_cada_falla_de_la_base_deja_registro_sin_datos_de_conexion`: con `database_url` falsa en la configuración, cada falla deja una línea `WARNING` o `ERROR` con la operación (`guardar cobro`, `guardar QR`, `borrar cobro`, `registrar pago`, `guardar aviso`, `cancelar`, `cargar cobro`), el id del cobro y el nombre de la clase; ni los registros ni las respuestas contienen la URL (RF-016, RF-021, CE-010).
  - **RF**: RF-004, RF-012 a RF-016, RF-021, RF-048, RF-052
  - **Dep.**: T050
  - **Hecho cuando**: las pruebas existen y fallan por la razón esperada.
- [ ] T054 [P] [US1] Pruebas de la salud con la base de datos en `backend/tests/test_salud_y_registros.py`
  - `test_la_salud_dice_si_la_base_responde_sin_mostrar_valores`: tres casos, `"responde"`, `"no responde"` (`AlmacenQueFalla.no_responde()`) y `"sin configurar"` (almacén en memoria sin `DATABASE_URL`); los otros tres campos no cambian ([contrato de salud](contracts/salud.md)).
  - `test_la_salud_guarda_la_respuesta_de_la_base_10_segundos`: dos peticiones seguidas consultan la base una vez; después de avanzar el `RelojFalso` 10 s, otra vez (DP-31).
  - **RF**: RF-023, RF-021
  - **Dep.**: T050
  - **Hecho cuando**: las pruebas existen y fallan porque no hay `base_de_datos` en la salud.

### Implementación de F5

- [ ] T055 [US1] Interfaz y almacén en memoria en `backend/app/almacen.py` (archivo nuevo, DP-6, plan §4)
  - `ErrorDeAlmacen(operacion: str, clase: str)`: la base de datos no responde; su texto es "Base de datos sin respuesta al <operacion> (<clase>)", nunca el texto del error original (DP-15).
  - `ErrorDeDatos(operacion, clase)`: PostgreSQL rechazó el valor (DP-34).
  - `Almacen` (clase abstracta) con operaciones asíncronas, cada una con `espera: float = 5`: `guardar_cobro`, `guardar_qr`, `borrar_cobro`, `cancelar`, `registrar_pago` (devuelve si el pago es nuevo y guarda el `webhook_id` en la misma transacción), `guardar_aviso`, `aviso_visto`, `cargar_por_id`, `cargar_por_codi_qr`, `cobros_con_ventana_terminada(desde, hasta)`, `leer_conciliado_hasta`, `guardar_conciliado_hasta`, `responde`; y `configurado: bool`, `abrir()` y `cerrar()`.
  - `AlmacenEnMemoria(datos=None, reloj=None)`: la misma interfaz con diccionarios en un objeto de datos que se puede compartir (para simular un reinicio). `configurado = False`.
  - **RF**: RF-001 a RF-005, RF-007, RF-061
  - **Dep.**: T051
  - **Hecho cuando**: las pruebas de T051 con `memoria` pasan.
- [ ] T056 [US1] Almacén de PostgreSQL en `backend/app/almacen_postgres.py` (archivo nuevo, data-model §2 y §3)
  - `AlmacenPostgres(url: SecretStr, reloj: Reloj)`: `psycopg_pool.AsyncConnectionPool` de 1 a 3 conexiones, creado con `open=False`; `abrir()` lo abre sin esperar a la base de datos (`wait=False`), para que el servidor arranque aunque no responda; `cerrar()`.
  - El constructor **no hace I/O** (QT-8): `backend/app/main.py:330` arma la app al importarse y las pruebas importan `app.main`; si el constructor se conectara, en una computadora con `DATABASE_URL` en `backend/.env` las pruebas tocarían la base real (CE-011).
  - SQL de data-model §3, siempre con parámetros de psycopg. Traduce Unix ↔ `timestamptz` en UTC y `""` ↔ `null`. Escribe **todas** las horas con el `Reloj` (`creado_en`, `expira_en`, `fin_ventana`, `cancelado_en`, `registrado_en`, `recibido_en`, `conciliado_hasta`), nunca con `default now()` (DP-10, RF-006). `ultima_consulta_pey` no se escribe (DP-12).
  - `registrar_pago`: una transacción con `insert into pagos … on conflict (transaccion_id) do nothing returning id` y, si trae `webhook_id`, `insert into avisos_webhook … on conflict do nothing`. Devuelve si el `insert` del pago devolvió fila.
  - Cada operación con `asyncio.wait_for(…, espera)`. Errores: `psycopg.DataError` y las violaciones de restricción que no son el `on conflict` → `ErrorDeDatos`; tiempo agotado, `OperationalError`, `InterfaceError`, `PoolTimeout` y cualquier otro `psycopg.Error` → `ErrorDeAlmacen`. Nunca se usa `str(error)`.
  - `responde()`: `select 1` con 2 s de espera (DP-31).
  - **RF**: RF-001 a RF-009, RF-020, RF-021, RF-022
  - **Dep.**: T055
  - **Hecho cuando**: las pruebas de T051 con `postgres` pasan (en el CI o con `PRUEBAS_DATABASE_URL`).
- [ ] T057 [US1] `RepositorioCobros` como caché de escritura directa en `backend/app/cobros.py` (DP-7, DP-8, DP-11, DP-13, DP-33)
  - El constructor recibe el almacén. `nuevo` sigue armando el `Cobro` en memoria; métodos asíncronos nuevos o cambiados: `guardar_nuevo(cobro, espera=2)`, `vincular_qr(…, espera=2)`, `descartar`, `obtener(id)` y `por_codi_qr(codi_qr_id)` (primero memoria, después almacén; si otra petición lo cargó mientras tanto, se usa el que ya está, sin `await` entre comprobar y guardar), `aviso_ya_visto` (memoria, después almacén), `marcar_aviso(webhook_id, tipo)`, `registrar_pago(…, webhook_id=None, tipo_aviso="")` y `cancelar`.
  - `registrar_pago` corre dentro de un `asyncio.Lock` por cobro: comprueba si la transacción ya está en `cobro.pagos`, calcula `numero = len(cobro.pagos) + 1`, guarda en el almacén y solo si el almacén dijo "nuevo" lo agrega a la memoria.
  - Se quita el conjunto global `vistas`; las transacciones de un cobro salen de sus pagos (DP-13).
  - Cada escritura va primero al almacén y después a la memoria; si el almacén falla, la memoria no cambia.
  - Conexión mínima para que la app no quede rota cuando los métodos pasan a ser asíncronos:
    - `backend/app/main.py`: `crear_app(config, cliente_pey, reloj, almacen=None, tareas_en_segundo_plano=True)`; sin almacén, `AlmacenEnMemoria`. Todavía sin `AlmacenPostgres`, sin respuestas 503 y sin ciclo de vida (eso es T060). Las rutas usan `await` con los métodos nuevos.
    - La fixture `app` de `backend/tests/conftest.py` pasa `almacen=AlmacenEnMemoria(reloj=reloj)` y `tareas_en_segundo_plano=False`.
    - Las pruebas que ya existían y llaman directo a `RepositorioCobros` (`backend/tests/test_modelo.py` y las demás) se ajustan aquí, solo con `await`, `async` o la fixture del almacén.
  - **RF**: RF-002, RF-005 a RF-008
  - **Dep.**: T055
  - **Hecho cuando**: las pruebas de T052 de numeración y carga a la vez pasan. Las que pasan por la consulta de respaldo (y la deduplicación aviso-consulta) pueden fallar hasta T058, porque `respaldo.py` todavía usa `vistas` y llamadas síncronas; T057 y T058 se hacen seguidas.
- [ ] T058 [US1] Consulta de respaldo con `await` y las transacciones del cobro en `backend/app/respaldo.py`
  - `registrar_y_avisar` pasa a `async`, publica el evento `pago` solo si el pago es nuevo y guardado (RF-002).
  - `consultar` pasa a `pagos_del_qr` las transacciones **de ese cobro** (DP-13). Si el almacén falla al registrar, deja la línea del contrato (operación `registrar pago`) y sigue; se reintenta en la próxima consulta (RF-016).
  - `backend/app/canal.py` solo cambia si hace falta un `await` nuevo.
  - **RF**: RF-002, RF-005, RF-007, RF-016
  - **Dep.**: T057
  - **Hecho cuando**: `test_tras_un_reinicio_la_consulta_de_respaldo_encuentra_el_pago`, `test_el_aviso_y_la_consulta_a_la_vez_registran_un_solo_pago` y las demás de deduplicación de T052 pasan, y todas las pruebas de la 001 siguen en verde (ajustadas solo con `await`, `async` o la fixture del almacén).
- [ ] T059 [US1] Lista de reintentos de avisos en `backend/app/tareas.py` (archivo nuevo, data-model §4)
  - `ReintentosDeAvisos`: diccionario por `webhook_id` con `codi_qr_id`, `transaccion_id`, `monto_recibido`, `pagado_en` e `intentos` (nada de `metadata`, RF-009). `agregar(...)` no duplica un `webhook_id` que ya está.
  - `una_vez()`: por cada aviso, busca el cobro (`por_codi_qr`), registra el pago con su `webhook_id` y, si es nuevo, lo emite por el canal como la consulta de respaldo; lo quita de la lista. Si el almacén falla, suma un intento y deja su línea. Si el cobro no existe, guarda el aviso como ignorado y lo quita.
  - `correr_tareas(reintentos, reloj, …)`: bucle que llama a `reintentos.una_vez()` y después `await reloj.dormir(15)` (DP-14). F6 le agrega el latido.
  - **RF**: RF-009, RF-014, RF-048
  - **Dep.**: T057
  - **Hecho cuando**: las dos pruebas de RF-048 de T053 pasan.
- [ ] T060 [US1] Usar el almacén en `backend/app/main.py`: creación, rutas, aviso, salud y ciclo de vida
  - `crear_app` (firma de T057): si no se da almacén, `AlmacenPostgres` con `config.database_url` o, sin ella, `AlmacenEnMemoria` con el `WARNING` "Sin DATABASE_URL: los cobros se guardan en memoria" (DP-16).
  - Ciclo de vida: `await almacen.abrir()`; si `tareas_en_segundo_plano`, crea la tarea de `correr_tareas` y la cancela al apagar; `await almacen.cerrar()`. El *pool* solo se abre aquí, nunca al crear la app (QT-8, CE-011).
  - `crear_cobro`: `guardar_nuevo` (falla → 503 sin llamar a pey); pey; si pey falla, `descartar` (si también falla, se registra y la respuesta de la 001 no cambia); `vincular_qr` (falla → 503 sin QR y el cobro sale de la memoria). Esperas de 2 s (DP-35).
  - `ver_cobro`, `eventos_cobro` y `cancelar_cobro`: cargan con `obtener`; `ErrorDeAlmacen` → 503 con los textos del contrato, nunca 404.
  - `webhook_pey`: después de la firma y de leer el JSON, un `amount` de 0 o negativo responde 400 sin marcar el `webhook-id` (DP-34). `aviso_ya_visto`, `por_codi_qr`, `registrar_pago` con el `webhook_id` y `marcar_aviso` con el `type` (vacío si no viene). `ErrorDeAlmacen` → 503 y, si el aviso trae un pago válido, a la lista de reintentos. `ErrorDeDatos` → se registra con la clase y responde 400, sin la lista.
  - `/salud`: `base_de_datos` = `"sin configurar"` si `almacen.configurado` es falso; si no, `"responde"` o `"no responde"`, guardado 10 s con el `Reloj` (DP-31).
  - Registros con el formato del [contrato](contracts/fallas-base-de-datos.md) §4.
  - **RF**: RF-001, RF-003 a RF-005, RF-012 a RF-016, RF-023, RF-048, RF-052
  - **Dep.**: T056, T058, T059
  - **Hecho cuando**: T052, T053 y T054 pasan.
- [ ] T061 [US1] Revisar el diff de las pruebas que ya existían en `backend/tests/` (ajustadas en T057 y T058)
  - `backend/tests/test_modelo.py` y las demás que llaman directo a `RepositorioCobros` o `ConsultaDeRespaldo`: el diff solo agrega `await`, `async` o la fixture del almacén. No se cambia ninguna comprobación de comportamiento (plan §7).
  - **RF**: — (CE-011)
  - **Dep.**: T060
  - **Hecho cuando**: las pruebas que ya existían pasan y la revisión del diff queda anotada en la sección F5 de la guía.
- [ ] T062 [P] [US1] Documentar `DATABASE_URL` en la tabla de variables de `backend/README.md` y en `backend/.env.example`
  - README: fila `DATABASE_URL` · "URL del *pooler* de Supabase en modo sesión. Sin ella, el servidor guarda en memoria y la salud dice `sin configurar`" · vacío.
  - `.env.example`: el comentario de `DATABASE_URL` dice lo mismo y "nunca en el repositorio".
  - **RF**: RF-020, RF-023
  - **Dep.**: T060
  - **Hecho cuando**: las dos líneas están y no se tocó nada más de esos archivos (C-6 toca otras líneas de `backend/README.md` en T064).
- [ ] T063 [US1] Revisar los registros y respuestas contra los datos de quien paga
  - `git grep -n "metadata" backend/app` solo muestra que no se leen (`pey.py`) y la lista de reintentos no los guarda.
  - **RF**: RF-009
  - **Dep.**: T060
  - **Hecho cuando**: la revisión queda anotada en la sección F5 de la guía.
- [ ] T064 [US1] Aplicar el cambio C-6 a la spec 001 (QP-11)
  - Las líneas citadas en C-6 (spec 003 §8.2) pudieron moverse: se busca el texto.
  - (a) `specs/001-backend-mvp/spec.md` §4, fila "Reinicio del servidor": se conservan (spec 003).
  - (b) §4, fila "Aviso de pago de un cobro desconocido": quitar "por ejemplo, tras reiniciar el servidor".
  - (c) RF-038 y `specs/001-backend-mvp/contracts/salud.md`: la salud también indica `base_de_datos` (RF-023 de la 003).
  - (d) §5, fila "Base de datos: los cobros se pierden al reiniciar": resuelto por la spec 003.
  - (e) `specs/001-backend-mvp/data-model.md` (línea 5, §5 y §6), `specs/001-backend-mvp/quickstart.md`, `specs/001-backend-mvp/contracts/ver-cobro.md` ("o se perdió al reiniciar") y `backend/README.md`: cobros, pagos y avisos se guardan; límites y canales siguen en memoria.
  - (f) `specs/001-backend-mvp/contracts/aviso-pey.md`: el manejador ya hace una llamada de red (guardar); la meta de menos de 1 s se mantiene.
  - (g) `specs/001-backend-mvp/contracts/aviso-pey.md`: la respuesta 400 y la fila de `amount` de la petición incluyen el `amount` de 0 o negativo, sin marcar el `webhook-id`.
  - (h) `specs/001-backend-mvp/quickstart.md` arranca sin `--host 0.0.0.0`, y `backend/README.md` dice que con el túnel `PROXIES_CONFIABLES` es `127.0.0.1`.
  - (i) §4, fila "Pago después de la ventana de escucha": la conciliación de la 003 (RF-061) consulta una vez a pey al terminar la ventana y registra lo que falte, sin canal.
  - En `specs/003-infraestructura-demo/spec.md` §8.2, la fila C-6 pasa a "… · **aplicado el AAAA-MM-DD** (F5)".
  - **RF**: RF-023, RF-061 (C-6)
  - **Dep.**: T060
  - **Hecho cuando**: `git grep -n "se perdió al reiniciar\|0.0.0.0" specs/001-backend-mvp backend/README.md` no encuentra nada vigente y la fila C-6 dice "aplicado".
- [ ] T065 [US1] Comprobar `git grep` de credenciales después de los cambios de F5
  - `git grep -nE "postgres(ql)?://[^ ]+:[^ ]+@" -- ':!backend/tests'` no encuentra nada, y en `backend/tests` solo valores falsos (`usuario-falso`, `clave-falsa`, `prueba`).
  - **RF**: RF-020, RF-021 (CE-010)
  - **Dep.**: T060
  - **Hecho cuando**: la búsqueda queda anotada en la sección F5 de la guía.
- [ ] T066 [US1] Comprobar en desarrollo el guardado y el reinicio
  - **Quién**: Hugo, con `backend/.env` (base de desarrollo y segunda llave), en el puerto 8001 si la demo está encendida.
  - `/salud` dice `"base_de_datos": "responde"`. Crear un cobro de $0.01 (QR real **sin pagar**, con su autorización), parar el servidor por su PID, arrancarlo y pedir `GET /api/cobros/<id>`: vuelve con su QR, su imagen y su tiempo restante.
  - **RF**: RF-001, RF-005, RF-010, RF-023
  - **Dep.**: T046, T048, T060
  - **Hecho cuando**: el resultado queda anotado en la sección F5 de la guía.
- [ ] T067 Cierre de F5: todo en verde, sección F5 en la guía de verificación y commit sugerido
  - Commit sugerido: `feat(003): guardar cobros, pagos y avisos en la base de datos, y C-6 (F5)`.
  - **RF**: RF-001 a RF-016, RF-020 a RF-023, RF-048, RF-052
  - **Dep.**: T061 a T066
  - **Hecho cuando**: todo en verde (regla 5), con el trabajo `base-de-datos` del CI en verde, y Hugo aprobó el cierre.

**Punto de control**: un cobro y sus pagos sobreviven a un reinicio, sin duplicados, en las pruebas y en desarrollo.

---

## Fase 6 (F6): Conciliación y demo con base de datos · 24–25 nov · corte 2

**Objetivo**: ningún pago se pierde aunque la demo esté apagada o el aviso se pierda en un reinicio (RF-061), la base de datos de la demo queda limpia y marcada, y Hugo enciende la demo con la guía completa (historias 1 y 4).

**Prueba independiente**: pruebas automáticas de conciliación con pey simulado (CE-017); quickstart §5 y §6 con dinero real (CE-001, CE-016).

### Pruebas de F6 (primero, deben fallar antes de implementar)

- [ ] T068 [US1] Pruebas de la conciliación en `backend/tests/test_conciliacion.py` (archivo nuevo)
  - `PeySimulado` (en `backend/tests/conftest.py`) aprende a responder por QR: un `codi_qr_id` distinto por cada cobro creado y, por cada uno, sus transacciones, un 4xx o una falla pasajera (5xx o sin conexión). Solo se agrega; lo que ya hace no cambia.
  - Con el almacén en memoria, `RelojFalso` y `LatidoDeConciliacion.una_vez()` llamado directo:
    - `test_la_primera_vez_no_se_revisa_hacia_atras`: sin fila en `estado_del_servidor`, se crea con la hora del `Reloj` y no se consulta a pey.
    - `test_al_arrancar_se_concilian_las_ventanas_que_terminaron_apagado`: un cobro pagado en pey mientras no había app; se avanza el `RelojFalso` más allá de `fin_ventana`, se arranca otra app con `reiniciar(app)` y el primer latido registra el pago una vez, con `fuente = consulta` y sin evento en el canal (RF-061, CE-017, historia 1, escenario 8).
    - `test_el_latido_registra_un_aviso_perdido_cuando_termina_la_ventana`.
    - `test_si_pey_falla_conciliado_hasta_no_avanza`: con una falla pasajera en el segundo de tres cobros, `conciliado_hasta` queda en la `fin_ventana` del primero y el siguiente latido empieza por el segundo.
    - `test_la_conciliacion_no_duplica_un_pago_ya_registrado` (RF-007).
    - `test_un_qr_que_pey_no_conoce_no_bloquea_la_conciliacion`: un 404 de pey se registra, el cobro se salta y `conciliado_hasta` avanza (QP-13).
    - `test_tras_10_fallas_el_cobro_se_salta_con_error`: 10 latidos con falla pasajera; en el décimo deja una línea `ERROR` con el id del cobro, lo salta y `conciliado_hasta` avanza (QP-13).
    - `test_el_latido_escribe_en_la_base_cada_minuto`: `correr_tareas` con `RelojPorPasos` (T050, QT-7); al soltar el reloj vuelta por vuelta, los reintentos corren cada 15 s y `conciliado_hasta` se escribe cada 60 s aunque no haya cobros (RF-039, RF-048).
    - `test_al_arrancar_se_corre_el_primer_latido`: con `RelojDetenido` y `tareas_en_segundo_plano=True`, al entrar al `TestClient` el latido corre una vez (RF-061).
    - `test_si_la_base_falla_en_el_latido_se_registra_y_se_reintenta`: con `cobros_con_ventana_terminada` en falla, línea con la operación `latido` y `conciliado_hasta` sin cambio (RF-016).
    - `test_cada_consulta_de_la_conciliacion_registra_el_requestid_de_pey`: con una respuesta correcta y con un 404 de pey, la línea de registro lleva el id del cobro y `requestId=r1` (el de `PeySimulado`), sin datos de quien paga (principio X, RF-009).
  - **RF**: RF-007, RF-009, RF-016, RF-039, RF-061
  - **Dep.**: T067
  - **Hecho cuando**: las pruebas existen y fallan porque `LatidoDeConciliacion` no existe.

### Implementación de F6

- [ ] T069 [US1] `LatidoDeConciliacion` en `backend/app/tareas.py` (data-model §4.1, DP-39, QP-13)
  - `una_vez()`: lee `conciliado_hasta` (si no hay, lo crea con la hora del `Reloj` y termina); toma los cobros con `fin_ventana` en (`conciliado_hasta`, ahora], en orden; por cada uno, lo carga (memoria o almacén, DP-33), pide a pey sus transacciones con las del cobro (DP-13) y registra cada una que falte con `fuente = consulta`, dentro del candado del cobro, **sin publicar en el canal** (RF-061).
  - 4xx de pey: línea con la operación `conciliar` y el id, y se salta. Falla pasajera de pey o del almacén: línea, contador en memoria por cobro y se para ahí (la marca queda en la `fin_ventana` anterior); con 10 fallas seguidas, línea `ERROR` y se salta.
  - Al final, `guardar_conciliado_hasta` con ahora (o la marca anterior al primer cobro que todavía se reintenta). Esta escritura es el uso diario de RF-039.
  - `correr_tareas`: corre el latido **al empezar** y después cada 60 s del `Reloj`, junto con los reintentos cada 15 s.
  - Línea de registro por cobro conciliado: `Conciliación cobro=<id> paginas=<n> pagos_nuevos=<n> requestId=<id de pey>`, igual que la consulta de respaldo (`backend/app/respaldo.py`); sin `requestId` si pey no lo manda. Con un 4xx o una falla pasajera de pey: `No se pudo conciliar el cobro <id> en pey (requestId=<id>)` (principio X, data-model §4.1). `pagos_del_qr` ya devuelve `request_id` y `ErrorPey` lo trae: no cambia `pey.py`.
  - **RF**: RF-039, RF-061
  - **Dep.**: T068
  - **Hecho cuando**: T068 pasa.
- [ ] T070 [US4] Completar `docs/operacion-demo.md` con la base de datos (DP-43, RF-050, RF-051, RF-058)
  - **Quién**: borrador de Grok; lo valida Hugo en T074.
  - **Antes de encender** (paso nuevo, antes de arrancar el servidor): exportar una copia de la base de la demo desde el panel de Supabase (cada tabla a CSV; el plan gratuito no tiene respaldos, RF-051), y después `uv run --env-file backend/.env.demo --directory backend python -m app.migraciones estado` y `aplicar` (QP-14). Sin `--env-file`, el comando usa la base de desarrollo.
  - **Comprobar desde fuera**: `/salud` debe decir `"base_de_datos": "responde"` (DP-16: después de T071, `"sin configurar"` en la demo es un error; antes de T071 es lo esperado, por la línea vacía de DP-44).
  - **Supabase pausado** (RF-050): cómo se ve (`"no responde"`), cómo reactivarlo en el panel y volver a pedir la salud. Encender al menos cada 5 días para que no se pause.
  - `DATABASE_URL` de la demo solo en `backend/.env.demo`.
  - **RF**: RF-050, RF-051, RF-058
  - **Dep.**: T069
  - **Hecho cuando**: la guía tiene esos pasos en el orden de RF-058 (código al día, cambios de estructura, servidor, túnel, comprobar).

### Base de la demo y pagos reales (Hugo)

- [ ] T071 [US4] Reemplazar la línea vacía `DATABASE_URL=` de `backend/.env.demo` por la de la demo y comprobar que es distinta de la de desarrollo
  - **Quién**: Hugo. URL del *pooler* en modo sesión del proyecto de la demo, en la misma línea que dejó vacía T002 (DP-44).
  - La comparación de T048 con `DATABASE_URL` dice `DISTINTAS`.
  - **RF**: RF-020, RF-049
  - **Dep.**: T070
  - **Hecho cuando**: el comando dice `DISTINTAS`.
- [ ] T072 [US6] Limpiar y marcar la base de la demo (quickstart §6, paso 2; historia 6, escenario 3)
  - **Quién**: Hugo, siguiendo la guía.
  - Exportar la copia; correr los `delete` del bloque F de `supabase/consultas_de_verificacion.sql` (datos de prueba del PR #97, H-12); `uv run --env-file backend/.env.demo --directory backend python -m app.migraciones aplicar --entorno demo --ya-aplicada 0001`.
  - **RF**: RF-018, RF-019, RF-051, RF-054
  - **Dep.**: T071
  - **Hecho cuando**: el comando anota 0001 sin correrla, aplica solo 0002 y 0003 sin borrar nada, y `estado` dice `demo`.
- [ ] T073 [US1] Pagos reales con la base de datos (quickstart §6, pasos 3 a 5)
  - **Quién**: Hugo, con su autorización en ese momento, con la demo encendida por la guía.
  - Paso 3 (CE-001): cobro en la demo, parar y arrancar el servidor, recargar la pantalla y pagar $0.01; vuelve el mismo QR con su tiempo restante y suena "Pago recibido".
  - Paso 4 (RF-061): cobro de $0.01, apagar el servidor, pagar, esperar a que termine la ventana (20 min) y encender; en el primer minuto el registro muestra la conciliación y `GET /api/cobros/<id>` lo da *pagado*, con un solo pago.
  - Paso 5 (RF-012, RF-015): con un servidor de desarrollo en el puerto 8001 y `DATABASE_URL=postgresql://nadie@127.0.0.1:1/x` en la línea de comando (valor falso, no un secreto), crear un cobro; mensaje para el dueño y el registro dice que no se llamó a pey.
  - Medir otra vez el QR con la base de datos: 10 cobros, 9 en menos de 3 s (CE-003, riesgo del plan §11). Si no se cumple, TK y decisión de Hugo (región del proyecto).
  - **RF**: RF-005, RF-012, RF-015, RF-061
  - **Dep.**: T072
  - **Hecho cuando**: los cuatro resultados quedan anotados en la sección F6 de la guía.
- [ ] T074 [US4] Encender la demo con la computadora recién prendida siguiendo solo la guía (quickstart §5, CE-016)
  - **Quién**: Hugo.
  - `/salud` por la dirección del túnel desde un celular con datos móviles.
  - **RF**: RF-023, RF-050, RF-058
  - **Dep.**: T072
  - **Hecho cuando**: dice `"llave_pey": true`, `"secreto_aviso_pey": true` y `"base_de_datos": "responde"`, sin pasos fuera de la guía (lo que faltó se agrega a `docs/operacion-demo.md`).
- [ ] T075 Cierre de F6: todo en verde, sección F6 en la guía de verificación y commit sugerido
  - Commit sugerido: `feat(003): conciliación de pagos y demo con base de datos (F6)`.
  - **RF**: RF-039, RF-050, RF-051, RF-058, RF-061
  - **Dep.**: T073, T074
  - **Hecho cuando**: todo en verde (regla 5) y la sección F6 tiene los resultados de T072 a T074.

**Punto de control (fin del corte 2)**: la demo guarda, concilia y se enciende con una sola guía.

---

## Fase N (FN): Cierre · 25 nov

- [ ] T076 Comprobar que C-6 y C-7 están aplicados (QP-11)
  - Las dos filas de la spec 003 §8.2 dicen "aplicado", y las búsquedas de T021 y T064 siguen limpias.
  - **RF**: RF-023, RF-029, RF-061
  - **Dep.**: T075
  - **Hecho cuando**: las dos comprobaciones quedan anotadas en la sección FN de la guía.
- [ ] T077 Revisión de seguridad (constitución, flujo 6; plan §10)
  - Secretos: `git grep -nE "(PEY_API_KEY|PEY_WEBHOOK_SECRET|DATABASE_URL)=.+"` solo encuentra valores vacíos o falsos de las pruebas; `ci.yml` sin `secrets.` (CE-010, RF-038).
  - Túnel: ninguna llave ni sesión de Tailscale en el repositorio (RF-059); `git grep -n "0.0.0.0" -- docs backend specs/003-infraestructura-demo` solo en textos que dicen no usarlo (RF-056).
  - Base de datos: RLS y `revoke` en todas las tablas, también las del comando y `estado_del_servidor` (T038, RF-022).
  - Aviso: firma verificada antes de tocar la base de datos; `amount` ≤ 0 rechazado (DP-34).
  - Demo pública: límites por IP real (DP-36 o DP-40), CORS con la dirección del túnel (RF-027) y CSP `connect-src 'self'` (RF-029).
  - Datos de quien paga: no se guardan ni se registran, tampoco en la conciliación (RF-009).
  - **RF**: RF-009, RF-020 a RF-022, RF-027, RF-029, RF-038, RF-056, RF-059
  - **Dep.**: T075
  - **Hecho cuando**: cada punto queda anotado como revisado en la sección FN de la guía.
- [ ] T078 Validar `quickstart.md` de punta a punta
  - Cada sección (§1 a §6) enlazada a su resultado en la guía de verificación; lo que no coincida se corrige en el quickstart o se anota como TK.
  - **RF**: todos (comprobación)
  - **Dep.**: T076, T077
  - **Hecho cuando**: cada sección del quickstart tiene su resultado anotado.
- [ ] T079 Cierre de FN: guía de verificación completa, PR del corte 2 y commit sugerido
  - Commit sugerido: `docs(003): cierre de la spec 003 y guía de verificación completa (FN)`.
  - PR con la plantilla, el enlace a `specs/003-infraestructura-demo/` y `Closes #90, #19, #94`. Lo une Hugo con el CI en verde; Juan y Leonel revisan después.
  - La descripción del PR lleva las comparativas que piden #19 y #94, en lugar de la nota de implementación (constitución 3.0.0; QT-5): librería de PostgreSQL (DP-2, research R-6), herramienta de migraciones (DP-3, R-7) y de dónde sale la imagen del QR (D-2 de la spec).
  - Estado de este archivo: "FN terminada (…, AAAA-MM-DD)".
  - **RF**: todos
  - **Dep.**: T078
  - **Hecho cuando**: todo en verde (regla 5), el PR está abierto con la plantilla y Hugo aprobó el cierre.

---

## Dependencias y orden de ejecución

```text
Corte 1:  F0 (Hugo) ─┐
          F1 (CI) ───┴→ F2 (demo por el túnel) → F3 (pago real)
Corte 2:  F4 (migraciones) → F5 (guardar) → F6 (conciliación y demo con base de datos) → FN
```

- **F0 y F1 van a la vez**: F0 es de Hugo y sin código; F1 es de Grok, en `feature/35-ci`. F2 necesita las dos.
- **F2 necesita** F1 unida a `main` (para que su PR pase por el CI), F0 en verde y la rama de la 003 al día con `main`.
- **F3 necesita** F2 y el aviso de pey dado de alta (T025).
- **El corte 2 no bloquea al corte 1** (DP-41): si F4 a F6 no llegan al 25 nov, lo que falte se anota y pasa a S2.
- **T045 (base de desarrollo de Juan) y T048 (segunda llave)** se pueden hacer antes de F4, en cuanto existan el proyecto y la llave.
- Dentro de cada fase, las tareas `[P]` se pueden hacer a la vez:
  - F2: T015 y T016 (pruebas); T019 en cuanto termina T017.
  - F3: T032 (README) mientras Hugo mide y paga.
  - F4: T035, T036 y T037.
  - F5: T050 primero; después T051, T052, T053 y T054 a la vez; T062 en cuanto termina T060.

## Estrategia

1. **MVP primero (corte 1)**: F0 → F1 → F2 → F3. Al terminar F3 la demo pública ya existe, con CI y pago real medido; los cobros siguen en memoria, como en la 001 (DP-41).
2. **Entrega incremental (corte 2)**: F4 deja el comando y el trabajo `base-de-datos` sin cambiar el servidor; F5 agrega el guardado con todas las pruebas de la 001 en verde; F6 agrega la conciliación y pasa la demo a la base de datos.
3. **Cada fase se puede demostrar sola** con su sección del quickstart y de la guía de verificación.

## Trazabilidad

| Requisito | Tareas |
|---|---|
| RF-001 | T051, T052, T055, T056, T060, T066 |
| RF-002 | T051, T052, T055, T056, T057, T058 |
| RF-003 | T051, T052, T055, T056, T060 |
| RF-004 | T051, T052, T053, T055, T056, T060 |
| RF-005 | T051, T052, T055, T056, T057, T058, T060, T066, T073 |
| RF-006 | T051, T052, T056, T057 |
| RF-007 | T031, T051, T052, T055, T056, T057, T058, T068 |
| RF-008 | T051, T052, T056, T057 |
| RF-009 | T052, T056, T059, T063, T068, T077 |
| RF-010 | T051, T052, T066 |
| RF-011 | T051, T052 |
| RF-012 | T053, T060, T073 |
| RF-013 | T053, T060 |
| RF-014 | T053, T059, T060 |
| RF-015 | T053, T060, T073 |
| RF-016 | T053, T058, T060, T068 |
| RF-017 | T034, T037, T038, T041, T046 |
| RF-018 | T038, T040, T041, T046, T072 |
| RF-019 | T038, T041, T046, T072 |
| RF-020 | T002, T036, T039, T045, T056, T062, T065, T071, T077 |
| RF-021 | T036, T037, T039, T041, T051, T053, T054, T056, T065, T077 |
| RF-022 | T038, T040, T056, T077 |
| RF-023 | T054, T060, T062, T064, T066, T074, T076 |
| RF-024 | T001, T003, T015, T017, T019, T020, T024, T026, T029, T031, T032 |
| RF-025 | T025, T030 |
| RF-026 | T004, T026, T030 |
| RF-027 | T002, T027, T077 |
| RF-028 | T005, T023, T026 |
| RF-029 | T015, T016, T017, T018, T020, T021, T076, T077 |
| RF-030 | T006, T025, T026 |
| RF-036 | T008, T009, T010, T012, T014, T042, T043 |
| RF-037 | T009, T013, T014, T044 |
| RF-038 | T008, T009, T011, T012, T014, T035, T042, T043, T077 |
| RF-039 | T068, T069 |
| RF-048 | T053, T059, T060 |
| RF-049 | T002, T038, T041, T045, T047, T048, T071 |
| RF-050 | T022, T070, T074 |
| RF-051 | T070, T072 |
| RF-052 | T051, T053, T060 |
| RF-053 | T002, T048 |
| RF-054 | T038, T040, T041, T046, T072 |
| RF-056 | T003, T022, T027, T077 |
| RF-057 | T004, T026, T030 |
| RF-058 | T022, T070, T074 |
| RF-059 | T001, T022, T077 |
| RF-060 | T022, T026, T032 |
| RF-061 | T040, T051, T055, T064, T068, T069, T073 |
| CE-001 | T073 |
| CE-002 | T030 |
| CE-003 | T029, T073 |
| CE-004 | T030 |
| CE-005 | T052 |
| CE-006 | T013, T014 |
| CE-007 | T038, T043, T046 |
| CE-010 | T053, T065, T077 |
| CE-011 | T035, T061 (todas las pruebas sin pey ni base de datos reales) |
| CE-015 | T027 |
| CE-016 | T074 |
| CE-017 | T068 |

## Revisión QA de tasks

**`/speckit-analyze` (2026-11-21).** Los 48 RF y los 12 CE tienen tarea. Salieron 12 hallazgos. Hugo aprobó aplicar los tres graves:

- **D1** (crítico, principio X): la conciliación no registraba el `requestId` de pey. Se agregó a T069 y a data-model §4.1, con su prueba en T068.
- **F1** (alto): la fixture de T050 y los métodos asíncronos de T057 dejaban rotas las pruebas de la 001 hasta T060. La fixture y la conexión mínima de `crear_app` pasan a T057; las pruebas existentes se ajustan en T057 y T058; T061 queda como revisión del diff.
- **U1** (alto, RF-049): sin la línea, `backend/.env.demo` tomaba la `DATABASE_URL` de desarrollo de `backend/.env`. T002 deja `DATABASE_URL=` vacía hasta T071 (DP-44 del plan), y T022, T070 y T071 lo explican.

Los otros nueve (D2, U2 a U5, I1 a I3 y C1) pasan a `/qa-spec 003 tasks`.

**`/qa-spec 003 tasks` (2026-11-21), una sola pasada.** Incluye los nueve hallazgos de `/speckit-analyze` que quedaron abiertos (D2, U2 a U5, I1 a I3 y C1) y los nuevos.

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QT-1 | Hueco | T012 marca `servidor` y `web` como obligatorios **antes** de unir el PR de F1 (T014). Desde ese momento, ningún PR abierto del equipo sin `ci.yml` se puede unir: GitHub espera trabajos que nunca corren. Después, cada rama abierta necesita traer `main` para tener `ci.yml`. | RF-037, CE-006 | Reordenar F1: unir el PR de F1 con el CI en verde, después marcar los trabajos como obligatorios y avisar a Juan, Miguel y Leonel que traigan `main` a sus ramas; al final, la prueba del error a propósito desde una rama nueva de `main`. | **Recomendada** (Hugo, 2026-11-21): unir, marcar los trabajos y avisar al equipo, y después la prueba del error. **Aplicada** el 2026-11-21 |
| QT-2 | Caso límite | T030 pide pagar "después del minuto 15 del canal" (CE-004), pero el QR vence en el minuto 10 (`EXPIRACION_SEGUNDOS=600`): la web lo oculta en *vencido* (spec 002) y no se sabe si el banco acepta un QR CoDi vencido. Tal como está, el paso puede no poder hacerse. pey no tiene máximo para `expiration` (`openapi.json`: "Minimum value when set is 360"). | CE-004, RF-026, RF-057 | Para ese único pago, arrancar la demo con `EXPIRACION_SEGUNDOS=1200` en la línea de comando (manda sobre `backend/.env.demo`): el QR sigue vigente y se paga en el minuto 16. Después se vuelve a arrancar normal. Se anota en la guía de verificación. | **Recomendada** (Hugo, 2026-11-21): `EXPIRACION_SEGUNDOS=1200` solo para ese pago. **Aplicada** el 2026-11-21 |
| QT-3 | Seguridad | Hugo es administrador y `enforce_admins` está apagado (comprobado el 2026-11-21): para él, un PR en rojo **sí** se puede unir, y CE-006 dice "no se puede unir". | RF-037, CE-006 | Activar `enforce_admins` al marcar los trabajos obligatorios, con su comando `gh api`. Desde la 3.0.0 ya no hace falta `--admin` para unir (0 aprobaciones). | **Recomendada** (Hugo, 2026-11-21): activar `enforce_admins`. **Aplicada** el 2026-11-21 |
| QT-4 | Seguridad | `StaticFiles` sobre `web/` (T017) entrega también `web/tests/*.py`, `web/pytest.ini`, `web/.pytest_cache/` y `web/.DS_Store`. El servidor simulado de la 002 excluye `tests/` a propósito (`web/tests/servidor_simulado.py:479-501`). No hay secretos (repositorio público), pero expone archivos que no son de la web. | RF-024, RF-029 | En T017, no entregar las rutas cuyo primer tramo sea `tests` ni las que empiecen con punto, ni `pytest.ini`, igual que el simulado; en T015, una prueba de que responden 404. | **Se acepta** (Hugo, 2026-11-21): repositorio público y sin secretos; queda como limitación aceptada y no cambia T017 |
| QT-5 | Hueco | Los issues que se cierran piden cosas sin tarea: #65 y #19, anotar el hosting y la base en `docs/plan-hackathon.md` (línea 114 dice "Supabase y AWS"); #19 y #94, la comparativa (DP-2, DP-3 y D-2), que con la constitución 3.0.0 va en la descripción del PR en lugar de la nota de implementación; #66, "cómo correrlo en local" y equipo y tecnologías en el `README.md` (hoy no están). | RF-024, RF-060 | Agregar a T028 la línea de `docs/plan-hackathon.md`; a T032, una sección corta del README con enlaces a `backend/README.md` y `web/README.md`, equipo y tecnologías; a T049 y T079, las comparativas en la descripción del PR. | **Recomendada** (Hugo, 2026-11-21): las tres. **Aplicada** el 2026-11-21 |
| QT-6 | Hueco | Ninguna tarea comprueba la historia 4, escenario 3 (la computadora se suspende o pierde internet con un cobro en pantalla y la pantalla se reconecta) ni el escenario 4 (con la demo apagada se ve el error del túnel). | Historia 4, RF-060 | Agregar dos pasos a T026: quitar el wifi de la Mac un minuto con un cobro en pantalla ("Reconectando…" y vuelve sola), y abrir el enlace con la demo apagada. | **Recomendada** (Hugo, 2026-11-21): dos pasos en T026. **Aplicada** el 2026-11-21 |
| QT-7 | Ambigüedad | `test_el_latido_escribe_en_la_base_cada_minuto` (T068) pide probar "con la tarea de fondo", pero con `RelojFalso.dormir` el bucle avanzaría el reloj sin parar (`backend/app/reloj.py:34`), y `RelojDetenido` solo sirve para una vuelta. | RF-039, RF-048 | Definir en T050 un `RelojPorPasos` cuyo `dormir` espera a que la prueba lo suelte (avanzando el reloj), y probar con él `correr_tareas`: reintentos cada 15 s y latido cada 60 s. | **Recomendada** (Hugo, 2026-11-21): `RelojPorPasos` en T050. **Aplicada** el 2026-11-21 |
| QT-8 | Caso límite | `main.py:330` arma la app al importarse, y las pruebas importan `app.main`. Si `AlmacenPostgres` abriera conexiones en su constructor, en una computadora con `DATABASE_URL` en `backend/.env` las pruebas tocarían la base real (CE-011). | CE-011, RF-020 | Escribir en T056 que el constructor no hace I/O y en T060 que el *pool* solo se abre en `abrir()`, dentro del ciclo de vida. | **Recomendada** (Hugo, 2026-11-21): escribirlo en T056 y T060. **Aplicada** el 2026-11-21 |
| QT-9 | Contradicción | El principio III dice credenciales "solo en `backend/.env` (en local) o en las variables del hosting", y la demo usa `backend/.env.demo` (QP-14, DP-44). La fila III del plan §2 dice "solo en `backend/.env`". Encaja si la Mac de la demo cuenta como el hosting, pero no está escrito. | RF-020, principio III | Escribir en la fila III del plan que la Mac de la demo es el hosting y `backend/.env.demo` son sus variables, sin cambiar la constitución. | **Recomendada** (Hugo, 2026-11-21): aclararlo en la fila III del plan, sin cambiar la constitución. **Aplicada** el 2026-11-21 |

**Erratas** (corregidas el 2026-11-21, con las decisiones):

1. Plan §7, fila RF-027: la prueba se llama `test_cors_solo_permite_los_origenes_configurados` (`backend/tests/test_proteccion.py:96`), no `test_cors_solo_acepta_el_origen_configurado`.
2. T021, «Hecho cuando»: `git grep 5173` también encuentra `specs/002-web-mvp/plan.md:323`, una fila histórica de la QA (QP-2). Hay que admitirla junto con las secciones con fecha.
3. T060: el aviso "Sin DATABASE_URL: los cobros se guardan en memoria" no está en ningún contrato; se agrega a `contracts/fallas-base-de-datos.md` §4.

**Lo que se comprobó en cada bloque:**

1. **Coherencia interna**: las 79 tareas tienen RF, dependencia y «Hecho cuando»; las pruebas van antes que su implementación; cada fase cierra con su tarea de cierre; el formato es correcto; todas las DP, QP, R, H y N citadas existen; siguiente C-n libre, C-10. `database_url` adelantada a F4 (T036) ya pide su TK. Salen QT-7, QT-9 y las erratas.
2. **Otras specs, issues y reglas**: los textos de C-6 y C-7 existen en las specs 001 y 002 y en `web/README.md`; los issues #35, #65, #66, #90, #19, #94, #27 y #64 leídos con `gh`; `docs/plan-hackathon.md` revisado; las reglas del hackathon (cobro real, producción, llave fuera del cliente) se cumplen con F3 y F6. Salen QT-1, QT-3, QT-5 y la errata 2.
3. **Código**: 109 pruebas del backend y 265 de la web en verde (32 saltadas, marcadas solo para Chromium); `config.py`, `main.py`, `reloj.py`, `respaldo.py`, `web/index.html`, `web/config.js` y el servidor simulado revisados. Salen QT-4, QT-7 y QT-8.
4. **API de pey**: `openapi.json` consultado. `expiration` no tiene máximo; `GET /transaction/codi/qr/{id}` responde 404 (sustenta QP-13); `pagos_del_qr` y `ErrorPey` ya traen `requestId` (D1). Sale QT-2.
5. **Dependencias externas**: cada una tiene dueño y estado en la tabla del principio; Tailscale, la llave de la demo y el aviso de pey siguen pendientes, de Hugo. Sin hallazgos nuevos.
6. **Casos límite**: pago tardío, aviso reenviado, aviso y consulta a la vez, QR desconocido, base sin respuesta, reinicio y demo apagada tienen tarea; el concepto "Prueba túnel" de T004 es válido. Salen QT-2 y QT-6.
7. **Seguridad**: secretos (reglas 8 y DP-44), firma antes de tocar la base, CORS, límites por IP real, CSP y CI sin secretos ni `pull_request_target`. Salen QT-3, QT-4 y QT-9.
8. **Construibilidad y reparto**: el corte 1 (F0 a F3) cabe en el 21 y 22 de noviembre solo si F0 y F1 van a la vez, como dice el orden; el reparto usa al equipo actual (Hugo, Juan, Miguel y Leonel; Grok implementa y Claude revisa). Sale QT-1.
