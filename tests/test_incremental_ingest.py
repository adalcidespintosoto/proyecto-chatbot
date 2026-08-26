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
    delete_document_chunks,
    get_existing_sources,
    ingest_multimodal
)


def test_deterministic_chunk_ids():
    """Verifica que los IDs de chunk se generen con formato determinista: {stem}_p{page}_c{idx}."""
    doc1_p1_c0 = Document(page_content="Texto 1", metadata={"source": "P-GT-01_Mantenimiento.pdf", "page_number": 1})
    doc1_p1_c1 = Document(page_content="Texto 2", metadata={"source": "P-GT-01_Mantenimiento.pdf", "page_number": 1})
    doc1_p2_c0 = Document(page_content="Texto 3", metadata={"source": "P-GT-01_Mantenimiento.pdf", "page_number": 2})
    doc2_s1_c0 = Document(page_content="Slide 1", metadata={"source": "Manual_Docentes.pptx", "slide_number": 1})

    chunks = [doc1_p1_c0, doc1_p1_c1, doc1_p2_c0, doc2_s1_c0]
    ids = generate_deterministic_chunk_ids(chunks)

    assert ids[0] == "P-GT-01_Mantenimiento_p1_c0"
    assert ids[1] == "P-GT-01_Mantenimiento_p1_c1"
    assert ids[2] == "P-GT-01_Mantenimiento_p2_c0"
    assert ids[3] == "Manual_Docentes_p1_c0"


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
