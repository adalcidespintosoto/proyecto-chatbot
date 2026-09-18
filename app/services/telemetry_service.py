"""
Servicio de Telemetría, Analítica y Observabilidad para UniMon.
Gestiona el almacenamiento SQLite local en data/analytics.db y el cálculo de KPIs en tiempo real.
"""

import sqlite3
import time
import json
import re
import logging
import io
import csv
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger("unimon.telemetry")

DB_PATH = Path("data/analytics.db")


def init_telemetry_db():
    """Inicializa la base de datos de telemetría y sus tablas si no existen."""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_sessions (
                    session_id TEXT PRIMARY KEY,
                    role TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    final_status TEXT DEFAULT 'ACTIVO',
                    escalated_ticket INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_query TEXT,
                    bot_response TEXT,
                    intent_category TEXT,
                    source_used TEXT,
                    referenced_docs TEXT,
                    latency_ms REAL,
                    prompt_tokens INTEGER DEFAULT 0,
                    eval_tokens INTEGER DEFAULT 0,
                    feedback TEXT DEFAULT 'NONE',
                    FOREIGN KEY (session_id) REFERENCES telemetry_sessions(session_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    email TEXT,
                    ticket_id INTEGER,
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_ignored_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT NOT NULL,
                    normalized_query TEXT UNIQUE NOT NULL,
                    reason TEXT DEFAULT 'No relevante',
                    dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Migración: asegurar existencia de bot_response y cached_tokens si la tabla fue creada previamente
            cursor.execute("PRAGMA table_info(telemetry_interactions);")
            cols = [c[1] for c in cursor.fetchall()]
            if "bot_response" not in cols:
                cursor.execute("ALTER TABLE telemetry_interactions ADD COLUMN bot_response TEXT;")
            if "cached_tokens" not in cols:
                cursor.execute("ALTER TABLE telemetry_interactions ADD COLUMN cached_tokens INTEGER DEFAULT 0;")
            conn.commit()
            logger.info("Base de datos de telemetría inicializada en: %s", DB_PATH)
    except Exception as e:
        logger.error("Error al inicializar base de datos de telemetría: %s", e)


def normalize_query_text(q: str) -> str:
    """Normaliza una consulta eliminando signos de puntuación, mayúsculas y espacios repetidos."""
    return re.sub(r'[\s\?\¿\!¡\.,]+', ' ', (q or '').lower()).strip()



def log_ticket_activity(
    session_id: str,
    email: str,
    ticket_id: int,
    action: str = "NUEVO"
):
    """Registra la creación de un ticket o adición de seguimiento en analytics.db."""
    try:
        if not DB_PATH.exists():
            init_telemetry_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    email TEXT,
                    ticket_id INTEGER,
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO telemetry_tickets (session_id, email, ticket_id, action)
                VALUES (?, ?, ?, ?)
            """, (session_id, email.strip().lower(), int(ticket_id), action.upper()))
            conn.commit()
            logger.info("Actividad de ticket registrada: email=%s, ticket_id=%s, action=%s", email, ticket_id, action)
    except Exception as e:
        logger.error("Error al registrar actividad de ticket en telemetría: %s", e)


def get_tickets_today_for_email_db(email: str) -> List[Dict[str, Any]]:
    """Consulta los tickets creados hoy en la base de datos local para un correo dado."""
    try:
        if not DB_PATH.exists():
            init_telemetry_db()
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    email TEXT,
                    ticket_id INTEGER,
                    action TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                SELECT ticket_id, action, created_at
                FROM telemetry_tickets
                WHERE LOWER(email) = ? AND action IN ('NUEVO', 'NUEVO_2')
                  AND DATE(created_at) = DATE('now')
                ORDER BY id DESC
            """, (email.strip().lower(),))
            rows = cursor.fetchall()
            return [{"ticket_id": r["ticket_id"], "action": r["action"], "created_at": r["created_at"]} for r in rows]
    except Exception as e:
        logger.error("Error al consultar tickets del día para %s: %s", email, e)
        return []


def log_interaction(
    session_id: str,
    role: Optional[str] = "general",
    query: str = "",
    bot_response: str = "",
    intent: str = "GENERAL",
    source: str = "UniMon",
    docs: Optional[List[str]] = None,
    latency_ms: float = 0.0,
    prompt_tokens: int = 0,
    cached_tokens: int = 0,
    eval_tokens: int = 0,
    feedback: str = "NONE"
):
    """
    Registra una interacción y actualiza/inserta la sesión en la base de datos de telemetría.
    """
    try:
        if not DB_PATH.exists():
            init_telemetry_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry_sessions (session_id, role)
                VALUES (?, ?)
                ON CONFLICT(session_id) DO UPDATE SET role=COALESCE(excluded.role, telemetry_sessions.role)
            """, (session_id, role or "general"))
            
            docs_str = ", ".join(docs) if docs else "None"
            cursor.execute("""
                INSERT INTO telemetry_interactions (
                    session_id, user_query, bot_response, intent_category, source_used,
                    referenced_docs, latency_ms, prompt_tokens, cached_tokens, eval_tokens, feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, 
                query, 
                bot_response,
                intent, 
                source or "UniMon", 
                docs_str, 
                latency_ms, 
                prompt_tokens, 
                cached_tokens,
                eval_tokens, 
                feedback
            ))
            conn.commit()
    except Exception as e:
        logger.warning("[Telemetry Error] log_interaction: %s", e)


def update_session_status(session_id: str, status: str, escalated: bool = False):
    """
    Actualiza el estado final y marca si la sesión requirió escalado a ticket de soporte.
    """
    try:
        if not DB_PATH.exists():
            init_telemetry_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE telemetry_sessions 
                SET final_status = ?, end_time = CURRENT_TIMESTAMP, escalated_ticket = ?
                WHERE session_id = ?
            """, (status, 1 if escalated else 0, session_id))
            conn.commit()
    except Exception as e:
        logger.warning("[Telemetry Error] update_session_status: %s", e)


def _build_sql_date_filter(date_col: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[List[str], List[str]]:
    """Genera las condiciones SQL y parámetros para filtrar por fecha."""
    conds = []
    params = []
    if start_date and start_date.strip():
        s = datetime.now().strftime("%Y-%m-%d") if start_date.strip().lower() in ("today", "hoy") else start_date.strip()
        conds.append(f"DATE({date_col}) >= DATE(?)")
        params.append(s)
    if end_date and end_date.strip():
        e = datetime.now().strftime("%Y-%m-%d") if end_date.strip().lower() in ("today", "hoy") else end_date.strip()
        conds.append(f"DATE({date_col}) <= DATE(?)")
        params.append(e)
    return conds, params


def get_kpis_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcula y retorna las métricas consolidadas de KPIs y observabilidad de UniMon
    directamente desde la base de datos SQLite (data/analytics.db), soportando filtros temporales.
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    # Normalizar valores "today" / "hoy"
    norm_start = datetime.now().strftime("%Y-%m-%d") if (start_date and start_date.strip().lower() in ("today", "hoy")) else (start_date.strip() if start_date else None)
    norm_end = datetime.now().strftime("%Y-%m-%d") if (end_date and end_date.strip().lower() in ("today", "hoy")) else (end_date.strip() if end_date else None)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        # Soporte para esquema unificado 'interactions'
        if "interactions" in tables and "telemetry_sessions" not in tables:
            int_conds, int_params = _build_sql_date_filter("timestamp", norm_start, norm_end)
            w_int = (" WHERE " + " AND ".join(int_conds)) if int_conds else ""
            and_int = (" AND " + " AND ".join(int_conds)) if int_conds else ""

            total_queries = cursor.execute(f"SELECT COUNT(*) FROM interactions{w_int}", int_params).fetchone()[0] or 0
            total_sessions = cursor.execute(f"SELECT COUNT(DISTINCT session_id) FROM interactions{w_int}", int_params).fetchone()[0] or 0

            resolved = cursor.execute(f"SELECT COUNT(*) FROM interactions WHERE resolved = 1{and_int}", int_params).fetchone()[0] or 0
            escalated = cursor.execute(f"SELECT COUNT(*) FROM interactions WHERE escalated = 1{and_int}", int_params).fetchone()[0] or 0

            rate_resolved = round((resolved / total_sessions * 100), 1) if total_sessions > 0 else 0.0
            rate_escalated = round((escalated / total_sessions * 100), 1) if total_sessions > 0 else 0.0

            avg_latency = cursor.execute(f"SELECT AVG(latency_ms) FROM interactions WHERE latency_ms > 0{and_int}", int_params).fetchone()[0] or 0.0
            tokens_in = cursor.execute(f"SELECT SUM(prompt_tokens) FROM interactions{w_int}", int_params).fetchone()[0] or 0
            tokens_out = cursor.execute(f"SELECT SUM(eval_tokens) FROM interactions{w_int}", int_params).fetchone()[0] or 0

            roles_data = cursor.execute(f"""
                SELECT COALESCE(user_role, role, 'No especificado') as role, COUNT(*) as count 
                FROM interactions{w_int}
                GROUP BY 1 
                ORDER BY count DESC
            """, int_params).fetchall()
            role_distribution = {row["role"]: row["count"] for row in roles_data}

            top_docs_data = cursor.execute(f"""
                SELECT docs_used, COUNT(*) as count 
                FROM interactions 
                WHERE docs_used IS NOT NULL AND docs_used NOT IN ('', 'None', '[]', 'null'){and_int}
                GROUP BY docs_used 
                ORDER BY count DESC 
                LIMIT 5
            """, int_params).fetchall()
            top_documents = [
                {
                    "name": row["docs_used"].replace('["', '').replace('"]', '').replace('"', ''),
                    "referenced_docs": row["docs_used"].replace('["', '').replace('"]', '').replace('"', ''),
                    "count": row["count"]
                }
                for row in top_docs_data
            ]

            top_queries_data = cursor.execute(f"""
                SELECT user_query, COUNT(*) as count 
                FROM interactions 
                WHERE length(TRIM(user_query)) > 5 
                  AND LOWER(TRIM(user_query)) NOT IN ('hola', 'estudiante', 'profesor', 'docente', 'administrativo', 'funcionario', 'otros', 'otro', 'resolved', 'retry_diagnosis'){and_int}
                GROUP BY LOWER(TRIM(user_query)) 
                ORDER BY count DESC 
                LIMIT 5
            """, int_params).fetchall()
            top_queries = [
                {
                    "query": row["user_query"],
                    "user_query": row["user_query"],
                    "count": row["count"]
                }
                for row in top_queries_data
            ]

        else:
            # Esquema estándar con 'telemetry_sessions' y 'telemetry_interactions'
            sess_conds, sess_params = _build_sql_date_filter("start_time", norm_start, norm_end)
            w_sess = (" WHERE " + " AND ".join(sess_conds)) if sess_conds else ""
            and_sess = (" AND " + " AND ".join(sess_conds)) if sess_conds else ""

            int_conds, int_params = _build_sql_date_filter("timestamp", norm_start, norm_end)
            w_int = (" WHERE " + " AND ".join(int_conds)) if int_conds else ""
            and_int = (" AND " + " AND ".join(int_conds)) if int_conds else ""

            total_sessions = cursor.execute(f"SELECT COUNT(*) FROM telemetry_sessions{w_sess}", sess_params).fetchone()[0] or 0
            total_queries = cursor.execute(f"SELECT COUNT(*) FROM telemetry_interactions{w_int}", int_params).fetchone()[0] or 0

            resolved = cursor.execute(
                f"SELECT COUNT(*) FROM telemetry_sessions WHERE final_status IN ('FINALIZADO', 'SOLUCIONADO', 'RESOLVED'){and_sess}",
                sess_params
            ).fetchone()[0] or 0

            escalated = cursor.execute(
                f"SELECT COUNT(*) FROM telemetry_sessions WHERE (escalated_ticket = 1 OR final_status IN ('RADICANDO_TICKET', 'TICKET_CREADO', 'ESCALADO')){and_sess}",
                sess_params
            ).fetchone()[0] or 0

            rate_resolved = round((resolved / total_sessions * 100), 1) if total_sessions > 0 else 0.0
            rate_escalated = round((escalated / total_sessions * 100), 1) if total_sessions > 0 else 0.0

            avg_lat_row = cursor.execute(f"SELECT AVG(latency_ms) FROM telemetry_interactions WHERE latency_ms > 0{and_int}", int_params).fetchone()[0]
            avg_latency = avg_lat_row or 0.0
            tokens_in = cursor.execute(f"SELECT SUM(prompt_tokens) FROM telemetry_interactions{w_int}", int_params).fetchone()[0] or 0
            try:
                tokens_cached = cursor.execute(f"SELECT SUM(COALESCE(cached_tokens, 0)) FROM telemetry_interactions{w_int}", int_params).fetchone()[0] or 0
            except Exception:
                tokens_cached = 0
            tokens_out = cursor.execute(f"SELECT SUM(eval_tokens) FROM telemetry_interactions{w_int}", int_params).fetchone()[0] or 0
            tokens_regular = max(0, (tokens_in or 0) - (tokens_cached or 0))

            # Cálculo de costo estimado en dólares y pesos (Tarifa GPT-5.6 Luna: $0.20 in, $0.02 cache, $1.20 out)
            cost_usd = (tokens_regular * 0.20 / 1_000_000) + (tokens_cached * 0.02 / 1_000_000) + (tokens_out * 1.20 / 1_000_000)
            cost_cop = cost_usd * 4150

            roles_data = cursor.execute(f"""
                SELECT COALESCE(role, 'No especificado') as role, COUNT(*) as count 
                FROM telemetry_sessions{w_sess}
                GROUP BY role 
                ORDER BY count DESC
            """, sess_params).fetchall()
            role_distribution = {row["role"]: row["count"] for row in roles_data}

            # Top 5 Documentos / Procedimientos Consultados
            top_docs_data = cursor.execute(f"""
                SELECT referenced_docs, COUNT(*) as count 
                FROM telemetry_interactions 
                WHERE referenced_docs IS NOT NULL AND referenced_docs NOT IN ('', 'None', '[]', 'null'){and_int}
                GROUP BY referenced_docs 
                ORDER BY count DESC 
                LIMIT 5
            """, int_params).fetchall()
            top_documents = [
                {
                    "name": str(row["referenced_docs"]).replace('["', '').replace('"]', '').replace('"', ''),
                    "referenced_docs": str(row["referenced_docs"]).replace('["', '').replace('"]', '').replace('"', ''),
                    "count": row["count"]
                }
                for row in top_docs_data
            ]

            # Top 5 Preguntas Más Frecuentes
            top_queries_data = cursor.execute(f"""
                SELECT user_query, COUNT(*) as count 
                FROM telemetry_interactions 
                WHERE user_query IS NOT NULL 
                  AND length(TRIM(user_query)) > 5 
                  AND LOWER(TRIM(user_query)) NOT IN ('hola', 'estudiante', 'profesor', 'docente', 'administrativo', 'funcionario', 'otros', 'otro', 'resolved', 'retry_diagnosis'){and_int}
                GROUP BY LOWER(TRIM(user_query)) 
                ORDER BY count DESC 
                LIMIT 5
            """, int_params).fetchall()
            top_queries = [
                {
                    "query": row["user_query"],
                    "user_query": row["user_query"],
                    "count": row["count"]
                }
                for row in top_queries_data
            ]

        total_tokens_val = (tokens_in or 0) + (tokens_out or 0)

        return {
            "period_start": norm_start,
            "period_end": norm_end,
            "resolution_rate": rate_resolved,
            "escalation_rate": rate_escalated,
            "resolved_count": resolved,
            "escalated_count": escalated,
            "avg_latency_ms": round(avg_latency, 1),
            "tokens_in": tokens_in or 0,
            "tokens_out": tokens_out or 0,
            "tokens_cached": tokens_cached or 0,
            "tokens_regular": tokens_regular or 0,
            "total_tokens": total_tokens_val,
            "estimated_cost_usd": round(cost_usd, 4),
            "estimated_cost_cop": round(cost_cop, 0),
            "total_sessions": total_sessions,
            "total_queries": total_queries,
            "role_distribution": role_distribution,
            "top_documents": top_documents,
            "top_queries": top_queries,
            # Alias heredados en español para retrocompatibilidad total
            "tasa_resolucion_n1_pct": rate_resolved,
            "tasa_escalado_tickets_pct": rate_escalated,
            "sesiones_resueltas": resolved,
            "sesiones_escaladas": escalated,
            "latencia_promedio_ms": round(avg_latency, 1),
            "total_prompt_tokens": tokens_in or 0,
            "total_cached_tokens": tokens_cached or 0,
            "total_regular_tokens": tokens_regular or 0,
            "total_eval_tokens": tokens_out or 0,
            "total_tokens_gastados": total_tokens_val,
            "gasto_estimado_usd": round(cost_usd, 4),
            "gasto_estimado_cop": round(cost_cop, 0),
            "total_sesiones": total_sessions,
            "total_consultas": total_queries,
            "distribucion_roles": role_distribution,
            "top_documentos_referenciados": top_documents,
            "top_preguntas_frecuentes": top_queries
        }


def get_unresolved_queries_ranking(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Identifica, clasifica y rankea las preguntas de usuarios que NO fueron resueltas por UniMon.
    Audita: feedback negativo/reintento, escalados a GLPI y respuestas con fallbacks de falta de procedimiento.
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    norm_start = datetime.now().strftime("%Y-%m-%d") if (start_date and start_date.strip().lower() in ("today", "hoy")) else (start_date.strip() if start_date else None)
    norm_end = datetime.now().strftime("%Y-%m-%d") if (end_date and end_date.strip().lower() in ("today", "hoy")) else (end_date.strip() if end_date else None)

    EXCLUDED_QUERIES = {
        'hola', 'buenas', 'buenos dias', 'buenas tardes', 'estudiante', 'profesor',
        'docente', 'administrativo', 'funcionario', 'otros', 'otro', 'visitante',
        'si', 'no', 'resolved', 'retry_diagnosis', 'gracias', 'ok', 'chao'
    }

    FALLBACK_SOURCES = {
        'unimon_sindocumentacion', 'unimon_no_doc_fallback', 'unimon_platform_not_documented',
        'knowledge_base_fallback', 'sin_documentacion', 'unimon_sin_doc_fallback',
        'unimon_sindocumentacion_directo'
    }

    UNRESOLVED_PHRASES = [
        'no dispongo de un procedimiento',
        'no dispongo de conocimiento',
        'no me encuentro en la capacidad de responder',
        'no cuento con información',
        'no poseo el procedimiento',
        'no encuentro información',
        'no se encuentra documentado',
        'no poseo un procedimiento institucional',
        'radicar directamente una solicitud de soporte técnico',
        'radique un caso de soporte técnico',
        'radicar un caso de soporte técnico',
        'no tengo registros en mi base',
        'no tengo información documentada',
        'sin documentación'
    ]

    HIGH_PRIORITY_KEYWORDS = [
        'clase', 'parcial', 'urgente', 'bloqueado', 'examen', 'sala', 'proyector', 
        'red', 'wifi', 'servidor', 'caido', 'clave', 'contraseña', 'audio', 'pantalla'
    ]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        if "telemetry_interactions" not in tables:
            return {"status": "success", "total_unresolved": 0, "ranking": []}

        ignored_keys = set()
        if "telemetry_ignored_queries" in tables:
            cursor.execute("SELECT normalized_query FROM telemetry_ignored_queries;")
            ignored_keys = {r[0] for r in cursor.fetchall()}

        # Mapeo de sesión -> última consulta sustantiva real (para cuando la interacción registró solo el rol o acción)
        cursor.execute("""
            SELECT session_id, user_query
            FROM telemetry_interactions
            WHERE user_query IS NOT NULL 
              AND length(TRIM(user_query)) >= 4
              AND LOWER(TRIM(user_query)) NOT IN (
                  'hola', 'buenas', 'buenos dias', 'buenas tardes', 'estudiante', 'profesor',
                  'docente', 'administrativo', 'funcionario', 'otros', 'otro', 'visitante',
                  'si', 'no', 'resolved', 'retry_diagnosis', 'create_ticket', 'gracias', 'ok', 'chao'
              )
            ORDER BY id ASC
        """)
        session_query_map = {}
        for r in cursor.fetchall():
            session_query_map[r[0]] = r[1]

        int_conds, int_params = _build_sql_date_filter("i.timestamp", norm_start, norm_end)
        w_int = (" WHERE " + " AND ".join(int_conds)) if int_conds else ""

        query_sql = f"""
            SELECT 
                i.id,
                i.session_id,
                i.timestamp,
                i.user_query,
                COALESCE(i.bot_response, '') as bot_response,
                COALESCE(s.role, 'general') as role,
                COALESCE(i.source_used, 'UniMon') as source_used,
                COALESCE(i.feedback, 'NONE') as feedback,
                COALESCE(s.final_status, 'UNKNOWN') as final_status,
                COALESCE(s.escalated_ticket, 0) as escalated_ticket
            FROM telemetry_interactions i
            LEFT JOIN telemetry_sessions s ON i.session_id = s.session_id
            {w_int}
            ORDER BY i.id DESC
        """
        cursor.execute(query_sql, int_params)
        rows = cursor.fetchall()

    groups: Dict[str, Dict[str, Any]] = {}
    total_unresolved_count = 0

    for row in rows:
        user_q = (row["user_query"] or "").strip()
        # Si la interacción registrada es un rol o comando de botón, resolver a la consulta técnica real de la sesión
        if user_q.lower() in EXCLUDED_QUERIES or len(user_q) < 4:
            user_q = session_query_map.get(row["session_id"], "").strip()

        if not user_q or len(user_q) < 4 or user_q.lower() in EXCLUDED_QUERIES:
            continue

        reasons = []
        feedback_val = str(row["feedback"] or "").upper()
        if feedback_val in ("RETRY", "ESCALATED", "NO", "NEGATIVE"):
            reasons.append("Feedback Negativo / Reintento")

        esc_ticket = int(row["escalated_ticket"] or 0)
        final_st = str(row["final_status"] or "").upper()
        if esc_ticket == 1 or any(st in final_st for st in ["RADICANDO", "TICKET", "ESCALADO"]):
            reasons.append("Escalado a Mesa de Ayuda GLPI")

        source_val = str(row["source_used"] or "").lower()
        bot_resp = str(row["bot_response"] or "")
        bot_resp_lower = bot_resp.lower()
        if source_val in FALLBACK_SOURCES or any(phrase in bot_resp_lower for phrase in UNRESOLVED_PHRASES):
            reasons.append("Sin Procedimiento en RAG")

        if not reasons:
            continue  # Consulta fue resuelta con éxito

        # Si la sesión terminó con éxito confirmado por el usuario y no hubo escalado ni fallback documental, omitir reintentos intermedios
        if (final_st in ("FINALIZADO", "SOLUCIONADO", "RESOLVED")) and esc_ticket == 0 and "Sin Procedimiento en RAG" not in reasons:
            continue

        norm_key = normalize_query_text(user_q)
        if norm_key in ignored_keys:
            continue

        total_unresolved_count += 1

        if norm_key not in groups:
            groups[norm_key] = {
                "query": user_q,
                "count": 0,
                "roles": set(),
                "reasons": set(),
                "last_seen": row["timestamp"] or "",
                "sample_response": bot_resp[:300] if bot_resp else "",
                "session_count": 0
            }

        item = groups[norm_key]
        item["count"] += 1
        if row["role"]:
            item["roles"].add(str(row["role"]))
        item["reasons"].update(reasons)
        if row["timestamp"] and (not item["last_seen"] or str(row["timestamp"]) > str(item["last_seen"])):
            item["last_seen"] = str(row["timestamp"])
            if bot_resp:
                item["sample_response"] = bot_resp[:300]

    ranking_list = []
    for norm_key, item in groups.items():
        roles_list = list(item["roles"]) or ["general"]
        roles_lower = [r.lower() for r in roles_list]

        is_teacher = any("prof" in r or "doc" in r for r in roles_lower)
        is_urgent = any(kw in item["query"].lower() for kw in HIGH_PRIORITY_KEYWORDS)

        if is_teacher or is_urgent:
            priority = "ALTA"
        elif item["count"] >= 3 or any("est" in r for r in roles_lower):
            priority = "MEDIA"
        else:
            priority = "NORMAL"

        ranking_list.append({
            "query": item["query"],
            "count": item["count"],
            "priority": priority,
            "roles": roles_list,
            "reasons": list(item["reasons"]),
            "last_seen": item["last_seen"],
            "sample_response": item["sample_response"]
        })

    # Ordenar por mayor conteo y luego fecha más reciente
    ranking_list.sort(key=lambda x: (x["count"], x["last_seen"]), reverse=True)

    # Asignar posición de ranking
    for idx, item in enumerate(ranking_list, start=1):
        item["rank"] = idx

    return {
        "status": "success",
        "period_start": norm_start,
        "period_end": norm_end,
        "total_unresolved_interactions": total_unresolved_count,
        "total_unique_knowledge_gaps": len(ranking_list),
        "ranking": ranking_list[:limit]
    }


def dismiss_unresolved_query(
    query: str,
    reason: str = "No relevante",
    delete_interactions: bool = False
) -> Dict[str, Any]:
    """
    Descarta una consulta del ranking de Knowledge Gaps marcándola como no relevante.
    Opcionalmente elimina los registros de interacción correspondientes en telemetry_interactions.
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    norm_key = normalize_query_text(query)
    clean_query = (query or "").strip()
    reason_clean = (reason or "No relevante").strip()

    if not clean_query:
        return {"status": "error", "message": "La consulta no puede estar vacía."}

    deleted_count = 0
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_ignored_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                normalized_query TEXT UNIQUE NOT NULL,
                reason TEXT DEFAULT 'No relevante',
                dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT INTO telemetry_ignored_queries (query_text, normalized_query, reason, dismissed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(normalized_query) DO UPDATE SET
                query_text = excluded.query_text,
                reason = excluded.reason,
                dismissed_at = CURRENT_TIMESTAMP
        """, (clean_query, norm_key, reason_clean))

        if delete_interactions:
            cursor.execute("SELECT id, user_query FROM telemetry_interactions")
            rows = cursor.fetchall()
            ids_to_delete = [
                r[0] for r in rows
                if normalize_query_text(r[1]) == norm_key or (r[1] and clean_query.lower() in r[1].lower())
            ]
            if ids_to_delete:
                placeholders = ",".join(["?"] * len(ids_to_delete))
                cursor.execute(
                    f"DELETE FROM telemetry_interactions WHERE id IN ({placeholders})",
                    ids_to_delete
                )
                deleted_count = len(ids_to_delete)

        conn.commit()

    logger.info("Pregunta '%s' descartada de Knowledge Gaps (delete_interactions=%s, deleted=%d)", clean_query, delete_interactions, deleted_count)
    return {
        "status": "success",
        "message": f"Pregunta '{clean_query}' descartada del ranking exitosamente.",
        "query": clean_query,
        "normalized_query": norm_key,
        "reason": reason_clean,
        "interactions_deleted": deleted_count
    }


def get_dismissed_unresolved_queries() -> List[Dict[str, Any]]:
    """
    Retorna el listado de consultas que han sido descartadas del ranking de Knowledge Gaps.
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_ignored_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                normalized_query TEXT UNIQUE NOT NULL,
                reason TEXT DEFAULT 'No relevante',
                dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            SELECT id, query_text, normalized_query, reason, dismissed_at
            FROM telemetry_ignored_queries
            ORDER BY dismissed_at DESC
        """)
        rows = cursor.fetchall()

    return [
        {
            "id": r["id"],
            "query": r["query_text"],
            "normalized_query": r["normalized_query"],
            "reason": r["reason"] or "No relevante",
            "dismissed_at": str(r["dismissed_at"])
        }
        for r in rows
    ]


def restore_dismissed_unresolved_query(
    query: Optional[str] = None,
    item_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Restaura una consulta previamente descartada para que vuelva a figurar en el ranking.
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_ignored_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                normalized_query TEXT UNIQUE NOT NULL,
                reason TEXT DEFAULT 'No relevante',
                dismissed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        if item_id:
            cursor.execute("DELETE FROM telemetry_ignored_queries WHERE id = ?", (item_id,))
        elif query:
            norm_key = normalize_query_text(query)
            cursor.execute("DELETE FROM telemetry_ignored_queries WHERE normalized_query = ? OR query_text = ?", (norm_key, query.strip()))
        else:
            return {"status": "error", "message": "Debe especificar 'id' o 'query' para restaurar."}

        affected = cursor.rowcount
        conn.commit()

    if affected > 0:
        logger.info("Consulta restaurada en Knowledge Gaps (query=%s, id=%s)", query, item_id)
        return {"status": "success", "message": "Pregunta restaurada en el ranking exitosamente."}
    else:
        return {"status": "warning", "message": "No se encontró ningún registro para restaurar."}



def compare_kpi_periods(
    p1_start: Optional[str] = None,
    p1_end: Optional[str] = None,
    p2_start: Optional[str] = None,
    p2_end: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compara las métricas de rendimiento y KPIs entre dos períodos (días o meses),
    calculando deltas numéricos, variaciones porcentuales e indicadores de tendencia.
    """
    kpi1 = get_kpis_summary(start_date=p1_start, end_date=p1_end)
    kpi2 = get_kpis_summary(start_date=p2_start, end_date=p2_end)

    def calc_delta(val1, val2, is_pct_points=False, lower_is_better=False):
        v1 = val1 or 0
        v2 = val2 or 0
        diff = round(v2 - v1, 1)
        if is_pct_points:
            pct_change = diff
        else:
            pct_change = round(((v2 - v1) / v1 * 100), 1) if v1 > 0 else (100.0 if v2 > 0 else 0.0)

        if diff == 0:
            trend = "neutral"
        elif lower_is_better:
            trend = "better" if diff < 0 else "worse"
        else:
            trend = "better" if diff > 0 else "worse"

        return {
            "period_1": v1,
            "period_2": v2,
            "diff": diff,
            "pct_change": pct_change,
            "trend": trend
        }

    deltas = {
        "queries": calc_delta(kpi1.get("total_queries", 0), kpi2.get("total_queries", 0)),
        "sessions": calc_delta(kpi1.get("total_sessions", 0), kpi2.get("total_sessions", 0)),
        "resolution_rate": calc_delta(kpi1.get("resolution_rate", 0.0), kpi2.get("resolution_rate", 0.0), is_pct_points=True, lower_is_better=False),
        "escalation_rate": calc_delta(kpi1.get("escalation_rate", 0.0), kpi2.get("escalation_rate", 0.0), is_pct_points=True, lower_is_better=True),
        "avg_latency_ms": calc_delta(kpi1.get("avg_latency_ms", 0.0), kpi2.get("avg_latency_ms", 0.0), lower_is_better=True),
        "tokens": calc_delta(kpi1.get("total_tokens", 0), kpi2.get("total_tokens", 0))
    }

    return {
        "status": "success",
        "period_1": {"start": p1_start, "end": p1_end, "kpis": kpi1},
        "period_2": {"start": p2_start, "end": p2_end, "kpis": kpi2},
        "deltas": deltas
    }


def generate_ai_observability_insights(
    kpis: Dict[str, Any],
    top_unresolved: List[Dict[str, Any]],
    period_label: str = "el período analizado"
) -> Dict[str, Any]:
    """
    Invoca al modelo local Ollama (unimon:8b) para realizar un diagnóstico analítico
    sobre los KPIs y vacíos de conocimiento, generando recomendaciones de mejora institucional.
    """
    from app.config import get_settings
    import httpx

    settings = get_settings()

    unresolved_txt = ""
    if top_unresolved:
        for item in top_unresolved[:6]:
            roles = ", ".join(item.get("roles", [])) or "general"
            reasons = ", ".join(item.get("reasons", [])) or "No especificado"
            unresolved_txt += f"- [{item.get('priority', 'MEDIA')}] \"{item.get('query')}\" ({item.get('count')} consultas, Roles: {roles}, Motivo: {reasons})\n"
    else:
        unresolved_txt = "- No se registraron preguntas no resueltas en este período."

    prompt = f"""Actúa como Consultor Senior de Observabilidad y Soporte TI para la Universidad Simón Bolívar (Barranquilla y Cúcuta).
Analiza las siguientes métricas de telemetría y brechas de conocimiento del chatbot institucional UniMon correspondientes a: {period_label}.

📊 MÉTRICAS CONSOLIDADAS:
- Total de Consultas: {kpis.get('total_queries', 0)}
- Sesiones de Usuario: {kpis.get('total_sessions', 0)}
- Tasa de Resolución Nivel 1: {kpis.get('resolution_rate', 0)}%
- Tasa de Escalado a Mesa GLPI: {kpis.get('escalation_rate', 0)}%
- Latencia Promedio: {kpis.get('avg_latency_ms', 0)} ms
- Distribución de Perfiles: {json.dumps(kpis.get('role_distribution', {}), ensure_ascii=False)}

⚠️ TOP PREGUNTAS NO RESUELTAS (BRECHAS DE CONOCIMIENTO):
{unresolved_txt}

Por favor, genera un INFORME EJECUTIVO DE OBSERVABILIDAD Y MEJORA CONTINUA en formato Markdown con las siguientes secciones:

### 1. 📋 Diagnóstico General del Desempeño
(Evalúa con criterio técnico la salud del asistente, tasa de autoservicio y tiempos de respuesta en el período).

### 2. ⚠️ Puntos Críticos y Brechas Detectadas
(Analiza detalladamente qué consultas o trámites fallaron, qué roles universitarios se vieron más afectados y cuál fue la causa raíz).

### 3. 🎯 Plan de Acción y Recomendaciones Prioritarias
(Enumera 3 acciones concretas y prioritarias para el equipo de TI: nuevos procedimientos a redactar para RAG, ajustes de flujos o medidas en Mesa de Ayuda).

Mantén un tono profesional, analítico y enfocado en la mejora continua del servicio de TI de la Universidad Simón Bolívar."""

    try:
        from app.services.llm_client import get_llm_client
        llm_client = get_llm_client()
        insights_text = llm_client.generate_sync(prompt=prompt, max_tokens=1000, timeout=45.0)
        if insights_text:
            return {
                "status": "success",
                "insights": insights_text,
                "period": period_label,
                "model": llm_client.active_model
            }
    except Exception as e:
        logger.warning("Error generando diagnóstico de IA con LLMClient: %s", e)

    # Fallback analítico determinista si Ollama no está disponible o timeout
    res_rate = kpis.get('resolution_rate', 0)
    diag = "favorable y estable" if res_rate >= 70 else ("aceptable con oportunidades" if res_rate >= 40 else "crítico requiriendo intervención")
    fallback_md = f"""### 1. 📋 Diagnóstico General del Desempeño
El asistente UniMon registró un desempeño **{diag}** en {period_label}, alcanzando una tasa de autoservicio Nivel 1 del **{res_rate}%** y una tasa de escalado a tickets GLPI del **{kpis.get('escalation_rate', 0)}%** sobre un volumen de **{kpis.get('total_queries', 0)} consultas**. La latencia promedio de respuesta fue de **{kpis.get('avg_latency_ms', 0)} ms**.

### 2. ⚠️ Puntos Críticos y Brechas Detectadas
Se identificaron **{len(top_unresolved)} temas o trámites sin resolver**. Las principales causas detectadas corresponden a consultas donde el asistente declaró no poseer procedimiento documentado o casos en que el usuario solicitó asistencia humana directa.

### 3. 🎯 Plan de Acción y Recomendaciones Prioritarias
1. **Redacción de Procedimientos Faltantes:** Priorizar en la base RAG las consultas con prioridad ALTA y recurrencia recurrente mediante el generador de procedimientos.
2. **Optimización de Diálogo y Empatía:** Ajustar los mensajes de fallback para ofrecer alternativas de autoservicio antes de escalar a ticket.
3. **Seguimiento Comparativo Interdiario:** Evaluar periódicamente la evolución de la tasa de resolución para medir el impacto de las nuevas guías indexadas.
"""
    return {
        "status": "fallback",
        "insights": fallback_md,
        "period": period_label,
        "model": "rule_based_fallback"
    }


def draft_procedure_with_ai(
    unresolved_query: str,
    target_role: str = "general"
) -> Dict[str, Any]:
    """
    Utiliza Ollama para generar un borrador estructurado de procedimiento institucional
    oficial de la Universidad Simón Bolívar en formato Markdown.
    """
    from app.config import get_settings
    import httpx

    settings = get_settings()

    prompt = f"""Actúa como Especialista en Soporte TI y Gestión Documental de la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta).
Redacta un PROCEDIMIENTO INSTITUCIONAL OFICIAL DE TI en formato Markdown para dar solución completa a la siguiente consulta de usuario:

Consulta del usuario: "{unresolved_query}"
Perfil objetivo: "{target_role}"

Estructura obligatoria del documento Markdown:
# PT-[CÓDIGO CORTO]: [TÍTULO DESCRIPTIVO EN MAYÚSCULAS]

## 1. OBJETIVO
(Explicar qué resuelve este procedimiento de TI de manera concisa).

## 2. ALCANCE Y ROLES APLICABLES
(Indicar si aplica a Estudiantes, Profesores o Administrativos en Barranquilla o Cúcuta).

## 3. REQUISITOS PREVIOS
(Credenciales, acceso a portales institucionales, conexión a internet/red USB).

## 4. PROCEDIMIENTO PASO A PASO
(Pasos numerados, directos, con nombres claros de opciones y botones).

## 5. RECOMENDACIONES Y PREGUNTAS FRECUENTES
(Qué verificar ante posibles fallas comunes o contratiempos).

## 6. CANALES DE ESCALADO Y ATENCIÓN
(Mesa de Ayuda TI USB, correo institucional soporteti@unisimon.edu.co, radicación en portal institucional).

Redacta únicamente el documento Markdown institucional, sin preámbulos ni explicaciones adicionales."""

    try:
        from app.services.llm_client import get_llm_client
        llm_client = get_llm_client()
        content = llm_client.generate_sync(prompt=prompt, max_tokens=1200, timeout=45.0)
        if content:
            first_line = content.split("\n")[0].replace("#", "").strip()
            title = first_line if first_line else f"Procedimiento para {unresolved_query[:40]}"
            return {
                "status": "success",
                "title": title,
                "content": content,
                "query": unresolved_query,
                "role": target_role
            }
    except Exception as e:
        logger.warning("Error redactando borrador de procedimiento con LLMClient: %s", e)

    clean_title = f"PT-TI: Procedimiento para {unresolved_query.capitalize()}"
    fallback_content = f"""# {clean_title}

## 1. OBJETIVO
Brindar el paso a paso institucional para atender solicitudes sobre "{unresolved_query}" en la Universidad Simón Bolívar.

## 2. ALCANCE Y ROLES APLICABLES
Aplica a: {target_role.capitalize()} (Sedes Barranquilla y Cúcuta).

## 3. REQUISITOS PREVIOS
- Disponer de correo institucional activo (@unisimon.edu.co).
- Estar conectado a la red institucional USB o portal oficial.

## 4. PROCEDIMIENTO PASO A PASO
1. Ingrese al portal web institucional de la Universidad Simón Bolívar ([www.unisimon.edu.co](https://www.unisimon.edu.co)).
2. Diríjase a la sección correspondiente a su perfil ({target_role.capitalize()}).
3. Siga las instrucciones del sistema para gestionar su trámite.
4. Si se presenta algún inconveniente, capture la evidencia del error.

## 5. RECOMENDACIONES Y PREGUNTAS FRECUENTES
- Verifique que su navegador tenga las cookies y caché limpias.
- No comparta sus credenciales de acceso con terceros.

## 6. CANALES DE ESCALADO Y ATENCIÓN
Si requiere asistencia presencial o remota, contacte a la Mesa de Ayuda TI:
- Correo: soporteti@unisimon.edu.co
- Portal de Autoservicio TI: Mesa de Ayuda GLPI
"""
    return {
        "status": "success",
        "title": clean_title,
        "content": fallback_content,
        "query": unresolved_query,
        "role": target_role
    }


def save_and_index_procedure(
    title: str,
    content: str,
    role: str = "general"
) -> Dict[str, Any]:
    """
    Guarda el procedimiento en la carpeta correspondiente de data/docs y lo re-indexa
    automáticamente en ChromaDB para estar disponible de inmediato en el chatbot.
    """
    r_lower = (role or "general").lower()
    if "prof" in r_lower or "doc" in r_lower:
        folder_name = "2_profesores"
    elif "est" in r_lower:
        folder_name = "1_estudiantes"
    elif "admin" in r_lower or "func" in r_lower:
        folder_name = "3_funcionarios_gestion"
    else:
        folder_name = "4_general_normativa"

    target_dir = Path("data/docs") / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    clean_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title.lower())
    clean_title = re.sub(r'_+', '_', clean_title).strip('_')[:50] or "nuevo_procedimiento"
    file_name = f"{clean_title}.md"
    file_path = target_dir / file_name

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    reindexed = False
    try:
        from scripts.ingest_multimodal_docs import ingest_multimodal, apply_taxonomy_to_chroma
        success = ingest_multimodal(file_path=str(file_path), incremental=True)
        try:
            apply_taxonomy_to_chroma()
        except Exception:
            pass
        reindexed = bool(success)
    except Exception as e:
        logger.warning("Error al auto re-indexar archivo %s en ChromaDB: %s", file_path, e)

    return {
        "status": "success",
        "file_name": file_name,
        "folder": folder_name,
        "file_path": str(file_path),
        "reindexed": reindexed,
        "message": f"Procedimiento guardado en '{folder_name}/{file_name}' e indexado exitosamente en RAG."
    }


def export_unresolved_queries_csv(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Exporta el ranking de preguntas no resueltas en formato CSV para análisis en Excel.
    """
    ranking_data = get_unresolved_queries_ranking(start_date=start_date, end_date=end_date, limit=300)
    items = ranking_data.get("ranking", [])

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Ranking", "Consulta No Resuelta", "Frecuencia", "Prioridad", "Roles Afectados", "Motivo de Falla", "Ultima Ocurrencia", "Respuesta Previa del Bot"])

    for item in items:
        roles_str = "; ".join(item.get("roles", []))
        reasons_str = "; ".join(item.get("reasons", []))
        writer.writerow([
            item.get("rank", ""),
            item.get("query", ""),
            item.get("count", 0),
            item.get("priority", "NORMAL"),
            roles_str,
            reasons_str,
            item.get("last_seen", ""),
            item.get("sample_response", "")
        ])

    return output.getvalue()


def reset_telemetry_db() -> Dict[str, Any]:
    """
    Elimina todos los registros históricos de telemetría (sesiones, interacciones y tickets)
    en data/analytics.db para permitir una medición limpia de desempeño.
    """
    try:
        if not DB_PATH.exists():
            init_telemetry_db()
            return {
                "status": "success",
                "interactions_cleared": 0,
                "sessions_cleared": 0,
                "tickets_cleared": 0,
                "message": "Base de datos inicializada sin registros previos."
            }

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            counts = {}
            for t in ["telemetry_interactions", "telemetry_sessions", "telemetry_tickets", "telemetry_ignored_queries"]:
                if t in tables:
                    counts[t] = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                    cursor.execute(f"DELETE FROM {t};")
                else:
                    counts[t] = 0

            conn.commit()
            cursor.execute("VACUUM;")
            logger.info("Base de datos de telemetría reseteada con éxito: %s", counts)

        return {
            "status": "success",
            "interactions_cleared": counts.get("telemetry_interactions", 0),
            "sessions_cleared": counts.get("telemetry_sessions", 0),
            "tickets_cleared": counts.get("telemetry_tickets", 0),
            "message": "Métricas y telemetría histórica reseteadas exitosamente."
        }
    except Exception as e:
        logger.error("Error al resetear la base de datos de telemetría: %s", e)
        return {"status": "error", "message": str(e)}

