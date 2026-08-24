import os
import sys
from pathlib import Path
import chromadb

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

CHROMA_PATH = "./chroma_db"


def categorize_doc(source_name: str):
    s = source_name.lower()
    
    # 1. Reglas para Estudiantes
    keywords_estudiante = [
        "estudiante", "aspirante", "matricula", "matrícula", 
        "inscripcion", "inscripción", "reintegro", "tutoria", "tutoría",
        "grado", "credito", "crédito", "enfasis", "énfasis", "desertor"
    ]
    
    # 2. Reglas para Funcionarios / Docentes
    keywords_funcionario = [
        "profesor", "docente", "funcionario", "pac", "asignacion", 
        "asignación", "kactus", "seven", "erp", "p-gt-", "autoevaluacion", 
        "autoevaluación", "evaluacion docente", "activos", "compras"
    ]
    
    # Asignación de Audiencia / Rol
    if any(k in s for k in keywords_estudiante):
        audience = "estudiante"
    elif any(k in s for k in keywords_funcionario):
        audience = "funcionario"
    else:
        audience = "general"
        
    # Asignación de Categoría Temática
    if "teams" in s or "reuniones" in s:
        category = "teams"
    elif "aula" in s or "moodle" in s:
        category = "aula_extendida"
    elif "kactus" in s or "seven" in s or "erp" in s:
        category = "erp_kactus_seven"
    elif "p-gt-" in s:
        category = "procedimientos_ti"
    elif "carnet" in s or "app" in s:
        category = "carnet_app"
    elif "portal" in s or "portales" in s:
        category = "portales"
    elif "contraseña" in s or "password" in s or "correo" in s:
        category = "cuentas_accesos"
    else:
        category = "general"
        
    return audience, category


def update_metadata():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collections = client.list_collections()
    if not collections:
        print("❌ No se encontraron colecciones en ChromaDB.")
        return
        
    collection = collections[0]
    print(f"🔄 Actualizando metadatos en colección: '{collection.name}' ({collection.count()} registros)...")
    
    results = collection.get(include=["metadatas"])
    ids = results["ids"]
    metadatas = results["metadatas"]
    
    updated_metadatas = []
    for meta in metadatas:
        source = meta.get("source", "") if meta else ""
        aud, cat = categorize_doc(source)
        new_meta = dict(meta) if meta else {}
        new_meta["audience"] = aud
        new_meta["category"] = cat
        updated_metadatas.append(new_meta)
        
    # Actualizar en lotes
    BATCH_SIZE = 500
    for i in range(0, len(ids), BATCH_SIZE):
        batch_ids = ids[i:i+BATCH_SIZE]
        batch_metas = updated_metadatas[i:i+BATCH_SIZE]
        collection.update(
            ids=batch_ids,
            metadatas=batch_metas
        )
        print(f"  ✓ Lote actualizado: {i + len(batch_ids)}/{len(ids)}")
        
    print("✅ ¡Metadatos actualizados exitosamente en ChromaDB!")


if __name__ == "__main__":
    update_metadata()
