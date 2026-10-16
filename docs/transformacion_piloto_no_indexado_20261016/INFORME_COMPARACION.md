# Comparación piloto: documentos originales y Markdown organizado

**Fecha:** 16 de octubre de 2026  
**Estado:** piloto para revisión humana; los Markdown no están indexados.

## Qué se comparó y cómo

Se compararon tres presentaciones originales (PPTX) con los tres PDF saneados que compartiste. Para cada presentación se usó el extractor actual del proyecto (texto de diapositivas y descripciones locales de imágenes) y después **OpenAI `gpt-6-luna`** organizó el material con el prompt actualizado. La auditoría comparó el resultado con el texto extraído del PPTX y con el PDF anterior.

Claude Haiku no se utilizó en esta prueba. El flujo de transformación aún no está integrado como proceso de ingestión del chatbot; la clave de Anthropic no está disponible en el entorno. La comparación/auditoría fue asistida por el mismo proveedor de modelo, por lo que sirve para encontrar diferencias y orientar revisión, pero no equivale a una validación humana independiente.

No se añadieron estos Markdown al RAG, no se reindexó y no se modificó el Golden Cache. El RAG y Golden Cache actuales tienen una copia verificada por SHA-256 en:

`C:\Users\adalcides.pintos\Documents\Backups\UniMon\pre_transform_20261016_093311`

El manifiesto confirma las colecciones y cantidades al momento de la copia: RAG `langchain` con 7.408 registros y Golden Cache `golden_resolved_qa` con 977. También incluye instrucciones para restaurar ambas carpetas.

## Fuentes comparadas

| Tema | PPTX original | PDF saneado anterior | Cobertura del texto fuente |
|---|---|---|---|
| Bienestar Universitario | `Bienestar universitario manual.pptx` | `MANUAL DE GESTIÓN INTEGRAL EN EL PORTAL DE BIENESTAR UNIVERSITARIO.pdf` | 34 de 34 diapositivas |
| Crédito interno SIAAF | `Aprobacion Solicitudes de credito.pptx` | `MANUAL DE GESTIÓN Y APROBACIÓN DE SOLICITUDES DE CRÉDITO INTERNO EN SIAAF.pdf` | Diapositivas 2–21 de una presentación de 21 diapositivas; no se extrajo contenido de la portada 1 |
| Elecciones, módulo Funcionarios | `Aplicativo Elecciones - Módulo Funcionarios.pptx` | `MANUAL DE GESTIÓN ELECTORAL PARA EL MÓDULO FUNCIONARIOS EN EL APLICATIVO DE ELECCIONES.pdf` | 11 de 11 diapositivas |

## Resultado de los Markdown

Los conteos de fragmentos son una simulación con el separador que usa actualmente el proyecto: **800 caracteres por fragmento y 150 de solapamiento**. Son cifras estimadas para esos archivos; aún no son registros almacenados en Chroma.

| Documento piloto | Palabras | Fragmentos simulados | Referencias a diapositivas | Evaluación del contenido frente al PPTX |
|---|---:|---:|---:|---|
| Bienestar | 1.426 | 17 | 49 | Revisión necesaria. Se corrigió el orden ambiguo de la ruta de apoyo y la ubicación/alcance del aviso al salir sin guardar; el PPTX no permite resolver la secuencia de la diapositiva 18. |
| Crédito SIAAF | 687 | 8 | 17 | Bien: pasos disponibles conservados, botones ilegibles marcados para validar y detalles no verificables no presentados como hechos. |
| Elecciones Funcionarios | 545 | 7 | 14 | Bien: pasos y búsqueda recuperados; campos de captura que no se distinguen se dejaron como pendientes de validación. |

Los Markdown finales están en esta carpeta, todavía fuera de la base de conocimiento:

- `bienestar.md`
- `credito_siaaf.md`
- `elecciones_funcionarios.md`

## Hallazgos importantes

### 1. Los PDF anteriores aportan información que no aparece en el PPTX extraído

La comparación encontró **8 grupos de detalles por cada PDF** que no se localizaron en el texto/descripciones extraídos de su presentación correspondiente. Esto no demuestra que sean falsos: pueden venir de capturas legibles visualmente, otro archivo, una versión del sistema o una fuente complementaria. Sí significa que no se deben atribuir a esas presentaciones sin verificar la procedencia.

- **Bienestar:** nombres de servicios y áreas, requisitos/campos, significado y colores del semáforo, datos detallados de estudiante, filtros, flujos de actividades y canales de soporte.
- **Crédito:** condiciones de cuenta y perfil, verificaciones financieras, etiquetas y botones, reglas detalladas de aprobación/rechazo, preguntas frecuentes y contactos.
- **Elecciones:** requisitos de administración/período, campos de elecciones y candidatos, efectos de eliminación, detalles de votos/resultados y canales de soporte.

Los nuevos Markdown quedan más conservadores y trazables a la fuente recibida. La consecuencia es que pueden contener menos detalle que los PDF antiguos hasta corroborar esos grupos con las diapositivas visuales u otros documentos. No conviene borrar ni reemplazar los PDF existentes por este piloto.

### 2. Hay una ambigüedad real en Bienestar

En la diapositiva 18, una frase dice que se eligen los motivos del servicio “elegido previamente”; otra dice “Primero elegimos el servicio”. El Markdown final ya no inventa un orden: deja la contradicción visible y pide validar la pantalla. La diapositiva 19 sí dice que aparece un mensaje de confirmación al guardar, pero no trae el texto literal del aviso.

La diapositiva 20 está bajo el título **Datos Académicos - (Matrícula)**, mientras su texto habla genéricamente de salir del servicio sin guardar. El Markdown final conserva esa nota y advierte que no se puede confirmar si aplica a otras pantallas.

### 3. Las imágenes siguen siendo el principal límite de precisión

El extractor generó descripciones de imágenes con texto repetido o que parece ajeno a algunas interfaces. Por eso se marcaron para revisión visual las diapositivas 4–7, 17–19 y 31–34 de Bienestar; 13–21 de Crédito; y 5 y 9 de Elecciones. En particular, varios botones/campos solo pueden confirmarse viendo directamente la diapositiva.

### 4. No hay garantía de duplicar la precisión por transformar a Markdown

Ordenar los pasos, conservar nombres de controles y poner citas de página/diapositiva facilita que el RAG encuentre el contenido. Pero si el PPTX no explica un paso, una imagen no se lee o hay instrucciones ambiguas, Markdown no recupera por sí mismo ese dato. La calidad final dependerá también de extracción/OCR visual, segmentación, recuperación de documentos complementarios y una evaluación con preguntas reales.

## Recomendación antes de indexar

1. Revisa los tres Markdown y, para cada detalle adicional que quieras conservar, identifica su fuente verificable. En especial, no reemplaces el contenido más completo de Bienestar/Crédito/Elecciones hasta resolver los grupos listados arriba.
2. Confirma visualmente las diapositivas marcadas y resuelve la secuencia de la ruta de apoyo en Bienestar.
3. Si apruebas el formato, integrar la generación de Markdown al flujo de ingestión como una etapa separada y auditable: conservar el original, guardar el `.md` derivado con trazabilidad al archivo/modelo/prompt, permitir revisión y poder volver a extraer/indexar desde el original.
4. Hacer una evaluación antes/después con preguntas de soporte que requieran combinar procedimientos, midiendo fuente correcta, fragmentos recuperados, contexto enviado y respuesta. Solo después de revisar resultados conviene incorporar los Markdown a la colección RAG.

## Archivos asociados

- Prompt propuesto para transformación: `docs/PROMPT_TRANSFORMACION_DOCUMENTOS_RAG.md`.
- Copia verificada del RAG y Golden Cache: `C:\Users\adalcides.pintos\Documents\Backups\UniMon\pre_transform_20261016_093311`.
- Resultados de generación y auditoría intermedia: `scratch/document_transform_pilot_20261016/` (área de trabajo local, no indexada).
