"""
Servicio de Semantic Golden Cache para UniMon.
Gestiona la colección `golden_resolved_qa` en ChromaDB, almacenando pares
pregunta/respuesta validados por usuarios con feedback positivo ('✅ Sí, me funcionó')
y reutilizándolos como Few-Shot dinámico cuando la similitud coseno >= 0.90.
Aplica validación estricta de calidad y grounding para evitar envenenamiento de caché.
"""

import logging
import re
from typing import Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
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


def get_embedding_model() -> SentenceTransformer:
    """Inicialización diferida (singleton) del modelo de embeddings para el Golden Cache."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"[GoldenCache] Cargando modelo de embeddings '{EMBEDDING_MODEL_NAME}'...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
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
    Evita envenenamiento de caché con alucinaciones o respuestas de fallback.
    """
    if not user_query or len(user_query.strip()) < 5:
        logger.debug("[GoldenCache] Descartado: consulta vacía o demasiado corta.")
        return False

    if not bot_response or len(bot_response.strip()) < 20:
        logger.debug("[GoldenCache] Descartado: respuesta vacía o demasiado corta.")
        return False

    resp_lower = bot_response.lower()
    for pat in INVALID_RESPONSE_PATTERNS:
        if re.search(pat, resp_lower):
            logger.info(f"[GoldenCache] Descartado por patrón de baja confianza/fallback: '{pat}'")
            return False

    return True


def save_golden_case(session_id: str, user_query: str, bot_response: str, role: str = "general") -> bool:
    """
    Guarda una interacción validada con feedback positivo en la colección golden tras pasar control de calidad.
    
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

        # Usar prefijo "query: " para consistencia con el modelo E5
        embedding = model.encode([f"query: {user_query}"])[0].tolist()
        doc_id = f"golden_{session_id}_{hash(user_query) % 1000000}"

        collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[bot_response],
            metadatas=[{
                "user_query": user_query,
                "role": role or "general",
                "source": "user_feedback_positive"
            }]
        )
        logger.info(f"[GoldenCache] Caso guardado exitosamente: '{user_query[:50]}...'")
        return True
    except Exception as e:
        logger.warning(f"[GoldenCache] Error guardando caso: {e}")
        return False


def search_golden_case(user_query: str, threshold: float = 0.90) -> Optional[Tuple[str, str, float]]:
    """
    Busca si existe una consulta similar previamente resuelta con éxito.
    
    Args:
        user_query: Consulta actual del usuario.
        threshold: Umbral mínimo de similitud coseno (default: 0.90).
    
    Returns:
        Tupla (pregunta_previa, respuesta_validada, similitud) si supera el umbral, None si no.
    """
    try:
        collection = get_golden_collection()
        if collection.count() == 0:
            return None

        model = get_embedding_model()
        embedding = model.encode([f"query: {user_query}"])[0].tolist()

        results = collection.query(
            query_embeddings=[embedding],
            n_results=1,
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
