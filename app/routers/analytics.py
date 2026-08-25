"""
Router para Métricas, KPIs y Analítica de Desempeño de UniMon.
Provee endpoints REST para consultar la observabilidad del sistema en tiempo real.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.services.telemetry_service import get_kpis_summary

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
