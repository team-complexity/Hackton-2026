# Constitución de PAGO FÁCIL

La constitución es la **regla común del equipo**, para las personas y para sus agentes de IA. Está en:

**[`.specify/memory/constitution.md`](.specify/memory/constitution.md)** (versión 3.0.1)

Vive en esa carpeta porque ahí la lee spec-kit: los comandos `/speckit-plan` y `/speckit-analyze` revisan cada plan contra sus principios. Este archivo solo apunta a ella para que se encuentre desde la raíz del repositorio.

## Si trabajas con un agente de IA

Pídele que lea la constitución antes de escribir código. Las guías personales de agentes (`AGENTS.md`, `CLAUDE.md`) no están en el repositorio: cada quien puede tener la suya en su computadora, y la de Hugo se le pide a él.

## Lo que más importa

- El pago solo se confirma en el servidor, y cada pago se procesa una sola vez.
- Las llaves y los secretos nunca salen del backend. Ni la web ni las apps hablan con pey.
- Se hace solo lo que pide el issue, y el commit y el pull request cuentan bien lo que se hizo, con la [plantilla de pull request](.github/pull_request_template.md).
- Cada quien decide cómo construye sus issues y si hace spec, plan y tareas.
- Cada quien une su propio pull request. Juan y Leonel revisan lo que entra a `main` y avisan si algo salió mal.
- Nadie es indispensable: si el responsable de una tarea no puede, otra persona la toma y lo deja anotado en el issue.
- Prioridad: la web de cobro, después las apps Android e iOS, y al final lo Premium.

## Cómo se cambia

Con un pull request que Hugo propone o aprueba, que explica el motivo y del que se avisa al equipo; Juan o Leonel pueden hacer observaciones. El detalle está en la sección "Gobierno" de la constitución.

Los roles, el calendario y el reparto de issues están en [`flujo-de-trabajo.md`](flujo-de-trabajo.md).
