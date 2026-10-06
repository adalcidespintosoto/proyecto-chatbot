"""Replay load cases through the real query expansion and RAG retrieval, capturing every context stage without answer generation."""
from __future__ import annotations
import argparse, asyncio, json, re, sys, time, unicodedata
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
from app.services import rag_service as rag_module
from app.services.rag_service import RAGService
from app.services.golden_cache_service import search_golden_case

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).casefold().strip()

def source_set(rows): return {norm(Path(str(x.get("source", ""))).name) for x in rows}

async def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,default=ROOT/"reports/coloquial_100_20261005_judged.json")
    ap.add_argument("--output",type=Path,default=ROOT/"reports/coloquial_100_20261005_trace.json")
    ap.add_argument("--reuse-variants",type=Path,default=None,help="Reproduce una traza usando expansiones previamente registradas, sin nuevas llamadas al generador de consultas")
    ap.add_argument("--concurrency",type=int,default=10)
    ap.add_argument("--disable-role-filter",action="store_true",help="Evaluación contrafactual: conserva filtros temáticos pero no filtra documentos por audience")
    args=ap.parse_args()
    original=json.loads(args.input.read_text(encoding="utf-8"))
    cached_variants={}
    if args.reuse_variants:
        previous=json.loads(args.reuse_variants.read_text(encoding="utf-8"))
        cached_variants={row["question"]:row.get("query_variants",[]) for row in previous["cases"]}
    service=RAGService()
    if service.vector_store is None: raise RuntimeError("No se pudo abrir la colección RAG")
    variant_map={}; prompt_map={}
    original_multi=rag_module.async_generate_multi_query_variants
    async def traced_multi(query,user_role="general",max_variants=3):
        if query in cached_variants:
            variant_map[query]=cached_variants[query]
            return cached_variants[query]
        variants=await original_multi(query,user_role,max_variants)
        variant_map[query]=variants
        return variants
    async def fake_answer(messages,**kwargs):
        user=next((m.get("content","") for m in reversed(messages) if m.get("role")=="user"),"")
        q=user.split("Consulta del usuario:",1)[-1].strip()
        prompt_map[q]=messages
        return {"content":"Respuesta suspendida para evaluación de recuperación.","model":"trace-no-generation"}
    sem=asyncio.Semaphore(args.concurrency)
    original_filter=service._build_query_filter
    async def one(row):
        async with sem:
            q=row["question"]
            role=row.get("inferred_role") or row.get("intended_role") or row.get("role") or "general"
            trace=[]
            started=time.perf_counter()
            golden=search_golden_case(q)
            golden_context=(
                f"Consulta similar validada para ampliar la búsqueda documental:\n{golden[0]}\n"
                if golden else ""
            )
            result=await service.query_rag(question=q,user_role=role,golden_context=golden_context,trace_callback=trace.append)
            elapsed=(time.perf_counter()-started)*1000
            stages={x["stage"]:x.get("chunks",[]) for x in trace}
            expected=row.get("expected_sources") or [row.get("expected_source")]
            # These onboarding questions are known to require complementary instructions.
            if not row.get("expected_sources") and ("credenciales_primiparo" in row.get("case_id","") or "credenciales_primer_semestre" in row.get("case_id","")):
                expected.append("GIE - ASPIRANTES NOV.2021.pptx")
            candidates=stages.get("candidates",[]); reranked=stages.get("reranked",[]); final=stages.get("final_context",[])
            outcome={**row,"role_used":role,"query_variants":variant_map.get(q,[]),
                "query_filter":service._build_query_filter(q,role),"candidates":candidates,"reranked":reranked,
                "final_chunks":final,"reranker_scores":stages.get("reranker_scores",[]),"expected_sources":expected,
                "candidate_source_hits":sorted(source_set(candidates)&{norm(x) for x in expected}),
                "reranked_source_hits":sorted(source_set(reranked)&{norm(x) for x in expected}),
                "final_source_hits":sorted(source_set(final)&{norm(x) for x in expected}),
                "all_expected_in_candidates":{norm(x) for x in expected}.issubset(source_set(candidates)),
                "all_expected_in_reranked":{norm(x) for x in expected}.issubset(source_set(reranked)),
                "all_expected_in_final":{norm(x) for x in expected}.issubset(source_set(final)),
                "final_context_tokens_est":sum((len(c.get("text", ""))+2)//3 for c in final),
                "latency_ms":round(elapsed,1),"rag_outcome_source":result.get("source"),
                "rag_has_context":result.get("has_context"),"llm_messages":prompt_map.get(q,[])}
            return outcome
    rows=[]; started=time.perf_counter()
    with patch("app.services.rag_service.async_generate_multi_query_variants",new=traced_multi), \
         patch.object(service.llm_client,"chat_completion",side_effect=fake_answer), \
         patch.object(service,"_build_query_filter",side_effect=(lambda question,user_role=None: original_filter(question,None) if args.disable_role_filter else original_filter(question,user_role))):
        for offset in range(0,len(original["results"]),args.concurrency):
            batch=original["results"][offset:offset+args.concurrency]
            rows.extend(await asyncio.gather(*(one(row) for row in batch)))
            print(f"Trazas {len(rows)}/{len(original['results'])}",flush=True)
    elapsed=time.perf_counter()-started
    summary={}
    for stage,key in [("candidates","all_expected_in_candidates"),("reranked","all_expected_in_reranked"),("final_context","all_expected_in_final")]:
        summary[stage]={"all_expected_present":sum(x[key] for x in rows),"cases":len(rows),"missing_case_numbers":[x["user"] for x in rows if not x[key]]}
    report={"generated_at":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"collection":service.vector_store._collection.name,
        "collection_count":service.vector_store._collection.count(),"concurrency":args.concurrency,
        "elapsed_seconds":round(elapsed,2),"document_audience_filter_applied":False,
        "query_filter_scope":"topic category only; user role/audience does not filter indexed documents",
        "generation":"answer LLM mocked; recorded/real multi-query variants, candidate retrieval, reranking and context packing executed",
        "summary":summary,"cases":rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"summary":summary,"elapsed_seconds":report["elapsed_seconds"],"output":str(args.output)},ensure_ascii=False,indent=2))

if __name__=="__main__": asyncio.run(main())
