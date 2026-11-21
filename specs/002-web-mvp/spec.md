# Spec 002: Web del MVP: cobrar con el teclado y oír que me pagaron

- **ID**: `002-web-mvp`
- **Fecha**: `2026-11-15`
- **Estado**: `Aprobada`. Hugo la aprobó el 2026-11-15, después de la entrevista (E-1 a E-10) y de la QA (QA-1 a QA-10 y sus 6 erratas, todas aplicadas). Se entrega en dos cortes (§1.2). Depende del cambio C-2 a la spec 001 (§8.2), aplicado el 2026-11-15 con el campo `hora_servidor`. El cambio C-3 (imagen del QR vacía) salió del plan y se aprobó y aplicó el 2026-11-15.
- **Rama**: `feature/64-web-mvp` (propuesta; la crea Hugo)
- **Issues**: #64 (página de cobro del MVP). Es la versión mínima de #31 (pantalla de cobro) y #32 (aviso de pago con sonido).
- **Entrada**: "Iniciemos la redaccion de la spec 002. En este caso ademas de lo que tienes tienes del proyecto, vamos a intridcir el backend que permita introducir la funcinalidad en la pantalla de mostrar un teclado numerico que permita introducir el onto de cobro y asi generar el QR."

> **Notas para los comandos de spec-kit.**
> - `RF-###` equivale a *Functional Requirement* (FR-###).
> - `CE-###` equivale a *Success Criterion* (SC-###).
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
>
> La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas de datos, los algoritmos y las firmas de funciones: eso va en `plan.md` y `tasks.md`. Toda la spec se escribe en español.

---

## 1. Contexto y propósito (por qué)

La spec 001 dejó listo el **servidor**: crea cobros CoDi reales con pey, confirma cada pago y lo avisa por un canal en tiempo real. Pero el dueño de la tiendita no habla con un servidor: necesita una pantalla en su celular donde teclear el monto, enseñar el QR al cliente y **oír** que le pagaron.

Esta spec cubre esa pantalla. Es la "app en vivo" que piden las reglas del hackathon y el momento que más pesa en la evaluación: 30 % es el uso de CoDi y de pey, con reacción visible y sonora, y 15 % es la experiencia del "momento del pago". Con ella se cierra el recorrido completo: **monto → QR → pago desde el banco → sonido y "Pago recibido"**.

La pantalla usa el servidor de la spec 001 **tal como está aprobado**. Si la QA o el plan descubren que el servidor necesita algo más, se propone como cambio `C-n` a la spec 001 (§8.2) y no se construye hasta que Hugo lo apruebe.

### 1.1 Glosario

Los términos *cobro*, *pago*, *monto fijo*, *monto libre*, *vigencia*, *ventana de escucha*, *canal de avisos*, *consulta de respaldo* y los estados del cobro (*pendiente*, *pagado*, *vencido*, *cancelado*) significan lo mismo que en la [spec 001](../001-backend-mvp/spec.md#11-glosario).

| Término | Significado en esta spec |
|---|---|
| Pantalla | La página web que el dueño abre en el navegador de su celular. Es lo que construye esta spec. |
| Servidor | El backend de PAGO FÁCIL de la spec 001. Es el único que habla con pey. |
| Dueño | Quien cobra con la pantalla. En el MVP hay un solo negocio de demo, sin cuenta ni inicio de sesión. |
| Cliente | Quien paga, desde la app de su banco en la opción CoDi. |
| Teclado | Los botones numéricos grandes de la pantalla para escribir el monto, sin abrir el teclado del sistema del celular. |
| Vista | Cada momento de la pantalla: **Teclado**, **Generando QR**, **QR**, **QR vencido**, **Pago recibido** y **Error**. Los errores al crear un cobro se muestran en la vista Teclado; la vista Error es solo para un cobro que el servidor ya no conoce (RF-057). |
| Cobro en pantalla | El cobro que la pantalla está mostrando en las vistas QR, QR vencido o Pago recibido. |
| Cobro anterior | Un cobro que el dueño dejó con Nuevo cobro o con Cancelar cobro (o que se canceló desde otra pantalla), y cuya ventana de escucha todavía no termina (corte 2). |
| Cobro en escucha | Un cobro del que la pantalla recibe avisos: el cobro en pantalla y, desde el corte 2, los cobros anteriores. |
| Aviso de pago | Lo que la pantalla recibe del servidor cuando se registra un pago, por el canal de avisos o por la consulta del estado. |
| Consulta del estado | Cuando la pantalla le pregunta al servidor cómo está un cobro, porque el canal de avisos se cortó. |
| Pago avisado | Un pago que la pantalla ya mostró como recibido, con o sin sonido. |

### 1.2 Cortes de entrega (E-2)

La spec se aprueba completa, pero se construye en dos cortes. Cada historia, escenario, RF y CE lleva el suyo. El formulario del kickoff (15 nov, 1:00 PM) se envía sin la pantalla de esta spec (QA-1).

| Corte | Fecha | Qué entrega |
|---|---|---|
| **Corte 1** | Antes del 20 nov (fin de M1, QA-1) | Teclado con monto fijo, QR con cuenta regresiva, sonido y "Pago recibido" (también para un segundo pago al mismo QR y con monto distinto visible), respaldo cuando se corta el canal, QR vencido con pagos tardíos (QA-4), Nuevo cobro y pantalla encendida mientras hay un cobro en escucha. Requiere el C-2 aplicado en la spec 001. |
| **Corte 2** | Antes del 21 nov (inicio de M2) | Monto libre, número de pago y total ("Pago 2"), volver a mostrar el QR después de un pago (QA-9), escuchar los cobros anteriores, cancelar un cobro y recuperar los cobros al recargar la página. |

**Comportamiento temporal del corte 1**, mientras no llega el corte 2. Cada punto deja de valer al entregar el corte 2:

- No hay tecla Monto libre: Cobrar sigue desactivado sin monto.
- Un segundo pago al mismo QR suena y muestra "Pago recibido" con su monto, sin el número de pago ni el total, y no hay botón para volver a mostrar el QR.
- Nuevo cobro deja de escuchar el cobro que estaba en pantalla.
- No hay botón Cancelar cobro.
- Recargar la página vuelve a la vista Teclado vacía y los cobros dejan de escucharse.

---

## 2. Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Teclear el monto y generar el QR (Prioridad: P1) · Corte 1 (monto libre: corte 2)

**Como** dueño de una tiendita, **quiero** escribir el monto con un teclado grande y pulsar Cobrar, **para** tener el QR listo en segundos sin pelearme con el celular.

**Por qué esta prioridad:** sin QR no hay cobro. Es el primer paso del recorrido que exigen las reglas.

**Prueba independiente:** abrir la pantalla en un celular, teclear 0.01, escribir "Tacos", pulsar Cobrar y ver el QR con "$0.01" y "Tacos"; escanearlo desde la app de un banco con CoDi y ver el mismo monto y concepto.

**Escenarios de aceptación:**

1. *(C1)* **Dado** la vista Teclado vacía, **cuando** el dueño pulsa 2, 5, punto, 5 y 0, **entonces** la pantalla muestra "$25.50" en grande.
2. *(C1)* **Dado** el monto "$25.50", **cuando** el dueño intenta escribir otro dígito, **entonces** la tecla se ignora y el monto sigue en "$25.50".
3. *(C1)* **Dado** el monto "$25.5", **cuando** el dueño pulsa borrar, **entonces** el monto queda en "$25.".
4. *(C1)* **Dado** el monto vacío o en 0, **cuando** el dueño mira la vista Teclado, **entonces** el botón Cobrar está desactivado.
5. *(C1)* **Dado** un monto válido, **cuando** el dueño pulsa Cobrar, **entonces** la pantalla muestra al instante que está generando el QR, y un segundo toque a Cobrar no crea otro cobro.
6. *(C1)* **Dado** que el servidor rechaza el cobro (por ejemplo, "El monto máximo de la demo es $100"), **cuando** responde, **entonces** la pantalla muestra ese mensaje y conserva el monto y el concepto escritos para corregirlos.
7. *(C1)* **Dado** que el celular no tiene internet, **cuando** el dueño pulsa Cobrar, **entonces** ve un mensaje que le pide revisar su conexión, y el monto sigue escrito.
12. *(C1)* **Dado** que el servidor crea el cobro pero lo devuelve sin imagen del QR, **cuando** responde, **entonces** vuelve la vista Teclado con "No se pudo mostrar el QR. Intenta de nuevo." y el monto y el concepto siguen escritos (C-3).
8. *(C2)* **Dado** la vista Teclado con el monto vacío y el concepto "Propina", **cuando** el dueño pulsa Monto libre, **entonces** se genera un QR que muestra "Monto libre" y "Propina", y al escanearlo el banco del cliente le pide escribir la cantidad.
9. *(C2)* **Dado** el monto "$25.50" escrito, **cuando** el dueño mira la vista Teclado, **entonces** la tecla Monto libre está desactivada.
10. *(C1)* **Dado** la vista Teclado vacía, **cuando** el dueño pulsa 0 y después 7, **entonces** el monto queda en "$7"; y si la primera tecla es el punto, queda en "$0.".
11. *(C1)* **Dado** el monto "$12345", **cuando** el dueño intenta escribir otro dígito entero, **entonces** la tecla se ignora.

---

### Historia 2 — Enseñar el QR al cliente (Prioridad: P1) · Corte 1

**Como** dueño, **quiero** un QR grande con el monto, el concepto y el tiempo que le queda, **para** que el cliente lo escanee sin dudas y yo sepa si todavía sirve.

**Por qué esta prioridad:** el QR es lo que el cliente ve. Si no se escanea bien o el cliente usa la cámara normal, no hay pago.

**Prueba independiente:** generar un cobro y comprobar, en un celular de 320 px de ancho, que el QR, el monto, el concepto, la cuenta regresiva y la indicación de CoDi se ven sin desplazarse hacia los lados.

**Escenarios de aceptación:**

1. **Dado** un cobro recién creado, **cuando** se muestra la vista QR, **entonces** se ven el QR en grande, el monto, el concepto, la indicación "Escanéalo desde la app de tu banco, en la opción CoDi" y una cuenta regresiva que empieza en 10:00.
2. **Dado** un celular cuyo reloj está adelantado 5 minutos, **cuando** se muestra la vista QR, **entonces** la cuenta regresiva empieza igual en 10:00 (con 2 segundos de margen).

---

### Historia 3 — Oír y ver que me pagaron (Prioridad: P1) · Corte 1 (número de pago y Mostrar QR otra vez: corte 2)

**Como** dueño, **quiero** que el celular suene y se ponga en verde con "Pago recibido" en cuanto el cliente pague, **para** entregar el producto sin revisar capturas ni la app de mi banco.

**Por qué esta prioridad:** es la "reacción visible al resultado" que exigen las reglas y el momento central de la demo.

**Prueba independiente:** con la vista QR abierta, un canal que entrega los eventos en vivo y el sonido habilitado, pagar $0.01 desde la app del banco. El celular suena y muestra "Pago recibido" con el monto y el concepto en menos de 2 segundos después de que el servidor emite el aviso.

**Escenarios de aceptación:**

1. *(C1)* **Dado** la vista QR abierta y sin tocar la pantalla después de pulsar Cobrar, **cuando** el servidor avisa un pago, **entonces** suena el sonido de pago recibido y la pantalla completa se pone verde con "Pago recibido", el monto recibido y el concepto.
2. *(C1)* **Dado** un celular que puede vibrar, **cuando** llega el aviso de pago, **entonces** además vibra.
3. *(C1)* **Dado** la vista Pago recibido, **cuando** pasan varios minutos sin que el dueño toque nada, **entonces** la vista sigue igual hasta que pulse Nuevo cobro (o, desde el corte 2, Mostrar QR otra vez).
4. *(C1)* **Dado** la vista Pago recibido de un cobro cuyo QR se vuelve a pagar, **cuando** el servidor avisa el segundo pago, **entonces** vuelve a sonar y muestra el monto de ese pago.
5. *(C2)* **Dado** el mismo caso, **cuando** el servidor avisa el segundo pago, **entonces** la vista muestra además "Pago 2" y el total recibido.
6. *(C1)* **Dado** un cobro de monto fijo de $25.50, **cuando** el servidor avisa un pago de $20.00, **entonces** la vista Pago recibido muestra el monto pedido y el monto recibido, para que el dueño note la diferencia.
7. *(C1)* **Dado** un pago ya avisado, **cuando** la pantalla vuelve a recibir ese mismo pago (al reconectarse o al consultar el estado), **entonces** no vuelve a sonar ni a mostrarlo como nuevo.
8. *(C1)* **Dado** un cobro en escucha y un navegador que permite mantener la pantalla encendida, **cuando** el dueño no toca el celular durante 10 minutos, **entonces** la pantalla no se apaga.
9. *(C2)* **Dado** la vista Pago recibido de un cobro cuyo QR sigue vigente, **cuando** el dueño pulsa Mostrar QR otra vez, **entonces** vuelve la vista QR del mismo cobro, con su cuenta regresiva, para que otro cliente lo escanee.

---

### Historia 4 — Recibir el pago si el canal se corta o queda mudo (Prioridad: P1) · Corte 1

**Como** dueño, **quiero** que la pantalla se entere del pago aunque el internet del celular falle un momento, **para** no quedarme con la duda frente al cliente.

**Por qué esta prioridad:** en un mostrador la señal del celular es inestable. Sin respaldo, un corte de unos segundos arruina el momento del pago.

**Prueba independiente:** con la vista QR abierta, cortar el canal de avisos (por ejemplo, activando y quitando el modo avión) y pagar; la pantalla avisa el pago en menos de 6 segundos después de que el servidor lo registra.

**Escenarios de aceptación:**

1. **Dado** la vista QR con el canal de avisos cortado, **cuando** el servidor registra un pago, **entonces** la pantalla lo descubre al consultar el estado del cobro (cada 3 segundos) y lo avisa igual: sonido y "Pago recibido".
2. **Dado** el canal cortado, **cuando** pasa el corte, **entonces** la pantalla vuelve a abrir el canal, quita «Reconectando…» y pasa a consultar cada 8 segundos.
3. **Dado** el canal cortado, **mientras** dura el corte, **entonces** la pantalla muestra un aviso discreto de "Reconectando…" sin quitar el QR.
4. **Dado** que el servidor rechaza el canal porque hay demasiadas pantallas abiertas, **cuando** ocurre, **entonces** la pantalla sigue enterándose de los pagos consultando el estado.
5. **Dado** un canal abierto cuyos eventos quedan retenidos en un proxy, **cuando** el servidor registra el pago, **entonces** la primera consulta que lo devuelve muestra «Pago recibido» y suena si el navegador permite la reproducción (C-4, C-5).

---

### Historia 5 — QR vencido y pagos tardíos (Prioridad: P2) · Corte 1

**Como** dueño, **quiero** saber cuándo el QR ya no sirve y que, aun así, me avise si el cliente alcanzó a pagar, **para** no cobrar dos veces ni perder un pago.

**Por qué esta prioridad:** pasa en el mostrador (el cliente tarda en abrir su banco), pero el cobro funciona sin esta historia.

**Prueba independiente:** con reloj controlado, dejar pasar los 10 minutos de vigencia y comprobar la vista QR vencido; después simular un pago 5 minutos tarde y comprobar que suena y se muestra "Pago recibido".

**Escenarios de aceptación:**

1. *(C1)* **Dado** un cobro sin pagos, **cuando** la cuenta regresiva llega a 0:00 o el servidor avisa que venció, **entonces** el QR desaparece y la pantalla muestra la vista QR vencido con el monto, el concepto y el botón Nuevo cobro.
2. *(C1)* **Dado** la vista QR vencido dentro de la ventana de escucha, **cuando** el dueño la mira, **entonces** ve el texto "Si el cliente ya pagó, aquí te avisamos".
3. *(C1)* **Dado** la vista QR vencido dentro de la ventana de escucha, **cuando** el servidor avisa un pago tardío, **entonces** suena y se muestra "Pago recibido" igual que un pago a tiempo.
4. *(C1)* **Dado** cualquier cobro en escucha, **cuando** termina su ventana de escucha, **entonces** la pantalla deja de escucharlo y no intenta reconectarse.

---

### Historia 6 — Empezar otro cobro sin perder los pagos del anterior (Prioridad: P2) · Corte 1 (cobros anteriores: corte 2)

**Como** dueño, **quiero** un botón Nuevo cobro y que la pantalla me siga avisando si alguien paga un QR anterior, **para** atender al siguiente cliente sin recargar la página y sin perder un pago tardío.

**Por qué esta prioridad:** sin Nuevo cobro el dueño tendría que recargar después de cada venta; el primer cobro funciona sin esta historia.

**Prueba independiente:** desde las vistas QR, QR vencido y Pago recibido, pulsar Nuevo cobro y comprobar que vuelve la vista Teclado vacía; después pagar el QR anterior y comprobar que suena y aparece su aviso.

**Escenarios de aceptación:**

1. *(C1)* **Dado** la vista Pago recibido, **cuando** el dueño pulsa Nuevo cobro, **entonces** vuelve a la vista Teclado con el monto y el concepto vacíos.
2. *(C2)* **Dado** un cobro de $30 "Refresco" que el dueño dejó con Nuevo cobro, **cuando** el cliente lo paga mientras el dueño teclea otro monto, **entonces** suena y aparece un aviso de pago de "Refresco" por $30, sin borrar el monto que se está tecleando.
3. *(C2)* **Dado** un cobro anterior, **cuando** termina su ventana de escucha, **entonces** la pantalla deja de escucharlo.

---

### Historia 7 — Cancelar un cobro equivocado (Prioridad: P2) · Corte 2

**Como** dueño, **quiero** cancelar un cobro que todavía no se paga, **para** quitarlo de la pantalla si me equivoqué de monto o el cliente se arrepintió.

**Por qué esta prioridad:** es un error común en el mostrador, pero Nuevo cobro ya permite seguir trabajando.

**Prueba independiente:** generar un cobro, pulsar Cancelar cobro y comprobar que vuelve la vista Teclado; después pagar ese QR desde el banco y comprobar que suena y aparece el aviso.

**Escenarios de aceptación:**

1. **Dado** la vista QR de un cobro sin pagos, **cuando** el dueño pulsa Cancelar cobro y el servidor lo confirma, **entonces** vuelve la vista Teclado vacía.
2. **Dado** un cobro cancelado (su QR sigue pagable porque pey no deja anularlo), **cuando** el cliente lo paga dentro de la ventana de escucha, **entonces** suena y aparece su aviso de pago.
3. **Dado** que el cobro se pagó justo antes de cancelarlo, **cuando** el servidor rechaza la cancelación, **entonces** la pantalla sigue mostrando el cobro con el mensaje del servidor, y el pago se avisa por el canal.
4. **Dado** que el dueño pulsó Cancelar cobro, **mientras** el servidor responde, **entonces** se ve "Cancelando…" y otro toque a Cancelar cobro no hace nada.
5. **Dado** la vista QR de un cobro, **cuando** el canal avisa que el cobro se canceló desde otra pantalla, **entonces** vuelve la vista Teclado vacía y el cobro se sigue escuchando como cobro anterior.

---

### Historia 8 — No perder los avisos si se recarga la página (Prioridad: P2) · Corte 2

**Como** dueño, **quiero** que la pantalla recupere mis cobros si se recarga o se cierra el navegador, **para** no perder el aviso de un pago por un toque equivocado.

**Por qué esta prioridad:** una recarga accidental en el mostrador es común, pero la demo funciona sin esta historia.

**Prueba independiente:** generar un cobro, recargar la página, tocar la pantalla y pagar el QR; suena y se muestra "Pago recibido".

**Escenarios de aceptación:**

1. **Dado** un cobro en pantalla dentro de su ventana de escucha, **cuando** el dueño recarga la página en el mismo celular, **entonces** la pantalla vuelve a mostrar ese cobro en la vista que corresponde a su estado y sigue escuchándolo, junto con los cobros anteriores.
2. **Dado** la página recién recuperada, **mientras** el dueño no toque la pantalla, **entonces** se ve el aviso "Toca para activar el sonido".
3. **Dado** un cobro recuperado que se pagó mientras la página estaba cerrada, **cuando** la pantalla lo recupera, **entonces** lo muestra como pagado, con su número de pagos y su total recibido, sin sonar.
4. **Dado** la página recuperada y ya tocada, **cuando** el servidor avisa un pago nuevo, **entonces** suena y se muestra igual que antes de recargar.
5. **Dado** un cobro anterior que se pagó mientras la página estaba cerrada, **cuando** la pantalla lo recupera, **entonces** aparece su aviso de pago (monto y concepto) sin sonar.
6. **Dado** un celular que no deja guardar datos (por ejemplo, en navegación privada), **cuando** el dueño recarga la página, **entonces** vuelve la vista Teclado vacía, igual que en el corte 1.

---

## 3. Requisitos *(obligatorio)*

### 3.1 Requisitos funcionales (notación EARS)

Cada RF lleva su corte: **[C1]** o **[C2]** (§1.2).

**Teclado y monto**

- **RF-001** (Ubicuo) [C1]: EL SISTEMA mostrará un teclado en pantalla con los dígitos del 0 al 9, el punto decimal y una tecla para borrar el último carácter.
- **RF-002** (Ubicuo) [C1]: EL SISTEMA mostrará en grande, con el signo de pesos, el monto que el dueño va escribiendo.
- **RF-003** (No deseado) [C1]: SI el dueño intenta escribir un tercer decimal, ENTONCES EL SISTEMA ignorará esa tecla.
- **RF-004** (No deseado) [C1]: SI el dueño intenta escribir un segundo punto decimal, ENTONCES EL SISTEMA ignorará esa tecla.
- **RF-005** (Ubicuo) [C1]: EL SISTEMA ofrecerá un campo opcional de concepto que acepta como máximo 40 caracteres.
- **RF-006** (Estado) [C1]: MIENTRAS el monto escrito está vacío o vale 0, EL SISTEMA mantendrá desactivado el botón Cobrar.
- **RF-007** (Ubicuo) [C2]: EL SISTEMA ofrecerá en la vista Teclado una tecla Monto libre, separada de Cobrar.
- **RF-008** (Dirigido por evento) [C2]: CUANDO el dueño pulsa Monto libre, EL SISTEMA pedirá al servidor un cobro de monto libre con el concepto escrito.
- **RF-065** (Estado) [C2]: MIENTRAS el monto escrito no está vacío ni vale 0, EL SISTEMA mantendrá desactivada la tecla Monto libre (QA-5).
- **RF-066** (Dirigido por evento) [C1]: CUANDO el monto escrito es "0" y el dueño pulsa otro dígito, EL SISTEMA reemplazará el 0 por ese dígito (QA-7).
- **RF-067** (Dirigido por evento) [C1]: CUANDO el monto está vacío y el dueño pulsa el punto, EL SISTEMA escribirá "0." (QA-7).
- **RF-068** (No deseado) [C1]: SI el dueño intenta escribir un sexto dígito en la parte entera del monto, ENTONCES EL SISTEMA ignorará esa tecla (QA-7).

**Crear el cobro**

- **RF-009** (Dirigido por evento) [C1]: CUANDO el dueño pulsa Cobrar con un monto mayor a 0, EL SISTEMA pedirá al servidor un cobro con ese monto y el concepto escrito.
- **RF-010** (Estado) [C1]: MIENTRAS el servidor crea el cobro, EL SISTEMA mostrará la vista Generando QR.
- **RF-011** (Estado) [C1; Monto libre en C2]: MIENTRAS el servidor crea el cobro, EL SISTEMA ignorará cualquier otro toque de Cobrar o de Monto libre.
- **RF-012** (No deseado) [C1]: SI el servidor rechaza el cobro, ENTONCES EL SISTEMA mostrará en la vista Teclado el mensaje que devuelve el servidor.
- **RF-013** (No deseado) [C1]: SI el servidor no responde o el celular no tiene conexión, ENTONCES EL SISTEMA mostrará en la vista Teclado un mensaje para el dueño que le pide revisar su conexión e intentar de nuevo.
- **RF-014** (No deseado) [C1]: SI el cobro no se crea o llega sin imagen del QR, ENTONCES EL SISTEMA conservará el monto y el concepto escritos para que el dueño los corrija o lo intente de nuevo.

**Mostrar el QR**

- **RF-015** (Dirigido por evento) [C1]: CUANDO el servidor devuelve el cobro creado con la imagen de su QR, EL SISTEMA mostrará la vista QR con esa imagen.
- **RF-078** (No deseado) [C1]: SI el servidor devuelve el cobro creado sin imagen del QR, ENTONCES EL SISTEMA mostrará en la vista Teclado "No se pudo mostrar el QR. Intenta de nuevo." y no escuchará ese cobro (C-3).
- **RF-016** (Ubicuo) [C1; "Monto libre" en C2]: EL SISTEMA mostrará en la vista QR el monto pedido (o "Monto libre") y el concepto.
- **RF-017** (Ubicuo) [C1]: EL SISTEMA mostrará en la vista QR la indicación "Escanéalo desde la app de tu banco, en la opción CoDi" (principio VII).
- **RF-018** (Estado) [C1]: MIENTRAS el cobro en pantalla está dentro de su vigencia, EL SISTEMA mostrará una cuenta regresiva en minutos y segundos del tiempo que le queda.
- **RF-019** (Ubicuo) [C1]: EL SISTEMA mostrará la cuenta regresiva con un error máximo de 2 segundos respecto a la vigencia que marca el servidor, aunque el reloj del celular esté desfasado (requiere el C-2 a la spec 001, QA-2).

**Saber que me pagaron**

- **RF-020** (Dirigido por evento) [C1]: CUANDO se muestra la vista QR, EL SISTEMA abrirá el canal de avisos del cobro.
- **RF-021** (Ubicuo) [C1]: EL SISTEMA solo mostrará un pago como recibido cuando el servidor lo informe (principio I).
- **RF-022** (Dirigido por evento) [C1]: CUANDO llega el aviso de un pago no avisado del cobro en pantalla, EL SISTEMA reproducirá el sonido de pago recibido, con las condiciones de RF-054 y RF-055.
- **RF-023** (Dirigido por evento) [C1]: CUANDO llega el aviso de un pago no avisado del cobro en pantalla, EL SISTEMA mostrará a pantalla completa, en verde, la vista Pago recibido con el monto recibido y el concepto.
- **RF-024** (Opcional) [C1]: DONDE el celular permite vibrar, EL SISTEMA vibrará al llegar el aviso de un pago no avisado.
- **RF-025** (Ubicuo) [C1]: EL SISTEMA intentará reproducir el sonido de pago recibido aunque el dueño no haya vuelto a tocar la pantalla después de pulsar Cobrar. Si el navegador lo rechaza, se aplica RF-054.
- **RF-026** (Estado) [C1; Mostrar QR otra vez en C2]: MIENTRAS se muestra la vista Pago recibido, EL SISTEMA la mantendrá hasta que el dueño pulse Nuevo cobro o Mostrar QR otra vez (E-7, QA-9).
- **RF-069** (Estado) [C2]: MIENTRAS el cobro en pantalla sigue dentro de su vigencia, EL SISTEMA mostrará en la vista Pago recibido el botón Mostrar QR otra vez (QA-9).
- **RF-070** (Dirigido por evento) [C2]: CUANDO el dueño pulsa Mostrar QR otra vez, EL SISTEMA mostrará la vista QR del mismo cobro, con su cuenta regresiva.
- **RF-071** (Dirigido por evento) [C2]: CUANDO un QR que se volvió a mostrar llega al final de su vigencia, EL SISTEMA volverá a la vista Pago recibido de ese cobro.
- **RF-027** (Dirigido por evento) [C2]: CUANDO llega el aviso del segundo pago de un cobro o de uno posterior, EL SISTEMA mostrará en la vista Pago recibido el número de pago y el total recibido.
- **RF-028** (No deseado) [C1]: SI un pago de un cobro de monto fijo trae un monto distinto al pedido, ENTONCES EL SISTEMA mostrará en la vista Pago recibido el monto pedido y el monto recibido.
- **RF-029** (Ubicuo) [C1]: EL SISTEMA avisará cada pago una sola vez, aunque vuelva a recibirlo al reconectarse o al consultar el estado.

**Consulta del estado durante la escucha**

- **RF-030** (Estado) [C1]: MIENTRAS el canal de avisos de un cobro en escucha está cortado dentro de su ventana de escucha, EL SISTEMA consultará el estado de ese cobro cada 3 segundos.
- **RF-031** (Estado) [C1]: MIENTRAS el canal de avisos de un cobro en escucha está cortado dentro de su ventana de escucha, EL SISTEMA intentará volver a abrirlo.
- **RF-032** (Estado) [C1]: MIENTRAS el canal de avisos del cobro en pantalla está cortado, EL SISTEMA mostrará un aviso de "Reconectando…" sin quitar el QR.
- **RF-033** (Dirigido por evento) [C1]: CUANDO la consulta del estado trae un pago no avisado, EL SISTEMA lo avisará igual que si hubiera llegado por el canal.
- **RF-034** (No deseado) [C1]: SI el servidor rechaza el canal por demasiadas pantallas abiertas, ENTONCES EL SISTEMA seguirá enterándose de los pagos con la consulta del estado.
- **RF-079** (Estado) [C1]: MIENTRAS el canal de un cobro está abierto dentro de su ventana de escucha, EL SISTEMA consultará su estado cada 8 segundos. EL SISTEMA mantendrá como máximo una consulta del estado en curso por cobro, incluso al cambiar de cadencia (C-4). Los pagos encontrados se avisan según RF-033 y RF-029.

**Vencimiento y fin de la escucha**

- **RF-035** (Dirigido por evento) [C1]: CUANDO un cobro en pantalla sin pagos llega al final de su vigencia, EL SISTEMA mostrará la vista QR vencido.
- **RF-036** (Ubicuo) [C1]: EL SISTEMA no mostrará el QR en la vista QR vencido (E-6).
- **RF-037** (Ubicuo) [C1; "Monto libre" en C2]: EL SISTEMA mostrará en la vista QR vencido el monto pedido (o "Monto libre") y el concepto.
- **RF-038** (Estado) [C1]: MIENTRAS el cobro en pantalla está vencido dentro de su ventana de escucha, EL SISTEMA mostrará en la vista QR vencido el texto "Si el cliente ya pagó, aquí te avisamos".
- **RF-039** (Estado) [C1]: MIENTRAS un cobro vencido sigue dentro de su ventana de escucha, EL SISTEMA seguirá avisando sus pagos igual que antes del vencimiento (QA-4).
- **RF-040** (Dirigido por evento) [C1]: CUANDO termina la ventana de escucha de un cobro en escucha, EL SISTEMA dejará de escucharlo sin intentar reconectarse.

**Nuevo cobro y cobros anteriores**

- **RF-041** (Ubicuo) [C1]: EL SISTEMA mostrará el botón Nuevo cobro en las vistas QR, QR vencido, Pago recibido y Error.
- **RF-042** (Dirigido por evento) [C1]: CUANDO el dueño pulsa Nuevo cobro, EL SISTEMA mostrará la vista Teclado con el monto y el concepto vacíos.
- **RF-043** (Dirigido por evento) [C2]: CUANDO el dueño pulsa Nuevo cobro, EL SISTEMA seguirá escuchando el cobro que estaba en pantalla hasta el fin de su ventana de escucha (E-4).
- **RF-044** (Dirigido por evento) [C2]: CUANDO llega el aviso de un pago no avisado de un cobro anterior, EL SISTEMA reproducirá el sonido de pago recibido, con las condiciones de RF-054 y RF-055.
- **RF-045** (Dirigido por evento) [C2]: CUANDO llega el aviso de un pago no avisado de un cobro anterior, EL SISTEMA mostrará un aviso con el monto recibido y el concepto de ese cobro, sin quitar la vista actual ni lo que el dueño esté escribiendo.

**Cancelar un cobro**

- **RF-046** (Estado) [C2]: MIENTRAS el cobro en pantalla está *pendiente*, EL SISTEMA mostrará el botón Cancelar cobro en la vista QR (E-5).
- **RF-047** (Dirigido por evento) [C2]: CUANDO el dueño pulsa Cancelar cobro, EL SISTEMA pedirá al servidor que cancele el cobro.
- **RF-048** (Dirigido por evento) [C2]: CUANDO el servidor confirma la cancelación, EL SISTEMA mostrará la vista Teclado con el monto y el concepto vacíos.
- **RF-049** (Dirigido por evento) [C2]: CUANDO el servidor confirma la cancelación, EL SISTEMA seguirá escuchando el cobro cancelado hasta el fin de su ventana de escucha, porque su QR sigue pagable.
- **RF-050** (No deseado) [C2]: SI el servidor rechaza la cancelación o no responde, ENTONCES EL SISTEMA seguirá mostrando el cobro con un mensaje para el dueño.
- **RF-072** (Estado) [C2]: MIENTRAS el servidor cancela el cobro, EL SISTEMA mostrará "Cancelando…" (QA-10).
- **RF-073** (Estado) [C2]: MIENTRAS el servidor cancela el cobro, EL SISTEMA ignorará cualquier otro toque de Cancelar cobro.
- **RF-074** (Dirigido por evento) [C2]: CUANDO el canal avisa que el cobro en pantalla se canceló sin que esta pantalla lo pidiera, EL SISTEMA actuará igual que con una cancelación propia confirmada (RF-048 y RF-049).

**Recuperar los cobros al recargar**

- **RF-051** (Dirigido por evento) [C2]: CUANDO la página se vuelve a abrir en el mismo celular, EL SISTEMA recuperará los cobros que estaban en escucha y siguen dentro de su ventana de escucha (E-8).
- **RF-052** (Dirigido por evento) [C2]: CUANDO recupera los cobros, EL SISTEMA mostrará el cobro que estaba en pantalla en la vista que corresponde a su estado.
- **RF-053** (No deseado) [C2]: SI el cobro que estaba en pantalla recibió pagos mientras la página estaba cerrada, ENTONCES EL SISTEMA los mostrará como pagados, con su número de pagos y su total recibido, sin sonido ni vibración (E-9).
- **RF-075** (No deseado) [C2]: SI un cobro anterior recuperado recibió pagos mientras la página estaba cerrada, ENTONCES EL SISTEMA mostrará el aviso de RF-045 de cada uno, sin sonido ni vibración (QA-6).
- **RF-076** (No deseado) [C2]: SI el celular no deja guardar los cobros en escucha, ENTONCES EL SISTEMA mostrará la vista Teclado vacía al volver a abrir la página (QA-6).
- **RF-054** (Estado, no deseado y dirigido por evento) [C1 ante un bloqueo o al volver a la página. C2 al recuperar]: MIENTRAS el dueño no haya tocado la pantalla después de recuperar los cobros, EL SISTEMA mostrará «Toca para activar el sonido». SI el navegador rechaza reproducir el sonido de un pago nuevo, ENTONCES EL SISTEMA mostrará ese aviso y reintentará el sonido en el primer toque. CUANDO la página vuelva a estar visible o reciba `pageshow`, EL SISTEMA preparará un desbloqueo para el primer toque (C-5).
- **RF-055** (No deseado) [C2]: SI llega un pago no avisado antes de que el dueño toque la pantalla tras recuperar los cobros, ENTONCES EL SISTEMA lo mostrará sin sonido.
- **RF-056** (No deseado) [C2]: SI el servidor ya no conoce un cobro anterior recuperado, ENTONCES EL SISTEMA dejará de escucharlo.

**Errores del cobro en pantalla**

- **RF-057** (No deseado) [C1]: SI el servidor ya no conoce el cobro en pantalla (por ejemplo, porque se reinició), ENTONCES EL SISTEMA mostrará la vista Error con un mensaje que pide revisar la app del banco para confirmar si llegó el pago.

**Pantalla encendida**

- **RF-058** (Opcional) [C1]: DONDE el navegador permite impedir que la pantalla del celular se apague, EL SISTEMA lo pedirá mientras haya al menos un cobro en escucha (E-10).
- **RF-059** (Dirigido por evento) [C1]: CUANDO deja de haber cobros en escucha, EL SISTEMA dejará que la pantalla del celular se apague normalmente.

**Generales**

- **RF-060** (Ubicuo) [C1]: EL SISTEMA mostrará el nombre PAGO FÁCIL en todas las vistas.
- **RF-061** (Ubicuo) [C1]: EL SISTEMA se podrá usar sin desplazarse hacia los lados en pantallas desde 320 px de ancho (principio VII).
- **RF-062** (Ubicuo) [C1]: EL SISTEMA mostrará todos sus mensajes en español, escritos para el dueño y sin códigos ni términos técnicos.
- **RF-063** (Ubicuo) [C1]: EL SISTEMA se comunicará solo con el servidor de PAGO FÁCIL, nunca directamente con pey (principio III).
- **RF-064** (Ubicuo) [C1]: EL SISTEMA tomará la dirección del servidor de un único valor de configuración.
- **RF-077** (Ubicuo) [C1]: EL SISTEMA mostrará el concepto, los mensajes del servidor y los datos guardados en el celular solo como texto, sin interpretarlos como contenido de la página (QA-8).

> Los RF se renumeraron al aplicar la entrevista. Los RF-065 a RF-077 salieron de la QA (QA-5 a QA-10), el RF-078 del cambio C-3 y el RF-079 del C-4. Se colocaron en su grupo para leerlos junto a los requisitos con los que se relacionan.

### 3.2 Entidades clave

La pantalla no crea datos de negocio: muestra los del servidor.

- **Cobro** (definido en la spec 001): interesan su QR, monto pedido o monto libre, concepto, estado, hora de creación, hora de vencimiento, fin de la ventana de escucha, número de pagos y total recibido.
- **Pago** (definido en la spec 001): su número dentro del cobro, el monto recibido, si es un monto distinto al pedido y su hora.
- **Pagos avisados**: qué pagos de cada cobro en escucha ya se mostraron, para no repetirlos (RF-029).
- **Cobros en escucha recordados** (corte 2): qué cobros estaban en escucha y cuál estaba en pantalla, guardado en el mismo celular para recuperarlos al recargar (RF-051). Se trata como dato no confiable al leerlo (RF-077).

---

## 4. Casos límite y manejo de errores

| Caso | Comportamiento esperado | Requisitos |
|---|---|---|
| Doble toque a Cobrar o a Monto libre | Solo se pide un cobro; el segundo toque se ignora mientras se genera el QR. | RF-011 |
| Tercer decimal o segundo punto | La tecla se ignora. | RF-003, RF-004 |
| Cero a la izquierda, punto como primera tecla o más de 5 dígitos enteros | "07" queda en "7"; el punto inicial escribe "0."; el sexto dígito entero se ignora. | RF-066, RF-067, RF-068 |
| Monto vacío o 0 | Cobrar queda desactivado. Desde el corte 2, el monto libre se pide solo con su tecla, que a su vez queda desactivada si hay un monto escrito, para que un toque sin querer no cree un QR donde el cliente decide cuánto paga. | RF-006, RF-007, RF-008, RF-065 |
| Monto mayor al máximo de la demo | El servidor lo rechaza con su mensaje ("El monto máximo de la demo es $100"); la pantalla lo muestra y conserva lo escrito. | RF-012, RF-014 |
| Concepto de más de 40 caracteres | El campo no deja escribir más. Si el servidor rechaza el concepto (por ejemplo, por caracteres no válidos), se muestra su mensaje. | RF-005, RF-012 |
| Concepto con forma de código (por ejemplo, `<script>`) | Se muestra tal cual, como texto; no se ejecuta. | RF-077 |
| Demasiados cobros seguidos desde el mismo celular | El servidor responde "Demasiados cobros seguidos. Espera un minuto."; la pantalla lo muestra y conserva lo escrito. | RF-012, RF-014 |
| **Falla de pey** al crear el cobro (mantenimiento, llave rechazada, error general) | La pantalla muestra el mensaje del servidor y conserva lo escrito para reintentar. | RF-012, RF-014 |
| El cobro llega sin imagen del QR (pey no la entregó) | Vista Teclado con "No se pudo mostrar el QR. Intenta de nuevo."; se conserva lo escrito. Nadie vio ese QR, así que no se escucha (C-3). | RF-078, RF-014 |
| Generar el QR tarda varios segundos (el primero después de arrancar el servidor midió 7 a 9 s, TK-5 de la spec 001) | La vista Generando QR se mantiene hasta que el servidor responda o falle. | RF-010, RF-013 |
| Sin internet o servidor caído | Mensaje que pide revisar la conexión; se conserva lo escrito. | RF-013, RF-014 |
| Reloj del celular desfasado | La cuenta regresiva sigue la hora del servidor (C-2); error máximo de 2 s. | RF-019 |
| El primer QR tarda varios segundos en crearse | La cuenta regresiva descuenta ese tiempo: arranca con lo que de verdad le queda al QR (C-2). | RF-019 |
| El cliente escanea con la cámara normal | No paga: la pantalla siempre indica usar la opción CoDi de la app del banco. | RF-017 |
| **Falla del aviso de pey** (no llega al servidor) | La resuelve el servidor (consulta de respaldo, spec 001); la pantalla recibe el pago por el canal igual. | RF-022, RF-023 |
| Corte del canal de avisos | Consulta del estado cada 3 s, aviso "Reconectando…" y reintento del canal; el pago se avisa igual. | RF-030 a RF-033 |
| Canal abierto con eventos retenidos | Consulta del estado cada 8 s. El pago se avisa una vez aunque el evento llegue después. | RF-079, RF-033, RF-029 |
| El navegador rechaza el sonido de un pago | Se ve el pago y «Toca para activar el sonido». El primer toque reintenta el sonido. | RF-023, RF-054 |
| Demasiadas pantallas abiertas desde la misma conexión (más de 10 canales por IP) | El servidor rechaza el canal; la pantalla sigue con la consulta del estado cada 3 s. Con más de 10 cobros en escucha (más de 10 cobros en 20 minutos, desde el corte 2) pasa seguido y multiplica las consultas a pey. **Limitación aceptada** (QA-3), hasta un issue por crear. | RF-034 |
| El mismo pago llega dos veces (reconexión o consulta) | Se muestra una sola vez. | RF-029 |
| **QR reutilizado** (varios pagos al mismo QR) | Cada pago nuevo suena y se muestra con su monto. Desde el corte 2, también con "Pago n" y el total recibido, y el dueño puede volver a mostrar el QR mientras siga vigente. | RF-022, RF-023, RF-027, RF-069, RF-070 |
| El QR que se volvió a mostrar vence | Vuelve la vista Pago recibido de ese cobro. | RF-071 |
| **Monto distinto** en un cobro de monto fijo | La vista Pago recibido muestra el monto pedido y el recibido. | RF-028 |
| Cobro de monto libre pagado | La vista Pago recibido muestra lo que pagó el cliente; no aplica "monto distinto". | RF-023 |
| **QR vencido** sin pagos | El QR desaparece; vista QR vencido con monto, concepto y Nuevo cobro. | RF-035 a RF-037, RF-041 |
| **Pago tardío** (dentro de la ventana de escucha) | Con la vista QR vencido abierta, suena y se muestra "Pago recibido" igual que a tiempo (corte 1, QA-4). Si el dueño ya pulsó Nuevo cobro, se avisa como cobro anterior desde el corte 2; en el corte 1 solo lo ve en su banco. | RF-039, RF-043, RF-044, RF-045 |
| Pago después de la ventana de escucha | La pantalla ya no lo escucha. El servidor lo registra (spec 001), pero el dueño solo lo ve en la app de su banco. | RF-040 |
| Pago a un cobro anterior mientras el dueño teclea otro monto | Suena y aparece el aviso de ese cobro sin borrar lo que se está tecleando (corte 2). | RF-044, RF-045 |
| Pago a un cobro cancelado | El QR sigue pagable porque pey no permite anularlo; suena y aparece su aviso (corte 2). | RF-049, RF-044, RF-045 |
| El cobro se paga justo antes de cancelarlo | El servidor rechaza la cancelación; la pantalla sigue mostrando el cobro con el mensaje, y el pago llega por el canal. | RF-050 |
| Doble toque a Cancelar cobro | Se ve "Cancelando…" y el segundo toque se ignora. | RF-072, RF-073 |
| El cobro en pantalla se cancela desde otra pantalla | Se trata como una cancelación propia confirmada: vuelve la vista Teclado y el cobro se sigue escuchando. | RF-074 |
| Reinicio del servidor con un cobro en pantalla | Vista Error: el cobro ya no se puede seguir; se pide revisar la app del banco. | RF-057 |
| Reinicio del servidor con cobros anteriores en escucha | Esos cobros dejan de escucharse. | RF-056 |
| Se recarga la página o se cierra el navegador | Desde el corte 2, se recuperan los cobros en escucha; los pagos que llegaron con la página cerrada se muestran sin sonar (el cobro en pantalla en su vista, los anteriores con su aviso), y se pide un toque para activar el sonido. En el corte 1, vuelve la vista Teclado vacía. | RF-051 a RF-055, RF-075 |
| El celular no deja guardar datos (navegación privada) | La recarga vuelve a la vista Teclado vacía, como en el corte 1. | RF-076 |
| El celular apaga la pantalla o el navegador pasa a segundo plano | Mientras haya un cobro en escucha, la pantalla pide no apagarse donde el navegador lo permite. Si aun así se pausa, al volver el canal o la consulta del estado traen el pago y se avisa. | RF-058, RF-029, RF-033 |
| **Devolución** | Fuera de alcance: pey no ofrece devoluciones por API; el dueño la hace desde su banco. | — |

---

## 5. Fuera de alcance *(obligatorio)*

| Fuera de alcance | Dónde se resuelve |
|---|---|
| Cambios al servidor | Spec 001; si hacen falta, como cambio `C-n` (§8.2) |
| Instalar la web como app (PWA con ícono y uso sin conexión) | #22 |
| Registro e inicio de sesión del negocio | #30, #24 |
| Historial de cobros y corte del día (más allá de los cobros en escucha) | #39, #38 |
| Recuperar los cobros en otro celular o en otro navegador | #24 (requiere cuentas) |
| Cupones y plan Premium | #40, #37 |
| Identidad visual completa (logo final, paleta y tipografía). La pantalla solo lleva el nombre PAGO FÁCIL y colores simples, como pide el #64 | #21 |
| Sonido y animación finales de pago recibido | #33 |
| Revisión de accesibilidad (incluidos el zoom al 200 % y los lectores de pantalla) y pruebas con usuarios reales | #42, #43 |
| Manejo avanzado de estados sin conexión más allá de esta spec | #41 |
| QR permanente o impreso para el mostrador | Issue por crear (spec 001, §5) |
| Enlaces de pago y cobro por notificación push CoDi | #36 |
| Bot de WhatsApp | #46–#48 |
| Despliegue de la web con HTTPS | #65, #34 |

---

## 6. Criterios de éxito *(obligatorio)*

- **CE-001** [C1]: desde un Android con Chrome y desde un iPhone con Safari, un cobro real de $0.01 se teclea, se genera, se paga desde la app de un banco y el celular suena y muestra "Pago recibido", de punta a punta.
- **CE-002** [C1]: con el canal entregando eventos en vivo y el sonido habilitado, el celular suena y muestra "Pago recibido" en menos de 2 segundos después de que el servidor emite el aviso de pago.
- **CE-003** [C1]: con el canal de avisos cortado, un pago se avisa en menos de 6 segundos después de que el servidor lo registra.
- **CE-004** [C1]: un cobro de $25.50 con concepto vacío se pide con 6 toques (2, 5, punto, 5, 0 y Cobrar).
- **CE-005** [C1]: después de pulsar Cobrar, la vista Generando QR aparece en menos de 0.1 segundos.
- **CE-006** [C1]: con el servidor funcionando normal y sin ser el primer cobro después de arrancarlo, el QR se ve en menos de 3 segundos después de pulsar Cobrar.
- **CE-007** [C1]: en una pantalla de 320 px de ancho, todas las vistas se usan sin desplazarse hacia los lados y el QR ocupa al menos el 70 % del ancho.
- **CE-008** [C1]: un mismo pago recibido por el canal, al reconectarse y por la consulta del estado se avisa una sola vez, comprobado con pruebas automáticas.
- **CE-009** [C1]: con el reloj del celular desfasado 5 minutos, la cuenta regresiva difiere en menos de 2 segundos de la vigencia que marca el servidor.
- **CE-010** [C1]: ningún archivo de la web contiene la llave de pey ni el secreto del aviso, y la web no hace ninguna petición a pey, comprobado revisando sus archivos y sus peticiones en el navegador.
- **CE-011** [C1]: en Chrome de Android, con un cobro en escucha, la pantalla del celular sigue encendida después de 10 minutos sin tocarla.
- **CE-012** [C1]: con la vista QR vencido abierta, un pago que llega 5 minutos después del vencimiento suena y se muestra, comprobado con pruebas automáticas con reloj controlado.
- **CE-013** [C2]: después de pulsar Nuevo cobro, un pago al cobro anterior suena y muestra su aviso sin borrar lo que se está tecleando, comprobado con pruebas automáticas.
- **CE-014** [C2]: después de recargar la página con un cobro en escucha y tocar la pantalla, un pago a ese cobro suena y se muestra; un pago que llegó con la página cerrada se muestra sin sonar.
- **CE-015** [C1]: un cobro con el concepto `<script>alert(1)</script>` muestra ese texto tal cual y no ejecuta nada, comprobado con pruebas automáticas.
- **CE-016** [C1]: con el C-2 aplicado y un primer cobro que tarda 9 segundos en crearse, la cuenta regresiva arranca en 9:51 (con 2 segundos de margen), comprobado con pruebas automáticas con reloj controlado.
- **CE-017** [C1]: con el canal abierto y mudo, el primer GET que devuelve el pago lo muestra y lo hace sonar con reproducción habilitada. La prueba con reloj controlado dispara la primera consulta a los 8 segundos y comprueba que el canal sigue abierto (C-4).
- **CE-018** [C1]: si `play()` rechaza un pago nuevo, la pantalla muestra «Pago recibido» y «Toca para activar el sonido». Al tocar, la pantalla vuelve a llamar a `play()` y quita el aviso cuando el intento se inicia, comprobado con pruebas automáticas (C-5).

---

## 7. Supuestos y dependencias

**Supuestos**

- El servidor de la spec 001 está completo (corte M0 y corte 2: ventana de gracia, monto libre y cancelación) y su contrato es el de `specs/001-backend-mvp/contracts/`. La pantalla no inventa reglas que ya decide el servidor: el máximo del monto, el límite de cobros por minuto y los mensajes de error vienen del servidor.
- Los mensajes de error del servidor ya están escritos para el dueño (principio VII, decisión DP-9 del plan 001), así que la pantalla los muestra tal cual.
- Los navegadores de celular pueden exigir un toque para reproducir audio. Cobrar o Monto libre pueden desbloquearlo. Al recuperar cobros, al volver a la página o cuando el navegador rechaza el sonido, se aplica RF-054.
- El celular puede estar en silencio o con el volumen bajo. La vista verde y la vibración (donde exista) siguen avisando. El plan comprueba si el interruptor de silencio del iPhone calla el sonido de la página.
- La vibración solo existe en algunos celulares; en Safari de iPhone no está disponible, por eso RF-024 es opcional. Lo mismo pasa con mantener la pantalla encendida (RF-058).
- El aviso de pago de un cobro anterior (RF-045) se cierra cuando el dueño lo toca. La QA puede cuestionarlo.
- El sonido es propio o tiene licencia libre, y se anota en la declaración de componentes de terceros que piden las reglas del hackathon (issue #64, #55).
- Cualquiera que abra la web puede cobrar con el negocio de demo: no hay cuentas (#24), igual que en la spec 001.
- La pantalla no hace pruebas automáticas contra el pey real ni contra el servidor real: usa un servidor simulado (principio V). Cómo se prueban se define en el plan de esta spec, la primera de la web (AGENTS.md §6).
- Las cifras de 3 segundos (consulta del estado), 2 segundos (margen de la cuenta regresiva y del aviso) y 70 % (tamaño del QR) salen del issue #64, del contrato del servidor (una consulta a pey cada 3 s por cobro) y del principio VII.

**Dependencias externas**

| Dependencia | Qué bloquea | Dueño | Estado (15 nov) |
|---|---|---|---|
| Cambio C-2 aplicado en la spec 001 (hora del servidor en cada cobro) | RF-019, CE-009, CE-016 | Hugo | Aplicado el 2026-11-15 (`hora_servidor`, F9 de la 001) |
| Servidor de la spec 001 desplegado con HTTPS | CE-001, CE-002 | Altairtm (#65) | Pendiente |
| Dominio de la web dado de alta en los orígenes permitidos del servidor | Que el navegador deje a la web usar el servidor (spec 001, RF-035) | Altairtm (#65) | Pendiente |
| Web publicada con HTTPS | CE-001 y CE-011 (los navegadores exigen HTTPS para varias funciones del celular) | #65, #34 | Pendiente |
| Sonido de pago recibido con licencia | RF-022, RF-044 | Responsable de #64 (Miguel) | Resuelto por R-7 del plan: la web genera su propio sonido, sin licencia que declarar (errata 4 de la QA de tasks, 2026-11-15) |
| CoDi activado en el banco con que se prueba | CE-001 | Hugo | Se activa el 15 nov |
| Un Android con Chrome y un iPhone con Safari | CE-001, CE-011 | Equipo | Por confirmar |

---

## 8. Dudas y decisiones

### 8.1 Entrevista con Hugo (2026-11-15)

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| E-1 | ¿Qué alcance tiene la spec 002? (antes del borrador) | **Todo el issue #64**: teclado, QR con cuenta regresiva, aviso de pago con sonido, pantalla verde y vibración, respaldo si se corta el canal y Nuevo cobro. El servidor se usa tal cual; si necesita algo, va como `C-n` a la 001. | Todos |
| E-2 | El #64 está en el milestone M0 (hoy, 1:00 PM). ¿Cómo se entrega? | **Dos cortes**, como la 001. Corte 1: lo mínimo de la demo. Corte 2 (antes del 21 nov): monto libre, QR vencido con pagos tardíos, "Pago 2" y lo que salió de esta entrevista. | §1.2, todos |
| E-3 | ¿Cómo pide el dueño un cobro de monto libre? | **Tecla "Monto libre"** propia. Cobrar queda desactivado mientras el monto esté vacío o en 0, para que un toque sin querer no cree un QR libre (el riesgo de QA-3 de la 001). Corte 2. | RF-006, RF-007, RF-008 |
| E-4 | Al pulsar Nuevo cobro, ¿qué pasa con el cobro anterior? | **Se sigue escuchando** hasta el fin de su ventana. Si llega un pago, suena y aparece un aviso con su monto y concepto, sin borrar el cobro en curso. Corte 2; en el corte 1, Nuevo cobro deja de escucharlo. | RF-043, RF-044, RF-045 |
| E-5 | ¿La pantalla ofrece cancelar un cobro? | **Botón Cancelar cobro** en la vista QR de un cobro sin pagos. Lo cancela en el servidor y vuelve al teclado; el cobro se sigue escuchando porque su QR sigue pagable. Corte 2. | RF-046 a RF-050 |
| E-6 | ¿Qué muestra la vista QR vencido? | **Se oculta el QR** para que nadie lo escanee de nuevo. Se ven "QR vencido", el monto, el concepto, "Si el cliente ya pagó, aquí te avisamos" (corte 2) y Nuevo cobro. | RF-035 a RF-038 |
| E-7 | ¿Cuánto dura la vista Pago recibido? | **Hasta que el dueño pulse Nuevo cobro.** Si el QR se vuelve a pagar, suena otra vez. | RF-026 |
| E-8 | ¿Qué pasa al recargar la página con un QR en pantalla? | **Se recuperan los cobros** que siguen dentro de su ventana de escucha, en el mismo celular: se muestra el que estaba en pantalla y se siguen escuchando los demás. Corte 2. | RF-051, RF-052, RF-056 |
| E-9 | ¿Qué pasa con los pagos que llegaron con la página cerrada? | **Se muestran sin sonar**, como pagados, con su número de pagos y su total. Solo suenan los pagos que lleguen después de recuperar, y antes se pide un toque ("Toca para activar el sonido"). | RF-053, RF-054, RF-055 |
| E-10 | ¿La pantalla pide al celular que no se apague? (P-1) | **Sí, mientras haya un cobro en escucha**, donde el navegador lo permita. Corte 1. | RF-058, RF-059 |

**Consecuencias aplicadas sin pregunta aparte** (salen de E-2 a E-10; la QA las puede cuestionar):

- En el corte 1, un segundo pago al mismo QR **suena igual** (RF-022 y RF-023 aplican a todo pago no avisado); el corte 2 solo agrega "Pago n" y el total (RF-027). Así el corte 1 no deja un pago sin avisar, el mismo choque con el principio VIII que resolvió el C-1 de la spec 001.
- El monto distinto visible (RF-028) va en el corte 1, porque el servidor ya lo informa en cada pago y el principio VIII exige definirlo.
- La consulta del estado y el reintento del canal (RF-030, RF-031) valen para todos los cobros en escucha, no solo el de pantalla.
- Cancelar cobro solo aparece con el cobro *pendiente*, igual que la regla del servidor (spec 001, RF-024).
- Lo que se recuerda para recuperar los cobros vive en el mismo celular; recuperarlos en otro equipo requiere cuentas (#24, §5).

### 8.2 Cambios a specs aprobadas

| # | Spec | Cambio propuesto | Origen | Estado |
|---|---|---|---|---|
| C-2 | 001 | RF-008 agrega "la hora actual del servidor" a cada cobro que se devuelve (crear, ver y cancelar) y a los eventos del canal, para que la cuenta regresiva no dependa del reloj del celular (RF-019). Afecta a RF-008, a `contracts/crear-cobro.md` (objeto cobro) y a `contracts/canal-avisos.md`. Se aplica antes del corte 1 de esta spec. | QA-2 | Aprobado por Hugo el 2026-11-15 y aplicado el mismo día en la 001: campo `hora_servidor` (plan 001 TK-6, tasks 001 F9) |
| C-3 | 002 (esta) | Nuevo RF (No deseado) [C1]: SI el cobro creado llega sin imagen del QR, ENTONCES EL SISTEMA mostrará en la vista Teclado "No se pudo mostrar el QR. Intenta de nuevo." y conservará el monto y el concepto. Más su fila en §4, y RF-015 lo excluye. | DP-2 y DP-3 del plan (la pantalla usa la imagen de pey, que puede llegar vacía) | Aprobado y aplicado por Hugo el 2026-11-15 (RF-078, RF-014, RF-015, §4, historia 1 escenario 12) |
| C-4 | 002 (esta) | Consulta cada 8 s con SSE abierto, un solo GET en curso por cobro y el mismo registro de pagos avisados (RF-079, CE-017). | Eventos retenidos por el túnel rápido de Cloudflare en las pruebas de Android e iPhone. | Aprobado por Hugo el 2026-11-16. Verificación manual pendiente. |
| C-5 | 002 (esta) | Amplía RF-054 para el rechazo de `play()`, el reintento con un toque y el desbloqueo al volver a la página (CE-018). | El navegador podía rechazar el sonido sin mostrar el aviso para activarlo. | Aprobado por Hugo el 2026-11-16. Verificación manual pendiente. |

### 8.3 Propuestas

| # | Propuesta | Por qué | Decisión |
|---|---|---|---|
| P-1 | Pedir al celular que no apague la pantalla mientras se muestra un QR, donde el navegador lo permita | Si la pantalla se apaga durante los 10 minutos de vigencia, el navegador puede pausar la página y el sonido llega tarde o no llega. No está en el issue #64. | **Aceptada** (E-10), mientras haya un cobro en escucha. Corte 1. |

### 8.4 Revisión QA (2026-11-15, una sola pasada)

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QA-1 | Promesa imposible | El corte 1 no tiene fecha (§1.2) y el #64 está en el milestone M0: la entrega del kickoff es hoy a la 1:00 PM y la QA empezó a las 10:32. Faltan la QA, el plan, las tasks y sus QA, la implementación con pruebas primero y el despliegue (#65 pendiente, §7). El formulario de Luma pide la app en vivo como "preferido", no como obligatorio (`docs/plan-hackathon.md`, §2). | §1.2, CE-001 | Fijar en §1.2 el corte 1 para antes del 20 nov (fin de M1) y enviar el formulario del kickoff sin la pantalla de esta spec (repo público y descripción). Hugo avisa al responsable del #64. | **Corte 1 antes del 20 nov** (fin de M1), como se recomienda. El formulario del kickoff va sin la pantalla de esta spec. Aplicada. |
| QA-2 | Hueco | RF-019 (cuenta regresiva con 2 s de error aunque el reloj del celular esté desfasado) no se puede cumplir con lo que da el servidor. (a) `creado_en` se fija **antes** de pedirle el QR a pey (`backend/app/main.py:181-185`, `backend/app/cobros.py:151`): con los 7 a 9 s del primer cobro (TK-5 de la 001), la cuenta empezaría en 10:00 cuando le quedan 9:51. (b) El objeto cobro no trae la hora actual del servidor (`contracts/crear-cobro.md`, "Objeto cobro"), así que al consultar el estado, al recibir eventos o al recuperar cobros (C2) la pantalla solo tiene el reloj del celular. | RF-019, CE-009, RF-040, RF-051 | Cambio **C-2 a la spec 001**: RF-008 agrega "la hora actual del servidor" a cada cobro que se devuelve, también en los eventos del canal. RF-019 queda igual. | **C-2 a la spec 001** (hora actual del servidor en cada cobro y en los eventos), como se recomienda. C-2 aprobado aparte, sin aplicar (§8.2). Aplicada. |
| QA-3 | Construibilidad | Con E-4 y E-5, cada cobro anterior se escucha con su propio canal hasta 20 min. El servidor admite como máximo 10 canales por IP (`backend/app/config.py:38`, `backend/app/main.py:250`) y, por cada canal abierto, le pregunta a pey cada 5 s (spec 001, RF-040). Un negocio con más de 10 cobros en 20 min llega al límite. Además se multiplican las consultas a pey, cuyo límite de peticiones se desconoce (spec 001, §8.5). | RF-030, RF-034, RF-043, RF-049, RF-051 | Solo el cobro en pantalla usa el canal de avisos. Los cobros anteriores se siguen con la consulta del estado cada 10 s y su aviso puede llegar hasta unos 12 s tarde (se agrega un CE). No hace falta ningún C-n. | **Aceptar el límite** (Hugo se aparta de la recomendación): cada cobro anterior se sigue escuchando con su canal; al pasar de 10 canales por IP, la pantalla consulta el estado cada 3 s (RF-034). Sin C-n. Aplicada. |
| QA-4 | Ambigüedad | El comportamiento temporal del corte 1 dice que al vencer el QR la pantalla deja de escuchar el cobro. Pero el servidor ya mantiene el canal abierto durante la ventana de gracia (corte 2 de la 001 entregado, commit `eeaa1d1`). Dejar de escuchar es trabajo extra y pierde el aviso de un pago hecho a las 9:59 cuyo aviso llega después de las 10:00. | §1.2, RF-038, RF-039 | Pasar RF-038 y RF-039 (pagos tardíos con la vista QR vencido) al corte 1 y quitar ese punto temporal. Los cobros anteriores siguen en el corte 2. | **Pagos tardíos al corte 1**: RF-038 y RF-039 pasan a [C1] y se quita el punto temporal de §1.2. Como se recomienda. Aplicada. |
| QA-5 | Caso límite | RF-008 crea el monto libre "sin importar el monto tecleado". Con "$25.50" escrito, un toque errado a Monto libre crea un QR donde el cliente decide cuánto paga: el mismo riesgo que E-3 quiso evitar. | RF-007, RF-008 | La tecla Monto libre solo está activa con el monto vacío o en 0, en espejo de RF-006. | **Monto libre solo sin monto**: la tecla solo está activa con el monto vacío o en 0. Como se recomienda. Aplicada. |
| QA-6 | Hueco | RF-053 muestra "como pagados" los cobros recuperados que se pagaron con la página cerrada. Pero ninguna vista lista los cobros anteriores, así que para ellos no hay dónde mostrarlo. Tampoco se dice qué pasa si el celular no deja guardar nada (modo privado). | RF-051, RF-053 | Para cada cobro anterior pagado con la página cerrada, mostrar el aviso de RF-045 sin sonido. Si el celular no deja guardar, la recarga se comporta como en el corte 1. | **Aviso sin sonido** por cada cobro anterior pagado con la página cerrada; sin poder guardar, la recarga se comporta como en el corte 1. Como se recomienda. Aplicada. |
| QA-7 | Ambigüedad | El teclado no define los ceros a la izquierda ("007"), qué pasa si el punto es la primera tecla ni cuántos dígitos enteros acepta: "$99999999" se escribe y el servidor lo rechaza hasta pulsar Cobrar. | RF-001 a RF-004 | Un 0 inicial seguido de otro dígito se reemplaza ("07" → "7"), un punto inicial escribe "0.", y la parte entera acepta como máximo 5 dígitos. El máximo de la demo lo sigue validando el servidor. | **Tres reglas**: el 0 inicial se reemplaza, el punto inicial escribe "0." y la parte entera acepta máximo 5 dígitos. Como se recomienda. Aplicada. |
| QA-8 | Seguridad | La pantalla muestra textos que no escribió ella: el concepto (pasa la validación de caracteres imprimibles del servidor, pero `<script>` es imprimible), los mensajes del servidor y los cobros recordados en el celular (C2). Si se interpretan como parte de la página, se puede inyectar código en la pantalla del negocio. | RF-016, RF-023, RF-037, RF-045, RF-051 | Nuevo RF [C1]: EL SISTEMA mostrará el concepto, los mensajes del servidor y los datos recordados solo como texto, sin interpretarlos como contenido de la página. | **Nuevo RF [C1]**: concepto, mensajes del servidor y datos guardados se muestran solo como texto. Como se recomienda. Aplicada. |
| QA-9 | Hueco | La spec 001 (E-3) permite reutilizar el QR **a propósito**. Pero desde el primer pago la pantalla se queda en Pago recibido hasta Nuevo cobro (E-7) y no hay forma de volver a mostrar el QR a un segundo cliente. | RF-026, Historia 3 | Anotar en §5 "Volver a mostrar el QR después de un pago", junto al QR permanente (issue por crear). Un segundo pago de alguien que ya escaneó se sigue avisando. | **Botón "Mostrar QR otra vez"** (Hugo se aparta de la recomendación): en la vista Pago recibido, mientras el QR siga vigente, vuelve a la vista QR del mismo cobro. Corte 2. Aplicada. |
| QA-10 | Caso límite | No se dice qué pasa mientras se cancela: no hay vista de carga ni protección contra el doble toque (principio VII: estado de carga, error y éxito). Tampoco se dice qué pasa si el canal trae `cancelado` de un cobro en pantalla que esta pantalla no canceló (otra pestaña o alguien con el identificador, `contracts/canal-avisos.md`). | RF-046 a RF-050 | Mientras el servidor cancela, se ve "Cancelando…" y se ignoran otros toques. Un `cancelado` que llega por el canal se trata igual que una cancelación propia confirmada (RF-048 y RF-049). | **"Cancelando…" y mismo trato**: se ignoran toques mientras cancela, y un *cancelado* que llega por el canal se trata como una cancelación propia confirmada. Como se recomienda. Aplicada. |

**Consecuencias aplicadas sin pregunta aparte** (salen directo de las decisiones):

- QA-9: si el QR que se volvió a mostrar vence, vuelve la vista Pago recibido (RF-071), porque la vista QR vencido es solo para cobros sin pagos (RF-035).
- QA-2: CE-016 comprueba con reloj controlado que la cuenta regresiva descuenta lo que tardó en crearse el primer QR.
- QA-10: el cobro cancelado desde otra pantalla pasa a ser un cobro anterior (glosario).

**Bloques de la pasada:**

1. **Coherencia interna**: glosario, 64 RF, 14 CE, E-1 a E-10 y P-1 existen y se usan con el mismo sentido; no quedan restos de las marcas resueltas. El siguiente `C-n` libre es C-2 (la 001 tiene C-1). Salen QA-4, QA-5, QA-6 y las erratas 1, 2 y 5.
2. **Otras specs, plan del hackathon, reglas e issues**: RF-003, RF-023, RF-024, RF-035 y RF-041 de la 001, su DP-9, su TK-5, su QA-3 y su C-1 existen y dicen lo que se les atribuye. Cumple con las reglas: cobro real con reacción visible, producción, la llave nunca en el cliente (RF-063) y no se revende el API. El issue #64 queda cubierto, salvo el logo (errata 3). Del calendario sale QA-1; de la E-3 de la 001, QA-9.
3. **Código (solo lectura)**: `web/` solo tiene su README. El backend tiene 104 pruebas en verde (`uv run --directory backend pytest -q`). CORS acepta `GET` y `POST` con `Content-Type` (`main.py:134-137`): alcanza para crear, ver, cancelar y abrir el canal. Salen QA-2 y QA-3.
4. **API de pey**: la web nunca llama a pey (RF-063), así que no usa ningún campo directamente. Los hechos que hereda (monto 0 = monto libre, no se puede anular un QR, QR pagable sin límite, imagen del QR más lenta) se comprobaron en la QA de la 001 el 14 nov. El dibujo del QR en la pantalla queda para el plan (§8.5).
5. **Dependencias externas**: todas tienen dueño y estado en §7. Las fallas de pey y del aviso las cubre el servidor y la pantalla las muestra (§4).
6. **Casos límite y pantallas**: carga, error, vacío y sin conexión cubiertos, salvo la cancelación (QA-10). 320 px cubierto. Zoom al 200 % y lector de pantalla sin cubrir (errata 4). Sonido bloqueado cubierto (RF-025, RF-054); celular en silencio sin cubrir (errata 6). La cámara normal está cubierta (RF-017). En cobros están el pago tardío, el monto distinto, el pago repetido, el QR vencido, las devoluciones y el reinicio. De aquí salen QA-5 a QA-7, QA-9 y QA-10.
7. **Seguridad y rendimiento**: la web no tiene secretos ni llama a pey (RF-063, CE-010). Las firmas y la deduplicación son del servidor; la pantalla solo deduplica sus avisos (RF-029). Los tiempos son medibles (CE-002, CE-003, CE-005, CE-006). Salen QA-8 (inyección) y QA-3 (consultas a pey).
8. **Construibilidad y reparto**: QA-1 (fecha). El #64 está asignado a Beer17 y sugiere a Miguel; el reparto va en el plan. La web todavía no tiene herramienta de pruebas: es la primera spec de la web, y elegirla exige comparativa en el plan (principio IX, AGENTS.md §6).

**Erratas** (sin efecto en el comportamiento; aplicadas el 2026-11-15, a pedido de Hugo):

1. RF-037 muestra "Monto libre" sin la nota "[C2]" que sí lleva RF-016.
2. RF-012 y RF-013 no dicen dónde aparece el mensaje: en la vista Teclado. La vista Error es solo la de RF-057; aclararlo en el glosario.
3. El #64 pide "logo y colores simples con el nombre PAGO FÁCIL"; RF-060 solo pide el nombre. Anotar en §5 que el logo final es de #21.
4. Zoom al 200 % y lector de pantalla: agregar a la fila de #42 en §5.
5. §7, dependencia del sonido: citar también RF-044.
6. Agregar a §4 la fila "Celular en silencio o con volumen bajo": la vista verde y la vibración (donde exista) siguen avisando. El plan comprueba si el interruptor de silencio del iPhone calla el sonido.

### 8.5 Pendientes

- No quedan marcas `[NECESITA ACLARACIÓN]` (resueltas con E-3, E-4 y E-5).
- Temas para el plan:
  - **Imagen del QR.** La medición TK-5 de la spec 001 dejó a esta spec la decisión de seguir con la imagen que genera pey (lenta en el primer cobro) o dibujar el QR en la pantalla. La decide el plan; afecta a CE-006.
  - **Herramienta de pruebas de la web.** Es la primera spec de la web: el plan elige con qué se prueban la pantalla y su servidor simulado, con comparativa (principio IX, AGENTS.md §6).
  - **El límite de canales** queda como limitación aceptada (QA-3, §4); el issue que la resuelva se crea cuando haga falta.

---

## 9. Criterios de finalización

- [ ] Cada RF tiene al menos una prueba automática o un paso de verificación manual.
- [ ] Todos los criterios de éxito (CE) están comprobados.
- [ ] No quedan marcas `[NECESITA ACLARACIÓN]` abiertas.
- [ ] Hay una revisión de seguridad hecha: la web no contiene secretos, no llama a pey y solo muestra un pago como recibido por avisos del servidor.
