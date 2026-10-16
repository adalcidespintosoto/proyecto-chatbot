# Procedimiento de Aseguramiento de Servicios en la Red

## Información del documento
- **Fuente original:** `P-GT-08_Procedimiento_Aseguramiento_de_Servicios_en_la_Red_.pdf` (páginas 1–6).
- **Sistema o módulo:** Servicios de la red; plataforma de red corporativa. (Fuentes: páginas 1–2)
- **Público o permisos mencionados por la fuente:** Dirección de TI, líderes de proceso, jefes de oficina, Secretario General, administradores de sistemas de información, coordinaciones y usuarios. (Fuentes: páginas 3–5)
- **Temas incluidos:** Alcance y definiciones; gestión de accesos privilegiados y credenciales; revisión de derechos de acceso; uso de información de autenticación; instalación, aseguramiento y puesta en marcha de servicios de red; bibliografía. (Fuentes: páginas 2–6)

## Procedimiento: Aseguramiento de servicios en la red

### Propósito
Describe cómo la Universidad Simón Bolívar protege la información publicada por los servicios y la que se transmite y transporta a través de la plataforma de red corporativa. Indica controles de seguridad para acceder a las redes cableada e inalámbrica, considera la privacidad de los activos de información y el uso de registros (logs) para facilitar la trazabilidad y el seguimiento de acciones sospechosas. (Fuente: página 2)

### Requisitos y permisos
- El procedimiento aplica a los sistemas de información y servicios informáticos que almacenen o transmitan datos de la Universidad Simón Bolívar. (Fuente: página 2)
- La fuente define:
  - **Cuenta de usuario:** identificador del usuario para ingresar a un sistema de información, terminal o computador personal.
  - **Clave de acceso:** combinación de letras, símbolos o números que se digitan para obtener acceso a un sistema de información, terminal o computador personal. La fuente indica que, si estas llaves se utilizan de forma personal, secreta e intransferible, garantizan una adecuada utilización, resguardo y confiabilidad de la información.
  - **Servicios de la plataforma tecnológica:** servicios controlados por componentes de Tecnologías de la Información y Comunicaciones y administrados desde el centro de cómputo de la Entidad.
  - **Rol:** funciones que cada usuario debe cumplir dentro del sistema.
  - **Usuario:** persona que utiliza un sistema o servicio informático. (Fuente: página 2)

### Pasos

#### Gestión de derechos de acceso privilegiado
1. La gestión en la Dirección de TI contempla tres tipos de accesos privilegiados: Infraestructura, Aplicaciones y Bases de Datos. (Fuente: página 3)
2. La asignación de accesos privilegiados a la plataforma tecnológica en la Dirección de TI se realiza a través del servicio de Directorio Activo de Microsoft. El director de la Dirección de TI autoriza los derechos de acceso a los servicios de red Microsoft para los usuarios de su área y de otras dependencias de la Universidad Simón Bolívar, de acuerdo con la solicitud de los líderes de los procesos. (Fuente: página 3)
3. La solicitud de usuarios con derechos de acceso privilegiado de áreas distintas a la Dirección de TI debe hacerse mediante la mesa de ayuda/servicios (GLPI), correo electrónico o memorando al Jefe de Dirección de TI. Debe enviarla un Líder de proceso, Jefe de Oficina o Secretario General. (Fuente: página 3)
4. Los sistemas de información deben garantizar la administración de usuarios con perfiles especiales de consulta para auditoría de los sistemas de información. (Fuente: página 3)
5. Si se necesita acceso remoto a la infraestructura de la Universidad Simón Bolívar, debe hacerse solamente a través del servicio VPN o conexiones SSH. Se debe solicitar el apoyo de la Dirección de TI, indicando la necesidad del acceso y su duración. (Fuente: página 3)

#### Gestión de claves de autenticación
1. La solicitud de claves para la autenticación confidencial de usuarios se gestiona a través de la herramienta de gestión de TI o de la mesa de ayuda/servicios (GLPI). (Fuente: página 3)
2. La transferencia de información confidencial de autenticación a los usuarios finales debe hacerse de manera segura. (Fuente: página 3)
3. El Directorio Activo solicita al usuario el cambio de contraseña en el primer inicio de sesión. (Fuente: página 3)

#### Revisión de los derechos de acceso de usuarios
1. Los administradores de cada sistema de información deben depurar anualmente los usuarios de los sistemas, de acuerdo con las indicaciones de la Coordinación de Seguridad de la Información de la Universidad Simón Bolívar. (Fuente: página 4)
2. La Coordinación debe comparar y depurar el listado correspondiente con el listado de funcionarios activos generado por el área de Talento Humano. (Fuente: página 4)

#### Uso de información de autenticación confidencial
1. Los usuarios de los sistemas de información no deben facilitar sus usuarios o claves de acceso a terceros. (Fuente: página 4)

#### Instalación, aseguramiento y puesta en marcha de un servicio de red
1. **Instalar el servicio de red.** Durante la instalación, no se deben habilitar las credenciales por defecto. Las credenciales utilizadas deben ser complejas para minimizar el riesgo de *password cracking* por fuerza bruta. Se deben reemplazar la configuración de rutas, el direccionamiento, los *banners* del servicio y otra configuración por defecto.  
   **Responsable:** Coordinación de Redes e Infraestructura Tecnológica. (Fuente: página 4)
2. **Asegurar el servicio de red.** Al instalar un nuevo servicio de red, sea DHCP, DNS, HTTP, FTP o BASES DE DATOS, se debe realizar un *hardening* y buscar configurar las opciones de seguridad disponibles en el servicio, como doble factor de autenticación y cifrado, entre otros.  
   **Responsables:** Coordinación de Redes e Infraestructura Tecnológica / Coordinación de Seguridad informática. (Fuente: página 4)
3. **Deshabilitar el acceso remoto.** Si el acceso remoto no está justificado para una persona, debe deshabilitarse cualquier opción de acceso remoto a la máquina, ya sea por escritorio remoto o aplicaciones de terceros como TeamViewer o AnyDesk, entre otras. Si es necesario, se deben configurar los logs y hacer que el acceso se deshabilite automáticamente después del tiempo necesario para realizar el trabajo remoto. Se deben utilizar protocolos seguros de conexión como SSH, nunca TELNET.  
   **Responsable:** Coordinación de Redes e Infraestructura Tecnológica. (Fuente: página 4)
4. **Desactivar servicios innecesarios.** Toda instalación nueva requiere depurar los servicios y opciones configurados por defecto, porque muchas de estas opciones son innecesarias y mantenerlas activas conlleva un mayor nivel de exposición. Se deben inspeccionar los servicios innecesarios. Como ejemplo, en una máquina con Windows se debe escribir `services.msc` en Ejecutar, depurar los servicios iniciados y detener los innecesarios.  
   **Responsable:** Coordinación de Seguridad informática. (Fuente: página 5)
5. **Habilitar firewall y antimalware.** Ninguna computadora, y especialmente ningún servidor, debe ponerse en operación antes de instalar el producto antimalware y firewall de la Universidad Simón Bolívar. Para esto, se debe seguir el procedimiento de protección de código malicioso que acompaña las políticas de seguridad de la información.  
   **Responsable:** Coordinación de Seguridad informática. (Fuente: página 5)
6. **Actualizar el sistema operativo y las aplicaciones.** Se debe conectar a internet y descargar los últimos parches del sistema operativo y de las aplicaciones instaladas para minimizar el número de vulnerabilidades.  
   **Responsables:** Coordinación de Redes e Infraestructura Tecnológica / Coordinación de Seguridad informática. (Fuente: página 5)
7. **Realizar análisis de vulnerabilidades.** Realizar test y pruebas de vulnerabilidades que permitan detectar de forma preventiva posibles debilidades.  
   **Responsable:** Coordinación de Seguridad informática. (Fuente: página 5)
8. **Socializar hallazgos.** Se deben socializar los hallazgos con la Coordinación de Redes e Infraestructura Tecnológica para tomar acciones que minimicen la probabilidad de que los fallos sean explotados.  
   **Responsable:** Coordinación de Seguridad informática. (Fuente: página 5)
9. **Realizar pruebas operativas y *hardening*.** Estas pruebas están destinadas a comprobar el correcto funcionamiento del servicio.  
   **Responsable:** Coordinación de Redes e Infraestructura Tecnológica. (Fuente: página 5)
10. **Poner en marcha el servicio.** El coordinador de seguridad de la información da el visto bueno para la puesta en marcha, y el coordinador de infraestructura habilita el servicio para el uso de los usuarios correspondientes.  
    **Responsable indicado en la tabla:** Coordinación de Redes e Infraestructura Tecnológica. (Fuente: página 5)

### Resultado esperado
- Para la puesta en marcha, el servicio cuenta con el visto bueno del coordinador de seguridad de la información y el coordinador de infraestructura lo habilita para los usuarios correspondientes. (Fuente: página 5)
- Las pruebas operativas están destinadas a comprobar el correcto funcionamiento del servicio. (Fuente: página 5)

### Errores, límites o excepciones documentadas
- El acceso remoto a la infraestructura de la Universidad Simón Bolívar debe realizarse solamente por VPN o conexiones SSH, con apoyo solicitado a la Dirección de TI e indicando la necesidad y duración del acceso. (Fuente: página 3)
- Si el acceso remoto a una máquina no está justificado para una persona, se debe deshabilitar cualquier opción de acceso remoto. Si es necesario, se configuran logs y se deshabilita automáticamente después del tiempo requerido para el trabajo remoto; se utilizan protocolos seguros como SSH, nunca TELNET. (Fuente: página 4)
- No se deben habilitar credenciales por defecto durante la instalación; las credenciales utilizadas deben ser complejas. (Fuente: página 4)
- Una computadora, en especial un servidor, no debe ponerse en operación antes de instalar el producto antimalware y firewall de la Universidad Simón Bolívar y seguir el procedimiento de protección de código malicioso indicado. (Fuente: página 5)

## Bibliografía
- ISO/IEC 27002, *Information Technology. Security Techniques. Code of practice for information security controls*. (Fuente: página 6)
- NTC ISO-22301:2012, *Continuidad de Negocio. Sistemas de gestión de Continuidad de Negocio. Requisitos*. (Fuente: página 6)
- NTC ISO-IEC 27001:2013, *Tecnología de la Información. Técnicas de Seguridad. Sistemas de Gestión de la Seguridad de la Información Requisitos*. (Fuente: página 6)
- *Guía: Controles de Seguridad y Privacidad de la Información*, MINTIC. (Fuente: página 6)

## Palabras y formas de búsqueda
Paráfrasis editoriales para mejorar la búsqueda; no son afirmaciones adicionales del documento:
- asegurar servicios de red
- proteger la red corporativa
- pedir acceso privilegiado
- solicitar usuarios con permisos especiales
- solicitar claves de usuario
- revisar o depurar usuarios de sistemas
- asegurar conexiones remotas
- instalar y endurecer servicios de red
- desactivar servicios innecesarios
- habilitar firewall y antimalware
- actualizar sistemas y aplicaciones
- análisis de vulnerabilidades y puesta en marcha

## Puntos por validar
- En la página 3, dos apartados consecutivos tienen el mismo encabezado, “Gestión de derechos de acceso privilegiado”; el segundo trata sobre la solicitud y transferencia de claves de autenticación y el cambio de contraseña. No se modifica el encabezado original por no estar clara la numeración o denominación prevista.
- En la actividad 10 de la página 5, la descripción asigna acciones al coordinador de seguridad de la información y al coordinador de infraestructura, pero la columna “Responsable” indica únicamente “Coordinación de Redes e Infraestructura Tecnológica”. Confirmar si la diferencia es intencional.
- La página 5 termina con el encabezado “6. BIBLIOGRAFÍA:” y la bibliografía aparece en la página 6; se conserva el contenido listado en esa página.
- La página 1 identifica el documento como “P-GT-08 Procedimiento de Aseguramiento de Servicios en la Red” y señala “Barranquilla y Cúcuta - Colombia”. No se atribuyen instrucciones operativas adicionales a la descripción automática de imagen, que está marcada como no verificada.
