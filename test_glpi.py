import asyncio
import json
import httpx

async def test_chat():
    payload = {
        "message": "Falla de prueba: No enciende el equipo del laboratorio 204 en la sede Barranquilla",
        "user_data": {
            "name": "Docente Unisimon",
            "email": "docente@unisimon.edu.co",
            "usb_id": "1042500000",
            "campus": "Barranquilla",
            "role": "Docente"
        },
        "force_ticket": True
    }
    async with httpx.AsyncClient() as client:
        res = await client.post("http://localhost:8000/api/chat", json=payload, timeout=20.0)
        print("Status Code:", res.status_code)
        data = res.json()
        print("Intent:", data.get("intent"))
        print("Ticket Details:", data.get("ticket_details"))
        print("Category:", data.get("category"))
        print("Source:", data.get("source"))

if __name__ == "__main__":
    asyncio.run(test_chat())

