# UniMon — Asistente conversacional de soporte TI

UniMon es un backend FastAPI con canales web y WhatsApp opcional, recuperación RAG en Chroma, proveedores LLM configurables, telemetría y una integración GLPI opcional.

## Documentos vigentes

- [Manual de usuario](docs/MANUAL_DE_USUARIO.md)
- [Manual técnico integral](docs/MANUAL_TECNICO_INTEGRAL.md)
- [Guía para replicar y operar el sistema](docs/REPLICAR_Y_OPERAR_UNIMON.md)
- [Flujo de una consulta](docs/flujo_procesamiento_sistema.md)

La bitácora de integración OpenAI y las comparativas RAG de la carpeta docs son históricas. La configuración real se determina desde .env y el código de esta revisión.

## Inicio rápido en Windows

~~~powershell
.\setup.ps1
# Configura .env con claves propias: no uses placeholders en un entorno real.
.\run.ps1
~~~

Abre / para el chat, /docs para el esquema de API y /admin para el panel con HTTP Basic. Revisa /health. Para preparar la base documental desde fuentes autorizadas, consulta la guía de réplica; el ingestor principal procesa PDF y PPTX.

## Arquitectura en una frase

Chat web/WhatsApp → FastAPI → router conversacional → reglas de dominio o RAG (expansión, búsqueda vectorial y léxica, reranking, expansión secuencial de vecinos, presupuesto adaptativo) → LLM configurado → telemetría; las acciones de ticket usan GLPI si está configurado.

## Hechos operativos que debes conocer

- El RAG no filtra documentos por rol; aplica algunos filtros por categoría temática.
- El corpus presente contiene formatos que el pipeline principal no indexa automáticamente; verifica la tabla completa en la guía de réplica.
- Las sesiones conversacionales viven en memoria y se pierden al reiniciar el proceso.
- Golden Cache recibe feedback positivo sujeto a validadores, pero una respuesta cacheada no sustituye las fuentes institucionales.
- Una corrida de 50 sesiones simultáneas completó 50 respuestas HTTP sin 429/5xx; latencia p50 fue 65,1 s y p95 70,7 s. Exactitud estricta medida: 50%. No equivale a validación de producción.

## Dependencias funcionales

Python y FastAPI ejecutan la app. Chroma y sentence-transformers realizan búsqueda/embeddings/reranking. LangChain aporta integraciones de documentos, splitter y vector store. OpenAI, Gemini u Ollama generan texto. GLPI y Meta son integraciones opcionales. CrewAI y LangGraph no son dependencias del flujo actual.


