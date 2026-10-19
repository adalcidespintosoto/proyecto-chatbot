# Auditoría de seguridad de UniMon — 13 de octubre de 2026

## Alcance y modelo de amenaza

Se revisaron la API FastAPI, el webhook de Meta, el panel y el chat web, el RAG, la ingesta de documentos, las integraciones con GLPI y proveedores LLM, los scripts de arranque, los datos versionados y las dependencias declaradas. Los activos sensibles son las credenciales, las consultas y respuestas de usuarios, los teléfonos de WhatsApp, los tickets y los documentos institucionales. Las entradas no confiables principales son mensajes del chat, eventos de webhook, archivos cargados y texto de documentos recuperados.

Esta revisión es estática. Se comprobó la sintaxis de los archivos Python y JavaScript modificados. Se auditó el inventario de 145 paquetes instalados con `pip-audit`; no se hicieron pruebas de penetración ni pruebas funcionales, por lo que no equivale a una certificación de seguridad.

## Hallazgos corregidos

| Prioridad | Hallazgo | Corrección |
| --- | --- | --- |
| Crítica | El webhook aceptaba mensajes sin firma si faltaba el App Secret o la cabecera de firma. | Ahora rechaza solicitudes sin secreto, sin firma o con HMAC SHA-256 inválido; valida el cuerpo original antes del JSON y limita cada evento a 1 MiB. |
| Crítica | La contraseña del administrador estaba escrita en `admin.html` y `.env.example`; el token de verificación también estaba publicado. | Se retiraron los valores del frontend y del ejemplo. La contraseña y el token locales se rotaron en `.env` sin imprimirlos. Las credenciales antiguas se rechazan. |
| Alta | Varias rutas de analítica, incluidas consultas de preguntas y borradores con IA, eran públicas. | Todo `/api/analytics` exige autenticación administrativa. Las operaciones de escritura verifican el origen de la solicitud. |
| Alta | `/static/admin.html` permitía descargar la interfaz administrativa sin pasar por `/admin`. | La ruta estática lo bloquea; el panel se sirve por la ruta autenticada. |
| Alta | Consultas, respuestas, nombres de documentos y resultados de IA se insertaban como HTML en el panel. | Se codifican los valores externos, se quitaron manejadores `onclick` construidos con texto externo y se usa `textContent` donde corresponde. |
| Alta | Las cargas podían copiar archivos sin límite efectivo previo y confiaban en la extensión. | Escritura incremental acotada, validación de nombre, firma PDF o estructura Office, límite de contenido descomprimido y reemplazo atómico. |
| Alta | La sesión pública por defecto se compartía y el chat podía usar el identificador `wa_` de WhatsApp. | IDs web aleatorios, rechazo de `default_session` y del espacio `wa_`, y límite de longitud de entrada. |
| Alta | La base de telemetría, los índices Chroma y sus copias estaban versionados. | Se retiraron del índice Git sin borrar los archivos locales y se agregaron reglas a `.gitignore`. También se retiraron un PDF y sus metadatos temporales de carga. |
| Media | Los logs registraban mensajes, preguntas, teléfonos, correos y cuerpos de error externos. | Se redujo el registro a estado, tamaños y códigos HTTP en los recorridos principales. |
| Media | Los fragmentos recuperados se interpolaban en el mensaje de sistema del LLM. | Las reglas se mantienen en el mensaje de sistema y los fragmentos se pasan como material de referencia de menor confianza. |
| Media | Las sesiones inactivas conservaban historial y objetos en memoria. | La limpieza periódica purga ambos tras el TTL. |
| Media | `run.ps1` exponía el servidor en toda la red y siempre usaba recarga. | Ahora escucha en localhost; la recarga se activa con `-DevReload`. |
| Media | El CORS global permitía credenciales y todos los métodos y cabeceras. | Se limitó a GET/POST, `Content-Type` y sin credenciales entre orígenes. |
| Media | El limitador de tasa agrupaba a todos los usuarios detrás del túnel local. | Usa `CF-Connecting-IP` solo si el salto inmediato es localhost y la cabecera contiene una IP válida. |

## Acciones operativas necesarias

1. **Reiniciar UniMon** para que la aplicación lea la contraseña y el token nuevos de `.env`. Volver a autenticar el panel con `ADMIN_PASSWORD` de ese archivo. No copiarlo a chats, tickets ni capturas.
2. **Configurar `WHATSAPP_APP_SECRET`** con el App Secret real de Meta y actualizar en Meta el nuevo `WHATSAPP_VERIFY_TOKEN` de `.env`. Hasta entonces, los eventos entrantes de WhatsApp se rechazan intencionalmente.
3. **Revisar el repositorio remoto y su historial.** `git rm --cached` impide nuevos commits de bases e índices, pero no borra versiones ya publicadas. Si el repositorio fue compartido, tratar la contraseña antigua y los datos anteriores como expuestos; planear limpieza de historial coordinada y rotación de cualquier otra credencial afectada.
4. **Proteger los resultados de evaluación.** Los 158 reportes históricos se retiraron del árbol de trabajo y se guardaron en un respaldo local fuera del repositorio; los nuevos resultados bajo `reports/` quedan ignorados por Git porque pueden contener preguntas, respuestas y contexto. Esta limpieza no borra esos archivos de commits anteriores: si el repositorio remoto es público, solo una limpieza coordinada del historial puede retirarlos de versiones ya publicadas.
5. **Exigir HTTPS en el despliegue** del panel HTTP Basic, restringir quién puede llegar a `/admin` y realizar copias de seguridad cifradas y con acceso limitado.

## Riesgos pendientes

- **Autenticación de usuarios y abuso de GLPI:** `/api/chat` sigue siendo público y puede iniciar el flujo de tickets. La limitación de tasa ayuda, pero no demuestra la identidad institucional del solicitante. Para producción se recomienda autenticación institucional o verificación antes de radicar tickets.
- **Sesiones web:** el identificador aleatorio es difícil de adivinar, pero sigue siendo un token portador controlado por el cliente. Si se filtra, otra persona puede continuar esa sesión. Una solución más fuerte requiere sesión firmada o autenticación institucional.
- **Documentos maliciosos:** la firma y los límites reducen el riesgo, pero no sustituyen antivirus, aislamiento del parser ni desarme de PDF/Office. El servidor o proxy también debe limitar el tamaño total del cuerpo multipart antes de que FastAPI lo procese.
- **Rate limit distribuido:** SlowAPI conserva contadores en memoria; varios workers no comparten el límite y una sola IP de salida institucional puede agrupar usuarios. Se requiere almacén central y métricas para despliegues con varios procesos.
- **Datos en reposo:** la telemetría almacena texto de consultas y respuestas. Se debe definir retención, acceso, respaldo y eliminación conforme a la política institucional. El índice vectorial y los archivos locales también requieren permisos de sistema.
- **Dependencias:** `requirements.txt` usa principalmente mínimos (`>=`) y no hay lockfile. El entorno `.venv` actual apunta a un Python inexistente. El escaneo aislado de 145 distribuciones reportó 17 entradas en dos paquetes, equivalentes a 10 identificadores únicos: ChromaDB 1.5.9 (cuatro IDs) y pip 25.0.1 (seis IDs). Las advertencias de ChromaDB describen endpoints del servidor HTTP y sus controles de autorización; este proyecto usa `PersistentClient` local y no expone ese servidor, por lo que no se confirmó una ruta remota explotable aquí. No se encontró versión reparada para esos avisos al momento del escaneo; mantener Chroma inaccesible desde la red y seguir los parches del proveedor. Reconstruir `.venv`, actualizar pip al menos a 26.2 y bloquear y reauditar las dependencias antes de publicar. El JSON del escaneo está en `data/scratch/security_audit.json` (ignorado por Git).
- **RAG:** separar fragmentos de las reglas reduce la posibilidad de inyección, pero un documento malicioso puede seguir influenciando la respuesta. La ingesta requiere aprobación humana y observación de respuestas sospechosas.
- **CSP:** se añadieron directivas defensivas de objeto, base, marco y formularios. El panel usa scripts inline; para una política estricta de scripts deben extraerse a archivos estáticos y eliminarse los manejadores inline restantes.

Referencias de criterio: [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [OWASP Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) y [aviso de ChromaDB en la base de GitHub](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c).
