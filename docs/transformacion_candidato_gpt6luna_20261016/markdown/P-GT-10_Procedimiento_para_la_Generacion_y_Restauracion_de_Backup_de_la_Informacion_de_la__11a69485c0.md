# Procedimiento para la generación y restauración de Backup de la Universidad Simón Bolívar

## Información del documento
- **Fuente original:** `P-GT-10_Procedimiento_para_la_Generacion_y_Restauracion_de_Backup_de_la_Informacion_de_la_Universidad_Simon_Bolivar.pdf` (Fuente: páginas 1–2)
- **Código y versión:** P-GT-10, versión 2, vigente desde 01-06-2023. (Fuente: páginas 2–19)
- **Sistema o módulo:** GLPI, gestores de bases de datos, Veeam Backup, servicios de almacenamiento y herramientas asignadas según la Tabla de Gestión de Backup. (Fuente: páginas 3–4, 8–13, 16–19)
- **Público o permisos mencionados por la fuente:** Personal que administra, gestiona o interactúa con la generación, custodia, verificación y restauración de copias relacionadas con información institucional. La fuente también asigna responsabilidades a usuarios, coordinaciones, técnicos y responsables definidos en la matriz RACIS. (Fuente: páginas 2, 5–7, 14–19)
- **Temas incluidos:** generación y custodia de copias de seguridad; restauración de bases de datos, infraestructura, equipos de cómputo y correo; solicitudes, autorizaciones, registros y retención. (Fuente: páginas 2, 8–19)

## Procedimiento: Generación de Backup para dispositivos finales de usuarios

### Propósito
Crear una copia de la información solicitada por el usuario, entregarla en un medio de almacenamiento y mantener una copia temporal en Soporte Técnico. (Fuente: página 16)

### Requisitos y permisos
- La solicitud puede enviarse al correo `solicitudcomputo@unisimon.edu.co` o realizarse al área de Soporte Técnico. (Fuente: página 16)
- Si se requieren medios de almacenamiento, el usuario los solicita en el almacén. La solicitud de bienes y servicios se identifica como `F-GF-01`. (Fuente: página 16)
- El usuario es responsable de almacenar la información institucional en su espacio de almacenamiento de la cuenta de Microsoft. (Fuente: páginas 7, 9)
- La fuente indica que no se permite alojar en servidores ONPREMISE y CLOUD institucionales backups de equipos de escritorio ni información personal, música, videos, documentos transitorios, documentos confidenciales personales u otra información que no sea relevante para los objetivos del procedimiento. (Fuente: página 9)

### Pasos
1. El usuario remite al correo `solicitudcomputo@unisimon.edu.co` la solicitud de Backup o copia de seguridad de la información, o la realiza al área de Soporte Técnico. (Fuente: página 16)
2. Si requiere medios de almacenamiento, el usuario los solicita en el almacén. (Fuente: página 16)
3. El Coordinador de Soporte Técnico o el Auxiliar Técnico registra la solicitud recibida en el sistema de información y la asigna a un responsable. (Fuente: página 16)
4. Como control, se verifica que la asignación de la tarea se haga en los plazos de atención (tiempos de entrega) y que el usuario cuente con los medios de almacenamiento donde se realizará el Backup. (Fuente: página 16)
5. El Auxiliar Técnico copia la información requerida, la entrega al solicitante en un medio de almacenamiento y mantiene en el área de Soporte Técnico una copia temporal durante **1 mes** como medida de seguridad. (Fuente: página 16)
6. Como controles de la copia, se verifica que el medio incluya la totalidad de los archivos solicitados y se realiza Backup de la totalidad de la información contenida en el disco duro del usuario, según el número total de archivos. (Fuente: página 16)
7. El Auxiliar Técnico registra en el sistema de información el servicio prestado para mantener actualizada la hoja de vida del equipo. (Fuente: página 16)
8. El Auxiliar Técnico cierra el servicio registrando el evento. El usuario evalúa el servicio recibido y lo registra en el sistema de información como constancia de atención a su solicitud. (Fuente: página 16)
9. El Coordinador de Soporte Técnico o el Auxiliar Técnico revisa la orden de trabajo realizada y recibida a satisfacción, verifica su estado y, de ser necesario, reprograma el servicio. (Fuente: página 16)

### Resultado esperado
La copia solicitada queda entregada al usuario en un medio de almacenamiento, se conserva una copia temporal en Soporte Técnico durante 1 mes y el servicio queda registrado en el sistema de información. (Fuente: página 16)

### Errores, límites o excepciones documentadas
- La fuente señala que deben verificarse los plazos de atención y la disponibilidad de los medios de almacenamiento del usuario. No especifica cuáles son esos plazos. (Fuente: página 16)
- La fuente establece que la información de usuarios debe almacenarse en las carpetas asociadas a OneDrive. (Fuente: página 9)

## Procedimiento: Generación periódica o a demanda de Backup

### Propósito
Generar copias según la periodicidad de la Tabla de Gestión de Backup o, cuando corresponda, a demanda. La generación de bases de datos se realiza mediante la configuración del gestor de base de datos conforme a los parámetros de dicha tabla. Para infraestructura de servidores se contemplan copias incrementales o totales y snapshots de máquinas virtuales como medida de contingencia en ambientes propensos a errores. (Fuente: páginas 10, 17)

### Requisitos y permisos
- El procedimiento aplica a los backups que tienen una periodicidad definida en la Tabla de Gestión de Backup. Para los demás, la fuente indica que se realizará un Backup a demanda según esa tabla. (Fuente: página 17)
- El cronograma se diligencia en la Tabla de Gestión de Backup y debe considerar los roles y actividades definidos en la matriz RACIS. (Fuente: página 17)
- La parametrización de copias de seguridad en el motor de base de datos debe contener periodicidad, tipo de Backup, tareas de retención y ubicación. (Fuente: páginas 8–9)
- Los backups deben cifrarse. (Fuente: página 8)
- La fuente describe estos medios y mecanismos:
  - Los backups de servidores virtuales se gestionan con VeeamBackup y se almacenan en SAN (Storage Area Network). (Fuente: página 11)
  - Las configuraciones de dispositivos de infraestructura de red se almacenan en un servidor de almacenamiento mediante FTP o TFTP, según la programación definida. (Fuente: página 11)
  - Los backups de correo se custodian en el centro de cumplimiento de Microsoft y se generan bajo demanda según requerimientos de usuario. (Fuente: página 11)
  - Los backups de bases de datos se gestionan desde el motor de base, según la programación definida, y se almacenan Onpremise en el datacenter físico, en Cloud y en unidad externa. (Fuente: página 11)
  - Los backups de dispositivos finales se establecen en un disco externo propiedad de la Coordinación de Soporte Técnico. La fuente también señala como contingencia que la cuenta institucional de Microsoft funcione como Backup de información de usuarios. (Fuente: página 11)

### Pasos
1. Al inicio del año o cuando se requiera, se actualiza y envía el cronograma de backups conforme a la Tabla de Gestión de Backup y a la aprobación definida en la matriz RACIS. Participan el Coordinador de Analítica y Gestión de Datos, el Ingeniero y Técnico de Redes e Infraestructura Tecnológica y el Técnico de Soporte ERP. (Fuente: página 17)
2. Se diligencia el cronograma en la Tabla de Gestión de Backup, teniendo en cuenta la matriz RACI, que define roles y actividades. (Fuente: página 17)
3. El responsable recibe una notificación desde GLPI para aprobar el cronograma anual de generación de Backup. La aprobación se distribuye así:
   - Coordinador de Analítica y Gestión de Datos: bases de datos.
   - Coordinador de Redes e Infraestructura Tecnológica: infraestructura de red y servidores.
   - Coordinador de Seguridad Informática: bases de datos Kactus y Seven. (Fuente: página 17)
4. Si el cronograma **no** se aprueba, quien detecte la necesidad de ajustes los comunica y registra en la herramienta de Soporte Técnico; se regresa a la actividad 1. Si se aprueba, se continúa con la actividad 3. (Fuente: página 17)
5. Se parametrizan y ejecutan las tareas de generación en las fechas establecidas, conforme a la Tabla de Gestión de Backup y a las herramientas destinadas para su ejecución. Participan el Coordinador de Analítica y Gestión de Datos, el Técnico e Ingeniero de Redes e Infraestructura Tecnológica y el Técnico de Soporte ERP. (Fuente: página 17)
6. El responsable de ejecutar la programación confirma la realización de la tarea de parametrización en las herramientas de gestión definidas en las tablas de Gestión de Backup. La matriz RACIS determina el responsable correspondiente. (Fuente: página 17)
7. Se da cierre a la tarea que se ejecutará según la periodicidad definida y se cierra el ticket. (Fuente: página 17)

### Resultado esperado
La programación de Backup queda aprobada, parametrizada y ejecutada conforme a la periodicidad y herramientas definidas, y la actividad queda cerrada en GLPI. (Fuente: página 17)

### Errores, límites o excepciones documentadas
- Si el cronograma requiere ajustes, se registra la necesidad en la herramienta de Soporte Técnico y se vuelve a la elaboración o modificación del cronograma. (Fuente: página 17)
- La fuente indica que los snapshots de máquinas virtuales se utilizan como medida de contingencia en ambientes propensos a errores para permitir un rollback sin afectar el estado de la máquina en un momento específico. (Fuente: página 10)
- La capacidad ONPREMISE depende de la capacidad de almacenamiento del datacenter físico de la Institución. (Fuente: página 11)
- La vigencia de los datos bajo custodia o almacenamiento externo/interno se establece según las necesidades operativas y de seguridad de la Institución. La tabla citada por el documento se denomina “Tabla de Gestión de Backup”. (Fuente: página 11)

## Procedimiento: Solicitud y restauración de Backup

### Propósito
Restaurar una copia de seguridad ante requerimientos o incidentes. El procedimiento descrito aplica a servicios de bases de datos e infraestructura de servidores. (Fuente: páginas 12, 18)

### Requisitos y permisos
- La restauración debe incluir la justificación de la recuperación de la información y ser autorizada por el líder de proceso o subproceso al que pertenece la información, según la matriz RACIS. (Fuente: página 12)
- Para las solicitudes de restauración, los líderes de proceso deben remitir:
  - Nombre del solicitante.
  - Cargo.
  - Fecha de la información requerida del sistema de información.
  - Backup referenciado con fecha.
  - Tipo de información generada del Backup, según el sistema tecnológico o la información. (Fuente: página 13)
- La fuente indica que dicho Backup solo podrá ser restaurado en ambiente de pruebas en el apartado de requisitos de solicitudes. (Fuente: página 13)
- Se debe validar la matriz RACIS según el activo de Backup para identificar a los solicitantes permitidos. (Fuente: página 13)
- La fuente indica que las solicitudes de restauración por parte del usuario se reciben en Soporte Técnico por correo electrónico en `solicitudcomputo@unisimon.edu.co`, desde donde se escalan para aprobación y gestión. (Fuente: página 13)

### Pasos
1. El líder del Sistema de Información o el Coordinador responsable del Sistema de Información envía por correo electrónico a `solicitudcomputo@unisimon.edu.co` la solicitud de restauración, teniendo en cuenta las consideraciones generales del ítem 5.3.1.6 citado en el documento. (Fuente: página 18)
2. Se clasifica la solicitud como incidente o requerimiento y se referencia el tipo de solicitud en GLPI:
   - **Incidente:** continúa en la actividad 5.
   - **Requerimiento:** continúa en la actividad 2. (Fuente: página 18)
3. Si es un incidente, debe solucionarse en primera instancia mediante la asignación de un responsable que ejecute y garantice que el sistema tecnológico o la información funcione a cabalidad. (Fuente: página 18)
4. Soporte Técnico recibe la solicitud y valida que cumpla los requisitos necesarios. Si no los cumple, continúa en la actividad A; si los cumple, continúa en la actividad 3. (Fuente: página 18)
5. Si faltan datos o requisitos, Soporte Técnico notifica al solicitante cuáles son los datos necesarios para procesar la solicitud. También notifica las aprobaciones correspondientes, según las validaciones y si quien solicita está definido en la matriz RACI. La actividad A indica además notificar al solicitante si la actividad fue realizada a cabalidad. (Fuente: página 18)
6. La coordinación responsable de aprobar, según la matriz RACIS, recibe la notificación y valida el cumplimiento de los lineamientos. Si no da aval, notifica al solicitante según la actividad A; si da aval, continúa en la actividad 4. (Fuente: página 18)
7. El responsable técnico asignado según la matriz RACIS recibe la notificación de restauración. (Fuente: página 19)
8. El responsable técnico selecciona el Backup y ejecuta la restauración. Si no es exitosa, repite esta actividad hasta que sea exitosa y valida los logs desde la herramienta de gestión disponible para el servicio de Backup. Si es exitosa, continúa en la actividad A. (Fuente: página 19)
9. El solicitante recibe y responde a través de la mesa de ayuda en GLPI, según se haya procesado o no la actividad:
   - Si la información no fue procesada, el usuario entrega retroalimentación sobre el caso y, si corresponde, modificaciones o requisitos necesarios para procesar la actividad.
   - Si la solicitud fue realizada, el usuario confirma su realización y el cierre de la actividad. También puede cerrarse el procesamiento por falta de requisitos cuando no se cumplan los permisos autorizados; en ese caso, la fuente indica continuar en la actividad 2. (Fuente: página 19)
10. El responsable técnico documenta el procesamiento en GLPI, cierra el ticket y verifica si el solicitante realizó la evaluación correspondiente. (Fuente: página 19)
11. Una vez recibida y aprobada la solicitud, el responsable asignado realiza la restauración verificando la integridad y disponibilidad de la información y deja un registro en la bitácora de GLPI. (Fuente: página 12)
12. Se utilizan los backups más recientes o los que sean necesarios, dependiendo del registro de dónde se hizo la modificación de datos. (Fuente: página 12)
13. Después de restaurar, el responsable definido en la matriz RACIS verifica que el aplicativo, servidor, dispositivo de red o equipo de cómputo funcione correctamente y que se haya restaurado toda la información necesaria. (Fuente: página 12)
14. Se monitorean las copias de seguridad para validar su integridad al momento de la restauración. La herramienta de gestión de Backup genera un log que valida si la generación fue exitosa; los responsables asignados en la matriz RACIS también validan la ejecución de la tarea. (Fuente: página 13)

### Resultado esperado
La información requerida queda restaurada y se verifica su integridad, disponibilidad y funcionamiento; la gestión se registra en GLPI y se cierra el ticket conforme al procedimiento. (Fuente: páginas 12–13, 19)

### Errores, límites o excepciones documentadas
- En caso de falla de una base de datos de producción, se toma la última copia de seguridad generada que esté en custodia y se restaura en el servidor de Producción. (Fuente: página 13)
- El flujo de restauración distingue incidentes y requerimientos; para incidentes, la fuente indica continuar en la actividad 5, y para requerimientos, en la actividad 2. (Fuente: página 18)
- Si la restauración no es exitosa, se repite la actividad 5 y se validan los logs. (Fuente: página 19)
- La fuente relaciona “restauración solo en ambiente de pruebas” con los requisitos de solicitudes, pero también contempla restauraciones en ambiente productivo y un caso de restauración de una base de datos de producción. (Fuente: páginas 13, 15, 19)

## Procedimiento: Custodia, retención y registro de los Backup

### Propósito
Custodiar copias de seguridad de recursos de infraestructura de red, servidores, bases de datos, correo electrónico y dispositivos de cómputo en almacenamiento ONPREMISE o CLOUD, según las necesidades de acceso y los requerimientos. La administración se asigna a las áreas de Redes e Infraestructura Tecnológica, Soporte Técnico y Analítica y Gestión de Datos. (Fuente: página 10)

### Requisitos y permisos
- Los backups deben clasificarse según su criticidad. Para los sistemas relevantes, los estándares de respaldo deben incluir periodicidad, clasificación de información, periodos de retención, definición de solicitud, tipo de almacenamiento y ubicación de los soportes. (Fuente: página 10)
- Toda generación, custodia o restauración sobre bases de datos, aplicativos, infraestructura de servidores y dispositivos finales debe registrarse en GLPI como bitácora, identificada por número de ticket. (Fuente: página 8)
- La bitácora de GLPI para generación y restauración debe contener identificador del ticket o soporte, tipo de copia, ruta de ubicación, fecha y hora y cuenta del responsable que gestiona el ticket. Las actividades también quedan registradas en los logs de bases de datos, servidores y dispositivos de red e infraestructura tecnológica. (Fuente: página 9)
- Para preservar la confidencialidad, las solicitudes de respaldo y su evolución ante el retiro de un colaborador se remiten únicamente al solicitante —jefe de área, departamento o decanatura—; no se atienden solicitudes realizadas por otras personas. (Fuente: página 8)
- El acceso a los backups se limita a las personas que necesiten conocer la información para cumplir sus funciones, con controles de acceso, autenticación y autorización. (Fuente: página 9)

### Pasos
1. Al planificar los backups, definir periodicidad, tipo de copia, retención y ubicación en la configuración del gestor de base de datos cuando corresponda. (Fuente: páginas 8–9)
2. Gestionar la custodia según el tipo de activo y almacenamiento indicado:
   - Servidores virtuales: VeeamBackup y almacenamiento SAN.
   - Configuraciones de dispositivos de red: servidor de almacenamiento mediante FTP o TFTP, según programación.
   - Correo electrónico: centro de cumplimiento de Microsoft; generación bajo demanda según requerimientos de usuario.
   - Bases de datos: motor de base y almacenamiento Onpremise en datacenter físico, Cloud y unidad externa.
   - Dispositivos finales: disco externo de propiedad de Soporte Técnico; la cuenta institucional de Microsoft se menciona como contingencia para la información de usuarios. (Fuente: página 11)
3. Registrar en GLPI los datos requeridos para la bitácora y conservar los logs de las bases de datos, servidores y dispositivos de red e infraestructura tecnológica. (Fuente: páginas 8–9)
4. Aplicar las medidas de custodia indicadas: seguridad física de los equipos y dispositivos de almacenamiento; acceso restringido; actualización y monitoreo de las medidas de seguridad; y designación de una persona o equipo responsable de gestionar y supervisar la seguridad de los backups. (Fuente: páginas 9–10)
5. Actualizar la Tabla de Gestión de Backup cuando sea necesario y evaluar cambios de programación según la criticidad de la situación o la incorporación de nuevos servicios de servidores, dispositivos de cómputo o bases de datos. (Fuente: página 13)

### Resultado esperado
Los backups quedan custodiados según el activo, la necesidad de acceso y los requerimientos, con registros en GLPI y logs como evidencia de las actividades. (Fuente: páginas 8–11)

### Errores, límites o excepciones documentadas
- Se prohíbe alojar en servidores ONPREMISE y CLOUD institucionales información personal, música, videos, documentos transitorios, documentos confidenciales personales, backups de equipos de escritorio, backups de correo electrónico u otra información no relevante para los objetivos del procedimiento. (Fuente: página 9)
- La información generada por los usuarios debe almacenarse en carpetas asociadas a OneDrive. (Fuente: página 9)
- El almacenamiento puede ser ONPREMISE o CLOUD según necesidad de acceso y requerimiento; para bases de datos también se menciona unidad externa. (Fuente: páginas 10–11)
- El período de custodia se establece en función de necesidades operativas y de seguridad institucional. (Fuente: página 11)

## Datos de la Tabla de Gestión de Backup transcritos en la fuente

La tabla presenta las siguientes filas y valores legibles. Se conservan las grafías tal como aparecen en la transcripción; la estructura de algunas celdas no queda clara. (Fuente: páginas 12–13)

| Tipo de activo | Criticidad | Tipo | Periodicidad | Tiempo de retención | Ubicación | Bitácora | Cronograma | Gestión | Coordinación responsable |
|---|---|---|---|---|---|---|---|---|---|
| Servidores | Alta | Incremental | Diaria | 7 días | ONPREMISE | GLPI | Sí | VEAM BACKUP | Redes e Infraestructura Tecnológica |
| Servidores | Alta | Completa | Semanal | 7 días | ONPREMISE | GLPI | Sí | VEAM BACKUP | Redes e Infraestructura Tecnológica |
| Servidores | Media | Incremental | Diaria | 4 días | ONPREMISE | GLPI | Sí | VEAM BACKUP | Redes e Infraestructura Tecnológica |
| Servidores | Media | Completa | Cada 4 días | 4 días | ONPREMISE | GLPI | Sí | VEAM BACKUP | Redes e Infraestructura Tecnológica |
| Servidores | Baja | Incremental | Semanal | 7 días | ONPREMISE | GLPI | Sí | VEAM BACKUP | Redes e Infraestructura Tecnológica |
| Servidores | Baja | Completa | Mensual | 30 días | ONPREMISE | GLPI | Sí | VEAM BACKUP | Redes e Infraestructura Tecnológica |
| Bases de datos | Alta | Diferencial | Diaria | 90 días | Disco externo; Cloud | GLPI | Sí | Manejador de base de datos | Gestión y Analítica de Datos |
| Bases de datos | Alta | Completa | Mensual | 5 años | No queda legible en la transcripción | GLPI | Sí | Manejador de base de datos | Gestión y Analítica de Datos |
| Bases de datos | Baja | Completa | Diaria | 30 días | Disco externo; Cloud | GLPI | Sí | Manejador de base de datos | Gestión y Analítica de Datos |
| Red | Alta | Completa | Mensual | 30 días | ONPREMISE | GLPI | Sí | TFTP | Redes e Infraestructura |
| Computador | Alta | Completa | A demanda | 30 días | Medio de almacenamiento; disco | GLPI | No | Manual | Soporte Técnico |
| Cuentas Microsoft | Alta | Completa | A demanda | 90 días | Cloud | GLPI | No | Microsoft Exchange | Seguridad Informática |

## Responsabilidades documentadas

- **Director de TI:** asegurar el cumplimiento de políticas y procedimientos para disponibilidad, integridad y confidencialidad de la información respaldada. (Fuente: página 5)
- **Coordinador de Seguridad de la Información:** gestionar la generación de Backup de Kactus y Seven en medios de almacenamiento a partir de la notificación de la mesa de ayuda; garantizar acceso oportuno y pertinente según el rol y evitar accesos no autorizados al servidor de respaldo; solicitar restauración en el servidor de producción por daño de base de datos; aprobar solicitudes de generación, traslados y restauración de backups de Kactus o Seven. (Fuente: página 5)
- **Coordinación de Soporte Técnico:** gestionar solicitudes de dependencias mediante GLPI, verificar que los datos estén completos y escalar al Técnico de Soporte ERP; solicitar a Analítica y Gestión de Datos la restauración de la base de datos de GLPI cuando haya requerimientos o incidentes. (Fuente: página 5)
- **Auxiliar de Soporte Técnico:** realizar backups, custodia y restauración de dispositivos de cómputo y documentar las tareas en GLPI. (Fuente: páginas 5–6)
- **Técnico de Redes e Infraestructura Tecnológica:** validar la generación, custodia y restauración de backups de redes y servidores, y documentar las tareas en GLPI. (Fuente: página 6)
- **Ingeniero de Redes e Infraestructura Tecnológica:** realizar y validar la política de Backup, custodia y restauración de infraestructura de redes y servidores, y documentar las tareas en GLPI. (Fuente: página 6)
- **Técnico Especializado en Soporte ERP:** realizar backups, custodia y restauración de Kactus y Seven según requerimientos o incidentes; programar al inicio del año el cronograma de Backup; solicitar almacenamiento externo a Soporte Técnico cuando sea necesario. (Fuente: página 6)
- **Coordinador de Analítica y Gestión de Datos:** validar la generación de backups en medios de almacenamiento a partir de notificaciones del manejador de base de datos; restaurar bases de datos en ambientes de prueba y productivo según requerimientos o incidentes; programar al inicio del año el cronograma; solicitar almacenamiento externo cuando sea necesario; documentar tareas en GLPI. (Fuente: página 6)
- **Analista de Datos:** realizar backups, custodia y restauración de dispositivos de reconocimiento facial y documentar tareas en GLPI. (Fuente: página 6)
- **Analista de Seguridad Informática:** realizar backups y restauración de cuentas de correo institucionales Microsoft ante requerimientos puntuales que se definan. (Fuente: página 6)
- **Coordinador de Red e Infraestructura Tecnológica:** garantizar el servicio de almacenamiento de servidores de la Institución, prever sus capacidades y validar los backups de infraestructura de red y servidores; documentar tareas en GLPI. (Fuente: páginas 6–7)
- **Usuario:** almacenar información institucional en su espacio de almacenamiento de la cuenta de Microsoft y solicitar creación o restauración de Backup según el tipo de información descrito en el alcance. (Fuente: página 7)

## Definiciones y criterios relacionados

- **Backup:** copia o proceso de copia de seguridad que permite restaurar el original después de una pérdida de datos; las copias garantizan integridad y disponibilidad. **Backup completa:** copia y almacena todos los elementos seleccionados y los marca como respaldados; en general, es el primer Backup al que se somete un sistema. (Fuente: página 2)
- **Backup incremental:** copia archivos creados o alterados desde el último Backup normal o incremental y los marca como respaldados; para restaurar se requiere el último Backup normal y todos los conjuntos incrementales. (Fuente: página 3)
- **Restaurar:** cargar en una base de datos uno o varios objetos desde una copia de seguridad; la restauración sobrescribe información de la base de datos con la información de la copia. (Fuente: páginas 3–4)
- **Snapshot:** imagen instantánea de una máquina virtual almacenada en un estado determinado; puede servir para revertir a ese estado sin crear varias máquinas virtuales. (Fuente: página 4)
- **Bitácora:** almacén de datos donde se pueden ver registros de eventos en un sistema de información o en GLPI. **LOG:** referencia al archivo o herramienta donde se registra la actividad de respaldo. (Fuente: páginas 3–4)
- **Frecuencia de copia de respaldo:** periodo definido para realizar una copia; puede ser diaria, semanal, mensual o según se defina. (Fuente: página 3)
- **Disponibilidad:** propiedad de que la información sea accesible y utilizable por solicitud de la Universidad Simón Bolívar. **Plan de Contingencia:** procedimientos alternativos para permitir el funcionamiento normal o la continuidad de operaciones pese a accidentes internos o externos. (Fuente: página 3)
- **Clasificación de información:** evaluación de activos según nivel de accesibilidad o confidencialidad. **Confidencial:** acceso restringido a usuarios definidos en la matriz RACIS. **Interna:** información institucional accesible para empleados. **Pública:** material institucional sin restricción de difusión. (Fuente: página 5)
- **KACTUS – HCM:** sistema modular para gestionar recursos humanos. **SEVEN:** sistema modular para gestionar procesos administrativos, financieros y contables. (Fuente: página 3)
- **FTP y TFTP:** protocolos descritos para transferir archivos entre dispositivos en red; TFTP se caracteriza como simple y liviano. **NAS:** tecnología de almacenamiento conectado en red. **Storage Server:** servidor para almacenar, acceder, asegurar y administrar datos digitales. **Veeam Backup:** software de Backup, recuperación, replicación de Backup y recuperación de desastres. (Fuente: páginas 4, 11)
- **Matriz RACIS:** define los roles como Responsable (R), Autoriza (A), Consultado (C), Informado (I) y Solicitante (S). Responsable realiza la tarea; Autoriza aprueba la solicitud; Consultado valida su pertinencia; Informado recibe comunicaciones sobre la tarea; Solicitante inicia el evento. (Fuente: página 14)

## Otros datos del documento
- El alcance incluye computadores, bases de datos de sistemas tercerizados e IN HOUSE definidos en el documento, infraestructura de servidores, correo y almacenamiento institucional de Microsoft, e infraestructura de red LAN y WLAN. El proceso inicia con la programación del Backup y termina con su verificación y custodia, para restaurarlo según el requerimiento. (Fuente: página 2)
- La fuente considera que la información de sistemas críticos en producción debe respaldarse con cierta frecuencia y que deben existir soluciones e infraestructura de respaldo disponibles incluso después de un desastre o falla de dispositivo. (Fuente: página 8)
- La rotulación de los archivos de Backup se define según la aplicación que los genere, conforme a la Tabla de Gestión de Backup. (Fuente: página 9)
- Entre los documentos aplicables se mencionan el Instructivo para generación y restauración; Ley 1273 de 5 de enero de 2009; Norma Técnica Colombiana NTC/ISO 27002:2015 y sus anexos indicados; Acuerdo 001 de 2020; Ley 1581 de 2012; Marco de Arquitectura Empresarial MINTIC; P-GT-01 Procedimiento mantenimiento equipos de cómputo; y los documentos establecidos en la matriz F-SI-17-GC. (Fuente: páginas 7–8)
- En la matriz RACIS transcrita se listan actividades y roles para infraestructura de servidores, bases de datos, Kactus y Seven, infraestructura de red, equipos de cómputo y correo electrónico. Algunas actividades aparecen con numeración repetida o faltante y los valores de las celdas no quedan inequívocamente asociados a todos los encabezados en el texto extraído. (Fuente: páginas 15–16)
- Los registros enumerados por el documento incluyen Solicitud de Back up (de usuario), Back up de usuario, herramienta asignada según Tabla de Gestión de Back up, logs, correo electrónico con solicitud de restauración de Backup y aplicativo GLPI. (Fuente: página 19)

## Palabras y formas de búsqueda
*Paráfrasis editoriales para mejorar la búsqueda; no son afirmaciones adicionales del documento.*

- crear, programar o generar un Backup
- copia de seguridad de computador o PC
- respaldar información de usuario
- restaurar una copia de seguridad
- recuperar una base de datos
- Backup de Kactus o Seven
- respaldo de servidores o máquinas virtuales
- snapshot y rollback
- respaldo de red, LAN o WLAN
- respaldo de correo Microsoft
- solicitud de Backup por correo o GLPI
- custodia, retención y bitácora de backups

## Puntos por validar
- El encabezado de la Tabla de Gestión de Backup y la asociación de algunos valores con columnas o filas no se recuperan con certeza. En particular, la fila de bases de datos Alta/Completa/Mensual/5 años no muestra ubicación legible en la transcripción. (Fuente: página 12)
- En la tabla aparece “VEAM BACKUP”, mientras el texto del documento define “Veeam Backup”; confirmar la grafía que debe usarse en la tabla. (Fuente: páginas 4, 12)
- El encabezado del procedimiento de restauración cita el ítem 5.3.1.6 para las consideraciones generales, pero ese contenido no aparece en la transcripción. (Fuente: página 18)
- La fuente afirma que el Backup solicitado en los requisitos de restauración solo podrá restaurarse en ambiente de pruebas, pero también incluye restauraciones en ambiente productivo y la restauración de una base de datos de producción. Confirmar cómo se aplica la restricción de ambiente. (Fuente: páginas 13, 15, 19)
- La numeración de los apartados de restauración y de las actividades de la matriz no es consistente en el texto extraído; la matriz repite algunos números y omite otros. (Fuente: páginas 12–15)
- El flujo de restauración combina referencias a actividades 2, 3, 4, 5 y A; además, la actividad A incluye notificaciones de requisitos, aprobaciones y resultado, sin que el texto extraído aclare por completo la secuencia entre ellas. (Fuente: páginas 18–19)
- El diagrama de flujo del anexo no es legible de forma fiable en la transcripción: la descripción automática menciona repetidamente “Iniciar sesión” y “Verificar datos de acceso”, pero no permite confirmar su relación con el procedimiento de Backup. (Fuente: páginas 20–22)
- La fuente usa variantes en nombres de roles y coordinaciones, entre ellas “Coordinador de Seguridad de la Información” y “Coordinador de Seguridad Informática”, así como “Coordinador de Analítica y Gestión de Datos” y “Coordinador de Gestión y Analítica de Datos”. Confirmar las denominaciones oficiales. (Fuente: páginas 5–7, 15, 17)
- En la sección de correo electrónico, la frase sobre generación de Backup a petición de usuarios queda incompleta después de “en caso de que se requiera alguna migración de una”. (Fuente: página 10)
- La descripción automática de la imagen de la portada no está verificada; no se usa como evidencia de ubicación, sistema ni procedimiento. (Fuente: página 1)
