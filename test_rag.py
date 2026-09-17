import asyncio
import sys
import logging
from app.services.rag_service import rag_service

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def main():
    res = await rag_service.query_rag(
        'se me olvido la contraseña de mi correo',
        user_role='estudiante'
    )
    print("HAS CONTEXT:", res.get("has_context"))
    print("SOURCE:", res.get("source"))
    print("MODEL:", res.get("model"))
    print("CHUNKS:", res.get("retrieved_chunks"))
    print("RESPONSE:")
    sys.stdout.buffer.write(res.get("response", "").encode('utf-8'))

if __name__ == "__main__":
    asyncio.run(main())
