# Calibración del reranker: prueba de 50 preguntas

**Ejecución:** 2026-10-06T09:48:26-05:00 — carga: 10 sequential waves of 10 independent concurrent sessions

**Disponibilidad y latencia:** 50/50 respuestas HTTP exitosas; 0 fallos; p50 14.50s, p95 21.72s, máximo 21.75s.
**Evaluación estricta:** correctas: 25, parciales: 16, incorrectas: 2, no verificables: 7 (de 50 preguntas).
**Recuperación de fuentes esperadas:** candidatos 49/50, reranking 48/50, contexto final 39/50.

## Qué muestran los umbrales

`Precisión retenida` es la proporción de respuestas juzgadas correctas entre las que el umbral dejaría pasar. `Débiles rechazadas` suma parciales, incorrectas y no verificables; `correctas rechazadas` muestra el costo de abstenerse.

| Score mínimo | Pasa | Correctas | Débiles que pasan | Precisión retenida | Correctas rechazadas | Débiles rechazadas |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 50 | 25 | 25 | 50.0% | 0 | 0 |
| 2 | 47 | 25 | 22 | 53.2% | 0 | 3 |
| 3 | 46 | 24 | 22 | 52.2% | 1 | 3 |
| 4 | 44 | 24 | 20 | 54.5% | 1 | 5 |
| 5 | 40 | 23 | 17 | 57.5% | 2 | 8 |
| 6 | 37 | 21 | 16 | 56.8% | 4 | 9 |
| 7 | 34 | 20 | 14 | 58.8% | 5 | 11 |
| 8 | 29 | 18 | 11 | 62.1% | 7 | 14 |
| 9 | 25 | 16 | 9 | 64.0% | 9 | 16 |
| 10 | 16 | 9 | 7 | 56.2% | 16 | 18 |
| 11 | 10 | 7 | 3 | 70.0% | 18 | 22 |
| 12 | 8 | 5 | 3 | 62.5% | 20 | 22 |

## Decisión de calibración

No se activa un rechazo global por score en esta muestra. Con score mínimo 9, la precisión de lo retenido es 64%, pero solo pasarían 25/50 casos: 9 respuestas correctas se rechazarían y 9 débiles aún pasarían. El score bajo sí detecta algunos casos problemáticos —incluida la consulta de reintegros—, pero hay consultas correctas con score bajo y casos no verificables con score alto.

El score del cross-encoder no es una probabilidad calibrada: además, el score trazado es el score final ajustado por heurísticas de la aplicación. Un umbral universal convertiría una señal útil en una regla de abstención con falsos rechazos. La opción segura es conservarlo como señal diagnóstica y calibrar una política conjunta con relevancia del título/acción, presencia de fuentes que cubran la intención y cobertura de los pasos solicitados, usando consultas etiquetadas separadas para calibración y validación.

## Casos individuales

| # | Score máx. | Veredicto | Fuente esperada en contexto final | Pregunta | Motivo del juez |
|---:|---:|---|:---:|---|---|
| 1 | 9.483 | correct | Sí | Soy estudiante nuevo de primer semestre. Ya hice la matrícula, ¿dónde encuentro el usuario y la clave para entrar? | La evidencia indica que el usuario y la contraseña están al final del recibo de matrícula, que se genera al finalizar el proceso. |
| 2 | 14.218 | incorrect | Sí | Soy estudiante y olvidé la contraseña del Portal Estudiantes, ¿cómo la puedo recuperar? | Incluye datos y pasos concretos no respaldados por los fragmentos, como la contraseña temporal «unisimon», la opción «Olvidé mi Usuario / Contraseña» y el enlace válido por 24 horas. |
| 3 | 8.686 | no_verificable | No | Como estudiante no recuerdo mi usuario del portal, ¿dónde lo consulto? | Los fragmentos aportados no muestran dónde consultar el usuario ni respaldan la ruta de recuperación sugerida. |
| 4 | 8.118 | no_verificable | No | Soy estudiante, ¿cómo entro a Teams con mi cuenta de la universidad? | La evidencia trata de matricular grupos en Teams, no de iniciar sesión; los pasos generales sugeridos no se pueden confirmar con estos documentos. |
| 5 | 10.027 | partial | Sí | Soy estudiante y no me aparecen mis materias en Teams y Moodle, ¿cómo me uno a mis grupos? | Indica ingresar al portal y seleccionar Calificaciones, y explica el caso de Moodle «No Activo»; la evidencia aportada no confirma los pasos para matricularse en Teams. |
| 6 | 10.938 | no_verificable | Sí | Como estudiante, ¿por dónde descargo e instalo Microsoft 365 con mi cuenta institucional? | La guía es para funcionarios y no permite confirmar la ruta ni la disponibilidad de Microsoft 365 para estudiantes; la respuesta reconoce esa limitación. |
| 7 | 3.160 | partial | No | Soy estudiante, ¿en qué parte del portal puedo mirar las notas que llevo? | Da la ruta hasta el Portal de Estudiantes, pero la evidencia no indica dónde consultar las notas y la respuesta no resuelve esa parte. |
| 8 | 7.404 | partial | Sí | Soy estudiante y quiero votar en las elecciones de la universidad, ¿qué pasos sigo? | Los pasos de selección y confirmación del voto están respaldados, pero la URL del portal de elecciones no aparece en la evidencia. |
| 9 | 7.994 | partial | Sí | Como estudiante necesito bajar un certificado, ¿cómo lo saco desde el portal? | La evidencia respalda el acceso al portal y la descarga mediante el ícono del certificado, pero no confirma todos los pasos concretos de la ruta que describe. |
| 10 | 5.970 | correct | Sí | Soy estudiante, ¿cómo solicito un certificado y luego descargo el volante o el documento? | La guía estudiantil respalda generar la solicitud eligiendo programa y período, y descargar luego el certificado con el ícono correspondiente; la respuesta distingue ese trámite del volante de otros procesos. |
| 11 | 9.521 | correct | Sí | Soy estudiante, ¿cómo inscribo una materia intersemestral desde el portal? | Los pasos para acceder, elegir cursos, inscribir y confirmar, además de descargar el informe y el volante tras autorización, están respaldados. |
| 12 | 10.214 | partial | Sí | Soy estudiante antiguo de pregrado, ¿cómo hago la matrícula para el próximo semestre? | Aclara que la guía disponible trata de generar un informe y no de matricularse, pero los pasos ofrecidos no responden cómo hacer la matrícula solicitada. |
| 13 | 12.346 | partial | Sí | Como estudiante, ¿dónde genero el informe de matrícula completa o media matrícula? | Explica cómo generar el informe con sus filtros, pero la guía no confirma que el módulo Rectoría esté habilitado para estudiantes; la ruta queda condicionada y no resuelve plenamente dónde generarlo. |
| 14 | 3.511 | no_verificable | No | Dejé de estudiar un tiempo y quiero volver a mi programa, ¿cómo pido el reintegro? | La evidencia no describe el trámite de reintegro. La recomendación de consultar a la Dirección del Programa tampoco está respaldada por los fragmentos. |
| 15 | 4.282 | partial | Sí | Vengo de otra universidad y quiero pasarme a Unisimón, ¿cómo inicio una transferencia externa? | Distingue correctamente el informe administrativo de una solicitud de ingreso, pero esos pasos no contestan cómo iniciar la transferencia; la recomendación de contactar a Admisiones no está documentada. |
| 16 | 1.346 | partial | No | Soy estudiante y quiero que me reconozcan materias que ya vi, ¿cómo solicito la homologación? | La evidencia describe acciones de personal en la trazabilidad y una etapa de aceptación estudiantil, no cómo solicitar homologación. Reunir certificados y contenidos programáticos y consultar oficinas se recomienda sin respaldo documental. |
| 17 | 9.300 | correct | Sí | Soy estudiante y ya voy a empezar prácticas, ¿qué debo hacer para cargar los requisitos? | El acceso, la carga de archivos, la revisión de estados y observaciones y la condición de aprobación de requisitos obligatorios coinciden con la guía. |
| 18 | 10.592 | correct | Sí | Como estudiante, ¿cómo actualizo mis datos personales en el sistema? | Los pasos y advertencias sobre navegador, campos obligatorios, guardado, datos inhabilitados y contacto de estudiantes antiguos están respaldados. |
| 19 | 8.979 | correct | Sí | Soy estudiante y quiero hacer movilidad académica, ¿por dónde empiezo el trámite? | Indica el acceso al portal, la entrada a Movilidad Académica y reconoce que no se detallan los pasos posteriores; coincide con la evidencia. |
| 20 | 7.482 | partial | Sí | Soy estudiante, ¿cómo pago la matrícula por internet desde el portal? | La evidencia respalda descargar el comprobante al finalizar, pero no acredita el paso genérico de realizar el pago desde el portal ni explica cómo iniciarlo. |
| 21 | 6.527 | partial | Sí | Como estudiante necesito pedir un crédito para pagar, ¿cómo radico la solicitud? | La mayoría de los pasos para solicitar el crédito están respaldados, pero la evidencia no confirma que se pueda descargar el formulario ni el paso adicional de cuota inicial si queda preaprobada. |
| 22 | 11.711 | correct | Sí | Como estudiante, ¿cómo encuentro en Moodle los grupos de mis asignaturas? | Describe los pasos y la espera aproximada de 3 minutos; también explica qué hacer si el grupo figura como «No Activo», de acuerdo con el instructivo. |
| 23 | 4.447 | incorrect | No | Soy estudiante nuevo y ya terminé el formulario, ¿qué me falta para oficializar la matrícula? | Responde sobre cursos intersemestrales, aunque la pregunta trata de un estudiante nuevo que terminó el formulario. La evidencia disponible no acredita que su trámite sea intersemestral. |
| 24 | 12.144 | correct | Sí | Como estudiante, ¿dónde hago la evaluación de mis profesores? | Identifica SIAAF Web y explica cómo comenzar y guardar la evaluación, conforme al instructivo. |
| 25 | 14.005 | correct | Sí | Soy docente, ¿por dónde ingreso las calificaciones de mis estudiantes en el portal? | Indica la ruta documentada para llegar al registro de calificaciones y seleccionar el programa académico. |
| 26 | 2.947 | correct | Sí | Soy profesor y quiero dejar las notas guardadas como borrador antes de enviarlas, ¿qué opción uso? | Distingue correctamente «Guardar Borrador» para conservar temporalmente las notas y «Finalizar» para enviarlas. |
| 27 | 5.308 | correct | Sí | Como docente ya revisé las notas, ¿qué botón las envía para que queden finalizadas? | Señala que «Finalizar» envía las notas y que el sistema vuelve a la pantalla de asignaturas. |
| 28 | 9.231 | partial | Sí | Soy docente de posgrado, ¿cómo registro la nota definitiva de un curso? | Los pasos de ingreso y envío están respaldados, pero la escala de 0.0 a 5.0 no aparece en la evidencia aportada. |
| 29 | 11.546 | correct | Sí | Soy profesor, ¿cómo conecto mis cursos de Moodle con los equipos de Teams? | Describe la ruta de integración y las opciones documentadas para asignar o matricular participantes y actualizar el curso en cada plataforma. |
| 30 | 13.527 | partial | Sí | Soy docente y quiero grabar una clase en Teams para compartirla después, ¿cómo lo hago? | Explica cómo cargar y compartir la grabación en Stream, pero no indica cómo iniciar ni descargar la grabación desde Teams; por ello no completa el procedimiento pedido. |
| 31 | 9.275 | correct | Sí | Soy profesor, ¿cómo creo una reunión de Teams que no pertenezca a uno de mis grupos? | Indica diligenciar los campos, agregar asistentes y guardar; también refleja las opciones documentadas para unirse o cancelar. |
| 32 | 9.518 | correct | Sí | Como docente, ¿cómo agrego o quito participantes de una reunión de Teams? | Los botones para agregar y eliminar participantes están respaldados; también lo está el cambio entre Asistente y Moderador y sus permisos. |
| 33 | 4.317 | correct | Sí | Soy profesor, ¿cómo diligencio mi PAC en el portal? | La ruta por Portales al Portal Profesores y Administrativos, el módulo Programa Analítico, los filtros y el inicio del proceso coinciden con la guía. |
| 34 | 10.761 | correct | Sí | Como docente, ¿dónde configuro las evaluaciones del curso? | El módulo Evaluaciones y las secciones Parametrización y Ofertas, junto con sus funciones descritas, están respaldados por la evidencia. |
| 35 | 9.066 | correct | Sí | Soy profesor y debo hacer la autoevaluación por grupos, ¿en qué módulo está? | La guía indica seleccionar Autoevaluación por Grupo, consultar las asignaturas pendientes y pulsar Comenzar. |
| 36 | 7.135 | correct | Sí | Como profesor, ¿dónde consulto mi asignación académica y los cursos a cargo? | La ruta Reporte → Asignación Académica y el filtro Función están documentados. Aclara que no se especifica una ruta individual para los cursos a cargo. |
| 37 | 6.453 | no_verificable | No | Soy docente, ¿cómo registro la asistencia de los estudiantes con el código QR? | La evidencia describe el QR de ingreso a la institución, no el registro de asistencia a clase. La respuesta distingue ambos usos, pero los fragmentos no permiten confirmar el procedimiento docente solicitado. |
| 38 | 7.155 | correct | No | Como profesor, ¿cómo agrego a un estudiante a mi equipo de Teams? | La integración permite consultar participantes y matricular a un estudiante individual o actualizar todo el curso en Teams. |
| 39 | 12.355 | correct | Sí | Trabajo en admisiones, ¿cómo genero el informe de estudiantes nuevos de pregrado y qué filtros pide? | La ruta por Portales, el módulo Rectoría, el informe y los filtros Año, Periodo y Fecha con Generar coinciden con la guía. |
| 40 | 9.412 | correct | Sí | Soy funcionario de registro, ¿qué informe uso para sacar el reporte de estudiantes antiguos de pregrado? | Identifica el informe Estudiantes Antiguos Pregrado en Rectoría y los filtros y la generación de PDF indicados en la evidencia. |
| 41 | 8.173 | correct | Sí | En el área administrativa, ¿cómo genero el reporte de matrícula completa y media matrícula? | Indica la ruta, el informe, los filtros y la generación en PDF, conforme al instructivo. |
| 42 | 1.019 | no_verificable | No | Soy funcionario y necesito sacar el reporte de reintegros, ¿qué opción selecciono en SIAAF? | Los fragmentos citados no incluyen el instructivo esperado sobre reintegros, por lo que no permiten confirmar la opción; la respuesta reconoce esa limitación. |
| 43 | 9.016 | partial | Sí | Trabajo en registro y necesito el informe de Ser Pilo Paga, ¿cómo lo genero? | La selección de Rectoría, informe y filtros está respaldada, pero omite el paso documentado de seleccionar Portales > Portal Profesores y Administrativos para acceder. |
| 44 | 6.528 | correct | Sí | Soy funcionario académico, ¿cómo registro la causa de ausencia o deserción de un estudiante? | Los filtros, la búsqueda, la selección de causa y la aceptación coinciden con el instructivo. |
| 45 | 12.416 | correct | Sí | En mi área debemos autorizar un supletorio, ¿cómo se registra la autorización? | Los pasos y la explicación del estado Pendiente coinciden con la evidencia. El rol inferido es general, pero no altera el procedimiento solicitado. |
| 46 | 5.572 | partial | Sí | Soy funcionario y debo aprobar una solicitud de crédito estudiantil, ¿qué pasos sigo? | La guía respalda el acceso, la preaprobación, el rechazo con motivo y la confirmación; no respalda consultar/imprimir el formulario ni editar datos, y la respuesta presenta esos detalles como documentados. |
| 47 | 12.102 | correct | Sí | En finanzas, ¿dónde consulto los anexos y el detalle de una factura? | La ruta por Portales, módulo App, consulta por número y botón Imprimir Anexo concuerdan con la evidencia; el detalle de los primeros pasos está respaldado. |
| 48 | 1.769 | partial | Sí | Soy funcionario de tesorería, ¿dónde reviso los bancos y cuentas disponibles para pagos? | Explica dónde consultar los bancos activos, pero la pregunta también pide cuentas disponibles para pagos y la evidencia no permite confirmar esa parte; la respuesta lo aclara. |
| 49 | 4.222 | no_verificable | No | Trabajo en cartera, ¿cómo verifico si un pago ya quedó aplicado en el sistema? | La evidencia permite consultar el estado de links de Paymentez, pero no verificar si un pago quedó aplicado en cartera; la respuesta distingue explícitamente ambos conceptos. |
| 50 | 10.022 | partial | No | Soy funcionario de admisiones, ¿qué opciones tengo en el módulo de gestión de inscripciones? | Enumera funciones del anexo de actualizaciones, pero la pregunta es sobre gestión de inscripciones de admisiones y la evidencia citada trata principalmente inscripción para grados; no confirma que sean las opciones de ese módulo. |

## Archivos de evidencia

- Respuestas completas: `quality_50_20261006_intent_guard_judged.md`.
- Evaluación JSON: `quality_50_20261006_intent_guard_judged.json`.
- Trazas de recuperación y chunks: `quality_50_20261006_trace_intent_guard.json`.
- Conteo del Golden Cache tras promover solo respuestas correctas con evidencia final: 81 casos únicos (antes: 76); 22 respuestas elegibles guardadas/actualizadas.
