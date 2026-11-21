# PAGO FÁCIL — Flujo de trabajo, roles e issues

**Hackatón México 2026** · Repositorio `Altairtm/Hackton-2026` · Versión del 15 de noviembre de 2026, actualizada el 20 de noviembre

Este documento dice quién hace qué, cuándo y con qué entregable. Sustituye al reparto del 14 de noviembre (`PAGO-FACIL-reparto-de-responsabilidades.pdf`).

> **Actualización del 20 de noviembre.** Leonel Mendiola entró como integrante oficial y el equipo vuelve a ser de cuatro. Las reglas de trabajo (secciones 1 y 4) ya están al día. El reparto por persona con Leonel y las 12 funciones nuevas está en [`docs/flujo-de-construccion.md`](docs/flujo-de-construccion.md). Las tablas de las secciones 5 y 6 son el reparto del 15 de noviembre.

Las reglas comunes del proyecto están en la [constitución](.specify/memory/constitution.md). Si este documento choca con ella, manda la constitución. Si la constitución choca con las [reglas del hackathon](https://hackatonmexico.com/reglas), mandan las reglas.

---

## 1. Lo esencial en una página

- **Somos cuatro:** Hugo, Leonel, Juan y Miguel. Los cuatro están inscritos en el hackathon.
- **El desarrollo termina el jueves 10 de diciembre.** El 11 y el 12 son solo para ajustes. La entrega oficial cierra el sábado 12 de diciembre a las 23:59, sin prórroga.
- **Construimos tres pantallas sobre un solo servidor:** la web de cobro, una app Android y una app iOS.
- **Cada quien decide cómo construir sus issues**, y también si hace spec, plan y tareas. Lo obligatorio para todos es que el **commit y el pull request cuenten bien lo que se hizo**, con la [plantilla de pull request](.github/pull_request_template.md).
- **Cada quien une su propio pull request.** Juan y Leonel revisan lo que entra a `main` y, si algo salió mal, lo hacen ver.
- **Nadie es indispensable.** Si el responsable de una tarea no puede, otra persona la toma sin pedir permiso y lo deja anotado en el issue.
- **La web va primero.** Es el enlace que evalúan los jueces. Después van las apps y al final lo Premium.

| Persona | Cuenta de GitHub | Responsabilidades | Respaldo |
|---|---|---|---|
| **Hugo** | `HugoAI23` | Producto (requisitos e historias de usuario), backend, integraciones (pey, WhatsApp, chatbot), la demo por túnel, CI, coordinación de la seguridad y la web de cobro hasta cerrar la spec 002 | Leonel, en el backend y la web |
| **Leonel** | `mendiolaleonel2002-debug` | Arquitectura (observaciones de cambios sobre lo implementado), revisión de lo que se une a `main`, front de la web (base PWA, notificaciones y pantallas) y pruebas de la demo por túnel para los jueces | Miguel en el front, Hugo en la revisión |
| **Juan** | `Altairtm` | Pruebas QA y revisión de lo que se une a `main`, bases de datos (Supabase y MongoDB) y la **app iOS** | Leonel en la revisión, Miguel en QA |
| **Miguel** | `Beer17` | Pantallas de la web y UI/UX, landing page, guías QA y la **app Android** | Leonel en las pantallas, Juan en las guías QA |

---

## 2. Producto

**Para quién:** comerciantes que todavía no cobran con dinero digital (tienditas, puestos, ferreterías, tortillerías).

**Qué hace:** el comerciante teclea el monto, enseña un QR de CoDi, el cliente paga desde la app de su banco y el comerciante oye y ve "Pago recibido".

| Requisito | Tipo | Estado al 15 de noviembre |
|---|---|---|
| Realizar un cobro en menos de 3 segundos | Núcleo | Servidor listo (spec 001). Falta medirlo en la demo pública |
| Generar el código QR en menos de 3 segundos | Núcleo | Servidor listo (spec 001, criterio CE-002) |
| Introducir el monto del cobro | Núcleo | Web en curso (spec 002, issue #64) |
| Sonido cuando se cobra | Núcleo | Web en curso (spec 002, issue #64) |
| Web móvil | Núcleo | En curso; falta publicarla con HTTPS (#65) |
| App Android | Núcleo | Sin empezar (Miguel, épica #73) |
| App iOS | Núcleo | Sin empezar (Juan, épica #74) |
| Que cada negocio reciba el dinero en su propia CLABE | **Por decidir** | Sin issue. Espera la respuesta de pey (ver "Punto abierto" en la sección 7) |
| Pago con NFC | Premium | Primero se investiga si es posible (#91, Hugo) |
| Chatbot dentro de la web | Premium | Backend Hugo (#92), pantalla Miguel (#93) |
| Integración con WhatsApp | Premium | Issues #46 a #48 (Hugo) |

**Premium** significa que solo se empieza cuando el núcleo ya funciona en la demo pública.

---

## 3. Stack

| Pieza | Decisión | Estado |
|---|---|---|
| Backend | Python con FastAPI | Decidido y en uso |
| Cobros | API de pey (CoDi) | Decidido y en uso |
| Web de cobro | HTML, CSS y JavaScript, sin framework | Decidido y en uso (spec 002) |
| Base de datos relacional | Supabase (PostgreSQL) | Decidido; falta crear el proyecto (Juan) |
| Nube | Sin nube por ahora: la demo sale por un túnel HTTPS (Tailscale Funnel) desde la computadora de Hugo | Decidido en la spec 003 (D-4 y DP-38). AWS queda como plan B (#34) |
| Landing page | React + Tailwind + Lovable (propuesta) | **Lo define Miguel** |
| App Android | Por elegir | **Lo define Miguel** |
| App iOS | Por elegir | **Lo define Juan** |
| Base de datos no relacional | MongoDB | **Juan define para qué sirve.** Primer candidato: guardar la imagen del QR |
| Imagen del QR | La que entrega pey, guardada en Supabase | Decidido en la spec 003 (D-2, #94): no se usan `qrcode` ni `segno` |
| Editor y agentes | Antigravity, Claude u otros | Libre. Todo agente lee la constitución antes de empezar |

Cada decisión pendiente se cierra con una comparativa corta por escrito: opción A frente a B, ventajas, desventajas y por qué se eligió. Va en la descripción del pull request del issue correspondiente.

---

## 4. Cómo se trabaja un issue

Los pasos son los mismos para los cuatro.

1. **Tomar el issue.** Asígnatelo en GitHub y crea la rama `feature/<número>-<descripcion-corta>`.
2. **Construirlo.** Cómo hacerlo lo decide su dueño, y también si hace spec, plan y tareas. Hugo trabaja con specs (spec-kit). Spec-kit está instalado en el repositorio para quien quiera usarlo.
3. **Guía QA, si el issue tiene pantalla.** Miguel la escribe en `docs/qa/`. Es la lista de pasos que Juan va a seguir en un celular.
4. **Commit y pull request documentados.** El pull request va hacia `main`, con `Closes #<número>`. Su descripción sigue la [plantilla](.github/pull_request_template.md): qué pedía el issue, qué se hizo, qué se decidió y por qué, cómo probarlo, qué quedó pendiente y la revisión de seguridad. Si trabajaste con spec, basta con enlazar su carpeta. No hay otro documento aparte.
5. **Unirlo.** El autor une su propio pull request cuando el CI está en verde y revisó su diff buscando llaves, `.env` o datos personales.
6. **Revisión después de unir.** Juan y Leonel revisan lo que entra a `main`. Comprueban que respete la constitución, que el pull request esté bien documentado y, si tiene pantalla, que la guía QA se cumpla. Si algo salió mal, lo comentan en el pull request o abren un issue `tipo: bug` para el dueño. Si rompe la demo, se corrige o se revierte con otro pull request.

**Arquitectura.** Leonel no aprueba planes antes de construir. Se implementa y él hace observaciones de cambios; el dueño decide cómo atenderlas.

**Seguridad.** La revisión de seguridad la hacen un agente de IA y Leonel sobre lo que se une a `main`. Hugo coordina y reparte los arreglos. Las llaves de pey solo las tienen integrantes y solo viven en `backend/.env` o en el hosting (constitución, principio III).

**Si el responsable no puede.** Cualquier integrante, de preferencia su respaldo (tabla de la sección 1), toma la tarea o la pasa a otra persona, sin pedir la aprobación de nadie. Basta con dejar en el issue que se hizo el cambio y reasignarlo; no hace falta explicar la causa. Las llaves no viajan con la tarea: si hacen falta, las da Hugo, que es el titular.

**Si trabajas con un agente de IA.** Pídele que lea `.specify/memory/constitution.md` antes de escribir código. Puedes tener tu propio archivo `AGENTS.md` en tu computadora: git lo ignora. El de Hugo no está en el repositorio; si lo quieres usar, pídeselo.

### Las tres pantallas usan el mismo servidor

La web, la app Android y la app iOS hablan con el backend de PAGO FÁCIL usando los mismos contratos, que están en `specs/001-backend-mvp/contracts/`:

| Contrato | Para qué |
|---|---|
| `crear-cobro.md` | Crear el cobro y recibir el QR |
| `canal-avisos.md` | Enterarse en tiempo real de que llegó el pago |
| `ver-cobro.md` | Consultar el estado de un cobro (respaldo si el canal se corta) |
| `cancelar-cobro.md` | Cancelar un cobro equivocado |
| `salud.md` | Saber si el servidor está listo |

Ninguna pantalla lleva la llave de pey ni habla con pey directamente. Eso solo lo hace el backend.

---

## 5. Calendario

| Etapa | Fechas | Meta |
|---|---|---|
| M0 Kickoff | 14–15 nov | Cerrada |
| **S1 — Cobro en vivo** | lun 16 – dom 22 nov | Un cobro real desde la URL pública |
| **S2 — Cuenta, historial y apps v1** | lun 23 – dom 29 nov | El negocio entra y ve sus cobros. Cada app crea un cobro y muestra el QR |
| **S3 — Apps completas, Premium y pilotos** | lun 30 nov – dom 6 dic | Las apps avisan el pago con sonido. Lo Premium se puede enseñar |
| **S4 — Cierre** | lun 7 – jue 10 dic | **Fin del desarrollo y postulación** |
| **Ajustes** | vie 11 – sáb 12 dic | Solo correcciones. Entrega antes de las 23:59 del 12 |

### Entregables por persona

**S1 — Cobro en vivo (16–22 nov)**

| Persona | Entregables |
|---|---|
| Hugo | Web de cobro completa (#64). Demo por túnel con HTTPS y webhook de pey conectado (spec 003, #65). README con el enlace en vivo (#66). CI en cada pull request (#35). Trámites de pey (#11, #12, #14, #15). Guía de instalación (#17). Requisitos e historias de usuario de las apps (#76). Decisión sobre las librerías de QR (#94). Pago real de $0.01 desde la demo pública, para cerrar #27 y #29 |
| Juan | Proyecto y esquema en Supabase (#19, #23). Propuesta de uso de MongoDB (#89). Revisión del pull request #72. Tecnología elegida y entorno de iOS funcionando (#81) |
| Miguel | Decisión sobre React + Tailwind + Lovable (#85). Mockups de la web y de las apps (#20). Identidad visual (#21). Plantilla de guía QA y guía QA del cobro (#87). Tecnología elegida y entorno de Android funcionando (#77) |

**S2 — Cuenta, historial y apps v1 (23–29 nov)**

| Persona | Entregables |
|---|---|
| Hugo | Cobros y pagos guardados en Supabase (#90). Registro e inicio de sesión (#24). Historial y corte del día (#38). Logs de la demo (#45). Resultado de la investigación de NFC (#91) |
| Juan | Primera ronda de QA sobre la web de cobro (#88). App iOS v1: teclear el monto y mostrar el QR (#82) |
| Miguel | Pantalla de cobro final con sonido y animación (#31, #32, #33). PWA instalable (#22). Pantallas de registro (#30). Landing v1 (#86). App Android v1: teclear el monto y mostrar el QR (#78) |

**S3 — Apps completas, Premium y pilotos (30 nov – 6 dic)**

| Persona | Entregables |
|---|---|
| Hugo | Chatbot, backend (#92). WhatsApp (#46–#48). Modelo de monetización (#49). Uno o dos negocios piloto (#50). Revisión de premios y bounties (#51). Revisión de seguridad con el agente y Leonel (#44, #95) |
| Juan | Segunda ronda de QA (registro, historial y apps). App iOS v2: aviso de pago con sonido y vibración (#83) |
| Miguel | Pantalla de historial (#39). Estados de carga, error y sin conexión (#41). Pantalla del chatbot (#93). Pantalla Premium (#40). Accesibilidad (#42). Landing final. App Android v2: aviso de pago (#79), y NFC si la investigación lo permite |

**S4 — Cierre (7–10 dic)**

| Persona | Entregables |
|---|---|
| Hugo | Revisión de seguridad final (#52). Descripción del proyecto (#53). Video de demo (#54). Postulación antes del 10 de diciembre (#56) |
| Juan | QA de regresión en web y apps. Instrucciones de prueba y declaración de componentes (#55). Compilación instalable de iOS (#84) |
| Miguel | Pulido de pantallas. Pruebas con usuarios reales (#43, con Hugo). APK instalable de Android (#80) |

**Ajustes (11–12 dic).** Solo se corrigen errores encontrados en QA y se afinan textos. No entra ninguna función nueva. Hugo envía la entrega (#56) y deja la demo congelada (#57).

### Regla de corte

Los jueces evalúan el enlace web, así que la web va primero. Si el **domingo 29 de noviembre** una app todavía no crea un cobro y muestra su QR, esa app deja de crecer: se entrega como está, se enseña en el video, y su dueño vuelve a sus tareas de web o de QA. Lo Premium nunca se adelanta al núcleo.

---

## 6. Cruce de los 68 issues

**Resumen.** De los 68 issues originales, 8 son épicas y 60 son tareas. Las asignaciones, los cierres y las etapas de esta sección ya están aplicados en GitHub.

| Situación | Cuántos | Issues |
|---|---|---|
| Cerrados | 11 | #13, #16, #18, #59, #62 y #63 desde antes. #25, #26 y #28 (los resolvió la spec 001, pull request #70) y #9 y #10 (los resuelve este documento), el 15 de noviembre |
| Código hecho, falta el pago real | 2 | #27 y #29. Se cierran con un cobro real de $0.01 desde la demo pública (#65) |
| Del kickoff: falta confirmar para cerrar | 4 | #60, #61, #67, #68 |
| Vivos | 43 | Hugo 29, Miguel 11, Juan 3 (sin contar #27 y #29) |

### Qué cambió respecto al reparto del 14 de noviembre

| Antes | Áreas | Ahora |
|---|---|---|
| Profesor (14 issues) | Backend, base de datos e integración con pey | El 15 de noviembre dejó de ser integrante: backend e integraciones pasaron a Hugo y base de datos a Juan. **El 19 de noviembre volvió como integrante oficial** (Leonel): arquitectura, revisión de lo unido, front y pruebas de la demo por túnel |
| Miguel (12) | Frontend y UX/UI | Igual, más landing page, guías QA y la app Android |
| Hugo (18) | IA, WhatsApp y producto | Igual, más backend, AWS, CI, chatbot, NFC y coordinación de la seguridad |
| Juan (14) | Seguridad, DevOps y coordinación | Deja esas tres áreas (pasan a Hugo). Toma revisión de pull requests, bases de datos, QA y la app iOS |

### Épicas

| # | Épica | Dueño | Cambio |
|---|---|---|---|
| #1 | Frontend (Web/PWA) | Miguel | Igual |
| #2 | UX/UI | Miguel | Igual |
| #3 | Backend | Hugo | Antes sin dueño |
| #4 | Base de datos | Juan | Antes sin dueño |
| #5 | Integraciones (pey y WhatsApp) | Hugo | Antes sin dueño |
| #6 | Seguridad | Hugo | Antes Juan |
| #7 | DevOps / Infraestructura | Hugo | Antes Juan |
| #8 | Producto y entrega | Hugo | Igual |

### Issues de Hugo

| # | Issue | Etapa | Nota |
|---|---|---|---|
| #9 | Definir el equipo oficial | Cerrado | Resuelto: equipo de 3 |
| #10 | Asignar roles y responsables | Cerrado | Resuelto con este documento |
| #11 | Titular de la API key de pey | S1 | Antes Juan |
| #12 | Registrar al equipo en pey.build | S1 | |
| #14 | Cuenta de pago CoDi en el portal de pey | S1 | Antes sin dueño. Tarda unos 5 días hábiles |
| #15 | API key y webhook en el portal de pey | S1 | Antes sin dueño |
| #17 | Entorno local y guía de instalación | S1 | Antes Juan |
| #24 | Registro e inicio de sesión (backend) | S2 | Antes sin dueño |
| #25 | Cliente del API de pey | Cerrado | Hecho en la spec 001 |
| #26 | Endpoint para crear un cobro | Cerrado | Hecho en la spec 001 |
| #27 | Recibir el webhook de pago | S1 | Código hecho en la spec 001. Falta el pago real desde la demo pública |
| #28 | Verificar la firma de los webhooks | Cerrado | Hecho en la spec 001 |
| #29 | Aviso en tiempo real a la web | S1 | Código hecho en la spec 001. Falta el pago real desde la demo pública |
| #34 | Desplegar backend y web con HTTPS | S1 | Antes Juan. Desde el 17 nov es el plan B: la demo sale por túnel (spec 003, D-4) |
| #35 | CI: lint y pruebas en cada pull request | S1 | Antes Juan |
| #36 | Enlaces de pago y push CoDi | S3 | Antes sin dueño. **Opcional** |
| #37 | Cupones antes de generar el QR | S3 | Antes sin dueño. **Opcional** |
| #38 | Historial de cobros y corte del día | S2 | |
| #43 | Pruebas con usuarios reales | S4 | Con Miguel |
| #44 | Proteger datos y validar entradas | S3 | Antes Juan. Con el agente de IA y Leonel |
| #45 | Logs y monitoreo de la demo | S2 | Antes Juan |
| #46 | WhatsApp Cloud API con número de prueba | S3 | Premium |
| #47 | Bot de WhatsApp: "cobra monto concepto" | S3 | Premium |
| #48 | Bot de WhatsApp: aviso "Te pagaron" | S3 | Premium |
| #49 | Modelo de monetización | S3 | |
| #50 | Negocios piloto y métricas | S3 | |
| #51 | Documento de premios y bounties | S3 | Se publican a más tardar el 30 de noviembre |
| #52 | Revisión de seguridad antes de la entrega | S4 | Antes Juan |
| #53 | Descripción del proyecto (500 palabras) | S4 | |
| #54 | Video de demo (3 minutos) | S4 | |
| #56 | Postulación (10 dic) y entrega (12 dic) | S4 y Ajustes | |
| #57 | Congelar la demo hasta el 31 de enero | Ajustes | Antes Juan |
| #58 | Pitch deck | S4 | **Opcional** |
| #60 | Nombre del equipo y descripción | Por confirmar | Del kickoff: se cierra al confirmar que se envió |
| #61 | API key de prueba con la CLABE de pey | Por confirmar | Sin dueño todavía. Se cierra al confirmar que la llave es esa |
| #64 | MVP web: página de cobro | S1 | Antes Miguel. Lo construye Hugo (spec 002, pull request #72) |
| #65 | Desplegar el MVP con HTTPS | S1 | Antes Juan |
| #66 | README con el enlace a la app en vivo | S1 | Depende de #65 |
| #67 | Video demo corto del kickoff | Por confirmar | Opcional. El video oficial es #54 |
| #68 | Formulario de Luma del kickoff | Por confirmar | Se cierra al confirmar que se envió |

### Issues de Miguel

| # | Issue | Etapa | Nota |
|---|---|---|---|
| #20 | Flujo y mockups de las pantallas | S1 | Ahora incluye las apps Android e iOS |
| #21 | Identidad visual: logo, colores y tipografía | S1 | |
| #22 | PWA base instalable | S2 | |
| #30 | Pantallas de registro e inicio de sesión | S2 | |
| #31 | Pantalla de cobro: monto, concepto y QR | S2 | Parte de lo que deje la spec 002 |
| #32 | Confirmación de pago con sonido y aviso visual | S2 | Parte de lo que deje la spec 002 |
| #33 | Sonido y animación de pago recibido | S2 | |
| #39 | Pantalla de historial y corte del día | S3 | |
| #40 | Pantallas de cupones y plan Premium | S3 | La parte de cupones es **opcional** |
| #41 | Estados de carga, error, QR vencido y sin conexión | S3 | |
| #42 | Accesibilidad y uso en celular | S3 | |

### Issues de Juan

| # | Issue | Etapa | Nota |
|---|---|---|---|
| #19 | Base de datos y esquema inicial | S1 | Antes sin dueño. Ya no es "elegir": es crear el proyecto en Supabase |
| #23 | Tablas: negocios, cobros, pagos y cupones | S1–S2 | Antes sin dueño |
| #55 | Instrucciones de prueba y declaración de componentes | S4 | |

### Issues nuevos

Son requisitos que no tenían issue. Se crearon en GitHub el 15 de noviembre, enlazados a su épica.

| # | Issue nuevo | Dueño | Etapa | Nota |
|---|---|---|---|---|
| #73 | Épica: App Android | Miguel | — | |
| #74 | Épica: App iOS | Juan | — | |
| #75 | Épica: QA y revisión | Juan | — | |
| #76 | Requisitos e historias de usuario de las apps móviles | Hugo | S1 | Lo que deben hacer las dos apps, igual para ambas |
| #77 | Android: elegir tecnología y preparar el entorno | Miguel | S1 | Con comparativa escrita |
| #78 | Android v1: teclear el monto y mostrar el QR | Miguel | S2 | |
| #79 | Android v2: aviso de pago con sonido y vibración | Miguel | S3 | |
| #80 | Android: APK instalable para la demo | Miguel | S4 | |
| #81 | iOS: elegir tecnología, entorno y cuenta de Apple | Juan | S1 | Con comparativa escrita |
| #82 | iOS v1: teclear el monto y mostrar el QR | Juan | S2 | |
| #83 | iOS v2: aviso de pago con sonido y vibración | Juan | S3 | |
| #84 | iOS: compilación instalable para la demo | Juan | S4 | TestFlight o equipos de prueba |
| #85 | Decidir dónde entra React + Tailwind + Lovable | Miguel | S1 | Con comparativa escrita |
| #86 | Landing page | Miguel | S2–S3 | |
| #87 | Plantilla de guía QA y guía por funcionalidad | Miguel | S1 en adelante | En `docs/qa/`. Cubre web y apps |
| #88 | Ejecutar QA por ronda y reportar errores | Juan | S2–S4 | Incluye medir "menos de 3 segundos". La app iOS la prueba Hugo o Miguel |
| #89 | Definir el uso de MongoDB | Juan | S1 | Primer candidato: la imagen del QR |
| #90 | Guardar cobros y pagos en Supabase desde el backend | Hugo | S2 | Hoy se pierden al reiniciar el servidor |
| #91 | Investigar el pago con NFC | Hugo | S2 | Tiempo fijo. Si es posible, se construye en Android |
| #92 | Chatbot en la web: backend | Hugo | S3 | Premium |
| #93 | Chatbot en la web: pantalla | Miguel | S3 | Premium |
| #94 | Decidir si el backend dibuja el QR o sigue la imagen de pey | Hugo | S1 | Decidido: la imagen de pey, guardada en Supabase (spec 003, D-2) |
| #95 | Coordinar la revisión de seguridad | Hugo | S3–S4 | Agente de IA y Leonel |

### Carga por persona

Tareas vivas más tareas nuevas, sin contar épicas ni lo que se va a cerrar.

| Persona | Vivas | Nuevas | Total | Además |
|---|---|---|---|---|
| Hugo | 31 | 6 | **37** | Dos solo esperan el pago real (#27, #29). Siete son opcionales o Premium (#36, #37, #46, #47, #48, #58 y #92) |
| Miguel | 11 | 8 | **19** | Escribe la guía QA de cada pantalla |
| Juan | 3 | 6 | **9** | Ejecuta todas las rondas de QA y, con Leonel, revisa lo que se une a `main` |

---

## 7. Riesgos

1. **Alcance.** Somos cuatro y quedan 21 días de desarrollo para una web, dos apps nativas, una landing, registro, historial y tres funciones Premium. Para eso está la regla de corte del 29 de noviembre.
2. **Carga desigual.** Hugo tiene 37 tareas, Miguel 19 y Juan 9. Si Hugo se atrasa, cualquiera puede tomar sus tareas (sección 4, "Si el responsable no puede"). Las primeras candidatas pasan a Juan sin salirse de su papel de QA: el CI (#35), verificar la guía de instalación (#17), los logs de la demo (#45) y congelar la demo (#57). El backend y la web los respalda Leonel.
3. **La revisión ya no frena a nadie.** Cada quien une su pull request y Juan y Leonel revisan después. El riesgo cambia: un error puede llegar a `main`. Por eso se revisa lo unido en menos de 24 horas y, si rompe la demo, se revierte con otro pull request.
4. **iOS necesita más que Android.** Hace falta una Mac con Xcode y, para instalar la app en un iPhone ajeno, una cuenta de desarrollador de Apple de pago. TestFlight tiene revisión previa. Android se reparte con un archivo APK.
5. **Cuatro formas de trabajar en un mismo repositorio.** El pull request bien documentado y la revisión de Juan y Leonel son lo que mantiene parejo el resultado. Sin ellos nadie sabe qué hizo el otro.
6. **Cuenta CoDi de pey.** El trámite tarda unos 5 días hábiles (#14). Hay que iniciarlo en S1.
7. **Cinco decisiones de tecnología abiertas en S1:** landing, Android, iOS, MongoDB y librerías de QR. Cada día sin decidir es un día menos de construcción.
8. **Nuevas reglas de CoDi del 14 de diciembre** (Circular 9/2026). Quedó como pregunta abierta desde el kickoff.

### Punto abierto: la CLABE de cada negocio

Hoy todos los cobros llegan a una sola cuenta: la que está ligada a nuestra API key. Para que PAGO FÁCIL sirva a un negocio real, el dinero tiene que llegar a **la cuenta de ese negocio**. Esto no tiene issue todavía, a propósito: **Hugo lo está consultando con el equipo de pey** y no se construye nada hasta tener su respuesta.

Lo que ya se sabe (revisado el 15 de noviembre):

- **El API de pey lo permite.** `POST /bank-account` registra una CLABE y `POST /codi/qr` acepta `bankAccountId` para elegir a qué cuenta va el cobro. El dinero va directo a esa cuenta; PAGO FÁCIL nunca lo recibe ni lo guarda.
- **El alta de una CLABE tarda hasta 5 días hábiles.** Un negocio piloto tendría que registrarla a más tardar el 1 de diciembre.
- **Las reglas lo condicionan.** Las reglas del hackathon (§7.3) prohíben cobrar a favor de cuentas que no sean del titular de las credenciales, y los Términos del API (cláusulas 3.3, 5.2 y 5.4) piden una autorización escrita de pey para que una plataforma registre las cuentas de sus comercios. Las cuentas concentradoras están prohibidas siempre.
- **Sin esa autorización**, la demo solo puede usar CLABEs del titular de la API key o la CLABE de prueba de pey.

A quién le toca cuando se decida: el backend a Hugo (registrar la cuenta y mandar `bankAccountId`), la pantalla de alta a Miguel y los campos nuevos de la tabla de negocios a Juan (#23). Va ligado al registro del negocio (#24) y a guardar los cobros en Supabase (#90), así que **esas dos tareas deben diseñarse dejando sitio para la cuenta del negocio**. La CLABE de un negocio es un dato bancario de un tercero: nunca va en el repositorio, en los logs ni en el video.

---

## Anexo: cambios aplicados en GitHub

Aplicados el 15 de noviembre de 2026.

**Cerrados (5):** #25, #26 y #28, citando el pull request #70. #9 y #10, citando este documento.

**No se cerraron, aunque estaba previsto:**

- #27 y #29. Su código está en `main`, pero sus criterios de aceptación piden un pago real, y los pagos reales de $0.01 siguen pendientes. Quedaron abiertos, asignados a Hugo, en S1.
- #60, #61, #67 y #68, del kickoff. Falta que Hugo confirme que se enviaron.

**Asignados a Hugo (`HugoAI23`):** épicas #3, #5, #6 y #7; issues #11, #14, #15, #17, #24, #25 a #29, #34, #35, #36, #37, #44, #45, #52, #57, #64 y #65.

**Asignados a Juan (`Altairtm`):** épica #4; issues #19 y #23.

**Etiqueta `opcional`:** agregada a #36 y #37. **Pendiente:** separar en #40 la parte de cupones, que es opcional, de la pantalla Premium.

**Títulos:** #19 es ahora "Crear el proyecto en Supabase y el esquema inicial". #34 es ahora "Desplegar backend y web en AWS con HTTPS".

**Etiquetas nuevas:** `area: android`, `area: ios`, `area: qa` y `premium`.

**Milestones:**

| Antes | Ahora | Fecha límite |
|---|---|---|
| M1 — Arranque y cuenta pey | S1 — Cobro en vivo | 22 nov |
| M2 — Cobro CoDi funcionando | S2 — Cuenta, historial y apps v1 | 29 nov |
| M3 — Extras y monetización | S3 — Apps completas, Premium y pilotos | 6 dic |
| M4 — Entrega | S4 — Cierre | 10 dic |
| (nuevo) | Ajustes y entrega | 12 dic |

**Issues que cambiaron de etapa:** #23, #27, #29, #34, #35, #64, #65 y #66 pasaron a S1. #22, #38 y #45 pasaron a S2. #43 pasó a S4. #57 pasó a "Ajustes y entrega".

**Issues nuevos:** #73 a #95 (3 épicas y 20 tareas), con su dueño, su etapa y su épica.
