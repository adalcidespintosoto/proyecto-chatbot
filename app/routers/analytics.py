"""
Router para Métricas, KPIs y Analítica de Desempeño de UniMon.
Provee endpoints REST para consultar la observabilidad del sistema en tiempo real.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.services.telemetry_service import get_kpis_summary
from app.services.clustering_service import analyze_query_clusters

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
async def get_query_clusters(n_clusters: Optional[int] = None) -> Dict[str, Any]:
    """
    Retorna el agrupamiento semántico de preguntas y la detección de vacíos documentales.
    """
    return analyze_query_clusters(n_clusters=n_clusters)

