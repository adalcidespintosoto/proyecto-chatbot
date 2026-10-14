# Prueba piloto de efectividad de UniMon — 14/10/2026

## Método

- 20 preguntas distintas de soporte TI escritas previamente por el usuario, repartidas en cuatro temas.
- Se ejecutó `RouterLogic.procesar_mensaje` con el LLM configurado y una sesión nueva por pregunta, dos sesiones a la vez.
- Se usaron el índice RAG y el Golden Cache tal como están en producción. No se envió feedback, no se promovieron respuestas a Golden Cache y no se registraron estas llamadas en la telemetría del panel.
- Se revisó cada respuesta contra la pregunta y, donde fue decisivo, contra los PDF originales. «Correcta» exige una orientación suficiente, segura y respaldada; «parcial» ayuda pero omite algo necesario; «incorrecta» desvía, inventa un dato importante o niega información que sí está documentada.
- Archivo con preguntas, respuestas, fuentes y tiempos: `reports/support_effectiveness_20261014.json`.

## Resultado

| Tema | Correctas | Parciales | Incorrectas | Total | Exactitud estricta |
|---|---:|---:|---:|---:|---:|
| Cuentas y acceso | 1 | 1 | 3 | 5 | 20 % |
| Conexión y equipos | 5 | 1 | 0 | 6 | 83,3 % |
| Aplicaciones y reuniones | 5 | 0 | 0 | 5 | 100 % |
| Seguridad y atención | 3 | 0 | 1 | 4 | 75 % |
| **Total** | **14** | **2** | **4** | **20** | **70 %** |

Latencia de la lógica conversacional: p50 **7,5 s**, p95 **22,7 s**, máximo **27,4 s**. Las 20 llamadas finalizaron sin excepción. Estas medidas no incluyen el transporte HTTP ni la latencia de una red externa.

## Revisión por pregunta

| # | Caso | Veredicto | Motivo |
|---:|---|---|---|
| 1 | No entra al correo | Incorrecta | Supone que es estudiante y reproduce un correo institucional mal formado (`trabajodesdecasa@unisim onbolivar.edu.co`). El PDF de activación contiene ese texto roto; no se debe transmitir como dirección válida. |
| 2 | Teams no deja iniciar sesión | Correcta | Separa rutas por perfil y ofrece comprobaciones reversibles. |
| 3 | Olvidó contraseña institucional | Parcial | Da pasos para Portal Estudiantes y otra ruta para Kactus/Seven, pero no identifica dónde abrir «Olvidé mi Usuario / Contraseña» ni cubre claramente otras cuentas institucionales. |
| 4 | Usuario bloqueado | Incorrecta | Envía al portal de administrativos sin conocer el perfil y no da una ruta verificable de desbloqueo. |
| 5 | Cambió contraseña y sigue sin entrar | Incorrecta | Supone Portal Estudiantes y da `trabajodesdecasa@unisimbolivar.edu.co`, dirección alterada que no está verificada en el documento. |
| 6 | Wi-Fi universitario | Correcta | Propone diagnóstico general seguro y aclara que no hay parámetros institucionales de red verificados. Las fuentes recuperadas son mayormente irrelevantes. |
| 7 | Conectado sin navegación | Correcta | Distingue falla del sitio, del equipo y de la red con pruebas sencillas. La sugerencia de acercarse al router aporta poco en campus. |
| 8 | Punto de red de oficina | Parcial | Indica Mesa de Ayuda y los canales de soporte, pero sugiere buscar una opción de incidente/red que los fragmentos no confirman. |
| 9 | Computador no enciende | Correcta | Incluye comprobaciones básicas, límite de seguridad y escalado autorizado. |
| 10 | Mouse y teclado dañados | Correcta | Indica solicitar revisión por Mesa de Servicio y distingue la regla para software/dotación. |
| 11 | Equipo lento | Correcta | Prioriza comprobaciones seguras y datos para reportar si persiste. |
| 12 | Teams no abre | Correcta | Ofrece reinicio de aplicación/equipo y ruta alternativa de acceso según perfil. |
| 13 | No escuchan en Teams | Correcta | Revisa silencio, permisos, dispositivo elegido y comparación con otra aplicación. |
| 14 | Micrófono o cámara de Teams | Correcta | Da comprobaciones reversibles de controles, permisos y dispositivos. |
| 15 | Solicitar instalación | Correcta | Aplica la autorización del jefe de dependencia y la Mesa de Servicio según P-GT-01. |
| 16 | Ayuda con VPN | Correcta | Remite a Dirección de TI y explica los datos de la solicitud de acceso remoto según P-GT-08. |
| 17 | Correo sospechoso | Correcta | Evita abrir/retransmitir el enlace y orienta a reportar la incidencia. |
| 18 | Posible virus | Correcta | Evita acciones administrativas peligrosas y escala a soporte/seguridad. |
| 19 | Recuperar archivo de backup | Incorrecta | Dice que no existe procedimiento, aunque P-GT-10 sí documenta la solicitud por `solicitudcomputo@unisimon.edu.co` (página 18) y la autorización para restaurar (página 12). La fuente no llegó a la respuesta. |
| 20 | Revisión presencial | Correcta | Indica radicar ticket en Mesa de Ayuda, describir la falla y solicitar revisión en sitio; también muestra los canales oficiales y la opción de generar reporte. |

## Prioridades derivadas de esta muestra

1. **Cuentas y acceso:** no elegir Portal Estudiantes o Administrativos cuando la pregunta no informa el perfil. Preguntar el servicio o dar rutas condicionales verificadas. Bloquear correos extraídos con espacios, dominios alterados u OCR dudoso antes de enviarlos al LLM o al usuario.
2. **Restauración de backup:** investigar por qué P-GT-10 no estuvo entre las fuentes finales para la pregunta 19. Agregar esa consulta a la evaluación de candidatos → reranking → contexto final; corregir la recuperación de forma general, no con un interceptor por nombre de archivo.
3. **Relevancia de fuentes:** Wi-Fi, navegación y lentitud recibieron varios documentos ajenos al problema. Mantener las comprobaciones generales útiles, pero reducir el contexto distractor y no presentarlo como respaldo institucional de esas pruebas.
4. **Ruta de radicación:** cuando la persona pregunta cómo reportar un daño, indicar un canal confirmado y evitar nombres de botones o categorías no documentados.

## Alcance del porcentaje

El **70 %** es una lectura estricta de estas 20 preguntas de primera línea; no estima por sí solo la exactitud de todos los documentos ni demuestra una mejora frente a pruebas anteriores, que usaron otras preguntas y criterios. El conjunto es pequeño y el Golden Cache estaba activo. Para decidir si se alcanzó 85–90 %, se necesita una muestra adicional de preguntas reales no usadas en ajustes, con respuestas esperadas y páginas verificadas antes de ejecutar la prueba, repartida por servicio, rol y casos sin respuesta documental. Conviene comparar la misma muestra con Golden Cache activo e inactivo y publicar ambos resultados.
