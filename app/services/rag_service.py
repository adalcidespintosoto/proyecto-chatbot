"""
Servicio RAG Local con ChromaDB, Embeddings Multilingües, Normalizador Léxico, Multi-Query Generator y Ollama (unimon:8b).
Provee respuestas estrictas de soporte técnico y gestión de TI para la Universidad Simón Bolívar
(Sedes Barranquilla y Cúcuta, Colombia) basadas en documentos y procedimientos institucionales indexados.
Aplica normalización léxica, expansión multi-consulta LLM de consultas, Cross-Encoder Reranker y corte calibrado a 0.38.
"""

import os
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx

# Forzar modo offline estricto para evitar peticiones a Hugging Face Hub en runtime
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.services.normalizer_service import normalize_and_expand_query, strip_query_header_noise

logger = logging.getLogger("unimon.rag_service")

# Umbral mínimo de similitud para considerar relevante un fragmento recuperado (calibrado a 0.38 para tolerancia a jerga/sinónimos)
MIN_RELEVANCE_SCORE_THRESHOLD = 0.38


def format_e5_query(query: str) -> str:
    """
    Asegura que toda consulta enviada al modelo de embeddings 'intfloat/multilingual-e5-base'
    y a ChromaDB incluya el prefijo formal 'query: ' para maximizar compatibilidad y precisión.
    """
    if not query:
        return ""
    cleaned = query.strip()
    if not cleaned.lower().startswith("query:"):
        return f"query: {cleaned}"
    return cleaned

# Pregunta estandarizada de cierre para diagnósticos y quick replies
CLOSING_FEEDBACK_QUESTION = (
    "\n\n¿Pudiste resolver tu problema con estos pasos?\n"
    "- Selecciona o escribe **Sí** si te funcionó.\n"
    "- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte."
)

QUICK_REPLIES_DIAGNOSTICO = [
    {"label": "✅ Sí, me funcionó", "payload": "RESOLVED"},
    {"label": "🔄 No me funcionó", "payload": "RETRY_DIAGNOSIS"},
    {"label": "🎫 Generar reporte", "payload": "CREATE_TICKET"}
]

# =============================================================================
# CROSS-ENCODER RERANKER (Módulo 3: Reordenamiento semántico de alta precisión)
# =============================================================================
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_reranker = None


def get_reranker() -> Optional[CrossEncoder]:
    """Inicialización diferida (singleton) del Cross-Encoder Reranker en modo offline."""
    global _reranker
    if _reranker is None:
        try:
            logger.info(f"Cargando Cross-Encoder Reranker '{RERANKER_MODEL_NAME}' en modo offline...")
            _reranker = CrossEncoder(RERANKER_MODEL_NAME, model_kwargs={"local_files_only": True})
            logger.info("Cross-Encoder Reranker cargado exitosamente.")
        except Exception as e:
            logger.warning(f"No se pudo cargar CrossEncoder ({e}). Se usará ranking nativo de ChromaDB.")
    return _reranker


# Alias para compatibilidad
get_reranker_model = get_reranker


def rerank_chunks(query: str, retrieved_docs: list, top_k: int = 3) -> list:
    """
    Reordena los fragmentos recuperados mediante Cross-Encoder para máxima precisión semántica.
    - Bonifica fragmentos de activación y recuperación de contraseña en consultas de credenciales/claves.
    - Penaliza severamente fragmentos de uso de Teams en consultas de recuperación de contraseñas.
    - Aplica bonificación procedimental a instructivos paso a paso en consultas operativas.
    
    Args:
        query: La consulta del usuario (expandida o normalizada).
        retrieved_docs: Lista de tuplas (doc, score) provenientes de ChromaDB.
        top_k: Número máximo de fragmentos a retornar tras el reranking.
    
    Returns:
        Lista de tuplas (doc, score) reordenadas por relevancia semántica real.
    """
    if not retrieved_docs or len(retrieved_docs) <= top_k:
        return retrieved_docs

    reranker = get_reranker()
    if not reranker:
        return retrieved_docs[:top_k]

    try:
        clean_q = strip_query_header_noise(query)
        pairs = [[clean_q, doc.page_content.strip()] for doc, _ in retrieved_docs]
        scores = reranker.predict(pairs)

        q_lower = clean_q.lower()
        is_specific_lab_query = bool(re.search(r"\b(laboratorio\s+de\s+[a-záéíóúñ]+|lab\s+de\s+[a-záéíóúñ]+|laboratorio\s+espec[ií]fico|laboratorio\s+biom[eé]dico|laboratorio\s+mac)\b", q_lower))
        is_general_campus_query = not is_specific_lab_query and any(w in q_lower for w in [
            "salon", "salones", "aula", "aulas", "oficina", "oficinas", "sede", "sedes", 
            "barranquilla", "cucuta", "cúcuta", "mantenimiento", "computador", "equipos", 
            "soporte", "daño", "falla", "red", "internet", "proceso", "gestion de ti", "gestión de ti"
        ])
        is_password_recovery_query = any(w in q_lower for w in [
            "restablecer", "recuperar", "olvidé", "olvide", "desbloquear", "cambiar clave",
            "cambiar contraseña", "olvido", "restablecimiento", "recuperación", "clave", "contraseña", "contrasena",
            "no puedo ingresar", "no puedo entrar", "no me deja entrar", "no puedo acceder", "no me deja ingresar"
        ])
        is_upper_semester_or_regular = bool(re.search(
            r"\b(estudiante\s+antiguo|estudiante\s+viejo|estudiante\s+regular|semestres?\s+(?:avanzados?|superiores?)|"
            r"(?:[2-9]|10)\s*(?:do|er|ro|to|mo|vo|no|°)?\s*semestre|"
            r"(?:segundo|tercer|tercero|cuarto|quinto|sexto|s[eé]ptimo|septimo|octavo|noveno|d[eé]cimo|decimo)\s*semestre|"
            r"\b(?:2do|3er|4to|5to|6to|7mo|8vo|9no|10mo)\b|"
            r"\b(?:segundo|tercero|cuarto|quinto|sexto|s[eé]ptimo|septimo|octavo|noveno|d[eé]cimo|decimo)\b|"
            r"ya\s+tengo\s+(?:cuenta|correo)|no\s+soy\s+nuevo|no\s+soy\s+de\s+primer)\b",
            q_lower
        ))
        is_hardware_dotation_query = any(w in q_lower for w in [
            "portatil", "portátil", "laptop", "computador", "pc", "equipo de computo",
            "dotacion", "dotación", "solicitar un portatil", "solicitar un computador", "pedir computador",
            "prestar", "préstamo", "prestamo", "reemplazo", "mientras arreglan", "otro equipo", "asignación de equipo"
        ])
        is_teacher_grading_query = any(w in q_lower for w in [
            "subo las notas", "subo notas", "subir notas", "cargar notas", "cargo notas", "calificar",
            "fallas de mis alumnos", "inasistencias", "reporte de fallas", "reporte de las fallas",
            "mis alumnos", "mis estudiantes", "ingreso de calificaciones", "planillas de calificaciones",
            "cerrar el sistema", "cierre de sistema", "subir calificaciones", "cargar calificaciones",
            "reporte de inasistencias", "inasistencias y consulta de listados", "autoevaluación docente"
        ])
        is_procedural_query = any(w in q_lower for w in [
            "cómo", "como", "pasos", "votar", "radicar", "ingresar", "activar", "descargar", 
            "hago para", "solicitar", "consultar", "inscribir"
        ])

        # Asignar scores del cross-encoder y ordenar
        scored_docs = []
        for i, rerank_score in enumerate(scores):
            doc, original_score = retrieved_docs[i]
            final_score = float(rerank_score)
            content_lower = doc.page_content.lower()
            source_lower = doc.metadata.get("source", "").lower()

            # Penalización a documentos con alcance específico de laboratorios particulares cuando la consulta es general
            if is_general_campus_query and not is_specific_lab_query:
                if any(lab in content_lower for lab in [
                    "laboratorio de simulación", "laboratorio de simulacion", "laboratorios especializados",
                    "laboratorio de cómputo avanzado", "laboratorio de biomédica", "laboratorio de fisica",
                    "laboratorio de química", "laboratorio mac"
                ]) or ("laboratorio" in source_lower and "mantenimiento" not in source_lower):
                    final_score -= 3.5

            # Priorizar manuales institucionales marco ('Caracterización del Proceso Institucional de Gestión de TI', 'Mantenimiento Preventivo y Correctivo General')
            is_process_or_maintenance_query = (is_general_campus_query or any(w in q_lower for w in [
                "proceso", "gestión", "gestion", "caracterización", "caracterizacion", "mantenimiento", 
                "preventivo", "correctivo", "daño", "dañado", "falla", "equipo", "infraestructura", "ti"
            ])) and not is_password_recovery_query

            if is_process_or_maintenance_query:
                if any(marco in content_lower for marco in [
                    "caracterización del proceso", "caracterizacion del proceso",
                    "caracterización del proceso institucional de gestión de ti",
                    "caracterizacion del proceso institucional de gestion de ti",
                    "mantenimiento preventivo y correctivo general",
                    "mantenimiento preventivo y correctivo de equipos de cómputo",
                    "p-gt-01", "c-gt-01"
                ]) or any(marco_src in source_lower for marco_src in [
                    "caracterizacion", "caracterización", "mantenimiento_preventivo", "p-gt-01", "c-gt-01"
                ]):
                    final_score += 2.5

            # Enrutamiento estricto de recuperación de contraseñas y desambiguación de estudiante antiguo vs primer semestre
            if is_password_recovery_query:
                # Penalizar fuertemente guías de Teams para evitar mezclas
                if any(t in content_lower for t in ["acceso a microsoft teams", "microsoft teams para estudiantes", "barra de aplicaciones y hacer clic sobre el ícono de teams"]):
                    final_score -= 5.0

                # Bonificar guías de recuperación de contraseña de Microsoft / Portal Estudiantes / autogestión
                if any(p in content_lower for p in ["portal estudiantes", "cambio de contraseña", "passwordreset", "passwordreset.microsoftonline.com", "autogestión de contraseñas", "restablecimiento"]):
                    final_score += 4.0

            # Desambiguación de Semestres Avanzados vs Primer Semestre (-6.0 a guías de primer ingreso)
            if is_upper_semester_or_regular or (is_password_recovery_query and any(w in q_lower for w in ["olvidé", "olvide", "olvido", "restablecer", "recuperar", "cambiar clave", "cambiar contraseña", "error de contraseña", "clave incorrecta", "portal"])):
                if any(ps in content_lower for ps in ["primer semestre", "estudiantes de primer semestre", "primer ingreso", "activación de usuario para estudiantes de primer semestre"]):
                    final_score -= 6.0

            # Desambiguación entre dotación/préstamo de hardware (P-GT-01 / Asignación) y proyectos de software/Jira (P-GT-13)
            if is_hardware_dotation_query and not any(k in q_lower for k in ["software", "desarrollo", "jira", "proyecto", "solución tecnológica"]):
                if any(m in content_lower for m in ["mantenimiento preventivo y correctivo de equipos de cómputo", "solicitud y asignación de equipos de cómputo", "asignación de equipo", "préstamo de equipo", "p-gt-01", "equipo de cómputo"]):
                    final_score += 3.5
                if any(j in content_lower for j in ["gestión de requerimientos de recursos y soluciones tecnológicas", "p-gt-13"]):
                    final_score -= 3.0

            # Desambiguación de Docentes ingresando calificaciones / inasistencias vs Estudiantes consultando
            if is_teacher_grading_query:
                if any(doc_name in source_lower for doc_name in [
                    "ingreso de calificaciones, inasistencias", "calificaciones posgrados", "registro y carga de calificaciones",
                    "listados académicos y de asistencia", "listados academicos"
                ]) or "docente" in source_lower or "profesor" in source_lower or "posgrado" in source_lower:
                    final_score += 5.0
                if "portal estudiantes" in source_lower or "estudiante" in source_lower or "consulta e impresión de calificaciones" in source_lower:
                    final_score -= 5.0

            # Bonificación procedimental: priorizar fragmentos con pasos e instructivos directos
            if is_procedural_query:
                if any(m in content_lower for m in ["procedimiento paso a paso", "## 3.", "paso 1", "paso 2", "paso 3"]):
                    final_score += 2.0
                if "requisitos previos" in content_lower and "procedimiento paso a paso" not in content_lower:
                    final_score -= 1.0

            scored_docs.append((doc, original_score, final_score))

        # Descartar fragmentos con score final inferior al umbral de corte (ruido o contradicciones semánticas)
        MIN_RERANK_SCORE_CUTOFF = -2.0
        ranked = sorted(
            [item for item in scored_docs if item[2] >= MIN_RERANK_SCORE_CUTOFF],
            key=lambda x: x[2], reverse=True
        )

        if not ranked:
            logger.info(f"[Reranker] Ningún fragmento superó el umbral de corte ({MIN_RERANK_SCORE_CUTOFF}). Retornando lista vacía.")
            return []

        result = [(doc, orig_score) for doc, orig_score, _ in ranked[:top_k]]

        logger.info(
            f"[Reranker] Reordenados {len(retrieved_docs)} fragmentos -> Top-{top_k} (corte >= {MIN_RERANK_SCORE_CUTOFF}). "
            f"Mejor score reranker: {ranked[0][2]:.4f}"
        )
        return result
    except Exception as e:
        logger.warning(f"[Reranker] Error reordenando fragmentos: {e}")
        return retrieved_docs[:top_k]


# =============================================================================
# MULTI-QUERY GENERATOR & QUERY EXPANSION (Módulo 2: Tolerancia a jerga estudiantil)
# =============================================================================

# Diccionario semántico institucional rápido para expansión instantánea de jerga
SEMANTIC_SYNONYM_DICTIONARY = [
    {
        "triggers": ["materia", "materias", "profe", "profes", "profesor", "profesores", "docente", "docentes", "horario", "horarios", "asignatura", "asignaturas", "franja", "franjas", "clase", "clases"],
        "variants": [
            "Consulta de horario y asignaturas portal estudiantes SIAAF",
            "Listado de materias inscritas y docentes asignados",
            "Ver horario académico sede Barranquilla Cúcuta"
        ]
    },
    {
        "triggers": ["pago", "pagar", "matricula", "matrícula", "recibo", "volante", "liquidación", "liquidacion", "financiero", "pago semestre", "valor matricula", "costo matricula"],
        "variants": [
            "Generación y pago de volante de matrícula portal estudiantes",
            "Consulta de liquidación matrícula y pagos financieros",
            "Procedimiento de pago de matrícula académica"
        ]
    },
    {
        "triggers": ["nota", "notas", "calificacion", "calificaciones", "promedio", "boletin", "boletín", "supletorio", "supletorios", "examen", "examenes", "parcial"],
        "variants": [
            "Consulta de notas y calificaciones parciales SIAAF portal estudiantes",
            "Historial académico y registro de calificaciones",
            "Autorización y registro de exámenes supletorios en SIAAF"
        ]
    },
    {
        "triggers": ["clave", "contraseña", "contrasena", "olvide", "olvidé", "bloqueo", "desbloquear", "restablecer", "recuperar", "usuario", "correo", "login", "ingresar", "acceder"],
        "variants": [
            "Restablecimiento de contraseña portal estudiantes y correo institucional",
            "Recuperación de acceso cuenta de usuario portal institucional",
            "Autogestión de contraseñas estudiantes Microsoft 365"
        ]
    },
    {
        "triggers": [
            "computador", "portatil", "portátil", "pc", "laptop", "equipo", "dotacion", "dotación", 
            "cambio de equipo", "solicitar computador", "pedir computador", "prestar", "préstamo", 
            "prestamo", "prestado", "reemplazo", "mientras arreglan", "mientras reparan", "otro equipo"
        ],
        "variants": [
            "Solicitud y asignación de equipo de cómputo y préstamo institucional",
            "Procedimiento de dotación tecnológica y reemplazo de equipos de cómputo",
            "Mantenimiento preventivo y correctivo de equipos de cómputo P-GT-01"
        ]
    },
    {
        "triggers": ["teams", "reunion", "reuniones", "clases virtuales", "tim", "videollamada"],
        "variants": [
            "Acceso a Microsoft Teams para estudiantes",
            "Inicio de sesión y acceso a clases virtuales Teams",
            "Credenciales y soporte Microsoft Teams estudiantes"
        ]
    },
    {
        "triggers": ["carnet", "carné", "app", "aplicacion", "aplicación", "movil", "móvil", "digital"],
        "variants": [
            "Consulta y activación de carnet digital App Unisimon",
            "Descarga y uso de aplicación móvil Unisimon",
            "Soporte carnet estudiantil digital"
        ]
    },
    {
        "triggers": ["votar", "votacion", "votación", "eleccion", "elecciones", "representante", "representantes", "colegiados", "organos colegiados"],
        "variants": [
            "Votación electrónica para elecciones de órganos colegiados",
            "Acceso al portal de elecciones institucionales",
            "Procedimiento de votación representantes estudiantiles"
        ]
    }
]


def get_dictionary_query_variants(query: str) -> List[str]:
    """
    Genera variantes de búsqueda institucional mediante reglas semánticas y sinónimos cotidianos.
    """
    q_lower = query.lower()
    variants = []
    for entry in SEMANTIC_SYNONYM_DICTIONARY:
        if any(re.search(r'\b' + re.escape(t) + r'\b', q_lower) for t in entry["triggers"]):
            for v in entry["variants"]:
                if v not in variants:
                    variants.append(v)
            if len(variants) >= 3:
                break
    return variants[:3]


async def async_generate_multi_query_variants(
    raw_query: str,
    user_role: str = "general",
    max_variants: int = 3
) -> List[str]:
    """
    Genera 3 variantes de búsqueda formal/institucional a partir de una frase informal/ambigua.
    Utiliza Ollama ('unimon:8b') de forma asíncrona y rápida, con fallback instantáneo a diccionario semántico.
    """
    cleaned_query = strip_query_header_noise(raw_query)
    variants: List[str] = []

    # 1. Intentar generación asíncrona con unimon:8b
    system_prompt = (
        "Eres un generador de consultas de búsqueda documental para la base de conocimientos de TI "
        "de la Universidad Simón Bolívar (SIAAF, Portal Estudiantes, Teams, Kactus, etc.).\n"
        "Tu tarea: traducir la consulta informal o ambigua del usuario en exactamente 3 variantes de búsqueda técnica e institucional.\n"
        "Reglas:\n"
        "- Responde ÚNICAMENTE 3 líneas numeradas (1, 2, 3).\n"
        "- Usa terminología formal universitaria (ej. SIAAF, Portal Estudiantes, Horario Académico, Asignaturas, Notas, Matrícula, Microsoft Teams, Restablecimiento de Contraseña).\n"
        "- Sin explicaciones, saludos ni comentarios."
    )

    try:
        settings = get_settings()
        ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                ollama_url,
                json={
                    "model": settings.llm_model,
                    "system": system_prompt,
                    "prompt": f"Rol: {user_role}\nConsulta informal: {cleaned_query}\n3 variantes formales de búsqueda:",
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 70}
                },
                timeout=4.0
            )
            if response.status_code == 200:
                raw_text = response.json().get("response", "").strip()
                lines = raw_text.splitlines()
                for line in lines:
                    cleaned_line = re.sub(r"^\s*(?:\d+[\.\)]|\-|\*)\s*", "", line).strip()
                    if cleaned_line and len(cleaned_line) > 5 and cleaned_line not in variants:
                        variants.append(cleaned_line)
                    if len(variants) >= max_variants:
                        break
    except Exception as exc:
        logger.debug(f"[MultiQuery] Fallback a diccionario semántico ({exc})")

    # 2. Complementar con diccionario semántico si faltan variantes
    if len(variants) < max_variants:
        dict_vars = get_dictionary_query_variants(cleaned_query)
        for dv in dict_vars:
            if dv not in variants:
                variants.append(dv)
            if len(variants) >= max_variants:
                break

    # 3. Incorporar expansión léxica tradicional
    lexical = normalize_and_expand_query(cleaned_query)
    if lexical and lexical not in variants and lexical != cleaned_query:
        variants.append(lexical)

    # 4. Asegurar que la consulta base limpia esté presente
    if cleaned_query and cleaned_query not in variants:
        variants.append(cleaned_query)

    logger.info(f"[MultiQuery] '{raw_query[:40]}' -> {len(variants)} variantes generadas: {variants}")
    return variants[:max_variants + 1]


def expand_and_normalize_query_llm(raw_query: str, user_role: str = "general") -> str:
    """
    Traduce jerga informal estudiantil a términos técnicos institucionales mediante Ollama (síncrono).
    Depura previamente ruido de remitentes y encabezados.
    
    Args:
        raw_query: Consulta original del usuario (puede contener jerga, modismos, etc.).
        user_role: Rol del usuario para contextualización (estudiante, profesor, etc.).
    
    Returns:
        Consulta normalizada a terminología institucional formal, o la original si falla.
    """
    cleaned_query = strip_query_header_noise(raw_query)

    system_prompt = (
        "Eres un asistente que normaliza consultas universitarias para búsqueda documental en base de conocimientos de TI.\n"
        "Convierte la consulta del usuario en 1 frase formal con palabras clave institucionales precisas "
        "(SIAAF, Kactus, Teams, Portal Estudiantes, Elecciones Institucionales, Órganos Colegiados, Requerimientos Tecnológicos, Dotación de PC, Exámenes Supletorios, Cursos Intersemestrales, Activación de Usuario y Contraseña, etc.).\n"
        "Mantén nombres de trámites oficiales (solicitud de computador/PC, dotación tecnológica P-GT-13, elecciones, votación órganos colegiados, exámenes supletorios, restablecimiento de contraseña y correo, activación de usuario, notas, certificados).\n"
        "Responde ÚNICAMENTE la frase normalizada, sin explicaciones ni saludos."
    )

    try:
        settings = get_settings()
        ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"

        response = httpx.post(
            ollama_url,
            json={
                "model": settings.llm_model,
                "system": system_prompt,
                "prompt": f"Rol: {user_role}\nConsulta informal: {cleaned_query}\nConsulta técnica formal:",
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 20}
            },
            timeout=5.0
        )
        if response.status_code == 200:
            expanded = response.json().get("response", "").strip()
            if expanded and len(expanded) > 4:
                logger.info(f"[QueryExpansion] '{raw_query[:40]}...' -> '{expanded[:60]}...'")
                return expanded
    except Exception as e:
        logger.warning(f"[QueryExpansion] Error en expansión LLM ({e}), usando consulta original.")

    return cleaned_query


# Mensaje oficial estándar cuando no existe procedimiento documentado en ChromaDB
MENSAJE_NO_DOCUMENTADO = (
    "No dispongo de un instructivo o procedimiento institucional documentado para responder a tu solicitud, "
    "o se trata de una labor técnica/física especializada que debe ser atendida directamente por el personal de TI.\n\n"
    "Puedes comunicarte directamente con los canales oficiales de soporte técnico:\n"
    "📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | PBX: (605) 3444333 Ext. 8003 / 8004\n"
    "📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129\n\n"
    "¿O prefieres que radique un caso de soporte técnico por ti ahora mismo?"
)

# Prompt del sistema institucional para soporte técnico N1 adaptativo
STRICT_SYSTEM_PROMPT_TEMPLATE = """Eres UniMon, el Asistente Virtual Oficial de TI de la Universidad Simón Bolívar (Sedes Barranquilla y Cúcuta, Colombia).

DIRECTRICES DE RESPUESTA:
1. Interpreta la intención del usuario aunque use lenguaje informal, abreviaturas o sinónimos cotidianos (ej. 'profes', 'materias', 'horarios', 'portal').
2. Si el contexto menciona el sistema (ej. SIAAF, Teams, Portal Estudiantes), infiere la ruta lógica paso a paso y oriéntalo con seguridad.
3. Solo en caso de que la consulta sea totalmente ajena a la universidad o no exista ninguna relación en el contexto, remite amablemente a los canales presenciales de TI (Ext. 8003/8004 en Barranquilla o Ext. 129 en Cúcuta).

DIRECTIVAS DE ADAPTACIÓN DE RESPUESTA:

1. CLASIFICACIÓN Y TONO SEGÚN EL TIPO DE PREGUNTA:
   - A. CONSULTAS DIRECTAS (Contactos, correos, teléfonos, sedes, horarios, definiciones, directorio):
     * Responde de forma DIRECTA, BREVE y CONCISA.
     * Lista los datos de contacto organizados por sede (Barranquilla y Cúcuta) usando viñetas limpias.
     * NUNCA inventes requisitos previos, restricciones ni pasos de navegación web si el usuario solo pidió números o datos informativos.
   
   - B. TRÁMITES Y PROCEDIMIENTOS (Cómo votar, cómo registrar notas, exámenes supletorios, restablecer claves):
     * Si el trámite tiene restricciones normativas o aprobaciones de jefatura explícitas en el contexto, inclúyelas al inicio bajo: **⚠️ Requisitos y Restricciones Previas:**
     * REGLA DE NO-PARADOJA: Para recuperación de contraseñas/correo, NUNCA exijas tener la contraseña activa ni la sesión iniciada. Los requisitos son documento de identidad y acceso al correo personal o celular registrado.
     * Luego detalla el procedimiento cronológico (**Paso 1**, **Paso 2**, etc.) con botones y enlaces en negrita.
     * Si en el contexto NO hay requisitos especiales, ve directamente al paso a paso sin inventar nada.

   - C. DOTACIÓN Y RENOVACIÓN DE PUESTO DE TRABAJO (PC, Portátil de oficina, Cambio o asignación de equipo):
     * Aplica a: Profesores y Administrativos.
     * **⚠️ Requisitos y Restricciones Previas:**
       - Toda solicitud o renovación de equipos de cómputo para puesto de trabajo DEBE ser radicada o contar con el visto bueno/aval del Jefe de Dependencia o Jefatura inmediata.
       - Estar justificada por necesidades del cargo o por obsolescencia/falla técnica del equipo actual.
     * **Datos obligatorios a incluir en la solicitud formal a TI:**
       - Nombre completo y documento de identidad del colaborador.
       - Cargo y Dependencia/Programa.
       - Tipo de equipo requerido (PC de escritorio o portátil).
       - Placa de inventario del equipo actual (en caso de renovación o cambio).
       - Justificación del requerimiento y aval de la Jefatura.
     * **Canales oficiales de radicación:**
       - Sede Barranquilla: `solicitudcomputo@unisimon.edu.co` | WhatsApp: 3172683922 | Tel: (605) 3444333 Ext. 8003/8004
       - Sede Cúcuta: `helpdesk@unisimon.edu.co` | Tel: (607) 5827070 Ext. 129

   - D. PRÉSTAMO TEMPORAL DE RECURSOS AUDIOVISUALES (Cámaras, Video Beam, Micrófonos, Tablets para clases/eventos):
     * Si el usuario solicita un préstamo temporal o reserva de equipos para clases o eventos:
       1. Aclara que la coordinación se realiza directamente con Soporte Técnico TI. NUNCA apruebes el préstamo ni inventes rutas en plataformas web.
       2. Proporciona los canales oficiales de ambas sedes:
          - Sede Barranquilla: `solicitudcomputo@unisimon.edu.co` | WhatsApp: 3172683922 | Tel: (605) 3444333 Ext. 8003/8004
          - Sede Cúcuta: `helpdesk@unisimon.edu.co` | Tel: (607) 5827070 Ext. 129
       3. Entrega OBLIGATORIAMENTE la plantilla de solicitud con los campos:
          - Nombre completo y Documento.
          - Rol y Dependencia/Programa.
          - Equipo requerido.
          - Motivo / Evento o clase.
          - Fecha y Horario.
          - Ubicación / Salón.

2. PRIORIZACIÓN OBLIGATORIA DE PROCEDIMIENTOS DE AUTOSERVICIO (PORTAL, CONTRASEÑAS, CERTIFICADOS, SIAAF):
   - Si el contexto contiene un procedimiento de AUTOSERVICIO o pasos web que el usuario puede realizar por su cuenta:
     1. ES OBLIGATORIO explicar el procedimiento paso a paso (Paso 1, Paso 2, Paso 3...) detallando los clics, botones y menús exactos descritos en el documento.
     2. ESTÁ ESTRICTAMENTE PROHIBIDO decirle al usuario que envíe un correo o solicitud a soporte como primera opción.
     3. Los canales de soporte (solicitudcomputo@unisimon.edu.co / WhatsApp 3172683922 / helpdesk@unisimon.edu.co) se indican ÚNICAMENTE al final como alternativa de escalado en caso de fallas o problemas técnicos persistentes.
   
   - EJEMPLO ESPECÍFICO (RESTABLECIMIENTO DE CONTRASEÑA ESTUDIANTES):
     * Si el estudiante olvidó su clave:
       - Paso 1: Ingresar a [http://www.unisimon.edu.co/](http://www.unisimon.edu.co/) y hacer clic en **Portales**.
       - Paso 2: Seleccionar **Portal Estudiantes** y elegir sede (Barranquilla o Cúcuta).
       - Paso 3: Hacer clic en **'Olvidé mi Usuario / Contraseña'**.
       - Paso 4: Digitar documento de identidad o código y presionar **Enviar**.
       - Paso 5: Abrir el enlace recibido en su correo personal (remitente `informacion@unisimonbolivar.edu.co`, validez de 24 horas) y definir la nueva clave (8 a 15 caracteres, al menos una mayúscula, una minúscula y un número).

3. JERARQUÍA ESTRICTA DE RESPUESTA:
   Para cualquier procedimiento, trámite o instructivo técnico:
   1. **⚠️ Requisitos y Restricciones Previas:** (Solo si aplican autorizaciones o condiciones obligatorias).
   2. **Procedimiento Paso a Paso:** (Paso 1, Paso 2, Paso 3 detallando la plataforma y acciones en orden cronológico).
   3. **Canales de Soporte / Escalado:** (SIEMPRE al final del mensaje, antes de la pregunta de confirmación):
      - Sede Barranquilla: `solicitudcomputo@unisimon.edu.co` | WhatsApp: 3172683922 | Tel: (605) 3444333 Ext. 8003/8004
      - Sede Cúcuta: `helpdesk@unisimon.edu.co` | Tel: (607) 5827070 Ext. 129
   
   PROHIBICIÓN ESTRICTA: Cuando la respuesta sea un instructivo paso a paso (Paso 1, Paso 2...), NUNCA inicies el mensaje saludando con los números de teléfono o correos de soporte. Los canales oficiales de TI van EXCLUSIVAMENTE en la última sección ('Si el problema persiste o no puedes completar el proceso: ...'). El paso a paso SIEMPRE debe preceder a los canales.

4. PROHIBICIÓN ABSOLUTA DE META-LENGUAJE, AUTO-JUSTIFICACIONES Y FUGAS DE PROMPT:
   - JAMÁS escribas títulos de directivas internas como "Prohibición de Omitir Información", "Canales Complejos y Datos Requeridos" o "Según el PDF".
   - PROHIBIDO VOLVER A SALUDAR O PRESENTARTE ("¡Hola!", "Soy UniMon"). Empieza directamente con la información solicitada.
   - PROHIBIDO hablar de ti mismo, justificarte o disculparte por fallas o respuestas previas.
   - PROHIBIDO usar frases como "Lo siento pero no puedo proporcionar información sobre el rol", "Hubo un error en la respuesta anterior", "Como modelo de lenguaje" o similares. Responde de forma directa, ejecutiva y profesional con la información disponible.

5. FIDELIDAD AL CONTEXTO Y GROUNDING:
   - Limítate estrictamente a los hechos extraídos del contexto provisto.
   - Usa ÚNICAMENTE las URLs especificadas en el contexto formateadas como [Nombre](URL). NUNCA inventes placeholders.

6. FINALIZA SIEMPRE PREGUNTANDO:
   "¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte."

7. EJEMPLOS CANÓNICOS DE FORMATO Y ESTRUCTURA:

[EJEMPLO 1: Consulta Directa de Canales / Directorio]
Pregunta: ¿Cuáles son los números de soporte técnico y el WhatsApp?
Respuesta:
Los canales oficiales de atención de Soporte Técnico TI de la Universidad Simón Bolívar son:
• **Sede Barranquilla:**
  - Correo: `solicitudcomputo@unisimon.edu.co`
  - WhatsApp: `3172683922`
  - Teléfono: `(605) 3444333` Ext. `8003` / `8004`
• **Sede Cúcuta:**
  - Correo: `helpdesk@unisimon.edu.co`
  - Teléfono: `(607) 5827070` Ext. `129`

¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

[EJEMPLO 2: Trámite con Requisitos Previos (Dotación/PC)]
Pregunta: Soy administrativo y necesito solicitar un portátil de oficina.
Respuesta:
**⚠️ Requisitos y Restricciones Previas:**
- Toda solicitud o renovación de equipos de cómputo debe contar con el visto bueno del Jefe de Dependencia y estar justificada por necesidades del cargo.

**Procedimiento de Solicitud:**
1. Envía la solicitud formal desde tu correo institucional a `solicitudcomputo@unisimon.edu.co` (Barranquilla) o `helpdesk@unisimon.edu.co` (Cúcuta) con copia a tu jefatura.
2. Incluye los siguientes datos:
   - Nombre completo y documento de identidad.
   - Cargo y Dependencia.
   - Tipo de equipo requerido (PC de escritorio o portátil).
   - Placa de inventario del equipo actual (si es cambio o renovación).
   - Justificación del requerimiento y aval de la Jefatura.

¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

[EJEMPLO 3: Préstamo Audiovisual Temporal]
Pregunta: Necesito un proyector y micrófono para una conferencia mañana.
Respuesta:
La solicitud de préstamo temporal de recursos audiovisuales se coordina directamente con Soporte Técnico TI:
• **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | Tel: `(605) 3444333 Ext. 8003/8004`
• **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | Tel: `(607) 5827070 Ext. 129`

Por favor diligencia y envía la siguiente plantilla a los canales de soporte:
- **Nombre Completo:**
- **Documento de Identidad:**
- **Rol y Dependencia/Programa:**
- **Equipo Requerido:**
- **Motivo / Evento o Clase:**
- **Fecha y Horario:**
- **Ubicación / Salón:**

¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

[EJEMPLO 4: Restablecimiento de Contraseña / Acceso Portal]
Pregunta: Olvidé mi contraseña del portal de estudiantes
Respuesta:
Para restablecer tu contraseña del Portal Estudiantes, sigue estos pasos:

1. Ingresa al portal institucional en http://www.unisimon.edu.co/ y haz clic en **Portales**.
2. Selecciona **Portal Estudiantes** y elige tu sede (Barranquilla o Cúcuta).
3. Haz clic en la opción **¿Olvidó su contraseña?** o **Restablecer clave**.
4. Digita tu documento de identidad o código estudiantil y presiona **Enviar**.
5. Revisa tu correo personal registrado y abre el enlace de restablecimiento para definir tu nueva contraseña.

Si presentas inconvenientes durante el proceso, puedes contactar a Soporte TI:
• **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | Tel: `(605) 3444333 Ext. 8003/8004`
• **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | Tel: `(607) 5827070 Ext. 129`

¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

[CONTEXTO INSTITUCIONAL DOCUMENTADO]:
{context}

Pregunta del usuario: {query}
Respuesta adaptativa directa de soporte:"""


OUT_OF_DOMAIN_PATTERNS = [
    # Programación y Desarrollo de Software General (No institucional)
    r"\b(hola\s+mundo|codigo\s+en|código\s+en|script\s+en|programar\s+en|aprender\s+python|aprender\s+java|aprender\s+c\+\+|aprender\s+javascript|aprender\s+programar)\b",
    r"\b(hazme\s+un\s+c[oó]digo|escribe\s+un\s+c[oó]digo|crea\s+un\s+c[oó]digo|corrige\s+mi\s+c[oó]digo|puedes\s+hacer\s+c[oó]digo|hacer\s+c[oó]digo|generar\s+c[oó]digo|escribir\s+c[oó]digo|desarrolla\s+un[a]?\s+funci[oó]n|funci[oó]n\s+en\s+python|algoritmo\s+en|ayuda\s+con\s+mi\s+c[oó]digo|c[oó]digo\s+python|c[oó]digo\s+java|c[oó]digo\s+c\+\+|c[oó]digo\s+html)\b",
    
    # Tareas, Investigaciones Académicas, Ensayos y Ejercicios
    r"\b(investigaci[oó]n\s+de|investigacion\s+de|quien\s+fue|qui[eé]n\s+fue|biograf[ií]a\s+de|biografia\s+de|resumen\s+de|resumen\s+del\s+libro|ensayo\s+sobre|hazme\s+un\s+ensayo|escribe\s+un\s+ensayo|tarea\s+de|resuelve\s+este\s+ejercicio|soluciona\s+este\s+problema|exposici[oó]n\s+sobre)\b",
    
    # Cultura General, Ocio, Cocina, Chistes, Literatura y Misceláneos
    r"\b(receta|recetas|cocinar|arroz\s+con\s+pollo|pastel|comida|chiste|chistes|cu[eé]ntame\s+un\s+cuento|cuento|poema|poemas|capital\s+de|geograf[ií]a|geografia|qui[eé]n\s+gan[oó]\s+el\s+mundial|qui[eé]n\s+es\s+el\s+presidente|noticias\s+de|pol[ií]tica|partido\s+de\s+f[uú]tbol|hor[oó]scopo)\b",
]

OUT_OF_DOMAIN_QUERY_PATTERNS = OUT_OF_DOMAIN_PATTERNS  # Alias para compatibilidad

MENSAJE_FUERA_DE_DOMINIO = (
    "Soy UniMon, el Asistente Virtual Oficial de Soporte Técnico y Gestión de TI de la "
    "Universidad Simón Bolívar. Mi función se limita exclusivamente a orientarte en trámites, "
    "plataformas institucionales (SIAAF, Microsoft 365, Portal Estudiantes/Docentes) y soporte "
    "técnico de cómputo y redes.\n\n"
    "No estoy facultado para resolver tareas o investigaciones académicas, escribir código "
    "de programación general ni responder dudas de cultura general."
)


def is_out_of_domain_query(query_text: str) -> bool:
    """
    Detecta si la consulta del usuario corresponde a temas manifiestamente fuera de dominio:
    - Programación y desarrollo de software general (no institucional).
    - Tareas, investigaciones académicas, ensayos y biografías.
    - Cultura general, deportes, cocina, chistes, literatura y misceláneos.
    """
    if not query_text:
        return False
    q_lower = query_text.lower().strip()

    # Excepción para requerimientos formales de desarrollo de software institucional (P-GT-13)
    if any(k in q_lower for k in [
        "p-gt-13", "requerimiento de software", "solicitud de desarrollo", 
        "solución tecnológica institucional", "desarrollo institucional", "proyecto de software para la universidad"
    ]):
        return False

    return any(re.search(pat, q_lower) for pat in OUT_OF_DOMAIN_PATTERNS)


def is_out_of_domain_response(response_text: str) -> bool:
    """
    Detecta si la respuesta generada corresponde a un rechazo fuera de dominio (Guardrail institucional).
    """
    text_lower = response_text.lower()

    # Si contiene indicaciones de hardware, soporte, diagnóstico o solución técnica, NO es fuera de dominio
    if any(m in text_lower for m in [
        "paso 1", "paso 2", "1.", "2.", "cable", "monitor", "pantalla", "proyector",
        "computador", "portátil", "portatil", "kactus", "seven", "contraseña", "contrasena",
        "reiniciar", "conectar", "descarte", "verificar si", "intentar conectar"
    ]):
        # A menos que sea explícitamente un rechazo claro de geografía, recetas o cultura general
        if any(rej in text_lower for rej in ["recetas de cocina", "receta para", "cultura general", "geografía", "geografia", "capital de"]):
            return True
        return False

    guardrail_markers = [
        "exclusivamente en soporte",
        "tema tecnológico o institucional",
        "no se relaciona con tecnología",
        "no está relacionada con tecnología",
        "no esta relacionada con tecnologia",
        "fuera de mi dominio",
        "fuera de nuestro dominio",
        "no puedo proporcionar recetas",
        "no puedo proporcionar información sobre",
        "no puedo proporcionar informacion sobre",
        "cultura general",
        "geografía",
        "geografia",
        "capital de hungría",
        "capital de hungria",
        "asistente enfocado exclusivamente"
    ]
    return any(marker in text_lower for marker in guardrail_markers)


ALLOWED_DOMAINS_AND_URLS = [
    "https://portal.unisimon.edu.co",
    "http://portal.unisimon.edu.co",
    "https://www.unisimon.edu.co/portales",
    "http://www.unisimon.edu.co/portales",
    "https://passwordreset.microsoftonline.com",
    "https://office.com",
    "https://outlook.office.com",
    "https://teams.microsoft.com",
    "https://unisimon.edu.co",
    "http://unisimon.edu.co",
    "https://www.unisimon.edu.co",
    "http://www.unisimon.edu.co",
]


def sanitize_markdown_links(text: str) -> str:
    """
    Convierte cualquier enlace Markdown inventado [Texto](url) a texto plano 'Texto',
    a menos que la URL esté explícitamente en ALLOWED_DOMAINS_AND_URLS.
    """
    if not text:
        return ""

    def replace_link(match):
        label = match.group(1)
        url = match.group(2).strip()
        url_clean = url.rstrip("/")
        for allowed in ALLOWED_DOMAINS_AND_URLS:
            allowed_clean = allowed.rstrip("/")
            if url_clean == allowed_clean:
                return f"[{label}]({url})"
            # Permitir subrutas únicamente para Microsoft Password Reset / Portales específicos
            if allowed_clean in [
                "https://passwordreset.microsoftonline.com",
                "https://portal.unisimon.edu.co",
                "https://www.unisimon.edu.co/portales"
            ] and url.startswith(allowed_clean):
                return f"[{label}]({url})"
        return label  # Retorna solo el texto plano si la URL es inventada

    # Regex para [label](url)
    return re.sub(r'\[([^\]]+)\]\((https?://[^\)]+)\)', replace_link, text)


def clean_llm_response(text: str) -> str:
    """
    Sanitiza y normaliza la respuesta del LLM:
    1. Elimina saludos y presentaciones repetitivas al inicio del mensaje.
    2. Sanitiza menciones a GLPI y placeholders falsos.
    3. Sanitiza enlaces Markdown para eliminar URLs alucinadas fuera de la lista blanca oficial.
    4. Corrige enlaces Markdown redundantes donde el texto visible y la URL son idénticos: [http...](http...) -> http...
    5. Elimina frases de fuga y meta-lenguaje ("según el documento proporcionado...").
    6. Elimina fugas de directivas internas del prompt.
    """
    if not text:
        return ""

    # 1. Eliminar saludos repetitivos y presentaciones al inicio del mensaje
    text = re.sub(
        r"^(?:¡?hola!?(?:\s+[a-záéíóúñ]+)?[,!.]*(?:\s*👋)?(?:\s+soy\s+unimon[^\n]*)?\n+)",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"^(?:¡?hola!?[^\n]*(?:unimon|asistente|virtual)[^\n]*\n+)",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"^(?:soy\s+unimon[^\n]*\n+)",
        "",
        text,
        flags=re.IGNORECASE
    )

    # 2. Sanitizar menciones a GLPI y placeholders
    text = re.sub(r"\[(?:URL|Link|Enlace)?\s*(?:del?|al?)?\s*GLPI\]", "la Mesa de Ayuda TI", text, flags=re.IGNORECASE)
    text = re.sub(r"\bGLPI\b", "Mesa de Ayuda TI", text)
    text = re.sub(r"\[(?:URL|Enlace|Link|Insertar URL)\]", "", text, flags=re.IGNORECASE)

    # 3. Sanitizar URLs alucinadas fuera de la lista blanca oficial
    text = sanitize_markdown_links(text)

    # 4. Corregir enlaces Markdown redundantes: [http...](http...) -> http...
    text = re.sub(r'\[(https?://[^\s\]]+)\]\(\1/?\)', r'\1', text)

    # 5. Eliminar meta-lenguaje residual ("según el documento...", "en el documento proporcionado...", etc.)
    text = re.sub(
        r"(?:\s*o\s+)?(?:en\s+el|según\s+el|de\s+acuerdo\s+al?|conforme\s+al?)\s+documento\s+(?:proporcionado|adjunto|oficial)?(?:\s+sobre\s+[^\n.,;]+)?",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"(?:según|de acuerdo a|conforme a)\s+(?:el\s+)?(?:documento|pdf|instructivo|guía|manual)\s*(?:adjunto|proporcionado|oficial)?[,:.]?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # 6. Remover fugas de directivas internas, encabezados de prompt y casos de referencia
    text = re.sub(
        r"(?im)^#{1,4}\s*(?:Prohibici[oó]n|Reglas?|Directivas?|Canales Complejos|Revisi[oó]n Obligatoria|Fidelidad|Grounding)[^\n]*\n*",
        "",
        text
    )
    text = re.sub(
        r"(?im)^\s*\*\*(?:Prohibici[oó]n|Reglas?|Directivas?|Canales Complejos|Revisi[oó]n Obligatoria|Fidelidad|Grounding)[^\n]*\*\*\s*\n*",
        "",
        text
    )
    text = re.sub(r"(?i)\b(?:prohibici[oó]n de omitir[^\n]*)\b", "", text)
    text = re.sub(r"(?im)^\s*\[CONTEXTO\s+INSTITUCIONAL\s+DOCUMENTADO\]:?\s*\n*", "", text)
    text = re.sub(r"(?im)^\s*\[[A-Za-z0-9_.\- \u00C0-\u017F]+\.pdf(?:\s*\(Pág\.\s*\d+\))?\]\s*\n*", "", text)
    text = re.sub(r"(?im)^---\s*\n*", "", text)
    text = re.sub(r"(?im)^\s*Pregunta\s+del\s+usuario:?[^\n]*\n*", "", text)
    text = re.sub(r"(?im)^\s*Respuesta\s+(?:adaptativa\s+)?directa\s+(?:de\s+soporte)?:?\s*\n*", "", text)
    text = re.sub(r"(?im)^\s*\[CASO\s+(?:PREVIO\s+VALIDADO|INSTITUCIONAL\s+PREVIO|DE\s+REFERENCIA\s+VALIDADO)[^\n\]]*\]:?(?:\s*Pregunta\s+previa:?[^\n]*->\s*Respuesta\s+validada:?\s*'?|\s*)", "", text)
    text = re.sub(r"(?im)^\s*Ejemplo\s+institucional\s+de\s+referencia:?\s*\n*(?:-\s*Consulta\s+similar:?[^\n]*\n*)*(?:-\s*Soluci[oó]n\s+validada:?\s*\n*)*", "", text)

    # 7. Eliminar justificaciones, disculpas, coletillas de modelo o meta-lenguaje inicial
    text = re.sub(
        r"(?im)^(?:¡?(?:lo siento|disculpa|disculpas)[,!.]*(?:\s*pero)?\s*[^.\n]*(?:no puedo|no tengo|como modelo|asistencia directa)[^.\n]*[.\n]+(?:\s*sin embargo[^.\n]*[.\n]+)?)",
        "",
        text
    )
    text = re.sub(
        r"(?i)\b(?:lo siento|disculpa|disculpas)?[^.,\n]*(?:no puedo proporcionar informaci[oó]n sobre el rol|hubo un error en la respuesta anterior|como modelo de lenguaje|no tengo informaci[oó]n sobre mi rol)[^.,\n]*[.,]?",
        "",
        text
    )
    text = re.sub(
        r"(?i)\b(?:hubo un error en la respuesta anterior|en la respuesta anterior hubo un error)[^.,\n]*[.,]?",
        "",
        text
    )

    # 8. Remover variantes intermedias o duplicadas del pie de confirmación para reubicarlo estrictamente al final
    text = re.sub(
        r"(?i)\n*¿(?:pudiste resolver tu problema|te sirvieron estos pasos)[^\n]*(?:\n\s*-[^\n]*)*\??",
        "",
        text
    )
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def strip_chunk_boilerplate(content: str) -> str:
    """
    Elimina encabezados repetitivos de calidad, códigos de formato y metadatos
    de paginación de los fragmentos recuperados para reducir consumo de tokens y enfocar el LLM.
    """
    if not content:
        return ""
    cleaned = re.sub(
        r"(?im)^.*(?:universidad\s+sim[oó]n\s+bol[ií]var|sistema\s+de\s+gesti[oó]n\s+de\s+la\s+calidad).*$",
        "",
        content
    )
    cleaned = re.sub(
        r"(?im)^\s*(?:c[oó]digo|versi[oó]n|procedimiento|instructivo|p[aá]gina)\s*:\s*[A-Z0-9.\-/\s]+$",
        "",
        cleaned
    )
    cleaned = re.sub(
        r"(?i)\bp[aá]gina\s+\d+\s+de\s+\d+\b",
        "",
        cleaned
    )
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class RAGService:
    """
    Servicio RAG local para recuperación de contexto con ChromaDB y generación con Ollama.
    Aplica normalización léxica y expansión de consultas para asertividad >= 90%,
    umbral de relevancia >= 0.48 y corte estricto contra alucinaciones.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        chroma_db_dir: Optional[str] = None,
        embedding_model: Optional[str] = None,
        min_relevance_score: float = MIN_RELEVANCE_SCORE_THRESHOLD
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.timeout = settings.ollama_timeout
        self.chroma_db_dir = Path(chroma_db_dir or settings.chroma_db_dir)
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.min_relevance_score = min_relevance_score

        self._embeddings = None
        self._vector_store = None

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Inicialización diferida (lazy-load) del modelo de embeddings en modo offline."""
        if self._embeddings is None:
            logger.info(f"Cargando modelo de embeddings '{self.embedding_model_name}' en modo offline...")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name,
                model_kwargs={"local_files_only": True},
                encode_kwargs={"normalize_embeddings": True}
            )
        return self._embeddings

    @property
    def vector_store(self) -> Optional[Chroma]:
        """Inicialización diferida de ChromaDB persistente."""
        if self._vector_store is None:
            try:
                self.chroma_db_dir.mkdir(parents=True, exist_ok=True)
                self._vector_store = Chroma(
                    persist_directory=str(self.chroma_db_dir),
                    embedding_function=self.embeddings
                )
                logger.info(f"ChromaDB cargado exitosamente desde {self.chroma_db_dir.resolve()}")
            except Exception as exc:
                logger.warning(f"No se pudo inicializar ChromaDB en {self.chroma_db_dir}: {exc}")
                self._vector_store = None
        return self._vector_store

    def reload_vector_store(self) -> None:
        """
        Fuerza la recarga de ChromaDB en memoria para reflejar nuevos documentos indexados.
        """
        logger.info("Recargando instancia de ChromaDB en memoria...")
        self._vector_store = None
        _ = self.vector_store

    def _build_role_filter(self, user_role: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Construye la condición de filtrado en ChromaDB según el rol del usuario:
        - Otros / Visitante / Sin Rol: Acceso irrestricto a toda la base documental (sin filtro de audiencia, retorna None).
        - Administrativo / Funcionario / Admin TI: Accede a documentos de general, administrativo, funcionario, profesor y admin_ti.
        - Profesor / Docente: Accede a documentos de general, profesor, docente y estudiante.
        - Estudiante: Accede a documentos y guías para estudiantes y general.
        """
        if not user_role:
            return None

        role_lower = user_role.strip().lower()

        if role_lower in ["otros", "otro", "visitante", "visitantes", "aspirante", "aspirantes", "egresado", "egresada", "externo", "externa", "general"]:
            # Acceso total irrestricto sin filtros
            return None
        elif role_lower in ["administrativo", "administrativa", "funcionario", "funcionaria", "admin_ti"]:
            return {
                "audience": {"$in": ["general", "administrativo", "funcionario", "profesor", "admin_ti"]}
            }
        elif role_lower in ["profesor", "profesora", "docente"]:
            return {
                "audience": {"$in": ["general", "profesor", "docente", "estudiante"]}
            }
        elif role_lower in ["estudiante", "alumno", "alumna"]:
            return {
                "audience": {"$in": ["general", "estudiante"]}
            }
        return None

    async def query_rag(
        self,
        question: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        user_role: Optional[str] = None,
        golden_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta el pipeline RAG completo:
        1. Expansión LLM de consulta (jerga -> terminología institucional).
        2. Normalización léxica estática (complementaria).
        3. Búsqueda por similitud con puntuación de relevancia en ChromaDB (k=8, umbral >= 0.48) y filtro por rol.
        4. Cross-Encoder Reranker: reordena Top-8 -> Top-3.
        5. Corte estricto / Fallback temático: Si ningún fragmento supera el umbral, evalúa fallback.
        6. Ensamblaje del System Prompt institucional + Golden Cache context + historial.
        7. Invocación asíncrona a Ollama (unimon:8b).
        """
        retrieved_docs = []
        sources: List[str] = []
        context_parts = []

        # 0. Guardrail Rápido Fuera de Dominio (Out-of-Domain)
        if is_out_of_domain_query(question):
            logger.info(f"Guardrail activado en query_rag para consulta fuera de dominio: '{question}'")
            return {
                "response": MENSAJE_FUERA_DE_DOMINIO,
                "sources": [],
                "source": "unimon_guardrail_out_of_domain",
                "model": None,
                "retrieved_chunks": 0,
                "has_context": False,
                "quick_replies": []
            }

        filter_condition = self._build_role_filter(user_role)

        # 1. Expansión Multi-Consulta asíncrona tolerante a jerga
        query_variants = await async_generate_multi_query_variants(question, user_role or "general", max_variants=3)

        # 2. Búsqueda por similitud con puntuación de relevancia en ChromaDB combinando variantes
        candidate_docs_map: Dict[str, tuple] = {}
        if self.vector_store is not None:
            try:
                filter_desc = f" con filtro {filter_condition}" if filter_condition else " sin filtro"
                logger.info(f"Buscando fragmentos en ChromaDB ({len(query_variants)} variantes, umbral >= {self.min_relevance_score}{filter_desc})")

                for q_var in query_variants:
                    formatted_query = format_e5_query(q_var)
                    if filter_condition:
                        docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                            formatted_query,
                            k=6,
                            filter=filter_condition
                        )
                    else:
                        docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                            formatted_query,
                            k=6
                        )

                    for doc, score in docs_with_scores:
                        if score is not None and score >= self.min_relevance_score:
                            source_path = doc.metadata.get("source", "")
                            page_num = doc.metadata.get("page", doc.metadata.get("page_number", ""))
                            # Clave única determinista por fragmento para deduplicación
                            chunk_key = f"{source_path}_{page_num}_{doc.page_content.strip()[:100]}"

                            if chunk_key not in candidate_docs_map or score > candidate_docs_map[chunk_key][1]:
                                candidate_docs_map[chunk_key] = (doc, score)

                valid_docs_with_scores = sorted(candidate_docs_map.values(), key=lambda x: x[1], reverse=True)
                for idx, (doc, score) in enumerate(valid_docs_with_scores[:8], 1):
                    score_val = f"{score:.4f}" if score is not None else "N/A"
                    source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                    source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                    page_num = doc.metadata.get("page", doc.metadata.get("page_number", None))
                    page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""
                    logger.info(f"  [Chunk #{idx} VÁLIDO] Score: {score_val} | Fuente: {source_filename}{page_info} | Texto: '{doc.page_content.strip()[:90]}...'")

            except Exception as exc:
                logger.warning(f"Error al realizar búsqueda de similitud en ChromaDB: {exc}")

        # 3. Cross-Encoder Reranker y Ensamblado de Contexto Jerárquico por Documento
        if valid_docs_with_scores:
            rerank_query = query_variants[0] if query_variants else question
            reranked = rerank_chunks(rerank_query, valid_docs_with_scores, top_k=3)

            # Identificar el documento principal con mayor relevancia semántica
            primary_doc, _ = reranked[0]
            primary_source = primary_doc.metadata.get("source")

            # Recolectar fragmentos del documento principal disponibles
            primary_chunks = []
            for doc, _ in valid_docs_with_scores:
                if doc.metadata.get("source") == primary_source:
                    if not any(doc.page_content.strip() == pc.page_content.strip() for pc in primary_chunks):
                        primary_chunks.append(doc)

            # Si solo hay 1 fragmento del documento principal y ChromaDB está activo,
            # recuperar proactivamente fragmentos complementarios (requisitos/pasos) del mismo archivo
            if len(primary_chunks) == 1 and self.vector_store is not None and primary_source:
                try:
                    search_q = format_e5_query(rerank_query)
                    extra_docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(
                        search_q,
                        k=4,
                        filter={"source": primary_source}
                    )
                    for edoc, escore in extra_docs_with_scores:
                        if escore is not None and escore >= self.min_relevance_score:
                            if not any(edoc.page_content.strip() == pc.page_content.strip() for pc in primary_chunks):
                                primary_chunks.append(edoc)
                except Exception as exc:
                    logger.debug(f"No se pudieron cargar fragmentos complementarios para {primary_source}: {exc}")

            # Ordenar fragmentos del documento principal en orden lógico estructural
            def chunk_logical_rank(chunk_doc):
                c_lower = chunk_doc.page_content.lower()
                if any(k in c_lower for k in ["1. generalidades", "1. objetivo", "1. alcance"]):
                    return 1
                if any(k in c_lower for k in ["2. requisitos", "requisitos previos", "restricciones", "roles autorizados"]):
                    return 2
                if any(k in c_lower for k in ["3. procedimiento", "procedimiento paso a paso", "paso 1"]):
                    return 3
                if any(k in c_lower for k in ["4. reglas", "4. políticas", "4. politicas"]):
                    return 4
                if any(k in c_lower for k in ["5. canales", "canales de escalado", "canales de soporte"]):
                    return 5
                return 6

            primary_chunks_sorted = sorted(primary_chunks, key=chunk_logical_rank)

            # Inyectar fragmentos del documento principal primero
            for doc in primary_chunks_sorted:
                retrieved_docs.append(doc)
                source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                page_num = doc.metadata.get("page", None)
                page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""
                if source_filename not in sources:
                    sources.append(source_filename)
                cleaned_chunk = strip_chunk_boilerplate(doc.page_content)
                context_parts.append(f"[{source_filename}{page_info}]\n{cleaned_chunk}")

            # Agregar fragmentos secundarios más relevantes de otros documentos (hasta un máximo de 4 fragmentos)
            for doc, _ in reranked[1:]:
                if len(context_parts) >= 4:
                    break
                if doc.metadata.get("source") != primary_source:
                    if not any(doc.page_content.strip() == pc.page_content.strip() for pc in primary_chunks):
                        retrieved_docs.append(doc)
                        source_path = doc.metadata.get("source", "Procedimiento Unisimon")
                        source_filename = Path(source_path).name if source_path else "Procedimiento Unisimon"
                        page_num = doc.metadata.get("page", None)
                        page_info = f" (Pág. {page_num + 1})" if isinstance(page_num, int) else ""
                        if source_filename not in sources:
                            sources.append(source_filename)
                        cleaned_chunk = strip_chunk_boilerplate(doc.page_content)
                        context_parts.append(f"[{source_filename}{page_info}]\n{cleaned_chunk}")


        # 3. Si ningún fragmento superó el umbral, evaluar fallback temático o mensaje estándar
        if not context_parts:
            # Si contiene palabras clave temáticas conocidas, entregar respuesta guiada temática
            q_lower = question.lower()
            if any(k in q_lower for k in [
                "portal", "correo", "teams", "carnet", "kactus", "seven", "backup",
                "malware", "virus", "computador", "portatil", "pantalla", "clave", "contraseña"
            ]):
                logger.info("Activando fallback temático institucional por coincidencia de categoría.")
                return self._generate_fallback_response(question, user_name, sources)

            logger.info(f"Cero fragmentos con score >= {self.min_relevance_score}. Retornando mensaje institucional estricto sin invocar LLM.")
            return {
                "response": MENSAJE_NO_DOCUMENTADO,
                "sources": [],
                "source": "unimon_no_doc_fallback",
                "model": None,
                "retrieved_chunks": 0,
                "has_context": False
            }

        context_text = "\n\n---\n\n".join(context_parts)

        # 5. Ensamblar System Prompt estricto + Golden Cache few-shot + historial y User Prompt
        full_context = context_text
        if golden_context:
            full_context = f"{full_context}\n\n---\n[CASO DE REFERENCIA VALIDADO]:\n{golden_context.strip()}"

        system_prompt = STRICT_SYSTEM_PROMPT_TEMPLATE.format(context=full_context, query=question)
        user_greeting = f"El usuario se llama {user_name}. " if user_name else ""
        role_ctx = f"[Rol del usuario: {user_role}] " if user_role else ""
        user_prompt = f"{user_greeting}{role_ctx}Consulta del usuario: {question}"

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": user_prompt})

        # 5. Llamada asíncrona a Ollama API
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "repeat_penalty": 1.15,
                "top_p": 0.9,
                "num_predict": 768
            }
        }

        url = f"{self.base_url}/api/chat"

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Enviando consulta a Ollama ({url}) con modelo '{self.model}'...")
                response = await client.post(url, json=payload, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    bot_message = data.get("message", {}).get("content", "").strip()
                    prompt_tokens = data.get("prompt_eval_count", 0) or 0
                    eval_tokens = data.get("eval_count", 0) or 0
                    logger.info("Respuesta generada exitosamente por Ollama (tokens: %s prompt, %s eval).", prompt_tokens, eval_tokens)

                    # Sanitizar saludos redundantes, placeholders, GLPI y enlaces duplicados
                    bot_message = clean_llm_response(bot_message)
                    
                    # Ubicar el pie de confirmación estrictamente al final del mensaje
                    bot_message = bot_message.rstrip() + CLOSING_FEEDBACK_QUESTION

                    return {
                        "response": bot_message,
                        "sources": sources,
                        "source": f"ollama_{self.model}",
                        "model": self.model,
                        "retrieved_chunks": len(retrieved_docs),
                        "has_context": True,
                        "quick_replies": QUICK_REPLIES_DIAGNOSTICO,
                        "prompt_tokens": prompt_tokens,
                        "eval_tokens": eval_tokens
                    }
                else:
                    logger.warning(f"Ollama respondió con código {response.status_code}: {response.text}")
                    return self._generate_fallback_response(question, user_name, sources)

        except Exception as exc:
            logger.warning(f"No se pudo conectar con el servidor Ollama ({exc}). Activando respuesta de contingencia.")
            return self._generate_fallback_response(question, user_name, sources)

    def _generate_fallback_response(
        self,
        user_message: str,
        user_name: Optional[str] = None,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generador de respuesta institucional de contingencia cuando Ollama no está disponible
        o como fallback temático de alta precisión.
        """
        saludo = f"¡Hola {user_name}!" if user_name else "¡Hola!"
        msg_lower = user_message.lower()

        if any(w in msg_lower for w in ["contacto", "canal", "canales", "telefono", "teléfono", "correo", "atención", "atencion", "wasap", "whatsapp", "directorio"]):
            contenido = (
                f"{saludo} Los canales oficiales de atención y soporte técnico TI de la **Universidad Simón Bolívar (Colombia)** son:\n\n"
                "• **Sede Barranquilla:**\n"
                "  - Correo: `solicitudcomputo@unisimon.edu.co`\n"
                "  - WhatsApp: `3172683922`\n"
                "  - Teléfono: `(605) 3444333` Ext. `8003` y `8004`\n\n"
                "• **Sede Cúcuta:**\n"
                "  - Correo: `helpdesk@unisimon.edu.co`\n"
                "  - Teléfono: `(607) 5827070` Ext. `129`\n\n"
                "También puedes radicar un caso directamente con nuestro equipo describiendo tu solicitud."
            )
        elif any(w in msg_lower for w in ["portal", "portal web", "pagina", "notas", "matricula", "matrícula"]):
            contenido = (
                f"{saludo} Para el acceso a los **Portales Institucionales Unisimon** (Estudiantes y Docentes):\n\n"
                "1. Ingresa a la página oficial: `https://unisimon.edu.co` y selecciona el Portal correspondiente.\n"
                "2. Digita tu usuario institucional y tu contraseña registrada.\n"
                "3. Si olvidaste tu contraseña o el sistema indica datos incorrectos, utiliza la opción **'¿Olvidó su contraseña?'** en la pantalla de inicio o contacta a Soporte TI."
            )
        elif any(w in msg_lower for w in ["carnet", "carné", "carnet digital", "app"]):
            contenido = (
                f"{saludo} Para la gestión de tu **Carnet Digital** en la **App Unisimon**:\n\n"
                "1. Descarga la App Unisimon desde Google Play Store o Apple App Store.\n"
                "2. Inicia sesión con tus credenciales de correo institucional.\n"
                "3. Ingresa a la sección 'Carnet Digital'. Si no visualizas tu foto o carnet, valida tu estado de matrícula con Registro Académico o reporta la incidencia a TI."
            )
        elif any(w in msg_lower for w in ["teams", "reunion", "reuniones", "tim"]):
            contenido = (
                f"{saludo} Para soporte en **Microsoft Teams Institucional**:\n\n"
                "1. Asegúrate de iniciar sesión con tu cuenta `@unisimon.edu.co` y contraseña institucional.\n"
                "2. Si la aplicación de escritorio presenta bloqueo, ingresa vía web en `https://teams.microsoft.com`.\n"
                "3. Si un grupo o clase no te aparece cargado, consulta con el docente titular o el área de Registro."
            )
        elif any(w in msg_lower for w in ["backup", "copia de seguridad", "copias", "respaldo"]):
            contenido = (
                f"{saludo} Conforme al procedimiento **P-GT-10** (*Generación y Restauración de Backup de la Información*):\n\n"
                "• La Universidad realiza copias de seguridad periódicas y programadas de los sistemas y bases de datos institucionales.\n"
                "• Para solicitudes de restauración de información o requerimientos de respaldo específico, comunícate con el área de TI o radica un ticket de servicio."
            )
        elif any(w in msg_lower for w in [
            "kactus", "katuc", "kaktu", "seven", "seben", "erp", "nómina", "nomina",
            "contraseña", "contrasena", "clave", "clabe", "bloqueo", "desbloquear", "login"
        ]):
            contenido = (
                f"{saludo} Para soporte en los sistemas institucionales **Kactus / Seven** (Procedimiento **P-GT-11** y **P-GT-12**):\n\n"
                "• Las incidencias y requerimientos deben ser radicados indicando el módulo afectado, captura de pantalla del error y usuario solicitante.\n"
                "• El equipo de soporte de aplicaciones gestionará el requerimiento conforme a los acuerdos de nivel de servicio (SLA)."
            )
        elif any(w in msg_lower for w in ["virus", "malware", "antivirus", "amenaza", "infectado"]):
            contenido = (
                f"{saludo} Según el procedimiento **P-GT-07** (*Protección de Código Malicioso*):\n\n"
                "• Todo equipo institucional debe contar con la solución de protección antimalware corporativa activa y actualizada.\n"
                "• Ante sospecha de infección, desconecta el equipo de la red y notifica inmediatamente a Soporte TI."
            )
        elif any(w in msg_lower for w in [
            "computador", "conputador", "portatil", "portátil", "pantalla", "pantaya",
            "monitor", "proyector", "proyestor", "mouse", "mause", "teclado", "cable",
            "hdmi", "red", "wifi", "internet", "interner", "no prende", "parpadea", "falla"
        ]):
            contenido = (
                f"{saludo} Soy UniMon, tu asistente de Soporte Técnico de Nivel 1 de la Universidad Simón Bolívar.\n\n"
                "Para ayudarte con este inconveniente técnico, te sugiero realizar estos pasos iniciales de descarte:\n"
                "1. Verifica que los cables de poder, red o video estén firmemente conectados.\n"
                "2. Reinicia el equipo o dispositivo y verifica si el comportamiento persiste.\n"
                "3. Si el inconveniente es en un aplicativo institucional, cierra sesión y vuelve a ingresar."
            )
        else:
            contenido = MENSAJE_NO_DOCUMENTADO

        is_doc = (contenido != MENSAJE_NO_DOCUMENTADO)
        if is_doc and "¿pudiste resolver tu problema con estos pasos?" not in contenido.lower():
            contenido = contenido.rstrip() + CLOSING_FEEDBACK_QUESTION

        return {
            "response": contenido,
            "sources": sources if sources is not None else [],
            "source": "knowledge_base_fallback",
            "model": "rule_based_institutional_unisimon",
            "retrieved_chunks": 0,
            "has_context": is_doc,
            "quick_replies": QUICK_REPLIES_DIAGNOSTICO if is_doc else []
        }

    async def answer_query(
        self,
        query: str,
        user_role: Optional[str] = None,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        golden_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Punto de entrada principal para responder consultas con normalización léxica,
        expansión LLM, reranking y filtrado de metadatos por rol.
        """
        return await self.query_rag(
            question=query,
            user_name=user_name,
            chat_history=chat_history,
            user_role=user_role,
            golden_context=golden_context
        )

    async def consultar(
        self,
        pregunta: str,
        user_name: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        es_diagnostico: bool = False,
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta al motor RAG de UniMon con soporte para historial de conversación y rol de usuario.
        """
        return await self.query_rag(
            question=pregunta,
            user_name=user_name,
            chat_history=chat_history,
            user_role=user_role
        )


# Instancia por defecto para importaciones limpias
rag_service = RAGService()


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Retorna la instancia del modelo de embeddings de RAG (singleton)."""
    return rag_service.embeddings
