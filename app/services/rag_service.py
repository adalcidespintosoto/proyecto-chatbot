"""
Servicio RAG Local con ChromaDB, Embeddings Multilingües y Ollama (Llama 3.1:8B).
Provee respuestas estrictas de soporte técnico y gestión de TI para la Universidad Simón Bolívar
(Sedes Barranquilla y Cúcuta, Colombia) basadas en documentos y procedimientos institucionales indexados.
Aplica corte estricto por umbral de relevancia (score >= 0.68) con cero alucinaciones sin invocar al LLM si no hay contexto.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import get_settings

logger = logging.getLogger("unimon.rag_service")

# Umbral mínimo de similitud para considerar relevante un fragmento recuperado
MIN_RELEVANCE_SCORE_THRESHOLD = 0.68

# Mensaje oficial estándar cuando no existe procedimiento documentado en ChromaDB
MENSAJE_NO_DOCUMENTADO = (
    "No dispongo de un instructivo o procedimiento institucional documentado para responder a tu solicitud, "
    "o se trata de una labor técnica/física especializada que debe ser atendida directamente por el personal de TI.\n\n"
    "Puedes comunicarte directamente con los canales oficiales de soporte técnico:\n"
    "📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | PBX: (605) 3444333 Ext. 8003 / 8004\n"
    "📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129\n\n"
    "¿O prefieres que radique el caso de soporte técnico directamente en GLPI por ti ahora mismo?"
)

# Prompt del sistema institucional estricto con reglas de oro contra alucinaciones
STRICT_SYSTEM_PROMPT_TEMPLATE = """Eres UniMon, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la Universidad Simón Bolívar.

REGLAS DE ORO OBLIGATORIAS:
1. Responde ÚNICA Y EXCLUSIVAMENTE con los pasos explícitos presentes en el contexto institucional.
2. Si el procedimiento específico no está en el contexto o requiere soporte físico/en sitio (daños de cables/cargadores, cambio de nombres de host, configuración en sitio), NO inventes rutas ni módulos en Seven o Kactus.
3. Si el contexto no contiene la solución, responde exactamente:
   "No dispongo de un procedimiento documentado para este caso específico. Puedes reportarlo a solicitudcomputo@unisimon.edu.co (Barranquilla) / helpdesk@unisimon.edu.co (Cúcuta) o indicarme si deseas que radique un ticket en GLPI por ti."

Contexto institucional:
{context}

Pregunta del usuario: {query}
Respuesta:"""


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
    Aplica corte estricto por umbral de relevancia (score >= 0.68) y evita invocar al LLM
    cuando no hay documentos relevantes.
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
        - 'estudiante': documentos para estudiante o generales.
        - 'funcionario' / 'docente' / 'profesor': documentos para funcionario o generales.
        - None / otros: sin filtro de audiencia.
        """
        if not user_role:
            return None

        role_lower = user_role.strip().lower()
        if role_lower == "estudiante":
            return {"audience": {"$in": ["estudiante", "general"]}}
        elif role_lower in ["funcionario", "docente", "profesor", "administrativo"]:
            return {"audience": {"$in": ["funcionario", "general"]}}

        return None

    async def query_rag(
        self,
        question: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline RAG completo:
        1. Búsqueda por similitud con puntuación de relevancia en ChromaDB (k=4, umbral >= 0.68) y filtro por rol.
        2. Corte estricto: Si ningún fragmento supera el umbral de 0.68, NO invoca al LLM y retorna respuesta estándar.
        3. Ensamblaje del System Prompt institucional e historial conversacional con fragmentos recuperados.
        4. Invocación asíncrona a Ollama (llama3.1:8b).
        """
        retrieved_docs = []
        sources: List[str] = []
        context_parts = []

        filter_condition = self._build_role_filter(user_role)

        # 1. Búsqueda por similitud con puntuación de relevancia en ChromaDB (k=4)
        if self.vector_store is not None:
            try:
                filter_desc = f" con filtro {filter_condition}" if filter_condition else " sin filtro"
                logger.info(f"Buscando fragmentos en ChromaDB (k=4, umbral >= {self.min_relevance_score}{filter_desc}) para: '{question[:50]}...'")
                
                if filter_condition:
                    docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                        question,
                        k=4,
                        filter=filter_condition
                    )
                else:
                    docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                        question,
                        k=4
                    )
                
                for doc, score in docs_with_scores:
                    if score is not None and score >= self.min_relevance_score:
                        retrieved_docs.append(doc)
                        source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                        source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                        if source_filename not in sources:
                            sources.append(source_filename)

                        page_num = doc.metadata.get("page", None)
                        page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""
                        context_parts.append(f"[{source_filename}{page_info}]\n{doc.page_content.strip()}")
                    else:
                        score_val = f"{score:.4f}" if score is not None else "None"
                        logger.info(f"Fragmento descartado por baja similitud ({score_val} < {self.min_relevance_score})")
            except Exception as exc:
                logger.warning(f"Error al realizar búsqueda de similitud en ChromaDB: {exc}")

        # 2. CERO ALUCINACIONES: Si ningún fragmento superó el umbral, NO invocar al LLM
        if not context_parts:
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

        # 3. Ensamblar System Prompt estricto, historial y User Prompt
        system_prompt = STRICT_SYSTEM_PROMPT_TEMPLATE.format(context=context_text, query=question)
        user_greeting = f"El usuario se llama {user_name}. " if user_name else ""
        role_ctx = f"[Rol del usuario: {user_role}] " if user_role else ""
        user_prompt = f"{user_greeting}{role_ctx}Consulta del usuario: {question}"

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": user_prompt})

        # 4. Llamada asíncrona a Ollama API
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
                    logger.info("Respuesta generada exitosamente por Ollama.")
                    return {
                        "response": bot_message,
                        "sources": sources,
                        "source": f"ollama_{self.model}",
                        "model": self.model,
                        "retrieved_chunks": len(retrieved_docs),
                        "has_context": True
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
        Generador de respuesta institucional de contingencia cuando Ollama no está disponible.
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
                "• El equipo de soporte de aplicaciones gestionará el requerimiento conforme a los acuerdos de nivel de servicio (SLA).\n\n"
                "¿Deseas ayuda con los pasos de recuperación de clave o requieres radicar un ticket?"
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
                "3. Si el inconveniente es en un aplicativo institucional, cierra sesión y vuelve a ingresar.\n\n"
                "¿Alguno de estos pasos te funcionó o el problema continúa?"
            )
        else:
            contenido = MENSAJE_NO_DOCUMENTADO

        return {
            "response": contenido,
            "sources": sources if sources is not None else [],
            "source": "knowledge_base_fallback",
            "model": "rule_based_institutional_unisimon",
            "retrieved_chunks": 0,
            "has_context": False
        }

    async def answer_query(
        self,
        query: str,
        user_role: Optional[str] = None,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para responder consultas con filtrado de metadatos por rol.
        """
        return await self.query_rag(
            question=query,
            user_name=user_name,
            chat_history=chat_history,
            user_role=user_role
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
