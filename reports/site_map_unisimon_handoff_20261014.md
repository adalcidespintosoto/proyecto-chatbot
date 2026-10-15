# Continuación pendiente: mapa público de unisimon.edu.co

Estado de continuación: 15/10/2026.

## Alcance y hallazgos

- URL inicial: `https://unisimon.edu.co/`.
- Se acordó revisar páginas públicas del host principal y registrar subdominios institucionales enlazados, sin ingresar a portales con autenticación.
- La portada muestra secciones como Aspirantes, La Universidad, Oferta Académica, Investigación, Noticias, Portales y Servicios.
- `robots.txt`, `sitemap.xml`, `sitemap_index.xml`, `sitemap-index.xml`, `sitemaps.xml`, `wp-sitemap.xml`, `/sitemap/` y `/mapa-del-sitio` respondieron 404.
- Primera pasada terminada con 1.057 páginas HTML inventariadas y 124 URL fallidas (112 respuestas 400 y 12 respuestas 404). Alcanzó el límite de 1.200 URL vistas, así que no demuestra que el inventario esté completo. Se encontró que varios enlaces mal formados y nombres de enlaces con espacios consumían el límite.
- Segunda pasada: se añadió filtro para enlaces mal formados, se aumentó el límite a 3.000 y se empezó de nuevo. Se interrumpió a las 78 páginas visitadas (448 en cola, 2 fallidas) cuando el usuario pidió pausar. El script escribe los CSV al terminar; esta pasada interrumpida no reemplazó los CSV de la primera.
- Tercera pasada: el 15/10 se volvió a iniciar con el rastreador actual. Se detuvo intencionalmente alrededor de 180 páginas procesadas porque la cola creció a 876 URL; el patrón sugiere rutas repetidas/relativas que podrían inflar el mapa con páginas artificiales. Como el script guarda sus CSV solo al completar, no se conservó este intento parcial y no se modificaron los CSV preliminares.
- Se creó `reports/propuesta_mapa_web_unisimon_validacion_20261015.md` para que el usuario valide el formato y el alcance antes de integrar contenido al chatbot.
- El 15/10 se revisaron las rutas aportadas por el usuario. La pasada del 14/10 sí contiene `/portales`, `/aspirantes/admisionespregrado` y `/aspirantes/apoyofinanciero`, pero no contiene `/portales/estudiantes` ni el PDF enlazado de Reglamento Estudiantil. La portada usa `href="javascript:portalestudiantes('…')"` para la ruta estudiantil; el crawler actual solo guarda `href` HTTP/HTTPS. El PDF es filtrado por extensión y no queda en el CSV; HTML/parser tampoco renderiza el login que se carga por `loginExterno.js`.
- El PDF indicado corresponde a “Reglamento Estudiantil”, Acuerdo de Sala General No. 40 de 2019, actualizado en enero de 2022; 84 páginas PDF, con 79 páginas numeradas de contenido. Clasificarlo como normativa académica, no como procedimiento TI.
- El HTML adjunto `C:\Users\adalcides.pintos\Downloads\Universidad Simón Bolivar - USB.html` se usó como snapshot de referencia; muestra enlaces PDF y rutas dinámicas JavaScript. No se alteró ni se usó para autenticación.
- Se actualizó `scratch/crawl_unisimon.py` para detectar URLs dentro de `href="javascript:..."`, atributos `data-id`/`data-url`, redirecciones internas, archivos enlazados, subdominios institucionales y contenido duplicado. Guarda un checkpoint por lote y no envía formularios ni sigue rutas de autenticación.
- Recorrido actualizado del 15/10 pausado con checkpoint: 105 elementos procesados, 96 páginas distintas guardadas, 514 URL en cola, 9 fallas y 132 recursos enlazados. Ya detectó `/portales/estudiantes` por su origen JavaScript y el PDF solicitado en el manifiesto; falta verificar el estado HTTP del PDF al completar el recorrido. No se ha generado el CSV final de esta pasada.

## Archivos disponibles

- `reports/unisimon_public_site_map_20261014.csv`: inventario preliminar de páginas, títulos, encabezados, profundidad y página de origen.
- `reports/unisimon_public_site_map_failures_20261014.csv`: respuestas 400/404 de la primera pasada.
- `scratch/crawl_unisimon.py`: crawler de solo lectura con extracción estática de rutas JavaScript y atributos `data-*`, manifiesto de documentos, checkpoint recuperable, deduplicación por hash y límite de 3.000 páginas.
- `reports/unisimon_20261015_checkpoint.json`: checkpoint para continuar el rastreo actualizado.

## Próximos pasos

1. Obtener validación del usuario sobre la propuesta antes de cualquier integración al chatbot/RAG.
2. Reanudar el rastreo desde el checkpoint y revisar el PDF y otros recursos enlazados.
3. Verificar mediante navegador solo las pantallas dinámicas seleccionadas, como `/portales/estudiantes`; detenerse antes de enviar credenciales o formularios.
4. Analizar URL fallidas: distinguir enlaces rotos, contenido mal formado y bloqueos temporales.
5. Generar el mapa jerárquico, inventario de páginas y manifiesto de archivos; revisar subdominios institucionales aparte, sin ingresar a autenticación.
6. Identificar páginas que aporten a soporte TI y crear guías visuales con rutas y capturas de flujos públicos verificados. Mantener los otros contenidos institucionales en el mapa general con metadatos temáticos.

## Comando para reanudar

Desde la raíz del proyecto, en PowerShell:

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe scratch\crawl_unisimon.py --max-pages 3000
```

El comando retoma el checkpoint automáticamente. Usar `--fresh` solo para descartar estado y reiniciar desde cero. El recorrido es público y de solo lectura. No se autenticaron cuentas ni se enviaron formularios.
