# Resumen de Integración: Migración a OpenAI (GPT-5.6 Luna) en UniMon

Este documento recopila el contexto, decisiones técnicas, archivos modificados, pruebas realizadas y el estado final del sistema tras la integración de la API comercial en la nube (**OpenAI GPT-5.6 Luna**) en sustitución del modelo local de Ollama.

---

## 1. Contexto y Motivación

* **Problema inicial:** El proyecto utilizaba modelos locales con Ollama (`unimon:8b` y `llama3.2-vision:11b`), los cuales exigían alto consumo de hardware/VRAM, lentitud de respuesta (5 a 20+ segundos en CPU/GPU doméstica) y limitaciones de razonamiento/seguimiento estricto de prompts RAG.
* **Evaluación económica:** Se analizaron proveedores económicos (Google Gemini Flash, Groq Llama 3.3 70B y GPT-5.6 Luna). Se determinó que para un volumen universitario típico de **3.000 consultas/mes**, el costo operativo con una API moderna ronda entre **$1.80 y $2.50 USD al mes** (~$8.000 a $11.000 COP), resultando infinitamente más barato que mantener un servidor en la nube con GPU dedicada ($80 - $150 USD/mes).
* **Modelo seleccionado para pruebas:** **OpenAI `gpt-5.6-luna`** (familia GPT-5.6 optimizada para alta velocidad, baja latencia, ventana de 1.000.000+ tokens, visión multimodal y soporte de prompt caching a $0.02 USD / 1M tokens).

---

## 2. Hallazgos Técnicos sobre el Modelo `gpt-5.6-luna`

Durante las pruebas directas contra la API de OpenAI con la clave provista, se descubrieron y adaptaron las siguientes particularidades técnicas:
1. **Límite de tokens:** No admite el parámetro clásico `max_tokens` (devuelve error 400). Requiere obligatoriamente **`max_completion_tokens`**.
2. **Tokens de razonamiento (Reasoning Tokens):** Como modelo de la nueva generación GPT-5.6, `completion_tokens` incluye tokens internos de razonamiento antes de emitir la respuesta visible. Se calibró el parámetro **`reasoning_effort: "low"`** para maximizar la velocidad de respuesta y se aseguró un margen suficiente de tokens (`max_completion_tokens >= 600`).
3. **Temperatura:** No permite anular la temperatura a `0.0` (solo valor predeterminado 1.0), por lo que se omite el parámetro de temperatura al consultar modelos GPT-5.

---

## 3. Resumen de Archivos Creados y Modificados

### Archivos Creados:
* **`app/services/llm_client.py`:**
  * Nuevo cliente unificado para llamadas de inferencia LLM.
  * Implementa `chat_completion`, `generate_async`, `generate_sync` y `check_health`.
  * Optimizado para OpenAI (`gpt-5.6-luna`) y compatible con Ollama.
  * **Modo Estricto:** Cuando `LLM_PROVIDER=openai`, **el fallback a Ollama está completamente deshabilitado** a solicitud del usuario, garantizando que el 100% de las respuestas provengan de la nube. Si la API falla, se lanza una excepción visible sin enmascarar el error.
  * Incluye trazabilidad en tiempo real en consola: `[OPENAI CLOUD] >>> Enviando...` y `[OPENAI CLOUD] <<< Respuesta exitosa...`.
* **`.env`:**
  * Archivo de variables de entorno activo con la clave API de OpenAI, `LLM_PROVIDER=openai` y `OPENAI_MODEL=gpt-5.6-luna`.
  * Protegido en `.gitignore` para no filtrarse en el control de versiones.

### Archivos Modificados:
* **`app/config.py`:**
  * Se añadieron los campos: `llm_provider`, `openai_api_key`, `openai_model`, `openai_base_url` y `openai_timeout`.
* **`.env.example`:**
  * Se documentaron las nuevas variables de entorno para que cualquier despliegue futuro sea inmediato.
* **`app/services/rag_service.py`:**
  * `answer_query()`: Desacoplado de la URL local de Ollama. Ahora invoca a `llm_client.chat_completion()`.
  * `generate_multi_queries_async()` y `normalize_slang_with_llm()`: Adaptadas para consultar el LLM activo de forma asíncrona/síncrona.
* **`app/services/telemetry_service.py`:**
  * `generate_ai_observability_insights()` y `draft_procedure_with_ai()` ahora generan informes ejecutivos y procedimientos Markdown usando el cliente LLM unificado.
* **`app/services/clustering_service.py`:**
  * `summarize_cluster_topic()` adaptado para titular clusters mediante `llm_client`.
* **`app/routers/admin_router.py`:**
  * El endpoint de diagnóstico `/admin/system-status` ahora evalúa la salud de OpenAI y reporta `provider: "openai"`, manteniendo compatibilidad con la interfaz web de `/admin`.
* **`run.ps1`:**
  * Paso `[2/5]`: Detecta si `LLM_PROVIDER=openai` en `.env` y valida la clave.
  * **No exige ni inicia Ollama** si se está trabajando en modo nube, permitiendo arrancar el backend limpiamente sin servicios locales pesados.

---

## 4. Pruebas Realizadas y Resultados

1. **Test de Conectividad Directa con Python:**
   * Petición enviada a `https://api.openai.com/v1/chat/completions` con `model: "gpt-5.6-luna"`.
   * **Resultado:** Código HTTP 200 OK con respuesta generada en menos de 1 segundo.
2. **Test Completo de Pipeline RAG (`test_rag.py`):**
   * Pregunta: *"se me olvido la contraseña de mi correo"*.
   * Proceso ejecutado: Multi-Query Expansion -> Recuperación en ChromaDB (17 fragmentos) -> Cross-Encoder Reranker (Top-4) -> Inferencia con `gpt-5.6-luna`.
   * **Tokens consumidos:** 8.602 de entrada y 378 de salida.
   * **Salida obtenida:** Guía paso a paso oficial distinguiendo entre estudiantes de primer semestre y estudiantes regulares, enlaces al portal de la Universidad Simón Bolívar y canales de soporte en Barranquilla y Cúcuta.
3. **Test de Diagnóstico `/admin/system-status`:**
   * Retorna `llm.active: True`, `provider: "openai"`, `active_model: "gpt-5.6-luna"`.

---

## 5. Explicación sobre el Dashboard de Facturación/Métricas de OpenAI

Si al revisar la consola web de OpenAI (sección *Uso / Usage*) los gráficos muestran 0 o `$0.00`:
1. **Retraso de reporte (15 a 45 minutos):** Los gráficos de OpenAI tienen un tiempo de propagación; no se actualizan en el mismo segundo de la llamada.
2. **Filtro de Proyecto:** En la parte superior de la interfaz de OpenAI suele estar seleccionado *"Proyecto predeterminado"*. Si la clave API pertenece a un proyecto específico o a la organización, se debe cambiar el filtro a *"Todos los proyectos"* o inspeccionar la pestaña *"Claves API"*.
3. **Monto en fracciones de centavo:** Las pruebas realizadas consumieron ~17.000 tokens en total, lo que representa apenas **$0.0034 USD** (un tercio de centavo). El panel suele mostrar `$0.00` hasta acumular cifras mayores.
4. **Filtro de Saludos:** Saludos iniciales como *"Hola"* o *"Buenos días"* devuelven plantillas estáticas de bienvenida diseñadas expresamente para no consumir saldo de la API. La llamada a OpenAI se dispara cuando el usuario formula su consulta o problema técnico.

---

## 6. Guía Rápida para la Nueva Sesión

### ¿En qué rama estamos?
* Todo el trabajo se encuentra en la rama: **`ultimo`**.

### ¿Cómo arrancar el proyecto?
Abre PowerShell en la raíz del proyecto y ejecuta:
```powershell
.\run.ps1
```
En el paso `[2/5]` verás:
```text
[OK] Proveedor en la nube: OpenAI (gpt-5.6-luna)
     [ESTRICTO] Modelo local (Ollama) DESHABILITADO. Modo 100% Cloud activo.
     Toda inferencia y generacion se procesa exclusivamente con OpenAI.
```

### ¿Cómo probar una consulta desde terminal?
Puedes correr en cualquier momento:
```powershell
.\.venv\Scripts\python test_rag.py
```
Verás en vivo la salida:
```text
[OPENAI CLOUD] >>> Enviando consulta al modelo: 'gpt-5.6-luna'...
[OPENAI CLOUD] <<< Respuesta exitosa de 'gpt-5.6-luna'! (Tokens: ...)
```

### ¿Cómo alternar de proveedor en el futuro?
En el archivo `.env`:
* **Para usar OpenAI (GPT-5.6 Luna):**
  ```env
  LLM_PROVIDER=openai
  ```
* **Para volver a Ollama local (`unimon:8b`):**
  ```env
  LLM_PROVIDER=ollama
  ```

---

## 7. Monitoreo y Desglose de Tokens (Entrada Regular vs. Caché vs. Salida)

Para auditar y estar 100% al tanto del gasto de cada categoría de tokens:

### A. En tu propia Terminal en Tiempo Real
Cada vez que el asistente responde, verás en la consola de PowerShell el desglose exacto calculado por la respuesta oficial de la API:
```text
[OPENAI CLOUD] <<< Respuesta exitosa de 'gpt-5.6-luna'!
               - Entrada regular ($0.20/1M):  2450 tokens
               - Entrada en CACHÉ ($0.02/1M): 6152 tokens
               - Salida generada ($1.20/1M):  378 tokens
```

### B. En el Dashboard Web de OpenAI (Sección "Uso")
En la pantalla de OpenAI que estabas revisando:
1. **Pestaña "Almacenamiento en caché de avisos" (Prompt Caching):**
   * Muestra la gráfica dividida entre **"Tokens leídos de la caché"** ($0.02) y **"Tokens no almacenados en caché"** ($0.20).
2. **Pestaña "Respuestas y finalización de chats":**
   * Muestra los **"Tokens de salida"** (Completion tokens) cobrados a $1.20 por millón.
3. **Pestaña "Categorías de gasto":**
   * Agrupa el gasto en dólares por cada concepto específico.

### C. En el Panel Administrativo Oficial (`http://localhost:8000/admin`)
Se añadió una tarjeta visual en la pestaña de **Métricas y Telemetría** que muestra en vivo:
* 📥 **Entrada Regular:** Tokens no cacheados y costo en USD ($0.20 / 1M).
* ⚡ **Entrada en CACHÉ:** Tokens leídos de memoria caché con indicador de 90% de ahorro ($0.02 / 1M).
* 📤 **Salida Generada:** Tokens de respuesta y costo en USD ($1.20 / 1M).
* 💰 **Gasto Estimado en Período:** Total acumulado en USD y su conversión aproximada a pesos colombianos (COP).
* En la pestaña **Diagnóstico y Servidor**, se muestra `Proveedor IA Activo: OPENAI` con el modelo `gpt-5.6-luna` y estado `🟢 En línea`.


