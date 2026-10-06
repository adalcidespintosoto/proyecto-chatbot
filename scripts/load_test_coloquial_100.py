"""Continuous ten-at-a-time test using 100 colloquial, document-grounded questions."""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.load_test_chat import CASES as BASE_CASES, percentile, run_case, write_report

LEADS = [
    "Hola, soy estudiante y necesito una mano: ",
    "Buenas, soy docente y no encuentro cómo hacer esto: ",
    "Hola, trabajo en el área administrativa y quisiera saber: ",
    "Profe por acá, ¿me orientas con esto?: ",
    "Hola, estoy haciendo este trámite y me enredé un poco: ",
    "Buenas, ¿me ayudas? No tengo claro lo siguiente: ",
    "Soy estudiante y es la primera vez que hago esto: ",
    "Hola, estoy apoyando este proceso y tengo una duda: ",
    "Disculpa, ¿me explicas de forma sencilla cómo se hace esto?: ",
    "Buenas, me quedé atascado con este trámite: ",
]

def make_cases():
    cases = []
    for i, (case_id, category, question, source) in enumerate(BASE_CASES):
        lead = LEADS[i % len(LEADS)]
        # Preserve evidence-seeking intent while phrasing it as a normal help request.
        colloquial = lead + question[0].lower() + question[1:]
        cases.append((f"coloquial_{case_id}", category, colloquial, source))
    return cases

CASES = make_cases()

async def run_batch(batch, offset, client, base_url, run_id, timeout):
    gate = asyncio.Event()
    tasks = [asyncio.create_task(run_case(offset + j, case, base_url, gate, client, run_id)) for j, case in enumerate(batch)]
    await asyncio.sleep(0.05)
    gate.set()
    return await asyncio.gather(*tasks)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "coloquial_100_20261005.json")
    parser.add_argument("--timeout", type=float, default=240)
    args = parser.parse_args()
    normalized = [" ".join(c[2].casefold().split()) for c in CASES]
    if len(CASES) != 100 or len(set(normalized)) != 100:
        raise RuntimeError(f"Se requieren 100 preguntas únicas; hay {len(set(normalized))} únicas.")
    run_id = datetime.now().strftime("coloquial-%Y%m%d-%H%M%S")
    limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    timeout = httpx.Timeout(args.timeout, connect=10)
    results = []
    started = time.perf_counter()
    async with httpx.AsyncClient(limits=limits, timeout=timeout, trust_env=False) as client:
        for batch_start in range(0, 100, 10):
            wave = time.perf_counter()
            rows = await run_batch(CASES[batch_start:batch_start+10], batch_start, client, args.base_url, run_id, timeout)
            results.extend(rows)
            print(json.dumps({"batch": batch_start // 10 + 1, "success": sum(r["ok"] for r in rows), "of": 10, "seconds": round(time.perf_counter()-wave, 1)}, ensure_ascii=False), flush=True)
    wall = time.perf_counter() - started
    latencies = [r["latency_ms"] for r in results]
    checked = [r for r in results if r["expected_source_found"] is not None]
    report = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_url": args.base_url,
        "load_shape": "10 sequential waves of 10 concurrent independent sessions; 100 distinct client IP headers",
        "summary": {
            "users": len(results), "successes": sum(r["ok"] for r in results), "failures": sum(not r["ok"] for r in results),
            "http_429": sum(r["http_status"] == 429 for r in results),
            "http_5xx": sum(r["http_status"] is not None and r["http_status"] >= 500 for r in results),
            "expected_source_hits": sum(r["expected_source_found"] is True for r in checked), "source_checks": len(checked),
            "wall_time_s": round(wall, 2), "p50_ms": round(percentile(latencies,50) or 0,1),
            "p95_ms": round(percentile(latencies,95) or 0,1), "max_ms": round(max(latencies,default=0),1),
            "requests_per_second": round(len(results)/wall,2) if wall else 0,
        }, "results": results,
    }
    write_report(report, args.output)
    md_path = args.output.with_suffix(".md")
    rendered = md_path.read_text(encoding="utf-8")
    rendered = rendered.replace(
        f"- Usuarios simulados simultáneos: **{len(results)}**",
        f"- Sesiones probadas: **{len(results)}** (10 tandas secuenciales de 10 concurrentes)",
    ).replace(
        f"Las {len(results)} preguntas comenzaron juntas en sesiones independientes.",
        f"Las {len(results)} preguntas se ejecutaron en 10 tandas secuenciales, con 10 sesiones independientes concurrentes por tanda.",
    )
    md_path.write_text(rendered, encoding="utf-8")
    print(json.dumps({"summary":report["summary"],"json":str(args.output),"markdown":str(args.output.with_suffix('.md'))},ensure_ascii=False,indent=2))

if __name__ == "__main__":
    asyncio.run(main())
