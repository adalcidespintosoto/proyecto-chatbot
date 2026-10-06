"""LLM-evaluate the 100 responses against retrieved source-document evidence and cache only verified answers."""
import asyncio, json, re, sys, unicodedata
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from app.services.rag_service import RAGService
from app.services.llm_client import LLMClient
from app.services.golden_cache_service import get_golden_collection, save_golden_case

inp=ROOT/"reports/coloquial_100_20261005.json"
out=ROOT/"reports/coloquial_100_20261005_judged.json"
report=json.loads(inp.read_text(encoding="utf-8"))
rag=RAGService(); llm=LLMClient()
if rag.vector_store is None: raise RuntimeError("No se pudo abrir el índice RAG")

def clean_answer(s):
    return re.split(r"\n\s*---\s*\n",s or "",maxsplit=1)[0].strip()

def source_evidence(item):
    names=[]
    for n in [item.get("expected_source"),*(item.get("sources") or [])]:
        if n and n not in names: names.append(n)
    chunks=[]
    for name in names[:4]:
        try:
            docs=rag.vector_store.similarity_search(item["question"],k=2,filter={"source":name})
        except Exception:
            docs=[]
        for d in docs:
            text=" ".join(d.page_content.split())[:850]
            chunks.append(f"[{d.metadata.get('source',name)} p.{d.metadata.get('page_number',d.metadata.get('slide_number','?'))}] {text}")
    return "\n".join(chunks)[:3800]

def chunks(seq,n):
    for i in range(0,len(seq),n): yield seq[i:i+n]

for start in range(0,len(report["results"]),10):
    batch=report["results"][start:start+10]
    items=[]
    for row in batch:
        items.append({"id":row["user"],"question":row["question"],"expected_source":row["expected_source"],"api_sources":row.get("sources",[]),"answer":clean_answer(row.get("answer","")),"evidence":source_evidence(row)})
    system=("Eres auditor de calidad de un asistente universitario de soporte de primer nivel. Evalúa cada respuesta SOLO contra la evidencia documental adjunta. "
      "Correcta = resuelve la petición principal con pasos/datos suficientes y sin afirmaciones no respaldadas; parcial = útil pero incompleta; incorrecta = contradice, responde otro rol/trámite o alucina; no_verificable = falta evidencia. "
      "No marques incorrecta solo por estilo. Da confianza 0..1 y razón breve en español. Devuelve JSON estricto: {\"items\":[{\"id\":n,\"verdict\":\"correct|partial|incorrect|no_verificable\",\"confidence\":0.0,\"reason\":\"...\"}]}.")
    user=json.dumps(items,ensure_ascii=False)
    response=asyncio.run(llm._call_openai_chat([{"role":"system","content":system},{"role":"user","content":user}],max_tokens=1800))
    raw=response.get("content","")
    m=re.search(r"\{[\s\S]*\}",raw)
    if not m: raise RuntimeError(f"Juez devolvió JSON inválido en lote {start//10+1}: {raw[:300]}")
    judged=json.loads(m.group())
    by_id={int(x["id"]):x for x in judged.get("items",[])}
    for row in batch:
        j=by_id.get(row["user"],{"verdict":"no_verificable","confidence":0,"reason":"El juez no devolvió este caso"})
        row["quality_review"]=j
    print(f"Evaluados {min(start+10,len(report['results']))}/100",flush=True)

# Store only grounded, high-confidence correct answers. Treat this judge validation as explicit QA,
# but preserve the application's own cache admissibility checks and real inferred session role.
import sqlite3
db=sqlite3.connect(ROOT/"data/analytics.db")
roles={sid:role for sid,role in db.execute("SELECT session_id,role FROM telemetry_sessions WHERE session_id LIKE 'load100-coloquial-%'")}
from app.services.golden_cache_service import is_valid_for_golden_cache
collection=get_golden_collection(); before=collection.count(); saved=[]
for row in report["results"]:
    j=row.get("quality_review",{})
    answer=clean_answer(row.get("answer",""))
    role=roles.get(row["session_id"]) or "general"
    row["inferred_role"]=role
    row["golden_cache_saved"]=False
    if j.get("verdict")=="correct" and float(j.get("confidence",0))>=0.95 and row.get("expected_source_found") is True and is_valid_for_golden_cache(row["question"],answer):
        row["golden_cache_saved"]=bool(save_golden_case(row["session_id"],row["question"],answer,role=role))
        if row["golden_cache_saved"]: saved.append(row["user"])
after=collection.count()
report["golden_cache"]={"before":before,"after":after,"saved_count":len(saved),"saved_case_numbers":saved,"policy":"solo veredicto correcta, confianza >=0.95, evidencia consultada y validadores internos aprobados"}
counts={v:sum(r.get("quality_review",{}).get("verdict")==v for r in report["results"]) for v in ["correct","partial","incorrect","no_verificable"]}
report["quality_summary"]=counts
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"quality":counts,"cache":report["golden_cache"],"report":str(out)},ensure_ascii=False,indent=2))
