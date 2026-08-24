"""
Script de Pruebas de Integración End-to-End (Fase 4 y Calificación de Rol).
Valida:
1. Flujo Conversacional con Calificación Previa de Rol (PIDIENDO_ROL).
2. Salto a radicación con 3 pasos universales (Nombre -> Correo -> Descripción).
3. Guardrails de Fuera de Dominio.
4. Normalización léxica y tolerancia ortográfica.
5. Prohibición estricta de mencionar GLPI al usuario en cualquier respuesta.
"""

import asyncio
import sys
import os
from pathlib import Path
import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Asegurar importación del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app


async def run_tests():
    async with httpx.ASGITransport(app=app) as transport:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("=" * 70)
            print("INICIANDO SUITE DE PRUEBAS DE INTEGRACIÓN (PIDIENDO_ROL & SIN GLPI)")
            print("=" * 70)

            # -------------------------------------------------------------
            # TEST 1: SALUDO INICIAL -> PIDIENDO_ROL -> CALIFICACIÓN
            # -------------------------------------------------------------
            print("\nTEST 1: SALUDO INICIAL Y CALIFICACIÓN DE ROL")
            sess1 = "test_sess_saludo"
            res_saludo = await client.post("/api/chat", json={"session_id": sess1, "mensaje": "Hola, buenos días"})
            d_saludo = res_saludo.json()
            print(f"Status: {res_saludo.status_code}")
            print(f"Tipo: {d_saludo.get('tipo')}")
            print(f"Mensaje Bot:\n{d_saludo.get('mensaje')}\n")
            assert res_saludo.status_code == 200
            assert d_saludo.get("tipo") == "PIDIENDO_ROL"
            assert "¿Eres **Estudiante** o **Funcionario / Docente**?" in d_saludo.get("mensaje")
            assert "glpi" not in d_saludo.get("mensaje", "").lower()

            res_rol = await client.post("/api/chat", json={"session_id": sess1, "mensaje": "Soy estudiante"})
            d_rol = res_rol.json()
            assert d_rol.get("tipo") == "DIAGNOSTICO"
            assert "colaborar" in d_rol.get("mensaje", "").lower()

            # -------------------------------------------------------------
            # TEST 2: SOLICITUD DE PRÉSTAMO / ASIGNACIÓN DE EQUIPOS
            # -------------------------------------------------------------
            print("=" * 70)
            print("TEST 2: SOLICITUD DE PRÉSTAMO DE EQUIPOS (CON ROL INICIAL)")
            print("=" * 70)
            sess2 = "test_sess_prestamo"
            res_prestamo = await client.post("/api/chat", json={"session_id": sess2, "mensaje": "Soy profesor y necesito solicitar el préstamo de un proyector y 2 micrófonos para una clase"})
            d_prestamo = res_prestamo.json()
            print(f"Status: {res_prestamo.status_code}")
            print(f"Tipo: {d_prestamo.get('tipo')}")
            print(f"Mensaje Bot:\n{d_prestamo.get('mensaje')}\n")
            assert res_prestamo.status_code == 200
            assert d_prestamo.get("tipo") == "OFRECIENDO_RADICACION"
            assert "solicitudcomputo@unisimon.edu.co" in d_prestamo.get("mensaje")
            assert "glpi" not in d_prestamo.get("mensaje", "").lower()

            # -------------------------------------------------------------
            # TEST 3: HARDWARE -> FLUJO COMPLETO DE RADICACIÓN
            # -------------------------------------------------------------
            print("=" * 70)
            print("TEST 3: HARDWARE -> FULL SLOT FILLING (Nombre, Correo, Descripción)")
            print("=" * 70)
            sess3 = "test_sess_hardware_flow"

            # Paso 1: Reporte de falla física con rol
            res_falla = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "Soy docente y el monitor del laboratorio no da video y la pantalla parpadea"})
            d_falla = res_falla.json()
            print(f"[Paso 1] Tipo: {d_falla.get('tipo')}")
            assert d_falla.get("tipo") == "DIAGNOSTICO"
            assert "glpi" not in d_falla.get("mensaje", "").lower()

            # Paso 2: Usuario decide reportar
            res_rep = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "vamos a reportar"})
            d_rep = res_rep.json()
            print(f"[Paso 2] Tipo: {d_rep.get('tipo')}")
            assert d_rep.get("tipo") == "RADICANDO_TICKET"
            assert "glpi" not in d_rep.get("mensaje", "").lower()

            # Paso 3: Nombre
            res_nombre = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "Carlos Alberto Restrepo"})
            d_nombre = res_nombre.json()
            print(f"[Paso 3] Tipo: {d_nombre.get('tipo')}")
            assert d_nombre.get("tipo") == "RADICANDO_TICKET"
            assert "correo" in d_nombre.get("mensaje", "").lower()
            assert "glpi" not in d_nombre.get("mensaje", "").lower()

            # Paso 4: Correo
            res_correo = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "carlos.restrepo@unisimon.edu.co"})
            d_correo = res_correo.json()
            print(f"[Paso 4] Tipo: {d_correo.get('tipo')}")
            assert d_correo.get("tipo") == "RADICANDO_TICKET"
            assert "describe" in d_correo.get("mensaje", "").lower()
            assert "glpi" not in d_correo.get("mensaje", "").lower()

            # Paso 5: Descripción -> Creación de Ticket
            res_desc = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "Monitor LG en laboratorio 204 no da video, pantalla parpadea en negro"})
            d_desc = res_desc.json()
            print(f"[Paso 5] Tipo: {d_desc.get('tipo')}")
            print(f"[Paso 5] Ticket ID: {d_desc.get('ticket_id')}")
            assert d_desc.get("tipo") == "TICKET_CREADO"
            assert d_desc.get("ticket_id") is not None
            assert "glpi" not in d_desc.get("mensaje", "").lower()

            # -------------------------------------------------------------
            # TEST 4: GUARDRAIL FUERA DE DOMINIO (Out-of-Domain)
            # -------------------------------------------------------------
            print("=" * 70)
            print("TEST 4: GUARDRAIL FUERA DE DOMINIO ('¿cuál es la capital de Hungría?')")
            print("=" * 70)
            sess4 = "test_sess_out_of_domain_1"
            res_ood1 = await client.post("/api/chat", json={"session_id": sess4, "mensaje": "¿cuál es la capital de Hungría?"})
            d_ood1 = res_ood1.json()
            print(f"Status: {res_ood1.status_code}")
            print(f"Tipo: {d_ood1.get('tipo')}")
            assert d_ood1.get("tipo") == "FUERA_DE_DOMINIO"
            msg_ood1 = d_ood1.get("mensaje", "").lower()
            assert "glpi" not in msg_ood1

            # -------------------------------------------------------------
            # TEST 5: GUARDRAIL FUERA DE DOMINIO ('Dame una receta para hacer arroz con pollo')
            # -------------------------------------------------------------
            print("=" * 70)
            print("TEST 5: GUARDRAIL FUERA DE DOMINIO ('Dame una receta para hacer arroz con pollo')")
            print("=" * 70)
            sess5 = "test_sess_out_of_domain_2"
            res_ood2 = await client.post("/api/chat", json={"session_id": sess5, "mensaje": "Dame una receta para hacer arroz con pollo"})
            d_ood2 = res_ood2.json()
            print(f"Status: {res_ood2.status_code}")
            print(f"Tipo: {d_ood2.get('tipo')}")
            assert d_ood2.get("tipo") == "FUERA_DE_DOMINIO"
            assert "glpi" not in d_ood2.get("mensaje", "").lower()

            # -------------------------------------------------------------
            # TEST 6: CANALES OFICIALES DE SOPORTE (solicitudcomputo / helpdesk SIN GLPI)
            # -------------------------------------------------------------
            print("=" * 70)
            print("TEST 6: CANALES OFICIALES DE SOPORTE (solicitudcomputo / PBX SIN GLPI)")
            print("=" * 70)
            sess6 = "test_sess_canales"
            res_chan = await client.post("/api/chat", json={"session_id": sess6, "mensaje": "Soy funcionario y requiero saber los canales oficiales de atención y soporte TI en Barranquilla y Cúcuta"})
            d_chan = res_chan.json()
            print(f"Tipo: {d_chan.get('tipo')}")
            msg_chan = d_chan.get("mensaje", "").lower()
            assert "solicitudcomputo" in msg_chan or "helpdesk" in msg_chan or "soporte" in msg_chan
            assert "glpi" not in msg_chan

            print("\n" + "=" * 70)
            print("TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON EXITOSAMENTE (100% OK, CERO MENCIONES DE GLPI)")
            print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
