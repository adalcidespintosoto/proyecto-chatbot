import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from app.config import get_settings

def purge_orphans():
    settings = get_settings()
    chroma_dir = Path(settings.chroma_db_dir)
    docs_dir = Path(settings.docs_dir)

    print("=" * 70)
    print("🧹 PURGA DE DOCUMENTOS HUÉRFANOS EN CHROMADB")
    print("=" * 70)
    print(f"Directorio ChromaDB: {chroma_dir.resolve()}")
    print(f"Directorio Documentos: {docs_dir.resolve()}")

    if not chroma_dir.exists():
        print("❌ El directorio ChromaDB no existe.")
        return

    client = chromadb.PersistentClient(path=str(chroma_dir), settings=Settings(anonymized_telemetry=False))
    try:
        col = client.get_collection("langchain")
    except Exception as e:
        print(f"❌ Error al abrir la colección 'langchain': {e}")
        return

    disk_files = {f.name for f in docs_dir.glob("**/*") if f.is_file()}
    print(f"📄 Archivos válidos en disco: {len(disk_files)}")

    all_data = col.get(include=["metadatas"])
    ids = all_data["ids"]
    metas = all_data["metadatas"]
    total_chunks_before = len(ids)
    print(f"📦 Total de fragmentos antes de la purga: {total_chunks_before}")

    orphan_ids = []
    orphan_sources = {}

    for chunk_id, meta in zip(ids, metas):
        src = meta.get("source") if meta else None
        if not src or src not in disk_files:
            orphan_ids.append(chunk_id)
            orphan_sources[src] = orphan_sources.get(src, 0) + 1

    if not orphan_ids:
        print("✅ No se encontraron fragmentos huérfanos. La base de datos está limpia.")
        return

    print(f"⚠️ Se encontraron {len(orphan_ids)} fragmentos huérfanos pertenecientes a {len(orphan_sources)} documentos inexistentes.")
    print("\nDocumentos a purgar:")
    for src, count in sorted(orphan_sources.items(), key=lambda x: str(x[0])):
        print(f"  - [{count} chunks] {src}")

    # Ejecutar eliminación por lotes
    BATCH_SIZE = 500
    for i in range(0, len(orphan_ids), BATCH_SIZE):
        batch = orphan_ids[i:i + BATCH_SIZE]
        col.delete(ids=batch)

    # Verificación post-purga
    post_data = col.get(include=["metadatas"])
    post_ids = post_data["ids"]
    post_metas = post_data["metadatas"]
    remaining_sources = {m.get("source") for m in post_metas if m and "source" in m}

    print("\n" + "=" * 70)
    print("✅ RESULTADO DE LA PURGA")
    print("=" * 70)
    print(f"🗑️ Fragmentos eliminados: {len(orphan_ids)}")
    print(f"📦 Fragmentos restantes en ChromaDB: {len(post_ids)}")
    print(f"📚 Fuentes únicas restantes: {len(remaining_sources)}")
    print(f"🎯 Coincidencia exacta con archivos en disco: {remaining_sources.issubset(disk_files)} (Restantes: {len(remaining_sources)} / Disco: {len(disk_files)})")
    print("=" * 70)

if __name__ == "__main__":
    purge_orphans()
