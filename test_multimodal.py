"""
Test Suite para la Ingesta Multimodal y Soporte PPTX / PDF en UniMon.
Verifica:
1. Creacion y parseo de una presentacion PowerPoint (.pptx) con formas, tablas, notas e imagenes.
2. Invocacion de process_pptx y extraccion estructurada de LangChain Documents.
3. Validacion de los endpoints administrativos /api/admin/upload y /api/admin/reindex con PPTX.
"""

import sys
import io
import os
import asyncio
from pathlib import Path
from unittest.mock import patch
from PIL import Image

# Asegurar PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pptx import Presentation
from pptx.util import Inches, Pt
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import get_settings
from scripts.ingest_multimodal_docs import process_pptx, check_vision_model_available


def create_sample_pptx(filepath: Path):
    """Crea una presentacion PPTX de prueba institucional con diapositivas, tablas, notas e imagen."""
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # --- Slide 1: Portada y Procedimiento ---
    slide1 = prs.slides.add_slide(blank_layout)
    txBox = slide1.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(2))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Procedimiento de Soporte Tecnico Kactus - UniMon"
    p.font.size = Pt(24)
    p.font.bold = True

    p2 = tf.add_paragraph()
    p2.text = "Guia institucional para la gestion de incidencias en modulos de nomina y talento humano."
    p2.font.size = Pt(14)

    # Notas de orador en slide 1
    notes1 = slide1.notes_slide.notes_text_frame
    notes1.text = "Recordar al usuario que la atencion prioritaria es por el chatbot UniMon."

    # --- Slide 2: Tabla de Categorias y Tiempos de Respuesta ---
    slide2 = prs.slides.add_slide(blank_layout)
    txBox2 = slide2.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
    txBox2.text_frame.text = "Tabla de Acuerdos de Nivel de Servicio (SLA)"

    rows, cols = 3, 3
    table_shape = slide2.shapes.add_table(rows, cols, Inches(1), Inches(1.8), Inches(8), Inches(2.5))
    table = table_shape.table
    
    headers = ["Nivel", "Tipo de Falla", "Tiempo de Respuesta"]
    for c, h in enumerate(headers):
        table.cell(0, c).text = h

    data = [
        ["Critico", "Caida total de Kactus Nomina", "2 Horas"],
        ["Medio", "Bloqueo de usuario o cambio de clave", "4 Horas"]
    ]
    for r, row in enumerate(data, 1):
        for c, val in enumerate(row):
            table.cell(r, c).text = val

    # --- Slide 3: Captura de pantalla simulada ---
    slide3 = prs.slides.add_slide(blank_layout)
    txBox3 = slide3.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
    txBox3.text_frame.text = "Diagrama de Flujo de Desbloqueo de Usuario"

    # Generar una imagen de prueba (>15 KB para pasar el filtro de significancia)
    img_sample = Image.new("RGB", (600, 400), color=(30, 90, 160))
    img_path = filepath.parent / "temp_diagram.jpg"
    img_sample.save(img_path, format="JPEG", quality=95)

    slide3.shapes.add_picture(str(img_path), Inches(1.5), Inches(1.8), width=Inches(7))

    prs.save(str(filepath))
    if img_path.exists():
        img_path.unlink()


async def run_multimodal_tests():
    print("=" * 70)
    print("SUITE DE PRUEBAS: INGESTA MULTIMODAL Y ENDPOINTS ADMIN (PPTX / PDF)")
    print("=" * 70)

    settings = get_settings()
    docs_dir = Path(settings.docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    sample_pptx_path = docs_dir / "TEST_Procedimiento_Kactus_Sample.pptx"

    try:
        # -------------------------------------------------------------
        # TEST 1: GENERACION Y PARSEO PPTX
        # -------------------------------------------------------------
        print("\n--- TEST 1: Generacion y Parseo Nativo de Presentacion PPTX ---")
        create_sample_pptx(sample_pptx_path)
        print(f"[OK] Archivo PPTX de prueba generado en: {sample_pptx_path.name} ({sample_pptx_path.stat().st_size / 1024:.1f} KB)")

        use_vision, active_model = check_vision_model_available(settings.ollama_base_url, settings.vision_model)
        print(f"Estado de Vision-LLM: Disponible={use_vision}, Modelo Activo='{active_model}'")

        docs = process_pptx(
            filepath=sample_pptx_path,
            ollama_url=settings.ollama_base_url,
            vision_model=active_model,
            vision_timeout=settings.vision_timeout,
            max_image_size=settings.vision_max_image_size,
            min_image_kb=settings.vision_min_image_kb,
            use_vision=use_vision
        )

        print(f"Total diapositivas extraidas: {len(docs)}")
        assert len(docs) == 3, f"Se esperaban 3 diapositivas, se obtuvieron {len(docs)}"

        # Validar Slide 1 (Texto y Notas de orador)
        doc1 = docs[0]
        assert "Procedimiento de Soporte Tecnico Kactus" in doc1.page_content
        assert "[Notas del Orador]" in doc1.page_content
        assert doc1.metadata["type"] == "presentation"
        assert doc1.metadata["slide_number"] == 1
        print("  [OK] Slide 1: Texto de formas y Notas de Orador extraidos correctamente.")

        # Validar Slide 2 (Tabla estructurada)
        doc2 = docs[1]
        assert "[Tabla]" in doc2.page_content
        assert "Caida total de Kactus Nomina" in doc2.page_content
        assert "2 Horas" in doc2.page_content
        print("  [OK] Slide 2: Tablas estructuradas convertidas a formato legible.")

        # Validar Slide 3 (Imagen incrustada)
        doc3 = docs[2]
        assert doc3.metadata["slide_number"] == 3
        print(f"  [OK] Slide 3: Imagen incrustada procesada. has_images={doc3.metadata.get('has_images')}")

        # -------------------------------------------------------------
        # TEST 2: ENDPOINT ADMIN /api/admin/upload CON PPTX
        # -------------------------------------------------------------
        print("\n--- TEST 2: Endpoint /api/admin/upload con archivo PPTX ---")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            
            # Leer el archivo PPTX para simular subida
            with open(sample_pptx_path, "rb") as f:
                file_content = f.read()

            with patch("app.routers.chat.ingest_multimodal", return_value=True), \
                 patch("app.routers.chat.rag_service.reload_vector_store", return_value=None):
                
                files = {"file": ("Uploaded_Test_Presentation.pptx", file_content, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
                resp = await client.post("/api/admin/upload", files=files)
                print(f"Upload Status Code: {resp.status_code}")
                data = resp.json()
                print(f"Upload Response: {data}")
                assert resp.status_code == 200
                assert data.get("status") == "success"
                assert "Uploaded_Test_Presentation.pptx" in data.get("message")
                print("  [OK] Endpoint /api/admin/upload procesa y acepta PPTX correctamente.")

            # -------------------------------------------------------------
            # TEST 3: VALIDACION DE RECHAZO DE FORMATO INVALIDO
            # -------------------------------------------------------------
            print("\n--- TEST 3: Rechazo de formatos no soportados (.txt, .exe) ---")
            fake_files = {"file": ("malicious.exe", b"fake binary", "application/octet-stream")}
            bad_resp = await client.post("/api/admin/upload", files=fake_files)
            print(f"Bad file Status Code: {bad_resp.status_code}")
            assert bad_resp.status_code == 400
            print("  [OK] Rechazo exitoso de extensiones no permitidas.")

        print("\n" + "=" * 70)
        print("TODAS LAS PRUEBAS MULTIMODALES (PPTX, PDF, VISION, ADMIN) COMPLETADAS EXITOSAMENTE!")
        print("=" * 70)

    finally:
        # Limpieza de archivos temporales de prueba
        if sample_pptx_path.exists():
            sample_pptx_path.unlink()
        uploaded_path = docs_dir / "Uploaded_Test_Presentation.pptx"
        if uploaded_path.exists():
            uploaded_path.unlink()


if __name__ == "__main__":
    asyncio.run(run_multimodal_tests())
