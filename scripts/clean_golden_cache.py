"""
Script para purgar la colección golden_resolved_qa en ChromaDB.
Limpia registros viciados o respuestas alucinadas almacenadas en caché.
"""

import sys
import os

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.golden_cache_service import clear_golden_cache

if __name__ == "__main__":
    print("Iniciando purga de Semantic Golden Cache...")
    success = clear_golden_cache()
    if success:
        print("[EXITO] Golden Cache purgado exitosamente.")
    else:
        print("[ERROR] No se pudo purgar Golden Cache.")
