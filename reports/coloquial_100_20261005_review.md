# Revisión de carga coloquial — UniMon

Fecha: 2026-10-05T16:05:39-05:00

## Resumen de ejecución

- Preguntas/sesiones: **100** (10 tandas de 10 en paralelo, una tanda a la vez).
- Respuestas HTTP con contenido: **100/100**; fallos: **0**.
- HTTP 429: **0**; HTTP 5xx: **0**.
- Duración: **151.51 s**; rendimiento: **0.66 solicitudes/s**.
- Latencia p50/p95/máxima: **13125.0 / 15344.2 / 17485.6 ms**.
- Fuente esperada entre las fuentes reportadas: **51/98**.
- Modelo reportado por la API: **openai_gpt-6-luna: 98**; sin documentación: **2**.

## Evaluación de calidad con evidencia

- Correctas: **26**
- Parciales: **31**
- Incorrectas: **39**
- No verificables: **4**

El juez comparó cada respuesta con fragmentos recuperados del índice para la fuente esperada y las fuentes que reportó la API. Las respuestas HTTP exitosas no se consideran necesariamente correctas. Las formulaciones son coloquiales, pero reutilizan los 100 temas/documentos de la batería anterior con otras expresiones; no representan 100 temas nuevos. La introducción de roles fue variada y en algunas preguntas no coincidió con el rol implícito del trámite, por lo que esta corrida no sirve como medición limpia del clasificador de roles.

## Golden Cache

- Antes: **42**; después del filtro de seguridad: **58**.
- Nuevas entradas conservadas: **16** (casos 1, 3, 5, 10, 11, 12, 14, 22, 27, 28, 49, 52, 71, 76, 78, 90).
- Se retiraron **7** respuestas inicialmente elegibles porque la API no había incluido su fuente esperada. Solo se conservan respuestas correctas con confianza ≥0.95, aprobación de validadores internos y fuente esperada en las fuentes RAG reportadas.

## Resultados de las 100 sesiones

### 1. Credenciales — correct (0.99)

**Pregunta:** Hola, soy estudiante y necesito una mano: soy primíparo y ya pagué matrícula. ¿Dónde encuentro mi usuario y clave?

**HTTP/latencia:** 200 / 13773.1 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; GIE - ASPIRANTES NOV.2021.pptx; 1. Estudiantes Nuevos Pregrado.pptx
**Revisión:** La evidencia indica que el usuario y la contraseña están al final del recibo de matrícula.
**Golden Cache:** Sí

**Respuesta:**

Entiendo que necesitas esos datos para comenzar a ingresar. El usuario y la contraseña aparecen **al final del recibo de matrícula**. Al terminar el proceso de matrícula se indica tu usuario institucional y se genera el recibo para descargar; revisa ese recibo, especialmente la parte final.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 2. Credenciales — partial (0.9)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: estoy en primer semestre, ¿qué parte del recibo de matrícula tiene mis datos de acceso?

**HTTP/latencia:** 200 / 13507.0 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; GIE - ASPIRANTES NOV.2021.pptx; Credenciales microsoft.pdf
**Revisión:** Ubica los datos al final del recibo, pero la documentación se refiere a estudiantes de primer semestre y no confirma que ese procedimiento aplique a docentes.
**Golden Cache:** No

**Respuesta:**

Buenas. Según la guía, el usuario y la contraseña aparecen **al final del recibo de matrícula**. Al finalizar el proceso de matrícula también se indica el usuario institucional y se genera el recibo para descargar.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 3. Credenciales — correct (0.98)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Cómo activo el usuario institucional que me asignaron al ingresar a primer semestre?

**HTTP/latencia:** 200 / 15345.6 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; GIE - ASPIRANTES NOV.2021.pptx; Credenciales microsoft.pdf
**Revisión:** Aclara que el instructivo es para estudiantes y evita presentar esos pasos como válidos para personal administrativo.
**Golden Cache:** Sí

**Respuesta:**

El instructivo disponible describe la activación para **estudiantes de primer semestre**, no para personal administrativo. Si tu usuario fue asignado por un proceso administrativo, no puedo confirmar que debas seguir esos pasos ni que funcionen para tu cuenta.

Como comprobación segura, revisa el mensaje o documento con el que te asignaron el usuario y sigue las instrucciones indicadas allí. Si no especifica cómo activarlo, consulta con el área que te lo asignó para que te confirme el procedimiento correspondiente.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 4. Credenciales — incorrect (0.99)

**Pregunta:** Profe por acá, ¿me orientas con esto?: al entrar por primera vez al Portal Estudiantes, ¿cómo cambio la clave temporal?

**HTTP/latencia:** 200 / 15345.2 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf
**Revisión:** Asegura una contraseña temporal y requisitos específicos para cambiarla que no están respaldados por la evidencia citada.
**Golden Cache:** No

**Respuesta:**

Claro, profe. Si es para orientar a un estudiante de **primer semestre (nuevo ingreso)**:

1. Debe consultar el pie de página de su **Recibo de Matrícula Financiera Web** para ver el usuario institucional asignado. La contraseña temporal es `unisimon`.
2. Luego, debe ingresar a [Portal Estudiantes](https://www.unisimon.edu.co/portales) con ese usuario y la clave temporal.
3. Al iniciar sesión aparecerá una ventana obligatoria para cambiarla. Debe crear una contraseña personal que tenga entre **8 y 15 caracteres**, incluya mayúsculas, minúsculas y al menos un número, y no contenga datos personales.

La nueva contraseña también servirá para Aula Extendida y el correo estudiantil.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 5. Credenciales — correct (0.98)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿En qué momento del proceso de matrícula se informa el correo institucional del estudiante nuevo?

**HTTP/latencia:** 200 / 13132.3 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** GIE - ASPIRANTES NOV.2021.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; GIE - ASPIRANTES NOV.2021.pptx
**Revisión:** La evidencia confirma que al finalizar el proceso se informa el correo institucional y se genera el recibo descargable.
**Golden Cache:** Sí

**Respuesta:**

Al finalizar el proceso de matrícula, el sistema informa el correo institucional del estudiante nuevo y genera el recibo de matrícula para descargar. Al final de ese recibo encontrarás el usuario y la contraseña.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 6. Portales — correct (0.96)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cómo entro al Portal Estudiantes desde la página de portales de la universidad?

**HTTP/latencia:** 200 / 14202.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** No
**Fuentes reportadas:** Certificados estudiantes_v2.pptx; Movilidad Académica - Estudiantes.pdf; Gestión Prácticas - Estudiantes.pdf; Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf; Solicitud de inscripción para grado.pdf
**Revisión:** Indica la ruta del Portal Estudiantes y el ingreso con usuario y contraseña, conforme a la evidencia.
**Golden Cache:** No

**Respuesta:**

¡Buenas! Desde la página de portales de la Universidad:

1. Abre https://www.unisimon.edu.co/portales/estudiantes.
2. Ingresa tu usuario y contraseña y presiona **Acceder**.

No compartas tus credenciales con otras personas.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 7. Credenciales — incorrect (0.99)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: olvidé la contraseña del Portal Estudiantes, ¿cómo la restablezco?

**HTTP/latencia:** 200 / 15344.2 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; instructivo portales estudiantes.pptx; Restablecimiento de contraseña.pptx
**Revisión:** Detalla procedimientos, correo de recuperación, vigencia y requisitos de contraseña que no se acreditan en la evidencia.
**Golden Cache:** No

**Respuesta:**

Como es tu primera vez, el proceso depende de si eres de **primer semestre** o ya eres estudiante regular:

### Si eres estudiante de primer semestre (nuevo ingreso)
1. Revisa el pie de página de tu **Recibo de Matrícula Financiera Web** para encontrar tu usuario institucional y la contraseña temporal, que es `unisimon`.
2. Ingresa a [Portal Estudiantes](https://www.unisimon.edu.co/portales) con esos datos.
3. En la ventana emergente, cambia la contraseña temporal por una personal segura.

### Si eres estudiante regular (segundo semestre en adelante)
1. Ingresa a [Portal Estudiantes](https://www.unisimon.edu.co/portales) y selecciona **Olvidé mi Usuario / Contraseña**.
2. Digita tu documento de identidad. Recibirás un enlace de restablecimiento en el **correo personal registrado en el sistema**; el enlace es válido por 24 horas.
3. Al crear la contraseña, debe tener entre **8 y 15 caracteres**, incluir mayúsculas, minúsculas y al menos un número, y no contener datos personales.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 8. Credenciales — incorrect (0.98)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿A qué correo llega el enlace para recuperar la contraseña institucional?

**HTTP/latencia:** 200 / 17485.6 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; instructivo portales estudiantes.pdf
**Revisión:** La evidencia solo menciona un mensaje recibido; no respalda que el enlace llegue al correo personal registrado ni la excepción para primer semestre.
**Golden Cache:** No

**Respuesta:**

El enlace llega al **correo personal registrado en el sistema**. Si eres estudiante de primer semestre, consulta en cambio el pie de página de tu Recibo de Matrícula Financiera Web para ver tu usuario y contraseña temporal.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 9. Credenciales — incorrect (0.99)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Qué requisitos debe tener la nueva contraseña del Portal Estudiantes?

**HTTP/latencia:** 200 / 13333.8 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; instructivo portales estudiantes.pdf
**Revisión:** Los requisitos concretos de longitud, combinación de caracteres y exclusión de datos personales no aparecen en la evidencia citada.
**Golden Cache:** No

**Respuesta:**

La nueva contraseña del Portal Estudiantes debe tener **entre 8 y 15 caracteres**, incluir **mayúsculas, minúsculas y al menos un número**. No puede contener datos personales como tu nombre, apellido, número de identificación, teléfono o fecha de nacimiento.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 10. Credenciales — correct (0.99)

**Pregunta:** Buenas, me quedé atascado con este trámite: ya tengo mi correo estudiantil, ¿por dónde debo abrirlo para que la cuenta sea reconocida?

**HTTP/latencia:** 200 / 13764.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Gestión Prácticas - Funcionarios.pdf; Instructivo Credito Empresarial.pptx; instructivo portales estudiantes.pdf
**Revisión:** La evidencia indica expresamente que se accede desde la web universitaria por Servicios y luego Correo Estudiantes.
**Golden Cache:** Sí

**Respuesta:**

Buenas. Para que tu cuenta sea reconocida, ingresa a la página web de la Universidad y ve a **Servicios → Correo Estudiantes**. La documentación indica que debes acceder por esa ruta.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 11. Microsoft 365 — correct (0.99)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cómo inicio sesión en Microsoft Teams con mi cuenta de estudiante?

**HTTP/latencia:** 200 / 12228.2 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Como_acceder_MS_Teams_Estudiantes.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Videollamadas en  Teams.pdf; Instructivo Credito Empresarial.pptx; instructivo portales estudiantes.pptx; Como_acceder_MS_Teams_Estudiantes.pdf
**Revisión:** Indica la ruta Servicios → Correo Estudiantes y luego iniciar sesión en Teams con las credenciales de Microsoft, tal como señala la guía.
**Golden Cache:** Sí

**Respuesta:**

1. Desde el sitio web de Unisimón, ve a **Servicios → Correo Estudiantes** e inicia sesión en tu correo institucional de Microsoft.
2. Luego, abre Microsoft Teams e inicia sesión con tu usuario y contraseña de Microsoft.

No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 12. Microsoft 365 — correct (0.99)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Desde qué sección del sitio de Unisimon se accede al correo para entrar a Teams?

**HTTP/latencia:** 200 / 11871.6 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Como_acceder_MS_Teams_Estudiantes.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Como_acceder_MS_Teams_Estudiantes.pdf; Como_acceder_a_Microsoft_Teams.pdf; Descarga e instalación Ms 365.pdf; instructivo portales estudiantes.pdf; instructivo portales estudiantes.pptx
**Revisión:** La ruta Servicios → Correo Funcionarios Microsoft está respaldada por la guía para funcionarios.
**Golden Cache:** Sí

**Respuesta:**

Buenas. Desde el sitio web de Unisimon, ve a **Servicios** y selecciona **Correo Funcionarios Microsoft**. Inicia sesión con tu correo institucional de Microsoft para acceder a Teams.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 13. Microsoft 365 — incorrect (0.98)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Cómo me matriculo en mis grupos de Teams y Moodle como estudiante?

**HTTP/latencia:** 200 / 13227.0 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Matricular_grupos_teams_moodle_Estudiante.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Estudiantes_Matricular grupos en teams ymoodle.pdf; Fucionarios_Integración Moodle y Teams.pdf; Matricular_grupos_teams_moodle_Estudiante.pdf; Agregar_miembros_Grupos_MS_Teams.pdf
**Revisión:** Aunque reconoce que no cubre Teams, añade pasos y detalles sobre Moodle —como esperar tres minutos y el significado de «No Activo»— que no aparecen en la evidencia citada.
**Golden Cache:** No

**Respuesta:**

Entiendo que quieres acceder a tus grupos de clase. Como indicas que eres estudiante, puedes revisar y solicitar la matrícula así:

1. En el sistema donde consultas tus grupos, espera unos segundos mientras verifica el estado de cada grupo en Moodle.
2. Si un grupo no aparece matriculado, selecciona **“Matricular en Moodle…”** y espera aproximadamente 3 minutos para que se complete.
3. Si el grupo aparece como **“No Activo”**, significa que no se ha asignado un docente o que el grupo aún no existe en el aula. Comunícate con el docente y espera a que se actualice el curso.

La guía disponible confirma estos pasos para Moodle, pero no contiene el procedimiento de matrícula en Teams para estudiantes.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 14. Microsoft 365 — correct (0.99)

**Pregunta:** Profe por acá, ¿me orientas con esto?: no veo mis cursos en Teams, ¿qué indica la guía de matrícula de grupos para estudiantes?

**HTTP/latencia:** 200 / 12607.6 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Estudiantes_Matricular grupos en teams ymoodle.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Profesores_Integración teams y moodle.pdf; Fucionarios_Integración Moodle y Teams.pdf; Matricular_grupos_teams_Estudiante.pdf; Estudiantes_Matricular grupos en teams ymoodle.pdf
**Revisión:** Los pasos de ingreso, verificación y matrícula en Teams, y la explicación de «No activo», coinciden con la guía estudiantil.
**Golden Cache:** Sí

**Respuesta:**

Claro, profe. La guía para estudiantes indica que deben:

1. En el sistema, seleccionar **Calificaciones**.
2. Esperar unos segundos mientras se verifica el estado de cada grupo en Teams.
3. Si un grupo no aparece matriculado, seleccionar **Matricular en Teams…**.

Si aparece **“No activo”**, significa que aún no se ha escogido horario para ese grupo o que no tiene profesor asignado. La guía no indica que se pueda matricular ese grupo en Teams mientras esté en ese estado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 15. Microsoft 365 — incorrect (0.99)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Dónde puedo descargar e instalar Microsoft 365 con mi cuenta institucional?

**HTTP/latencia:** 200 / 12718.5 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Descarga e instalación Ms 365.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Descarga e instalación Ms 365.pdf
**Revisión:** La guía indica acceder por Servicios → Correo Funcionarios Microsoft y seleccionar «Instalar Office»; la respuesta da credenciales y pasos de instalación no respaldados por la evidencia.
**Golden Cache:** No

**Respuesta:**

Hola. Para descargar e instalar Microsoft 365 con tu cuenta institucional:

1. Inicia sesión en Microsoft con el usuario y la contraseña que utilizas en el Portal de Gestión Académico-Administrativa.
2. En las opciones de instalación, selecciona **«Otras opciones de instalación»** y sigue las instrucciones que aparezcan.
3. Durante la descarga, mantente conectado a Internet y espera a que termine la instalación.
4. Cuando finalice, haz clic en **«Cerrar»**.

No tengo una URL institucional verificada para iniciar la descarga. Si no encuentras la opción de instalación o la cuenta no te permite avanzar, detente ahí y contacta al canal oficial de soporte de la Universidad.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 16. Microsoft 365 — incorrect (0.98)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Qué credenciales debo usar para iniciar sesión en los servicios Microsoft de la universidad?

**HTTP/latencia:** 200 / 13338.9 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Credenciales microsoft.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Credenciales microsoft.pdf; instructivo portales estudiantes.pptx; instructivo portales estudiantes.pdf
**Revisión:** La clave inicial está respaldada, pero la respuesta agrega sin evidencia que el portal permite actualizarla y requisitos específicos de longitud y complejidad.
**Golden Cache:** No

**Respuesta:**

¡Claro! Las credenciales de Microsoft se consultan en el **Portal de Gestión Académico-Administrativa**:

1. Ingresa desde la página de la Universidad, en **Portales**, y accede con tu usuario y contraseña del portal.
2. Al entrar, aparecerá una ventana con tus credenciales de Microsoft: el usuario y la clave inicial, que se forma con **Usb** (U mayúscula) seguido de tu número de documento.
3. Si cambiaste esa clave, usa la nueva. Si necesitas actualizarla, el portal permite cambiarla; la nueva debe tener entre 8 y 15 caracteres, incluir mayúsculas, minúsculas y al menos un número, y no contener datos personales.

No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 17. Microsoft 365 — correct (0.97)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Cómo ingreso al correo institucional de Microsoft desde la web universitaria?

**HTTP/latencia:** 200 / 12225.2 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Como_acceder_a_Microsoft_Teams.pdf · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; instructivo portales estudiantes.pdf; Experiencias Extracurriculares (Estudiantes).pptx; Como_acceder_MS_Teams_Estudiantes.pdf; instructivo portales estudiantes.pptx
**Revisión:** La ruta Servicios → Correo Estudiantes está respaldada por la evidencia de acceso al correo estudiantil.
**Golden Cache:** No

**Respuesta:**

1. Desde tu navegador, ingresa a **http://www.unisimon.edu.co/**.
2. En el menú principal, selecciona **Servicios** y luego **Correo Estudiantes** para acceder al correo institucional de Microsoft.
3. Inicia sesión con tu cuenta institucional. No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 18. Microsoft 365 — correct (0.97)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Cómo accede un profesor a Teams para sus clases?

**HTTP/latencia:** 200 / 12303.9 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Profesores_Integración teams y moodle.pdf · **Incluida por API:** No
**Fuentes reportadas:** Videollamadas en  Teams.pdf; Grabar un clase en Teams y compartir en Stream.pdf; Como_acceder_a_Microsoft_Teams.pdf
**Revisión:** La ruta de acceso para funcionarios está respaldada y la guía de videollamadas confirma que los cursos asignados se encuentran en Teams.
**Golden Cache:** No

**Respuesta:**

Hola. Para acceder a Teams, inicia sesión en tu correo institucional de Microsoft desde el sitio web de Unisimón: ve a **Servicios → Correo Funcionarios Microsoft**. Una vez dentro de Teams, podrás ingresar al curso correspondiente para tus clases.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 19. Microsoft 365 — incorrect (0.99)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Cómo puedo grabar una clase o reunión de Teams y compartirla?

**HTTP/latencia:** 200 / 13661.6 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Grabar un clase en Teams y compartir en Stream.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Grabar un clase en Teams y compartir en Stream.pdf; Grabar videollamadas en Teams.pdf
**Revisión:** La evidencia citada solo acredita pasos para unirse; no respalda iniciar la grabación ni compartirla mediante «Usuarios» → «Mis grupos».
**Golden Cache:** No

**Respuesta:**

Claro. En Teams, puedes hacerlo así:

1. Entra al curso y selecciona la reunión a la que quieres unirte. Luego pulsa **«Unirse»**.
2. Ya dentro de la reunión, abre **«Más acciones»** y selecciona **«Iniciar grabación»**.
3. Para compartirla, el material institucional indica que debes elegir **«Usuarios» → «Mis grupos»**, buscar el grupo escribiendo **«Baq»** y pulsar **Enter**.
4. Selecciona la asignatura correspondiente y haz clic en **«Publicar»**.

Los nombres de algunas opciones pueden variar según la versión de Teams o tu acceso. Si no ves «Iniciar grabación» o no puedes compartirla, no intentes cambiar permisos; puede depender de la configuración de la reunión o de tu cuenta.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 20. Microsoft 365 — no_verificable (0.95)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Cómo creo una reunión de Teams que no esté asociada a un grupo?

**HTTP/latencia:** 200 / 12522.9 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Crear reuniones No asociadas a grupos.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Crear reuniones No asociadas a grupos.pdf; Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf; Ajustes participantes reuniones  Ms Teams.pdf
**Revisión:** La evidencia aportada no describe crear una reunión desde Calendario sin asociarla a un grupo, así que no permite verificar el procedimiento propuesto.
**Golden Cache:** No

**Respuesta:**

¡Buenas! Para crear una reunión de Teams que no esté asociada a un grupo, abre **Calendario** y crea una reunión. Completa los datos y agrega a los participantes, pero no la compartas en un canal ni selecciones un curso. Después, guárdala; debería aparecer en tu calendario.

La documentación disponible no especifica los nombres exactos de los botones para guardar una reunión no asociada a un grupo.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 21. Calificaciones — incorrect (0.99)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cuál es la ruta para que un docente ingrese calificaciones en el portal?

**HTTP/latencia:** 200 / 12377.7 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Calificaciones.pdf · **Incluida por API:** No
**Fuentes reportadas:** Solicitud de inscripción para grado.pdf; Autorización de Supletorios.pdf; Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf; Reactivación de Inscripción.pptx; Bloqueos, Sanciones y Excepciones.pptx
**Revisión:** La evidencia sí especifica la ruta: «Registro de Calificaciones» y luego seleccionar el Programa Académico. La respuesta afirma que la ruta no está especificada y no la proporciona.
**Golden Cache:** No

**Respuesta:**

Hola. La ruta exacta dentro del portal no está especificada en la información disponible. Si se trata de la calificación de un supletorio, el docente puede digitarla después de que autoricen el supletorio y realices el pago del volante correspondiente.

Para otras calificaciones, no tengo una ruta institucional verificada. Como estudiante, consulta con tu docente cuál módulo debe usar; si el problema es técnico al ingresar la nota, el docente puede solicitar apoyo por los canales institucionales.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 22. Calificaciones — correct (1.0)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Cómo guardo como borrador las notas antes de enviarlas?

**HTTP/latencia:** 200 / 11587.4 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Calificaciones.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Calificaciones.pdf; Evaluacion Profesoral - Estudiante.pdf; Unisimon App.pdf; Autoevaluacion por Grupos - Funcionarios.pdf; Evaluaciones de selección ILE-TICS (ASPIRANTES).pdf
**Revisión:** Indica correctamente «Guardar Borrador» para conservar las notas y «Finalizar» para enviarlas, tal como señala la evidencia.
**Golden Cache:** Sí

**Respuesta:**

En la pantalla de calificaciones, después de ingresar las notas, selecciona **Guardar Borrador**. Esto conservará temporalmente las calificaciones sin finalizar el proceso. Cuando quieras enviarlas, presiona **Finalizar**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 23. Calificaciones — incorrect (1.0)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: después de revisar las calificaciones, ¿qué botón finaliza y envía el borrador?

**HTTP/latencia:** 200 / 12152.2 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Calificaciones.pdf · **Incluida por API:** No
**Fuentes reportadas:** P-GT-13_Procedimiento_para_la_gestion_de_requerimientos_de_recursos_y_soluciones_tecnologicas.pdf; Instructivo Aprobación de Requisitos.pdf; Aprobación de Requisitos.pptx; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf
**Revisión:** La evidencia confirma que el botón «Finalizar» envía las notas del borrador; la respuesta dice que no puede confirmarlo.
**Golden Cache:** No

**Respuesta:**

No cuento con un procedimiento institucional verificado sobre el registro y envío de calificaciones, así que no puedo confirmar qué botón finaliza el borrador. Revisa las instrucciones de la plataforma correspondiente o consulta al área responsable del proceso antes de enviarlo.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 24. Calificaciones — partial (0.87)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Dónde consulto mis calificaciones como estudiante?

**HTTP/latencia:** 200 / 12138.5 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Calificaciones.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Autorización de Supletorios.pdf; Bloqueos, Sanciones y Excepciones.pptx; Calificaciones.pptx; Matricula (2).pptx
**Revisión:** Incluye los pasos respaldados de seleccionar Programa y Período, y el ícono de impresión. La ruta específica desde unisimon.edu.co y «Portales» no está respaldada por la evidencia aportada.
**Golden Cache:** No

**Respuesta:**

Claro. Para consultar tus calificaciones como estudiante:

1. Desde un navegador, ingresa a **unisimon.edu.co** y selecciona **Portales** en el menú principal.
2. Entra al **Portal de Estudiantes** y selecciona **Calificaciones**.
3. Elige tu **Programa** y el **Período** que quieres consultar.

Si deseas imprimir el listado, selecciona el ícono de impresión.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 25. Calificaciones — incorrect (0.99)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Cómo registra un docente una nota definitiva de un curso de posgrado?

**HTTP/latencia:** 200 / 12296.3 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Calificaciones Posgrados.pdf · **Incluida por API:** No
**Fuentes reportadas:** Estudiantes_Matricular grupos en teams ymoodle.pdf; Videollamadas en  Teams.pdf; Trabajo de grado.pdf; Matricula (2).pptx; Instructivo Atencion a Estudiantes (Tutorías).pdf
**Revisión:** La evidencia solo indica escoger el curso y período y seleccionar el ícono de la columna «Definitiva». La escala, el botón «Enviar» y otras afirmaciones de la respuesta no están respaldados.
**Golden Cache:** No

**Respuesta:**

Para un curso de posgrado, el docente registra directamente la nota final; no se habilitan casillas de parciales, porque la evaluación es modular.

1. En SIAAF/SIA, el docente debe ingresar la nota en la columna **Definitiva / Calificación**, usando la escala de **0.0 a 5.0**.
2. Luego debe hacer clic en **Enviar** para registrar la nota.

Como estudiante, no podrás ingresarla desde tu cuenta. Si tienes dudas o desacuerdos sobre la calificación, comunícate con el docente o con la Dirección de Programa.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 26. Elecciones — partial (0.94)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cuál es el paso a paso para votar en las elecciones institucionales?

**HTTP/latencia:** 200 / 12905.9 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aplicativo Elecciones -  Cómo votar.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Aplicativo Elecciones -  Órganos colegiados.pptx; Aplicativo Elecciones -  Cómo votar.pptx
**Revisión:** La evidencia respalda elegir «Votar» en una elección disponible, pero no respalda los pasos sobre seleccionar candidato y confirmar la acción.
**Golden Cache:** No

**Respuesta:**

1. Ingresa al portal de elecciones institucionales: https://elecciones.unisimon.edu.co/.
2. Revisa el listado de elecciones disponibles para tu rol y selecciona **Votar** en la que corresponda.
3. Haz clic en el nombre o la foto del candidato por quien deseas votar. El sistema te pedirá confirmar la acción; revisa tu selección y confirma.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 27. Elecciones — correct (0.99)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿En qué página ingreso para participar en las elecciones de la universidad?

**HTTP/latencia:** 200 / 11860.2 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aplicativo Elecciones -  Cómo votar.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Aplicativo Elecciones -  Cómo votar.pptx; Aplicativo Elecciones -  Órganos colegiados.pptx; Aplicativo elecciones - Módulo Configuración.pptx; Aplicativo Elecciones -  Módulo Estudiantes.pptx
**Revisión:** La evidencia respalda el enlace, el inicio de sesión con usuario y contraseña institucional y la selección de «Votar» en una elección disponible.
**Golden Cache:** Sí

**Respuesta:**

Ingresa a https://elecciones.unisimon.edu.co/ e inicia sesión con tu usuario y contraseña institucional. Luego verás las elecciones disponibles según tu rol; selecciona **“Votar”** en la elección en la que quieras participar.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 28. Elecciones — correct (0.99)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ya elegí candidato, ¿cómo confirmo mi voto en el aplicativo de elecciones?

**HTTP/latencia:** 200 / 12295.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aplicativo Elecciones -  Cómo votar.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Aplicativo Elecciones -  Cómo votar.pptx; Aplicativo Elecciones -  Órganos colegiados.pptx
**Revisión:** La evidencia indica hacer clic en la foto del candidato y que el sistema solicitará confirmación. La respuesta refleja esos pasos.
**Golden Cache:** Sí

**Respuesta:**

Entra al portal de elecciones: https://elecciones.unisimon.edu.co/. Selecciona **Votar** en la elección correspondiente y haz clic en el nombre o la foto del candidato que elegiste. El sistema te solicitará confirmar la acción; sigue esa indicación para registrar tu voto.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 29. Elecciones — partial (0.98)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Cómo participa un estudiante en la jornada electoral institucional?

**HTTP/latencia:** 200 / 14629.8 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aplicativo Elecciones -  Cómo votar.pptx · **Incluida por API:** No
**Fuentes reportadas:** Aplicativo Elecciones -  Órganos colegiados.pptx; Aplicativo Elecciones -  Módulo Estudiantes.pptx; Anulación y Modificación de Programa Pre-inscripciones.pptx; Aplicativo Elecciones -  Módulo Egresados.pptx; Solicitud de crédito.pptx
**Revisión:** Orienta sobre el acceso y el inicio de sesión, pero omite el paso respaldado de seleccionar «Votar» en la elección correspondiente. La advertencia sobre contraseñas no aparece en la evidencia.
**Golden Cache:** No

**Respuesta:**

Para participar en la jornada electoral institucional:

1. Entra a https://elecciones.unisimon.edu.co/.
2. Escribe tu usuario y contraseña institucional e inicia sesión.
3. Sigue las opciones que te muestre el portal para emitir tu voto. La guía disponible no detalla los pasos dentro de la votación.

No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 30. Elecciones — partial (0.9)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Con qué cuenta ingreso al sistema de votaciones institucionales?

**HTTP/latencia:** 200 / 12170.1 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aplicativo Elecciones -  Cómo votar.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Aplicativo Elecciones -  Cómo votar.pptx; Aplicativo Elecciones -  Órganos colegiados.pptx
**Revisión:** Es consistente con que las elecciones disponibles dependen del rol, pero el enlace no está respaldado por los extractos aportados y no confirma qué cuenta debe usarse.
**Golden Cache:** No

**Respuesta:**

Ingresa al portal de elecciones institucionales: https://elecciones.unisimon.edu.co/. El acceso con una cuenta específica no está indicado en la información disponible; una vez dentro, verás las elecciones habilitadas según tu rol institucional.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 31. Certificados — correct (0.96)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cómo descargo un certificado estudiantil electrónico?

**HTTP/latencia:** 200 / 14117.8 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Certificados estudiantes_v2.pptx · **Incluida por API:** No
**Fuentes reportadas:** Certificados Electrónicos.pptx; Instructivo Credito Empresarial.pptx; Autorización de Supletorios.pdf
**Revisión:** Indica cómo generar la solicitud y descargar el certificado; los pasos coinciden con el material citado.
**Golden Cache:** No

**Respuesta:**

1. Desde tu navegador, ingresa a [unisimon.edu.co](http://www.unisimon.edu.co/) y selecciona **«Portales»** en el menú principal. Accede al Portal de Estudiantes y abre el módulo **«Certificados»**.
2. Para solicitarlo, selecciona el ícono a la derecha del certificado que necesitas. Elige el **Programa** y el **Período**, y presiona **«Generar»**.
3. Cuando el certificado electrónico esté disponible, descárgalo seleccionando el ícono ubicado a la derecha del certificado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 32. Certificados — incorrect (0.94)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Qué pasos debo seguir para solicitar un certificado como estudiante?

**HTTP/latencia:** 200 / 12029.6 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Descarga de certificados.pptx · **Incluida por API:** No
**Fuentes reportadas:** Manual de Usuario - Registro de Ingreso.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf; Evaluacion Profesoral - Estudiante.pdf
**Revisión:** La respuesta afirma que no hay un procedimiento verificado, aunque la evidencia describe el acceso a certificados y la descarga del volante o certificado.
**Golden Cache:** No

**Respuesta:**

Buenas. Como docente, no tengo un procedimiento institucional verificado para solicitar un certificado **como estudiante**. No uses el Portal Estudiantes para un trámite propio de docente: consulta con la dependencia universitaria que emite ese certificado para confirmar el proceso que corresponde a tu caso.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 33. Certificados — incorrect (0.99)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿En qué portal se consultan los certificados electrónicos de estudiantes?

**HTTP/latencia:** 200 / 11888.4 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Certificados Electrónicos.pptx · **Incluida por API:** No
**Fuentes reportadas:** Credenciales microsoft.pdf; Movilidad Académica - Administrativo.pdf; Manual de Usuario - Portal CovidApp.pdf; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; Como_acceder_a_Microsoft_Teams.pdf
**Revisión:** La evidencia identifica explícitamente el Portal de Estudiantes para los certificados electrónicos; la respuesta lo niega.
**Golden Cache:** No

**Respuesta:**

No tengo información institucional verificada sobre dónde se consultan los certificados electrónicos de estudiantes. El material disponible solo describe el acceso a portales administrativos y a otros sistemas; no indica el portal para esos certificados.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 34. Certificados — correct (0.93)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Cómo verifico o descargo el certificado electrónico después de solicitarlo?

**HTTP/latencia:** 200 / 12568.7 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Certificados estudiantes_v2.pptx · **Incluida por API:** No
**Fuentes reportadas:** Certificados Electrónicos.pptx; Gestión de Ingreso -  Funcionarios.pdf; Descarga e instalación Ms 365.pdf; Instructivo - Inscripción ed. continuada.pdf
**Revisión:** Explica seleccionar el módulo de certificados y usar el ícono a la derecha para descargar; además aclara que el estado pendiente no está detallado.
**Golden Cache:** No

**Respuesta:**

Claro, profe. Para descargar el certificado electrónico:

1. Entra al portal y selecciona el módulo **Certificados**.
2. Busca el certificado solicitado y presiona el icono que aparece a su derecha para descargarlo.

Si no aparece disponible, revisa más adelante si la solicitud ya fue procesada; la documentación disponible no detalla cómo consultar el estado de una solicitud pendiente.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 35. Matrícula — incorrect (0.99)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Cómo hago la inscripción a cursos intersemestrales?

**HTTP/latencia:** 200 / 13256.6 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Inscripcion de cursos intersemestrales.pdf · **Incluida por API:** No
**Fuentes reportadas:** Videollamadas en  Teams.pdf; GIE - ASPIRANTES NOV.2021.pptx; Gestión de Ingreso -  Funcionarios.pdf; Nueva Hoja de Vida.pdf; Trazabilidad de transferencia externa.pptx
**Revisión:** La evidencia sí indica seleccionar el módulo, elegir los cursos ofertados y confirmar la inscripción; la respuesta dice que no hay procedimiento.
**Golden Cache:** No

**Respuesta:**

Hola. Entiendo que el trámite puede ser confuso. La información disponible no incluye el procedimiento institucional para inscribirse en cursos intersemestrales, así que no quiero indicarte una ruta o requisitos que podrían no corresponder.

Puedes revisar los avisos oficiales de la Universidad sobre el periodo intersemestral y confirmar con la dependencia académica que gestione la inscripción. Si el problema es técnico en una plataforma, dime cuál estás usando y qué ocurre; puedo ayudarte con comprobaciones generales seguras.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 36. Matrícula — partial (0.91)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cómo matriculo un curso intersemestral desde el portal?

**HTTP/latencia:** 200 / 12807.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Matricula de Cursos Intersemestrales.pptx · **Incluida por API:** No
**Fuentes reportadas:** Inscripcion de cursos intersemestrales.pdf; Inscripcion de cursos intersemestrales.pptx; Gestión Prácticas - Estudiantes.pdf; Fucionarios_Integración Moodle y Teams.pdf; Gestión de Ayudas Educativas.pdf
**Revisión:** Orienta sobre seleccionar cursos y esperar autorización para el volante, pero no incluye el paso de oficializar la matrícula indicado en la evidencia.
**Golden Cache:** No

**Respuesta:**

¡Buenas! Para iniciar la inscripción a un curso intersemestral, ingresa al portal y selecciona los cursos que deseas. El volante de pago no estará disponible de inmediato: solo podrás generarlo y descargarlo con el botón **«Volante»** cuando tu programa académico autorice la inscripción a los cursos seleccionados.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 37. Matrícula — correct (0.91)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Qué pasos sigue un estudiante antiguo para realizar su matrícula?

**HTTP/latencia:** 200 / 12028.4 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 2. Estudiantes Antiguos Pregrado.pptx · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Matricula (2).pptx; Bienestar universitario manual.pptx
**Revisión:** Los pasos sobre completar el formulario, verificar pagos, guardar y generar un volante por el saldo están respaldados por la evidencia.
**Golden Cache:** No

**Respuesta:**

Para un estudiante antiguo, el instructivo indica que debes completar la información del formulario según el semestre y el tipo de matrícula que vas a realizar. Luego:

1. Verifica los pagos realizados y las fechas límite.
2. Presiona **Guardar** para generar la matrícula.
3. Si queda un saldo pendiente, puedes generar un volante por el monto restante con el botón **Volante de matrícula**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 38. Matrícula — incorrect (0.96)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Dónde consulto el procedimiento de matrícula completa o media matrícula?

**HTTP/latencia:** 200 / 12806.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 3. Matricula Completa-Media matricula.pptx · **Incluida por API:** No
**Fuentes reportadas:** Gestión de Ingreso -  Funcionarios.pdf; Matricula de Cursos Intersemestrales.pptx; GIE - ASPIRANTES NOV.2021.pptx; Videollamadas en  Teams.pdf; Matrícula Antiguos Posgrados.pdf
**Revisión:** La evidencia ubica el informe en SIAAF Web y señala que se debe seleccionar «Matrícula completa / Media matrícula»; la respuesta no ofrece esa ruta.
**Golden Cache:** No

**Respuesta:**

Hola. La documentación disponible no indica dónde consultar específicamente el procedimiento de matrícula completa o media matrícula. Para una comprobación general, revisa el portal o sistema institucional en el que estás apoyando el proceso y busca la sección de matrícula; no puedo confirmar una ruta o nombre de opción sin documentación.

Si me indicas qué sistema o portal estás usando, puedo orientarte con la información disponible para ese proceso.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 39. Matrícula — partial (0.82)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Qué debo hacer para solicitar un reintegro a un programa de pregrado?

**HTTP/latencia:** 200 / 12566.0 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 6. Reintegro.pptx · **Incluida por API:** No
**Fuentes reportadas:** GIE - ASPIRANTES NOV.2021.pptx; Solicitud de inscripción para grado.pdf; Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf; Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf; Instructivo Módulo Atención Estudiantes (Completo).pdf
**Revisión:** La evidencia respalda seleccionar Reingreso y consultar a Matrículas si no aparece el programa o no se cumplen requisitos; no documenta con claridad todo el inicio del trámite descrito.
**Golden Cache:** No

**Respuesta:**

Claro. Para solicitar un reintegro a un programa de pregrado, inicia una solicitud de admisión y selecciona **Reingreso** como tipo de inscripción. Luego elige el programa que deseas retomar.

El sistema verificará requisitos académicos, como tu promedio y el tiempo transcurrido desde tu última matrícula activa. Si no aparece el programa o el sistema indica que no cumples algún requisito, comunícate con la **Oficina de Matrículas**, que atiende los reingresos de pregrado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 40. Matrícula — partial (0.9)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Cómo se tramita una transferencia externa para ingresar a la universidad?

**HTTP/latencia:** 200 / 16604.6 ms · **Rol inferido:** otros · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 4. Transferencia Externa.pptx · **Incluida por API:** No
**Fuentes reportadas:** Manual de Usuario - Portal CovidApp.pdf; Trazabilidad de transferencia externa.pptx; Gestión de Ingreso -  Funcionarios.pdf; Demo tipos de admisión.pptx
**Revisión:** Distingue correctamente el seguimiento interno del inicio de una solicitud, pero la evidencia citada no respalda el paso específico de asignar la fecha de homologación.
**Golden Cache:** No

**Respuesta:**

Buenas. La documentación disponible no describe el trámite completo para solicitar una transferencia externa ni sus requisitos de admisión. Sí documenta una parte del seguimiento interno: seleccionar la sede, abrir **«Inscritos»**, filtrar por año, periodo, nivel y programa, y pulsar **«Buscar»**. Para asignar la fecha de homologación, indica usar el ícono de la columna **«Acción»** cuando la solicitud esté en etapa **«Inscripción»**.

Esos pasos corresponden a consultar y gestionar solicitudes ya inscritas; no confirman cómo iniciar una solicitud como aspirante. Si estás haciendo la gestión como aspirante, verifica el procedimiento vigente con el área de admisiones antes de continuar, ya que aquí no tengo un contacto o enlace institucional confirmado para ese trámite.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 41. Admisiones — partial (0.91)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cómo reactivo una inscripción que quedó inactiva?

**HTTP/latencia:** 200 / 13608.4 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aspirantes - Reactivación de Inscripción.pdf · **Incluida por API:** No
**Fuentes reportadas:** Reactivación de Inscripción.pptx; Inscripción.pptx; Gestión de inscripciones - Anexo actualizaciones.pdf
**Revisión:** La selección del tipo de inscripción está respaldada, pero el ingreso con identificación y fecha de expedición, el envío del formulario y completar la hoja de vida no aparecen en la evidencia proporcionada.
**Golden Cache:** No

**Respuesta:**

Para reactivar una inscripción anterior, sigue estos pasos:

1. Ingresa a la plataforma con tu número de identificación y la fecha de expedición del documento; luego presiona **Continuar**.
2. Selecciona el tipo de inscripción que deseas reactivar.
3. Completa el formulario que aparece y envíalo.
4. Al finalizar, completa todos los campos solicitados en el formulario de **Hoja de vida**.

Si no puedes ingresar o la opción de reactivación no aparece, la guía disponible no especifica cómo resolver esos casos; evita enviar datos por formularios que no reconozcas y consulta el canal institucional correspondiente.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 42. Admisiones — incorrect (0.98)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Cómo oficializa su matrícula un aspirante después de completar el formulario?

**HTTP/latencia:** 200 / 17325.2 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** GIE - ASPIRANTES NOV.2021.pptx · **Incluida por API:** No
**Fuentes reportadas:** Demo tipos de admisión.pptx; Matricula de Cursos Intersemestrales.pptx; Matricula.pptx; Volantes.pdf
**Revisión:** Responde con detalles de oficialización de pagos y matrícula de cursos intersemestrales, no con el flujo para aspirantes. La evidencia indica que, tras la encuesta poblacional, se confirma la oficialización y se presiona «Confirmar».
**Golden Cache:** No

**Respuesta:**

Los fragmentos sí muestran un paso de oficialización de matrícula: en la sección **«Oficializar pagos»** se revisan el estado académico, los valores de matrícula, los abonos y el resumen del estado de cuenta; para oficializar, se presiona **«Oficializar»**.

Sin embargo, no se confirma que ese sea el paso que debe seguir un aspirante justo después de completar el formulario. La pantalla de admisión mostrada solo describe el registro de usuario, así que no puedo asegurar que ambos procesos correspondan.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 43. Admisiones — incorrect (0.96)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Cómo consulto y gestiono una inscripción de aspirante?

**HTTP/latencia:** 200 / 13298.4 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Gestión de inscripciones.pdf · **Incluida por API:** No
**Fuentes reportadas:** P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; Reportes de Caracterización.pptx; Estadísticas institucionales.pdf; Gestión de Ingreso -  Funcionarios.pdf; Autorización de Supletorios.pdf
**Revisión:** Los pasos sobre seleccionar proceso, periodo, nivel y programa, buscar aspirantes y permisos no están respaldados por la evidencia. Esta sí describe opciones concretas para gestionar una inscripción, como ver requisitos y aprobar o admitir la solicitud.
**Golden Cache:** No

**Respuesta:**

1. Ingresa al Portal con tu cuenta institucional y selecciona **“Gestión de Ingreso de Estudiantes”**.
2. En el módulo, selecciona el **proceso, periodo, nivel y programa académico**. Las opciones disponibles dependen de los permisos asociados a tu usuario.
3. Si lo necesitas, elige un **tipo de búsqueda** e ingresa un texto en **“Buscar”**; luego selecciona **“Buscar”** para consultar los aspirantes.

Este módulo permite consultar y gestionar el proceso de admisión desde la inscripción hasta la matrícula. Si no aparece el proceso, nivel o programa que necesitas, verifica que estés usando el periodo correcto; si persiste, es posible que tu usuario no tenga los permisos correspondientes.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 44. Cuentas — partial (0.91)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Qué puedo hacer si mi usuario institucional aparece bloqueado?

**HTTP/latencia:** 200 / 15236.1 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Instructivo Bloqueos.pdf · **Incluida por API:** No
**Fuentes reportadas:** Manual de Usuario - Portal CovidApp.pdf; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf
**Revisión:** Distingue entre sistemas y describe el desbloqueo de CovidApp de forma respaldada, pero la pregunta no identifica el sistema y el procedimiento citado para cuentas institucionales no establece esas instrucciones específicas de recuperación.
**Golden Cache:** No

**Respuesta:**

Profe, entiendo que el bloqueo te impide usar la cuenta. Primero identifica **qué sistema** muestra el bloqueo:

- **Kactus/Seven (ERP):** la recuperación de contraseña por bloqueo se gestiona mediante la mesa de servicio, siguiendo el procedimiento institucional.
- **Portal de autogestión de Kactus:** si eres colaborador, debes solicitar el reinicio al área de Talento Humano.
- **Portal CovidApp:** el manual describe el desbloqueo como una acción para quien administra la aplicación: debe ubicar a la persona en el listado de usuarios bloqueados, seleccionarla, elegir la opción de desbloqueo e indicar el motivo. No intentes modificar el bloqueo desde una cuenta ajena.

Si se trata de otro sistema institucional, no tengo un procedimiento verificado para ese bloqueo. Puedes probar, como comprobación general y segura, cerrar sesión y volver a ingresar; si sigue bloqueado, contacta el canal de soporte institucional correspondiente al sistema. No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 45. Cuentas — incorrect (0.99)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: no recuerdo mi usuario del Portal Estudiantes, ¿cómo lo consulto?

**HTTP/latencia:** 200 / 11197.7 ms · **Rol inferido:** general · **Modelo/estado:** UniMon_SinDocumentacion / OFRECIENDO_RADICACION
**Fuente esperada:** Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf · **Incluida por API:** sin fuentes
**Fuentes reportadas:** sin fuentes
**Revisión:** Afirma que no hay documentación, aunque la evidencia indica ingresar el código de estudiante o número de identificación y presionar «Enviar»; además, la imagen menciona la opción «Recordar usuario».
**Golden Cache:** No

**Respuesta:**

Actualmente no me encuentro en la capacidad de responder a tu solicitud, ya que no dispongo de conocimiento, instructivo o procedimiento institucional documentado sobre la plataforma **Estudiantes**.

Puedes comunicarte directamente con los canales oficiales de soporte técnico TI para verificar el acceso y estado de tu cuenta:
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | PBX: (605) 3444333 Ext. 8003 / 8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129

¿O prefieres que radique un caso de soporte técnico por ti ahora mismo?

### 46. Cuentas — partial (0.97)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cómo cambio la contraseña de mi cuenta del Portal Estudiantes?

**HTTP/latencia:** 200 / 15221.7 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf
**Revisión:** La evidencia respalda que la contraseña restablecida sirve también para Aula Extendida y correo estudiantil, y cómo acceder al Portal. No respalda los pasos diferenciados por semestre, el enlace de restablecimiento ni los requisitos específicos de contraseña.
**Golden Cache:** No

**Respuesta:**

¡Buenas! Para cambiarla o restablecerla, sigue el paso que corresponda a tu situación:

**Si eres estudiante de primer semestre (nuevo ingreso):**
1. Revisa el pie de página de tu Recibo de Matrícula Financiera Web para encontrar tu usuario institucional y la contraseña temporal `unisimon`.
2. Ingresa a [Portal Estudiantes](https://www.unisimon.edu.co/portales) con esos datos.
3. En la ventana emergente obligatoria, establece una contraseña personal segura.

**Si eres estudiante regular (segundo semestre en adelante):**
1. Ingresa a [Portal Estudiantes](https://www.unisimon.edu.co/portales) y selecciona **Olvidé mi Usuario / Contraseña**.
2. Digita tu documento de identidad. Recibirás un enlace de restablecimiento en tu correo personal registrado; el enlace es válido por 24 horas.
3. Sigue el enlace para definir la nueva contraseña. Debe tener entre **8 y 15 caracteres**, incluir mayúsculas, minúsculas y al menos un número, y no contener datos personales como nombres, identificación, teléfono o fecha de nacimiento.

Una vez restablecida, esa misma contraseña te servirá para Aula Extendida y el Correo Estudiantil. Para ingresar al correo, accede desde la web de la Universidad, en **Servicios → Correo Estudiantes**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 47. Aula Extendida — partial (0.96)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Cómo accedo a Aula Extendida con mis credenciales institucionales?

**HTTP/latencia:** 200 / 14177.3 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Matricular_grupos_teams_moodle_Estudiante.pdf · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; instructivo portales estudiantes.pdf
**Revisión:** La contraseña unificada para Aula Extendida está respaldada, pero no se explica una ruta de acceso a esa plataforma. La opción de registro para estudiantes de Barranquilla proviene de un instructivo de crédito y no responde al acceso solicitado.
**Golden Cache:** No

**Respuesta:**

1. Entra primero al **Portal de Estudiantes** desde el sitio de la Universidad: http://www.unisimon.edu.co/ → **Portales**.
2. Si aún no has iniciado sesión o no recuerdas tu contraseña, selecciona **«Olvidé mi Usuario / Contraseña»**, ingresa tu código de estudiante o número de identificación y presiona **«Enviar»** para restablecerla. La contraseña nueva debe tener entre 8 y 15 caracteres, incluir mayúsculas, minúsculas y al menos un número, y no contener datos personales.
3. Usa esa misma contraseña para acceder a **Aula Extendida**. Si es la primera vez que te inscribes y estudias en Barranquilla, el instructivo indica que debes elegir **«Soy Inscrito por primera vez. (Solo para estudiante Barranquilla)»** y seguir el registro solicitado.

La guía disponible no especifica la ruta exacta para abrir Aula Extendida. Tampoco compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 48. Aula Extendida — incorrect (0.99)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Cómo encuentro los grupos de mis asignaturas en Moodle?

**HTTP/latencia:** 200 / 13605.8 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Estudiantes_Matricular grupos en teams ymoodle.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Estudiantes_Matricular grupos en teams ymoodle.pdf; Profesores_Integración teams y moodle.pdf; Videollamadas en  Teams.pdf; Autorización estudiantes en proceso de créditos_v2.pdf
**Revisión:** Las instrucciones sobre esperar unos segundos, matricular en Moodle, esperar tres minutos y el estado «No Activo» no están respaldadas. La evidencia solo indica ingresar al Portal de Estudiantes y seleccionar Calificaciones.
**Golden Cache:** No

**Respuesta:**

Para ubicar tus grupos de asignaturas en Moodle, entra al sistema donde consultas tus grupos y espera unos segundos mientras verifica el estado de cada uno. Si un grupo no aparece matriculado en Moodle, selecciona **«Matricular en Moodle…»** y espera aproximadamente 3 minutos para que se complete la asignación.

Si aparece como **«No Activo»**, significa que aún no se ha asignado un docente o que el grupo no existe en el aula. En ese caso, comunícate con el docente y espera a que se actualice el curso.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 49. Aula Extendida — correct (0.99)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿La contraseña del portal también sirve para correo estudiantil y Aula Extendida?

**HTTP/latencia:** 200 / 13605.2 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Activar Usuario y Correo institucional.pdf; Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf
**Revisión:** La respuesta coincide con la evidencia: la contraseña restablecida sirve para Portal de Estudiantes, Aula Extendida y Correo Estudiantil, y el correo se abre desde Servicios → Correo Estudiantes.
**Golden Cache:** Sí

**Respuesta:**

Sí. La misma contraseña te sirve para el Portal de Estudiantes, el Aula Extendida y el Correo Estudiantil.

Para entrar al correo, accede desde la página web de la Universidad, en **Servicios → Correo Estudiantes**. Si ingresas por otra vía, es posible que la cuenta no sea reconocida.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 50. Portales — correct (0.99)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Qué opción de sede debo elegir al ingresar al Portal Estudiantes de Barranquilla?

**HTTP/latencia:** 200 / 13116.1 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Activar Usuario y Correo institucional.pdf · **Incluida por API:** No
**Fuentes reportadas:** Instructivo - Estudiantes.pptx; Restablecimiento de contraseña.pptx; Certificados estudiantes_v2.pptx; Aspirantes - Reactivación de Inscripción.pdf; Gestión de Ingreso -  Funcionarios.pdf
**Revisión:** La sede Barranquilla y la ruta Portales → Portal Estudiantes están respaldadas por la evidencia proporcionada.
**Golden Cache:** No

**Respuesta:**

Buenas. Debes elegir la sede **Barranquilla** en la sección **Portal Estudiantes**. En el sitio de la Universidad, entra a **Portales**, selecciona **Portal Estudiantes** y luego **Barranquilla**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 51. Microsoft 365 — partial (0.91)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cómo instalo las aplicaciones de Office usando mi cuenta institucional?

**HTTP/latencia:** 200 / 12967.1 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Descarga e instalación Ms 365.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Descarga e instalación Ms 365.pdf
**Revisión:** La evidencia respalda iniciar sesión con la cuenta institucional y seleccionar «Instalar Office», pero no respalda varios pasos adicionales mencionados, como «Otras opciones de instalación» y aceptar el contrato.
**Golden Cache:** No

**Respuesta:**

Claro, te acompaño con la instalación de Office usando tu cuenta institucional:

1. Ingresa al portal institucional de TI con tu cuenta y contraseña. No compartas esos datos con nadie.
2. Selecciona **Otras opciones de instalación** y luego **Instalar Office**.
3. Sigue las indicaciones en pantalla y espera a que termine la descarga e instalación; mantén el equipo conectado a Internet.
4. Cuando finalice, haz clic en **Cerrar**.
5. Abre una aplicación de Office y acepta el contrato de licencia cuando aparezca.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 52. Microsoft 365 — correct (0.96)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Cómo agrego a una persona a un equipo o grupo de Microsoft Teams?

**HTTP/latencia:** 200 / 12599.8 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Agregar_miembros_Grupos_MS_Teams.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Crear reuniones No asociadas a grupos.pdf; Profesores_Integración teams y moodle.pdf; Grupos_en_Teams.pdf; Agregar_miembros_Grupos_MS_Teams.pdf
**Revisión:** Indica seleccionar el equipo y usar «Más opciones» → «Agregar miembro», pasos respaldados por la guía; las recomendaciones finales no contradicen la evidencia.
**Golden Cache:** Sí

**Respuesta:**

Buenas. Como docente, puedes agregar miembros así:

1. En Microsoft Teams, ve a **Equipos** y selecciona el equipo al que quieres agregar a la persona.
2. Busca **Más opciones** del equipo y selecciona **Agregar miembro**.
3. Busca a la persona y selecciónala para agregarla. En el flujo de creación de grupos también se indica buscar cada usuario y pulsar **Agregar**.

Si no encuentras la opción o la persona no aparece, no intentes cambiar permisos: verifica que estás en el equipo correcto y que el nombre esté bien escrito.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 53. Microsoft 365 — partial (0.94)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Cómo cambio o administro los participantes de una reunión de Teams?

**HTTP/latencia:** 200 / 13125.0 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Ajustes participantes reuniones Ms Teams.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** P-GT-13_Procedimiento_para_la_gestion_de_requerimientos_de_recursos_y_soluciones_tecnologicas.pdf; Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf; Ajustes participantes reuniones  Ms Teams.pdf
**Revisión:** La guía respalda ajustes de roles y permisos, pero la respuesta no explica cómo agregar o quitar participantes y describe un ajuste de roles específico.
**Golden Cache:** No

**Respuesta:**

Para administrar quién participa en una reunión de Teams, puedes ajustar las opciones de los asistentes:

1. Abre las opciones de la reunión. Se abrirá una nueva pestaña.
2. En las dos listas desplegables, selecciona **Solo yo** y luego elige **Guardar**.
3. Con ese ajuste, los demás participantes ingresarán como **Asistentes**: podrán hablar, compartir video, participar en el chat y ver los archivos que otra persona comparta.

La guía disponible documenta este ajuste de roles, pero no explica cómo agregar o quitar participantes de la invitación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 54. Microsoft 365 — partial (0.93)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Cómo programo una reunión de Teams desde un iPad?

**HTTP/latencia:** 200 / 12362.2 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Crear reuniones No asociadas a grupos.pdf; Grabar videollamadas en Teams.pdf; Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf
**Revisión:** La evidencia confirma el acceso a Calendario y que la reunión creada aparece allí, pero no respalda los pasos de «Nueva reunión», «Guardar» ni «Reunirse ahora» en iPad.
**Golden Cache:** No

**Respuesta:**

Claro. En Teams desde tu iPad:

1. Abre **Calendario** y selecciona **Nueva reunión**.
2. Completa los campos de la reunión y agrega a los asistentes.
3. Pulsa **Guardar**. Luego podrás seleccionar la reunión en el calendario para unirte.

Si solo necesitas empezar una reunión en ese momento, ve a **Calendario** y selecciona **Reunirse ahora**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 55. Microsoft 365 — partial (0.95)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Dónde consulto los grupos de Teams asociados a mis cursos?

**HTTP/latencia:** 200 / 12964.6 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Grupos_en_Teams.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Profesores_Integración teams y moodle.pdf; Grupos_en_Teams.pdf; Videollamadas en  Teams.pdf; Agregar_miembros_Grupos_MS_Teams.pdf; Fucionarios_Integración Moodle y Teams.pdf
**Revisión:** Aporta información sobre estados de asignación y matrícula, pero «Ver integración» y la ruta para consultar los grupos no están respaldadas por la evidencia citada.
**Golden Cache:** No

**Respuesta:**

Para consultar la integración de Teams asociada a un curso, la guía indica revisar el grupo correspondiente y seleccionar **«Ver integración»**. Allí podrás ver el listado de profesores y estudiantes del curso y su estado en Teams y Moodle.

Si una persona aparece sin asignar o matricular, las opciones documentadas para actualizar son **«Asignar»** o **«Matricular»** en su registro, o **«Matricular Curso en Teams»** para actualizar el curso completo. La guía disponible no especifica la ruta exacta para llegar al listado de grupos.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 56. Aula Extendida — partial (0.94)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Qué debo revisar si un curso duplicado sigue apareciendo en Teams o Aula Extendida?

**HTTP/latencia:** 200 / 13844.8 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Depuración de cursos (Teams y Aula Extendida).pdf · **Incluida por API:** No
**Fuentes reportadas:** Grabar un clase en Teams y compartir en Stream.pdf; Movilidad Académica - Estudiantes.pdf; Fucionarios_Integración Moodle y Teams.pdf; Profesores_Integración teams y moodle.pdf
**Revisión:** La evidencia apunta a un procedimiento de depuración y a confirmar el proceso, pero la respuesta no ofrece sus pasos y agrega comprobaciones generales no documentadas.
**Golden Cache:** No

**Respuesta:**

¡Claro! Si el curso duplicado sigue apareciendo, revisa primero **en qué plataforma lo ves**:

1. **En Teams:** confirma que sea realmente un curso duplicado y no otro equipo con un nombre similar. La guía institucional indica que los cursos asignados aparecen en la sección **Equipos**. Si eres docente, la integración permite verificar la asignación de participantes y usar **«Matricular Curso en Teams»** para actualizar el curso completo; no lo uses para borrar el duplicado.
2. **En Aula Extendida:** no tengo un procedimiento institucional verificado para eliminar u ocultar cursos duplicados. Como comprobación general y segura, actualiza la página o cierra y vuelve a abrir la plataforma para confirmar que el curso aún aparece.
3. Si el duplicado persiste, evita eliminarlo o cambiar matrículas por tu cuenta: eso podría afectar el curso correcto. Haría falta que el área responsable revise cuál es el curso válido y cómo retirar el duplicado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 57. Microsoft 365 — incorrect (0.98)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Cómo se graba una videollamada de Teams?

**HTTP/latencia:** 200 / 12965.7 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Grabar videollamadas en Teams.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Grabar videollamadas en Teams.pdf
**Revisión:** La evidencia solo respalda seleccionar el curso y unirse; no respalda iniciar la grabación, su disponibilidad para el grupo ni las indicaciones sobre permisos.
**Golden Cache:** No

**Respuesta:**

1. En Teams, ve a **Equipos** en el panel izquierdo y selecciona el curso donde realizarás la videollamada.
2. Abre la reunión a la que quieres unirte y selecciona **Unirse**.
3. Ya dentro de la reunión, selecciona **Más acciones** y luego **Iniciar grabación**. Teams te indicará cuando la grabación haya comenzado.
4. Al finalizar la reunión, la grabación estará disponible para los miembros del grupo.

Si no aparece la opción **Iniciar grabación**, no intentes cambiar permisos o configuraciones: consulta con el organizador de la reunión o con el soporte correspondiente.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 58. Microsoft 365 — correct (0.97)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Qué cuenta debo usar para entrar a las herramientas Microsoft institucionales?

**HTTP/latencia:** 200 / 11850.0 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Credenciales microsoft.pdf · **Incluida por API:** No
**Fuentes reportadas:** Videollamadas en  Teams.pdf; Demo tipos de admisión.pptx; Descarga e instalación Ms 365.pdf
**Revisión:** La guía indica acceder al Portal de Gestión Académico-Administrativa para obtener las credenciales de Microsoft; la respuesta resume ese acceso sin divulgar datos sensibles.
**Golden Cache:** No

**Respuesta:**

Hola. Para ingresar a las herramientas Microsoft institucionales, usa el usuario y la clave indicados en el **Portal de Gestión Académico-Administrativa**. No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 59. Microsoft 365 — partial (0.91)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Cuál es el acceso indicado para abrir Microsoft Teams como estudiante?

**HTTP/latencia:** 200 / 12965.3 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Como_acceder_MS_Teams_Estudiantes.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf; Instructivo Credito Empresarial.pptx; Como_acceder_MS_Teams_Estudiantes.pdf; Descarga e instalación Ms 365.pdf
**Revisión:** La evidencia respalda iniciar sesión con usuario y contraseña de Microsoft, pero no respalda la ruta «Servicios → Correo Estudiantes».
**Golden Cache:** No

**Respuesta:**

Como estudiante, accede al sitio web de Unisimón y ve a **Servicios → Correo Estudiantes**. Inicia sesión en tu correo institucional de Microsoft; luego podrás acceder a Microsoft Teams.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 60. Docentes — incorrect (0.99)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Cómo diligencio el PAC como profesor?

**HTTP/latencia:** 200 / 12068.0 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Diligenciamiento de PAC (Profesores).pdf · **Incluida por API:** No
**Fuentes reportadas:** Bienestar universitario manual.pptx; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf; Asignación Académica.pptx
**Revisión:** La evidencia sí documenta el acceso al Portal Profesores y Administrativos y completar filtros para pulsar «Diligenciar»; la respuesta afirma que no dispone de ese procedimiento.
**Golden Cache:** No

**Respuesta:**

Buenas. La información disponible no incluye el procedimiento para diligenciar el PAC como profesor, así que no quiero indicarte pasos que podrían no corresponder a esa plataforma.

Como comprobación general, confirma que ingresaste con tu propia cuenta y que estás en el sistema institucional correcto. Si el formulario no aparece o no puedes avanzar, indícame qué pantalla o mensaje ves (sin compartir contraseñas ni códigos) para orientarte con seguridad.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 61. Docentes — no_verificable (0.96)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Quién puede habilitar permisos de PAC para un director de programa?

**HTTP/latencia:** 200 / 14559.1 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Habilitar permisos PAC (Director de programa).pdf · **Incluida por API:** No
**Fuentes reportadas:** retorno al campus 2021.pdf; Instructivo Credito Empresarial.pptx; Bloqueos, Sanciones y Excepciones.pptx
**Revisión:** La evidencia no identifica quién habilita permisos PAC; solo menciona que las acciones disponibles dependen de los permisos del usuario.
**Golden Cache:** No

**Respuesta:**

Los fragmentos indican que las opciones y acciones disponibles en el sistema dependen de los permisos asociados a cada usuario. Sin embargo, no especifican quién puede habilitar permisos de PAC para un director de programa ni el trámite para solicitarlos; ese es el dato que falta.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 62. Docentes — correct (0.91)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Dónde se configura la evaluación profesoral para funcionarios?

**HTTP/latencia:** 200 / 12820.5 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Configuracion de Evaluacion Profesoral - Funcionarios.pptx · **Incluida por API:** No
**Fuentes reportadas:** Jefe Inmediato - Funcionarios.pdf; Reportes de Caracterización.pptx; Manual Evaluación CAQ - Funcionarios.pdf; Evaluacion Profesoral - Estudiante.pdf; Configuracion de Evaluaciones.pptx
**Revisión:** Indica la ruta de configuración y la selección de CAQ o KOLB seguida de «Crear», respaldadas por el instructivo.
**Golden Cache:** No

**Respuesta:**

Buenas. Para configurar la evaluación profesoral para funcionarios:

1. Ingresa al aplicativo de evaluación CAQ.
2. Selecciona el módulo **Configuración**.
3. Entra en **Configuración de Evaluaciones**.
4. Selecciona el tipo de evaluación correspondiente (**CAQ** o **KOLB**) y presiona **Crear** para configurar la oferta.

La documentación disponible no detalla los pasos posteriores a **Crear**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 63. Docentes — partial (0.98)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Cómo se configuran las evaluaciones de un curso?

**HTTP/latencia:** 200 / 14215.2 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Configuracion de Evaluaciones.pptx · **Incluida por API:** No
**Fuentes reportadas:** P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; Manual Evaluación CAQ - Funcionarios.pdf; Estadísticas institucionales.pdf; Matricula (2).pptx
**Revisión:** Identifica la sección de configuración, pero omite los pasos documentados de seleccionar CAQ o KOLB y presionar «Crear».
**Golden Cache:** No

**Respuesta:**

Si te refieres al aplicativo de Evaluación CAQ, el instructivo para funcionarios indica que, después de ingresar, debes seleccionar el módulo **Configuración**. La documentación disponible no detalla los pasos siguientes para configurar las evaluaciones de un curso, así que no puedo confirmar qué opciones elegir ni qué datos registrar.

Si hablas de otra plataforma, dime cuál; el procedimiento puede ser distinto.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 64. Gestión académica — partial (0.97)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Cómo registro las causas de deserción o ausencia de estudiantes?

**HTTP/latencia:** 200 / 13178.7 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Ingreso de Causas de Desertores y Ausentes.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** instructivo desertores y ausentes.pptx; Ingreso de Causas de Desertores y Ausentes.pdf; Instructivo Atencion a Estudiantes (Tutorías).pdf; Calificaciones.pdf; Manual de Usuario - Portal CovidApp.pdf; Calificaciones Posgrados-S3-DITI-PC07.pdf
**Revisión:** Explica cómo elegir y guardar la causa, pero omite completar los filtros y buscar al estudiante.
**Golden Cache:** No

**Respuesta:**

Claro, profe. En el sistema, selecciona al estudiante correspondiente, elige la causa de deserción o ausencia en la lista desplegable y presiona **Aceptar**. La causa debería actualizarse para ese estudiante.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 65. Gestión académica — incorrect (0.99)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Qué instructivo explica la parametrización de desertores y ausentes?

**HTTP/latencia:** 200 / 12979.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** instructivo parametrizacion desertores y ausentes.pptx · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Reportes de Desertores.pdf; Instructivo Módulo Atención Estudiantes (Completo).pdf; Videollamadas en  Teams.pdf; instructivo portales estudiantes.pptx
**Revisión:** La evidencia sí identifica el instructivo de parametrización y señala que se debe ingresar al módulo «Desertores»; la respuesta confunde ese trámite con la generación de reportes.
**Golden Cache:** No

**Respuesta:**

El instructivo de **Reportes de Desertores** explica cómo generar el reporte: completar los filtros de año, periodo y tipo de deserción, y luego seleccionar **Buscar**. No encuentro en la documentación disponible pasos de parametrización para desertores y ausentes.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 66. Matrícula — partial (0.86)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Qué autorización necesito para inscribirme en un curso de énfasis?

**HTTP/latencia:** 200 / 12978.7 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Autorizacion de Inscripcion Curso de Enfasis.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Autorizacion de Inscripcion Curso de Enfasis.pptx; Instructivo autorizaciones grados.pdf; Autorización estudiantes en proceso de créditos.pdf; Autorización estudiantes en proceso de créditos_v2.pdf
**Revisión:** Nombra la autorización pertinente, pero la recomendación de consultar al Programa Académico no está respaldada por la evidencia.
**Golden Cache:** No

**Respuesta:**

¡Buenas! La autorización que necesitas es la **Autorización de Inscripción de Curso de Énfasis**. El instructivo disponible describe cómo el personal autorizado crea ese registro en SIAAF WEB, pero no indica cómo solicitarlo como estudiante ni si debes gestionarlo con una dependencia específica. Te recomiendo consultar con tu Programa Académico para que te indiquen cómo tramitarla.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 67. Matrícula — partial (0.92)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Cómo se autorizan cursos intersemestrales?

**HTTP/latencia:** 200 / 13649.4 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Autorizaciones cursos intersemestrales.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Inscripcion de cursos intersemestrales.pdf; Matricula de Cursos Intersemestrales.pptx; Autorizaciones cursos intersemestrales.pptx
**Revisión:** Ofrece pasos para la sección de autorización y distingue la inscripción del estudiante, pero no explica cómo se completa la autorización más allá de elegir filtros.
**Golden Cache:** No

**Respuesta:**

Entiendo que es tu primera vez y el proceso puede resultar confuso. La autorización se realiza en SIA Web y, estos pasos son para quien autoriza las matrículas:

1. Entra a **unisimon.edu.co** y, desde el menú principal, selecciona **Portales**.
2. Ingresa a SIA Web y abre el módulo **Matrícula**.
3. Entra en **Autorización de cursos intersemestrales**.
4. Selecciona los filtros de **año, periodo, programa y curso** para buscar las matrículas.

El instructivo no detalla qué opciones debe elegir un estudiante ni confirma si tiene acceso a esa sección. Para inscribir tus propios cursos, el proceso documentado es distinto: entra al módulo **Cursos Intersemestrales**, selecciona los cursos habilitados y pulsa **Inscribir**; al final, confirma la inscripción.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 68. Grados — incorrect (0.99)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Cómo presento la solicitud de inscripción para grado?

**HTTP/latencia:** 200 / 14671.9 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Solicitud de inscripción para grado.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Solicitud de inscripción para grado.pdf; Gestión de inscripciones.pdf
**Revisión:** Presenta numerosos pasos y condiciones que no están respaldados por los fragmentos de evidencia proporcionados.
**Golden Cache:** No

**Respuesta:**

1. Ingresa al Portal de Estudiantes y selecciona **«Solicitud de inscripción para grado»**. El módulo se muestra si estás en el último semestre, hay una oferta de inscripción activa para tu programa o ya tienes una inscripción en curso.
2. Selecciona el programa académico para el cual harás la solicitud.
3. Revisa el estado de los requisitos previos. Si el botón **«Inscripción para grado»** está inhabilitado porque alguno aparece como **«Pendiente»**, consulta con el área correspondiente —por ejemplo, tu Programa académico u Oficina de créditos— para verificarlo.
4. Si el botón está habilitado, selecciónalo y completa las pestañas del formulario, leyendo los mensajes informativos. Envía la solicitud.
5. Después del envío, recibirás información sobre la verificación y un correo que notificará el inicio del proceso. Podrás visualizar y descargar el formulario diligenciado como constancia de inicio; no tienes que firmarlo ni agregarle datos. Ese formulario no significa que la solicitud ya fue aprobada: la decisión te llegará por correo después de que verifiquen los requisitos.
6. Si te notifican que fue aprobada, vuelve al módulo para descargar el volante de pago y la constancia de inscripción a grado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 69. Grados — incorrect (1.0)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Qué pasos se realizan en el sistema para graduar a un estudiante?

**HTTP/latencia:** 200 / 13076.2 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Graduar.pptx · **Incluida por API:** No
**Fuentes reportadas:** Solicitud de inscripción para grado.pdf; Movilidad Académica - Estudiantes.pdf; Bloqueos, Sanciones y Excepciones.pptx; Instructivo Módulo Atención Estudiantes (Completo).pdf; Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf
**Revisión:** Afirma que no hay procedimiento, aunque la evidencia indica buscar al estudiante, seleccionar su programa y presionar «Graduar».
**Golden Cache:** No

**Respuesta:**

Claro. La documentación disponible no incluye el procedimiento para graduar a un estudiante, así que no puedo indicarte pasos del sistema sin verificarlos. Para el trámite de grado, consulta con la dependencia académica correspondiente de la Universidad.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 70. Grados — partial (0.95)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Cómo se revisa o aprueba el cumplimiento de requisitos para grado?

**HTTP/latencia:** 200 / 13547.8 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Instructivo Aprobación de Requisitos.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Gestión de Ingreso -  Funcionarios.pdf; Gestión de Ingreso -  Solo Consulta .pdf; Solicitud de inscripción para grado.pdf; Instructivo Aprobación de Requisitos.pdf; Aprobación de Requisitos.pptx
**Revisión:** Explica de forma respaldada quién aprueba requisitos documentales y cómo se tratan las pruebas, pero agrega detalles sobre la solicitud de grado que no constan en la evidencia.
**Golden Cache:** No

**Respuesta:**

Buenas. Para revisar los requisitos de una solicitud de grado:

1. En la etapa de solicitud, consulta los **requisitos de cumplimiento previo**. El sistema verifica su estado automáticamente.
2. Si alguno aparece **pendiente**, no se habilitará el botón **«Inscripción para grado»**. Debes comunicarte con la dependencia responsable de ese requisito para verificar su estado.
3. Cuando todos los requisitos previos estén cumplidos, reúne los documentos requeridos escaneados en formato PDF y selecciona **«Inscripción para grado»** para iniciar la solicitud.

La revisión de documentos cargados por aspirantes corresponde al área u oficina responsable de cada requisito. Un usuario de esa área, sujeto a sus permisos, puede revisarlos y aprobarlos; también puede visualizar y descargar el documento o reemplazarlo si no cumple lo solicitado o está dañado. Las pruebas o evaluaciones, en cambio, se marcan como realizadas automáticamente al completarse.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 71. Admisiones — correct (0.99)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Qué debo hacer para solicitar la homologación de asignaturas?

**HTTP/latencia:** 200 / 13840.9 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Homologaciones.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Homologaciones.pdf; Proyección (agregar, elimnar, homologar).pptx; Instructivo Módulo Atención Estudiantes (Completo).pdf
**Revisión:** Resume los pasos de homologación y las restricciones para períodos históricos y validaciones tal como aparecen en la evidencia.
**Golden Cache:** Sí

**Respuesta:**

Para homologar asignaturas en la proyección académica:

1. En el sistema, selecciona el botón **«HO»**.
2. Elige el semestre al que pertenece el curso que deseas homologar.
3. Selecciona uno o más cursos de la lista y pulsa **«Agregar»**.
4. Al cerrar la ventana, el listado de calificaciones debería actualizarse con los cambios.

Esta opción está disponible solo para **períodos históricos**. El sistema también valida los criterios de calificaciones y demás condiciones establecidas para el proceso; si no te permite agregar un curso, puede que no cumplas alguno de esos criterios.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 72. Admisiones — incorrect (0.99)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Cómo se anula o modifica un programa en una preinscripción?

**HTTP/latencia:** 200 / 14426.2 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Anulación y Modificación de Programa Pre-inscripciones.pptx · **Incluida por API:** No
**Fuentes reportadas:** Gestión de Ingreso -  Funcionarios.pdf; Bloqueos, Sanciones y Excepciones.pptx; Gestión de Ayudas Educativas.pdf; Instructivo autorizaciones grados.pdf
**Revisión:** Afirma que la documentación no explica cómo anular, pero la evidencia indica que la opción «Anular» permite anular la preinscripción. Además, la respuesta no ofrece esos pasos.
**Golden Cache:** No

**Respuesta:**

Buenas. Para modificar el programa de una preinscripción, el instructivo de Gestión de Ingreso indica que se debe usar la opción **Editar** del registro; permite cambiar el programa y/o el tipo de admisión. No especifica la ruta para encontrar esa opción, así que no puedo confirmar dónde aparece en tu acceso.

Ten en cuenta estas condiciones:

- Si la preinscripción tiene una inscripción asociada, primero hay que modificar la inscripción para que coincida con los datos de la preinscripción.
- Si tiene un volante de pago, el programa solo se modifica en el volante si aún no está pagado. Si ya está pagado, el cambio en la preinscripción no modifica el volante; este debe ajustarse mediante el procedimiento establecido para ello.

La documentación recuperada no explica cómo **anular** una preinscripción ni confirma que esta opción esté disponible para docentes. Si no ves **Editar** o necesitas anular el registro, consulta con el área autorizada para gestionar preinscripciones.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 73. Admisiones — no_verificable (0.96)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Qué tipos de admisión contempla el proceso para aspirantes?

**HTTP/latencia:** 200 / 12822.0 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Demo tipos de admisión.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Instructivo Aprobación de Requisitos.pdf; Demo tipos de admisión.pptx; Aprobación de Requisitos.pptx; Gestión de Ingreso -  Funcionarios.pdf; Reporte de aprobadas vs ejecutadas.pdf
**Revisión:** La evidencia aportada no permite confirmar que los tipos sean «Primer ingreso» y «Reinicio de un periodo»; solo se identifica este último en la descripción de una imagen.
**Golden Cache:** No

**Respuesta:**

La documentación disponible distingue **Primer ingreso** y **Reinicio de un periodo** como tipos de admisión para aspirantes. No detalla las condiciones ni los pasos de cada tipo.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 74. Admisiones — correct (0.98)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Cómo verifico y apruebo los requisitos de un aspirante?

**HTTP/latencia:** 200 / 14161.0 ms · **Rol inferido:** otros · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aprobación de Requisitos.pptx · **Incluida por API:** No
**Fuentes reportadas:** Gestión de Ingreso -  Funcionarios.pdf; Gestión de inscripciones.pdf; Instructivo Aprobación de Requisitos.pdf
**Revisión:** Explica la revisión, aprobación y actualización de requisitos, e incluye la confirmación de inscripción y la restricción sobre quién gestiona la solicitud.
**Golden Cache:** No

**Respuesta:**

Claro, profe. Para revisar los requisitos de un aspirante:

1. En la solicitud de inscripción, selecciona **Ver requisitos** o **Requisitos**. Allí se listan los requisitos asociados al programa.
2. En cada requisito, selecciona **Ver** para visualizar el documento y, si corresponde, descargarlo. Comprueba que cumpla con lo solicitado.
3. Selecciona **Aprobar requisito** si está conforme. Esta acción puede depender de tus permisos; además, los requisitos que sean pruebas o evaluaciones se marcan como realizados automáticamente cuando se completan.
4. Si un documento no cumple o está dañado, el sistema permite actualizarlo o reemplazarlo. Si no tienes esa opción o no cuentas con permisos, detente y consulta con el área responsable del requisito.
5. Ten en cuenta que, al aprobar el primer requisito, la solicitud queda a cargo del usuario que realizó esa aprobación: otro usuario no podrá continuar gestionándola.
6. Cuando todos los requisitos estén aprobados, selecciona **Confirmar inscripción**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 75. Admisiones — partial (0.87)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Dónde puedo consultar la hoja de vida de matrícula de un estudiante?

**HTTP/latencia:** 200 / 12937.1 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Consulta de Hoja de Vida - Matrículas.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Nueva Hoja de Vida.pdf; Bienestar universitario manual.pptx; Consulta de Hoja de Vida - Matrículas.pdf; Instructivo Credito Empresarial.pptx
**Revisión:** Indica correctamente que se ingresa por el icono «Matrícula», pero la evidencia aportada no respalda los pasos de búsqueda ni la selección del icono «Hoja de vida» en los resultados.
**Golden Cache:** No

**Respuesta:**

Hola. En SIA WEB, puedes consultar la hoja de vida de matrícula así:

1. Selecciona el icono **Matrícula**.
2. Elige el tipo de búsqueda, escribe el texto o número correspondiente y haz clic en **Buscar**.
3. En los resultados, selecciona el icono **Hoja de vida**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 76. Cuentas — correct (0.99)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cómo consulto si un estudiante tiene excepciones, bloqueos o sanciones?

**HTTP/latencia:** 200 / 13662.7 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Consulta de Excepciones, bloqueos y sanciones.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Bloqueos, Sanciones y Excepciones.pptx; Manual de Usuario - Portal CovidApp.pdf; Consulta de Excepciones, bloqueos y sanciones.pdf; Matricula (2).pptx
**Revisión:** Coincide con el procedimiento de consulta descrito e informa que también pueden descargarse reportes y que las opciones dependen de los permisos.
**Golden Cache:** Sí

**Respuesta:**

¡Buenas! Si tienes acceso al módulo de consulta, puedes revisar la información así:

1. Selecciona **Bloqueos**, **Sanciones** o **Excepciones**.
2. Elige uno de los criterios de búsqueda disponibles y pulsa **Buscar**.
3. Si necesitas el resultado en un archivo, también puedes descargar el reporte en formato Excel.

Las opciones visibles dependen de los permisos de tu usuario. Los pasos documentados corresponden a un módulo de consulta, pero no confirman que esté disponible para estudiantes; si no lo ves o no tienes acceso, consulta el canal institucional autorizado para este trámite.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 77. Cuentas — partial (0.91)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Qué pasos muestra el instructivo para gestionar bloqueos de usuarios?

**HTTP/latencia:** 200 / 13663.2 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Instructivo Bloqueos.pdf · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Manual de Usuario - Registro de Ingreso.pdf; Bloqueos, Sanciones y Excepciones.pptx
**Revisión:** Describe la creación de un bloqueo y advierte sobre permisos, pero la evidencia no respalda explícitamente la ruta «Concepto» y «Nuevo»; además, la consulta pide cómo gestionar bloqueos en general.
**Golden Cache:** No

**Respuesta:**

El instructivo describe cómo **crear un bloqueo**:

1. En el campo **Concepto**, selecciona **Bloqueos** y luego pulsa **Nuevo**.
2. En la ventana emergente, ingresa el número de identificación o código del estudiante y presiona **Enter** para cargar sus datos básicos.
3. Completa los demás campos y selecciona **Guardar**.

Ten en cuenta que las opciones y acciones disponibles dependen de los permisos asociados a tu usuario. Como estudiante, si no ves estas opciones, no intentes gestionar bloqueos de otros usuarios; consulta con la dependencia autorizada para este trámite.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 78. Cuentas — correct (0.98)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿En qué módulo se revisan bloqueos y sanciones asociados a estudiantes?

**HTTP/latencia:** 200 / 12820.5 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Bloqueos, Sanciones y Excepciones.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Gestión de Ingreso -  Funcionarios.pdf; Manual de Usuario - Portal CovidApp.pdf; Bloqueos, Sanciones y Excepciones.pptx; Consulta de Excepciones, bloqueos y sanciones.pdf; Videollamadas en  Teams.pdf
**Revisión:** Identifica el módulo correspondiente y resume la búsqueda por Bloqueos o Sanciones, de acuerdo con la evidencia.
**Golden Cache:** Sí

**Respuesta:**

Hola. Se revisan en el módulo de **Bloqueos, Sanciones y Excepciones**. Allí selecciona **Bloqueos** o **Sanciones**, elige un criterio de búsqueda y pulsa **Buscar** para consultar la información asociada al estudiante. Las opciones disponibles dependen de los permisos de tu usuario.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 79. Créditos — no_verificable (0.99)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Cómo se tramita una autorización para estudiantes en proceso de crédito?

**HTTP/latencia:** 200 / 13471.2 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Autorización estudiantes en proceso de créditos_v2.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Solicitud de inscripción para grado.pdf; Autorización estudiantes en proceso de créditos_v2.pdf; Autorización estudiantes en proceso de créditos.pdf; P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf
**Revisión:** La evidencia confirma el acceso a la opción de autorización, pero no respalda los filtros, la búsqueda, la selección de grupos ni la condición sobre la asignación académica.
**Golden Cache:** No

**Respuesta:**

Claro. El trámite se realiza así:

1. En el módulo, selecciona **«Estudiantes en proceso de créditos»** y luego **«Autorización de estudiantes en proceso de créditos»**.
2. Completa los filtros de **año, periodo y documento**, y presiona **«Buscar»**.
3. Cuando aparezca el estudiante, presiona la **lupa** del curso que corresponda.
4. Revisa los grupos teóricos y horarios disponibles, selecciona el grupo correspondiente y presiona **«Seleccionar Grupo»**.

Los grupos y horarios se muestran según la asignación académica que haya creado previamente el programa académico.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 80. Créditos — incorrect (1.0)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Cómo se aprueba una solicitud de crédito estudiantil?

**HTTP/latencia:** 200 / 13470.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Aprobacion Solicitudes de credito.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Gestión de Ingreso -  Funcionarios.pdf; P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf; Aprobacion Solicitudes de credito.pptx
**Revisión:** La evidencia sí contiene una sección de aprobación y señala confirmar la aprobación o el rechazo. La respuesta niega que haya procedimiento y añade contactos no respaldados.
**Golden Cache:** No

**Respuesta:**

Buenas. El instructivo disponible explica cómo registrar una solicitud de Crédito Empresarial, pero no incluye el procedimiento para aprobarla. Sí indica que las notificaciones de aprobación o rechazo llegan por correo.

Para consultar el estado de tu solicitud, revisa el correo asociado al trámite. Si necesitas que te orienten sobre la aprobación, puedes contactar al área de Crédito Empresarial:

- **Barranquilla:** credemp@unisimonbolivar.edu.co (atención a estudiantes ICETEX) o usb.facturacion@unisimonbolivar.edu.co; 3444333, ext. 105.
- **Cúcuta:** creditoempresarialcucuta@unisimonbolivar.edu.co; 3153196571 o 5827070, ext. 110.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 81. Pagos — partial (0.94)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cómo verifico en el sistema si un pago ya fue aplicado?

**HTTP/latencia:** 200 / 13080.8 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Instructivo Verificación pagos V2.pdf · **Incluida por API:** No
**Fuentes reportadas:** Inscripción.pptx; Pagos en Linea.pptx; Autorización de Supletorios.pdf; Matricula (2).pptx; Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf
**Revisión:** Indica que el comprobante puede descargarse y reconoce que la evidencia no confirma el estado de aplicación, pero no da la ruta documentada al módulo «Verificación de pagos».
**Golden Cache:** No

**Respuesta:**

Puedes verificarlo desde el Portal de Estudiantes: busca el comprobante de pago generado y revisa que corresponda al pago que realizaste. La documentación disponible indica que el comprobante se descarga desde ese portal, pero no detalla una pantalla o estado específico para confirmar que el pago ya fue aplicado.

Si no aparece el comprobante o no puedes confirmar el pago, conserva el comprobante de tu entidad financiera y consulta los canales oficiales de la Universidad para verificar el registro.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 82. Pagos — partial (0.91)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Dónde consulto los anexos o el detalle de una factura?

**HTTP/latencia:** 200 / 13256.8 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Detalle factura (Anexos).pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf; Pagos en Linea.pptx; Detalle factura (Anexos).pptx
**Revisión:** Indica el módulo y cómo consultar el detalle con el número de factura o interno; la ruta inicial por Portales y App no está respaldada por la evidencia citada.
**Golden Cache:** No

**Respuesta:**

Buenas. Como docente, puedes consultar el detalle de una factura en SIAAF WEB:

1. Entra al sitio de la Universidad y selecciona **Portales** en el menú principal.
2. Ingresa al módulo **App**.
3. Selecciona **Factura (Anexos)**.
4. Escribe el número de factura o el número interno y presiona **Visualizar** para ver el detalle.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 83. Pagos — incorrect (0.97)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Qué información institucional está disponible sobre bancos y cuentas para pagos?

**HTTP/latencia:** 200 / 12886.4 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Bancos y cuentas_v1_20211007.pdf · **Incluida por API:** No
**Fuentes reportadas:** Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf; Estadísticas institucionales.pdf; SITE 2.0.pptx
**Revisión:** Omite que la documentación describe un listado de bancos activos en Contabilidad y la creación de cuentas bancarias; en cambio, afirma que no se detalla esa información.
**Golden Cache:** No

**Respuesta:**

La información disponible indica que el sistema Paymentez permite consultar transacciones y filtrar por método de pago, fecha, zona horaria o moneda. Para ver una transacción específica, se puede buscar por cédula o correo del cliente y seleccionar el App Code asociado al comercio.

La documentación recuperada no detalla qué bancos o cuentas institucionales reciben pagos ni publica sus datos bancarios.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 84. Financiero — incorrect (0.99)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Cómo se gestiona un reporte de notas crédito?

**HTTP/latencia:** 200 / 13831.1 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Gestión de Notas Crédito.pdf · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Reportes generales.pptx; Instructivo Reportes Consolidados.pdf; Calificaciones.pdf; Bloqueos, Sanciones y Excepciones.pptx; Solicitud de crédito.pptx
**Revisión:** Desvía la consulta a reportes de Crédito Interno, sin respaldo en la evidencia; la guía pertinente es la de Gestión de Notas Crédito.
**Golden Cache:** No

**Respuesta:**

Claro, profe. Si te refieres a un **reporte de notas relacionado con Crédito Interno**, la guía disponible indica esta ruta:

1. Ingresa al sistema que utilizas para la gestión académica.
2. Selecciona el módulo **«Crédito»**.
3. Entra en **«Crédito Interno»** y luego en **«Reportes»**.
4. Al seleccionar **«Exportar»**, se abrirá otra pestaña y se descargará un archivo **.csv**. Para algunos reportes, la descarga viene dentro de un **.zip**; en el reporte de Variación de notas, el .csv depende del rango de fechas elegido.

La documentación no aclara cuál reporte específico corresponde a «notas crédito» ni cómo seleccionarlo. Si te refieres al registro o corrección de notas oficiales, eso se gestiona con el docente o la Dirección de Programa, no mediante un reporte de Crédito Interno.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 85. Financiero — partial (0.89)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Dónde se configura la liquidación de servicios académicos?

**HTTP/latencia:** 200 / 12980.8 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Liquidacion de servicios academicos - Configuración.pptx · **Incluida por API:** No
**Fuentes reportadas:** Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf; Bienestar universitario manual.pptx; Instructivo Módulo Atención Estudiantes (Completo).pdf
**Revisión:** Es prudente al no inventar una ruta, pero no aprovecha que la guía sí describe la configuración de descuentos según año, periodo, nivel académico y tipo de curso.
**Golden Cache:** No

**Respuesta:**

No encuentro en la información disponible el procedimiento para configurar la liquidación de servicios académicos. Para orientarte con instrucciones exactas, necesito saber en qué sistema o módulo estás haciendo el trámite y qué opción o pantalla tienes abierta.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 86. Financiero — partial (0.95)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cómo consulto los descuentos asociados a un programa académico?

**HTTP/latencia:** 200 / 12588.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Descuentos por Programa.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Instructivo Módulo Atención Estudiantes (Completo).pdf; Gestión de Ingreso -  Funcionarios.pdf; Malla academica.pptx; Descuentos por Programa.pptx
**Revisión:** Da la ruta al módulo respaldada por la guía, pero afirma sin evidencia que se requieren como mínimo año y periodo para filtrar.
**Golden Cache:** No

**Respuesta:**

¡Claro! Para consultar los descuentos asociados a un programa:

1. En el menú lateral, busca y selecciona **“Descuentos por programa”**.
2. En el módulo, filtra los registros indicando como mínimo un **año** y un **periodo**. Luego podrás visualizar los registros correspondientes.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 87. Financiero — incorrect (0.99)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Cómo genero el reporte de valor de matrícula en SIAAF?

**HTTP/latencia:** 200 / 13571.7 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 7. Valor matrícula.pptx · **Incluida por API:** No
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Matricula (2).pptx; Reporte - No matriculados (1).pdf
**Revisión:** La evidencia identifica el informe «Valor Matrícula» en SIAAF WEB; la respuesta afirma que no hay procedimiento y ofrece una orientación genérica en lugar de indicar el informe.
**Golden Cache:** No

**Respuesta:**

No encuentro en la información disponible un procedimiento para que un estudiante genere en SIAAF un reporte del valor de su matrícula. El material sobre reportes trata de funciones de gestión de matrícula, no de este trámite para estudiantes, así que no quiero indicarte una ruta o botones que podrían no corresponder.

Como comprobación general, ingresa únicamente por el acceso a SIAAF que ya utilizas y revisa si allí aparece información de matrícula o pagos. Si no encuentras el valor, consulta con la dependencia universitaria que gestiona tu matrícula; no compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 88. Admisiones — incorrect (1.0)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Qué filtros pide el reporte de estudiantes nuevos de pregrado antes de generarlo?

**HTTP/latencia:** 200 / 12457.6 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 1. Estudiantes Nuevos Pregrado.pptx · **Incluida por API:** No
**Fuentes reportadas:** Manual de Usuario - Portal CovidApp.pdf; Reporte - Estudiantes autorizados en proceso de créditos_v2.pdf
**Revisión:** La evidencia especifica los filtros Año, Periodo y Fecha y el botón «Generar», pero la respuesta afirma que no dispone de esa información.
**Golden Cache:** No

**Respuesta:**

No tengo información institucional verificada sobre los filtros del reporte de estudiantes nuevos de pregrado. El contexto disponible describe filtros de reportes de CovidApp y de estudiantes autorizados en procesos de créditos, pero no ese reporte.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 89. Admisiones — incorrect (1.0)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Cómo genero el consolidado de inscripciones y matrículas de estudiantes nuevos?

**HTTP/latencia:** 200 / 11103.7 ms · **Rol inferido:** general · **Modelo/estado:** UniMon_SinDocumentacion / OFRECIENDO_RADICACION
**Fuente esperada:** 1. Estudiantes Nuevos Pregrado.pptx · **Incluida por API:** sin fuentes
**Fuentes reportadas:** sin fuentes
**Revisión:** No responde cómo generar el consolidado y deriva a soporte técnico, aunque la evidencia corresponde al instructivo del informe de estudiantes nuevos de pregrado.
**Golden Cache:** No

**Respuesta:**

Entiendo que necesitas resolver esta consulta. No encontré información institucional suficiente para indicarte un procedimiento específico con seguridad.

Si se trata de un problema técnico, cuéntame qué servicio o equipo falla y qué mensaje aparece; también puedes contactar a Soporte Técnico TI:
- **Barranquilla:** `solicitudcomputo@unisimon.edu.co` | (605) 3444333, ext. 8003/8004 | WhatsApp 3172683922
- **Cúcuta:** `helpdesk@unisimon.edu.co` | (607) 5827070, ext. 129

### 90. Admisiones — correct (0.99)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Qué informe se usa para generar el reporte de estudiantes antiguos de pregrado?

**HTTP/latencia:** 200 / 12320.1 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 2. Estudiantes Antiguos Pregrado.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** Caracterización de estudiantes.pptx; Reporte - No matriculados (1).pdf; Reporte de estudiantes graduados - Resolucion 4008.pptx; 2. Estudiantes Antiguos Pregrado.pptx; 1. Estudiantes Nuevos Pregrado.pptx
**Revisión:** Identifica correctamente el informe «Estudiantes Antiguos Pregrado» y aclara que la evidencia no detalla el módulo ni todos los pasos.
**Golden Cache:** Sí

**Respuesta:**

Buenas. Se usa el informe **«Estudiantes Antiguos Pregrado»** de SIAAF WEB. La guía disponible no especifica el módulo donde se encuentra ni los pasos completos para generarlo.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 91. Admisiones — incorrect (0.98)

**Pregunta:** Hola, soy estudiante y necesito una mano: ¿Cómo se genera el reporte de matrícula completa y media matrícula?

**HTTP/latencia:** 200 / 14266.7 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 3. Matricula Completa-Media matricula.pptx · **Incluida por API:** No
**Fuentes reportadas:** Matricula (2).pptx; Reporte - No matriculados (1).pdf
**Revisión:** La evidencia sí indica que, tras ingresar al módulo, se debe seleccionar el informe «Matrícula completa / Media matrícula»; la respuesta lo niega y no da ese paso.
**Golden Cache:** No

**Respuesta:**

Hola. En la documentación disponible no aparece el procedimiento para generar el reporte de **matrícula completa y media matrícula**; solo se describe cómo generar otros reportes de matrícula. Para no indicarte una ruta o filtros que podrían no corresponder, no puedo confirmar los pasos exactos.

Como comprobación general, revisa si en el sistema de matrícula tienes una opción **Reportes** y si allí aparece ese reporte. Si no lo encuentras o necesitas el archivo oficial, consulta con la dependencia encargada del proceso de matrícula.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 92. Admisiones — incorrect (0.97)

**Pregunta:** Buenas, soy docente y no encuentro cómo hacer esto: ¿Cuál es el instructivo de SIAAF para generar el reporte de reintegros?

**HTTP/latencia:** 200 / 13918.7 ms · **Rol inferido:** profesor · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 6. Reintegro.pptx · **Incluida por API:** No
**Fuentes reportadas:** Reporte - Horas x Docente.pptx; Distribución por procedencia educativa oficial y privada.pptx; Reporte de estudiantes graduados - Resolucion 4008.pptx; Distribución por escolaridad de los miembros de la familia.pptx; Reporte de estudiantes graduados.pptx; Reporte de Distribución de estudiantes por promedios acumulados.pptx
**Revisión:** La evidencia identifica el paso de seleccionar el informe «Reintegro» después de ingresar al módulo, pero la respuesta afirma que no hay pasos documentados.
**Golden Cache:** No

**Respuesta:**

Buenas. La información disponible confirma que los instructivos de SIAAF indican ingresar desde el sitio de la Universidad y seleccionar **«Portales»**, pero no incluye los pasos para generar el reporte de reintegros. No quiero darte una ruta que no esté verificada.

Como comprobación general, revisa si el instructivo específico está disponible entre los recursos de SIAAF a los que tienes acceso. Si no aparece, consulta al área responsable de SIAAF para obtener el procedimiento correcto.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 93. Admisiones — partial (0.96)

**Pregunta:** Hola, trabajo en el área administrativa y quisiera saber: ¿Qué documento explica el reporte de transferencias externas?

**HTTP/latencia:** 200 / 12470.5 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 4. Transferencia Externa.pptx · **Incluida por API:** Sí
**Fuentes reportadas:** 4. Transferencia Externa.pptx; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; Credenciales microsoft.pdf; Manual de Usuario - Portal CovidApp.pdf; 5. Ser Pilo Paga.pptx
**Revisión:** Identifica correctamente el documento, pero atribuye a la diapositiva 7 filtros y acciones que no están respaldados por la evidencia proporcionada.
**Golden Cache:** No

**Respuesta:**

El documento es **«4. Transferencia Externa.pptx»**. En la diapositiva 7 se explica que debes aplicar los filtros de año, periodo y fecha y luego presionar **«Generar»** para crear el reporte en PDF.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 94. Admisiones — incorrect (0.98)

**Pregunta:** Profe por acá, ¿me orientas con esto?: ¿Cómo se consulta el informe de estudiantes Ser Pilo Paga?

**HTTP/latencia:** 200 / 13281.3 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** 5. Ser Pilo Paga.pptx · **Incluida por API:** No
**Fuentes reportadas:** Autorización de Supletorios.pdf; Bloqueos, Sanciones y Excepciones.pptx; 4. Transferencia Externa.pptx; Gestión de Ayudas Educativas.pdf; Gestión de Códigos EK.pdf
**Revisión:** La evidencia confirma que existe un instructivo y que se debe seleccionar el informe «Ser Pilo Paga»; la respuesta afirma que no hay documentación verificada.
**Golden Cache:** No

**Respuesta:**

Profe, no tengo documentación institucional verificada sobre el informe de estudiantes “Ser Pilo Paga”, así que no puedo confirmar la ruta para consultarlo. Como docente, evita usar el Portal Estudiantes para este trámite. Si tienes acceso al sistema institucional correspondiente, puedes buscar el nombre del informe; no puedo confirmar en qué módulo se encuentra.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 95. Admisiones — incorrect (0.99)

**Pregunta:** Hola, estoy haciendo este trámite y me enredé un poco: ¿Qué opciones ofrece el módulo de gestión de inscripciones?

**HTTP/latencia:** 200 / 13244.7 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Gestión de inscripciones.pdf · **Incluida por API:** No
**Fuentes reportadas:** Gestión de Ingreso -  Funcionarios.pdf; Bienestar universitario manual.pptx; Instructivo Aprobación de Requisitos.pdf; Gestión Prácticas - Funcionarios.pdf; Videollamadas en  Teams.pdf
**Revisión:** Responde sobre gestión de ingresos y procesos de aspirantes, no sobre las opciones del módulo de gestión de inscripciones.
**Golden Cache:** No

**Respuesta:**

Entiendo que quieres ubicarte dentro del trámite. La documentación disponible menciona opciones de gestión de ingresos y procesos de aspirantes, pero no describe de forma completa las opciones del módulo de gestión de inscripciones.

Como referencia, en **Gestión de ingresos** se puede consultar la hoja de vida del aspirante; si tienes permiso de edición, aparecerá **Guardar** para conservar los cambios. En **Procesos estudiantes**, se puede seleccionar el proceso, periodo, nivel y programa académico para listar aspirantes, o buscar uno por número de identificación con **Documento** y **Buscar**.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 96. Atención estudiantil — incorrect (0.91)

**Pregunta:** Buenas, ¿me ayudas? No tengo claro lo siguiente: ¿Cómo se atiende una solicitud en el módulo de atención a estudiantes?

**HTTP/latencia:** 200 / 13134.8 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Instructivo Módulo Atención Estudiantes (Completo).pdf · **Incluida por API:** No
**Fuentes reportadas:** Gestión de Ayudas Educativas.pdf; P-GT-09_Procedimiento_para_el_Mantenimiento_de_Equipos_de_Computo_del_Laboratorio_de_Diagnostico_Molecular.pdf; Instructivo Reportes Consolidados.pdf; Instructivo Atencion a Estudiantes (Tutorías).pdf
**Revisión:** Da instrucciones específicas sobre remisiones y estados que no aparecen en la evidencia proporcionada para respaldarlas.
**Golden Cache:** No

**Respuesta:**

¡Claro! Si te refieres a una remisión para tutoría, puedes consultarla así:

1. Ingresa al sistema y selecciona el icono **«Atención a Estudiantes»**.
2. En el menú lateral, elige **«Atención a Estudiantes Remitidos»**.
3. Completa todos los campos del filtro de búsqueda —son obligatorios— y selecciona **«Buscar»**.
4. Una vez realizada la tutoría, la remisión cambia al estado **«Atendido»** y puedes consultar el resumen del proceso en la columna siguiente.

La guía disponible no especifica los pasos para registrar la atención durante la tutoría.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 97. Atención estudiantil — incorrect (0.98)

**Pregunta:** Soy estudiante y es la primera vez que hago esto: ¿Cómo se registra o gestiona una tutoría para un estudiante?

**HTTP/latencia:** 200 / 13410.3 ms · **Rol inferido:** estudiante · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Instructivo Atencion a Estudiantes (Tutorías).pdf · **Incluida por API:** Sí
**Fuentes reportadas:** Instructivo Credito Empresarial.pptx; Instructivo Módulo Atención Estudiantes (Completo).pdf; Instructivo Atencion a Estudiantes (Tutorías).pdf
**Revisión:** La evidencia describe cómo registrar una tutoría: digitar el código del estudiante, completar los campos obligatorios y guardar. La respuesta lo omite y ofrece pasos no respaldados sobre cambiar estados.
**Golden Cache:** No

**Respuesta:**

El instructivo disponible describe cómo gestionar una tutoría para un estudiante remitido; no explica cómo crear una remisión nueva.

1. En el listado de estudiantes remitidos, busca el registro cuyo estado sea **«No Atendido»**.
2. En ese registro, selecciona **«Cambiar Estado»** y realiza la tutoría.
3. Una vez realizada, la remisión quedará como **«Atendido»** y podrás ver un resumen del proceso. Al guardar la tutoría, el listado se actualiza.

Si lo que necesitas es registrar una remisión nueva, el procedimiento no está especificado en la información disponible.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 98. Prácticas — incorrect (0.99)

**Pregunta:** Hola, estoy apoyando este proceso y tengo una duda: ¿Qué procedimiento deben seguir los estudiantes para gestionar sus prácticas?

**HTTP/latencia:** 200 / 12772.1 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Gestión Prácticas - Estudiantes.pdf · **Incluida por API:** No
**Fuentes reportadas:** P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; GIE - ASPIRANTES NOV.2021.pptx; CP-GT-01_Gestion_de_TI.pdf
**Revisión:** La evidencia sí explica la carga de requisitos para prácticas formativas, pero la respuesta sostiene que no hay información institucional sobre el procedimiento.
**Golden Cache:** No

**Respuesta:**

No tengo información institucional verificada sobre el procedimiento para gestionar prácticas formativas. El material disponible solo indica que, para ciertos aspirantes, los requisitos de inscripción o selección pueden incluir evaluaciones como ILE, TICS, CAQ o KOLB; no describe el trámite de prácticas para estudiantes.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 99. Funcionarios — incorrect (0.98)

**Pregunta:** Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ¿Cómo se administra la autoevaluación por grupos de funcionarios?

**HTTP/latencia:** 200 / 13895.4 ms · **Rol inferido:** administrativo · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Autoevaluacion por Grupos - Funcionarios.pdf · **Incluida por API:** No
**Fuentes reportadas:** Manual de Usuario - Registro de Ingreso.pdf; P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf; P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf; P-GT-14_Procedimiento_para_la_gestion_de_actualizaciones_de_versiones_en_Kactus_y_o_Seven.pdf
**Revisión:** La evidencia indica dirigirse al Portal Profesores y Administrativos y seleccionar el módulo «Autoevaluación por Grupo»; la respuesta afirma que no identifica sistema ni pasos.
**Golden Cache:** No

**Respuesta:**

Claro. La documentación disponible no describe cómo administrar la autoevaluación por grupos de funcionarios ni identifica el sistema o los pasos para hacerlo. Para evitar indicarte una ruta incorrecta, necesito saber en qué plataforma o módulo estás trabajando; con ese dato puedo revisar qué orientación corresponde.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 100. Académico — partial (0.88)

**Pregunta:** Buenas, me quedé atascado con este trámite: ¿Qué pasos indica el documento para autorizar un examen supletorio?

**HTTP/latencia:** 200 / 12924.4 ms · **Rol inferido:** general · **Modelo/estado:** openai_gpt-6-luna / DIAGNOSTICO
**Fuente esperada:** Autorización de Supletorios.pdf · **Incluida por API:** Sí
**Fuentes reportadas:** P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf; Autorización de Supletorios.pdf; P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf; Manual de Usuario - Portal CovidApp.pdf
**Revisión:** La evidencia respalda el mensaje de confirmación y el paso posterior al pago, pero no permite verificar los filtros, la selección de estudiantes ni el botón «Aprobar» descritos.
**Golden Cache:** No

**Respuesta:**

¡Buenas! El documento indica estos pasos para autorizar un examen supletorio:

1. Ingresa al Portal y selecciona **Calificaciones**.
2. Elige los filtros de **año, periodo y programa**, y presiona **Buscar**.
3. Selecciona del listado a los estudiantes que vas a autorizar y presiona **Aprobar**.
4. Revisa el mensaje de confirmación. Luego, los estudiantes autorizados podrán descargar el volante de pago desde su portal estudiantil; una vez realizado el pago, el profesor podrá registrar la calificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

