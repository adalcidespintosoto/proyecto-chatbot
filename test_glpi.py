import asyncio
import sys
import httpx

# Asegurar stdout utf-8 en Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def test_conversational_state_machine():
    base_url = "http://localhost:8000/api/chat"

    print("=" * 70)
    print("TEST 0: SALUDO PURO Y CORTESÍA (GREETING)")
    print("=" * 70)
    session_0 = "test_session_greeting"
    msg_greet = {"session_id": session_0, "message": "¡Hola! Buenos días, ¿cómo estás?"}
    async with httpx.AsyncClient() as client:
        res0 = await client.post(base_url, json=msg_greet, timeout=10.0)
        data0 = res0.json()
        print("Mensaje:", msg_greet["message"])
        print("Respuesta Bot:\n", data0.get("reply"))
        print("Intent:", data0.get("intent"))
        print("Source:", data0.get("source"))

    print("\n" + "=" * 70)
    print("TEST 1: FLUJO CONVERSACIONAL EN PASOS (Falla -> Datos de Contacto)")
    print("=" * 70)
    session_1 = "test_session_flow_1"

    # Paso 1: Usuario describe la falla
    msg_1 = {"session_id": session_1, "message": "El computador del laboratorio 102 no enciende y huele a quemado"}
    async with httpx.AsyncClient() as client:
        res1 = await client.post(base_url, json=msg_1, timeout=20.0)
        data1 = res1.json()
        print("[Paso 1] Mensaje:", msg_1["message"])
        print("[Paso 1] Respuesta Bot:\n", data1.get("reply"))
        print("[Paso 1] Intent:", data1.get("intent"))
        print("[Paso 1] Ticket:", data1.get("ticket_details"))

    # Paso 2: Usuario responde con su nombre y correo
    msg_2 = {"session_id": session_1, "message": "Soy Carlos Perez y mi correo es carlos.perez@unisimon.edu.co"}
    async with httpx.AsyncClient() as client:
        res2 = await client.post(base_url, json=msg_2, timeout=20.0)
        data2 = res2.json()
        print("\n[Paso 2] Mensaje:", msg_2["message"])
        print("[Paso 2] Respuesta Bot:\n", data2.get("reply"))
        print("[Paso 2] Ticket Details:", data2.get("ticket_details"))
        print("[Paso 2] Category:", data2.get("category"))

    print("\n" + "=" * 70)
    print("TEST 2: MENSAJE TODO EN UNO (Falla + Nombre + Correo en 1 solo mensaje)")
    print("=" * 70)
    session_2 = "test_session_all_in_one"
    msg_all = {
        "session_id": session_2,
        "message": "Soy Maria Gomez maria.gomez@unisimon.edu.co y el proyector de la sala 10 no enciende"
    }
    async with httpx.AsyncClient() as client:
        res3 = await client.post(base_url, json=msg_all, timeout=20.0)
        data3 = res3.json()
        print("Mensaje:", msg_all["message"])
        print("Respuesta Bot:\n", data3.get("reply"))
        print("Ticket Details:", data3.get("ticket_details"))


if __name__ == "__main__":
    asyncio.run(test_conversational_state_machine())



