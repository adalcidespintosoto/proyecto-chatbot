"""Run 50 role-consistent, everyday, document-grounded questions concurrently."""
from __future__ import annotations
import argparse,asyncio,json,time,sys
from datetime import datetime
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.load_test_chat import ROOT,percentile,run_case,write_report

# role is included as evaluation metadata; the HTTP endpoint infers it from the
# naturally worded question (the API request schema does not accept an explicit role).
CASES=[
 ("student_receipt_credentials","Estudiantes","estudiante","Soy estudiante nuevo de primer semestre. Ya hice la matrícula, ¿dónde encuentro el usuario y la clave para entrar?",["Activar Usuario y Correo institucional.pdf","GIE - ASPIRANTES NOV.2021.pptx"]),
 ("student_reset_password","Estudiantes","estudiante","Soy estudiante y olvidé la contraseña del Portal Estudiantes, ¿cómo la puedo recuperar?",["Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf"]),
 ("student_remember_user","Estudiantes","estudiante","Como estudiante no recuerdo mi usuario del portal, ¿dónde lo consulto?",["Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf"]),
 ("student_teams_login","Estudiantes","estudiante","Soy estudiante, ¿cómo entro a Teams con mi cuenta de la universidad?",["Como_acceder_MS_Teams_Estudiantes.pdf"]),
 ("student_enroll_teams_moodle","Estudiantes","estudiante","Soy estudiante y no me aparecen mis materias en Teams y Moodle, ¿cómo me uno a mis grupos?",["Matricular_grupos_teams_moodle_Estudiante.pdf"]),
 ("student_office_install","Estudiantes","estudiante","Como estudiante, ¿por dónde descargo e instalo Microsoft 365 con mi cuenta institucional?",["Descarga e instalación Ms 365.pdf"]),
 ("student_check_grades","Estudiantes","estudiante","Soy estudiante, ¿en qué parte del portal puedo mirar las notas que llevo?",["Calificaciones.pptx"]),
 ("student_vote","Estudiantes","estudiante","Soy estudiante y quiero votar en las elecciones de la universidad, ¿qué pasos sigo?",["Aplicativo Elecciones -  Cómo votar.pptx"]),
 ("student_download_certificate","Estudiantes","estudiante","Como estudiante necesito bajar un certificado, ¿cómo lo saco desde el portal?",["Certificados estudiantes_v2.pptx"]),
 ("student_request_certificate","Estudiantes","estudiante","Soy estudiante, ¿cómo solicito un certificado y luego descargo el volante o el documento?",["Descarga de certificados.pptx"]),
 ("student_intersemestral_signup","Estudiantes","estudiante","Soy estudiante, ¿cómo inscribo una materia intersemestral desde el portal?",["Inscripcion de cursos intersemestrales.pdf"]),
 ("student_old_enrollment","Estudiantes","estudiante","Soy estudiante antiguo de pregrado, ¿cómo hago la matrícula para el próximo semestre?",["2. Estudiantes Antiguos Pregrado.pptx"]),
 ("student_full_half_enrollment","Estudiantes","estudiante","Como estudiante, ¿dónde genero el informe de matrícula completa o media matrícula?",["3. Matricula Completa-Media matricula.pptx"]),
 ("student_reentry","Estudiantes","estudiante","Dejé de estudiar un tiempo y quiero volver a mi programa, ¿cómo pido el reintegro?",["6. Reintegro.pptx"]),
 ("student_transfer","Estudiantes","estudiante","Vengo de otra universidad y quiero pasarme a Unisimón, ¿cómo inicio una transferencia externa?",["4. Transferencia Externa.pptx"]),
 ("student_homologation","Estudiantes","estudiante","Soy estudiante y quiero que me reconozcan materias que ya vi, ¿cómo solicito la homologación?",["Homologaciones.pdf"]),
 ("student_practices","Estudiantes","estudiante","Soy estudiante y ya voy a empezar prácticas, ¿qué debo hacer para cargar los requisitos?",["Gestión Prácticas - Estudiantes.pdf"]),
 ("student_update_data","Estudiantes","estudiante","Como estudiante, ¿cómo actualizo mis datos personales en el sistema?",["Instrucciones Actualización Datos Estudiantes.pdf"]),
 ("student_mobility","Estudiantes","estudiante","Soy estudiante y quiero hacer movilidad académica, ¿por dónde empiezo el trámite?",["Movilidad Académica - Estudiantes.pdf"]),
 ("student_online_payment","Estudiantes","estudiante","Soy estudiante, ¿cómo pago la matrícula por internet desde el portal?",["Pagos en linea - Estudiantes.pdf"]),
 ("student_credit_request","Estudiantes","estudiante","Como estudiante necesito pedir un crédito para pagar, ¿cómo radico la solicitud?",["Solicitud de crédito.pptx"]),
 ("student_moodle_courses","Estudiantes","estudiante","Como estudiante, ¿cómo encuentro en Moodle los grupos de mis asignaturas?",["Estudiantes_Matricular grupos en teams ymoodle.pdf"]),
 ("student_new_enrollment","Estudiantes","estudiante","Soy estudiante nuevo y ya terminé el formulario, ¿qué me falta para oficializar la matrícula?",["GIE - ASPIRANTES NOV.2021.pptx"]),
 ("student_evaluate_teacher","Estudiantes","estudiante","Como estudiante, ¿dónde hago la evaluación de mis profesores?",["Evaluacion Profesoral - Estudiante.pdf"]),
 ("faculty_enter_grades","Docentes","profesor","Soy docente, ¿por dónde ingreso las calificaciones de mis estudiantes en el portal?",["Calificaciones.pdf"]),
 ("faculty_save_draft","Docentes","profesor","Soy profesor y quiero dejar las notas guardadas como borrador antes de enviarlas, ¿qué opción uso?",["Calificaciones.pdf"]),
 ("faculty_finalize_grades","Docente","profesor","Como docente ya revisé las notas, ¿qué botón las envía para que queden finalizadas?",["Calificaciones.pdf"]),
 ("faculty_postgraduate_grade","Docentes","profesor","Soy docente de posgrado, ¿cómo registro la nota definitiva de un curso?",["Calificaciones Posgrados.pdf"]),
 ("faculty_teams_courses","Docentes","profesor","Soy profesor, ¿cómo conecto mis cursos de Moodle con los equipos de Teams?",["Profesores_Integración teams y moodle.pdf"]),
 ("faculty_record_class","Docentes","profesor","Soy docente y quiero grabar una clase en Teams para compartirla después, ¿cómo lo hago?",["Grabar un clase en Teams y compartir en Stream.pdf"]),
 ("faculty_schedule_meeting","Docentes","profesor","Soy profesor, ¿cómo creo una reunión de Teams que no pertenezca a uno de mis grupos?",["Crear reuniones No asociadas a grupos.pdf"]),
 ("faculty_meeting_participants","Docentes","profesor","Como docente, ¿cómo agrego o quito participantes de una reunión de Teams?",["Ajustes participantes reuniones  Ms Teams.pdf"]),
 ("faculty_fill_pac","Docentes","profesor","Soy profesor, ¿cómo diligencio mi PAC en el portal?",["Diligenciamiento de PAC (Profesores).pdf"]),
 ("faculty_configure_evaluations","Docentes","profesor","Como docente, ¿dónde configuro las evaluaciones del curso?",["Configuracion de Evaluaciones.pptx"]),
 ("faculty_auto_evaluation","Docentes","profesor","Soy profesor y debo hacer la autoevaluación por grupos, ¿en qué módulo está?",["Autoevaluacion por Grupos - Funcionarios.pdf"]),
 ("faculty_assignment_list","Docentes","profesor","Como profesor, ¿dónde consulto mi asignación académica y los cursos a cargo?",["Reporte - Asignacion Académica.pdf"]),
 ("faculty_attendance_qr","Docentes","profesor","Soy docente, ¿cómo registro la asistencia de los estudiantes con el código QR?",["Instructivo - Reporte de asistencias QR.pdf"]),
 ("faculty_add_teams_members","Docentes","profesor","Como profesor, ¿cómo agrego a un estudiante a mi equipo de Teams?",["Agregar_miembros_Grupos_MS_Teams.pdf"]),
 ("admin_new_student_report","Administrativos","administrativo","Trabajo en admisiones, ¿cómo genero el informe de estudiantes nuevos de pregrado y qué filtros pide?",["1. Estudiantes Nuevos Pregrado.pptx"]),
 ("admin_old_student_report","Administrativos","administrativo","Soy funcionario de registro, ¿qué informe uso para sacar el reporte de estudiantes antiguos de pregrado?",["2. Estudiantes Antiguos Pregrado.pptx"]),
 ("admin_full_half_report","Administrativos","administrativo","En el área administrativa, ¿cómo genero el reporte de matrícula completa y media matrícula?",["3. Matricula Completa-Media matricula.pptx"]),
 ("admin_reentry_report","Administrativos","administrativo","Soy funcionario y necesito sacar el reporte de reintegros, ¿qué opción selecciono en SIAAF?",["6. Reintegro.pptx"]),
 ("admin_ser_pilo_report","Administrativos","administrativo","Trabajo en registro y necesito el informe de Ser Pilo Paga, ¿cómo lo genero?",["5. Ser Pilo Paga.pptx"]),
 ("admin_absence_causes","Administrativos","administrativo","Soy funcionario académico, ¿cómo registro la causa de ausencia o deserción de un estudiante?",["Ingreso de Causas de Desertores y Ausentes.pdf"]),
 ("admin_supletorio_authorization","Administrativos","administrativo","En mi área debemos autorizar un supletorio, ¿cómo se registra la autorización?",["Autorización de Supletorios.pdf"]),
 ("admin_credit_approval","Administrativos","administrativo","Soy funcionario y debo aprobar una solicitud de crédito estudiantil, ¿qué pasos sigo?",["Aprobacion Solicitudes de credito.pptx"]),
 ("admin_invoice_detail","Administrativos","administrativo","En finanzas, ¿dónde consulto los anexos y el detalle de una factura?",["Detalle factura (Anexos).pptx"]),
 ("admin_bank_accounts","Administrativos","administrativo","Soy funcionario de tesorería, ¿dónde reviso los bancos y cuentas disponibles para pagos?",["Bancos y cuentas_v1_20211007.pdf"]),
 ("admin_payment_verification","Administrativos","administrativo","Trabajo en cartera, ¿cómo verifico si un pago ya quedó aplicado en el sistema?",["Instructivo Verificación pagos V2.pdf"]),
 ("admin_inscriptions_module","Administrativos","administrativo","Soy funcionario de admisiones, ¿qué opciones tengo en el módulo de gestión de inscripciones?",["Gestión de inscripciones.pdf"]),
]

async def main():
    ap=argparse.ArgumentParser();ap.add_argument("--base-url",default="http://127.0.0.1:8000")
    ap.add_argument("--output",type=Path,default=ROOT/"reports/quality_50_20261006.json")
    ap.add_argument("--concurrency",type=int,default=50,help="Maximum sessions released together (1-50).")
    ap.add_argument("--timeout",type=float,default=240);args=ap.parse_args()
    if not 1 <= args.concurrency <= 50: ap.error("--concurrency debe estar entre 1 y 50")
    if len(CASES)!=50 or len({c[0] for c in CASES})!=50 or len({c[3].casefold() for c in CASES})!=50: raise RuntimeError("Se requieren 50 preguntas distintas")
    run_id=datetime.now().strftime("q50-%Y%m%d-%H%M%S");results=[];started=time.perf_counter()
    limits=httpx.Limits(max_connections=args.concurrency,max_keepalive_connections=min(args.concurrency,20))
    async with httpx.AsyncClient(limits=limits,timeout=httpx.Timeout(args.timeout,connect=10),trust_env=False) as client:
        for base in range(0,50,args.concurrency):
            gate=asyncio.Event()
            async def call(j,case):
                case_id,cat,role,q,sources=case
                row=await run_case(base+j, (case_id,cat,q,sources[0]),args.base_url,gate,client,run_id)
                row["expected_sources"]=sources;row["intended_role"]=role
                return row
            tasks=[asyncio.create_task(call(j,c)) for j,c in enumerate(CASES[base:base+args.concurrency])]
            await asyncio.sleep(.05);wave=time.perf_counter();gate.set();batch=await asyncio.gather(*tasks);results.extend(batch)
            print(json.dumps({"batch":base//10+1,"completed":len(results),"success":sum(r['ok'] for r in batch),"seconds":round(time.perf_counter()-wave,1)},ensure_ascii=False),flush=True)
    wall=time.perf_counter()-started;lat=[r['latency_ms'] for r in results];checked=[r for r in results if r.get('expected_source_found') is not None]
    # Multi-document onboarding item passes if all expected sources were reported.
    for row in results:
        if len(row['expected_sources'])>1:
            observed=' '.join(row.get('sources') or []).casefold()
            row['expected_source_found']=all(src.casefold() in observed for src in row['expected_sources']) if row.get('sources') else None
    report={"timestamp":datetime.now().astimezone().isoformat(timespec='seconds'),"base_url":args.base_url,
      "load_shape":f"independent concurrent sessions in groups of {args.concurrency}","summary":{
       "users":50,"successes":sum(r['ok'] for r in results),"failures":sum(not r['ok'] for r in results),
       "http_429":sum(r['http_status']==429 for r in results),"http_5xx":sum(r['http_status'] is not None and r['http_status']>=500 for r in results),
       "expected_source_hits":sum(r['expected_source_found'] is True for r in results if r['expected_source_found'] is not None),
       "source_checks":sum(r['expected_source_found'] is not None for r in results),"wall_time_s":round(wall,2),
       "p50_ms":round(percentile(lat,50) or 0,1),"p95_ms":round(percentile(lat,95) or 0,1),"max_ms":round(max(lat,default=0),1),
       "requests_per_second":round(50/wall,2) if wall else 0},"results":results}
    write_report(report,args.output)
    md=args.output.with_suffix('.md');text=md.read_text(encoding='utf8').replace("Usuarios simulados simultáneos: **50**",f"Sesiones probadas: **50** (grupos de hasta {args.concurrency} concurrentes)").replace("Las 50 preguntas comenzaron juntas en sesiones independientes.",f"Las 50 preguntas se ejecutaron en grupos de hasta {args.concurrency} sesiones independientes concurrentes.")
    md.write_text(text,encoding='utf8')
    print(json.dumps({"summary":report['summary'],"json":str(args.output),"markdown":str(md)},ensure_ascii=False,indent=2))
if __name__=='__main__': asyncio.run(main())
