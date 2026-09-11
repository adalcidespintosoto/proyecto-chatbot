"""
Router para Métricas, KPIs y Analítica de Desempeño de UniMon.
Provee endpoints REST para consultar la observabilidad del sistema en tiempo real,
auditar preguntas no resueltas, comparar períodos y generar diagnósticos con IA.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, status, Response, Query, Depends, HTTPException
from pydantic import BaseModel, Field

from app.security import require_admin_auth
from app.services.telemetry_service import (
    get_kpis_summary, 
    reset_telemetry_db,
    get_unresolved_queries_ranking,
    compare_kpi_periods,
    generate_ai_observability_insights,
    draft_procedure_with_ai,
    save_and_index_procedure,
    export_unresolved_queries_csv
)
from app.services.golden_cache_service import clear_golden_cache
from app.services.clustering_service import get_query_clusters as fetch_clusters, export_dpo_dataset, export_dpo_dataset_jsonl

logger = logging.getLogger("unimon.analytics_router")

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analítica & KPIs UniMon"]
)


class DraftProcedureRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Consulta del usuario para la cual se redactará el procedimiento")
    role: Optional[str] = Field(default="general", description="Perfil objetivo: estudiante, profesor, administrativo o general")


class SaveProcedureRequest(BaseModel):
    title: str = Field(..., min_length=4, description="Título del procedimiento institucional")
    content: str = Field(..., min_length=15, description="Contenido completo del procedimiento en formato Markdown")
    role: Optional[str] = Field(default="general", description="Perfil objetivo para asignar a la carpeta correspondiente")


@router.get(
    "/kpis",
    status_code=status.HTTP_200_OK,
    summary="Obtener Resumen Ejecutivo de KPIs de UniMon con Filtros Temporales",
    description="Retorna métricas consolidadas de resolución en Nivel 1, tasa de escalado, latencia promedio, tokens y uso por rol, filtrables por rango de fechas."
)
async def get_kpis(
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (YYYY-MM-DD o 'today')"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (YYYY-MM-DD o 'today')")
) -> Dict[str, Any]:
    """
    Endpoint que retorna el dashboard consolidado de métricas de telemetría.
    """
    kpis = get_kpis_summary(start_date=start_date, end_date=end_date)
    return {
        "status": "success",
        "data": kpis
    }


@router.get(
    "/unresolved-queries",
    status_code=status.HTTP_200_OK,
    summary="Ranking de Preguntas No Resueltas (Knowledge Gaps)",
    description="Identifica las consultas no resueltas por el chatbot (feedback negativo, escalados a GLPI o sin procedimiento en RAG) y las rankea por frecuencia."
)
async def get_unresolved_queries(
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (YYYY-MM-DD o 'today')"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (YYYY-MM-DD o 'today')"),
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad máxima de preguntas a retornar")
) -> Dict[str, Any]:
    """
    Retorna el ranking de preguntas más frecuentes que no tuvieron respuesta satisfactoria.
    """
    return get_unresolved_queries_ranking(start_date=start_date, end_date=end_date, limit=limit)


@router.get(
    "/compare",
    status_code=status.HTTP_200_OK,
    summary="Comparativa de Rendimiento entre Dos Períodos",
    description="Compara las métricas de rendimiento entre el Período 1 y el Período 2 (días o meses), calculando deltas y variaciones porcentuales."
)
async def compare_periods(
    p1_start: Optional[str] = Query(default=None, description="Inicio Período 1 (YYYY-MM-DD)"),
    p1_end: Optional[str] = Query(default=None, description="Fin Período 1 (YYYY-MM-DD)"),
    p2_start: Optional[str] = Query(default=None, description="Inicio Período 2 (YYYY-MM-DD)"),
    p2_end: Optional[str] = Query(default=None, description="Fin Período 2 (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """
    Retorna la comparativa detallada con cálculo de deltas inter-período.
    """
    return compare_kpi_periods(p1_start=p1_start, p1_end=p1_end, p2_start=p2_start, p2_end=p2_end)


@router.get(
    "/ai-insights",
    status_code=status.HTTP_200_OK,
    summary="Diagnóstico y Recomendaciones Estratégicas con IA",
    description="Invoca a la IA local (Ollama) para analizar los KPIs y preguntas no resueltas del período seleccionado y generar un dictamen con sugerencias de mejora."
)
async def get_ai_insights(
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (YYYY-MM-DD o 'today')"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (YYYY-MM-DD o 'today')")
) -> Dict[str, Any]:
    """
    Retorna el análisis y recomendaciones generado por el LLM local sobre la telemetría.
    """
    kpis = get_kpis_summary(start_date=start_date, end_date=end_date)
    top_unresolved = get_unresolved_queries_ranking(start_date=start_date, end_date=end_date, limit=6).get("ranking", [])

    if start_date and end_date:
        period_label = f"del {start_date} al {end_date}"
    elif start_date:
        period_label = f"a partir del {start_date}"
    elif end_date:
        period_label = f"hasta el {end_date}"
    else:
        period_label = "el histórico completo auditado"

    return generate_ai_observability_insights(kpis=kpis, top_unresolved=top_unresolved, period_label=period_label)


@router.post(
    "/draft-procedure",
    status_code=status.HTTP_200_OK,
    summary="Generar Borrador de Procedimiento Institucional con IA",
    description="Redacta automáticamente una propuesta de procedimiento estándar USB en formato Markdown para una consulta no resuelta."
)
async def draft_procedure(
    body: DraftProcedureRequest
) -> Dict[str, Any]:
    """
    Genera un borrador de procedimiento institucional usando el modelo local.
    """
    return draft_procedure_with_ai(unresolved_query=body.query, target_role=body.role or "general")


@router.post(
    "/save-procedure",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_auth)],
    summary="Guardar e Indexar Procedimiento en Base RAG",
    description="Guarda el procedimiento en la carpeta de data/docs y lo re-indexa inmediatamente en ChromaDB."
)
async def save_procedure(
    body: SaveProcedureRequest
) -> Dict[str, Any]:
    """
    Persiste el procedimiento generado y actualiza la colección vectorial de ChromaDB.
    """
    res = save_and_index_procedure(title=body.title, content=body.content, role=body.role or "general")
    return res


@router.get(
    "/export-unresolved-csv",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_auth)],
    summary="Exportar Ranking de Preguntas No Resueltas a CSV",
    description="Descarga el listado de preguntas no resueltas, frecuencias, prioridades y roles en formato CSV compatible con Excel."
)
async def export_unresolved_csv(
    start_date: Optional[str] = Query(default=None, description="Fecha inicio (YYYY-MM-DD o 'today')"),
    end_date: Optional[str] = Query(default=None, description="Fecha fin (YYYY-MM-DD o 'today')")
):
    """
    Exporta el ranking de brechas documentales en CSV.
    """
    csv_content = export_unresolved_queries_csv(start_date=start_date, end_date=end_date)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=preguntas_no_resueltas.csv"
        }
    )


@router.get(
    "/clusters",
    status_code=status.HTTP_200_OK,
    summary="Agrupamiento Semántico de Consultas y Detección de Brechas Documentales",
    description="Retorna el agrupamiento semántico de preguntas, tasas de resolución por tema e identificación de vacíos de conocimiento."
)
async def get_query_clusters(
    n_clusters: Optional[int] = Query(default=None, description="Número explícito de clusters (K-Means)"),
    min_samples: int = Query(default=2, description="Mínimo de muestras por cluster (DBSCAN)"),
    eps: float = Query(default=0.25, description="Radio épsilon de distancia coseno (DBSCAN)")
) -> Dict[str, Any]:
    """
    Retorna el agrupamiento semántico de preguntas y la detección de vacíos documentales.
    """
    return fetch_clusters(n_clusters=n_clusters, min_samples=min_samples, eps=eps)


@router.get(
    "/export-dpo-dataset",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_auth)],
    summary="Exportar Dataset DPO (Direct Preference Optimization)",
    description="Exporta pares de preferencia (prompt, chosen, rejected) en formato JSONL para alineación y fine-tuning de modelos."
)
async def export_dpo(
    format: str = Query(default="jsonl", description="Formato de exportación ('jsonl' o 'json')")
):
    """
    Exporta el dataset de preferencias humanas en formato JSONL o JSON.
    """
    if format.lower() == "json":
        dataset = export_dpo_dataset()
        return {
            "status": "success",
            "total_pairs": len(dataset),
            "dataset": dataset
        }

    jsonl_content = export_dpo_dataset_jsonl()
    return Response(
        content=jsonl_content,
        media_type="application/x-ndjson",
        headers={
            "Content-Disposition": "attachment; filename=dpo_preference_dataset.jsonl"
        }
    )


@router.post(
    "/reset-metrics",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_admin_auth)],
    summary="Limpiar y Reiniciar Métricas de Telemetría",
    description="Elimina el historial de consultas, sesiones y tickets de analytics.db. Opcionalmente purga Golden Cache."
)
async def reset_metrics(
    include_golden_cache: bool = Query(default=False, description="Si es True, purga también la colección de Semantic Golden Cache")
) -> Dict[str, Any]:
    """
    Reinicia las métricas históricas para permitir una evaluación limpia del desempeño actual del chatbot.
    """
    res = reset_telemetry_db()
    if include_golden_cache:
        golden_purged = clear_golden_cache()
        res["golden_cache_purged"] = golden_purged

    return res




