"""Mide respuestas de la lógica conversacional sin registrar telemetría ni Golden Cache.

Usa preguntas escritas por el usuario, sesiones aisladas y el proveedor LLM real.
La clasificación de calidad se hace después, contrastando cada respuesta con
la documentación; una respuesta HTTP exitosa no cuenta como respuesta correcta.
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.router_logic import RouterLogic


def save_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--ids", help="Identificadores de casos separados por comas para una repetición focalizada")
    parser.add_argument("--input", type=Path, default=ROOT / "tests" / "fixtures" / "support_effectiveness_questions.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "support_effectiveness_20261014.json")
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 4:
        parser.error("--concurrency debe estar entre 1 y 4")

    cases = json.loads(args.input.read_text(encoding="utf-8"))
    if args.ids:
        requested_ids = {item.strip() for item in args.ids.split(",") if item.strip()}
        selected = [case for case in cases if case["id"] in requested_ids]
        if len(selected) != len(requested_ids):
            parser.error("--ids contiene un identificador inexistente")
    else:
        if not 1 <= args.limit <= len(cases):
            parser.error(f"--limit debe estar entre 1 y {len(cases)}")
        selected = cases[:args.limit]
    run_id = datetime.now().strftime("effectiveness_%Y%m%d_%H%M%S")
    report = {"run_id": run_id, "method": "RouterLogic real, sesiones aisladas; sin API, telemetría ni promoción a Golden Cache", "results": []}
    semaphore = asyncio.Semaphore(args.concurrency)

    async def evaluate(index: int, case: dict) -> dict:
        async with semaphore:
            started = time.perf_counter()
            try:
                result = await RouterLogic.procesar_mensaje(case["question"], session_id=f"{run_id}_{index}")
                return {
                    **case,
                    "answer": result.get("mensaje", ""),
                    "sources": result.get("sources") or [],
                    "route": result.get("tipo"),
                    "source": result.get("source"),
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "quality_verdict": None,
                    "quality_reason": None,
                }
            except Exception as exc:
                return {**case, "answer": "", "sources": [], "route": "ERROR", "error": str(exc),
                        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                        "quality_verdict": "incorrect", "quality_reason": "Falló la ejecución"}

    for offset in range(0, len(selected), args.concurrency):
        batch = await asyncio.gather(*(evaluate(offset + index, case) for index, case in enumerate(selected[offset:offset + args.concurrency])))
        report["results"].extend(batch)
        save_report(args.output, report)
        print(f"Evaluadas {len(report['results'])}/{len(selected)} preguntas", flush=True)
    print(args.output)


if __name__ == "__main__":
    asyncio.run(main())
