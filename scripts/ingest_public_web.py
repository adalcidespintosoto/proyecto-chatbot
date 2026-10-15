"""Add a small, reviewed set of public Unisimón pages to the existing RAG index.

The script only fetches HTTPS pages from the exact institutional host listed in
the manifest. It never follows cross-host redirects, runs page JavaScript, or
submits forms. Run without ``--apply`` to preview extraction and chunk counts.
"""

from __future__ import annotations

import argparse
import codecs
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_MANIFEST = ROOT / "data" / "public_web_sources.json"
DEFAULT_REPORT = ROOT / "data" / "public_web_ingest_latest.json"
ALLOWED_HOST = "unisimon.edu.co"
MAX_RESPONSE_BYTES = 2_000_000
MAX_TEXT_CHARS = 25_000
MAX_LINKS = 80
MAX_REDIRECTS = 5
REQUEST_TIMEOUT_SECONDS = 20
USER_AGENT = "UniMon-Public-Knowledge-Indexer/1.0"
AUTH_PATH = re.compile(r"^/(?:login|signin|sign-in|auth|autenticacion|acceso)(?:/|$)", re.I)
QUOTED_URL = re.compile(r"['\"]((?:https?://|/)[^'\"]+)['\"]", re.I)
URL_ATTRS = ("data-id", "data-url", "data-href", "data-link", "data-target")
LOGGER = logging.getLogger("unimon.public_web_ingest")


def is_allowed_public_url(url: str) -> bool:
    """Allow only canonical HTTPS paths on the reviewed institutional host."""
    try:
        parts = urlsplit((url or "").strip())
        if parts.scheme.lower() != "https" or parts.hostname != ALLOWED_HOST:
            return False
        if parts.username or parts.password or parts.port or parts.query or parts.fragment:
            return False
        if AUTH_PATH.search(parts.path or "/"):
            return False
        if "\\" in parts.path or re.search(r"(?:^|/)\.\.(?:/|$)", parts.path):
            return False
        return True
    except ValueError:
        return False


class _VisiblePageParser(HTMLParser):
    """Extract visible text and internal link labels without executing HTML."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg", "header", "nav", "footer", "form"}
    _SKIP_DIV_IDS = {"servicios", "mymodal1", "menu-es"}
    _SKIP_DIV_CLASSES = {"dnonem", "lockm", "modal", "modal1"}
    _VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: list[str] = []
        self.visible_text: list[str] = []
        self.links: list[dict[str, str]] = []
        self.ui_headings: list[str] = []
        self.ui_navigation: list[dict[str, str]] = []
        self.ui_fields: list[dict[str, str]] = []
        self.ui_actions: list[str] = []
        self.ui_labels: dict[str, str] = {}
        self._skip_depth = 0
        self._skip_div_nesting = 0
        self._in_title = False
        self._anchor_href = ""
        self._in_anchor = False
        self._anchor_label: list[str] = []
        self._anchor_targets: list[str] = []
        self._anchor_is_navigation = False
        self._anchor_is_action = False
        self._navigation_tag_depth = 0
        self._menu_div_depth = 0
        self._form_depth = 0
        self._active_heading: str | None = None
        self._heading_buffer: list[str] = []
        self._active_button: list[str] | None = None
        self._button_visible = False
        self._active_label_for = ""
        self._label_buffer: list[str] = []
        self._ui_suppressed_depth = 0
        self._ui_tag_stack: list[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        classes = set((attrs_map.get("class") or "").casefold().split())
        style = (attrs_map.get("style") or "").casefold().replace(" ", "")
        explicitly_hidden = (
            "hidden" in attrs_map
            or "aria-hidden" in attrs_map and attrs_map.get("aria-hidden", "").casefold() == "true"
            or "display:none" in style
            or "visibility:hidden" in style
            or bool(classes.intersection({"hidden", "d-none", "visually-hidden", "modal", "modal1", "dnonem", "lockm"}))
        )
        suppress_ui = tag in {"footer", "script", "style", "noscript", "svg"} or explicitly_hidden
        if tag not in self._VOID_TAGS:
            self._ui_tag_stack.append((tag, suppress_ui))
        if suppress_ui:
            self._ui_suppressed_depth += 1
        if tag in {"header", "nav"}:
            self._navigation_tag_depth += 1
        if tag == "div" and ((attrs_map.get("id") or "").casefold() == "menu-es" or self._menu_div_depth):
            self._menu_div_depth += 1
        if tag == "form":
            self._form_depth += 1

        if tag == "title":
            self._in_title = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and not self._skip_depth:
            self._active_heading = tag
            self._heading_buffer = []
        if tag == "label" and not self._ui_suppressed_depth:
            self._active_label_for = attrs_map.get("for") or ""
            self._label_buffer = []
        if tag == "input" and not self._ui_suppressed_depth:
            input_type = (attrs_map.get("type") or "text").casefold()
            if input_type not in {"hidden", "submit", "button", "reset", "image"}:
                field = {
                    "label": attrs_map.get("aria-label") or attrs_map.get("placeholder") or "",
                    "type": input_type,
                    "id": attrs_map.get("id") or "",
                    "name": attrs_map.get("name") or "",
                }
                self.ui_fields.append(field)
        if tag == "button" and not self._ui_suppressed_depth and (self._form_depth or not self._skip_depth):
            self._active_button = []
            self._button_visible = True
        if tag == "a":
            self._anchor_href = attrs_map.get("href") or ""
            self._in_anchor = True
            self._anchor_label = []
            self._anchor_targets = self._literal_targets(self._anchor_href)
            for attr in URL_ATTRS:
                self._anchor_targets.extend(self._literal_targets(attrs_map.get(attr) or ""))
            self._anchor_targets.extend(self._literal_targets(attrs_map.get("onclick") or ""))
            in_navigation = bool(self._navigation_tag_depth or self._menu_div_depth)
            self._anchor_is_navigation = in_navigation and not self._ui_suppressed_depth
            self._anchor_is_action = not self._skip_depth and not self._ui_suppressed_depth and not in_navigation
        elif tag in {"button", "area"}:
            label = attrs_map.get("aria-label") or attrs_map.get("title") or attrs_map.get("alt") or ""
            targets = []
            for attr in URL_ATTRS:
                targets.extend(self._literal_targets(attrs_map.get(attr) or ""))
            targets.extend(self._literal_targets(attrs_map.get("onclick") or ""))
            for target in targets:
                self.links.append({"raw_url": target, "label": label})
        if tag == "div":
            if self._skip_div_nesting:
                self._skip_div_nesting += 1
            elif (attrs_map.get("id") or "").casefold() in self._SKIP_DIV_IDS:
                self._skip_div_nesting = 1
                self._skip_depth += 1
            elif classes.intersection({"menu-mobile", "menu-desktop", "social-menu"} | self._SKIP_DIV_CLASSES):
                self._skip_div_nesting = 1
                self._skip_depth += 1
        elif tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._active_heading == tag:
            heading = " ".join(" ".join(self._heading_buffer).split())
            if heading:
                self.ui_headings.append(heading[:250])
            self._active_heading = None
            self._heading_buffer = []
        if tag == "label" and self._active_label_for:
            label = " ".join(" ".join(self._label_buffer).split())
            if label:
                self.ui_labels[self._active_label_for] = label[:160]
            self._active_label_for = ""
            self._label_buffer = []
        if tag == "button" and self._active_button is not None:
            label = " ".join(" ".join(self._active_button).split())
            if self._button_visible and label:
                self.ui_actions.append(label[:200])
            self._active_button = None
            self._button_visible = False
        if tag == "a" and self._in_anchor:
            label = " ".join(" ".join(self._anchor_label).split())
            if label and not self._skip_depth:
                for target in dict.fromkeys(self._anchor_targets):
                    self.links.append({"raw_url": target, "label": label})
            if label and self._anchor_is_navigation:
                self.ui_navigation.append({"raw_url": self._anchor_href, "label": label})
            if label and self._anchor_is_action:
                self.ui_actions.append(label[:200])
            self._anchor_href = ""
            self._in_anchor = False
            self._anchor_label = []
            self._anchor_targets = []
            self._anchor_is_navigation = False
            self._anchor_is_action = False
        if tag == "form" and self._form_depth:
            self._form_depth -= 1
        if tag in {"header", "nav"} and self._navigation_tag_depth:
            self._navigation_tag_depth -= 1
        if tag == "div" and self._menu_div_depth:
            self._menu_div_depth -= 1
        for index in range(len(self._ui_tag_stack) - 1, -1, -1):
            if self._ui_tag_stack[index][0] == tag:
                closed_tags = self._ui_tag_stack[index:]
                del self._ui_tag_stack[index:]
                self._ui_suppressed_depth = max(
                    0, self._ui_suppressed_depth - sum(1 for _name, suppressed in closed_tags if suppressed)
                )
                break
        if tag == "div" and self._skip_div_nesting:
            self._skip_div_nesting -= 1
            if self._skip_div_nesting == 0 and self._skip_depth:
                self._skip_depth -= 1
        elif tag in self._SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        text = " ".join((data or "").split())
        if not text:
            return
        if text.startswith("{") and text.endswith("}"):
            try:
                payload = json.loads(text)
            except (json.JSONDecodeError, TypeError):
                payload = None
            if isinstance(payload, dict) and any(key in payload for key in ("error", "message", "info")):
                return
        if self._in_title:
            self.title.append(text)
        if self._active_heading is not None:
            self._heading_buffer.append(text)
        if self._active_label_for:
            self._label_buffer.append(text)
        if self._active_button is not None:
            self._active_button.append(text)
        if self._in_anchor and (not self._skip_depth or self._anchor_is_navigation):
            self._anchor_label.append(text)
        if not self._skip_depth and not self._in_title:
            self.visible_text.append(text)

    @staticmethod
    def _literal_targets(value: str) -> list[str]:
        value = (value or "").strip()
        if not value or value.startswith(("#", "mailto:", "tel:", "data:")):
            return []
        if value.startswith(("https://", "http://", "/")):
            return [value]
        return [match.group(1) for match in QUOTED_URL.finditer(value)]


def _internal_link(raw_url: str, page_url: str) -> str | None:
    raw_url = (raw_url or "").strip()
    if not raw_url or raw_url.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None
    target = urljoin(page_url, raw_url)
    parts = urlsplit(target)
    if parts.scheme.lower() != "https" or parts.hostname != ALLOWED_HOST:
        return None
    if parts.username or parts.password or parts.port or AUTH_PATH.search(parts.path or "/"):
        return None
    return urlunsplit(("https", ALLOWED_HOST, parts.path or "/", "", ""))


def extract_public_page(
    html: str,
    *,
    url: str,
    title_hint: str,
    section: str,
) -> dict:
    """Return a bounded plain-text representation of visible page content."""
    if not is_allowed_public_url(url):
        raise ValueError(f"URL de origen no permitida: {url}")

    parser = _VisiblePageParser()
    parser.feed(html or "")
    title = " ".join(" ".join(parser.title).split()) or title_hint

    body: list[str] = []
    seen_text: set[str] = set()
    for item in parser.visible_text:
        normalized = " ".join(item.split())
        key = normalized.casefold()
        if normalized and key not in seen_text:
            seen_text.add(key)
            body.append(normalized)

    links: list[dict[str, str]] = []
    seen_links: set[tuple[str, str]] = set()
    for link in parser.links:
        target = _internal_link(link["raw_url"], url)
        label = " ".join(link["label"].split())
        key = (label.casefold(), target or "")
        if target and label and key not in seen_links:
            seen_links.add(key)
            links.append({"label": label[:250], "url": target})
        if len(links) >= MAX_LINKS:
            break

    ui_navigation: list[dict[str, str]] = []
    seen_navigation: set[tuple[str, str]] = set()
    for item in parser.ui_navigation:
        target = _internal_link(item["raw_url"], url)
        label = " ".join(item["label"].split())
        key = (label.casefold(), target or "")
        if target and label and key not in seen_navigation:
            seen_navigation.add(key)
            ui_navigation.append({"label": label[:200], "url": target})
        if len(ui_navigation) >= 30:
            break

    ui_fields: list[dict[str, str]] = []
    seen_fields: set[tuple[str, str]] = set()
    for field in parser.ui_fields:
        label = field["label"] or parser.ui_labels.get(field["id"], "") or field["name"] or field["id"]
        label = " ".join(label.split())
        kind = field["type"]
        key = (label.casefold(), kind)
        if label and key not in seen_fields:
            seen_fields.add(key)
            ui_fields.append({"label": label[:160], "type": kind})
        if len(ui_fields) >= 30:
            break

    ui_actions = list(dict.fromkeys(" ".join(item.split())[:200] for item in parser.ui_actions if item.strip()))[:40]

    visible_text = "\n".join(body)[:MAX_TEXT_CHARS].strip()
    if not visible_text:
        raise ValueError(f"No se encontró contenido visible en {url}")
    return {
        "url": url,
        "title": title[:500],
        "section": section[:200],
        "text": visible_text,
        "links": links,
        "ui_map": {
            "headings": list(dict.fromkeys(parser.ui_headings))[:30],
            "navigation": ui_navigation,
            "fields": ui_fields,
            "actions": ui_actions,
        },
    }


def _decode_html(content: bytes, content_type: str) -> str:
    match = re.search(r"charset\s*=\s*['\"]?([\w.-]+)", content_type, flags=re.I)
    encodings = [match.group(1)] if match else []
    encodings.extend(["utf-8", "windows-1252"])
    for encoding in encodings:
        try:
            codecs.lookup(encoding)
            return content.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return content.decode("utf-8", errors="replace")


def _read_bounded_response(response: requests.Response) -> bytes:
    parts: list[bytes] = []
    total = 0
    for part in response.iter_content(chunk_size=64 * 1024):
        if not part:
            continue
        total += len(part)
        if total > MAX_RESPONSE_BYTES:
            raise ValueError(f"La página supera el límite de {MAX_RESPONSE_BYTES} bytes")
        parts.append(part)
    return b"".join(parts)


def fetch_public_page(page: dict) -> dict:
    """Fetch one manifest URL, restricting redirects to the same HTTPS host."""
    initial_url = page.get("url", "")
    if not is_allowed_public_url(initial_url):
        raise ValueError(f"URL de origen no permitida: {initial_url}")

    current_url = initial_url
    for _ in range(MAX_REDIRECTS + 1):
        response = requests.get(
            current_url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
            allow_redirects=False,
            stream=True,
        )
        try:
            if 300 <= response.status_code < 400:
                location = response.headers.get("Location", "")
                next_url = urljoin(current_url, location)
                if not is_allowed_public_url(next_url):
                    raise ValueError(f"Redirección fuera del host autorizado desde {current_url}")
                current_url = next_url
                continue
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                raise ValueError(f"Tipo de contenido no HTML en {current_url}: {content_type or 'desconocido'}")
            content = _read_bounded_response(response)
            html = _decode_html(content, content_type)
            parsed = extract_public_page(
                html,
                url=initial_url,
                title_hint=page.get("title", "Página institucional"),
                section=page.get("section", "Sitio web"),
            )
            parsed["http_status"] = response.status_code
            parsed["fetched_url"] = current_url
            return parsed
        finally:
            response.close()
    raise ValueError(f"Se superó el máximo de {MAX_REDIRECTS} redirecciones para {initial_url}")


def build_public_documents(
    pages: list[dict],
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[Document]:
    """Convert extracted pages to ordered, source-attributed RAG chunks."""
    if not 200 <= chunk_size <= 4000 or not 0 <= chunk_overlap < chunk_size:
        raise ValueError("Tamaño de chunk u overlap fuera de límites seguros")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    documents: list[Document] = []
    seen_sources: set[str] = set()

    for page in pages:
        url = str(page.get("url", ""))
        slug = str(page.get("slug", ""))
        if not is_allowed_public_url(url):
            raise ValueError(f"URL de origen no permitida: {url}")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", slug):
            raise ValueError(f"Slug inválido en el manifiesto: {slug!r}")
        source = f"Web_Unisimon_{slug}.md"
        if source in seen_sources:
            raise ValueError(f"Fuente duplicada en el manifiesto: {source}")
        seen_sources.add(source)

        page_text = str(page.get("text", "")).strip()
        if not page_text:
            raise ValueError(f"Página sin texto extraído: {url}")
        link_lines = [f"- {item['label']}: {item['url']}" for item in page.get("links", []) if item.get("label") and item.get("url")]
        header = (
            f"Fuente oficial: Universidad Simón Bolívar — {page.get('title') or page.get('title_hint') or slug}\n"
            f"Sección: {page.get('section') or 'Sitio web'}\n"
            f"URL oficial: {url}"
        )
        complete_text = header + "\n\nContenido visible de la página:\n" + page_text
        if link_lines:
            complete_text += "\n\nEnlaces institucionales visibles:\n" + "\n".join(link_lines)
        split_docs = splitter.split_documents([
            Document(page_content=complete_text, metadata={
                "source": source,
                "page_number": 1,
                "source_url": url,
                "source_title": str(page.get("title") or slug)[:500],
                "section": str(page.get("section") or "Sitio web")[:200],
                "source_type": "public_web",
            })
        ])
        for chunk_index, doc in enumerate(split_docs):
            # Keep provenance and URL in every chunk, including later splits.
            if not doc.page_content.startswith(header):
                doc.page_content = header + "\n\n" + doc.page_content
            doc.metadata["chunk_index"] = chunk_index
            documents.append(doc)

        ui_map = page.get("ui_map") or {}
        if not page.get("ui_map_verified"):
            continue
        ui_lines: list[str] = [
            f"Mapa visual de interfaz pública: {page.get('title') or page.get('title_hint') or slug}",
            f"Fuente oficial: Universidad Simón Bolívar — {page.get('title') or page.get('title_hint') or slug}",
            f"URL oficial: {url}",
            f"Verificado visualmente: {page.get('ui_snapshot_date') or 'fecha no registrada'}.",
            "Mapa de regiones y controles visibles; no almacena valores escritos, nombres de usuario ni contraseñas.",
        ]
        regions = ui_map.get("regions", [])
        if regions:
            ui_lines.append("Distribución visual, de arriba hacia abajo:")
            for region in regions[:20]:
                name = str(region.get("name", "")).strip()
                items = [str(item).strip() for item in region.get("items", []) if str(item).strip()]
                if name and items:
                    ui_lines.append(f"- {name}: " + " → ".join(items[:20]))
        headings = [str(item).strip() for item in ui_map.get("headings", []) if str(item).strip()]
        if headings:
            ui_lines.append("Encabezados visibles: " + " → ".join(headings[:20]))
        navigation = ui_map.get("navigation", [])
        if navigation:
            ui_lines.append("Navegación visible: " + " → ".join(str(item["label"]) for item in navigation[:20]))
            ui_lines.extend(f"- Menú {item['label']}: {item['url']}" for item in navigation[:30] if item.get("label") and item.get("url"))
        fields = ui_map.get("fields", [])
        if fields:
            type_names = {"text": "texto", "password": "contraseña", "email": "correo", "search": "búsqueda", "tel": "teléfono", "number": "número", "date": "fecha", "checkbox": "casilla", "radio": "opción"}
            ui_lines.append("Campos visibles (solo etiqueta y tipo, nunca valores):")
            ui_lines.extend(f"- Campo: {item['label']} ({type_names.get(item['type'], item['type'])})" for item in fields[:30] if item.get("label"))
        actions = [str(item).strip() for item in ui_map.get("actions", []) if str(item).strip()]
        if actions:
            ui_lines.append("Acciones visibles, en orden de aparición: " + " → ".join(actions[:30]))
        ui_source = f"Web_UI_Unisimon_{slug}.md"
        documents.append(Document(page_content="\n".join(ui_lines), metadata={
            "source": ui_source,
            "page_number": 1,
            "source_url": url,
            "source_title": str(page.get("title") or slug)[:500],
            "section": str(page.get("section") or "Sitio web")[:200],
            "source_type": "public_web_ui",
            "ui_verified": True,
            "ui_snapshot_date": str(page.get("ui_snapshot_date") or "")[:10],
            "chunk_index": 0,
        }))
    return documents


def upsert_public_documents(vector_store: Chroma, embeddings: HuggingFaceEmbeddings, documents: list[Document]) -> dict:
    """Add/refresh web chunks, then remove only stale chunks for refreshed pages."""
    if not documents:
        raise ValueError("No hay fragmentos web para indexar")
    by_source: dict[str, list[tuple[str, Document]]] = defaultdict(list)
    for document in documents:
        by_source[str(document.metadata["source"])].append(("", document))

    from scripts.ingest_multimodal_docs import generate_deterministic_chunk_ids

    all_ids: list[str] = []
    all_documents: list[Document] = []
    for source, rows in by_source.items():
        docs = [document for _unused, document in rows]
        ids = generate_deterministic_chunk_ids(docs)
        all_ids.extend(ids)
        all_documents.extend(docs)

    texts = [doc.page_content for doc in all_documents]
    metadatas = [doc.metadata for doc in all_documents]
    vectors = embeddings.embed_documents([f"passage: {text}" for text in texts])
    collection = vector_store._collection
    before_count = collection.count()

    # Upsert first so a transient embedding/index error cannot erase the last
    # successful snapshot. Remove obsolete IDs only after all new chunks exist.
    collection.upsert(ids=all_ids, documents=texts, metadatas=metadatas, embeddings=vectors)
    stale_ids: list[str] = []
    for source, rows in by_source.items():
        current_ids = set(generate_deterministic_chunk_ids([doc for _unused, doc in rows]))
        existing = collection.get(where={"source": source}, include=["metadatas"])
        stale_ids.extend(chunk_id for chunk_id in existing.get("ids", []) if chunk_id not in current_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)
    return {
        "chunks_upserted": len(all_ids),
        "stale_chunks_removed": len(stale_ids),
        "collection_count_before": before_count,
        "collection_count_after": collection.count(),
        "sources": sorted(by_source),
    }


def load_manifest(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pages = payload.get("pages") if isinstance(payload, dict) else None
    if not isinstance(pages, list) or not pages:
        raise ValueError("El manifiesto debe incluir una lista pages no vacía")
    seen_urls: set[str] = set()
    seen_slugs: set[str] = set()
    for page in pages:
        if not isinstance(page, dict) or not is_allowed_public_url(str(page.get("url", ""))):
            raise ValueError(f"Entrada de página inválida o no permitida: {page!r}")
        slug = str(page.get("slug", ""))
        if slug in seen_slugs or page["url"] in seen_urls:
            raise ValueError("El manifiesto contiene URLs o slugs duplicados")
        seen_slugs.add(slug)
        seen_urls.add(page["url"])
    return pages


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true", help="Escribe los fragmentos en la colección RAG existente")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    pages_config = load_manifest(args.manifest)
    pages: list[dict] = []
    errors: list[dict[str, str]] = []
    for item in pages_config:
        try:
            result = fetch_public_page(item)
            result["slug"] = item["slug"]
            if item.get("ui_map"):
                result["ui_map"] = item["ui_map"]
                result["ui_map_verified"] = True
                result["ui_snapshot_date"] = item.get("ui_snapshot_date", "")
            pages.append(result)
            LOGGER.info("Página extraída: %s — %d caracteres", result["url"], len(result["text"]))
        except Exception as exc:
            errors.append({"url": item.get("url", ""), "error": str(exc)[:500]})
            LOGGER.error("No se pudo extraer %s: %s", item.get("url", ""), exc)

    if errors:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "applied": False,
            "page_count": len(pages),
            "errors": errors,
            "message": "No se cambió ChromaDB: para indexar deben extraerse todas las páginas del manifiesto.",
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 1

    documents = build_public_documents(pages)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "applied": False,
        "page_count": len(pages),
        "chunk_count": len(documents),
        "pages": [{"url": p["url"], "title": p["title"], "section": p["section"],
                   "http_status": p["http_status"], "characters": len(p["text"]),
                   "chunks": sum(1 for doc in documents if doc.metadata["source"] == f"Web_Unisimon_{p['slug']}.md"),
                   "ui_source": f"Web_UI_Unisimon_{p['slug']}.md" if p.get("ui_map_verified") else None,
                   "ui_map_verified": bool(p.get("ui_map_verified")),
                   "ui_snapshot_date": p.get("ui_snapshot_date"),
                   "ui_map": p.get("ui_map") if p.get("ui_map_verified") else None}
                  for p in pages],
        "errors": [],
    }
    if args.apply:
        from app.config import get_settings

        settings = get_settings()
        embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"local_files_only": True},
            encode_kwargs={"normalize_embeddings": True},
        )
        vector_store = Chroma(
            persist_directory=str(settings.chroma_db_dir),
            embedding_function=embeddings,
        )
        summary["index_result"] = upsert_public_documents(vector_store, embeddings, documents)
        summary["applied"] = True

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "applied": summary["applied"],
        "page_count": summary["page_count"],
        "chunk_count": summary["chunk_count"],
        "ui_maps_verified": sum(1 for page in summary["pages"] if page["ui_map_verified"]),
        "errors": summary["errors"],
        "index_result": summary.get("index_result"),
        "report": str(args.report),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
