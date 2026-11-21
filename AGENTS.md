# AGENTS.md — PAGO FÁCIL

Instrucciones para cualquier agente de IA que trabaje en este repositorio (Claude, Codex, Gemini u otro). Es el resumen operativo de la constitución, [`.specify/memory/constitution.md`](.specify/memory/constitution.md): si algo de aquí choca con ella, manda la constitución. Si la constitución choca con las [reglas del hackathon](https://hackatonmexico.com/reglas), mandan las reglas.

---

## 1. Antes de escribir código

1. **Nada de código sin spec, plan y tasks aprobados** (`specs/NNN-<nombre>/`).
   - Aprobar un paso no autoriza el siguiente: después de una aprobación solo cambia el Estado del documento, y se espera a que Hugo pida el paso que sigue.
2. **Solo se hace la tarea pedida**, en el orden de `tasks.md` y respetando sus dependencias. Nada de funciones sorpresa, retoques cosméticos ni refactorizaciones que la tarea no pida.
3. **Ante una duda, se pregunta.** Nunca se rellena un hueco suponiendo: se para y se consulta a Hugo con opciones (`AskUserQuestion`, una pregunta cada vez, la recomendada primero).
4. **Si el código obliga a cambiar algo**, se actualizan la spec y el plan en el momento, en el *Registro de implementación* del plan.
   - Un cambio a una spec ya aprobada se presenta como cambio `C-n`. Hugo lo aprueba por separado y solo se aplica cuando él lo pide.
5. **Librerías o herramientas nuevas**: se presenta una comparativa (opción A frente a B, ventajas, desventajas, curva de aprendizaje y recomendación). Decide Hugo.

## 2. Flujo de specs (spec-kit + estilo del equipo)

| Paso | Comando | Resultado |
|---|---|---|
| Constitución | `/speckit-constitution` | `.specify/memory/constitution.md` |
| Borrador de spec | `/speckit-specify <descripción>` | `specs/NNN-nombre/spec.md` |
| Entrevista | `/entrevista-spec NNN` | Tabla E-n y requisitos EARS |
| Aclaraciones (opcional) | `/speckit-clarify` | Huecos menores resueltos |
| QA de la spec | `/qa-spec NNN` | Tabla QA-n, decidida una a una → spec **Aprobada** |
| Plan y contratos | `/speckit-plan <stack y restricciones>` | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` |
| QA del plan | `/qa-spec NNN plan` | Tabla QP-n → plan **Aprobado** |
| Tareas | `/speckit-tasks`, después `/speckit-analyze` | `tasks.md` |
| QA de tareas | `/qa-spec NNN tasks` | Tabla QT-n → tasks **Aprobado** |
| Implementación | `/speckit-implement` por fases, después `/speckit-converge` | Código, pruebas y `verification-guide.md` |

- Las plantillas en español están en `.specify/templates/overrides/`. No edites las de `.specify/templates/`: spec-kit las regenera.
- Las specs, los planes y las tareas usan `RF-###` (requisito funcional, en EARS), `CE-###` (criterio de éxito) y `[NECESITA ACLARACIÓN: …]`.
- Las QA son de **una sola pasada**. Lo que aparezca después se resuelve como `DP-n` (decisión del plan) o `TK-n` (registro de implementación), no como una ronda nueva de preguntas.
- Spec-kit está instalado **sin** su extensión git: no crea ramas. La carpeta de la spec se elige con `--number` y `--short-name`.

## 3. Git

- **Solo lectura**: `git status`, `git diff`, `git log` y `git show`.
- **Prohibido** cualquier comando que cambie el repositorio: `git add`, `git commit`, `git push`, `git checkout`, `git switch`, `git branch`, `git rm`, `git reset` o `git stash`. Para borrar un archivo se usa `rm`.
- Si un agente cambia el índice o el historial por error, no lo deshace: avisa a Hugo en el acto con el comando exacto que ejecutó.
- Al terminar una tarea o fase se sugiere el mensaje de commit. Lo ejecuta Hugo, que también hace el push y el pull request.
- **Formato del mensaje**: `tipo(NNN): descripción en español`, con `feat`, `fix`, `docs`, `style`, `test` o `refactor` y el número de la spec como ámbito. Ejemplo: `feat(001): crear cobro CoDi con pey (F3)`.
- **Ramas del equipo**: una por issue, `feature/<número>-<descripcion>`; los pull requests llevan `Closes #<número>`. Ver [docs/flujo-git-y-secretos.md](docs/flujo-git-y-secretos.md).

## 4. Idioma

Todo va en **español** (decisión de Hugo del 2026-11-14, constitución v1.0.0):

- **Nombres del código**: variables, funciones, clases, módulos, archivos, rutas del API y campos JSON. Ejemplos: `crear_cobro`, `RepositorioCobros`, `/api/cobros`, `monto`.
  - Excepción: los nombres que imponen las librerías, los protocolos o pey se dejan como son. Ejemplos: `lifespan`, `codiQrId`, `webhook-id`.
- **Comentarios, docstrings, specs, planes, guías, mensajes de commit, mensajes para el usuario y explicaciones al equipo.**
- **Nombres de pruebas**, como el comportamiento que comprueban. Ejemplo: `def test_un_webhook_sin_firma_se_rechaza`.

## 5. Estilo de código (backend)

- Python 3.11 o superior, sangría de 4 espacios y anotaciones de tipo en todas las funciones.
- Formato y lint con `ruff`, configurado en `backend/pyproject.toml` (líneas de 100 caracteres). No se reformatea código que la tarea no toque.
- Cada función o clase pública lleva un docstring en español con los requisitos que cubre, por ejemplo `(spec 001, RF-007)`.
- Dentro del código, solo comentarios que explican un porqué que no se ve: una regla de la spec, una decisión del plan o un fallo que se evita. Nunca comentarios que repiten la línea ni código comentado.
- Dependencias con `uv`; nunca `pip install` suelto.

## 6. Pruebas

- **Pruebas primero en todo, backend y web** (principio V de la constitución, no negociable): se escriben, se ven fallar y después se implementa.
- **Ninguna prueba automática llama al pey real** ni espera tiempo real: pey simulado (`httpx.MockTransport`) y reloj controlado.
- **Pruebas con dinero real**: solo de $0.01, solo con cuentas propias o las CLABEs de prueba de pey, y solo con la autorización de Hugo en ese momento.

| Qué | Comando (desde la raíz) |
|---|---|
| Pruebas del backend | `uv run --directory backend pytest -q` |
| Lint | `uv run --directory backend ruff check .` |
| Formato | `uv run --directory backend ruff format --check .` |
| Pruebas de la web | `uv run --directory backend pytest ../web -q` (la primera vez, `uv run --directory backend playwright install chromium webkit`) |
| Lint y formato de las pruebas de la web | `uv run --directory backend ruff check --config pyproject.toml ../web` y `uv run --directory backend ruff format --config pyproject.toml --check ../web` |
| Conexión real con pey | `cd backend && uv run python scripts/probar_pey.py --esperar` |

Una fase no se cierra sin tres cosas: todo en verde, su sección en `verification-guide.md` para Hugo y el mensaje de commit sugerido.

## 7. Procesos, datos y seguridad

- **Procesos**: se paran solo por su PID exacto, nunca con `pkill` o `killall` por nombre.
- **Secretos**: `PEY_API_KEY` y `PEY_WEBHOOK_SECRET` solo viven en `backend/.env` o en el hosting. Nunca se leen en voz alta, se imprimen, se citan ni se pegan en chats, issues o pull requests. Para saber si están configurados, se usa `GET /salud`.
- **Datos personales**: en pruebas, solo datos propios o ficticios; nunca CLABEs ni teléfonos de terceros.
- **Seguridad del API**:
  - entradas validadas en el servidor;
  - webhooks con firma verificada;
  - CORS restringido al dominio de la web;
  - límite de peticiones en la demo pública.
- El detalle está en [docs/flujo-git-y-secretos.md](docs/flujo-git-y-secretos.md).
