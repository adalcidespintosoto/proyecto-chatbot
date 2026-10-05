"""Mide tasas de overlap en Chroma sin modificar la colección.

Uso: python scripts/audit_overlap_rates.py [--sample-size 250] [--seed 20261005]
Compara la fórmula previa con la conversión correcta de la métrica configurada.
"""

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.rag_service import RAGService


def distance_to_similarity(distance: float, metric: str) -> float:
    metric = (metric or "l2").casefold()
    similarity = 1.0 - float(distance) / 2.0 if metric in {"l2", "euclidean"} else 1.0 - float(distance)
    return max(-1.0, min(1.0, similarity))


def summarize(values: list[float], redundant: float, ambiguous: float) -> dict:
    total = len(values)
    if not total:
        return {"sample_size": 0, "redundant_pct": 0, "ambiguous_pct": 0, "novel_pct": 0}
    return {
        "sample_size": total,
        "redundant_pct": round(sum(value >= redundant for value in values) * 100 / total, 1),
        "ambiguous_pct": round(sum(ambiguous <= value < redundant for value in values) * 100 / total, 1),
        "novel_pct": round(sum(value < ambiguous for value in values) * 100 / total, 1),
    }


def main() -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-size", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20261005)
    parser.add_argument("--redundant-threshold", type=float, default=0.88)
    parser.add_argument("--ambiguous-threshold", type=float, default=0.65)
    parser.add_argument("--output", type=Path, help="Guarda el resultado JSON en esta ruta")
    args = parser.parse_args()

    service = RAGService()
    store = service.vector_store
    if store is None:
        raise RuntimeError(f"No se pudo abrir Chroma local: {service.chroma_db_dir}")
    collection = store._collection
    configuration = getattr(collection, "configuration", None) or {}
    metadata = getattr(collection, "metadata", None) or {}
    metric = (configuration.get("hnsw") or {}).get("space") or metadata.get("hnsw:space", "l2")
    corpus = collection.get(include=["documents", "metadatas"])
    rows = [
        (text, item_metadata)
        for text, item_metadata in zip(corpus.get("documents") or [], corpus.get("metadatas") or [])
        if text and (item_metadata or {}).get("source")
    ]
    random.Random(args.seed).shuffle(rows)
    rows = rows[:max(0, args.sample_size)]
    if not rows:
        raise RuntimeError("La colección no contiene fragmentos utilizables para medir.")

    embeddings = service.embeddings.embed_documents([f"passage: {text}" for text, _metadata in rows])
    hits = collection.query(
        query_embeddings=embeddings,
        n_results=min(12, collection.count()),
        include=["distances", "metadatas"],
    )
    old_values = []
    corrected_values = []
    for index, (_text, item_metadata) in enumerate(rows):
        source = item_metadata.get("source")
        distances = [
            distance
            for distance, match_metadata in zip(hits["distances"][index], hits["metadatas"][index])
            if (match_metadata or {}).get("source") != source
        ]
        if not distances:
            continue
        nearest_distance = min(distances)
        old_values.append(max(0.0, 1.0 - nearest_distance))
        corrected_values.append(distance_to_similarity(nearest_distance, metric))

    report = {
        "collection": collection.name,
        "collection_count": collection.count(),
        "metric": metric,
        "seed": args.seed,
        "requested_sample_size": args.sample_size,
        "nearest_other_source_among_top_k": 12,
        "thresholds": {"redundant": args.redundant_threshold, "ambiguous": args.ambiguous_threshold},
        "previous_formula": summarize(old_values, args.redundant_threshold, args.ambiguous_threshold),
        "corrected_formula": summarize(corrected_values, args.redundant_threshold, args.ambiguous_threshold),
        "mutates_collection": False,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(main(), ensure_ascii=False, indent=2))
