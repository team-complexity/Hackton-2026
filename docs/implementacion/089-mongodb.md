# Nota de implementación #89: ¿para qué se usa MongoDB?

- **Issue**: #89 (épica #4, Base de datos)
- **Fecha**: 2026-11-17
- **Decide**: Juan (base de datos), con la comparativa del principio IX
- **Relacionado**: #23 (tablas en Supabase, PR #97), #90 (guardar cobros en Supabase), #94 (de dónde sale la imagen del QR)

## Decisión

**MongoDB no entra al proyecto.** Todos los datos de PAGO FÁCIL se guardan en Supabase (PostgreSQL).

Si más adelante hace falta guardar archivos (por ejemplo, imágenes), se usa **Supabase Storage**, que viene en el mismo proyecto.

## Qué se pensaba guardar en MongoDB

El primer candidato era la **imagen del QR** (`qr_imagen`, un PNG en base64 que pey entrega si se pide `generateImage: true`).

## Por qué no hace falta guardar la imagen del QR

1. **Se puede volver a dibujar.** La imagen sale del texto `qrString`, que ya se guarda en `cobros.qr`. Con el mismo texto se obtiene el mismo QR, en el backend o en la pantalla (#94 compara la imagen de pey, `qrcode` y `segno`).
2. **Solo sirve unos minutos.** Un QR vence a los 10 minutos (más la ventana de gracia). Después nadie lo vuelve a escanear; el historial solo necesita monto, concepto, estado y pagos.
3. **Pey puede no mandarla.** La imagen puede llegar vacía (spec 002, DP-2 y C-3), así que el sistema ya tiene que funcionar sin ella.
4. **Pedirla es lento.** Crear un cobro con imagen tardó entre 2.39 s y 9.09 s (plan 001, TK-5). Si se dibuja aparte, ni siquiera hace falta pedírsela a pey.

## Comparativa

| | **A. Todo en Supabase** (recomendada) | **B. Supabase + MongoDB** |
|---|---|---|
| Qué guarda | Tablas de #23; la imagen no se guarda (o va a Supabase Storage si algún día hace falta) | Tablas en Supabase; imágenes del QR en MongoDB |
| Ventajas | Una sola base, una sola credencial, una sola copia de seguridad. Los pagos, cobros y cupones viven juntos y se consultan con SQL. Ya está creada y probada (PR #97) | Guarda documentos sueltos sin esquema fijo |
| Desventajas | Ninguna para lo que necesita la demo | Otra cuenta, otra credencial en el backend que proteger (principio III), otra conexión que puede fallar y otra pieza que desplegar. Guarda algo que se puede regenerar |
| Curva de aprendizaje | Ya la conoce el equipo: el esquema está hecho | Hay que aprender MongoDB y su driver de Python, y probarlo sin la base real (principio V) |
| Costo | Plan gratis de Supabase | Plan gratis de MongoDB Atlas, pero con más trabajo de mantenimiento |
| Riesgo para la demo | Bajo | Más piezas que se pueden romper antes del 12 de diciembre |

## Recomendación

**Opción A.** Cumple el principio IX ("lo más simple que gane la demo"): no se agrega una pieza que ninguna spec justifica. La imagen del QR se resuelve en #94 dibujándola desde `qrString`, sin guardarla.

## Cuándo se podría reconsiderar

Solo si aparece un dato que no encaja en tablas y que una spec justifique. Por ejemplo, un historial de conversaciones del chatbot (#92) con estructura muy variable. Aun así, primero se probaría con una columna `jsonb` en Supabase.

## Qué sigue

- No se crea issue de construcción: MongoDB no entra.
- #94 decide cómo se dibuja el QR (imagen de pey, `qrcode` o `segno`).
- #90 conecta el backend a Supabase con las tablas de #23.
