"""
Pruebas Unitarias y de Integración para el Módulo de Telemetría, Analítica y KPIs de UniMon.
"""

import sys
import os
import asyncio
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services import telemetry_service
from app.services.telemetry_service import (
    init_telemetry_db,
    log_interaction,
    update_session_status,
    get_kpis_summary,
    DB_PATH
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Configura una base de datos SQLite temporal para cada prueba de telemetría."""
    test_db = tmp_path / "test_analytics.db"
    monkeypatch.setattr(telemetry_service, "DB_PATH", test_db)
    init_telemetry_db()
    yield
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass


def test_init_and_log_interaction():
    """Verifica la inserción y registro correcto de sesiones e interacciones."""
    log_interaction(
        session_id="test_sess_01",
        role="docente",
        query="¿Cómo subo notas a SIAAF?",
        intent="DIAGNOSTICO",
        source="ollama_rag",
        docs=["manual_siaaf.pdf", "P-GT-01.pdf"],
        latency_ms=350.5,
        prompt_tokens=120,
        eval_tokens=85,
        feedback="NONE"
    )

    kpis = get_kpis_summary()
    assert kpis["total_sesiones"] == 1
    assert kpis["total_consultas"] == 1
    assert kpis["total_tokens_gastados"] == 205
    assert kpis["latencia_promedio_ms"] == 350.5
    assert kpis["distribucion_roles"].get("docente") == 1
    assert len(kpis["top_documentos_referenciados"]) == 1
    assert "manual_siaaf.pdf" in kpis["top_documentos_referenciados"][0]["referenced_docs"]
    assert len(kpis["top_preguntas_frecuentes"]) == 1


def test_session_resolution_and_escalation_kpis():
    """Verifica el cálculo de tasas de resolución en N1 y escalado a tickets."""
    # Sesión 1: Resuelta
    log_interaction(session_id="s1", role="estudiante", query="¿Cómo cambio mi contraseña?", intent="DIAGNOSTICO", source="RAG", latency_ms=200)
    update_session_status(session_id="s1", status="FINALIZADO", escalated=False)

    # Sesión 2: Escalada
    log_interaction(session_id="s2", role="funcionario", query="El cable de red está roto", intent="RADICANDO_TICKET", source="SemanticRouter", latency_ms=100)
    update_session_status(session_id="s2", status="TICKET_CREADO", escalated=True)

    # Sesión 3: Resuelta
    log_interaction(session_id="s3", role="docente", query="Guía de backups", intent="DIAGNOSTICO", source="RAG", latency_ms=300)
    update_session_status(session_id="s3", status="SOLUCIONADO", escalated=False)

    # Sesión 4: Activa
    log_interaction(session_id="s4", role="estudiante", query="Hola", intent="SALUDO", source="Assistant", latency_ms=50)

    kpis = get_kpis_summary()
    assert kpis["total_sesiones"] == 4
    assert kpis["sesiones_resueltas"] == 2
    assert kpis["sesiones_escaladas"] == 1
    # 2/4 = 50.0%
    assert kpis["tasa_resolucion_n1_pct"] == 50.0
    # 1/4 = 25.0%
    assert kpis["tasa_escalado_tickets_pct"] == 25.0
    assert kpis["distribucion_roles"]["estudiante"] == 2
    assert kpis["distribucion_roles"]["funcionario"] == 1
    assert kpis["distribucion_roles"]["docente"] == 1


@pytest.mark.asyncio
async def test_analytics_api_endpoint():
    """Verifica que el endpoint GET /api/analytics/kpis retorne el resumen completo en formato JSON."""
    log_interaction(session_id="api_sess", role="docente", query="Prueba API", intent="DIAGNOSTICO", source="Test", latency_ms=150.0)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/analytics/kpis")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"
        data = json_data["data"]
        assert "tasa_resolucion_n1_pct" in data
        assert "tasa_escalado_tickets_pct" in data
        assert "latencia_promedio_ms" in data
        assert "total_tokens_gastados" in data
        assert "distribucion_roles" in data
        assert "top_documentos_referenciados" in data
        assert "top_preguntas_frecuentes" in data


@pytest.mark.asyncio
async def test_chat_pipeline_records_telemetry_automatically():
    """Verifica que enviar un mensaje por POST /api/chat guarde automáticamente la telemetría."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/chat", json={
            "session_id": "auto_telemetry_sess",
            "mensaje": "Hola, buenos días"
        })
        assert res.status_code == 200

    kpis = get_kpis_summary()
    assert kpis["total_sesiones"] >= 1
    assert kpis["total_consultas"] >= 1
    assert kpis["latencia_promedio_ms"] > 0
