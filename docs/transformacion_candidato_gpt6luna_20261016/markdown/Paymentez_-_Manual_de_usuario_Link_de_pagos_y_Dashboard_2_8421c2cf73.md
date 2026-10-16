# Manual de usuario del Administrador de transacciones y Generador de Links de pago de Paymentez

## Información del documento
- **Fuente original:** *Paymentez - Manual de usuario Link de pagos y Dashboard (2).pdf*
- **Sistema o módulo:** Administrador de transacciones y Generador Link de pagos; el documento también usa el nombre «Linktopay».
- **Público o permisos mencionados por la fuente:** Usuarios de la plataforma; para solicitar un nuevo acceso, la fuente menciona miembros del equipo o un nuevo cliente.
- **Temas incluidos:** inicio de sesión y recuperación de contraseña, resumen, transacciones, generación y envío de links de pago, búsqueda, reportes e integración. El índice también incluye «Compartir Link de Pago» y «Resumen de gráficas/ Transacciones». (Fuente: página 2)

## Procedimiento: Inicio de sesión y recuperación de contraseña

### Requisitos y permisos
- El correo electrónico debe estar registrado previamente en el Administrador. (Fuente: página 4)
- Para solicitar un nuevo acceso a la plataforma para miembros del equipo o un nuevo cliente, la fuente indica enviar una solicitud al correo `soporte.integracionesdav@paymentez.com` con nombre completo, correo asociado, cargo, zona y nombre de jefe autorizador. (Fuente: página 3)

### Pasos
1. En la pantalla de login, haga clic en «Olvidé mi contraseña». (Fuente: página 3)
2. Ingrese el correo electrónico vinculado a la plataforma. (Fuente: página 4)
3. El sistema mostrará una confirmación indicando que se envió un mensaje al correo. (Fuente: página 4)
4. Revise la bandeja de entrada o la bandeja de spam, abra el mensaje y haga clic en «Recuperar contraseña». (Fuente: página 4)
5. Será redirigido a la pantalla para crear una nueva contraseña. (Fuente: página 4)

### Resultado esperado
- Se envía un mensaje al correo registrado y, al seguir el enlace indicado, se abre la pantalla de creación de una nueva contraseña. (Fuente: páginas 3–4)

## Procedimiento: Consultar el resumen de actividad

### Propósito
Al ingresar al Administrador, la primera vista es el resumen de actividad de las transacciones en tiempo real. El menú lateral izquierdo puede contraerse y suprimirse temporalmente por el usuario. (Fuente: página 5)

### Pasos
1. Para controlar la visualización, puede realizar búsquedas específicas por Comercios, Appcodes, Métodos de pago, Fecha, Zona horaria y/o Moneda. (Fuente: página 5)
2. Al seleccionar una fecha o un periodo de fechas, seleccione la zona horaria correspondiente a la consulta para obtener la información correcta. (Fuente: página 5)
3. La fuente indica seleccionar la palabra «INTEGRALES» y seleccionar los códigos asignados a la zona, tanto Client como Server. (Fuente: página 5)

### Errores, límites o excepciones documentadas
- La fuente no explica con más detalle el contexto ni la relación entre «INTEGRALES», los códigos Client y Server y la consulta del resumen. (Fuente: página 5; véase «Puntos por validar»).

## Procedimiento: Consultar transacciones

### Propósito
La sección «Transacciones» muestra en tiempo real el detalle de las transacciones una a una. (Fuente: página 6)

### Pasos
1. Seleccione el App Code asociado al Comercio. (Fuente: página 6)
2. Puede seleccionar las columnas que espera ver en la lista de transacciones consultada. (Fuente: página 6)
3. Puede buscar una transacción por cédula o correo del cliente. También puede controlar la visualización con búsquedas por Métodos de pago, Fecha, Zona horaria y/o Moneda. (Fuente: página 6)
4. Al seleccionar una fecha o un periodo de fechas, seleccione la zona horaria correspondiente a la consulta para obtener la información correcta. (Fuente: página 6)

## Procedimiento: Revisar el historial y las gráficas del resumen

### Propósito
La pantalla «Inicio / Resumen» muestra seis visualizaciones de datos. (Fuente: páginas 10–11)

### Resultado esperado
Las visualizaciones descritas son:
1. Volumen transaccional por estado: Aprobada, Rechazada y Pendiente. (Fuente: página 10)
2. Volumen transaccional por cada hora del día, incluyendo aprobadas y rechazadas. La visualización de «Horario de actividad» muestra valores promedio dentro del periodo de fechas seleccionado. (Fuente: página 10)
3. Valor en dinero ($) correspondiente a los estados Aprobada, Rechazada y Pendiente. (Fuente: página 10)
4. Total de transacciones rechazadas, dividido en el porcentaje correspondiente a cada tipo de rechazo. (Fuente: página 11)
5. Volumen transaccional procesado por cada carrier habilitado dentro de la pasarela. (Fuente: página 11)
6. Conversión porcentual correspondiente a los estados finales Aprobada y Rechazada. (Fuente: página 11)

### Historial de transacciones
La sección «Resumen | Transacciones» presenta una tabla transaccional con estados y parámetros. Permite seleccionar el número de filas y las columnas a visualizar, acceder al detalle de cada transacción y validar logs. La imagen se identifica como «Imagen de referencia». (Fuente: página 12)

## Procedimiento: Generar un link de pago

### Propósito
La sección «Linktopay» permite generar links de pago con parámetros predefinidos por el usuario. La fuente describe un formulario con los parámetros necesarios para generar el link. (Fuente: página 7)

### Requisitos y permisos
- El App Code debe ser «SERVER» en todos los casos. (Fuente: página 7)

### Pasos
1. Diligencie todo el formulario de generación del link de pago. La fuente identifica el campo del valor total de la compra como obligatorio y también marca otros campos como «Campo obligatorio», sin especificar sus nombres en el texto extraído. (Fuente: página 7)
2. La fuente indica que una opción «Aplica para pagos PSE». No especifica en el texto extraído el nombre del campo o control al que corresponde. (Fuente: página 7)
3. Una vez diligenciado todo el formulario, se enviará un correo electrónico al cliente con la instrucción para el pago. (Fuente: páginas 8–9)

### Resultado esperado
- El link de pago que recibe el cliente puede presentarse con el logo de la compañía y los colores definidos de marca. La fuente identifica las modalidades «PAGO CON TARJETA DE CRÉDITO» y «PAGO CON PSE». (Fuente: página 9)

### Errores, límites o excepciones documentadas
- La fuente no especifica en el texto extraído los nombres de todos los campos obligatorios del formulario. (Fuente: página 7; véase «Puntos por validar»).

## Procedimiento: Compartir un link de pago

### Propósito
Compartir el link generado con el cliente. (Fuente: página 8)

### Pasos
1. Después de generar el link, puede copiarlo y compartirlo por diferentes medios, redes sociales o SMS. (Fuente: página 8)
2. El mensaje del chat es personalizable por la Empresa. (Fuente: página 8)

## Procedimiento: Buscar transacciones específicas

### Pasos
1. Seleccione un filtro. (Fuente: página 13)
2. Ingrese un valor válido para el filtro. Puede ingresar varios valores separados por comas (`,`). (Fuente: página 13)
3. Agregue los valores a la búsqueda. (Fuente: página 13)
4. Haga clic en «Buscar». (Fuente: página 13)

## Procedimiento: Generar reportes

### Pasos
1. Haga clic en «Exportar». (Fuente: página 14)
2. Ingrese el nombre del reporte. Si desea ver todas las columnas correspondientes al detalle de las transacciones, marque la casilla. (Fuente: página 14)
3. Si el reporte contiene un volumen de datos muy grande (`>3.000 líneas`), quedará en estado «En proceso». (Fuente: página 14)
4. Haga clic en «Ir a Reportes» para ver el estado del reporte creado. (Fuente: página 14)

## Procedimiento: Integrar el link de pagos

### Propósito
Para efectos de conciliación en línea, el Comercio puede realizar una integración a su sistema, ERP o software. Si no se requiere conciliación en línea, el link de pago no requiere integración para su uso. (Fuente: página 15)

### Requisitos y permisos
- La fuente indica que el acompañamiento en integración del Link to Pay incluye 10 horas (Convenio Davivienda). (Fuente: página 15)

### Referencias incluidas en la fuente
- `https://paymentez.github.io/api-doc/#payment-methods-linktopay` (Fuente: página 15)
- `https://paymentez.github.io/api-doc/#webhook` (Fuente: página 15)

## Palabras y formas de búsqueda
Paráfrasis editoriales para mejorar la búsqueda; no son afirmaciones adicionales del documento: acceso a la plataforma, recuperar clave, restablecer contraseña, consultar el dashboard, ver transacciones, generar link de pago, compartir enlace de pago, buscar una transacción, exportar transacciones, crear reporte, integración para conciliación.

## Puntos por validar
- La página 2 presenta un índice y páginas de referencia, pero el número de página impreso y la página física del archivo no coinciden necesariamente. El índice enumera: «Inicio / Resumen» (2), «Transacciones» (4), «Link de Pago» (5), «Compartir Link de Pago» (6), «Resumen de gráficas/ Transacciones» (7), «Búsqueda de transacciones» (8–9–10), «Generación de reportes» (11), «Login» (12) y «Recuperación de contraseña» (3). (Fuente: página 2)
- En la página 3 se indica que, después de ingresar el correo corporativo y hacer clic en «Continuar», se revise el buzón —incluidos los correos no deseados— para asignar la clave y luego se genere la nueva contraseña. La relación exacta entre esas indicaciones y los pasos de recuperación de la página 4 no queda completamente detallada. (Fuente: página 3)
- Las descripciones automáticas de imágenes de las páginas 3 y 4 presentan requisitos de contraseña distintos: una menciona al menos 6 caracteres y que no se permiten caracteres especiales ni números; otra menciona al menos 6 caracteres y al menos una letra mayúscula, un número y un símbolo especial. Son descripciones automáticas no verificadas y parecen contradecirse; confirmar en el documento visual original. (Fuente: páginas 3–4)
- La página 5 menciona seleccionar «INTEGRALES» y los códigos asignados a la zona, tanto Client como Server, pero no detalla el procedimiento ni aclara a qué consulta o selección concreta pertenecen esas instrucciones. (Fuente: página 5)
- La página 7 identifica campos obligatorios y una opción aplicable a pagos PSE, pero el texto extraído no permite determinar todos los nombres de los campos ni el nombre del control asociado a PSE. Confirmar en el documento visual original. (Fuente: página 7)
- En la página 8, las descripciones automáticas de imágenes muestran un link de ejemplo y controles como «Copiar», «Cerrar» y «Aceptar», pero no son texto operativo confirmado. No se reproduce el link de ejemplo. Confirmar si esos controles forman parte del procedimiento real en el documento visual original. (Fuente: página 8)
- La página 16 solo identifica «Canales de Soporte» y «Pasarela de pagos»; no contiene texto extraído con datos de contacto o instrucciones. (Fuente: página 16)
