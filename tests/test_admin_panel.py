"""
Pruebas Unitarias y de Integración para el Panel de Administración de UniMon (/admin).
"""

import sys
import io
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_admin_html_endpoint():
    """Verifica que /admin sirva la interfaz web administrativa."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/admin")
        assert res.status_code == 200
        assert "UniMon Admin Console" in res.text
        assert "Métricas & Observabilidad" in res.text


@pytest.mark.asyncio
async def test_admin_list_docs():
    """Verifica que /api/admin/docs retorne la lista de documentos."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/docs")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["status"] == "success"
        assert "documents" in json_data
        assert "total_documents" in json_data


@pytest.mark.asyncio
async def test_admin_system_status():
    """Verifica que /api/admin/system-status retorne el estado de infraestructura."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/system-status")
        assert res.status_code == 200
        data = res.json()
        assert "gpu_active" in data
        assert "ollama" in data
        assert "knowledge_base" in data


@pytest.mark.asyncio
async def test_admin_upload_and_delete_doc(tmp_path):
    """Verifica la subida de un documento de prueba y su posterior eliminación."""
    test_pdf_content = b"%PDF-1.4 Mock PDF content for test"
    files = {
        "file": ("test_doc_admin_upload.pdf", io.BytesIO(test_pdf_content), "application/pdf")
    }
    data = {
        "audience": "estudiante",
        "auto_index": "false"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Subir documento
        upload_res = await client.post("/api/admin/upload-doc", files=files, data=data)
        assert upload_res.status_code == 200
        upload_json = upload_res.json()
        assert upload_json["status"] == "success"
        assert upload_json["filename"] == "test_doc_admin_upload.pdf"

        # 2. Verificar que aparezca en el listado
        list_res = await client.get("/api/admin/docs")
        assert list_res.status_code == 200
        docs = [d["filename"] for d in list_res.json()["documents"]]
        assert "test_doc_admin_upload.pdf" in docs

        # 3. Eliminar documento
        del_res = await client.delete("/api/admin/docs/test_doc_admin_upload.pdf")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"


@pytest.mark.asyncio
async def test_user_index_html_rendering_and_secret_admin_trigger():
    """Verifica que index.html contenga la estructura de renderizado de texto y el trigger secreto a /admin."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        html = res.text
        assert "msg-text" in html
        assert "openAdminSecret" in html
        assert "badge-online" in html
        assert "data.mensaje" in html or "botText" in html
        assert "Ctrl+Alt+A" in html or "ctrlKey" in html
