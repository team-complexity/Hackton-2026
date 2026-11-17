# Spec 003: Infraestructura de la demo pública: guardar los cobros, publicar con HTTPS y probar cada cambio

- **ID**: `003-infraestructura-demo`
- **Fecha**: `2026-11-17`
- **Estado**: `Borrador`. Lo redactó Claude el 2026-11-17 con `/speckit-specify`, a partir de la descripción que Hugo ajustó ese día: alcance Supabase + AWS + CI, imagen del QR guardada (decisión de #94) y tope de gasto con apagado automático. Faltan la entrevista (`/entrevista-spec 003`) y la QA. Propone el cambio C-6 a la spec 001 (§8.2).
- **Rama**: `feature/90-infraestructura-demo` (propuesta; la crea Hugo)
- **Issues**: #90 (guardar cobros y pagos), #19 (conexión y cambios de estructura con un comando), #34 y #65 (publicar en AWS con HTTPS y el aviso de pey), #35 (CI), #94 (de dónde sale la imagen del QR). Con el pago real de esta spec se cierran #27, #29 y #64.
- **Entrada**: "Infraestructura de la demo pública: el backend guarda cobros, pagos y avisos de webhook en Supabase (PostgreSQL) en lugar de en memoria, con el esquema del PR #97, y backend y web se publican en AWS con HTTPS, el webhook de pey dado de alta y CI en cada pull request. Issues: #90, #19, #34 y #65, #35, #94 y el pago real de $0.01 que cierra #27, #29 y #64. Debe cumplir: después de reiniciar el servidor, un cobro pendiente sigue ahí, su pago se avisa y la web puede volver a mostrar su QR; la imagen del QR es la que manda pey y se guarda con el cobro, en una columna nueva de `cobros` que esta spec agrega con una migración sobre el esquema de #97, y si pey no la manda la web sigue mostrando el mensaje de C-3; un pago se registra una sola vez; las pruebas automáticas no usan ni la base de datos real ni pey real; las credenciales solo viven en el backend y en el hosting; el servicio de AWS no corta el canal de 20 minutos y corre un solo proceso; se mide que suene en menos de 2 s con el webhook activo, en Android y en iPhone; tope de gasto de 200 dólares de crédito hasta el 31 de enero de 2027, con correos al 50 %, 80 % y 100 % y por pronóstico, apagado automático al 100 % y presupuesto medido antes del crédito. Fuera de alcance: inicio de sesión (#24), historial (#38), cuenta bancaria por negocio y logs y monitoreo (#45)."

> **Notas para los comandos de spec-kit.**
> - `RF-###` equivale a *Functional Requirement* (FR-###).
> - `CE-###` equivale a *Success Criterion* (SC-###).
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
>
> La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas de datos, los algoritmos y las firmas de funciones: eso va en `plan.md` y `tasks.md`. Toda la spec se escribe en español. Supabase y AWS se nombran solo porque son decisiones ya tomadas por el equipo (constitución 2.0.0, tabla de restricciones técnicas); los requisitos no dependen de ellos.

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

### 1.2 Orden sugerido de entrega

No son cortes con fecha propia: todo entra en S1 (16 al 22 de noviembre). El orden lo decide el plan; esta es la propuesta, de lo que más desbloquea a lo que menos:

1. **CI** (historia 5): desbloquea la revisión del PR #72, que Juan condiciona a ver las pruebas en GitHub.
2. **Guardar cobros, pagos y avisos** (historias 1 y 6).
3. **Publicar con HTTPS y presupuesto** (historias 2 y 4).
4. **Pago real desde la demo pública** (historia 3), que cierra #27, #29 y #64.

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
2. **Dado** la demo pública, **cuando** el dueño crea un cobro, **entonces** ve el QR en menos de 3 segundos.
3. **Dado** un cobro en pantalla, **cuando** el cliente lo paga, **entonces** el aviso de pey llega al servidor publicado con su firma válida.
4. **Dado** un canal de avisos abierto, **cuando** pasan 20 minutos (vigencia más ventana de escucha), **entonces** el canal sigue abierto hasta que el servidor lo cierra por fin de ventana, sin cortes de la infraestructura.
5. **Dado** una página de otro dominio, **cuando** intenta usar el servidor publicado desde el navegador, **entonces** el navegador lo bloquea.
6. **Dado** una publicación nueva del servidor, **cuando** termina, **entonces** la dirección pública y la del aviso de pey siguen siendo las mismas.

---

### Historia 3 — Oír el pago real en menos de 2 segundos desde la demo pública (Prioridad: P1)

**Como** dueño de la tiendita, **quiero** que la pantalla suene en cuanto el cliente paga, **para** entregarle su mercancía sin esperar ni revisar mi banco.

**Por qué esta prioridad:** es el "momento del pago" que más pesa en la evaluación y el criterio que falta para cerrar #27, #29 y #64.

**Prueba independiente:** con autorización de Hugo, cobrar $0.01 desde la demo pública en un Android y en un iPhone, pagar desde otro celular y medir el tiempo entre que pey entrega el aviso y la pantalla muestra "Pago recibido".

**Escenarios de aceptación:**

1. **Dado** un cobro de $0.01 en la demo pública, en un Android con datos móviles, **cuando** el cliente paga desde la app de su banco, **entonces** la pantalla suena y muestra "Pago recibido" en menos de 2 segundos después de que pey entrega el aviso.
2. **Dado** lo mismo en un iPhone, **cuando** el cliente paga, **entonces** pasa lo mismo.
3. **Dado** un pago real ya avisado, **cuando** pey reenvía el aviso, **entonces** la pantalla no vuelve a sonar y el cobro sigue con un solo pago.

---

### Historia 4 — Que el gasto de AWS no pase de 200 dólares (Prioridad: P2)

**Como** Hugo, responsable del proyecto, **quiero** que el equipo reciba avisos del gasto y que el servidor se apague solo al llegar al tope, **para** que el crédito alcance hasta el 31 de enero y nadie pague de su bolsillo.

**Por qué esta prioridad:** AWS no tiene un tope de gasto que corte solo. Un error de configuración puede consumir el crédito en días. Va después de las historias 1 a 3 porque solo importa cuando ya hay algo publicado, pero se configura antes de publicar.

**Prueba independiente:** revisar que el presupuesto existe con sus avisos y su acción, y provocar un aviso de prueba que llegue a los tres correos del equipo.

**Escenarios de aceptación:**

1. **Dado** el presupuesto configurado, **cuando** el gasto real llega al 50 %, al 80 % y al 100 % de 200 dólares, **entonces** los tres integrantes del equipo reciben un correo en cada umbral.
2. **Dado** el presupuesto configurado, **cuando** el pronóstico de gasto del periodo pasa de 200 dólares, **entonces** el equipo recibe un correo.
3. **Dado** que el gasto real llega al 100 %, **cuando** se dispara el aviso, **entonces** el servidor de la demo se apaga solo.
4. **Dado** que el crédito cubre el gasto, **cuando** se calcula el presupuesto, **entonces** se mide el gasto antes de descontar el crédito, para que los avisos lleguen aunque la factura sea de 0.

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

**Prueba independiente:** aplicar el comando en una base de datos vacía y después otra vez seguida: la primera crea todo y la segunda no cambia nada ni marca error.

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
- **RF-006** (Ubicuo): EL SISTEMA calculará el estado y la ventana de escucha de un cobro guardado con la hora del servidor y las mismas reglas de la spec 001 (RF-017, RF-021 y RF-022), haya habido reinicio o no.
- **RF-007** (Ubicuo): EL SISTEMA registrará cada transacción pagada de pey una sola vez, aunque el aviso y la consulta de respaldo la traigan al mismo tiempo, aunque pey reenvíe el aviso y aunque haya habido un reinicio entre las dos llegadas.
- **RF-008** (Ubicuo): EL SISTEMA numerará los pagos de un cobro sin saltos ni repetidos (1, 2, 3…), haya habido reinicio o no.
- **RF-009** (Ubicuo): EL SISTEMA no guardará datos de quien paga (nombre, cuenta, banco ni teléfono), solo lo que la spec 001 guarda de cada pago (RF-018).

**Imagen del QR** (historia 1, decisión de #94)

- **RF-010** (Dirigido por evento): CUANDO se consulta un cobro guardado, EL SISTEMA devolverá la imagen del QR que pey mandó al crearlo, haya habido reinicio o no.
- **RF-011** (No deseado): SI pey no mandó la imagen del QR al crear el cobro, ENTONCES EL SISTEMA devolverá el cobro sin imagen, como hoy (la pantalla aplica RF-078 de la spec 002).

**Fallas de la base de datos** (historia 1)

- **RF-012** (No deseado): SI la base de datos no responde al crear un cobro, ENTONCES EL SISTEMA no le pedirá el QR a pey y responderá con un mensaje para el dueño.
- **RF-013** (No deseado): SI pey ya creó el QR pero la base de datos no responde al guardarlo, ENTONCES EL SISTEMA no devolverá el QR a la pantalla y responderá con un mensaje para el dueño, para que nadie pague un QR que el servidor no recuerda.
- **RF-014** (No deseado): SI la base de datos no responde al registrar un pago que llegó por el aviso de pey, ENTONCES EL SISTEMA le responderá a pey con error para que lo reenvíe, y no emitirá el pago por el canal.
- **RF-015** (No deseado): SI la base de datos no responde al consultar un cobro, ENTONCES EL SISTEMA responderá con un error temporal distinto de "cobro inexistente", para que la pantalla siga reintentando en lugar de mostrar la vista Error (spec 002, RF-057).
- **RF-016** (Ubicuo): EL SISTEMA dejará un registro de cada falla de la base de datos, con el identificador del cobro cuando lo haya, sin credenciales ni datos bancarios.

**Cambios de estructura** (historia 6)

- **RF-017** (Ubicuo): EL SISTEMA creará y actualizará la estructura de la base de datos con un solo comando, el mismo en local y en la demo pública.
- **RF-018** (Ubicuo): EL SISTEMA incluirá en ese comando el esquema del PR #97 y la columna nueva de la imagen del QR.
- **RF-019** (Dirigido por evento): CUANDO se aplica el comando a una base de datos que ya está al día, EL SISTEMA no cambiará nada ni borrará datos.

**Credenciales y acceso** (historias 1 y 2)

- **RF-020** (Ubicuo): EL SISTEMA solo leerá las credenciales de la base de datos de la configuración del servidor (en local) o de las variables del hosting, nunca del repositorio.
- **RF-021** (Ubicuo): EL SISTEMA nunca incluirá las credenciales de la base de datos en sus respuestas, mensajes de error o registros.
- **RF-022** (Ubicuo): EL SISTEMA solo permitirá leer y escribir los datos guardados desde el servidor; la web, las apps y cualquiera con la dirección pública de la base de datos no podrán leerlos ni cambiarlos.
- **RF-023** (Dirigido por evento): CUANDO se consulta la salud del servidor, EL SISTEMA indicará además si la base de datos está configurada y responde, sin mostrar sus valores (amplía RF-038 de la spec 001, cambio C-6).

**Demo pública** (historias 2 y 3)

- **RF-024** (Ubicuo): EL SISTEMA publicará la web y el servidor en una dirección con HTTPS que abre cualquier celular sin invitación ni inicio de sesión.
- **RF-025** (Ubicuo): EL SISTEMA recibirá los avisos de pey en la dirección pública del servidor, dada de alta en el portal de pey con su secreto.
- **RF-026** (Estado): MIENTRAS un canal de avisos está dentro de la ventana de escucha de su cobro, EL SISTEMA lo mantendrá abierto, sin cortes de la infraestructura, hasta que el servidor lo cierre (hasta 20 minutos).
- **RF-027** (Ubicuo): EL SISTEMA aceptará peticiones del navegador solo desde el dominio publicado de la web (aplica RF-035 de la spec 001 con la dirección real).
- **RF-028** (Ubicuo): EL SISTEMA aplicará los límites por IP de la spec 001 (RF-034 y RF-041) con la IP real del celular, no con la del intermediario del hosting.
- **RF-029** (Ubicuo): EL SISTEMA hará que la web publicada solo se conecte al servidor publicado de PAGO FÁCIL.
- **RF-030** (Dirigido por evento): CUANDO se publica una versión nueva del servidor, EL SISTEMA conservará la misma dirección pública y la misma dirección del aviso de pey.

**Presupuesto** (historia 4)

- **RF-031** (Ubicuo): EL SISTEMA tendrá un presupuesto de 200 dólares en AWS que mide el gasto antes de descontar el crédito.
- **RF-032** (Dirigido por evento): CUANDO el gasto real llega al 50 %, al 80 % o al 100 % del presupuesto, EL SISTEMA enviará un correo a los tres integrantes del equipo.
- **RF-033** (Dirigido por evento): CUANDO el pronóstico de gasto pasa de 200 dólares, EL SISTEMA enviará un correo a los tres integrantes del equipo.
- **RF-034** (Dirigido por evento): CUANDO el gasto real llega al 100 % del presupuesto, EL SISTEMA apagará el servidor de la demo sin intervención de nadie.
- **RF-035** (Ubicuo): EL SISTEMA usará una configuración cuyo costo estimado, desde su publicación hasta el 31 de enero de 2027, no pase del 75 % del presupuesto (150 dólares), para que el apagado automático no llegue antes de esa fecha.

**CI** (historia 5)

- **RF-036** (Dirigido por evento): CUANDO se abre un pull request hacia `main` o se le suben cambios, EL SISTEMA correrá las pruebas y el lint del servidor y de la web, y mostrará el resultado en el pull request.
- **RF-037** (No deseado): SI una prueba o el lint fallan, ENTONCES EL SISTEMA marcará el pull request como fallido e impedirá unirlo.
- **RF-038** (Ubicuo): EL SISTEMA correrá el CI sin pey real, sin la base de datos real y sin ningún secreto.

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
| **Falla de pey** al crear el QR | Sin cambios respecto a la spec 001 (RF-009 y RF-010): el cobro no se guarda como válido y la pantalla muestra el mensaje. | RF-012 |
| **Falla del aviso de pey** (no llega o llega tarde) | La consulta de respaldo sigue funcionando, también para cobros creados antes de un reinicio. | RF-005 |
| El aviso de pey y la consulta de respaldo traen el mismo pago a la vez | Se registra una sola vez y la pantalla suena una sola vez. | RF-007 |
| La base de datos no responde al crear un cobro | No se le pide el QR a pey; mensaje para el dueño. | RF-012 |
| La base de datos falla justo después de que pey creó el QR | La pantalla no recibe el QR y ve un mensaje; ese QR queda sin enseñarse. | RF-013 |
| La base de datos no responde cuando llega un aviso de pago | Se le responde con error a pey para que lo reenvíe; el pago se registra cuando la base de datos vuelve. | RF-014 |
| La base de datos no responde al consultar un cobro | Error temporal; la pantalla muestra "Reconectando…" y reintenta, sin ir a la vista Error. | RF-015 |
| Aviso de pey de un QR que no está en la base de datos | Se le responde bien a pey y queda registro, como en la spec 001. Ya no se espera por reinicio: solo por un QR ajeno o por RF-013. | RF-016 |
| Reinicio con canales de avisos abiertos | Los canales se cortan; la pantalla aplica su respaldo y su reconexión (spec 002, historia 4) y recibe el estado guardado. | RF-005 |
| Límites por IP tras un reinicio | Empiezan de cero. Limitación aceptada: un reinicio no es algo que un atacante provoque. | — |
| El proyecto de Supabase está pausado o sin servicio | La salud del servidor lo indica y los cobros nuevos se rechazan con un mensaje (RF-012). Ver la duda del plan gratuito en §8.5. | RF-012, RF-023 |
| El presupuesto llega al 100 % | El servidor se apaga solo y la demo deja de responder hasta que alguien lo vuelva a encender. | RF-034 |
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
| Varios servidores a la vez o escalado automático | No hace falta para la demo; la spec 001 exige un solo proceso |
| Dominio propio (por ejemplo `pagofacil.mx`) | Ver supuestos (§7) |
| Cupones | #37 |
| Congelar la demo después de la entrega | #57 |

---

## 6. Criterios de éxito *(obligatorio)*

- **CE-001**: un cobro creado antes de un reinicio del servidor de la demo pública se paga con $0.01 después del reinicio, y la pantalla recargada vuelve a mostrar su QR y suena "Pago recibido".
- **CE-002**: desde la demo pública, con datos móviles, un pago real de $0.01 suena y muestra "Pago recibido" en menos de 2 segundos después de que pey entrega el aviso, en un Android y en un iPhone. Cierra #27, #29 y #64 (spec 002, CE-001 y CE-002).
- **CE-003**: desde la demo pública, el dueño ve el QR en menos de 3 segundos después de tocar Cobrar, en 9 de cada 10 intentos.
- **CE-004**: un canal de avisos abierto en la demo pública dura los 20 minutos de vigencia y ventana sin cortarse antes de que el servidor lo cierre.
- **CE-005**: ninguna transacción se registra dos veces, comprobado con pruebas automáticas de aviso reenviado, de aviso y consulta simultáneos y de llegada antes y después de un reinicio.
- **CE-006**: todo pull request hacia `main` muestra el resultado del CI, y uno con un error a propósito queda marcado como fallido y no se puede unir.
- **CE-007**: el comando de cambios de estructura se aplica dos veces seguidas sobre una base de datos vacía sin error, y la segunda vez no cambia nada.
- **CE-008**: los avisos del presupuesto están configurados y un aviso de prueba llega a los tres correos del equipo.
- **CE-009**: el costo estimado de la demo hasta el 31 de enero de 2027 no pasa de 150 dólares, con el cálculo anotado en el plan.
- **CE-010**: ninguna credencial de pey ni de la base de datos aparece en el repositorio, en las respuestas del servidor ni en sus registros, comprobado con búsquedas en el repositorio y con pruebas automáticas.
- **CE-011**: todas las pruebas automáticas pasan sin conexión a pey ni a la base de datos real.

---

## 7. Supuestos y dependencias

**Supuestos**

- Los 200 dólares son crédito de AWS y no cubren Supabase ni otros servicios (lo confirma Hugo).
- La demo usa la dirección que entrega AWS, sin dominio propio. Si Hugo quiere un dominio, se agrega en la entrevista.
- Los correos del presupuesto son los tres del equipo que ya están en el formulario del kickoff (#68). Ningún correo se escribe en el repositorio.
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
| PR #72 unido (web de cobro en `main`) | Publicar la web desde `main` | Juan | Abierto, con cambios pedidos ya atendidos |
| Un Android, un iPhone y la autorización de Hugo para pagos de $0.01 | CE-001 y CE-002 | Hugo | Disponibles el 16 nov |

---

## 8. Dudas y decisiones

### 8.1 Entrevista con Hugo

Pendiente (`/entrevista-spec 003`). Decisiones ya tomadas antes de redactar, el 2026-11-17:

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| D-1 | ¿Qué abarca la spec 003? | Supabase + AWS + CI en una sola spec. | Toda la spec |
| D-2 | ¿De dónde sale la imagen del QR (#94)? | La que manda pey, guardada con el cobro en una columna nueva. Hugo agrega la columna con una migración. | RF-010, RF-011, RF-018 |
| D-3 | ¿Qué pasa al llegar a los 200 dólares? | Correos al 50 %, 80 % y 100 % y por pronóstico, y apagado automático al 100 %. | RF-031 a RF-035 |

### 8.2 Cambios a specs aprobadas

| # | Spec | Cambio propuesto | Origen | Estado |
|---|---|---|---|---|
| C-6 | 001 | (a) §4, fila "Reinicio del servidor": los cobros, pagos y avisos se conservan (spec 003), ya no se pierden. (b) §4, fila "Aviso de pago de un cobro desconocido": quitar "por ejemplo, tras reiniciar el servidor". (c) RF-038 y `contracts/salud.md`: la salud también indica si la base de datos está configurada y responde (RF-023 de esta spec). | Esta spec | Propuesto |

### 8.3 Propuestas

| # | Propuesta | Por qué | Decisión |
|---|---|---|---|
| P-1 | Entregar primero el CI (§1.2) | Desbloquea la revisión del PR #72 y protege todo lo demás de esta spec | Pendiente |

### 8.4 Revisión QA

Pendiente (`/qa-spec 003`).

### 8.5 Pendientes

- `[NECESITA ACLARACIÓN: según la política que conocemos, el plan gratuito de Supabase pausa un proyecto tras una semana sin uso, y la demo debe vivir hasta el 31 de enero de 2027 (#57). ¿Se paga el plan de pago de Supabase (fuera del crédito de AWS) o se mantiene el gratuito con alguna medida para que no se pause?]`
- `[NECESITA ACLARACIÓN: cuando el presupuesto apague el servidor (RF-034), ¿quién lo vuelve a encender y con qué criterio, sobre todo entre el 10 y el 14 de diciembre, cuando evalúan los jueces?]`

---

## 9. Criterios de finalización

- [ ] Cada RF tiene al menos una prueba automática o un paso de verificación manual.
- [ ] Todos los criterios de éxito (CE) están comprobados.
- [ ] No quedan marcas `[NECESITA ACLARACIÓN]` abiertas.
- [ ] Hay una revisión de seguridad hecha: secretos, firma de webhooks y validación de entradas, más las credenciales de la base de datos y el acceso a ella solo desde el servidor.
- [ ] El cambio C-6 a la spec 001 está aprobado y aplicado.
- [ ] #27, #29, #64, #90, #34, #65, #35 y #94 tienen su cierre o su nota de implementación.
