"""Review each 50-case response against indexed source evidence; this pass does not modify Golden Cache."""
import asyncio,json,re,sqlite3,sys
import argparse
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from app.services.rag_service import RAGService
from app.services.llm_client import LLMClient

parser=argparse.ArgumentParser()
parser.add_argument("--input",type=Path,default=ROOT/"reports/quality_50_20261006.json")
parser.add_argument("--output",type=Path,default=ROOT/"reports/quality_50_20261006_judged.json")
parser.add_argument("--trace",type=Path,default=None,help="Usa exactamente los chunks finales entregados al LLM en una traza RAG")
args=parser.parse_args()
source=args.input
out=args.output
report=json.loads(source.read_text(encoding="utf-8"));rag=RAGService();llm=LLMClient()
trace_by_user={}
if args.trace:
 trace_data=json.loads(args.trace.read_text(encoding="utf-8"))
 trace_by_user={int(row["user"]):row for row in trace_data.get("cases",[])}
def body(text):return re.split(r"\n\s*---\s*\n",text or "",maxsplit=1)[0].strip()

def evidence_for(row):
 trace_row=trace_by_user.get(int(row["user"]))
 if trace_row is not None:
  return "\n".join(
   f"[{chunk.get('source','')}, página/diapositiva {chunk.get('page','?')}] {' '.join(str(chunk.get('text','')).split())[:1100]}"
   for chunk in trace_row.get("final_chunks",[])
  )[:10000]
 names=[]
 for name in [*(row.get("expected_sources") or []),*(row.get("sources") or [])]:
  if name and name not in names:names.append(name)
 pieces=[]
 for name in names[:5]:
  try: docs=rag.vector_store.similarity_search(row["question"],k=2,filter={"source":name})
  except Exception:docs=[]
  for d in docs:
   meta=d.metadata or {};page=meta.get("page_number",meta.get("slide_number","?"))
   pieces.append(f"[{meta.get('source',name)}, página/diapositiva {page}] {' '.join(d.page_content.split())[:700]}")
 return "\n".join(pieces)[:4200]

async def main():
 conn=sqlite3.connect(ROOT/"data/analytics.db")
 roles={sid:role for sid,role in conn.execute("SELECT session_id,role FROM telemetry_sessions WHERE session_id LIKE 'load100-q50-%'")}
 for offset in range(0,len(report['results']),10):
  batch=report['results'][offset:offset+10];items=[]
  for row in batch:
   row['inferred_role']=roles.get(row['session_id']) or 'general'
   items.append({"id":row['user'],"question":row['question'],"intended_role":row.get('intended_role'),"inferred_role":row['inferred_role'],
    "expected_sources":row['expected_sources'],"api_sources":row.get('sources',[]),"answer":body(row.get('answer','')),"document_evidence":evidence_for(row)})
  system=("Eres auditor independiente de respuestas de un asistente de soporte universitario. Juzga cada respuesta SOLO con la evidencia documental adjunta. "
   "Correcta: responde lo que se pregunta, con pasos suficientes cuando pide procedimiento y sin afirmaciones/instrucciones importantes no respaldadas. Parcial: responde algo útil pero omite un paso/dato necesario. "
   "Incorrecta: contradice documentos, responde otro procedimiento/rol o inventa indicaciones relevantes. No verificable: los fragmentos no permiten confirmar la solución. No penalices solo estilo ni el footer. "
   "Si el rol inferido contradice el rol solicitado, indícalo. Emite JSON estricto {\"items\":[{\"id\":1,\"verdict\":\"correct|partial|incorrect|no_verificable\",\"confidence\":0.0,\"reason\":\"breve en español\"}]}.")
  messages=[{"role":"system","content":system},{"role":"user","content":json.dumps(items,ensure_ascii=False)}]
  response=await llm._call_openai_chat(messages,max_tokens=1500)
  raw=response.get('content','');match=re.search(r"\{[\s\S]*\}",raw)
  if not match:raise RuntimeError(f"Juez JSON inválido, lote {offset//10+1}: {raw[:300]}")
  judged=json.loads(match.group());byid={int(x['id']):x for x in judged['items']}
  for row in batch:row['quality_review']=byid.get(row['user'],{"verdict":"no_verificable","confidence":0,"reason":"Juez no devolvió caso"})
  print(f"Evaluadas {min(offset+10,50)}/50",flush=True)
 counts={v:sum(r.get('quality_review',{}).get('verdict')==v for r in report['results']) for v in ['correct','partial','incorrect','no_verificable']}
 report['quality_summary']=counts
 report['quality_definition']="Correcta solo si resuelve completamente lo pedido y está respaldada; no se guarda Golden Cache en esta evaluación preliminar."
 out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({"quality":counts,"correct_pct":round(100*counts['correct']/50,1),"report":str(out)},ensure_ascii=False,indent=2))
asyncio.run(main())
