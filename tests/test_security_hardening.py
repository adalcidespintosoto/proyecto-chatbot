"""
Pruebas de Blindaje de Seguridad y Hardening para UniMon.
Valida:
1. Autenticación HTTP Basic en /admin y endpoints administrativos protegidos.
2. Rechazo de accesos no autorizados (401).
3. Límite de tamaño de subida de archivos (413).
4. Detección de IP real detrás de Cloudflare y proxies (CF-Connecting-IP / X-Forwarded-For).
5. Rate limiting estricto por IP independientemente de rotaciones de session_id.
"""

import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
import base64

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.config import get_settings
from app.routers import chat
from app.services import telemetry_service
from app.services.telemetry_service import init_telemetry_db

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Asegura que las pruebas de seguridad usen una base de datos aislada temporal y no toquen la de producción."""
    test_db = tmp_path / "test_sec_analytics.db"
    monkeypatch.setattr(telemetry_service, "DB_PATH", test_db)
    init_telemetry_db()
    yield
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass

def get_auth_header(username: str, password: str) -> dict:
    creds = f"{username}:{password}".encode("utf-8")
    encoded = base64.b64encode(creds).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}


@pytest.mark.asyncio
async def test_admin_ui_requires_auth():
    """Verifica que el panel /admin exija autenticación HTTP Basic."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Sin credenciales -> 401
        res = await client.get("/admin")
        assert res.status_code == 401
        assert "WWW-Authenticate" in res.headers

        # 2. Con credenciales erróneas -> 401
        bad_headers = get_auth_header("hacker", "password123")
        res_bad = await client.get("/admin", headers=bad_headers)
        assert res_bad.status_code == 401

        # 3. Con credenciales correctas -> 200
        settings = get_settings()
        good_headers = get_auth_header(settings.admin_username, settings.admin_password)
        res_good = await client.get("/admin", headers=good_headers)
        assert res_good.status_code == 200


@pytest.mark.asyncio
async def test_protected_analytics_endpoints_require_auth():
    """Verifica que reset-metrics y export-dpo-dataset requieran autenticación administrativa."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Exportar DPO sin credenciales -> 401
        r_dpo = await client.get("/api/analytics/export-dpo-dataset")
        assert r_dpo.status_code == 401

        # Reset metrics sin credenciales -> 401
        r_reset = await client.post("/api/analytics/reset-metrics")
        assert r_reset.status_code == 401

        # Reset metrics con credenciales válidas -> 200
        settings = get_settings()
        good_headers = get_auth_header(settings.admin_username, settings.admin_password)
        r_reset_ok = await client.post("/api/analytics/reset-metrics", headers=good_headers)
        assert r_reset_ok.status_code == 200


@pytest.mark.asyncio
async def test_upload_file_size_limit_enforced():
    """Verifica que subir un archivo que exceda el límite configure un error 413 Payload Too Large."""
    settings = get_settings()
    good_headers = get_auth_header(settings.admin_username, settings.admin_password)

    # Simular archivo de 16MB (límite configurado en 15MB)
    oversized_content = b"%PDF-1.4 " + b"0" * (16 * 1024 * 1024)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("malicious_large.pdf", oversized_content, "application/pdf")}
        data = {"audience": "general"}
        res = await client.post("/api/admin/audit-doc", headers=good_headers, files=files, data=data)
        assert res.status_code == 413
        assert "excede el tamaño máximo" in res.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="Rate limiting is tested via integration. SlowAPI blocks TestClient in loop.")
async def test_real_ip_detection_and_rate_limiting():
    """Verifica que el rate limiter detecte CF-Connecting-IP y limite por IP real."""
    # SlowAPI default limit is 30/minute
    MAX_REQUESTS_PER_MINUTE = 30

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        test_ip = "198.51.100.42"
        headers = {"CF-Connecting-IP": test_ip, "X-Forwarded-For": test_ip}

        # Realizar peticiones hasta agotar la cuota rotando session_id
        for i in range(MAX_REQUESTS_PER_MINUTE):
            res = await client.post(
                "/api/chat",
                json={"mensaje": f"Consulta {i}", "session_id": f"fake_sess_{i}"},
                headers=headers
            )
            assert res.status_code == 200

        # La petición MAX+1 debe ser rechazada con 429 Too Many Requests
        res_blocked = await client.post(
            "/api/chat",
            json={"mensaje": "Consulta bloqueada", "session_id": "another_new_sess"},
            headers=headers
        )
        assert res_blocked.status_code == 429
        assert "Rate limit exceeded" in res_blocked.json()["error"] or "Too Many Requests" in res_blocked.text or res_blocked.status_code == 429


@pytest.mark.asyncio
async def test_security_headers_present_in_responses():
    """Verifica que las cabeceras de seguridad estén presentes en todas las respuestas."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.headers["X-Content-Type-Options"] == "nosniff"
        assert res.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert res.headers["X-Permitted-Cross-Domain-Policies"] == "none"
