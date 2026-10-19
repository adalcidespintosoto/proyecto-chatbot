# Resultados locales de evaluación

Los scripts de `scripts/` guardan aquí los resultados JSON, Markdown y CSV. Pueden incluir preguntas, respuestas del modelo, fragmentos recuperados y nombres de fuentes, por lo que esta carpeta se excluye de Git.

Los resultados se generan de nuevo al ejecutar las evaluaciones. Por ejemplo:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_rag_retrieval.py --output reports\mi_evaluacion.json
.\.venv\Scripts\python.exe scripts\load_test_quality_50.py --concurrency 50 --output reports\mi_carga.json
```

Los informes históricos se conservan en un respaldo local fuera del repositorio.

Las utilidades históricas `review_partial_answers_multievidence.py` y `retest_partial_answers.py` necesitan sus informes de entrada antiguos. Si se van a volver a usar, restaura esos JSON desde el respaldo en esta carpeta o indica un informe compatible con `--input`; el mensaje de error explica este requisito.
