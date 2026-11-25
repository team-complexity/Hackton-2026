# Contrato: vistas de la pantalla

## 1. Propósito

Lo que ve y toca el dueño en cada vista, y los atributos `data-prueba` que usan las pruebas (DP-14). Los textos entre comillas son los que exige la spec. Los demás son orientativos y se pueden pulir sin cambiar este contrato, salvo que una prueba los use.

## 2. Requisitos

RF-001 a RF-078 (cada fila cita los suyos).

## 3. Elementos comunes

| Elemento | `data-prueba` | Requisitos |
|---|---|---|
| Nombre "PAGO FÁCIL", en todas las vistas | `marca` | RF-060 |
| Aviso "Reconectando…" (sobre las vistas del cobro en pantalla) | `reconectando` | RF-032 |
| Aviso «Toca para activar el sonido» al recuperar cobros o si el navegador rechaza el aviso sonoro | `activar-sonido` | RF-054 |
| Aviso de pago de un cobro anterior (C2): monto recibido y concepto; se cierra al tocarlo | `aviso-anterior` | RF-045, RF-075 |

## 4. Vistas

### Teclado (`data-prueba="vista-teclado"`)

| Elemento | `data-prueba` | Comportamiento | Requisitos |
|---|---|---|---|
| Monto en grande con "$" | `monto` | Muestra el texto tecleado tal cual ("$25.", "$0.") | RF-002 |
| Teclas 0 a 9 | `tecla-0` … `tecla-9` | `aplicar_tecla` | RF-001, RF-003, RF-066, RF-068 |
| Tecla punto | `tecla-punto` | `aplicar_tecla` | RF-001, RF-004, RF-067 |
| Tecla borrar | `tecla-borrar` | Quita el último carácter | RF-001 |
| Campo concepto (`maxlength="40"`) | `concepto` | Opcional; abre el teclado del sistema solo al tocarlo | RF-005 |
| Botón "Cobrar" | `cobrar` | Desactivado si el monto está vacío o vale 0 | RF-006, RF-009, RF-011 |
| Botón "Monto libre" (C2) | `monto-libre` | Desactivado si hay un monto mayor a 0 | RF-007, RF-008, RF-065 |
| Mensaje de error | `mensaje` | Texto del servidor, "No hay conexión con el servidor. Revisa tu internet e intenta de nuevo." o "No se pudo mostrar el QR. Intenta de nuevo." (RF-078). Se borra al teclear | RF-012, RF-013, RF-078 |

### Generando QR (`data-prueba="vista-generando"`)

| Elemento | `data-prueba` | Comportamiento | Requisitos |
|---|---|---|---|
| Texto "Generando QR…" con indicador de carga | `generando` | Aparece en menos de 0.1 s después del toque | RF-010, CE-005 |

### QR (`data-prueba="vista-qr"`)

| Elemento | `data-prueba` | Comportamiento | Requisitos |
|---|---|---|---|
| Imagen del QR (`qr_imagen`) | `qr` | Al menos el 70 % del ancho; `image-rendering: pixelated` | RF-015, CE-007 |
| Monto pedido o "Monto libre" | `qr-monto` | — | RF-016 |
| Concepto | `qr-concepto` | Solo texto | RF-016, RF-077 |
| "Escanéalo desde la app de tu banco, en la opción CoDi" | `indicacion-codi` | Siempre visible | RF-017 |
| Cuenta regresiva `m:ss` | `cuenta` | Con la hora del servidor | RF-018, RF-019 |
| Botón "Cancelar cobro" (C2) | `cancelar` | Solo con el cobro *pendiente*; mientras cancela muestra "Cancelando…" y no responde | RF-046, RF-047, RF-072, RF-073 |
| Mensaje de cancelación rechazada (C2) | `mensaje-cancelar` | Texto del servidor o de conexión | RF-050 |
| Botón "Nuevo cobro" | `nuevo-cobro` | — | RF-041, RF-042 |

### QR vencido (`data-prueba="vista-vencido"`)

| Elemento | `data-prueba` | Comportamiento | Requisitos |
|---|---|---|---|
| Título "QR vencido" (sin imagen del QR) | `vencido` | — | RF-035, RF-036 |
| Monto pedido o "Monto libre", y concepto | `vencido-monto`, `vencido-concepto` | — | RF-037 |
| "Si el cliente ya pagó, aquí te avisamos" | `vencido-espera` | Solo dentro de la ventana de escucha | RF-038 |
| Botón "Nuevo cobro" | `nuevo-cobro` | — | RF-041 |

### Pago recibido (`data-prueba="vista-pagado"`, fondo verde a pantalla completa)

| Elemento | `data-prueba` | Comportamiento | Requisitos |
|---|---|---|---|
| "Pago recibido" | `pagado` | — | RF-023 |
| Monto recibido del último pago | `pagado-monto` | — | RF-023 |
| Concepto | `pagado-concepto` | Solo texto | RF-023, RF-077 |
| Monto pedido y monto recibido, si es distinto | `pagado-distinto` | Solo si el pago trae `monto_distinto` | RF-028 |
| "Pago n" y total recibido (C2) | `pagado-numero`, `pagado-total` | Desde el segundo pago | RF-027 |
| Botón "Mostrar QR otra vez" (C2) | `mostrar-qr` | Solo mientras el QR siga vigente | RF-069, RF-070 |
| Botón "Nuevo cobro" | `nuevo-cobro` | La vista se queda hasta este toque (o Mostrar QR otra vez) | RF-026, RF-041 |

### Error (`data-prueba="vista-error"`)

| Elemento | `data-prueba` | Comportamiento | Requisitos |
|---|---|---|---|
| Mensaje "Este cobro ya no se puede seguir. Revisa la app de tu banco para confirmar si llegó el pago." | `error` | — | RF-057 |
| Botón "Nuevo cobro" | `nuevo-cobro` | — | RF-041 |

## 5. Ejemplo

Prueba que crea un cobro de $25.50 y espera la vista QR:

```text
tocar tecla-2, tecla-5, tecla-punto, tecla-5, tecla-0 → monto = "$25.50"
tocar cobrar → vista-generando visible
el servidor simulado responde 201 con imagen → vista-qr visible, qr-monto = "$25.50", cuenta = "10:00"
```

## 6. Seguridad

- Todo texto que viene del servidor o del almacenamiento se pone con `textContent` (RF-077, DP-13).
- La imagen del QR solo acepta `data:image/png;base64,` con el contenido del campo `qr_imagen`. La política de seguridad de contenido solo permite imágenes del propio sitio y `data:`.
- La política de seguridad de contenido permite el sonido en `blob:` y las conexiones al servidor configurado (R-11, QP-2).
