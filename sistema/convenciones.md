# Convenciones

## Una sede y una identidad

Clasifica por el propósito principal mediante la [guía](guia-de-clasificacion.md). Cada asunto conserva una sede. Otras áreas enlazan esa nota y mantienen solo su contexto propio. Busca el título, los nombres alternativos y los conceptos relacionados antes de crear contenido.

Usa nombres descriptivos en minúsculas, sin tildes y con guiones. El texto conserva el español normal. Un tema pequeño empieza como un archivo con nombre explícito. Cuando necesite una carpeta, su nota principal conserva el identificador y el contenido vivo. El README de esa carpeta pasa a ser una portada breve que enlaza la nota principal y sus detalles.

## Metadatos

Toda nota de contenido necesita cinco campos. Los README son portadas sin metadatos de contenido. Las guías, plantillas y archivos de prueba también quedan exentos.

```yaml
---
id: n-<new-uuid-v4>
tipo: tema
estado: activo
actualizado: "YYYY-MM-DD"
resumen: "Una oración que describe el contenido."
---
```

- `id` lleva `n-` y un UUID v4 nuevo. Se conserva al mover, dividir o renombrar el tema principal. Los nuevos documentos de detalle reciben su propio ID.
- `tipo` admite `tema`, `proyecto`, `persona`, `decision`, `idea`, `aprendizaje`, `experiencia` y `registro`.
- `estado` admite `activo`, `borrador`, `en-curso`, `por-confirmar`, `cerrado`, `archivado` y `sustituido`.
- `actualizado` identifica la edición y usa una fecha ISO entre comillas. No acredita una verificación de todo el contenido.
- `resumen` es una oración clara y no vacía.
- `aliases`, opcional, es una lista de nombres alternativos.
- `verificado`, opcional, es una fecha ISO. El cuerpo describe el alcance y la evidencia de esa comprobación.
- `sustituido_por`, opcional, apunta al ID existente de la nota que reemplaza íntegramente a otra. Una sustitución parcial se explica junto a la decisión afectada.

Genera un identificador con cualquier herramienta segura para UUID v4. Este ejemplo usa Python.

```bash
python -c 'import uuid; print("n-" + str(uuid.uuid4()))'
```

## Estado, historia y procedencia

Corrige el estado vigente en su lugar. Conserva solo los hitos necesarios para comprenderlo. Git registra cada edición. Cuando el histórico dificulte la lectura, muévelo a `historico/` dentro de la misma sede y enlázalo desde la nota vigente.

Separa decisiones confirmadas, propuestas, hechos verificados, datos reportados e hipótesis. Los hechos importantes llevan fecha, fuente y alcance. Si no existe un enlace recuperable, registra honestamente la fecha y el contexto de la declaración.

Las decisiones breves viven en el tema. Una decisión extensa o citada desde varias notas puede tener un documento propio en `decisiones/` dentro de su sede. La intención, el borrador, el envío, la publicación, el pago y la conciliación se acreditan por separado en sus sistemas originales.

## Fuentes y archivos

Usa enlaces Markdown relativos para documentos de Nexo. Los originales permanecen en las carpetas existentes de Drive o de tu archivo documental. Conserva nombre, fecha relevante, función, enlace directo e ID disponible. Lee el archivo para acreditar una conclusión. Encontrar su carpeta solo acredita ubicación.

Cada examen de otra fecha es un documento independiente. Una corrección también conserva un archivo separado y enlaza el original. Los documentos anteriores siguen disponibles. Reutiliza las carpetas existentes y crea una subdivisión solo cuando un archivo real la necesite.

Mantén las credenciales y los secretos fuera del repositorio. Conserva únicamente información personal pertinente en tu copia privada.

## Lectura y tamaño

Una consulta acotada suele requerir el [mapa](../START_HERE.md), un índice y una o dos notas. Profundiza en fuentes, historia u otros ámbitos cuando la pregunta lo necesite. La búsqueda descubre candidatos. La lectura por ruta en `main` confirma la versión.

| Pieza | Orientación de mantenimiento |
| --- | --- |
| README raíz | Aproximadamente 200 a 500 palabras |
| START_HERE | Hasta unas 700 palabras |
| Índice local | Normalmente 100 a 350 palabras más enlaces |
| Nota vigente | Preferentemente menos de 1.500 palabras |
| Documento grande | Revisar división al superar 2.000 palabras o 30 KiB |
| Índice amplio | Revisar agrupación al acercarse a 40 entradas |

Los umbrales orientan. Divide por significado. El validador puede advertir sobre documentos grandes, índices amplios, rutas locales, fechas futuras y notas sin ruta desde los índices. Las advertencias ayudan al mantenimiento y no equivalen a errores.

## Publicar y comprobar

Sigue [cómo usar Nexo](como-usar-nexo.md). Publica juntos los cambios relacionados en `main`. Integra avances remotos y relee las partes afectadas antes de escribir. Los conflictos de significado requieren una resolución explícita aunque Git pueda unir las líneas. Comprueba el texto publicado desde el repositorio remoto.
