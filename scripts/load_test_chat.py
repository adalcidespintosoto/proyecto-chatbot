"""Burst load test for the real FastAPI chat endpoint using isolated sessions.

The test sends one synchronized burst. X-Forwarded-For gives each test session a
distinct simulated client IP when Uvicorn proxy headers are enabled.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("credenciales_primiparo", "Credenciales", "Soy primíparo y ya pagué matrícula. ¿Dónde encuentro mi usuario y clave?", "Activar Usuario y Correo institucional.pdf"),
    ("credenciales_primer_semestre", "Credenciales", "Estoy en primer semestre, ¿qué parte del recibo de matrícula tiene mis datos de acceso?", "Activar Usuario y Correo institucional.pdf"),
    ("activar_usuario_nuevo", "Credenciales", "¿Cómo activo el usuario institucional que me asignaron al ingresar a primer semestre?", "Activar Usuario y Correo institucional.pdf"),
    ("cambio_clave_inicial", "Credenciales", "Al entrar por primera vez al Portal Estudiantes, ¿cómo cambio la clave temporal?", "Activar Usuario y Correo institucional.pdf"),
    ("correo_nuevo_ingreso", "Credenciales", "¿En qué momento del proceso de matrícula se informa el correo institucional del estudiante nuevo?", "GIE - ASPIRANTES NOV.2021.pptx"),
    ("portal_estudiantes_barranquilla", "Portales", "¿Cómo entro al Portal Estudiantes desde la página de portales de la universidad?", "Activar Usuario y Correo institucional.pdf"),
    ("recuperar_contrasena_estudiante", "Credenciales", "Olvidé la contraseña del Portal Estudiantes, ¿cómo la restablezco?", "Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf"),
    ("correo_personal_recuperacion", "Credenciales", "¿A qué correo llega el enlace para recuperar la contraseña institucional?", "Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf"),
    ("clave_segura_portal", "Credenciales", "¿Qué requisitos debe tener la nueva contraseña del Portal Estudiantes?", "Activar Usuario y Correo institucional.pdf"),
    ("correo_estudiantil_acceso", "Credenciales", "Ya tengo mi correo estudiantil, ¿por dónde debo abrirlo para que la cuenta sea reconocida?", "Activar Usuario y Correo institucional.pdf"),
    ("teams_estudiante_acceso", "Microsoft 365", "¿Cómo inicio sesión en Microsoft Teams con mi cuenta de estudiante?", "Como_acceder_MS_Teams_Estudiantes.pdf"),
    ("teams_sitio_universidad", "Microsoft 365", "¿Desde qué sección del sitio de Unisimon se accede al correo para entrar a Teams?", "Como_acceder_MS_Teams_Estudiantes.pdf"),
    ("teams_grupos_estudiante", "Microsoft 365", "¿Cómo me matriculo en mis grupos de Teams y Moodle como estudiante?", "Matricular_grupos_teams_moodle_Estudiante.pdf"),
    ("teams_grupos_moodle", "Microsoft 365", "No veo mis cursos en Teams, ¿qué indica la guía de matrícula de grupos para estudiantes?", "Estudiantes_Matricular grupos en teams ymoodle.pdf"),
    ("descargar_office", "Microsoft 365", "¿Dónde puedo descargar e instalar Microsoft 365 con mi cuenta institucional?", "Descarga e instalación Ms 365.pdf"),
    ("credenciales_microsoft", "Microsoft 365", "¿Qué credenciales debo usar para iniciar sesión en los servicios Microsoft de la universidad?", "Credenciales microsoft.pdf"),
    ("acceso_outlook", "Microsoft 365", "¿Cómo ingreso al correo institucional de Microsoft desde la web universitaria?", "Como_acceder_a_Microsoft_Teams.pdf"),
    ("teams_profesores", "Microsoft 365", "¿Cómo accede un profesor a Teams para sus clases?", "Profesores_Integración teams y moodle.pdf"),
    ("grabar_reunion_teams", "Microsoft 365", "¿Cómo puedo grabar una clase o reunión de Teams y compartirla?", "Grabar un clase en Teams y compartir en Stream.pdf"),
    ("reunion_no_asociada", "Microsoft 365", "¿Cómo creo una reunión de Teams que no esté asociada a un grupo?", "Crear reuniones No asociadas a grupos.pdf"),
    ("registrar_calificaciones", "Calificaciones", "¿Cuál es la ruta para que un docente ingrese calificaciones en el portal?", "Calificaciones.pdf"),
    ("guardar_borrador_notas", "Calificaciones", "¿Cómo guardo como borrador las notas antes de enviarlas?", "Calificaciones.pdf"),
    ("finalizar_notas", "Calificaciones", "Después de revisar las calificaciones, ¿qué botón finaliza y envía el borrador?", "Calificaciones.pdf"),
    ("consultar_notas_estudiante", "Calificaciones", "¿Dónde consulto mis calificaciones como estudiante?", "Calificaciones.pptx"),
    ("calificaciones_posgrado", "Calificaciones", "¿Cómo registra un docente una nota definitiva de un curso de posgrado?", "Calificaciones Posgrados.pdf"),
    ("votar_elecciones", "Elecciones", "¿Cuál es el paso a paso para votar en las elecciones institucionales?", "Aplicativo Elecciones -  Cómo votar.pptx"),
    ("portal_elecciones", "Elecciones", "¿En qué página ingreso para participar en las elecciones de la universidad?", "Aplicativo Elecciones -  Cómo votar.pptx"),
    ("confirmar_voto", "Elecciones", "Ya elegí candidato, ¿cómo confirmo mi voto en el aplicativo de elecciones?", "Aplicativo Elecciones -  Cómo votar.pptx"),
    ("elecciones_estudiante", "Elecciones", "¿Cómo participa un estudiante en la jornada electoral institucional?", "Aplicativo Elecciones -  Cómo votar.pptx"),
    ("elecciones_credenciales", "Elecciones", "¿Con qué cuenta ingreso al sistema de votaciones institucionales?", "Aplicativo Elecciones -  Cómo votar.pptx"),
    ("descargar_certificado", "Certificados", "¿Cómo descargo un certificado estudiantil electrónico?", "Certificados estudiantes_v2.pptx"),
    ("solicitar_certificado", "Certificados", "¿Qué pasos debo seguir para solicitar un certificado como estudiante?", "Descarga de certificados.pptx"),
    ("certificado_portal", "Certificados", "¿En qué portal se consultan los certificados electrónicos de estudiantes?", "Certificados Electrónicos.pptx"),
    ("certificado_pago", "Certificados", "¿Cómo verifico o descargo el certificado electrónico después de solicitarlo?", "Certificados estudiantes_v2.pptx"),
    ("inscripcion_cursos_intersemestrales", "Matrícula", "¿Cómo hago la inscripción a cursos intersemestrales?", "Inscripcion de cursos intersemestrales.pdf"),
    ("matricula_intersemestral", "Matrícula", "¿Cómo matriculo un curso intersemestral desde el portal?", "Matricula de Cursos Intersemestrales.pptx"),
    ("estudiante_antiguo_matricula", "Matrícula", "¿Qué pasos sigue un estudiante antiguo para realizar su matrícula?", "2. Estudiantes Antiguos Pregrado.pptx"),
    ("matricula_completa_media", "Matrícula", "¿Dónde consulto el procedimiento de matrícula completa o media matrícula?", "3. Matricula Completa-Media matricula.pptx"),
    ("reintegro_estudiante", "Matrícula", "¿Qué debo hacer para solicitar un reintegro a un programa de pregrado?", "6. Reintegro.pptx"),
    ("transferencia_externa", "Matrícula", "¿Cómo se tramita una transferencia externa para ingresar a la universidad?", "4. Transferencia Externa.pptx"),
    ("reactivacion_inscripcion", "Admisiones", "¿Cómo reactivo una inscripción que quedó inactiva?", "Aspirantes - Reactivación de Inscripción.pdf"),
    ("oficializar_matricula", "Admisiones", "¿Cómo oficializa su matrícula un aspirante después de completar el formulario?", "GIE - ASPIRANTES NOV.2021.pptx"),
    ("gestion_inscripciones", "Admisiones", "¿Cómo consulto y gestiono una inscripción de aspirante?", "Gestión de inscripciones.pdf"),
    ("bloqueo_usuario", "Cuentas", "¿Qué puedo hacer si mi usuario institucional aparece bloqueado?", "Instructivo Bloqueos.pdf"),
    ("recuperar_usuario_portal", "Cuentas", "No recuerdo mi usuario del Portal Estudiantes, ¿cómo lo consulto?", "Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf"),
    ("cambiar_clave_portal", "Cuentas", "¿Cómo cambio la contraseña de mi cuenta del Portal Estudiantes?", "Activar Usuario y Correo institucional.pdf"),
    ("acceso_moodle_estudiante", "Aula Extendida", "¿Cómo accedo a Aula Extendida con mis credenciales institucionales?", "Matricular_grupos_teams_moodle_Estudiante.pdf"),
    ("acceso_moodle_grupos", "Aula Extendida", "¿Cómo encuentro los grupos de mis asignaturas en Moodle?", "Estudiantes_Matricular grupos en teams ymoodle.pdf"),
    ("uso_correo_y_aula", "Aula Extendida", "¿La contraseña del portal también sirve para correo estudiantil y Aula Extendida?", "Activar Usuario y Correo institucional.pdf"),
    ("acceso_portales_sedes", "Portales", "¿Qué opción de sede debo elegir al ingresar al Portal Estudiantes de Barranquilla?", "Activar Usuario y Correo institucional.pdf"),
    ("instalar_office_portal", "Microsoft 365", "¿Cómo instalo las aplicaciones de Office usando mi cuenta institucional?", "Descarga e instalación Ms 365.pdf"),
    ("agregar_integrante_teams", "Microsoft 365", "¿Cómo agrego a una persona a un equipo o grupo de Microsoft Teams?", "Agregar_miembros_Grupos_MS_Teams.pdf"),
    ("ajustar_asistentes_reunion", "Microsoft 365", "¿Cómo cambio o administro los participantes de una reunión de Teams?", "Ajustes participantes reuniones Ms Teams.pdf"),
    ("reunion_teams_ipad", "Microsoft 365", "¿Cómo programo una reunión de Teams desde un iPad?", "Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf"),
    ("administrar_grupos_teams", "Microsoft 365", "¿Dónde consulto los grupos de Teams asociados a mis cursos?", "Grupos_en_Teams.pdf"),
    ("depurar_curso_aula", "Aula Extendida", "¿Qué debo revisar si un curso duplicado sigue apareciendo en Teams o Aula Extendida?", "Depuración de cursos (Teams y Aula Extendida).pdf"),
    ("grabar_videollamada", "Microsoft 365", "¿Cómo se graba una videollamada de Teams?", "Grabar videollamadas en Teams.pdf"),
    ("credenciales_servicios_microsoft", "Microsoft 365", "¿Qué cuenta debo usar para entrar a las herramientas Microsoft institucionales?", "Credenciales microsoft.pdf"),
    ("acceso_teams_desde_portal", "Microsoft 365", "¿Cuál es el acceso indicado para abrir Microsoft Teams como estudiante?", "Como_acceder_MS_Teams_Estudiantes.pdf"),
    ("pac_profesores", "Docentes", "¿Cómo diligencio el PAC como profesor?", "Diligenciamiento de PAC (Profesores).pdf"),
    ("habilitar_pac_director", "Docentes", "¿Quién puede habilitar permisos de PAC para un director de programa?", "Habilitar permisos PAC (Director de programa).pdf"),
    ("configurar_evaluacion_profesoral", "Docentes", "¿Dónde se configura la evaluación profesoral para funcionarios?", "Configuracion de Evaluacion Profesoral - Funcionarios.pptx"),
    ("configurar_evaluaciones", "Docentes", "¿Cómo se configuran las evaluaciones de un curso?", "Configuracion de Evaluaciones.pptx"),
    ("ausentes_causas", "Gestión académica", "¿Cómo registro las causas de deserción o ausencia de estudiantes?", "Ingreso de Causas de Desertores y Ausentes.pdf"),
    ("parametrizar_ausencias", "Gestión académica", "¿Qué instructivo explica la parametrización de desertores y ausentes?", "instructivo parametrizacion desertores y ausentes.pptx"),
    ("inscripcion_curso_enfasis", "Matrícula", "¿Qué autorización necesito para inscribirme en un curso de énfasis?", "Autorizacion de Inscripcion Curso de Enfasis.pptx"),
    ("autorizacion_intersemestral", "Matrícula", "¿Cómo se autorizan cursos intersemestrales?", "Autorizaciones cursos intersemestrales.pptx"),
    ("inscripcion_grado", "Grados", "¿Cómo presento la solicitud de inscripción para grado?", "Solicitud de inscripción para grado.pdf"),
    ("tramite_graduacion", "Grados", "¿Qué pasos se realizan en el sistema para graduar a un estudiante?", "Graduar.pptx"),
    ("aprobacion_requisitos_grado", "Grados", "¿Cómo se revisa o aprueba el cumplimiento de requisitos para grado?", "Instructivo Aprobación de Requisitos.pdf"),
    ("homologar_asignaturas", "Admisiones", "¿Qué debo hacer para solicitar la homologación de asignaturas?", "Homologaciones.pdf"),
    ("anular_preinscripcion", "Admisiones", "¿Cómo se anula o modifica un programa en una preinscripción?", "Anulación y Modificación de Programa Pre-inscripciones.pptx"),
    ("demo_tipos_admision", "Admisiones", "¿Qué tipos de admisión contempla el proceso para aspirantes?", "Demo tipos de admisión.pptx"),
    ("aprobar_requisitos_aspirante", "Admisiones", "¿Cómo verifico y apruebo los requisitos de un aspirante?", "Aprobación de Requisitos.pptx"),
    ("consultar_hoja_vida", "Admisiones", "¿Dónde puedo consultar la hoja de vida de matrícula de un estudiante?", "Consulta de Hoja de Vida - Matrículas.pdf"),
    ("excepciones_bloqueos", "Cuentas", "¿Cómo consulto si un estudiante tiene excepciones, bloqueos o sanciones?", "Consulta de Excepciones, bloqueos y sanciones.pdf"),
    ("gestion_bloqueos", "Cuentas", "¿Qué pasos muestra el instructivo para gestionar bloqueos de usuarios?", "Instructivo Bloqueos.pdf"),
    ("bloqueo_excepciones_sanciones", "Cuentas", "¿En qué módulo se revisan bloqueos y sanciones asociados a estudiantes?", "Bloqueos, Sanciones y Excepciones.pptx"),
    ("creditos_autorizacion", "Créditos", "¿Cómo se tramita una autorización para estudiantes en proceso de crédito?", "Autorización estudiantes en proceso de créditos_v2.pdf"),
    ("solicitud_credito", "Créditos", "¿Cómo se aprueba una solicitud de crédito estudiantil?", "Aprobacion Solicitudes de credito.pptx"),
    ("verificar_pago", "Pagos", "¿Cómo verifico en el sistema si un pago ya fue aplicado?", "Instructivo Verificación pagos V2.pdf"),
    ("detalle_factura", "Pagos", "¿Dónde consulto los anexos o el detalle de una factura?", "Detalle factura (Anexos).pptx"),
    ("cuentas_bancarias", "Pagos", "¿Qué información institucional está disponible sobre bancos y cuentas para pagos?", "Bancos y cuentas_v1_20211007.pdf"),
    ("reporte_notas_credito", "Financiero", "¿Cómo se gestiona un reporte de notas crédito?", "Gestión de Notas Crédito.pdf"),
    ("liquidacion_servicios_academicos", "Financiero", "¿Dónde se configura la liquidación de servicios académicos?", "Liquidacion de servicios academicos - Configuración.pptx"),
    ("descuentos_programa", "Financiero", "¿Cómo consulto los descuentos asociados a un programa académico?", "Descuentos por Programa.pptx"),
    ("valor_matricula", "Financiero", "¿Cómo genero el reporte de valor de matrícula en SIAAF?", "7. Valor matrícula.pptx"),
    ("matricula_nuevos_reporte", "Admisiones", "¿Qué filtros pide el reporte de estudiantes nuevos de pregrado antes de generarlo?", "1. Estudiantes Nuevos Pregrado.pptx"),
    ("reporte_inscripciones_consolidado", "Admisiones", "¿Cómo genero el consolidado de inscripciones y matrículas de estudiantes nuevos?", "1. Estudiantes Nuevos Pregrado.pptx"),
    ("reporte_estudiantes_antiguos", "Admisiones", "¿Qué informe se usa para generar el reporte de estudiantes antiguos de pregrado?", "2. Estudiantes Antiguos Pregrado.pptx"),
    ("reporte_matricula_completa", "Admisiones", "¿Cómo se genera el reporte de matrícula completa y media matrícula?", "3. Matricula Completa-Media matricula.pptx"),
    ("reporte_reintegro", "Admisiones", "¿Cuál es el instructivo de SIAAF para generar el reporte de reintegros?", "6. Reintegro.pptx"),
    ("reporte_transferencias", "Admisiones", "¿Qué documento explica el reporte de transferencias externas?", "4. Transferencia Externa.pptx"),
    ("reporte_ser_pilo", "Admisiones", "¿Cómo se consulta el informe de estudiantes Ser Pilo Paga?", "5. Ser Pilo Paga.pptx"),
    ("informe_inscripciones", "Admisiones", "¿Qué opciones ofrece el módulo de gestión de inscripciones?", "Gestión de inscripciones.pdf"),
    ("atencion_modulo_estudiantes", "Atención estudiantil", "¿Cómo se atiende una solicitud en el módulo de atención a estudiantes?", "Instructivo Módulo Atención Estudiantes (Completo).pdf"),
    ("tutorias_estudiantes", "Atención estudiantil", "¿Cómo se registra o gestiona una tutoría para un estudiante?", "Instructivo Atencion a Estudiantes (Tutorías).pdf"),
    ("practicas_estudiantes", "Prácticas", "¿Qué procedimiento deben seguir los estudiantes para gestionar sus prácticas?", "Gestión Prácticas - Estudiantes.pdf"),
    ("autoevaluacion_funcionarios", "Funcionarios", "¿Cómo se administra la autoevaluación por grupos de funcionarios?", "Autoevaluacion por Grupos - Funcionarios.pdf"),
    ("solicitud_supletorio", "Académico", "¿Qué pasos indica el documento para autorizar un examen supletorio?", "Autorización de Supletorios.pdf"),
]


def normalize_source_name(value: str) -> str:
    """Compara nombres de fuente ignorando acentos y espacios duplicados."""
    decomposed = unicodedata.normalize("NFKD", str(value or ""))
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_accents.casefold().split())


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((percent / 100) * (len(ordered) - 1))))
    return ordered[index]


async def run_case(
    index: int,
    case: tuple[str, str, str, str],
    base_url: str,
    gate: asyncio.Event,
    client: httpx.AsyncClient,
    run_id: str,
) -> dict:
    case_id, category, question, expected_source = case
    session_id = f"load100-{run_id}-{index:03d}"
    await gate.wait()
    started = time.perf_counter()
    try:
        response = await client.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"mensaje": question, "session_id": session_id},
            headers={"X-Forwarded-For": f"198.51.100.{index + 1}"},
        )
        latency_ms = (time.perf_counter() - started) * 1000
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        message = payload.get("mensaje") or payload.get("response") or payload.get("reply") or ""
        sources = payload.get("sources") or []
        expected_key = normalize_source_name(expected_source)
        source_match = any(expected_key in normalize_source_name(source) for source in sources)
        return {
            "user": index + 1,
            "case_id": case_id,
            "category": category,
            "session_id": session_id,
            "question": question,
            "expected_source": expected_source,
            "http_status": response.status_code,
            "ok": response.is_success and bool(message.strip()),
            "latency_ms": round(latency_ms, 1),
            "response_type": payload.get("tipo"),
            "state": payload.get("state"),
            "source": payload.get("source"),
            "sources": sources,
            "expected_source_found": source_match if sources else None,
            "answer": message,
            "error": payload.get("detail") if not response.is_success else None,
        }
    except Exception as exc:  # Keep every user in the report even on transport failures.
        return {
            "user": index + 1,
            "case_id": case_id,
            "category": category,
            "session_id": session_id,
            "question": question,
            "expected_source": expected_source,
            "http_status": None,
            "ok": False,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "response_type": None,
            "state": None,
            "source": None,
            "sources": [],
            "expected_source_found": False,
            "answer": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def write_report(report: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    md_path = output.with_suffix(".md")
    report["markdown_report"] = str(md_path)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = report["summary"]
    rows = [
        f"# Prueba de carga de UniMon — {report['timestamp']}",
        "",
        f"- Usuarios simulados simultáneos: **{summary['users']}**",
        f"- Solicitudes correctas con respuesta: **{summary['successes']}/{summary['users']}**",
        f"- Errores HTTP/transporte: **{summary['failures']}**",
        f"- Fuente esperada presente cuando la API expuso fuentes: **{summary['expected_source_hits']}/{summary['source_checks']}**",
        f"- Duración de la ráfaga: **{summary['wall_time_s']} s**",
        f"- Latencia p50/p95/máxima: **{summary['p50_ms']} / {summary['p95_ms']} / {summary['max_ms']} ms**",
        f"- Throughput: **{summary['requests_per_second']} solicitudes/s**",
        "",
        f"Las {summary['users']} preguntas comenzaron juntas en sesiones independientes. Cada una usó un X-Forwarded-For distinto; esto simula claves de rate limit de clientes distintos, pero no representa latencia de {summary['users']} redes físicas. La API completa sí se ejecutó con el proveedor LLM configurado.",
        "",
        "## Resultado por usuario",
        "",
        "| # | Categoría | Pregunta | HTTP | ms | Tipo | Fuente(s) RAG | Fuente esperada | Respuesta | Error |",
        "|--:|---|---|--:|--:|---|---|---|---|---|",
    ]
    for item in report["results"]:
        safe = lambda value: str(value or "").replace("|", "\\|").replace("\r", "").replace("\n", "<br>")
        rows.append(
            f"| {item['user']} | {safe(item['category'])} | {safe(item['question'])} | "
            f"{item['http_status'] or '—'} | {item['latency_ms']} | {safe(item['response_type'])} | "
            f"{safe(', '.join(item['sources']))} | {safe(item['expected_source'])} "
            f"({'sí' if item['expected_source_found'] else 'no' if item['expected_source_found'] is not None else 'sin fuente'}) | "
            f"{safe(item['answer'])} | {safe(item['error'])} |"
        )
    md_path.write_text("\n".join(rows) + "\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "load_test_100_users_20261005.json")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    if len(CASES) != 100:
        raise RuntimeError(f"La prueba debe tener 100 casos; encontró {len(CASES)}")
    normalized_questions = [" ".join(case[2].casefold().split()) for case in CASES]
    if len(set(normalized_questions)) != len(CASES):
        raise RuntimeError("La batería contiene preguntas duplicadas")

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    gate = asyncio.Event()
    limits = httpx.Limits(max_connections=120, max_keepalive_connections=100)
    timeout = httpx.Timeout(args.timeout, connect=10.0)
    async with httpx.AsyncClient(limits=limits, timeout=timeout, trust_env=False) as client:
        tasks = [
            asyncio.create_task(run_case(index, case, args.base_url, gate, client, run_id))
            for index, case in enumerate(CASES)
        ]
        await asyncio.sleep(0.05)
        started = time.perf_counter()
        gate.set()
        results = await asyncio.gather(*tasks)
        wall_time = time.perf_counter() - started

    latencies = [float(row["latency_ms"]) for row in results]
    successes = sum(row["ok"] for row in results)
    checked_sources = [row for row in results if row["expected_source_found"] is not None]
    report = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_url": args.base_url,
        "provider": "Configuración del backend; consultar /health para el nombre sin credenciales",
        "load_shape": f"{len(results)} concurrent POST /api/chat; barrier synchronized; distinct X-Forwarded-For; isolated session_id per user",
        "summary": {
            "users": len(results),
            "successes": successes,
            "failures": len(results) - successes,
            "http_429": sum(row["http_status"] == 429 for row in results),
            "http_5xx": sum(row["http_status"] is not None and row["http_status"] >= 500 for row in results),
            "expected_source_hits": sum(row["expected_source_found"] is True for row in checked_sources),
            "source_checks": len(checked_sources),
            "wall_time_s": round(wall_time, 2),
            "p50_ms": round(percentile(latencies, 50) or 0, 1),
            "p95_ms": round(percentile(latencies, 95) or 0, 1),
            "max_ms": round(max(latencies, default=0), 1),
            "requests_per_second": round(len(results) / wall_time, 2) if wall_time else 0,
        },
        "results": results,
    }
    write_report(report, args.output)
    print(json.dumps({"summary": report["summary"], "json_report": str(args.output), "markdown_report": str(args.output.with_suffix('.md'))}, ensure_ascii=False, indent=2))
    return 0 if successes == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
