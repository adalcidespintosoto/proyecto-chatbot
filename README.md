# UniMon — Asistente conversacional de soporte TI

UniMon es un backend FastAPI con canales web y WhatsApp opcional, recuperación RAG en Chroma, proveedores LLM configurables, telemetría y una integración GLPI opcional.

## Documentos vigentes

- [Manual de usuario](docs/MANUAL_DE_USUARIO.md)
- [Manual técnico integral](docs/MANUAL_TECNICO_INTEGRAL.md)
- [Guía para replicar y operar el sistema](docs/REPLICAR_Y_OPERAR_UNIMON.md)
- [Crear asistentes para otras dependencias](docs/CHATBOTS_POR_DEPENDENCIA.md)
- [Flujo de una consulta](docs/flujo_procesamiento_sistema.md)

La bitácora de integración OpenAI y las comparativas RAG de la carpeta docs son históricas. La configuración real se determina desde .env y el código de esta revisión.

## Inicio rápido en Windows

~~~powershell
.\setup.ps1
# Configura .env con claves propias: no uses placeholders en un entorno real.
.\run.ps1
~~~

Abre / para el chat, /docs para el esquema de API en desarrollo y /admin para el panel con HTTP Basic. Revisa /health. Para preparar la base documental desde fuentes autorizadas, consulta la guía de réplica y [la guía de ingesta Markdown](docs/INGESTA_MARKDOWN_AUTOMATICA.md): las fuentes PDF, PPTX y DOCX compatibles se transforman a Markdown antes de generar embeddings. La carga desde el panel de una instancia compara el Markdown con el original antes de indexarlo.

## Arquitectura en una frase

Chat web/WhatsApp → FastAPI → router conversacional → reglas de dominio o RAG (expansión, búsqueda vectorial y léxica, reranking, expansión secuencial de vecinos y tope de chunks) → LLM configurado → telemetría; las acciones de ticket usan GLPI si está configurado. El modo opcional `/?router=1` clasifica la intención con los alcances declarados y catálogos de metadatos documentales; delega a un RAG aislado por dependencia cuando corresponde.

## Hechos operativos que debes conocer

- El RAG no filtra documentos por rol; aplica algunos filtros por categoría temática.
- El corpus presente contiene formatos que el pipeline principal no indexa automáticamente; verifica la tabla completa en la guía de réplica.
- Las sesiones conversacionales viven en memoria y se pierden al reiniciar el proceso.
- Las instancias adicionales tienen índices, Golden Cache y catálogos de especialidad separados; su telemetría se agrega a los KPIs globales y conserva un desglose por instancia.
- Golden Cache recibe feedback positivo sujeto a validadores, pero una respuesta cacheada no sustituye las fuentes institucionales ni acredita exactitud.
- En la medición local del 6 de octubre de 2026, 50 sesiones simultáneas completaron 50 respuestas HTTP sin 429/5xx; la latencia p50 fue 65,1 s y p95 70,7 s. La exactitud estricta juzgada fue 25/50 (50%). Es una línea base histórica, no una validación del código actual ni de producción.
- El árbol de trabajo local incluye cambios recientes de ingesta, auditoría documental y enrutamiento. Verifica las pruebas y el flujo completo en el entorno de entrega antes de declarar esos cambios desplegados.

## Dependencias funcionales

Python y FastAPI ejecutan la app. Chroma y sentence-transformers realizan búsqueda/embeddings/reranking. LangChain aporta integraciones de documentos, splitter y vector store. OpenAI, Gemini u Ollama generan texto. GLPI y Meta son integraciones opcionales. CrewAI y LangGraph no son dependencias del flujo actual.


