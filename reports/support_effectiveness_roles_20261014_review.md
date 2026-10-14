# Efectividad de soporte TI por perfil — 14/10/2026

## Método y alcance

- Se usaron las 20 situaciones de soporte TI de la prueba anterior. Se repitieron sin perfil con el código actual y con una declaración de perfil al inicio de cada pregunta: 6 estudiantes, 7 docentes y 7 administrativos.
- Cada pregunta se ejecutó en una sesión aislada mediante `RouterLogic.procesar_mensaje`, con el LLM real, el índice y Golden Cache activos. No se enviaron comentarios de resolución ni se promovieron respuestas a Golden Cache. El ejecutor no escribe la telemetría del panel.
- La evaluación fue manual. **Correcta**: orientación suficiente, segura y respaldada; **parcial**: ayuda, pero omite una ruta o dato necesario; **incorrecta**: da un dato inválido, propone una acción no autorizada o niega una ruta que sí consta en los documentos. Una llamada exitosa al LLM no cuenta como acierto.
- Son 20 situaciones emparejadas, no una muestra representativa de todos los documentos o usuarios. Las respuestas del LLM pueden variar entre ejecuciones.

## Resultado

| Ejecución | Correctas | Parciales | Incorrectas | Exactitud estricta | Latencia p50 | Latencia p95 | Fallos de ejecución |
|---|---:|---:|---:|---:|---:|---:|---:|
| Prueba anterior, preguntas sin perfil, código anterior | 14 | 2 | 4 | 70% | 7,5 s | 22,4 s | 0 |
| Repetición sin perfil, código actual | 12 | 6 | 2 | 60% | 8,0 s | 15,2 s | 0 |
| Con perfil explícito, código actual | 13 | 4 | 3 | 65% | 7,9 s | 20,6 s | 0 |

Por perfil explícito: **estudiantes 4/6 (66,7%)**, **docentes 5/7 (71,4%)**, **administrativos 4/7 (57,1%)**. Una diferencia de una respuesta cambia cinco puntos porcentuales en el total; esta muestra no demuestra una tendencia estadística.

## Revisión emparejada

| # | Situación | Perfil añadido | Sin perfil, actual | Con perfil | Observación principal |
|---:|---|---|---|---|---|
| 1 | Acceso al correo | Estudiante | Parcial | Incorrecta | Con perfil recupera la guía estudiantil, pero reproduce tres veces un correo con un espacio en el dominio. |
| 2 | Inicio de sesión en Teams | Docente | Correcta | Correcta | Ruta de Microsoft para funcionarios y comprobaciones seguras. |
| 3 | Contraseña olvidada | Administrativo | Parcial | Parcial | Distingue Kactus/Seven y Talento Humano, pero necesita identificar la cuenta concreta para dar el trámite completo. |
| 4 | Usuario bloqueado | Docente | Parcial | Parcial | Respuesta de contingencia sin procedimiento ni diagnóstico de cuenta; pide el servicio afectado. |
| 5 | Cambio de clave sin acceso | Estudiante | Parcial | Parcial | Da la relación Portal/Aula/correo, pero no resuelve qué hacer si también falla el Portal. |
| 6 | Wi-Fi universitario | Estudiante | Correcta | Correcta | Diagnóstico básico útil; las fuentes recuperadas no documentan la configuración del Wi-Fi. |
| 7 | Conectado sin navegación | Administrativo | Correcta | Correcta | Comparación entre sitios, dispositivos y redes; contexto documental muy disperso. |
| 8 | Punto de red en oficina | Administrativo | Correcta | Correcta | Indica Mesa de Ayuda y datos para describir la falla. |
| 9 | Computador no enciende | Docente | Correcta | Correcta | Comprobaciones de alimentación y escalado sin abrir el equipo. |
| 10 | Mouse y teclado dañados | Administrativo | Parcial | Parcial | Remite a soporte, pero la consulta con rol no conserva P-GT-01 en sus fuentes finales y queda menos precisa. |
| 11 | Equipo lento | Docente | Correcta | Correcta | Comprobaciones reversibles y datos para soporte. |
| 12 | Teams no abre | Estudiante | Correcta | Correcta | Acceso por Correo Estudiantes y pruebas de aplicación/navegador. |
| 13 | No escuchan en Teams | Docente | Parcial | Correcta | Sin perfil supone que usa iPad; con perfil ofrece diagnóstico válido para distintos dispositivos. |
| 14 | Micrófono o cámara en Teams | Docente | Correcta | Correcta | Permisos, controles y selección de dispositivos. |
| 15 | Instalar programa | Administrativo | Correcta | Correcta | P-GT-01: solicitud del jefe de dependencia a Mesa de Servicio. |
| 16 | VPN fuera de campus | Administrativo | Correcta | Correcta | Dirección de TI y justificación de acceso remoto; P-GT-08 está entre las fuentes. |
| 17 | Correo sospechoso | Estudiante | Correcta | Correcta | P-GT-07: no abrir ni reenviar, informar a seguridad/TI. |
| 18 | Posible virus | Docente | Incorrecta | Incorrecta | Sin perfil recomienda análisis y eliminación por cuenta propia; con perfil el router lo desvía a soporte físico y aconseja cerrar programas sospechosos. P-GT-07 asigna análisis y cuarentena a Seguridad Informática. |
| 19 | Restaurar archivo desde backup | Administrativo | Incorrecta | Incorrecta | P-GT-10 ya se recupera, pero llega una sección sobre aprobación sin la página que indica el canal `solicitudcomputo@unisimon.edu.co`; la respuesta afirma que no existe ruta confirmada. |
| 20 | Atención presencial | Estudiante | Correcta | Correcta | Ticket de Mesa de Ayuda y revisión en sitio según diagnóstico. |

## Hallazgos verificables y prioridad

1. **Direcciones extraídas con OCR roto.** `Activar Usuario y Correo institucional.pdf`, página 5, contiene `trabajodesdecasa@unisim onbolivar.edu.co`. La instrucción al LLM de no reproducir direcciones fragmentadas no bastó. Hace falta una validación general de correos y enlaces en la respuesta final: si el texto no cumple sintaxis y dominio verificable, omitirlo y mostrar el canal oficial confirmado, sin adivinar cómo unirlo.
2. **Seguridad y enrutamiento.** P-GT-07, página 3, asigna el análisis de discos, desinfección y cuarentena a Seguridad Informática. La pregunta sobre virus tomó dos rutas distintas entre corridas, ambas dieron pasos impropios al usuario. El router debe reconocer incidentes de seguridad antes que el flujo genérico de hardware, y la respuesta debe limitarse a contención básica y escalado autorizado.
3. **Contexto incompleto dentro del documento correcto.** P-GT-10 apareció en la pregunta de restauración, pero faltó la página pertinente. La página 18 indica el correo para restauración de bases de datos/servidores; la página 16 documenta el canal para solicitar backups de equipos de usuario. La respuesta debe distinguir esos alcances y usar páginas contiguas o secciones relacionadas antes de negar un canal.
4. **Deriva del reranking por palabras de perfil.** En el caso de mouse/teclado, la versión con “funcionario administrativo” seleccionó manuales administrativos ajenos y perdió P-GT-01. El perfil debe servir para redactar la respuesta y, cuando proceda, desempatar; no debe superar la coincidencia entre el problema técnico y el procedimiento.
5. **Falta de procedimiento frente a consulta ambigua.** El bloqueo de usuario requiere saber el servicio. La respuesta de contingencia debería pedir ese dato concreto y dar las comprobaciones reversibles aplicables, sin atribuir una plataforma por defecto.

Archivos de resultados completos: `support_effectiveness_unscoped_current_20261014.json` y `support_effectiveness_roles_20261014.json`. El conjunto de preguntas con perfil está en `tests/fixtures/support_effectiveness_role_matched_20261014.json`.
