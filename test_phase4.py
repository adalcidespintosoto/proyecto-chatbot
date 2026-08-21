import asyncio
import sys
import httpx
from httpx import ASGITransport

from app.main import app

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


async def run_tests():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # -------------------------------------------------------------
        # TEST 1: SALUDO INICIAL
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 1: SALUDO INICIAL (tipo == SALUDO)")
        print("=" * 70)
        sess1 = "test_sess_saludo"
        res = await client.post("/api/chat", json={"session_id": sess1, "mensaje": "¡Hola! Buenos días"})
        data = res.json()
        print(f"Status: {res.status_code}")
        print(f"Tipo: {data.get('tipo')}")
        print(f"Mensaje: {data.get('mensaje')}\n")
        assert data.get("tipo") == "SALUDO"

        # -------------------------------------------------------------
        # TEST 2: DIAGNÓSTICO NIVEL 1 Y RESOLUCIÓN EXITOSA
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 2: DIAGNÓSTICO NIVEL 1 -> CASO SOLUCIONADO")
        print("=" * 70)
        sess2 = "test_sess_resuelto"
        # Paso 1: Reporte
        res1 = await client.post("/api/chat", json={"session_id": sess2, "mensaje": "El monitor parpadea y se pone negro"})
        data1 = res1.json()
        print(f"[Paso 1] Tipo: {data1.get('tipo')}")
        print(f"[Paso 1] Mensaje Bot:\n{data1.get('mensaje')}\n")
        assert data1.get("tipo") == "DIAGNOSTICO"

        # Paso 2: Usuario confirma que se solucionó
        res2 = await client.post("/api/chat", json={"session_id": sess2, "mensaje": "Listo, ajusté el cable HDMI y ya funcionó, muchas gracias"})
        data2 = res2.json()
        print(f"[Paso 2] Tipo: {data2.get('tipo')}")
        print(f"[Paso 2] Mensaje Bot:\n{data2.get('mensaje')}\n")
        assert data2.get("tipo") == "SOLUCIONADO"

        # -------------------------------------------------------------
        # TEST 3: HARDWARE (Diagnóstico -> Persiste -> Nombre -> Correo -> Ubicación -> Placa -> Ticket)
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 3: HARDWARE -> FULL SLOT FILLING (Nombre, Correo, Ubicación, Placa)")
        print("=" * 70)
        sess3 = "test_sess_hardware_flow"

        # Paso 1: Reporte de falla física
        res_falla = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "El monitor del laboratorio no da video y la pantalla parpadea"})
        d_falla = res_falla.json()
        print(f"[Paso 1] Tipo: {d_falla.get('tipo')}")
        print(f"[Paso 1] Mensaje Bot:\n{d_falla.get('mensaje')}\n")
        assert d_falla.get("tipo") == "DIAGNOSTICO"

        # Paso 2: Falla persiste
        res_persist = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "No sirvió, sigue igual, no da video"})
        d_persist = res_persist.json()
        print(f"[Paso 2] Tipo: {d_persist.get('tipo')}")
        print(f"[Paso 2] Mensaje Bot:\n{d_persist.get('mensaje')}\n")
        assert d_persist.get("tipo") == "RADICANDO_TICKET"

        # Paso 3: Nombre
        res_nombre = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "Carlos Alberto Restrepo"})
        d_nombre = res_nombre.json()
        print(f"[Paso 3] Tipo: {d_nombre.get('tipo')}")
        print(f"[Paso 3] Mensaje Bot:\n{d_nombre.get('mensaje')}\n")
        assert d_nombre.get("tipo") == "RADICANDO_TICKET"

        # Paso 4: Correo
        res_correo = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "carlos.restrepo@unisimon.edu.co"})
        d_correo = res_correo.json()
        print(f"[Paso 4] Tipo: {d_correo.get('tipo')}")
        print(f"[Paso 4] Mensaje Bot:\n{d_correo.get('mensaje')}\n")
        assert d_correo.get("tipo") == "RADICANDO_TICKET"
        assert "ubicación" in d_correo.get("mensaje", "").lower() or "ubicacion" in d_correo.get("mensaje", "").lower()

        # Paso 5: Ubicación
        res_ubic = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "Sede Barranquilla, Bloque 3, Laboratorio 204"})
        d_ubic = res_ubic.json()
        print(f"[Paso 5] Tipo: {d_ubic.get('tipo')}")
        print(f"[Paso 5] Mensaje Bot:\n{d_ubic.get('mensaje')}\n")
        assert d_ubic.get("tipo") == "RADICANDO_TICKET"
        assert "placa" in d_ubic.get("mensaje", "").lower() or "activo" in d_ubic.get("mensaje", "").lower()

        # Paso 6: Placa / Activo -> Creación en GLPI
        res_activo = await client.post("/api/chat", json={"session_id": sess3, "mensaje": "ACT-USB-88421"})
        d_activo = res_activo.json()
        print(f"[Paso 6] Tipo: {d_activo.get('tipo')}")
        print(f"[Paso 6] Ticket ID: {d_activo.get('ticket_id')}")
        print(f"[Paso 6] Mensaje Bot:\n{d_activo.get('mensaje')}\n")
        assert d_activo.get("tipo") == "TICKET_CREADO"
        assert d_activo.get("ticket_id") is not None

        # -------------------------------------------------------------
        # TEST 4: SOFTWARE / CUENTAS (Diagnóstico -> Persiste -> Nombre -> Correo -> Ticket Inmediato)
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 4: SOFTWARE / CUENTAS -> DYNAMIC SHORT SLOTS (Solo Nombre y Correo)")
        print("=" * 70)
        sess4 = "test_sess_software_flow"

        # Paso 1: Reporte de software / contraseña
        res_sw = await client.post("/api/chat", json={"session_id": sess4, "mensaje": "No puedo ingresar a Kactus y mi contraseña aparece bloqueada"})
        d_sw = res_sw.json()
        print(f"[Paso 1] Tipo: {d_sw.get('tipo')}")
        print(f"[Paso 1] Mensaje Bot:\n{d_sw.get('mensaje')}\n")
        assert d_sw.get("tipo") == "DIAGNOSTICO"

        # Paso 2: Persiste
        res_sw_persist = await client.post("/api/chat", json={"session_id": sess4, "mensaje": "Sigue bloqueada, no me deja entrar"})
        d_sw_persist = res_sw_persist.json()
        print(f"[Paso 2] Tipo: {d_sw_persist.get('tipo')}")
        print(f"[Paso 2] Mensaje Bot:\n{d_sw_persist.get('mensaje')}\n")
        assert d_sw_persist.get("tipo") == "RADICANDO_TICKET"

        # Paso 3: Nombre
        res_sw_nom = await client.post("/api/chat", json={"session_id": sess4, "mensaje": "Ana Milena Rodriguez"})
        d_sw_nom = res_sw_nom.json()
        print(f"[Paso 3] Tipo: {d_sw_nom.get('tipo')}")
        print(f"[Paso 3] Mensaje Bot:\n{d_sw_nom.get('mensaje')}\n")
        assert d_sw_nom.get("tipo") == "RADICANDO_TICKET"

        # Paso 4: Correo -> Radicación Inmediata (NO debe pedir ubicación ni placa)
        res_sw_cor = await client.post("/api/chat", json={"session_id": sess4, "mensaje": "ana.rodriguez@unisimon.edu.co"})
        d_sw_cor = res_sw_cor.json()
        print(f"[Paso 4] Tipo: {d_sw_cor.get('tipo')}")
        print(f"[Paso 4] Ticket ID: {d_sw_cor.get('ticket_id')}")
        print(f"[Paso 4] Mensaje Bot:\n{d_sw_cor.get('mensaje')}\n")
        assert d_sw_cor.get("tipo") == "TICKET_CREADO"
        assert d_sw_cor.get("ticket_id") is not None
        assert "software" in d_sw_cor.get("mensaje", "").lower() or "cuentas" in d_sw_cor.get("mensaje", "").lower() or "radicado" in d_sw_cor.get("mensaje", "").lower()

        # -------------------------------------------------------------
        # TEST 5: GUARDRAIL FUERA DE DOMINIO (Out-of-Domain)
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 5: GUARDRAIL FUERA DE DOMINIO ('¿cuál es la capital de Hungría?')")
        print("=" * 70)
        sess5 = "test_sess_out_of_domain_1"
        res_ood1 = await client.post("/api/chat", json={"session_id": sess5, "mensaje": "¿cuál es la capital de Hungría?"})
        d_ood1 = res_ood1.json()
        print(f"Status: {res_ood1.status_code}")
        print(f"Tipo: {d_ood1.get('tipo')}")
        print(f"Mensaje Bot:\n{d_ood1.get('mensaje')}\n")
        assert d_ood1.get("tipo") == "FUERA_DE_DOMINIO"
        msg_ood1 = d_ood1.get("mensaje", "").lower()
        assert "exclusivamente en soporte" in msg_ood1 or "institucionales de la universidad simón bolívar" in msg_ood1 or "tema tecnológico o institucional" in msg_ood1
        # Verificar PROHIBICIÓN ESTRICTA: no mencionar GLPI ni pasos de descarte de hardware
        assert "glpi" not in msg_ood1
        assert "cable" not in msg_ood1
        assert "reinicia" not in msg_ood1

        # -------------------------------------------------------------
        # TEST 6: GUARDRAIL FUERA DE DOMINIO ('Dame una receta para hacer arroz con pollo')
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 6: GUARDRAIL FUERA DE DOMINIO ('Dame una receta para hacer arroz con pollo')")
        print("=" * 70)
        sess6 = "test_sess_out_of_domain_2"
        res_ood2 = await client.post("/api/chat", json={"session_id": sess6, "mensaje": "Dame una receta para hacer arroz con pollo"})
        d_ood2 = res_ood2.json()
        print(f"Status: {res_ood2.status_code}")
        print(f"Tipo: {d_ood2.get('tipo')}")
        print(f"Mensaje Bot:\n{d_ood2.get('mensaje')}\n")
        assert d_ood2.get("tipo") == "FUERA_DE_DOMINIO"
        assert "glpi" not in d_ood2.get("mensaje", "").lower()

        # -------------------------------------------------------------
        # TEST 7: TOLERANCIA ORTOGRÁFICA HARDWARE ('el proyestor no da video y la pantaya parpadea')
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 7: TOLERANCIA ORTOGRÁFICA HARDWARE ('proyestor' / 'pantaya')")
        print("=" * 70)
        sess7 = "test_sess_typo_hw"
        res_hw_typo = await client.post("/api/chat", json={"session_id": sess7, "mensaje": "el proyestor no da video y la pantaya parpadea"})
        d_hw_typo = res_hw_typo.json()
        print(f"Status: {res_hw_typo.status_code}")
        print(f"Tipo: {d_hw_typo.get('tipo')}")
        print(f"Mensaje Bot:\n{d_hw_typo.get('mensaje')}\n")
        assert d_hw_typo.get("tipo") == "DIAGNOSTICO"

        # -------------------------------------------------------------
        # TEST 8: TOLERANCIA ORTOGRÁFICA SOFTWARE ('no puedo entrar a katuc se me olvido la clabe')
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 8: TOLERANCIA ORTOGRÁFICA SOFTWARE ('katuc' / 'clabe')")
        print("=" * 70)
        sess8 = "test_sess_typo_sw"
        res_sw_typo = await client.post("/api/chat", json={"session_id": sess8, "mensaje": "no puedo entrar a katuc se me olvido la clabe"})
        d_sw_typo = res_sw_typo.json()
        print(f"Status: {res_sw_typo.status_code}")
        print(f"Tipo: {d_sw_typo.get('tipo')}")
        print(f"Mensaje Bot:\n{d_sw_typo.get('mensaje')}\n")
        assert d_sw_typo.get("tipo") == "DIAGNOSTICO"

        # -------------------------------------------------------------
        # TEST 9: CONTINUIDAD CONVERSACIONAL CON RESPUESTAS CORTAS ('si', 'dale', 'por favor')
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 9: CONTINUIDAD CONVERSACIONAL (Pregunta -> 'si' -> Pasos detallados)")
        print("=" * 70)
        sess9 = "test_sess_continuity"
        # Turno 1: Usuario consulta
        res_t1 = await client.post("/api/chat", json={"session_id": sess9, "mensaje": "no puedo entrar a katuc se me olvido la clabe"})
        d_t1 = res_t1.json()
        print(f"[Turno 1] Tipo: {d_t1.get('tipo')}")
        print(f"[Turno 1] Mensaje Bot:\n{d_t1.get('mensaje')}\n")
        assert d_t1.get("tipo") == "DIAGNOSTICO"

        # Turno 2: Usuario responde únicamente 'si'
        res_t2 = await client.post("/api/chat", json={"session_id": sess9, "mensaje": "si"})
        d_t2 = res_t2.json()
        print(f"[Turno 2] Tipo: {d_t2.get('tipo')}")
        print(f"[Turno 2] Mensaje Bot:\n{d_t2.get('mensaje')}\n")
        assert d_t2.get("tipo") == "DIAGNOSTICO"
        msg_t2 = d_t2.get("mensaje", "").lower()
        # Verificar que NO sea un rechazo ni respuesta vacía y mantenga la solución de contraseña/kactus
        assert len(msg_t2) > 30
        assert "contraseña" in msg_t2 or "contrasena" in msg_t2 or "kactus" in msg_t2 or "clave" in msg_t2 or "pasos" in msg_t2 or "portal" in msg_t2

        # -------------------------------------------------------------
        # TEST 10: CANALES OFICIALES DE SOPORTE (GLPI vs Compras/Activos Fijos)
        # -------------------------------------------------------------
        print("=" * 70)
        print("TEST 10: CANALES OFICIALES DE SOPORTE (GLPI / solicitudcomputo)")
        print("=" * 70)
        sess10 = "test_sess_channels"
        res_chan = await client.post("/api/chat", json={"session_id": sess10, "mensaje": "¿Dónde debo reportar si un computador de mi oficina se dañó?"})
        d_chan = res_chan.json()
        print(f"Status: {res_chan.status_code}")
        print(f"Tipo: {d_chan.get('tipo')}")
        print(f"Mensaje Bot:\n{d_chan.get('mensaje')}\n")
        assert d_chan.get("tipo") == "DIAGNOSTICO"
        msg_chan = d_chan.get("mensaje", "").lower()
        assert "glpi" in msg_chan or "solicitudcomputo" in msg_chan or "8003" in msg_chan or "helpdesk" in msg_chan
        assert "compras" not in msg_chan
        assert "activos fijos" not in msg_chan

        print("=" * 70)
        print("¡TODAS LAS PRUEBAS (SALUDO, SOLUCIÓN, HARDWARE, SOFTWARE, OUT-OF-DOMAIN, TYPOS, CONTINUIDAD Y CANALES) COMPLETADAS CON ÉXITO!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())


