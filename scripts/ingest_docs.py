"""
Script de Ingestión de Documentos PDF para UniMon (Universidad Simón Bolívar - Colombia).
Carga documentos y procedimientos institucionales en ./data/docs/, genera fragmentos con solapamiento,
calcula embeddings multilingües (intfloat/multilingual-e5-base) y los persiste de manera limpia en ChromaDB.
"""

import os
import sys
import time
import shutil
import logging
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from app.config import get_settings

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("unimon.ingest_docs")


def ingest_documents(docs_path: str = None, chroma_path: str = None, model_name: str = None) -> bool:
    """
    Lee archivos PDF desde docs_path, limpia la base vectorial previa en chroma_path,
    fragmenta los textos, genera embeddings con HuggingFace y almacena la colección limpia.
    """
    settings = get_settings()
    docs_dir = Path(docs_path or settings.docs_dir)
    chroma_dir = Path(chroma_path or settings.chroma_db_dir)
    embedding_model_name = model_name or settings.embedding_model

    logger.info("=" * 65)
    logger.info(" INGESTIÓN DE PROCEDIMIENTOS INSTITUCIONALES - UNISIMON COLOMBIA")
    logger.info("=" * 65)
    logger.info(f"Directorio de Documentos: {docs_dir.resolve()}")
    logger.info(f"Directorio de ChromaDB:   {chroma_dir.resolve()}")
    logger.info(f"Modelo de Embeddings:     {embedding_model_name}")

    # 1. Asegurar existencia del directorio de documentos
    if not docs_dir.exists():
        logger.info(f"Creando directorio de documentos: {docs_dir}")
        docs_dir.mkdir(parents=True, exist_ok=True)

    # 2. Cargar todos los documentos PDF usando PyPDFDirectoryLoader
    logger.info(f"Verificando y cargando archivos PDF desde '{docs_dir}'...")
    loader = PyPDFDirectoryLoader(str(docs_dir))
    raw_docs = loader.load()

    pdf_files = list(docs_dir.glob("*.pdf"))
    if not raw_docs or not pdf_files:
        logger.warning(
            f"[!] No se encontraron archivos PDF en '{docs_dir}'.\n"
            f"Por favor, asegúrate de colocar los procedimientos oficiales de Unisimon en formato PDF dentro de '{docs_dir}'."
        )
        return False

    total_pdf_count = len(pdf_files)
    total_pages_count = len(raw_docs)
    logger.info(f"Documentos PDF encontrados: {total_pdf_count} archivo(s), {total_pages_count} página(s) procesada(s):")
    for idx, pdf in enumerate(pdf_files, 1):
        logger.info(f"  [{idx}/{total_pdf_count}] {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")

    # 3. Limpiar o reiniciar base vectorial previa para evitar fragmentos desactualizados
    if chroma_dir.exists():
        logger.info(f"Limpiando base vectorial previa en '{chroma_dir}' para garantizar sincronización limpia...")
        try:
            shutil.rmtree(chroma_dir)
            logger.info("Directorio ChromaDB previo eliminado con éxito.")
        except Exception as exc:
            logger.warning(f"No se pudo eliminar directorio completo ({exc}), se procederá a sobrescribir.")
    
    chroma_dir.mkdir(parents=True, exist_ok=True)

    # 4. Dividir documentos en fragmentos (chunk_size=800, chunk_overlap=150)
    chunk_size = 800
    chunk_overlap = 150
    logger.info(f"Fragmentando documentos (chunk_size={chunk_size}, chunk_overlap={chunk_overlap})...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(raw_docs)
    total_chunks = len(chunks)
    logger.info(f"Total de fragmentos generados: {total_chunks}")

    # 5. Inicializar modelo de embeddings multilingües (intfloat/multilingual-e5-base)
    logger.info(f"Cargando modelo de embeddings '{embedding_model_name}'...")
    start_time = time.time()
    embeddings = HuggingFaceEmbeddings(
        model_name=embedding_model_name,
        encode_kwargs={"normalize_embeddings": True}
    )

    # 6. Indexar y persistir en ChromaDB
    logger.info(f"Generando embeddings e indexando {total_chunks} fragmentos en ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(chroma_dir)
    )

    elapsed_time = time.time() - start_time
    logger.info("=" * 65)
    logger.info(" [ÉXITO] Ingestión y vectorización completada con éxito.")
    logger.info(f" • Total de documentos PDF leídos: {total_pdf_count} ({total_pages_count} páginas)")
    logger.info(f" • Total de fragmentos indexados:  {total_chunks}")
    logger.info(f" • Tiempo total de procesamiento:  {elapsed_time:.2f} segundos")
    logger.info(f" • Base vectorial persistida en:   {chroma_dir.resolve()}")
    logger.info("=" * 65)
    return True


if __name__ == "__main__":
    success = ingest_documents()
    sys.exit(0 if success else 1)

