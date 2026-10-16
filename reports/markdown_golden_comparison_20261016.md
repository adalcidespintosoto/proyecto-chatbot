# Comparación de respuestas con Golden Cache activa

**Fecha:** 16/10/2026  
**Modelo:** openai / gpt-6-luna

## Resultado

| Medida | Sin Golden Cache | Golden Cache activa |
|---|---:|---:|
| Preguntas | 20 | 20 |
| Llamadas completadas | 20 | 20 |
| Errores | 0 | 0 |
| Tiempo medio | 8.1 s | 7.8 s |
| Golden Cache aportó referencia | 0 | 6 de 20 |
| Entradas guardadas en Golden Cache | 977 → 977 | 977 → 977 |

Con la caché activa, el sistema siguió llamando al LLM para las 20 preguntas; la respuesta guardada se aporta como referencia secundaria. No se registró telemetría de chat ni se guardaron casos nuevos. La entrada “cached tokens” de los logs de OpenAI corresponde al caché de prompt del proveedor, no a Golden Cache.

## Preguntas donde sí coincidió Golden Cache

| Pregunta | Similitud | Observación |
|---|---:|---|
| Teams no me deja iniciar sesión, ¿qué puedo hacer? | 0.944 | El RAG y el LLM también participaron en la respuesta. |
| El computador dice que está conectado, pero no abre ninguna página, ¿cómo reviso si es la red? | 1.000 | El RAG y el LLM también participaron en la respuesta. |
| El punto de red de mi oficina no funciona, ¿cómo reporto esa falla? | 0.905 | El RAG y el LLM también participaron en la respuesta. |
| En Teams no me escuchan cuando entro a una reunión, ¿qué reviso? | 0.959 | El RAG y el LLM también participaron en la respuesta. |
| No puedo activar el micrófono o la cámara en una videollamada de Teams, ¿cómo lo soluciono? | 0.908 | El RAG y el LLM también participaron en la respuesta. |
| Creo que mi computador tiene un virus, ¿qué pasos debo seguir? | 1.000 | El RAG y el LLM también participaron en la respuesta. |

## Respuestas con Golden Cache activa

### 1. No puedo entrar al correo institucional, ¿qué reviso?

**Categoría:** Cuentas y acceso  
**Golden Cache:** no  
**Fuentes recuperadas:** Activar Usuario y Correo institucional.pdf, instructivo portales estudiantes.pptx, instructivo portales estudiantes.pdf, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf  
**Tiempo:** 17.6 s

**Respuesta:**

Revisa primero que tengas conexión a internet y que estés usando el usuario institucional completo y la contraseña de esa cuenta. Si puedes, prueba desde una ventana privada o desde otro navegador; así descartas un problema de sesión o caché. No compartas tu contraseña ni códigos de verificación.

Los fragmentos disponibles mencionan guías de acceso al correo estudiantil, pero no incluyen los pasos ni el enlace para entrar o restablecer la contraseña. ¿Tu cuenta es de estudiante, docente o funcionario? El siguiente paso depende del perfil.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 2. Teams no me deja iniciar sesión, ¿qué puedo hacer?

**Categoría:** Cuentas y acceso  
**Golden Cache:** sí, similitud 0.944  
**Fuentes recuperadas:** Como_acceder_a_Microsoft_Teams.pdf, Como_acceder_MS_Teams_Estudiantes.pdf, instructivo portales estudiantes.pptx  
**Tiempo:** 14.5 s

**Respuesta:**

Entiendo el inconveniente. Prueba estos pasos para entrar a Teams desde el correo institucional:

1. En el sitio web de Unisimon, abre **Servicios** y elige la opción correspondiente: **Correo Estudiantes** si eres estudiante, o **Correo Funcionarios Microsoft** si eres funcionario.
2. Inicia sesión con tu usuario y contraseña de Microsoft. Si eres funcionario, usa el usuario y la clave indicados en el Portal de Gestión Académico-Administrativa.
3. Cuando aparezca el panel principal, selecciona el icono de **Teams**.

Si no puedes iniciar sesión en el correo, verifica que estés usando el correo institucional y la contraseña de Microsoft correspondientes y que no haya errores al escribirlos. No compartas tu contraseña ni códigos de verificación. Si continúa el problema, dime en qué paso se detiene y qué mensaje de error aparece, sin incluir datos personales ni credenciales.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 3. Se me olvidó la contraseña de la cuenta institucional, ¿cómo la recupero?

**Categoría:** Cuentas y acceso  
**Golden Cache:** no  
**Fuentes recuperadas:** Web_UI_Unisimon_Portal_Estudiantes.md, Restablecimiento de contraseña.pptx, Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf, instructivo portales estudiantes.pdf  
**Tiempo:** 8.2 s

**Respuesta:**

La recuperación depende de si es una cuenta de **estudiante** o de **colaborador**:

**Si eres estudiante**, desde el sitio de la Universidad entra a **Portales → Portal estudiantes**, selecciona la sede **Barranquilla** y abre **«Olvidé mi Usuario / Contraseña»**. Ingresa tu código de estudiante o número de identificación y presiona **«Enviar»**. Revisa tu correo personal; el procedimiento indica seguir el enlace **«Restablecer contraseña»**, escribir y confirmar la nueva contraseña, y presionar **«Enviar»**. Debería aparecer un mensaje de confirmación.

**Si eres colaborador**, el procedimiento cambia según el servicio: para el portal, la recuperación se gestiona mediante **Talento Humano**; si el problema es un bloqueo de **KACTUS o SEVEN**, se solicita mediante la mesa de servicio.

¿La cuenta es de estudiante o de colaborador, y de qué servicio se trata?

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 4. Me bloquearon el usuario, ¿cómo vuelvo a entrar?

**Categoría:** Cuentas y acceso  
**Golden Cache:** no  
**Fuentes recuperadas:** Web_UI_Unisimon_Portal_Estudiantes.md, Reportes de Caracterización.pptx, Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf, Instructivo StrategicU.pdf, GIE - ASPIRANTES NOV.2021.pptx, instructivo portales estudiantes.pptx, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf  
**Tiempo:** 7.8 s

**Respuesta:**

No sigas intentando iniciar sesión repetidamente; primero verifica que estés usando el usuario correcto. El paso depende del sistema:

- **Si es el Portal de Estudiantes:** en la pantalla de acceso aparece **«Olvidé mi Usuario / Contraseña»** como opción de recuperación. La guía disponible confirma que existe el restablecimiento de la contraseña unificada, pero no detalla cómo desbloquear una cuenta bloqueada.
- **Si es KACTUS o SEVEN (ERP):** el restablecimiento de contraseña corresponde al Técnico Especializado ERP; la documentación disponible no confirma un procedimiento de autoservicio para desbloquear el usuario.

¿En qué sistema te aparece el bloqueo y qué perfil tienes (estudiante, docente o funcionario)?

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 5. Ya cambié la contraseña y todavía no puedo acceder, ¿qué hago?

**Categoría:** Cuentas y acceso  
**Golden Cache:** no  
**Fuentes recuperadas:** Restablecimiento de contraseña este yaaaaaaaaaaaaaaaaaa listo.pdf, Restablecimiento de contraseña.pptx, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, Activar Usuario y Correo institucional.pdf  
**Tiempo:** 7.7 s

**Respuesta:**

Prueba primero a escribir la contraseña manualmente y verifica que el usuario corresponda al servicio al que intentas entrar. Si cambiaste la contraseña desde el Portal Estudiantes, esa misma contraseña también sirve para Aula Extendida y el Correo Estudiantil; no compartas tu contraseña ni códigos de verificación.

¿A qué servicio intentas acceder y qué perfil tienes (estudiante, docente o funcionario)? Ese dato cambia los siguientes pasos.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 6. No me funciona el wifi de la Universidad, ¿qué puedo revisar?

**Categoría:** Conexión y equipos  
**Golden Cache:** no  
**Fuentes recuperadas:** Instructivo StrategicU.pdf, Verificacion de pagos_v1_20211105.pdf, P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf  
**Tiempo:** 6.5 s

**Respuesta:**

Prueba estas verificaciones seguras:

1. Confirma que el Wi‑Fi esté activado y que el modo avión esté desactivado.
2. Desconéctate de la red de la Universidad y vuelve a seleccionarla. Si te solicita iniciar sesión, usa únicamente tus propias credenciales institucionales; no las compartas aquí.
3. Prueba si otros sitios o aplicaciones cargan y, si puedes, compara con otro dispositivo. Así podrás identificar si el problema afecta a la red o solo a un equipo.
4. Reinicia el Wi‑Fi del dispositivo; si sigue igual, reinícialo y vuelve a conectarte.

No tengo instrucciones institucionales verificadas para configurar esta red. Si el problema continúa, contacta al canal oficial de soporte de la Universidad.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 7. El computador dice que está conectado, pero no abre ninguna página, ¿cómo reviso si es la red?

**Categoría:** Conexión y equipos  
**Golden Cache:** sí, similitud 1.000  
**Fuentes recuperadas:** Web_UI_Unisimon_Inicio.md, P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf, P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf, Manual de Usuario - Registro de Ingreso.pdf, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, Instructivo Remisiones desde Calificaciones y Módulo Atención.pdf, P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, Credenciales microsoft.pdf, P-GT-11_Proc._Atencion_de_Incidencias_y_Requerimientos_Katus_Y_Seven_.pdf, Carga de codigos EK.pdf, Gestión de Ingreso -  Solo Consulta .pdf, Evaluación Profesoral.pdf  
**Tiempo:** 8.0 s

**Respuesta:**

Prueba estos pasos para distinguir si el problema está en la red o en el computador:

1. **Abre varias páginas distintas** y vuelve a cargarlas. Si solo falla una, podría ser un problema de ese sitio.
2. **Prueba otro dispositivo conectado a la misma red.** Si tampoco navega, el problema probablemente está en la red; si sí navega, revisa el computador.
3. **Desconecta y vuelve a conectar el Wi‑Fi** en el computador. Como comprobación general, también puedes reiniciarlo.
4. Si usas Wi‑Fi, **acércate al router** para comprobar si mejora la conexión. Si tienes otra red autorizada disponible, prueba conectarte a ella y compara.

Si otros dispositivos tampoco navegan, o si el problema persiste solo en el computador después de estas pruebas, será necesario contactar al canal de soporte técnico autorizado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 8. El punto de red de mi oficina no funciona, ¿cómo reporto esa falla?

**Categoría:** Conexión y equipos  
**Golden Cache:** sí, similitud 0.905  
**Fuentes recuperadas:** P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, GIE - ASPIRANTES NOV.2021.pptx, Instructivo Reportes Consolidados.pdf  
**Tiempo:** 8.4 s

**Respuesta:**

Los documentos disponibles no indican el canal ni los pasos institucionales para reportar una falla de un punto de red de oficina, así que no puedo confirmar una ruta o formulario específico.

Antes de reportarla, puedes comprobar que el cable esté bien conectado y, si tienes uno disponible, probar con otro cable de red. Si el punto sigue sin funcionar, comunícalo por el canal oficial de soporte de TI que use tu oficina e incluye la ubicación exacta, la identificación del punto si la tiene, cuándo empezó la falla y qué comprobaste. No manipules el cableado ni el equipo de red.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 9. Mi computador no enciende, ¿qué debo hacer?

**Categoría:** Conexión y equipos  
**Golden Cache:** no  
**Fuentes recuperadas:** Manual de Usuario - Registro de Ingreso.pdf, P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, Detalle factura (Anexos).pptx, P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf, P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf, CP-GT-01_Gestion_de_TI.pdf, P-GT-13_Procedimiento_para_la_gestion_de_requerimientos_de_recursos_y_soluciones_tecnologicas.pdf, Reporte - Inscripción Reactivada.pptx  
**Tiempo:** 6.7 s

**Respuesta:**

Si tu computador no enciende, prueba estas comprobaciones seguras:

1. Revisa que el cable de alimentación esté bien conectado al computador y al tomacorriente. Si es portátil, verifica también el cargador y prueba otro tomacorriente que sepas que funciona.
2. Desconecta accesorios externos (por ejemplo, memorias USB o periféricos) e intenta encenderlo de nuevo.
3. Observa si aparece alguna luz, sonido o mensaje. Si detectas olor a quemado, calor inusual o daño en el cable, desconéctalo y no sigas intentando encenderlo.

Si sigue sin encender, en Cúcuta puedes contactar la mesa de servicio para reportar el problema. La solicitud se registra como un ticket en Mesa de Ayuda TI; soporte prioriza la atención remota y, si no es posible, coordina una visita o la recogida del equipo.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 10. Se dañaron el mouse y el teclado de mi puesto, ¿cómo solicito que los revisen?

**Categoría:** Conexión y equipos  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf, P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, Anexo_1_CP-GT-01_Descripcion_de_Indicadores_del_proceso__Gestion_de_TI.pdf, P-GT-11_Proc._Atencion_de_Incidencias_y_Requerimientos_Katus_Y_Seven_.pdf, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf  
**Tiempo:** 5.8 s

**Respuesta:**

Contacta a la mesa de servicio por uno de sus canales de atención y describe que el mouse y el teclado de tu puesto están dañados y requieren revisión. La solicitud se registra para que sea categorizada, priorizada y asignada; si no se resuelve en el primer nivel, puede escalarse al segundo nivel.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 11. El equipo está muy lento desde esta mañana, ¿qué puedo revisar antes de pedir soporte?

**Categoría:** Conexión y equipos  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, P-GT-14_Procedimiento_para_la_gestion_de_actualizaciones_de_versiones_en_Kactus_y_o_Seven.pdf, Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf  
**Tiempo:** 6.1 s

**Respuesta:**

Prueba estas revisiones seguras antes de pedir soporte:

1. **Reinicia el equipo** y observa si mejora; esto puede cerrar procesos que estén consumiendo recursos.
2. **Cierra las aplicaciones y pestañas que no estés usando**, especialmente si hay muchas abiertas.
3. **Revisa si hay tareas activas** —por ejemplo, copias, descargas o actualizaciones— y deja que terminen si parecen estar ralentizando el equipo.
4. **Comprueba que haya espacio disponible** en el almacenamiento. Evita borrar archivos o programas si no sabes para qué sirven.

Si sigue lento después de estas pruebas, puedes reportarlo mediante un ticket en **Mesa de Ayuda TI**. La documentación institucional indica ese canal para reportar fallas de equipos.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 12. Teams no abre en mi computador, ¿qué puedo intentar?

**Categoría:** Aplicaciones y reuniones  
**Golden Cache:** no  
**Fuentes recuperadas:** Como_acceder_a_Microsoft_Teams.pdf, Como_acceder_MS_Teams_Estudiantes.pdf, instructivo portales estudiantes.pptx  
**Tiempo:** 8.7 s

**Respuesta:**

Prueba primero cerrar Teams por completo y volver a abrirlo; si sigue sin iniciar, reinicia el computador y comprueba que tengas conexión a internet.

También puedes intentar abrirlo desde el panel de tu correo institucional de Microsoft, usando la ruta que corresponde a tu perfil:

- **Si eres estudiante:** entra en el sitio web de la Universidad → **Servicios → Correo Estudiantes**. Inicia sesión con tu usuario y contraseña de Microsoft y selecciona el icono de **Teams**.
- **Si eres funcionario:** entra en el sitio web de la Universidad → **Servicios → Correo Funcionarios Microsoft**. Inicia sesión con el usuario y la clave indicados en el Portal de Gestión Académico-Administrativa y selecciona el icono de **Teams**.

Si Teams tampoco abre desde ese panel, anota el mensaje de error que aparece y cuándo ocurre para que soporte pueda revisar el caso.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 13. En Teams no me escuchan cuando entro a una reunión, ¿qué reviso?

**Categoría:** Aplicaciones y reuniones  
**Golden Cache:** sí, similitud 0.959  
**Fuentes recuperadas:** Crear reuniones en teams - iPads aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.pdf, Ajustes participantes reuniones  Ms Teams.pdf, Crear reuniones No asociadas a grupos.pdf  
**Tiempo:** 7.6 s

**Respuesta:**

Revisa primero que el micrófono no esté silenciado en la reunión. Si sigue sin funcionar:

1. En Teams, comprueba que esté seleccionado el micrófono que estás usando, especialmente si tienes audífonos conectados.
2. Desconecta temporalmente los audífonos o el dispositivo Bluetooth y prueba el micrófono integrado.
3. Revisa en los ajustes de tu dispositivo que Teams tenga permiso para usar el micrófono; después sal de la reunión y vuelve a entrar.

Si aún no te escuchan, prueba el micrófono en otra aplicación que grabe audio. Si tampoco funciona allí, el problema podría estar en el dispositivo o el micrófono.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 14. No puedo activar el micrófono o la cámara en una videollamada de Teams, ¿cómo lo soluciono?

**Categoría:** Aplicaciones y reuniones  
**Golden Cache:** sí, similitud 0.908  
**Fuentes recuperadas:** Grabar videollamadas en Teams.pdf, Videollamadas en  Teams.pdf, Grabar un clase en Teams y compartir en Stream.pdf  
**Tiempo:** 7.0 s

**Respuesta:**

Prueba estas comprobaciones seguras, en orden:

1. Confirma que el micrófono y la cámara estén conectados y que no tengan una tapa física o un interruptor de silencio activado.
2. Cierra otras aplicaciones o pestañas que puedan estar usando la cámara o el micrófono y vuelve a la llamada.
3. Revisa en la configuración de privacidad de tu dispositivo que Teams tenga permiso para usar el micrófono y la cámara. Si cambias un permiso, cierra y vuelve a abrir Teams.
4. Si sigue igual, reinicia Teams y el dispositivo; si usas Teams desde un navegador, prueba con otro navegador actualizado.

No tengo una guía institucional verificada para resolver este problema específico en Teams, así que no puedo confirmar rutas o botones propios de la Universidad. Si el bloqueo persiste después de estas comprobaciones, contacta al canal de soporte técnico oficial.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 15. Necesito instalar un programa para trabajar, ¿cómo solicito la instalación?

**Categoría:** Aplicaciones y reuniones  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf  
**Tiempo:** 3.4 s

**Respuesta:**

Entiendo que necesitas el programa para poder trabajar; te ayudo a encaminar la solicitud. Según el procedimiento institucional, cuando se trata de instalar software, **la solicitud debe presentarla el jefe de tu Dependencia por la Mesa de Servicio**. Soporte la registra y la asigna al responsable de atenderla.

Puedes compartirle al jefe el nombre del programa y para qué lo necesitas; si tienes a mano la placa del equipo, incluirla también puede ayudar a identificarlo. ¿Qué programa necesitas? Si me dices el nombre, puedo ayudarte a redactar la solicitud para tu jefe.

📌 **Canales de Soporte TI:**
• **Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp `3172683922` | PBX (605) 3444333 Ext. 8003/8004
• **Cúcuta:** `helpdesk@unisimon.edu.co` | PBX (607) 5827070 Ext. 129

### 16. No puedo conectarme a la VPN desde fuera de la Universidad, ¿a quién debo pedir ayuda?

**Categoría:** Aplicaciones y reuniones  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf, Certificados Electrónicos.pptx, Gestión de Ingreso -  Funcionarios.pdf, Volantes.pdf, P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf, 4. Transferencia Externa.pptx, Servicios Institucionales - Profesores.pdf, instructivo portales estudiantes.pptx, P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, Web_Unisimon_Contacto.md, Manual de Usuario - Registro de Ingreso.pdf  
**Tiempo:** 5.0 s

**Respuesta:**

Para conectarte a la infraestructura de la Universidad desde fuera, el procedimiento indica usar únicamente la VPN o conexiones SSH y solicitar apoyo a la **Dirección de TI**, explicando qué acceso necesitas y por cuánto tiempo. No compartas tu contraseña ni códigos de verificación.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 17. Me llegó un correo extraño con un enlace, ¿lo abro o qué hago?

**Categoría:** Seguridad y atención  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf  
**Tiempo:** 6.7 s

**Respuesta:**

No abras el enlace ni respondas al correo. La Universidad indica que no se deben reenviar correos spam ni hacer reenvíos masivos; además, los posibles incidentes de seguridad deben ser evaluados por la Coordinación de Seguridad Informática o por personal designado por la Dirección de TI.

Si ya abriste el enlace, no ingreses contraseñas ni códigos. Detente y repórtalo por el canal institucional de seguridad informática; no puedo confirmar aquí cuál es ese canal.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 18. Creo que mi computador tiene un virus, ¿qué pasos debo seguir?

**Categoría:** Seguridad y atención  
**Golden Cache:** sí, similitud 1.000  
**Fuentes recuperadas:** P-GT-07_Procedimiento_Proteccion_de_Codigo_Malicioso_.pdf, P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf, P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf  
**Tiempo:** 7.1 s

**Respuesta:**

Entiendo la preocupación. Si sospechas que tu computador está infectado, **no intentes analizarlo, desinfectarlo ni eliminar archivos por tu cuenta**: la evaluación y esas acciones corresponden al personal de Seguridad Informática o al personal designado por TI.

1. Desconecta el equipo de Wi‑Fi o de la red si puedes hacerlo con normalidad, y evita usarlo para ingresar contraseñas o acceder a cuentas importantes.
2. No abras archivos sospechosos ni conectes dispositivos removibles.
3. Reporta el incidente al **Oficial de Seguridad de la Información** o, en su defecto, a la **Dirección de TI**, para que lo evalúen. No puedo confirmar en la información disponible un teléfono, correo o enlace específico para ese reporte.
4. Si recibiste un correo sospechoso relacionado con el incidente, no lo abras ni lo reenvíes; repórtalo por el mismo canal.

Evita borrar archivos o instalar herramientas de limpieza; espera las indicaciones del personal autorizado.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 19. Necesito recuperar un archivo de una copia de seguridad, ¿cómo solicito esa ayuda?

**Categoría:** Seguridad y atención  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf, Instructivo Credito Empresarial.pptx, Activar Usuario y Correo institucional.pdf, P-GT-02_Procedimiento_para_el_otorgamiento_modificacion_o_retiro_de_acceso_a_usuarios_del_sistema_de_Informacion.pdf, Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf  
**Tiempo:** 6.9 s

**Respuesta:**

Para solicitar la recuperación, envía la solicitud al área de Soporte Técnico. La restauración sobrescribe información en la base de datos, así que el equipo responsable debe revisar y aprobar la solicitud antes de realizarla.

El procedimiento disponible no indica un correo, formulario ni ruta específicos para pedir la restauración de un archivo. Si se trata de información de un computador de usuario y necesitas **generar una copia** (no restaurar una ya existente), puedes escribir a `solicitudcomputo@unisimon.edu.co`; el procedimiento para esa solicitud indica que debes contar con un medio de almacenamiento para recibir los archivos.



¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

### 20. La falla necesita que un técnico revise mi puesto presencialmente, ¿cómo radico el caso?

**Categoría:** Seguridad y atención  
**Golden Cache:** no  
**Fuentes recuperadas:** P-GT-01_Procedimiento_mantenimiento_equipos_de_computo.pdf, P-GT-14_Procedimiento_para_la_gestion_de_actualizaciones_de_versiones_en_Kactus_y_o_Seven.pdf, P-GT-11_Proc._Atencion_de_Incidencias_y_Requerimientos_Katus_Y_Seven_.pdf, retorno al campus 2021.pdf, P-GT-12_Procedimiento_para_la_gestion_de_cuentas_de_usuario_en_KACTUS_o_SEVEN.pdf, P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf  
**Tiempo:** 6.6 s

**Respuesta:**

Radica la solicitud en la mesa de ayuda para que quede registrada. Una vez recibida, el servicio se prioriza de forma remota; si no es posible resolverlo así, se programa una visita en sitio o, en su defecto, la recogida del equipo para llevarlo al taller de Soporte Técnico.

Al registrarse, recibirás un correo automático con el número de ticket. Los fragmentos disponibles no especifican la URL ni los pasos para abrir la solicitud; no quiero indicarte una ruta que no esté verificada.

---
📌 **Canales Oficiales de Soporte TI:**
📧 **Sede Barranquilla:** `solicitudcomputo@unisimon.edu.co` | WhatsApp: `3172683922` | PBX: (605) 3444333 Ext. 8003/8004
📧 **Sede Cúcuta:** `helpdesk@unisimon.edu.co` | PBX: (607) 5827070 Ext. 129


¿Pudiste resolver tu problema con estos pasos?
- Selecciona o escribe **Sí** si te funcionó.
- Selecciona o escribe **No** para indicarme qué error tienes o generar un reporte.

## Lectura comparativa

- La caché aportó una referencia en 6 casos: acceso a Teams, navegación sin páginas, punto de red, audio en Teams, cámara/micrófono y posible malware.
- En el caso del punto de red, con caché activa la respuesta dejó de atribuir la solicitud al “Líder Funcional”, que venía de una guía específica de KACTUS/SEVEN. Es una mejora en ese ejemplo, aunque todavía faltan pasos institucionales claros.
- Para audio y cámara, la caché ayudó a dar pasos de diagnóstico más directos. Aun así, los manuales recuperados no eran guías específicas de solución de micrófono/cámara.
- Tener una similitud alta no demuestra por sí sola que la respuesta sea correcta. Hay que contrastar cada caso con el documento fuente.
- Las respuestas también cambian por la variación normal del LLM; no se deben atribuir todos los cambios de redacción a Golden Cache.
- La observación sobre el tono y las aprobaciones del jefe inmediato queda como propuesta para ajustar las instrucciones: mencionar los canales del pie con naturalidad y señalar autorización solo cuando el procedimiento correspondiente la exige.

**Informe de la prueba sin caché:** `C:\Users\adalcides.pintos\Documents\proyecto-chatbot\reports\markdown_no_golden_20261016_150913.md`
