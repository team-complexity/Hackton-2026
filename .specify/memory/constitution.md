# Constitución de PAGO FÁCIL

PAGO FÁCIL es un punto de venta para comerciantes de México que todavía no cobran con dinero digital (tienditas, puestos, ferreterías, tortillerías). Cobra con **CoDi**, sin comisión. El negocio escribe el monto. El cliente escanea el QR desde **la app de su banco**. El negocio oye y ve "Pago recibido" en segundos. Usamos el API de pey como integración, y PAGO FÁCIL **no revende** el acceso a ese API.

Esta constitución es la regla común del repositorio, para las personas del equipo y para sus agentes de IA. Manda sobre specs, planes, tareas, código y cualquier guía personal. Si choca con las [reglas oficiales del hackathon](https://hackatonmexico.com/reglas), mandan las reglas.

## Principios fundamentales

### I. El pago se confirma en el servidor (NO NEGOCIABLE)

- Un cobro solo DEBE pasar a *pagado* por una de dos fuentes:
  - un webhook de pey con firma Standard Webhooks válida;
  - una consulta directa del backend al API de pey.
- Nada que venga del navegador, de una app, de una captura de pantalla o del cliente PUEDE marcar un cobro como pagado.
- Un webhook sin firma válida DEBE rechazarse sin cambiar ningún dato.

*Por qué:* la demo es pública. Sin esta regla, cualquiera podría hacer sonar la pantalla del negocio por dinero que nunca llegó.

### II. Una orden nunca se ejecuta dos veces (NO NEGOCIABLE)

- Cada pago DEBE procesarse una sola vez, aunque pey reenvíe el webhook o la consulta de respaldo lo vuelva a encontrar.
- La deduplicación DEBE usar el `transactionId` de pey. El `webhook-id` sirve como primera barrera.
- Toda acción que dispare un pago (sonido, aviso, cupón, inventario) DEBE colgar de esa única transición de *pendiente* a *pagado*.

### III. Los secretos nunca salen del backend (NO NEGOCIABLE)

- `PEY_API_KEY`, `PEY_WEBHOOK_SECRET` y cualquier otra credencial solo PUEDEN vivir en `backend/.env` (en local) o en las variables del hosting.
- NUNCA PUEDEN aparecer en código, commits, issues, pull requests, logs, respuestas del API, capturas ni chats.
- Ni la web ni las apps (Android e iOS) llaman a pey directamente, y ninguna lleva credenciales dentro. Todo pasa por el backend.
- Quien revisa desde fuera del equipo trabaja sobre el repositorio público y NUNCA recibe llaves ni secretos.
- Si una llave se filtra, se rota y se avisa a pey en menos de 24 horas, como indica `docs/flujo-git-y-secretos.md`.

### IV. Alcance anclado y trabajo documentado (NO NEGOCIABLE)

Para todo el equipo:

- **Solo lo pedido.** Se hace lo que pide el issue. Nada de funciones sorpresa, retoques cosméticos ni refactorizaciones no pedidas.
- **Nunca suponer.** Ante una duda o un caso límite sin definir, la persona o su agente se detiene y pregunta.
- **Commit y pull request documentados.** Cada commit dice qué cambió. La descripción de cada pull request DEBE seguir la plantilla `.github/pull_request_template.md` y contar qué pedía el issue, qué se hizo, qué se decidió y por qué, cómo probarlo, qué quedó pendiente y la revisión de seguridad. No hay otro documento aparte.
- **Cómo construirlo lo decide su dueño.** Cada integrante elige su forma de trabajo para sus issues.

Flujo de specs (spec → plan → tareas, con spec-kit):

- **Cada quien decide** si hace spec, plan y tareas para lo que implementa. Spec-kit está instalado en el repositorio para quien quiera usarlo. Hugo lo usa en lo suyo.
- Quien abre una carpeta en `specs/` cumple ahí lo siguiente:
  - el código de esa spec no se escribe sin `spec.md`, `plan.md` y `tasks.md` aprobados por su dueño en `specs/NNN-<nombre>/`;
  - aprobar un paso no autoriza el siguiente: el siguiente empieza cuando el dueño de la spec lo decide;
  - se hacen solo las tareas de `tasks.md`, en su orden;
  - si el código obliga a cambiar algo, la spec y el plan se actualizan en el momento, en el registro de implementación del plan;
  - un cambio a una spec aprobada se presenta como `C-n` y su dueño lo aprueba por separado.
- Quien trabaja con specs puede enlazar su carpeta de `specs/` desde el pull request en vez de repetir su contenido.

*Por qué:* cuatro personas trabajan de cuatro formas en un mismo repositorio. El pull request documentado es lo que permite a los demás saber qué se hizo sin leer todo el código.

### V. Pruebas primero, en todo (NO NEGOCIABLE)

- En el backend y en la web, cada comportamiento DEBE tener su prueba escrita y vista fallar **antes** de implementarse.
- Las pruebas automáticas NUNCA llaman al pey real ni dependen del reloj real. Usan un pey simulado y un reloj controlado.
- Las pruebas con dinero real son de **$0.01 MXN**. Solo se hacen con cuentas propias o con las CLABEs de prueba que entregó pey, y con la autorización de Hugo en ese momento.
- Los nombres de las pruebas se escriben en español, como el comportamiento que comprueban.
- Una fase no se cierra sin tres cosas: todas las pruebas en verde, su guía de verificación manual y el mensaje de commit sugerido.

### VI. CoDi real, reacción real

- Toda funcionalidad de cobro DEBE demostrarse con un **cobro CoDi real** creado con el API de pey en producción.
- También DEBE demostrarse la **reacción visible del sistema al resultado** de ese cobro.
- Las reglas del hackathon no aceptan simularlo.

### VII. Pensado para el mostrador

- Cada pantalla (web, Android o iOS) y cada respuesta del API se diseña para un negocio pequeño, con un celular y sin capacitación: monto grande, QR grande, sonido claro.
- **Rapidez.** Con pey funcionando normal, el QR DEBE estar en pantalla en menos de 3 segundos después de pedirlo, y el aviso de pago DEBE llegar en menos de 3 segundos después de que pey lo confirma.
- El cliente paga **desde la app de su banco, en la opción CoDi**. La cámara normal del teléfono no paga el QR, así que la interfaz SIEMPRE lo indica.
- Todo lo que el usuario toca responde al instante, con estado de carga, de error y de éxito.
- La interfaz funciona desde 320 px de ancho.
- Los mensajes de error se escriben para el dueño del negocio, no para un programador.

### VIII. Un pago no prueba identidad ni entrega

- "Pagado" significa que el dinero llegó a la cuenta. No identifica al cliente ni confirma la entrega.
- Toda spec con cobros DEBE definir qué pasa con:
  - los **pagos tardíos** (después de vencer el QR);
  - los **montos distintos** al pedido;
  - las **fallas** de pey o del webhook;
  - las **devoluciones**.
- El sistema NUNCA pierde un pago. Si llega dinero de un cobro conocido, se registra aunque llegue tarde o sea por otro monto, y se avisa.

### IX. Lo más simple que gane la demo

- Primero se construye el recorrido completo más corto (cobro → QR → pago → aviso). Los extras vienen después.
- **Orden de prioridad:** la web de cobro, después las apps Android e iOS, y al final lo Premium (pago con NFC, chatbot e integración con WhatsApp). Los jueces evalúan el enlace web. Lo Premium solo empieza cuando el núcleo ya funciona en la demo pública.
- **Regla de corte.** Si el 29 de noviembre de 2026 una app todavía no crea un cobro y muestra su QR, deja de crecer: se entrega como está y su dueño vuelve a la web o a QA.
- No se agrega una pieza (base de datos, cola, framework de frontend, servicio externo) hasta que un issue o una spec la justifique.
- Una librería o herramienta nueva requiere una comparativa escrita: opción A frente a B, ventajas, desventajas, curva de aprendizaje y recomendación. Decide el dueño del área (Hugo en el backend y en la web de cobro) y la comparativa queda en la descripción del pull request.
- Cada limitación aceptada se escribe, con el issue que la resolverá.

### X. Si no se ve, no existe

- Cada interacción con pey y cada webhook DEBE dejar un registro (log) con el identificador del cobro y el `requestId` de pey.
- Ese registro NUNCA incluye secretos ni datos bancarios.
- `GET /salud` indica si el backend tiene configuradas sus credenciales, sin mostrar sus valores.
- Antes de culpar a pey, se revisan el historial de webhooks de su portal y nuestros logs.

## Equipo y responsabilidades

| Persona | Cuenta de GitHub | Responsabilidades | Respaldo |
|---|---|---|---|
| Hugo | `HugoAI23` | Producto (requisitos e historias de usuario), backend, integraciones (pey, WhatsApp, chatbot), la demo por túnel, CI, coordinación de la seguridad y la web de cobro | Leonel, en el backend y la web |
| Leonel | `mendiolaleonel2002-debug` | Arquitectura (observaciones de cambios sobre lo implementado), revisión de lo que se une a `main`, front de la web (base PWA, notificaciones y pantallas) y pruebas de la demo por túnel para los jueces | Miguel en el front, Hugo en la revisión |
| Juan | `Altairtm` | Pruebas QA y revisión de lo que se une a `main`, bases de datos (Supabase y MongoDB) y la app iOS | Leonel en la revisión, Miguel en QA |
| Miguel | `Beer17` | Pantallas de la web y UI/UX, landing page, guías QA y la app Android | Leonel en las pantallas, Juan en las guías QA |

- **Unir.** Cada quien une su propio pull request cuando el CI está en verde y revisó su diff buscando llaves, `.env` o datos personales. No hace falta aprobación previa.
- **Revisión después de unir.** Juan y Leonel revisan lo que entra a `main`. Si algo salió mal, lo hacen ver con un comentario en el pull request o con un issue `tipo: bug` para su dueño. Si rompe la demo, se corrige o se revierte con otro pull request.
- **Arquitectura.** Leonel no aprueba planes antes de construir. Se implementa y él hace observaciones de cambios; el dueño decide cómo atenderlas.
- **QA.** Miguel escribe la guía QA de cada funcionalidad con pantalla, en `docs/qa/`. Juan la ejecuta en cada ronda de QA y reporta los errores como issues.
- **Seguridad.** La revisión de seguridad la hacen un agente de IA y Leonel sobre lo que se une a `main`. Hugo la coordina y reparte los arreglos.
- **Suplencia.** Ningún trabajo depende de una sola persona. Si el responsable no puede, cualquier integrante (de preferencia su respaldo) toma la tarea o la pasa a otra persona, sin pedir la aprobación de nadie. Basta con dejar en el issue que se hizo el cambio y reasignarlo; no hace falta explicar la causa.
  - Las llaves no viajan con la tarea. Las da Hugo, como titular, al integrante que las necesite (los cuatro están inscritos en el hackathon; regla 8.1).
- **Demo para los jueces.** Leonel prueba la demo pública por el túnel HTTPS desde fuera de la red del equipo, con otros dispositivos y redes, como la verían los jueces. La prueba se hace antes de cada puerta semanal y durante la evaluación (12 al 14 de diciembre), y cada falla se avisa a Hugo en el momento. Para esas pruebas no necesita llaves.
- **Calendario.** El desarrollo termina el 10 de diciembre de 2026. El 11 y el 12 solo se aceptan correcciones. El detalle de fechas, entregables e issues está en `flujo-de-trabajo.md`.

## Restricciones técnicas e idioma

| Tema | Decisión |
|---|---|
| Backend | Python 3.11+, FastAPI, `httpx`, `pydantic-settings`, `standardwebhooks` |
| Herramientas del backend | `uv` para dependencias, `ruff` para formato y lint, `pytest` para pruebas |
| Web de cobro | PWA con HTML, CSS y JavaScript, sin framework, pensada primero para celular |
| Landing page | Por definir por Miguel (propuesta: React, Tailwind y Lovable) |
| App Android | A cargo de Miguel. Tecnología por definir por él |
| App iOS | A cargo de Juan. Tecnología por definir por él |
| Demo evaluada | El enlace web. Las apps se entregan como instalables y en el video |
| Tiempo real | Server-Sent Events, con consulta del estado como respaldo |
| API de pey | `https://api.pey.mx`, autenticación `Bearer`, montos en MXN. No hay ambiente de pruebas: se prueba en producción con $0.01 |
| Base de datos | Supabase (PostgreSQL). MongoDB solo entra si Juan justifica su uso |
| Hosting | La computadora de la demo, con un túnel HTTPS de dirección fija (Tailscale Funnel, spec 003). AWS queda como plan B (#34) |
| Imagen del QR | La que entrega pey, guardada con el cobro en Supabase (#94, spec 003) |
| Editores y agentes | Libres (Antigravity, Claude u otros). Todo agente lee esta constitución antes de escribir código |
| Specs | spec-kit (`specify` 1.4.0) con plantillas en español en `.specify/templates/overrides/` |

**Idioma** (decisión de Hugo del 2026-11-14):

- **Nombres del código en español**: variables, funciones, clases, módulos, archivos, rutas del API y campos JSON. Ejemplos: `crear_cobro`, `RepositorioCobros`, `/api/cobros`, `monto`.
- Los nombres que imponen las librerías, los protocolos, las plataformas o pey se dejan como son. Ejemplos: `lifespan`, `codiQrId`, `webhook-id`.
- **También en español**: comentarios, docstrings, nombres de pruebas, specs, planes, guías, descripciones de pull requests, mensajes de commit, mensajes para el usuario y explicaciones al equipo.

## Flujo de desarrollo y calidad

1. **Flujo de cada issue**, igual para todo el equipo:

   ```text
   tomar el issue → rama feature/<número>-<descripcion> → construir
   → guía QA (si hay pantalla) → commit y pull request documentados
   con "Closes #<número>" → CI en verde → el autor lo une a main
   → revisión de Juan y Leonel (observaciones o issue de bug si algo salió mal)
   ```

2. **Flujo de specs.** Es el de Hugo, y opcional para todos (principio IV). Cada paso se aprueba antes de pasar al siguiente:

   ```text
   /speckit-specify → /entrevista-spec → (/speckit-clarify) → /qa-spec NNN
   → /speckit-plan → /qa-spec NNN plan → /speckit-tasks → /speckit-analyze
   → /qa-spec NNN tasks → /speckit-implement por fases → /speckit-converge
   ```

   - Las preguntas de entrevistas y QA se hacen una por una, con opciones y la recomendada primero.
   - Cada QA es de **una sola pasada**. Lo que aparezca después se resuelve como `DP-n` (decisión del plan) o `TK-n` (registro de implementación), no como una ronda nueva de preguntas.
   - Los requisitos se escriben en notación EARS (`RF-###`), con criterios de éxito medibles (`CE-###`) y la sección "Fuera de alcance" obligatoria.
3. **Ramas y pull requests.** Una rama por issue y un pull request documentado que une su autor, como indica `docs/flujo-git-y-secretos.md`. El mensaje de commit lleva el formato `tipo(ámbito): descripción en español`.
4. **Git y agentes de IA.** Cada persona decide qué puede hacer su agente con git y responde por ello. Los agentes de Hugo trabajan en solo lectura (`git status`, `git diff`, `git log` y `git show`): sugieren el mensaje de commit, y Hugo hace el commit, el push y el pull request.
5. **Rol del agente: mentoría breve.** El agente explica en pocas líneas el porqué de cada decisión técnica y deja lo necesario para que otra persona pueda comprobar el trabajo.
6. **Seguridad antes de cerrar.** Se revisan:
   - que los secretos estén fuera del repo, de la web y de las apps;
   - la firma de los webhooks;
   - la validación de entradas en el servidor;
   - CORS y el límite de peticiones de la demo pública.
7. **Calendario.** Desde el 11 de diciembre de 2026 solo entran correcciones (`fix`) y documentación (`docs`). Ninguna función nueva.

## Gobierno

- **Prioridad.** Esta constitución manda sobre cualquier otra práctica del proyecto, incluidas las guías personales de agentes (`AGENTS.md`, `CLAUDE.md` u otras), que no forman parte del repositorio.
- **Aprobaciones.** Cada dueño decide en lo suyo: aprueba sus specs, planes y tareas si los hace, y decide los hallazgos de sus entrevistas y QA. Leonel hace observaciones de arquitectura sobre lo implementado.
- **Enmiendas.** La constitución solo cambia por un **pull request** que cumpla tres condiciones:
  - Hugo lo propone o lo aprueba;
  - explica el motivo del cambio;
  - se avisa al equipo, y Juan o Leonel pueden hacer observaciones.
  - Los principios marcados como NO NEGOCIABLE solo cambian si cambian las reglas del hackathon, las condiciones del API de pey o la composición del equipo.
- **Versionado semántico.**
  - Versión **mayor**: se retira o se redefine un principio.
  - Versión **menor**: se agrega un principio o una sección, o se amplía de forma importante.
  - **Parche**: cambios de redacción.
- **Cumplimiento.**
  - Cada revisión de un pull request comprueba esta constitución y que su descripción siga la plantilla, no solo que el código funcione.
  - Quien trabaja con specs llena en cada plan su verificación de la constitución (*Constitution Check*) antes y después del diseño, y justifica toda excepción en el seguimiento de complejidad (*Complexity Tracking*).

**Versión**: 3.0.1 | **Ratificada**: 2026-11-14 | **Última enmienda**: 2026-11-20
