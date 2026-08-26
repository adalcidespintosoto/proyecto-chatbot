"""
Pruebas Unitarias para el Módulo de Roles, Quick Replies y Acceso Total para 'Otros'.
"""

import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app.services.router_service import (
    ROLE_QUICK_REPLIES,
    ROLE_SYNONYMS,
    normalize_role
)
from app.services.router_logic import router_logic, EstadoTicket
from app.services.rag_service import rag_service
from scripts.ingest_multimodal_docs import get_metadata_from_path


def test_role_quick_replies_structure():
    """Verifica que ROLE_QUICK_REPLIES contenga los 4 perfiles requeridos con sus emojis y payloads."""
    payloads = [qr["payload"] for qr in ROLE_QUICK_REPLIES]
    labels = [qr["label"] for qr in ROLE_QUICK_REPLIES]

    assert "estudiante" in payloads
    assert "profesor" in payloads
    assert "administrativo" in payloads
    assert "otros" in payloads

    assert any("Estudiante" in l for l in labels)
    assert any("Profesor" in l for l in labels)
    assert any("Administrativo" in l for l in labels)
    assert any("Otros" in l for l in labels)


def test_normalize_role_synonyms():
    """Verifica la normalización precisa de roles y sinónimos."""
    # Estudiantes
    assert normalize_role("estudiante") == "estudiante"
    assert normalize_role("soy alumno de primer semestre") == "estudiante"
    assert normalize_role("alumna") == "estudiante"
    assert normalize_role("pregrado") == "estudiante"

    # Profesores
    assert normalize_role("profesor") == "profesor"
    assert normalize_role("docente") == "profesor"
    assert normalize_role("catedrático") == "profesor"
    assert normalize_role("soy profesora de ingenieria") == "profesor"

    # Administrativos
    assert normalize_role("administrativo") == "administrativo"
    assert normalize_role("funcionario") == "administrativo"
    assert normalize_role("soy empleada de gestion humana") == "administrativo"
    assert normalize_role("colaborador") == "administrativo"

    # Otros / Visitantes
    assert normalize_role("otros") == "otros"
    assert normalize_role("otro") == "otros"
    assert normalize_role("visitante") == "otros"
    assert normalize_role("aspirante") == "otros"
    assert normalize_role("egresado") == "otros"
    assert normalize_role("externo") == "otros"
    assert normalize_role("persona externa") == "otros"


def test_build_role_filter_unrestricted_otros():
    """Verifica que el rol 'otros' y variantes reciban acceso irrestricto (filter=None) a toda la base ChromaDB."""
    # Rol 'otros' -> Acceso Total (None)
    assert rag_service._build_role_filter("otros") is None
    assert rag_service._build_role_filter("otro") is None
    assert rag_service._build_role_filter("visitante") is None
    assert rag_service._build_role_filter("aspirante") is None
    assert rag_service._build_role_filter("egresado") is None
    assert rag_service._build_role_filter(None) is None

    # Rol 'administrativo'
    admin_filter = rag_service._build_role_filter("administrativo")
    assert admin_filter is not None
    assert "administrativo" in admin_filter["audience"]["$in"]
    assert "general" in admin_filter["audience"]["$in"]

    # Rol 'profesor'
    prof_filter = rag_service._build_role_filter("profesor")
    assert prof_filter is not None
    assert "profesor" in prof_filter["audience"]["$in"]
    assert "general" in prof_filter["audience"]["$in"]

    # Rol 'estudiante'
    est_filter = rag_service._build_role_filter("estudiante")
    assert est_filter is not None
    assert "estudiante" in est_filter["audience"]["$in"]
    assert "general" in est_filter["audience"]["$in"]


def test_metadata_mapping_administrativo_path():
    """Verifica que get_metadata_from_path asigne correctamente 'administrativo' a las carpetas de gestión."""
    path_est = Path("data/docs/1_estudiantes/manual_siaaf.pdf")
    path_prof = Path("data/docs/2_profesores/guia_calificaciones.pdf")
    path_func = Path("data/docs/3_funcionarios_gestion/kactus_permisos.pdf")
    path_gen = Path("data/docs/4_general_normativa/reglamento_ti.pdf")

    assert get_metadata_from_path(path_est)["audience"] == "estudiante"
    assert get_metadata_from_path(path_prof)["audience"] == "profesor"
    assert get_metadata_from_path(path_func)["audience"] == "administrativo"
    assert get_metadata_from_path(path_gen)["audience"] == "general"


@pytest.mark.asyncio
async def test_pidiendo_rol_delivers_quick_replies():
    """Verifica que el estado PIDIENDO_ROL entregue los botones ROLE_QUICK_REPLIES."""
    sess_id = "sess_test_qr_roles"
    router_logic.reset_session(sess_id)

    # 1. Mensaje inicial sin rol -> PIDIENDO_ROL
    res = await router_logic.procesar_mensaje("Hola, necesito ayuda", session_id=sess_id)
    assert res["tipo"] == "PIDIENDO_ROL"
    assert "quick_replies" in res
    assert len(res["quick_replies"]) == 4
    assert res["quick_replies"] == ROLE_QUICK_REPLIES

    # 2. El usuario presiona el botón '🌐 Otros / Visitante' (payload: "otros")
    with patch.object(rag_service, "answer_query", new=AsyncMock()) as mock_rag:
        res2 = await router_logic.procesar_mensaje("otros", session_id=sess_id)
        assert res2["tipo"] == "DIAGNOSTICO"
        assert router_logic.get_session(sess_id).user_role == "otros"
        assert res2.get("quick_replies") == []
        mock_rag.assert_not_called()
