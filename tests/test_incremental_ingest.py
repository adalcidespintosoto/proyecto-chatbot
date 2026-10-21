"""
Pruebas Unitarias para Ingesta Incremental, Archivo Único, IDs Deterministas y Borrado en ChromaDB.
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from scripts.ingest_multimodal_docs import (
    generate_deterministic_chunk_ids,
    _distance_to_similarity,
    delete_document_chunks,
    get_existing_sources,
    is_useful_image_description,
    strip_chunk_boilerplate as strip_ingest_chunk_boilerplate,
    ingest_multimodal
)


@pytest.mark.parametrize("distance, expected", [(0.0, 1.0), (0.24, 0.88), (1.0, 0.5), (2.0, 0.0)])
def test_squared_l2_distance_is_converted_to_cosine_for_normalized_vectors(distance, expected):
    assert _distance_to_similarity(distance, "l2") == pytest.approx(expected)


def test_cosine_distance_conversion_keeps_existing_cosine_interpretation():
    assert _distance_to_similarity(0.12, "cosine") == pytest.approx(0.88)


def test_deterministic_chunk_ids():
    """Verifica que los IDs de chunk se generen con formato determinista: {stem}_p{page}_c{idx}."""
    doc1_p1_c0 = Document(page_content="Texto 1", metadata={"source": "P-GT-01_Mantenimiento.pdf", "page_number": 1})
    doc1_p1_c1 = Document(page_content="Texto 2", metadata={"source": "P-GT-01_Mantenimiento.pdf", "page_number": 1})
    doc1_p2_c0 = Document(page_content="Texto 3", metadata={"source": "P-GT-01_Mantenimiento.pdf", "page_number": 2})
    doc2_s1_c0 = Document(page_content="Slide 1", metadata={"source": "Manual_Docentes.pptx", "slide_number": 1})

    chunks = [doc1_p1_c0, doc1_p1_c1, doc1_p2_c0, doc2_s1_c0]
    ids = generate_deterministic_chunk_ids(chunks)

    assert ids[0] == "P-GT-01_Mantenimiento_943c80_p1_c0"
    assert ids[1] == "P-GT-01_Mantenimiento_943c80_p1_c1"
    assert ids[2] == "P-GT-01_Mantenimiento_943c80_p2_c0"
    assert ids[3] == "Manual_Docentes_c74246_p1_c0"


def test_vision_refusals_and_decorative_images_are_not_indexed_as_content():
    assert not is_useful_image_description("Lo siento, pero no puedo ayudar con la descripción de imágenes.")
    assert not is_useful_image_description("[IMAGEN_NO_RELEVANTE]")
    assert is_useful_image_description("La captura muestra el botón Guardar y el campo de usuario.")


def test_openai_non_relevant_marker_falls_back_instead_of_dropping_image(monkeypatch):
    from types import SimpleNamespace
    from PIL import Image
    import io
    import scripts.ingest_multimodal_docs as ingestion

    calls = []
    saved_cache = {}

    class FakeResponse:
        status_code = 200

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, **kwargs):
            calls.append(url)
            if url.endswith("/chat/completions"):
                return FakeResponse({"choices": [{"message": {"content": "[IMAGEN_NO_RELEVANTE]"}}]})
            return FakeResponse({"response": "Descripción decorativa generada por Ollama."})

    image_buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color="white").save(image_buffer, format="PNG")
    monkeypatch.setattr(ingestion, "get_settings", lambda: SimpleNamespace(
        openai_api_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        openai_timeout=35.0,
    ))
    monkeypatch.setattr(ingestion, "load_vision_cache", lambda: saved_cache)
    monkeypatch.setattr(ingestion, "save_vision_cache_entry", lambda key, value: saved_cache.setdefault(key, value))
    monkeypatch.setattr(ingestion.httpx, "Client", FakeClient)
    monkeypatch.setattr(ingestion, "stats", {key: 0 for key in ingestion.stats})

    result = ingestion.describe_image_with_vllm(
        image_buffer.getvalue(),
        filename="decorative_slide_image",
        ollama_url="http://ollama.test",
        vision_model="llava:13b",
    )

    assert result == "Descripción decorativa generada por Ollama."
    assert calls == [
        "https://api.openai.com/v1/chat/completions",
        "http://ollama.test/api/generate",
    ]
    assert ingestion.stats["images_skipped"] == 0
    assert "[IMAGEN_NO_RELEVANTE]" not in saved_cache.values()

    cached_result = ingestion.describe_image_with_vllm(
        image_buffer.getvalue(),
        filename="decorative_slide_image",
        ollama_url="http://ollama.test",
        vision_model="llava:13b",
    )

    assert cached_result == "Descripción decorativa generada por Ollama."
    assert calls == [
        "https://api.openai.com/v1/chat/completions",
        "http://ollama.test/api/generate",
        "https://api.openai.com/v1/chat/completions",
    ]
    assert ingestion.stats["images_skipped"] == 0


def test_ollama_remains_fallback_after_a_real_openai_error(monkeypatch):
    from types import SimpleNamespace
    from PIL import Image
    import io
    import scripts.ingest_multimodal_docs as ingestion

    calls = []

    class FakeResponse:
        def __init__(self, payload, error=None):
            self.payload = payload
            self.error = error

        def raise_for_status(self):
            if self.error:
                raise self.error

        def json(self):
            return self.payload

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, url, **kwargs):
            calls.append(url)
            if url.endswith("/chat/completions"):
                return FakeResponse({}, RuntimeError("OpenAI HTTP 500"))
            return FakeResponse({"response": "La captura muestra el botón Guardar."})

    image_buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color="white").save(image_buffer, format="PNG")
    monkeypatch.setattr(ingestion, "get_settings", lambda: SimpleNamespace(
        openai_api_key="test-key",
        openai_base_url="https://api.openai.com/v1",
        openai_timeout=35.0,
    ))
    monkeypatch.setattr(ingestion, "load_vision_cache", lambda: {})
    monkeypatch.setattr(ingestion, "save_vision_cache_entry", lambda key, value: None)
    monkeypatch.setattr(ingestion.httpx, "Client", FakeClient)
    monkeypatch.setattr(ingestion, "stats", {key: 0 for key in ingestion.stats})

    result = ingestion.describe_image_with_vllm(
        image_buffer.getvalue(),
        filename="technical_screenshot",
        ollama_url="http://ollama.test",
        vision_model="llava:13b",
    )

    assert result == "La captura muestra el botón Guardar."
    assert calls == [
        "https://api.openai.com/v1/chat/completions",
        "http://ollama.test/api/generate",
    ]


def test_ingestion_cleaner_preserves_document_instructions():
    text = (
        "UNIVERSIDAD SIMÓN BOLÍVAR\n"
        "Para ingresar al portal de la Universidad Simón Bolívar, sigue el procedimiento.\n"
        "Digite su usuario y contraseña institucional para acceder al sistema, y luego presione el botón Acceder."
    )

    cleaned = strip_ingest_chunk_boilerplate(text)

    assert "Para ingresar al portal de la Universidad Simón Bolívar" in cleaned
    assert "Digite su usuario y contraseña institucional" in cleaned


def test_delete_and_upsert_chunks(tmp_path):
    """Verifica que delete_document_chunks y upsert eliminen huérfanos y mantengan el conteo exacto."""
    chroma_dir = tmp_path / "test_chroma_db"
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vector_store = Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=embeddings
    )

    # Insertar 3 chunks para doc_A y 2 chunks para doc_B
    chunks_A = [
        Document(page_content="A1", metadata={"source": "doc_A.pdf", "page_number": 1}),
        Document(page_content="A2", metadata={"source": "doc_A.pdf", "page_number": 1}),
        Document(page_content="A3", metadata={"source": "doc_A.pdf", "page_number": 2})
    ]
    chunks_B = [
        Document(page_content="B1", metadata={"source": "doc_B.pdf", "page_number": 1}),
        Document(page_content="B2", metadata={"source": "doc_B.pdf", "page_number": 2})
    ]

    all_chunks = chunks_A + chunks_B
    ids = generate_deterministic_chunk_ids(all_chunks)
    texts = [c.page_content for c in all_chunks]
    metas = [c.metadata for c in all_chunks]

    vector_store._collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metas,
        embeddings=embeddings.embed_documents(texts)
    )

    assert vector_store._collection.count() == 5
    sources = get_existing_sources(vector_store)
    assert "doc_A.pdf" in sources
    assert "doc_B.pdf" in sources

    # Eliminar doc_A
    deleted = delete_document_chunks(vector_store, "doc_A.pdf")
    assert deleted == 3
    assert vector_store._collection.count() == 2
    sources_after = get_existing_sources(vector_store)
    assert "doc_A.pdf" not in sources_after
    assert "doc_B.pdf" in sources_after


def test_incremental_mode_and_single_file_cli(tmp_path, monkeypatch):
    """Verifica que el orquestador ingest_multimodal soporte modo incremental y archivo único."""
    from unittest.mock import patch
    monkeypatch.setattr("scripts.ingest_multimodal_docs.check_vision_model_available", lambda url, model: (False, model))

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    chroma_dir = tmp_path / "chroma"

    # Crear un PDF de prueba usando PyMuPDF
    import fitz
    doc_pdf1 = fitz.open()
    page1 = doc_pdf1.new_page()
    page1.insert_text((50, 50), "Este es el manual de pruebas para estudiantes sobre SIAAF.")
    pdf1_path = docs_dir / "manual_estudiantes.pdf"
    doc_pdf1.save(str(pdf1_path))
    doc_pdf1.close()

    # 1. Ingesta de archivo único
    success = ingest_multimodal(
        docs_path=str(docs_dir),
        chroma_path=str(chroma_dir),
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        file_path=str(pdf1_path)
    )
    assert success is True

    # Comprobar conteo en ChromaDB
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    vector_store = Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=embeddings
    )
    initial_count = vector_store._collection.count()
    assert initial_count >= 1
    assert "manual_estudiantes.pdf" in get_existing_sources(vector_store)

    # 2. Ingesta Incremental sin archivos nuevos -> debe retornar True sin reprocesar
    success_inc = ingest_multimodal(
        docs_path=str(docs_dir),
        chroma_path=str(chroma_dir),
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        incremental=True
    )
    assert success_inc is True
    assert vector_store._collection.count() == initial_count

    # 3. Agregar segundo archivo y correr incremental -> debe aumentar solo por el nuevo
    doc_pdf2 = fitz.open()
    page2 = doc_pdf2.new_page()
    page2.insert_text((50, 50), "Guía para docentes sobre carga de notas institucionales.")
    pdf2_path = docs_dir / "guia_docentes.pdf"
    doc_pdf2.save(str(pdf2_path))
    doc_pdf2.close()

    success_inc2 = ingest_multimodal(
        docs_path=str(docs_dir),
        chroma_path=str(chroma_dir),
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        incremental=True
    )
    assert success_inc2 is True
    new_count = vector_store._collection.count()
    assert new_count > initial_count
    assert "guia_docentes.pdf" in get_existing_sources(vector_store)

    # 4. Eliminar documento con --delete-doc
    success_del = ingest_multimodal(
        chroma_path=str(chroma_dir),
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        delete_doc="manual_estudiantes.pdf"
    )
    assert success_del is True
    assert "manual_estudiantes.pdf" not in get_existing_sources(vector_store)
    assert vector_store._collection.count() == new_count - initial_count
