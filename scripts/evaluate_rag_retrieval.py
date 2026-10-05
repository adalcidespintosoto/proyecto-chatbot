"""Evalúa etapas reales de recuperación contra el Chroma local, sin llamar al LLM.

Uso: python scripts/evaluate_rag_retrieval.py [--output ruta.json]
La salida conserva candidatos, orden rerankeado, contexto final y fuente esperada.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CASES_PATH = ROOT / "tests" / "fixtures" / "rag_retrieval_eval.json"

from app.services.rag_service import RAGService


async def evaluate_case(service: RAGService, case: dict) -> dict:
    trace = []
    llm_mock = AsyncMock(return_value={"content": "Evaluación de recuperación sin generación.", "model": "eval"})
    with patch(
        "app.services.rag_service.async_generate_multi_query_variants",
        new=AsyncMock(return_value=[case["query"]]),
    ), patch.object(
        service.llm_client,
        "chat_completion",
        new=llm_mock,
    ):
        await service.query_rag(
            question=case["query"],
            user_role=case.get("role"),
            trace_callback=trace.append,
        )

    stages = {item["stage"]: item["chunks"] for item in trace}
    expected = {name.casefold() for name in case["expected_sources"]}
    result = {
        **case,
        "candidates": stages.get("candidates", []),
        "reranked": stages.get("reranked", []),
        "final_chunks": stages.get("final_context", []),
        "llm_messages": (
            llm_mock.await_args.kwargs.get("messages", []) if llm_mock.await_args else []
        ),
    }
    require_all_sources = case.get("require_all_expected_sources", False)
    for key in ("candidates", "reranked", "final_chunks"):
        observed = {Path(chunk["source"]).name.casefold() for chunk in result[key]}
        result[f"expected_source_hit_{key}"] = (
            expected.issubset(observed) if require_all_sources else bool(expected & observed)
        )
        result[f"missing_expected_sources_{key}"] = sorted(expected - observed)
    result["estimated_final_context_tokens"] = sum(
        (len(chunk["text"]) + 2) // 3 for chunk in result["final_chunks"]
    )
    return result


async def main() -> dict:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    service = RAGService()
    if service.vector_store is None:
        raise RuntimeError(f"No se pudo abrir Chroma local: {service.chroma_db_dir}")
    results = [await evaluate_case(service, case) for case in cases]
    return {
        "collection_count": service.vector_store._collection.count(),
        "collection_name": service.vector_store._collection.name,
        "cases": results,
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Guarda el reporte JSON también en esta ruta")
    args = parser.parse_args()
    report = asyncio.run(main())
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
