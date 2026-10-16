# Procedimiento para la gestión de actualizaciones de versiones en KACTUS y/o SEVEN

## Información del documento
- **Fuente original:** `P-GT-14_Procedimiento_para_la_gestion_de_actualizaciones_de_versiones_en_Kactus_y_o_Seven.pdf`
- **Código, versión y vigencia:** P-GT-14, versión 1, vigente desde 23-11-2023.
- **Sistema o módulo:** KACTUS – HCM y SEVEN.
- **Público o permisos mencionados por la fuente:** Administradores de Kactus y/o Seven y usuarios que participan en la gestión de cambios de actualizaciones. También se mencionan el Técnico especializado en soporte ERP, el Coordinador de Seguridad Informática, los Líderes Funcionales y el proveedor DIGITALWARE.
- **Temas incluidos:** Gestión de ServicePack; registro y descarga de actualizaciones; pruebas, notificación de fallas, aprobación y aplicación en producción; cierre de tarea en GLPI. (Fuente: páginas 1–7)

## Procedimiento: Gestión de actualizaciones de ServicePack en Kactus y Seven

### Propósito
Establecer la normativa para implementar cambios requeridos en las actualizaciones de Kactus y/o Seven, de modo que se registren, valoren, autoricen, documenten e implementen de forma planeada y controlada, minimizando el impacto en producción ante inconvenientes. (Fuente: página 2)

El alcance indicado inicia con la publicación por DIGITALWARE de paquetes de actualización (ServicePack), scripts de base de datos y manuales técnicos y de usuarios en `http://sac.digitalware.co`; contempla su descarga y despliegue en los servidores productivos de aplicaciones de Kactus y Seven de la Universidad Simón Bolívar, y finaliza con la entrega oficial al funcionario. Incluye el registro de planes en pruebas, la gestión de aprobación para las actualizaciones, actividades funcionales productivas y la comunicación de incidentes a terceros. (Fuente: página 2)

### Requisitos y permisos
- Las ServicePack solo se deben descargar desde `http://sac.digitalware.co`. (Fuente: página 5)
- Cada actualización se realiza primero en ambiente de pruebas y, después de las validaciones, en producción. (Fuente: página 5)
- Los usuarios funcionales deben validar sus aplicativos dentro de las 24 horas siguientes a la instalación de los parches. (Fuente: página 5)
- La aplicación de los parches debe realizarse en las ventanas de tiempo definidas y aprobadas. (Fuente: página 5)
- El proveedor DIGITALWARE carga las actualizaciones requeridas para Kactus y/o Seven; también realiza soportes, capacitaciones y atención de incidentes, y es descrito como soporte de tercer nivel. (Fuente: página 3)
- El Técnico especializado en soporte ERP registra las notificaciones de nuevas actualizaciones, programa su publicación en los servidores donde están los archivos de Kactus y Seven, las aplica inicialmente en pruebas y registra el ServicePack y los programas afectados. (Fuente: página 3)
- El Líder Funcional valida funcionalmente Kactus y/o Seven en pruebas e informa al Técnico especializado en soporte ERP de errores funcionales o resultados no deseados tras el despliegue. (Fuente: página 4)
- El Coordinador de Seguridad Informática revisa el riesgo e impacto de las peticiones, coordina la asignación de miembros con el perfil del proceso de Gestión de Cambios, revisa los cambios implementados para verificar si alcanzaron sus objetivos y revisa los cambios fallidos o que debieron deshacerse. También debe asegurar que el Técnico especializado ERP cumpla los procedimientos de cambio establecidos. (Fuente: página 4)
- El responsable de cada actividad debe verificar que la información recibida esté acorde con el procedimiento antes de entregarla o liberar la actividad siguiente. (Fuente: página 4)

### Pasos
1. **Recibir notificaciones y revisar al final de cada mes si se cargaron nuevos ServicePack.** El Técnico especializado en soporte ERP recibe un correo electrónico cada vez que el proveedor carga un nuevo ServicePack en `http://sac.digitalware.co`. Al final del mes revisa si se cargaron nuevos paquetes y verifica que coincidan con las notificaciones por correo. Registro indicado: correo electrónico. (Fuente: página 5)

2. **Descargar los nuevos ServicePack.** El Técnico especializado en soporte ERP descarga los ServicePack notificados por correo, dirigiéndose a `http://sac.digitalware.co`. Registro indicado: plataforma DIGITALWARE. (Fuente: página 5)

3. **Registrar el proceso de actualización como tarea en GLPI.** El Técnico especializado en soporte ERP crea una tarea en GLPI para el proceso de las nuevas actualizaciones. En la tarea debe especificar, mediante un listado o anexando el documento, los programas actualizados del ServicePack entregado por DIGITALWARE. Se documentan en el ticket las evidencias de las actividades 1 y 2. Registro indicado: aplicativo GLPI. (Fuentes: páginas 5–6)

4. **Realizar y registrar la actualización de los programas en el ambiente de pruebas.** El Técnico especializado en soporte ERP realiza las actualizaciones de los ServicePack y anexa el log de actualizaciones. Si las pruebas son exitosas, continúa con la actividad 7. Si no son exitosas, continúa con la actividad 6 hasta lograr el correcto funcionamiento. Registros indicados: aplicativo GLPI y log de actualización. (Fuente: página 6)

5. **Notificar al proveedor cuando se presenten inconvenientes.** Se notifica al proveedor los inconvenientes que ocurran durante las actualizaciones y las pruebas funcionales. Se anexa en GLPI el reporte de la mesa de ayuda de DIGITALWARE. La tabla indica que, si la validación de pruebas es exitosa, se continúa con la actividad 7. Responsable indicado: Técnico de Soporte ERP. Registros indicados: aplicativo GLPI y plataforma DIGITALWARE. (Fuente: página 6)

6. **Actualizar la falla reportada.** Una vez recibida la corrección del fallo reportado, se actualiza el programa. Si la validación es satisfactoria, se continúa con la actividad 7; si no lo es, se vuelve a la actividad 5. Responsable indicado: Técnico de Soporte ERP. Registro indicado: aplicativo GLPI. (Fuente: página 6)

7. **Informar sobre las actualizaciones en pruebas y enviar manuales de usuario.** El Técnico especializado en soporte ERP informa por correo a los Líderes Funcionales involucrados. La actividad se titula “Informar de actualizaciones en el ambiente pruebas y enviar manuales de usuario”. Registro indicado: aplicativo GLPI. (Fuente: página 6)

8. **Notificar el resultado de las pruebas y solicitar aprobación para producción.** Se notifica el resultado de las pruebas realizadas en el ambiente de pruebas y se solicita aprobación para realizar la actualización en producción. Responsable indicado: Coordinador de Seguridad Informática. Registro indicado: aplicativo GLPI. Si se aprueba, se continúa con la actividad 9; si no, se continúa con la actividad 8.1. (Fuentes: páginas 6–7)

   8.1. **Definir las condiciones de aplicación en producción.** Se valida si se han cumplido condiciones como el tiempo de ejecución o el cumplimiento del ciclo de pruebas, considerando el impacto que esto podría tener en las actividades de los colaboradores. Si no se cumplen estas condiciones, la tarea se aplaza. La descripción indica que esta actividad finalizará y pasará a la actividad 9 cuando se cumpla lo señalado, y que se notificará al responsable para realizar la actualización. (Fuente: página 7)

9. **Aplicar las actualizaciones en el servidor productivo.** El Técnico especializado en soporte ERP ejecuta la actualización en el ambiente productivo. Registro indicado: aplicativo GLPI. (Fuente: página 7)

10. **Cerrar la tarea GLPI.** El Técnico de Soporte ERP cierra la tarea documentando los cambios realizados. Registro indicado: aplicativo GLPI. (Fuente: página 7)

### Resultado esperado
- Los cambios requeridos quedan registrados, valorados, autorizados, documentados e implementados de forma planeada y controlada. (Fuente: página 2)
- La actualización se valida en pruebas antes de pasar a producción; los inconvenientes reportados se corrigen y vuelven a validarse según las actividades descritas. (Fuentes: páginas 5–7)
- La tarea de GLPI se cierra documentando los cambios realizados. (Fuente: página 7)

### Errores, límites o excepciones documentadas
- Si las pruebas en el ambiente de pruebas no son exitosas, se notifica al proveedor y se continúa con la corrección del fallo; si la validación posterior sigue siendo negativa, se vuelve a notificar al proveedor. (Fuente: página 6)
- Si no se aprueba la aplicación en producción, se pasa a la actividad 8.1, que contempla aplazar la tarea cuando no se cumplan las condiciones indicadas. (Fuente: página 7)
- La actualización productiva debe ejecutarse en fechas no críticas que puedan afectar el proceso y, si corresponde, se debe informar al Líder Funcional. (Fuente: página 3)
- El Coordinador de Seguridad Informática revisa los cambios implementados, incluidos aquellos que hayan fracasado o tenido que deshacerse. La definición de “ROLL BACK” en el documento es una operación que devuelve el servidor a su estado previo. (Fuentes: páginas 2 y 4)

## Definiciones y registros relacionados

- **Ambiente de Desarrollo:** servidores destinados a realizar pruebas y validaciones de nuevos procesos o despliegues antes de implementarlos en producción. (Fuente: página 2)
- **Ambiente de Producción:** ambiente donde se encuentran los datos operativos y donde los usuarios finales consultan, envían, reciben o intercambian información. (Fuente: página 2)
- **Parches:** cambios aplicados a un sistema informático para corregir errores o actualizarlo. (Fuente: página 2)
- **ROLL BACK:** operación que devuelve el servidor a su estado previo. (Fuente: página 2)
- **ServicePack:** paquete que contiene los scripts de base de datos y programas que se van a actualizar. (Fuente: página 2)
- **GLPI:** software de libre distribución bajo licencia GPL que facilita la administración de recursos informáticos. Incluye software de mesa de ayuda para registrar y atender solicitudes de soporte técnico, gestionar cuentas de usuarios y posibilitar notificaciones por correo electrónico a usuarios y al personal de soporte al inicio, durante los avances o al cierre de una solicitud. (Fuente: página 2)
- **KACTUS – HCM:** sistema modular cuya función principal es gestionar los recursos humanos de las empresas mediante programas que pueden trabajar de forma independiente o estrechamente relacionados, según la necesidad y el criterio de la organización. (Fuente: página 3)
- **SEVEN:** sistema modular cuya función principal es gestionar procesos administrativos, financieros y contables de las empresas que lo poseen, mediante programas que pueden trabajar de forma independiente o estrechamente relacionados, según la necesidad y el criterio de la organización. (Fuente: página 3)
- **Documentos aplicables:** Reglamento interno de trabajo y los documentos establecidos en la Matriz de requisitos reglamentarios y de documentos externos, F-SI-17-GC. (Fuente: página 4)
- **Actores que intervienen:** Líder Funcional, Técnico especializado en soporte ERP, Coordinador de Seguridad Informática y proveedor DIGITALWARE. (Fuente: página 4)
- **Registros del procedimiento:** correo electrónico, aplicativo GLPI, log de actualización y plataforma `http://sac.digitalware.co`. (Fuente: página 7)
- **Anexo mencionado:** Anexo 1, diagrama de flujo. (Fuente: página 7)

## Palabras y formas de búsqueda
*Paráfrasis editoriales para mejorar la búsqueda; no son afirmaciones adicionales del documento.*

- Actualizar Kactus o Seven
- Descargar ServicePack
- Registrar una actualización en GLPI
- Probar una actualización en ambiente de pruebas
- Reportar una falla de actualización a DIGITALWARE
- Solicitar aprobación para actualizar en producción
- Aplicar un ServicePack en producción
- Cerrar la tarea de actualización en GLPI

## Puntos por validar
- La actividad 8.1 indica que, si no se cumplen las condiciones, la tarea se aplaza; también señala que la actividad pasará a la actividad 9 cuando se cumpla lo indicado. No precisa qué ocurre con la aprobación pendiente ni cómo se retoma formalmente el flujo. (Fuente: página 7)
- La actividad 8 se titula “Validaciones de ejecución en productivo”, aunque su descripción trata de notificar los resultados de pruebas en ambiente de pruebas y solicitar aprobación para producción. (Fuente: página 6)
- La actividad 5 incluye la indicación “Validación de pruebas: Exitosa: Continua actividad 7”, aunque la actividad 5 se refiere a notificar inconvenientes. No queda explícito si esta condición corresponde a esa actividad o a otra parte del flujo. (Fuente: página 6)
- La actividad 7 menciona el envío de manuales de usuario en el título, pero la descripción solo especifica informar por correo a los Líderes Funcionales; no detalla el envío de manuales. (Fuente: página 6)
- El alcance menciona una entrega oficial al funcionario, pero el procedimiento enumerado no describe una actividad de entrega. (Fuentes: páginas 2, 5–7)
- Se menciona la programación de publicación de los ServicePack en servidores donde están los archivos de Kactus y Seven, pero las actividades enumeradas no describen cuándo ni cómo se realiza esa publicación. (Fuentes: páginas 3, 5–7)
- La fuente define “Ambiente de Desarrollo”, mientras que las actividades describen un “ambiente de pruebas”; no aclara si los términos se refieren al mismo ambiente. (Fuentes: páginas 2, 5–7)
- La actividad 4 indica que las pruebas no exitosas continúan con la actividad 6, y la actividad 6 remite a la actividad 5 cuando la validación sigue siendo negativa. La secuencia entre notificación al proveedor y actualización de la falla se conserva según la numeración, pero la fuente no detalla quién realiza la corrección del fallo. (Fuente: página 6)
- La descripción automática de imágenes de las páginas 2–8 contiene texto no verificado sobre páginas web y logotipos; no se utiliza para documentar el procedimiento. (Fuentes: páginas 2–8)
