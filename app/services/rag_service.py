"""
Servicio RAG Local con ChromaDB, Embeddings Multilingües y Ollama (Llama 3.1:8B).
Provee respuestas estrictas de soporte técnico para la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta, Colombia)
basadas en documentos y procedimientos institucionales indexados.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import get_settings

logger = logging.getLogger("unimon.rag_service")

# Prompt del sistema institucional empático y profesional con guardrails estrictos y tolerancia ortográfica
STRICT_SYSTEM_PROMPT_TEMPLATE = """Eres UniMon, Asistente Oficial de Soporte TI de la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta, Colombia).

INSTRUCCIONES CLAVE DE ATENCIÓN:

1. DOMINIO DE TI Y SOPORTE NIVEL 1 (CONSULTAS DENTRO DE DOMINIO):
   - Atiendes problemas y dudas técnicas de:
     * Equipos físicos y hardware (computadores, portátiles, monitores, pantallas, proyectores/video beam, mouse, teclado, impresoras, cables de video/poder).
     * Conectividad y redes (cableada, wifi institucional, internet).
     * Software, cuentas y plataformas (ERP Kactus, Seven, Teams, Office 365, Moodle, correo institucional, restablecimiento de contraseñas y cuentas).
     * Procedimientos institucionales de TI (P-GT-01, P-GT-07, P-GT-08, P-GT-10, P-GT-11, P-GT-13).
   - Para estas consultas de TI:
     * Brinda de 2 a 3 pasos breves, claros y prácticos de solución o descarte inicial.
     * Al finalizar, pregunta amablemente si alguno de estos pasos le sirvió o si el inconveniente continúa.

2. TOLERANCIA ORTOGRÁFICA:
   - Interpreta con flexibilidad cualquier error ortográfico o tipeo informal (ej: "proyestor" -> proyector, "pantaya" -> pantalla, "katuc" -> Kactus, "clabe" -> clave, "no prende", "interner" -> internet, etc.). Siempre brinda soporte a la intención técnica.

3. CONTINUIDAD CONVERSACIONAL Y RESPUESTAS CORTAS ("SÍ", "CLARO", "DALE", "OK", "POR FAVOR"):
   - Si el usuario responde afirmativamente a una pregunta de seguimiento previa (ej: "¿Deseas que te explique los pasos?" -> "sí", "dale", "ok", "claro", "por favor"), continúa la conversación explicando los pasos solicitados de manera clara y directa sin rechazar la consulta.

4. CANALES OFICIALES DE SOPORTE EN UNISIMON:
   - Plataforma oficial de atención y tickets: GLPI (https://glpi.unisimon.edu.co / Mesa de Ayuda).
   - Sede Barranquilla: solicitudcomputo@unisimon.edu.co | WhatsApp: 3172683922 | Teléfono: 3444333 Ext. 8003 y 8004.
   - Sede Cúcuta: helpdesk@unisimon.edu.co | Teléfono: 5827070 Ext. 129.
   - PROHIBICIÓN ESTRICTA: NO indicar a los usuarios finales que reporten fallas técnicas a Compras, Activos Fijos o Almacén. Esas dependencias realizan trámites administrativos internos entre dependencias, no atención al usuario. Todo reporte de usuario debe radicarse en GLPI o a través de solicitudcomputo@unisimon.edu.co / helpdesk@unisimon.edu.co.

5. GUARDRAIL FUERA DE DOMINIO (CONSULTAS AJENAS A TI):
   - Si el usuario pregunta por temas completamente ajenos a tecnología y a la Universidad Simón Bolívar (ej: preguntas de cultura general como "¿cuál es la capital de Hungría?", geografía, recetas de cocina, deportes, tareas no de TI):
     * Responde de forma directa, educada y asertiva:
       "Soy un asistente enfocado exclusivamente en soporte técnico, gestión de TI y procedimientos institucionales de la Universidad Simón Bolívar. ¿En qué tema tecnológico o institucional de la universidad te puedo colaborar hoy?"
     * PROHIBICIÓN ESTRICTA: NO proporciones pasos de descarte de hardware ni menciones GLPI si la pregunta no es de soporte técnico o TI.

============================================================
CONTEXTO INSTITUCIONAL RECUPERADO:
{context}
============================================================
"""


def is_out_of_domain_response(response_text: str) -> bool:
    """
    Detecta si la respuesta generada corresponde a un rechazo fuera de dominio (Guardrail institucional).
    """
    text_lower = response_text.lower()

    # Si contiene pasos de descarte técnico o solución guiada, está dentro de dominio
    if any(m in text_lower for m in ["paso 1", "paso 2", "1.", "2.", "restablecer", "restablece", "proyector", "kactus", "descarte"]):
        # A menos que sea explícitamente un rechazo
        if "exclusivamente en soporte" not in text_lower and "no puedo proporcionar" not in text_lower and "cultura general" not in text_lower:
            return False

    guardrail_markers = [
        "exclusivamente en soporte",
        "tema tecnológico o institucional",
        "no se relaciona con",
        "no está relacionada con",
        "no esta relacionada con",
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
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        chroma_db_dir: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = settings.ollama_timeout
        self.chroma_db_dir = Path(chroma_db_dir or settings.chroma_db_dir)
        self.embedding_model_name = embedding_model or settings.embedding_model

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

    async def query_rag(
        self,
        question: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline RAG completo:
        1. Búsqueda por similitud en ChromaDB (k=4) usando intfloat/multilingual-e5-base.
        2. Extracción de fragmentos y nombres de fuentes.
        3. Ensamblaje del System Prompt institucional estricto e historial conversacional.
        4. Invocación asíncrona a Ollama (llama3.1:8b).

        Args:
            question: Pregunta o consulta del usuario.
            user_name: Nombre opcional del usuario para personalización cordial.
            chat_history: Lista opcional de turnos previos [{"role": "user"/"assistant", "content": "..."}].

        Returns:
            Dict con:
                - 'response': Texto de respuesta generado por el LLM o fallback.
                - 'sources': Lista de nombres de archivos fuentes recuperados.
                - 'source': Identificador de la fuente ('ollama_rag' o 'fallback').
                - 'model': Modelo LLM utilizado.
                - 'retrieved_chunks': Número de fragmentos recuperados.
        """
        retrieved_docs = []
        sources: List[str] = []
        context_parts = []

        # 1. Búsqueda por similitud en ChromaDB (k=4)
        if self.vector_store is not None:
            try:
                logger.info(f"Buscando fragmentos relevantes en ChromaDB (k=4) para: '{question[:50]}...'")
                docs = self.vector_store.similarity_search(question, k=4)
                if docs:
                    retrieved_docs = docs
                    for doc in docs:
                        source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                        source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                        if source_filename not in sources:
                            sources.append(source_filename)

                        page_num = doc.metadata.get("page", None)
                        page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""
                        context_parts.append(f"[{source_filename}{page_info}]\n{doc.page_content.strip()}")
            except Exception as exc:
                logger.warning(f"Error al realizar búsqueda de similitud en ChromaDB: {exc}")

        # Si no se recuperaron fragmentos de documentos, usar contexto base de procedimientos Unisimon
        if context_parts:
            context_text = "\n\n---\n\n".join(context_parts)
        else:
            context_text = (
                "[INFORMACIÓN INSTITUCIONAL BASE UNISIMON COLOMBIA]\n"
                "- Sedes: Barranquilla y Cúcuta, Colombia.\n"
                "- Sede Barranquilla: solicitudcomputo@unisimon.edu.co | WhatsApp: 3172683922 | Teléfono: 3444333 Ext. 8003 y 8004.\n"
                "- Sede Cúcuta: helpdesk@unisimon.edu.co | Teléfono: 5827070 Ext. 129.\n"
                "- Procedimientos TI: P-GT-01 (Mantenimiento Cómputo), P-GT-07 (Protección Antimalware), "
                "P-GT-08 (Aseguramiento de Redes), P-GT-10 (Backups de Información), P-GT-11 (Incidencias Kactus/Seven), "
                "P-GT-13 (Gestión de Requerimientos y Soluciones Tecnológicas)."
            )
            sources = ["Procedimientos Institucionales Unisimon"]

        # 2. Ensamblar System Prompt estricto, historial y User Prompt
        system_prompt = STRICT_SYSTEM_PROMPT_TEMPLATE.format(context=context_text)
        user_greeting = f"El usuario se llama {user_name}. " if user_name else ""
        user_prompt = f"{user_greeting}Consulta del usuario: {question}"

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            # Mantener los últimos 6 mensajes del historial (3 turnos)
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": user_prompt})

        # 3. Llamada asíncrona a Ollama API
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
                        "retrieved_chunks": len(retrieved_docs)
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
        Aplica guardrails institucionales para no forzar pasos de hardware a temas no relacionados.
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
            # Guardrail institucional para consultas fuera de dominio
            contenido = (
                "Soy un asistente enfocado exclusivamente en soporte técnico, gestión de TI y procedimientos institucionales de la Universidad Simón Bolívar. "
                "¿En qué tema tecnológico o institucional de la universidad te puedo colaborar hoy?"
            )

        return {
            "response": contenido,
            "sources": sources or ["Procedimientos Institucionales Unisimon"],
            "source": "knowledge_base_fallback",
            "model": "rule_based_institutional_unisimon",
            "retrieved_chunks": 0
        }

    async def consultar(
        self,
        pregunta: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        es_diagnostico: bool = False
    ) -> Dict[str, Any]:
        """
        Consulta al motor RAG de UniMon con soporte para historial de conversación.
        Pasa la consulta del usuario directamente al LLM bajo el System Prompt institucional con guardrails y tolerancia ortográfica.
        """
        return await self.query_rag(question=pregunta, user_name=user_name, chat_history=chat_history)


# Instancia por defecto para importaciones limpias
rag_service = RAGService()



