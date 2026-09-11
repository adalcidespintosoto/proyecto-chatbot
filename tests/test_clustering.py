"""
Tests unitarios para el servicio de Clustering Semántico y Detección de Brechas Documentales.
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.clustering_service import analyze_query_clusters, summarize_cluster_topic


@pytest.fixture
def temp_analytics_db(tmp_path):
    """Crea una base de datos SQLite temporal con datos de prueba estructurados."""
    db_file = tmp_path / "test_analytics.db"
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE queries_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Insertar datos de prueba: 3 resueltos (certificados) y 3 no resueltos (carnetización)
    sample_data = [
        ("¿Cómo saco un certificado de notas?", "FINALIZADO"),
        ("¿Dónde solicito certificado de estudio?", "FINALIZADO"),
        ("Quiero descargar certificado académico", "FINALIZADO"),
        ("¿Cómo pido un duplicado del carnet estudiantil?", "RADICANDO_TICKET"),
        ("Se me perdió el carnet cómo lo repongo", "CANCELADO"),
        ("Trámite para carnetización física", "RADICANDO_TICKET"),
    ]
    cursor.executemany("INSERT INTO queries_log (query, status) VALUES (?, ?)", sample_data)
    conn.commit()
    conn.close()
    return str(db_file)


def test_clustering_insufficient_data(tmp_path):
    """Valida el retorno seguro cuando no hay suficientes consultas registradas."""
    empty_db = tmp_path / "empty_analytics.db"
    conn = sqlite3.connect(empty_db)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE queries_log (query TEXT, status TEXT)")
    conn.commit()
    conn.close()

    with patch("app.services.clustering_service.DB_PATH", str(empty_db)):
        result = analyze_query_clusters(min_queries_required=5)
        assert result["status"] == "insufficient_data"
        assert result["clusters"] == []
        assert "al menos 5 consultas" in result["message"]


def test_clustering_nonexistent_db(tmp_path):
    """Valida el manejo de error si el archivo de base de datos no existe."""
    fake_db = tmp_path / "nonexistent.db"
    with patch("app.services.clustering_service.DB_PATH", str(fake_db)):
        result = analyze_query_clusters(min_queries_required=2)
        assert result["status"] == "error"
        assert "no existe" in result["message"]


def test_clustering_success_with_gap_detection(temp_analytics_db):
    """Valida la agrupación K-Means, el cálculo de resolución y la detección de vacíos documentales."""
    with patch("app.services.clustering_service.DB_PATH", temp_analytics_db), \
         patch("app.services.clustering_service.summarize_cluster_topic", return_value="Trámites Universitarios"):

        result = analyze_query_clusters(n_clusters=2, min_queries_required=3)
        assert result["status"] == "success"
        assert result["total_analyzed_queries"] == 6
        assert len(result["clusters"]) == 2

        # Verificar que el cluster de baja resolución active requires_new_doc
        low_res_cluster = next((c for c in result["clusters"] if c["resolution_rate_pct"] < 50.0), None)
        if low_res_cluster:
            assert low_res_cluster["requires_new_doc"] is True

        # Verificar cluster con resolución alta
        high_res_cluster = next((c for c in result["clusters"] if c["resolution_rate_pct"] >= 50.0), None)
        if high_res_cluster:
            assert high_res_cluster["requires_new_doc"] is False


def test_summarize_cluster_topic_fallback():
    """Valida que summarize_cluster_topic retorne el título de fallback ante errores de conexión a Ollama."""
    with patch("httpx.post", side_effect=Exception("Connection refused")):
        topic = summarize_cluster_topic(["¿Cómo restablecer contraseña?"])
        assert topic == "Consultas Generales y Soporte TI"


def test_summarize_cluster_topic_empty():
    """Valida que si no hay consultas se devuelva el título por defecto."""
    topic = summarize_cluster_topic([])
    assert topic == "Consultas Generales y Soporte TI"


def test_api_analytics_clusters_endpoint(temp_analytics_db):
    """Valida la respuesta del endpoint HTTP GET /api/analytics/clusters."""
    with patch("app.services.clustering_service.DB_PATH", temp_analytics_db), \
         patch("app.services.clustering_service.summarize_cluster_topic", return_value="Gestión de Carnet"):

        client = TestClient(app)
        response = client.get("/api/analytics/clusters?n_clusters=2")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "clusters" in data
        assert len(data["clusters"]) == 2


def test_export_dpo_dataset(temp_analytics_db):
    """Valida la exportación de pares DPO (prompt, chosen, rejected) desde SQLite."""
    from app.services.clustering_service import export_dpo_dataset, export_dpo_dataset_jsonl

    with patch("app.services.clustering_service.DB_PATH", temp_analytics_db):
        dataset = export_dpo_dataset(temp_analytics_db)
        assert isinstance(dataset, list)
        
        jsonl = export_dpo_dataset_jsonl(temp_analytics_db)
        assert isinstance(jsonl, str)


def test_api_export_dpo_endpoint(temp_analytics_db):
    """Valida el endpoint HTTP GET /api/analytics/export-dpo-dataset."""
    with patch("app.services.clustering_service.DB_PATH", temp_analytics_db):
        client = TestClient(app)
        
        # Test formato JSONL por defecto
        res_jsonl = client.get("/api/analytics/export-dpo-dataset", auth=("admin", "UniMonAdmin2026*"))
        assert res_jsonl.status_code == 200
        assert res_jsonl.headers.get("content-type", "").startswith("application/x-ndjson")

        # Test formato JSON estructurado
        res_json = client.get("/api/analytics/export-dpo-dataset?format=json", auth=("admin", "UniMonAdmin2026*"))
        assert res_json.status_code == 200
        data = res_json.json()
        assert data["status"] == "success"
        assert "dataset" in data

