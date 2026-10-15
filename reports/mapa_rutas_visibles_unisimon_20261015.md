# Mapa superficial de rutas visibles de Unisimón

**Fecha del rastreo:** 15 de octubre de 2026  
**Alcance:** navegación pública visible desde la portada, hasta dos enlaces de profundidad. Se detuvo el rastreo amplio de subdominios y se dejó el checkpoint sin cola pendiente.  
**Uso:** inventario de referencia y navegación pública, con texto y mapas visuales verificados para las páginas seleccionadas.

## Mapa para estudiantes, aspirantes y visitantes

```text
Inicio — https://unisimon.edu.co/
├── Portales — https://unisimon.edu.co/portales
│   ├── Portal Estudiantes — https://unisimon.edu.co/portales/estudiantes
│   │   └── La pantalla de credenciales se completa con JavaScript; no se ingresaron credenciales.
│   ├── Portales Administrativos — https://unisimon.edu.co/portales/administrativos
│   └── Reglamento Estudiantil — PDF enlazado desde la página principal
├── Aspirantes — https://unisimon.edu.co/aspirantes
│   ├── Admisiones pregrado — https://unisimon.edu.co/aspirantes/admisionespregrado
│   ├── Apoyo financiero — https://unisimon.edu.co/aspirantes/apoyofinanciero
│   ├── Inscripciones — https://unisimon.edu.co/aspirantes/inscripciones
│   ├── Listado de admitidos — https://unisimon.edu.co/aspirantes/admitidos
│   ├── Calendario académico — https://unisimon.edu.co/aspirantes/calendario
│   └── Matrículas y valores — https://unisimon.edu.co/aspirantes/matriculas
├── Pregrados — https://unisimon.edu.co/pregrados
├── Posgrados — https://unisimon.edu.co/posgrados
└── Atención y servicios
    ├── Centro de Ayuda — https://unisimon.edu.co/servicios/centrodeayuda
    ├── Contacto — https://unisimon.edu.co/servicios/contacto
    └── Bienestar Universitario — https://unisimon.edu.co/servicios/bienestaruniversitario
```

La ruta de Portal Estudiantes termina en una pantalla de acceso. Se verificó visualmente que la sección **Credenciales** muestra los campos **Usuario** y **Contraseña**, el botón **Acceder** y el enlace **Olvidé mi Usuario / Contraseña**. No se ingresaron credenciales, no se envió el formulario y no se consultó información privada.

## Estado de incorporación al chatbot

- Se indexaron de forma aditiva las **16 páginas públicas seleccionadas** en `data/public_web_sources.json`; la colección Chroma quedó en **7.408 chunks**. No se borraron los documentos ni se reconstruyó la colección.
- Se incorporaron mapas visuales verificados de **Inicio** y **Portal Estudiante**. Incluyen regiones, menú, campos, acciones y enlaces; no contienen valores escritos en campos.
- Las preguntas que consultan dónde está un campo, botón o ruta de navegación realizan una búsqueda adicional limitada al tipo `public_web_ui`. Los mapas elegidos se priorizan antes del límite por cantidad de chunks.
- El recortador de contexto por estimación de tokens quedó retirado. Se mantienen topes de cantidad: 8 chunks para consultas directas y 24 para procedimientos/contexto extendido.
- Prueba real con `gpt-6-luna` el 15/10/2026: la consulta de navegación incluyó los mapas de Inicio y Portal Estudiante en el contexto final; la consulta de credenciales incluyó el mapa de Portal Estudiante y respondió con Usuario, Contraseña y Acceder.
- Informe de la corrida: `site_ui_map_live_final_20261015.json`.

## Recursos y comprobaciones

- Se registraron **515 páginas HTML** públicas a profundidad 0–2: 1 portada, 94 rutas a un enlace y 420 rutas a dos enlaces. El diagrama anterior es una selección funcional para navegación cotidiana, no una lista de todas las páginas indexadas por el sitio.
- Se registraron **337 archivos enlazados** dentro de ese alcance. La comprobación HTTP obtuvo 323 respuestas 200, 11 respuestas 404 y 3 redirecciones 302.
- El PDF de Reglamento Estudiantil compartido para revisión respondió **200** con tipo `application/pdf`: [abrir PDF](https://barranquillas.unisimon.edu.co/web/index.php/showimagen/showpdf/centrodocumentos/20220215165955_0.pdf). Es un reglamento académico, no una guía de soporte TI.
- Se conservaron **487 enlaces externos** como referencias; el rastreador no visitó dominios de terceros.
- Se detectaron **1.176 rutas de autenticación o límites de acceso** y no se visitaron.
- Quedaron **104 fallos HTTP o de navegación** en páginas del alcance: 80 límites de redirección, 15 respuestas 404, 7 respuestas 400 y 2 respuestas 403. Un límite de redirección puede ser un ciclo o una cadena no resuelta; no prueba por sí solo que la página haya sido retirada.

## Archivos del inventario

- `unisimon_20261015_pages.csv`: título, URL, profundidad, origen, respuesta HTTP y datos de página pública.
- `unisimon_20261015_resources.csv`: PDF y otros archivos enlazados, con página de origen y estado HTTP.
- `unisimon_20261015_external_links.csv`: destinos de otros dominios registrados, sin rastrearlos.
- `unisimon_20261015_boundaries.csv`: accesos autenticados y rutas excluidas.
- `unisimon_20261015_failures.csv`: fallos y rutas que requieren revalidación.
- `unisimon_20261015_edges.csv`: relaciones entre enlaces y páginas; es un archivo técnico grande, no pensado para lectura manual.
- `unisimon_20261015_checkpoint.json`: checkpoint reducido, con la cola vacía.
- `unisimon_20261015_checkpoint_broad_879.json`: copia del checkpoint amplio previo al ajuste de alcance, conservada para trazabilidad.

## Límites de esta revisión

El rastreador leyó HTML estático y referencias explícitas a enlaces. No ejecutó JavaScript; los menús desplegables, pantallas posteriores al acceso y contenido cargado dinámicamente pueden no estar representados. Por eso los mapas visuales se añadieron solo para las dos páginas abiertas y confirmadas visualmente. Las otras páginas seleccionadas aportan su texto estático y URL; requieren inspección visual antes de crear mapas equivalentes.
