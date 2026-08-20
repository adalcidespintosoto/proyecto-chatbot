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

# Prompt del sistema institucional empático y profesional
STRICT_SYSTEM_PROMPT_TEMPLATE = """Eres UniMon, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta, Colombia).
Tu objetivo es resolver inquietudes de estudiantes, docentes y funcionarios con calidez, claridad y empatía, basándote en los procedimientos institucionales suministrados en el contexto (mantenimiento de cómputo P-GT-01, protección antimalware P-GT-07, aseguramiento de redes P-GT-08, backups P-GT-10, incidencias ERP Kactus/Seven P-GT-11 y gestión tecnológica P-GT-13).

Pautas y Reglas de Respuesta:
1. Tono de comunicación: Empático, servicial, conciso y profesional en español.
2. Canales oficiales de soporte en Unisimon Colombia:
   - Sede Barranquilla: solicitudcomputo@unisimon.edu.co | WhatsApp: 3172683922 | Teléfono: 3444333 Ext. 8003 y 8004.
   - Sede Cúcuta: helpdesk@unisimon.edu.co | Teléfono: 5827070 Ext. 129.
3. Tratamiento de ambigüedad o falta de información en el contexto:
   - Evita frases excesivamente negativas o defensivas como "Lo siento, no tengo información".
   - Si la consulta es muy ambigua o general, orienta amablemente al usuario:
     "Para brindarte la información exacta según las guías técnicas de la Universidad Simón Bolívar, ¿podrías especificar si tu consulta es sobre mantenimiento de equipos, asignación de cuentas, backups o reporte de incidentes?"
   - Si se trata de un trámite no documentado, invítalo cordialmente a contactar a los canales oficiales o solicitar la radicación de un ticket en GLPI.
4. Identidad estricta: No hagas referencia a entidades o sedes externas ajenas a la Universidad Simón Bolívar de Colombia.

============================================================
CONTEXTO INSTITUCIONAL RECUPERADO:
{context}
============================================================
"""



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

    async def query_rag(self, question: str, user_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ejecuta el pipeline RAG completo:
        1. Búsqueda por similitud en ChromaDB (k=4) usando intfloat/multilingual-e5-base.
        2. Extracción de fragmentos y nombres de fuentes.
        3. Ensamblaje del System Prompt institucional estricto.
        4. Invocación asíncrona a Ollama (llama3.1:8b).

        Args:
            question: Pregunta o consulta del usuario.
            user_name: Nombre opcional del usuario para personalización cordial.

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

        # 2. Ensamblar System Prompt estricto y User Prompt
        system_prompt = STRICT_SYSTEM_PROMPT_TEMPLATE.format(context=context_text)
        user_greeting = f"El usuario se llama {user_name}. " if user_name else ""
        user_prompt = f"{user_greeting}Consulta del usuario: {question}"

        # 3. Llamada asíncrona a Ollama API
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2
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
        elif any(w in msg_lower for w in ["kactus", "seven", "erp", "nómina", "nomina"]):
            contenido = (
                f"{saludo} Para soporte en los sistemas institucionales **Kactus / Seven** (Procedimiento **P-GT-11** y **P-GT-12**):\n\n"
                "• Las incidencias y requerimientos deben ser radicados indicando el módulo afectado, captura de pantalla del error y usuario solicitante.\n"
                "• El equipo de soporte de aplicaciones gestionará el requerimiento conforme a los acuerdos de nivel de servicio (SLA)."
            )
        elif any(w in msg_lower for w in ["virus", "malware", "antivirus", "amenaza"]):
            contenido = (
                f"{saludo} Según el procedimiento **P-GT-07** (*Protección de Código Malicioso*):\n\n"
                "• Todo equipo institucional debe contar con la solución de protección antimalware corporativa activa y actualizada.\n"
                "• Ante sospecha de infección, desconecta el equipo de la red y notifica inmediatamente a Soporte TI."
            )
        else:
            contenido = (
                f"{saludo} Soy UniMon, tu asistente de Soporte Técnico de Nivel 1 de la Universidad Simón Bolívar.\n\n"
                "Para ayudarte con este inconveniente, te sugiero realizar estos pasos iniciales de descarte:\n"
                "1. Verifica que los cables de poder, red o video estén firmemente conectados.\n"
                "2. Reinicia el equipo o dispositivo y verifica si el comportamiento persiste.\n"
                "3. Si el inconveniente es en un aplicativo institucional (Kactus/Seven o correo), cierra sesión y vuelve a ingresar.\n\n"
                "¿Alguno de estos pasos te funcionó o el problema continúa?"
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
        es_diagnostico: bool = True
    ) -> Dict[str, Any]:
        """
        Consulta al motor RAG de UniMon.
        Si es_diagnostico=True, instruye a Llama 3.1 para actuar como técnico de Nivel 1:
        proporciona de 2 a 3 pasos breves de descarte/solución y pregunta si funcionó o persiste.
        """
        if es_diagnostico:
            instruccion_nivel1 = (
                f"{pregunta}\n\n"
                "[INSTRUCCIÓN DE SOPORTE NIVEL 1: Actúa como técnico de soporte TI de Nivel 1 de la Universidad Simón Bolívar. "
                "Proporciona de 2 a 3 pasos breves y prácticos de descarte o solución rápida según los procedimientos del contexto. "
                "Al finalizar tu respuesta, pregunta amablemente al usuario si alguno de estos pasos le funcionó o si el problema persiste.]"
            )
            return await self.query_rag(question=instruccion_nivel1, user_name=user_name)
        else:
            return await self.query_rag(question=pregunta, user_name=user_name)


# Instancia por defecto para importaciones limpias
rag_service = RAGService()



