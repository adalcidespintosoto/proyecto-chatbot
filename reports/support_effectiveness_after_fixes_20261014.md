# Efectividad de soporte TI después de las correcciones — 14/10/2026

## Alcance y criterio

Se repitieron las mismas 20 preguntas de soporte TI de la muestra anterior, una vez sin perfil y otra vez con perfiles de estudiante, docente o administrativo. Cada respuesta se obtuvo del chatbot con el LLM configurado (`gpt-6-luna`) y se revisó manualmente contra la solicitud y los documentos disponibles. **Correcta** significa que ofrece una ruta útil, segura y suficientemente sustentada; **parcial** significa que ayuda, pero deja una parte necesaria sin resolver; **incorrecta** significa que indica una ruta errónea o insegura. No se contó una respuesta parcial como acierto.

| Muestra | Antes | Después | Cambio |
| --- | ---: | ---: | ---: |
| 20 preguntas sin perfil | 12 correctas, 6 parciales, 2 incorrectas (60%) | **16 correctas, 4 parciales, 0 incorrectas (80%)** | +20 puntos |
| Las mismas 20 con perfil | 13 correctas, 4 parciales, 3 incorrectas (65%) | **17 correctas, 3 parciales, 0 incorrectas (85%)** | +20 puntos |

No hubo errores de ejecución en las 40 solicitudes posteriores a los cambios. La latencia media fue 9,73 s sin perfil y 8,98 s con perfil; el percentil 95 observado fue 17,49 s y 14,49 s, respectivamente. Son muestras pequeñas, repetidas y relacionadas entre sí. Estos porcentajes describen esta batería, no garantizan 80% en consultas nuevas ni en todos los documentos.

## Revisión por pregunta

| # | Tema | Sin perfil | Con perfil | Observación |
| ---: | --- | --- | --- | --- |
| 1 | Acceso al correo | Parcial | Correcta | Sin perfil, el bot da comprobaciones seguras, pero pide el servicio y el perfil antes de indicar la recuperación concreta. |
| 2 | Inicio en Teams | Correcta | Correcta | Orienta según la cuenta institucional. |
| 3 | Contraseña olvidada | Correcta | Parcial | Sin perfil ofrece rutas condicionadas; con perfil aún pide precisar la cuenta. |
| 4 | Usuario bloqueado | Parcial | Parcial | Falta identificar la plataforma para dar un desbloqueo concreto. |
| 5 | Acceso tras cambiar clave | Parcial | Parcial | Requiere servicio y error exacto; el diagnóstico inicial es genérico. |
| 6 | Wi-Fi | Correcta | Correcta | Comprobaciones de primer nivel. |
| 7 | Conexión sin navegación | Correcta | Correcta | Distingue red local, página y dispositivo. |
| 8 | Punto de red | Correcta | Correcta | Indica reporte a Mesa de Ayuda. |
| 9 | Equipo que no enciende | Correcta | Correcta | Comprobaciones seguras y escalamiento. |
| 10 | Mouse y teclado | Parcial | Correcta | Sin perfil usa canales generales y no precisa la radicación en Mesa de Ayuda. |
| 11 | Equipo lento | Correcta | Correcta | Comprobaciones de usuario y soporte. |
| 12 | Teams no abre | Correcta | Correcta | Acceso alternativo y diagnóstico básico. |
| 13 | Audio en Teams | Correcta | Correcta | Ya no presupone que el usuario tiene un iPad por el título de una guía. |
| 14 | Micrófono/cámara | Correcta | Correcta | Pasos comunes de primer nivel. |
| 15 | Instalación de software | Correcta | Correcta | Respeta la solicitud institucional por el jefe de dependencia y Mesa de Servicio. |
| 16 | VPN | Correcta | Correcta | Orienta hacia TI con los datos necesarios. |
| 17 | Correo sospechoso | Correcta | Correcta | Evita abrir el enlace y remite a Seguridad de la Información. |
| 18 | Sospecha de virus | Correcta | Correcta | No asigna al usuario tareas de análisis o cuarentena reservadas a Seguridad Informática. |
| 19 | Restauración de archivo | Correcta | Correcta | Incluye el correo institucional respaldado por el procedimiento de copias. |
| 20 | Atención presencial | Correcta | Correcta | Indica radicación y posible visita de soporte. |

Los dictámenes y el texto íntegro de cada respuesta están en `support_effectiveness_unscoped_improved_20261014.json` y `support_effectiveness_roles_improved_20261014.json`.

## Cambios que explican la mejora

1. Se detectan consultas de seguridad antes del enrutamiento de hardware. El RAG prioriza el procedimiento de seguridad y el LLM recibe la limitación de no pedir al usuario análisis, desinfección o cuarentena.
2. La selección de contexto reserva evidencia de contacto cuando la pregunta pide solicitar, radicar o reportar. Así llegó al prompt la página con el canal para restauración de copias, que antes se perdía entre candidatos.
3. El perfil declarado al comienzo de la pregunta ya no sesga los términos usados para escoger títulos, fragmentos y presupuesto de contexto. Se mantiene como información de la persona para la respuesta.
4. Se redactan correos institucionales dañados por OCR antes de enviarlos al LLM o mostrar la respuesta. La fuente de activación tenía un dominio partido.
5. Se indica al LLM que no deduzca el dispositivo del título del documento cuando el usuario no lo indicó.

No se eliminaron documentos ni se reindexó ChromaDB. No se promovieron estas respuestas al Golden Cache: esta medición, incluso con revisión manual, no sustituye la confirmación individual de casos resueltos por usuarios reales.

## Comprobaciones y trabajo pendiente

- `pytest tests/test_rag_retrieval_precision.py tests/test_role_quick_replies.py -q`: **62 passed**.
- `git diff --check`: sin errores de formato; Git notificó conversión LF/CRLF en archivos de trabajo.
- Servidor del entorno virtual reiniciado después de los cambios; `GET http://127.0.0.1:8000/`: **200**.
- Una ejecución más amplia de `test_router_rules.py` tiene tres pruebas antiguas que esperan el estado `PIDIENDO_ROL`, retirado antes de estas correcciones; requieren actualización separada de sus expectativas. Las comprobaciones focalizadas de seguridad y recuperación sí pasaron.

Para medir si se mantiene el 80% fuera de esta muestra, hay que usar preguntas nuevas de personas reales, registrar la fuente esperada y revisar por separado recuperación, seguridad y solicitudes administrativas. La mejora más clara pendiente aquí es preguntar primero por **plataforma y mensaje de error** en los tres casos de acceso ambiguos; después recuperar la guía específica y continuar el diagnóstico en la misma sesión.
