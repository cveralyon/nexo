# Verificación de la base pública

Esta ficha describe únicamente la base reutilizable publicada. El contenido de los ámbitos empieza vacío y los escenarios de las pruebas utilizan datos sintéticos en directorios temporales.

## Alcance de publicación

Se conserva la estructura de diez ámbitos, la bandeja temporal, la lectura selectiva, el protocolo común, las convenciones de documentos vivos, las guías de clasificación y originales, tres plantillas y las utilidades locales. README funciona como portada; las notas personales se crean en la copia de cada usuario.

La base se prepara en un repositorio independiente con historial nuevo. La revisión de publicación comprueba archivos, enlaces, metadatos, fuentes incluidas y objetos Git antes de compartirla. La licencia de la base es [MIT](../LICENSE).

## Comprobaciones

El 6 de octubre de 2026 se ejecutó la validación local de la base completa con Python 3.12.10 y las dependencias fijadas. El resultado fue cero errores y cero advertencias. La suite pasó 60 pruebas en 1,733 segundos. Incluye escenarios sintéticos de identidad estable, errores estructurales, traslado de notas, conservación de originales y concurrencia entre clones temporales.

Se revisaron los 30 archivos preparados, incluidos 23 Markdown. Los diez ámbitos contienen únicamente portadas. No hay notas personales, identificadores de notas privadas, enlaces a originales privados, documentos históricos personales ni configuraciones por proveedor. Los ejemplos están en bloques de plantilla o repositorios temporales de prueba. La revisión independiente dio PASS sobre los 30 archivos preparados y volvió a ejecutar las 60 pruebas con éxito. Antes del primer commit, los únicos objetos Git eran los 30 blobs del índice, sin commits, referencias, remotos ni objetos ajenos. El historial de publicación se inicia con esta base vacía.

El [workflow manual](../.github/workflows/validate.yml) permite repetir las comprobaciones por decisión del propietario de cada copia, con Python 3.12, acciones fijadas por SHA, permisos de lectura y límite de cinco minutos. No hay ejecuciones por push, PR ni calendario, y publicar una nota no exige un check de CI. Los resultados locales anteriores no afirman una ejecución de GitHub Actions.

## Uso posterior

La base pública puede compartirse y contribuirse mediante forks. Para conservar memoria personal, la [guía de inicio](empezar.md) explica cómo crear una copia privada desde la plantilla. Una copia pública no debe recibir datos privados ni enlaces a originales personales.
