"""Regenerate the remaining partial answers and regrade with all final chunks.

Use --limit N for a prompt ablation, or omit it to rerun all residual partial
and unverifiable cases. Golden Cache promotion is opt-in via --promote.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config import get_settings
from app.services.golden_cache_service import get_golden_collection, save_golden_case
from app.services.llm_client import LLMClient
from app.services.rag_service import RAGService
from scripts.review_partial_answers_multievidence import (
    answer_body,
    atomic_write,
    judge_batch,
    normalize_source,
    safe_clip_trace,
)


BASELINE_PATH = ROOT / "reports" / "partial_multievidence_review_20261006.json"
DEFAULT_OUTPUT = ROOT / "reports" / "partial_prompt_retest_20261013.json"
JUDGE_BATCH_SIZE = 4


def applicable_configured_policy(question: str, system_prompt: str) -> list[str]:
    policies: list[str] = []
    q = question.casefold()
    if any(term in q for term in ("elección", "elecciones", "votar", "voto", "votación")):
        line = next((
            item.strip(" -*") for item in system_prompt.splitlines()
            if "portal configurado es https://elecciones.unisimon.edu.co/" in item.casefold()
        ), None)
        if line:
            policies.append(line)
    marker = "[POLÍTICAS INSTITUCIONALES CONFIGURADAS POR LA APLICACIÓN; NO SON CHUNKS RECUPERADOS]"
    if marker in system_prompt:
        configured = system_prompt.split(marker, 1)[1].split("[CONTEXTO INSTITUCIONAL RECUPERADO]", 1)[0].strip()
        if configured:
            policies.append(configured)
    return policies


async def generate_case(service: RAGService, baseline_row: dict[str, Any]) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    captured_system_prompts: list[str] = []
    original_chat_completion = service.llm_client.chat_completion

    async def capture_chat_completion(*args: Any, **kwargs: Any) -> dict[str, Any]:
        messages = kwargs.get("messages")
        if messages is None and args:
            messages = args[0]
        if messages:
            captured_system_prompts.append(str(messages[0].get("content") or ""))
        return await original_chat_completion(*args, **kwargs)

    with patch.object(service.llm_client, "chat_completion", new=capture_chat_completion):
        result = await service.query_rag(
            question=baseline_row["question"],
            user_role="general",
            trace_callback=trace.append,
        )

    chunks = safe_clip_trace(trace, "final_context", 100)
    expected = normalize_source(baseline_row.get("source", ""))
    expected_found = any(normalize_source(chunk.get("source", "")) == expected for chunk in chunks)
    prompt = captured_system_prompts[-1] if captured_system_prompts else ""
    return {
        **baseline_row,
        "baseline_answer": baseline_row.get("answer", ""),
        "baseline_multievidence_verdict": (baseline_row.get("multievidence_review") or {}).get("verdict"),
        "answer": str(result.get("response") or ""),
        "answer_without_footer": answer_body(str(result.get("response") or "")),
        "generation_model": result.get("model"),
        "generation_source": result.get("source"),
        "generation_error": result.get("error"),
        # A baseline row may contain a judge verdict for an older answer. Clear
        # it so review_cases always grades this newly generated response.
        "new_multievidence_review": None,
        "retrieval_rebuilt": {
            "candidate_chunks_top25": safe_clip_trace(trace, "candidates", 25),
            "candidate_chunks_top100_diagnostic": safe_clip_trace(trace, "candidates", 100),
            "reranker_scores_top80_diagnostic": safe_clip_trace(trace, "reranker_scores", 80),
            "reranked_chunks_top30": safe_clip_trace(trace, "reranked", 30),
            "expanded_chunks_before_budget": safe_clip_trace(trace, "expanded_context", 100),
            "chunks_after_budget": safe_clip_trace(trace, "budgeted_context", 100),
            "final_chunks": chunks,
            "final_sources": sorted({normalize_source(c.get("source", "")) for c in chunks}),
            "expected_source_in_final_context": expected_found,
        },
        "applicable_configured_policies": applicable_configured_policy(baseline_row["question"], prompt),
        "generation_system_prompt_captured": bool(prompt),
    }


async def review_cases(
    rows: list[dict[str, Any]],
    llm: LLMClient,
    checkpoint: dict[str, Any],
    checkpoint_path: Path,
) -> None:
    judge_rows = []
    for row in rows:
        judge_rows.append({
            **row,
            "answer": row.get("answer_without_footer", ""),
            "sources": [chunk.get("source", "") for chunk in row["retrieval_rebuilt"]["final_chunks"]],
            "review_retrieval": {
                "final_chunks": row["retrieval_rebuilt"]["final_chunks"],
                "expected_source_in_reconstructed_final_context": row["retrieval_rebuilt"]["expected_source_in_final_context"],
            },
            "applicable_configured_policies_for_judge": row.get("applicable_configured_policies", []),
        })
    pending = [row for row in judge_rows if not row.get("new_multievidence_review")]
    for start in range(0, len(pending), JUDGE_BATCH_SIZE):
        batch = pending[start : start + JUDGE_BATCH_SIZE]
        await judge_batch(batch, llm, asyncio.Semaphore(1))
        for updated in batch:
            target = next(row for row in rows if row["case_id"] == updated["case_id"])
            target["new_multievidence_review"] = updated.get("multievidence_review")
        checkpoint["phase"] = "judging"
        atomic_write(checkpoint_path, checkpoint)
        completed = sum(bool(row.get("new_multievidence_review")) for row in rows)
        print(f"Respuestas revisadas: {completed}/{len(rows)}", flush=True)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=BASELINE_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=0, help="Solo N casos para probar el prompt.")
    parser.add_argument("--case-id", action="append", default=[], help="Limita a uno o más IDs del informe base; se puede repetir.")
    parser.add_argument("--generation-only", action="store_true", help="Elegir parciales cuyo contexto previo era suficiente.")
    parser.add_argument("--promote", action="store_true", help="Guardar respuestas correctas y verificadas en Golden Cache.")
    parser.add_argument("--review-checkpoint", action="store_true", help="Reutilizar un JSON de respuestas generadas y ejecutar solo el juez.")
    args = parser.parse_args()

    settings = get_settings()
    if settings.llm_provider.casefold() != "openai" or not settings.openai_api_key:
        raise RuntimeError("La regeneración requiere OpenAI configurado; no se cambiará silenciosamente a otro juez.")
    if args.review_checkpoint:
        if not args.output.exists():
            raise FileNotFoundError(f"No existe el checkpoint: {args.output}")
        output = json.loads(args.output.read_text(encoding="utf-8"))
        rows = output.get("results", [])
        if not rows or any("answer_without_footer" not in row for row in rows):
            raise ValueError("El checkpoint no contiene respuestas generadas para revisar.")
        print(f"Reutilizando {len(rows)} respuestas generadas desde {args.output}.", flush=True)
    else:
        baseline = json.loads(args.input.read_text(encoding="utf-8"))
        rows = [row for row in baseline["results"] if row["multievidence_review"]["verdict"] in {"partial", "no_verificable"}]
        if args.case_id:
            requested = set(args.case_id)
            rows = [row for row in rows if row["case_id"] in requested]
        if args.generation_only:
            rows = [row for row in rows if "evidencia suficiente" in row["multievidence_review"].get("diagnosis", "")]
        if args.limit > 0:
            rows = rows[:args.limit]

        output = {
            "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "input_report": str(args.input),
            "prompt_version": "exact-scope-contract-20261013",
            "configured_model": settings.openai_model,
            "generation_mode": "RAGService.query_rag direct; live MultiQuery; no API Golden Cache read",
            "golden_cache_before": get_golden_collection().count(),
            "results": [],
            "summary": {},
        }
        service = RAGService()
        if service.vector_store is None:
            raise RuntimeError(f"No se pudo abrir el índice RAG: {service.chroma_db_dir}")
        print(f"Regenerando {len(rows)} respuestas con {service.vector_store._collection.count()} chunks.", flush=True)

        for index, row in enumerate(rows, 1):
            try:
                generated = await generate_case(service, row)
            except Exception as exc:
                generated = {
                    **row,
                    "baseline_answer": row.get("answer", ""),
                    "answer": "",
                    "answer_without_footer": "",
                    "generation_error": f"{type(exc).__name__}: {exc}",
                    "retrieval_rebuilt": {"final_chunks": [], "final_sources": [], "expected_source_in_final_context": False},
                    "applicable_configured_policies": [],
                }
            output["results"].append(generated)
            if index % 5 == 0 or index == len(rows):
                print(f"Respuestas generadas: {index}/{len(rows)}", flush=True)
                atomic_write(args.output, output)

    llm = LLMClient()
    await review_cases(output["results"], llm, output, args.output)

    saved = 0
    if args.promote:
        for row in output["results"]:
            review = row.get("new_multievidence_review") or {}
            retrieval = row.get("retrieval_rebuilt") or {}
            eligible = (
                review.get("verdict") == "correct"
                and float(review.get("confidence", 0)) >= 0.98
                and not review.get("unsupported_material_claims")
                and retrieval.get("expected_source_in_final_context") is True
                and row.get("evidence_valid") is True
            )
            row["golden_cache_eligible"] = eligible
            row["golden_cache_saved"] = False
            if eligible:
                row["golden_cache_saved"] = bool(save_golden_case(
                    session_id=f"partial-retest-{output['run_id']}-{row['case_id']}",
                    user_query=row["question"],
                    bot_response=row.get("answer_without_footer", ""),
                    role="general",
                ))
                saved += int(row["golden_cache_saved"])

    final = Counter((r.get("new_multievidence_review") or {}).get("verdict", "no_verificable") for r in output["results"])
    before_correct = sum(r.get("baseline_multievidence_verdict") == "correct" for r in output["results"])
    after_correct = final["correct"]
    output["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    output["golden_saved"] = saved
    output["golden_cache_after"] = get_golden_collection().count()
    output["summary"] = {
        "reviewed": len(output["results"]),
        "previously_correct_among_cohort": before_correct,
        "new_correct": after_correct,
        "correctness_delta": after_correct - before_correct,
        "partial": final["partial"],
        "incorrect": final["incorrect"],
        "no_verificable": final["no_verificable"],
        "expected_source_hits": sum(bool((r.get("retrieval_rebuilt") or {}).get("expected_source_in_final_context")) for r in output["results"]),
        "golden_saved": saved,
        "golden_cache_before": output["golden_cache_before"],
        "golden_cache_after": output["golden_cache_after"],
        "by_previous_verdict": {
            f"{previous or 'unknown'} -> {verdict}": count
            for (previous, verdict), count in Counter(
                (r.get("baseline_multievidence_verdict"), (r.get("new_multievidence_review") or {}).get("verdict", "no_verificable"))
                for r in output["results"]
            ).items()
        },
    }
    output["phase"] = "completed"
    atomic_write(args.output, output)
    print(json.dumps({"summary": output["summary"], "output": str(args.output)}, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
