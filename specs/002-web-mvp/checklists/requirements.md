# Checklist de calidad de la spec: 002 Web del MVP

**Propósito**: comprobar que la spec está completa y bien escrita antes de la entrevista, la QA y el plan.
**Creado**: 2026-11-15
**Spec**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, frameworks, rutas, esquemas)
- [x] Centrada en el valor para el negocio y en sus necesidades
- [x] Escrita para personas no técnicas
- [x] Todas las secciones obligatorias completas

## Requisitos completos

- [x] No quedan marcas `[NECESITA ACLARACIÓN]` (resueltas en la entrevista del 2026-11-15: E-3, E-4 y E-5)
- [x] Los requisitos se pueden probar y no son ambiguos
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito no mencionan tecnología
- [x] Todos los escenarios de aceptación están definidos
- [x] Los casos límite están identificados (pago tardío, monto distinto, fallas, devoluciones, QR vencido, corte del canal)
- [x] El alcance está acotado (§5 Fuera de alcance)
- [x] Dependencias y supuestos identificados

## Lista para el plan

- [x] Cada requisito funcional tiene criterios de aceptación claros
- [x] Los escenarios cubren los flujos principales
- [x] La funcionalidad cumple los resultados medibles de los criterios de éxito
- [x] No se filtran detalles de implementación en la spec

## Notas

- 2026-11-15, cambio C-3 (sale del plan, DP-2 y DP-3): aprobado y aplicado. Nuevo RF-078; RF-014 y RF-015 ajustados; fila en §4 y escenario 12 de la historia 1. El checklist sigue en orden.

- 2026-11-15, después de aplicar la QA (QA-1 a QA-10) y sus 6 erratas: 77 RF (RF-065 a RF-077 nuevos) y 16 CE. Se revisó otra vez el checklist y todo sigue en orden. Queda el C-2 a la spec 001, aprobado y sin aplicar, como dependencia del corte 1. Hugo la **aprobó** el mismo día.
- 2026-11-15, después de la entrevista (E-1 a E-10): la spec quedó en dos cortes, con 64 RF y 14 CE renumerados y marcados [C1] o [C2]. Se revisó otra vez el checklist y todo está en orden; la spec pasa a **En QA**.

- 2026-11-15, primera validación del borrador. Se corrigió:
  - RF-010 y RF-011 unían dos comportamientos (mostrar el mensaje y conservar lo escrito): se separó RF-043.
  - RF-016 decía *cómo* calcular la cuenta regresiva: ahora dice solo el margen de error.
  - RF-031 repetía el botón Nuevo cobro, que ya cubre RF-034.
  - Un escenario de la historia 6 llevaba una marca duplicada: ahora remite a §8.5.
- Las 3 marcas `[NECESITA ACLARACIÓN]` (monto libre, escuchar el cobro anterior tras Nuevo cobro y cancelar) no se resuelven con la tabla de preguntas de `/speckit-specify`. En este proyecto se resuelven en `/entrevista-spec 002`, como en la spec 001.
- Se nombran Chrome de Android, Safari de iPhone, el ancho de 320 px y la vibración porque vienen del issue #64 y del principio VII (son condiciones de la demo, no decisiones de implementación). La imagen del QR que genera pey solo aparece como tema pendiente para el plan.
