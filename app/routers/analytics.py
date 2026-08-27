"""
Router para Métricas, KPIs y Analítica de Desempeño de UniMon.
Provee endpoints REST para consultar la observabilidad del sistema en tiempo real.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, status, Response, Query
from pydantic import BaseModel, Field

from app.services.telemetry_service import get_kpis_summary
from app.services.clustering_service import get_query_clusters as fetch_clusters, export_dpo_dataset, export_dpo_dataset_jsonl

logger = logging.getLogger("unimon.analytics_router")

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analítica & KPIs UniMon"]
)


@router.get(
    "/kpis",
    status_code=status.HTTP_200_OK,
    summary="Obtener Resumen Ejecutivo de KPIs de UniMon",
    description="Retorna métricas consolidadas de resolución en Nivel 1, tasa de escalado, latencia promedio, tokens y uso por rol."
)
async def get_kpis() -> Dict[str, Any]:
    """
    Endpoint que retorna el dashboard consolidado de métricas de telemetría.
    """
    kpis = get_kpis_summary()
    return {
        "status": "success",
        "data": kpis
    }


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


