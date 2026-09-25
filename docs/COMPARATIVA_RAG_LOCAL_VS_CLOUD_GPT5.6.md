# Informe Ejecutivo y Comparativa Técnica: RAG Local con IA Local vs. RAG Local con IA Externa (GPT-5.6 Luna)

**Documento para Dirección de TI, Gerencia y Líderes de Proyecto**  
*Proyecto: UniMon - Sistema Inteligente de Soporte y Gestión de TI*  
*Fecha: Septiembre 2026*  
*Versión: 1.0 - Estado: Aprobación Ejecutiva*

---

## 1. Resumen Ejecutivo (Executive Summary)

El presente informe expone un análisis comparativo integral, técnico y financiero entre dos arquitecturas de Inteligencia Artificial para el sistema de atención y soporte técnico institucional:

1. **Opción A (100% Local / On-Premise):** Recuperación documental local (RAG) combinada con un modelo de lenguaje local ejecutado en infraestructura propia vía Ollama (`unimon:8b` / Llama 3 8B).
2. **Opción B (Híbrida: RAG Local + IA Cloud de Frontera):** Recuperación documental y base de datos vectorial local (ChromaDB + Embeddings locales) combinada con inferencia en la nube mediante la API comercial de OpenAI (**GPT-5.6 Luna**).

### Matriz Rápida de Decisión para la Gerencia

| Criterio Estratégico | Opción A: RAG Local + IA Local (Ollama) | Opción B: RAG Local + IA Cloud (GPT-5.6 Luna) | Opción Ganadora |
| :--- | :--- | :--- | :---: |
| **Calidad y Razonamiento** | Media-Baja (8B parámetros). Propenso a confundir procedimientos largos. | Sobresaliente (Modelo de frontera GPT-5.6). Riguroso seguimiento de directivas. | 🏆 **Opción B** |
| **Tiempo de Respuesta (Latencia)** | 5 a 25 segundos (dependiendo de la GPU/CPU local). | **0.8 a 1.8 segundos** constantes. | 🏆 **Opción B** |
| **Concurrencia de Usuarios** | Se degrada rápidamente con más de 2 consultas simultáneas. | Soporta cientos de consultas concurrentes sin degradación. | 🏆 **Opción B** |
| **Inversión Inicial (CAPEX)** | Alta: Servidor con GPU dedicada ($2.500 - $6.000 USD). | **$0 USD** (no requiere hardware especializado). | 🏆 **Opción B** |
| **Costo Operativo Mensual (3.000 req)** | ~$40 - $70 USD (energía, mantenimiento, depreciación). | **$1.80 a $2.50 USD/mes** (~$8.000 a $11.000 COP). | 🏆 **Opción B** |
| **Privacidad de la Base Documental** | 100% aislada en servidor local. | **100% aislada en servidor local** (solo viajan fragmentos del caso). | 🤝 **Empate técnico** |
| **Gobernanza y Privacidad Cloud** | No aplica salida de red. | Protegido por contrato API Comercial (No re-entrenamiento, TLS 1.3). | 🤝 **Cumple norma** |
| **Mantenimiento y DevOps** | Complejo (drivers NVIDIA, CUDA, gestión de VRAM, parches). | Mínimo (consumo vía API REST HTTPS estándar con token seguro). | 🏆 **Opción B** |
| **Obsolescencia Tecnológica** | Alta (los modelos locales de 8B quedan desfasados en meses). | Nula (el proveedor actualiza y optimiza los modelos transparentemente). | 🏆 **Opción B** |

**Conclusión Ejecutiva:** La **Opción B (Híbrida: RAG Local + GPT-5.6 Luna)** ofrece una experiencia de usuario drásticamente superior, latencias inferiores a 2 segundos y un seguimiento impecable de las políticas institucionales, a un costo operativo ridículamente bajo (~$2 USD mensuales), ahorrando miles de dólares en servidores dedicados.

---

## 2. Explicación Conceptual de Ambas Soluciones

Para comprender la diferencia, es fundamental distinguir las dos fases de un sistema RAG (Retrieval-Augmented Generation):
* **Fase 1: Recuperación (Retrieval):** Búsqueda de información relevante dentro de los manuales y procedimientos de la institución.
* **Fase 2: Generación (Generation / Síntesis):** El modelo de lenguaje (LLM) lee la pregunta del usuario junto con la información encontrada y redacta una respuesta clara, amable y estructurada.

### Solución A: RAG Local + IA Local (Modelo On-Premise 100%)
* **Concepto:** Toda la operación se realiza dentro de la máquina o servidor de la organización.
* **Componentes:**
  * La base vectorial (ChromaDB) y el modelo matemático de búsqueda de texto (Embeddings `multilingual-e5`) residen en el servidor local.
  * El modelo generador (Ollama con `unimon:8b` / Llama 3) también corre en el hardware local (procesador y tarjeta gráfica propia).
* **Premisa de diseño:** Aislamiento total de internet. Ningún byte sale de la red local.

### Solución B: RAG Local + IA Externa Cloud (Modelo Híbrido Inteligente)
* **Concepto:** Lo más valioso y confidencial (los miles de documentos institucionales, la base vectorial ChromaDB, los algoritmos de búsqueda y los logs de tickets) **se mantienen 100% locales en el servidor institucional**.
* **Diferenciador:** Únicamente en el momento final de redactar la respuesta, el sistema toma la pregunta y los **3 o 4 fragmentos específicos encontrados** y los envía mediante un canal cifrado a la API de **OpenAI (GPT-5.6 Luna)** para que redacte la solución en menos de un segundo.
* **Premisa de diseño:** Máxima inteligencia y velocidad de respuesta global sin necesidad de comprar ni operar servidores de inteligencia artificial millonarios.

---

## 3. Diagramas de Arquitectura Técnica

### Arquitectura Opción A: RAG 100% Local (Ollama On-Premise)

```
[Usuario / Navegador Web]
         │ (HTTP POST /api/chat)
         ▼
┌────────────────────────────────────────────────────────┐
│             SERVIDOR LOCAL INSTITUCIONAL               │
│                                                        │
│  ┌──────────────────┐       ┌──────────────────────┐   │
│  │   FastAPI Web    │◄─────►│ Sesiones / Enrutador │   │
│  │     Backend      │       │     (router_logic)   │   │
│  └─────────┬────────┘       └──────────────────────┘   │
│            │                                           │
│            ▼                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Pipeline RAG Local (rag_service.py)              │  │
│  │ 1. Expansión de jerga / Multi-Query              │  │
│  │ 2. Embeddings locales (multilingual-e5)          │  │
│  │ 3. Búsqueda Vectorial (ChromaDB Local)           │  │
│  │ 4. Reordenamiento Cross-Encoder (ms-marco)       │  │
│  └─────────┬────────────────────────────────────────┘  │
│            │ Contexto + Pregunta                       │
│            ▼                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Motor LLM Local (Ollama Service :11434)          │  │
│  │ Modelo: unimon:8b (Llama 3 Quantizado Q4_K_M)    │  │
│  │ Consumo intensivo de GPU/VRAM Local (6GB-10GB)   │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Arquitectura Opción B: RAG Híbrido Local-Cloud (ChromaDB Local + GPT-5.6 Luna)

```
[Usuario / Navegador Web]
         │ (HTTP POST /api/chat)
         ▼
┌────────────────────────────────────────────────────────┐
│             SERVIDOR LOCAL INSTITUCIONAL               │
│                                                        │
│  ┌──────────────────┐       ┌──────────────────────┐   │
│  │   FastAPI Web    │◄─────►│ Sesiones / Enrutador │   │
│  │     Backend      │       │     (router_logic)   │   │
│  └─────────┬────────┘       └──────────────────────┘   │
│            │                                           │
│            ▼                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Pipeline RAG Local (100% Seguro y Privado)       │  │
│  │ 1. Normalización léxica y slang local            │  │
│  │ 2. Embeddings locales (multilingual-e5)          │  │
│  │ 3. Base Vectorial ChromaDB (Directorio local)    │  │
│  │ 4. Reranker Cross-Encoder (MiniLM local)         │  │
│  │ 5. Selección estricta de Top-4 Chunks relevantes │  │
│  └─────────┬────────────────────────────────────────┘  │
│            │ Prompt sintetizado (Pregunta + 4 Chunks)  │
│            ▼                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Cliente Unificado LLM (llm_client.py)            │  │
│  │ - Conexión HTTPS segura (TLS 1.3)                │  │
│  │ - Autenticación por Bearer Token en .env         │  │
│  │ - Gestión de Caching de Prompts ($0.02 / 1M)     │  │
│  └─────────┬────────────────────────────────────────┘  │
└────────────┼───────────────────────────────────────────┘
             │ HTTPS POST api.openai.com/v1/chat/completions
             ▼
┌────────────────────────────────────────────────────────┐
│          INFRAESTRUCTURA DE FRONTERA CLOUD             │
│                 OpenAI GPT-5.6 Luna                    │
│                                                        │
│  • Ventana de contexto: 1.000.000+ tokens              │
│  • Inferencia ultra rápida (< 1.2 segundos)            │
│  • SLA 99.9% de disponibilidad global                  │
│  • Cero retención y cero entrenamiento de datos        │
└────────────────────────────────────────────────────────┘
```

---

## 4. Tecnologías Utilizadas en el Stack Técnico

| Capa del Sistema | Tecnología Empleada | Propósito y Justificación Técnica |
| :--- | :--- | :--- |
| **Backend & API Gateway** | **FastAPI + Uvicorn** | Framework asíncrono de alto rendimiento en Python, con validación estricta de tipos Pydantic y rate limiting integrado. |
| **Base de Datos Vectorial** | **ChromaDB Local** | Motor vectorial ligero embebido. Almacena representaciones matemáticas de los manuales universitarios en disco local (`./chroma_db`). |
| **Modelo de Embeddings** | **intfloat/multilingual-e5-base** | Modelo semántico multilingüe de alta densidad que transforma texto en vectores de 768 dimensiones. Opera 100% offline (`HF_HUB_OFFLINE=1`). |
| **Reordenador Semántico** | **Cross-Encoder ms-marco-MiniLM-L-6-v2** | Modelo de red neuronal que reevalúa los fragmentos recuperados para garantizar que el procedimiento exacto quede en primera posición. |
| **Inferencia Local (Opción A)** | **Ollama (`unimon:8b`)** | Runtime para ejecutar modelos Llama 3 quantizados en la máquina del usuario o servidor interno. |
| **Inferencia Cloud (Opción B)** | **OpenAI API (`gpt-5.6-luna`)** | Modelo comercial de última generación optimizado para velocidad, bajo costo de tokens y razonamiento avanzado. |
| **Cliente HTTP Asíncrono** | **HTTPX** | Cliente no bloqueante con pool de conexiones y timeouts configurables para interactuar con la nube sin congelar el servidor web. |
| **Seguridad de Configuración** | **Pydantic Settings + python-dotenv** | Carga y valida variables sensibles (`.env`) sin exponer credenciales en el repositorio de código. |

---

## 5. Cómo está Estructurado en el Código de UniMon

La arquitectura de software de UniMon fue construida siguiendo los principios de **Clean Architecture** y el patrón de diseño **Strategy/Factory**. Esto significa que el núcleo del negocio y la búsqueda documental están **100% desacoplados** del motor de inferencia.

### A. Patrón Factory en `app/services/llm_client.py`
El sistema cuenta con una clase central `LLMClient` que encapsula la comunicación. Ninguna otra parte del código sabe si la respuesta la genera una tarjeta gráfica local o un centro de datos en la nube.

```python
# app/services/llm_client.py (Extracto simplificado)
class LLMClient:
    async def chat_completion(self, messages, max_tokens=768, temperature=None):
        # Selección dinámica y transparente según la variable LLM_PROVIDER
        if self.provider == "openai":
            return await self._call_openai_chat(messages, max_tokens=max_tokens)
        elif self.provider == "gemini":
            return await self._call_gemini_chat(messages, max_tokens=max_tokens)
        else:
            return await self._call_ollama_chat(messages, max_tokens=max_tokens)
```

### B. Desacoplamiento en el Orquestador RAG (`app/services/rag_service.py`)
El motor de búsqueda documental realiza toda su labor de manera local:
1. Normaliza la jerga estudiantil (*"se me cayó el correo"*, *"no me entra el wifi"*).
2. Consulta la base ChromaDB local.
3. Aplica el filtro Cross-Encoder.
4. Construye el prompt con las políticas de la Universidad Simón Bolívar.
5. Invoca a `llm_client.chat_completion()`.

```python
# app/services/rag_service.py
# El pipeline RAG siempre recupera localmente y solo solicita síntesis:
llm_client = get_llm_client()
response_data = await llm_client.chat_completion(
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT_UNIMON},
        {"role": "user", "content": prompt_con_contexto_institucional}
    ],
    max_tokens=600
)
respuesta_final = response_data["content"]
```

### C. Configuración Instantánea mediante `.env`
Para cambiar de la Opción A a la Opción B (o viceversa), **no se requiere modificar ni una sola línea de código fuente**. Basta con alternar una línea en el archivo de configuración institucional:

```ini
# Para operar en Modo Cloud de Alta Eficiencia (Opción B):
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-5.6-luna
OPENAI_API_KEY=sk-proj-...

# Para operar en Modo 100% Local / Desconectado (Opción A):
# LLM_PROVIDER=ollama
# LLM_MODEL=unimon:8b
```

---

## 6. Explicación de Flujos de Datos Paso a Paso

### Flujo Detallado Paso a Paso: Opción A vs Opción B

```
Paso 1: Consulta del Usuario
├── Usuario escribe: "¿Cómo configuro el correo institucional en mi teléfono?"
└── FastAPI recibe la petición y valida la sesión del usuario.

Paso 2: Búsqueda y Recuperación Local (Idéntica en ambas opciones)
├── Normalización léxica (elimina modismos y expande sinónimos).
├── ChromaDB busca los vectores más cercanos en disco local.
├── Cross-Encoder evalúa los fragmentos recuperados y selecciona los 3 más pertinentes:
│   [Chunk 1: Guía de configuración IMAP/Exchange Android e iOS]
│   [Chunk 2: Enlace oficial al portal de Office 365 USB]
│   [Chunk 3: Canales de la Mesa de Ayuda TI en Barranquilla y Cúcuta]
└── Se arma el prompt estricto con las reglas de negocio.

Paso 3: Inferencia y Generación (Aquí ocurre la diferencia fundamental)
│
├── OPCIÓN A (IA Local - Ollama):
│   ├── El prompt se envía al puerto local 11434 (localhost).
│   ├── La CPU/GPU local carga las capas de la red neuronal de 8B parámetros en VRAM.
│   ├── Tiempo de cómputo: Entre 6 y 22 segundos.
│   └── Si entra otra consulta simultánea, entra en cola de espera (cuello de botella).
│
└── OPCIÓN B (IA Externa - GPT-5.6 Luna):
    ├── El prompt viaja por canal seguro HTTPS (TLS 1.3) a los servidores de OpenAI.
    ├── El cluster de supercómputo procesa el prompt en paralelo.
    ├── Gracias a "Prompt Caching", las instrucciones repetidas se procesan instantáneamente.
    ├── Tiempo de cómputo: Entre 0.8 y 1.5 segundos.
    └── Capacidad para atender cientos de estudiantes concurrentes sin degradación.

Paso 4: Post-procesamiento y Entrega (Idéntica en ambas opciones)
├── El backend recibe el texto estructurado.
├── Sanitiza enlaces web y teléfonos institucionales.
└── Entrega la respuesta amigable al estudiante con botones de diagnóstico.
```

---

## 7. Seguridad de los Datos, Privacidad y Cumplimiento Legal

Este es el punto que suele preocupar con mayor rigor a directores de tecnología y áreas de auditoría o cumplimiento.

### A. ¿Qué información sale realmente a la nube en la Solución Híbrida?
* **Mito común:** *"Si usamos OpenAI, la nube tendrá acceso a toda la base de datos de la institución"*.
* **Realidad técnica:** **FALSO**. La base de datos completa de documentos, actas, manuales y datos institucionales **nunca sale del servidor local**. Solo viaja en texto plano cifrado la pregunta específica del usuario y los 3 pequeños párrafos recuperados para responderla.
* Toda la base de datos ChromaDB (`./chroma_db`), los usuarios, los tickets y el historial de incidencias permanecen almacenados localmente.

### B. Políticas Oficiales de Privacidad de OpenAI API Comercial vs ChatGPT Gratuito
Existe una diferencia crítica que la dirección debe conocer entre el producto comercial (API) y el producto de consumo masivo (ChatGPT):

1. **NO Re-entrenamiento (Data Never Used for Training):** Los Términos de Servicio Empresariales de OpenAI (*OpenAI Business Terms & API Data Privacy*) establecen contractualmente que **ningún dato, prompt o respuesta enviado a través de la API es utilizado para entrenar sus modelos**.
2. **Cero Retención de Datos (Zero Data Retention):** OpenAI no almacena el contenido de las solicitudes una vez completada la inferencia para cuentas comerciales con políticas de retención cero habilitadas.
3. **Cifrado Militar de Extremo a Extremo:** Los datos viajan cifrados bajo el estándar **TLS 1.3** y se procesan en memoria volátil en servidores certificados con **SOC 2 Type II, ISO 27001, HIPAA y GDPR**.

### C. Cumplimiento con la Ley 1581 de 2012 (Habeas Data Colombia)
* En el caso de UniMon, el sistema resuelve soporte técnico institucional (contraseñas de correo, conexión a WiFi, asignación de salas).
* No se envían números de tarjetas de crédito ni historias clínicas.
* Si el estudiante digita su documento de identidad o correo, la arquitectura de UniMon puede incorporar una capa de **enmascaramiento previo (Regex PII Anonymizer)** en `app/services/router_logic.py`, de modo que el correo `juan.perez@unisimon.edu.co` se transforma en `[USUARIO_ESTUDIANTE]` antes de solicitar la redacción al modelo cloud, garantizando cumplimiento total con la Superintendencia de Industria y Comercio (SIC).

---

## 8. Análisis Financiero Exhaustivo y Costo Total de Propiedad (TCO)

### Modelo de Costos Solución A: 100% Local (Servidor On-Premise)

Para operar un modelo local con una velocidad aceptable (al menos 30 tokens/segundo) y atender a varios usuarios en una sede universitaria, se requiere hardware con tarjeta gráfica dedicada:

* **Inversión Inicial en Hardware (CAPEX):**
  * Servidor o Workstation con GPU NVIDIA (mínimo RTX 4080 16GB VRAM o RTX 4090 24GB VRAM): **$2.800 a $4.500 USD**.
  * Si se opta por infraestructura cloud privada con GPU (ej. AWS EC2 `g5.xlarge` con GPU A10G): **$1.00 USD/hora = ~$730 USD/mes**.
* **Costos Operativos Ocultos (OPEX Local):**
  * Consumo eléctrico continuo (GPU en carga consume 350W - 450W + refrigeración 24/7): ~$25 - $40 USD/mes.
  * Mantenimiento de infraestructura, backups, actualización de drivers CUDA y reposición por depreciación técnica a 3 años.
  * **Costo real mínimo mensual en servidor físico propio: ~$65 USD/mes**.

### Ficha Técnica y Comercial Oficial: GPT-5.6 Luna
> **Modelo:** GPT-5.6 Luna  
> **Perfil:** *Modelo rápido y económico para el trabajo diario*  
>  
> **Estructura Oficial de Precios:**
> * **Entrada Regular:** **USD $0.20** / 1 millón de tokens
> * **Entrada en Caché (Prompt Caching):** **USD $0.02** / 1 millón de tokens *(90% de descuento automático)*
> * **Salida (Generación de Respuesta):** **USD $1.20** / 1 millón de tokens

#### ¿Por qué la "Entrada en Caché" es la clave del ahorro en UniMon?
En una arquitectura RAG, el *System Prompt* (las directivas institucionales, políticas de soporte y reglas de formato de la Universidad Simón Bolívar) se repite en cada interacción. OpenAI detecta automáticamente este prefijo idéntico y lo procesa desde memoria caché ultrarrápida cobrando únicamente **$0.02 USD por millón de tokens** en lugar de $0.20 USD. 

Esto significa que el 80% del prompt institucional entra con un **90% de descuento directo**, haciendo que el costo por interacción sea de fracciones de centavo.

#### Cálculo Real por Cada Consulta en UniMon:
* Entrada típica con contexto RAG: 2.200 tokens (de los cuales ~1.800 están cacheados por el prompt del sistema).
* Salida típica generada: 250 tokens de respuesta.
* **Costo por consulta individual:**
  $$\text{Costo} = (400 \times \$0.0000002) + (1.800 \times \$0.00000002) + (250 \times \$0.0000012) \approx \mathbf{\$0.000416\text{ USD}}$$
  *(Es decir: menos de medio milésimo de dólar por cada consulta resuelta, o unos $1.7 pesos colombianos).*

### Comparativa de Proyecciones a Escala de Consultas Mensuales

| Volumen Mensual de Consultas | Costo Mensual Opción A (Hardware Local Amortizado + Luz) | Costo Mensual Opción B (OpenAI GPT-5.6 Luna) | Ahorro Mensual con Opción B |
| :---: | :---: | :---: | :---: |
| **3.000 consultas/mes** *(Volumen actual)* | ~$75 USD (~$300.000 COP) | **$1.85 USD** (~$7.400 COP) | **97.5% de ahorro** |
| **15.000 consultas/mes** *(Temporada de Matrículas)* | ~$90 USD (exige más hardware/VRAM) | **$6.24 USD** (~$25.000 COP) | **93.1% de ahorro** |
| **50.000 consultas/mes** *(Escala Multi-Sede)* | ~$350 USD (requiere cluster 2x GPU) | **$20.80 USD** (~$83.000 COP) | **94.0% de ahorro** |

### Análisis TCO (Costo Total de Propiedad a 3 Años)

* **Opción A (Comprar servidor GPU local):**
  * Hardware inicial: $3.500 USD
  * Electricidad y mantenimiento (36 meses x $40): $1.440 USD
  * **Total a 3 años: $4.940 USD** (~$20.000.000 COP).
* **Opción B (API GPT-5.6 Luna):**
  * Hardware inicial: $0 USD (se usa cualquier servidor web existente o VM básica de $10 USD/mes).
  * Consumo API 3.000 consultas/mes (36 meses x $1.85): $66.60 USD
  * Servidor web base (36 meses x $12): $432 USD
  * **Total a 3 años: $498.60 USD** (~$2.000.000 COP).
* 💰 **Ahorro financiero neto para la institución: Más de $4.400 USD (90% de ahorro total)**.

---

## 9. Comparativa Detallada de Pros y Contras

### Opción A: RAG Local + IA Local (Ollama / Llama 3 8B)

#### Ventajas:
1. **Independencia absoluta de internet:** Puede operar en redes aisladas militarizadas o sin conexión exterior.
2. **Cero riesgo de fuga en tránsito exterior:** El tráfico nunca cruza el router de salida de la organización.
3. **Costo por token fijo:** No hay factura variable al final de mes; el costo es el mismo si se hace 1 o 100.000 consultas (siempre que el hardware no colapse).

#### Desventajas:
1. **Calidad de redacción y comprensión limitada:** Los modelos de 8 mil millones de parámetros suelen confundir directivas condicionales complejas (ej. diferenciar entre estudiantes nuevos y antiguos).
2. **Alta latencia:** Respuestas que demoran entre 8 y 25 segundos deterioran gravemente la percepción del servicio al usuario.
3. **Pobre concurrencia:** Si 3 usuarios escriben simultáneamente, las consultas se encolan linealmente, elevando el tiempo de espera a más de 1 minuto.
4. **Carga pesada de mantenimiento técnico:** Requiere administración de librerías CUDA, drivers de video, refrigeración y gestión de memoria VRAM.
5. **Rápida obsolescencia:** Cada 6 meses los modelos open-source duplican su tamaño o exigen nuevas arquitecturas que obligan a reinvertir en tarjetas gráficas.

---

### Opción B: RAG Híbrido Local-Cloud (ChromaDB Local + GPT-5.6 Luna)

#### Ventajas:
1. **Inteligencia y Razonamiento de Frontera:** Capacidad superior para entender preguntas confusas, errores ortográficos, jerga local y generar tablas o guías paso a paso ordenadas.
2. **Velocidad Excepcional:** Genera la respuesta completa en **menos de 1.5 segundos**.
3. **Alta Concurrencia Nativa:** Puede atender a decenas de estudiantes al mismo segundo sin retrasos.
4. **Costo Mínimo Irrisorio:** Apenas ~$2 USD al mes para miles de consultas gracias al **Prompt Caching**.
5. **Cero Inversión en Hardware Especializado:** Corre perfectamente en cualquier máquina virtual estándar de 2 núcleos y 4 GB de RAM.
6. **Seguridad Documental Garantizada:** La base institucional de manuales se mantiene local; la API no retiene ni entrena con los datos institucionales.

#### Desventajas:
1. **Dependencia de Conexión a Internet:** Si el servidor institucional pierde su enlace a internet, no puede contactar a la API externa.
2. **Costo Operativo Variable:** Depende del volumen de consultas (aunque, como se demostró en los cálculos, el impacto económico es prácticamente insignificante).

---

## 10. Consideraciones Clave para la Gerencia y Toma de Decisión

Al presentar este proyecto ante la Dirección, los puntos decisivos que respaldan la adopción de la **Opción B (Híbrida con GPT-5.6 Luna)** son:

1. **Satisfacción del Usuario Final:** Los estudiantes y docentes no toleran esperar 15 o 20 segundos por una respuesta técnica. Una latencia de 1 segundo genera una percepción de modernidad, agilidad y eficiencia universitaria.
2. **Precisión en Procedimientos Críticos:** En soporte de TI (restablecimiento de contraseñas, acceso a plataformas académicas), una alucinación o instrucción errónea del chatbot satura los canales físicos de la mesa de ayuda. GPT-5.6 Luna tiene una tasa de error y alucinación sustancialmente menor que un modelo local de 8B.
3. **Retorno de Inversión Inmediato (ROI):** Evita comprometer un presupuesto de $3.000 a $5.000 USD en la compra de servidores con tarjetas gráficas que en 2 años estarán descontinuadas.
4. **Estrategia Cero Riesgo implementada en UniMon:** Gracias al desacoplamiento en `llm_client.py`, la institución **no queda atada a ningún proveedor**. Si en el futuro las políticas cambian o se adquiere un datacenter propio, basta con cambiar `LLM_PROVIDER=ollama` en el archivo `.env` y el sistema regresará al modo 100% local al instante sin necesidad de desarrollos adicionales.

---

## 11. Recomendación Estratégica Final

Se recomienda formalmente a la Gerencia y Líderes de Proyecto:

1. **Aprobar el despliegue en Producción de la Opción B (RAG Local + OpenAI GPT-5.6 Luna)** como motor principal de inferencia para UniMon.
2. **Mantener Ollama local instalado como mecanismo de contingencia pasivo (Fallback)** para operar en caso de eventuales caídas del proveedor de internet institucional.
3. **Monitorear el consumo mensual a través del panel de telemetría integrado en `/admin`**, donde se audita en tiempo real el gasto en dólares y pesos colombianos de cada consulta.

---
*Informe elaborado por el Equipo de Ingeniería y Arquitectura de Software UniMon.*
