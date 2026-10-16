"""Compare the active RAG and an isolated candidate with logged user questions.

Questions are sourced from the existing retrieval fixture and read-only analytics
telemetry. The run does not write chat telemetry, Golden Cache, or either index.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import re
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.services.rag_service import RAGService

FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "rag_retrieval_eval.json"
ANALYTICS_PATH = PROJECT_ROOT / "data" / "analytics.db"
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
LONG_NUMBER_RE = re.compile(r"\b\d{7,}\b")
SOURCE_FILE_RE = re.compile(
    r"(?:^|[,;\n]\s*)(.+?\.(?:pdf|pptx|docx|xlsx|md|html?|txt))(?=\s*(?:[,;\n]|$))",
    flags=re.IGNORECASE,
)


def parse_sources(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    # Telemetry historically stores sources as a plain comma-separated string,
    # but document names may themselves contain commas. Parse through each file
    # extension first so names such as "Reportes (A, B).pptx" stay intact.
    matched = [match.group(1).strip().strip("\"'") for match in SOURCE_FILE_RE.finditer(text)]
    if matched:
        return matched
    return [item.strip().strip("\"'") for item in re.split(r"[,;\n]", text) if item.strip()]


def read_questions(limit: int, seed: int) -> list[dict[str, Any]]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    selected: list[dict[str, Any]] = [
        {
            "id": item["id"],
            "question": item["query"],
            "expected_sources": item["expected_sources"],
            "label_basis": "fixture",
        }
        for item in fixture
        if item.get("query") and item.get("expected_sources")
    ]
    seen = {re.sub(r"\s+", " ", item["question"].casefold()).strip() for item in selected}

    db_uri = f"file:{ANALYTICS_PATH.resolve().as_posix()}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """SELECT user_query, referenced_docs, timestamp
               FROM telemetry_interactions
               WHERE COALESCE(user_query, '') <> ''
                 AND COALESCE(referenced_docs, '') NOT IN ('', 'None', '[]', 'null')
               ORDER BY timestamp DESC"""
        ).fetchall()

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rng = random.Random(seed)
    for row in rows:
        question = re.sub(r"\s+", " ", str(row["user_query"] or "")).strip()
        normalized = question.casefold()
        if len(question) < 15 or normalized in seen:
            continue
        if EMAIL_RE.search(question) or LONG_NUMBER_RE.search(question):
            continue
        if normalized in {"resolved", "retry_diagnosis", "sí", "si", "no", "gracias"}:
            continue
        expected = parse_sources(row["referenced_docs"])
        if not expected:
            continue
        item = {
            "id": f"telemetry_{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:12]}",
            "question": question,
            "expected_sources": expected,
            "label_basis": "historical_bot_references_proxy",
        }
        by_source[expected[0]].append(item)
        seen.add(normalized)

    for items in by_source.values():
        rng.shuffle(items)
    source_groups = list(by_source.values())
    rng.shuffle(source_groups)
    while source_groups and len(selected) < limit:
        remaining = []
        for group in source_groups:
            if group and len(selected) < limit:
                selected.append(group.pop())
            if group:
                remaining.append(group)
        source_groups = remaining
    return selected[:limit]


def compact_trace(trace: list[dict[str, Any]]) -> dict[str, Any]:
    stages: dict[str, Any] = {}
    for item in trace:
        stage = str(item.get("stage", "unknown"))
        chunks = item.get("chunks") or []
        stages[stage] = [
            {
                "source": chunk.get("source"),
                "page": chunk.get("page"),
                "score": chunk.get("score"),
                "text": chunk.get("text", "")[:700],
            }
            for chunk in chunks
        ]
    return stages


async def run_query(service: RAGService, item: dict[str, Any]) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    started = time.perf_counter()
    try:
        answer = await service.query_rag(
            question=item["question"],
            user_role=None,
            golden_context=None,
            trace_callback=trace.append,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        stages = compact_trace(trace)
        final_sources = list(dict.fromkeys(str(source) for source in answer.get("sources", []) if source))
        expected = item["expected_sources"]
        matched = [source for source in expected if Path(source).name in final_sources]
        return {
            "id": item["id"],
            "question": item["question"],
            "expected_sources": expected,
            "label_basis": item["label_basis"],
            "response": answer.get("response", ""),
            "returned_sources": final_sources,
            "matched_expected_sources": matched,
            "expected_source_recall": round(len(matched) / len(expected), 3) if expected else None,
            "all_expected_sources_returned": len(matched) == len(expected) if expected else None,
            "retrieved_chunks": answer.get("retrieved_chunks"),
            "has_context": answer.get("has_context"),
            "model": answer.get("model"),
            "latency_ms": elapsed_ms,
            "trace": stages,
            "error": None,
        }
    except Exception as exc:
        return {
            "id": item["id"], "question": item["question"],
            "expected_sources": item["expected_sources"], "label_basis": item["label_basis"],
            "response": "", "returned_sources": [], "matched_expected_sources": [],
            "expected_source_recall": 0.0, "all_expected_sources_returned": False,
            "retrieved_chunks": 0, "has_context": False, "model": None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "trace": compact_trace(trace), "error": str(exc)[:1000],
        }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [item for item in results if not item.get("error")]
    return {
        "questions": len(results),
        "successes": len(valid),
        "errors": len(results) - len(valid),
        "expected_source_recall_mean": round(
            sum(item.get("expected_source_recall") or 0 for item in valid) / len(valid), 3
        ) if valid else None,
        "all_expected_sources_rate": round(
            sum(bool(item.get("all_expected_sources_returned")) for item in valid) / len(valid), 3
        ) if valid else None,
        "latency_ms_mean": round(sum(item["latency_ms"] for item in results) / len(results), 2) if results else None,
        "latency_ms_p95": round(sorted(item["latency_ms"] for item in results)[max(0, int(len(results) * 0.95) - 1)], 2) if results else None,
    }


async def evaluate(output_dir: Path, candidate_path: Path, limit: int, seed: int) -> None:
    settings = get_settings()
    questions = read_questions(limit, seed)
    if len(questions) < limit:
        print(f"Aviso: solo hay {len(questions)} preguntas distintas con fuentes de referencia aptas.")
    baseline = RAGService(chroma_db_dir=str(Path(settings.chroma_db_dir).resolve()))
    candidate = RAGService(chroma_db_dir=str(candidate_path.resolve()))
    outputs: dict[str, list[dict[str, Any]]] = {"baseline": [], "candidate": []}
    for variant, service in (("baseline", baseline), ("candidate", candidate)):
        for index, item in enumerate(questions, 1):
            print(f"[{variant}] {index}/{len(questions)} {item['id']}", flush=True)
            outputs[variant].append(await run_query(service, item))

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": settings.openai_model,
        "evaluation_note": (
            "Fixture cases have curated expected sources. Historical telemetry source names are only proxies "
            "for expected evidence; this source-recall metric is not a human-verified answer-accuracy score."
        ),
        "question_count": len(questions),
        "question_source_counts": {
            "fixture": sum(item["label_basis"] == "fixture" for item in questions),
            "historical_telemetry_proxy": sum(item["label_basis"] != "fixture" for item in questions),
        },
        "baseline_summary": summarize(outputs["baseline"]),
        "candidate_summary": summarize(outputs["candidate"]),
        "questions": questions,
        "baseline": outputs["baseline"],
        "candidate": outputs["candidate"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "retrieval_evaluation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "evaluation_file": str(output_dir / "retrieval_evaluation.json"),
        "baseline": report["baseline_summary"],
        "candidate": report["candidate_summary"],
        "question_source_counts": report["question_source_counts"],
    }, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261016)
    args = parser.parse_args()
    asyncio.run(evaluate(args.output_dir.resolve(), args.candidate.resolve(), args.limit, args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
