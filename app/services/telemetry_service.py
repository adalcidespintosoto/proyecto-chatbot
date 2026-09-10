"""
Servicio de Telemetría, Analítica y Observabilidad para UniMon.
Gestiona el almacenamiento SQLite local en data/analytics.db y el cálculo de KPIs en tiempo real.
"""

import sqlite3
import time
import json
import re
import logging
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
            # Migración: asegurar existencia de bot_response si la tabla fue creada previamente
            cursor.execute("PRAGMA table_info(telemetry_interactions);")
            cols = [c[1] for c in cursor.fetchall()]
            if "bot_response" not in cols:
                cursor.execute("ALTER TABLE telemetry_interactions ADD COLUMN bot_response TEXT;")
            conn.commit()
            logger.info("Base de datos de telemetría inicializada en: %s", DB_PATH)
    except Exception as e:
        logger.error("Error al inicializar base de datos de telemetría: %s", e)


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
    Calcula y retorna las métricas consolidadas de KPIs y observabilidad de UniMon
    directamente desde la base de datos SQLite (data/analytics.db).
    """
    if not DB_PATH.exists():
        init_telemetry_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]

        # Soporte para esquema unificado 'interactions'
        if "interactions" in tables and "telemetry_sessions" not in tables:
            total_queries = cursor.execute("SELECT COUNT(*) FROM interactions").fetchone()[0] or 0
            total_sessions = cursor.execute("SELECT COUNT(DISTINCT session_id) FROM interactions").fetchone()[0] or 0

            resolved = cursor.execute("SELECT COUNT(*) FROM interactions WHERE resolved = 1").fetchone()[0] or 0
            escalated = cursor.execute("SELECT COUNT(*) FROM interactions WHERE escalated = 1").fetchone()[0] or 0

            rate_resolved = round((resolved / total_sessions * 100), 1) if total_sessions > 0 else 0.0
            rate_escalated = round((escalated / total_sessions * 100), 1) if total_sessions > 0 else 0.0

            avg_latency = cursor.execute("SELECT AVG(latency_ms) FROM interactions WHERE latency_ms > 0").fetchone()[0] or 0.0
            tokens_in = cursor.execute("SELECT SUM(prompt_tokens) FROM interactions").fetchone()[0] or 0
            tokens_out = cursor.execute("SELECT SUM(eval_tokens) FROM interactions").fetchone()[0] or 0

            roles_data = cursor.execute("""
                SELECT COALESCE(user_role, role, 'No especificado') as role, COUNT(*) as count 
                FROM interactions 
                GROUP BY 1 
                ORDER BY count DESC
            """).fetchall()
            role_distribution = {row["role"]: row["count"] for row in roles_data}

            top_docs_data = cursor.execute("""
                SELECT docs_used, COUNT(*) as count 
                FROM interactions 
                WHERE docs_used IS NOT NULL AND docs_used NOT IN ('', 'None', '[]', 'null')
                GROUP BY docs_used 
                ORDER BY count DESC 
                LIMIT 5
            """).fetchall()
            top_documents = [
                {
                    "name": row["docs_used"].replace('["', '').replace('"]', '').replace('"', ''),
                    "referenced_docs": row["docs_used"].replace('["', '').replace('"]', '').replace('"', ''),
                    "count": row["count"]
                }
                for row in top_docs_data
            ]

            top_queries_data = cursor.execute("""
                SELECT user_query, COUNT(*) as count 
                FROM interactions 
                WHERE length(TRIM(user_query)) > 5 
                  AND LOWER(TRIM(user_query)) NOT IN ('hola', 'estudiante', 'profesor', 'docente', 'administrativo', 'funcionario', 'otros', 'otro', 'resolved', 'retry_diagnosis')
                GROUP BY LOWER(TRIM(user_query)) 
                ORDER BY count DESC 
                LIMIT 5
            """).fetchall()
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
            total_sessions = cursor.execute("SELECT COUNT(*) FROM telemetry_sessions").fetchone()[0] or 0
            total_queries = cursor.execute("SELECT COUNT(*) FROM telemetry_interactions").fetchone()[0] or 0

            resolved = cursor.execute(
                "SELECT COUNT(*) FROM telemetry_sessions WHERE final_status IN ('FINALIZADO', 'SOLUCIONADO', 'RESOLVED')"
            ).fetchone()[0] or 0

            escalated = cursor.execute(
                "SELECT COUNT(*) FROM telemetry_sessions WHERE escalated_ticket = 1 OR final_status IN ('RADICANDO_TICKET', 'TICKET_CREADO', 'ESCALADO')"
            ).fetchone()[0] or 0

            rate_resolved = round((resolved / total_sessions * 100), 1) if total_sessions > 0 else 0.0
            rate_escalated = round((escalated / total_sessions * 100), 1) if total_sessions > 0 else 0.0

            avg_lat_row = cursor.execute("SELECT AVG(latency_ms) FROM telemetry_interactions WHERE latency_ms > 0").fetchone()[0]
            avg_latency = avg_lat_row or 0.0
            tokens_in = cursor.execute("SELECT SUM(prompt_tokens) FROM telemetry_interactions").fetchone()[0] or 0
            tokens_out = cursor.execute("SELECT SUM(eval_tokens) FROM telemetry_interactions").fetchone()[0] or 0

            roles_data = cursor.execute("""
                SELECT COALESCE(role, 'No especificado') as role, COUNT(*) as count 
                FROM telemetry_sessions 
                GROUP BY role 
                ORDER BY count DESC
            """).fetchall()
            role_distribution = {row["role"]: row["count"] for row in roles_data}

            # Top 5 Documentos / Procedimientos Consultados
            top_docs_data = cursor.execute("""
                SELECT referenced_docs, COUNT(*) as count 
                FROM telemetry_interactions 
                WHERE referenced_docs IS NOT NULL AND referenced_docs NOT IN ('', 'None', '[]', 'null')
                GROUP BY referenced_docs 
                ORDER BY count DESC 
                LIMIT 5
            """).fetchall()
            top_documents = [
                {
                    "name": str(row["referenced_docs"]).replace('["', '').replace('"]', '').replace('"', ''),
                    "referenced_docs": str(row["referenced_docs"]).replace('["', '').replace('"]', '').replace('"', ''),
                    "count": row["count"]
                }
                for row in top_docs_data
            ]

            # Top 5 Preguntas Más Frecuentes
            top_queries_data = cursor.execute("""
                SELECT user_query, COUNT(*) as count 
                FROM telemetry_interactions 
                WHERE user_query IS NOT NULL 
                  AND length(TRIM(user_query)) > 5 
                  AND LOWER(TRIM(user_query)) NOT IN ('hola', 'estudiante', 'profesor', 'docente', 'administrativo', 'funcionario', 'otros', 'otro', 'resolved', 'retry_diagnosis')
                GROUP BY LOWER(TRIM(user_query)) 
                ORDER BY count DESC 
                LIMIT 5
            """).fetchall()
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
            # Claves estándar solicitadas
            "resolution_rate": rate_resolved,
            "escalation_rate": rate_escalated,
            "resolved_count": resolved,
            "escalated_count": escalated,
            "avg_latency_ms": round(avg_latency, 1),
            "tokens_in": tokens_in or 0,
            "tokens_out": tokens_out or 0,
            "total_tokens": total_tokens_val,
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
            "total_eval_tokens": tokens_out or 0,
            "total_tokens_gastados": total_tokens_val,
            "total_sesiones": total_sessions,
            "total_consultas": total_queries,
            "distribucion_roles": role_distribution,
            "top_documentos_referenciados": top_documents,
            "top_preguntas_frecuentes": top_queries
        }


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
            for t in ["telemetry_interactions", "telemetry_sessions", "telemetry_tickets"]:
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

