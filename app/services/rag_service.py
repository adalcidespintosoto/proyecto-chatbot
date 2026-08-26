"""
Servicio RAG Local con ChromaDB, Embeddings Multilingües, Normalizador Léxico y Ollama (Llama 3.1:8B).
Provee respuestas estrictas de soporte técnico y gestión de TI para la Universidad Simón Bolívar
(Sedes Barranquilla y Cúcuta, Colombia) basadas en documentos y procedimientos institucionales indexados.
Aplica normalización léxica, expansión LLM de consultas, Cross-Encoder Reranker y corte calibrado a 0.48.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.services.normalizer_service import normalize_and_expand_query

logger = logging.getLogger("unimon.rag_service")

# Umbral mínimo de similitud para considerar relevante un fragmento recuperado (calibrado a 0.48)
MIN_RELEVANCE_SCORE_THRESHOLD = 0.48

# Pregunta estandarizada de cierre para diagnósticos y quick replies
CLOSING_FEEDBACK_QUESTION = (
    "\n\n¿Pudiste resolver tu problema con estos pasos?\n"
    "- Selecciona o escribe **Sí** si te funcionó.\n"
    "- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte."
)

QUICK_REPLIES_DIAGNOSTICO = [
    {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
    {"label": "🔄 No me funcionó", "payload": "RETRY_DIAGNOSIS"},
    {"label": "🎫 Generar reporte", "payload": "CREATE_TICKET"}
]

# =============================================================================
# CROSS-ENCODER RERANKER (Módulo 3: Reordenamiento semántico de alta precisión)
# =============================================================================
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_reranker = None


def get_reranker() -> Optional[CrossEncoder]:
    """Inicialización diferida (singleton) del Cross-Encoder Reranker."""
    global _reranker
    if _reranker is None:
        try:
            logger.info(f"Cargando Cross-Encoder Reranker '{RERANKER_MODEL_NAME}'...")
            _reranker = CrossEncoder(RERANKER_MODEL_NAME)
            logger.info("Cross-Encoder Reranker cargado exitosamente.")
        except Exception as e:
            logger.warning(f"No se pudo cargar CrossEncoder ({e}). Se usará ranking nativo de ChromaDB.")
    return _reranker


def rerank_chunks(query: str, retrieved_docs: list, top_k: int = 3) -> list:
    """
    Reordena los fragmentos recuperados mediante Cross-Encoder para máxima precisión semántica.
    
    Args:
        query: La consulta del usuario (expandida o normalizada).
        retrieved_docs: Lista de tuplas (doc, score) provenientes de ChromaDB.
        top_k: Número máximo de fragmentos a retornar tras el reranking.
    
    Returns:
        Lista de tuplas (doc, score) reordenadas por relevancia semántica real.
    """
    if not retrieved_docs or len(retrieved_docs) <= top_k:
        return retrieved_docs

    reranker = get_reranker()
    if not reranker:
        return retrieved_docs[:top_k]

    try:
        pairs = [[query, doc.page_content.strip()] for doc, _ in retrieved_docs]
        scores = reranker.predict(pairs)

        # Asignar scores del cross-encoder y ordenar
        scored_docs = []
        for i, rerank_score in enumerate(scores):
            doc, original_score = retrieved_docs[i]
            scored_docs.append((doc, original_score, float(rerank_score)))

        ranked = sorted(scored_docs, key=lambda x: x[2], reverse=True)
        result = [(doc, orig_score) for doc, orig_score, _ in ranked[:top_k]]

        logger.info(
            f"[Reranker] Reordenados {len(retrieved_docs)} fragmentos -> Top-{top_k}. "
            f"Mejor score reranker: {ranked[0][2]:.4f}"
        )
        return result
    except Exception as e:
        logger.warning(f"[Reranker] Error reordenando fragmentos: {e}")
        return retrieved_docs[:top_k]


# =============================================================================
# QUERY EXPANSION LLM (Módulo 2: Traducción de jerga a terminología institucional)
# =============================================================================

def expand_and_normalize_query_llm(raw_query: str, user_role: str = "general") -> str:
    """
    Traduce jerga informal estudiantil a términos técnicos institucionales mediante Ollama.
    Complementa la expansión léxica estática del normalizer_service.
    
    Args:
        raw_query: Consulta original del usuario (puede contener jerga, modismos, etc.).
        user_role: Rol del usuario para contextualización (estudiante, profesor, etc.).
    
    Returns:
        Consulta normalizada a terminología institucional formal, o la original si falla.
    """
    system_prompt = (
        "Eres un asistente que normaliza consultas universitarias para búsqueda documental.\n"
        "Convierte la consulta del usuario en 1 frase formal con palabras clave institucionales "
        "(SIAAF, Kactus, Teams, Portal Estudiantes, etc.).\n"
        "Mantén nombres de trámites oficiales (prematrícula, inasistencias, notas, certificados).\n"
        "Responde ÚNICAMENTE la frase normalizada, sin explicaciones ni saludos."
    )

    try:
        settings = get_settings()
        ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

        response = httpx.post(
            ollama_url,
            json={
                "model": settings.llm_model,
                "system": system_prompt,
                "prompt": f"Rol: {user_role}\nConsulta informal: {raw_query}\nConsulta técnica formal:",
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 30}
            },
            timeout=3.0
        )
        if response.status_code == 200:
            expanded = response.json().get("response", "").strip()
            if expanded and len(expanded) > 4:
                logger.info(f"[QueryExpansion] '{raw_query[:40]}...' -> '{expanded[:60]}...'")
                return expanded
    except Exception as e:
        logger.warning(f"[QueryExpansion] Error en expansión LLM ({e}), usando consulta original.")

    return raw_query

# Mensaje oficial estándar cuando no existe procedimiento documentado en ChromaDB
MENSAJE_NO_DOCUMENTADO = (
    "No dispongo de un instructivo o procedimiento institucional documentado para responder a tu solicitud, "
    "o se trata de una labor técnica/física especializada que debe ser atendida directamente por el personal de TI.\n\n"
    "Puedes comunicarte directamente con los canales oficiales de soporte técnico:\n"
    "📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | PBX: (605) 3444333 Ext. 8003 / 8004\n"
    "📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129\n\n"
    "¿O prefieres que radique un caso de soporte técnico por ti ahora mismo?"
)

# Prompt del sistema institucional para soporte técnico N1 directo
STRICT_SYSTEM_PROMPT_TEMPLATE = """Eres UniMon, el Agente Oficial de Soporte Técnico N1 de la Universidad Simón Bolívar.

REGLAS DE ORO OBLIGATORIAS:
1. PROHIBICIÓN TOTAL DE REFERENCIAR MANUALES AL USUARIO: NUNCA le digas al usuario "revisa el instructivo", "consulta el PDF", "dirígete a la presentación" o "sigue los pasos del documento X". Tú eres el soporte: extrae los pasos del contexto y redacta la solución directa en tu mensaje.
2. PROHIBICIÓN TOTAL DE PLACEHOLDERS Y ENLACES FALSOS: NUNCA inventes placeholders como "[URL del GLPI]", "[Enlace]", "[Link]", "[URL]", "[Insertar URL]". NUNCA le digas al usuario que ingrese a GLPI ni que se asigne tickets manualmente. Solo usa URLs completas si aparecen textualmente en el contexto provisto (ej: https://unisimon.edu.co).
3. GUÍA ACCIONABLE PASO A PASO: Si el procedimiento es de autoservicio digital (portales, claves, teams, office, carnet, siaaf, kactus, seven), explica con claridad qué debe hacer el usuario (Paso 1: Entra a [URL/Opción], Paso 2: Haz clic en [Botón/Menú], Paso 3: Diligencia [Campo]).
4. SOPORTE DE HARDWARE, REDES FÍSICAS O DAÑOS DE EQUIPOS: Si la consulta es una falla física (pantalla rota o sin video, cable dañado, puerto dañado, pc no enciende o red cableada) que requiere atención presencial de TI:
   - Proporciona únicamente 1 o 2 descartes básicos (verificar cables conectados y encendido).
   - Informa los canales oficiales de soporte (solicitudcomputo@unisimon.edu.co en Barranquilla / helpdesk@unisimon.edu.co en Cúcuta).
   - Pregunta si desea que se radique el reporte de soporte técnico.
5. Finaliza siempre preguntando:
   "¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte."
6. Si el contexto NO contiene los pasos de solución, responde únicamente:
   "No dispongo de un instructivo institucional documentado para este caso específico. Puedes reportarlo a solicitudcomputo@unisimon.edu.co (Barranquilla) / helpdesk@unisimon.edu.co (Cúcuta) o indicarme si deseas que radique un caso de soporte técnico por ti."

Contexto institucional provisto:
{context}

Pregunta del usuario: {query}
Respuesta directa de soporte:"""


OUT_OF_DOMAIN_QUERY_PATTERNS = [
    r"\b(receta|recetas|cocinar|arroz con pollo|pastel|comida|capital de|geograf[ií]a|poema|poemas|chiste|chistes|qui[eé]n gan[oó] el mundial|qui[eé]n es el presidente)\b"
]

MENSAJE_FUERA_DE_DOMINIO = (
    "Soy UniMon, tu asistente virtual enfocado exclusivamente en soporte técnico y procedimientos institucionales de la Universidad Simón Bolívar. "
    "No puedo ayudarte con consultas de cultura general, recetas u otros temas no tecnológicos ni institucionales."
)


def is_out_of_domain_query(query_text: str) -> bool:
    """
    Detecta si la consulta del usuario corresponde a temas manifiestamente fuera de dominio.
    """
    q_lower = query_text.lower().strip()
    return any(re.search(pat, q_lower) for pat in OUT_OF_DOMAIN_QUERY_PATTERNS)


def is_out_of_domain_response(response_text: str) -> bool:
    """
    Detecta si la respuesta generada corresponde a un rechazo fuera de dominio (Guardrail institucional).
    """
    text_lower = response_text.lower()

    # Si contiene indicaciones de hardware, soporte, diagnóstico o solución técnica, NO es fuera de dominio
    if any(m in text_lower for m in [
        "paso 1", "paso 2", "1.", "2.", "cable", "monitor", "pantalla", "proyector",
        "computador", "portátil", "portatil", "kactus", "seven", "contraseña", "contrasena",
        "reiniciar", "conectar", "descarte", "verificar si", "intentar conectar"
    ]):
        # A menos que sea explícitamente un rechazo claro de geografía, recetas o cultura general
        if any(rej in text_lower for rej in ["recetas de cocina", "receta para", "cultura general", "geografía", "geografia", "capital de"]):
            return True
        return False

    guardrail_markers = [
        "exclusivamente en soporte",
        "tema tecnológico o institucional",
        "no se relaciona con tecnología",
        "no está relacionada con tecnología",
        "no esta relacionada con tecnologia",
        "fuera de mi dominio",
        "fuera de nuestro dominio",
        "no puedo proporcionar recetas",
        "no puedo proporcionar información sobre",
        "no puedo proporcionar informacion sobre",
        "cultura general",
        "geografía",
        "geografia",
        "capital de hungría",
        "capital de hungria",
        "asistente enfocado exclusivamente"
    ]
    return any(marker in text_lower for marker in guardrail_markers)


class RAGService:
    """
    Servicio RAG local para recuperación de contexto con ChromaDB y generación con Ollama.
    Aplica normalización léxica y expansión de consultas para asertividad >= 90%,
    umbral de relevancia >= 0.48 y corte estricto contra alucinaciones.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        chroma_db_dir: Optional[str] = None,
        embedding_model: Optional[str] = None,
        min_relevance_score: float = MIN_RELEVANCE_SCORE_THRESHOLD
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = settings.ollama_timeout
        self.chroma_db_dir = Path(chroma_db_dir or settings.chroma_db_dir)
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.min_relevance_score = min_relevance_score

        self._embeddings = None
        self._vector_store = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Inicialización diferida (lazy-load) del modelo de embeddings."""
        if self._embeddings is None:
            logger.info(f"Cargando modelo de embeddings '{self.embedding_model_name}'...")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                encode_kwargs={"normalize_embeddings": True}
            )
        return self._embeddings

    @property
    def vector_store(self) -> Optional[Chroma]:
        """Inicialización diferida de ChromaDB persistente."""
        if self._vector_store is None:
            try:
                self.chroma_db_dir.mkdir(parents=True, exist_ok=True)
                self._vector_store = Chroma(
                    persist_directory=str(self.chroma_db_dir),
                    embedding_function=self.embeddings
                )
                logger.info(f"ChromaDB cargado exitosamente desde {self.chroma_db_dir.resolve()}")
            except Exception as exc:
                logger.warning(f"No se pudo inicializar ChromaDB en {self.chroma_db_dir}: {exc}")
                self._vector_store = None
        return self._vector_store

    def reload_vector_store(self) -> None:
        """
        Fuerza la recarga de ChromaDB en memoria para reflejar nuevos documentos indexados.
        """
        logger.info("Recargando instancia de ChromaDB en memoria...")
        self._vector_store = None
        _ = self.vector_store

    def _build_role_filter(self, user_role: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Construye la condición de filtrado en ChromaDB según el rol del usuario:
        - Otros / Visitante / Sin Rol: Acceso irrestricto a toda la base documental (sin filtro de audiencia, retorna None).
        - Administrativo / Funcionario / Admin TI: Accede a documentos de general, administrativo, funcionario, profesor y admin_ti.
        - Profesor / Docente: Accede a documentos de general, profesor, docente y estudiante.
        - Estudiante: Accede a documentos y guías para estudiantes y general.
        """
        if not user_role:
            return None

        role_lower = user_role.strip().lower()

        if role_lower in ["otros", "otro", "visitante", "visitantes", "aspirante", "aspirantes", "egresado", "egresada", "externo", "externa", "general"]:
            # Acceso total irrestricto sin filtros
            return None
        elif role_lower in ["administrativo", "administrativa", "funcionario", "funcionaria", "admin_ti"]:
            return {
                "audience": {"$in": ["general", "administrativo", "funcionario", "profesor", "admin_ti"]}
            }
        elif role_lower in ["profesor", "profesora", "docente"]:
            return {
                "audience": {"$in": ["general", "profesor", "docente", "estudiante"]}
            }
        elif role_lower in ["estudiante", "alumno", "alumna"]:
            return {
                "audience": {"$in": ["general", "estudiante"]}
            }
        return None

    async def query_rag(
        self,
        question: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_role: Optional[str] = None,
        golden_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline RAG completo:
        1. Expansión LLM de consulta (jerga -> terminología institucional).
        2. Normalización léxica estática (complementaria).
        3. Búsqueda por similitud con puntuación de relevancia en ChromaDB (k=8, umbral >= 0.48) y filtro por rol.
        4. Cross-Encoder Reranker: reordena Top-8 -> Top-3.
        5. Corte estricto / Fallback temático: Si ningún fragmento supera el umbral, evalúa fallback.
        6. Ensamblaje del System Prompt institucional + Golden Cache context + historial.
        7. Invocación asíncrona a Ollama (unimon:8b).
        """
        retrieved_docs = []
        sources: List[str] = []
        context_parts = []

        filter_condition = self._build_role_filter(user_role)

        # 1. Expansión LLM de consulta (traduce jerga a términos institucionales)
        llm_expanded = expand_and_normalize_query_llm(question, user_role or "general")

        # 2. Normalización léxica estática (complementaria)
        lexical_expanded = normalize_and_expand_query(question)

        # Usar la expansión LLM si difiere del original; si no, usar la léxica
        if llm_expanded != question:
            expanded_query = llm_expanded
            logger.info(f"Query expandido por LLM: '{expanded_query[:80]}...'")
        elif lexical_expanded != question.lower().strip():
            expanded_query = lexical_expanded
            logger.info(f"Query expandido léxicamente: '{expanded_query[:80]}...'")
        else:
            expanded_query = question

        # 3. Búsqueda por similitud con puntuación de relevancia en ChromaDB (k=8 para reranking)
        valid_docs_with_scores = []
        if self.vector_store is not None:
            try:
                filter_desc = f" con filtro {filter_condition}" if filter_condition else " sin filtro"
                logger.info(f"Buscando fragmentos en ChromaDB (k=8, umbral >= {self.min_relevance_score}{filter_desc}) para: '{expanded_query[:60]}...'")
                
                if filter_condition:
                    docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                        expanded_query,
                        k=8,
                        filter=filter_condition
                    )
                else:
                    docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                        expanded_query,
                        k=8
                    )
                
                for idx, (doc, score) in enumerate(docs_with_scores, 1):
                    score_val = f"{score:.4f}" if score is not None else "N/A"
                    source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                    source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                    page_num = doc.metadata.get("page", None)
                    page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""

                    if score is not None and score >= self.min_relevance_score:
                        valid_docs_with_scores.append((doc, score))
                        logger.info(f"  [Chunk #{idx} VÁLIDO] Score: {score_val} | Fuente: {source_filename}{page_info} | Texto: '{doc.page_content.strip()[:100]}...'")
                    else:
                        logger.info(f"  [Chunk #{idx} DESCARTADO] Score: {score_val} < {self.min_relevance_score} | Fuente: {source_filename}{page_info}")
            except Exception as exc:
                logger.warning(f"Error al realizar búsqueda de similitud en ChromaDB: {exc}")

        # 4. Cross-Encoder Reranker: reordenar y seleccionar Top-3
        if valid_docs_with_scores:
            reranked = rerank_chunks(expanded_query, valid_docs_with_scores, top_k=3)
            for doc, score in reranked:
                retrieved_docs.append(doc)
                source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                page_num = doc.metadata.get("page", None)
                page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""
                if source_filename not in sources:
                    sources.append(source_filename)
                context_parts.append(f"[{source_filename}{page_info}]\n{doc.page_content.strip()}")

        # 3. Si ningún fragmento superó el umbral, evaluar fallback temático o mensaje estándar
        if not context_parts:
            # Si contiene palabras clave temáticas conocidas, entregar respuesta guiada temática
            q_lower = question.lower()
            if any(k in q_lower for k in [
                "portal", "correo", "teams", "carnet", "kactus", "seven", "backup",
                "malware", "virus", "computador", "portatil", "pantalla", "clave", "contraseña"
            ]):
                logger.info("Activando fallback temático institucional por coincidencia de categoría.")
                return self._generate_fallback_response(question, user_name, sources)

            logger.info(f"Cero fragmentos con score >= {self.min_relevance_score}. Retornando mensaje institucional estricto sin invocar LLM.")
            return {
                "response": MENSAJE_NO_DOCUMENTADO,
                "sources": [],
                "source": "unimon_no_doc_fallback",
                "model": None,
                "retrieved_chunks": 0,
                "has_context": False
            }

        context_text = "\n\n---\n\n".join(context_parts)

        # 5. Ensamblar System Prompt estricto + Golden Cache few-shot + historial y User Prompt
        system_prompt = STRICT_SYSTEM_PROMPT_TEMPLATE.format(context=context_text, query=question)
        if golden_context:
            system_prompt += golden_context
        user_greeting = f"El usuario se llama {user_name}. " if user_name else ""
        role_ctx = f"[Rol del usuario: {user_role}] " if user_role else ""
        user_prompt = f"{user_greeting}{role_ctx}Consulta del usuario: {question}"

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": user_prompt})

        # 5. Llamada asíncrona a Ollama API
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }

        url = f"{self.base_url}/api/chat"

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Enviando consulta a Ollama ({url}) con modelo '{self.model}'...")
                response = await client.post(url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    bot_message = data.get("message", {}).get("content", "").strip()
                    prompt_tokens = data.get("prompt_eval_count", 0) or 0
                    eval_tokens = data.get("eval_count", 0) or 0
                    logger.info("Respuesta generada exitosamente por Ollama (tokens: %s prompt, %s eval).", prompt_tokens, eval_tokens)

                    # Sanitizar placeholders y menciones a GLPI
                    clean_msg = re.sub(r"\[(?:URL|Link|Enlace)?\s*(?:del?|al?)?\s*GLPI\]", "la Mesa de Ayuda TI", bot_message, flags=re.IGNORECASE)
                    clean_msg = re.sub(r"\bGLPI\b", "Mesa de Ayuda TI", clean_msg)
                    clean_msg = re.sub(r"\[(?:URL|Enlace|Link|Insertar URL)\]", "", clean_msg, flags=re.IGNORECASE)
                    bot_message = clean_msg.strip()
                    
                    if "¿pudiste resolver tu problema con estos pasos?" not in bot_message.lower() and "¿te sirvieron estos pasos" not in bot_message.lower():
                        bot_message = bot_message.rstrip() + CLOSING_FEEDBACK_QUESTION

                    return {
                        "response": bot_message,
                        "sources": sources,
                        "source": f"ollama_{self.model}",
                        "model": self.model,
                        "retrieved_chunks": len(retrieved_docs),
                        "has_context": True,
                        "quick_replies": QUICK_REPLIES_DIAGNOSTICO,
                        "prompt_tokens": prompt_tokens,
                        "eval_tokens": eval_tokens
                    }
                else:
                    logger.warning(f"Ollama respondió con código {response.status_code}: {response.text}")
                    return self._generate_fallback_response(question, user_name, sources)

        except Exception as exc:
            logger.warning(f"No se pudo conectar con el servidor Ollama ({exc}). Activando respuesta de contingencia.")
            return self._generate_fallback_response(question, user_name, sources)

    def _generate_fallback_response(
        self,
        user_message: str,
        user_name: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generador de respuesta institucional de contingencia cuando Ollama no está disponible
        o como fallback temático de alta precisión.
        """
        saludo = f"¡Hola {user_name}!" if user_name else "¡Hola!"
        msg_lower = user_message.lower()

        if any(w in msg_lower for w in ["contacto", "canal", "canales", "telefono", "teléfono", "correo", "atención", "atencion"]):
            contenido = (
                f"{saludo} Los canales oficiales de atención y soporte TI de la **Universidad Simón Bolívar (Colombia)** son:\n\n"
                "• **Sede Barranquilla:**\n"
                "  - Correo: `solicitudcomputo@unisimon.edu.co`\n"
                "  - WhatsApp: `3172683922`\n"
                "  - Teléfono: `(605) 3444333` Ext. `8003` y `8004`\n\n"
                "• **Sede Cúcuta:**\n"
                "  - Correo: `helpdesk@unisimon.edu.co`\n"
                "  - Teléfono: `(607) 5827070` Ext. `129`\n\n"
                "También puedes radicar un caso directamente en esta plataforma describiendo la falla."
            )
        elif any(w in msg_lower for w in ["portal", "portal web", "pagina", "notas", "matricula", "matrícula"]):
            contenido = (
                f"{saludo} Para el acceso a los **Portales Institucionales Unisimon** (Estudiantes y Docentes):\n\n"
                "1. Ingresa a la página oficial: `https://unisimon.edu.co` y selecciona el Portal correspondiente.\n"
                "2. Digita tu usuario institucional y tu contraseña registrada.\n"
                "3. Si olvidaste tu contraseña o el sistema indica datos incorrectos, utiliza la opción **'¿Olvidó su contraseña?'** en la pantalla de inicio o contacta a Soporte TI."
            )
        elif any(w in msg_lower for w in ["carnet", "carné", "carnet digital", "app"]):
            contenido = (
                f"{saludo} Para la gestión de tu **Carnet Digital** en la **App Unisimon**:\n\n"
                "1. Descarga la App Unisimon desde Google Play Store o Apple App Store.\n"
                "2. Inicia sesión con tus credenciales de correo institucional.\n"
                "3. Ingresa a la sección 'Carnet Digital'. Si no visualizas tu foto o carnet, valida tu estado de matrícula con Registro Académico o reporta la incidencia a TI."
            )
        elif any(w in msg_lower for w in ["teams", "reunion", "reuniones", "tim"]):
            contenido = (
                f"{saludo} Para soporte en **Microsoft Teams Institucional**:\n\n"
                "1. Asegúrate de iniciar sesión con tu cuenta `@unisimon.edu.co` y contraseña institucional.\n"
                "2. Si la aplicación de escritorio presenta bloqueo, ingresa vía web en `https://teams.microsoft.com`.\n"
                "3. Si un grupo o clase no te aparece cargado, consulta con el docente titular o el área de Registro."
            )
        elif any(w in msg_lower for w in ["backup", "copia de seguridad", "copias", "respaldo"]):
            contenido = (
                f"{saludo} Conforme al procedimiento **P-GT-10** (*Generación y Restauración de Backup de la Información*):\n\n"
                "• La Universidad realiza copias de seguridad periódicas y programadas de los sistemas y bases de datos institucionales.\n"
                "• Para solicitudes de restauración de información o requerimientos de respaldo específico, comunícate con el área de TI o radica un ticket de servicio."
            )
        elif any(w in msg_lower for w in [
            "kactus", "katuc", "kaktu", "seven", "seben", "erp", "nómina", "nomina",
            "contraseña", "contrasena", "clave", "clabe", "bloqueo", "desbloquear", "login"
        ]):
            contenido = (
                f"{saludo} Para soporte en los sistemas institucionales **Kactus / Seven** (Procedimiento **P-GT-11** y **P-GT-12**):\n\n"
                "• Las incidencias y requerimientos deben ser radicados indicando el módulo afectado, captura de pantalla del error y usuario solicitante.\n"
                "• El equipo de soporte de aplicaciones gestionará el requerimiento conforme a los acuerdos de nivel de servicio (SLA)."
            )
        elif any(w in msg_lower for w in ["virus", "malware", "antivirus", "amenaza", "infectado"]):
            contenido = (
                f"{saludo} Según el procedimiento **P-GT-07** (*Protección de Código Malicioso*):\n\n"
                "• Todo equipo institucional debe contar con la solución de protección antimalware corporativa activa y actualizada.\n"
                "• Ante sospecha de infección, desconecta el equipo de la red y notifica inmediatamente a Soporte TI."
            )
        elif any(w in msg_lower for w in [
            "computador", "conputador", "portatil", "portátil", "pantalla", "pantaya",
            "monitor", "proyector", "proyestor", "mouse", "mause", "teclado", "cable",
            "hdmi", "red", "wifi", "internet", "interner", "no prende", "parpadea", "falla"
        ]):
            contenido = (
                f"{saludo} Soy UniMon, tu asistente de Soporte Técnico de Nivel 1 de la Universidad Simón Bolívar.\n\n"
                "Para ayudarte con este inconveniente técnico, te sugiero realizar estos pasos iniciales de descarte:\n"
                "1. Verifica que los cables de poder, red o video estén firmemente conectados.\n"
                "2. Reinicia el equipo o dispositivo y verifica si el comportamiento persiste.\n"
                "3. Si el inconveniente es en un aplicativo institucional, cierra sesión y vuelve a ingresar."
            )
        else:
            contenido = MENSAJE_NO_DOCUMENTADO

        is_doc = (contenido != MENSAJE_NO_DOCUMENTADO)
        if is_doc and "¿pudiste resolver tu problema con estos pasos?" not in contenido.lower():
            contenido = contenido.rstrip() + CLOSING_FEEDBACK_QUESTION

        return {
            "response": contenido,
            "sources": sources if sources is not None else [],
            "source": "knowledge_base_fallback",
            "model": "rule_based_institutional_unisimon",
            "retrieved_chunks": 0,
            "has_context": is_doc,
            "quick_replies": QUICK_REPLIES_DIAGNOSTICO if is_doc else []
        }

    async def answer_query(
        self,
        query: str,
        user_role: Optional[str] = None,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        golden_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para responder consultas con normalización léxica,
        expansión LLM, reranking y filtrado de metadatos por rol.
        """
        return await self.query_rag(
            question=query,
            user_name=user_name,
            chat_history=chat_history,
            user_role=user_role,
            golden_context=golden_context
        )

    async def consultar(
        self,
        pregunta: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        es_diagnostico: bool = False,
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta al motor RAG de UniMon con soporte para historial de conversación y rol de usuario.
        """
        return await self.query_rag(
            question=pregunta,
            user_name=user_name,
            chat_history=chat_history,
            user_role=user_role
        )


# Instancia por defecto para importaciones limpias
rag_service = RAGService()
