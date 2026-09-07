"""
Servicio de Semantic Golden Cache para UniMon.
Gestiona la colección `golden_resolved_qa` en ChromaDB, almacenando pares
pregunta/respuesta validados por usuarios con feedback positivo ('✅ Sí, me funcionó')
y reutilizándolos como Few-Shot dinámico cuando la similitud coseno >= 0.90.
Aplica validación estricta de calidad y grounding para evitar envenenamiento de caché.
"""

import os
import logging
import re
import hashlib
from typing import Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings

# Forzar modo offline estricto para evitar peticiones a Hugging Face Hub
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer

logger = logging.getLogger("unimon.golden_cache")

CHROMA_PATH = "data/chroma_db"
COLLECTION_NAME = "golden_resolved_qa"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"

_embedding_model = None
_golden_collection = None

# Patrones de respuestas no aptas para almacenar en Golden Cache (fallbacks, rechazos o alucinaciones)
INVALID_RESPONSE_PATTERNS = [
    r"no dispongo de un instructivo",
    r"no dispongo de un procedimiento",
    r"fuera de (mi|nuestro) dominio",
    r"exclusivamente en soporte",
    r"ocurri[oó] un inconveniente",
    r"no se pudo conectar",
    r"kactus\.unisimon\.edu\.co",
    r"\[(?:url|link|enlace)\]",
]


def normalize_text(text: str) -> str:
    """Normaliza texto para hashing y búsqueda determinista."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def get_embedding_model() -> SentenceTransformer:
    """Inicialización diferida (singleton) del modelo de embeddings para el Golden Cache en modo offline."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"[GoldenCache] Cargando modelo de embeddings '{EMBEDDING_MODEL_NAME}' en modo offline...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    return _embedding_model


def get_golden_collection():
    """Inicialización diferida (singleton) de la colección ChromaDB para casos resueltos."""
    global _golden_collection
    if _golden_collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _golden_collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"[GoldenCache] Colección '{COLLECTION_NAME}' inicializada ({_golden_collection.count()} casos).")
    return _golden_collection


def init_golden_cache():
    """Pre-carga el modelo de embeddings y la colección de Golden Cache en memoria (Warmup)."""
    get_embedding_model()
    get_golden_collection()


def clear_golden_cache() -> bool:
    """
    Elimina todos los registros de la colección golden_resolved_qa para limpiar casos viciados.
    
    Returns:
        True si se purgó exitosamente, False en caso de error.
    """
    global _golden_collection
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        _golden_collection = None
        logger.info("[GoldenCache] Colección golden_resolved_qa purgada exitosamente.")
        return True
    except Exception as e:
        logger.warning(f"[GoldenCache] Error al purgar colección: {e}")
        return False


def is_valid_for_golden_cache(user_query: str, bot_response: str) -> bool:
    """
    Valida la calidad y confiabilidad de la interacción antes de almacenarla en Golden Cache.
    Evita envenenamiento de caché con alucinaciones, respuestas de fallback, footers aislados
    o disculpas de LLM.
    """
    if not user_query or len(user_query.strip()) < 5:
        logger.debug("[GoldenCache] Descartado: consulta vacía o demasiado corta.")
        return False

    if not bot_response or len(bot_response.strip()) < 60:
        logger.debug("[GoldenCache] Descartado: respuesta vacía o demasiado corta (< 60 chars).")
        return False

    resp_lower = bot_response.strip().lower()

    # Rechazar si la respuesta es solo la pregunta de cierre/feedback (footer aislado)
    if resp_lower.startswith("¿pudiste resolver") or resp_lower.startswith("**¿pudiste resolver"):
        logger.info("[GoldenCache] Descartado: respuesta contiene solo el footer de confirmación.")
        return False

    # Rechazar frases de disculpa o meta-lenguaje del LLM
    llm_apology_phrases = [
        "lo siento", "error en la respuesta", "como modelo de lenguaje",
        "lamento la confusión", "lamento la confusion",
        "hubo un error", "no puedo continuar con la conversación"
    ]
    for phrase in llm_apology_phrases:
        if phrase in resp_lower:
            logger.info(f"[GoldenCache] Descartado por frase de disculpa/meta-lenguaje LLM: '{phrase}'")
            return False

    for pat in INVALID_RESPONSE_PATTERNS:
        if re.search(pat, resp_lower):
            logger.info(f"[GoldenCache] Descartado por patrón de baja confianza/fallback: '{pat}'")
            return False

    return True


def save_golden_case(session_id: str, user_query: str, bot_response: str, role: str = "general") -> bool:
    """
    Guarda o actualiza una interacción validada con feedback positivo en la colección golden tras pasar control de calidad.
    Utiliza un hash determinista basado en el rol y consulta para evitar duplicidad (Upsert idempotente).
    
    Args:
        session_id: Identificador de la sesión del usuario.
        user_query: Pregunta original del usuario.
        bot_response: Respuesta del bot que fue confirmada como exitosa.
        role: Rol institucional del usuario (estudiante, profesor, administrativo, otros).
    
    Returns:
        True si se guardó exitosamente, False en caso contrario.
    """
    try:
        if not is_valid_for_golden_cache(user_query, bot_response):
            return False

        collection = get_golden_collection()
        model = get_embedding_model()

        clean_query = normalize_text(user_query)
        role_clean = (role or "general").strip().lower()
        doc_id = hashlib.sha256(f"{role_clean}:{clean_query}".encode("utf-8")).hexdigest()

        # Usar prefijo "query: " para consistencia con el modelo E5
        embedding = model.encode([f"query: {user_query}"])[0].tolist()

        collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[bot_response],
            metadatas=[{
                "user_query": user_query,
                "role": role_clean,
                "session_id": session_id,
                "source": "user_feedback_positive"
            }]
        )
        logger.info(f"[GoldenCache] Caso guardado/actualizado exitosamente (ID: {doc_id[:8]}...): '{user_query[:50]}...'")
        return True
    except Exception as e:
        logger.warning(f"[GoldenCache] Error guardando caso: {e}")
        return False


def invalidate_golden_cache_entry(query: str, role: str = "general") -> bool:
    """
    Elimina una entrada específica del Golden Cache ante feedback negativo o reintento fallido.
    
    Args:
        query: Consulta del usuario a invalidar.
        role: Rol institucional del usuario.
        
    Returns:
        True si se eliminó exitosamente, False ante error.
    """
    try:
        if not query:
            return False
        clean_query = normalize_text(query)
        role_clean = (role or "general").strip().lower()
        doc_id = hashlib.sha256(f"{role_clean}:{clean_query}".encode("utf-8")).hexdigest()
        collection = get_golden_collection()
        collection.delete(ids=[doc_id])
        logger.info(f"[GoldenCache] Entrada invalidada/eliminada por feedback negativo (ID: {doc_id[:8]}...): '{query[:50]}...'")
        return True
    except Exception as e:
        logger.warning(f"[GoldenCache] Error al invalidar entrada: {e}")
        return False


def search_golden_case(user_query: str, threshold: float = 0.90, role: Optional[str] = None) -> Optional[Tuple[str, str, float]]:
    """
    Busca si existe una consulta similar previamente resuelta con éxito.
    
    Args:
        user_query: Consulta actual del usuario.
        threshold: Umbral mínimo de similitud coseno (default: 0.90).
        role: Rol institucional del usuario para filtrar resultados por contexto (opcional).
    
    Returns:
        Tupla (pregunta_previa, respuesta_validada, similitud) si supera el umbral, None si no.
    """
    try:
        collection = get_golden_collection()
        if collection.count() == 0:
            return None

        model = get_embedding_model()
        embedding = model.encode([f"query: {user_query}"])[0].tolist()

        # Filtrar por rol si se especifica uno distinto a "general"
        where_filter = None
        if role and role.strip().lower() != "general":
            where_filter = {"role": {"$in": [role.strip().lower(), "general"]}}

        results = collection.query(
            query_embeddings=[embedding],
            n_results=1,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

        if results and results["documents"] and len(results["documents"][0]) > 0:
            distance = results["distances"][0][0]
            similarity = 1.0 - distance  # Métrica coseno: distancia = 1 - similitud

            if similarity >= threshold:
                matched_query = results["metadatas"][0][0].get("user_query", "")
                matched_response = results["documents"][0][0]
                logger.info(
                    f"[GoldenCache] Coincidencia encontrada (similitud={similarity:.4f}): "
                    f"'{matched_query[:50]}...'"
                )
                return (matched_query, matched_response, similarity)
            else:
                logger.debug(
                    f"[GoldenCache] Mejor coincidencia ({similarity:.4f}) por debajo del umbral ({threshold})."
                )
    except Exception as e:
        logger.warning(f"[GoldenCache] Error consultando cache: {e}")

    return None


def purge_anomalous_golden_entries() -> int:
    """
    Recorre la colección golden_resolved_qa y elimina entradas anómalas:
    - Respuestas con menos de 60 caracteres (truncadas o vacías).
    - Respuestas que son solo el footer de confirmación (¿Pudiste resolver...?).
    - Respuestas con disculpas de LLM o meta-lenguaje prohibido.
    
    Returns:
        Número de entradas eliminadas.
    """
    try:
        collection = get_golden_collection()
        data = collection.get(include=["documents", "metadatas"])

        if not data or not data["ids"]:
            logger.info("[GoldenCache] Colección vacía, nada que purgar.")
            return 0

        ids_to_delete = []
        llm_apology_phrases = [
            "lo siento", "error en la respuesta", "como modelo de lenguaje",
            "lamento la confusión", "lamento la confusion",
            "hubo un error", "no puedo continuar con la conversación"
        ]

        for doc_id, doc in zip(data["ids"], data["documents"]):
            doc_strip = doc.strip()
            doc_lower = doc_strip.lower()

            # Respuesta demasiado corta
            if len(doc_strip) < 60:
                ids_to_delete.append(doc_id)
                continue

            # Solo footer de confirmación
            if doc_lower.startswith("¿pudiste resolver") or doc_lower.startswith("**¿pudiste resolver"):
                ids_to_delete.append(doc_id)
                continue

            # Disculpas o meta-lenguaje de LLM
            if any(phrase in doc_lower for phrase in llm_apology_phrases):
                ids_to_delete.append(doc_id)
                continue

            # Patrones de fallback registrados
            for pat in INVALID_RESPONSE_PATTERNS:
                if re.search(pat, doc_lower):
                    ids_to_delete.append(doc_id)
                    break

        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"[GoldenCache] Purgadas {len(ids_to_delete)} entradas anómalas en saneamiento.")
        else:
            logger.info("[GoldenCache] No se encontraron entradas anómalas.")

        return len(ids_to_delete)
    except Exception as e:
        logger.warning(f"[GoldenCache] Error durante purga de anomalías: {e}")
        return 0
