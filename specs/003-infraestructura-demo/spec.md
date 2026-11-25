# Spec 003: Infraestructura de la demo: guardar los cobros, abrir la demo local por un túnel y probar cada cambio

- **ID**: `003-infraestructura-demo`
- **Fecha**: `2026-11-17`
- **Estado**: `Aprobada` el 2026-11-20 por Hugo, con la QA de la versión con túnel (QA-12 a QA-20, §8.4) decidida y aplicada. Estado anterior: `Borrador` (cambio de rumbo). El 2026-11-17 el equipo decidió no montar nada en la nube por ahora (D-4): esta spec, que ese mismo día estaba `Aprobada` con Supabase + AWS + CI, se reescribió para que todo corra en local. En la entrevista del cambio de rumbo (E-6 a E-10), Hugo decidió que Supabase se queda, que la demo sale entera por un túnel con una dirección fija, que el CI se queda y que la demo se enciende solo en momentos acordados. La versión con AWS (spec, plan, QA del plan y C-9) queda en el historial de git, en el commit `fe837cc`, por si se retoma. Lo redactó Claude el 2026-11-17. Sin marcas abiertas. Propone el cambio C-6 a la spec 001 y el C-7 a la spec 002 (§8.2), que se aprueban aparte. Sigue vigente el C-8: el plan se aprueba cuando se unan los PR #72 y #96.
- **Rama**: `feature/90-infraestructura-demo`
- **Issues**: corte 1: #35 (CI), #65 (HTTPS y aviso de pey, ahora por el túnel) y #66 (README con el enlace de la demo y cuándo está encendida); corte 2: #90 (guardar cobros y pagos), #19 (conexión y cambios de estructura con un comando; el PR #99 de Juan lo referencia) y #94 (de dónde sale la imagen del QR) (QA-12, QA-20). #34 (AWS) y #57 (mantener la demo hasta el 31 de enero) quedan fuera y siguen abiertos. Con el pago real de esta spec se cierran #27 y #64; #29 queda abierto hasta el inicio de sesión (#24), porque también pide que un negocio no reciba avisos de otro (QA-6).
- **Entrada**: "Cambio de rumbo de la spec 003 (Hugo, 2026-11-17): por decisiones del equipo, por ahora no se monta nada en la nube; todo se hace local, y puede que se retome en el futuro. La base de datos sigue siendo Supabase (E-6). La web, el servidor y el aviso de pey salen por un túnel con HTTPS desde la computadora que corre la demo (E-7). El CI en cada pull request se queda (E-8). Salen AWS, el dominio propio, el presupuesto y la publicación." La entrada de la versión con AWS está en `fe837cc`.

> **Notas para los comandos de spec-kit.**
> - `RF-###` equivale a *Functional Requirement* (FR-###).
> - `CE-###` equivale a *Success Criterion* (SC-###).
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
>
> La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas de datos, los algoritmos y las firmas de funciones: eso va en `plan.md` y `tasks.md`. Toda la spec se escribe en español. Supabase se nombra solo porque es una decisión ya tomada por el equipo (constitución 3.0.0 del PR #96, tabla de restricciones técnicas; la QA-19 la lleva a 3.0.1). El servicio de túnel lo elige el plan, con su comparativa (principio IX).

---

## 1. Contexto y propósito (por qué)

Las specs 001 y 002 dejaron listo el recorrido completo: el dueño teclea el monto, enseña el QR, el cliente paga desde su banco y la pantalla suena. Pero hoy ese recorrido tiene dos huecos que impiden enseñarlo a los jueces y a un negocio piloto:

1. **No hay un enlace público que funcione bien.** Los entregables del hackathon piden una demo pública por enlace, y pey solo entrega sus avisos de pago a una dirección pública con HTTPS. En las pruebas del 16 de noviembre, sin aviso de pey, el primer pago tardó más de 30 segundos en reportarse. Además, los túneles gratuitos que se probaron retenían el canal de avisos o se cortaban. La promesa de "suena en menos de 2 segundos" (spec 002, CE-001 y CE-002) no se ha podido medir.
2. **El servidor olvida todo al reiniciarse.** Los cobros, los pagos y los avisos ya procesados viven en memoria (spec 001, §4, limitación aceptada hasta #23). Cada reinicio borra los cobros en curso: un cliente podría pagar un QR que el servidor ya no reconoce.

Esta spec cierra los dos huecos **sin nube**, y deja la base que van a usar las tres pantallas (web, Android e iOS) y las specs que siguen (inicio de sesión #24 e historial #38):

- el servidor guarda cobros, pagos y avisos en la base de datos del proyecto (Supabase, con el esquema de Juan del PR #97);
- la web, el servidor y el aviso de pey salen por un túnel con HTTPS desde la computadora que corre la demo, sin que el túnel retenga ni corte el canal de avisos;
- cada pull request se prueba solo, antes de que se revise.

Sin nube, la demo solo existe mientras la computadora de la demo y su túnel están encendidos (RF-060).

El comportamiento del cobro **no cambia**: lo que el dueño ve y oye es lo mismo que en las specs 001 y 002. Lo que cambia es que ahora sobrevive a un reinicio y se puede usar desde cualquier celular mientras la demo está encendida.

### 1.1 Glosario

Los términos *cobro*, *pago*, *monto fijo*, *monto libre*, *vigencia*, *ventana de escucha*, *canal de avisos*, *consulta de respaldo*, *aviso de pey* y los estados del cobro (*pendiente*, *pagado*, *vencido*, *cancelado*) significan lo mismo que en la [spec 001](../001-backend-mvp/spec.md#11-glosario). *Pantalla*, *vista* y *cobro en pantalla* significan lo mismo que en la [spec 002](../002-web-mvp/spec.md#11-glosario).

| Término | Significado en esta spec |
|---|---|
| Servidor | El backend de PAGO FÁCIL de la spec 001. Es el único que habla con pey y con la base de datos. |
| Base de datos | Donde el servidor guarda cobros, pagos y avisos para que sobrevivan a un reinicio. Es el proyecto de Supabase de la demo, que creó Juan (#19, #23); los servidores de desarrollo usan otro (RF-049). |
| Reinicio | Cualquier momento en que el servidor deja de correr y vuelve a arrancar: una versión nueva, una falla, la computadora que se apaga o se suspende, o un reinicio a mano. |
| Computadora de la demo | La computadora del equipo donde corren el servidor y el túnel de la demo. |
| Túnel | El servicio que le da a la computadora de la demo una dirección pública con HTTPS y le hace llegar las peticiones de los celulares y los avisos de pey, sin abrir puertos de la red donde está. |
| Demo pública | La web y el servidor de la computadora de la demo, abiertos por el túnel en una dirección HTTPS que cualquier celular abre sin invitación ni inicio de sesión. |
| Demo encendida | El servidor y el túnel corriendo en la computadora de la demo. |
| Servidor de desarrollo | El servidor que cada integrante corre en su computadora para programar y probar. Usa otra base de datos y otra llave de pey (RF-049 y RF-053). |
| Cambio de estructura | Crear o modificar las tablas de la base de datos (una *migración*). Incluye el esquema inicial del PR #97 y la columna nueva de la imagen del QR. |
| CI | La revisión automática que corre las pruebas y el lint en cada pull request y muestra el resultado en GitHub. |

### 1.2 Orden de entrega

Dos cortes (QA-12). Sustituyen a los de QA-1, cuyo corte 2 (publicación automática, RF-047, CE-012 y CE-013) salió con D-4. El orden va de lo que más desbloquea a lo que menos (P-1, E-5):

**Corte 1, a más tardar el domingo 22 de noviembre (puerta S1):**

1. **CI** (historia 5): desbloquea la revisión de lo que se une a `main`.
2. **Demo pública por el túnel y guía para encenderla** (historias 2 y 4), con los cobros todavía en memoria.
3. **Pago real desde la demo pública** (historia 3), que cierra #27 y #64.

**Corte 2, a más tardar el miércoles 25 de noviembre**, antes de construir las specs 004 y 005, que dependen de esta:

4. **Guardar cobros, pagos y avisos, cambios de estructura e imagen del QR** (historias 1 y 6), con la conciliación al arrancar (RF-061).

Las partes de la historia 4 que dependen de la base de datos (escenario 2, salud de la base de datos en CE-016) se comprueban en el corte 2.

---

## Aclaraciones

### Sesión 2026-11-17

- P: ¿Cómo evitamos que la base de datos de Supabase se pause antes del 31 de enero? → R: Plan gratuito, y el servidor publicado consulta la base de datos al menos una vez al día para que nunca pase una semana sin uso (RF-039, CE-012). *Ajustada por D-4: sin un servidor siempre encendido, la consulta solo pasa mientras hay un servidor encendido; si se pausa, Hugo lo reactiva con su guía (RF-039 y RF-050). CE-012 se retiró.*
- P: Si el presupuesto apaga el servidor al llegar a 200 dólares, ¿quién lo vuelve a encender y con qué criterio? → R: Solo Hugo, después de revisar qué consumió el crédito y corregir la causa (RF-040, RF-041). *Sustituida por D-4: no hay presupuesto.*
- P: ¿Con qué dirección se publica la demo? → R: La que asigna AWS, con su HTTPS, sin dominio propio (RF-024). *Sustituida por C-9 y después por D-4: la dirección es la del túnel (RF-024 y RF-030).*
- P: ¿Cómo se publica una versión nueva del servidor y la web en la demo? → R: Automáticamente cada vez que se une un pull request a `main` (RF-042 a RF-045). *Sustituida por D-4: Hugo actualiza la computadora de la demo con su guía (RF-058).*
- P: ¿Se aplican también solos los cambios de estructura de la base de datos al publicar? → R: No. La publicación solo sube código; Hugo aplica las migraciones a mano con el comando, después de revisarlas (RF-046, RF-047). *Sustituida por D-4: no hay publicación; Hugo aplica el comando al encender la demo (RF-058).*

---

## 2. Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — No perder cobros ni pagos si el servidor se reinicia (Prioridad: P1)

**Como** dueño de la tiendita, **quiero** que mi cobro y sus pagos sigan ahí aunque el servidor se reinicie, **para** que el cliente que ya escaneó el QR no pague a un cobro que nadie escucha.

**Por qué esta prioridad:** los reinicios pasan solos: una versión nueva, una falla o la computadora de la demo que se apaga o se suspende. Sin esto, la demo perdería pagos, y la constitución dice que el sistema nunca pierde un pago (principio VIII).

**Prueba independiente:** crear un cobro, reiniciar el servidor, recargar la pantalla y pagar ese QR con $0.01: la pantalla vuelve a mostrar el QR y suena "Pago recibido".

**Escenarios de aceptación:**

1. **Dado** un cobro *pendiente* con su QR en pantalla, **cuando** el servidor se reinicia y el dueño recarga la página, **entonces** la pantalla vuelve a mostrar el mismo QR, con el monto, el concepto y el tiempo que le queda.
2. **Dado** un cobro creado antes de un reinicio, **cuando** llega su aviso de pago de pey después del reinicio, **entonces** el pago se registra y la pantalla suena, igual que si no hubiera habido reinicio.
3. **Dado** un cobro creado antes de un reinicio, **cuando** el aviso de pey no llega pero la consulta de respaldo encuentra el pago, **entonces** el pago se registra y la pantalla suena.
4. **Dado** un cobro con dos pagos ya registrados, **cuando** el servidor se reinicia, **entonces** al consultarlo devuelve los dos pagos con su número, monto y hora, y el siguiente pago es el número 3.
5. **Dado** un cobro *cancelado* o *vencido* antes de un reinicio, **cuando** el servidor arranca, **entonces** el cobro conserva su estado y sus pagos tardíos se siguen registrando dentro de la ventana de escucha.
6. **Dado** un cobro cuya imagen del QR no mandó pey, **cuando** se consulta después de un reinicio, **entonces** se devuelve sin imagen y la pantalla muestra "No se pudo mostrar el QR. Intenta de nuevo." (spec 002, C-3).
7. **Dado** que la base de datos no responde, **cuando** el dueño pide un cobro nuevo, **entonces** el servidor no le pide el QR a pey y la pantalla muestra un mensaje para el dueño.
8. **Dado** un cobro pagado mientras el servidor estaba apagado, cuya ventana de escucha terminó antes de que volviera, **cuando** el servidor arranca, **entonces** consulta el cobro en pey y registra el pago, sin sonido, para que aparezca en el historial (QA-14).

---

### Historia 2 — Abrir la demo desde cualquier celular (Prioridad: P1)

**Como** juez del hackathon o dueño de un negocio piloto, **quiero** abrir un enlace con HTTPS desde mi celular y cobrar, **para** probar PAGO FÁCIL sin instalar nada ni pedir acceso.

**Por qué esta prioridad:** es la "demo pública por enlace" de los entregables del hackathon y la dirección a la que pey entrega sus avisos. Sin ella no se puede medir la promesa de los 2 segundos.

**Prueba independiente:** con la demo encendida, abrir el enlace con datos móviles (no el wifi de la computadora de la demo) en un Android y en un iPhone, crear un cobro y ver el QR.

**Escenarios de aceptación:**

1. **Dado** la demo encendida y un celular con datos móviles, **cuando** abre la dirección pública, **entonces** carga la pantalla de cobro con HTTPS, sin advertencias del navegador ni inicio de sesión.
2. **Dado** la demo pública, **cuando** el dueño crea un cobro, **entonces** ve el QR en 5 segundos o menos, en 9 de cada 10 intentos (C-10).
3. **Dado** un cobro en pantalla, **cuando** el cliente lo paga, **entonces** el aviso de pey llega al servidor a través del túnel, con su firma válida.
4. **Dado** un canal de avisos abierto por la dirección pública, **cuando** pasa toda la ventana de escucha (20 minutos con la vigencia actual), **entonces** el canal sigue abierto hasta que el servidor lo cierra por fin de ventana, sin cortes del túnel.
5. **Dado** un canal de avisos abierto por la dirección pública, **cuando** el servidor emite un evento, **entonces** la pantalla lo recibe en ese momento, sin que el túnel lo retenga hasta cerrar el canal.
6. **Dado** una página de otro dominio, **cuando** intenta usar el servidor desde el navegador, **entonces** el navegador lo bloquea.
7. **Dado** otro equipo conectado a la misma red que la computadora de la demo, **cuando** intenta conectarse directo al servidor sin pasar por el túnel, **entonces** no recibe respuesta.
8. **Dado** que el servidor, el túnel o la computadora de la demo se reinician, **cuando** vuelven, **entonces** la dirección pública y la del aviso de pey son las mismas que antes.

---

### Historia 3 — Oír el pago real en menos de 2 segundos desde la demo pública (Prioridad: P1)

**Como** dueño de la tiendita, **quiero** que la pantalla suene en cuanto el cliente paga, **para** entregarle su mercancía sin esperar ni revisar mi banco.

**Por qué esta prioridad:** es el "momento del pago" que más pesa en la evaluación y el criterio que falta para cerrar #27 y #64 (#29 espera además al inicio de sesión, #24).

**Prueba independiente:** con autorización de Hugo, cobrar $0.01 desde la demo pública en un Android y en un iPhone, pagar desde otro celular y medir el tiempo entre que pey entrega el aviso y la pantalla muestra "Pago recibido".

**Escenarios de aceptación:**

1. **Dado** un cobro de $0.01 en la demo pública, en un Android con datos móviles, **cuando** el cliente paga desde la app de su banco, **entonces** la pantalla suena y muestra "Pago recibido" en menos de 2 segundos después de que pey entrega el aviso.
2. **Dado** lo mismo en un iPhone, **cuando** el cliente paga, **entonces** pasa lo mismo.
3. **Dado** un pago real ya avisado, **cuando** pey reenvía el aviso, **entonces** la pantalla no vuelve a sonar y el cobro sigue con un solo pago.

---

### Historia 4 — Encender la demo cuando hace falta (Prioridad: P2)

**Como** Hugo, responsable del proyecto, **quiero** encender la demo siguiendo una sola guía y comprobar desde fuera que todo responde, **para** enseñarla a los jueces o a un negocio piloto sin improvisar.

**Por qué esta prioridad:** sin nube, la demo no está siempre encendida. Cada vez que se enciende hay que poner al día el código, arrancar el servidor y el túnel y comprobar la base de datos. Va después de las historias 1 a 3 porque solo importa cuando ya funcionan.

**Prueba independiente:** con la computadora de la demo recién encendida, seguir la guía y pedir la salud del servidor por la dirección pública desde un celular con datos móviles.

**Escenarios de aceptación:**

1. **Dado** la computadora de la demo encendida, **cuando** Hugo sigue la guía, **entonces** la salud del servidor pedida por la dirección pública indica que el servidor responde y que la base de datos y pey están configurados y responden.
2. **Dado** que el proyecto de Supabase se pausó, **cuando** Hugo enciende la demo, **entonces** la salud lo indica y la guía le dice cómo reactivarlo.
3. **Dado** un cobro en pantalla, **cuando** la computadora de la demo se suspende o pierde internet y después vuelve, **entonces** la pantalla se reconecta sola y los pagos de ese rato se registran por la consulta de respaldo o por un aviso reenviado, si llegan dentro de la ventana de escucha.
4. **Dado** la demo apagada, **cuando** alguien abre el enlace, **entonces** ve el error del túnel o de su navegador; no hay página de "demo en pausa" (E-3).

---

### Historia 5 — Saber antes de unir un pull request si algo se rompió (Prioridad: P1)

**Como** integrante que une su propio pull request (constitución 3.0.0), **quiero** ver en cada pull request si las pruebas y el lint pasan, **para** no tener que correrlos a mano ni unir algo roto.

**Por qué esta prioridad:** cada quien une su PR cuando el CI está en verde, y Juan y Leonel revisan después lo que entró a `main`. Es lo más rápido de entregar y lo primero que desbloquea.

**Prueba independiente:** abrir un pull request con un error a propósito y ver que el CI falla; corregirlo y ver que pasa.

**Escenarios de aceptación:**

1. **Dado** un pull request hacia `main`, **cuando** se abre o se le suben cambios, **entonces** corren las pruebas y el lint del servidor y de la web, y el resultado aparece en el pull request.
2. **Dado** un pull request con una prueba que falla o un error de lint, **cuando** termina el CI, **entonces** el pull request se marca como fallido y no se puede unir.
3. **Dado** cualquier pull request, incluido uno desde un fork, **cuando** corre el CI, **entonces** no usa pey real, la base de datos real ni ningún secreto.

---

### Historia 6 — Cambiar la estructura de la base de datos con un comando (Prioridad: P2)

**Como** Hugo o Juan, **quiero** crear o actualizar las tablas con un solo comando, igual en desarrollo y en la demo, **para** no pegar SQL a mano en el editor de Supabase y no dejar la base de la demo distinta de lo que dice el repositorio.

**Por qué esta prioridad:** hoy el esquema de #97 se corre a mano. Esta spec agrega una columna (la imagen del QR) y las specs de inicio de sesión e historial van a agregar más. Sin un comando repetible, la base de datos de la demo y la del repositorio terminan siendo distintas.

**Prueba independiente:** aplicar el comando en una base de datos vacía y después otra vez seguida: la primera crea todo y la segunda no cambia nada ni marca error. En la base de la demo, el comando lo corre solo Hugo.

**Escenarios de aceptación:**

1. **Dado** una base de datos vacía, **cuando** se aplica el comando, **entonces** queda la estructura del PR #97 más la columna de la imagen del QR.
2. **Dado** una base de datos ya al día, **cuando** se aplica el comando otra vez, **entonces** no cambia nada, no borra datos y no marca error.
3. **Dado** la base de datos de la demo con el esquema de #97 ya corrido a mano, **cuando** se aplica el comando, **entonces** solo agrega lo que falta, sin borrar datos.

---

## 3. Requisitos *(obligatorio)*

### 3.1 Requisitos funcionales (notación EARS)

Los números retirados por D-4 no se reutilizan (§8.1).

**Guardar cobros, pagos y avisos** (historia 1)

- **RF-001** (Ubicuo): EL SISTEMA guardará en la base de datos cada cobro creado, con todo lo que la spec 001 devuelve de él (RF-008), incluida la imagen del QR cuando pey la manda.
- **RF-002** (Ubicuo): EL SISTEMA guardará en la base de datos cada pago registrado antes de emitirlo por el canal de avisos.
- **RF-003** (Ubicuo): EL SISTEMA guardará en la base de datos el identificador de cada aviso de pey ya procesado.
- **RF-004** (Ubicuo): EL SISTEMA guardará en la base de datos la cancelación de cada cobro con su hora.
- **RF-005** (Dirigido por evento): CUANDO el servidor arranca, EL SISTEMA atenderá los cobros guardados (consultar, abrir el canal, consulta de respaldo, cancelar y registrar pagos) igual que si no se hubiera reiniciado.
- **RF-006** (Ubicuo): EL SISTEMA calculará el estado y la ventana de escucha de un cobro guardado con la hora del servidor, no con la de la base de datos, y las mismas reglas de la spec 001 (RF-017, RF-021 y RF-022), haya habido reinicio o no (QA-11). Las horas que guarda (creación, vencimiento, pago y cancelación) las pone el servidor con su reloj, no la base de datos (QA-18).
- **RF-007** (Ubicuo): EL SISTEMA registrará cada transacción pagada de pey una sola vez, aunque el aviso y la consulta de respaldo la traigan al mismo tiempo, aunque pey reenvíe el aviso y aunque haya habido un reinicio entre las dos llegadas.
- **RF-008** (Ubicuo): EL SISTEMA numerará los pagos de un cobro sin saltos ni repetidos (1, 2, 3…), haya habido reinicio o no.
- **RF-009** (Ubicuo): EL SISTEMA no guardará en la base de datos ni escribirá en los registros los datos de quien paga (nombre, CLABE o cuenta, banco, teléfono ni clave de rastreo), aunque pey los mande en el aviso o en la consulta; de cada pago solo guarda lo que pide la spec 001 (RF-018) (QA-10).
- **RF-061** (Dirigido por evento): CUANDO el servidor arranca, EL SISTEMA consultará en pey los cobros guardados cuya ventana de escucha terminó mientras estaba apagado y registrará sus pagos una sola vez (RF-007), sin emitirlos por el canal porque nadie los escucha, para que el sistema nunca pierda un pago (principio VIII) (QA-14).

**Imagen del QR** (historia 1, decisión de #94)

- **RF-010** (Dirigido por evento): CUANDO se consulta un cobro guardado, EL SISTEMA devolverá la imagen del QR que pey mandó al crearlo, haya habido reinicio o no.
- **RF-011** (No deseado): SI pey no mandó la imagen del QR al crear el cobro, ENTONCES EL SISTEMA devolverá el cobro sin imagen, como hoy (la pantalla aplica RF-078 de la spec 002).

**Fallas de la base de datos** (historia 1)

- **RF-012** (No deseado): SI la base de datos no responde al crear un cobro, ENTONCES EL SISTEMA no le pedirá el QR a pey y responderá con un mensaje para el dueño.
- **RF-052** (No deseado): SI pey no crea el QR de un cobro que el servidor ya había guardado, ENTONCES EL SISTEMA borrará ese cobro de la base de datos, para que no quede ni aparezca en el historial (#38), como pide RF-009 de la spec 001 (QA-8).
- **RF-013** (No deseado): SI pey ya creó el QR pero la base de datos no responde al guardarlo, ENTONCES EL SISTEMA no devolverá el QR a la pantalla y responderá con un mensaje para el dueño, para que nadie pague un QR que el servidor no recuerda.
- **RF-014** (No deseado): SI la base de datos no responde al registrar un pago que llegó por el aviso de pey, ENTONCES EL SISTEMA le responderá a pey con error (por si lo reenvía), no emitirá el pago por el canal y conservará el aviso en memoria para registrarlo después.
- **RF-048** (Estado): MIENTRAS el servidor conserva avisos de pago sin registrar por una falla de la base de datos, EL SISTEMA reintentará registrarlos cada 15 segundos y, al lograrlo, emitirá cada pago por el canal como en RF-002. pey no documenta si reenvía un aviso respondido con error, así que el servidor no depende de ello (QA-3).
- **RF-015** (No deseado): SI la base de datos no responde al consultar un cobro, ENTONCES EL SISTEMA responderá con un error temporal distinto de "cobro inexistente", para que la pantalla siga reintentando en lugar de mostrar la vista Error (spec 002, RF-057).
- **RF-016** (Ubicuo): EL SISTEMA dejará un registro de cada falla de la base de datos, con el identificador del cobro cuando lo haya, sin credenciales ni datos bancarios.

**Cambios de estructura** (historia 6)

- **RF-017** (Ubicuo): EL SISTEMA creará y actualizará la estructura de la base de datos con un solo comando, el mismo en los servidores de desarrollo y en la demo.
- **RF-018** (Ubicuo): EL SISTEMA incluirá en ese comando el esquema del PR #97 y la columna nueva de la imagen del QR.
- **RF-019** (Dirigido por evento): CUANDO se aplica el comando a una base de datos que ya está al día, EL SISTEMA no cambiará nada ni borrará datos.
- **RF-049** (Ubicuo): EL SISTEMA usará en los servidores de desarrollo una base de datos distinta de la de la demo, para que las pruebas de desarrollo no queden en los datos de la demo (QA-4).
- **RF-053** (Ubicuo): EL SISTEMA usará en los servidores de desarrollo una segunda llave de producción de pey, distinta de la de la demo y con su propio aviso; quien prueba sin túnel lo hace sin aviso, con la consulta de respaldo. El ambiente de pruebas de pey se propone aparte cuando pey lo publique (E-1, QA-15).
- **RF-054** (Ubicuo): EL SISTEMA cargará los datos de prueba ficticios solo en la base de datos de desarrollo, nunca en la de la demo (E-2).
- **RF-051** (Dirigido por evento): CUANDO Hugo va a aplicar un cambio de estructura en la base de datos de la demo, EL SISTEMA le indicará en su guía que primero exporte una copia de esa base de datos, porque el plan gratuito no incluye respaldos (QA-5).

**Credenciales y acceso** (historias 1 y 2)

- **RF-020** (Ubicuo): EL SISTEMA solo leerá las credenciales de la base de datos de la configuración del servidor en la computadora donde corre, nunca del repositorio.
- **RF-021** (Ubicuo): EL SISTEMA nunca incluirá las credenciales de la base de datos en sus respuestas, mensajes de error o registros.
- **RF-059** (Ubicuo): EL SISTEMA guardará las credenciales del túnel, si el servicio las pide, solo en la computadora de la demo; nunca en el repositorio, en las respuestas ni en los registros.
- **RF-022** (Ubicuo): EL SISTEMA solo permitirá leer y escribir los datos guardados desde el servidor; la web, las apps y cualquiera con la dirección pública de la base de datos no podrán leerlos ni cambiarlos.
- **RF-023** (Dirigido por evento): CUANDO se consulta la salud del servidor, EL SISTEMA indicará además si la base de datos está configurada y responde, sin mostrar sus valores (amplía RF-038 de la spec 001, cambio C-6).
- **RF-039** (Estado): MIENTRAS el servidor está encendido, EL SISTEMA consultará la base de datos al menos una vez al día, aunque nadie cree cobros, para que el plan gratuito no la pause por falta de uso.
- **RF-050** (Ubicuo): EL SISTEMA tendrá en la guía de Hugo los pasos para reactivar el proyecto de Supabase de la demo si se pausa, y para comprobar después con la salud del servidor que la base de datos responde (QA-5). La guía también pide encender la demo y comprobar la salud al menos cada 5 días y el día antes de cada momento acordado, para que el proyecto no pase 7 días sin uso (QA-13).

**Demo pública por el túnel** (historias 2, 3 y 4)

- **RF-024** (Estado): MIENTRAS la demo está encendida, EL SISTEMA abrirá la web y el servidor por el túnel en una dirección pública con HTTPS, y cualquier celular la abrirá sin invitación ni inicio de sesión (E-7).
- **RF-060** (Estado): MIENTRAS dura un momento acordado por el equipo (pruebas, grabación del video, demos con negocios piloto y las pruebas de Leonel antes de cada puerta) o la evaluación, sin parar desde la entrega del 12 de diciembre hasta el anuncio del 14 de diciembre, EL SISTEMA estará encendido en la computadora de Hugo y responderá en la dirección pública; fuera de esos momentos la demo puede estar apagada (E-9, QA-13).
- **RF-056** (Ubicuo): EL SISTEMA solo atenderá las peticiones que llegan de fuera de la computadora de la demo a través del túnel; otro equipo de la misma red que intente conectarse directo al servidor no recibirá respuesta, porque por ahí pasarían sin cifrar los avisos de pey con los datos bancarios de quien paga.
- **RF-025** (Ubicuo): EL SISTEMA recibirá los avisos de pey en la dirección pública del túnel, dada de alta en el portal de pey con su secreto.
- **RF-026** (Estado): MIENTRAS un canal de avisos está dentro de la ventana de escucha de su cobro, EL SISTEMA lo mantendrá abierto, sin cortes del túnel, durante toda esa ventana y hasta que el servidor lo cierre (hoy, 20 minutos; con F-04, de la spec 004, puede ser más) (QA-17).
- **RF-057** (Ubicuo): EL SISTEMA hará llegar cada evento del canal de avisos a la pantalla en el momento en que el servidor lo emite, sin que el túnel lo retenga. En las pruebas de la 002, el túnel rápido de Cloudflare retuvo los eventos hasta que se cerró el canal.
- **RF-027** (Ubicuo): EL SISTEMA aceptará peticiones del navegador solo desde la dirección de la web de la demo (aplica RF-035 de la spec 001 con la dirección real).
- **RF-028** (Ubicuo): EL SISTEMA aplicará los límites por IP de la spec 001 (RF-034 y RF-041) con la IP real del celular, no con la del túnel.
- **RF-029** (Ubicuo): EL SISTEMA hará que la web de la demo solo se conecte a su propio servidor.
- **RF-030** (Dirigido por evento): CUANDO el servidor, el túnel o la computadora de la demo se reinician, EL SISTEMA conservará la misma dirección pública y la misma dirección del aviso de pey, para que el enlace de la entrega del hackathon y el aviso dado de alta en pey sigan sirviendo (E-10).
- **RF-058** (Ubicuo): EL SISTEMA tendrá una guía para Hugo con los pasos para encender y apagar la demo: poner al día la computadora de la demo con `main`, aplicar los cambios de estructura pendientes (RF-017 y RF-051), arrancar el servidor y el túnel, y comprobar la salud por la dirección pública.

**CI** (historia 5)

- **RF-036** (Dirigido por evento): CUANDO se abre un pull request hacia `main` o se le suben cambios, EL SISTEMA correrá las pruebas y el lint del servidor y de la web, y mostrará el resultado en el pull request.
- **RF-037** (No deseado): SI una prueba o el lint fallan, ENTONCES EL SISTEMA marcará el pull request como fallido e impedirá unirlo.
- **RF-038** (Ubicuo): EL SISTEMA correrá las revisiones de los pull requests sin pey real, sin la base de datos real y sin ningún secreto.

### 3.2 Entidades clave

- **Cobro**: lo mismo que en la spec 001, ahora guardado. Se le agrega la imagen del QR que manda pey (puede faltar). Queda sin negocio asociado hasta el inicio de sesión (#24).
- **Pago**: lo mismo que en la spec 001, ahora guardado. Su identificador de transacción de pey es único en todo el sistema.
- **Aviso de pey procesado**: el identificador de cada aviso ya atendido, para descartar reenvíos (primera barrera del principio II).
- **Cambio de estructura**: cada modificación de las tablas, con un orden y un registro de cuáles ya se aplicaron en cada base de datos.

Los límites por IP y los canales abiertos **no** se guardan: siguen en la memoria del servidor y empiezan de cero tras un reinicio (§4).

---

## 4. Casos límite y manejo de errores

| Caso | Comportamiento esperado | Requisitos |
|---|---|---|
| **Pago tardío** tras un reinicio (el QR venció antes o después del reinicio) | Se registra y se avisa si llega dentro de la ventana de escucha, igual que sin reinicio. | RF-005, RF-006 |
| **Monto distinto** al pedido | Sin cambios respecto a la spec 001 (RF-019 y RF-020); el monto base y el recibido quedan guardados. | RF-002 |
| **Falla de pey** al crear el QR | Sin cambios respecto a la spec 001 (RF-009 y RF-010): el cobro que se había guardado se borra y la pantalla muestra el mensaje. | RF-052 |
| **Falla del aviso de pey** (no llega o llega tarde) | La consulta de respaldo sigue funcionando, también para cobros creados antes de un reinicio. | RF-005 |
| El aviso de pey y la consulta de respaldo traen el mismo pago a la vez | Se registra una sola vez y la pantalla suena una sola vez. | RF-007 |
| La base de datos no responde al crear un cobro | No se le pide el QR a pey; mensaje para el dueño. | RF-012 |
| La base de datos falla justo después de que pey creó el QR | La pantalla no recibe el QR y ve un mensaje; ese QR queda sin enseñarse. | RF-013 |
| La base de datos no responde cuando llega un aviso de pago | Se le responde con error a pey, por si lo reenvía, y el servidor conserva el aviso y reintenta registrarlo cada 15 s; el pago se registra y suena cuando la base de datos vuelve. | RF-014, RF-048 |
| El servidor se reinicia con avisos todavía sin registrar | Esos avisos se pierden de la memoria. El pago se recupera si pey reenvía el aviso, si la consulta de respaldo lo encuentra dentro de la ventana de escucha o, después de la ventana, con la conciliación al arrancar. | RF-014, RF-048, RF-061 |
| La base de datos no responde al consultar un cobro | Error temporal; la pantalla muestra "Reconectando…" y reintenta, sin ir a la vista Error. | RF-015 |
| Aviso de pey de un QR que no está en la base de datos | Se le responde bien a pey y queda registro, como en la spec 001. Ya no se espera por reinicio: solo por un QR ajeno o por RF-013. | RF-016 |
| Reinicio con canales de avisos abiertos | Los canales se cortan; la pantalla aplica su respaldo y su reconexión (spec 002, historia 4) y recibe el estado guardado. | RF-005 |
| Límites por IP tras un reinicio | Empiezan de cero. Limitación aceptada: un reinicio no es algo que un atacante provoque. | — |
| El proyecto de Supabase está pausado o sin servicio | Si en 7 días nadie enciende un servidor, Supabase puede pausar el proyecto, y no garantiza qué cuenta como uso (RF-039). Si no responde, la salud del servidor lo indica, los cobros nuevos se rechazan con un mensaje (RF-012) y Hugo lo reactiva con su guía (RF-050). | RF-012, RF-023, RF-039, RF-050 |
| Una migración daña datos de la demo | El plan gratuito no tiene respaldos: Hugo restaura la copia que exportó antes de aplicarla. | RF-051 |
| La computadora de la demo se suspende, se apaga o pierde internet | La demo deja de responder y la pantalla muestra "Reconectando…". Al volver, los pagos de ese rato se registran por la consulta de respaldo o por un aviso reenviado, si llegan dentro de la ventana de escucha. Si la ventana termina con la demo apagada, el pago se registra al volver a arrancar, sin sonido, y aparece en el historial; la pantalla no lo avisa en su momento (limitación de correr en una computadora). | RF-005, RF-060, RF-061 |
| El túnel se cae con la demo encendida | Igual que la fila anterior. La guía de Hugo dice cómo volver a arrancarlo; la dirección sigue siendo la misma (RF-030). | RF-030, RF-058 |
| Un juez abre el enlace fuera de un momento acordado | Ve el error del túnel o de su navegador. El video y las instrucciones de prueba de la entrega muestran el flujo completo y dicen cuándo está encendida la demo. | RF-060 |
| El túnel retiene los eventos del canal o lo corta antes de que termine la ventana de escucha | Incumple RF-026 y RF-057. El plan elige un túnel que no lo haga y lo prueba antes que todo lo demás de la demo pública. | RF-026, RF-057 |
| Otro equipo de la misma red intenta conectarse directo al servidor | No recibe respuesta: el servidor solo atiende lo que llega por el túnel. | RF-056 |
| La demo está apagada | Quien abre el enlace ve el error del túnel o de su navegador; no hay página de "demo en pausa". | RF-060, E-3 |
| El servicio de túnel termina el HTTPS en sus servidores | Ve sin cifrar los avisos de pey, con los datos de quien paga. Si el túnel elegido no termina el HTTPS en la computadora de la demo, queda como limitación aceptada y escrita, igual que con cualquier hosting (§7, criterios del túnel). | RF-056, §7 |
| **Devolución** | Fuera de alcance, como en la spec 001: pey no ofrece devoluciones por API. | — |

---

## 5. Fuera de alcance *(obligatorio)*

| Fuera de alcance | Dónde se resuelve |
|---|---|
| Publicar en la nube (AWS u otro hosting), dominio propio, presupuesto de AWS y publicación automática al unir a `main` | Decisión del equipo del 2026-11-17 (D-4). Se puede retomar con otra spec; la versión con AWS está en el commit `fe837cc`. #34 sigue abierto |
| Avisar en la salud de un cambio de estructura sin aplicar (antes RF-047) | Sin publicación automática, Hugo aplica el comando al encender la demo (RF-058) |
| Registro e inicio de sesión del negocio; ligar cada cobro a su negocio | #24 (spec propia) |
| Historial de cobros y corte del día | #38 (spec propia) |
| Cuenta bancaria propia por negocio | Espera la respuesta de pey (flujo-de-trabajo §7, "Punto abierto") |
| Logs centralizados, monitor de disponibilidad y alertas si la demo se cae | #45 |
| Dibujar el QR en el servidor | Decidido en #94: se usa la imagen de pey (D-2) |
| Guardar los límites por IP y los canales abiertos | No hace falta mientras corra un solo servidor |
| Varios servidores a la vez o escalado automático | La spec 001 exige un solo proceso (E-4) |
| Página de "demo en pausa" cuando la demo está apagada | No se construye: se ve el error del túnel o del navegador (E-3) |
| Cupones | #37 |
| Demo encendida sin parar fuera de la evaluación (por ejemplo, hasta el 31 de enero) | Solo en momentos acordados y del 12 al 14 de diciembre (E-9, QA-13, RF-060). #57 sigue abierto por si se retoma la nube |

---

## 6. Criterios de éxito *(obligatorio)*

- **CE-001**: un cobro creado antes de un reinicio del servidor de la demo se paga con $0.01 después del reinicio, y la pantalla recargada vuelve a mostrar su QR y suena "Pago recibido".
- **CE-002**: desde la demo pública, con datos móviles, un pago real de $0.01 suena y muestra "Pago recibido" en menos de 2 segundos después de que pey entrega el aviso, en un Android y en un iPhone. Cierra #27 y #64 (spec 002, CE-001 y CE-002). #29 queda abierto hasta el inicio de sesión (#24), con una nota (QA-6).
- **CE-003**: desde la demo pública, el dueño ve el QR en 5 segundos o menos después de tocar Cobrar, en 9 de cada 10 intentos (C-10; antes, menos de 3 segundos).
- **CE-004**: un canal de avisos abierto por la dirección pública dura los 20 minutos de vigencia y ventana actuales sin cortarse antes de que el servidor lo cierre, y un pago avisado después del minuto 15 de ese canal suena en menos de 2 segundos.
- **CE-005**: ninguna transacción se registra dos veces, comprobado con pruebas automáticas de aviso reenviado, de aviso y consulta simultáneos y de llegada antes y después de un reinicio.
- **CE-006**: todo pull request hacia `main` muestra el resultado del CI, y uno con un error a propósito queda marcado como fallido y no se puede unir.
- **CE-007**: el comando de cambios de estructura se aplica dos veces seguidas sobre una base de datos vacía sin error, y la segunda vez no cambia nada.
- **CE-010**: ninguna credencial de pey, de la base de datos ni del túnel aparece en el repositorio, en las respuestas del servidor ni en sus registros, comprobado con búsquedas en el repositorio y con pruebas automáticas.
- **CE-011**: todas las pruebas automáticas pasan sin conexión a pey ni a la base de datos real.
- **CE-015**: con la demo encendida, la dirección pública abre con HTTPS, y una conexión directa al servidor desde otro equipo de la misma red no recibe respuesta.
- **CE-016**: Hugo enciende la demo con la computadora recién prendida siguiendo solo su guía, y la salud pedida por la dirección pública, desde un celular con datos móviles, indica que el servidor responde y que la base de datos y pey están configurados y responden.
- **CE-017**: un pago de un cobro cuya ventana de escucha terminó con el servidor apagado queda registrado una sola vez al volver a arrancar, comprobado con pruebas automáticas con pey simulado (RF-061).

---

## 7. Supuestos y dependencias

**Supuestos**

- La computadora de la demo es la de Hugo. Mientras la demo está encendida, esa computadora sigue prendida, sin suspenderse y con internet.
- Existe un servicio de túnel gratuito que cumple los **criterios del túnel** (QA-16). El plan los compara con su comparativa (principio IX):
  1. HTTPS sin advertencias ni páginas intermedias en el navegador (historia 2, escenario 1);
  2. entrega los eventos del canal sin retenerlos (RF-057);
  3. no corta el canal durante toda la ventana de escucha (RF-026); la comparativa anota cuánto aguanta un canal abierto (QA-17);
  4. dirección fija, aunque para eso pida una cuenta gratuita (RF-030);
  5. hace llegar al servidor la IP real del celular (RF-028);
  6. gratuito;
  7. de preferencia, el HTTPS termina en la computadora de la demo, para que el servicio no vea los avisos de pey sin cifrar; si no, queda como limitación aceptada (§4).

  Los dos que se probaron en la 002 no cumplían: el túnel rápido de Cloudflare retuvo el canal y el de `localhost.run` se cortó cada ~16 minutos (`specs/002-web-mvp/verification-guide.md`). Si solo hay opción de pago, es una decisión nueva de Hugo.
- Supabase se queda en el plan gratuito. Su documentación dice que "may pause" los proyectos gratuitos con poca actividad en 7 días, sin definir qué cuenta como actividad, y que el plan gratuito no incluye respaldos (QA-5). Sin un servidor siempre encendido, la consulta diaria (RF-039) solo pasa mientras hay uno encendido; si el proyecto se pausa, Hugo lo reactiva (RF-050). Pasar al plan de pago es una decisión nueva de Hugo.
- pey admite un solo webhook por llave, así que la demo y los servidores de desarrollo usan llaves distintas (RF-053). El ambiente de pruebas de pey está "coming soon" en su documentación oficial (solo `docs.pey.mx/llms.txt` menciona `https://api.dev.pey.mx`), así que desarrollo usa una segunda llave de producción, ligada en el portal a la misma cuenta CoDi del titular (QA-15). Se supone que el portal permite ligar una cuenta CoDi a dos llaves; Hugo lo confirma al crearla. Las CLABEs que se den de alta por el API (`POST /bank-account`) quedan bajo la llave que las registró. El aviso de desarrollo llega por un túnel a la computadora de quien prueba (E-1).
- El servidor no usa el estado que calcula la vista `cobros_con_estado` del PR #97 (con la hora de la base de datos): lo calcula él con su reloj (RF-006). Se le avisó a Juan en la revisión del PR #97, y el plan lo registra como decisión (QA-11).
- El servidor sigue corriendo como un solo proceso, como exige la spec 001 (plan, QP-5): los canales de avisos y los límites por IP viven en su memoria.
- La base de datos no guarda la CLABE ni datos bancarios del negocio (comentario de la tabla de negocios del PR #97).
- La imagen del QR de pey pesa unos pocos KB por cobro, así que guardarla no compromete el espacio de la base de datos durante el hackathon. Pedirla a pey puede ser lento (plan de la 001, TK-5): se mide con CE-003.
- No hay costo: Supabase gratuito, CI gratuito en un repositorio público y túnel gratuito.

**Dependencias**

| Dependencia | Para qué | Dueño | Estado |
|---|---|---|---|
| PR #97 unido (esquema inicial) | RF-018 y todo el guardado | Hugo | Unido por Hugo el 2026-11-17 (`f773939`); cerró #23 |
| Proyecto de Supabase de la demo | Base de datos de la demo | Juan (#19) | Creado, según Hugo y el PR #97 |
| Segundo proyecto gratuito de Supabase para desarrollo | RF-049 (QA-4) | Juan (dueño de la organización de Supabase) | Pendiente |
| Credenciales de Supabase en la configuración del servidor de cada computadora | RF-020 | Hugo y cada integrante | Pendiente |
| Servicio de túnel elegido, con su dirección fija y su cuenta si la pide | RF-024, RF-026, RF-030, RF-057 | Hugo | Se elige en el plan |
| Aviso dado de alta en el portal de pey con la dirección del túnel | RF-025 | Hugo (#15) | Pendiente; depende del túnel |
| Segunda llave de producción de pey para desarrollo, ligada a la cuenta CoDi del titular, con su aviso | RF-053 (E-1, QA-15) | Hugo | Pendiente |
| Protección de la rama `main` que exige el CI y ya no exige aprobación (constitución 3.0.0) | RF-037 | Quien administra el repositorio (organización `team-complexity`) | Pendiente |
| Prueba de la demo desde fuera de la red del equipo (N-17) | RF-024, RF-060 | Leonel | Pendiente; necesita la demo encendida |
| PR #72 unido (web de cobro en `main`), **antes de aprobar el plan** | La demo sirve la web desde `main`; esta rama sale de la suya (QA-9, C-8) | Hugo (une su PR, constitución 3.0.0) | Unido el 2026-11-21, con los 4 cambios que pidió Juan atendidos (`Refs #64`, descripción al día, reparto de #64 con Miguel y fase FN) |
| PR #96 unido (constitución 3.0.0, con el parche 3.0.1 de QA-19), **antes de aprobar el plan** | La verificación de la constitución del plan se hace contra esa versión (QA-9, C-8) | Hugo | Unido el 2026-11-21 con la 3.0.1 |
| Computadora de la demo con internet estable | RF-024, RF-060 | Hugo | Disponible |
| Un Android, un iPhone y la autorización de Hugo para pagos de $0.01 | CE-001, CE-002 y CE-004 | Hugo | Disponibles el 16 nov |

---

## 8. Dudas y decisiones

### 8.1 Entrevista con Hugo (2026-11-17)

**Entrevista del cambio de rumbo** (2026-11-17, después de D-4):

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| E-6 | Si todo será local, ¿la base de datos sigue siendo Supabase o pasa a un PostgreSQL en la computadora? | Supabase sigue: solo sale AWS. Se reusan el esquema del PR #97 y el diseño del guardado. | Historias 1 y 6, RF-001 a RF-023 |
| E-7 | Sin dirección pública, ¿cómo se cumple la regla de reaccionar al aviso de pey? | Con un túnel para todo: la web, el servidor, el canal de avisos y el aviso de pey salen por la dirección del túnel. | RF-024 a RF-030, RF-056 a RF-060 |
| E-8 | ¿El CI en cada pull request se queda? | Sí. Solo sale la publicación automática, que dependía de AWS. | Historia 5, RF-036 a RF-038 |
| E-9 | ¿Cuándo debe estar encendida la demo? | Solo en momentos acordados: pruebas, grabación del video, demos con negocios piloto y la demo en vivo de la evaluación (12 al 14 de diciembre). No sin parar durante la evaluación ni hasta el 31 de enero. | RF-060, §4, §5 |
| E-10 | ¿La dirección pública es siempre la misma o puede cambiar cada vez que se enciende la demo? | Siempre la misma, aunque se apague la computadora, para que sirvan el enlace de la entrega y el aviso dado de alta en pey. Puede pedir una cuenta gratuita en el servicio del túnel. | RF-030, RF-058, §7 |

**Entrevista de la versión con AWS** (2026-11-17, después de la QA y de la aprobación, a pedido de Hugo):

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| E-1 | ¿Con qué llave de pey trabaja el servidor local? | Con el ambiente de pruebas de pey, con su propia llave y su propio aviso. Si no funciona, con una segunda llave de producción solo para local, también con su propio aviso. Sustituye la decisión de QA-4 de trabajar en local solo con la consulta de respaldo. *Con D-4, "local" se llama "servidor de desarrollo".* | RF-053 |
| E-2 | ¿Se cargan en la demo los datos de prueba ficticios del PR #97? | No: solo en la base de datos local (ahora, de desarrollo). | RF-054 |
| E-3 | ¿Qué ve quien abre el enlace con la demo apagada o caída? | El error del navegador; no se construye una página de "demo en pausa". *Con D-4, también el error del túnel.* | §4, §5 |
| E-4 | ¿Se acepta que la demo deje de responder en cada publicación? | Sí: se mantiene un solo proceso (spec 001) y la demo vuelve a responder en menos de 1 minuto. Varios procesos sin corte quedan fuera de alcance. *Con D-4 ya no hay publicaciones (RF-055 retirado); sigue el solo proceso.* | §5 |
| E-5 | ¿Se entrega primero el CI dentro del corte 1 (P-1)? | Sí. *Con D-4 hay una sola entrega, y el CI sigue primero.* | §1.2, P-1 |

**Decisiones tomadas antes de redactar:**

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| D-1 | ¿Qué abarca la spec 003? | Supabase + AWS + CI en una sola spec. *Sustituida por D-4.* | Toda la spec |
| D-2 | ¿De dónde sale la imagen del QR (#94)? | La que manda pey, guardada con el cobro en una columna nueva. Hugo agrega la columna con una migración. | RF-010, RF-011, RF-018 |
| D-3 | ¿Qué pasa al llegar a los 200 dólares? | Correos al 50 %, 80 % y 100 % y por pronóstico, y apagado automático. La QA (QA-2) bajó el apagado al 90 % por el retraso de AWS. *Sustituida por D-4: no hay presupuesto.* | — |
| D-4 | ¿Se monta la demo en la nube? | No, por ahora: decisión del equipo del 2026-11-17. Todo corre local, con Supabase como base de datos (E-6), un túnel para la demo (E-7) y el CI (E-8). Se puede retomar después. | Toda la spec, §5 |

**Requisitos retirados y reescritos por D-4.** Los números retirados no se reutilizan:

- Retirados: RF-031 a RF-035 y RF-040 a RF-041 (presupuesto), RF-042 a RF-045 (publicación automática), RF-046 y RF-047 (cambios de estructura durante la publicación), RF-055 (corte al publicar); CE-008 y CE-009 (presupuesto), CE-012 (8 días sin pausa), CE-013 (publicación automática) y CE-014 (tres publicaciones).
- Reescritos para el túnel: RF-017, RF-020, RF-024, RF-025 a RF-030, RF-039, RF-049, RF-053, RF-054, RF-056, CE-004, CE-010 y CE-015.
- Nuevos: RF-057 (eventos sin retención), RF-058 (guía para encender la demo), RF-059 (credenciales del túnel), RF-060 (cuándo está encendida la demo) y CE-016 (encender la demo con la guía).

### 8.2 Cambios a specs aprobadas

| # | Spec | Cambio propuesto | Origen | Estado |
|---|---|---|---|---|
| C-6 | 001 | (a) §4, fila "Reinicio del servidor": los cobros, pagos y avisos se conservan (spec 003), ya no se pierden. (b) §4, fila "Aviso de pago de un cobro desconocido": quitar "por ejemplo, tras reiniciar el servidor". (c) RF-038 y `contracts/salud.md`: la salud también indica si la base de datos está configurada y responde (RF-023 de esta spec). (d) §5, fila "Base de datos: los cobros se pierden al reiniciar": resuelto por la spec 003. (e) `data-model.md` (línea 5 y §5 y §6), `quickstart.md:80`, `contracts/ver-cobro.md:22` ("o se perdió al reiniciar") y `backend/README.md:118`: los cobros, pagos y avisos se guardan en la base de datos; los límites por IP y los canales siguen en memoria. (f) `contracts/aviso-pey.md:42`: el manejador ya hace una llamada de red (guardar en la base de datos); la meta de responder en menos de 1 s (CE-010 de la 001) se mantiene. (g) `contracts/aviso-pey.md`, respuesta 400: un `amount` de 0 o negativo se rechaza igual que uno ilegible, sin marcar el `webhook-id`, porque la base de datos no acepta pagos de 0 o menos (QP-3 del plan de la 003); también en la fila de `amount` de la petición (`contracts/aviso-pey.md:28`). (h) `quickstart.md:80` arranca sin `--host 0.0.0.0` (solo `127.0.0.1`, RF-056 de esta spec), y `backend/README.md:41` dice que, con el túnel, `PROXIES_CONFIABLES` es `127.0.0.1`. (i) §4, fila "Pago después de la ventana de escucha": agregar que la conciliación de esta spec (RF-061) consulta una vez a pey cuando termina la ventana y registra lo que falte, sin canal. | Esta spec, QA-7, QP-3 y la revisión de C-6 del 2026-11-20 | **Aprobado por Hugo el 2026-11-20, ampliado con (h) e (i) · aplicado el 2026-11-24** (F5) |
| C-7 | 002 | (a) RF-057: quitar el ejemplo "(por ejemplo, porque se reinició)", porque con la spec 003 un reinicio ya no hace que el servidor olvide un cobro. El comportamiento no cambia. (b) El flujo local abre la web desde el servidor en `http://localhost:8000` (el servidor la entrega, plan de la 003, DP-21) en lugar del puerto 5173 con `config.js` en `http://localhost:8000`: `quickstart.md:32-40`, `verification-guide.md:79-82` y `web/README.md:34-45`. (c) La política de seguridad de contenido queda en `connect-src 'self'`: `research.md:128-130` y `plan.md:379`, como ya anticipaba `quickstart.md:55`. *(b) y (c) salieron del plan de la versión con AWS (DP-21, QP-8) y los confirma el plan nuevo (DP-21, R-12).* (d) §4, filas "Reinicio del servidor con un cobro en pantalla" y "Reinicio del servidor con cobros anteriores en escucha": con la spec 003 el cobro sigue guardado, y la pantalla reconecta y lo sigue escuchando. (e) `quickstart.md` §4: servir la web desde el backend ya lo hace la spec 003 (DP-21), sin C-n a la 001. En `verification-guide.md` no se tocan las secciones con fecha: solo se agrega una nota con el flujo nuevo en las líneas 79-82 y 153-163. | QA-7, QP-8 y la revisión de C-7 del 2026-11-20 | **Aprobado por Hugo el 2026-11-20, ampliado con (d) y (e) · aplicado el 2026-11-21** (F2) |
| C-9 | 003 | RF-024: la demo se publica en un dominio propio del equipo con HTTPS, en lugar de la dirección de AWS. Nuevo RF-056: el tramo entre el intermediario del hosting y el servidor también va cifrado. Nuevo CE-015. Se quita de §5 la fila "Dominio propio". §7: el dominio como dependencia de Hugo y como supuesto de costo. La aclaración del 2026-11-17 sobre la dirección queda sustituida. | QA del plan, QP-7 (Hugo, 2026-11-17) | Aprobado y aplicado el 2026-11-17. **Retirado** el mismo día por D-4: no hay dominio; RF-056 y CE-015 se reescribieron para el túnel |
| C-8 | 003 | §7 y QA-9: los PR #72 y #96 unidos pasan de "antes del plan" a "antes de aprobar el plan". El plan se redacta ya, contra la constitución 2.0.0 del PR #96 (Juan ya aprobó su contenido) y el código de la rama del PR #72; su QA (`/qa-spec 003 plan`) no lo aprueba hasta que los dos estén en `main`. Si al unirse cambian algo que el plan usa, se ajusta en esa QA. | Hugo, por el corte 1 (≤ 22 nov) | Aprobado por Hugo y aplicado el 2026-11-17. Cumplido el 2026-11-21: #72 y #96 unidos y el plan aprobado |
| C-10 | 003 | **CE-003** y la **historia 2, escenario 2**: el dueño ve el QR en **5 segundos o menos** después de tocar Cobrar, en 9 de cada 10 intentos, en lugar de "menos de 3 segundos". Mismo cambio en los lugares que repiten la cifra: `plan.md` (§ metas de rendimiento, constitución VII y riesgo de pey lento), `quickstart.md` §4 paso 2, `tasks.md` (objetivo de F3, T029, T031 y T073) y el texto de `docs/operacion-demo.md` §10. No toca CE-006 de la spec 002 (QR en menos de 3 s con el servidor normal y sin ser el primer cobro tras arrancar): queda como está y se vuelve a medir en F6. | Medición de T029 (2026-11-22): 10 cobros desde el celular de Hugo con datos móviles tardaron de 3 a 5 s. En el servidor, crear el QR en pey tarda unos 2.3 s por sí solo (11 cobros locales, 2.2 a 2.6 s), el túnel suma unos 0.6 s y la red del celular el resto. Se observaron además 2 picos de 8 y 9 s en la llamada a pey (T030), por lo que la meta nueva tolera 1 intento de cada 10. Es la decisión de Hugo del 2026-11-22: relajar la meta en lugar de cambiar cómo se dibuja el QR (D-2) | **Aprobado por Hugo y aplicado el 2026-11-22** (F3) |

### 8.3 Propuestas

| # | Propuesta | Por qué | Decisión |
|---|---|---|---|
| P-1 | Entregar primero el CI (§1.2) | Desbloquea la revisión de los pull requests y protege todo lo demás de esta spec | Aceptada por Hugo el 2026-11-17 (E-5) |

### 8.4 Revisión QA de la versión con AWS (2026-11-17, una sola pasada)

> Esta tabla revisó la versión con AWS, antes de D-4. QA-1 (dos cortes) y QA-2 (presupuesto) quedan sin efecto; las demás siguen aplicadas en el texto, con "local" leído como "desarrollo". Esta versión lleva su propia QA de una sola pasada (`/qa-spec 003`), con numeración desde QA-12.

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QA-1 | Promesa imposible | 47 RF y 13 CE para S1, que termina el 22 nov (quedan 5 días), con dependencias sin resolver: PR #72, #96 y #97 sin unir, cuenta de AWS sin confirmar y protección de `main` a cargo de Juan. La publicación automática sin credenciales (RF-042 a RF-045) es lo más incierto, y CE-012 tarda 8 días en comprobarse. | RF-042 a RF-045, RF-047, CE-012, CE-013 | Dos cortes. **Corte 1 (≤ 22 nov):** CI, guardar en la base de datos, publicar a mano, presupuesto y pago real. **Corte 2 (≤ 29 nov):** publicación automática (RF-042 a RF-045, CE-013), RF-047 y CE-012. | Aceptada por Hugo el 2026-11-17: dos cortes (≤ 22 nov y ≤ 29 nov). Aplicada el mismo día |
| QA-2 | Promesa imposible | AWS no garantiza el presupuesto como está escrito. (a) Las acciones de presupuesto solo aplican políticas de IAM o SCP o detienen instancias EC2 y RDS ([budgets-controls](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-controls.html)); App Runner, ECS y Lightsail no aparecen. (b) Los datos se actualizan "up to three times a day", con 8 a 12 h entre actualizaciones ([budgets-managing-costs](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)): el gasto puede pasar de 200 antes del apagado. (c) El pronóstico necesita "approximately 5 weeks of usage data" ([budgets-best-practices](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)): RF-033 no avisará antes de fines de diciembre. | RF-033, RF-034, CE-008 | RF-034 apaga al **90 %**, para absorber el retraso; anotar en §4 que el apagado puede tardar hasta unas 12 h y que el pronóstico solo funciona tras unas 5 semanas. El plan elige un servicio que el presupuesto pueda detener o conecta el aviso a una función que lo detenga. | Aceptada por Hugo el 2026-11-17: apagado al 90 % y limitaciones anotadas. Aplicada el mismo día |
| QA-3 | API de pey | Los reintentos del aviso de pey no están documentados ([webhooks/introduction](https://docs.pey.mx/en/docs/webhooks/introduction) solo habla de "delivery attempts"). RF-014 confía en que pey reenvíe: si la base de datos falla, pey no reintenta y nadie tiene la pantalla abierta, el pago no se registra nunca (principio VIII). | RF-014 | Además de responderle con error a pey, el servidor conserva el aviso en memoria y reintenta registrarlo hasta que la base de datos vuelva. La consulta de respaldo sigue como segunda red. | Aceptada por Hugo el 2026-11-17: reintento en memoria además del error a pey. Aplicada el mismo día |
| QA-4 | API de pey | "An API key can only have one webhook" ([set-up-webhooks](https://docs.pey.mx/en/docs/tutorials/getting-started/set-up-webhooks)). Cuando el aviso apunte a AWS, el servidor local ya no lo recibe, y los cobros creados en local con la misma llave mandan su aviso a la demo. La spec no dice qué base de datos usa el servidor local: si es la de la demo, las pruebas locales la ensucian. Además, `llms.txt` menciona un ambiente de pruebas (`https://api.dev.pey.mx`, con un simulador de banco), y la constitución dice que no hay. | RF-017, RF-025 | El servidor local usa su propio proyecto gratuito de Supabase (el plan permite dos) y, sin aviso de pey, se apoya en la consulta de respaldo. Hugo pregunta a pey por el ambiente de pruebas; si existe, se propone aparte. | Aceptada por Hugo el 2026-11-17: proyecto propio de Supabase en local y consulta de respaldo; Hugo pregunta a pey por el ambiente de pruebas. Aplicada el mismo día. La parte de la llave local la sustituyó E-1 (ambiente de pruebas de pey o segunda llave de producción) |
| QA-5 | Caso límite | La pausa de Supabase no está garantizada como supone RF-039. La documentación dice que "may pause" proyectos "that exhibit low activity in a 7-day period" ([going-into-prod](https://supabase.com/docs/guides/platform/going-into-prod)) y no define qué cuenta como actividad. El plan gratuito no incluye respaldos ([pricing](https://supabase.com/pricing)). Si el presupuesto apaga el servidor, nadie hace la consulta diaria. CE-012 tarda 8 días en comprobarse. | RF-039, RF-041, RF-046, CE-012 | Mantener RF-039. La guía de Hugo (RF-041) incluye reactivar un proyecto pausado. Hugo exporta una copia de la base de datos de la demo antes de cada migración. CE-012 se comprueba después de cerrar la spec, sin bloquearla. | Aceptada por Hugo el 2026-11-17: guía de reactivación, copia antes de cada migración y CE-012 después del cierre. Aplicada el mismo día |
| QA-6 | Contradicción | La spec dice que CE-002 cierra #29, pero #29 también pide "Un negocio no recibe avisos de otro", y sin inicio de sesión (#24, fuera de alcance) no hay negocios. | CE-002 | CE-002 cierra #27 y #64. #29 queda abierto, con una nota, hasta #24. | Aceptada por Hugo el 2026-11-17: #29 queda abierto hasta #24. Aplicada el mismo día |
| QA-7 | Contradicción | C-6 no cubre todo lo que en la 001 dice que los cobros viven en memoria o se pierden al reiniciar: `spec.md:288` (§5), `data-model.md:5` y §5 y §6, `quickstart.md:80`, `contracts/aviso-pey.md:42` ("no hace llamadas de red… publica en memoria"), `contracts/ver-cobro.md:22` ("o se perdió al reiniciar") y `backend/README.md:118`. En la 002, RF-057 pone como ejemplo "porque se reinició". | RF-023, C-6 | Ampliar C-6 a esos lugares de la 001 (CE-010 de la 001, el aviso en menos de 1 s, se mantiene como meta). Nuevo **C-7** a la 002: quitar de RF-057 el ejemplo "por ejemplo, porque se reinició". | Aceptada por Hugo el 2026-11-17: C-6 ampliado y C-7 a la 002; los dos se aprueban aparte. Aplicada el mismo día |
| QA-8 | Ambigüedad | RF-012 implica guardar el cobro antes de pedirle el QR a pey. Si después pey falla, RF-009 de la 001 dice "no guardará el cobro", y §4 de esta spec dice "no se guarda como válido", sin aclarar si el registro queda en la base de datos. | RF-012, RF-013 | Nuevo RF (No deseado): SI pey no crea el QR, ENTONCES el servidor borra el cobro que había guardado, para que no quede en la base de datos ni en el historial (#38). En §4, quitar "como válido". | Aceptada por Hugo el 2026-11-17: el cobro guardado se borra. Aplicada el mismo día |
| QA-9 | Contradicción | La spec se apoya en la constitución 2.0.0 (Supabase y AWS en la tabla de restricciones), pero esta rama tiene la 1.0.0: el PR #96 no está unido, y en la 1.0.0 la tabla no tiene base de datos ni hosting. La rama además sale de `feature/64-web-mvp` (PR #72 sin unir). | §1, §7 | Agregar a las dependencias (§7) el PR #96 y el PR #72 unidos antes del plan, y citar la constitución como "2.0.0 (PR #96)". | Aceptada por Hugo el 2026-11-17: #96 y #72 unidos antes del plan. Aplicada el mismo día. El mismo día, C-8 la cambió a "antes de aprobar el plan" |
| QA-10 | Seguridad | El aviso de pey y la consulta de transacciones traen en `metadata` la CLABE, el banco y la clave de rastreo de quien paga ([metadata-response](https://docs.pey.mx/en/docs/types/metadata-response)). Hoy el código no los lee (`backend/app/pey.py:183`, `backend/app/main.py:268-327`). RF-009 cubre la base de datos, pero no los registros (principio X). | RF-009 | Ampliar RF-009: los datos de quien paga (nombre, CLABE o cuenta, banco, teléfono y clave de rastreo) no se guardan en la base de datos ni aparecen en los registros. | Aceptada por Hugo el 2026-11-17: RF-009 ampliado a los registros. Aplicada el mismo día |
| QA-11 | Contradicción | La vista `cobros_con_estado` del PR #97 calcula el estado con la hora de la base de datos (`now()`). RF-006 exige la hora del servidor, que las pruebas controlan (principio V). Si el servidor lee el estado de la vista, las pruebas con reloj controlado no sirven, y la hora del servidor y la de la base de datos pueden no coincidir. | RF-006 | Mantener RF-006: el servidor calcula el estado con su propio reloj y no usa la columna `estado` de la vista. Queda como decisión del plan (DP) y se le avisa a Juan. | Aceptada por Hugo el 2026-11-17: el servidor calcula el estado; DP del plan y aviso a Juan. Aplicada el mismo día |

**Bloques de la pasada:**

1. **Coherencia interna:** términos del glosario, casos límite contra RF, CE contra RF y numeración. RF-001 a RF-047 sin huecos ni repetidos; el siguiente C-n libre es C-7. Salen QA-8 y las erratas.
2. **Otras specs, plan, reglas e issues:** los 14 RF citados de la 001 y los citados de la 002 (RF-057, RF-078, CE-001 y CE-002) existen y dicen lo atribuido. Revisados los lugares de la 001 que contradicen C-6, `docs/plan-hackathon.md` (fechas, evaluación del 12 al 14 dic y demo hasta el 31 ene), las reglas (cobro real, producción, llave fuera del cliente, sin reventa) y los criterios de #90, #19, #34, #65, #35, #94, #27, #29 y #64. Salen QA-6, QA-7 y QA-9.
3. **Código:** `backend/app/main.py` (webhook, salud y límites por IP con `ProxyHeadersMiddleware`), `backend/app/cobros.py` (pagos en memoria), `backend/app/pey.py` (pide `generateImage` y no lee `metadata`), `backend/app/config.py` (no lee `DATABASE_URL`, aunque `.env.example` la tiene) y `web/js/servidor.js` (un 503 al consultar ya se trata como "sin conexión", así que RF-015 no cambia la web). `web/index.html:8` tiene `connect-src … http://localhost:8000 https:`, que RF-029 obliga a cerrar. Backend: 109 pruebas en verde. Salen QA-10 y QA-11.
4. **API de pey:** `openapi.json` (versión 2026-10-20) y páginas de webhooks, metadatos y CoDi. `qrImage` puede ser `null` aunque se pida, `expiration` es 0 o al menos 360, `numRef` tiene hasta 7 dígitos, existe `GET /transaction/codi/qr/{id}`, hay un solo webhook por llave y no hay límites de peticiones documentados. Salen QA-3, QA-4 y QA-10.
5. **Dependencias externas:** cada una de §7 tiene dueño y estado. Agregados #96 y #72 (QA-9). Supabase gratuito: dos proyectos activos, 500 MB, sin respaldos, conexión directa solo por IPv6, así que desde AWS se usa el *pooler* en modo sesión (decisión del plan). Sale QA-5.
6. **Ambigüedades y casos límite:** reinicio, pago tardío, monto distinto, pago repetido, aviso desconocido o reenviado, QR vencido, devoluciones, falla de pey, de la base de datos y de la publicación. No hay pantallas nuevas: los estados de la pantalla son los de la 002. Salen QA-3, QA-5 y QA-8.
7. **Seguridad y rendimiento:** credenciales solo en el servidor y en el hosting (RF-020, RF-021 y RF-043), firma y deduplicación sin cambios, CORS y límites por IP con la IP real (RF-027 y RF-028), y tiempos medibles (CE-002, CE-003 y CE-004). El balanceador de AWS admite hasta 4000 s de inactividad, así que el canal de 20 minutos es posible. No se pudo leer el límite de App Runner ni de Lightsail: queda para el plan. Sale QA-10.
8. **Construibilidad y reparto:** fechas de S1 y S2 y el reparto (Hugo: AWS, pey y migraciones; Juan: #97, protección de `main` y revisión). Salen QA-1 y QA-2.

**Erratas** (corregidas el 2026-11-17 junto con las decisiones):

1. Historia 2, escenario 2: agregar "en 9 de cada 10 intentos", como CE-003.
2. Historia 4, prueba independiente: AWS no tiene un botón de "aviso de prueba"; se prueba bajando un umbral un momento.
3. Encabezado y §9: quitar #29 de lo que se cierra si se acepta QA-6.
4. §8.1, D-3: actualizar el umbral del apagado si se acepta QA-2.

#### Revisión QA de la versión con túnel (2026-11-20, una sola pasada)

> Revisada contra la constitución 3.0.0 (PR #96, commit `a962dc5`), porque es la que regirá el plan (C-8), y contra el código de esta rama (`5db47ed`).

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QA-12 | Promesa imposible | §1.2 promete toda la spec "hasta el 22 de noviembre". Hoy es 20 nov y faltan la QA, el plan, su QA, las tareas, su QA, la construcción (Grok), la revisión y el pago real. Además, el plan no se aprueba hasta unir #72 (con 4 cambios pedidos por Juan) y #96 (C-8). El issue #90 está en el milestone **S2** (29 nov), y la puerta S1 de `docs/flujo-de-construccion.md` pide "los datos en Supabase". Las specs 004 y 005 (S2) dependen de la 003 (N-06 y N-07). | §1.2, P-1, CE-001 a CE-016 | Dos cortes. **Corte 1 (≤ dom 22 nov), lo que pide la puerta S1 sin base de datos:** CI (historia 5), demo pública por el túnel y guía (historias 2 y 4) y pago real (historia 3); cierra #35, #65, #27 y #64. **Corte 2 (≤ mié 25 nov), antes de construir 004 y 005:** guardar, migraciones e imagen del QR (historias 1 y 6); cierra #90, #19 y #94. Ajustar la puerta S1 de `flujo-de-construccion.md` (PR #96). | Aceptada por Hugo el 2026-11-20: dos cortes (≤ dom 22 nov y ≤ mié 25 nov). Aplicada el 2026-11-20 |
| QA-13 | Ambigüedad | RF-060 dice "la demo en vivo de la evaluación, del 12 al 14 de diciembre", pero no aclara si la demo queda encendida **los tres días** o solo durante la demo en vivo. Los jueces evalúan el enlace (constitución 3.0.0, IX; `docs/plan-hackathon.md:27` y `:40`). Además, choca con `flujo-de-construccion.md` §6.2: "Juan congela la demo y la deja encendida durante la evaluación (#57)", y con la constitución 3.0.0 (Leonel la prueba del 12 al 14). La spec supone que la computadora de la demo es la de Hugo. Por último, con E-9 la consulta diaria (RF-039) no evita la pausa de Supabase: entre momentos acordados pueden pasar más de 7 días sin un servidor encendido, y el día 12 la base podría estar pausada. | RF-039, RF-050, RF-060, §5 | RF-060: encendida **sin parar desde la entrega (12 dic) hasta el anuncio (14 dic)**, además de los momentos acordados. Los jueces no tienen otra forma de probar el enlace. La guía (RF-050 y RF-058) pide encender la demo y comprobar la salud al menos cada 5 días y el día antes de cada momento acordado. Queda en la computadora de Hugo; #57 pasa de Juan a Hugo, o la computadora de la demo se cambia a la de Juan. | Aceptada por Hugo el 2026-11-20: encendida sin parar del 12 al 14 dic en la computadora de Hugo, además de los momentos acordados; guía con encendido y salud al menos cada 5 días y el día antes de cada momento; #57 pasa a Hugo. Aplicada el 2026-11-20 |
| QA-14 | Contradicción | Principio VIII: "El sistema NUNCA pierde un pago… se registra aunque llegue tarde". §4 acepta dos pérdidas. (a) "Si la ventana termina con la demo apagada… la pantalla no lo avisa". El pago tampoco queda en la base de datos, porque nada lo consulta después. (b) "El servidor se reinicia con avisos todavía sin registrar". pey no documenta reintentos del aviso (QA-3). Con la demo encendida solo en momentos acordados (E-9), (a) deja de ser raro. pey tiene `GET /transaction/codi/qr/{id}` (QA de la versión con AWS, bloque 4). | RF-005, RF-014, RF-048, §4 | Nuevo RF (Dirigido por evento): CUANDO el servidor arranca, EL SISTEMA consultará en pey los cobros guardados cuya ventana de escucha terminó mientras estaba apagado y registrará sus pagos, sin sonido porque no hay pantalla escuchando, para que aparezcan en el historial (#38). Así se cierran las dos filas de §4. | Aceptada por Hugo el 2026-11-20: RF nuevo de conciliación con pey al arrancar. Aplicada el 2026-11-20 |
| QA-15 | API de pey | RF-053 y §7 suponen que el ambiente de pruebas de pey da una llave propia con su aviso. Solo `docs.pey.mx/llms.txt` menciona `https://api.dev.pey.mx`. La guía oficial para crear la llave ([create-an-api-key](https://docs.pey.mx/en/docs/tutorials/getting-started/create-an-api-key)) y `openapi.json` (versión 2026-10-20) dicen "A dedicated test environment is coming soon" y solo listan producción. Que el ambiente de pruebas admita avisos no está documentado. La tarea de §8.5 de corregir la fila "No hay ambiente de pruebas" de la constitución deja de tener sentido: hoy esa fila es correcta. | RF-053, §7, §8.5 | RF-053: los servidores de desarrollo usan una **segunda llave de producción** con su propio aviso. Quien no tenga túnel prueba sin aviso, apoyado en la consulta de respaldo. El ambiente de pruebas se propone aparte cuando pey lo publique. Se quita de §8.5 la tarea de corregir la constitución. Hugo confirma en el portal que puede crear una segunda llave. | Aceptada por Hugo el 2026-11-20, después de que se le explicara cómo funciona: segunda llave de producción con su propio aviso; sin túnel, consulta de respaldo; Hugo confirma en el portal que puede crearla; se quita de §8.5 la tarea de la constitución. Aplicada el 2026-11-20 |
| QA-16 | Hueco | Lo que debe cumplir el túnel está repartido: HTTPS sin advertencias (historia 2, escenario 1), canal sin retención (RF-057), canal de 20 minutos (RF-026), dirección fija (RF-030), IP real del celular (RF-028) y gratis (§7). Falta un criterio de seguridad: si el servicio de túnel termina el HTTPS en sus propios servidores, ve sin cifrar los avisos de pey, que traen nombre, CLABE y banco de quien paga (QA-10). RF-056 protege ese mismo dato en la red local. Por ejemplo, el plan gratuito de un túnel conocido muestra una página de advertencia a los navegadores, lo que ya choca con la historia 2. | RF-024 a RF-030, RF-056, RF-057, §7 | Juntar en §7 la lista de **criterios del túnel**: los seis anteriores, más "de preferencia, el HTTPS termina en la computadora de la demo". Si el túnel elegido termina el HTTPS en su servicio, queda como limitación aceptada y escrita (igual que pasaría con cualquier hosting). El plan compara los túneles con esa lista. | Aceptada por Hugo el 2026-11-20: lista de criterios del túnel en §7, con el HTTPS en la computadora de la demo como preferencia; si no se cumple, limitación aceptada y escrita. Aplicada el 2026-11-20 |
| QA-17 | Caso límite | RF-026 y CE-004 fijan el canal en "hasta 20 minutos" (10 de vigencia más 10 de ventana, spec 001, RF-021 y RF-022). F-04 (spec 004, S2) deja elegir la duración del QR, quizá sin vencimiento (`flujo-de-construccion.md` §3.2). Un túnel elegido para 20 minutos podría no servir una semana después. | RF-026, CE-004 | RF-026: el canal se mantiene "durante toda la ventana de escucha del cobro", sin un número fijo. CE-004 sigue midiendo 20 minutos. La comparativa del plan anota cuánto aguanta cada túnel un canal abierto. | Aceptada por Hugo el 2026-11-20: el canal dura toda la ventana de escucha; CE-004 sigue en 20 minutos. Aplicada el 2026-11-20 |
| QA-18 | Ambigüedad | RF-006 pide calcular el estado con la hora del servidor, pero no dice de dónde salen las **horas guardadas**. El esquema del PR #97 pone `default now()` (hora de la base de datos) en `cobros.creado_en`, `pagos.registrado_en` y `avisos_webhook.recibido_en` (`supabase/001_esquema_inicial.sql:66`, `:93` y `:109`, en `main`). Si el servidor deja que la base de datos ponga la creación, el cálculo mezcla dos relojes, y las pruebas con reloj controlado (principio V) dejan de servir. | RF-006 | Ampliar RF-006: las horas de creación, vencimiento, pago y cancelación que se guardan las pone el servidor con su reloj, no la base de datos. | Aceptada por Hugo el 2026-11-20: las horas guardadas las pone el reloj del servidor (RF-006 ampliado). Aplicada el 2026-11-20 |
| QA-19 | Contradicción | La tabla de restricciones de la constitución 3.0.0 contradice decisiones de esta spec. "Hosting: AWS" choca con D-4 (no hay nube). "Imagen del QR: … está por decidir" choca con D-2 (la imagen de pey, guardada en Supabase). "MongoDB solo entra si Juan justifica su uso (primer candidato: la imagen del QR)" también choca con D-2. El plan se verifica contra esa tabla (constitución 3.0.0, Gobierno, Cumplimiento). | §5, D-2, D-4 | Hugo propone una enmienda de **parche** (redacción de la tabla, sin tocar principios): Hosting = "computadora de la demo con túnel HTTPS (spec 003); AWS como plan B (#34)"; Imagen del QR = "la que entrega pey, guardada con el cobro en Supabase (#94)"; se quita la imagen del QR como candidata de MongoDB. Puede ir en el mismo PR #96 antes de unirlo. | Aceptada por Hugo el 2026-11-20: enmienda de parche (3.0.1) en el mismo PR #96, antes de unirlo. Aplicada el 2026-11-20 |
| QA-20 | Hueco | Los issues de la spec no cuadran con ella ni con la 3.0.0. (a) #19 está asignado a **Juan** (S1) y pide "el backend se conecta" y "migraciones con un comando", que construye esta spec. Juan tiene el PR #99 (decisión de Supabase) con "#19". (b) #90 y #94 piden "La nota de implementación está en `docs/implementacion/`", y la 3.0.0 la quitó. (c) #66 (README con el enlace en vivo, Hugo, S1) depende de #65 y la dirección fija (RF-030) lo hace posible, pero la spec no lo nombra. (d) #65 todavía habla de Render o Railway y del "profesor". | Encabezado, §9 | La spec cierra con "Closes" #19 (conexión y comando), y el PR #99 de Juan usa "Refs #19". Se avisa a Juan en ese PR. Hugo quita de #90 y #94 el criterio de la nota y actualiza el contexto de #65. #66 entra en el encabezado como issue que se cierra con el corte 1, con la nota de cuándo está encendida la demo. | Aceptada por Hugo el 2026-11-20: issues alineados como se recomienda, con #66 en el corte 1. Aplicada el 2026-11-20 |

**Bloques de la pasada:**

1. **Coherencia interna:** glosario, casos límite contra RF, CE contra RF, restos de AWS y numeración. RF-001 a RF-030, RF-036 a RF-039 y RF-048 a RF-060 sin repetidos (los huecos son los retirados por D-4). CE-001 a CE-007, CE-010, CE-011, CE-015 y CE-016. El siguiente C-n libre es **C-10**. Salen QA-14, QA-17, QA-18 y las erratas 1 a 5.
2. **Otras specs, plan, reglas e issues:** los 13 RF citados de la 001 (RF-008 a RF-010, RF-017 a RF-022, RF-034, RF-035, RF-038 y RF-041) y los de la 002 (RF-057, RF-078, CE-001 y CE-002) existen y dicen lo atribuido. C-6 y C-7 siguen cubriendo los lugares de la 001 y la 002. Constitución 3.0.0, `docs/plan-hackathon.md` (evaluación 12 al 14 dic, demo pública por enlace, producción de pey), `flujo-de-construccion.md` (puertas, F-04 y #57) e issues #90, #19, #35, #94, #65, #27, #29, #64, #66 y #57. Salen QA-12, QA-13, QA-19 y QA-20.
3. **Código:** `backend/app/config.py` no lee `DATABASE_URL` (`.env.example:9` la tiene vacía). `backend/app/main.py:140` ya confía en las cabeceras del proxy configurado (RF-028). uvicorn escucha en `127.0.0.1` por defecto (`backend/README.md:12`), lo que ayuda a RF-056. `web/index.html:8` sigue con `connect-src … http://localhost:8000 https:` (RF-029 y C-7). El esquema de #97 no está en esta rama (sale de `feature/64-web-mvp`), solo en `main`, y tiene RLS activado en las 5 tablas sin políticas, lo que cumple RF-022 para la llave pública. Backend: **109 pruebas en verde** y `ruff` limpio. Sale QA-18.
4. **API de pey:** `llms.txt`, webhooks, set-up-webhooks, create-an-api-key y `openapi.json` (2026-10-20). Un solo webhook por llave. Reintentos del aviso sin documentar. Ningún requisito documentado para la dirección del aviso. El aviso solo se cambia en el portal. `qrImage` solo llega si se pide `generateImage`, y puede ser `null`. El ambiente de pruebas está "coming soon". Salen QA-14 y QA-15.
5. **Dependencias externas:** cada fila de §7 tiene dueño y estado. Falta la prueba de Leonel desde fuera de la red (N-17, constitución 3.0.0), que depende de que la demo esté encendida. Se agrega a §7 con la errata 4. Salen QA-13 y QA-16.
6. **Ambigüedades y casos límite:** reinicio, pago tardío, monto distinto, pago repetido, aviso desconocido o reenviado, QR vencido, devoluciones, falla de pey, de la base de datos y del túnel, demo apagada y QR largo (F-04). No hay pantallas nuevas: RF-012 y RF-015 usan los mensajes y la reconexión de la 002. Salen QA-14 y QA-17.
7. **Seguridad y rendimiento:** credenciales (RF-020, RF-021 y RF-059), RLS de #97 (RF-022), firma y deduplicación sin cambios, CORS y límites con la IP real (RF-027 y RF-028), datos de quien paga en el túnel y tiempos medibles (CE-002, CE-003 y CE-004). Sale QA-16.
8. **Construibilidad y reparto:** quedan 2 días para S1, dependencias de #72 y #96, Grok implementa y Claude revisa, Juan tiene #19 y Supabase de desarrollo, Leonel tiene N-17 y Hugo tiene la computadora de la demo y las llaves. Salen QA-12, QA-13 y QA-20.

**Erratas** (sin efecto en el comportamiento; corregidas el 2026-11-20 junto con las decisiones):

1. Notas de spec-kit (§0), historia 5 y §7: citan la "constitución 2.0.0" y reglas que la 3.0.0 cambió. Historia 5: "quien revisa y une (Juan…)" pasa a "quien une su propio pull request (cada autor)". §7, fila del PR #97: quitar "nadie une su propio PR".
2. §9: quitar "o su nota de implementación" y "#65 tiene su nota", porque la 3.0.0 quitó la nota. Lo hecho queda en el PR con la plantilla.
3. §1.2: "lo que era del corte 2 (publicación automática, RF-047 y CE-012)" debe decir también CE-013.
4. §7: agregar la dependencia "Prueba de la demo desde fuera de la red (N-17)", con Leonel como dueño. En la fila de la protección de `main`, el dueño es quien administra el repositorio (ahora en la organización `team-complexity`), y la protección debe exigir el CI y dejar de exigir la aprobación (constitución 3.0.0).
5. Glosario, "Base de datos": hay dos proyectos (demo y desarrollo, RF-049). Decir "el proyecto de Supabase de la demo; los servidores de desarrollo usan otro".

### 8.5 Pendientes

- Ninguna marca abierta: las dos del cambio de rumbo se resolvieron el 2026-11-17 (E-9 y E-10).
- QA de la versión con túnel hecha el 2026-11-20 (QA-12 a QA-20), decidida y aplicada.
- Tarea de Hugo fuera de la spec (QA-15): crear en el portal de pey la segunda llave de producción, ligada a la cuenta CoDi actual. Si el portal no deja ligar esa cuenta a dos llaves, se avisa antes del plan. La tarea de corregir la fila "No hay ambiente de pruebas" de la constitución se retiró: esa fila es correcta mientras pey no publique su ambiente de pruebas.
- Tarea de Hugo fuera de la spec (QA-19): enmienda de parche 3.0.1 en el PR #96, antes de unirlo: Hosting = computadora de la demo con túnel HTTPS (spec 003), AWS como plan B (#34); Imagen del QR = la que entrega pey, guardada con el cobro en Supabase (#94); se quita la imagen del QR como candidata de MongoDB.
- Tarea de Hugo fuera de la spec (QA-20): quitar de #90 y #94 el criterio de la nota de implementación, actualizar el contexto de #65 y avisar a Juan en el PR #99 que use "Refs #19". #57 pasa de Juan a Hugo en `flujo-de-construccion.md` (QA-13), y la puerta S1 de ese documento deja los datos en Supabase para el corte 2 (QA-12).
- Tarea de Hugo fuera de la spec (QA-11): avisar a Juan en la revisión del PR #97 que el servidor no usa la columna `estado` de la vista. Hecha el 2026-11-17, en la aprobación del PR #97.
- Con D-4 ya no hacen falta el dominio, la cuenta de AWS de la demo, la AWS CLI ni el complemento de Session Manager.

---

## 9. Criterios de finalización

- [ ] Cada RF tiene al menos una prueba automática o un paso de verificación manual.
- [ ] Todos los criterios de éxito (CE) están comprobados.
- [ ] No quedan marcas `[NECESITA ACLARACIÓN]` abiertas.
- [ ] Hay una revisión de seguridad hecha: secretos, firma de webhooks y validación de entradas, más las credenciales de la base de datos y del túnel, el acceso a la base de datos solo desde el servidor y el servidor solo por el túnel.
- [ ] El cambio C-6 a la spec 001 está aprobado y aplicado.
- [ ] El cambio C-7 a la spec 002 está aprobado y aplicado.
- [ ] #27, #64, #35, #65 y #66 (corte 1) y #90, #19 y #94 (corte 2) están cerrados por su pull request, documentado con la plantilla, y #29 tiene una nota de que queda abierto hasta #24.
