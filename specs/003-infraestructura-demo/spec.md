# Spec 003: Infraestructura de la demo pública: guardar los cobros, publicar con HTTPS y probar cada cambio

- **ID**: `003-infraestructura-demo`
- **Fecha**: `2026-11-17`
- **Estado**: `Aprobada`. Hugo la aprobó el 2026-11-17, después de las aclaraciones y de la QA, y pidió la entrevista a continuación; la entrevista (E-1 a E-5) se hizo y se aplicó el mismo día, sin QA nueva. Lo redactó Claude el 2026-11-17 con `/speckit-specify`, a partir de la descripción que Hugo ajustó ese día: alcance Supabase + AWS + CI, imagen del QR guardada (decisión de #94) y tope de gasto con apagado automático. El mismo día se resolvieron 5 aclaraciones con `/speckit-clarify` (sección "Aclaraciones"), incluidas las dos marcas del borrador. La QA del 2026-11-17 (QA-1 a QA-11) está decidida y aplicada el mismo día, con sus 4 erratas. Falta la entrevista (`/entrevista-spec 003`). Se entrega en dos cortes (§1.2). Propone el cambio C-6 a la spec 001 y el C-7 a la spec 002 (§8.2).
- **Rama**: `feature/90-infraestructura-demo` (propuesta; la crea Hugo)
- **Issues**: #90 (guardar cobros y pagos), #19 (conexión y cambios de estructura con un comando), #34 y #65 (publicar en AWS con HTTPS y el aviso de pey), #35 (CI), #94 (de dónde sale la imagen del QR). Con el pago real de esta spec se cierran #27 y #64; #29 queda abierto hasta el inicio de sesión (#24), porque también pide que un negocio no reciba avisos de otro (QA-6).
- **Entrada**: "Infraestructura de la demo pública: el backend guarda cobros, pagos y avisos de webhook en Supabase (PostgreSQL) en lugar de en memoria, con el esquema del PR #97, y backend y web se publican en AWS con HTTPS, el webhook de pey dado de alta y CI en cada pull request. Issues: #90, #19, #34 y #65, #35, #94 y el pago real de $0.01 que cierra #27, #29 y #64. Debe cumplir: después de reiniciar el servidor, un cobro pendiente sigue ahí, su pago se avisa y la web puede volver a mostrar su QR; la imagen del QR es la que manda pey y se guarda con el cobro, en una columna nueva de `cobros` que esta spec agrega con una migración sobre el esquema de #97, y si pey no la manda la web sigue mostrando el mensaje de C-3; un pago se registra una sola vez; las pruebas automáticas no usan ni la base de datos real ni pey real; las credenciales solo viven en el backend y en el hosting; el servicio de AWS no corta el canal de 20 minutos y corre un solo proceso; se mide que suene en menos de 2 s con el webhook activo, en Android y en iPhone; tope de gasto de 200 dólares de crédito hasta el 31 de enero de 2027, con correos al 50 %, 80 % y 100 % y por pronóstico, apagado automático al 100 % y presupuesto medido antes del crédito. Fuera de alcance: inicio de sesión (#24), historial (#38), cuenta bancaria por negocio y logs y monitoreo (#45)."

> **Notas para los comandos de spec-kit.**
> - `RF-###` equivale a *Functional Requirement* (FR-###).
> - `CE-###` equivale a *Success Criterion* (SC-###).
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
>
> La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas de datos, los algoritmos y las firmas de funciones: eso va en `plan.md` y `tasks.md`. Toda la spec se escribe en español. Supabase y AWS se nombran solo porque son decisiones ya tomadas por el equipo (constitución 2.0.0 del PR #96, tabla de restricciones técnicas); los requisitos no dependen de ellos.

---

## 1. Contexto y propósito (por qué)

Las specs 001 y 002 dejaron listo el recorrido completo: el dueño teclea el monto, enseña el QR, el cliente paga desde su banco y la pantalla suena. Pero hoy ese recorrido solo funciona en una computadora del equipo, y tiene dos huecos que impiden enseñarlo a los jueces y a un negocio piloto:

1. **No hay enlace público.** Las reglas del hackathon piden una demo abierta sin invitación, y pey solo entrega sus avisos de pago a una dirección pública con HTTPS. En las pruebas del 16 de noviembre, sin aviso de pey, el primer pago tardó más de 30 segundos en reportarse, y los túneles gratuitos retenían el canal de avisos o se cortaban. La promesa de "suena en menos de 2 segundos" (spec 002, CE-001 y CE-002) no se ha podido medir.
2. **El servidor olvida todo al reiniciarse.** Los cobros, los pagos y los avisos ya procesados viven en memoria (spec 001, §4, limitación aceptada hasta #23). En un hosting real, cada reinicio o publicación nueva borraría los cobros en curso: un cliente podría pagar un QR que el servidor ya no reconoce.

Esta spec cierra los dos huecos y deja la base que van a usar las tres pantallas (web, Android e iOS) y las specs que siguen (inicio de sesión #24 e historial #38):

- el servidor guarda cobros, pagos y avisos en la base de datos del proyecto (Supabase, con el esquema de Juan del PR #97);
- servidor y web se publican en AWS con HTTPS y el aviso de pey dado de alta;
- cada pull request se prueba solo, antes de que Juan lo revise;
- el gasto en AWS queda acotado a los 200 dólares de crédito, hasta el 31 de enero de 2027.

El comportamiento del cobro **no cambia**: lo que el dueño ve y oye es lo mismo que en las specs 001 y 002. Lo que cambia es que ahora sobrevive a un reinicio y se puede usar desde cualquier celular.

### 1.1 Glosario

Los términos *cobro*, *pago*, *monto fijo*, *monto libre*, *vigencia*, *ventana de escucha*, *canal de avisos*, *consulta de respaldo*, *aviso de pey* y los estados del cobro (*pendiente*, *pagado*, *vencido*, *cancelado*) significan lo mismo que en la [spec 001](../001-backend-mvp/spec.md#11-glosario). *Pantalla*, *vista* y *cobro en pantalla* significan lo mismo que en la [spec 002](../002-web-mvp/spec.md#11-glosario).

| Término | Significado en esta spec |
|---|---|
| Servidor | El backend de PAGO FÁCIL de la spec 001. Es el único que habla con pey y con la base de datos. |
| Base de datos | Donde el servidor guarda cobros, pagos y avisos para que sobrevivan a un reinicio. Es el proyecto de Supabase que creó Juan (#19, #23). |
| Reinicio | Cualquier momento en que el servidor deja de correr y vuelve a arrancar: una publicación nueva, una falla, un apagado del hosting o un reinicio a mano. |
| Demo pública | La web y el servidor publicados en AWS, con una dirección HTTPS que abre cualquier celular sin invitación ni inicio de sesión. |
| Cambio de estructura | Crear o modificar las tablas de la base de datos (una *migración*). Incluye el esquema inicial del PR #97 y la columna nueva de la imagen del QR. |
| CI | La revisión automática que corre las pruebas y el lint en cada pull request y muestra el resultado en GitHub. |
| Presupuesto | El tope de gasto en AWS: 200 dólares de crédito que deben alcanzar hasta el 31 de enero de 2027. |
| Equipo | Hugo, Juan y Miguel. Son quienes reciben los correos del presupuesto. |

### 1.2 Cortes de entrega (QA-1)

La spec se entrega en dos cortes. Cada uno se puede enseñar solo.

**Corte 1 (hasta el 22 de noviembre, meta de S1):** todo lo que no está en el corte 2. Dentro del corte, el orden acordado (P-1, E-5) va de lo que más desbloquea a lo que menos:

1. **CI** (historia 5): desbloquea la revisión del PR #72, que Juan condiciona a ver las pruebas en GitHub.
2. **Guardar cobros, pagos y avisos** (historias 1 y 6).
3. **Presupuesto y publicación a mano por Hugo** (historias 4 y 2). El presupuesto se configura antes de publicar por primera vez.
4. **Pago real desde la demo pública** (historia 3), que cierra #27 y #64.

**Corte 2 (hasta el 29 de noviembre, S2):**

- publicación automática al unir a `main`, sin credenciales guardadas (RF-042 a RF-045 y CE-013);
- aviso en la salud del servidor de un cambio de estructura sin aplicar (RF-047);
- comprobación de 8 días de la base de datos sin pausa (CE-012), que no bloquea el cierre de la spec.

Mientras no esté el corte 2, Hugo publica a mano desde `main` siguiendo su guía.

---

## Aclaraciones

### Sesión 2026-11-17

- P: ¿Cómo evitamos que la base de datos de Supabase se pause antes del 31 de enero? → R: Plan gratuito, y el servidor publicado consulta la base de datos al menos una vez al día para que nunca pase una semana sin uso (RF-039, CE-012).
- P: Si el presupuesto apaga el servidor al llegar a 200 dólares, ¿quién lo vuelve a encender y con qué criterio? → R: Solo Hugo, después de revisar qué consumió el crédito y corregir la causa (RF-040, RF-041).
- P: ¿Con qué dirección se publica la demo? → R: La que asigna AWS, con su HTTPS, sin dominio propio (RF-024).
- P: ¿Cómo se publica una versión nueva del servidor y la web en la demo? → R: Automáticamente cada vez que se une un pull request a `main` (RF-042 a RF-045).
- P: ¿Se aplican también solos los cambios de estructura de la base de datos al publicar? → R: No. La publicación solo sube código; Hugo aplica las migraciones a mano con el comando, después de revisarlas (RF-046, RF-047).

---

## 2. Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — No perder cobros ni pagos si el servidor se reinicia (Prioridad: P1)

**Como** dueño de la tiendita, **quiero** que mi cobro y sus pagos sigan ahí aunque el servidor se reinicie, **para** que el cliente que ya escaneó el QR no pague a un cobro que nadie escucha.

**Por qué esta prioridad:** en un hosting real los reinicios pasan solos (publicaciones nuevas, fallas, mantenimiento). Sin esto, la demo pública perdería pagos, y la constitución dice que el sistema nunca pierde un pago (principio VIII).

**Prueba independiente:** crear un cobro, reiniciar el servidor, recargar la pantalla y pagar ese QR con $0.01: la pantalla vuelve a mostrar el QR y suena "Pago recibido".

**Escenarios de aceptación:**

1. **Dado** un cobro *pendiente* con su QR en pantalla, **cuando** el servidor se reinicia y el dueño recarga la página, **entonces** la pantalla vuelve a mostrar el mismo QR, con el monto, el concepto y el tiempo que le queda.
2. **Dado** un cobro creado antes de un reinicio, **cuando** llega su aviso de pago de pey después del reinicio, **entonces** el pago se registra y la pantalla suena, igual que si no hubiera habido reinicio.
3. **Dado** un cobro creado antes de un reinicio, **cuando** el aviso de pey no llega pero la consulta de respaldo encuentra el pago, **entonces** el pago se registra y la pantalla suena.
4. **Dado** un cobro con dos pagos ya registrados, **cuando** el servidor se reinicia, **entonces** al consultarlo devuelve los dos pagos con su número, monto y hora, y el siguiente pago es el número 3.
5. **Dado** un cobro *cancelado* o *vencido* antes de un reinicio, **cuando** el servidor arranca, **entonces** el cobro conserva su estado y sus pagos tardíos se siguen registrando dentro de la ventana de escucha.
6. **Dado** un cobro cuya imagen del QR no mandó pey, **cuando** se consulta después de un reinicio, **entonces** se devuelve sin imagen y la pantalla muestra "No se pudo mostrar el QR. Intenta de nuevo." (spec 002, C-3).
7. **Dado** que la base de datos no responde, **cuando** el dueño pide un cobro nuevo, **entonces** el servidor no le pide el QR a pey y la pantalla muestra un mensaje para el dueño.

---

### Historia 2 — Abrir la demo desde cualquier celular (Prioridad: P1)

**Como** juez del hackathon o dueño de un negocio piloto, **quiero** abrir un enlace con HTTPS desde mi celular y cobrar, **para** probar PAGO FÁCIL sin instalar nada ni pedir acceso.

**Por qué esta prioridad:** es el "enlace a la app en vivo" que evalúan los jueces y la dirección a la que pey entrega sus avisos. Sin ella no se puede medir la promesa de los 2 segundos.

**Prueba independiente:** abrir el enlace con datos móviles (no el wifi de casa) en un Android y en un iPhone, crear un cobro y ver el QR.

**Escenarios de aceptación:**

1. **Dado** un celular con datos móviles, **cuando** abre la dirección pública, **entonces** carga la pantalla de cobro con HTTPS, sin advertencias del navegador ni inicio de sesión.
2. **Dado** la demo pública, **cuando** el dueño crea un cobro, **entonces** ve el QR en menos de 3 segundos, en 9 de cada 10 intentos.
3. **Dado** un cobro en pantalla, **cuando** el cliente lo paga, **entonces** el aviso de pey llega al servidor publicado con su firma válida.
4. **Dado** un canal de avisos abierto, **cuando** pasan 20 minutos (vigencia más ventana de escucha), **entonces** el canal sigue abierto hasta que el servidor lo cierra por fin de ventana, sin cortes de la infraestructura.
5. **Dado** una página de otro dominio, **cuando** intenta usar el servidor publicado desde el navegador, **entonces** el navegador lo bloquea.
6. **Dado** una publicación nueva del servidor, **cuando** termina, **entonces** la dirección pública y la del aviso de pey siguen siendo las mismas.

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

### Historia 4 — Que el gasto de AWS no pase de 200 dólares (Prioridad: P2)

**Como** Hugo, responsable del proyecto, **quiero** que el equipo reciba avisos del gasto y que el servidor se apague solo al llegar al tope, **para** que el crédito alcance hasta el 31 de enero y nadie pague de su bolsillo.

**Por qué esta prioridad:** AWS no tiene un tope de gasto que corte solo. Un error de configuración puede consumir el crédito en días. Va después de las historias 1 a 3 porque solo importa cuando ya hay algo publicado, pero se configura antes de publicar.

**Prueba independiente:** revisar que el presupuesto existe con sus avisos y su acción, y provocar un aviso de prueba bajando un momento un umbral por debajo del gasto actual (AWS no tiene un botón de aviso de prueba), para ver que llega a los tres correos del equipo.

**Escenarios de aceptación:**

1. **Dado** el presupuesto configurado, **cuando** el gasto real llega al 50 %, al 80 % y al 100 % de 200 dólares, **entonces** los tres integrantes del equipo reciben un correo en cada umbral.
2. **Dado** el presupuesto configurado, **cuando** el pronóstico de gasto del periodo pasa de 200 dólares, **entonces** el equipo recibe un correo.
3. **Dado** que AWS reporta que el gasto real llegó al 90 %, **cuando** se dispara la acción, **entonces** el servidor de la demo se apaga solo (puede tardar hasta unas 12 horas desde el gasto, por el retraso de AWS).
4. **Dado** que el crédito cubre el gasto, **cuando** se calcula el presupuesto, **entonces** se mide el gasto antes de descontar el crédito, para que los avisos lleguen aunque la factura sea de 0.
5. **Dado** el servidor apagado por el presupuesto, **cuando** Hugo revisa qué consumió el crédito y corrige la causa, **entonces** solo él puede volver a encenderlo, siguiendo su guía.

---

### Historia 5 — Saber antes de unir un pull request si algo se rompió (Prioridad: P1)

**Como** Juan, que revisa y une todos los pull requests, **quiero** ver en cada pull request si las pruebas y el lint pasan, **para** no tener que correrlos a mano ni unir algo roto.

**Por qué esta prioridad:** Juan condiciona la revisión del PR #72 a ver las pruebas en GitHub. Es lo más rápido de entregar y lo primero que desbloquea.

**Prueba independiente:** abrir un pull request con un error a propósito y ver que el CI falla; corregirlo y ver que pasa.

**Escenarios de aceptación:**

1. **Dado** un pull request hacia `main`, **cuando** se abre o se le suben cambios, **entonces** corren las pruebas y el lint del servidor y de la web, y el resultado aparece en el pull request.
2. **Dado** un pull request con una prueba que falla o un error de lint, **cuando** termina el CI, **entonces** el pull request se marca como fallido y no se puede unir.
3. **Dado** cualquier pull request, incluido uno desde un fork, **cuando** corre el CI, **entonces** no usa pey real, la base de datos real ni ningún secreto.

---

### Historia 6 — Cambiar la estructura de la base de datos con un comando (Prioridad: P2)

**Como** Hugo o Juan, **quiero** crear o actualizar las tablas con un solo comando, igual en local y en la demo, **para** no pegar SQL a mano en el editor de Supabase y no dejar la demo distinta de lo que dice el repositorio.

**Por qué esta prioridad:** hoy el esquema de #97 se corre a mano. Esta spec agrega una columna (la imagen del QR) y las specs de inicio de sesión e historial van a agregar más. Sin un comando repetible, la base de datos de la demo y la del repositorio terminan siendo distintas.

**Prueba independiente:** aplicar el comando en una base de datos vacía y después otra vez seguida: la primera crea todo y la segunda no cambia nada ni marca error. En la demo, el comando lo corre solo Hugo; la publicación automática no lo corre.

**Escenarios de aceptación:**

1. **Dado** una base de datos vacía, **cuando** se aplica el comando, **entonces** queda la estructura del PR #97 más la columna de la imagen del QR.
2. **Dado** una base de datos ya al día, **cuando** se aplica el comando otra vez, **entonces** no cambia nada, no borra datos y no marca error.
3. **Dado** la base de datos de la demo con el esquema de #97 ya corrido a mano, **cuando** se aplica el comando, **entonces** solo agrega lo que falta, sin borrar datos.

---

## 3. Requisitos *(obligatorio)*

### 3.1 Requisitos funcionales (notación EARS)

**Guardar cobros, pagos y avisos** (historia 1)

- **RF-001** (Ubicuo): EL SISTEMA guardará en la base de datos cada cobro creado, con todo lo que la spec 001 devuelve de él (RF-008), incluida la imagen del QR cuando pey la manda.
- **RF-002** (Ubicuo): EL SISTEMA guardará en la base de datos cada pago registrado antes de emitirlo por el canal de avisos.
- **RF-003** (Ubicuo): EL SISTEMA guardará en la base de datos el identificador de cada aviso de pey ya procesado.
- **RF-004** (Ubicuo): EL SISTEMA guardará en la base de datos la cancelación de cada cobro con su hora.
- **RF-005** (Dirigido por evento): CUANDO el servidor arranca, EL SISTEMA atenderá los cobros guardados (consultar, abrir el canal, consulta de respaldo, cancelar y registrar pagos) igual que si no se hubiera reiniciado.
- **RF-006** (Ubicuo): EL SISTEMA calculará el estado y la ventana de escucha de un cobro guardado con la hora del servidor, no con la de la base de datos, y las mismas reglas de la spec 001 (RF-017, RF-021 y RF-022), haya habido reinicio o no (QA-11).
- **RF-007** (Ubicuo): EL SISTEMA registrará cada transacción pagada de pey una sola vez, aunque el aviso y la consulta de respaldo la traigan al mismo tiempo, aunque pey reenvíe el aviso y aunque haya habido un reinicio entre las dos llegadas.
- **RF-008** (Ubicuo): EL SISTEMA numerará los pagos de un cobro sin saltos ni repetidos (1, 2, 3…), haya habido reinicio o no.
- **RF-009** (Ubicuo): EL SISTEMA no guardará en la base de datos ni escribirá en los registros los datos de quien paga (nombre, CLABE o cuenta, banco, teléfono ni clave de rastreo), aunque pey los mande en el aviso o en la consulta; de cada pago solo guarda lo que pide la spec 001 (RF-018) (QA-10).

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

- **RF-017** (Ubicuo): EL SISTEMA creará y actualizará la estructura de la base de datos con un solo comando, el mismo en local y en la demo pública.
- **RF-018** (Ubicuo): EL SISTEMA incluirá en ese comando el esquema del PR #97 y la columna nueva de la imagen del QR.
- **RF-019** (Dirigido por evento): CUANDO se aplica el comando a una base de datos que ya está al día, EL SISTEMA no cambiará nada ni borrará datos.
- **RF-049** (Ubicuo): EL SISTEMA usará en el servidor local una base de datos distinta de la de la demo, para que las pruebas locales no queden en los datos de la demo (QA-4).
- **RF-053** (Ubicuo): EL SISTEMA usará en el servidor local una llave de pey distinta de la de la demo, con su propio aviso: la del ambiente de pruebas de pey o, si ese ambiente no funciona, una segunda llave de producción (E-1).
- **RF-054** (Ubicuo): EL SISTEMA cargará los datos de prueba ficticios solo en la base de datos local, nunca en la de la demo (E-2).
- **RF-046** (Ubicuo): EL SISTEMA no aplicará cambios de estructura en la base de datos de la demo durante la publicación automática; solo Hugo los aplica, con el comando de RF-017, después de revisarlos.
- **RF-051** (Dirigido por evento): CUANDO Hugo va a aplicar un cambio de estructura en la base de datos de la demo, EL SISTEMA le indicará en su guía que primero exporte una copia de esa base de datos, porque el plan gratuito no incluye respaldos (QA-5).
- **RF-047** (No deseado): SI la versión publicada necesita un cambio de estructura que todavía no se aplicó, ENTONCES EL SISTEMA lo indicará en la salud del servidor y rechazará los cobros nuevos con un mensaje para el dueño, en lugar de fallar a medias.

**Credenciales y acceso** (historias 1 y 2)

- **RF-020** (Ubicuo): EL SISTEMA solo leerá las credenciales de la base de datos de la configuración del servidor (en local) o de las variables del hosting, nunca del repositorio.
- **RF-021** (Ubicuo): EL SISTEMA nunca incluirá las credenciales de la base de datos en sus respuestas, mensajes de error o registros.
- **RF-022** (Ubicuo): EL SISTEMA solo permitirá leer y escribir los datos guardados desde el servidor; la web, las apps y cualquiera con la dirección pública de la base de datos no podrán leerlos ni cambiarlos.
- **RF-023** (Dirigido por evento): CUANDO se consulta la salud del servidor, EL SISTEMA indicará además si la base de datos está configurada y responde, sin mostrar sus valores (amplía RF-038 de la spec 001, cambio C-6).
- **RF-039** (Estado): MIENTRAS la demo pública está publicada, EL SISTEMA consultará la base de datos al menos una vez al día, aunque nadie cree cobros, para que el plan gratuito no la pause por falta de uso.

**Demo pública** (historias 2 y 3)

- **RF-024** (Ubicuo): EL SISTEMA publicará la web y el servidor en la dirección con HTTPS que asigna el hosting, sin dominio propio, y cualquier celular la abrirá sin invitación ni inicio de sesión.
- **RF-025** (Ubicuo): EL SISTEMA recibirá los avisos de pey en la dirección pública del servidor, dada de alta en el portal de pey con su secreto.
- **RF-026** (Estado): MIENTRAS un canal de avisos está dentro de la ventana de escucha de su cobro, EL SISTEMA lo mantendrá abierto, sin cortes de la infraestructura, hasta que el servidor lo cierre (hasta 20 minutos).
- **RF-027** (Ubicuo): EL SISTEMA aceptará peticiones del navegador solo desde el dominio publicado de la web (aplica RF-035 de la spec 001 con la dirección real).
- **RF-028** (Ubicuo): EL SISTEMA aplicará los límites por IP de la spec 001 (RF-034 y RF-041) con la IP real del celular, no con la del intermediario del hosting.
- **RF-029** (Ubicuo): EL SISTEMA hará que la web publicada solo se conecte al servidor publicado de PAGO FÁCIL.
- **RF-030** (Dirigido por evento): CUANDO se publica una versión nueva del servidor, EL SISTEMA conservará la misma dirección pública y la misma dirección del aviso de pey.
- **RF-055** (Dirigido por evento): CUANDO se publica una versión nueva del servidor, EL SISTEMA volverá a responder en menos de 1 minuto, con un solo proceso como exige la spec 001 (E-4).
- **RF-042** (Dirigido por evento): CUANDO se une un pull request a `main` y su CI pasó, EL SISTEMA publicará solo la versión nueva del servidor y de la web en la demo pública.
- **RF-043** (Ubicuo): EL SISTEMA publicará sin guardar ninguna credencial de AWS en el repositorio ni en su configuración de GitHub, para respetar el principio III (las credenciales solo viven en `backend/.env` o en el hosting).
- **RF-044** (No deseado): SI la publicación automática falla, ENTONCES EL SISTEMA dejará atendiendo la versión anterior y mostrará el fallo en GitHub.
- **RF-045** (No deseado): SI el servidor está apagado por el presupuesto, ENTONCES EL SISTEMA no lo volverá a encender con una publicación automática (RF-040).

**Presupuesto** (historia 4)

- **RF-031** (Ubicuo): EL SISTEMA tendrá un presupuesto de 200 dólares en AWS que mide el gasto antes de descontar el crédito.
- **RF-032** (Dirigido por evento): CUANDO el gasto real llega al 50 %, al 80 % o al 100 % del presupuesto, EL SISTEMA enviará un correo a los tres integrantes del equipo.
- **RF-033** (Dirigido por evento): CUANDO el pronóstico de gasto pasa de 200 dólares, EL SISTEMA enviará un correo a los tres integrantes del equipo. AWS solo calcula el pronóstico después de unas 5 semanas de datos, así que este aviso no funcionará antes de fines de diciembre (QA-2).
- **RF-034** (Dirigido por evento): CUANDO AWS reporta que el gasto real llegó al 90 % del presupuesto, EL SISTEMA apagará el servidor de la demo sin intervención de nadie. El 10 % restante absorbe el retraso de AWS, que actualiza el gasto hasta tres veces al día (QA-2).
- **RF-035** (Ubicuo): EL SISTEMA usará una configuración cuyo costo estimado, desde su publicación hasta el 31 de enero de 2027, no pase del 75 % del presupuesto (150 dólares), para que el apagado automático no llegue antes de esa fecha.
- **RF-040** (Ubicuo): EL SISTEMA solo permitirá a Hugo volver a encender el servidor apagado por el presupuesto.
- **RF-041** (Ubicuo): EL SISTEMA tendrá una guía para Hugo con los pasos para revisar qué consumió el crédito, corregir la causa y volver a encender el servidor.
- **RF-050** (Ubicuo): EL SISTEMA tendrá en la guía de Hugo los pasos para reactivar el proyecto de Supabase de la demo si se pausa, y para comprobar después con la salud del servidor que la base de datos responde (QA-5).

**CI** (historia 5)

- **RF-036** (Dirigido por evento): CUANDO se abre un pull request hacia `main` o se le suben cambios, EL SISTEMA correrá las pruebas y el lint del servidor y de la web, y mostrará el resultado en el pull request.
- **RF-037** (No deseado): SI una prueba o el lint fallan, ENTONCES EL SISTEMA marcará el pull request como fallido e impedirá unirlo.
- **RF-038** (Ubicuo): EL SISTEMA correrá las revisiones de los pull requests sin pey real, sin la base de datos real y sin ningún secreto.

### 3.2 Entidades clave

- **Cobro**: lo mismo que en la spec 001, ahora guardado. Se le agrega la imagen del QR que manda pey (puede faltar). Queda sin negocio asociado hasta el inicio de sesión (#24).
- **Pago**: lo mismo que en la spec 001, ahora guardado. Su identificador de transacción de pey es único en todo el sistema.
- **Aviso de pey procesado**: el identificador de cada aviso ya atendido, para descartar reenvíos (primera barrera del principio II).
- **Cambio de estructura**: cada modificación de las tablas, con un orden y un registro de cuáles ya se aplicaron en cada base de datos.
- **Presupuesto**: el tope de 200 dólares en AWS, sus umbrales de aviso, a quién avisa y la acción de apagado.

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
| El servidor se reinicia con avisos todavía sin registrar | Esos avisos se pierden de la memoria. El pago se recupera si pey reenvía el aviso o si la consulta de respaldo lo encuentra dentro de la ventana de escucha. Limitación aceptada: requiere una falla de la base de datos y un reinicio a la vez. | RF-014, RF-048 |
| La base de datos no responde al consultar un cobro | Error temporal; la pantalla muestra "Reconectando…" y reintenta, sin ir a la vista Error. | RF-015 |
| Aviso de pey de un QR que no está en la base de datos | Se le responde bien a pey y queda registro, como en la spec 001. Ya no se espera por reinicio: solo por un QR ajeno o por RF-013. | RF-016 |
| Reinicio con canales de avisos abiertos | Los canales se cortan; la pantalla aplica su respaldo y su reconexión (spec 002, historia 4) y recibe el estado guardado. | RF-005 |
| Límites por IP tras un reinicio | Empiezan de cero. Limitación aceptada: un reinicio no es algo que un atacante provoque. | — |
| El proyecto de Supabase está pausado o sin servicio | La consulta diaria reduce el riesgo de pausa, pero Supabase no garantiza qué cuenta como uso (RF-039). Si no responde, la salud del servidor lo indica, los cobros nuevos se rechazan con un mensaje (RF-012) y Hugo lo reactiva con su guía (RF-050). | RF-012, RF-023, RF-039, RF-050 |
| Una migración daña datos de la demo | El plan gratuito no tiene respaldos: Hugo restaura la copia que exportó antes de aplicarla. | RF-051 |
| Se publica una versión nueva | La demo deja de responder menos de 1 minuto. La pantalla muestra "Reconectando…" y recupera sus cobros; los pagos de ese momento se registran por el aviso de pey o la consulta de respaldo, aunque sin la promesa de los 2 segundos. | RF-055 |
| La demo está apagada por el presupuesto o caída | Quien abre el enlace ve el error de su navegador; no hay página de "demo en pausa". | RF-034 |
| La publicación automática falla a medias | Sigue atendiendo la versión anterior y el fallo se ve en GitHub. | RF-044 |
| Se publica código que necesita una migración que Hugo todavía no aplicó | La salud del servidor lo indica y los cobros nuevos se rechazan con un mensaje hasta que Hugo la aplique. Conviene aplicar la migración antes de unir el pull request que la usa. | RF-046, RF-047 |
| Se une un pull request con un error que las pruebas no detectan | Se publica solo y lo ven los jueces. Se corrige con otro pull request; el CI (RF-037) es la única barrera. | RF-042 |
| El gasto llega al 90 % del presupuesto | El servidor se apaga solo y la demo deja de responder. Como AWS actualiza el gasto hasta tres veces al día (8 a 12 horas entre una y otra), el apagado puede llegar horas después; el 10 % restante es el margen para ese retraso. Solo Hugo lo vuelve a encender, después de revisar qué consumió el crédito y corregir la causa. | RF-034, RF-040, RF-041 |
| El servidor lleva días apagado por el presupuesto | Nadie hace la consulta diaria (RF-039) y Supabase puede pausar el proyecto. Al volver a encender, Hugo comprueba la salud del servidor y, si hace falta, reactiva el proyecto con su guía. | RF-039, RF-050 |
| Aviso por pronóstico en las primeras semanas | AWS no calcula el pronóstico hasta tener unas 5 semanas de datos: antes de eso solo llegan los avisos por gasto real. | RF-033 |
| **Devolución** | Fuera de alcance, como en la spec 001: pey no ofrece devoluciones por API. | — |

---

## 5. Fuera de alcance *(obligatorio)*

| Fuera de alcance | Dónde se resuelve |
|---|---|
| Registro e inicio de sesión del negocio; ligar cada cobro a su negocio | #24 (spec propia) |
| Historial de cobros y corte del día | #38 (spec propia) |
| Cuenta bancaria propia por negocio | Espera la respuesta de pey (flujo-de-trabajo §7, "Punto abierto") |
| Logs centralizados, monitor de disponibilidad y alertas si la demo se cae | #45 |
| Dibujar el QR en el servidor | Decidido en #94: se usa la imagen de pey |
| Guardar los límites por IP y los canales abiertos | No hace falta mientras corra un solo servidor |
| Varios servidores a la vez, escalado automático o publicar sin dejar de responder | No hace falta para la demo; la spec 001 exige un solo proceso y se acepta el corte de RF-055 (E-4) |
| Página de "demo en pausa" cuando el servidor está apagado o caído | No se construye: se ve el error del navegador (E-3) |
| Dominio propio (por ejemplo `pagofacil.mx`) | No entra en el hackathon: la demo usa la dirección de AWS (aclaración del 2026-11-17) |
| Cupones | #37 |
| Congelar la demo después de la entrega | #57 |

---

## 6. Criterios de éxito *(obligatorio)*

- **CE-001**: un cobro creado antes de un reinicio del servidor de la demo pública se paga con $0.01 después del reinicio, y la pantalla recargada vuelve a mostrar su QR y suena "Pago recibido".
- **CE-002**: desde la demo pública, con datos móviles, un pago real de $0.01 suena y muestra "Pago recibido" en menos de 2 segundos después de que pey entrega el aviso, en un Android y en un iPhone. Cierra #27 y #64 (spec 002, CE-001 y CE-002). #29 queda abierto hasta el inicio de sesión (#24), con una nota (QA-6).
- **CE-003**: desde la demo pública, el dueño ve el QR en menos de 3 segundos después de tocar Cobrar, en 9 de cada 10 intentos.
- **CE-004**: un canal de avisos abierto en la demo pública dura los 20 minutos de vigencia y ventana sin cortarse antes de que el servidor lo cierre.
- **CE-005**: ninguna transacción se registra dos veces, comprobado con pruebas automáticas de aviso reenviado, de aviso y consulta simultáneos y de llegada antes y después de un reinicio.
- **CE-006**: todo pull request hacia `main` muestra el resultado del CI, y uno con un error a propósito queda marcado como fallido y no se puede unir.
- **CE-007**: el comando de cambios de estructura se aplica dos veces seguidas sobre una base de datos vacía sin error, y la segunda vez no cambia nada.
- **CE-008**: los avisos del presupuesto están configurados y un aviso de prueba llega a los tres correos del equipo.
- **CE-009**: el costo estimado de la demo hasta el 31 de enero de 2027 no pasa de 150 dólares, con el cálculo anotado en el plan.
- **CE-010**: ninguna credencial de pey ni de la base de datos aparece en el repositorio, en las respuestas del servidor ni en sus registros, comprobado con búsquedas en el repositorio y con pruebas automáticas.
- **CE-011**: todas las pruebas automáticas pasan sin conexión a pey ni a la base de datos real.
- **CE-012**: durante 8 días seguidos sin cobros, los registros del servidor publicado muestran al menos una consulta diaria a la base de datos, y el proyecto de Supabase sigue activo al final. Es del corte 2 y se comprueba después de cerrar la spec, sin bloquearla (QA-5).
- **CE-013**: un pull request unido a `main` queda publicado en la demo sin que nadie haga nada, y una búsqueda en el repositorio y en su configuración de GitHub no encuentra credenciales de AWS.
- **CE-014**: en tres publicaciones seguidas de la demo, cada una deja de responder menos de 1 minuto y una pantalla con un cobro abierto se reconecta sola sin perder sus pagos (E-4).

---

## 7. Supuestos y dependencias

**Supuestos**

- Los 200 dólares son crédito de AWS y no cubren Supabase ni otros servicios (lo confirma Hugo).
- Supabase se queda en el plan gratuito. Su documentación dice que "may pause" los proyectos gratuitos con poca actividad en 7 días, sin definir qué cuenta como actividad, y que el plan gratuito no incluye respaldos (QA-5). Se supone que una consulta diaria basta; si aun así se pausa, Hugo lo reactiva (RF-050). Pasar al plan de pago es una decisión nueva de Hugo.
- AWS actualiza el gasto del presupuesto hasta tres veces al día y solo calcula el pronóstico tras unas 5 semanas de datos. Sus acciones automáticas solo detienen instancias EC2 o RDS, o aplican políticas de permisos: el plan elige un servicio que el presupuesto pueda detener o conecta el aviso a una función que lo detenga (QA-2).
- Solo Hugo tiene acceso a la cuenta de AWS; Juan y Miguel no lo necesitan para esta spec.
- Los correos del presupuesto son los tres del equipo que ya están en el formulario del kickoff (#68). Ningún correo se escribe en el repositorio.
- pey admite un solo webhook por llave, así que la demo y el servidor local usan llaves distintas (RF-053). Se supone que el ambiente de pruebas de pey (`https://api.dev.pey.mx`, que menciona `docs.pey.mx/llms.txt`) da una llave propia con su aviso; el aviso local llega por un túnel hasta la computadora de quien prueba (E-1).
- El servidor no usa el estado que calcula la vista `cobros_con_estado` del PR #97 (con la hora de la base de datos): lo calcula él con su reloj (RF-006). Se le avisa a Juan en la revisión del PR #97 y el plan lo registra como decisión (QA-11).
- El servidor sigue corriendo como un solo proceso, como exige la spec 001 (plan, QP-5): los canales de avisos y los límites por IP viven en su memoria.
- La base de datos no guarda la CLABE ni datos bancarios del negocio (comentario de la tabla de negocios del PR #97).
- La imagen del QR de pey pesa unos pocos KB por cobro, así que guardarla no compromete el espacio de la base de datos durante el hackathon.

**Dependencias**

| Dependencia | Para qué | Dueño | Estado |
|---|---|---|---|
| PR #97 unido (esquema inicial) | RF-018 y todo el guardado | Juan, revisa Hugo | Abierto, sin revisar |
| Proyecto de Supabase creado | Base de datos de la demo | Juan (#19) | Creado, según Hugo y el PR #97 |
| Credenciales de Supabase en `backend/.env` y en el hosting | RF-020 | Hugo | Pendiente |
| Cuenta de AWS con los 200 dólares de crédito | Historias 2 y 4 | Hugo | Pendiente de confirmar |
| Aviso dado de alta en el portal de pey con la dirección pública | RF-025 | Hugo (#15) | Pendiente; depende de la publicación |
| Protección de la rama `main` para exigir el CI | RF-037 | Juan (dueño del repositorio) | Pendiente |
| Permiso para que GitHub publique en la cuenta de AWS sin credenciales guardadas | RF-042 y RF-043 | Hugo (AWS) y Juan (configuración del repositorio) | Pendiente; si no es posible, hace falta enmendar el principio III |
| PR #72 unido (web de cobro en `main`), **antes del plan** | Publicar la web desde `main`; esta rama sale de la suya (QA-9) | Juan | Abierto, con cambios pedidos ya atendidos |
| PR #96 unido (constitución 2.0.0), **antes del plan** | La verificación de la constitución del plan se hace contra la 2.0.0, que agrega la base de datos y el hosting a la tabla de restricciones (QA-9) | Juan revisa, Hugo propone | Abierto |
| Segundo proyecto gratuito de Supabase para el servidor local | RF-049 (QA-4) | Juan (dueño de la organización de Supabase) | Pendiente |
| Llave de pey para el servidor local, del ambiente de pruebas o una segunda de producción | RF-053 (E-1) | Hugo, con pey | Pendiente |
| Un Android, un iPhone y la autorización de Hugo para pagos de $0.01 | CE-001 y CE-002 | Hugo | Disponibles el 16 nov |

---

## 8. Dudas y decisiones

### 8.1 Entrevista con Hugo (2026-11-17)

La entrevista se hizo después de la QA y de la aprobación, a pedido de Hugo.

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| E-1 | ¿Con qué llave de pey trabaja el servidor local? | Con el ambiente de pruebas de pey, con su propia llave y su propio aviso. Si no funciona, con una segunda llave de producción solo para local, también con su propio aviso. Sustituye la decisión de QA-4 de trabajar en local solo con la consulta de respaldo. | RF-053 |
| E-2 | ¿Se cargan en la demo los datos de prueba ficticios del PR #97? | No: solo en la base de datos local. | RF-054 |
| E-3 | ¿Qué ve quien abre el enlace con la demo apagada o caída? | El error del navegador; no se construye una página de "demo en pausa". | §4, §5 |
| E-4 | ¿Se acepta que la demo deje de responder en cada publicación? | Sí: se mantiene un solo proceso (spec 001) y la demo vuelve a responder en menos de 1 minuto. Varios procesos sin corte quedan fuera de alcance. | RF-055, §4, §5 |
| E-5 | ¿Se entrega primero el CI dentro del corte 1 (P-1)? | Sí. | §1.2, P-1 |

Decisiones tomadas antes de redactar, el 2026-11-17:

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| D-1 | ¿Qué abarca la spec 003? | Supabase + AWS + CI en una sola spec. | Toda la spec |
| D-2 | ¿De dónde sale la imagen del QR (#94)? | La que manda pey, guardada con el cobro en una columna nueva. Hugo agrega la columna con una migración. | RF-010, RF-011, RF-018 |
| D-3 | ¿Qué pasa al llegar a los 200 dólares? | Correos al 50 %, 80 % y 100 % y por pronóstico, y apagado automático. La QA (QA-2) bajó el apagado al 90 % por el retraso de AWS. | RF-031 a RF-035 |

### 8.2 Cambios a specs aprobadas

| # | Spec | Cambio propuesto | Origen | Estado |
|---|---|---|---|---|
| C-6 | 001 | (a) §4, fila "Reinicio del servidor": los cobros, pagos y avisos se conservan (spec 003), ya no se pierden. (b) §4, fila "Aviso de pago de un cobro desconocido": quitar "por ejemplo, tras reiniciar el servidor". (c) RF-038 y `contracts/salud.md`: la salud también indica si la base de datos está configurada y responde (RF-023 de esta spec). (d) §5, fila "Base de datos: los cobros se pierden al reiniciar": resuelto por la spec 003. (e) `data-model.md` (línea 5 y §5 y §6), `quickstart.md:80`, `contracts/ver-cobro.md:22` ("o se perdió al reiniciar") y `backend/README.md:118`: los cobros, pagos y avisos se guardan en la base de datos; los límites por IP y los canales siguen en memoria. (f) `contracts/aviso-pey.md:42`: el manejador ya hace una llamada de red (guardar en la base de datos); la meta de responder en menos de 1 s (CE-010 de la 001) se mantiene. | Esta spec y QA-7 | Propuesto |
| C-7 | 002 | RF-057: quitar el ejemplo "(por ejemplo, porque se reinició)", porque con la spec 003 un reinicio ya no hace que el servidor olvide un cobro. El comportamiento no cambia. | QA-7 | Propuesto |

### 8.3 Propuestas

| # | Propuesta | Por qué | Decisión |
|---|---|---|---|
| P-1 | Entregar primero el CI (§1.2) | Desbloquea la revisión del PR #72 y protege todo lo demás de esta spec | Aceptada por Hugo el 2026-11-17 (E-5) |

### 8.4 Revisión QA (2026-11-17, una sola pasada)

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
| QA-9 | Contradicción | La spec se apoya en la constitución 2.0.0 (Supabase y AWS en la tabla de restricciones), pero esta rama tiene la 1.0.0: el PR #96 no está unido, y en la 1.0.0 la tabla no tiene base de datos ni hosting. La rama además sale de `feature/64-web-mvp` (PR #72 sin unir). | §1, §7 | Agregar a las dependencias (§7) el PR #96 y el PR #72 unidos antes del plan, y citar la constitución como "2.0.0 (PR #96)". | Aceptada por Hugo el 2026-11-17: #96 y #72 unidos antes del plan. Aplicada el mismo día |
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

### 8.5 Pendientes

- Ninguna marca abierta. Las dos dudas del borrador se resolvieron en las aclaraciones del 2026-11-17.
- Tarea de Hugo fuera de la spec (E-1): confirmar con pey que su ambiente de pruebas da una llave propia con su aviso; si no, pedir una segunda llave de producción para local.
- Tarea de Hugo fuera de la spec (E-1): proponer el pull request que corrige la fila de la constitución que dice "No hay ambiente de pruebas: se prueba en producción con $0.01". La demo sigue en producción (principio VI), así que no cambia ningún principio.
- Tarea de Hugo fuera de la spec (QA-11): avisar a Juan en la revisión del PR #97 que el servidor no usa la columna `estado` de la vista.

---

## 9. Criterios de finalización

- [ ] Cada RF tiene al menos una prueba automática o un paso de verificación manual.
- [ ] Todos los criterios de éxito (CE) están comprobados.
- [ ] No quedan marcas `[NECESITA ACLARACIÓN]` abiertas.
- [ ] Hay una revisión de seguridad hecha: secretos, firma de webhooks y validación de entradas, más las credenciales de la base de datos y el acceso a ella solo desde el servidor.
- [ ] El cambio C-6 a la spec 001 está aprobado y aplicado.
- [ ] #27, #64, #90, #34, #65, #35 y #94 tienen su cierre o su nota de implementación, y #29 tiene una nota de que queda abierto hasta #24.
- [ ] El cambio C-7 a la spec 002 está aprobado y aplicado.
