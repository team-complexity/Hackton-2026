---
name: qa-spec
description: Revisión QA de una spec, un plan o un tasks de PAGO FÁCIL en UNA sola pasada y a fondo, contra las otras specs, el código, la documentación del API de pey y las reglas del hackathon, antes de aprobarlo. Úsala cuando Hugo pida la QA (ej. «/qa-spec 001», «/qa-spec 001 plan», «/qa-spec 001 tasks»).
---

# QA en una sola pasada (PAGO FÁCIL)

Argumentos: el número de la spec (ej. `001`) y, opcionalmente, el documento: `spec`, `plan` o `tasks`. Por defecto es `spec`.

| Documento | Tabla de hallazgos | Sección donde va |
|---|---|---|
| `spec` | QA-n | §8.4 de `spec.md` |
| `plan` | QP-n | §9.3 de `plan.md` |
| `tasks` | QT-n | «Revisión QA de tasks» de `tasks.md` |

## Por qué existe

Cuando la QA sale por rondas, Hugo pasa horas decidiendo. Así ocurrió en otro proyecto: una pasada miró otras specs y la siguiente, al mirar el código, encontró hallazgos nuevos. Con la entrega del hackathon encima, no hay tiempo para rondas.

**Regla:** todo lo que se pueda encontrar se encuentra en ESTA pasada. Después no se abren rondas nuevas de preguntas sobre el mismo documento. Lo que aparezca más tarde se resuelve como decisión del plan (DP-n) o como registro de implementación (TK-n), salvo que algo sea imposible de construir.

## Reglas que no se rompen

- Lee `AGENTS.md` y `.specify/memory/constitution.md`. Si chocan con esta skill, mandan ellos.
- Git solo en lectura: `git status`, `git diff`, `git log` y `git show`.
- **Nunca se crean cobros reales** con el API de pey durante la QA. Si un hallazgo solo se puede confirmar con uno, se propone una prueba de $0.01 y Hugo decide.
- La API key y el secreto del webhook nunca se leen, se imprimen ni se citan. Para saber si están configurados, se usa `GET /salud` o se comprueba si la variable está vacía, sin mostrarla.
- La QA solo detecta y recomienda. No cambia requisitos ni otras specs: decide Hugo, una por una.

## La pasada (todo, de una vez)

Relee el documento entero, del título a los criterios de finalización o aprobación. Si revisas el plan o el tasks, relee también la spec, porque el plan responde a ella y el tasks a los dos.

Después recorre cada bloque. Si un bloque no aplica, anótalo en el informe con su motivo: no lo saltes en silencio.

### 1. Coherencia interna

- Cada término del glosario se usa con el mismo sentido en los RF, los casos límite, los criterios de éxito, el plan y las tareas.
- Cada caso límite da el resultado que dicen sus RF. Busca casos que contradigan un RF.
- Cada criterio de éxito se puede comprobar y no contradice ningún RF.
- No quedan restos de decisiones sustituidas: busca los términos de lo retirado.
- Numeración:
  - RF, CE, E, P, C, QA y DP citados que no existen;
  - el siguiente `C-n` libre se calcula con `grep -rho 'C-[0-9]\+' specs | sort -t- -k2 -n | tail -1`.
- **En `plan`:** cada RF tiene una pieza, un contrato o una prueba en la estrategia de pruebas. La verificación de la constitución está completa y no quedan `[NECESITA ACLARACIÓN]`.
- **En `tasks`:**
  - cada RF aparece en la trazabilidad;
  - cada tarea cita RF y tiene «Hecho cuando»;
  - las pruebas van antes que su implementación;
  - cada fase termina con su cierre;
  - el formato `- [ ] T001 [P] [US1] …` es correcto;
  - las rutas de archivo existen o el plan las crea.

### 2. Otras specs, el plan del hackathon y las reglas

- Cada RF de otra spec que se cita existe y dice lo que se le atribuye: `grep -n '\*\*RF-0' specs/*/spec.md`.
- Para cada cambio C-n: ¿qué RF, casos, criterios o fuera de alcance de la spec afectada dicen lo contrario y no están en el C-n?
- Choques con `docs/plan-hackathon.md`: fechas, requisitos obligatorios, criterios de evaluación y milestones.
- Choques con las reglas del hackathon:
  - al menos un cobro CoDi real con pey y reacción a su resultado;
  - funcionar en producción;
  - API key nunca en el cliente ni en un repo público;
  - no revender el acceso al API.
- Choques con los issues de GitHub de la spec (`gh issue view <n>`): criterios de aceptación que la spec no cubre o contradice.

### 3. Código (solo lectura)

- Lo que el documento da por hecho existe en `backend/` o `web/`: rutas, módulos, configuración y pruebas. Cita archivo y línea.
- Lo que el prototipo ya hace distinto de lo que dice el documento: cada diferencia es un hallazgo que Hugo decide (cambiar la spec o cambiar el código).
- Si algo es nuevo, ¿hay un RF que diga quién lo dispara, cuándo y con qué resultado?
- Corre las pruebas existentes (`uv run --directory backend pytest -q`) para saber de qué punto se parte.

### 4. API de pey

Fuentes:
- `https://docs.pey.mx/openapi.json`;
- las páginas de `docs.pey.mx` (en español sin `/en/`, en inglés con `/en/`);
- el índice `https://docs.pey.mx/llms.txt`.

Qué se revisa:
- Cada campo, código de respuesta, límite y evento que el documento usa existe tal cual en el API. Ejemplos:
  - `expiration` es 0 o al menos 360;
  - `numRef` tiene hasta 7 dígitos;
  - `codiQrId` en el webhook es el `id` del QR;
  - una API key admite un solo webhook.
- Lo que el documento promete y pey no ofrece. Ejemplo: devoluciones, que no tienen endpoint.
- Lo que pey ofrece y el documento ignora pero cambia el diseño. Ejemplo: `GET /transaction/codi/qr/{id}` como respaldo del webhook, o `metadata` que vuelve en el webhook.

### 5. Fuentes y dependencias externas

- Cada dependencia externa tiene un dueño y un estado:
  - CoDi activado en el banco con que se prueba;
  - API key y webhook configurados en el portal de pey;
  - hosting con HTTPS.
- ¿Qué muestra el sistema cuando pey falla, está en mantenimiento o el webhook no llega?

### 6. Ambigüedades y casos límite

- **Por cada RF:** valor vacío, cero, uno solo, el máximo, un dato que llega tarde, un dato repetido, un dato que cambia y un valor no válido.
- **En cobros:**
  - pago tardío;
  - monto distinto al pedido;
  - pago repetido;
  - webhook de un cobro desconocido o reenviado;
  - QR vencido;
  - devoluciones;
  - reinicio del servidor.
- **Por cada pantalla:**
  - carga, error, vacío y sin conexión;
  - celular de 320 px y zoom al 200 %;
  - lector de pantalla;
  - sonido bloqueado por el navegador;
  - el aviso de que la cámara normal no sirve: hay que usar la app del banco, en CoDi.

### 7. Seguridad y rendimiento

- **Secretos:** solo en `.env` o en el hosting; nunca en respuestas, logs, issues ni capturas.
- **Webhooks:** firma Standard Webhooks verificada, rechazo sin cambiar datos y deduplicación por `webhook-id` y `transactionId`.
- **Entradas:** validadas en el servidor, con montos y textos acotados.
- **Demo pública:** límite por IP, CORS restringido y nada que permita generar cobros sin límite.
- **Tiempos:** con una referencia medible. Ejemplos: QR en menos de 3 s y aviso en menos de 2 s.

### 8. Construibilidad y reparto

- Promesas imposibles con el API de pey, con el tiempo o con el equipo.
- **Fechas:** entrega del kickoff el 15 nov a la 1:00 PM; cierre el 12 dic a las 23:59.
- **Dependencias entre fases y personas:** web sin backend, webhook sin URL pública, prueba de pago sin CoDi activo.
- **Reparto del equipo:** Profesor, Altairtm, Miguel, Hugo.

## Cómo trabajar

- Si el documento toca muchas fuentes, reparte los bloques 2 y 4 entre subagentes. Cada uno recibe la lista cerrada de comprobaciones de su bloque y devuelve hallazgos con su cita (archivo y línea, o URL de la documentación).
- Comprueba cada hallazgo de un subagente antes de presentarlo: cita exacta y consulta repetida.
- Agrupa los hallazgos que se resuelven con la misma decisión. No presentes dos veces el mismo problema.

## Informe

Una tabla en la sección de QA del documento, con numeración que sigue la existente:

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|

- **Tipo**: Contradicción, Hueco, Ambigüedad, Promesa imposible, Caso límite, API de pey, Seguridad o Errata.
- **Hallazgo**: con su prueba (cita, consulta, URL o número).
- **Recomendación**: una sola y concreta. Si exige un C-n, di a qué spec y RF.
- Debajo de la tabla, una línea por bloque con lo que se comprobó, para que se vea que no se saltó ninguno.
- Las erratas sin efecto en el comportamiento no se preguntan: se listan y se corrigen cuando Hugo lo pida.

## Decisiones con Hugo

- Antes de la primera pregunta, di cuántas decisiones hay en total y numéralas («3 de 7»).
- Pregunta con `AskUserQuestion`, una pregunta cada vez, con la opción recomendada primero y el contexto en las descripciones, en español.
- Si una decisión cambia otra spec, el C-n se aprueba aparte y queda «Aprobado · sin aplicar» hasta que Hugo pida aplicarlo.
- Al terminar, registra cada decisión en la tabla. Aplícalas a la redacción solo si Hugo lo pide.

## Cierre

- La QA termina cuando todos los hallazgos están decididos.
- Aprobar el documento solo cambia su Estado. No autoriza el paso siguiente: se espera a que Hugo lo pida.
- Lo nuevo que aparezca después se resuelve como DP-n en el plan o TK-n en el registro de implementación, no como una ronda nueva de preguntas.
