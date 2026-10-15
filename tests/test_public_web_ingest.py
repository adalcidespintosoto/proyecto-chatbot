import json
from pathlib import Path
from urllib.parse import urlsplit

from scripts.ingest_public_web import (
    build_public_documents,
    extract_public_page,
    is_allowed_public_url,
    upsert_public_documents,
)
from langchain_core.documents import Document


ROOT = Path(__file__).resolve().parents[1]


def test_public_web_source_registry_is_curated_and_same_host():
    registry = json.loads((ROOT / "data" / "public_web_sources.json").read_text(encoding="utf-8"))

    assert 1 <= len(registry["pages"]) <= 30
    assert all(is_allowed_public_url(item["url"]) for item in registry["pages"])
    assert len({item["slug"] for item in registry["pages"]}) == len(registry["pages"])


def test_public_url_validation_rejects_external_non_https_and_auth_routes():
    assert is_allowed_public_url("https://unisimon.edu.co/portales")
    assert not is_allowed_public_url("http://unisimon.edu.co/portales")
    assert not is_allowed_public_url("https://evil.example/unisimon.edu.co/portales")
    assert not is_allowed_public_url("https://sub.unisimon.edu.co/portales")
    assert not is_allowed_public_url("https://unisimon.edu.co/login")
    assert not is_allowed_public_url("https://unisimon.edu.co/portales?next=https://evil.example")


def test_page_extraction_keeps_visible_text_and_links_but_drops_scripts_nav_and_forms():
    html = """<!doctype html><html><head><title>Portal estudiantes</title></head>
    <body><header>Menú repetido</header><nav><a href='/ruido'>Ruido</a></nav>
    <div id='servicios'><a href='/repetido'>Menú lateral repetido</a></div>
    <div id='menu-es'><a href='/encabezado'>Encabezado repetido</a></div>
    <div class='modal fade'>Aviso temporal oculto</div>
    <div class='lockm'>Pie alternativo repetido</div>
    <main><h1>Portal Estudiantes</h1><p>Accede desde la página de Portales.</p>
    <a href='/portales/estudiantes'>Abrir portal</a>
    <a href='#' data-id='/portales/estudiantes' onclick="go('/portales/estudiantes')">Portal dinámico</a>
    <a href='#'>Ancla de página</a>
    <a href='https://evil.example/phishing'>Enlace externo</a>
    <script>texto secreto</script><form action='/login'><input name='password'></form></main>
    <footer>Pie repetido</footer></body></html>"""

    page = extract_public_page(
        html,
        url="https://unisimon.edu.co/portales/estudiantes",
        title_hint="Portal Estudiantes",
        section="Portales",
    )

    assert page["title"] == "Portal estudiantes"
    assert "Accede desde la página de Portales." in page["text"]
    assert "Abrir portal" in page["text"]
    assert "Menú repetido" not in page["text"]
    assert "Menú lateral repetido" not in page["text"]
    assert "Encabezado repetido" not in page["text"]
    assert "Aviso temporal oculto" not in page["text"]
    assert "Pie alternativo repetido" not in page["text"]
    assert "texto secreto" not in page["text"]
    assert "password" not in page["text"]
    assert page["links"] == [
        {"label": "Abrir portal", "url": "https://unisimon.edu.co/portales/estudiantes"},
        {"label": "Portal dinámico", "url": "https://unisimon.edu.co/portales/estudiantes"},
    ]


def test_ui_map_captures_visible_form_controls_without_values_and_adds_separate_rag_document():
    html = """<html><body><header><nav><a href='/portales'>Portales</a></nav></header>
    <main><h1>Portal Estudiante</h1><form>
    <label for='usuario'>Usuario</label><input id='usuario' type='text' value='NO_INDEXAR_USUARIO'>
    <label for='clave'>Contraseña</label><input id='clave' type='password' value='NO_INDEXAR_CLAVE'>
    <button type='submit'>Acceder</button></form>
    <a href='/recuperar'>Olvidé mi Usuario / Contraseña</a></main></body></html>"""
    page = extract_public_page(
        html,
        url="https://unisimon.edu.co/portales/estudiantes",
        title_hint="Portal Estudiante",
        section="Portales",
    )

    assert page["ui_map"]["headings"] == ["Portal Estudiante"]
    assert page["ui_map"]["navigation"] == [
        {"label": "Portales", "url": "https://unisimon.edu.co/portales"}
    ]
    assert page["ui_map"]["fields"] == [
        {"label": "Usuario", "type": "text"},
        {"label": "Contraseña", "type": "password"},
    ]
    assert page["ui_map"]["actions"] == ["Acceder", "Olvidé mi Usuario / Contraseña"]
    ui_docs = [doc for doc in build_public_documents([{
        **page,
        "slug": "Portal_Estudiantes",
        "ui_map": {
            **page["ui_map"],
            "regions": [{"name": "Área de acceso", "items": ["Usuario", "Contraseña", "Acceder"]}],
        },
        "ui_map_verified": True,
        "ui_snapshot_date": "2026-10-15",
    }])
               if doc.metadata["source_type"] == "public_web_ui"]
    assert len(ui_docs) == 1
    assert "Campo: Usuario (texto)" in ui_docs[0].page_content
    assert "Campo: Contraseña (contraseña)" in ui_docs[0].page_content
    assert "Verificado visualmente: 2026-10-15" in ui_docs[0].page_content
    assert "Acceder" in ui_docs[0].page_content
    assert "Distribución visual, de arriba hacia abajo" in ui_docs[0].page_content
    assert "Área de acceso: Usuario → Contraseña → Acceder" in ui_docs[0].page_content
    assert "NO_INDEXAR" not in ui_docs[0].page_content
    assert ui_docs[0].metadata["ui_verified"] is True
    assert not any(doc.metadata["source_type"] == "public_web_ui"
                   for doc in build_public_documents([{**page, "slug": "Portal_Estudiantes"}]))


def test_manifest_keeps_visual_map_reviewed_separate_from_crawled_page_text():
    registry = json.loads((ROOT / "data" / "public_web_sources.json").read_text(encoding="utf-8"))
    pages = {page["slug"]: page for page in registry["pages"]}
    portal = pages["Portal_Estudiantes"]

    assert portal["ui_snapshot_date"] == "2026-10-15"
    assert portal["ui_map"]["fields"] == [
        {"label": "Usuario", "type": "text"},
        {"label": "Contraseña", "type": "password"},
    ]
    assert "Valor de Usuario" not in json.dumps(portal["ui_map"], ensure_ascii=False)
    navigation_urls = [link["url"] for page in pages.values()
                       for link in page.get("ui_map", {}).get("navigation", [])]
    assert all(urlsplit(url).scheme == "https" and not urlsplit(url).username and not urlsplit(url).password
               for url in navigation_urls)


def test_chunked_web_documents_keep_url_title_section_and_stable_page_order():
    pages = [{
        "url": "https://unisimon.edu.co/portales",
        "title": "Portales institucionales",
        "section": "Portales",
        "slug": "Portales",
        "text": "Portal Estudiantes Aula Extendida " * 120,
        "links": [{"label": "Portal Estudiantes", "url": "https://unisimon.edu.co/portales/estudiantes"}],
    }]

    chunks = build_public_documents(pages, chunk_size=300, chunk_overlap=30)
    content_chunks = [chunk for chunk in chunks if chunk.metadata["source_type"] == "public_web"]

    assert len(content_chunks) > 1
    assert all(chunk.metadata["source"] == "Web_Unisimon_Portales.md" for chunk in content_chunks)
    assert all(chunk.metadata["source_url"] == pages[0]["url"] for chunk in content_chunks)
    assert all(chunk.metadata["section"] == "Portales" for chunk in content_chunks)
    assert [chunk.metadata["chunk_index"] for chunk in content_chunks] == list(range(len(content_chunks)))
    assert all("URL oficial: https://unisimon.edu.co/portales" in chunk.page_content for chunk in content_chunks)
    assert any("Portal Estudiantes" in chunk.page_content for chunk in content_chunks)


def test_public_web_upsert_is_repeatable_and_removes_only_stale_chunks():
    class FakeCollection:
        def __init__(self):
            self.rows = {}

        def count(self):
            return len(self.rows)

        def upsert(self, *, ids, documents, metadatas, embeddings):
            for chunk_id, text, metadata, vector in zip(ids, documents, metadatas, embeddings):
                self.rows[chunk_id] = {"document": text, "metadata": metadata, "vector": vector}

        def get(self, *, where, include):
            source = where["source"]
            ids = [chunk_id for chunk_id, row in self.rows.items() if row["metadata"]["source"] == source]
            return {"ids": ids}

        def delete(self, *, ids):
            for chunk_id in ids:
                self.rows.pop(chunk_id, None)

    class FakeEmbeddings:
        def embed_documents(self, texts):
            return [[float(len(text))] for text in texts]

    class FakeStore:
        _collection = FakeCollection()

    store = FakeStore()
    embeddings = FakeEmbeddings()
    first_docs = build_public_documents([{
        "url": "https://unisimon.edu.co/portales",
        "title": "Portales",
        "section": "Portales",
        "slug": "Portales",
        "text": "Portal estudiantes. " * 100,
        "links": [],
    }], chunk_size=300, chunk_overlap=30)
    first = upsert_public_documents(store, embeddings, first_docs)
    repeated = upsert_public_documents(store, embeddings, first_docs)

    assert first["collection_count_after"] == first["chunks_upserted"]
    assert repeated["collection_count_before"] == repeated["collection_count_after"]
    assert repeated["stale_chunks_removed"] == 0

    shorter_docs = build_public_documents([{
        "url": "https://unisimon.edu.co/portales",
        "title": "Portales",
        "section": "Portales",
        "slug": "Portales",
        "text": "Portal estudiantes.",
        "links": [],
    }], chunk_size=300, chunk_overlap=30)
    refreshed = upsert_public_documents(store, embeddings, shorter_docs)
    assert refreshed["stale_chunks_removed"] == len(first_docs) - len(shorter_docs)
    assert refreshed["collection_count_after"] == len(shorter_docs)
