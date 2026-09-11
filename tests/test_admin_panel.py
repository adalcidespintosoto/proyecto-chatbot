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
from app.security import require_admin_auth


@pytest.fixture(autouse=True)
def override_admin_auth():
    """Omite la autenticación en las pruebas funcionales del panel administrativo."""
    app.dependency_overrides[require_admin_auth] = lambda: "admin"
    yield
    app.dependency_overrides.pop(require_admin_auth, None)


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
    """Verifica que index.html contenga la estructura de renderizado de texto y el trigger secreto a /admin sin exponer botones visibles a usuarios."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        html = res.text
        assert "msg-text" in html
        assert "openAdminSecret" in html
        assert "badge-online" not in html  # El botón visible 'En Línea' fue removido de cara al usuario
        assert "data.mensaje" in html or "botText" in html
        assert "Ctrl + Alt + A" in html or "ctrlKey" in html


@pytest.mark.asyncio
async def test_admin_audit_doc_and_cancel():
    """Verifica que /api/admin/audit-doc analice el archivo y que resolve-upload cancele la operación."""
    test_content = b"Procedimiento Institucional de Gestion TI UniMon. Soporte y Mantenimiento de Equipos."
    files = {
        "file": ("test_audit_doc.pdf", io.BytesIO(test_content), "application/pdf")
    }
    data = {
        "audience": "general",
        "threshold": "0.85"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Auditar documento
        audit_res = await client.post("/api/admin/audit-doc", files=files, data=data)
        assert audit_res.status_code == 200
        audit_json = audit_res.json()
        assert audit_json["status"] == "success"
        assert "staged_id" in audit_json
        assert "metrics" in audit_json
        assert "total_chunks" in audit_json["metrics"]
        assert "redundancy_ratio" in audit_json["metrics"]
        assert "overlapping_sources" in audit_json
        assert "detailed_chunks" in audit_json

        staged_id = audit_json["staged_id"]

        # 2. Cancelar la subida
        resolve_res = await client.post(
            "/api/admin/resolve-upload",
            json={"staged_id": staged_id, "action": "cancel"}
        )
        assert resolve_res.status_code == 200
        resolve_json = resolve_res.json()
        assert resolve_json["status"] == "cancelled"
        assert resolve_json["action"] == "cancel"


@pytest.mark.asyncio
async def test_admin_resolve_upload_force_and_cleanup():
    """Verifica resolución forzada (force) de documento y posterior limpieza."""
    test_content = b"Documento de Prueba Unitaria para Ingesta Forzada en ChromaDB UniMon USB."
    files = {
        "file": ("test_force_doc.pdf", io.BytesIO(test_content), "application/pdf")
    }
    data = {
        "audience": "general",
        "threshold": "0.85"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Auditar
        audit_res = await client.post("/api/admin/audit-doc", files=files, data=data)
        assert audit_res.status_code == 200
        staged_id = audit_res.json()["staged_id"]

        # 2. Resolver con 'force'
        resolve_res = await client.post(
            "/api/admin/resolve-upload",
            json={"staged_id": staged_id, "action": "force"}
        )
        assert resolve_res.status_code == 200
        resolve_json = resolve_res.json()
        assert resolve_json["status"] == "success"
        assert resolve_json["action"] == "force"

        # 3. Verificar que aparezca en el listado
        list_res = await client.get("/api/admin/docs")
        docs = [d["filename"] for d in list_res.json().get("documents", [])]
        assert "test_force_doc.pdf" in docs

        # 4. Eliminar documento
        del_res = await client.delete("/api/admin/docs/test_force_doc.pdf")
        assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_admin_resolve_upload_deduplicate_and_replace():
    """Verifica los endpoints de deduplicate y replace."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Probar deduplicate
        files1 = {"file": ("test_dedup_doc.pdf", io.BytesIO(b"Contenido deduplicado de prueba"), "application/pdf")}
        audit1 = await client.post("/api/admin/audit-doc", files=files1, data={"audience": "estudiante"})
        assert audit1.status_code == 200
        staged_id1 = audit1.json()["staged_id"]

        res_dedup = await client.post(
            "/api/admin/resolve-upload",
            json={"staged_id": staged_id1, "action": "deduplicate"}
        )
        assert res_dedup.status_code == 200
        assert res_dedup.json()["action"] == "deduplicate"

        # Limpiar
        await client.delete("/api/admin/docs/test_dedup_doc.pdf")

        # Probar replace
        files2 = {"file": ("test_replace_doc.pdf", io.BytesIO(b"Contenido reemplazado de prueba"), "application/pdf")}
        audit2 = await client.post("/api/admin/audit-doc", files=files2, data={"audience": "profesor"})
        assert audit2.status_code == 200
        staged_id2 = audit2.json()["staged_id"]

        res_replace = await client.post(
            "/api/admin/resolve-upload",
            json={"staged_id": staged_id2, "action": "replace", "target_to_replace": "test_replace_doc.pdf"}
        )
        assert res_replace.status_code == 200
        assert res_replace.json()["action"] == "replace"

        # Limpiar
        await client.delete("/api/admin/docs/test_replace_doc.pdf")


@pytest.mark.asyncio
async def test_admin_html_contains_redundancy_modal():
    """Verifica que admin.html contenga todos los elementos de la interfaz modal de redundancia y el panel inline."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/admin")
        assert res.status_code == 200
        html = res.text
        assert "redundancyModal" in html
        assert "Alta Redundancia y Ambigüedad Detectada" in html
        assert "Inspección Detallada de Fragmentos" in html
        assert "Actualizar / Reemplazar Documento Existente" in html
        assert "Guardar como Nuevo (con Deduplicación de Fragmentos)" in html
        assert "Forzar Indexación Completa (Sin Filtrado)" in html
        assert "Descartar Archivo (Cancelar)" in html
        # Verificaciones del panel inline y nuevos botones
        assert "Analizar Ambigüedad y Redundancia" in html
        assert "Subir Directo" in html
        assert "inlineAuditCard" in html
        assert "auditActionReplace" in html
        assert "auditActionDedup" in html
        assert "auditActionForce" in html


@pytest.mark.asyncio
async def test_admin_audit_ambiguity_metrics():
    """Verifica que el endpoint /api/admin/audit-doc retorne métricas completas de ambigüedad."""
    test_content = b"Procedimiento de Activacion y Restablecimiento de Credenciales de Usuario Institucional."
    files = {
        "file": ("test_ambiguity_check.pdf", io.BytesIO(test_content), "application/pdf")
    }
    data = {
        "audience": "general",
        "threshold": "0.85",
        "ambiguity_threshold": "0.65"
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        audit_res = await client.post("/api/admin/audit-doc", files=files, data=data)
        assert audit_res.status_code == 200
        audit_json = audit_res.json()
        assert audit_json["status"] == "success"
        assert "ambiguity_detected" in audit_json
        assert "redundancy_detected" in audit_json
        assert "overall_status" in audit_json
        assert "ambiguity_ratio" in audit_json["metrics"]
        assert "ambiguous_chunks" in audit_json["metrics"]
        assert "redundancy_ratio" in audit_json["metrics"]
        assert "novel_chunks" in audit_json["metrics"]

        # Limpiar staging
        staged_id = audit_json["staged_id"]
        res_cancel = await client.post(
            "/api/admin/resolve-upload",
            json={"staged_id": staged_id, "action": "cancel"}
        )
        assert res_cancel.status_code == 200



