# Wireframes del informe de práctica

Las tres figuras incluidas en la sección 5.4.2 del informe se generan a partir de las vistas implementadas en `app/static/index.html` y `app/static/admin.html`.

- `01_chat_web.svg` representa el estado inicial del chat público: identidad de UniMon, canal rápido, bienvenida, caja de consulta y acción para iniciar otra conversación.
- `02_consulta_tramite.svg` representa una interacción de consulta con fuente RAG y las dos acciones rápidas que contempla el flujo: confirmar resolución o radicar un ticket.
- `03_panel_admin.svg` representa el tablero inicial de métricas del panel administrativo, con sus filtros, indicadores, desglose de tokens y paneles de distribución y documentos.

Los textos de respuesta, fuentes y valores métricos de las figuras son ilustrativos, porque dependen de los datos y de la ejecución. No se representa una pantalla de acceso nueva. Los archivos SVG son las fuentes editables; los PNG insertados en el DOCX se rasterizan a 2200 píxeles de ancho con Sharp. Para regenerar las figuras se ejecuta `generate_wireframes.py` y luego se rasterizan los SVG a PNG. `update_report_wireframes.py` muestra los cambios aplicados a la sección existente y a la fila de historial R71; conserva la estructura de la plantilla y no crea nuevos títulos de índice.
