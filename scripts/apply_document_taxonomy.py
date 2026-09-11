"""
Script de Taxonomía Documental para UniMon (Universidad Simón Bolívar - Colombia).
Clasifica y actualiza los metadatos de los fragmentos existentes en ChromaDB con tres etiquetas:
  - doc_type: autoservicio | gestion_interna | normativa
  - audience: estudiante | profesor | funcionario | general | admin_ti
  - category: cuentas_accesos | portales | academico | financiero | hardware_redes | ...

NO recalcula embeddings ni reprocesa imágenes. Solo actualiza metadatos en lote.
"""

import os
import re
import sys
from pathlib import Path
from collections import Counter

import chromadb

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

CHROMA_PATH = "./chroma_db"

# ─────────────────────────────────────────────────────────────────────
# PATRONES DE CLASIFICACIÓN POR NOMBRE DE ARCHIVO / FUENTE
# ─────────────────────────────────────────────────────────────────────

# Gestión Interna / Backoffice (doc_type: "gestion_interna")
INTERNAL_PATTERNS = [
    r"habilitar\s*permisos", r"gesti[oó]n\s*de\s*c[oó]digos",
    r"asignaci[oó]n\s*acad[eé]mica", r"bancos\s*y\s*cuentas",
    r"aprobaci[oó]n\s*solicitudes", r"reporte\s*de", r"reportes",
    r"desertores", r"director", r"solo\s*consulta",
    r"evaluaciones\s*de\s*selecci[oó]n", r"parametrizaci[oó]n",
    r"gesti[oó]n\s*de\s*ingreso.*funcionarios",
    r"instructivo\s*bloqueos\s*\(admin\)", r"bloqueos\s*admin",
    r"activos\s*fijos", r"compras",
    r"liquidaci[oó]n", r"n[oó]mina", r"nomina",
    r"presupuesto", r"contabilidad",
    r"auditor[ií]a", r"control\s*interno",
]

# Normativa / Reglamentos / Estatutos
NORMATIVE_PATTERNS = [
    r"estatuto", r"reglamento", r"calendario\s*acad[eé]mico",
    r"resoluci[oó]n", r"acuerdo\s*\d+", r"normativa",
    r"pol[ií]tica\s*de", r"c[oó]digo\s*de\s*[eé]tica",
]

# Autoservicio para Estudiantes
STUDENT_PATTERNS = [
    r"estudiante", r"estudiantes", r"aspirante", r"aspirantes",
    r"reintegro", r"pregrado",
    r"matricula\s*antiguos", r"matr[ií]cula\s*antiguos",
    r"inscripci[oó]n", r"inscripcion",
    r"movilidad\s*acad[eé]mica.*estudiante",
    r"certificados?\s*estudiante",
    r"instructivo\s*portales?\s*estudiante",
    r"portal\s*estudiante",
    r"tutor[ií]a", r"tutoria",
    r"grado\b", r"cr[eé]dito", r"credito",
    r"[eé]nfasis", r"enfasis",
]

# Autoservicio para Profesores/Docentes
TEACHER_PATTERNS = [
    r"profesor", r"profesores", r"docente", r"docentes",
    r"pac\s*\(profesores\)", r"pac\s*profesores",
    r"diligenciamiento\s*de\s*pac",
    r"servicios\s*institucionales.*profesores",
    r"evaluaci[oó]n\s*docente",
    r"autoevaluaci[oó]n", r"autoevaluacion",
    r"registro.*calificaciones", r"calificaciones.*posgrado",
    r"calificaciones.*profesor", r"inasistencias.*portal\s*profesor",
]

# Funcionarios específicos (no admin_ti, pero sí usuario de sistemas internos)
FUNCIONARIO_PATTERNS = [
    r"funcionario", r"funcionarios",
    r"administrativo", r"administrativos",
    r"kactus", r"seven", r"erp",
    r"p-gt-\d+",
]

# ─────────────────────────────────────────────────────────────────────
# PATRONES DE CATEGORÍA TEMÁTICA
# ─────────────────────────────────────────────────────────────────────

CATEGORY_RULES = [
    # (patrón, categoría)
    (r"teams|reuniones|microsoft\s*teams", "teams"),
    (r"aula|moodle|aula\s*extendida", "aula_extendida"),
    (r"kactus|katuc|seven|seben|erp", "erp_kactus_seven"),
    (r"p-gt-\d+|procedimiento", "procedimientos_ti"),
    (r"carnet|carn[eé]|app\s*unisimon", "carnet_app"),
    (r"portal|portales", "portales"),
    (r"contrase[ñn]a|password|clave|bloqueo|desbloque|correo\s*institucional|correo\s*electr[oó]nico|acceso|cuenta", "cuentas_accesos"),
    (r"matr[ií]cula|matricula|inscripci[oó]n|inscripcion|reintegro|grado|cr[eé]dito|credito", "academico"),
    (r"computador|port[aá]til|monitor|pantalla|proyector|mouse|teclado|red|wifi|internet|hdmi|cable|impresora|esc[aá]ner", "hardware_redes"),
    (r"n[oó]mina|nomina|liquidaci[oó]n|presupuesto|bancos|contabilidad|financiero", "financiero"),
    (r"virus|malware|antivirus|antimalware|amenaza", "seguridad"),
    (r"backup|copia\s*de\s*seguridad|respaldo|restauraci[oó]n", "backup_restauracion"),
]


def classify_document(source_name: str) -> dict:
    """
    Clasifica un documento por su nombre de archivo/fuente y retorna:
    {"doc_type": ..., "audience": ..., "category": ...}
    """
    name = source_name.lower()
    clean_src = Path(source_name).name

    # ── 0. Verificación por carpeta física si el archivo existe en data/docs ──
    folder_audience = None
    folder_doc_type = None
    for folder in ["1_estudiantes", "2_profesores", "3_funcionarios_gestion", "4_general_normativa"]:
        if (Path("data/docs") / folder / clean_src).exists():
            if folder == "2_profesores":
                folder_audience = "profesor"
                folder_doc_type = "autoservicio"
            elif folder == "1_estudiantes":
                folder_audience = "estudiante"
                folder_doc_type = "autoservicio"
            elif folder == "3_funcionarios_gestion":
                folder_audience = "funcionario"
                folder_doc_type = "gestion_interna"
            elif folder == "4_general_normativa":
                folder_audience = "general"
                folder_doc_type = "normativa"
            break

    # ── 1. Determinar doc_type ──
    doc_type = folder_doc_type or "autoservicio"

    for pattern in NORMATIVE_PATTERNS:
        if re.search(pattern, name):
            doc_type = "normativa"
            break

    if doc_type != "normativa":
        for pattern in INTERNAL_PATTERNS:
            if re.search(pattern, name):
                doc_type = "gestion_interna"
                break

    # ── 2. Determinar audience ──
    if doc_type == "gestion_interna":
        if any(re.search(p, name) for p in [r"permiso", r"c[oó]digo", r"parametrizaci[oó]n", r"bloqueos\s*\(admin\)", r"bloqueos\s*admin"]):
            audience = "admin_ti"
        else:
            audience = "funcionario"
    elif doc_type == "normativa":
        audience = "general"
    elif folder_audience:
        # Si la carpeta física lo define (ej. 2_profesores), respetar esa audiencia institucional
        audience = folder_audience
    elif any(re.search(p, name) for p in TEACHER_PATTERNS):
        audience = "profesor"
    elif any(re.search(p, name) for p in STUDENT_PATTERNS):
        audience = "estudiante"
    elif any(re.search(p, name) for p in FUNCIONARIO_PATTERNS):
        audience = "funcionario"
    else:
        audience = "general"

    # ── 3. Determinar category ──
    category = "general"
    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, name):
            category = cat
            break

    return {
        "doc_type": doc_type,
        "audience": audience,
        "category": category,
    }


def run_taxonomy_update():
    """
    Itera sobre la colección actual de ChromaDB y actualiza los metadatos
    de todos los chunks existentes sin recalcular embeddings.
    """
    print("=" * 70)
    print(" TAXONOMÍA DOCUMENTAL - ACTUALIZACIÓN DE METADATOS EN CHROMADB")
    print("=" * 70)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collections = client.list_collections()

    if not collections:
        print("❌ No se encontraron colecciones en ChromaDB.")
        return

    collection = collections[0]
    total = collection.count()
    print(f"\n📂 Colección: '{collection.name}' ({total} fragmentos)")

    # Obtener todos los IDs y metadatos
    data = collection.get(include=["metadatas"])
    ids = data["ids"]
    metadatas = data["metadatas"]

    # Contadores para reporte
    type_counter = Counter()
    audience_counter = Counter()
    category_counter = Counter()

    updated_metadatas = []
    for meta in metadatas:
        source = meta.get("source", "") if meta else ""
        classification = classify_document(source)

        new_meta = dict(meta) if meta else {}
        new_meta["doc_type"] = classification["doc_type"]
        new_meta["audience"] = classification["audience"]
        new_meta["category"] = classification["category"]
        updated_metadatas.append(new_meta)

        type_counter[classification["doc_type"]] += 1
        audience_counter[classification["audience"]] += 1
        category_counter[classification["category"]] += 1

    # Actualización en lotes
    BATCH_SIZE = 500
    for i in range(0, len(ids), BATCH_SIZE):
        batch_ids = ids[i:i + BATCH_SIZE]
        batch_metas = updated_metadatas[i:i + BATCH_SIZE]
        collection.update(
            ids=batch_ids,
            metadatas=batch_metas
        )
        processed = min(i + BATCH_SIZE, len(ids))
        print(f"  ✓ Lote actualizado: {processed}/{len(ids)}")

    # ── Reporte Final ──
    print(f"\n{'─' * 50}")
    print(f"📊 DISTRIBUCIÓN POR doc_type:")
    for dtype, count in type_counter.most_common():
        print(f"   {dtype:25s} → {count:5d} chunks")

    print(f"\n📊 DISTRIBUCIÓN POR audience:")
    for aud, count in audience_counter.most_common():
        print(f"   {aud:25s} → {count:5d} chunks")

    print(f"\n📊 DISTRIBUCIÓN POR category:")
    for cat, count in category_counter.most_common():
        print(f"   {cat:25s} → {count:5d} chunks")

    print(f"\n✅ Taxonomía aplicada exitosamente a {len(ids)} fragmentos.")
    print("=" * 70)


if __name__ == "__main__":
    run_taxonomy_update()
