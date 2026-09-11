"""
Pruebas unitarias para Límite de Dominio (Trámites Académicos / Reclamo de Notas)
y Elecciones Institucionales en UniMon.
"""

import pytest
import re
from unittest.mock import patch, AsyncMock

from app.services.router_logic import RouterLogic, validar_tramite_academico, EstadoTicket
from app.services.normalizer_service import normalize_and_expand_query
from app.services.rag_service import (
    STRICT_SYSTEM_PROMPT_TEMPLATE,
    ALLOWED_DOMAINS_AND_URLS,
    clean_llm_response,
    sanitize_markdown_links,
    RAGService
)


# =============================================================================
# 1. PRUEBAS DE INTERCEPTOR OUT-OF-SCOPE: VALIDAR TRÁMITE ACADÉMICO
# =============================================================================

def test_validar_tramite_academico_detects_grade_claims():
    """Detecta reclamos, correcciones y solicitudes de cambio de notas."""
    casos_reclamo = [
        "el profesor me clavó un 2.0 y quiero cambiar la nota",
        "necesito subir la nota del parcial que me fue mal",
        "quisiera corregir mi calificación definitiva",
        "vengo a hacer un reclamo de calificacion porque es injusta la nota",
        "el docente me clavo una nota injusta",
        "cómo puedo cambiar mi nota del examen final",
        "quiero que me suban la calificación del corte"
    ]
    for caso in casos_reclamo:
        resultado = validar_tramite_academico(caso)
        assert resultado is not None, f"Debe detectar trámite académico en: '{caso}'"
        assert "Aviso de Alcance Institucional" in resultado
        assert "Portal Estudiantes" in resultado
        assert "docente de la asignatura" in resultado
        assert "Dirección de tu Programa Académico" in resultado


def test_validar_tramite_academico_ignores_legitimate_it_and_docente():
    """No debe interceptar soporte técnico legítimo ni a docentes cargando notas de sus alumnos."""
    casos_legitimos = [
        "cómo configuro la red wifi de la universidad",
        "no puedo entrar al portal estudiantes con mi clave",
        "olvidé mi contraseña de teams",
        "¿dónde descargo el carnet digital?",
        "¿Cómo y hasta cuándo puedo subir las notas de mis estudiantes y reportar las fallas a clase?"
    ]
    for caso in casos_legitimos:
        resultado = validar_tramite_academico(caso, user_role="docente" if "estudiantes" in caso else "estudiante")
        assert resultado is None, f"No debe interceptar caso legítimo: '{caso}'"


@pytest.mark.asyncio
async def test_router_logic_intercepts_academic_claim():
    """Verifica que RouterLogic intercepte reclamos de notas sin crear ticket ni pedir datos."""
    sess_id = "test_reclamo_notas_sess"
    RouterLogic.reset_session(sess_id)
    session = RouterLogic.get_session(sess_id)
    session.user_role = "estudiante"

    msg = "profe me clavaron un 1.5 en el parcial y necesito cambiar esa nota urgente"
    res = await RouterLogic.procesar_mensaje(msg, session_id=sess_id)

    assert res["tipo"] == "FUERA_DE_DOMINIO"
    assert res["ticket_id"] is None
    assert "Aviso de Alcance Institucional" in res["mensaje"]
    assert "docente de la asignatura" in res["mensaje"]
    # Verificar que el estado no avanzó a pedir nombre o crear ticket
    sess = RouterLogic.get_session(sess_id)
    assert sess.estado == EstadoTicket.IDLE


# =============================================================================
# 2. PRUEBAS DEL EXPANSOR SEMÁNTICO / NORMALIZADOR
# =============================================================================

def test_normalizer_preserves_elecciones_entity():
    """Verifica que consultas de elecciones/votar preserven la URL oficial y no desvíen a certificados."""
    consultas = [
        "dónde puedo votar por el representante de estudiantes",
        "quiero votar en las elecciones",
        "cómo voto por mi candidato a consejo"
    ]
    for c in consultas:
        exp = normalize_and_expand_query(c)
        assert "elecciones" in exp.lower() or "votar" in exp.lower()
        assert "https://elecciones.unisimon.edu.co/" in exp
        assert "certificados" not in exp.lower()


def test_normalizer_preserves_grade_claim_entity():
    """Verifica que consultas de reclamo de nota preserven la directiva académica."""
    consultas = [
        "me clavaron en el parcial",
        "quiero cambiar nota",
        "corregir nota de calculo",
        "reclamo calificacion"
    ]
    for c in consultas:
        exp = normalize_and_expand_query(c)
        assert "reclamo calificacion revision docente direccion de programa" in exp.lower()


# =============================================================================
# 3. PRUEBAS DEL SYSTEM PROMPT Y WHITELIST
# =============================================================================

def test_system_prompt_has_mandatory_directives():
    """Verifica que STRICT_SYSTEM_PROMPT_TEMPLATE contenga las 4 directrices solicitadas."""
    prompt = STRICT_SYSTEM_PROMPT_TEMPLATE

    assert "GROUNDING ESTRICTO" in prompt
    assert "LÍMITE DE DOMINIO - TRÁMITES ACADÉMICOS (RECLAMO DE NOTAS)" in prompt
    assert "ELECCIONES INSTITUCIONALES" in prompt
    assert "RESPUESTAS TRANSPARENTES" in prompt
    assert "https://elecciones.unisimon.edu.co/" in prompt
    assert "VOTAR" in prompt
    assert "DOCENTE" in prompt
    assert "DIRECCIÓN DE PROGRAMA" in prompt
    assert "GLPI" in prompt


def test_elecciones_url_in_allowed_domains():
    """Verifica que https://elecciones.unisimon.edu.co esté en la lista blanca de enlaces."""
    assert "https://elecciones.unisimon.edu.co" in ALLOWED_DOMAINS_AND_URLS

    link_test = "Accede a [Elecciones Institucionales](https://elecciones.unisimon.edu.co/) para votar."
    sanitized = sanitize_markdown_links(link_test)
    assert "[Elecciones Institucionales](https://elecciones.unisimon.edu.co/)" in sanitized


# =============================================================================
# 4. PRUEBAS DE SANITIZACIÓN Y CLEAN_LLM_RESPONSE
# =============================================================================

def test_clean_llm_response_normalizes_election_urls():
    """Verifica normalización de URLs de elecciones."""
    raw = "Ingresa a http://unisimon.edu.co/elecciones para registrar tu voto."
    cleaned = clean_llm_response(raw)
    assert "https://elecciones.unisimon.edu.co/" in cleaned


def test_clean_llm_response_neutralizes_glpi_in_grade_claims():
    """Verifica que no se ofrezca ticket de TI ante solicitudes de cambio de nota."""
    raw = "Si deseas cambiar tu nota, puedes radicar un ticket en la Mesa de Ayuda TI."
    cleaned = clean_llm_response(raw)
    assert "trámite estrictamente académico" in cleaned
    assert "docente de la materia" in cleaned


# =============================================================================
# 5. PRUEBA DE FALLBACK INSTITUCIONAL
# =============================================================================

def test_rag_fallback_responses():
    """Verifica que el fallback responda adecuadamente para elecciones y reclamo de notas."""
    service = RAGService()

    # Caso elecciones
    resp_elec = service._generate_fallback_response("cómo hago para votar por el candidato")
    assert "https://elecciones.unisimon.edu.co/" in resp_elec["response"]
    assert "VOTAR" in resp_elec["response"]
    assert "Portal Estudiantes habitual ni en SIAAF" in resp_elec["response"]

    # Caso reclamo nota
    resp_nota = service._generate_fallback_response("el profesor me clavó la nota y la quiero cambiar")
    assert "Aviso de Alcance Institucional" in resp_nota["response"]
    assert "docente de la asignatura" in resp_nota["response"]
