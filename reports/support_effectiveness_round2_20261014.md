# Segunda ronda de efectividad — soporte TI — 14/10/2026

## Resultado

Se enviaron 20 preguntas nuevas al chatbot con `gpt-6-luna`, usando sesiones aisladas y sin registrar los resultados como feedback ni Golden Cache. Se revisó cada respuesta contra los documentos citados y los manuales pertinentes.

- **13 correctas (65%)**
- **5 parciales (25%)**
- **2 incorrectas (10%)**
- **0 errores de ejecución**
- Latencia media: **7,03 s**; P95: **14,54 s**

La ronda anterior dio 80% sin perfil sobre otra batería. Esta nueva muestra no confirma ese nivel: muestra que la efectividad cae con otras formulaciones y temas. No son mediciones estadísticas de todas las conversaciones, pero sí revelan fallos concretos que requieren corrección.

## Revisión por pregunta

| # | Pregunta | Veredicto | Hallazgo |
| ---: | --- | --- | --- |
| 1 | ¿Dónde encuentro credenciales para entrar por primera vez? | Correcta | Ubica usuario y contraseña al final del recibo de matrícula. |
| 2 | ¿Puedo recuperar la clave olvidada de Kactus desde el portal? | Parcial | La documentación describe cambiar una clave con acceso, pero no recuperar una clave olvidada. |
| 3 | ¿Cómo se solicita crear usuario para alguien nuevo? | Correcta | Distingue cuentas de Kactus/ERP de correo y red, y limita lo que puede confirmar. |
| 4 | ¿Quién pide modificar permisos por cambio de funciones? | Correcta | Indica que lo solicita el jefe inmediato y qué información incluir. |
| 5 | No aparece la materia en Teams, ¿cómo me agregan? | Correcta | Indica la autogestión desde el Portal de Estudiantes y el estado de matrícula en Teams. |
| 6 | Como docente, ¿cómo agrego a un estudiante al equipo? | **Incorrecta** | El manual de Teams sí documenta Equipos → Más opciones → Agregar miembro → buscar usuario → Enviar solicitud, pero el RAG no lo recuperó y respondió que no había guía. |
| 7 | ¿Dónde queda guardada la grabación de Teams? | Correcta | Distingue chat/calendario, OneDrive y SharePoint como comprobaciones generales, y aclara que la ubicación institucional no está confirmada. |
| 8 | ¿Cómo comparto la grabación de una clase? | Correcta | Da la ruta de carga a Stream y asignación de permisos al grupo. |
| 9 | ¿Cómo creo reunión con una persona fuera de un curso o grupo? | Parcial | Encuentra Calendario → Nueva reunión, pero no termina de orientar el envío de invitación. |
| 10 | En iPad no me oyen en Teams, ¿qué reviso? | Correcta | Da comprobaciones generales de micrófono y permisos, distinguiéndolas de lo documentado. |
| 11 | ¿Cómo matriculo mis grupos de Moodle? | Correcta | Da la ruta del Portal de Estudiantes, el botón y el significado de “No Activo”. |
| 12 | ¿Dónde consulto las notas que me puso el profesor? | **Incorrecta** | Se clasificó como una pregunta sobre MIRO y no respondió la consulta. |
| 13 | ¿Cómo descargo un certificado estudiantil? | Correcta | Indica módulo Certificados, selección y generación. |
| 14 | ¿Cómo saco el PDF de estudiantes nuevos con fecha y período? | Parcial | El RAG recuperó el instructivo, pero la respuesta omitió filtros de año, período y fecha, y el botón Generar que aparecen en la guía. |
| 15 | ¿Quién tramita instalar un programa en mi portátil? | Correcta | Señala al jefe de dependencia y la Mesa de Servicio. |
| 16 | ¿Qué envío para solicitar VPN? | Parcial | No encontró los requisitos del procedimiento de acceso remoto y se quedó en una orientación general. |
| 17 | ¿Cómo solicito restaurar un archivo borrado? | Correcta | Incluye el correo, datos requeridos y condición de aprobación del líder de proceso. |
| 18 | ¿A quién reporto un enlace que pide validar la contraseña? | Parcial | Da consejos seguros y canal general, pero omite el Oficial de Seguridad de la Información indicado en el procedimiento. |
| 19 | Windows alertó de malware, ¿lo limpio yo? | Correcta | Remite la evaluación y cuarentena a Seguridad Informática/TI; no asigna acciones reservadas al usuario. |
| 20 | Kactus cambió de versión y dejó de funcionar, ¿cómo lo reporto? | Correcta | Recomienda informar al técnico ERP y aportar versión, función afectada y error. |

Las respuestas completas, fuentes y latencias están en [support_effectiveness_round2_20261014.json](support_effectiveness_round2_20261014.json). La batería que se ejecutó está en [support_effectiveness_round2_20261014.json](../tests/fixtures/support_effectiveness_round2_20261014.json) dentro de `tests/fixtures`.

## Prioridades que salen de esta ronda

1. Corregir la clasificación de “notas/calificaciones” para que no se convierta en MIRO y recuperar el procedimiento adecuado según estudiante o profesor.
2. Revisar recuperación de miembros de grupos de Teams: el documento existe e incluso apareció en resultados de la consulta, pero la selección final no conservó sus pasos.
3. Mejorar la cobertura de preguntas sobre reportes: en “Estudiantes Nuevos Pregrado” el chunk relevante no aportó los filtros y la generación PDF a la respuesta, aunque la guía los detalla.
4. Mejorar la combinación de guía y política en VPN y reportes de phishing: existen documentos pertinentes, pero la respuesta dejó fuera los datos y responsables específicos.
5. Completar las instrucciones de reuniones de Teams con las acciones finales de guardar/enviar.

El evaluador no insertó resultados en Golden Cache. El caché actual se alimenta de interacciones confirmadas con feedback positivo; esta ejecución mide respuestas automáticamente y no equivale a una confirmación del usuario final. Guardar respuestas parciales o no verificadas como casos resueltos podría propagar errores.
