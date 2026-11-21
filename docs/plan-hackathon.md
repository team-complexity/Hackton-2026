# Plan del hackathon — PAGO FÁCIL

Plan general del proyecto para el **Hackatón México 2026**. Cada issue del repositorio enlaza a este documento.

Fuente de las reglas: [hackatonmexico.com/reglas](https://hackatonmexico.com/reglas) (versión del 4 de noviembre de 2026). Documentación del API: [docs.pey.mx](https://docs.pey.mx). Si algo de aquí contradice las reglas oficiales, mandan las reglas.

## 1. La idea

Un **punto de venta sencillo para negocios** que cobra con CoDi:

- El negocio escribe el monto → aparece un **QR CoDi**.
- El cliente lo escanea con **la app de su banco** y paga. No necesita instalar PAGO FÁCIL.
- Cuando el pago llega, la pantalla del negocio **suena** y muestra **"Pago recibido"**.
- *(Opcional)* Bot de WhatsApp para cobrar escribiendo "cobra 150 tacos" y recibir el aviso "Te pagaron $150".

**Por qué gana el negocio:** CoDi no cobra comisión por transacción y el dinero llega al instante, mientras una terminal de tarjeta cobra alrededor del 3.5 %.

## 2. Fechas clave (hora CDMX)

| Fecha | Qué pasa |
|---|---|
| 14 nov 2026 | Arranque y kickoff presencial (opcional) |
| **15 nov, 1:00 PM** | **Entrega del kickoff (formulario de Luma): nombre y descripción, repo público, app en vivo, video opcional y correos** |
| ≤ 30 nov | Publicación de bounties de patrocinadores |
| **10 dic, 23:59** | Cierre de postulación (último día para cambiar integrantes) |
| **12 dic, 23:59** | **Cierre de entregas, sin prórroga** |
| 12–14 dic | Evaluación (puede haber demo en vivo de hasta 20 min) |
| 14 dic | Resultados |
| 31 ene 2027 | Fecha sugerida para mantener accesibles demo, video y repo |

## 3. Requisitos obligatorios

- Generar **al menos un cobro CoDi real** con el API de pey y **reaccionar a su resultado** (webhook). No vale simularlo.
- Funcionar en el **ambiente de producción** de pey.
- Integración construida entre el 14 nov y el 12 dic. Lo hecho antes se declara.
- Equipo de **1 a 5 personas**. Para ser más hace falta autorización escrita.
- La API key va a nombre de un integrante **mayor de edad**, y para producción la integradora debe ser persona moral o persona física con actividad empresarial, con una CLABE a su nombre.
- La API key **nunca** va en un repo público ni en código del cliente.

**Entregables:** descripción (máx. 500 palabras), demo pública por enlace, video (máx. 3 min) con el flujo completo del cobro, instrucciones de prueba (máx. 1000 palabras), declaración de componentes previos o de terceros, y lista de integrantes. El repositorio es opcional.

## 4. Cómo nos evalúan

| Criterio | Peso | Qué hacemos para sumar |
|---|---|---|
| Uso de CoDi y del API de pey | **30 %** | QR + webhook + enlace de pago o push. Reacción visible y sonora |
| Impacto y relevancia | 25 % | Negocios pequeños, cero comisiones, pilotos reales |
| Ejecución técnica | 15 % | Código limpio, firma de webhooks verificada, sin secretos expuestos |
| Experiencia y diseño | 15 % | El "momento del pago": QR claro, sonido y animación |
| Originalidad | 15 % | Bot de WhatsApp *(opcional)*, cupones en el cobro |

## 5. Arquitectura

```
[Web PWA del negocio] ──HTTPS──> [Backend FastAPI] ──> [API de pey] ──> CoDi / Banxico
        ▲                              │   ▲
        └──── aviso en tiempo real ────┘   └── webhook codi.qr.payment_received
                                       │
                                  [Base de datos]
                                       │
                       (opcional) [WhatsApp Cloud API]
```

- **Backend:** Python + FastAPI. Es el único que conoce la API key.
- **Web:** HTML, CSS y JS como PWA, instalable en Android, iPhone y computadora.
- **Apps nativas** (decisión del 15 nov): una app Android (Miguel) y una app iOS (Juan), sobre el mismo backend. La demo que se evalúa sigue siendo el enlace web.
- **Seguridad:** firma de webhooks, secretos en variables de entorno, HTTPS y validación de entradas.

Endpoints de pey que usaremos:

- `POST /codi/qr`: crear el QR (monto, concepto, expiración, referencia).
- Webhook `codi.qr.payment_received`: confirma el pago (monto, `codiQrId`, `transactionId`, `datePaid`…).
- Enlaces de pago y `POST /codi/push`: cobrar a distancia (por WhatsApp o al teléfono del cliente).

No hay sandbox: se prueba en producción con cobros de **$0.01 MXN**.

## 6. Organización en GitHub

| Dimensión | Herramienta | Valores |
|---|---|---|
| Área | Épicas + etiqueta `area:` | frontend, ux-ui, backend, base-de-datos, integraciones, seguridad, devops, producto |
| Tiempo | Milestones | M0–M4 |
| Tipo | Etiqueta `tipo:` | funcionalidad, tarea, investigación, documentación, bug |
| Urgencia | Etiqueta `prioridad:` | alta, media, baja |
| Extras | Etiqueta `opcional` | Bot de WhatsApp, pitch deck… |

### Milestones

> **Actualización del 15 nov.** El calendario vigente, con roles, entregables por persona y el reparto de los issues, está en [flujo-de-trabajo.md](../flujo-de-trabajo.md): el desarrollo termina el 10 de diciembre y el 11 y el 12 son solo para ajustes. La tabla siguiente es el plan original; los milestones de GitHub ya llevan los nombres y fechas nuevos (S1 a S4 y "Ajustes y entrega").

| Milestone | Fechas | Meta |
|---|---|---|
| M0 — Entrega kickoff | 14–15 nov (1:00 PM) | MVP en vivo (QR + webhook + sonido) con la CLABE de prueba de pey, repo público y formulario de Luma enviado |
| M1 — Arranque y cuenta pey | 14–20 nov | Equipo, titular de la API key, cuenta CoDi en trámite, entorno y diseño |
| M2 — Cobro CoDi funcionando | 21 nov–1 dic | QR real, webhook, sonido y aviso visual, desplegado con HTTPS |
| M3 — Extras y monetización | 2–7 dic | Cupones, historial, Premium, pilotos, *(opcional)* bot de WhatsApp |
| M4 — Entrega | 8–12 dic | Revisión de seguridad, video, textos, postulación y demo congelada |

### Flujo de trabajo

1. Toma un issue y asígnatelo.
2. Crea una rama `feature/<número>-<descripcion-corta>`.
3. Abre un pull request que diga `Closes #<número>` y documenta lo que hiciste con la [plantilla de pull request](../.github/pull_request_template.md).
4. Únelo tú a `main` cuando el CI esté en verde y cumpla los criterios de aceptación.
5. Juan y Leonel revisan lo que entra a `main` y avisan si algo salió mal.

El detalle está en [flujo-de-trabajo.md](../flujo-de-trabajo.md).

## 7. Decisiones pendientes

- [ ] Titular de la API key de pey (requisitos de la sección 3).
- [x] Integrantes oficiales: Hugo, Juan y Miguel (15 nov).
- [x] Responsables de cada área: ver [flujo-de-trabajo.md](../flujo-de-trabajo.md) (15 nov).
- [x] Base de datos y hosting: Supabase y AWS (15 nov).
- [ ] Tecnología de la landing, de la app Android y de la app iOS; uso de MongoDB; librerías de QR.

## 8. Monetización (para el pitch)

- **Freemium:** gratis QR + sonido. Premium (~$99–199/mes) con bot de WhatsApp, varias cajas, reportes y corte de caja.
- **Cupones y promos pagados por marcas** en el momento del cobro.
- **Lealtad / cashback** financiado por el negocio o la marca.
- **Plan para cadenas** con varias sucursales.

No se revende el acceso al API de pey (lo prohíben las reglas): PAGO FÁCIL es un punto de venta que lo integra.
