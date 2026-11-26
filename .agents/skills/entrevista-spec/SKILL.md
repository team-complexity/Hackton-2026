---
name: entrevista-spec
description: Entrevista de requisitos con Hugo para una spec de PAGO FÁCIL, una pregunta cada vez y con opciones. Úsala después de /speckit-specify (o cuando Hugo pida "la entrevista" de una spec, ej. «/entrevista-spec 001») para convertir el borrador en una spec acordada, con requisitos EARS y la tabla E-n.
---

# Entrevista de una spec (PAGO FÁCIL)

Argumento: el número de la spec (ej. `001`). Si no se da, usa la de `.specify/feature.json`.

Convierte un borrador en una especificación acordada. La spec es el contrato: lo que no está en ella no se construye.

## Lugar en el flujo

`/speckit-specify` (borrador) → **`/entrevista-spec`** → `/speckit-clarify` (opcional) → `/qa-spec NNN` → aprobación → `/speckit-plan` → …

Aprobar un paso no autoriza el siguiente: al terminar, se espera a que Hugo lo pida.

## Proceso

1. **Lee el contexto antes de preguntar.**
   - `AGENTS.md` y `.specify/memory/constitution.md`. Si chocan con esta skill, mandan ellos.
   - Las specs previas de `specs/`, para no contradecir lo ya acordado.
   - `docs/plan-hackathon.md`, el issue o issues de la spec (`gh issue view <n>`) y el borrador actual de `spec.md`.
2. **Prepara la lista de dudas.**
   - Prioriza las que **cambian lo que hay que construir**. Descarta las que tienen una respuesta obvia por defecto: esas se escriben como supuesto en §7 de la spec.
   - Cubre siempre casos límite, comportamiento ante errores y qué queda fuera.
   - En cobros, la constitución exige responder: pagos tardíos, montos distintos, fallas de pey o del webhook, devoluciones y QR vencido.
   - Di cuántas preguntas hay en total antes de empezar.
3. **Pregunta de UNA en UNA** con `AskUserQuestion`.
   - Una pregunta por llamada, numerada («3 de 9»), y espera la respuesta antes de seguir.
   - La opción recomendada va primera, con «(Recomendada)» al final.
   - El contexto va en las descripciones de las opciones: qué implica cada una y qué cambia en lo que se construye.
   - Todo en español, aunque el sistema esté en inglés.
   - Hugo usa «Other» para matices: esa respuesta manda sobre las opciones.
   - Si una respuesta abre una duda nueva que cambia lo que se construye, agrégala a la lista y actualiza el total.
4. **Solo el QUÉ, nunca el CÓMO.** Si Hugo pregunta «¿cómo lo harías?», redirige a qué debe pasar y deja la técnica para el plan.
5. **Registra y aplica.**
   - Cada respuesta va como fila E-n en §8.1 de la spec (`| # | Duda | Decisión | Requisitos |`), con la fecha de la entrevista.
   - Después se reescriben los RF, los casos límite (§4), el fuera de alcance (§5) y los criterios de éxito (§6) afectados.
6. **Marca lo que no sepas** con `[NECESITA ACLARACIÓN: pregunta concreta]`. Nunca rellenes un hueco inventando: un hueco visible es información; una suposición silenciosa es deuda.
7. **Cierra.**
   - Pon el Estado de la spec en «En QA».
   - Resume a Hugo las decisiones (E-1…E-n) y lo que queda pendiente.
   - No lances la QA, el plan ni el código hasta que Hugo lo pida.

## Reglas de redacción

- La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas, los algoritmos y las firmas de funciones: eso va en `plan.md` y en `contracts/`.
- La sección «Fuera de alcance» es obligatoria. Es la que evita que la funcionalidad crezca sola.
- **Un requisito, una frase.** Si necesitas un «y» para unir dos comportamientos, son dos requisitos.
- **Sin adjetivos no medibles.** «Rápido», «intuitivo» o «robusto» no son requisitos: escribe el umbral o no lo escribas.
- Cada requisito debe ser verificable. Si no se te ocurre cómo comprobarlo, está mal escrito.
- Numeración: `RF-001`, `RF-002`… y `CE-001`… (la plantilla explica su equivalencia con FR y SC de spec-kit).

## Notación EARS

Cinco patrones. Elige el que corresponda y no los mezcles:

| Patrón | Forma | Cuándo |
|---|---|---|
| Ubicuo | EL SISTEMA \<hará\> | siempre es cierto |
| Dirigido por evento | CUANDO \<disparador\>, EL SISTEMA \<hará\> | responde a algo |
| Estado | MIENTRAS \<estado\>, EL SISTEMA \<hará\> | durante una condición |
| Opcional | DONDE \<característica\>, EL SISTEMA \<hará\> | solo si está presente |
| No deseado | SI \<condición\>, ENTONCES EL SISTEMA \<hará\> | errores y casos límite |

Bien escrito:

> **RF-012** (No deseado): SI llega un aviso de pago cuya firma no es válida, ENTONCES EL SISTEMA lo rechazará sin cambiar el estado de ningún cobro.

Mal escrito, para contrastar:

> ~~RF-012: El sistema debe manejar bien los webhooks y ser seguro.~~
> No usa ningún patrón EARS, no tiene criterio verificable, junta dos ideas y usa adjetivos no medibles.

## Si Hugo pide revisar en vez de entrevistar

No reescribas: **detecta y lista**, numerado, en cuatro bloques:

1. ambigüedades;
2. contradicciones entre requisitos;
3. casos límite no cubiertos;
4. conflictos con la constitución.

No propongas soluciones hasta que te las pida. Para una revisión completa antes de aprobar, usa `/qa-spec`.
