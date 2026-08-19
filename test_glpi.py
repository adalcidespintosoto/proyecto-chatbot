import asyncio
import json
import httpx

async def test_chat():
    payload = {
        "message": "Falla de prueba: No funciona el punto de red cableada en laboratorio 103 de Sartenejas",
        "user_data": {
            "name": "Prueba USB",
            "email": "18-00000@usb.ve",
            "usb_id": "18-00000",
            "campus": "Sartenejas",
            "role": "Estudiante"
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
