"""
Servicio de Telemetría, Analítica y Observabilidad para UniMon.
Gestiona el almacenamiento SQLite local en data/analytics.db y el cálculo de KPIs en tiempo real.
"""

import sqlite3
import time
import logging
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
            # Migración: asegurar existencia de bot_response si la tabla fue creada previamente
            cursor.execute("PRAGMA table_info(telemetry_interactions);")
            cols = [c[1] for c in cursor.fetchall()]
            if "bot_response" not in cols:
                cursor.execute("ALTER TABLE telemetry_interactions ADD COLUMN bot_response TEXT;")
            conn.commit()
            logger.info("Base de datos de telemetría inicializada en: %s", DB_PATH)
    except Exception as e:
        logger.error("Error al inicializar base de datos de telemetría: %s", e)


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
                    referenced_docs, latency_ms, prompt_tokens, eval_tokens, feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, 
                query, 
                bot_response,
                intent, 
                source or "UniMon", 
                docs_str, 
                latency_ms, 
                prompt_tokens, 
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


def get_kpis_summary() -> Dict[str, Any]:
    """
    Calcula y retorna las métricas consolidadas de KPIs de UniMon.
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Totales y Tasas
        total_sessions_row = cursor.execute("SELECT COUNT(*) FROM telemetry_sessions").fetchone()
        raw_total_sessions = total_sessions_row[0] if total_sessions_row else 0
        total_sessions = raw_total_sessions if raw_total_sessions > 0 else 1
        
        resolved_row = cursor.execute(
            "SELECT COUNT(*) FROM telemetry_sessions WHERE final_status IN ('FINALIZADO', 'SOLUCIONADO')"
        ).fetchone()
        resolved_sessions = resolved_row[0] if resolved_row else 0

        escalated_row = cursor.execute(
            "SELECT COUNT(*) FROM telemetry_sessions WHERE escalated_ticket = 1 OR final_status IN ('RADICANDO_TICKET', 'TICKET_CREADO')"
        ).fetchone()
        escalated_sessions = escalated_row[0] if escalated_row else 0
        
        # 2. Recursos y Rendimiento
        perf = cursor.execute("""
            SELECT 
                AVG(latency_ms) as avg_latency,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(eval_tokens) as total_eval_tokens,
                COUNT(*) as total_queries
            FROM telemetry_interactions
        """).fetchone()
        
        avg_lat = perf["avg_latency"] if perf and perf["avg_latency"] is not None else 0.0
        tot_prompt = perf["total_prompt_tokens"] if perf and perf["total_prompt_tokens"] is not None else 0
        tot_eval = perf["total_eval_tokens"] if perf and perf["total_eval_tokens"] is not None else 0
        tot_queries = perf["total_queries"] if perf and perf["total_queries"] is not None else 0

        # 3. Distribución por Rol
        roles_rows = cursor.execute(
            "SELECT COALESCE(role, 'general') as user_role, COUNT(*) as count FROM telemetry_sessions GROUP BY role"
        ).fetchall()
        roles_dist = {r["user_role"]: r["count"] for r in roles_rows} if roles_rows else {}
        
        # 4. Top 5 Documentos Más Consultados
        top_docs = cursor.execute("""
            SELECT referenced_docs, COUNT(*) as count 
            FROM telemetry_interactions 
            WHERE referenced_docs IS NOT NULL AND referenced_docs != 'None' AND referenced_docs != ''
            GROUP BY referenced_docs 
            ORDER BY count DESC LIMIT 5
        """).fetchall()
        
        # 5. Top 5 Preguntas Más Frecuentes
        top_queries = cursor.execute("""
            SELECT user_query, COUNT(*) as count 
            FROM telemetry_interactions 
            WHERE user_query IS NOT NULL AND user_query != ''
            GROUP BY LOWER(TRIM(user_query)) 
            ORDER BY count DESC LIMIT 5
        """).fetchall()

        tasa_res = round((resolved_sessions / total_sessions) * 100, 1) if raw_total_sessions > 0 else 0.0
        tasa_esc = round((escalated_sessions / total_sessions) * 100, 1) if raw_total_sessions > 0 else 0.0

        return {
            "total_sesiones": raw_total_sessions,
            "sesiones_resueltas": resolved_sessions,
            "sesiones_escaladas": escalated_sessions,
            "tasa_resolucion_n1_pct": tasa_res,
            "tasa_escalado_tickets_pct": tasa_esc,
            "latencia_promedio_ms": round(avg_lat, 1),
            "total_tokens_gastados": tot_prompt + tot_eval,
            "total_prompt_tokens": tot_prompt,
            "total_eval_tokens": tot_eval,
            "total_consultas": tot_queries,
            "distribucion_roles": roles_dist,
            "top_documentos_referenciados": [dict(r) for r in top_docs],
            "top_preguntas_frecuentes": [dict(q) for q in top_queries]
        }
