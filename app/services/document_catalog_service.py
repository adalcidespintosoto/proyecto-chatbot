"""Compact, per-chatbot document catalogs used by the head router."""

from __future__ import annotations

import html
import json
import logging
import re
import unicodedata
import uuid
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger("unimon.document_catalog")

_GENERIC_HEADINGS = {
    "informacion del documento", "información del documento", "proposito", "propósito",
    "requisitos y permisos", "pasos", "paso a paso", "resultado esperado",
    "errores, limites o excepciones documentadas", "errores comunes",
    "palabras y formas de busqueda", "palabras y formas de búsqueda",
    "puntos por validar", "fuentes", "referencias",
}
_STOP_WORDS = {
    "para", "como", "cómo", "donde", "dónde", "cuando", "cuándo", "que", "qué",
    "quien", "quién", "cual", "cuál", "por", "con", "sin", "una", "uno", "unos",
    "unas", "del", "las", "los", "les", "mis", "sus", "este", "esta", "esto",
    "estos", "estas", "desde", "hasta", "sobre", "entre", "ante", "hacia", "quiero",
    "necesito", "tengo", "puedo", "debo", "hay", "ser", "estar", "hacer", "me", "mi",
    "el", "la", "lo", "y", "o", "a", "en", "un", "es", "se", "al", "ya", "no",
}
_LABELS = {
    "fuente original": "source",
    "temas incluidos": "description",
    "sistema o modulo": "system",
    "sistema o módulo": "system",
}
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d().\s-]{7,}\d)(?!\w)")


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", plain).strip()


def _safe_text(value: str, limit: int = 360) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"!?(\[([^\]]*)\])\([^)]*\)", r"\2", text)
    text = re.sub(r"[`*_>#~]+", " ", text)
    text = _EMAIL_RE.sub("[correo omitido]", text)
    text = _URL_RE.sub("[enlace omitido]", text)
    text = _PHONE_RE.sub("[teléfono omitido]", text)
    return re.sub(r"\s+", " ", text).strip()[:limit]


def _manifest_markdown_paths(manifest_path: Path | None) -> dict[str, dict[str, Any]] | None:
    if manifest_path is None or not manifest_path.is_file():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("No se pudo leer el manifiesto al actualizar el catálogo: %s", manifest_path)
        return {}
    records = payload.get("records", {}) if isinstance(payload, dict) else {}
    if not isinstance(records, dict):
        return {}
    selected: dict[str, dict[str, Any]] = {}

    def relative_markdown_path(value: Any) -> str:
        relative = str(value or "").replace("\\", "/").lstrip("/")
        if relative.casefold().startswith("markdown/"):
            relative = relative[len("markdown/"):]
        return relative

    for record in records.values():
        if not isinstance(record, dict) or record.get("status") != "success":
            continue
        source_hash = str(record.get("source_sha256") or "")
        indexed_hash = str(record.get("indexed_sha256") or "")
        if not source_hash or indexed_hash != source_hash:
            continue
        relative = relative_markdown_path(record.get("markdown_relative_path"))
        if relative:
            selected[relative.casefold()] = record
        for part in record.get("parts") or record.get("markdown_parts") or []:
            if isinstance(part, dict):
                part_path = relative_markdown_path(part.get("markdown_relative_path"))
                if part_path:
                    selected[part_path.casefold()] = {**record, **part, "status": "success"}
    return selected


def _extract_markdown_metadata(path: Path, content: str, record: dict[str, Any] | None) -> dict[str, Any]:
    title = ""
    headings: list[str] = []
    labels: dict[str, str] = {}
    search_terms: list[str] = []
    in_search_terms = False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            heading_text = _safe_text(heading.group(1), 160)
            if not title and raw_line.lstrip().startswith("# "):
                title = heading_text
            if heading_text and _normalize(heading_text) not in {_normalize(item) for item in _GENERIC_HEADINGS}:
                headings.append(heading_text)
            in_search_terms = _normalize(heading_text) in {
                "palabras y formas de busqueda", "terminos de busqueda", "formas de consulta",
            }
            continue

        plain_line = re.sub(r"[*_`]+", "", line)
        label_match = re.match(r"^\s*[-*]?\s*(fuente original|temas incluidos|sistema o módulo|sistema o modulo)\s*:\s*(.*)$", plain_line, re.IGNORECASE)
        if label_match:
            normalized_label = _normalize(label_match.group(1))
            key = _LABELS.get(normalized_label)
            if key and label_match.group(2).strip():
                labels.setdefault(key, _safe_text(label_match.group(2), 360))

        if in_search_terms and re.match(r"^\s*[-*+]\s+", line):
            term = _safe_text(re.sub(r"^\s*[-*+]\s+", "", line), 140)
            if term and term not in search_terms:
                search_terms.append(term)

    record = record or {}
    source_metadata = record.get("source_metadata") if isinstance(record.get("source_metadata"), dict) else {}
    source_type = str(record.get("source_type") or "")
    source_title = _safe_text(str(record.get("source_title") or source_metadata.get("source_title") or ""), 180)
    section = _safe_text(str(record.get("section") or source_metadata.get("section") or ""), 120)
    source = _safe_text(str(record.get("source_filename") or record.get("source") or labels.get("source") or path.name), 180)
    description = labels.get("description", "")
    if not description:
        useful_headings = [heading for heading in headings if _normalize(heading) != _normalize(title)]
        description = _safe_text("; ".join(useful_headings[:3]), 300)
    if source_type == "public_web_ui":
        title = source_title or title
        if section and _normalize(section) not in _normalize(title):
            title = _safe_text(f"{title} — {section}", 180)
        visual_summaries: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if re.match(r"^(?:Distribución visual(?:, de arriba hacia abajo)?|Navegación visible|Accesos académicos|Accesos de Aspirantes|Campos visibles|Acciones visibles)\s*:", line, re.IGNORECASE):
                summary = _safe_text(line, 180)
                if summary:
                    visual_summaries.append(summary)
            elif re.match(r"^-\s*(?:Menú|Acceso|Enlace)\s+", line, re.IGNORECASE):
                term = _safe_text(line.split(":", 1)[0], 120)
                if term and term not in search_terms:
                    search_terms.append(term)
        if not description:
            description = _safe_text("; ".join(([f"Sección: {section}"] if section else []) + visual_summaries[:2]), 360)
    system = labels.get("system", "")
    terms = [_safe_text(item, 140) for item in search_terms[:10]]
    if not terms:
        terms = [_safe_text(item, 120) for item in headings[:8] if _normalize(item) != _normalize(title)]
    if title == "":
        first_text_line = next((line.strip() for line in content.splitlines() if line.strip()), "")
        title = _safe_text(first_text_line or path.stem.replace("_", " "), 180)
    if system and system not in description:
        description = _safe_text(f"{description}; Sistema o módulo: {system}".strip("; "), 360)

    return {
        "markdown_path": path.as_posix(),
        "title": title,
        "source": source,
        "description": description,
        "search_terms": terms,
        "source_type": source_type,
    }


def build_document_catalog(
    markdown_root: Path,
    manifest_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Read metadata from every eligible Markdown without copying procedure bodies."""
    root = markdown_root.resolve()
    if not root.is_dir():
        return []
    selected = _manifest_markdown_paths(manifest_path)
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md"), key=lambda item: item.as_posix().casefold()):
        if path.is_symlink() or not path.is_file():
            continue
        resolved = path.resolve()
        if root not in resolved.parents:
            continue
        relative_key = path.relative_to(root).as_posix().casefold()
        record = selected.get(relative_key) if selected is not None else None
        if selected is not None and record is None:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("No se pudo leer Markdown para el catálogo (%s): %s", type(exc).__name__, path.name)
            continue
        entries.append(_extract_markdown_metadata(path.relative_to(root), content, record))

    # A source document can produce several Markdown parts (especially the public-site map).
    # Present one routing card per original document and combine only their short metadata.
    grouped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = str(entry.get("source") or entry.get("markdown_path") or "").casefold()
        existing = grouped.get(key)
        if existing is None:
            entry["markdown_paths"] = [entry.pop("markdown_path")]
            grouped[key] = entry
            continue
        existing["markdown_paths"].append(entry.pop("markdown_path"))
        descriptions = [part for part in (existing.get("description"), entry.get("description")) if part]
        existing["description"] = _safe_text("; ".join(dict.fromkeys(descriptions)), 360)
        existing["search_terms"] = list(dict.fromkeys([
            *existing.get("search_terms", []), *entry.get("search_terms", []),
        ]))[:10]
    return list(grouped.values())


def _topic_overview(entries: list[dict[str, Any]], limit: int = 12) -> list[str]:
    counts: Counter[str] = Counter()
    for entry in entries:
        for phrase in re.split(r"[;,|]", str(entry.get("description") or "")):
            phrase = _safe_text(phrase, 100)
            if len(_normalize(phrase).split()) >= 2:
                counts[phrase] += 1
    return [phrase for phrase, _ in counts.most_common(limit)]


def _catalog_markdown(catalog: dict[str, Any]) -> str:
    bot = catalog["bot"]
    lines = [
        f"# Catálogo de documentos de {bot['display_name']}",
        "",
        f"- Dependencia: {bot['dependency_name']}",
        f"- Alcance declarado: {_safe_text(bot['scope_description'], 500)}",
        f"- Documentos disponibles: {catalog['document_count']}",
        "",
        "Este archivo contiene metadatos breves para orientar el enrutamiento. No contiene el cuerpo de los procedimientos.",
        "",
        "## Temas generales",
    ]
    lines.extend(f"- {topic}" for topic in catalog["topic_overview"])
    lines.extend(["", "## Documentos"])
    if not catalog["documents"]:
        lines.append("- No hay documentos Markdown procesados.")
    for entry in catalog["documents"]:
        lines.append(f"- **{entry['title']}** (fuente: {entry['source']})")
        if entry["description"]:
            lines.append(f"  - Temas: {entry['description']}")
        if entry["search_terms"]:
            lines.append(f"  - Búsquedas relacionadas: {'; '.join(entry['search_terms'][:5])}")
    return "\n".join(lines).rstrip() + "\n"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def write_document_catalog(
    markdown_root: Path,
    json_path: Path,
    markdown_path: Path,
    *,
    bot_id: str,
    display_name: str,
    dependency_name: str,
    scope_description: str,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    entries = build_document_catalog(markdown_root, manifest_path)
    catalog = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bot": {
            "bot_id": bot_id,
            "display_name": _safe_text(display_name, 120),
            "dependency_name": _safe_text(dependency_name, 160),
            "scope_description": _safe_text(scope_description, 500),
        },
        "document_count": len(entries),
        "topic_overview": _topic_overview(entries),
        "documents": entries,
    }
    _atomic_write(json_path, json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    _atomic_write(markdown_path, _catalog_markdown(catalog))
    return catalog


@lru_cache(maxsize=256)
def _read_document_catalog_cached(path_text: str, modified_ns: int, size: int) -> dict[str, Any]:
    del modified_ns, size  # The stat fingerprint invalidates stale cache entries.
    try:
        payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def read_document_catalog(json_path: Path) -> dict[str, Any]:
    try:
        path = json_path.resolve()
        stat = path.stat()
    except OSError:
        return {}
    return _read_document_catalog_cached(str(path), stat.st_mtime_ns, stat.st_size)


def relevant_document_cards(json_path: Path, question: str, limit: int = 4) -> list[dict[str, Any]]:
    """Return only compact metadata cards with lexical evidence for this question."""
    catalog = read_document_catalog(json_path)
    query_terms = {
        term for term in _normalize(question).split()
        if len(term) >= 3 and term not in {_normalize(item) for item in _STOP_WORDS}
    }
    if not query_terms:
        return []
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for entry in catalog.get("documents", []):
        if not isinstance(entry, dict):
            continue
        title_terms = set(_normalize(str(entry.get("title") or "")).split())
        description_terms = set(_normalize(str(entry.get("description") or "")).split())
        source_terms = set(_normalize(str(entry.get("source") or "")).split())
        search_phrases = [str(term) for term in entry.get("search_terms", []) if term]
        search_terms = set(_normalize(" ".join(search_phrases)).split())
        score = (
            5 * len(query_terms & title_terms)
            + 3 * len(query_terms & search_terms)
            + 2 * len(query_terms & description_terms)
            + len(query_terms & source_terms)
        )
        normalized_query = _normalize(question)
        if any(len(_normalize(phrase)) > 5 and _normalize(phrase) in normalized_query for phrase in search_phrases):
            score += 3
        if score:
            scored.append((score, str(entry.get("title") or "").casefold(), entry))
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [
        {
            "title": str(entry.get("title") or "")[:180],
            "source": str(entry.get("source") or "")[:180],
            "description": str(entry.get("description") or "")[:360],
            "search_terms": [str(term)[:140] for term in entry.get("search_terms", [])[:5]],
        }
        for _, _, entry in scored[:max(0, limit)]
    ]


def unimon_catalog_paths() -> tuple[Path, Path, Path, Path]:
    """Return UniMon's private catalog files and the sanitized corpus locations."""
    from app.config import get_settings

    settings = get_settings()
    markdown_root = Path(settings.sanitized_docs_dir).resolve() / "markdown"
    manifest_path = Path(settings.sanitized_docs_dir).resolve() / "manifest.json"
    catalog_root = Path(settings.docs_dir).resolve().parent / "chatbots" / "unimon"
    return markdown_root, manifest_path, catalog_root / "specialization.json", catalog_root / "specialization.md"


def refresh_unimon_document_catalog() -> dict[str, Any]:
    """Rebuild UniMon TI's catalog from its sanitized Markdown corpus."""
    markdown_root, manifest_path, json_path, markdown_path = unimon_catalog_paths()
    return write_document_catalog(
        markdown_root,
        json_path,
        markdown_path,
        bot_id="unimon",
        display_name="UniMon Soporte TI",
        dependency_name="Mesa de Ayuda TI",
        scope_description=(
            "Asistente predeterminado de soporte técnico de primera línea: cuentas y acceso, correo y Teams, "
            "computadores y periféricos, conectividad, aplicaciones institucionales, instalación autorizada "
            "de software y orientación básica de seguridad."
        ),
        manifest_path=manifest_path,
    )

