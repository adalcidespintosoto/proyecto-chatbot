# Diagramas UML del informe de práctica

Estas ocho figuras reemplazan, en el mismo orden, las figuras del informe. Se conservaron los apartados y la numeración del formato institucional. Cada título identifica el tipo de vista UML que representa; los elementos y dependencias se contrastaron con el código y los esquemas actuales.

| Figura | Tipo UML | Fuente | Base de verificación |
| --- | --- | --- | --- |
| 1 | Casos de uso | `01_casos_de_uso.svg` / `.png` | `app/routers/chat.py`, `app/routers/admin_router.py`, `app/routers/whatsapp.py`, `app/services/glpi_service.py` |
| 2 | Secuencia: consulta RAG y generación | `02_secuencia_rag.svg` / `.png` | `app/routers/chat.py`, `app/services/router_logic.py`, `app/services/rag_service.py`, `app/services/llm_client.py` |
| 3 | Secuencia: radicación en GLPI | `03_secuencia_glpi.svg` / `.png` | `app/services/router_logic.py`, `app/services/glpi_service.py`, `app/services/telemetry_service.py` |
| 4 | Actividad: diagnóstico y escalamiento | `04_actividad.svg` / `.png` | `EstadoTicket` y `RouterLogic.procesar_mensaje` en `app/services/router_logic.py` |
| 5 | Paquetes y dependencias de módulos | `05_modulos.svg` / `.png` | `app/main.py`, `app/routers/`, `app/services/` |
| 6 | Clases de persistencia | `06_modelo_datos.svg` / `.png` | `app/services/telemetry_service.py`, `app/services/bot_instance_service.py` |
| 7 | Componentes | `07_componentes.svg` / `.png` | `app/main.py`, `app/config.py`, `app/routers/`, `app/services/` |
| 8 | Despliegue de referencia | `08_despliegue.svg` / `.png` | `app/main.py`, `app/config.py`, `app/services/rag_service.py`, `app/services/bot_instance_service.py` |

## Criterios de representación

Se aplicó la notación de UML 2.5.1: asociaciones sin flecha en casos de uso; mensajes, líneas de vida, activaciones y fragmentos `alt`/`opt` en secuencia; nodos de acción, decisiones y flujos de control en actividad; dependencias `«use»` entre módulos y componentes; clases con atributos, multiplicidades y restricciones de persistencia; y nodos, artefactos y rutas de comunicación en despliegue. La figura 4 es un diagrama de actividad del flujo conversacional; no se titula como diagrama de máquina de estados porque no representa cada estado enumerado de `EstadoTicket`.

Las figuras muestran diseño y dependencias del producto; no presentan por sí solas métricas ni resultados de pruebas. La figura 8 es una topología de referencia y no prueba un despliegue productivo. La figura 6 distingue las tablas SQLite, los índices vectoriales ChromaDB y GLPI, que conserva los tickets oficiales. La figura 7 representa Ollama como servicio local y el proveedor LLM como alternativa configurada.

## Generación

`generate_diagrams.py` reconstruye las ocho fuentes SVG. Los PNG del informe se rasterizaron desde esos SVG a 2200 px de ancho; al insertarlos o sustituirlos en Word, se debe mantener la proporción de cada figura.

## Referencia del estándar

Object Management Group, *Unified Modeling Language (UML), Version 2.5.1* (2017): <https://www.omg.org/spec/UML/2.5.1/PDF>.
