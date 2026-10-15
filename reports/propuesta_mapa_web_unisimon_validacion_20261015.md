# Propuesta para validar: mapa web de Unisimón

**Estado:** borrador para revisión. Este archivo describe el contenido y el comportamiento propuestos; todavía no se integra al RAG ni cambia el chatbot.

## Qué se prepararía

1. **Mapa jerárquico navegable** de las páginas públicas encontradas en `unisimon.edu.co`, agrupadas por sección y enlazadas a la página real.
2. **Inventario CSV completo** con título, URL canónica, sección, profundidad, enlace de origen, estado HTTP y fecha de verificación. Los subdominios institucionales se listarían aparte, sin entrar a sistemas autenticados. Los PDF y otros archivos descargables enlazados se registrarían en un manifiesto separado, con URL y página de origen.
3. **Guías visuales de navegación** solo para las páginas o trámites que sean útiles para soporte TI. Cada guía tendría capturas y pasos verificables para reconocer botones, menús y pantallas.
4. **Índice para el chatbot**, preparado como fuente documental con texto extraído, título, URL, fecha y sección. El índice será evidencia para recuperar fragmentos pertinentes; no se enviaría el sitio completo al LLM en cada consulta. Los archivos descargables se procesarían solo después de comprobar que son públicos y pertinentes para soporte TI.

## Ejemplo de cómo se vería el mapa

```text
Inicio — https://unisimon.edu.co/
├── Aspirantes — https://unisimon.edu.co/aspirantes
│   ├── Admisiones — https://unisimon.edu.co/aspirantes/admisiones
│   ├── Admisiones pregrado — https://unisimon.edu.co/aspirantes/admisionespregrado
│   ├── Matrículas y valores — https://unisimon.edu.co/aspirantes/matriculas
│   └── Calendario académico — https://unisimon.edu.co/aspirantes/calendario
├── Portales — enlace y destinos enlazados desde la página
├── Servicios — páginas públicas de servicios y atención
└── Otras secciones — La Universidad, Oferta Académica, Investigación,
    Noticias, Bienestar Universitario y demás páginas encontradas
```

Las rutas de arriba son ejemplos de la primera pasada del 14/10/2026. Se volverán a comprobar antes de marcarse como verificadas; algunas páginas del primer rastreo pueden ser enlaces duplicados o rutas defectuosas.

## Revisión de las rutas que compartiste (15/10/2026)

```text
Inicio
├── Portales
│   ├── Portal Estudiantes
│   │   └── Pantalla de credenciales (se carga con JavaScript)
│   └── Reglamento Estudiantil [PDF alojado en barranquillas.unisimon.edu.co]
└── Aspirantes
    ├── Admisiones Pregrado
    └── Apoyo Financiero y Becas
```

- `https://unisimon.edu.co/portales`: la portada pública muestra entradas de Portal Estudiantes, Aula Extendida, Crédito Empresarial e ICETEX, Portal Laboral, Reglamento Estudiantil, entre otras. Hay destinos en subdominios institucionales y otros dominios externos.
- `https://unisimon.edu.co/portales/estudiantes`: responde 200 y presenta “Portal Estudiante” / “Credenciales”. El HTML inicial carga `loginExterno.js` desde `barranquillas.unisimon.edu.co`, que inserta los controles de inicio de sesión. La revisión no envió credenciales ni pulsó “Acceder”.
- `https://unisimon.edu.co/aspirantes/admisionespregrado`: contiene un flujo general dividido en inscripción, admisión/selección y matrícula; enlaza a Gestión de Ingreso y a información financiera. Es contenido de admisiones, no un procedimiento TI.
- `https://unisimon.edu.co/aspirantes/apoyofinanciero`: contiene opciones de apoyo financiero y becas, ICETEX y enlaces a trámites/portales. Es contenido financiero/académico, distinto de soporte TI.
- El PDF de `barranquillas.unisimon.edu.co` enlazado como Reglamento Estudiantil es un documento oficial de 84 páginas (79 páginas numeradas de contenido más preliminares), Acuerdo de Sala General No. 40 de 2019, actualizado en enero de 2022. Debe estar en el inventario documental con título, fecha, páginas y origen. No lo clasificaría como una guía de soporte TI.

### Qué falta en el rastreador actual

El inventario preliminar del 14/10 sí tiene `/portales`, `/aspirantes/admisionespregrado` y `/aspirantes/apoyofinanciero`, pero **no** tiene `/portales/estudiantes` ni el PDF que compartiste. Con el recolector ajustado, el checkpoint parcial del 15/10 ya encontró `/portales/estudiantes` y añadió el PDF al manifiesto pendiente de verificación HTTP; todavía no hay CSV final porque el recorrido completo no ha terminado. La causa de las omisiones del rastreador anterior está identificada en `scratch/crawl_unisimon.py`:

- Solo guarda `href` de etiquetas `<a>` y solo acepta enlaces HTTP/HTTPS. Por eso descarta `href="javascript:portalestudiantes('…/portales/estudiantes')"`, aunque sea el destino real del control visible.
- Filtra las extensiones PDF/Office y exige `text/html`; los documentos se pierden del inventario en vez de ir a un manifiesto de archivos.
- No renderiza JavaScript. Puede detectar que una página referencia un script, pero no documenta los controles que el script inserta en pantalla.
- La página de Portales también expone enlaces como `data-id`; deben extraerse como destinos, pero nunca ejecutar el JavaScript para descubrirlos.

La corrección general ahora implementada en el recolector lee de forma estática `href`, `data-id`/`data-url` y destinos explícitos de enlaces JavaScript con una regla de extracción acotada; registra archivos por separado y guarda checkpoints para reanudar. La captura visual de controles dinámicos sigue pendiente y se hará solo en las pantallas elegidas. Cada destino conserva la página de origen y el tipo de acceso. No se hace clic en inicios de sesión ni se envían formularios.

Las cuatro páginas HTML y el PDF están revisados como evidencia de alcance. La lista y la captura de controles se consideran verificadas únicamente en la fecha indicada; el mapa completo aún no se ha regenerado con un rastreador corregido.

## Muestra de una guía visual

La primera guía candidata sería **“Encontrar un portal institucional desde la portada”**:

```text
1. Abrir https://unisimon.edu.co/.
2. Ubicar “Portales” en la navegación visible.
3. Abrir la página pública de Portales.
4. Mostrar los enlaces encontrados y marcar cuáles llevan a autenticación.
5. Detener la guía en la pantalla de inicio de sesión; no ingresar credenciales.
```

Los pasos 2–5 quedan como una estructura de ejemplo hasta que se verifiquen en la página y en las capturas. No asumiré que un sistema enlazado es un portal público ni afirmaré rutas internas que no se puedan observar.

## Plantilla para una guía visual de página

```text
Nombre de la página:
Para qué sirve / a quién le aplica:
Enlace de entrada:
Ruta desde la página principal:
Qué elementos visibles debe buscar:
Pasos observados en pantalla:
Resultado esperado:
¿Requiere inicio de sesión?:
Qué no se pudo verificar:
Capturas y fecha de revisión:
Fuente oficial:
```

Las capturas y los pasos se documentan solo cuando se observa el flujo real. Si el destino requiere credenciales, se indica dónde termina la guía pública y no se intenta iniciar sesión.

## Cómo lo usaría el chatbot

- Buscaría pasajes relevantes en las páginas indexadas junto con los documentos actuales, sin filtrar la búsqueda por rol.
- Podría combinar páginas distintas si juntas contestan la consulta, conservando título, URL y fecha como procedencia.
- Respondería con la ruta de navegación observada y enlaces oficiales. Si el mapa no contiene los pasos dentro de una aplicación, lo diría claramente y ofrecería el canal de soporte adecuado.
- Una consulta no dispararía un rastreo indiscriminado del sitio. Si se decide agregar consulta en vivo, se limitaría a una lista permitida de dominios y a páginas públicas pertinentes, con límites de tiempo y tamaño.
- El contenido de una página web sería evidencia documental, no una instrucción que pueda modificar las reglas del asistente ni autorizar al usuario a realizar acciones restringidas.

## Fuera de esta aprobación

Hasta que se valide este enfoque, no se modifica el prompt, el código del chatbot, el índice vectorial, el Golden Cache ni las reglas de acceso. Después de revisar el borrador se podría integrar el índice en una etapa separada y comprobarlo con preguntas de navegación reales.

## Calidad y actualización

- Distinguir páginas únicas de rutas duplicadas, páginas de error y enlaces rotos.
- No afirmar que el rastreo cubrió todo el dominio si llega al límite de páginas.
- Mantener registro de URL, respuesta HTTP, fecha de rastreo y relación de navegación.
- Revalidar enlaces antes de utilizarlos como instrucciones vigentes.
