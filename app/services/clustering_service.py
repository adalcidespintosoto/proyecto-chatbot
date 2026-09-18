"""
Servicio de Clustering Semántico, Detección de Brechas Documentales y Exportador DPO para UniMon.
Agrupa consultas de usuarios registradas en data/analytics.db utilizando embeddings multilingües (DBSCAN / K-Means),
resume temas con el modelo LLM, detecta vacíos de conocimiento institucional y exporta datasets de preferencia DPO.
"""

import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# Forzar modo offline estricto para evitar peticiones a Hugging Face Hub
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sentence_transformers import SentenceTransformer
import httpx

from app.config import get_settings

logger = logging.getLogger("unimon.clustering")

DB_PATH = "data/analytics.db"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"

_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Retorna una instancia única (lazy loading) del modelo de embeddings en modo offline."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Cargando modelo de embeddings para clustering: '{EMBEDDING_MODEL_NAME}' en modo offline...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
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
        from app.services.llm_client import get_llm_client
        llm_client = get_llm_client()
        topic = llm_client.generate_sync(prompt=prompt, max_tokens=100, timeout=5.0)
        if topic and len(topic) > 3:
            return topic.strip().strip('"').strip("'").split("\n")[0].strip()
    except Exception as e:
        logger.warning(f"[Clustering] Error resumiendo tema con LLMClient: {e}")

    return "Consultas Generales y Soporte TI"


def get_query_clusters(
    db_path: Optional[str] = None,
    min_samples: int = 2,
    eps: float = 0.25,
    n_clusters: Optional[int] = None,
    min_queries_required: int = 2
) -> Dict[str, Any]:
    """
    Agrupa semánticamente las consultas históricas de analytics.db y detecta brechas de conocimiento.
    Utiliza DBSCAN por defecto o K-Means cuando se especifica n_clusters.
    """
    active_db = db_path or DB_PATH
    try:
        db_file = Path(active_db)
        if not db_file.exists():
            return {
                "status": "error",
                "message": f"La base de datos '{active_db}' no existe.",
                "total_queries": 0,
                "total_analyzed_queries": 0,
                "total_clusters": 0,
                "clusters_count": 0,
                "knowledge_gaps_detected": 0,
                "clusters": []
            }

        conn = sqlite3.connect(active_db)
        cursor = conn.cursor()

        # Detectar tablas disponibles en la base de datos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        rows: List[Tuple[Any, ...]] = []

        if "chat_telemetry" in tables:
            cursor.execute("""
                SELECT session_id, user_message, bot_response, final_state, role, source_refs
                FROM chat_telemetry 
                WHERE user_message IS NOT NULL AND TRIM(user_message) != ''
                ORDER BY rowid DESC LIMIT 500
            """)
            rows = cursor.fetchall()
        elif "telemetry_interactions" in tables and "telemetry_sessions" in tables:
            cursor.execute("""
                SELECT 
                    i.session_id, 
                    i.user_query, 
                    COALESCE(i.bot_response, ''), 
                    COALESCE(s.final_status, i.feedback, 'UNKNOWN'),
                    COALESCE(s.role, 'general'),
                    COALESCE(i.referenced_docs, '')
                FROM telemetry_interactions i
                LEFT JOIN telemetry_sessions s ON i.session_id = s.session_id
                WHERE i.user_query IS NOT NULL AND TRIM(i.user_query) != ''
                ORDER BY i.id DESC LIMIT 500
            """)
            rows = cursor.fetchall()
        elif "queries_log" in tables or "interactions" in tables:
            target = "queries_log" if "queries_log" in tables else "interactions"
            cursor.execute(f"PRAGMA table_info({target});")
            columns = [col[1] for col in cursor.fetchall()]
            
            q_col = "query" if "query" in columns else ("user_query" if "user_query" in columns else columns[1])
            s_col = "status" if "status" in columns else ("final_status" if "final_status" in columns else columns[-1])
            
            cursor.execute(f"""
                SELECT rowid, {q_col}, '', {s_col}, 'general', ''
                FROM {target}
                WHERE {q_col} IS NOT NULL AND TRIM({q_col}) != ''
                ORDER BY rowid DESC LIMIT 500
            """)
            rows = cursor.fetchall()

        conn.close()

        if not rows or len(rows) < min_queries_required:
            return {
                "status": "insufficient_data",
                "message": f"Se requieren al menos {min_queries_required} consultas registradas para calcular clusters.",
                "total_queries": len(rows) if rows else 0,
                "total_analyzed_queries": len(rows) if rows else 0,
                "total_clusters": 0,
                "clusters_count": 0,
                "knowledge_gaps_detected": 0,
                "clusters": []
            }

        queries = [str(r[1]).strip() for r in rows if r[1] and str(r[1]).strip()]
        if len(queries) < min_queries_required:
            return {
                "status": "insufficient_data",
                "message": f"Se requieren al menos {min_queries_required} consultas válidas registradas.",
                "total_queries": len(queries),
                "total_analyzed_queries": len(queries),
                "total_clusters": 0,
                "clusters_count": 0,
                "knowledge_gaps_detected": 0,
                "clusters": []
            }

        model = get_embedding_model()
        embeddings = model.encode([f"query: {q}" for q in queries], normalize_embeddings=True, show_progress_bar=False)

        # Determinar algoritmo de agrupamiento (K-Means si se especifica n_clusters, DBSCAN por defecto)
        if n_clusters is not None and n_clusters > 0:
            k = max(1, min(n_clusters, len(queries)))
            if k > 1 and len(queries) >= k:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)
            else:
                labels = np.zeros(len(queries), dtype=int)
        else:
            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit(embeddings)
            labels = clustering.labels_
            # Si DBSCAN dejó todo como ruido (-1) y hay datos suficientes, usar K-Means dinámico
            unique_non_noise = [l for l in set(labels) if l != -1]
            if not unique_non_noise and len(queries) >= 2:
                k = min(6, max(2, len(queries) // 4))
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embeddings)

        clusters_dict: Dict[str, Dict[str, Any]] = {}
        for idx, label in enumerate(labels):
            label_key = f"cluster_{label}" if label != -1 else "outliers_noise"
            if label_key not in clusters_dict:
                clusters_dict[label_key] = {
                    "cluster_id": int(label) if label != -1 else -1,
                    "samples": [],
                    "total_count": 0,
                    "resolved_count": 0,
                    "failed_count": 0,
                    "roles": set(),
                    "refs_used": set()
                }

            row = rows[idx]
            status_val = str(row[3]).upper() if row[3] else "UNKNOWN"
            is_resolved = any(ok in status_val for ok in ["FINALIZADO", "RESOLVED", "EXITO", "SUCCESS", "SOLUCIONADO"])

            clusters_dict[label_key]["samples"].append(row[1])
            clusters_dict[label_key]["total_count"] += 1
            if is_resolved:
                clusters_dict[label_key]["resolved_count"] += 1
            else:
                clusters_dict[label_key]["failed_count"] += 1

            if len(row) > 4 and row[4]:
                clusters_dict[label_key]["roles"].add(str(row[4]))
            if len(row) > 5 and row[5] and str(row[5]) != "None":
                clusters_dict[label_key]["refs_used"].add(str(row[5]))

        # Construcción de resultados con métricas de resolución y brechas
        cluster_results = []
        cluster_idx = 1
        for k, v in clusters_dict.items():
            if k == "outliers_noise" and len(clusters_dict) > 1:
                continue
            total = v["total_count"]
            resolved = v["resolved_count"]
            resolution_rate = round(resolved / total, 2) if total > 0 else 0.0
            resolution_rate_pct = round((resolved / total) * 100, 1) if total > 0 else 0.0

            # Alerta de brecha documental: tasa de resolución baja (< 50%) con recurrencia >= 2
            requires_new_doc = bool(resolution_rate < 0.50 and total >= 2)
            topic_name = summarize_cluster_topic(v["samples"])

            cluster_results.append({
                "cluster_id": cluster_idx,
                "cluster_name": topic_name or (v["samples"][0][:60] + "..."),
                "topic": topic_name,
                "representative_query": max(set(v["samples"]), key=v["samples"].count) if v["samples"] else "",
                "size": total,
                "total_queries": total,
                "resolution_rate": resolution_rate,
                "resolution_rate_pct": resolution_rate_pct,
                "requires_new_doc": requires_new_doc,
                "roles": list(v["roles"]) if v["roles"] else ["general"],
                "sample_queries": list(dict.fromkeys(v["samples"]))[:5],
                "refs": list(v["refs_used"])
            })
            cluster_idx += 1

        cluster_results.sort(key=lambda x: x["size"], reverse=True)

        return {
            "status": "success",
            "total_queries": len(queries),
            "total_analyzed_queries": len(queries),
            "total_clusters": len(cluster_results),
            "clusters_count": len(cluster_results),
            "knowledge_gaps_detected": sum(1 for c in cluster_results if c["requires_new_doc"]),
            "clusters": cluster_results
        }

    except Exception as e:
        logger.error(f"[Clustering] Error analizando clusters: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "total_queries": 0,
            "total_analyzed_queries": 0,
            "total_clusters": 0,
            "clusters_count": 0,
            "knowledge_gaps_detected": 0,
            "clusters": []
        }


def analyze_query_clusters(n_clusters: Optional[int] = None, min_queries_required: int = 4) -> Dict[str, Any]:
    """
    Función de compatibilidad que invoca get_query_clusters.
    """
    return get_query_clusters(
        db_path=DB_PATH,
        n_clusters=n_clusters,
        min_queries_required=min_queries_required
    )


def export_dpo_dataset(db_path: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Extrae y construye pares de preferencia DPO (prompt, chosen, rejected) a partir
    del historial de interacciones resueltas y fallidas en analytics.db y Golden Cache.
    
    Returns:
        Lista de diccionarios en formato {"prompt": str, "chosen": str, "rejected": str}.
    """
    active_db = db_path or DB_PATH
    dataset: List[Dict[str, str]] = []
    seen_prompts: Set[str] = set()

    # 1. Extraer casos validados desde Golden Cache (ChromaDB)
    try:
        import chromadb
        chroma_client = chromadb.PersistentClient(path="data/chroma_db")
        try:
            col = chroma_client.get_collection("golden_resolved_qa")
            results = col.get(include=["metadatas", "documents"])
            if results and results["documents"]:
                for doc, meta in zip(results["documents"], results["metadatas"]):
                    q = meta.get("user_query", "").strip() if meta else ""
                    if q and doc and q not in seen_prompts:
                        seen_prompts.add(q)
                        dataset.append({
                            "prompt": q,
                            "chosen": doc.strip(),
                            "rejected": "No dispongo de un instructivo institucional documentado para este caso específico. Por favor comunícate con la Mesa de Ayuda TI."
                        })
        except Exception as e:
            logger.debug(f"[DPO Export] Info consultando golden_resolved_qa: {e}")
    except Exception as e:
        logger.debug(f"[DPO Export] ChromaDB no accesible: {e}")

    # 2. Extraer interacciones de SQLite
    try:
        db_file = Path(active_db)
        if db_file.exists():
            conn = sqlite3.connect(active_db)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]

            if "telemetry_interactions" in tables:
                cursor.execute("""
                    SELECT 
                        i.user_query, 
                        COALESCE(i.bot_response, ''), 
                        COALESCE(s.final_status, i.feedback, 'UNKNOWN')
                    FROM telemetry_interactions i
                    LEFT JOIN telemetry_sessions s ON i.session_id = s.session_id
                    WHERE i.user_query IS NOT NULL AND length(trim(i.user_query)) > 5
                    ORDER BY i.id ASC
                """)
                rows = cursor.fetchall()

                resolved_map: Dict[str, str] = {}
                failed_map: Dict[str, str] = {}

                for query_val, resp_val, status_val in rows:
                    q_clean = query_val.strip()
                    resp_clean = resp_val.strip() if resp_val else ""
                    is_ok = any(ok in str(status_val).upper() for ok in ["FINALIZADO", "RESOLVED", "SOLUCIONADO", "EXITO"])

                    if is_ok and resp_clean and len(resp_clean) > 20:
                        resolved_map[q_clean] = resp_clean
                    elif not is_ok and resp_clean and len(resp_clean) > 10:
                        failed_map[q_clean] = resp_clean

                for q_key, chosen_resp in resolved_map.items():
                    if q_key not in seen_prompts:
                        seen_prompts.add(q_key)
                        rejected_resp = failed_map.get(
                            q_key,
                            "No se pudo completar la solicitud. Puedes intentar nuevamente o comunicarte con soporte técnico."
                        )
                        dataset.append({
                            "prompt": q_key,
                            "chosen": chosen_resp,
                            "rejected": rejected_resp
                        })

                for q_key, rejected_resp in failed_map.items():
                    if q_key not in seen_prompts:
                        seen_prompts.add(q_key)
                        dataset.append({
                            "prompt": q_key,
                            "chosen": f"Para atender tu requerimiento sobre '{q_key}', comunícate directamente con Soporte TI a solicitudcomputo@unisimon.edu.co (Barranquilla) o helpdesk@unisimon.edu.co (Cúcuta).",
                            "rejected": rejected_resp
                        })

            elif "chat_telemetry" in tables:
                cursor.execute("""
                    SELECT user_message, bot_response, final_state
                    FROM chat_telemetry
                    WHERE user_message IS NOT NULL AND length(trim(user_message)) > 5
                """)
                for q_val, resp_val, state_val in cursor.fetchall():
                    q_clean = q_val.strip()
                    if q_clean not in seen_prompts and resp_val:
                        seen_prompts.add(q_clean)
                        is_ok = "RESOLVED" in str(state_val).upper() or "FINALIZADO" in str(state_val).upper()
                        if is_ok:
                            dataset.append({
                                "prompt": q_clean,
                                "chosen": resp_val.strip(),
                                "rejected": "Error en el procedimiento. Por favor intenta más tarde."
                            })
                        else:
                            dataset.append({
                                "prompt": q_clean,
                                "chosen": "Comunícate con Soporte Técnico TI para gestionar tu solicitud.",
                                "rejected": resp_val.strip()
                            })

            conn.close()
    except Exception as e:
        logger.warning(f"[DPO Export] Error extrayendo dataset de SQLite: {e}")

    return dataset


def export_dpo_dataset_jsonl(db_path: Optional[str] = None) -> str:
    """
    Retorna el dataset DPO serializado en formato JSONL (1 objeto JSON por línea).
    """
    pairs = export_dpo_dataset(db_path=db_path)
    return "\n".join(json.dumps(p, ensure_ascii=False) for p in pairs)
