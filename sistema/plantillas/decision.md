# Plantilla de decisión

Las decisiones breves pueden vivir junto al tema. Usa un documento propio dentro de su ámbito o proyecto cuando la decisión sea extensa o se cite desde varias notas. Si se sustituye íntegramente, añade `sustituido_por` con el ID de la nota vigente y actualiza su estado.

```markdown
---
id: n-<new-uuid-v4>
tipo: decision
estado: activo
actualizado: "YYYY-MM-DD"
resumen: "<Una oración que describa la decisión.>"
---

# <Decisión concreta>

## Decisión vigente

<Qué se decidió, cuándo y con qué autoridad. Una propuesta abierta no es una decisión confirmada.>

## Alcance y motivo

<Qué cubre y qué evidencia sostiene el criterio.>

## Alternativas consideradas

<Alternativas reales evaluadas y motivo de la elección.>

## Consecuencias y pendientes

<Efectos, límites y acciones autorizadas todavía por ejecutar.>

## Cambios significativos

<Parte que sigue vigente, decisión reemplazada y enlaces correspondientes.>

## Fuentes relacionadas

<Fecha y procedencia recuperable, o descripción honesta de la declaración sin enlace.>

## Fuentes y archivos

<Sección opcional. Nombre, fecha relevante, función, enlace directo e ID disponible.>
```
