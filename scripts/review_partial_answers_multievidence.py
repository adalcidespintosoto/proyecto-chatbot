"""Re-review partial answers against the full final RAG context.

The baseline evaluator compared each response with one quote. This script
reconstructs current RAG final contexts for every partial case, asks the
configured OpenAI model to judge all returned evidence together, writes a
case-by-case report, and promotes only strict high-confidence verified cases
whose expected source was actually present in the reconstructed context.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.config import get_settings
from app.services.golden_cache_service import get_golden_collection, save_golden_case
from app.services.llm_client import LLMClient
from app.services.rag_service import RAGService


DEFAULT_INPUT = ROOT / "reports" / "indexed_documents_eval_20261006.json"
DEFAULT_OUTPUT = ROOT / "reports" / "partial_multievidence_review_20261006.json"
JUDGE_BATCH_SIZE = 4
JUDGE_CONCURRENCY = 3


def parse_json(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start = text.find("{")
    if start < 0:
        raise ValueError(f"El modelo no devolvió JSON: {text[:240]}")
    # Parse the first complete JSON object. Some model responses append a
    # short explanation or a second object after the requested strict JSON;
    # taking rfind('}') makes valid JSON fail with "Extra data".
    parsed, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(parsed, dict):
        raise ValueError("El modelo no devolvió un objeto JSON.")
    return parsed


def normalize_source(value: str) -> str:
    import unicodedata

    value = Path(str(value or "").replace("\\", "/")).name
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w]+", " ", value.casefold())
    return " ".join(value.split())


def expected_source_in_stage(row: dict[str, Any], stage: str) -> bool:
    target = normalize_source(row.get("source", ""))
    retrieval = row.get("review_retrieval") or {}
    return any(
        normalize_source(chunk.get("source", "")) == target
        for chunk in retrieval.get(stage, [])
    )


def answer_body(value: str) -> str:
    return re.split(r"\n\s*---\s*\n", value or "", maxsplit=1)[0].strip()


def atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def safe_clip_trace(trace: list[dict[str, Any]], stage: str, limit: int) -> list[dict[str, Any]]:
    event = next((item for item in trace if item.get("stage") == stage), {})
    chunks = event.get("chunks") or []
    result = []
    for chunk in chunks[:limit]:
        result.append({
            "source": str(chunk.get("source") or ""),
            "page": chunk.get("page"),
            "score": chunk.get("score"),
            "text": str(chunk.get("text") or "")[:1200],
        })
    return result


async def reconstruct_contexts(rows: list[dict[str, Any]], output: Path) -> None:
    service = RAGService()
    if service.vector_store is None:
        raise RuntimeError(f"No se pudo abrir el índice RAG: {service.chroma_db_dir}")
    print(
        f"Índice {service.vector_store._collection.name}: "
        f"{service.vector_store._collection.count()} chunks; reconstruyendo contexto de {len(rows)} casos.",
        flush=True,
    )

    for index, row in enumerate(rows, 1):
        trace: list[dict[str, Any]] = []
        llm_mock = AsyncMock(return_value={"content": "Revisión de contexto; respuesta omitida.", "model": "retrieval-audit"})
        # Keep the live MultiQuery expansion and retrieval pipeline. Stub only
        # the final answer generation because this phase captures its context.
        with patch.object(service.llm_client, "chat_completion", new=llm_mock):
            result = await service.query_rag(
                question=row["question"],
                user_role="general",
                trace_callback=trace.append,
            )

        final_chunks = safe_clip_trace(trace, "final_context", 100)
        expected = normalize_source(row.get("source", ""))
        final_sources = sorted({normalize_source(chunk["source"]) for chunk in final_chunks if chunk.get("source")})
        original_sources = row.get("sources") or []
        row["review_retrieval"] = {
            "retrieved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "collection": service.vector_store._collection.name,
            "query_expansion": "MultiQuery de producción; el fallback Ollama configurado puede activarse ante fallos",
            "candidate_chunks_top25": safe_clip_trace(trace, "candidates", 25),
            "reranked_chunks_top30": safe_clip_trace(trace, "reranked", 30),
            "final_chunks": final_chunks,
            "final_sources": final_sources,
            "expected_source_in_reconstructed_final_context": expected in final_sources,
            "expected_source_in_original_api_sources": any(
                normalize_source(source) == expected for source in original_sources
            ),
            "final_chunk_count": len(final_chunks),
            "final_context_tokens_estimate": sum((len(chunk["text"]) + 2) // 3 for chunk in final_chunks),
            "retrieval_error": None if trace else "No se recibió traza del pipeline RAG.",
        }

        if index % 5 == 0 or index == len(rows):
            print(f"Contextos reconstruidos: {index}/{len(rows)}", flush=True)
            checkpoint = json.loads(output.read_text(encoding="utf-8"))
            checkpoint["phase"] = "retrieval"
            checkpoint["results"] = rows
            atomic_write(output, checkpoint)


JUDGE_SYSTEM = """Eres un segundo auditor de calidad de respuestas RAG universitarias.
Evalúa la RESPUESTA YA GENERADA contra la pregunta y TODOS los fragmentos finales
que se muestran debajo. Los fragmentos pertenecen a varios documentos y páginas;
pueden complementarse. La cita y la respuesta de referencia son una ayuda y NO
son la única evidencia disponible ni necesariamente contienen todos los pasos.

Reglas:
- Usa los fragmentos finales como evidencia principal; el nombre de una fuente
  no prueba lo que dice su contenido.
- Correcta: contesta lo pedido con los datos/pasos necesarios, no contradice el
  contexto y sus afirmaciones materiales están respaldadas por uno o más fragmentos.
- Parcial: está en el tema, pero omite un dato/paso necesario o agrega una
  afirmación material que no está respaldada por el contexto.
- Incorrecta: contradice los documentos, resuelve otro trámite o inventa una
  instrucción importante que podría desviar al usuario.
- No verificable: el contexto no permite confirmar la respuesta ni juzgarla.
- No penalices empatía, formato, pie de ayuda ni un detalle adicional que sí esté
  respaldado por cualquiera de los fragmentos. No exijas coincidencia literal con
  la cita o la respuesta de referencia.
- Las políticas institucionales configuradas por la aplicación aparecen en un
  campo separado de los fragmentos. Úsalas solo para validar exactamente las
  reglas de aplicación que declaran (por ejemplo, una URL oficial); no las trates
  como contenido de un documento ni como respaldo de otros hechos.
- Separa si el fallo se debe a que falta evidencia en los fragmentos finales
  (recuperación/contexto) o a que el chatbot no usó evidencia que sí tenía.
- No declares una respuesta correcta solo porque suene razonable o porque el
  informe anterior la haya llamado parcial.

Devuelve un objeto JSON estricto con una entrada por id:
{"items":[{"id":"...","verdict":"correct|partial|incorrect|no_verificable",
"confidence":0.0,"reason":"breve en español",
"missing_required_details":["..."],"unsupported_material_claims":["..."],
"supporting_evidence":[{"source":"...","page":"...","claim":"..."}],
"retrieval_adequacy":"sufficient|partial|insufficient|irrelevant"}]}"""


async def judge_batch(batch: list[dict[str, Any]], llm: LLMClient, semaphore: asyncio.Semaphore) -> list[dict[str, Any]]:
    items = []
    for row in batch:
        retrieval = row.get("review_retrieval") or {}
        items.append({
            "id": row["case_id"],
            "question": row["question"],
            "original_chatbot_answer": answer_body(row.get("answer", "")),
            "original_expected_source": row.get("source"),
            "source_reported_by_original_api": row.get("sources", []),
            "original_single_quote_not_exhaustive": row.get("evidence_quote"),
            "reference_answer_not_exhaustive": row.get("reference_answer"),
            "applicable_configured_policies_not_document_chunks": row.get("applicable_configured_policies_for_judge", []),
            "reconstructed_final_chunks_sent_by_current_rag_pipeline": retrieval.get("final_chunks", []),
            "expected_source_in_reconstructed_final_context": retrieval.get("expected_source_in_reconstructed_final_context"),
        })
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": json.dumps({"cases": items}, ensure_ascii=False)},
    ]
    async with semaphore:
        # Call the configured OpenAI endpoint directly so an outage cannot
        # silently change the judge to the local fallback model.
        response = await llm._call_openai_chat(messages, max_tokens=3200)
    parsed = parse_json(response.get("content", ""))
    by_id = {str(item.get("id")): item for item in parsed.get("items", []) if isinstance(item, dict)}
    reviewed = []
    for row in batch:
        item = by_id.get(row["case_id"], {})
        verdict = item.get("verdict")
        if verdict not in {"correct", "partial", "incorrect", "no_verificable"}:
            verdict = "no_verificable"
        try:
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0))))
        except (TypeError, ValueError):
            confidence = 0.0
        retrieval = row.get("review_retrieval") or {}
        current_source_hit = bool(retrieval.get("expected_source_in_reconstructed_final_context"))
        if not current_source_hit:
            diagnosis = "fallo de recuperación: falta la fuente esperada en el contexto final reconstruido"
        elif verdict == "correct":
            diagnosis = "la respuesta pasa al revisar conjuntamente los fragmentos; el primer juez fue demasiado estricto o la cita aislada era incompleta"
        elif item.get("retrieval_adequacy") in {"partial", "insufficient", "irrelevant"}:
            diagnosis = "contexto recuperado incompleto o poco pertinente"
        else:
            diagnosis = "el contexto contiene evidencia suficiente; falla la respuesta o su uso de la evidencia"
        review = {
            "verdict": verdict,
            "confidence": confidence,
            "reason": str(item.get("reason") or "El segundo juez no entregó motivo."),
            "missing_required_details": item.get("missing_required_details") or [],
            "unsupported_material_claims": item.get("unsupported_material_claims") or [],
            "supporting_evidence": item.get("supporting_evidence") or [],
            "retrieval_adequacy": item.get("retrieval_adequacy") or "insufficient",
            "diagnosis": diagnosis,
            "judge_model": response.get("model") or "configured_openai",
        }
        row["multievidence_review"] = review
        reviewed.append(row)
    return reviewed


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    selected_verdicts = ", ".join(report.get("selected_baseline_verdicts", ["partial"]))
    projected = summary["projected_full_evaluation"]
    lines = [
        f"# Revisión multi-evidencia de respuestas — {report['run_id']}",
        "",
        f"- Casos con veredicto inicial ({selected_verdicts}) revisados: **{summary['reviewed']}**.",
        f"- Segunda revisión: **{summary['correct']} correctas**, **{summary['partial']} parciales**, **{summary['incorrect']} incorrectas**, **{summary['no_verificable']} no verificables**.",
        f"- Proyección compuesta al sustituir solo estos veredictos: **{projected['correct']}/{projected['total']} correctas ({projected['correct_percent']}%)**. Es una reevaluación, no una nueva ejecución completa.",
        f"- Fuente esperada presente en el contexto RAG reconstruido: **{summary['current_expected_source_hits']}/{summary['reviewed']}**.",
        f"- Recorrido de la fuente esperada: candidatos top 25 **{summary['candidate_source_hits_top25']}/{summary['reviewed']}**, reranking top 30 **{summary['reranked_source_hits_top30']}/{summary['reviewed']}**, contexto final **{summary['current_expected_source_hits']}/{summary['reviewed']}**.",
        f"- Entre las respuestas que siguen sin estar correctas, la fuente se perdió entre reranking y presupuesto en **{summary['partial_dropped_after_reranking']}**, no llegó al top 30 rerankeado en **{summary['partial_dropped_by_reranker']}**, y no apareció en los 25 candidatos en **{summary['partial_absent_from_candidate_top25']}**.",
        f"- Correctas con fuente esperada presente: **{summary['correct_with_expected_source']}**; correctas sustentadas por otros documentos complementarios aunque faltó la fuente esperada: **{summary['correct_without_expected_source']}**.",
        f"- Parciales con fuente esperada presente: **{summary['partial_with_expected_source']}**; parciales sin esa fuente: **{summary['partial_without_expected_source']}**.",
        f"- Golden Cache: **{summary['golden_saved']}** guardadas (sin afirmaciones materiales no respaldadas); colección antes/después: **{summary['golden_cache_before']} → {summary['golden_cache_after']}**.",
        f"- Expansión MultiQuery: se observaron **{report.get('multiquery_fallbacks_observed', 'no registrado')}** fallback(s) a Ollama durante la reconstrucción de contexto.",
        "",
        "> Esta es una segunda evaluación automática contra la traza de contexto RAG reconstruida en la fecha del informe; no es una validación humana ni conserva el prompt exacto de la corrida original.",
        "",
        "## Casos revisados",
        "",
        "| ID | Documento esperado | Pregunta | Original | Revisión multi-evidencia | Fuente actual | Diagnóstico | Motivo |",
        "|---|---|---|---|---|---:|---|---|",
    ]
    def cell(value: Any) -> str:
        text = str(value or "").replace("\n", " ").replace("|", "\\|")
        return re.sub(r"\s+", " ", text).strip()
    for row in report["results"]:
        review = row.get("multievidence_review") or {}
        retrieval = row.get("review_retrieval") or {}
        lines.append(
            f"| {cell(row.get('case_id'))} | {cell(row.get('source'))} | {cell(row.get('question'))} | "
            f"{cell((row.get('quality_review') or {}).get('verdict'))} | {cell(review.get('verdict'))} "
            f"({review.get('confidence', 0):.2f}) | {'sí' if retrieval.get('expected_source_in_reconstructed_final_context') else 'no'} | "
            f"{cell(review.get('diagnosis'))} | {cell(review.get('reason'))} |"
        )
        answer = answer_body(row.get("answer", ""))
        lines.append(f"|  |  | **Respuesta original:** {cell(answer)[:1400]} |  |  |  |  |  |")
        chunks = retrieval.get("final_chunks") or []
        for chunk in chunks:
            lines.append(
                f"|  |  | **Evidencia:** {cell(chunk.get('source'))}, pág. {cell(chunk.get('page'))}: "
                f"{cell(chunk.get('text'))[:650]} |  |  |  |  |  |"
            )
    lines.extend([
        "",
        "## Limitaciones",
        "",
        "- El evaluador inicial guardó una cita literal por pregunta, no la totalidad de los chunks usados en esa respuesta.",
        "- La traza original completa no estaba guardada; los contextos aquí se reconstruyeron con el índice y el pipeline actuales, incluyendo MultiQuery.",
        "- El segundo juez es automático. Las respuestas correctas con alta confianza se guardaron en Golden Cache solo si la fuente esperada también apareció en el contexto final y la cita inicial estaba verificada en el índice.",
        "- Los fallos de recuperación se cuentan aparte de la corrección factual de la respuesta.",
        "",
    ])
    return "\n".join(lines)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--skip-golden-cache", action="store_true")
    parser.add_argument(
        "--verdict", action="append", choices=["correct", "partial", "incorrect", "no_verificable"],
        help="Veredicto inicial que se desea auditar; se puede repetir. Predeterminado: partial.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limita el piloto a los primeros N casos seleccionados.")
    args = parser.parse_args()

    settings = get_settings()
    if settings.llm_provider.casefold() != "openai" or not settings.openai_api_key:
        raise RuntimeError("La revisión multi-evidencia necesita el proveedor OpenAI configurado.")
    baseline = json.loads(args.input.read_text(encoding="utf-8"))
    selected_verdicts = sorted(set(args.verdict or ["partial"]))
    rows = [
        row for row in baseline.get("results", [])
        if (row.get("quality_review") or {}).get("verdict") in selected_verdicts
    ]
    if args.limit > 0:
        rows = rows[:args.limit]
    if not rows:
        raise RuntimeError(f"No hay casos con los veredictos iniciales seleccionados: {selected_verdicts}.")

    output: dict[str, Any] = {
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "baseline_run_id": baseline.get("run_id"),
        "review_method": "Current RAG final context reconstruction + multi-evidence OpenAI judge",
        "selected_baseline_verdicts": selected_verdicts,
        "configured_model": settings.openai_model,
        "chroma_dir": str(Path(settings.chroma_db_dir)),
        "golden_cache_before": get_golden_collection().count(),
        "results": rows,
        "summary": {},
    }
    atomic_write(args.output, output)
    llm_logger = logging.getLogger("unimon.llm_client")

    class FallbackCapture(logging.Handler):
        def __init__(self) -> None:
            super().__init__(level=logging.WARNING)
            self.count = 0

        def emit(self, record: logging.LogRecord) -> None:
            if "contingencia ollama" in record.getMessage().casefold():
                self.count += 1

    fallback_capture = FallbackCapture()
    llm_logger.addHandler(fallback_capture)
    try:
        await reconstruct_contexts(rows, args.output)
    finally:
        llm_logger.removeHandler(fallback_capture)
    output["multiquery_fallbacks_observed"] = fallback_capture.count

    llm = LLMClient()
    semaphore = asyncio.Semaphore(JUDGE_CONCURRENCY)
    batches = [rows[i : i + JUDGE_BATCH_SIZE] for i in range(0, len(rows), JUDGE_BATCH_SIZE)]
    for batch_number, batch in enumerate(batches, 1):
        try:
            await judge_batch(batch, llm, semaphore)
        except Exception as exc:
            for row in batch:
                row["multievidence_review"] = {
                    "verdict": "no_verificable",
                    "confidence": 0.0,
                    "reason": f"No se pudo completar la segunda revisión: {type(exc).__name__}: {exc}",
                    "missing_required_details": [],
                    "unsupported_material_claims": [],
                    "supporting_evidence": [],
                    "retrieval_adequacy": "insufficient",
                    "diagnosis": "juez automático no disponible",
                }
        if batch_number % 5 == 0 or batch_number == len(batches):
            print(f"Lotes revisados por multi-evidencia: {batch_number}/{len(batches)}", flush=True)
            atomic_write(args.output, output)

    golden_saved = 0
    if not args.skip_golden_cache:
        for row in rows:
            review = row.get("multievidence_review") or {}
            retrieval = row.get("review_retrieval") or {}
            eligible = (
                review.get("verdict") == "correct"
                and float(review.get("confidence", 0)) >= 0.98
                and not review.get("unsupported_material_claims")
                and retrieval.get("expected_source_in_reconstructed_final_context") is True
                and row.get("evidence_valid") is True
                and bool(answer_body(row.get("answer", "")))
            )
            row["golden_cache_eligible_after_multievidence_review"] = eligible
            row["golden_cache_saved_after_multievidence_review"] = False
            if eligible:
                saved = save_golden_case(
                    session_id=f"partial-multievidence-{output['run_id']}-{row['case_id']}",
                    user_query=row["question"],
                    bot_response=answer_body(row.get("answer", "")),
                    role="general",
                )
                row["golden_cache_saved_after_multievidence_review"] = bool(saved)
                golden_saved += int(bool(saved))

    verdicts = Counter((row.get("multievidence_review") or {}).get("verdict", "no_verificable") for row in rows)
    current_source_hits = sum(
        bool((row.get("review_retrieval") or {}).get("expected_source_in_reconstructed_final_context"))
        for row in rows
    )
    remaining_not_correct = [row for row in rows if row["multievidence_review"]["verdict"] != "correct"]
    projected_verdicts = {
        row.get("case_id"): (row.get("quality_review") or {}).get("verdict")
        for row in baseline.get("results", [])
    }
    for row in rows:
        projected_verdicts[row.get("case_id")] = row["multievidence_review"]["verdict"]
    projected_counts = Counter(projected_verdicts.values())
    projected_total = len(projected_verdicts)
    output["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    output["golden_saved"] = golden_saved
    output["golden_cache_after"] = get_golden_collection().count()
    output["summary"] = {
        "reviewed": len(rows),
        "baseline_selected": len(rows),
        "correct": verdicts["correct"],
        "partial": verdicts["partial"],
        "incorrect": verdicts["incorrect"],
        "no_verificable": verdicts["no_verificable"],
        "current_expected_source_hits": current_source_hits,
        "candidate_source_hits_top25": sum(expected_source_in_stage(row, "candidate_chunks_top25") for row in rows),
        "reranked_source_hits_top30": sum(expected_source_in_stage(row, "reranked_chunks_top30") for row in rows),
        "partial_dropped_after_reranking": sum(
            expected_source_in_stage(row, "candidate_chunks_top25")
            and expected_source_in_stage(row, "reranked_chunks_top30")
            and not expected_source_in_stage(row, "final_chunks")
            for row in remaining_not_correct
        ),
        "partial_dropped_by_reranker": sum(
            expected_source_in_stage(row, "candidate_chunks_top25")
            and not expected_source_in_stage(row, "reranked_chunks_top30")
            and not expected_source_in_stage(row, "final_chunks")
            for row in remaining_not_correct
        ),
        "partial_absent_from_candidate_top25": sum(
            not expected_source_in_stage(row, "candidate_chunks_top25")
            and not expected_source_in_stage(row, "reranked_chunks_top30")
            and not expected_source_in_stage(row, "final_chunks")
            for row in remaining_not_correct
        ),
        "correct_with_expected_source": sum(
            row["multievidence_review"]["verdict"] == "correct"
            and row["review_retrieval"]["expected_source_in_reconstructed_final_context"]
            for row in rows
        ),
        "correct_without_expected_source": sum(
            row["multievidence_review"]["verdict"] == "correct"
            and not row["review_retrieval"]["expected_source_in_reconstructed_final_context"]
            for row in rows
        ),
        "partial_with_expected_source": sum(
            row["multievidence_review"]["verdict"] == "partial"
            and row["review_retrieval"]["expected_source_in_reconstructed_final_context"]
            for row in rows
        ),
        "partial_without_expected_source": sum(
            row["multievidence_review"]["verdict"] == "partial"
            and not row["review_retrieval"]["expected_source_in_reconstructed_final_context"]
            for row in rows
        ),
        "golden_saved": golden_saved,
        "golden_cache_before": output["golden_cache_before"],
        "golden_cache_after": output["golden_cache_after"],
        "projected_full_evaluation": {
            "correct": projected_counts["correct"],
            "partial": projected_counts["partial"],
            "incorrect": projected_counts["incorrect"],
            "no_verificable": projected_counts["no_verificable"],
            "total": projected_total,
            "correct_percent": round(projected_counts["correct"] * 100 / projected_total, 1) if projected_total else 0.0,
        },
        "diagnoses": dict(Counter((row.get("multievidence_review") or {}).get("diagnosis", "sin diagnóstico") for row in rows)),
    }
    atomic_write(args.output, output)
    markdown = args.output.with_suffix(".md")
    markdown.write_text(markdown_report(output), encoding="utf-8")
    print(json.dumps({"summary": output["summary"], "json": str(args.output), "markdown": str(markdown)}, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
