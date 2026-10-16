# Primera tanda: documentos 1–20 (5 preguntas por documento)

- Índice: langchain; 260 documentos y 7408 chunks.
- Evaluados: 20 documentos; 100/100 respuestas recibidas; HTTP fallidos: 0.
- Juez automático preliminar: 49 correctas, 16 parciales, 32 incorrectas y 3 no verificables (49.0% clasificadas como correctas).
- Fuente objetivo recuperada: 56/100; latencia p50/p95: 132378.8/242597.2 ms.
- Golden Cache: sin escrituras. La clasificación automática es orientativa; la validación final queda pendiente de tu revisión.

## Cómo revisar

En cada pregunta compara lo que se pidió, la cita y respuesta de referencia contra la respuesta del bot. Los fallos de fuente y el veredicto del juez son señales para revisar, no una calificación humana.

## Documento 1: 1. Estudiantes Nuevos Pregrado.pptx

Juez preliminar: 1/5 correctas · fuente objetivo: 1/5 · chunks indexados: 14.

### Pregunta 1

**Pregunta:** ¿Por dónde entro para empezar a generar el informe?

**Respuesta del chatbot (HTTP 200; 9440.7 ms):**

> Para empezar a generar el **informe de costo de nómina**, entra desde tu navegador a **http://www.unisimon.edu.co/** y selecciona **«Portales»** en el menú principal. Luego, en la sección **«Profesores y Administrativos»**, accede con tu usuario y contraseña y selecciona el módulo **«Costo nómina»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Reporte - Costo Nomina.pptx, Todos_Reportes.pptx, Evaluaciones de selección ILE-TICS (FUNCIONARIOS).pptx, Planeación - Informe de Gestión.pdf, Reporte - Contabilidad - Creditos.pptx, Reportes Anexos de Facturas.pptx
**Referencia documental:** Ingresa al sitio web de la Universidad y selecciona «Portales» en el menú principal.
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Incorrecta (preliminar) · confianza 0.98 · Da la ruta correcta, pero añade instrucciones concretas sobre «Profesores y Administrativos» y el módulo «Costo nómina» sin respaldo en la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué portal tengo que abrir para acceder al sistema?

**Respuesta del chatbot (HTTP 200; 16626.6 ms):**

> Actualmente no me encuentro en la capacidad de responder a tu solicitud, ya que no dispongo de conocimiento, instructivo o procedimiento institucional documentado sobre la plataforma **Tengo**.
>
> Puedes comunicarte directamente con los canales oficiales de soporte técnico TI para verificar el acceso y estado de tu cuenta:
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | PBX: (605) 3444333 Ext. 8003 / 8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
> ¿O prefieres que radique un caso de soporte técnico por ti ahora mismo?

**Fuente esperada recuperada:** no · **Fuentes devueltas:** (ninguna reportada)
**Referencia documental:** Dirígete a «Portal Profesores y Administrativos».
**Cita y página:** «Dirigirse a la sección «Portal Profesores y Administrativos»» (p. 3)
**Juez automático:** No verificable (preliminar) · confianza 0.99 · No responde qué portal abrir y declara que no puede responder sobre «Tengo»; la evidencia sí identifica «Portal Profesores y Administrativos».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué hago para iniciar sesión?

**Respuesta del chatbot (HTTP 200; 10095.0 ms):**

> Los fragmentos describen dos sistemas distintos:
>
> - **SITE 2.0:** abre https://site.unisimon.edu.co en un navegador e ingresa tu usuario y contraseña individuales de funcionario.
> - **Portal CovidApp:** abre https://covidapp.unisimon.edu.co. Está destinado al funcionario o encargado del control de ingreso y requiere el usuario y la contraseña creados para cada sede.
>
> ¿Cuál de estos sistemas necesitas usar?
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Manual de Usuario - Registro de Ingreso.pdf, SITE 2.0.pptx
**Referencia documental:** Ingresa tu usuario y contraseña y presiona «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Parcial (preliminar) · confianza 0.96 · Mezcla sistemas distintos y no responde claramente el procedimiento solicitado; sí menciona usuario, contraseña y «Acceder» para el Portal Estudiante.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** Ya entré al sistema, ¿qué módulo y qué informe debo elegir para estudiantes nuevos de pregrado?

**Respuesta del chatbot (HTTP 200; 18070.2 ms):**

> En el módulo **«Rectoría»**, elige el informe **«Estudiantes Nuevos Pregrado»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 1. Estudiantes Nuevos Pregrado.pptx, 2. Estudiantes Antiguos Pregrado.pptx, Todos_Reportes.pptx
**Referencia documental:** Selecciona el módulo «Rectoría» y luego el informe «Estudiantes Nuevos Pregrado».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Estudiantes Nuevos Pregrado»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica el módulo «Rectoría» y el informe «Estudiantes Nuevos Pregrado».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Qué filtros uso y en qué formato se genera el reporte?

**Respuesta del chatbot (HTTP 200; 18464.9 ms):**

> Para el reporte **Mercadeo / Seguimiento**, selecciona los filtros **Año, Periodo y Programa** y presiona **«Generar»**. El reporte se crea como un documento de **Excel**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Reporte de Seguimiento.pptx, Reportes generales.pptx, Reportes de Bienestar.pptx
**Referencia documental:** Aplica los filtros Año, Periodo y Fecha; al presionar «Generar», se crea un PDF para visualizar.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Indica filtros y formato distintos: Programa y Excel, en vez de Año, Periodo y Fecha, y PDF.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 2: 2. Estudiantes Antiguos Pregrado.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 1/5 · chunks indexados: 12.

### Pregunta 1

**Pregunta:** ¿Cuál es la dirección web para comenzar y qué opción selecciono después?

**Respuesta del chatbot (HTTP 200; 20662.9 ms):**

> La guía de pagos no especifica una dirección web para comenzar. Indica dirigirse a la sección «Portal Estudiantes» y, después de iniciar sesión, en «Matrícula» seleccionar el ícono «Pagos en línea».
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Pagos en Linea.pptx, Ajustes participantes reuniones  Ms Teams.pdf
**Referencia documental:** Ingresa a http://www.unisimon.edu.co/ y selecciona «Portales» en el menú principal.
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Responde sobre pagos en línea y no da la dirección web ni la opción «Portales» solicitadas.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿A qué sección tengo que ir para entrar al sistema?

**Respuesta del chatbot (HTTP 200; 25281.5 ms):**

> Ve a la sección **“Portal Estudiantes”** y selecciona **“Barranquilla”**. Luego ingresa tu usuario y contraseña y presiona **“ACCEDER”**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Instructivo - Estudiantes.pptx, Reporte - Asignaturas por Grupos.pptx
**Referencia documental:** A «Portal Profesores y Administrativos».
**Cita y página:** «Dirigirse a la sección «Portal Profesores y Administrativos»» (p. 3)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Indica «Portal Estudiantes», pero la evidencia señala «Portal Profesores y Administrativos».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo accedo una vez que estoy en el portal?

**Respuesta del chatbot (HTTP 200; 29260.8 ms):**

> En el Portal de Estudiantes, escribe tu usuario y contraseña en los campos **Usuario** y **Contraseña** y pulsa **Acceder**. Si no recuerdas alguno, usa el enlace **Olvidé mi Usuario / Contraseña**; no compartas tu contraseña con nadie.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Movilidad Académica - Administrativo.pdf, Movilidad Académica - Estudiantes.pdf, Gestión de Ingreso -  Funcionarios.pdf, instructivo portales estudiantes.pptx, instructivo portales estudiantes.pdf
**Referencia documental:** Escribe tu usuario y contraseña y presiona el botón «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.98 · Indica escribir usuario y contraseña y pulsar «Acceder»; el dato adicional sobre recuperar credenciales no contradice la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Dónde encuentro el informe de estudiantes antiguos de pregrado?

**Respuesta del chatbot (HTTP 200; 25631.7 ms):**

> Ingresa al sistema, selecciona el módulo **«Rectoría»** y luego el informe **«Estudiantes Antiguos Pregrado»**. Para generarlo, aplica los filtros de **Año, Periodo y Fecha** y presiona **«Generar»**; se creará un PDF para visualizarlo.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 2. Estudiantes Antiguos Pregrado.pptx, 1. Estudiantes Nuevos Pregrado.pptx, Matrícula Antiguos Posgrados.pdf
**Referencia documental:** Entra al módulo «Rectoría» y selecciona «Estudiantes Antiguos Pregrado».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Estudiantes Antiguos Pregrado»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 1.0 · Ubica el informe en «Rectoría» y nombra «Estudiantes Antiguos Pregrado».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Qué tengo que completar para generar el PDF del informe?

**Respuesta del chatbot (HTTP 200; 31314.3 ms):**

> Para generar el PDF del **Informe de Gestión**, selecciona los campos **Sede**, **Año** y **Proceso**, y luego pulsa **«Generar informe»**. El informe se abrirá en una nueva ventana como archivo PDF, disponible para descargar.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Trazabilidad de transferencia externa.pptx, 3. Matricula Completa-Media matricula.pptx, Planeación - Informe de Gestión.pdf, Evaluaciones de selección ILE-TICS (FUNCIONARIOS).pdf, Evaluaciones de selección ILE-TICS (FUNCIONARIOS).pptx
**Referencia documental:** Aplica los filtros Año, Periodo y Fecha y presiona «Generar»; el reporte se crea en PDF.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Responde con campos de otro informe; los filtros correctos son Año, Periodo y Fecha, y el resultado es PDF.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 3: 3. Matricula Completa-Media matricula.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 1/5 · chunks indexados: 12.

### Pregunta 1

**Pregunta:** ¿Cómo llego al acceso de los portales desde la web de la Universidad?

**Respuesta del chatbot (HTTP 200; 30871.5 ms):**

> Desde la web de la Universidad, selecciona **Portales** en el menú principal. Desde allí verás las opciones disponibles, como **Portal Estudiantes**, **Aula Extendida** y **Portal Laboral**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Inicio.md, Web_UI_Unisimon_Portal_Estudiantes.md, Web_Unisimon_Portal_Estudiantes.md, Web_Unisimon_Portales.md, Web_Unisimon_Portal_Profesores_y_Administrativos.md, instructivo portales estudiantes.pdf
**Referencia documental:** Abre el sitio web de la Universidad y elige «Portales» en el menú principal.
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Correcta (preliminar) · confianza 0.95 · Indica elegir «Portales» en el menú principal, como pide la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué sección del portal debo buscar?

**Respuesta del chatbot (HTTP 200; 40941.0 ms):**

> Busca la sección **«Portal estudiantes»**. El instructivo indica que se accede desde el menú principal del sitio de la Universidad y luego se selecciona la sede **Barranquilla**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** instructivo portales estudiantes.pptx, instructivo portales estudiantes.pdf
**Referencia documental:** Busca «Portal Profesores y Administrativos».
**Cita y página:** «Dirigirse a la sección «Portal Profesores y Administrativos»» (p. 3)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Indica «Portal estudiantes», no «Portal Profesores y Administrativos».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** No sé cómo entrar al sistema, ¿qué datos y botón indica el instructivo?

**Respuesta del chatbot (HTTP 200; 43784.1 ms):**

> Si te refieres a la **App Unisimón**, el instructivo indica ingresar el **nombre de usuario** y la **contraseña**, y tocar **Entrar**. Para estudiantes se usan las credenciales del Portal Estudiantes; para profesores y funcionarios administrativos, las del Portal Gestión Académico-Administrativo.
>
> Si te refieres al **Portal Estudiante en la web**, la pantalla muestra los campos **Usuario** y **Contraseña**, y el botón **Acceder**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Unisimon App.pdf, Manual de Usuario - Registro de Ingreso.pdf
**Referencia documental:** Ingresa tu usuario y contraseña y luego presiona «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Parcial (preliminar) · confianza 0.95 · Da la instrucción correcta para el Portal Estudiante, pero mezcla esa respuesta con instrucciones de la app, que usa otro botón y otros datos.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué módulo y qué informe selecciono para matrícula completa o media matrícula?

**Respuesta del chatbot (HTTP 200; 40953.1 ms):**

> Selecciona el módulo **«Rectoría»** y, dentro de este, el informe **«Matrícula completa / Media matrícula»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 3. Matricula Completa-Media matricula.pptx, 7. Valor matrícula.pptx, Activación de matrículas.pdf
**Referencia documental:** Selecciona «Rectoría» y después «Matrícula completa / Media matrícula».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Matrícula completa / Media matrícula»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 1.0 · Indica «Rectoría» y el informe «Matrícula completa / Media matrícula».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cuáles son los filtros y cómo veo el reporte generado?

**Respuesta del chatbot (HTTP 200; 41703.6 ms):**

> Para el reporte **Mercadeo / Seguimiento**, selecciona los filtros **Año, Periodo y Programa** y presiona **«Generar»**. Se creará un archivo de Excel; ábrelo desde las descargas de tu navegador o en la ubicación donde este guarde los archivos descargados para ver el reporte.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Reportes generales.pptx, Reporte de Seguimiento.pptx, Instructivo Reportes Consolidados.pdf
**Referencia documental:** Completa Año, Periodo y Fecha, presiona «Generar» y visualiza el reporte en PDF.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Da filtros y formato de otro reporte: Programa y Excel, en lugar de Año, Periodo, Fecha y PDF.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 4: 4. Transferencia Externa.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 1/5 · chunks indexados: 13.

### Pregunta 1

**Pregunta:** ¿Desde qué sitio empiezo y dónde está la opción de portales?

**Respuesta del chatbot (HTTP 200; 41689.4 ms):**

> Empieza en el sitio web oficial de la Universidad: https://unisimon.edu.co/. La opción **Portales** está en el menú principal horizontal, junto a **Noticias** e **Intranet**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Inicio.md, Web_UI_Unisimon_Portal_Estudiantes.md, instructivo portales estudiantes.pdf
**Referencia documental:** Ingresa a http://www.unisimon.edu.co/ y selecciona «Portales» en el menú principal.
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Correcta (preliminar) · confianza 0.94 · Indica el sitio de la Universidad y «Portales» en el menú principal; la diferencia entre HTTP y HTTPS no cambia el destino.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Cuál es la sección que da acceso al sistema?

**Respuesta del chatbot (HTTP 200; 51245.4 ms):**

> La sección es **«Profesores y Administrativos»**. Ingresa allí con tu usuario y contraseña y presiona **«Ingresar»** para acceder al sistema.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Reportes créditos general.pptx, Inscripcion de cursos intersemestrales.pdf
**Referencia documental:** «Portal Profesores y Administrativos».
**Cita y página:** «Dirigirse a la sección «Portal Profesores y Administrativos»» (p. 3)
**Juez automático:** Parcial (preliminar) · confianza 0.96 · Identifica la sección, aunque omite «Portal» en el nombre y añade pasos de acceso no respaldados, con un botón distinto del indicado en la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo inicio sesión en el portal?

**Respuesta del chatbot (HTTP 200; 54204.4 ms):**

> 1. Entra al Portal Estudiante.
> 2. En la sección **Credenciales**, escribe tu usuario y contraseña en los campos correspondientes.
> 3. Pulsa **Acceder**. La página recomienda usar Google Chrome.
>
> Si no recuerdas tus datos, selecciona **Olvidé mi Usuario / Contraseña**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Manual de Usuario - Portal CovidApp.pdf, instructivo portales estudiantes.pdf
**Referencia documental:** Digita tu usuario y contraseña y presiona «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Parcial (preliminar) · confianza 0.94 · Incluye usuario, contraseña y «Acceder», pero cambia al Portal Estudiante y añade instrucciones no sustentadas por la evidencia citada.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿En qué parte del sistema está el informe de transferencia externa?

**Respuesta del chatbot (HTTP 200; 51726.4 ms):**

> El informe está en el módulo **Rectoría**. Una vez allí, selecciona **Transferencia Externa**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 4. Transferencia Externa.pptx, Trazabilidad de transferencia externa.pptx, Reporte - Reingresos y Transferencias Internas.pdf
**Referencia documental:** En el módulo «Rectoría», selecciona el informe «Transferencia Externa».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Transferencia Externa»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 1.0 · Indica correctamente «Rectoría» y el informe «Transferencia Externa».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Qué filtros pide el informe y qué pasa cuando aprieto «Generar»?

**Respuesta del chatbot (HTTP 200; 54206.5 ms):**

> Depende del informe. La documentación recuperada describe estas opciones:
>
> - **Inscritos:** pide obligatoriamente **Año, Periodo y Nivel de formación**. Como filtros opcionales, permite **Programa, Nivel de avance, Rango fecha de inscripción y Matriculado (Sí/No)**. Al presionar **«Generar»**, se muestra la información solicitada.
> - **Reportes generales:** indica aplicar los filtros necesarios y presionar **«Generar»**, pero no especifica cuáles son esos filtros.
> - **Caracterización de estudiantes:** pide **Año, Periodo y filtro**; después permite imprimir o generar un documento en Excel.
>
> No encontré documentación que confirme los filtros ni el resultado de **«Generar»** para el informe **«Estudiantes Nuevos Pregrado»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Caracterización de estudiantes.pptx, Reportes generales.pptx, Reporte - Inscritos.pdf
**Referencia documental:** Pide Año, Periodo y Fecha; al presionar «Generar», crea un documento PDF para visualizar.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · No responde los filtros y resultado del informe solicitado; ofrece datos de otros reportes.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 5: 5. Ser Pilo Paga.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 1/5 · chunks indexados: 15.

### Pregunta 1

**Pregunta:** ¿Cómo llego a la opción «Portales» para empezar?

**Respuesta del chatbot (HTTP 200; 62598.1 ms):**

> Desde el sitio web de la Universidad, selecciona **«Portales»** en el menú principal:
>
> 1. Abre el navegador e ingresa a **https://unisimon.edu.co/**.
> 2. En el menú principal, elige **«Portales»**.
>
> Esto te llevará a la sección de portales; la opción específica que debes elegir después depende del trámite que vayas a realizar.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Inicio.md, Web_UI_Unisimon_Portal_Estudiantes.md, instructivo portales estudiantes.pdf
**Referencia documental:** Entra al sitio web de la Universidad y selecciona «Portales» en el menú principal.
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Correcta (preliminar) · confianza 0.96 · Indica entrar al sitio de la Universidad y seleccionar «Portales» en el menú principal.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿A qué sección tengo que dirigirme para acceder?

**Respuesta del chatbot (HTTP 200; 64609.4 ms):**

> Dirígete a la sección **«Profesores y Administrativos»** dentro de **«Portales»**. Allí ingresa con tu usuario y contraseña y presiona **«Ingresar»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Reportes créditos general.pptx, Reporte - Asignaturas por Grupos.pptx, Como_acceder_MS_Teams_Estudiantes.pdf
**Referencia documental:** A «Portal Profesores y Administrativos».
**Cita y página:** «Dirigirse a la sección «Portal Profesores y Administrativos»» (p. 3)
**Juez automático:** Parcial (preliminar) · confianza 0.96 · Señala la sección correcta, aunque omite «Portal» en el nombre y añade instrucciones de inicio de sesión no respaldadas.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué hago con mis credenciales para entrar?

**Respuesta del chatbot (HTTP 200; 67676.3 ms):**

> Si son las credenciales de **Microsoft Teams**, úsalas para iniciar sesión en Teams. Según la guía, aparecen en una ventana emergente al ingresar al Portal de Gestión Académico-Administrativa: el usuario es tu número de documento y la clave es **Usb** (con U mayúscula) seguido de ese número.
>
> Si cambias la clave, debe tener entre 8 y 15 caracteres, incluir mayúsculas, minúsculas y al menos un número, y no contener datos personales.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Credenciales microsoft.pdf, Matrícula Antiguos Posgrados.pdf
**Referencia documental:** Digita tu usuario y contraseña y presiona el botón «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Responde sobre credenciales de Microsoft Teams y no indica usar usuario, contraseña y «Acceder».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Dónde selecciono el reporte de Ser Pilo Paga?

**Respuesta del chatbot (HTTP 200; 64337.6 ms):**

> Después de ingresar al sistema, selecciona el módulo **«Rectoría»** y, dentro de ese módulo, el informe **«Ser Pilo Paga»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 5. Ser Pilo Paga.pptx, Reporte - Estudiantes sin grupos escogidos.pdf, Reporte de Seguimiento.pptx, Reporte de estudiantes matriculados.pptx
**Referencia documental:** Entra al módulo «Rectoría» y selecciona el informe «Ser Pilo Paga».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Ser Pilo Paga»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 1.0 · Ubica «Ser Pilo Paga» en el módulo «Rectoría».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Qué información filtro antes de generar el reporte y cómo lo obtengo?

**Respuesta del chatbot (HTTP 200; 75713.6 ms):**

> No puedo confirmar los filtros del reporte de **preinscritos**: los instructivos disponibles no documentan ese reporte ni sus criterios.
>
> Sí aparecen estos procedimientos, por separado:
>
> - **Inscripciones reactivadas:** en el módulo «Matrícula», abre «Inscripciones reactivadas». Completa los filtros obligatorios **año y periodo**; **nivel y programa** son opcionales. Luego presiona «Buscar» para que se muestre la información.
> - **Reportes Consolidados:** desde «Portales» administrativos, ingresa al sistema y selecciona «Atención a estudiantes» > «Reportes Consolidados». Elige el reporte y usa «Exportar». Los filtros dependen del reporte; por ejemplo, los primeros cuatro usan el año y periodo activos, además de los filtros que aparezcan al seleccionarlos.
>
> Si te refieres al de preinscritos, necesitaría saber en qué sistema o módulo lo estás generando para orientarte sin mezclarlo con otro reporte.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Instructivo Reportes Consolidados.pdf, Reporte - Inscripción Reactivada.pptx, Reporte - Inscripción Reactivada.pdf
**Referencia documental:** Aplica Año, Periodo y Fecha, y presiona «Generar» para crear el reporte en PDF.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · No responde los filtros ni la generación del informe «Ser Pilo Paga»; desvía la respuesta a otros procedimientos.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 6: 6. Reintegro.pptx

Juez preliminar: 1/5 correctas · fuente objetivo: 2/5 · chunks indexados: 14.

### Pregunta 1

**Pregunta:** ¿Por dónde entro al sistema para sacar el informe de reintegro?

**Respuesta del chatbot (HTTP 200; 64950.0 ms):**

> Desde [www.unisimon.edu.co](http://www.unisimon.edu.co/), selecciona **Portales** y luego **Portal Profesores y Administrativos**. Ingresa con tu usuario y contraseña y pulsa **Acceder**; dentro del sistema, selecciona el módulo **Rectoría** y el informe **Reintegro**.
>
> Para generarlo, completa los filtros de **Año**, **Periodo** y **Fecha**, y pulsa **Generar**. Se creará un reporte en PDF para visualizarlo.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 6. Reintegro.pptx, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, SITE 2.0.pptx
**Referencia documental:** Desde el sitio web de la Universidad, selecciona «Portales» y luego «Portal Profesores y Administrativos».
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La ruta hasta Portales está respaldada, pero agrega módulos, filtros y generación de PDF sin respaldo en la cita verificada para esta pregunta.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué tengo que hacer para iniciar sesión en el portal?

**Respuesta del chatbot (HTTP 200; 77857.4 ms):**

> Para iniciar sesión en el **Portal CovidApp**, ve a https://covidapp.unisimon.edu.co. Si eres estudiante, usa tus credenciales del **Portal Estudiantes**; si eres docente o funcionario administrativo, usa las del **Portal Gestión Académico - Administrativo**. No compartas tu contraseña con nadie.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Manual de Usuario - Portal CovidApp.pdf, instructivo portales estudiantes.pdf
**Referencia documental:** Ingresa tu usuario y contraseña y presiona «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Responde sobre Portal CovidApp, no sobre el portal del procedimiento; omite la instrucción aplicable de usuario, contraseña y «Acceder».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** Ya entré al sistema, ¿qué módulo debo abrir primero?

**Respuesta del chatbot (HTTP 200; 85440.8 ms):**

> Depende de lo que quieras hacer. Si buscas listar estudiantes atendidos voluntariamente o registrar una tutoría voluntaria, abre **«Atención a Estudiantes Voluntaria»** en el menú lateral. No puedo confirmar con la información disponible qué módulo corresponde a gestionar la matrícula; ¿te refieres a matrícula o a una atención/tutoría estudiantil?
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Instructivo Módulo Atención Estudiantes (Completo).pdf, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf
**Referencia documental:** Selecciona el módulo «Rectoría».
**Cita y página:** «Luego de ingresar al sistema deberá seleccionar el módulo «Rectoría»» (p. 5)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Indica módulos de atención estudiantil, no el módulo «Rectoría» requerido.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Dónde encuentro el informe de reintegro?

**Respuesta del chatbot (HTTP 200; 77584.1 ms):**

> En SIAAF Web, selecciona el módulo **«Rectoría»** y luego el informe **«Reintegro»**. Si necesitas generar el reporte, indica los filtros de **Año, Periodo y Fecha** y presiona **«Generar»** para visualizarlo en PDF.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 6. Reintegro.pptx
**Referencia documental:** Dentro del módulo, selecciona el informe «Reintegro».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Reintegro»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 0.97 · Indica que se accede a «Rectoría» y luego se elige «Reintegro», conforme a la evidencia; el detalle adicional no contradice la cita.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Qué filtros tengo que poner y cómo genero el reporte?

**Respuesta del chatbot (HTTP 200; 77856.0 ms):**

> Para generar el **reporte de seguimiento de Mercadeo**:
>
> 1. Entra al módulo **Mercadeo** y luego abre **Reportes**.
> 2. Selecciona el reporte **Mercadeo / Seguimiento**.
> 3. Elige los filtros **Año, Periodo y Programa**.
> 4. Presiona **«Generar»**. El sistema creará un documento de Excel.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Reporte de Seguimiento.pptx, Reportes créditos general.pptx, Reportes de Bienestar.pptx
**Referencia documental:** Aplica los filtros de Año, Periodo y Fecha, y presiona «Generar» para crear el reporte en PDF.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Describe otro reporte y filtros distintos; la evidencia pide Año, Periodo y Fecha y generar un PDF.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 7: 7. Valor matrícula.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 2/5 · chunks indexados: 12.

### Pregunta 1

**Pregunta:** ¿Desde qué sitio puedo entrar al portal para generar el informe del valor de matrícula?

**Respuesta del chatbot (HTTP 200; 87403.6 ms):**

> Puedes iniciar desde el sitio web de la Universidad: http://www.unisimon.edu.co/. En el menú principal, selecciona **«Portales»** para acceder al portal desde el que se genera el informe de valor de matrícula.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 7. Valor matrícula.pptx, Matricula.pptx
**Referencia documental:** Entra en un navegador a http://www.unisimon.edu.co/ y selecciona «Portales».
**Cita y página:** «Ingrese desde su navegador al sitio web de la Universidad: http://www.unisimon.edu.co/ y seleccionar en menú principal la opción «Portales»» (p. 2)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica el sitio de la Universidad y la opción «Portales», como establece la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué datos uso para iniciar sesión en el portal?

**Respuesta del chatbot (HTTP 200; 87694.7 ms):**

> Para ingresar al Portal Movilidad Académica, usa tu usuario y contraseña institucionales. Desde la página de la Universidad, entra a **Portales > Administrativos**, ingresa esos datos y pulsa **Acceder**; luego selecciona **DICO > Portal Movilidad Académica**, vuelve a ingresar tu usuario y contraseña y pulsa **ENTRAR**. No compartas tu contraseña ni códigos de verificación.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Movilidad Académica - Administrativo.pdf, Demo tipos de admisión.pptx
**Referencia documental:** Ingresa tu usuario y contraseña, y luego presiona «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Parcial (preliminar) · confianza 0.96 · Incluye usuario, contraseña y «Acceder», pero responde con un procedimiento específico de Movilidad Académica no sustentado por la cita para este trámite.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué módulo tengo que seleccionar después de ingresar?

**Respuesta del chatbot (HTTP 200; 88259.5 ms):**

> Depende del trámite: si eres docente y vas a hacer una remisión desde Calificaciones, selecciona **«Calificaciones»**. Si gestionas remisiones como coordinador(a) PIEA, selecciona **«Atención a estudiantes»**. ¿Cuál de esos procesos necesitas realizar?
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Instructivo Módulo Atención Estudiantes (Completo).pdf, Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf
**Referencia documental:** Selecciona el módulo «Rectoría».
**Cita y página:** «Luego de ingresar al sistema deberá seleccionar el módulo «Rectoría»» (p. 5)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Ofrece opciones de otros procesos; la respuesta requerida es seleccionar «Rectoría».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Cómo se llama el informe que debo elegir para consultar el valor de matrícula?

**Respuesta del chatbot (HTTP 200; 87121.2 ms):**

> El informe se llama **«Valor Matrícula»**. En el sistema, lo encontrarás dentro del módulo **«Rectoría»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** 7. Valor matrícula.pptx, Consulta de Hoja de Vida - Matrículas.pdf, Matricula (2).pptx
**Referencia documental:** El informe se llama «Valor Matrícula».
**Cita y página:** «Luego de ingresar al módulo deberá seleccionar el informe «Valor Matrícula»» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Identifica correctamente el informe «Valor Matrícula».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo genero el reporte y en qué formato queda?

**Respuesta del chatbot (HTTP 200; 97706.2 ms):**

> Para generar el reporte de **Estudiantes Remitidos**:
>
> 1. Selecciona el icono **Atención a Estudiantes**.
> 2. En el menú lateral, entra en **Reportes** y luego en **Remisión y Atención**.
> 3. En el campo **Reporte**, selecciona **Estudiantes Remitidos** y completa **Programa**, **Estrategia**, **Fecha Inicio** y **Fecha Fin**. Revisa especialmente **Fecha Inicio**, porque por defecto aparece la fecha actual.
> 4. Selecciona **Buscar**. Cuando aparezca el listado de resultados, podrás descargarlo en formato **PDF o Excel**.
>
> La referencia disponible no confirma el procedimiento para **Grupos sin Estudiantes**; los pasos anteriores corresponden al reporte de Estudiantes Remitidos.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Instructivo Reportes Estrategias.pdf, Instructivo Planeación Actualizado.pdf
**Referencia documental:** Aplica los filtros de Año, Periodo y Fecha y presiona «Generar»; el reporte se crea en PDF.
**Cita y página:** «Para crear el reporte deberá aplicar los filtros solicitados de: Año, Periodo y Fecha. Posteriormente presionar el botón «Generar», este creará el reporte en un documento PDF para su visualización.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Describe otro reporte, con filtros diferentes y formatos PDF o Excel; la evidencia especifica Año, Periodo, Fecha y PDF.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 8: Activación de matrículas.pdf

Juez preliminar: 4/5 correctas · fuente objetivo: 4/5 · chunks indexados: 42.

### Pregunta 1

**Pregunta:** ¿Dónde inicio sesión para hacer la activación de matrículas?

**Respuesta del chatbot (HTTP 200; 97704.7 ms):**

> Inicia sesión desde la sección **Portales** del sitio web de la Universidad, en http://www.unisimon.edu.co/portales/administrativos. Ingresa tu usuario y contraseña y selecciona **Acceder**; después, abre el módulo **Matrícula** y selecciona **Activación de matrículas**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Activación de matrículas.pdf
**Referencia documental:** Desde la sección «Portales» de la página de la Universidad, ingresa tu usuario y contraseña y presiona «Acceder».
**Cita y página:** «Desde la página web de la universidad, en la sección de «Portales» (http://www.unisimon.edu.co/portales/administrativos), ingrese su usuario y contraseña, y presione el botón «Acceder»» (p. 2)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica la sección Portales, la dirección administrativa, las credenciales y «Acceder», conforme a la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué módulos tengo que abrir para llegar a Activación de matrículas?

**Respuesta del chatbot (HTTP 200; 99891.8 ms):**

> Desde el portal administrativo, abre el módulo **Matrícula** y luego selecciona **Activación de matrículas**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Activación de matrículas.pdf
**Referencia documental:** Primero selecciona «Matrícula» y luego «Activación de matrículas».
**Cita y página:** «Luego, seleccione el módulo “Activación de matrículas”.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Da los dos módulos en el orden requerido: «Matrícula» y «Activación de matrículas».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** Después de llenar los campos de búsqueda, ¿cómo veo los resultados?

**Respuesta del chatbot (HTTP 200; 97705.1 ms):**

> Después de completar los campos de búsqueda, selecciona **“Buscar”**. El sistema generará el listado de resultados; luego puedes usar la flecha en el encabezado de cada columna para filtrar u ordenar la lista.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Resultados de aprendizaje.pptx, Activación de matrículas.pdf
**Referencia documental:** Presiona «Buscar»; también puedes filtrar u ordenar usando la flecha en la cabecera de cada columna.
**Cita y página:** «Luego de diligenciar los campos según la búsqueda a realizar, seleccione el botón “Buscar”. Adicionalmente haciendo clic en la flecha que aparece en la cabecera de cada columna, podrá realizar un filtro u ordenamiento de los resultados obtenidos.» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica presionar «Buscar» y usar las flechas de columnas para filtrar u ordenar resultados.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Cómo activo una o varias matrículas y les asigno una fecha?

**Respuesta del chatbot (HTTP 200; 100695.7 ms):**

> 1. Desde la página web de la Universidad, entra en **Portales** y accede con tu usuario y contraseña. Selecciona el módulo **Matrícula** y luego **Activación de matrículas**.
> 2. En la búsqueda, elige el tipo (**Rango de fecha** o **Periodo**) y completa los campos obligatorios correspondientes. Puedes añadir filtros como nivel académico, programa, nivel de avance, estado de matrícula o fecha de activación; luego selecciona **Buscar**.
> 3. En los resultados, selecciona una o varias matrículas y pulsa **Activar**.
> 4. En la ventana que aparece, elige si asignarás la misma fecha a las matrículas seleccionadas o una fecha específica, indica la fecha y pulsa **Guardar**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Activación de matrículas.pdf
**Referencia documental:** Selecciona uno o más registros, presiona «Activar», elige la fecha —igual para todas o específica— y luego presiona «Guardar».
**Cita y página:** «Seleccione uno o más registros, luego seleccione el botón “Activar”. Automáticamente aparecerá una nueva ventana dónde deberá seleccionar la fecha que se asignará a la(s) matrícula(s) seleccionada(s).» (p. 7)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Incluye seleccionar registros, «Activar», asignar fecha y «Guardar», en concordancia con la referencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Se puede exportar a Excel lo que salió en la búsqueda?

**Respuesta del chatbot (HTTP 200; 111445.9 ms):**

> Sí. Depende del módulo:
>
> - **Remisiones en Atención a estudiantes:** el listado resultante de la búsqueda se puede exportar a Excel. La búsqueda puede hacerse por programa académico o por código del estudiante.
> - **Reporte de asistencias QR:** completa los filtros y selecciona la lupa; los resultados aparecen en un listado con opción de exportar a Excel.
>
> ¿En cuál de estos módulos estás trabajando?
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Instructivo Módulo Atención Estudiantes (Completo).pdf, Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf, Instructivo - Reporte de asistencias QR.pdf
**Referencia documental:** Sí. Selecciona el botón «Excel» para generar un archivo Excel con la información de la búsqueda.
**Cita y página:** «Para generar un archivo Excel con la información obtenida a través de una búsqueda, seleccione el botón “Excel”.» (p. 9)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Habla de exportación en otros módulos y no responde que en este procedimiento se usa el botón «Excel».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 9: Activar Usuario y Correo institucional.pdf

Juez preliminar: 0/5 correctas · fuente objetivo: 2/5 · chunks indexados: 9.

### Pregunta 1

**Pregunta:** ¿A qué portal entro para activar mi usuario y correo institucional?

**Respuesta del chatbot (HTTP 200; 110020.4 ms):**

> Entra a **https://www.unisimon.edu.co/portales**, selecciona **“Portal Estudiantes”** y luego **Barranquilla**. Desde allí puedes iniciar la activación de tu usuario; el correo institucional se habilita con la misma contraseña que establezcas para el Portal de Estudiantes.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Activar Usuario y Correo institucional.pdf
**Referencia documental:** Entra a https://www.unisimon.edu.co/portales y selecciona «Portal Estudiantes».
**Cita y página:** «Ingrese a https://www.unisimon.edu.co/portales seleccione “Portal Estudiantes”.» (p. 3)
**Juez automático:** Parcial (preliminar) · confianza 0.92 · Indica correctamente el portal y «Portal Estudiantes», pero agrega pasos y afirmaciones sobre activación y correo que no constan en la cita.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** No encuentro mi usuario y contraseña, ¿dónde aparecen?

**Respuesta del chatbot (HTTP 200; 110462.7 ms):**

> En el **Portal Estudiante**, los campos **Usuario** y **Contraseña** aparecen en la sección **Credenciales**. Si no recuerdas alguno, selecciona **«Olvidé mi Usuario / Contraseña»**; para restablecer la contraseña, ingresa tu código o número de identificación y presiona **«Enviar»**. La contraseña se enviará a tu correo personal y podrás cambiarla desde el enlace recibido.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Restablecimiento de contraseña.pptx, Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf
**Referencia documental:** El usuario y la contraseña están al final del recibo de matrícula.
**Cita y página:** «El usuario y contraseña, se encuentran al final del recibo de matrícula.» (p. 5)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Ubica las credenciales en una sección del portal y propone recuperación, en vez de indicar que están al final del recibo de matrícula.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué hago si tengo problemas con la contraseña?

**Respuesta del chatbot (HTTP 200; 118089.7 ms):**

> Para restablecerla, ingresa tu **código de estudiante o número de identificación** y pulsa **«Enviar»**. La contraseña se enviará a tu correo personal; abre el mensaje y selecciona **«Restablecer contraseña»** para continuar.
>
> Si no encuentras el correo, revisa también la carpeta de correo no deseado. Si no llega o ya no tienes acceso a ese correo, contacta a través de un canal oficial de soporte de la Universidad.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Restablecimiento de contraseña.pptx, Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf
**Referencia documental:** Escribe a trabajodesdecasa@unisim onbolivar.edu.co con tus datos personales.
**Cita y página:** «En caso de presentar inconvenientes con la contraseña, escríbanos a trabajodesdecasa@unisim onbolivar.edu.co con sus datos personales.» (p. 5)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Da pasos de restablecimiento que no responden a la instrucción documentada de escribir al correo indicado con los datos personales.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué requisitos tiene que cumplir la nueva contraseña?

**Respuesta del chatbot (HTTP 200; 120163.0 ms):**

> La nueva contraseña debe tener **al menos 8 caracteres** e incluir **una letra mayúscula, una minúscula, un número y un símbolo especial**. Luego debes ingresarla nuevamente en el campo de confirmación y presionar **«Enviar»**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Restablecimiento de contraseña.pptx, Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf
**Referencia documental:** Debe tener entre 8 y 15 caracteres, mayúsculas, minúsculas y al menos un número; no puede incluir datos personales.
**Cita y página:** «Mínimo 8 caracteres, máximo 15. Mayúsculas, minúsculas y al menos 1 número. No podrá contener ningún dato personal» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 1.0 · Omite el máximo de 15 caracteres y la prohibición de datos personales, y agrega el requisito de símbolo especial sin respaldo.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿La misma contraseña sirve para el Aula Extendida y el correo? ¿Cómo entro al correo institucional?

**Respuesta del chatbot (HTTP 200; 111735.0 ms):**

> Sí. La guía indica que la contraseña es unificada para el Portal de Estudiantes, el Aula Extendida y el correo institucional.
>
> Los fragmentos disponibles no especifican la dirección ni los pasos para abrir el correo. Para evitar enviarte a un enlace incorrecto, accede desde un enlace de correo institucional publicado por la Universidad; no puedo confirmar cuál es la ruta exacta con esta información.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf, Activar Usuario y Correo institucional.pdf
**Referencia documental:** Sí, la contraseña restablecida sirve para ambos. Para acceder al correo, entra por la web de la Universidad, en «Servicios» y luego «Correo Estudiantes».
**Cita y página:** «esa misma contraseña le servirá para su Aula Extendida y Correo Estudiantil. Recuerde que para acceder a su correo institucional, siempre debe hacerlo a través de la página web de la Universidad, en la sección Servicios y luego Correo Estudiantes» (p. 8)
**Juez automático:** Parcial (preliminar) · confianza 0.99 · Confirma que la contraseña sirve para ambos servicios, pero no da la ruta documentada para entrar al correo: «Servicios» y «Correo Estudiantes».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 10: Administración de Autoevaluación.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 3/5 · chunks indexados: 41.

### Pregunta 1

**Pregunta:** ¿Cómo entro al sistema de autoevaluación desde el portal?

**Respuesta del chatbot (HTTP 200; 123929.5 ms):**

> Hay dos rutas documentadas para procesos de autoevaluación; depende de cuál necesites:
>
> - **Autoevaluación por Grupo (profesores):** desde el sitio de la Universidad, entra en **Portales** y dirígete a **Portal Profesores y Administrativos**. Inicia sesión con tu usuario y contraseña; luego selecciona el módulo **Autoevaluación por Grupo**.
> - **SIAAF Web:** desde el sitio de la Universidad, entra en **Servicios**, luego en **Autoevaluación** y selecciona **Procesos en curso**. Allí eliges el tipo de usuario (Profesor, Estudiante o Invitado), ingresas la información solicitada y presionas **Ingresar**.
>
> ¿Cuál de estos dos procesos estás intentando abrir?
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Inicio.md, Web_UI_Unisimon_Portal_Estudiantes.md, Autoevaluacion por Grupos - Funcionarios.pdf, Proceso de Autoevaluación.pptx
**Referencia documental:** Dirígete a «Portal Profesores y Administrativos», ingresa tu usuario y contraseña y presiona «Acceder».
**Cita y página:** «Digite su usuario y contraseña para acceder al sistema y luego presione sobre el botón «Acceder»» (p. 4)
**Juez automático:** Parcial (preliminar) · confianza 0.91 · Incluye la ruta y el inicio de sesión pertinentes, pero mezcla procedimientos distintos y agrega una alternativa de SIAAF no necesaria para responder.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué módulo tengo que seleccionar para administrar la autoevaluación?

**Respuesta del chatbot (HTTP 200; 125756.5 ms):**

> Después de ingresar al sistema, selecciona el módulo **«Autoevaluación»**. Para acceder, la guía indica entrar al sitio de la Universidad, ir a **«Portales»**, elegir **«Portal Profesores y Administrativos»** e iniciar sesión.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Administración de Autoevaluación.pptx
**Referencia documental:** Selecciona el módulo «Autoevaluación».
**Cita y página:** «Módulo Luego de ingresar deberá seleccionar el módulo “Autoevaluación”» (p. 5)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica seleccionar el módulo «Autoevaluación», que es lo solicitado y está respaldado.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo creo un evento en el módulo?

**Respuesta del chatbot (HTTP 200; 120161.7 ms):**

> Para crear un evento en el módulo de **Autoevaluación**:
>
> 1. Ingresa al módulo **Autoevaluación**.
> 2. En la sección **Eventos**, presiona **Nuevo**.
> 3. Completa el formulario solicitado y presiona **Guardar**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Administración de Autoevaluación.pptx, SITE 2.0.pptx, Módulo de instrumentos de autoevaluación.pptx
**Referencia documental:** Presiona «Nuevo», completa el formulario y selecciona «Guardar».
**Cita y página:** «Para realizar la creación de un evento, presionar el botón «Nuevo», completar el formulario solicitado y presionar el botón «Guardar»» (p. 7)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica presionar «Nuevo», completar el formulario y «Guardar», conforme al procedimiento.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué regla hay que seguir al ponderar los factores?

**Respuesta del chatbot (HTTP 200; 126268.7 ms):**

> Los fragmentos disponibles indican cómo iniciar la ponderación: en «Evaluaciones disponibles», presiona el ícono correspondiente a la evaluación que deseas realizar. No especifican una regla para los valores —por ejemplo, si deben sumar 100 o ser distintos de cero— ni documentan un botón para guardar, así que no puedo confirmar esos detalles.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Proceso de Autoevaluación.pptx
**Referencia documental:** No ingreses valores en cero y asegúrate de que la suma de las ponderaciones sea 100.
**Cita y página:** «No se pueden ingresar valores en cero (0) y la suma de todas las ponderaciones debe ser igual a 100.» (p. 10)
**Juez automático:** No verificable (preliminar) · confianza 0.99 · Reconoce que los fragmentos disponibles no permiten confirmar la regla; no inventa pasos ni cifras.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo agrego permisos a alguien para un evento?

**Respuesta del chatbot (HTTP 200; 138025.1 ms):**

> Para agregar permisos a una persona, busca primero el evento. Esta acción adicional está disponible cuando el evento está en estado **«Ponderando»**.
>
> 1. En la sección de eventos, busca el evento usando los filtros y selecciona la acción para agregar permisos.
> 2. En el módulo **«Agregar permisos»**, escribe la identificación o los nombres y apellidos de la persona.
> 3. Selecciona la opción correspondiente en la lista de resultados. Este módulo permite asignar permisos a profesores, estudiantes e invitados.
>
> La guía no especifica qué opción de permiso elegir ni el botón final para confirmar la asignación.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Habilitar permisos PAC (Director de programa).pdf, Administración de Autoevaluación.pptx
**Referencia documental:** Busca a la persona por identificación o por nombres y apellido, y selecciona la opción deseada del listado.
**Cita y página:** «Para realizar la búsqueda digite la identificación o los nombres y apellido del usuario, y presione la opción deseada del listado.» (p. 12)
**Juez automático:** Parcial (preliminar) · confianza 0.96 · Incluye buscar por identificación o nombres y seleccionar una opción del listado, pero añade condiciones y pasos adicionales no sustentados por la cita.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 11: Agregar_miembros_Grupos_MS_Teams.pdf

Juez preliminar: 3/5 correctas · fuente objetivo: 4/5 · chunks indexados: 14.

### Pregunta 1

**Pregunta:** ¿Cómo elijo el equipo al que quiero agregar a alguien?

**Respuesta del chatbot (HTTP 200; 132095.2 ms):**

> En Teams, ve a la sección **«Equipos»** y selecciona el equipo al que quieres agregar a la persona. Después, abre **«Más opciones»** junto al equipo y elige **«Agregar miembro»** para iniciar el proceso.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Agregar_miembros_Grupos_MS_Teams.pdf, Proyección (agregar, eliminar, habilitar).pptx, Proyección (agregar, eliminar, habilitar).pdf
**Referencia documental:** En «Equipos», selecciona el equipo al que quieres agregar miembros.
**Cita y página:** «En la sección «Equipos», seleccione el equipo al que agregar miembro(s).» (p. 2)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica seleccionar el equipo desde «Equipos», como señala la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Dónde encuentro la opción para agregar un miembro al equipo?

**Respuesta del chatbot (HTTP 200; 132378.8 ms):**

> En Microsoft Teams, ve a **Equipos** y selecciona el equipo al que quieres agregar el miembro. Junto al nombre del equipo, abre **Más opciones** y elige **Agregar miembro**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Agregar_miembros_Grupos_MS_Teams.pdf, Grupos_en_Teams.pdf
**Referencia documental:** Abre «Más opciones» y selecciona «Agregar miembro».
**Cita y página:** «Haga clic sobre sobre la opción “Más opciones” y luego seleccione “Agregar miembro”.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Identifica correctamente «Más opciones» y «Agregar miembro».
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué información puedo escribir para buscar a la persona que voy a agregar?

**Respuesta del chatbot (HTTP 200; 143194.5 ms):**

> El procedimiento disponible no especifica qué datos escribir para buscar a una persona en una pantalla de búsqueda. Indica que, para solicitudes de creación o modificación de accesos, se deben informar datos claros y completos del usuario; menciona el nombre completo y el número de identificación, pero no confirma que esos datos sean campos de búsqueda.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf
**Referencia documental:** Puedes buscarla por correo electrónico o nombre de usuario.
**Cita y página:** «Escriba el correo electrónico o nombre de usuario para iniciar la búsqueda.» (p. 4)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La información sí está documentada: se busca por correo electrónico o nombre de usuario. La respuesta no la proporciona.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** Ya seleccioné a la persona; ¿qué botón tengo que presionar para enviar la solicitud?

**Respuesta del chatbot (HTTP 200; 143195.1 ms):**

> La guía indica cómo buscar y seleccionar a la persona, pero no documenta qué botón presionar después para enviar la solicitud. No quiero indicarte uno por suposición; revisa las opciones que aparecen en esa pantalla y, si no está claro cuál confirma la acción, detente antes de enviarla y consulta el canal oficial correspondiente.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Web_UI_Unisimon_Inicio.md, Pagos en Linea_vPaymentz.pptx, Agregar_miembros_Grupos_MS_Teams.pdf
**Referencia documental:** Selecciona el botón «Enviar solicitud».
**Cita y página:** «Luego de seleccionar el usuario, seleccione el botón “Enviar solicitud”.» (p. 5)
**Juez automático:** No verificable (preliminar) · confianza 0.97 · Reconoce que la guía no documenta el botón, aunque la evidencia indexada sí indica «Enviar solicitud»; la cita está verificada y HTTP fue exitoso, por lo que la omisión de la respuesta esperada es incorrecta.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo sé si se envió la solicitud para que la persona se una al grupo?

**Respuesta del chatbot (HTTP 200; 140006.9 ms):**

> Después de seleccionar a la persona y enviar la solicitud, se te notificará que fue enviada para que pueda unirse al grupo. Ese aviso confirma el envío de la solicitud; no significa que la persona ya se haya unido.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Agregar_miembros_Grupos_MS_Teams.pdf, Movilidad Académica - Estudiantes.pdf, Crear reuniones No asociadas a grupos.pdf
**Referencia documental:** Se te notificará que la solicitud fue enviada al usuario para que se una al grupo.
**Cita y página:** «Se le notificará que ha sido enviada la solicitud al usuario, para que éste se una al grupo.» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Explica que se notifica el envío de la solicitud y distingue correctamente ese aviso de la incorporación al grupo.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 12: Ajustes participantes reuniones  Ms Teams.pdf

Juez preliminar: 3/5 correctas · fuente objetivo: 4/5 · chunks indexados: 38.

### Pregunta 1

**Pregunta:** ¿Cuándo tengo que ajustar los roles de una reunión agendada?

**Respuesta del chatbot (HTTP 200; 145574.3 ms):**

> Los roles de una reunión agendada se ajustan **después de crearla**. Vuelve a abrir la reunión, selecciona **«Opciones de reunión»** y configura los roles que necesites.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Ajustes participantes reuniones  Ms Teams.pdf, Crear reuniones No asociadas a grupos.pdf
**Referencia documental:** Después de crear la reunión, vuelve a entrar en ella y selecciona «Opciones de reunión».
**Cita y página:** «Luego de haber creado la reunión, ingrese nuevamente a ella. 2. Seleccione “Opciones de reunión”» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica que se ajustan después de crear la reunión y volver a entrar en ella.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué opción debo seleccionar en las dos listas para que los demás entren como asistentes?

**Respuesta del chatbot (HTTP 200; 145575.7 ms):**

> Selecciona **“Solo yo”** en las dos listas desplegables y luego pulsa **“Guardar”**. Así, los demás participantes ingresarán con el rol de **Asistente**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Ajustes participantes reuniones  Ms Teams.pdf, Reporte - Estudiantes sin grupos escogidos.pdf
**Referencia documental:** Selecciona «Solo yo» en las dos listas desplegables y luego guarda los cambios.
**Cita y página:** «deberá seleccionar “Solo yo” en las dos listas desplegables, tal y como se muestra en la siguiente imagen, al finalizar, seleccione “Guardar”.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Da las dos selecciones «Solo yo» y el paso de guardar, conforme a la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué pueden hacer los participantes si tienen el rol de asistente?

**Respuesta del chatbot (HTTP 200; 152386.8 ms):**

> Con el rol **Asistente**, pueden hablar, compartir video, participar en el chat y ver los archivos que comparta otra persona durante la reunión. No pueden compartir su pantalla ni silenciar o quitar a otros participantes de la reunión.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Ajustes participantes reuniones  Ms Teams.pdf
**Referencia documental:** Pueden hablar, compartir video, participar en el chat y ver los archivos compartidos por otra persona.
**Cita y página:** «sólo podrán, hablar y compartir video, participar en el chat y ver los archivos compartidos por otra persona.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.97 · Enumera las acciones permitidas respaldadas por la evidencia; las restricciones adicionales no contradicen lo citado.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Por qué no me aparece la opción para compartir pantalla como asistente?

**Respuesta del chatbot (HTTP 200; 152691.0 ms):**

> Los fragmentos disponibles no documentan los permisos para compartir pantalla según el rol en Teams, así que no puedo confirmar si el rol de asistente es la causa ni recomendar un cambio de rol.
>
> Como comprobación general, verifica que estés dentro de la reunión y prueba salir y volver a entrar. Si la opción sigue sin aparecer, consulta al organizador para confirmar qué permisos de presentación tiene configurados.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Grabar un clase en Teams y compartir en Stream.pdf
**Referencia documental:** Los asistentes no tienen habilitada la opción de compartir pantalla; esa opción queda disponible al convertirlos en moderadores.
**Cita y página:** «Con el rol “Asistentes”, los participantes no tendrán habilitadas las opciones adicionales de compartir pantalla» (p. 5)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La evidencia sí explica que el rol de asistente no tiene habilitado compartir pantalla; la respuesta lo niega como información disponible.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo cambio los permisos en una reunión no agendada?

**Respuesta del chatbot (HTTP 200; 152954.1 ms):**

> 1. Crea una reunión no agendada en Microsoft Teams y únete a ella.
> 2. Una vez dentro, cambia el participante de **“Asistente”** a **“Moderador”** para que pueda compartir pantalla, silenciar o quitar a otros asistentes.
> 3. Después de su intervención, puedes devolverlo a **“Asistente”**.
>
> La guía confirma que debes unirte primero para cambiar los permisos, pero no especifica la ruta o los controles exactos para hacerlo.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Ajustes participantes reuniones  Ms Teams.pdf
**Referencia documental:** Después de crearla, únete a la reunión para cambiar los permisos de acciones.
**Cita y página:** «Luego de crear una reunión no agendada, deberá unirse a esta para cambiar los permisos de acciones.» (p. 7)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La evidencia solo indica unirse a la reunión para cambiar permisos; la respuesta añade instrucciones concretas de cambiar roles y revertirlos sin respaldo en la cita.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 13: Anexo_1_CP-GT-01_Descripcion_de_Indicadores_del_proceso__Gestion_de_TI.pdf

Juez preliminar: 2/5 correctas · fuente objetivo: 2/5 · chunks indexados: 9.

### Pregunta 1

**Pregunta:** ¿Cuál es la meta para el tiempo promedio de respuesta al usuario?

**Respuesta del chatbot (HTTP 200; 158116.7 ms):**

> La meta para el **tiempo promedio de respuesta al usuario** es de **8 horas laborales o menos**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, Anexo_1_CP-GT-01_Descripcion_de_Indicadores_del_proceso__Gestion_de_TI.pdf
**Referencia documental:** La meta es de hasta 8 horas laborales.
**Cita y página:** «Tiempo promedio de respuesta al usuario Atención oportuna de solicitudes Mensual <= 8 horas laborales 24 horas calendario» (p. 1)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Expresa correctamente la meta de hasta 8 horas laborales.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Cada cuánto se mide el tiempo promedio de respuesta al usuario?

**Respuesta del chatbot (HTTP 200; 162480.5 ms):**

> El tiempo promedio de respuesta al usuario se mide **mensualmente**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Anexo_1_CP-GT-01_Descripcion_de_Indicadores_del_proceso__Gestion_de_TI.pdf, Instructivo Bloqueos.pdf
**Referencia documental:** Se mide mensualmente.
**Cita y página:** «Tiempo promedio de respuesta al usuario Atención oportuna de solicitudes Mensual <= 8 horas laborales» (p. 1)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica correctamente que la medición es mensual.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué porcentaje mínimo se establece para la ejecución del mantenimiento preventivo de Cómputo?

**Respuesta del chatbot (HTTP 200; 164823.3 ms):**

> En los fragmentos disponibles no aparece un porcentaje mínimo para ejecutar el mantenimiento preventivo de equipos de cómputo. Solo se indica que los equipos con más de seis meses de uso entran al programa y se describen frecuencias de mantenimiento; no se especifica un porcentaje.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf
**Referencia documental:** La meta indicada es de al menos 90%.
**Cita y página:** «Ejecución del mantenimiento preventivo Cómputo X 100 > = 90%» (p. 1)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La meta está documentada como al menos 90%; la respuesta afirma que no aparece.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué meta de disponibilidad se indica para el servicio de internet?

**Respuesta del chatbot (HTTP 200; 164822.5 ms):**

> No puedo confirmar la meta de disponibilidad del servicio de internet con los documentos disponibles: estos describen el aseguramiento de servicios de red, pero no indican ese porcentaje. La cifra de la referencia histórica no está respaldada por la documentación recuperada.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf
**Referencia documental:** La meta es de al menos 94%.
**Cita y página:** «Conectividad Disponibilidad de servicio de internet X 100 >=94 Mensual» (p. 2)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La evidencia indica una meta de disponibilidad de al menos 94%; la respuesta dice que no puede confirmarla.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cuál es el tiempo máximo indicado para la solución promedio al usuario?

**Respuesta del chatbot (HTTP 200; 164453.2 ms):**

> No puedo confirmar el tiempo máximo indicado: los fragmentos disponibles no especifican una meta de tiempo para la solución promedio. La referencia histórica menciona un plazo de respuesta, pero no está respaldada por la documentación actual y no equivale necesariamente al tiempo de solución.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Web_UI_Unisimon_Portal_Estudiantes.md, P-GT-13_Procedimiento_para_la_gestion_de_requerimientos_de_recursos_y_soluciones_tecnologicas.pdf
**Referencia documental:** Hasta 13 horas laborales.
**Cita y página:** «Solución oportuna de solicitudes Tiempo promedio de solución al usuario <= 13 horas laborales» (p. 2)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La evidencia establece un máximo de 13 horas laborales; la respuesta afirma que no hay una meta especificada.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 14: Anulación y Modificación de Programa Pre-inscripciones.pptx

Juez preliminar: 4/5 correctas · fuente objetivo: 3/5 · chunks indexados: 18.

### Pregunta 1

**Pregunta:** ¿En qué parte del aplicativo puedo cambiar el periodo académico en curso?

**Respuesta del chatbot (HTTP 200; 173297.3 ms):**

> Puedes cambiarlo en **Configuración → Configuración**. Allí modifica el periodo académico en curso y selecciona **Guardar**, en la parte inferior de la ventana; ese periodo se usará para crear nuevas elecciones.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo elecciones - Módulo Configuración.pptx, Anulación y Modificación de Programa Pre-inscripciones.pptx, Aplicativo Elecciones -  Cómo votar.pptx
**Referencia documental:** En el submódulo «Configuración - Configuración».
**Cita y página:** «Configuración - Configuración En esté submódulo podrá modificar la información básica del aplicativo, incluyendo el periodo académico en curso» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.94 · Da la ruta «Configuración → Configuración» solicitada; los detalles adicionales no contradicen la evidencia citada.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** Después de modificar la configuración, ¿cómo guardo los cambios?

**Respuesta del chatbot (HTTP 200; 174198.9 ms):**

> Al terminar de modificar los campos, selecciona **«Guardar»** en la parte inferior de la ventana. Esto guarda los cambios realizados.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo elecciones - Módulo Configuración.pptx, Anulación y Modificación de Programa Pre-inscripciones.pptx, Liquidacion de servicios academicos - Configuración.pptx
**Referencia documental:** Selecciona «Guardar», que aparece en la parte inferior de la ventana.
**Cita y página:** «Al finalizar la modificación de los campos, seleccione el botón “Guardar” que aparece en la parte inferior de la ventana para guardar los cambios realizados.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica seleccionar «Guardar» en la parte inferior de la ventana.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué puedo hacer desde el submódulo de usuarios?

**Respuesta del chatbot (HTTP 200; 174759.1 ms):**

> Desde el submódulo **Configuración - Usuarios** puedes ver la lista de usuarios con acceso a los módulos de gestión, crear usuarios nuevos y modificar o inactivar los existentes. Para crear uno, selecciona **“Nuevo agente”** y completa los campos requeridos, incluidos el nombre de usuario, nombre, apellidos, correo electrónico, cargo, contraseña y los módulos a los que tendrá acceso.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Anulación y Modificación de Programa Pre-inscripciones.pptx, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf
**Referencia documental:** Puedes listar usuarios con acceso a los módulos de gestión, crear usuarios nuevos y modificar o inactivar los existentes.
**Cita y página:** «En esté submódulo podrá listar todos los usuarios que tienen acceso a los módulos de gestión del aplicativo, crear nuevos usuarios, y modificar o inactivar los ya existentes.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.96 · Resume correctamente las funciones documentadas del submódulo; los campos añadidos para crear usuarios están respaldados por la evidencia aportada para la pregunta siguiente.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué datos hay que completar para crear un usuario nuevo?

**Respuesta del chatbot (HTTP 200; 180647.5 ms):**

> ¿Te refieres a crear un usuario nuevo en **Portal CovidApp** o a registrar una **ayuda educativa**? Los fragmentos disponibles no describen la creación de una cuenta de usuario: solo indican que, para autorizar a alguien en CovidApp, se ingresa su tipo de documento, número de identificación y fecha máxima de ingreso. Para crear una ayuda educativa, se ingresa el documento o código del estudiante y se completan los demás campos del formulario.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Manual de Usuario - Portal CovidApp.pdf, Gestión de Ayudas Educativas.pdf
**Referencia documental:** Como mínimo, nombre de usuario, nombre, apellidos, email, cargo, contraseña y los módulos a los que se asignarán permisos.
**Cita y página:** «Deberá diligenciar al menos los campos “Nombre de usuario”, “Nombre”, “Apellidos”, “Email”, “Cargo”, la contraseña y los módulos a los que se le asignará permisos.» (p. 5)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La evidencia especifica los campos requeridos para crear un usuario; la respuesta contesta sobre otros sistemas y datos.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo creo una elección dirigida a estudiantes?

**Respuesta del chatbot (HTTP 200; 174208.8 ms):**

> Para crear una elección dirigida a estudiantes:
>
> 1. En el submódulo **Estudiantes**, selecciona **Agregar Elección**.
> 2. Completa los campos de la ventana emergente.
> 3. Selecciona **Guardar**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx
**Referencia documental:** Selecciona «Agregar elección», completa los campos de la ventana emergente y luego selecciona «Guardar».
**Cita y página:** «Para crear una elección dirigida a estudiantes, seleccione el botón “Agregar elección” y luego diligencie los campos de la ventana emergente que aparecerá. Por último seleccione el botón “Guardar”.» (p. 9)
**Juez automático:** Correcta (preliminar) · confianza 0.97 · Indica los tres pasos documentados: agregar elección, completar los campos y guardar.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 15: Aplicativo Elecciones -  Cómo votar.pptx

Juez preliminar: 4/5 correctas · fuente objetivo: 5/5 · chunks indexados: 5.

### Pregunta 1

**Pregunta:** ¿Cómo empiezo a votar en una elección?

**Respuesta del chatbot (HTTP 200; 183787.3 ms):**

> Ingresa al portal de elecciones: https://elecciones.unisimon.edu.co/. Verás las elecciones en las que puedes participar según tu rol; selecciona **Votar** en la elección que deseas. Después, haz clic en la foto del candidato y confirma la acción. Al finalizar, el sistema volverá a la pantalla de inicio e indicará que tu voto fue enviado con éxito.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** En el listado de elecciones, selecciona «Votar» en la elección en la que quieres participar.
**Cita y página:** «Para iniciar, seleccione el botón “Votar” de la elección en la que desea participar.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.94 · Incluye seleccionar «Votar» en la elección; los pasos adicionales coinciden con la evidencia del mismo flujo.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Cómo sé qué elecciones puedo votar?

**Respuesta del chatbot (HTTP 200; 184497.1 ms):**

> Ingresa a **https://elecciones.unisimon.edu.co/**. Al entrar, verás el listado de elecciones en las que puedes participar según tu rol dentro de la institución; cada una aparecerá con la opción **Votar**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Al ingresar, verás las elecciones en las que puedes participar según tu rol en la institución.
**Cita y página:** «Al ingresar podrá visualizar un listado con todas las elecciones en las que podrá participar según su rol dentro de la institución.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.96 · Explica que el listado muestra las elecciones disponibles según el rol institucional.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo selecciono al candidato por quien quiero votar?

**Respuesta del chatbot (HTTP 200; 185580.4 ms):**

> En la elección correspondiente, haz clic en el **nombre o la foto del candidato** que elegiste. El sistema te pedirá confirmar la acción.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Haz clic sobre la foto del candidato elegido.
**Cita y página:** «Haga clic sobre la foto del candidato por el que desea votar, el sistema le solicitará confirmación de la acción.» (p. 4)
**Juez automático:** Parcial (preliminar) · confianza 0.96 · Incluye hacer clic en la foto, pero añade que también se puede seleccionar por el nombre, sin respaldo en la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿El sistema me pide confirmar cuando elijo a un candidato?

**Respuesta del chatbot (HTTP 200; 186423.3 ms):**

> Sí. Al hacer clic en la foto del candidato por quien desea votar, el sistema le solicitará confirmar la acción.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Cómo votar.pptx
**Referencia documental:** Sí. Después de hacer clic en la foto del candidato, el sistema solicita confirmar la acción.
**Cita y página:** «Haga clic sobre la foto del candidato por el que desea votar, el sistema le solicitará confirmación de la acción.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Confirma correctamente que el sistema solicita confirmación tras seleccionar la foto del candidato.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo confirmo que mi voto se envió correctamente?

**Respuesta del chatbot (HTTP 200; 197081.3 ms):**

> Al finalizar la votación, el aplicativo vuelve automáticamente a la pantalla de inicio y te indica que tu voto fue enviado con éxito. Esa confirmación en pantalla es la señal de que se registró correctamente.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** El sistema vuelve automáticamente a la pantalla de inicio e indica que el voto se envió con éxito.
**Cita y página:** «Al finalizar, el sistema automáticamente volverá a la pantalla de inicio, indicándole que su voto ha sido enviado con éxito.» (p. 5)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Describe correctamente el retorno a la pantalla de inicio y el aviso de envío exitoso.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 16: Aplicativo elecciones - Módulo Configuración.pptx

Juez preliminar: 3/5 correctas · fuente objetivo: 3/5 · chunks indexados: 8.

### Pregunta 1

**Pregunta:** ¿Qué información puedo cambiar en el submódulo Configuración?

**Respuesta del chatbot (HTTP 200; 195102.7 ms):**

> En el submódulo **Configuración - Configuración** puedes modificar la información básica del aplicativo, incluido el período académico en curso. Ese período determina el que se usará al crear nuevas elecciones; al terminar los cambios, selecciona **Guardar** en la parte inferior de la ventana.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo elecciones - Módulo Configuración.pptx, Anulación y Modificación de Programa Pre-inscripciones.pptx, Matricula (2).pptx
**Referencia documental:** La información básica del aplicativo, incluido el periodo académico en curso.
**Cita y página:** «En este submódulo podrá modificar la información básica del aplicativo, incluyendo el periodo académico en curso» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.97 · Indica la información básica y el periodo académico en curso; el dato adicional sobre nuevas elecciones está respaldado por la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿De qué depende el periodo académico de las nuevas elecciones?

**Respuesta del chatbot (HTTP 200; 194824.0 ms):**

> Depende del periodo académico en curso configurado en el submódulo **Configuración** del aplicativo de Elecciones. Ese valor se usa al crear nuevas elecciones.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx
**Referencia documental:** Del periodo académico en curso configurado en el aplicativo.
**Cita y página:** «de este dato dependerá el periodo académico para la creación de nuevas elecciones.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Responde que depende del periodo académico en curso configurado en Configuración.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo guardo los cambios que hice en la configuración?

**Respuesta del chatbot (HTTP 200; 195102.6 ms):**

> Al terminar de modificar los campos, selecciona **«Guardar»** en la parte inferior de la ventana. Así se guardan los cambios realizados en la configuración del aplicativo.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo elecciones - Módulo Configuración.pptx, Liquidacion de servicios academicos - Configuración.pptx, Anulación y Modificación de Programa Pre-inscripciones.pptx
**Referencia documental:** Al terminar de modificar los campos, selecciona “Guardar” en la parte inferior de la ventana.
**Cita y página:** «seleccione el botón “Guardar” que aparece en la parte inferior de la ventana para guardar los cambios realizados.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica seleccionar “Guardar” al terminar, en la parte inferior de la ventana.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Puedo modificar o inactivar usuarios que ya tienen acceso al aplicativo?

**Respuesta del chatbot (HTTP 200; 205203.8 ms):**

> La modificación o inactivación de usuarios debe gestionarse según las funciones y necesidades de acceso de cada persona; no puedo confirmar que puedas hacerlo directamente dentro del aplicativo. La Universidad establece que la Dirección de TI, junto con las jefaturas correspondientes, administra la creación, modificación e inhabilitación de usuarios y perfiles. Si necesitas cambiar un acceso, coordínalo con tu jefe inmediato para que gestione la solicitud ante el área de TI.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf
**Referencia documental:** Sí. En el submódulo Usuarios se pueden modificar o inactivar los usuarios existentes.
**Cita y página:** «crear nuevos usuarios, y modificar o inactivar los ya existentes.» (p. 4)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · La evidencia confirma que se pueden modificar o inactivar usuarios existentes; la respuesta lo pone en duda y ofrece otro procedimiento.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Qué datos tengo que completar para crear un usuario nuevo?

**Respuesta del chatbot (HTTP 200; 208598.7 ms):**

> Los fragmentos disponibles no documentan la creación de un usuario nuevo en un sistema específico: el manual de CovidApp cubre autorizaciones y bloqueos, y la guía de Movilidad Académica describe la gestión de recursos. Por eso no puedo confirmar qué campos debes completar para crear una cuenta. ¿En qué sistema o módulo estás intentando crear el usuario?
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Manual de Usuario - Portal CovidApp.pdf, Movilidad Académica - Administrativo.pdf
**Referencia documental:** Como mínimo, nombre de usuario, nombre, apellidos, email, cargo, contraseña y los módulos a los que tendrá permisos.
**Cita y página:** «Deberá diligenciar al menos los campos “Nombre de usuario”, “Nombre”, “Apellidos”, “Email”, “Cargo”, la contraseña y los módulos a los que se le asignará permisos.» (p. 5)
**Juez automático:** Parcial (preliminar) · confianza 0.98 · No inventa campos y reconoce la falta de información en sus fuentes, pero no da los datos que la evidencia sí documenta.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 17: Aplicativo Elecciones -  Módulo Docentes.pptx

Juez preliminar: 3/5 correctas · fuente objetivo: 5/5 · chunks indexados: 13.

### Pregunta 1

**Pregunta:** ¿Puedo buscar una elección de docentes sin revisar toda la tabla?

**Respuesta del chatbot (HTTP 200; 210289.6 ms):**

> No puedo confirmar que el módulo de elecciones de docentes tenga un buscador o filtro; la guía disponible no documenta esa opción. Como alternativa general, puedes usar **Ctrl+F** (o **⌘+F** en Mac) para buscar el nombre de la elección entre el contenido que esté visible en la página. Si la tabla tiene varias páginas, quizá debas revisar cada una.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Sí, puedes usar el filtro de la esquina superior derecha de la tabla de registros.
**Cita y página:** «podrá realizar búsquedas rápidas usando el filtro que se encuentra en la esquina superior derecha de la tabla de registros.» (p. 3)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Niega que haya un filtro, aunque la evidencia lo confirma, y propone una alternativa no solicitada.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Cómo creo una elección para docentes?

**Respuesta del chatbot (HTTP 200; 207958.0 ms):**

> Para crear una elección dirigida a docentes, ingresa al aplicativo de elecciones en https://elecciones.unisimon.edu.co/ con tu usuario y contraseña institucional. Luego, en el submódulo **Docentes**, selecciona **Agregar Elección**, completa los campos de la ventana emergente y haz clic en **Guardar**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx
**Referencia documental:** Selecciona “Agregar Elección”, completa los campos de la ventana emergente y luego selecciona “Guardar”.
**Cita y página:** «seleccione el botón “Agregar Elección” y luego diligencie los campos de la ventana emergente que aparecerá. Por último seleccione el botón “Guardar”.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Incluye los pasos documentados: entrar al submódulo, agregar la elección, completar los campos y guardar.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo cierro las votaciones de una elección que está activa?

**Respuesta del chatbot (HTTP 200; 208305.0 ms):**

> Para cerrar las votaciones, en el módulo de elecciones selecciona **Configuración** en la elección correspondiente y cambia su estado de **Activo** a **Inactivo**. Mientras esté activa, las personas podrán votar; al dejarla inactiva, se cierran las votaciones.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** Cambia el estado de la elección a “Inactivo”.
**Cita y página:** «para cerrar las votaciones cambie el estado a “Inactivo”.» (p. 5)
**Juez automático:** Correcta (preliminar) · confianza 0.97 · Indica cambiar el estado a “Inactivo” para cerrar las votaciones.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué tengo que hacer para eliminar una elección?

**Respuesta del chatbot (HTTP 200; 218389.3 ms):**

> La guía disponible no documenta los pasos para eliminar una elección; solo indica que se pueden crear, modificar o eliminar elecciones en los submódulos de **Estudiantes, Docentes, Egresados y Funcionarios**, sin especificar el botón ni el proceso. Si tienes acceso al módulo correspondiente a la comunidad de la elección, busca allí la opción de eliminación; no confirmes una acción irreversible si no estás seguro de que seleccionaste la elección correcta.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** Selecciona “Eliminar”; el sistema pedirá que confirmes la acción.
**Cita y página:** «Para eliminar una elección, seleccione el botón “Eliminar”, el sistema le pedirá confirmación de la acción.» (p. 6)
**Juez automático:** Parcial (preliminar) · confianza 0.99 · No proporciona el paso documentado de seleccionar “Eliminar” y confirmar la acción.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Dónde consulto los votos de cada candidato?

**Respuesta del chatbot (HTTP 200; 220595.5 ms):**

> En el aplicativo de Elecciones, entra en **Resultados** desde el menú lateral y selecciona **Ver** en la elección que quieres consultar. Se abrirá una ventana con el total de votos y los votos obtenidos por cada candidato.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** En “Resultados”, selecciona “Ver” en la elección que quieres consultar; aparecerá el total general y los votos por candidato.
**Cita y página:** «Aparecerá una ventana en la cual visualizará el total de votos general y los obtenidos por cada candidato.» (p. 11)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica entrar en Resultados, seleccionar “Ver” y consultar los votos generales y por candidato.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 18: Aplicativo Elecciones -  Módulo Egresados.pptx

Juez preliminar: 3/5 correctas · fuente objetivo: 3/5 · chunks indexados: 13.

### Pregunta 1

**Pregunta:** ¿Se puede buscar una elección de egresados usando un filtro?

**Respuesta del chatbot (HTTP 200; 220278.7 ms):**

> En la información disponible no se documenta un filtro para buscar elecciones de egresados. La guía solo indica que, para editar una elección, debes seleccionar **«Configuración»**, modificar los campos que necesites y pulsar **«Guardar»**; eso no confirma que haya una opción de búsqueda por filtro.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Sí, el filtro está en la esquina superior derecha de la tabla de registros.
**Cita y página:** «podrá realizar búsquedas rápidas usando el filtro que se encuentra en la esquina superior derecha de la tabla de registros.» (p. 3)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Niega que esté documentado un filtro, aunque la evidencia confirma que existe en la esquina superior derecha.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Cuál es el procedimiento para agregar una elección de egresados?

**Respuesta del chatbot (HTTP 200; 221115.8 ms):**

> Para agregar una elección dirigida a egresados:
>
> 1. En el submódulo **Egresados**, selecciona **Agregar Elección**.
> 2. Completa los campos de la ventana emergente.
> 3. Selecciona **Guardar** para crearla.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx
**Referencia documental:** Selecciona “Agregar Elección”, completa los campos de la ventana emergente y pulsa “Guardar”.
**Cita y página:** «seleccione el botón “Agregar Elección” y luego diligencie los campos de la ventana emergente que aparecerá. Por último seleccione el botón “Guardar”.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Describe los pasos documentados para agregar la elección y guardarla.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Cómo hago para que ya no se pueda votar en una elección?

**Respuesta del chatbot (HTTP 200; 220596.0 ms):**

> La guía documenta cómo emitir un voto, pero no cómo cerrar o deshabilitar una elección. No puedo confirmar que esa opción esté disponible para votantes; si necesitas finalizar una elección, debes gestionarlo por el canal institucional autorizado para administrar elecciones.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Cambia el estado de la elección a “Inactivo”.
**Cita y página:** «para cerrar las votaciones cambie el estado a “Inactivo”.» (p. 5)
**Juez automático:** Parcial (preliminar) · confianza 0.99 · No da el estado “Inactivo” que la evidencia señala para cerrar las votaciones.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** Al eliminar una elección, ¿el sistema pide confirmación?

**Respuesta del chatbot (HTTP 200; 228808.3 ms):**

> Sí. Al seleccionar **“Eliminar”**, el sistema pide confirmar la acción.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Sí, al seleccionar “Eliminar” el sistema pide confirmar la acción.
**Cita y página:** «Para eliminar una elección, seleccione el botón “Eliminar”, el sistema le pedirá confirmación de la acción.» (p. 6)
**Juez automático:** Correcta (preliminar) · confianza 0.98 · Responde correctamente que al seleccionar “Eliminar” el sistema pide confirmación.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo veo el total de votos de una elección y los votos por candidato?

**Respuesta del chatbot (HTTP 200; 229095.7 ms):**

> En el portal de Elecciones, abre **Resultados** en el menú lateral y selecciona **Ver** junto a la elección que quieres consultar. Se abrirá una ventana con el total general de votos y los votos obtenidos por cada candidato.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** En el menú lateral, entra en “Resultados” y selecciona “Ver” en la elección correspondiente.
**Cita y página:** «Aparecerá una ventana en la cual visualizará el total de votos general y los obtenidos por cada candidato.» (p. 11)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica la ruta de Resultados y “Ver”, y explica qué datos muestra la ventana.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 19: Aplicativo Elecciones -  Módulo Estudiantes.pptx

Juez preliminar: 4/5 correctas · fuente objetivo: 5/5 · chunks indexados: 13.

### Pregunta 1

**Pregunta:** ¿Puedo filtrar la lista para encontrar una elección estudiantil?

**Respuesta del chatbot (HTTP 200; 235751.2 ms):**

> Sí. En el submódulo **Estudiantes - Elecciones**, puedes usar el filtro ubicado en la esquina superior derecha de la tabla de registros para buscar una elección estudiantil.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Sí, usa el filtro ubicado en la esquina superior derecha de la tabla de registros.
**Cita y página:** «podrá realizar búsquedas rápidas usando el filtro que se encuentra en la esquina superior derecha de la tabla de registros.» (p. 3)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Confirma el filtro y ubica correctamente su posición en la tabla.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Cómo agrego una elección dirigida a estudiantes?

**Respuesta del chatbot (HTTP 200; 229095.6 ms):**

> 1. En el submódulo **Estudiantes**, selecciona **“Agregar Elección”**.
> 2. Completa los campos de la ventana emergente.
> 3. Selecciona **“Guardar”** para crearla.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx
**Referencia documental:** Pulsa “Agregar Elección”, completa los campos de la ventana emergente y selecciona “Guardar”.
**Cita y página:** «seleccione el botón “Agregar Elección” y luego diligencie los campos de la ventana emergente que aparecerá. Por último seleccione el botón “Guardar”.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Incluye los pasos requeridos: “Agregar Elección”, completar los campos y guardar.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** ¿Qué estado debo poner para cerrar las votaciones?

**Respuesta del chatbot (HTTP 200; 232202.9 ms):**

> Cambia el estado de la elección a **“Inactivo”** para cerrar las votaciones. Mientras esté en **“Activo”**, los usuarios podrán votar.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** Debes cambiar el estado de la elección a “Inactivo”.
**Cita y página:** «para cerrar las votaciones cambie el estado a “Inactivo”.» (p. 5)
**Juez automático:** Correcta (preliminar) · confianza 0.98 · Indica cambiar el estado a “Inactivo”, como señala la evidencia.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Cómo elimino una elección estudiantil?

**Respuesta del chatbot (HTTP 200; 242598.8 ms):**

> No tengo un procedimiento institucional verificado para eliminar una elección estudiantil. La guía disponible solo muestra opciones relacionadas con la elección y un botón **GUARDAR**; no documenta su eliminación. Como borrar una elección puede requerir permisos administrativos, no intentes hacerlo desde esa pantalla: consulta con la persona o dependencia responsable de gestionar las elecciones estudiantiles.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Selecciona el botón “Eliminar” y confirma la acción cuando el sistema lo solicite.
**Cita y página:** «Para eliminar una elección, seleccione el botón “Eliminar”, el sistema le pedirá confirmación de la acción.» (p. 6)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Afirma que no hay un procedimiento documentado y recomienda no intentarlo, aunque la evidencia indica seleccionar “Eliminar” y confirmar.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Dónde veo cuántos votos obtuvo cada candidato?

**Respuesta del chatbot (HTTP 200; 239113.3 ms):**

> Ingresa al portal de elecciones y selecciona **Resultados** en el menú lateral. Luego, haz clic en **Ver** junto a la elección que quieres consultar; se abrirá una ventana con el total general de votos y los votos obtenidos por cada candidato.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** Ve a “Resultados” en el menú lateral y pulsa “Ver” en la elección que te interesa.
**Cita y página:** «Aparecerá una ventana en la cual visualizará el total de votos general y los obtenidos por cada candidato.» (p. 11)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Indica abrir Resultados, seleccionar “Ver” y consultar el total y los votos por candidato.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

## Documento 20: Aplicativo Elecciones -  Módulo Funcionarios.pptx

Juez preliminar: 2/5 correctas · fuente objetivo: 4/5 · chunks indexados: 13.

### Pregunta 1

**Pregunta:** ¿Cómo encuentro rápido una elección para funcionarios?

**Respuesta del chatbot (HTTP 200; 242597.2 ms):**

> No puedo confirmar con estos fragmentos una búsqueda rápida de elecciones en el módulo de Funcionarios: solo describen cómo editar una elección existente, desde **Configuración** y luego **Guardar**. No indican cómo localizarla ni qué filtros usar.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Funcionarios.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** Usa el filtro de la esquina superior derecha de la tabla de registros.
**Cita y página:** «podrá realizar búsquedas rápidas usando el filtro que se encuentra en la esquina superior derecha de la tabla de registros.» (p. 3)
**Juez automático:** Incorrecta (preliminar) · confianza 0.99 · Niega que esté documentada la búsqueda rápida, pese a que la evidencia confirma el filtro de la tabla.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 2

**Pregunta:** ¿Qué pasos sigo para crear una elección para funcionarios?

**Respuesta del chatbot (HTTP 200; 244638.3 ms):**

> 1. En el aplicativo de Elecciones, entra al submódulo **Funcionarios**.
> 2. Selecciona **Agregar Elección**.
> 3. Completa los campos de la ventana emergente y selecciona **Guardar**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Funcionarios.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx
**Referencia documental:** Selecciona “Agregar Elección”, completa los campos de la ventana emergente y pulsa “Guardar”.
**Cita y página:** «seleccione el botón “Agregar Elección” y luego diligencie los campos de la ventana emergente que aparecerá. Por último seleccione el botón “Guardar”.» (p. 4)
**Juez automático:** Correcta (preliminar) · confianza 0.99 · Describe los pasos documentados para crear una elección de funcionarios.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 3

**Pregunta:** Una elección está activa, ¿cómo impido que se siga votando?

**Respuesta del chatbot (HTTP 200; 247113.9 ms):**

> En el módulo de elecciones correspondiente, cambia el estado de la elección de **“Activo”** a **“Inactivo”**. Mientras esté activa, las personas podrán votar; al ponerla inactiva, se cierran las votaciones. La guía indica que el cambio se hace desde **“Configuración”**, editando el estado y seleccionando **“Guardar”**.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Estudiantes.pptx, Aplicativo Elecciones -  Módulo Egresados.pptx, Aplicativo Elecciones -  Módulo Funcionarios.pptx
**Referencia documental:** Cambia el estado de la elección a “Inactivo”.
**Cita y página:** «para cerrar las votaciones cambie el estado a “Inactivo”.» (p. 5)
**Juez automático:** Correcta (preliminar) · confianza 0.97 · Indica poner la elección en “Inactivo” para cerrar las votaciones.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 4

**Pregunta:** ¿Qué pasa si selecciono “Eliminar” en una elección?

**Respuesta del chatbot (HTTP 200; 250631.3 ms):**

> Los fragmentos disponibles no indican qué ocurre al seleccionar **“Eliminar”** en una elección, así que no puedo confirmar si la acción se puede revertir ni qué información afectaría. Para evitar cambios no deseados, no lo selecciones hasta verificarlo con el canal institucional responsable de administrar las elecciones.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** no · **Fuentes devueltas:** Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Módulo Docentes.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx
**Referencia documental:** El sistema te pedirá que confirmes la acción.
**Cita y página:** «Para eliminar una elección, seleccione el botón “Eliminar”, el sistema le pedirá confirmación de la acción.» (p. 6)
**Juez automático:** Parcial (preliminar) · confianza 0.99 · No responde que el sistema pide confirmar la acción al seleccionar “Eliminar”.
**Tu validación:** correcta / parcial / incorrecta / no verificable.

### Pregunta 5

**Pregunta:** ¿Cómo consulto los resultados de una elección de funcionarios?

**Respuesta del chatbot (HTTP 200; 251300.5 ms):**

> No puedo confirmar en la documentación disponible cómo consultar los resultados de una elección de funcionarios: los fragmentos solo explican la creación y edición de elecciones y la gestión de candidatos, no el acceso a resultados. Para evitar indicarte una opción o ruta incorrecta, consulta con la persona responsable de esa elección o con quien administra el aplicativo.
>
> ---
> 📌 **Canales Oficiales de Soporte TI:**
> 📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
> 📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129
>
>
> ¿Pudiste resolver tu problema con estos pasos?
> - Selecciona o escribe **Sí** si te funcionó.
> - Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

**Fuente esperada recuperada:** sí · **Fuentes devueltas:** Aplicativo Elecciones -  Módulo Funcionarios.pptx, Aplicativo Elecciones -  Cómo votar.pptx, Aplicativo Elecciones -  Órganos colegiados.pptx, Aplicativo elecciones - Módulo Configuración.pptx, Aplicativo Elecciones -  Módulo Usuarios Votantes.pptx
**Referencia documental:** En el menú lateral, selecciona “Resultados” y luego “Ver” en la elección correspondiente.
**Cita y página:** «Aparecerá una ventana en la cual visualizará el total de votos general y los obtenidos por cada candidato.» (p. 11)
**Juez automático:** Parcial (preliminar) · confianza 0.99 · No responde la ruta documentada para consultar resultados: entrar en Resultados y seleccionar “Ver”.
**Tu validación:** correcta / parcial / incorrecta / no verificable.
