"""
Router alias para Analitica y KPIs de UniMon (retrocompatibilidad).
Re-exporta los endpoints y el router desde app.routers.analytics.
"""

from app.routers.analytics import (
    router,
    get_kpis,
    get_query_clusters,
    export_dpo,
    get_kpis_summary
)

__all__ = [
    "router",
    "get_kpis",
    "get_query_clusters",
    "export_dpo",
    "get_kpis_summary"
]
