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
        res = await client.post(
            "/api/chat",
            json={
                "session_id": "auto_telemetry_sess",
                "mensaje": "Hola, buenos días"
            },
            headers={"X-Forwarded-For": "198.51.100.99"}
        )
        assert res.status_code == 200

    kpis = get_kpis_summary()
    assert kpis["total_sesiones"] >= 1
    assert kpis["total_consultas"] >= 1
    assert kpis["latencia_promedio_ms"] > 0


def test_reset_telemetry_db_clears_all_records():
    """Verifica que reset_telemetry_db limpie completamente las tablas y deje los KPIs en cero."""
    from app.services.telemetry_service import reset_telemetry_db

    log_interaction(session_id="s1", role="estudiante", query="q1", intent="DIAGNOSTICO", source="test", latency_ms=100.0)
    log_interaction(session_id="s2", role="profesor", query="q2", intent="DIAGNOSTICO", source="test", latency_ms=200.0)

    kpis_before = get_kpis_summary()
    assert kpis_before["total_consultas"] == 2
    assert kpis_before["total_sesiones"] == 2

    res = reset_telemetry_db()
    assert res["status"] == "success"
    assert res["interactions_cleared"] == 2
    assert res["sessions_cleared"] == 2

    kpis_after = get_kpis_summary()
    assert kpis_after["total_consultas"] == 0
    assert kpis_after["total_sesiones"] == 0
    assert kpis_after["total_tokens_gastados"] == 0


@pytest.mark.asyncio
async def test_reset_metrics_api_endpoint():
    """Verifica el endpoint POST /api/analytics/reset-metrics con y sin Golden Cache."""
    from app.services.telemetry_service import reset_telemetry_db
    from app.config import get_settings

    log_interaction(session_id="api_s1", role="administrativo", query="q_api", intent="DIAGNOSTICO", source="test", latency_ms=150.0)

    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.routers.analytics.clear_golden_cache", return_value=True) as mock_clear_gc:
            response = await client.post(
                "/api/analytics/reset-metrics?include_golden_cache=true",
                auth=(settings.admin_username, settings.admin_password)
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["interactions_cleared"] >= 1
            assert data["golden_cache_purged"] is True
            mock_clear_gc.assert_called_once()


@pytest.mark.asyncio
async def test_kpis_date_filtering_and_ranking():
    """Verifica filtros de fecha y ranking de preguntas no resueltas."""
    from app.services.telemetry_service import reset_telemetry_db, get_unresolved_queries_ranking, compare_kpi_periods

    reset_telemetry_db()

    # Inserciones con diferentes características
    # 1. Consulta exitosa
    log_interaction(session_id="sess_ok", role="estudiante", query="Como cambio mi clave", bot_response="Pasos para cambio de clave...", feedback="RESOLVED")
    update_session_status("sess_ok", "FINALIZADO")

    # 2. Consulta no resuelta por falta de documentación (Docente -> Prioridad ALTA)
    log_interaction(
        session_id="sess_fail1",
        role="profesor",
        query="Como configuro el proyector de la sala 402 para parcial",
        bot_response="No dispongo de un procedimiento para proyector sala 402.",
        source="UniMon_SinDocumentacion",
        feedback="RETRY"
    )
    update_session_status("sess_fail1", "RADICANDO_TICKET", escalated=True)

    # 3. Consulta no resuelta repetida (Estudiante -> Prioridad MEDIA)
    log_interaction(
        session_id="sess_fail2",
        role="estudiante",
        query="Como descargo mi carnet digital",
        bot_response="No encuentro información sobre carnet digital.",
        source="knowledge_base_fallback",
        feedback="NONE"
    )
    log_interaction(
        session_id="sess_fail3",
        role="estudiante",
        query="como descargo mi carnet digital",
        bot_response="No encuentro información sobre carnet digital.",
        source="knowledge_base_fallback",
        feedback="NO"
    )

    # Test KPI con filtro 'today'
    kpi_today = get_kpis_summary(start_date="today", end_date="today")
    assert kpi_today["total_queries"] == 4
    assert kpi_today["total_sessions"] == 4
    assert kpi_today["escalated_count"] == 1

    # Test Ranking de preguntas no resueltas
    unresolved_res = get_unresolved_queries_ranking(start_date="today", end_date="today")
    assert unresolved_res["status"] == "success"
    assert unresolved_res["total_unresolved_interactions"] == 3
    assert unresolved_res["total_unique_knowledge_gaps"] == 2

    ranking = unresolved_res["ranking"]
    # El carnet digital tiene 2 ocurrencias, proyector tiene 1 pero es de profesor con prioridad ALTA
    carnet_item = next(r for r in ranking if "carnet" in r["query"].lower())
    assert carnet_item["count"] == 2
    assert "Sin Procedimiento en RAG" in carnet_item["reasons"]

    proyector_item = next(r for r in ranking if "proyector" in r["query"].lower())
    assert proyector_item["priority"] == "ALTA"
    assert "profesor" in proyector_item["roles"]

    # Test Comparativa de períodos
    comp = compare_kpi_periods(p1_start="2026-01-01", p1_end="2026-01-02", p2_start="today", p2_end="today")
    assert comp["status"] == "success"
    assert "deltas" in comp
    assert comp["deltas"]["queries"]["period_2"] == 4


@pytest.mark.asyncio
async def test_analytics_api_new_endpoints():
    """Valida los endpoints HTTP /unresolved-queries, /compare, /ai-insights y /export-unresolved-csv."""
    from app.config import get_settings

    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/analytics/unresolved-queries
        res_unres = await client.get("/api/analytics/unresolved-queries?start_date=today&end_date=today")
        assert res_unres.status_code == 200
        json_unres = res_unres.json()
        assert "ranking" in json_unres
        assert "total_unresolved_interactions" in json_unres

        # 2. GET /api/analytics/compare
        res_comp = await client.get("/api/analytics/compare?p1_start=2026-01-01&p1_end=2026-01-02&p2_start=today&p2_end=today")
        assert res_comp.status_code == 200
        json_comp = res_comp.json()
        assert "deltas" in json_comp

        # 3. GET /api/analytics/ai-insights con mock de Ollama
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "### 1. Diagnóstico General\nEl asistente opera con normalidad."}
        with patch("httpx.post", return_value=mock_response):
            res_ai = await client.get("/api/analytics/ai-insights?start_date=today&end_date=today")
            assert res_ai.status_code == 200
            json_ai = res_ai.json()
            assert "insights" in json_ai
            assert "Diagnóstico" in json_ai["insights"]

        # 4. GET /api/analytics/export-unresolved-csv
        res_csv = await client.get(
            "/api/analytics/export-unresolved-csv?start_date=today&end_date=today",
            auth=(settings.admin_username, settings.admin_password)
        )
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "Consulta No Resuelta" in res_csv.text

        # 5. POST /api/analytics/draft-procedure con mock de Ollama
        mock_draft = MagicMock()
        mock_draft.status_code = 200
        mock_draft.json.return_value = {"response": "# PT-01: PERMISO DE PARQUEADERO\n\n## 1. OBJETIVO\nTramitar acceso vehicular."}
        with patch("httpx.post", return_value=mock_draft):
            res_draft = await client.post(
                "/api/analytics/draft-procedure",
                json={"query": "Como tramitar permiso de parqueadero", "role": "docente"}
            )
            assert res_draft.status_code == 200
            json_draft = res_draft.json()
            assert "content" in json_draft
            assert "OBJETIVO" in json_draft["content"]

        # 6. POST /api/analytics/save-procedure
        with patch("scripts.ingest_multimodal_docs.ingest_multimodal", return_value=True):
            res_save = await client.post(
                "/api/analytics/save-procedure",
                json={
                    "title": "PT-TI: Prueba Procedimiento Automatizado",
                    "content": "# PT-TI: Procedimiento de Prueba\n\n## 1. OBJETIVO\nValidar guardado.",
                    "role": "profesor"
                },
                auth=(settings.admin_username, settings.admin_password)
            )
            assert res_save.status_code == 200
            json_save = res_save.json()
            assert json_save["status"] == "success"
            assert "2_profesores" in json_save["folder"]


def test_dismiss_and_restore_unresolved_query():
    """Valida la exclusión de preguntas no relevantes del ranking y su restauración."""
    from app.services.telemetry_service import (
        reset_telemetry_db,
        log_interaction,
        get_unresolved_queries_ranking,
        dismiss_unresolved_query,
        get_dismissed_unresolved_queries,
        restore_dismissed_unresolved_query
    )

    reset_telemetry_db()

    # Inserción de 2 preguntas no resueltas
    log_interaction(
        session_id="s_fail_1",
        role="estudiante",
        query="la impresora le falta tinta negra y no imprime bien",
        bot_response="No poseo información para esa impresora.",
        source="UniMon_SinDocumentacion",
        feedback="RETRY"
    )
    log_interaction(
        session_id="s_fail_2",
        role="docente",
        query="Como configuro el proyector de la sala 402",
        bot_response="No dispongo de un procedimiento.",
        source="knowledge_base_fallback",
        feedback="NO"
    )

    ranking_before = get_unresolved_queries_ranking()
    assert ranking_before["total_unique_knowledge_gaps"] == 2

    # 1. Descartar pregunta de la impresora sin borrar interacciones
    res_dismiss = dismiss_unresolved_query(
        query="la impresora le falta tinta negra y no imprime bien",
        reason="No relevante / Fuera de alcance",
        delete_interactions=False
    )
    assert res_dismiss["status"] == "success"
    assert res_dismiss["interactions_deleted"] == 0

    # Verificar que ya no figura en el ranking
    ranking_after = get_unresolved_queries_ranking()
    assert ranking_after["total_unique_knowledge_gaps"] == 1
    assert not any("impresora" in r["query"].lower() for r in ranking_after["ranking"])

    # Verificar que aparece en la lista de descartadas
    dismissed_list = get_dismissed_unresolved_queries()
    assert len(dismissed_list) == 1
    assert "impresora" in dismissed_list[0]["query"].lower()
    assert dismissed_list[0]["reason"] == "No relevante / Fuera de alcance"

    # 2. Restaurar la pregunta
    res_restore = restore_dismissed_unresolved_query(query="la impresora le falta tinta negra y no imprime bien")
    assert res_restore["status"] == "success"

    ranking_restored = get_unresolved_queries_ranking()
    assert ranking_restored["total_unique_knowledge_gaps"] == 2
    assert any("impresora" in r["query"].lower() for r in ranking_restored["ranking"])

    # 3. Descartar con delete_interactions=True
    res_dismiss_del = dismiss_unresolved_query(
        query="la impresora le falta tinta negra y no imprime bien",
        reason="Prueba eliminada",
        delete_interactions=True
    )
    assert res_dismiss_del["status"] == "success"
    assert res_dismiss_del["interactions_deleted"] >= 1


@pytest.mark.asyncio
async def test_dismiss_and_restore_api_endpoints():
    """Valida los endpoints REST POST /dismiss, GET /dismissed y POST /restore con autenticación."""
    from app.config import get_settings
    from app.services.telemetry_service import reset_telemetry_db, log_interaction

    reset_telemetry_db()
    log_interaction(
        session_id="s_api_01",
        role="estudiante",
        query="Pregunta de prueba no relevante",
        bot_response="Sin documentación",
        source="UniMon_SinDocumentacion",
        feedback="RETRY"
    )

    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Sin autenticación -> 401
        res_no_auth = await client.post(
            "/api/analytics/unresolved-queries/dismiss",
            json={"query": "Pregunta de prueba no relevante"}
        )
        assert res_no_auth.status_code == 401

        # 2. Con autenticación -> 200 OK
        res_dismiss = await client.post(
            "/api/analytics/unresolved-queries/dismiss",
            json={
                "query": "Pregunta de prueba no relevante",
                "reason": "Prueba de integración",
                "delete_interactions": False
            },
            auth=(settings.admin_username, settings.admin_password)
        )
        assert res_dismiss.status_code == 200
        data_dismiss = res_dismiss.json()
        assert data_dismiss["status"] == "success"

        # 3. GET /dismissed
        res_list = await client.get(
            "/api/analytics/unresolved-queries/dismissed",
            auth=(settings.admin_username, settings.admin_password)
        )
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert data_list["total"] >= 1
        item_id = data_list["data"][0]["id"]

        # 4. POST /restore por ID
        res_restore = await client.post(
            "/api/analytics/unresolved-queries/restore",
            json={"id": item_id},
            auth=(settings.admin_username, settings.admin_password)
        )
        assert res_restore.status_code == 200
        assert res_restore.json()["status"] == "success"





