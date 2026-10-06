"""Promote only independently verified, grounded load-test answers to Golden Cache."""
from __future__ import annotations
import argparse, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from app.services.golden_cache_service import get_golden_collection, save_golden_case


def norm(value: str) -> str:
    folded = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(ch for ch in folded if not unicodedata.combining(ch)).casefold()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--min-confidence", type=float, default=0.95)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    trace_by_user = {int(row["user"]): row for row in trace.get("cases", [])}
    collection = get_golden_collection()
    before = collection.count()
    candidates = []
    for row in report.get("results", []):
        review = row.get("quality_review", {})
        if review.get("verdict") != "correct" or float(review.get("confidence", 0)) < args.min_confidence:
            continue
        traced = trace_by_user.get(int(row["user"]))
        if not traced:
            continue
        final_sources = {norm(Path(str(chunk.get("source", ""))).name) for chunk in traced.get("final_chunks", [])}
        expected_sources = [norm(Path(str(source)).name) for source in row.get("expected_sources", [])]
        if not expected_sources or not all(source in final_sources for source in expected_sources):
            continue
        answer = re.split(r"\n\s*---\s*\n", row.get("answer", ""), maxsplit=1)[0].strip()
        if len(answer) < 60:
            continue
        candidates.append((row, answer))
    saved = 0
    rejected = 0
    for row, answer in candidates:
        if save_golden_case(
            session_id=row["session_id"],
            user_query=row["question"],
            bot_response=answer,
            role="general",
        ):
            saved += 1
        else:
            rejected += 1
    after = collection.count()
    print(json.dumps({
        "before": before,
        "quality_correct_total": sum(r.get("quality_review", {}).get("verdict") == "correct" for r in report.get("results", [])),
        "qualified_with_grounded_final_sources": len(candidates),
        "saved_or_updated": saved,
        "rejected_by_cache_validators": rejected,
        "after": after,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
