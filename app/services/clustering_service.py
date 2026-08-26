"""
Servicio de Clustering Semántico y Detección de Brechas Documentales para UniMon.
Agrupa consultas de usuarios registradas en data/analytics.db utilizando K-Means y embeddings multilingües,
resume temas con el modelo LLM y detecta vacíos de conocimiento institucional.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
import httpx

from app.config import get_settings

logger = logging.getLogger("unimon.clustering")

DB_PATH = "data/analytics.db"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"

_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Retorna una instancia única (lazy loading) del modelo de embeddings."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Cargando modelo de embeddings para clustering: '{EMBEDDING_MODEL_NAME}'...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def summarize_cluster_topic(sample_queries: List[str]) -> str:
    """Invoca a unimon:8b para resumir el tema principal del grupo en un título corto."""
    if not sample_queries:
        return "Consultas Generales y Soporte TI"

    queries_text = "\n".join([f"- {q}" for q in sample_queries[:6]])
    prompt = f"""Analiza las siguientes consultas de usuarios universitarios y responde ÚNICAMENTE con un TÍTULO CORTO (máximo 5 palabras) que identifique el trámite o problema común:

Consultas:
{queries_text}

Título descriptivo:"""

    try:
        settings = get_settings()
        ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

        response = httpx.post(
            ollama_url,
            json={
                "model": settings.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 25
                }
            },
            timeout=4.0
        )
        if response.status_code == 200:
            topic = response.json().get("response", "").strip().strip('"').strip("'")
            if topic and len(topic) > 3:
                return topic.split("\n")[0].strip()
    except Exception as e:
        logger.warning(f"[Clustering] Error resumiendo tema con LLM: {e}")

    return "Consultas Generales y Soporte TI"


def analyze_query_clusters(n_clusters: Optional[int] = None, min_queries_required: int = 4) -> Dict[str, Any]:
    """
    Lee las consultas de data/analytics.db, genera embeddings, aplica K-Means y devuelve
    los clusters con métricas de resolución y banderas de vacíos documentales.
    """
    try:
        db_file = Path(DB_PATH)
        if not db_file.exists():
            return {
                "status": "error",
                "message": f"La base de datos '{DB_PATH}' no existe.",
                "clusters": []
            }

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Detectar tablas disponibles en analytics.db
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        target_table = None
        for cand in ["queries_log", "telemetry_interactions", "interactions"]:
            if cand in tables:
                target_table = cand
                break

        if not target_table:
            conn.close()
            return {
                "status": "error",
                "message": "No se encontró tabla de logs en analytics.db",
                "clusters": []
            }

        # Extraer consultas y estado/resultado
        if target_table == "telemetry_interactions" and "telemetry_sessions" in tables:
            cursor.execute("""
                SELECT i.user_query, COALESCE(s.final_status, i.feedback, 'UNKNOWN')
                FROM telemetry_interactions i
                LEFT JOIN telemetry_sessions s ON i.session_id = s.session_id
                WHERE i.user_query IS NOT NULL AND length(trim(i.user_query)) > 6
                ORDER BY i.id DESC LIMIT 400
            """)
            rows = cursor.fetchall()
        else:
            cursor.execute(f"PRAGMA table_info({target_table});")
            columns = [col[1] for col in cursor.fetchall()]

            query_col = "query" if "query" in columns else (
                "user_query" if "user_query" in columns else (
                    "user_message" if "user_message" in columns else columns[1]
                )
            )
            status_col = "status" if "status" in columns else (
                "final_status" if "final_status" in columns else (
                    "final_state" if "final_state" in columns else columns[-1]
                )
            )

            cursor.execute(f"""
                SELECT {query_col}, {status_col} 
                FROM {target_table} 
                WHERE {query_col} IS NOT NULL AND length(trim({query_col})) > 6
                ORDER BY rowid DESC LIMIT 400
            """)
            rows = cursor.fetchall()

        conn.close()

        if not rows or len(rows) < min_queries_required:
            return {
                "status": "insufficient_data",
                "message": f"Se requieren al menos {min_queries_required} consultas registradas para calcular clusters.",
                "total_queries": len(rows) if rows else 0,
                "clusters": []
            }

        queries = [r[0].strip() for r in rows]
        statuses = [str(r[1]).upper() if r[1] else "UNKNOWN" for r in rows]

        total_q = len(queries)

        # Determinar k dinámicamente si no se especifica
        if n_clusters is None:
            k = min(6, max(2, total_q // 5))
        else:
            k = max(2, min(n_clusters, total_q))

        k = min(k, total_q)
        if k < 2 and total_q >= 2:
            k = 2

        # Vectorizar consultas con prefijo query: para modelo e5
        model = get_embedding_model()
        embeddings = model.encode([f"query: {q}" for q in queries], show_progress_bar=False)

        # Agrupar con K-Means
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        clusters_result = []
        for cluster_id in range(k):
            cluster_indices = [i for i, lbl in enumerate(labels) if lbl == cluster_id]
            if not cluster_indices:
                continue

            cluster_queries = [queries[i] for i in cluster_indices]
            cluster_statuses = [statuses[i] for i in cluster_indices]

            total_in_cluster = len(cluster_queries)
            resolved_count = sum(
                1 for s in cluster_statuses
                if any(ok in s for ok in ["FINALIZADO", "RESOLVED", "EXITO", "SUCCESS", "SOLUCIONADO"])
            )
            resolution_rate = round((resolved_count / total_in_cluster) * 100, 1) if total_in_cluster > 0 else 0.0

            # Obtener resumen temático con LLM
            topic_name = summarize_cluster_topic(cluster_queries)

            clusters_result.append({
                "cluster_id": cluster_id + 1,
                "topic": topic_name,
                "total_queries": total_in_cluster,
                "resolution_rate_pct": resolution_rate,
                "requires_new_doc": bool(resolution_rate < 50.0 and total_in_cluster >= 2),
                "sample_queries": list(dict.fromkeys(cluster_queries))[:5]
            })

        # Ordenar por volumen de consultas descendente
        clusters_result.sort(key=lambda x: x["total_queries"], reverse=True)

        return {
            "status": "success",
            "total_analyzed_queries": total_q,
            "clusters_count": len(clusters_result),
            "clusters": clusters_result
        }

    except Exception as e:
        logger.error(f"[Clustering] Error analizando clusters: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "clusters": []
        }
