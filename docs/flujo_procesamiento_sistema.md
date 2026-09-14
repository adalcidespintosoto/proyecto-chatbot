# Arquitectura y Flujo Integral de Procesamiento de UniMon

Este documento describe con máximo nivel de detalle técnico el ciclo de vida completo de un mensaje en el sistema **UniMon** (Universidad Simón Bolívar), desde que el usuario envía su consulta en la interfaz web hasta la entrega de la solución técnica, la actualización de la memoria rápida (Golden Cache) o la radicación formal de un ticket en GLPI.

---

## 1. Mapa de Componentes y Arquitectura del Sistema

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CAPA DE PRESENTACIÓN                                   │
│            Interfaz Web Interactiva (HTML5 / Vanilla CSS / Botones de Diagnóstico)     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP POST /api/chat (JSON)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        CAPA DE SERVICIOS API Y SEGURIDAD (FastAPI)                     │
│  • Endpoint Chat: POST /api/chat (Protegido por slowapi Rate Limit: 30 req/min)        │
│  • Seguridad Perimetral: Bloqueo estricto de orígenes no autorizados vía CORS.         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Invoca RouterLogic.procesar_mensaje()
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ORQUESTADOR DE DIÁLOGO Y MÁQUINA DE ESTADOS                     │
│                             app/services/router_logic.py                               │
│  • Gestión de Sesiones en Memoria (TicketSession con TTL de 30 min)                    │
│  • Reglas Globales: Cancelación, Cierre Solucionado, Directorio Inmediato.             │
│  • Guardrail OOD: Intercepta temas fuera de dominio (ej. programación general).        │
│  • Calificación de Rol: Filtra el RAG según el rol del usuario (Docente, Estudiante).  │
│  • Enrutamiento Rápido de Hardware: Bypassea el RAG para enviar hardware directo a GLPI│
└────────────┬──────────────────────────────┬─────────────────────────────┬──────────────┘
             │                              │                             │
    Memoria  │                 Consulta     │                   Radicación│
    Rápida   ▼                 RAG N1       ▼                   de Ticket ▼
┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────────┐
│       GOLDEN CACHE       │ │       MOTOR RAG N1       │ │   CLIENTE REST DE TICKETS    │
│ golden_cache_service.py  │ │  app/services/rag_service│ │ app/services/glpi_service.py │
│                          │ │                          │ │                              │
│ • Búsqueda exact match   │ │ 1. Expansión Multi-Query │ │ 1. Auth GLPI (App+User Token)│
│ • Similitud Coseno >=0.90│ │ 2. Búsqueda Vectorial    │ │ 2. POST /Ticket (Cat, urg)   │
│ • Few-Shot LLM Injection │ │ 3. Reranker Cross-Encoder│ │ 3. POST /Ticket_User (Email) │
│ • Auto-invalidación      │ │ 4. Prompt Estricto N1    │ │ 4. killSession               │
└──────────────────────────┘ └──────────────┬───────────┘ └──────────────────────────────┘
                                            │ Post-Procesamiento (clean_llm_response)
                                            ▼
                             ┌──────────────────────────┐
                             │ POST-PROCESADOR / GUARDS │
                             │ • Truncado de etiquetas  │
                             │   crudas del contexto RAG│
                             │ • Sanitizador URLs       │
                             │ • Footer Condicional TI  │
                             └──────────────────────────┘
```

---

## 2. Diagrama de Flujo Integral del Procesamiento

```mermaid
flowchart TD
    Inicio([👤 Usuario envía mensaje]) --> RateLimit[🛡️ FastAPI: Control de Rate Limit 30req/min]
    RateLimit --> ObtenerSesion[Obtener / Inicializar TicketSession en memoria]

    %% REGLAS GLOBALES Y GUARDRAILS
    ObtenerSesion --> CheckCancel{¿Es cancelación?<br/>'no', 'cancelar', 'ya no'}
    CheckCancel -- Sí --> ResetCancel[Limpiar sesión a IDLE] --> RespCancel[Retornar: CANCELADO]
    
    CheckCancel -- No --> CheckSolved{¿Es confirmación de solución?<br/>'ya funcionó', 'ya pude'}
    CheckSolved -- Sí --> SaveGoldenGlobal[Guardar caso en Golden Cache] --> ResetSolved[Limpiar sesión a IDLE] --> RespSolved[Retornar: SOLUCIONADO]

    CheckSolved -- No --> CheckDirectorio{¿Pide canales de atención o directorio?}
    CheckDirectorio -- Sí --> RespDirectorio[Retornar Directorio TI Inmediato]

    CheckDirectorio -- No --> CheckOOD{¿Consulta Fuera de Dominio?<br/>ej. hazme un ensayo}
    CheckOOD -- Sí --> PurgeOOD[Purga pending_query y reset a IDLE] --> RespOOD[Retornar: FUERA_DE_DOMINIO]

    %% EVALUACIÓN DE ESTADOS CONVERSACIONALES
    CheckOOD -- No --> EvalEstado{Estado de la Sesión}

    %% ESTADO: PIDIENDO_ROL
    EvalEstado -- PIDIENDO_ROL --> ParseRol{¿Seleccionó o declaró Rol?}
    ParseRol -- No identificado --> ReAskRol[Reiterar MENSAJE_PIDIENDO_ROL]
    ParseRol -- Identificado --> SetRol[Asignar user_role en sesión]
    SetRol --> CheckPendingOOD{¿pending_query era OOD?}
    CheckPendingOOD -- Sí --> PurgePending[pending_query = None] --> ReadyMsg[Retornar DIAGNOSTICO]
    CheckPendingOOD -- No --> CheckPendingValida{¿Había pregunta técnica previa?}
    CheckPendingValida -- Sí --> CheckHardwareFastPending{¿Es falla física o hardware?}
    CheckHardwareFastPending -- Sí --> JumpNombreHW[Salto a PIDIENDO_NOMBRE]
    CheckHardwareFastPending -- No --> PipelineRAG
    CheckPendingValida -- No --> ReadyMsg

    %% ESTADO: IDLE
    EvalEstado -- IDLE --> CheckRolAsignado{¿Tiene user_role en sesión?}
    CheckRolAsignado -- No --> TryDetectRol{¿Menciona su rol en el mensaje?}
    TryDetectRol -- Sí --> SetRolDirecto[Asignar user_role] --> CheckEsSoloRol{¿Es solo declaración?}
    CheckEsSoloRol -- Sí --> SaludoRol[Retornar DIAGNOSTICO]
    CheckEsSoloRol -- No --> CheckHardwareFastIDLE{¿Es falla física?}
    CheckHardwareFastIDLE -- Sí --> JumpNombreHW
    CheckHardwareFastIDLE -- No --> PipelineRAG
    TryDetectRol -- No --> RetenerPregunta[Guardar pregunta en pending_query] --> SetPidiendoRol[Estado: PIDIENDO_ROL] --> MsgPidiendoRol[Retornar MENSAJE_PIDIENDO_ROL]

    CheckRolAsignado -- Sí --> CheckHardwareFastKnown{¿Es falla física?}
    CheckHardwareFastKnown -- Sí --> JumpNombreHW
    CheckHardwareFastKnown -- No --> PipelineRAG

    %% ESTADO: DIAGNOSTICO
    EvalEstado -- DIAGNOSTICO --> CheckFeedbackDiagnostico{Feedback del usuario}
    CheckFeedbackDiagnostico -- RESOLVED ('Sí, me funcionó') --> SaveGoldenDiag[Guardar en Golden Cache] --> ResetDiagSolved[Limpiar a IDLE] --> RespSolved
    CheckFeedbackDiagnostico -- CREATE_TICKET ('No, radicar ticket') --> InvalidateGolden[Invalidar caso en Golden Cache] --> JumpNombre[Salto a PIDIENDO_NOMBRE]
    CheckFeedbackDiagnostico -- RETRY_DIAGNOSIS ('Intentar de nuevo') --> InvalidateGoldenRetry[Invalidar caso] --> CheckIntentos{Intentos < 2}
    CheckIntentos -- Sí --> IncrIntento[Incrementar intento] --> PipelineRAG
    CheckIntentos -- No --> AutoEscalar[Escalado automático a Radicación] --> JumpNombre
    CheckFeedbackDiagnostico -- Texto Libre / Nueva Consulta --> PipelineRAG

    %% FLUIDO DE SLOT-FILLING
    EvalEstado -- PIDIENDO_NOMBRE --> ValidarNombre{Nombre válido?<br/>>= 2 palabras}
    ValidarNombre -- Sí --> SaveNombre[Guardar session.nombre] --> NextCorreo[Estado: PIDIENDO_CORREO]

    EvalEstado -- PIDIENDO_CORREO --> ValidarCorreo{Email válido institucional?}
    ValidarCorreo -- Sí --> SaveCorreo[Guardar session.correo] --> NextDesc[Estado: PIDIENDO_DESCRIPCION]

    EvalEstado -- PIDIENDO_DESCRIPCION --> SaveDesc[Guardar session.descripcion] --> CrearTicketGLPI[Ejecutar radicación en GLPI REST API]
    CrearTicketGLPI --> ResetSesionGLPI[Limpiar sesión a IDLE] --> RespTicketCreado[Retornar TICKET_CREADO #ID]

    %% PIPELINE RAG Y MOTOR DE GENERACIÓN
    subgraph PipelineRAG [Pipeline RAG Local & Inferencia]
        ConsultarGolden{1. ¿Existe coincidencia en Golden Cache?<br/>Score >= 0.90}
        ConsultarGolden -- Sí --> InyectarFewShot[2. Inyectar respuesta previa como plantilla (Few-Shot)]
        ConsultarGolden -- No --> MultiQuery[2. Expansión Multi-Query LLM (3 variantes)]
        MultiQuery --> BuildRoleFilter[3. Búsqueda Vectorial k=8 múltiple]
        InyectarFewShot --> BuildRoleFilter
        BuildRoleFilter --> Reranker[4. Cross-Encoder Reranker: Top-8 -> Top-3]
        Reranker --> CheckMinScore{5. ¿Top chunk tiene Score >= 0.48?}
        CheckMinScore -- No --> FallbackNoDoc[Retornar MENSAJE_NO_DOCUMENTADO]
        CheckMinScore -- Sí --> AssembleStrictPrompt[6. Ensamblar Prompt Estricto N1 + Golden]
        AssembleStrictPrompt --> OllamaInference[7. Invocación Ollama unimon:8b Temp: 0.0]
        OllamaInference --> PostProcessing[8. Post-Procesador:<br/>- Sanitización URLs<br/>- Truncado fugas documento<br/>- Footer Condicional Contactos]
        PostProcessing --> RespDiagnosticoFinal[Retornar DIAGNOSTICO]
    end
```

---

## 3. Desglose Fase por Fase del Proceso

### Fase 0: Ingesta e Indexación Multimodal (Vision-LLM)
Antes de que el usuario envíe un mensaje, la base de conocimiento (ChromaDB) debe construirse de forma precisa para que el RAG funcione. UniMon utiliza un pipeline multimodal (`ingest_multimodal_docs.py`) que no solo lee texto, sino que interpreta imágenes usando **Llama 3.2 Vision (11B)**.
1. Cuando se carga un manual institucional (PDF, PPTX) que contiene capturas de Kactus, GLPI o portales, el sistema recorta la imagen y se la envía al modelo de visión con el siguiente **prompt estricto**:
   > *"Analiza detalladamente esta imagen de documentación técnica de TI institucional. Si es una captura de pantalla de software (Kactus, Seven, GLPI, Windows, portales web, etc.): describe la ventana activa, menús, botones seleccionados, campos completados y el procedimiento exacto que se muestra. Si es un diagrama de flujo o mapa de procesos: describe la secuencia lógica, decisiones, roles y pasos de inicio a fin. Si es una tabla: transcribe las columnas, filas y datos relevantes. Si contiene texto o mensajes de error: transcribe literalmente los textos clave. Sé conciso, técnico y estructurado. Responde en español."*
2. La IA de visión genera un texto descriptivo de la imagen, el cual se inyecta en el documento. 
3. Luego, el script `apply_document_taxonomy.py` asigna **metadatos** (Ficha Técnica) automáticamente basándose en la ubicación y nombre del archivo (ej. `audience: estudiante`, `doc_type: autoservicio`). Esto permite que el RAG sepa a quién va dirigido cada fragmento de texto.


### Fase 1: Recepción, Seguridad (Rate Limit) e Inicialización
1. El usuario interactúa mediante la interfaz web o un cliente HTTP.
2. La petición ingresa por FastAPI y pasa por el **Middleware `slowapi`**. Si una IP supera las 30 peticiones por minuto, el sistema bloquea inmediatamente la IP devolviendo `HTTP 429 Too Many Requests` para proteger contra ataques DoS/DDoS o bots descontrolados. También se ejecuta un bloqueo estricto de dominios web externos vía configuración CORS.
3. Superada la seguridad, se envía el JSON de la consulta al enrutador de FastAPI.
4. Se obtiene o crea la instancia de `TicketSession` en memoria (con un TTL de expiración de 30 minutos por inactividad).

---

### Fase 2: Reglas Globales y Guardrails Tempranos (Bypass Pre-RAG)
Antes de operaciones pesadas, `RouterLogic.procesar_mensaje()` evalúa cuatro reglas globales:

1. **Regla Global 1 (Cancelación Universal):** Si envía *"cancelar"*, se aborta cualquier trámite y se vuelve a IDLE.
2. **Regla Global 2 (Cierre por Solución Confirmada):** Si envía *"ya funcionó"*, se guarda la consulta y respuesta anterior en la base de datos **Golden Cache** (`golden_resolved_qa`). Esto es el mecanismo de aprendizaje del sistema.
3. **Regla Global 3 (Directorio TI Inmediato):** Consultas como *"cuál es el whatsapp"* devuelven un directorio *hardcoded* para evitar demoras y alucinaciones.
4. **Regla Global 4 (Guardrail Estricto Fuera de Dominio):** Intercepta de forma inmediata temas ajenos al alcance de TI (ensayos, chistes, recetas, código "hola mundo"), purga la memoria y retorna que no tiene alcance.

---

### Fase 3: Calificación de Rol y Purga de Contexto
El RAG necesita saber con quién habla. Si el usuario no tiene rol:
1. Su consulta técnica se guarda en "pausa" (`pending_query`).
2. Se le exige hacer clic en Estudiante, Administrativo o Docente.
3. Al recibir el rol, el sistema re-evalúa si la pregunta que estaba en pausa era válida o no (gracias a los nuevos ajustes de las expresiones regulares, esto es sumamente preciso y evita que la palabra "notas" bloquee falsamente flujos válidos) y continúa el flujo.

---

### Fase 4: Enrutamiento Rápido de Hardware (SOPORTE FISICO)
Las reglas semánticas fueron refinadas para detectar averías físicas (pantallas rotas, teclado dañado, cable quemado). En lugar de buscar documentos PDF, el sistema bypassea el motor RAG e inyecta la plantilla `PROMPT_HARDWARE_DIRECT`. Esto obliga al usuario a contactar directamente a infraestructura o a radicar un ticket presencial sin hacerlo perder tiempo interactuando con manuales de software.

---

### Fase 5: Memoria de Aprendizaje (Golden Cache & Few-Shot)
Cuando la solicitud pasa las reglas, entra a `golden_cache_service.py`.
1. Busca en la colección `golden_resolved_qa` si alguien preguntó lo mismo en el pasado (Similitud Coseno >= 0.90).
2. Si encuentra una coincidencia, **no vomita la respuesta robóticamente**. En su lugar, el sistema extrae la respuesta antigua y la inyecta como un **"Ejemplo Institucional de Referencia" (Few-Shot Prompting)** dentro de las instrucciones secretas del LLM.
3. Esto le permite al LLM ver cómo se resolvió un problema idéntico en el pasado, utilizarlo como plantilla maestra, pero redactar un mensaje fresco y adaptado a las minucias exactas de la nueva pregunta del usuario.

---

### Fase 6: Expansión de Consultas (Multi-Query Generation)
Si la pregunta del usuario es demasiado vaga, ambigua o está mal escrita, entra a la función `async_generate_multi_query_variants` en `rag_service.py`.
1. El sistema utiliza el LLM en segundo plano para "reescribir" y "adivinar" las intenciones del usuario en 3 preguntas alternativas perfectas.
2. Luego, realiza la búsqueda vectorial usando simultáneamente la pregunta vaga original + las 3 preguntas perfectas generadas. 
3. Esto garantiza matemáticamente que, sin importar cuán mal se exprese el usuario, el motor vectorial encontrará el manual correcto.

---

### Fase 7: Pipeline de Recuperación RAG y Reranking Estricto
1. **Filtro por Rol:** Se construye un filtro en ChromaDB (`$in: ['estudiante', 'general']`).
2. **Búsqueda (k=8):** Se traen los 8 fragmentos de texto más similares (`BAAI/bge-m3`).
3. **Cross-Encoder Reranker (Top-8 -> Top-3):** Los 8 documentos se pasan por un modelo evaluador implacable. Se aplican bonificaciones (ej. reseteo de claves Microsoft recibe +4.0) y penalizaciones (-6.0 si un estudiante de último semestre recupera un manual de inducción de 1er semestre).
4. **Corte de Umbral:** Si ningún documento supera un score de `0.48`, el sistema asume que no sabe y emite el `MENSAJE_NO_DOCUMENTADO`.

---

### Fase 8: Inferencia LLM y Sanitización Extrema de Output
El LLM procesa la pregunta, el contexto de los documentos, el rol del usuario y los ejemplos del Golden Cache para generar una respuesta en Temperatura `0.0`. Sin embargo, para evitar que el LLM haga desastres, se ejecuta `clean_llm_response()`:
1. **Truncado de Fugas de Contexto:** Si el LLM, por error, copia la etiqueta secreta del RAG (ej. `[DOCUMENTO INSTITUCIONAL COMPLETO: ...]` o `FICHA TÉCNICA DEL DOCUMENTO`), la función intercepta la cadena, la corta exactamente antes de que aparezca esa basura técnica y limpia el string.
2. **Sanitización de Links:** Cualquier URL generada que no pertenezca a unisimon.edu.co o dominios de Microsoft permitidos es inmediatamente eliminada.
3. **Inserción Condicional de Footer:** Si el LLM no mencionó espontáneamente en su respuesta los correos de soporte oficial, el sistema concatena incondicionalmente el bloque de **"📌 Canales Oficiales de Soporte TI"**. Si el modelo ya los había incluido copiando del PDF, el sistema lo detecta y no añade el bloque redundante.

---

### Fase 9: Slot-Filling de Ticket GLPI
Si el usuario hace clic en **"🎫 Generar Reporte / No me funcionó"**, se ejecuta el circuito ITSM:
1. Pide Nombre Completo.
2. Pide Correo (validado con Regex Unicode).
3. Pide Descripción.
4. Conecta mediante HTTP REST a GLPI usando `App-Token` y `User-Token`, radica la incidencia y devuelve el ID al usuario. Destruye todos los datos de memoria inmediatamente por seguridad (GDPR/Habeas Data).
