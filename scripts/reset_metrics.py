"""
Script para reiniciar y limpiar las métricas de telemetría en data/analytics.db.
Permite evaluar el desempeño actual de UniMon desde cero, eliminando consultas y sesiones históricas.
"""

import sys
import os
import argparse
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.services.telemetry_service import reset_telemetry_db
from app.services.golden_cache_service import clear_golden_cache

def main():
    parser = argparse.ArgumentParser(description="Limpiar métricas históricas de UniMon")
    parser.add_argument(
        "--include-golden-cache",
        action="store_true",
        help="Purgar también la colección de Semantic Golden Cache (casos resueltos cacheados)"
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Omitir confirmación interactiva"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("🧹 REINICIO DE MÉTRICAS Y TELEMETRÍA - UNIMON")
    print("=" * 70)

    if not args.yes:
        confirm = input("¿Estás seguro de que deseas eliminar todas las métricas de analytics.db? [s/N]: ")
        if confirm.lower() not in ["s", "si", "sí", "y", "yes"]:
            print("Operación cancelada.")
            return

    res = reset_telemetry_db()
    if res.get("status") == "success":
        print("✅ Base de datos de telemetría (data/analytics.db) reseteada exitosamente:")
        print(f"   - Consultas eliminadas: {res.get('interactions_cleared', 0)}")
        print(f"   - Sesiones eliminadas:  {res.get('sessions_cleared', 0)}")
        print(f"   - Tickets eliminados:   {res.get('tickets_cleared', 0)}")
    else:
        print(f"❌ Error al resetear telemetría: {res.get('message')}")
        return

    if args.include_golden_cache:
        print("\nPurgando Semantic Golden Cache en ChromaDB...")
        if clear_golden_cache():
            print("✅ Golden Cache purgado exitosamente.")
        else:
            print("⚠️ Error al purgar Golden Cache.")

    print("=" * 70)
    print("🎯 Métricas listas desde cero para evaluar la precisión del chatbot actual.")
    print("=" * 70)

if __name__ == "__main__":
    main()
