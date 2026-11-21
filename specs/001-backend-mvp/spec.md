# Spec 001: Backend del MVP: cobrar con CoDi y saber que me pagaron

- **ID**: `001-backend-mvp`
- **Fecha**: `2026-11-14`
- **Estado**: `Aprobada`. Hugo la aprobó el 2026-11-14, después de la entrevista (E-1 a E-7) y de la QA (QA-1 a QA-10, todas aplicadas). Se entrega en dos cortes (§1.2). El cambio C-1 (QR reutilizado y monto distinto en el corte M0) se aprobó y aplicó el 2026-11-14 (§8.2). El cambio C-2 (hora actual del servidor en cada cobro, pedido por la spec 002) se aprobó y aplicó el 2026-11-15.
- **Rama**: `feature/18-backend-mvp`
- **Issues**: #18 (estructura), #62 (crear cobro), #63 (aviso de pago), #65 (despliegue, solo como dependencia)
- **Entrada**: "iniciemos la entrevista y preparativos de la redaccion de la spec 001"

> **Notas para los comandos de spec-kit.**
> - `RF-###` equivale a *Functional Requirement* (FR-###).
> - `CE-###` equivale a *Success Criterion* (SC-###).
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
>
> La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas de datos, los algoritmos y las firmas de funciones: eso va en `plan.md` y `tasks.md`. Toda la spec se escribe en español.

---

## 1. Contexto y propósito (por qué)

Los negocios pequeños de México (tienditas, ferreterías, tortillerías) casi no cobran con medios electrónicos porque las terminales cobran comisión. CoDi permite cobrar sin comisión con un QR que el cliente paga desde la app de su banco, pero el negocio necesita una herramienta que genere ese QR y le diga en segundos que el dinero llegó.

Esta spec cubre el **servidor** de PAGO FÁCIL: crear un cobro CoDi real con pey, confirmar cada pago de forma confiable y avisar a la pantalla del negocio. Es el recorrido mínimo que exigen las reglas del hackathon: un cobro CoDi real y una reacción visible a su resultado. La pantalla del negocio es otra spec (#64); esta deja listo todo lo que esa pantalla necesita.

Ya existe un prototipo con 15 pruebas que creó un cobro real el 14 nov. Esta spec es el contrato contra el que se revisa ese prototipo: donde difieren, manda la spec y el código se ajusta con pruebas primero (QA-10).

### 1.1 Glosario

| Término | Significado en esta spec |
|---|---|
| Negocio | Quien cobra. En el MVP hay un solo negocio de demo, sin cuenta ni inicio de sesión. |
| Cliente | Quien paga, desde la app de su banco en la opción CoDi. |
| Cobro | Lo que el negocio pide a sus clientes, con un QR CoDi. Puede ser de monto fijo o de monto libre. |
| Monto fijo | El negocio escribe un monto mayor a 0; el banco del cliente cobra exactamente esa cantidad y el cliente no la puede cambiar. |
| Monto libre | El negocio deja el monto vacío o escribe 0; el cliente escribe en su banco cuánto paga. |
| Pago | Una transacción **pagada** que pey confirma para el QR de un cobro. Las transacciones que pey reporta como pendientes no son pagos. Un cobro puede recibir varios pagos (QR reutilizado). |
| Monto recibido | El total de un pago que reporta pey. Puede incluir propina o comisión cobrada al pagador, si pey las reporta. |
| Monto base | La parte del pago sin propina ni comisión, cuando pey reporta ese desglose. |
| Número de pago | El orden del pago dentro de su cobro: 1, 2, 3… sin límite. |
| pey | El proveedor cuyo API crea los QR CoDi y avisa de los pagos. |
| Aviso de pago de pey | El mensaje firmado que pey manda al servidor cuando un QR recibe un pago (webhook). |
| Consulta de respaldo | Cuando el servidor le pregunta directamente a pey qué pagos tiene el QR de un cobro. |
| Canal de avisos | La conexión abierta por la que la pantalla del negocio se entera, sin recargar, de los pagos y cambios de estado de un cobro. |
| IP del cliente | La dirección de quien usa la demo, no la del proxy del hosting por el que pasa la petición. |
| Vigencia | Los 10 minutos durante los que el QR se muestra como cobrable. |
| Ventana de escucha | Desde que se crea el cobro hasta 10 minutos después de su vencimiento (en el corte M0, hasta el vencimiento). Durante ella el sistema sigue detectando y avisando pagos. |
| Estados del cobro | *Pendiente* (sin pagos, dentro de la vigencia), *pagado* (recibió al menos un pago), *vencido* (pasó la vigencia sin pagos) y *cancelado* (el negocio lo canceló sin pagos). |

### 1.2 Cortes de entrega (QA-1)

La spec se aprueba completa, pero se construye en dos cortes. Cada historia, escenario y RF lleva el suyo.

| Corte | Fecha | Qué entrega |
|---|---|---|
| **Corte M0** | 15 nov, 1:00 PM (kickoff) | Cobro de monto fijo, aviso de cada pago con firma, deduplicación y su número (QR reutilizado), monto distinto visible, consulta de respaldo (también la que hace el servidor por su cuenta), canal de avisos, protección de la demo pública y salud. |
| **Corte 2** | Antes del 21 nov (inicio de M2) | Ventana de gracia de 10 minutos, monto libre y cancelación. (El QR reutilizado y el monto distinto visible pasaron al corte M0 con C-1.) |

**Comportamiento temporal del corte M0**, mientras no llega el corte 2. Cada punto deja de valer al entregar el corte 2:

- Un monto vacío o 0 se rechaza como monto no válido, porque todavía no hay monto libre.
- La ventana de escucha termina al vencer el QR, sin los 10 minutos de gracia.
- No hay cancelación.

---

## 2. Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Cobrar con un QR (Prioridad: P1) · Corte M0 (monto libre: corte 2)

**Como** dueño de una tiendita, **quiero** escribir el monto, o dejarlo libre, y obtener un QR CoDi, **para** que mi cliente me pague sin efectivo y sin que yo pague comisión.

**Por qué esta prioridad:** sin QR no hay cobro. Es el primer paso del recorrido que exigen las reglas.

**Prueba independiente:** crear un cobro de $0.01 y escanear el QR desde la app de un banco con CoDi activado; la app del banco muestra el monto y el concepto.

**Escenarios de aceptación:**

1. *(M0)* **Dado** un servidor con su llave de pey configurada, **cuando** el negocio pide un cobro de $0.01 con concepto "Tacos", **entonces** recibe un cobro *pendiente* con su QR (contenido e imagen), su identificador y la hora en que vence.
2. *(Corte 2)* **Dado** un cobro pedido sin monto o con monto 0, **cuando** el cliente lo escanea, **entonces** su banco le pide escribir la cantidad.
3. *(M0)* **Dado** un monto negativo, con más de 2 decimales, no numérico o mayor al máximo de la demo, **cuando** el negocio pide el cobro, **entonces** se rechaza con un mensaje para el dueño y no se le pide nada a pey.
4. *(M0)* **Dado** un concepto con caracteres no imprimibles, **cuando** el negocio pide el cobro, **entonces** se rechaza con un mensaje para el dueño y no se le pide nada a pey.
5. *(M0)* **Dado** que pey está en mantenimiento o rechaza la solicitud, **cuando** el negocio pide el cobro, **entonces** recibe un mensaje que puede mostrar en pantalla y el cobro no queda guardado.

---

### Historia 2 — Saber que me pagaron (Prioridad: P1) · Corte M0

**Como** dueño, **quiero** enterarme de cada pago en cuanto ocurre, **para** entregar el producto sin revisar capturas ni la app de mi banco.

**Por qué esta prioridad:** es la "reacción al resultado" que exigen las reglas y el momento que más pesa en la evaluación (30 % del puntaje es el uso de CoDi y de pey).

**Prueba independiente:** con el canal de avisos del cobro abierto, pagar el QR desde la app del banco; el canal recibe el pago en menos de 2 segundos después de que pey entrega su aviso.

**Escenarios de aceptación:**

1. *(M0)* **Dado** un cobro *pendiente* con el canal de avisos abierto, **cuando** llega un aviso de pago de pey con firma válida para ese cobro, **entonces** el cobro pasa a *pagado* y el canal recibe el pago con su número (1), el monto recibido y su hora.
2. *(M0)* **Dado** un cobro ya *pagado* cuyo QR se reutiliza, **cuando** llega un pago con otra transacción, **entonces** el canal recibe un aviso nuevo con el número de pago 2 y el total recibido.
3. *(M0)* **Dado** un aviso de pago sin firma, con firma de otro secreto o con firma vencida, **cuando** llega al servidor, **entonces** se rechaza y ningún cobro cambia.
4. *(M0)* **Dado** un pago ya registrado, **cuando** pey reenvía su aviso o la consulta de respaldo lo vuelve a encontrar, **entonces** se le responde bien a pey pero el pago no se registra dos veces ni se vuelve a avisar.
5. *(M0)* **Dado** un cobro que ya recibió pagos, **cuando** la pantalla abre su canal de avisos, **entonces** recibe de inmediato el estado actual con el número de pagos y el total recibido.
6. *(M0)* **Dado** un cobro de monto fijo, **cuando** pey reporta un pago cuyo monto base es distinto al pedido, **entonces** el aviso muestra el monto pedido y el monto realmente recibido.

---

### Historia 3 — No perder un pago si falla el aviso de pey o llega tarde (Prioridad: P1) · Corte M0 (escenarios 4 y 5: corte 2)

**Como** dueño, **quiero** que el sistema confirme los pagos aunque el aviso de pey no llegue o el cliente pague justo al vencer el QR, **para** no quedarme con la duda frente al cliente.

**Por qué esta prioridad:** el aviso de pey depende de que el servidor esté publicado con HTTPS y el aviso configurado en el portal de pey (#65). Sin respaldo, una falla ahí arruina la demo del kickoff.

**Prueba independiente:** sin aviso de pey configurado y con el canal de avisos abierto, pagar un QR; el servidor le pregunta a pey por su cuenta y el canal recibe el pago sin que la pantalla consulte nada.

**Escenarios de aceptación:**

1. *(M0)* **Dado** un cobro con el canal de avisos abierto y sin aviso de pey recibido, **cuando** pey registra un pago, **entonces** el servidor lo encuentra al preguntarle a pey por su cuenta (cada 5 segundos) y lo avisa por el canal.
2. *(M0)* **Dado** un cobro dentro de su ventana de escucha, **cuando** la pantalla consulta su estado, **entonces** el servidor le pregunta a pey y registra y avisa cada pago nuevo que pey reporte.
3. *(M0)* **Dado** muchas consultas seguidas del mismo cobro, **cuando** la pantalla insiste, **entonces** el servidor le pregunta a pey como máximo una vez cada 3 segundos por cobro.
4. *(Corte 2)* **Dado** un cobro *vencido* hace 5 minutos, **cuando** llega su pago, **entonces** pasa a *pagado* y el canal, que sigue abierto, avisa del pago.
5. *(Corte 2)* **Dado** un cobro que venció hace más de 10 minutos, **cuando** la pantalla consulta su estado o abre su canal, **entonces** el servidor ya no le pregunta a pey y el canal emite el estado actual y se cierra.

---

### Historia 4 — Cancelar un cobro equivocado (Prioridad: P2) · Corte 2

**Como** dueño, **quiero** cancelar un cobro que todavía no se paga, **para** quitarlo de la pantalla si me equivoqué de monto o el cliente se arrepintió.

**Por qué esta prioridad:** es un error común en el mostrador, pero el cobro funciona sin esta historia.

**Prueba independiente:** crear un cobro, cancelarlo y comprobar que queda *cancelado*; después pagar ese QR desde el banco y comprobar que el pago se registra y se avisa.

**Escenarios de aceptación:**

1. **Dado** un cobro *pendiente*, **cuando** el negocio lo cancela, **entonces** queda *cancelado* y el canal avisa la cancelación en menos de 15 segundos.
2. **Dado** un cobro *cancelado*, **cuando** el cliente paga ese QR desde su banco (pey no permite anular un QR), **entonces** el cobro pasa a *pagado* y el pago se avisa igual.
3. **Dado** un cobro *pagado* o *vencido*, **cuando** el negocio intenta cancelarlo, **entonces** se rechaza con un mensaje para el dueño.

---

### Historia 5 — Una demo pública que no se pueda abusar (Prioridad: P2) · Corte M0

**Como** equipo, **queremos** que cualquiera pueda probar la demo sin poder saturarla ni gastar nuestra cuenta de pey, **para** compartir el enlace con los jueces y con negocios piloto.

**Por qué esta prioridad:** el formulario del kickoff pide el enlace a la app en vivo; desde ese momento cualquiera puede generar QR.

**Prueba independiente:** pedir cobros seguidos desde la misma IP del cliente hasta pasar el límite; el siguiente se rechaza sin pedirle nada a pey.

**Escenarios de aceptación:**

1. **Dado** una misma IP del cliente que ya pidió los cobros permitidos en un minuto, **cuando** pide uno más, **entonces** se rechaza con un mensaje de "espera un minuto" y no se le pide nada a pey.
2. **Dado** dos visitantes con IP distinta que llegan por el mismo proxy del hosting, **cuando** cada uno pide cobros, **entonces** cada uno tiene su propio límite.
3. **Dado** una misma IP del cliente con 10 canales de avisos abiertos, **cuando** intenta abrir otro, **entonces** se rechaza con un mensaje de "cierra otras pantallas".
4. **Dado** una página servida desde un dominio que no es el de la web de PAGO FÁCIL, **cuando** intenta usar el servidor desde el navegador, **entonces** el navegador lo bloquea.

---

### Historia 6 — Saber si el servidor está bien configurado (Prioridad: P3) · Corte M0

**Como** quien despliega, **quiero** comprobar en segundos que el servidor responde y tiene sus credenciales, **para** detectar un despliegue mal configurado antes de la demo, sin exponer las credenciales.

**Por qué esta prioridad:** ahorra tiempo al desplegar (#65), pero el cobro funciona sin ella.

**Prueba independiente:** consultar la salud del servidor con y sin credenciales configuradas; la respuesta dice cuáles faltan y nunca muestra sus valores.

**Escenarios de aceptación:**

1. **Dado** un servidor sin el secreto del aviso de pey, **cuando** se consulta su salud, **entonces** indica que responde, que la llave está configurada y que el secreto falta.

---

## 3. Requisitos *(obligatorio)*

### 3.1 Requisitos funcionales (notación EARS)

Cada RF lleva su corte: **[M0]** para el kickoff o **[C2]** para el corte 2 (§1.2).

**Crear cobro**

- **RF-001** (Dirigido por evento) [M0]: CUANDO el negocio pide un cobro válido, EL SISTEMA creará un QR CoDi con pey y devolverá el cobro en estado *pendiente*.
- **RF-002** (Ubicuo) [M0]: EL SISTEMA aceptará como monto fijo una cantidad en MXN mayor a 0, con máximo 2 decimales y menor o igual al máximo de la demo, configurable y de $100 por defecto.
- **RF-003** (Dirigido por evento) [C2]: CUANDO el negocio pide un cobro sin monto o con monto 0, EL SISTEMA creará un cobro de monto libre, cuyo QR deja que el cliente escriba la cantidad en su banco.
- **RF-004** (No deseado) [M0]: SI el monto no es válido, ENTONCES EL SISTEMA rechazará el cobro con un mensaje para el dueño sin pedirle nada a pey.
- **RF-005** (Ubicuo) [M0]: EL SISTEMA aceptará un concepto opcional de máximo 40 caracteres imprimibles, usará "Cobro" cuando falte y quitará los espacios sobrantes.
- **RF-042** (No deseado) [M0]: SI el concepto tiene caracteres no imprimibles, ENTONCES EL SISTEMA rechazará el cobro con un mensaje para el dueño sin pedirle nada a pey.
- **RF-006** (Ubicuo) [M0]: EL SISTEMA pedirá cada QR a pey con una vigencia de 10 minutos.
- **RF-007** (Ubicuo) [M0]: EL SISTEMA enviará a pey el identificador interno del cobro junto con la solicitud del QR, para poder relacionar cada pago con su cobro.
- **RF-008** (Ubicuo) [M0]: EL SISTEMA devolverá de cada cobro su identificador, su identificador CoDi, el monto pedido o la indicación de monto libre, el concepto, el estado, el contenido del QR, la imagen del QR cuando pey la entregue, la hora de creación, la hora de vencimiento, el número de pagos recibidos, el total recibido, la hora del último pago y la hora actual del servidor (C-2).
- **RF-009** (No deseado) [M0]: SI pey no crea el QR, ENTONCES EL SISTEMA responderá con un mensaje para el dueño y no guardará el cobro.
- **RF-010** (No deseado) [M0]: SI pey no crea el QR, ENTONCES EL SISTEMA distinguirá en su respuesta cuatro causas: falta configuración, llave rechazada, pey en mantenimiento y error general.

**Registrar pagos**

- **RF-011** (No deseado) [M0]: SI llega un aviso de pago de pey cuya firma no es válida con el secreto configurado, ENTONCES EL SISTEMA lo rechazará sin cambiar ningún cobro.
- **RF-012** (Dirigido por evento) [M0]: CUANDO llega un aviso de pago de pey con firma válida, EL SISTEMA registrará el pago en el cobro al que corresponde el QR.
- **RF-013** (No deseado) [M0]: SI llega un aviso de pey de un tipo distinto a "QR pagado", ENTONCES EL SISTEMA le responderá bien a pey y lo ignorará.
- **RF-014** (Ubicuo) [M0]: EL SISTEMA registrará cada transacción pagada de pey una sola vez, aunque pey reenvíe el aviso o la consulta de respaldo la vuelva a encontrar.
- **RF-015** (Ubicuo) [M0]: EL SISTEMA registrará como pago nuevo, sin límite de cantidad, cada transacción pagada distinta que reciba el QR de un cobro.
- **RF-016** (Ubicuo) [M0]: EL SISTEMA asignará a cada pago su número dentro del cobro, en orden de registro: 1, 2, 3…
- **RF-017** (Dirigido por evento) [M0]: CUANDO un cobro sin pagos (*pendiente*, *vencido* o *cancelado*) recibe su primer pago, EL SISTEMA lo pasará a *pagado*.
- **RF-018** (Ubicuo) [M0]: EL SISTEMA guardará de cada pago el monto recibido, el monto base cuando pey lo reporte, su hora y su identificador de transacción.
- **RF-019** (No deseado) [M0]: SI un pago de un cobro de monto fijo tiene un monto base distinto al pedido (o un monto recibido distinto, cuando pey no reporta el monto base), ENTONCES EL SISTEMA mostrará el monto pedido y el monto recibido en el cobro y en el aviso.
- **RF-020** (No deseado) [M0]: SI un pago de un cobro de monto fijo tiene un monto base distinto al pedido (o un monto recibido distinto, cuando pey no reporta el monto base), ENTONCES EL SISTEMA dejará una advertencia en el registro.

**Vigencia, vencimiento y cancelación**

- **RF-021** (Dirigido por evento) [M0]: CUANDO pasan 10 minutos desde la creación de un cobro *pendiente*, EL SISTEMA lo pasará a *vencido*.
- **RF-022** (Estado) [C2]: MIENTRAS un cobro está dentro de los 10 minutos posteriores a su vencimiento, EL SISTEMA seguirá registrando y avisando sus pagos, sea cual sea su estado.
- **RF-023** (Dirigido por evento) [C2]: CUANDO el negocio cancela un cobro *pendiente*, EL SISTEMA lo pasará a *cancelado*.
- **RF-024** (No deseado) [C2]: SI el negocio intenta cancelar un cobro que no está *pendiente*, ENTONCES EL SISTEMA lo rechazará con un mensaje para el dueño.

**Consulta de respaldo**

- **RF-025** (Estado) [M0]: MIENTRAS un cobro está dentro de su ventana de escucha, EL SISTEMA le preguntará a pey por los pagos de su QR cuando se consulte el cobro, como máximo una vez cada 3 segundos por cobro.
- **RF-040** (Estado) [M0]: MIENTRAS un cobro tiene al menos un canal de avisos abierto dentro de su ventana de escucha, EL SISTEMA le preguntará a pey por los pagos de su QR cada 5 segundos, sin esperar a que la pantalla consulte.
- **RF-026** (Dirigido por evento) [M0]: CUANDO la consulta de respaldo encuentra una transacción pagada nueva, EL SISTEMA la registrará y la avisará igual que si hubiera llegado por el aviso de pey.
- **RF-027** (No deseado) [M0]: SI pey no responde a la consulta de respaldo, ENTONCES EL SISTEMA devolverá el cobro con su último estado conocido.

**Avisar en tiempo real**

- **RF-028** (Ubicuo) [M0]: EL SISTEMA ofrecerá por cada cobro un canal de avisos.
- **RF-029** (Dirigido por evento) [M0]: CUANDO se registra un pago, EL SISTEMA emitirá por el canal un aviso de pago con su número, el monto recibido, su hora, el monto pedido o la indicación de monto libre y el total recibido.
- **RF-030** (Dirigido por evento) [M0; *cancelado* en C2]: CUANDO un cobro pasa a *vencido* o a *cancelado*, EL SISTEMA emitirá ese estado por el canal en menos de 15 segundos.
- **RF-031** (Dirigido por evento) [M0]: CUANDO la pantalla abre el canal de un cobro, EL SISTEMA emitirá de inmediato su estado actual, con el número de pagos y el total recibido.
- **RF-032** (Dirigido por evento) [M0]: CUANDO termina la ventana de escucha de un cobro, EL SISTEMA cerrará su canal de avisos.
- **RF-043** (No deseado) [M0]: SI la pantalla abre el canal de un cobro cuya ventana de escucha ya terminó, ENTONCES EL SISTEMA emitirá su estado actual y cerrará el canal de inmediato.
- **RF-033** (Estado) [M0]: MIENTRAS el canal de avisos está abierto, EL SISTEMA enviará una señal de vida al menos cada 15 segundos.

**Proteger la demo**

- **RF-034** (No deseado) [M0]: SI una misma IP del cliente pide más cobros de los permitidos en un minuto (10 por defecto, configurable), ENTONCES EL SISTEMA rechazará el exceso con un mensaje de "espera un minuto" sin pedirle nada a pey.
- **RF-041** (No deseado) [M0]: SI una misma IP del cliente intenta tener abiertos más de 10 canales de avisos a la vez, ENTONCES EL SISTEMA rechazará el siguiente con un mensaje de "cierra otras pantallas".
- **RF-035** (Ubicuo) [M0]: EL SISTEMA aceptará peticiones desde el navegador solo cuando vengan de los dominios configurados de la web de PAGO FÁCIL.
- **RF-036** (Ubicuo) [M0]: EL SISTEMA nunca incluirá la llave de pey ni el secreto del aviso en sus respuestas, mensajes de error o registros.
- **RF-037** (No deseado) [M0]: SI el secreto del aviso de pey no está configurado, ENTONCES EL SISTEMA rechazará todo aviso de pago sin procesarlo.

**Operar**

- **RF-038** (Dirigido por evento) [M0]: CUANDO se consulta la salud del servidor, EL SISTEMA indicará que responde y si la llave de pey y el secreto del aviso están configurados, sin mostrar sus valores.
- **RF-039** (Ubicuo) [M0; cancelación en C2]: EL SISTEMA dejará un registro, visible al correr el servidor, de cada cobro creado o cancelado, cada error de pey con su identificador de solicitud, cada pago registrado y cada aviso ignorado o rechazado.

> Los RF-040 a RF-043 salieron de la QA (QA-2, QA-7, QA-8 y QA-5) y se colocaron en su grupo para leerlos junto a los requisitos con los que se relacionan.

### 3.2 Entidades clave

- **Cobro**: lo que el negocio pide. Monto pedido (o monto libre), concepto, referencia numérica, identificador CoDi, contenido e imagen del QR, estado (*pendiente*, *pagado*, *vencido*, *cancelado*), hora de creación, hora de vencimiento y fin de la ventana de escucha. Tiene cero o más pagos.
- **Pago**: una transacción pagada que pey confirma para el QR de un cobro. Identificador de transacción (único), número dentro del cobro, monto recibido, monto base (cuando pey lo reporta) y hora de pago.

---

## 4. Casos límite y manejo de errores

| Caso | Comportamiento esperado | Requisitos |
|---|---|---|
| QR vencido sin pago | A los 10 minutos el cobro pasa a *vencido* y el canal lo avisa en menos de 15 s. Desde el corte 2, el canal sigue abierto 10 minutos más por si llega un pago tardío. | RF-021, RF-030, RF-022 |
| **Pago tardío** (hasta 10 minutos después de vencer) | Desde el corte 2, pasa a *pagado* y se avisa por el canal, igual que un pago a tiempo (principio VIII). En el corte M0, si llega por el aviso de pey, pasa a *pagado* pero el canal ya está cerrado. | RF-017, RF-022 |
| Pago después de la ventana de escucha | Si llega por el aviso de pey, se registra en el cobro y queda en el registro, pero el canal ya está cerrado y la consulta de respaldo ya no pregunta a pey. | RF-012, RF-025, RF-032 |
| Abrir el canal después de la ventana de escucha | Emite el estado actual y se cierra de inmediato. | RF-043 |
| **QR reutilizado** (varios pagos al mismo QR) | Cada transacción pagada distinta es un pago nuevo: se registra, se numera y se avisa, sin límite (desde el corte M0, C-1). | RF-015, RF-016, RF-029 |
| **Monto distinto** en un cobro de monto fijo | Con monto fijo el banco cobra exactamente lo pedido, así que no debería ocurrir. Se compara el monto base (o el recibido, si pey no da el desglose); si difiere, se registra, el aviso muestra ambos montos y queda una advertencia. Una propina o comisión reportada en el desglose no cuenta como monto distinto. | RF-018, RF-019, RF-020 |
| Monto 0 o vacío | Desde el corte 2, crea un cobro de monto libre. En el corte M0, se rechaza como monto no válido. | RF-003, RF-004 |
| Cobro de monto libre | No hay monto pedido: el aviso muestra lo que el cliente pagó. No aplica "monto distinto". | RF-003, RF-029 |
| Concepto con caracteres no imprimibles | Se rechaza con un mensaje para el dueño, sin pedirle nada a pey. | RF-042 |
| Pago a un cobro *cancelado* | El QR sigue pagable porque pey no permite anularlo. El cobro pasa a *pagado* y se avisa. | RF-017, RF-022 |
| Cancelar un cobro que no está *pendiente* | Se rechaza con un mensaje para el dueño. | RF-024 |
| **Falla de pey** al crear el cobro | Mensaje para el dueño según la causa; el cobro no se guarda. | RF-009, RF-010 |
| **Falla del aviso de pey** (no llega) | Con el canal abierto, el servidor le pregunta a pey cada 5 s y avisa el pago; si la pantalla consulta el cobro, también pregunta. | RF-040, RF-025, RF-026 |
| pey no responde durante la consulta de respaldo | Se devuelve el último estado conocido y se vuelve a preguntar en la siguiente consulta. | RF-027 |
| Transacción que pey reporta como pendiente | No es un pago: no se registra ni se avisa hasta que pey la reporte como pagada. | RF-014, RF-026 |
| Aviso de pago de un cobro desconocido (por ejemplo, tras reiniciar el servidor) | Se le responde bien a pey para que no reintente y queda registro. | RF-039 |
| Aviso de otro tipo de evento | Se le responde bien a pey y se ignora. | RF-013 |
| Aviso reenviado o transacción repetida | Se responde bien; el pago no se registra dos veces. | RF-014 |
| Secreto del aviso sin configurar | Todo aviso se rechaza sin procesarlo; el respaldo sigue detectando pagos. | RF-037, RF-040 |
| Llave de pey sin configurar | Crear cobro responde "falta configuración". | RF-010 |
| Muchos visitantes detrás del mismo proxy del hosting | Cada IP del cliente tiene su propio límite. | RF-034 |
| Una IP abre más de 10 canales | El siguiente canal se rechaza con "cierra otras pantallas". | RF-041 |
| Reinicio del servidor | Se pierden los cobros guardados. Limitación aceptada hasta #23. | — |
| **Devolución** (incluido un pago repetido por error) | Fuera de alcance: pey no ofrece devoluciones por API; el negocio la hace desde su banco. | — |

---

## 5. Fuera de alcance *(obligatorio)*

| Fuera de alcance | Dónde se resuelve |
|---|---|
| La pantalla del negocio (monto, QR grande, sonido, contador "pago n"). La pantalla podrá escuchar varios cobros a la vez para enterarse de pagos tardíos o de cobros cancelados. | #64 (spec propia de la web) |
| Despliegue con HTTPS y alta del aviso en el portal de pey | #65 |
| QR permanente o con vigencia elegida por el dueño (por ejemplo, impreso en el mostrador) | Issue por crear |
| Registro e inicio de sesión de negocios: hay un solo negocio de demo | #24 |
| Base de datos: los cobros se pierden al reiniciar | #19, #23 |
| Cuenta bancaria propia por negocio | Issue por crear |
| Enlaces de pago y cobro por notificación push CoDi | #36 |
| Historial y corte del día | #38 |
| Cupones | #37 |
| Bot de WhatsApp | #46–#48 |
| Devoluciones automáticas | No hay endpoint de pey; se hacen a mano desde el banco |

---

## 6. Criterios de éxito *(obligatorio)*

- **CE-001** [M0]: desde la URL pública, un cobro real de $0.01 se crea, se paga desde la app de un banco y el canal de avisos recibe el pago, de punta a punta.
- **CE-002** [M0]: el QR está listo para mostrarse en menos de 3 segundos después de pedirlo, con pey funcionando normal.
- **CE-003** [M0]: el canal de avisos recibe cada pago en menos de 2 segundos después de que pey entrega su aviso.
- **CE-004** [M0]: el 100 % de los avisos de pago sin firma válida se rechazan sin cambiar ningún cobro, comprobado con pruebas automáticas.
- **CE-005** [M0]: ninguna transacción se registra dos veces, comprobado con pruebas automáticas de reenvío del aviso y de consulta de respaldo.
- **CE-006** [M0]: dos transacciones distintas al mismo QR producen dos avisos con números de pago 1 y 2 y el total correcto, comprobado con pruebas automáticas.
- **CE-007** [C2]: un pago que llega 5 minutos después del vencimiento se avisa por el canal, comprobado con pruebas automáticas con reloj controlado.
- **CE-008** [M0]: sin aviso de pey y con el canal abierto, un pago se avisa a más tardar 5 segundos después de que pey lo reporta en su consulta, sin que la pantalla consulte nada, comprobado con pruebas automáticas con reloj controlado.
- **CE-009** [M0]: ningún archivo del repositorio, respuesta ni registro contiene la llave de pey o el secreto del aviso.
- **CE-010** [M0]: el servidor responde a cada aviso de pey en menos de 1 segundo, comprobado con pruebas automáticas.

---

## 7. Supuestos y dependencias

**Supuestos**

- pey firma sus avisos con Standard Webhooks y manda uno por llave de API (documentación de pey, revisada el 14 nov).
- El aviso de QR pagado trae el identificador CoDi, el identificador de transacción, el monto recibido y la hora de pago, pero no el desglose en base, propina y comisión; ese desglose solo viene en la consulta de transacciones (documentación de pey).
- Con monto fijo, el banco del cliente cobra exactamente el monto del QR; con monto 0, el cliente escribe la cantidad (documentación de pey, campo `amount`).
- Un mismo QR puede recibir pagos sin límite (lo confirmó el equipo de pey a Hugo, 14 nov).
- pey no ofrece operaciones para cancelar un QR ni para devolver un pago (lista de endpoints de pey, revisada el 14 nov).
- La cámara normal del teléfono no paga un QR CoDi: el cliente usa la opción CoDi de la app de su banco (comprobado por Hugo el 14 nov).
- pey solo tiene ambiente de producción; las pruebas reales son de $0.01 con autorización de Hugo.
- Un solo servidor atiende la demo; no hay varias copias corriendo a la vez.
- Cualquiera que conozca el identificador de un cobro puede verlo o cancelarlo. Se acepta en el MVP porque no hay cuentas (#24) y los identificadores no se pueden adivinar.
- El máximo de $100 por cobro, la vigencia de 10 minutos y el límite de 10 cobros por minuto por IP vienen del issue #62 y del prototipo, y no se preguntaron por tener una respuesta obvia.

**Dependencias externas**

| Dependencia | Qué bloquea | Dueño | Estado (14 nov) |
|---|---|---|---|
| CoDi activado en el banco con que se prueba | La prueba de pago real (CE-001) | Hugo | Se activa el 15 nov |
| Hosting con HTTPS y URL pública | CE-001 y el aviso de pey | Altairtm (#65) | Pendiente |
| Aviso (webhook) dado de alta en el portal de pey, con su secreto en el hosting | El aviso de pey (RF-011, RF-012); sin él, solo funciona el respaldo | Altairtm (#65), con Hugo | Pendiente: el secreto está vacío |
| Pantalla del negocio | La reacción visible y sonora que piden las reglas | #64 | Pendiente |

---

## 8. Dudas y decisiones

### 8.1 Entrevista con Hugo (2026-11-14)

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| E-1 | ¿Qué pasa si el cliente paga un monto distinto al pedido? | Hugo pidió revisar cómo funciona CoDi: con monto fijo el banco cobra exactamente lo pedido. Se queda como caso **defensivo y visible**: si pey reporta otra cantidad, se registra el monto recibido, el cobro y el aviso muestran ambos montos y queda una advertencia. | RF-018, RF-019, RF-020 |
| E-2 | ¿Cómo se entera el dueño de un pago que llega justo al vencer el QR? | ***Vencido* no es final.** El canal sigue abierto y la consulta de respaldo sigue preguntando a pey durante 10 minutos después del vencimiento; si llega un pago, pasa a *pagado* y se avisa. | RF-021, RF-022, RF-025, RF-032 |
| E-3 | ¿Qué pasa si un cobro ya pagado recibe otro pago real (otra transacción)? | El dueño puede **reutilizar el QR a propósito**. Cada pago distinto suena y avisa, con su número de pago dentro de la misma operación. | RF-015, RF-016, RF-029 |
| E-4 | ¿Cómo se muestra el contador y qué pasa después de 20 pagos? | Según el equipo de pey, un QR se puede pagar **sin límite**. El contador es "pago n", sin tope; el 20 era solo el tamaño de página de la consulta de pey. | RF-015, RF-016 |
| E-5 | ¿Cuánto dura un QR que se reutiliza? | **10 minutos fijos** en el MVP, más los 10 de gracia de E-2. Un QR permanente queda como issue nuevo. | RF-006, RF-021 |
| E-6 | ¿Entra el monto libre (el cliente escribe la cantidad)? | **Dentro del MVP.** El negocio puede dejar el monto vacío y el aviso muestra lo que pagó el cliente. | RF-003, RF-008, RF-029 |
| E-7 | ¿El dueño puede cancelar un cobro pendiente? | **Sí, cancelación local.** El cobro pasa a *cancelado*, pero el QR sigue pagable en el banco (pey no permite anularlo); un pago posterior se registra y avisa igual. | RF-023, RF-024, RF-017 |

**Consecuencias aplicadas sin pregunta aparte** (salen directo de E-2, E-3 y E-7; la QA las puede cuestionar):

- El canal de avisos ya no se cierra al primer pago ni al vencer: se cierra al terminar la ventana de escucha (RF-032).
- La consulta de respaldo pregunta a pey en cualquier estado mientras dure la ventana de escucha, no solo en *pendiente* (RF-025).
- Solo se puede cancelar un cobro *pendiente* (RF-024).
- El máximo de $100 aplica solo al monto fijo; en monto libre, el cliente decide cuánto paga (RF-002, RF-003).

### 8.2 Cambios a otras specs

No hay specs previas. Cambios a **esta** spec después de aprobada:

| # | Cambio | Por qué | Afecta | Estado |
|---|---|---|---|---|
| C-1 | El QR reutilizado (varios pagos numerados) y el monto distinto visible pasan del corte 2 al corte M0. Se quitan de §1.2 los puntos temporales "solo el primer pago se registra y se avisa" y "el cobro todavía no muestra ambos montos". | QT-3 de `tasks.md`: con la regla temporal, el segundo pago a un QR no se avisaba, en choque con el principio VIII ("se registra… y se avisa"). Hugo prefirió adelantar el QR reutilizado a registrar una excepción temporal. | §1.2, historia 2 (escenarios 2 y 6), RF-015, RF-016, RF-019, RF-020, §4 (QR reutilizado y monto distinto), CE-006; QA-1 queda modificada en ese punto | Aprobado y aplicado por Hugo el 2026-11-14 |
| C-2 | RF-008 agrega "la hora actual del servidor" a cada cobro que se devuelve (crear, ver y cancelar) y a los eventos del canal de avisos. | QA-2 de la spec 002: `creado_en` se fija antes de pedirle el QR a pey (`main.py:181-185`), y sin la hora del servidor la pantalla no puede mostrar la cuenta regresiva con 2 s de error si el reloj del celular está desfasado (spec 002, RF-019). | RF-008, `contracts/crear-cobro.md` (objeto cobro), `contracts/canal-avisos.md`, pruebas del objeto cobro | Aprobado por Hugo el 2026-11-15 y aplicado el mismo día (campo `hora_servidor`; plan TK-6, tasks F9) |

### 8.3 Propuestas

| # | Propuesta | Por qué | Decisión |
|---|---|---|---|
| P-1 | Usar el prototipo actual como punto de partida de la implementación, ajustándolo con pruebas primero | Ya cumple parte de los RF y tiene 15 pruebas; rehacerlo pone en riesgo la entrega del domingo. Las decisiones E-2, E-3, E-6 y E-7 lo cambian bastante (varios pagos por cobro, ventana de escucha, monto libre, cancelación). | Pendiente (se decide en el plan) |

### 8.4 Revisión QA (2026-11-14, una sola pasada)

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QA-1 | Promesa imposible | Con E-2, E-3, E-6 y E-7 el alcance creció, pero la entrega del kickoff es el 15 nov a la 1:00 PM y todavía faltan el plan, las tasks, sus QA, la web (#64) y el despliegue (#65). El prototipo cubre el cobro de monto fijo con un solo pago; no cubre pagos repetidos, la ventana de gracia, el monto libre ni la cancelación (`cobros.py:97`, `main.py:29`, `main.py:178`). | Todos | Entregar en dos cortes. **Corte M0** (domingo): historias 1 (monto fijo), 2 (escenarios 1, 3, 4 y 5), 3 (escenarios 1 y 2), 5 y 6. **Corte 2** (antes de M2, 21 nov): QR reutilizado, monto distinto visible, ventana de gracia, monto libre y cancelación. Cada RF se marca con su corte. | **Dos cortes** (Hugo, 14 nov), como se recomienda. Aplicada. |
| QA-2 | Hueco | La consulta de respaldo solo ocurre "cuando se consulte el cobro" (RF-025). Si la pantalla solo escucha el canal de avisos y el aviso de pey no llega (por ejemplo, sin el secreto configurado: hoy `PEY_WEBHOOK_SECRET` está vacío), nadie le pregunta a pey y el pago nunca se avisa. La historia 3 depende de que la web consulte por su cuenta. | RF-025, RF-026, CE-008 | Nuevo RF: MIENTRAS un cobro tenga al menos un canal de avisos abierto dentro de su ventana de escucha, EL SISTEMA le preguntará a pey por sus pagos cada 5 segundos, sin esperar a que la pantalla consulte. | **El servidor pregunta solo**, cada 5 s mientras haya un canal abierto. Va en el corte M0. Aplicada. |
| QA-3 | Ambigüedad | RF-002 rechaza el monto 0 por no ser "mayor a 0", y RF-003 crea un cobro de monto libre "sin monto". No se dice qué pasa si el negocio manda 0 a propósito: ¿error o monto libre? Para pey, `amount: 0` es monto libre (openapi, `POST /codi/qr`). | RF-002, RF-003, RF-004 | Solo el monto vacío crea un cobro de monto libre. Un 0 escrito se rechaza como monto no válido, para que un error de dedo no cree un QR donde el cliente paga lo que quiera. | **0 es monto libre**: escribir 0 o dejar el monto vacío crea un cobro de monto libre, igual que en pey. Se aparta de la recomendación. Aplicada. |
| QA-4 | API de pey | El `amount` de las transacciones de pey es el **total**, con un desglose `base`, `tip` (propina) y `fee` (comisión cobrada al pagador). El aviso de pey solo trae `amount`, "the amount received". Si un banco agrega propina o comisión, RF-019 marcaría "monto distinto" en un pago correcto. | RF-018, RF-019, RF-020 | Para detectar el monto distinto se compara la parte base del pago cuando pey la reporte, y el total cuando no. Se muestra siempre el total recibido. Se agrega la pregunta a pey de si un QR CoDi puede traer propina o comisión. | **Comparar la base cuando exista**, y si no, el total. Se agrega la pregunta a pey. Aplicada. |
| QA-5 | Ambigüedad | (a) RF-030 no dice cuánto puede tardar en emitirse *vencido*; el prototipo lo emite en el siguiente latido, hasta 15 s tarde (`main.py:171-174`). (b) No se dice qué pasa si la pantalla abre el canal de un cobro cuya ventana de escucha ya terminó. | RF-030, RF-031, RF-032 | (a) *Vencido* y *cancelado* se emiten en menos de 15 segundos. (b) Abrir el canal después de la ventana emite el estado actual y cierra el canal de inmediato. | **Menos de 15 s y cierre**, como se recomienda. Aplicada. |
| QA-6 | Seguridad | El límite por IP (RF-034) usa la IP de la conexión (`main.py:118`). En un hosting con proxy (Render o Railway, #65), todas las peticiones llegan con la IP del proxy: el límite pasaría a ser de 10 cobros por minuto **para todos** los visitantes de la demo. | RF-034 | RF-034 dice "la IP del cliente, no la del proxy del hosting". La forma de obtenerla queda como decisión del plan. | **IP real del cliente**. La forma de obtenerla es una decisión del plan. Va en el corte M0. Aplicada. |
| QA-7 | Seguridad | Nada limita cuántos canales de avisos abre una IP. Con QA-2, cada canal abierto genera consultas a pey. Una IP con 10 cobros por minuto y ventanas de 20 minutos puede tener unos 200 cobros vivos y saturar el límite de peticiones de la llave (desconocido, §8.5), lo que afectaría la demo real. | RF-025, RF-034 | Nuevo RF: SI una misma IP tiene abiertos más de 10 canales de avisos, ENTONCES EL SISTEMA rechazará el siguiente con un mensaje de "cierra otras pantallas". | **Máximo 10 canales por IP**. Va en el corte M0. Aplicada. |
| QA-8 | Hueco | RF-005 no dice qué pasa con caracteres no imprimibles en el concepto. El prototipo los rechaza (`main.py:36-37`). Tampoco se sabe si pey o los bancos aceptan emojis en el concepto. | RF-005 | RF-005 acepta solo caracteres imprimibles. Nuevo RF: SI el concepto tiene caracteres no válidos, ENTONCES EL SISTEMA rechazará el cobro con un mensaje para el dueño. Lo de los emojis se agrega a las preguntas para pey. | **Rechazar con mensaje**. Se agrega la pregunta de los emojis a pey. Aplicada. |
| QA-9 | Hueco | El issue #63 pide "responder 200 rápido a pey", pero no hay RF ni CE con un tiempo. Si la respuesta tarda, pey puede reintentar o dar el aviso por fallido (sus reintentos son desconocidos, §8.5). | RF-012, CE-003 | Nuevo CE: el servidor responde a cada aviso de pey en menos de 1 segundo, comprobado con pruebas automáticas. | **Nuevo CE: respuesta a pey en menos de 1 s.** Aplicada. |
| QA-10 | Contradicción | El prototipo hace siete cosas distintas a la spec: (1) un solo pago por cobro (`cobros.py:97`); (2) cierra el canal al primer pago (`main.py:178`) y al vencer (`main.py:172-174`); (3) el respaldo solo corre en *pendiente* (`main.py:148`), se detiene en la primera transacción (`main.py:104`) y no pide las páginas siguientes; (4) no acepta monto libre (`main.py:29`); (5) no tiene cancelación; (6) la respuesta no trae monto recibido, número de pagos ni total (`cobros.py:38-51`); (7) los registros *info* no se ven (no hay configuración de logs). Además, marca el `webhook-id` como visto **antes** de procesarlo (`main.py:210`), así que si el procesamiento falla, el reintento de pey se ignora. | RF-008, RF-015, RF-016, RF-003, RF-023, RF-025, RF-032, RF-039, RF-014 | Manda la spec: el código se ajusta en la implementación, con pruebas primero (decisión P-1 en el plan). No se cambia ningún RF por el prototipo. | **Manda la spec.** El código se ajusta en la implementación; P-1 se decide en el plan. Aplicada. |

**Bloques de la pasada:**

1. **Coherencia interna**: glosario, RF, casos límite y CE coherentes entre sí; RF-001 a RF-039, CE-001 a CE-009, E-1 a E-7 y P-1 existen y no faltan números; no hay `C-n` (es la primera spec). Salen QA-3 y QA-5, más las erratas 1 y 3.
2. **Otras specs, plan del hackathon, reglas e issues**: no hay otras specs. Cumple el cobro real, la reacción, producción, la API key fuera del cliente y no revender el API. Revisados los issues #18, #62, #63 y #65: del #63 sale QA-9. El plan del hackathon pide "QR + webhook + sonido" en M0, que es el corte M0 de QA-1.
3. **Código (solo lectura)**: 15 pruebas en verde (`uv run --directory backend pytest -q`). Las diferencias están en QA-10; la IP de la conexión en QA-6.
4. **API de pey** (`openapi.json`, páginas de webhooks y lista de endpoints): `expiration` es 0 o al menos 360 (10 min cumple); `numRef` tiene hasta 7 dígitos; `amount: 0` es monto libre; el `transactionId` del aviso es un ULID, igual que el `id` de las transacciones; hay transacciones *PENDING* y *PAID*; la consulta devuelve 20 por página con `nextToken`; no hay endpoints para cancelar ni devolver. Salen QA-3, QA-4 y la errata 2.
5. **Dependencias externas**: CoDi activo en el banco de Hugo (15 nov), secreto del aviso vacío en `backend/.env`, hosting con HTTPS (#65) y pantalla (#64) sin dueño en la spec. Sale la errata 4; la falla del aviso se cubre con QA-2.
6. **Casos límite**: pago tardío, monto distinto, pago repetido, QR reutilizado, aviso desconocido o reenviado, QR vencido, cancelación, devoluciones y reinicio, todos con su fila en §4. Pantallas: no aplica, son de la spec de la web (#64).
7. **Seguridad y rendimiento**: `backend/.env` está ignorado por git; no hay llaves en los archivos del repositorio (la única coincidencia está en `.claude/settings.local.json`, que está fuera de git, y es un patrón de búsqueda, no una llave); firma Standard Webhooks con 5 minutos de tolerancia (`standardwebhooks`); deduplicación por transacción. Salen QA-6, QA-7, QA-8 y QA-9.
8. **Construibilidad y reparto**: el riesgo de fecha está en QA-1. El reparto (Profesor en #62 y #63, Altairtm en #65) va en el plan.

**Erratas** (sin efecto en el comportamiento; corregidas al aprobar, el 2026-11-14):

1. *(Corregida, también en RF-014)* RF-015 y RF-026 decían "transacción", y ahora dicen "transacción **pagada**", como define el glosario (pey también reporta transacciones *PENDING*).
2. *(Queda para el plan)* Nota para el plan, no para la spec: la consulta de respaldo tiene que recorrer todas las páginas de transacciones (20 por página), porque un QR no tiene límite de pagos (E-4).
3. RF-029 no incluye la hora del pago en el aviso, aunque RF-008 sí la devuelve en el cobro: agregada.
4. §7 debe listar las dependencias externas con su dueño y su estado: CoDi activo (Hugo, 15 nov), secreto del aviso en el portal de pey y hosting con HTTPS (#65, Altairtm), pantalla del negocio (#64). Agregadas en §7.

### 8.5 Pendientes

- No quedan marcas `[NECESITA ACLARACIÓN]`.
- Preguntas para pey en el kickoff, que no bloquean la spec:
  - ¿Cuántas veces y durante cuánto tiempo reintenta un aviso que falla, y qué respuesta considera exitosa?
  - ¿Banxico deja pagar un QR después de su vencimiento? Si no, la ventana de gracia de E-2 solo cubre los pagos en curso al vencer.
  - ¿Qué límite de peticiones tiene la llave de API? Puede obligar a bajar RF-025, RF-040, RF-034 o RF-041.
  - ¿Con qué bancos se ha probado el pago de sus QR?
  - ¿Un pago a un QR CoDi puede traer propina o comisión al pagador (`tip` y `fee` del desglose)? (QA-4)
  - ¿pey y los bancos aceptan emojis y acentos en el concepto del QR? (QA-8)

---

## 9. Criterios de finalización

- [ ] Cada RF tiene al menos una prueba automática o un paso de verificación manual.
- [ ] Todos los criterios de éxito (CE) están comprobados.
- [ ] No quedan marcas `[NECESITA ACLARACIÓN]` abiertas.
- [ ] Hay una revisión de seguridad hecha: secretos, firma de webhooks y validación de entradas.
