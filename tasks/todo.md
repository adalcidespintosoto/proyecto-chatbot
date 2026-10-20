# Tareas: reutilizar la carga normal por dependencia

- [x] Agregar por dependencia las acciones **Analizar Ambigüedad y Redundancia** y **Subir Directo**.
- [x] Reutilizar sanitización, validación, fragmentación e indexación Markdown existentes.
- [x] Aislar staging, auditoría y resolución al `bot_id`; el Chroma global y Golden Cache quedan fuera.
- [x] Agregar `.docx` a los selectores, la validación de API y la extracción, conservando PDF/PPTX.
- [x] Usar GPT-6 Luna primero y Ollama como último recurso; registrar el proveedor/modelo utilizado.
- [x] Comparar el Markdown con el original antes de indexar; bloquear conversiones dudosas.
- [x] Aplicar el límite configurado y documentar las rutas `docs/`, `sanitized_docs/markdown/` y `chroma_db/` por instancia.
- [ ] Hacer prueba funcional de ambas opciones, Word/PDF/PPTX, fallos e aislamiento entre dos instancias; comparar conteos de Golden Cache y el RAG global antes/después.

Detalles, criterios de aceptación y verificaciones: [plan.md](plan.md).
