# PAGO FÁCIL — Flujo de construcción de la app

**Hackatón México 2026** · Repositorio `team-complexity/Hackton-2026` · Versión del 20 de noviembre de 2026 · **Estado: Propuesta** (la aprueba Hugo)

Este documento dice **qué vamos a construir, quién lo hace, en qué orden y cómo se trabaja cada pieza** desde hoy hasta la entrega del 12 de diciembre. Suma al equipo al profesor Leonel Mendiola y ordena las 11 funciones que pidió Hugo el 19 de noviembre, más una propuesta (F-12).

Cuando se apruebe, sustituye el reparto y el calendario de `flujo-de-trabajo.md` (PR #96, versión del 15 de noviembre). Las reglas comunes siguen en la [constitución](../.specify/memory/constitution.md) y en [AGENTS.md](../AGENTS.md): si este documento choca con ellas, mandan ellas. Si ellas chocan con las [reglas del hackathon](https://hackatonmexico.com/reglas), mandan las reglas.

---

## 1. Lo esencial en una página

- **Somos cuatro:** Hugo, Leonel, Juan y Miguel. Leonel entra como **integrante oficial** y ya está inscrito en el portal del hackathon (regla 4.3).
- **Trabajo flexible:** cada quien une su propio pull request, Juan y Leonel revisan lo unido, y si alguien no puede con una tarea, otra persona la toma (2.4).
- **Quedan tres semanas de desarrollo:** del viernes 20 de noviembre al **jueves 10 de diciembre**. El 11 y el 12 son solo para ajustes. La entrega cierra el **sábado 12 de diciembre a las 23:59**, sin prórroga.
- **Construimos 12 funciones** (sección 3) sobre un solo servidor y tres pantallas: la web de cobro, la app Android y la app iOS.
- **Todo cobro pasa por el API de pey.** Nada se marca como pagado sin el aviso firmado de pey o una consulta del backend.
- **El orden manda:** primero el núcleo (cobrar rápido y enterarse siempre del pago), después cobrar a distancia y fidelizar, y al final lo deseable. Cada domingo hay una **puerta**. Si no se cumple, se corta según la sección 6.4.

| Persona | GitHub | Rol en una línea |
|---|---|---|
| **Hugo** | `HugoAI23` | Producto y coordinación, backend e integraciones (pey, WhatsApp y asistente) |
| **Leonel** | `mendiolaleonel2002-debug` | Arquitectura por observaciones, revisión de lo unido, front (PWA, notificaciones y pantallas) y pruebas de la demo por túnel para los jueces |
| **Juan** | `Altairtm` | Base de datos, QA y unión de pull requests, cupones y cuentas, app iOS |
| **Miguel** | `Beer17` | UI/UX y pantallas de la web, guías QA, landing y app Android |

| Puerta | Fecha | Qué tiene que funcionar en la demo pública |
|---|---|---|
| S1 | dom 22 nov | Un cobro real de $0.01 desde la URL pública por el túnel y el CI en verde. Los datos en Supabase llegan el miércoles 25 (spec 003, corte 2) |
| S2 | dom 29 nov | Cobrar con la calculadora y la duración elegida. El pago suena y llega como notificación aunque la web esté en segundo plano. Cada app crea un cobro y muestra su QR |
| S3 | dom 6 dic | **Funciones congeladas.** Cobro a distancia, asistente, cupones, cuentas y entregas se enseñan con cobros reales |
| S4 | jue 10 dic | Postulación enviada con los cuatro integrantes. Video, textos y revisión de seguridad listos |

---

## 2. Equipo y roles

### 2.1 Quién hace qué

| Persona | Responsable de | Entregables que se repiten |
|---|---|---|
| **Hugo** | **Producto:** prioriza, escribe y aprueba las specs. **Backend** (FastAPI) e **integraciones**: pey, WhatsApp y el servicio de IA. Trámites con pey. Demo pública. Entregables del hackathon (descripción, video y postulación) | Cada spec lista antes de que empiece su etapa. Planeación de los lunes y demo de los domingos |
| **Leonel** | **Arquitectura:** hace observaciones de cambios sobre lo implementado, no aprueba planes antes de construir. **Revisión de lo que se une a `main`**, junto con Juan. **Front:** la base de la web instalable (PWA), las notificaciones de pago, la calculadora y la vista del repartidor. **Pruebas de la demo por túnel:** la abre desde fuera de nuestra red, con otros celulares y redes, como la verán los jueces. Revisión de seguridad final | Revisión de arquitectura de los miércoles. Revisión de lo unido en menos de 24 h. Prueba de la demo por túnel antes de cada demo del domingo (N-17) |
| **Juan** | **Base de datos** (Supabase): tablas, permisos y migraciones de cada función. **QA:** ejecuta las guías en celulares reales y, con Leonel, revisa lo que se une a `main`. Funciones de **cupones** y **varias cuentas**. **App iOS** | Una ronda de QA por etapa. Tablas listas antes de construir cada función |
| **Miguel** | **UI/UX:** mockups, identidad visual, sonido y animación. **Pantallas** de la web para cada función nueva. Guía QA de cada pantalla. Landing. **App Android** | Mockup antes de construir cada pantalla. Guía QA en `docs/qa/` |

**Las dos apps se mantienen.** Antes de escribir código, Juan y Miguel deciden juntos **cómo se desarrollan para los dos sistemas** (una sola base de código o dos), con comparativa escrita y revisión de Leonel (issue nuevo N-05).

### 2.2 Qué cambia respecto al 15 de noviembre

| Persona | Antes (`flujo-de-trabajo.md`) | Ahora |
|---|---|---|
| Leonel | No era integrante: revisor externo de seguridad, sin llaves | **Integrante oficial, ya inscrito en el portal del hackathon:** arquitectura por observaciones, revisión de lo unido, front y pruebas de la demo por túnel para los jueces. Para probar el túnel no necesita llaves. Si las necesita, por ejemplo para correr el backend de la demo, se las da Hugo (regla 8.1) |
| Hugo | Producto, backend, integraciones, AWS, CI, seguridad y web de cobro | Igual, con la demo por túnel (spec 003) en lugar de AWS. Une sus propios pull requests. Deja los logs (#45) a Juan; la demo encendida del 12 al 14 de diciembre (#57) sigue con él, en su computadora (spec 003, QA-13) |
| Juan | Revisaba y unía todos los pull requests. BD, QA y app iOS | Hace QA y, con Leonel, revisa lo que se une a `main`. Ya no une los pull requests de los demás: cada quien une el suyo. Suma cupones (F-09), varias cuentas (F-11) y #45 |
| Miguel | Frontend web, UI/UX, landing, guías QA y app Android | Igual, centrado en diseño y pantallas. La PWA base (#22) pasa a Leonel |

### 2.3 Cómo entra Leonel (primeras 72 horas)

1. Ya está inscrito en el portal del hackathon y es colaborador del repositorio. Falta que Hugo lo sume en pey.build (#12), si no se ha hecho.
2. Lee la constitución, `AGENTS.md`, el `README.md`, `docs/flujo-git-y-secretos.md` y las specs 001 (backend), 002 (web, PR #72) y 003 (infraestructura, rama `feature/90-infraestructura-demo`).
3. Corre el backend, la web y sus pruebas en local (Anexo A). Para el front no necesita llaves: las pruebas de la web usan un servidor simulado.
4. Hace observaciones al PR #72 (web del MVP) y al PR #96 (roles y constitución).
5. Entrega la revisión de arquitectura de las specs 001 a 003 (N-03) y la propuesta de arquitectura del front (N-04).
6. Acuerda con Hugo sus horas por semana y su horario de revisión.

### 2.4 Cómo se une y se revisa

- **Cada quien une su propio pull request** cuando el CI está en verde y revisó su diff buscando llaves, `.env` o datos personales. No hace falta aprobación previa. Hugo quita en GitHub la aprobación obligatoria de `main`.
- **Juan y Leonel revisan lo que entra a `main`** en menos de 24 horas. Si algo salió mal, lo hacen ver con un comentario en el pull request o con un issue `tipo: bug` para su dueño. Si rompe la demo, se corrige o se revierte con otro pull request.
- **Arquitectura:** Leonel no aprueba planes antes de construir. Se implementa y él hace observaciones de cambios; el dueño decide cómo atenderlas.
- **QA:** Juan ejecuta las guías en celulares reales; las piezas de Juan las prueba Miguel.
- **Seguridad:** la revisión final (#52, #95) la hacen Leonel y un agente de IA. Hugo la coordina y reparte los arreglos.

**Respaldos.** Ningún trabajo depende de una sola persona. Si el responsable no puede, cualquier integrante, de preferencia su respaldo, toma la tarea o la pasa a otra persona, sin pedir la aprobación de nadie. Basta con dejar en el issue que se hizo el cambio y reasignarlo; no hace falta explicar la causa. Las llaves no viajan con la tarea: si hacen falta, las da Hugo.

| Responsable | Respaldo |
|---|---|
| Hugo (backend, integraciones y web) | Leonel |
| Leonel (front y revisión) | Miguel en el front, Hugo en la revisión |
| Juan (QA, revisión, base de datos e iOS) | Leonel en la revisión, Miguel en QA |
| Miguel (pantallas, guías QA y Android) | Leonel en las pantallas, Juan en las guías QA |

### 2.5 Cómo trabaja cada quien

- **Spec opcional.** Cada quien decide si hace spec, plan y tareas para lo que implementa. Hugo la usa en lo suyo. Las specs previstas (4.3) son una propuesta: su dueño decide si las escribe.
- **Commit y pull request documentados**, para todos. La descripción del pull request sigue la plantilla `.github/pull_request_template.md`. No hay nota de implementación aparte.
- **Pruebas primero** en el backend y en la web (principio V). Las apps definen sus pruebas en la decisión de stack (N-05).
- **Agentes de IA libres** (regla 9.3: no hay que declararlos). Todo agente lee la constitución antes de escribir código. En las specs de Hugo, las fases las implementa Grok y las revisa Claude; después Juan y Leonel revisan lo unido.

---

## 3. Las funciones

### 3.1 Mapa

Prioridad: **Núcleo** (no se corta), **Importante** (entra si se cumplen las puertas) y **Deseable** (lo primero que se corta). Los `N-xx` son issues nuevos por crear (sección 7.1).

| F | Función | ¿Ya existía? | Issues | Prioridad | Dueño | Etapa |
|---|---|---|---|---|---|---|
| F-01 | Asistente que ayuda a cobrar (chatbot en la web) | Sí, con otro alcance | #92, #93 | Importante | Hugo | S3 |
| F-02 | Cobrar por WhatsApp | Sí | #36, #46, #47, #48 | Importante | Hugo | S2–S3 |
| F-03 | Calculadora que arma la cuenta y genera el cobro | Sí | #100 | Núcleo | Leonel | S2 |
| F-04 | Elegir la duración del QR | No | N-06 | Núcleo | Hugo | S2 |
| F-05 | Sonido de pago aunque el QR ya no esté en pantalla | En parte (spec 002) | N-07, N-08 | Núcleo | Leonel | S2 |
| F-06 | Aviso de pago con forma de notificación | En parte | #32, #33, N-07, N-08 | Núcleo | Leonel | S2 |
| F-07 | UI/UX sencilla e inmediata | Sí | #20, #21, #31, #32, #33, #41, #42, #43 | Núcleo | Miguel | S1–S4 |
| F-08 | Todo cobro con el API de pey | Regla del proyecto | Todos | Núcleo | Hugo | Siempre |
| F-09 | Cupones por pagar con QR | En parte (canje, #37) | #37, #40, N-13, N-14 | Importante | Juan | S3 |
| F-10 | Cobro en entregas a domicilio (repartidores) | No | N-15, N-16 | Importante (versión mínima) | Leonel | S3 |
| F-11 | Varias cuentas para recibir pagos (demo) | No | N-10, N-11, N-12 | Importante | Juan | S1 (trámite) y S3 |
| F-12 | Bocina de cobro: el pago se anuncia en voz alta (**propuesta**) | No | N-09 | Deseable | Leonel | S2 |

### 3.2 Ficha de cada función

**F-01 · Asistente que ayuda a cobrar.** Hugo (backend, #92) · Miguel (pantalla, #93) · spec 007

- El dueño escribe "cobra 3 tacos de 25 y un refresco de 20". El asistente arma la cuenta, enseña el total y, cuando el dueño confirma, crea el cobro CoDi. También contesta "¿cuánto vendí hoy?".
- Cambia el alcance de #92 y #93, que solo contestaban preguntas.
- La IA solo interpreta: **el total lo calcula el backend** en centavos enteros y nada se cobra sin confirmación. La llave de la IA vive solo en el backend.
- Usa el mismo motor que F-02. Para las preguntas de ventas depende del historial (#38).
- Por decidir en la spec 007: el proveedor de IA, con comparativa. Antes se revisan los bounties (#51).
- Suma en: originalidad y experiencia.

**F-02 · Cobrar por WhatsApp.** Hugo (#36, #46–#48) · spec 007

- El dueño le escribe al bot "cobra 150 tacos" y recibe el QR, o el bot le manda al cliente un enlace de pago o un cobro push CoDi a su celular (#36). Cuando pey confirma, el bot avisa "Te pagaron $150".
- Mismo motor que F-01: WhatsApp es otro canal.
- Trámites largos: app de Meta, número de prueba y plantilla aprobada para "Te pagaron" (#48). El número de prueba solo escribe a unos cuantos números verificados; en pruebas, solo teléfonos propios.
- Suma en: uso de CoDi y pey (QR, enlaces y push) y originalidad.

**F-03 · Calculadora.** Leonel (comportamiento) · Miguel (diseño) · spec 004

- Tecla `+` (y `×`, por decidir) en el teclado de cobro. Cobrar usa el total con las reglas de un monto normal: mínimo, máximo y dos decimales. El detalle está en #100.
- Solo cambia la pantalla: el backend sigue recibiendo un monto final.
- Entra en los requisitos de las apps (#76).
- Suma en: experiencia e impacto.

**F-04 · Elegir la duración del QR.** Hugo (backend) · Leonel (selector) · spec 004

- Hoy todo QR dura 10 minutos (spec 001, RF-006), y la spec 001 dejó esto como "issue por crear". El dueño elige la duración antes de cobrar.
- Es un cambio `C-n` a las specs 001 y 002. La entrevista define las opciones y si entra un QR sin vencimiento para imprimir en el mostrador. Antes se verifican los límites de `expiration` en docs.pey.mx.
- Un QR largo deja la pantalla escuchando mucho tiempo: por eso F-05 y F-06 van en la misma etapa.
- Suma en: uso de CoDi y experiencia.

**F-05 · Sonido de pago aunque el QR ya no esté en pantalla.** Leonel (web) · Hugo (backend) · spec 005

- Ya está en parte: la spec 002 (PR #72) sigue escuchando los cobros anteriores y suena aunque el QR ya no se vea, **mientras la página esté abierta**.
- Falta que suene con la web en segundo plano, con la pantalla bloqueada o con la página cerrada. Eso se logra con la notificación de F-06, en la web instalada y en las apps.
- Límite conocido: en iPhone, la web solo recibe notificaciones si está instalada en la pantalla de inicio (iOS 16.4 o posterior). Las instrucciones de prueba (#55) lo dirán.
- Suma en: experiencia (el "momento del pago").

**F-06 · Aviso con forma de notificación de pago.** Miguel (diseño, #33) · Leonel (web) · Hugo (envío) · spec 005

- El pago llega como la notificación de la app del banco: "PAGO FÁCIL · Recibiste $150.00 · Tacos · 12:41". La entrevista de la spec 005 precisa si es un aviso dentro de la app, una notificación del sistema o ambos.
- La notificación sale **solo** del backend y solo de la transición de pendiente a pagado (principios I y II). Nunca la dispara la pantalla.
- Pieza nueva: notificaciones push, con sus llaves en `backend/.env` y una librería para enviarlas (comparativa, principio IX).
- Suma en: experiencia.

**F-07 · UI/UX sencilla e inmediata.** Miguel · revisa Leonel

- Meta medible: del monto al QR con un solo toque de Cobrar, el QR en pantalla en menos de 3 segundos (9 de cada 10 veces, como pide la spec 003) y un dueño sin capacitación cobra a la primera, sin ayuda (se mide en #43).
- Cubre mockups (#20), identidad (#21), pantalla de cobro (#31, #32), sonido y animación (#33), estados (#41), accesibilidad (#42) y pruebas con negocios reales (#43, #50).
- Suma en: experiencia e impacto.

**F-08 · Todo cobro con el API de pey.** Hugo · regla para todos

- QR, enlace, push, WhatsApp, asistente, entregas y cuentas: el cobro lo crea el backend contra pey en producción, y se confirma con su aviso firmado o con una consulta del backend (principios I y VI).
- Endpoints que suman al criterio del 30 %: `POST /codi/qr`, cobro push CoDi, enlaces de pago, `POST /bank-account` y sus webhooks.
- Ninguna función se da por hecha sin un cobro real de $0.01 (sección 5.3).

**F-09 · Cupones por pagar con QR.** Juan (BD y backend) · Miguel (pantallas) · spec 008

- Como en China, pagar con QR da un premio. El negocio configura una promoción ("10 % en tu siguiente compra"). Cuando el cobro pasa a pagado (una sola vez, principio II), la pantalla enseña un QR de cupón que el cliente escanea **con la cámara normal** y que abre una página pública con su código.
- En la siguiente compra, el dueño teclea o escanea el código y el descuento se aplica antes de crear el QR (canje, #37). La tabla `cupones` ya existe en Supabase (#23).
- pey no dice quién pagó y no pedimos datos personales: el cupón es anónimo, de un solo uso y con vigencia.
- Suma en: originalidad e impacto, y alimenta el modelo de negocio (#49).

**F-10 · Cobro en entregas a domicilio.** Leonel (vista del repartidor) · Hugo (backend) · Juan (tabla) · spec 009

- Para pizzerías, fondas o cualquier negocio con reparto, sin integrarse a DiDi ni a Uber Eats. El negocio crea un pedido a domicilio. El cliente paga por enlace o push (F-02, #36), o el repartidor enseña el QR en la puerta desde su celular.
- Cuando pey confirma, el celular del repartidor suena: **"Pagado: entrega el pedido"**. Después el repartidor marca "Entregado".
- Pagado no es entregado (principio VIII): la entrega es un estado aparte, y lo marca el repartidor.
- Versión mínima: un enlace del pedido para el repartidor, sin cuenta propia.
- Suma en: impacto y originalidad.

**F-11 · Varias cuentas para recibir pagos (demo).** Juan (BD y backend) · Miguel (pantalla) · Hugo (alta en pey) · spec 010

- Decisión del 19 de noviembre: **real, solo con CLABEs del titular de la API key** (regla 7.3 c). Se registran dos o más cuentas con `POST /bank-account`, y cada cobro elige la suya con `bankAccountId`.
- El negocio ve sus cuentas (alias, banco, últimos 4 dígitos y estado), elige una predeterminada y puede cambiarla en cada cobro.
- El alta tarda hasta 5 días hábiles: **Hugo registra las cuentas a más tardar el lunes 23 de noviembre** (N-10).
- La CLABE completa nunca va al repositorio, a los logs, a capturas ni al video. Que cada negocio cobre en su propia CLABE sigue esperando la respuesta de pey (`flujo-de-trabajo.md`, §7).
- Suma en: uso del API de pey.

**F-12 · Bocina de cobro (propuesta).** Leonel · spec 005

- Al llegar el pago, el celular dice en voz alta "Recibiste ciento cincuenta pesos", con la voz del propio dispositivo (síntesis de voz del navegador, sin servicios externos).
- Es lo que usan las tienditas de India y China con sus bocinas de pagos QR: el dueño se entera sin mirar la pantalla, que es justo el caso de F-05.
- Esfuerzo pequeño. Si el celular no tiene voz en español, se queda el sonido normal.
- Suma en: experiencia y originalidad. **La decide Hugo.**

### 3.3 Lo que ya estaba y sigue

| Pieza | Issues | Qué pasa |
|---|---|---|
| Cuenta del negocio (registro e inicio de sesión) | #24, #30 | Se queda en S2: separa los datos de cada negocio para el asistente, los cupones y las cuentas. Si se atrasa, las funciones nuevas se enseñan con el negocio de demo |
| Historial y corte del día | #38, #39 | Se queda en S2–S3. Idea pequeña: que el corte diga cuánto se ahorró el negocio frente a una terminal de tarjeta (~3.5 %) |
| Web instalable (PWA) | #22 | Pasa a Leonel. Es la base de F-05 y F-06 |
| Enlaces de pago y push CoDi | #36 | Sube de prioridad: es la base de F-02 y F-10 |
| Apps Android e iOS | #73–#84 | Se mantienen. Hacen el núcleo: calculadora, duración, QR y aviso con notificación. El resto vive en la web (propuesta para #76) |
| Landing | #86 | Publicada por Miguel. Se actualiza con las funciones nuevas en S3 |
| Premium y monetización | #40, #49 | Se quedan para el pitch |
| Pago con NFC | #91 | **Propuesta: congelar.** No está en la lista y libera tiempo de Hugo |

---

## 4. Arquitectura

### 4.1 Cómo encajan las piezas

```text
 Pantallas del negocio              Servidor                    Servicios externos
 ─────────────────────              ────────                    ──────────────────
 Web de cobro (PWA)   ─┐                                   ┌──► API de pey (CoDi): QR, push,
 App Android          ─┼─ HTTPS ─►  Backend FastAPI  ──────┤    enlaces de pago y cuentas
 App iOS              ─┤            (el único con llaves)  │◄── avisos de pey (webhooks firmados)
 Vista del repartidor ─┘                  │                ├──► WhatsApp Cloud API (bot)
          ▲                               │                └──► Servicio de IA (asistente)
          └── aviso en vivo (SSE)         ▼
              y notificación push    Supabase (PostgreSQL)
                                     cobros · pagos · cupones · pedidos · cuentas
```

La demo pública sale por un túnel con HTTPS desde la computadora de la demo (spec 003). El cliente paga desde la app de su banco y, si recibe un cupón, lo abre con la cámara normal.

### 4.2 Reglas para las funciones nuevas

1. **Todo cobro nace en el backend y va a pey** (F-08). Ninguna pantalla, bot ni IA habla con pey.
2. **"Pagado" solo llega por un aviso firmado de pey o por una consulta del backend** (principio I). El sonido, la notificación, la voz, el cupón y "entrega el pedido" cuelgan de esa única transición de pendiente a pagado (principio II).
3. **Las cuentas las hace el código**, en centavos enteros. La IA solo interpreta lo que dice el dueño, y el dueño confirma antes de cobrar.
4. **Un solo motor de asistente** para la web y para WhatsApp.
5. **Un solo servidor para las tres pantallas.** La web y las dos apps usan los mismos contratos (`specs/001-backend-mvp/contracts/`, ampliados por cada spec).
6. **Pagado no es entregado** (principio VIII): el pedido tiene su propio estado de entrega.
7. **Sin datos personales de terceros.** Los cupones son anónimos, los pedidos guardan solo lo necesario y en pruebas solo se usan teléfonos y CLABEs propios.
8. **Llaves nuevas** (IA, WhatsApp y notificaciones push) solo en `backend/.env` o en el hosting, con su variable vacía en `.env.example` (principio III).
9. **Pieza nueva, comparativa nueva** (principio IX): toda librería o servicio llega con opción A frente a B. Leonel revisa la arquitectura y Hugo decide en el backend y la web de cobro.

### 4.3 Specs previstas

| Spec | Qué cubre | Funciones e issues | La escribe | La construyen | Etapa |
|---|---|---|---|---|---|
| 003 | Infraestructura de la demo: Supabase, túnel y CI (spec aprobada; dos cortes, 22 y 25 nov) | #35, #65, #66 (corte 1); #90, #19, #94 (corte 2) | Hugo | Hugo | S1 |
| 004 | Cobro rápido | F-03, F-04, F-07 · #100, N-06, #31, #32 | Hugo | Leonel (comportamiento), Miguel (visual), Hugo (backend) | S2 |
| 005 | Aviso de pago en todas partes | F-05, F-06, F-12 · #22, #33, N-07, N-08, N-09 | Hugo | Leonel (web), Miguel (diseño), Hugo (backend) | S2 |
| 006 | Cuenta del negocio e historial | #24, #30, #38, #39 | Hugo | Hugo, Miguel | S2–S3 |
| 007 | Cobro a distancia y asistente | F-01, F-02 · #36, #92, #93, #46–#48 | Hugo | Hugo, Miguel | Spec en S2, construcción en S3 |
| 008 | Cupones por pagar con QR | F-09 · #37, #40, N-13, N-14 | Juan | Juan, Miguel | Spec en S2, construcción en S3 |
| 009 | Cobro en entregas a domicilio | F-10 · N-15, N-16 | Leonel | Leonel, Hugo, Juan | Spec a más tardar el 1 dic, construcción en S3 |
| 010 | Varias cuentas del titular | F-11 · N-11, N-12 | Juan | Juan, Miguel | Spec en S2, construcción en S3 |

Cada dueño aprueba sus specs, planes y tareas, y decide si las escribe (constitución). Leonel hace observaciones de arquitectura sobre lo implementado. Cuando dos personas construyen la misma spec, cada una toma tareas distintas del mismo `tasks.md` y no tocan los mismos archivos a la vez.

---

## 5. El flujo de trabajo: de la idea al cobro real

### 5.1 El recorrido de cada pieza

```text
 1. Issue ──► 2. Spec, plan y tareas ──► 3. Construir con ──► 4. Guía QA ──► 5. Pull request
    listo       (opcionales)               pruebas primero      (si hay        documentado
                                                                 pantalla)      (Closes #N)

 ──► 6. El autor ──► 7. Revisión de Juan y Leonel ──► 8. QA en ──► 9. Cobro real
        une a main      (observaciones o bug)            celular      de $0.01
```

| Paso | Qué se hace | Responsable |
|---|---|---|
| 1. Issue listo | Cumple "Listo para empezar" (5.2) | Hugo |
| 2. Spec, plan y tareas | Opcionales: los decide quien construye. Si se hacen, con spec-kit: `/speckit-specify` → `/entrevista-spec` → `/qa-spec` → `/speckit-plan` → `/speckit-tasks` | Quien construye |
| 3. Construir | Rama `feature/<número>-<descripcion>`. Pruebas primero, con pey simulado y reloj controlado | Quien construye |
| 4. Guía QA | Si tiene pantalla, en `docs/qa/` | Miguel |
| 5. Pull request | Hacia `main`, con `Closes #<número>` y la descripción con la plantilla: qué pedía el issue, qué se hizo, decisiones, cómo probarlo, pendientes y seguridad | Quien construye |
| 6. Unir | Con el CI en verde y sin secretos en el diff | Quien construye |
| 7. Revisión | En menos de 24 h: constitución, contratos, pruebas, seguridad, legibilidad y arquitectura. Si algo salió mal, comentario o issue `tipo: bug` | Juan y Leonel |
| 8. QA | La guía QA en un Android y un iPhone reales | Juan (Miguel si el autor es Juan) |
| 9. Cobro real | Si la pieza toca cobros: $0.01 desde la demo pública, con la autorización de Hugo | Hugo |

Quien trabaja con specs sigue sus reglas: aprobar un paso no autoriza el siguiente, y el siguiente empieza cuando el dueño de la spec lo decide (principio IV).

### 5.2 Listo para empezar

Un issue se puede tomar cuando tiene:

- [ ] Dueño, etapa (milestone), épica y función (`F-xx`).
- [ ] Objetivo, criterios de aceptación y pruebas.
- [ ] Dependencias resueltas o con fecha.
- [ ] Mockup aprobado, si tiene pantalla.
- [ ] Spec, plan y tareas aprobados, si su dueño decidió hacerlos.

### 5.3 Hecho

Un issue se cierra cuando:

- [ ] Cumple sus criterios de aceptación.
- [ ] Sus pruebas se escribieron primero y están en verde en el CI, con `ruff` limpio.
- [ ] Su pull request está documentado con la plantilla y, si tiene pantalla, su guía QA se ejecutó.
- [ ] No expone llaves ni datos personales, y las observaciones de Juan o Leonel quedaron atendidas o con issue.
- [ ] Si toca cobros, se demostró con un cobro real de $0.01 en la demo pública (principio VI).
- [ ] La spec, el plan y la documentación quedaron al día.

### 5.4 Ritmo del equipo

| Cuándo | Qué | Quién | Dura |
|---|---|---|---|
| Lunes | Planeación: issues de la etapa, dueños y bloqueos | Todos; la lleva Hugo | 20 min |
| Diario, antes de las 10:00 | Parte por escrito en el grupo: qué hice, qué sigue y qué me bloquea | Todos | 2 min |
| Miércoles | Revisión de arquitectura: observaciones de Leonel sobre lo implementado en la semana | Leonel y quien construyó cada pieza | 45 min |
| Domingo | Demo interna con un cobro real de $0.01 y revisión de la puerta | Todos; la lleva Hugo | 30 min |
| Siempre | Revisión de lo unido a `main` en menos de 24 horas | Juan y Leonel | — |

Los horarios se confirman en la primera planeación, según la disponibilidad de Leonel.

### 5.5 Ramas, commits y secretos

- Una rama por issue: `feature/<número>-<descripcion>`, y `fix/` para errores. Nadie sube directo a `main`.
- Mensajes de commit: `tipo(NNN): descripción en español`. Por ejemplo, `feat(004): sumar importes en el teclado de cobro`.
- Las llaves se comparten solo con quien las necesita para su issue, por mensaje privado o con un gestor de contraseñas. El detalle está en [flujo-git-y-secretos.md](flujo-git-y-secretos.md).

---

## 6. Calendario

### 6.1 Etapas

| Etapa | Fechas | Meta |
|---|---|---|
| **S1 — Cobro en vivo** | vie 20 – dom 22 nov (lo que queda) | El núcleo cerrado en la demo pública y Leonel integrado |
| **S2 — Cobro rápido y aviso en todas partes** | lun 23 – dom 29 nov | F-03, F-04, F-05, F-06 y F-12. Cuenta del negocio. Apps v1 |
| **S3 — Cobrar a distancia, fidelizar y repartir** | lun 30 nov – dom 6 dic | F-01, F-02, F-09, F-10 y F-11. Historial. Apps v2. **Funciones congeladas el domingo** |
| **S4 — Cierre** | lun 7 – jue 10 dic | Seguridad, QA de regresión, video, textos y postulación |
| **Ajustes** | vie 11 – sáb 12 dic | Solo correcciones. Entrega antes de las 23:59 del sábado |

### 6.2 Entregables por persona

**S1 — Lo que queda de la semana (20–22 nov)**

| Persona | Entregables |
|---|---|
| Hugo | Spec 003 aprobada y su corte 1 construido: túnel y CI (#35, #65, #66); el corte 2, Supabase (#90, #19, #94), el miércoles 25. Cobro real de $0.01 desde la URL pública, que cierra #27 y #64. Alta de las CLABEs del titular en pey (N-10). Leonel en pey.build (N-01). Constitución 3.0.0 y flujo al día con el equipo de cuatro (N-02, PR #96). Issues de este documento creados. Requisitos de las apps con las funciones nuevas (#76) |
| Leonel | Arranque (2.3 y Anexo A). Revisión de los PR #72 y #96. Revisión de arquitectura de las specs 001 a 003 (N-03). Propuesta de arquitectura del front (N-04). Primera prueba de la URL pública por túnel desde fuera de nuestra red (N-17) |
| Juan | Unir los PR #72, #96, #98, #99 y #101 cuando estén revisados. Comparativa del stack de las apps con Miguel (N-05). Primera ronda de QA de la web de cobro (#88) |
| Miguel | Mockups con las funciones nuevas: calculadora, duración, notificación, cupón, vista del repartidor, cuentas y asistente (#20). Identidad visual (#21). Plantilla de guía QA (#87). Comparativa del stack de las apps con Juan (N-05) |

**S2 — Cobro rápido y aviso en todas partes (23–29 nov)**

| Persona | Entregables |
|---|---|
| Hugo | Specs 004 y 005, con el backend de la duración del QR (N-06) y el envío de notificaciones (N-07). Spec 006: inicio de sesión (#24) e historial (#38). Spec 007 escrita y aprobada para construirla desde el lunes 30. App de Meta y número de prueba de WhatsApp (#46) |
| Leonel | Decisión del front cerrada el lunes 23 (N-04). PWA base (#22). Notificaciones en la web (N-08). Calculadora (#100) y selector de duración (parte web de N-06). Bocina de voz, si Hugo la aprueba (N-09). Observaciones de arquitectura sobre 004 a 006. Spec 009 escrita. Prueba de la demo por túnel antes del domingo 29 (N-17) |
| Juan | Decisión del stack de las apps el martes 24 (N-05) y entorno de iOS (#81). Tablas de las specs 004 a 006. Segunda ronda de QA (#88). App iOS v1: teclear el monto y mostrar el QR (#82). Specs 008 y 010 escritas |
| Miguel | Parte visual de la pantalla de cobro con calculadora y duración (#31, #32). Diseño de la notificación, el sonido y la animación (#33). Pantallas de registro (#30). Guías QA de las specs 004 y 005. Entorno de Android (#77) y app Android v1 (#78) |

**S3 — Cobrar a distancia, fidelizar y repartir (30 nov – 6 dic)**

| Persona | Entregables |
|---|---|
| Hugo | Spec 007 construida: enlaces y push CoDi (#36), asistente (#92) y WhatsApp (#47, #48). Backend de los pedidos (N-15). Historial terminado (#38). Protección de datos y validación de entradas (#44). Bounties (#51), monetización (#49) y negocios piloto (#50) |
| Leonel | Spec 009 construida: vista del repartidor (N-16). Observaciones de arquitectura sobre 007 a 010. Empieza la revisión de seguridad (#95). Prueba de la demo por túnel antes del domingo 6 (N-17) |
| Juan | Spec 008 construida: emitir cupones (N-13) y canje (#37). Spec 010 construida: varias cuentas (N-11). Tabla de pedidos (N-15). Logs de la demo (#45). Tercera ronda de QA (#88). App iOS v2: aviso con sonido y notificación (#83) |
| Miguel | Pantallas del asistente (#93), historial (#39), cupones (N-14), Premium (#40) y cuentas (N-12). Estados de carga y error (#41). Accesibilidad (#42). Landing con las funciones nuevas. App Android v2 (#79) |

**S4 — Cierre (7–10 dic)**

| Persona | Entregables |
|---|---|
| Hugo | Revisión de seguridad final con Leonel (#52). Descripción (#53). Video (#54). Postulación con los cuatro integrantes antes del jueves 10 a las 23:59 (#56) |
| Leonel | Revisión de seguridad (#95) y revisión final del código. Pulido del front. Ensayo general de la demo por túnel con celulares y redes ajenos, siguiendo las instrucciones de prueba que leerán los jueces (N-17, #55) |
| Juan | QA de regresión en la web y las apps (#88). Instrucciones de prueba y declaración de componentes (#55). Compilación instalable de iOS (#84) |
| Miguel | Pulido de pantallas. Pruebas con negocios reales (#43, con Hugo). APK de Android (#80) |

**Ajustes (11–12 dic).** Solo se corrigen errores de QA y se afinan textos; no entra ninguna función nueva. Hugo envía la entrega (#56). Hugo congela la demo y la deja encendida en su computadora del 12 al 14 (#57, spec 003). Leonel la prueba por el túnel cada día del 12 al 14 y avisa a Hugo y a Juan en el momento si algo falla (N-17).

### 6.3 Trámites que hay que empezar ya

| Trámite | Por qué ya | Dueño | Fecha límite |
|---|---|---|---|
| Alta de dos o más CLABEs del titular en pey (N-10) | Tarda hasta 5 días hábiles en quedar activa | Hugo | lun 23 nov |
| Leonel en pey.build (N-01, #12). El portal del hackathon **ya está hecho** | Para que pueda ver el portal de pey y sus webhooks durante las pruebas de la demo | Hugo y Leonel | vie 27 nov |
| Cuenta de desarrollador de Apple, si el stack la pide para instalar en iPhones ajenos | Es de pago y su activación puede tardar | Juan | mié 25 nov |
| App de Meta, número de prueba y plantilla "Te pagaron" (#46, #48) | La plantilla pasa por la aprobación de Meta | Hugo | dom 29 nov |
| Proveedor y llave del servicio de IA del asistente | La spec 007 lo necesita, y los bounties pueden premiar a uno | Hugo | lun 30 nov |
| Demo encendida sin parar del 12 al 14 de diciembre en la computadora de Hugo (spec 003, RF-060); #34 queda como plan B | Sin nube, la demo solo existe con la computadora y el túnel encendidos | Hugo | dom 6 dic |

### 6.4 Orden de corte

Si una puerta no se cumple, se corta en este orden, de arriba abajo. Lo que quede a medias se puede enseñar en el video.

1. F-12 Bocina de voz.
2. F-10 Entregas a domicilio, más allá de la versión mínima.
3. Uno de los dos canales del asistente (F-01 o F-02): se queda el más avanzado, porque el motor es el mismo.
4. F-11 Varias cuentas.
5. F-09 Cupones (se queda el canje de #37 si ya funciona).

**No se cortan:** la demo pública (spec 003), F-03, F-04, F-05, F-06, F-07 y F-08.

**Apps:** sigue la regla de corte del 29 de noviembre. Si ese día una app no crea un cobro y muestra su QR, deja de crecer, se entrega como esté y su dueño vuelve a la web o a QA.

---

## 7. Issues

### 7.1 Issues nuevos

Se crean cuando Hugo apruebe este documento, con la plantilla del Anexo B.

| Id | Título propuesto | F | Dueño | Etapa | Épica | Depende de |
|---|---|---|---|---|---|---|
| N-01 | Integrar a Leonel: pey.build y accesos (el portal del hackathon ya está) | — | Hugo | S1 | #8 | — |
| N-02 | Actualizar la constitución y el flujo de trabajo con el equipo de cuatro | — | Hugo | S1 | #8 | PR #96 |
| N-03 | Revisar la arquitectura de las specs 001 a 003 | — | Leonel | S1 | #75 | — |
| N-04 | Decidir la arquitectura del front para las pantallas nuevas | F-07 | Leonel | S1 | #1 | #85 |
| N-05 | Decidir cómo se desarrollan las dos apps (stack para Android e iOS) | — | Miguel y Juan | S1 | #73, #74 | #76 |
| N-06 | Elegir la duración del QR al crear el cobro | F-04 | Hugo (backend), Leonel (web) | S2 | #3 | Spec 003 |
| N-07 | Enviar el aviso de pago como notificación push desde el backend | F-05, F-06 | Hugo | S2 | #3 | Spec 003 |
| N-08 | Recibir el aviso de pago como notificación en la web instalada | F-05, F-06 | Leonel | S2 | #1 | #22, N-07 |
| N-09 | Anunciar el pago en voz alta (bocina de cobro) | F-12 | Leonel | S2 | #1 | Spec 005 |
| N-10 | Dar de alta en pey dos o más CLABEs del titular de la API key | F-11 | Hugo | S1 | #5 | #14 |
| N-11 | Varias cuentas: guardarlas y elegir a cuál va cada cobro (backend y tabla) | F-11 | Juan | S3 | #3, #4 | N-10, spec 010 |
| N-12 | Varias cuentas: pantalla para verlas y elegir la del cobro | F-11 | Miguel | S3 | #1 | N-11 |
| N-13 | Cupones por pagar con QR: emitir el cupón cuando llega el pago (backend y tabla) | F-09 | Juan | S3 | #3, #4 | Spec 008 |
| N-14 | Cupones por pagar con QR: enseñar el cupón y su página pública | F-09 | Miguel | S3 | #1 | N-13 |
| N-15 | Entregas a domicilio: el pedido y su estado de entrega (backend y tabla) | F-10 | Hugo (backend), Juan (tabla) | S3 | #3, #4 | #36, spec 009 |
| N-16 | Entregas a domicilio: vista del repartidor que suena al pagar y marca "Entregado" | F-10 | Leonel | S3 | #1 | N-15, N-08 |
| N-17 | Probar la demo por túnel desde fuera de nuestra red, como la verán los jueces | — | Leonel | S1 a Ajustes | #7 | Spec 003 (#90) |

### 7.2 Issues que cambian

| # | Cambio |
|---|---|
| #12 | Registrar también a Leonel en pey.build |
| #20 | Sumar los flujos de las funciones F-01 a F-12 |
| #22 | Pasa de Miguel a Leonel, en la primera mitad de S2 |
| #31, #32 | Incluyen la calculadora, el selector de duración y el aviso con forma de notificación (parte visual) |
| #33 | Suma el diseño de la notificación de pago (F-06) |
| #34 | Sigue abierto como plan B para tener la demo encendida en la evaluación (6.3) |
| #36 | Sube de prioridad (base de F-02 y F-10), pierde la etiqueta `opcional` y entra en la spec 007 |
| #37 | Es el canje de los cupones de F-09 |
| #40 | Se separa: los cupones pasan a N-14 y queda la pantalla Premium |
| #45 | Pasa de Hugo a Juan. #57 se queda con Hugo (spec 003, QA-13) |
| #46, #47, #48 | Pierden "(Opcional)" y la etiqueta `opcional`: WhatsApp es la F-02. #46 pasa a S2 por los tiempos de Meta |
| #56 | La lista de integrantes incluye a Leonel |
| #60, #61, #67, #68 | Hugo confirma que se enviaron (vienen del kickoff) y los cierra |
| #76 | Los requisitos de las apps suman la calculadora, la duración del QR y la notificación en segundo plano |
| #77, #81 | Dependen de N-05 y quedan como "preparar el entorno con el stack elegido" |
| #79, #83 | Incluyen la notificación con la app en segundo plano |
| #88 | Las rondas de QA cubren las funciones nuevas |
| #91 | **Propuesta:** congelar (NFC no está en la lista de funciones) |
| #92, #93 | Nuevo alcance: el asistente arma la cuenta y crea el cobro con confirmación, además de contestar preguntas |
| #95 | Nuevo título: "Coordinar la revisión de seguridad con Leonel y un agente de IA" |
| #100 | Se asigna a Leonel, en S2 y dentro de la spec 004 |

### 7.3 Carga por persona

| Persona | Construye o escribe | Además | Carga |
|---|---|---|---|
| Hugo | Specs 003 a 007. Backend de N-06, N-07, N-15, #24, #36, #38, #44, #92 y WhatsApp (#46–#48) | Aprueba sus specs y prioriza el producto. Trámites con pey y Meta. Pilotos, bounties y entregables (#53, #54, #56) | **Alta.** Por eso Grok implementa sus fases, Leonel escribe la spec 009, Juan la 008 y la 010, y #45 y #91 salen de su lista |
| Leonel | #22, N-08, #100, parte web de N-06, N-09, N-16 y la spec 009 | Con Juan, revisa lo que se une a `main`. Observaciones de arquitectura. N-03, N-04, seguridad (#52, #95) y pruebas de la demo por túnel (N-17) | **Media o alta**, según sus horas. Si tiene menos tiempo, #100 y N-09 pasan a Miguel |
| Juan | Specs 008 y 010. N-11, N-13, la tabla de N-15 y las tablas de 004 a 006. App iOS (#81–#84) | QA de cada etapa (#88), #45 y #55 | **Alta.** La app iOS sigue la regla de corte del 29 de noviembre |
| Miguel | #30, #31, #32, #33, #39, #40, #93, N-12, N-14 y la landing. App Android (#77–#80) | Mockups (#20), identidad (#21), guías QA (#87), accesibilidad (#42) y pruebas con usuarios (#43) | **Alta.** La PWA base pasa a Leonel. La app Android sigue la regla de corte |

---

## 8. Riesgos

| # | Riesgo | Qué hacemos |
|---|---|---|
| 1 | **Alcance:** 12 funciones, dos apps y el núcleo en tres semanas | Prioridades (3.1), puertas de cada domingo (sección 1) y orden de corte (6.4) |
| 2 | **Hugo es cuello de botella:** escribe sus specs y hace el backend | Cada quien une su propio pull request y decide si hace spec, así nadie espera a Hugo. Leonel lo respalda en el backend y la web. Grok implementa sus fases. Juan escribe las specs 008 y 010 y Leonel la 009. #45 y #57 pasan a Juan. NFC se congela |
| 3 | **Disponibilidad de Leonel** | Acordar sus horas esta semana. Revisiones asíncronas en menos de 24 h. Si tiene menos tiempo, sus piezas de construcción pasan a Miguel y él se queda con arquitectura y revisión |
| 4 | **S1 va tarde:** el plan de la 003 espera a que se unan los PR #72 y #96 | Hugo une los dos en cuanto estén listos (constitución 3.0.0), y la 003 va en dos cortes (22 y 25 nov). Si la puerta S1 no se cumple, se mueve como máximo al martes 24, y S2 empieza igual con las specs |
| 5 | **Trámites externos** (pey, Meta y Apple) | Empiezan esta semana (6.3) |
| 6 | **Notificaciones en iPhone:** la web solo las recibe si está instalada (iOS 16.4 o posterior) | La app iOS las cubre. Con la web abierta suena igual. Las instrucciones de prueba lo dicen (#55) |
| 7 | **Demo sin nube** (spec 003): sin la computadora encendida no hay demo | Leonel prueba el túnel desde fuera cada semana (N-17), así las fallas salen antes de la evaluación. Del 12 al 14 de diciembre queda encendida sin parar en la computadora de Hugo (spec 003, RF-060); el 6 de diciembre se confirma, o se vuelve a la nube (#34) |
| 8 | **Reglas del hackathon:** cuentas ajenas (7.3 c), integrantes (4.3), componentes de terceros (9.2) y credenciales (8.1) | F-11 solo con cuentas del titular. Leonel ya inscrito. #55 declara lo de terceros. Las llaves, solo a quien las necesita |
| 9 | **Montos equivocados del asistente** | El código calcula y el dueño confirma (4.2, regla 3) |
| 10 | **Bounties** publicados hasta el 30 de noviembre | Se revisan en la planeación del lunes 30 (#51) y pueden mover prioridades de S3 |
| 11 | **Reglas nuevas de CoDi** del 14 de diciembre (Circular 9/2026) | Sigue como pregunta abierta desde el kickoff. Hugo la revisa antes de S4 |

---

## 9. Decisiones pendientes

| Decisión | Quién | Para cuándo |
|---|---|---|
| Aprobar este documento y decidir si se une junto con el PR #96 | Hugo | vie 20 nov |
| Horas por semana y horario de Leonel | Leonel | vie 20 nov |
| Arquitectura del front para las pantallas nuevas (N-04): seguir sin framework, como la spec 002, o usar React, como propuso Miguel en #85 | Leonel propone, Hugo decide | lun 23 nov |
| Congelar NFC (#91) | Hugo | lun 23 nov |
| Incluir la bocina de voz (F-12) | Hugo | lun 23 nov |
| Stack de las dos apps (N-05) | Miguel y Juan; revisa Leonel | mar 24 nov |
| Opciones de duración del QR y si entra el QR sin vencimiento | Hugo, en la entrevista de la spec 004 | S2 |
| Proveedor de IA del asistente | Hugo, en la spec 007 | lun 30 nov |
| Qué premia la promoción de cupones (porcentaje, monto y vigencia) | Juan y Hugo, en la spec 008 | S2 |
| Demo encendida en la evaluación o regreso a la nube | Hugo | dom 6 dic |
| Que cada negocio cobre en su propia CLABE (respuesta de pey) | Hugo, con legal@pey.mx (regla 7.7) | Antes del 10 dic |

---

## Anexo A. Arranque técnico

Desde la raíz del repositorio, con [uv](https://docs.astral.sh/uv/) y Python 3.11 o superior:

```bash
uv sync --directory backend
```

```bash
uv run --directory backend pytest -q
```

```bash
uv run --directory backend ruff check .
```

Las pruebas de la web están en el PR #72 (rama `feature/64-web-mvp`). Usan un servidor simulado y no necesitan llaves. La primera vez se instalan los navegadores:

```bash
uv run --directory backend playwright install chromium webkit
```

```bash
uv run --directory backend pytest ../web -q
```

Para correr el backend y la web contra pey de verdad hace falta `backend/.env` ([README](../README.md#cómo-correrlo-en-local)). Las llaves las da Hugo por mensaje privado o con un gestor de contraseñas, solo si el issue lo pide.

## Anexo B. Plantilla de issue

```markdown
## Objetivo
Qué cambia para el dueño del negocio, en una frase.

## Contexto
Por qué hace falta y qué ya existe.

## Incluye
- …

## Depende de
#… (o "Nada")

## Criterios de aceptación
- [ ] …
- [ ] Si toca cobros: se demostró con un cobro real de $0.01.
- [ ] El pull request está documentado con la plantilla `.github/pull_request_template.md`.

## Pruebas
Cómo se comprueba.

Función: F-xx · Spec: NNN · Épica: #…

Flujo de construcción: docs/flujo-de-construccion.md
```
