# Figuras actualizadas para el informe de práctica

Estas ocho figuras sustituyen, en orden, las figuras 1 a 8 del informe de septiembre de 2026. Los archivos SVG son las fuentes editables y los PNG corresponden a esas mismas fuentes para insertar en Word. `generate_diagrams.py` reconstruye los SVG de forma determinista.

| Figura | Archivo | Sustituye | Base de verificación |
| --- | --- | --- | --- |
| 1 | `01_casos_de_uso` | Casos de uso | `app/routers/chat.py`, `app/routers/admin_router.py`, `app/routers/whatsapp.py`, `app/services/glpi_service.py` |
| 2 | `02_secuencia_rag` | Secuencia RAG con modelo fijo | `app/routers/chat.py`, `app/services/router_logic.py`, `app/services/rag_service.py`, `app/services/llm_client.py` |
| 3 | `03_secuencia_glpi` | Secuencia de radicación GLPI | `app/services/router_logic.py`, `app/services/glpi_service.py`, `app/services/telemetry_service.py` |
| 4 | `04_fsm` | Máquina de estados | `EstadoTicket` y `RouterLogic.procesar_mensaje` en `app/services/router_logic.py` |
| 5 | `05_modulos` | Diagrama de clases anterior | `app/main.py` y paquetes `app/routers`, `app/services` |
| 6 | `06_modelo_datos` | Modelo SQLite de una tabla | `app/services/telemetry_service.py`, `app/services/bot_instance_service.py`, `app/services/golden_cache_service.py` |
| 7 | `07_componentes` | Componentes | `app/main.py`, `app/config.py`, `app/routers`, `app/services` |
| 8 | `08_despliegue` | Despliegue híbrido | `app/main.py`, `app/config.py`, `app/services/rag_service.py`, `app/services/bot_instance_service.py` |

La figura 5 se denomina **vista lógica de módulos** porque los servicios y routers de Python no forman una jerarquía de clases única. La figura 8 describe una **topología de referencia de piloto**; el repositorio no demuestra por sí solo un despliegue en producción. Las figuras representan rutas de código y almacenamiento configurado, no resultados de pruebas ni confirmación de que estén disponibles los servicios externos.

La configuración del proveedor LLM es variable: `app/config.py` define Gemini como proveedor inicial, OpenAI con `gpt-6-luna` como opción, y Ollama local con `unimon:8b`. Los asistentes por dependencia pueden tener configuración propia. Ninguna figura afirma que todas las ejecuciones hayan usado un mismo modelo, que se haya negociado TLS 1.3 en cada conexión, ni que GLPI o WhatsApp hayan respondido en una prueba en vivo.

Para regenerar: ejecute `generate_diagrams.py` con Python 3 y convierta cada SVG en PNG con un rasterizador SVG. Los PNG entregados fueron convertidos con el runtime empaquetado de Codex y `sharp` a 144 dpi. Al insertar en Word, conserve la proporción y use 6,2 pulgadas de ancho o una página apaisada cuando haga falta.
