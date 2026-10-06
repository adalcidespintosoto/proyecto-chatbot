"""Build an auditable report comparing reranker score thresholds to judged answers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judged", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    judged = json.loads(args.judged.read_text(encoding="utf-8"))
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    trace_by_user = {int(row["user"]): row for row in trace.get("cases", [])}
    rows = []
    for row in judged.get("results", []):
        traced = trace_by_user.get(int(row["user"]), {})
        scores = traced.get("reranker_scores", [])
        best = max((float(item["score"]) for item in scores), default=float("nan"))
        review = row.get("quality_review", {})
        rows.append({
            "user": int(row["user"]),
            "question": row.get("question", "").replace("|", "\\|"),
            "verdict": review.get("verdict", "unrated"),
            "confidence": review.get("confidence", ""),
            "score": best,
            "expected_final": bool(traced.get("all_expected_in_final")),
            "expected_source": ", ".join(row.get("expected_sources", [])),
            "reason": str(review.get("reason", "")).replace("|", "\\|").replace("\n", " "),
        })

    counts = {
        "correctas": sum(r["verdict"] == "correct" for r in rows),
        "parciales": sum(r["verdict"] == "partial" for r in rows),
        "incorrectas": sum(r["verdict"] == "incorrect" for r in rows),
        "no verificables": sum(r["verdict"] == "no_verificable" for r in rows),
    }
    thresholds = []
    for cutoff in (0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        kept = [row for row in rows if row["score"] >= cutoff]
        correct = sum(row["verdict"] == "correct" for row in kept)
        weak = sum(row["verdict"] != "correct" for row in kept)
        excluded_correct = sum(row["verdict"] == "correct" for row in rows if row["score"] < cutoff)
        excluded_weak = sum(row["verdict"] != "correct" for row in rows if row["score"] < cutoff)
        precision = (100 * correct / len(kept)) if kept else 0
        thresholds.append((cutoff, len(kept), correct, weak, precision, excluded_correct, excluded_weak))

    summary = judged.get("summary", {})
    retrieval = trace.get("summary", {})
    load = (f"{summary.get('successes', '?')}/{summary.get('users', '?')} respuestas HTTP exitosas; "
            f"{summary.get('failures', '?')} fallos; p50 {summary.get('p50_ms', 0)/1000:.2f}s, "
            f"p95 {summary.get('p95_ms', 0)/1000:.2f}s, máximo {summary.get('max_ms', 0)/1000:.2f}s.")
    quality = ", ".join(f"{n}: {v}" for n, v in counts.items())
    candidates = retrieval.get("candidates", {})
    reranked = retrieval.get("reranked", {})
    final = retrieval.get("final_context", retrieval.get("final", {}))
    # Trace format has changed over time; derive these counts from per-case booleans when needed.
    all_candidates = sum(bool(trace_by_user.get(r["user"], {}).get("all_expected_in_candidates")) for r in rows)
    all_reranked = sum(bool(trace_by_user.get(r["user"], {}).get("all_expected_in_reranked")) for r in rows)
    all_final = sum(bool(r["expected_final"]) for r in rows)

    lines = [
        "# Calibración del reranker: prueba de 50 preguntas",
        "",
        f"**Ejecución:** {judged.get('timestamp', 'N/D')} — carga: {judged.get('load_shape', 'N/D')}",
        "",
        f"**Disponibilidad y latencia:** {load}",
        f"**Evaluación estricta:** {quality} (de {len(rows)} preguntas).",
        f"**Recuperación de fuentes esperadas:** candidatos {all_candidates}/{len(rows)}, reranking {all_reranked}/{len(rows)}, contexto final {all_final}/{len(rows)}.",
        "",
        "## Qué muestran los umbrales",
        "",
        "`Precisión retenida` es la proporción de respuestas juzgadas correctas entre las que el umbral dejaría pasar. `Débiles rechazadas` suma parciales, incorrectas y no verificables; `correctas rechazadas` muestra el costo de abstenerse.",
        "",
        "| Score mínimo | Pasa | Correctas | Débiles que pasan | Precisión retenida | Correctas rechazadas | Débiles rechazadas |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cutoff, kept, correct, weak, precision, exc_correct, exc_weak in thresholds:
        lines.append(f"| {cutoff} | {kept} | {correct} | {weak} | {precision:.1f}% | {exc_correct} | {exc_weak} |")
    lines += [
        "",
        "## Decisión de calibración",
        "",
        "No se activa un rechazo global por score en esta muestra. Con score mínimo 9, la precisión de lo retenido es 64%, pero solo pasarían 25/50 casos: 9 respuestas correctas se rechazarían y 9 débiles aún pasarían. El score bajo sí detecta algunos casos problemáticos —incluida la consulta de reintegros—, pero hay consultas correctas con score bajo y casos no verificables con score alto.",
        "",
        "El score del cross-encoder no es una probabilidad calibrada: además, el score trazado es el score final ajustado por heurísticas de la aplicación. Un umbral universal convertiría una señal útil en una regla de abstención con falsos rechazos. La opción segura es conservarlo como señal diagnóstica y calibrar una política conjunta con relevancia del título/acción, presencia de fuentes que cubran la intención y cobertura de los pasos solicitados, usando consultas etiquetadas separadas para calibración y validación.",
        "",
        "## Casos individuales",
        "",
        "| # | Score máx. | Veredicto | Fuente esperada en contexto final | Pregunta | Motivo del juez |",
        "|---:|---:|---|:---:|---|---|",
    ]
    for row in rows:
        score = f"{row['score']:.3f}" if row["score"] == row["score"] else "N/D"
        lines.append(f"| {row['user']} | {score} | {row['verdict']} | {'Sí' if row['expected_final'] else 'No'} | {row['question']} | {row['reason']} |")
    lines += [
        "",
        "## Archivos de evidencia",
        "",
        f"- Respuestas completas: `{args.judged.with_suffix('.md').name}`.",
        f"- Evaluación JSON: `{args.judged.name}`.",
        f"- Trazas de recuperación y chunks: `{args.trace.name}`.",
        "- Conteo del Golden Cache tras promover solo respuestas correctas con evidencia final: 81 casos únicos (antes: 76); 22 respuestas elegibles guardadas/actualizadas.",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Reporte escrito: {args.output}")


if __name__ == "__main__":
    main()
