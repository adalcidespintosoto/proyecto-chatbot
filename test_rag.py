"""
Script de prueba para el Motor RAG Local y endpoint /api/chat.
Verifica la recuperación de fragmentos desde ChromaDB y generación de respuesta con Ollama para Unisimon Colombia.
"""

import asyncio
import httpx
from app.services.rag_service import RAGService


async def test_rag_service():
    print("=" * 60)
    print("PROBANDO RAGSERVICE DIRECTO (UNISIMON COLOMBIA)")
    print("=" * 60)
    service = RAGService()
    
    question = "¿Cuáles son las políticas de generación y restauración de backups según el procedimiento P-GT-10?"
    print(f"Pregunta: {question}")
    result = await service.query_rag(question=question, user_name="Docente Unisimon")
    
    print("\n--- Respuesta del RAGService ---")
    print("Respuesta:\n", result.get("response"))
    print("\nFuentes:", result.get("sources"))
    print("Fuente:", result.get("source"))
    print("Modelo:", result.get("model"))
    print("Fragmentos recuperados:", result.get("retrieved_chunks"))


async def test_chat_endpoint():
    print("\n" + "=" * 60)
    print("PROBANDO ENDPOINT /api/chat CON CONSULTA INFORMATIVA")
    print("=" * 60)
    payload = {
        "message": "¿Cuáles son los canales oficiales de atención y soporte técnico de TI en Barranquilla y Cúcuta?",
        "user_data": {
            "name": "Prueba Unisimon",
            "email": "funcionario@unisimon.edu.co",
            "campus": "Barranquilla",
            "role": "Funcionario / Administrativo"
        },
        "force_ticket": False
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post("http://localhost:8000/api/chat", json=payload, timeout=30.0)
            print("Status Code:", res.status_code)
            data = res.json()
            print("Intent:", data.get("intent"))
            print("Reply:\n", data.get("reply"))
            print("Sources:", data.get("sources"))
            print("Category:", data.get("category"))
    except Exception as exc:
        print(f"Nota: Servidor uvicorn no está corriendo en localhost:8000 ({exc})")


async def main():
    await test_rag_service()
    await test_chat_endpoint()


if __name__ == "__main__":
    asyncio.run(main())

