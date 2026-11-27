# Spec 004: Cobro rápido: calculadora, duración del QR y descarga del código

- **ID**: `004-cobro-rapido`
- **Fecha**: `2026-11-26`
- **Estado**: `Aprobada`. Hugo la aprobó el 2026-11-26 después de la entrevista (`E-1` a `E-9`) y de la revisión QA en una sola pasada (`QA-1` a `QA-8` y sus 2 erratas, todas aplicadas). Se entrega en dos cortes (§1.2). Sin marcas `[NECESITA ACLARACIÓN]` abiertas. Los cambios a specs aprobadas (`C-12` en spec 001, `C-13` en spec 002 y `C-14` en spec 003, §8.2) quedan aprobados por separado y pendientes de aplicar en sus fases correspondientes.
- **Rama**: `feature/132-spec-004-cobro-rapido`
- **Issues**: #132 (escribir la spec 004), #120 (duración del QR en el servidor, N-06), #100 (calculadora en la pantalla de cobro), #121 (selector de duración en la web, N-06). Depende de #119 (actualización de persistencia para QR sin vencimiento en el corte 2) y alimenta #76 (requisitos de las apps móviles). Los issues #31 y #32 ya se cerraron como cumplidos en la spec 002; el rediseño visual global sigue en #118.
- **Entrada**: "revisa el repo, instalate spec kit y de acuerdo a las issues que Hugo tiene asignadas en el repo, vamos a realizar la spec 004 para continuar el desarrollo."

> **Notas para los comandos de spec-kit.**
> - `RF-###` equivale a *Functional Requirement* (FR-###).
> - `CE-###` equivale a *Success Criterion* (SC-###).
> - `[NECESITA ACLARACIÓN: …]` equivale a *NEEDS CLARIFICATION*.
>
> La spec describe **QUÉ** y **POR QUÉ**. Están prohibidos el stack, la arquitectura, los nombres de archivos, los esquemas de datos, los algoritmos y las firmas de funciones: eso va en `plan.md` y `tasks.md`. Toda la spec se escribe en español.

---

## 1. Contexto y propósito (por qué)

Las specs 001, 002 y 003 dejaron listo el núcleo de PAGO FÁCIL: un cobro CoDi real con pey, aviso de pago con sonido en pantalla, cobros persistidos y demo pública por túnel. Sin embargo, en el uso real de un mostrador (tienditas, fondas, ferreterías, puestos) aparecen dos fricciones inmediatas:

1. **Sumar varios productos fuera de la app.** Hoy el teclado de cobro solo admite un monto único. Cuando un cliente lleva varios artículos (por ejemplo, 3 tacos de $25 y un refresco de $20), el comerciante tiene que sacar otra calculadora o sumar mentalmente antes de teclear el total. Integrar suma y multiplicación directo en el teclado elimina ese paso y reduce errores de cobro.
2. **Vigencia rígida de 10 minutos.** Hoy todo QR CoDi se crea con exactamente 10 minutos de vigencia. Un puesto rápido puede preferir un QR corto (6 minutos), un negocio que manda el cobro o atiende pedidos con demora puede necesitar 30 minutos, 1 hora o 24 horas, y un mostrador fijo necesita un QR sin vencimiento (para imprimirlo o descargarlo y pegarlo junto a la caja) donde cualquier cliente pague durante días sin generar un código nuevo cada vez.

Esta spec define el comportamiento de ambas funciones (**F-03 calculadora** y **F-04 duración del QR**, incluyendo el botón sencillo para descargar la imagen del QR) sobre el servidor y la pantalla web, manteniendo la experiencia de mostrador pensada para celulares desde 320 px de ancho y sirviendo como referencia funcional para las apps móviles (#76).

### 1.1 Glosario

Los términos *negocio*, *dueño*, *cliente*, *cobro*, *pago*, *monto fijo*, *monto libre*, *vigencia*, *ventana de escucha*, *canal de avisos*, *consulta de respaldo*, *aviso de pago de pey*, *cobro en pantalla*, *cobro anterior*, *cobro en escucha*, *vista* y los estados del cobro (*pendiente*, *pagado*, *vencido*, *cancelado*) significan lo mismo que en las [spec 001](../001-backend-mvp/spec.md#11-glosario) y [spec 002](../002-web-mvp/spec.md#11-glosario), ampliados con las definiciones siguientes:

| Término | Significado en esta spec |
|---|---|
| Duración del QR | El tiempo elegido por el negocio durante el cual un QR es vigente para recibir pagos: un plazo finito entre 6 minutos y 24 horas, o *sin vencimiento*. |
| Duración por defecto | 10 minutos. Es la duración seleccionada inicialmente en la pantalla y la que aplica el servidor cuando una solicitud de cobro no indica duración. |
| QR con duración finita | Un cobro cuya vigencia dura entre 6 minutos y 24 horas desde su creación; al cumplirse ese plazo sin pagos pasa a estado *vencido*. |
| QR sin vencimiento | Un cobro creado sin fecha de expiración (corte 2). Nunca pasa a estado *vencido* y su QR permanece pagable de forma indefinida. |
| Expresión de cobro | La cuenta que el dueño arma en el teclado usando números y los operadores `+` y `×` (por ejemplo, `3 × 25 + 20`). |
| Operando | Cada número individual dentro de una expresión de cobro. |
| Operador final | Un signo `+` o `×` escrito al final de la expresión sin un operando posterior (por ejemplo, `25 +` o `3 ×`). |
| Total calculado | El resultado numérico en MXN de evaluar la expresión de cobro, con precedencia de `×` sobre `+` y redondeado a 2 decimales. Es el único monto que la pantalla envía al servidor al cobrar. |

### 1.2 Cortes de entrega (E-9, QA-8)

La spec se aprueba completa, pero se construye en dos cortes para no bloquear la puerta S2 (domingo 29 de noviembre de 2026) mientras entra la actualización de persistencia (#119). Cada historia, escenario, RF y CE lleva su corte: **`[C1]`** o **`[C2]`**.

| Corte | Fecha meta | Qué entrega | Dependencia |
|---|---|---|---|
| **Corte 1 `[C1]`** | Antes del domingo 29 de noviembre de 2026 (puerta S2) | Duraciones finitas del QR (de 6 minutos a 24 horas en servidor y atajos de 6 min, 10 min, 30 min, 1 h y 24 h en pantalla), calculadora completa (`+`, `×`, `⌫`, `C`) con expresión y total en tiempo real, y botón sencillo **Descargar QR**. | Ninguna adicional (opera sobre la persistencia actual de la spec 003). |
| **Corte 2 `[C2]`** | En cuanto entre `#119` (S2–S3) | Opción **Sin vencimiento** para monto fijo y monto libre, con etiqueta "Sin vencimiento" en lugar de cuenta regresiva, ventana de escucha en vivo de 24 horas, aviso en pantalla al terminar esa escucha y registro permanente de avisos firmados de pey. | Actualización de persistencia para admitir cobros sin fecha de vencimiento (#119). |

**Comportamiento temporal del corte 1**, mientras no llega el corte 2. Cada punto deja de valer al entregar el corte 2:

- La opción **Sin vencimiento** no se muestra en el selector de la pantalla.
- El servidor rechaza la duración `0` (sin vencimiento) como duración fuera de rango, aceptando únicamente valores de 6 minutos a 24 horas.

---

## 2. Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Elegir la duración del QR al cobrar (Prioridad: P1) · Corte 1

**Como** dueño de un negocio, **quiero** elegir cuánto tiempo dura el QR antes de generarlo, **para** adaptarlo tanto a ventas rápidas de mostrador como a clientes que tardan más en pagar.

**Por qué esta prioridad:** desbloquea el uso de CoDi más allá de los 10 minutos fijos y cubre los issues #120 y #121 sin requerir cambios de persistencia.

**Prueba independiente:** en la pantalla de cobro, seleccionar 6 minutos (o 30 minutos), escribir `$0.01`, pulsar Cobrar, comprobar que la cuenta regresiva arranca en `06:00` (o `30:00`) y pagar el QR real desde la app de un banco hasta ver "Pago recibido".

**Escenarios de aceptación:**

1. *(C1)* **Dado** la vista Teclado recién abierta, **cuando** el dueño mira el selector de duración, **entonces** ve las opciones **6 min**, **10 min**, **30 min**, **1 h** y **24 h**, con **10 min** seleccionada por defecto.
2. *(C1)* **Dado** que el dueño elige **30 min**, teclea `$0.01` y pulsa Cobrar, **entonces** el servidor crea el QR con vigencia de 30 minutos y la vista QR muestra la cuenta regresiva empezando en `30:00` (con margen máximo de 2 segundos).
3. *(C1)* **Dado** que el dueño elige **24 h** y genera un cobro, **entonces** la vista QR muestra la cuenta regresiva con horas, minutos y segundos (empezando en `24:00:00`, con margen máximo de 2 segundos), incluso si el reloj del celular está desfasado.
4. *(C1)* **Dado** que el dueño elige **6 min** y pulsa **Monto libre**, **entonces** se genera un cobro de monto libre cuya vigencia es de 6 minutos.
5. *(C1)* **Dado** un cobro creado sin indicar duración (por un cliente anterior o sin cambiar la opción), **cuando** el servidor lo procesa, **entonces** aplica 10 minutos por defecto.
6. *(C1)* **Dado** un cobro creado con duración de **1 h**, **cuando** el dueño pulsa **Nuevo cobro**, cancela el cobro o recarga la página, **entonces** el selector en la vista Teclado vuelve a **10 min**.
7. *(C1)* **Dado** que el dueño elige **30 min**, escribe un monto y al pulsar Cobrar el servidor rechaza el cobro o no hay conexión, **entonces** la pantalla vuelve a la vista Teclado conservando **30 min** seleccionada junto con el monto y el concepto.

---

### Historia 2 — Sumar y multiplicar importes antes de cobrar (Prioridad: P1) · Corte 1

**Como** dueño de una tiendita, **quiero** sumar y multiplicar los precios de varios artículos directo en el teclado de cobro, **para** obtener el total y generar el QR sin salir a otra calculadora.

**Por qué esta prioridad:** elimina el mayor punto de fricción en mostrador (#100) y se construye en paralelo con el backend de duración.

**Prueba independiente:** en un celular de 320 px de ancho, armar la cuenta `3 × 0.01 + 0.02 + 0.01` (al menos tres términos), comprobar que se muestra la expresión y el total `$0.06`, pulsar Cobrar y comprobar en la app del banco que el QR CoDi pide exactamente `$0.06`.

**Escenarios de aceptación:**

1. *(C1)* **Dado** la vista Teclado vacía, **cuando** el dueño pulsa `15`, `+`, `22.50`, `+`, `8`, **entonces** ve arriba la expresión `15 + 22.50 + 8` en texto secundario y abajo el total `$45.50` en grande.
2. *(C1)* **Dado** la vista Teclado vacía, **cuando** el dueño pulsa `3`, `×`, `25`, `+`, `20`, **entonces** ve la expresión `3 × 25 + 20` y el total `$95.00` (aplicando `×` antes que `+`).
3. *(C1)* **Dado** la expresión `3 × 25 + 20`, **cuando** el dueño pulsa Cobrar, **entonces** la pantalla pide al servidor un cobro por el monto único `$95.00` y el concepto queda independiente de la expresión.
4. *(C1)* **Dado** que el dueño escribe solo `25.50` sin pulsar `+` ni `×`, **cuando** mira la pantalla, **entonces** ve únicamente `$25.50` en grande, sin repetir una línea de expresión arriba.
5. *(C1)* **Dado** la expresión `25 + 10`, **cuando** el dueño pulsa borrar (`⌫`) tres veces, **entonces** borra `0`, luego `1` y luego el operador `+`, quedando en `$25`.
6. *(C1)* **Dado** la expresión `3 × 25 + 20`, **cuando** el dueño pulsa limpiar todo (`C`), **entonces** la expresión y el total quedan vacíos, Cobrar queda desactivado y Monto libre vuelve a estar activo.
7. *(C1)* **Dado** la expresión `25 +` (operador final sin operando), **cuando** el dueño mira la pantalla, **entonces** ve el total parcial `$25.00` en grande, Cobrar y Monto libre están desactivados, y si pulsa `×` la expresión cambia a `25 ×` (QA-1).
8. *(C1)* **Dado** la expresión `60 + 50` (total `$110.00`, superior al máximo de la demo), **cuando** el dueño pulsa Cobrar y el servidor rechaza el monto, **entonces** la pantalla muestra el mensaje del servidor y conserva la expresión completa `60 + 50` para corregirla.

---

### Historia 3 — Descargar la imagen del QR desde la pantalla (Prioridad: P2) · Corte 1

**Como** dueño, **quiero** descargar la imagen del QR con un toque, **para** guardarla, imprimirla o enviarla cuando lo necesite sin tomar capturas recortadas.

**Por qué esta prioridad:** complementa las duraciones largas y prepara el caso de uso de mostrador del QR sin vencimiento con un esfuerzo mínimo.

**Prueba independiente:** generar un cobro con imagen de QR, pulsar **Descargar QR** y comprobar que el dispositivo guarda un archivo de imagen `.png` con nombre descriptivo, legible por la app de un banco en la opción CoDi.

**Escenarios de aceptación:**

1. *(C1)* **Dado** la vista QR de un cobro que tiene imagen de QR (recién creado, recuperado tras recargar o reabierto con *Mostrar QR otra vez*), **cuando** el dueño pulsa **Descargar QR**, **entonces** el navegador inicia la descarga de la imagen PNG con nombre descriptivo sin salir de la vista QR ni interrumpir la escucha de pagos (QA-6).
2. *(C1)* **Dado** que el navegador impide o falla al guardar el archivo de imagen, **cuando** ocurre, **entonces** la pantalla muestra un mensaje claro para el dueño sin ocultar el QR ni detener la escucha de pagos.

---

### Historia 4 — Crear un QR sin vencimiento para mostrador (Prioridad: P2) · Corte 2

**Como** dueño de un negocio, **quiero** crear un QR sin vencimiento (con monto fijo o monto libre), **para** descargarlo y pegarlo en mi mostrador sin tener que generar uno nuevo cada día.

**Por qué esta prioridad:** aporta un caso de uso muy valorado por comercios pequeños (QR permanente en mostrador), pero depende de la migración de base de datos (#119), por lo que va en el corte 2 para no retrasar el corte 1.

**Prueba independiente:** seleccionar **Sin vencimiento**, generar un cobro de monto libre (o de `$0.01`), comprobar que la pantalla muestra "Sin vencimiento" en lugar de cuenta regresiva, descargarlo, pagarlo desde la app del banco y comprobar que suena y muestra "Pago recibido"; además verificar con reloj controlado que tras 24 horas no pasa a *vencido* y que un pago posterior por aviso firmado de pey se sigue registrando.

**Escenarios de aceptación:**

1. *(C2)* **Dado** la vista Teclado, **cuando** el dueño abre el selector de duración, **entonces** ve además la opción **Sin vencimiento** junto a las duraciones finitas.
2. *(C2)* **Dado** que el dueño elige **Sin vencimiento** y genera un cobro (de monto fijo o de monto libre), **entonces** el servidor crea el QR sin expiración en pey y la vista QR muestra el texto **"Sin vencimiento"** en lugar de la cuenta regresiva.
3. *(C2)* **Dado** un cobro **Sin vencimiento** recién creado, **cuando** transcurren más de 10 minutos o más de 24 horas sin pagos, **entonces** su estado sigue siendo *pendiente* y nunca pasa a *vencido*.
4. *(C2)* **Dado** un cobro **Sin vencimiento**, **mientras** está dentro de sus primeras 24 horas desde la creación, **entonces** mantiene su canal de avisos en vivo, la consulta de respaldo y la recuperación al recargar la página (si se deja como cobro anterior, la escucha en pantalla se acota a 20 minutos, QA-4).
5. *(C2)* **Dado** un cobro **Sin vencimiento** abierto en la vista QR (con o sin pagos previos), **cuando** se cumplen las 24 horas de escucha en vivo, **entonces** el servidor cierra el canal, ejecuta una conciliación final y la pantalla permanece en la vista QR mostrando un aviso de que el QR sigue vigente pero los avisos en vivo en esta pantalla terminaron, con **Descargar QR** y **Nuevo cobro** disponibles y sin **Cancelar cobro** (QA-7).
6. *(C2)* **Dado** un cobro **Sin vencimiento** cuya escucha en vivo de 24 horas ya terminó, **cuando** llega un aviso de pago firmado de pey días después, **entonces** el servidor registra el pago normalmente y actualiza el estado, el número de pagos y el total recibido del cobro.

---

### Historia 5 — Validación de duraciones y recuperación al recargar (Prioridad: P2) · Corte 1 (sin vencimiento: Corte 2)

**Como** equipo y dueño, **queremos** que el servidor rechace duraciones inválidas sin molestar a pey y que al recargar el celular los cobros con duración elegida sigan mostrándose bien, **para** evitar errores y proteger la demo pública.

**Por qué esta prioridad:** garantiza seguridad de entradas en el servidor y coherencia con la recuperación de la spec 002.

**Prueba independiente:** enviar al servidor una solicitud con duración de 5 minutos (300 s), una de 25 horas, una negativa y un valor booleano; comprobar que todas se rechazan con un mensaje en español sin llamar a pey. Además, crear un cobro de 30 minutos, recargar la página y comprobar que recupera la cuenta regresiva correcta.

**Escenarios de aceptación:**

1. *(C1)* **Dado** una solicitud de cobro con duración menor a 6 minutos, mayor a 24 horas, negativa, booleana o no numérica, **cuando** llega al servidor, **entonces** se rechaza con un mensaje para el dueño en español y no se llama a pey ni se guarda el cobro.
2. *(C1)* **Dado** un cobro en pantalla de **30 min** (o un cobro anterior de **1 h**), **cuando** el dueño recarga la página dentro de su ventana de escucha, **entonces** la pantalla recupera el cobro con el tiempo restante correcto.
3. *(C2)* **Dado** un cobro en pantalla **Sin vencimiento** dentro de sus primeras 24 horas, **cuando** el dueño recarga la página, **entonces** la pantalla lo recupera mostrando "Sin vencimiento" y continúa escuchándolo hasta completar las 24 horas.

---

## 3. Requisitos *(obligatorio)*

### 3.1 Requisitos funcionales (notación EARS)

Cada requisito lleva su corte: **`[C1]`** o **`[C2]`** (§1.2).

**Duración del QR en el servidor (#120)**

- **RF-001** (Dirigido por evento) `[C1]`: CUANDO el negocio solicita un cobro sin especificar duración, EL SISTEMA aplicará la duración por defecto de 10 minutos (600 segundos) (E-1).
- **RF-002** (Ubicuo) `[C1]`: EL SISTEMA aceptará como duración finita del QR un número entero de segundos entre 360 (6 minutos) y 86 400 (24 horas), ambos inclusive (E-1).
- **RF-003** (Dirigido por evento) `[C1]`: CUANDO el negocio solicita un cobro con una duración finita válida, EL SISTEMA pedirá a pey el QR con esa vigencia y fijará su vencimiento en la hora de creación más esa duración (E-1).
- **RF-004** (Dirigido por evento) `[C1]`: CUANDO pasan los segundos de la duración elegida desde la creación de un cobro *pendiente* con duración finita, EL SISTEMA lo pasará a estado *vencido* (E-1).
- **RF-005** (Estado) `[C1]`: MIENTRAS un cobro con duración finita está dentro de su vigencia más 10 minutos de gracia posteriores a su vencimiento, EL SISTEMA lo mantendrá dentro de su ventana de escucha (canal de avisos, consulta de respaldo y conciliación al cierre) (E-3).
- **RF-006** (No deseado) `[C1]`: SI la solicitud de cobro incluye una duración que no es un entero válido dentro de los valores permitidos (incluyendo booleanos, decimales o texto no entero), ENTONCES EL SISTEMA rechazará el cobro con un mensaje en español para el dueño sin pedirle nada a pey ni guardar el cobro (E-1, errata 2).
- **RF-007** (Ubicuo) `[C1; sin vencimiento en C2]`: EL SISTEMA devolverá en cada cobro su duración solicitada en segundos (o `0` cuando es sin vencimiento en el corte 2), su hora de vencimiento cuando sea finito y el fin de su ventana de escucha (E-1, E-2, E-3).
- **RF-008** (Dirigido por evento) `[C2]`: CUANDO el negocio solicita un cobro con duración `0` (sin vencimiento), EL SISTEMA pedirá a pey un QR sin expiración y lo guardará sin hora de vencimiento, tanto para monto fijo como para monto libre (E-2).
- **RF-009** (Ubicuo) `[C2]`: EL SISTEMA nunca pasará a estado *vencido* ni emitirá evento de vencimiento para un cobro creado sin vencimiento (E-2, E-3, QA-3).
- **RF-010** (Estado) `[C2]`: MIENTRAS un cobro sin vencimiento está dentro de las 24 horas posteriores a su creación, EL SISTEMA lo mantendrá dentro de su ventana de escucha en vivo (canal de avisos y consulta de respaldo) (E-3).
- **RF-011** (Dirigido por evento) `[C2]`: CUANDO se cumplen 24 horas desde la creación de un cobro sin vencimiento, EL SISTEMA cerrará su canal de avisos y ejecutará la conciliación de fin de ventana una sola vez (E-3).
- **RF-012** (Dirigido por evento) `[C2]`: CUANDO llega un aviso de pago de pey con firma válida para un cobro sin vencimiento después de terminadas sus 24 horas de escucha en vivo, EL SISTEMA registrará el pago sin duplicarlo, pasará el cobro a *pagado* si no tenía pagos y actualizará el número de pagos y el total recibido (Principio VIII, E-3).

**Selector de duración y vista QR en pantalla (#121)**

- **RF-013** (Ubicuo) `[C1]`: EL SISTEMA ofrecerá en la vista Teclado un selector de duración con las opciones predefinidas **6 min**, **10 min**, **30 min**, **1 h** y **24 h** (E-1).
- **RF-014** (Ubicuo) `[C2]`: EL SISTEMA incluirá en el selector de duración de la vista Teclado la opción **Sin vencimiento** (E-2).
- **RF-015** (Ubicuo) `[C1]`: EL SISTEMA seleccionará **10 min** por defecto al abrir la vista Teclado por primera vez (E-1, E-4).
- **RF-016** (Dirigido por evento) `[C1; sin vencimiento en C2]`: CUANDO el dueño pulsa Cobrar o Monto libre, EL SISTEMA enviará al servidor la duración seleccionada en ese momento (E-1, E-2).
- **RF-017** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa Nuevo cobro, confirma una cancelación o recarga la página volviendo a la vista Teclado, EL SISTEMA restablecerá la duración seleccionada a **10 min** (E-4).
- **RF-018** (No deseado) `[C1; sin vencimiento en C2]`: SI el cobro no se crea por rechazo del servidor, falta de conexión o llegada sin imagen del QR, ENTONCES EL SISTEMA conservará la duración seleccionada en la vista Teclado para que el dueño pueda corregir o reintentar (E-4).
- **RF-019** (Estado) `[C1]`: MIENTRAS un cobro en pantalla con duración finita tiene 60 minutos o más restantes, EL SISTEMA mostrará la cuenta regresiva en formato de horas, minutos y segundos (`H:MM:SS`) con un error máximo de 2 segundos respecto a la hora del servidor (E-1).
- **RF-020** (Estado) `[C1]`: MIENTRAS un cobro en pantalla con duración finita tiene menos de 60 minutos restantes, EL SISTEMA mostrará la cuenta regresiva en formato de minutos y segundos (`MM:SS` o `M:SS`) con un error máximo de 2 segundos respecto a la hora del servidor (E-1).
- **RF-021** (Ubicuo) `[C2]`: EL SISTEMA mostrará la etiqueta **"Sin vencimiento"** en la vista QR de un cobro sin vencimiento en lugar de una cuenta regresiva (E-2).
- **RF-022** (Estado) `[C2]`: MIENTRAS un cobro sin vencimiento está en la vista Pago recibido dentro de sus 24 horas de escucha en vivo, EL SISTEMA mostrará el botón **Mostrar QR otra vez**, y al terminar esas 24 horas lo ocultará manteniendo **Nuevo cobro** (E-2, E-3, QA-7).
- **RF-023** (Dirigido por evento) `[C2]`: CUANDO termina la ventana de escucha en vivo de 24 horas de un cobro sin vencimiento que está en la vista QR (con o sin pagos previos), EL SISTEMA dejará de escucharlo, ocultará **Cancelar cobro** y permanecerá en la vista QR mostrando un aviso de que el QR sigue vigente pero los avisos en vivo en esta pantalla terminaron, con **Descargar QR** y **Nuevo cobro** disponibles (E-3, QA-7).
- **RF-024** (Dirigido por evento) `[C1; sin vencimiento en C2]`: CUANDO la página recupera cobros en escucha tras una recarga, EL SISTEMA conservará la duración y el tiempo restante real de cada cobro finito o la condición "Sin vencimiento" de cada cobro permanente dentro de su ventana de escucha (E-1, E-2, E-3).
- **RF-044** (Estado) `[C1; sin vencimiento en C2]`: MIENTRAS un cobro con duración mayor a 1 hora (`24 h` o *sin vencimiento*) pasa a ser un cobro anterior (tras pulsar Nuevo cobro o cancelar), EL SISTEMA acotará su escucha en vivo en pantalla a un máximo de 20 minutos desde que dejó la pantalla, conservando su ventana completa de 24 horas mientras permanezca en pantalla y el registro permanente de pagos por aviso firmado de pey y conciliación (QA-4).

**Descargar imagen del QR (E-5)**

- **RF-025** (Estado) `[C1]`: MIENTRAS la vista QR muestra un cobro con imagen del QR (recién creado, recuperado tras recargar o reabierto con *Mostrar QR otra vez*), EL SISTEMA mostrará un botón **Descargar QR** (E-5, QA-6).
- **RF-026** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa **Descargar QR**, EL SISTEMA descargará la imagen PNG del QR entregada por el servidor con un nombre de archivo `.png` descriptivo basado en PAGO FÁCIL y el cobro (sin caracteres problemáticos), sin cerrar la vista QR ni interrumpir la escucha de pagos (E-5, QA-6).
- **RF-027** (No deseado) `[C1]`: SI el navegador no puede completar la descarga de la imagen del QR, ENTONCES EL SISTEMA mostrará un mensaje claro en español para el dueño sin ocultar el QR ni interrumpir la escucha de pagos (E-5).

**Calculadora en el teclado de cobro (#100)**

- **RF-028** (Ubicuo) `[C1]`: EL SISTEMA ofrecerá en el teclado de la vista Teclado, además de los dígitos `0` a `9`, el punto decimal y borrar un carácter (`⌫`), las teclas de suma (`+`), multiplicación (`×`) y limpiar todo (`C`) (E-6).
- **RF-029** (Dirigido por evento) `[C1]`: CUANDO el dueño escribe números separados por `+` o `×`, EL SISTEMA evaluará la expresión aplicando precedencia de multiplicación (`×`) antes que suma (`+`) y redondeando el total calculado a 2 decimales con redondeo mitad hacia arriba (E-6).
- **RF-030** (Ubicuo) `[C1]`: EL SISTEMA aplicará a cada operando individual las mismas reglas de escritura que a un monto simple: máximo 5 dígitos enteros, máximo 2 decimales, un solo punto decimal, punto inicial como `0.` y sustitución de `0` inicial por el siguiente dígito (E-6, QA-5).
- **RF-045** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa `+` o `×` inmediatamente después de un operando terminado en punto decimal, EL SISTEMA normalizará ese operando quitando el punto sobrante (por ejemplo, `25.` + `+` → `25 +`) (QA-5).
- **RF-046** (No deseado) `[C1]`: SI la expresión de cobro ya contiene 20 operandos y el dueño pulsa `+` o `×`, ENTONCES EL SISTEMA ignorará esa tecla (QA-5).
- **RF-047** (No deseado) `[C1]`: SI el total calculado de la expresión supera `$999,999.99`, ENTONCES EL SISTEMA mostrará el aviso "El total es demasiado grande", mantendrá desactivado el botón **Cobrar** y nunca mostrará notación científica (QA-5).
- **RF-031** (Estado) `[C1]`: MIENTRAS la expresión de cobro contiene al menos un operador (`+` o `×`), EL SISTEMA mostrará la expresión completa en texto secundario encima del total calculado en grande, actualizando ambos tras cada tecla; si termina en un operador final, el total grande mostrará el total parcial calculado hasta antes de ese operador final (E-7, QA-1).
- **RF-032** (Estado) `[C1]`: MIENTRAS la entrada del teclado contiene un único número sin operadores, EL SISTEMA mostrará únicamente ese monto en grande sin línea secundaria de expresión (E-7).
- **RF-033** (No deseado) `[C1]`: SI el dueño pulsa `+` o `×` cuando la pantalla está vacía, ENTONCES EL SISTEMA ignorará esa tecla (E-6).
- **RF-034** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa `+` o `×` inmediatamente después de un operador final, EL SISTEMA reemplazará el operador final por el nuevo operador pulsado (E-8).
- **RF-035** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa borrar un carácter (`⌫`), EL SISTEMA eliminará el último carácter del operando actual o, si la expresión termina en un operador final, eliminará ese operador final (E-6).
- **RF-036** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa limpiar todo (`C`), EL SISTEMA vaciará toda la expresión de cobro y el total calculado (E-6).
- **RF-037** (Estado) `[C1]`: MIENTRAS la expresión de cobro está vacía, termina en un operador final, tiene un total calculado igual a `$0.00` o supera `$999,999.99`, EL SISTEMA mantendrá desactivado el botón **Cobrar** (E-8, QA-1, QA-5).
- **RF-038** (Estado) `[C1]`: MIENTRAS la entrada del teclado contiene algún operador (`+` o `×`, como `"0 × 25"` o `"0 +"`) o tiene un valor numérico mayor a `0`, EL SISTEMA mantendrá desactivada la tecla **Monto libre**; permanecerá activa en cualquier entrada sin operadores cuyo valor numérico sea `0` (`""`, `"0"`, `"0."`, `"0.0"`, `"0.00"`) (E-8, QA-1, ajustado por QP-1 el 2026-11-27).
- **RF-039** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa Cobrar con una expresión completa cuyo total calculado es mayor a `$0.00` y menor o igual a `$999,999.99`, EL SISTEMA enviará al servidor únicamente ese total calculado como monto del cobro y mantendrá el campo de concepto independiente de la expresión (E-8).
- **RF-040** (No deseado) `[C1]`: SI el servidor rechaza el cobro, no responde o devuelve el cobro sin imagen del QR tras usar la calculadora, ENTONCES EL SISTEMA conservará la expresión completa escrita por el dueño en la vista Teclado para que pueda corregirla (E-8).
- **RF-041** (Dirigido por evento) `[C1]`: CUANDO el dueño pulsa Nuevo cobro o se confirma una cancelación, EL SISTEMA limpiará la expresión de cobro completa junto con el concepto (E-6).

**Generales y experiencia de mostrador (F-07 acotado)**

- **RF-042** (Ubicuo) `[C1; sin vencimiento en C2]`: EL SISTEMA permitirá usar el selector de duración, la calculadora (incluida una expresión larga), la cuenta regresiva y el botón Descargar QR sin desplazamiento horizontal de la página en pantallas desde 320 px de ancho (Principio VII).
- **RF-043** (Ubicuo) `[C1; sin vencimiento en C2]`: EL SISTEMA mantendrá todas las comunicaciones con pey exclusivamente en el servidor y mostrará todos los mensajes de validación y error en español redactados para el dueño (Principios III y VII).
- **RF-048** (Ubicuo) `[C1; sin vencimiento en C2]`: EL SISTEMA asignará nombres accesibles en español para lector de pantalla al selector de duración, a las teclas `+`, `×`, `⌫` y `C`, y al botón **Descargar QR** (QA-7).

> Los RF-044 a RF-048 salieron de la revisión QA (`QA-4`, `QA-5` y `QA-7`) y se colocaron en su grupo correspondiente para leerlos junto a los requisitos con los que se relacionan.

### 3.2 Entidades clave

- **Cobro** (extiende la entidad de la spec 001): incorpora la **duración elegida** (en segundos finitos entre 360 y 86 400, o `0` para sin vencimiento en el corte 2), la **hora de vencimiento** (presente en cobros finitos, ausente en cobros sin vencimiento) y el **fin de la ventana de escucha** (vencimiento + 10 minutos en cobros finitos; creación + 24 horas en cobros sin vencimiento).
- **Expresión de cobro** (estado transitorio en la pantalla, no se guarda en el servidor): secuencia alternada de hasta 20 operandos y operadores (`+`, `×`) de la que se deriva el **total calculado** redondeado a 2 decimales (o total parcial si termina en operador final).

---

## 4. Casos límite y manejo de errores

| Caso | Comportamiento esperado | Requisitos |
|---|---|---|
| Duración omitida al crear un cobro | El servidor aplica 10 minutos (600 s) por defecto; compatibilidad total con clientes de las specs 001 y 002. | RF-001 |
| Duración fuera de rango (< 6 min, > 24 h, negativa, decimal, booleana o no numérica; y `0` durante el corte 1) | El servidor la rechaza con un mensaje en español para el dueño, sin llamar a pey ni guardar el cobro. | RF-002, RF-006 |
| QR con duración de 1 h o 24 h y reloj del celular desfasado | La cuenta regresiva se calcula respecto a la hora del servidor en formato `H:MM:SS` con error máximo de 2 s. | RF-019 |
| **Pago tardío** en QR con duración finita (ej. 30 min) | Durante los 10 minutos posteriores al vencimiento el cobro sigue en ventana de escucha, pasa a *pagado* y se avisa igual que un pago a tiempo. Después de esa ventana, un aviso firmado de pey se registra igual en el servidor. | RF-004, RF-005 |
| **Pago tardío** en QR sin vencimiento (después de 24 h) `[C2]` | El QR nunca vence; pasadas las 24 h la pantalla ya no escucha en vivo, pero todo pago confirmado por aviso firmado de pey se registra siempre en el servidor sin duplicarse. | RF-009, RF-011, RF-012 |
| QR sin vencimiento que llega a sus 24 h abierto en pantalla `[C2]` | En vista QR (con o sin pagos) permanece ahí sin pasar a "QR vencido", oculta *Cancelar cobro* y avisa que el QR sigue vigente pero los avisos en vivo terminaron (conserva *Descargar QR* y *Nuevo cobro*). En *Pago recibido* oculta *Mostrar QR otra vez*. | RF-009, RF-022, RF-023 |
| Cobro de 24 h o Sin vencimiento dejado con *Nuevo cobro* o cancelado (cobro anterior) | La pantalla acota su escucha en vivo como cobro anterior a 20 minutos (evita saturar canales, consultas a pey y pantalla encendida 24 h); pagos posteriores siguen registrándose por aviso firmado de pey y conciliación. | RF-044, RF-012 |
| Cancelar un QR sin vencimiento pendiente `[C2]` | Pasa a *cancelado* localmente; su QR sigue pagable en pey, la escucha como anterior dura hasta 20 min en pantalla (el servidor mantiene la ventana de 24 h) y cualquier pago posterior por aviso de pey pasa el cobro a *pagado* y se registra igual. | RF-010, RF-012, RF-044 |
| Corte del túnel en canales de larga duración (> 25 min) | La pantalla muestra "Reconectando…", activa la consulta de respaldo cada 3 s y reintenta abrir el canal según la spec 002 (`RF-030`, `RF-031`, `RF-079`) sin perder pagos. | RF-005, RF-010 |
| **Monto distinto al pedido** (con duración personalizada, sin vencimiento o total de calculadora) | Se mantiene intacta la regla de las specs 001 y 002: se registra, se muestran ambos montos en pantalla y queda advertencia en el servidor. | RF-039 |
| **Fallas de pey** al crear un cobro con duración elegida o calculadora | El servidor responde con el mensaje en español según la causa sin guardar el cobro; la pantalla vuelve a Teclado conservando la duración elegida, la expresión completa y el concepto. | RF-018, RF-040 |
| **Falla del aviso de pey** (no llega) | Dentro de la ventana de escucha (duración + 10 min en finitos; 24 h en sin vencimiento) la consulta de respaldo del servidor y la conciliación final detectan y registran pagos faltantes. | RF-005, RF-010, RF-011 |
| **Devoluciones** | Fuera de alcance: pey no ofrece devoluciones por API; el negocio las realiza desde su banco (se mantiene la regla de la spec 001). | — |
| Recarga de página con cobro de 30 min / 24 h / Sin vencimiento en escucha | Se recupera el cobro con su tiempo restante real o con "Sin vencimiento"; al volver a Teclado el selector arranca en 10 min. | RF-017, RF-024 |
| Descarga de QR fallida o bloqueada por el navegador | Se muestra un mensaje en español para el dueño sin ocultar el QR ni cortar la escucha de pagos. | RF-027 |
| Pulsar `+` o `×` con el teclado vacío | La tecla se ignora. | RF-033 |
| Operando terminado en punto seguido de operador (`25. + 10`) o punto inicial tras operador (`25 + .5`) | `25.` + `+` se normaliza a `25 +`; `25 +` + `.` escribe `25 + 0.`. | RF-030, RF-045 |
| Pulsar operador tras operador (`25 +` luego `×`) | El operador final se reemplaza (`25 ×`), se muestra el total parcial `$25.00`, y Cobrar y Monto libre siguen desactivados hasta escribir otro operando. | RF-031, RF-034, RF-037, RF-038 |
| Multiplicación con resultado de más de 2 decimales (`1.25 × 1.25 = 1.5625` o `1.25 × 1.30 = 1.625`) | Se redondea mitad hacia arriba a 2 decimales (`$1.56` y `$1.63`), mostrando y cobrando exactamente ese total. | RF-029, RF-039 |
| Multiplicación por cero (`0 × 25` o `25 × 0`) | El total calculado es `$0.00`; tanto Cobrar como Monto libre permanecen desactivados; si se suma `+ 10`, pasa a `$10.00` y Cobrar se activa. | RF-029, RF-037, RF-038 |
| Más de 20 operandos o total calculado > `$999,999.99` | Al llegar a 20 operandos se ignoran `+` y `×`. Si el total supera `$999,999.99`, se muestra "El total es demasiado grande", Cobrar queda desactivado y nunca aparece notación científica. | RF-046, RF-047, RF-037 |
| Total de la calculadora supera el máximo de la demo (ej. `60 + 50 = $110` con tope `$100`) | El servidor lo rechaza con su mensaje en español y la pantalla conserva la expresión completa `60 + 50` para editarla. | RF-039, RF-040 |
| Expresión larga (p. ej. 6 o más importes) en pantalla de 320 px | La línea de expresión se ajusta o desplaza internamente sin provocar desplazamiento horizontal de la página ni tapar el total grande. | RF-031, RF-042 |
| Borrar (`⌫`) sobre un punto decimal o sobre un operador final | Borra exactamente el último carácter o el operador final, recalculando el total al instante. | RF-035 |
| Doble toque a Cobrar tras armar una cuenta | Solo se crea un cobro (se mantiene la protección de la spec 002). | RF-039 |

---

## 5. Fuera de alcance *(obligatorio)*

| Fuera de alcance | Dónde se resuelve |
|---|---|
| Notificaciones push y aviso sonoro con la web en segundo plano o pantalla bloqueada | Spec 005 (#22, #122, #123) |
| Anuncio del pago en voz alta (bocina de cobro) | Spec 005 (#124) |
| Cuenta del negocio, inicio de sesión, historial de cobros y corte del día | Spec 006 (#24, #30, #38, #39) |
| Rediseño visual completo de la web (landing, login, dashboard, paleta final) | #118 (y #20, #21) |
| Decisión de arquitectura o migración de framework del front | #115 |
| Implementación de las apps nativas Android e iOS (solo toman esta spec como entrada funcional) | #76, #78–#84 |
| Plantillas diseñadas para imprimir el QR, generación de PDF o botón nativo de compartir | Spec o issue futuro si el equipo lo prioriza |
| Resta (`−`), división (`÷`), paréntesis o memoria en la calculadora | No requerido para mostrador; fuera de #100 |
| Auditoría completa de accesibilidad (zoom al 200 % y WCAG completo) | #42 |
| Enlaces de pago, notificaciones push CoDi, bot de WhatsApp y asistente IA | Spec 007 (#36, #46–#48, #92, #93) |
| Cupones, entregas a domicilio y varias cuentas del titular | Specs 008, 009 y 010 |
| Devoluciones automáticas de pagos | pey no ofrece endpoint de devoluciones; se hacen desde el banco |

---

## 6. Criterios de éxito *(obligatorio)*

- **CE-001** `[C1]`: desde la demo pública, un cobro real de `$0.01` con una duración distinta a 10 minutos (por ejemplo, 6 minutos o 30 minutos) se genera, muestra la cuenta regresiva correspondiente, se paga desde la app de un banco y la pantalla avisa "Pago recibido" de punta a punta.
- **CE-002** `[C1]`: desde la demo pública, el dueño arma una cuenta con al menos tres términos usando `+` y `×` (por ejemplo `2 × 0.01 + 0.01 + 0.01 = $0.04`), genera el QR real y comprueba en la app del banco que solicita el total exacto y avisa el pago al completarse.
- **CE-003** `[C1]`: el 100 % de las solicitudes de cobro con duración fuera del rango permitido (menores a 6 minutos, mayores a 24 horas, negativas, booleanas o no enteras) se rechazan en el servidor con un mensaje en español y cero llamadas a pey, comprobado con pruebas automáticas.
- **CE-004** `[C1]`: el 100 % de las solicitudes de cobro que omiten duración siguen creándose con 10 minutos de vigencia, sin romper pruebas existentes de las specs 001 y 002.
- **CE-005** `[C1]`: en cobros de 1 hora o 24 horas con el reloj del celular desfasado 5 minutos, la cuenta regresiva difiere en menos de 2 segundos respecto al vencimiento real del servidor, comprobado con pruebas automáticas.
- **CE-006** `[C1]`: el botón **Descargar QR** descarga una imagen `.png` válida con nombre descriptivo del QR mostrado sin cerrar la vista QR ni detener la escucha de pagos, comprobado con pruebas automáticas y manuales.
- **CE-007** `[C1]`: desde la demo pública, un cobro con duración elegida o armado con la calculadora muestra el QR en **5 segundos o menos** tras pulsar Cobrar, en 9 de cada 10 intentos (QA-2, alineado con spec 003 `CE-003` / `C-10`).
- **CE-008** `[C1; sin vencimiento en C2]`: en una pantalla de 320 px de ancho, el teclado con calculadora (`+`, `×`, `⌫`, `C`), el selector de duración, la expresión, el total grande y la vista QR con **Descargar QR** se usan sin desplazamiento horizontal de la página.
- **CE-009** `[C2]`: un cobro real de `$0.01` creado con **Sin vencimiento** (y otro de monto libre) muestra "Sin vencimiento" en pantalla, se paga desde la app de un banco y avisa "Pago recibido" de punta a punta.
- **CE-010** `[C2]`: con reloj controlado en pruebas automáticas, un cobro **Sin vencimiento** nunca pasa a estado *vencido*, cierra su canal y concilia a las 24 horas, y registra correctamente un pago recibido por aviso firmado de pey 48 horas después de su creación.

---

## 7. Supuestos y dependencias

**Supuestos**

- **API de pey verificada** (`docs.pey.mx/openapi.json`, versión `2026-10-20`, consultada el 2026-11-26, QA-8): en `POST /codi/qr`, el parámetro `expiration` es un entero con mínimo `0`, valor `0` para sin vencimiento y mínimo `360` segundos (6 minutos) cuando se fija vencimiento, **sin límite máximo documentado**. Se validará en vivo con cobros reales de `$0.01` para 24 h (Corte 1) y para `0` (Corte 2).
- **Túnel en canales largos (QA-8)**: en la spec 003 (`research.md`), Tailscale Funnel se probó con canales de 25 minutos; no está documentado cuánto sostiene un canal SSE continuo de varias horas. Si el túnel corta un canal largo, la reconexión automática y la consulta de respaldo de la spec 002 (`RF-030`, `RF-031`, `RF-079`) mantienen la entrega de avisos sin perder pagos.
- El redondeo estándar a 2 decimales (mitad hacia arriba) es suficiente para multiplicaciones con centavos en un punto de venta mexicano; los montos siguen manejándose sin errores de coma flotante al cobrarse.
- El cálculo de la calculadora se realiza en la pantalla y el servidor continúa recibiendo un único monto final, por lo que F-03 no modifica el contrato de creación de cobros ni exige cambios en el servidor (#100).
- El comportamiento de esta spec es agnóstico a la tecnología visual del front, por lo que sigue siendo válido independientemente de la decisión de arquitectura de `#115` y del rediseño visual de `#118`.

**Dependencias**

| Dependencia | Qué bloquea | Dueño | Estado (2026-11-26) |
|---|---|---|---|
| Base de datos y demo pública funcionando (spec 003) | Corte 1 y Corte 2 | Hugo | Listo (PR #144 unido a `main`) |
| Actualización de persistencia para permitir cobros sin hora de vencimiento (#119) | Únicamente el **Corte 2** (QR sin vencimiento) | Juan (`Altairtm`) | Pendiente (se destraba al aprobar esta spec) |
| Verificación de `expiration` en `docs.pey.mx/openapi.json` | Aprobación en `/qa-spec 004` | Hugo / QA | Verificado en `openapi.json` v`2026-10-20` (sin máximo documentado; pendiente cobro real de `$0.01` en C1 y C2) |

---

## 8. Dudas y decisiones

### 8.1 Entrevista con Hugo (2026-11-26)

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| E-1 | ¿Qué duraciones finitas debe permitir elegir para el QR y cómo debe validarlas el servidor? | Opciones predefinidas en pantalla (**6 min, 10 min por defecto, 30 min, 1 h y 24 h**) y rango acotado en el servidor de **6 min (360 s) a 24 h (86 400 s)**; si se omite duración, usa **10 min (600 s)** para compatibilidad. | RF-001, RF-002, RF-003, RF-004, RF-006, RF-007, RF-013, RF-015, RF-016, RF-019, RF-020 |
| E-2 | ¿Entra la opción de QR **Sin vencimiento** (duración `0`) en la Spec 004? | **Sí entra** (tanto para monto fijo como para monto libre), mostrando `"Sin vencimiento"` en lugar de cuenta regresiva y aceptando la actualización de persistencia en `#119`. | RF-007, RF-008, RF-009, RF-014, RF-016, RF-021, RF-022, RF-024 |
| E-3 | ¿Cuánto dura la ventana de escucha en vivo (canal, respaldo y conciliación) para QR largos y QR sin vencimiento? | **QR finitos**: duración elegida + 10 min de gracia (con conciliación al cierre). **QR sin vencimiento**: **24 horas** de escucha en vivo desde su creación (nunca pasa a *vencido*; al cumplirse las 24 h cierra canal, concilia y avisa en pantalla que el QR sigue vigente pero los avisos en vivo terminaron); después de las 24 h todo pago por aviso firmado de pey se registra siempre. | RF-005, RF-009, RF-010, RF-011, RF-012, RF-022, RF-023 |
| E-4 | Al pulsar *Nuevo cobro*, cancelar o recargar, ¿la pantalla vuelve a 10 min o recuerda la última duración elegida? | **Siempre vuelve a 10 minutos** al iniciar un cobro nuevo, cancelar o recargar, para evitar dejar por descuido `24 h` o `Sin vencimiento`. Si falla la creación del cobro, sí conserva la duración elegida junto con el monto/expresión y concepto para corregir o reintentar. | RF-015, RF-017, RF-018 |
| E-5 | Para el caso de uso de QR en mostrador, ¿se incluye descarga de la imagen del QR? | **Sí**: un botón sencillo **"Descargar QR"** en la vista QR para descargar la imagen PNG que ya entrega el servidor, sin plantillas de impresión ni PDFs. | RF-025, RF-026, RF-027 |
| E-6 | ¿Qué operaciones incluye la calculadora del teclado de cobro (#100)? | **Suma (`+`)**, **multiplicación (`×`)** con precedencia matemática estándar (`×` antes que `+`) y redondeo a 2 decimales, **borrar un carácter (`⌫`)** y **limpiar todo (`C`)**. | RF-028, RF-029, RF-030, RF-033, RF-035, RF-036, RF-041 |
| E-7 | Mientras se arma la cuenta, ¿se muestra el desglose o solo el total? | **Ambos**: la expresión en texto secundario arriba (`3 × 25 + 20`) y el total calculado en grande abajo (`$95.00`), actualizados al instante. Si solo se teclea un número sin operadores, se ve igual que hoy (sin línea repetida). | RF-031, RF-032 |
| E-8 | ¿Cómo se comporta la calculadora con un operador colgando al final y ante un rechazo del servidor? | Con operador final colgando (`25 +` o `3 ×`), **Cobrar** queda desactivado; pulsar el otro operador reemplaza el final (`25 +` → `25 ×`). Si el servidor rechaza el total, se conserva toda la expresión (`60 + 50`) para corregirla. Concepto independiente y **Monto libre** desactivado si hay expresión o monto. | RF-034, RF-037, RF-038, RF-039, RF-040 |
| E-9 | ¿Cómo se organizan los cortes de entrega considerando la puerta S2 (29 nov) y la migración `#119`? | **Dos cortes** dentro de la spec aprobada completa: **Corte 1** entrega duraciones finitas (`6 min` a `24 h`), calculadora completa (`#100`) y "Descargar QR" sin esperar migración; **Corte 2** suma **"Sin vencimiento"** en cuanto entre `#119`. | §1.2 (todos los RF y CE etiquetados `[C1]`/`[C2]`) |

### 8.2 Cambios a otras specs

*(El último cambio registrado en `main` es `C-11` del PR #146. `C-12`, `C-13` y `C-14` se aplicarán en las specs afectadas durante la ejecución de las fases correspondientes.)*

| # | Spec | Cambio propuesto | Origen | Estado |
|---|---|---|---|---|
| C-12 | 001 | Ampliar la vigencia fija de 10 minutos (`RF-006`, `RF-021`, `RF-030`, `§1.1`, `§4`, `§5`) para aceptar duración configurable de 6 minutos a 24 horas en el corte 1 (por defecto 10 minutos, manteniendo gracia de +10 min en `RF-022`/`RF-025`/`RF-032`) y duración `0` sin vencimiento en el corte 2 (sin expiración, sin evento `vencido`, ventana de escucha en vivo de 24 h y registro permanente de avisos firmados). Ampliar `RF-008` con la duración del cobro y la hora de vencimiento opcional (ausente en cobros sin vencimiento). | E-1, E-2, E-3, E-9, QA-3 | Aprobado · sin aplicar (2026-11-26) |
| C-13 | 002 | Ampliar el teclado (`RF-001`–`RF-004`, `RF-006`, `RF-008`, `RF-009`, `RF-014`, `RF-042`, `RF-048`, `RF-065`–`RF-068`) para soportar la calculadora por operando (`+`, `×`, `⌫`, `C`, expresión secundaria y total grande, conservación de expresión en error) y el selector de duración en Cobrar y Monto libre con reinicio a 10 min; ampliar la vista QR y la escucha (`RF-018`, `RF-035`, `RF-043`, `RF-051`, `RF-069`, `RF-071`, `§4`, `§5`) con formato `H:MM:SS` desde 60 min, acotado de 20 min para cobros anteriores > 1 h (`QA-4`), etiqueta `"Sin vencimiento"` con aviso al fin de 24 h (corte 2) y botón **Descargar QR**. | E-1 a E-9, QA-1, QA-3, QA-4, QA-5, QA-6, QA-7 | Aprobado · sin aplicar (2026-11-26) |
| C-14 | 003 | Ampliar `RF-001`, `RF-006` y `RF-018` para incluir en el guardado y las migraciones (`#119`) la duración del cobro y permitir cobros sin hora de vencimiento (`expira_en` ausente) en el corte 2, manteniendo `fin_ventana` obligatoria (24 h desde la creación) para la conciliación de `RF-061`. | E-2, E-3, QA-3 | Aprobado · sin aplicar (2026-11-26) |

### 8.3 Propuestas

*Sin propuestas pendientes en este momento.*

### 8.4 Revisión QA (2026-11-26, una sola pasada)

| # | Tipo | Hallazgo | Requisitos | Recomendación | Decisión |
|---|---|---|---|---|---|
| QA-1 | Contradicción / Ambigüedad | (a) `RF-038` activaría *Monto libre* con expresiones como `0 × 25` o `0 +` (no vacías pero con total `$0.00`). (b) `RF-031`/`RF-037` no definen qué muestra el total grande mientras hay un operador final colgando (`25 +`, `3 ×`). | RF-031, RF-037, RF-038 | (a) Mantener *Monto libre* desactivada ante cualquier expresión con operadores o monto distinto de vacío/`"0"` simple. (b) Mostrar en grande el total parcial calculado antes del operador final, manteniendo *Cobrar* desactivado. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. *(Ajuste posterior: `RF-038` se ajustó el 2026-11-27 por `QP-1` del plan para conservar compatibilidad con `"0."` y `"0.00"` de la spec 002, manteniendo Monto libre activo en cualquier entrada sin operadores con valor `0`.)* |
| QA-2 | Contradicción | `CE-007` promete el QR en menos de 3 s, pero `spec 003` (`CE-003`, cambio `C-10`) ya relajó esa meta a **5 segundos o menos en 9 de cada 10 intentos** desde la demo pública. | CE-007 | Alinear `CE-007` con `spec 003 CE-003` (`C-10`): 5 segundos o menos en 9 de cada 10 intentos desde la demo pública. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |
| QA-3 | Hueco | En `§8.2` faltan RF afectados en `C-12` (`RF-030` de la 001; `backend/app/canal.py:22,86`), en `C-13` (`RF-003`, `RF-004`, `RF-008`, `RF-009`, `RF-048`, `RF-066`–`RF-068` de la 002; `web/js/teclado.js`, `app.js:198`, `cuenta.js:26-43`) y falta proponer `C-14` para la spec 003 (`RF-001`, `RF-006`, `RF-018` por `expira_en` anulable en Corte 2 / `#119`). | §8.2, RF-008, RF-016, RF-017, RF-024, RF-030 | Completar `C-12` y `C-13` con esos RF y añadir `C-14` (Propuesto) para la spec 003 (Corte 2 / `#119`), para aprobación separada. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |
| QA-4 | Seguridad / Rendimiento | `web/js/escucha.js:306-441` mantiene cobros anteriores con hasta 3 canales SSE + polling cada 3 s (`backend/app/main.py:354`) y Wake Lock (`spec 002 RF-058`). Dejar un QR de 24 h o Sin vencimiento como anterior durante 24 h dispararía ~28 800 consultas/día a pey (riesgo de `429 CALL_LIMIT_REACHED`), saturaría los 10 canales por IP (`RF-041`) y dejaría la pantalla encendida 24 h. | RF-005, RF-010, RF-024, RF-044, §4 | Para cobros > 1 h (`24 h` y `Sin vencimiento`), acotar la escucha como cobro anterior (tras *Nuevo cobro* o cancelar) a **20 minutos**, manteniendo las 24 h completas mientras estén en pantalla y el registro permanente por aviso firmado de pey y conciliación. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |
| QA-5 | Ambigüedad / Caso límite | La calculadora (`RF-029`, `RF-030`) no fija normalización de punto final/inicial en operandos (`25. + 10`, `25 + .5`), tope de operandos ni protección contra desbordamiento/notación científica (`99999 × 99999 × …`). | RF-029, RF-030, RF-033, RF-045, RF-046, RF-047, §4 | Normalizar `25.` + operador → `25 +` y operador + `.` → `0.`; tope de **20 operandos** por expresión; sobre `$999,999.99` mostrar `"El total es demasiado grande"` con *Cobrar* desactivado (nunca notación científica). | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |
| QA-6 | Hueco | `RF-025`/`RF-026` (*Descargar QR*) no precisa su disponibilidad tras recargar la página o tras *Mostrar QR otra vez* (posible por `spec 003 RF-010`) ni el criterio de nombre del archivo `.png`. | RF-025, RF-026, CE-006 | Aclarar que *Descargar QR* aparece siempre que la vista QR muestre imagen (también tras recarga y *Mostrar QR otra vez*) y descarga un `.png` con nombre descriptivo basado en PAGO FÁCIL y el cobro. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |
| QA-7 | Caso límite / Ambigüedad | Al cumplirse las 24 h de escucha de un QR sin vencimiento (`RF-022`, `RF-023`), no se define el comportamiento si se había reabierto desde *Pago recibido* ni si desaparece *Cancelar cobro*; tampoco se piden nombres accesibles en español para lector de pantalla en los controles nuevos. | RF-022, RF-023, RF-042, RF-048 | Al terminar las 24 h: en vista QR (con o sin pagos) permanece ahí con el aviso de fin de escucha, *Descargar QR* y *Nuevo cobro*, ocultando *Cancelar cobro*; en *Pago recibido* oculta *Mostrar QR otra vez*. Añadir nombres accesibles en español para los controles nuevos. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |
| QA-8 | API de pey / Construibilidad | `docs.pey.mx/openapi.json` (v`2026-10-20`) confirma `expiration` entero `0` o `>= 360`, sin máximo documentado. Falta anotar en `§1.2` la meta del Corte 1 (puerta S2, 29 nov) y en `§7`/`§4` que si Tailscale Funnel (probado 25 min en `spec 003`) corta un canal largo, la reconexión y consulta de respaldo de la 002 cubren los avisos. | §1.2, §4, §7 | Actualizar `§7` con la confirmación real de `openapi.json` (verificando 24 h y `0` con cobros reales de `$0.01`) y la mitigación de túnel en canales largos, y agregar fecha meta del Corte 1 (antes del domingo 29 nov) en `§1.2`. | **Aceptada** (Hugo, 2026-11-26), como se recomienda. Aplicada el 2026-11-26. |

**Bloques de la pasada:**
1. **Coherencia interna**: glosario, `RF-001`–`RF-043`, `CE-001`–`CE-010`, `E-1`–`E-9` y `C-12`–`C-13` (siguiente libre tras `C-11` del PR #146). Salen `QA-1` y `QA-5`.
2. **Otras specs, plan del hackathon, reglas e issues**: revisados RF citados de specs 001, 002 y 003, `docs/plan-hackathon.md`, reglas del hackathon e issues `#132`, `#120`, `#100`, `#121`, `#119` (`#31`/`#32` cerrados). Salen `QA-2` y `QA-3`.
3. **Código (solo lectura)**: revisados `backend/app/main.py`, `cobros.py`, `canal.py`, `almacen_postgres.py`, `tareas.py`, `config.py`, `supabase/migraciones/0001_esquema_inicial.sql` y `web/js/app.js`, `vistas.js`, `teclado.js`, `cuenta.js`, `escucha.js`, `memoria.js`, `web/index.html`; `ruff` en verde (`39 files`); `pytest` pendiente de `uv sync` por `psycopg==3.3.8`. Salen `QA-3`, `QA-4`, `QA-6` y `QA-7`.
4. **API de pey**: consultado `https://docs.pey.mx/openapi.json` (v`2026-10-20`): `POST /codi/qr` admite `expiration` entero `0` o `>= 360`, sin máximo documentado; existe `429 CALL_LIMIT_REACHED`. Salen `QA-4` y `QA-8`.
5. **Fuentes y dependencias externas**: `spec 003` lista, `#119` (Juan) solo bloquea Corte 2, Tailscale Funnel probado 25 min (`spec 003 research.md`). Sale `QA-8`.
6. **Ambigüedades y casos límite**: cubiertos los 4 obligatorios del Principio VIII, estados de pantalla, 320 px, lector de pantalla, recarga y bordes de calculadora. Salen `QA-1`, `QA-5`, `QA-6` y `QA-7`.
7. **Seguridad y rendimiento**: sin secretos, validación de duración antes de pey, `C-11` intacto, CSP compatible con PNG base64; riesgo de polling/canales con QR de 24 h. Salen `QA-2` y `QA-4`.
8. **Construibilidad y reparto**: puerta S2 el 29 nov, reparto Hugo (`#120`), Leonel (`#100`, `#121`), Juan (`#119`), cortes C1/C2 desacoplados. Sale `QA-8`.

**Erratas** *(corregidas el 2026-11-26)*:
1. *(Corregida)* En `§8.1` fila `E-2` se cambió `expiration = 0` por `duración 0` (dejando el nombre del parámetro de pey solo en `§7 Supuestos`).
2. *(Corregida)* En `§4` y `RF-006` se añadió explícitamente `"booleana"` junto a `"negativa, decimal o no numérica"`.

### 8.5 Pendientes

*Sin marcas `[NECESITA ACLARACIÓN]` abiertas.*

---

## 9. Criterios de finalización

- [x] Revisión `/qa-spec 004` ejecutada en una sola pasada y todos los hallazgos QA (`QA-1` a `QA-8`) decididos y aplicados por Hugo.
- [x] Cambios `C-12`, `C-13` y `C-14` aprobados por separado por Hugo (pendientes de aplicar en sus fases correspondientes).
- [ ] Cada RF (`RF-001` a `RF-048`) tiene al menos una prueba automática o un paso de verificación manual en el plan y las tareas.
- [ ] Todos los criterios de éxito (`CE-001` a `CE-010`) están comprobados (incluidos los cobros reales de `$0.01` de Corte 1 y Corte 2).
- [x] No quedan marcas `[NECESITA ACLARACIÓN]` abiertas.
- [ ] Revisión de seguridad realizada: validación de duración en servidor, secretos fuera de la web y del repositorio, firma de webhooks intacta y expresión de calculadora tratada solo como texto seguro.
