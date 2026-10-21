"""Helpers for turning extracted source units into traceable RAG Markdown."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


_PROMPT_BLOCK = re.compile(r"```text\s*(.*?)\s*```", flags=re.DOTALL | re.IGNORECASE)
_CITATION = re.compile(
    r"(?P<label>p[aá]ginas?|p[aá]g\.?|pp?\.?|pages?|diapositivas?|secciones?|sections?)\s*"
    r"(?P<sequence>\d+(?:\s*(?:[-–—]\s*\d+|[,;]\s*\d+|\by\b\s*\d+))*)",
    flags=re.IGNORECASE,
)
_IMAGE_DESCRIPTION = re.compile(r"\[Imagen:\s*(.*?)\]", flags=re.DOTALL | re.IGNORECASE)
_SOURCE_CITATION_LABEL = re.compile(
    r"(?P<prefix>\bfuentes?\s*:\s*)"
    r"(?P<label>p[aá]ginas?|p[aá]g\.?|pp?\.?|pages?|diapositivas?|secciones?|sections?)",
    flags=re.IGNORECASE,
)
_PROCEDURAL_VERB = re.compile(
    r"\b(abr[ae]|acced[ae]|adjunt[ae]|carg[ae]|clic|configur[ae]|continu[ae]|"
    r"descarg[ae]|dig[ií]t[ae]|envi[ae]|ingres[ae]|inici[ae]|instal[ae]|"
    r"seleccion[ae]|marc[ae]|presion[ae]|puls[ae]|registr[ae]|siga|sigue|"
    r"utilic[ae]|us[ae]|guard[ae]|escrib[ae]|haga|realic[ae]|solicit[ae]|"
    r"tramite|tramitar|debe|debes|deber[aá]n?|puede|pueden|podr[aá]n?|"
    r"necesita|necesitan|requier[ae]|ingresar|seleccionar|presionar|guardar|"
    r"es|son|est[aá]n?|tiene|tienen|permite|incluye|contiene|encuentra|"
    r"aparece|corresponde|consiste)\b",
    flags=re.IGNORECASE,
)
_FACTUAL_CUE = re.compile(
    r"\b(usuario|contrase[nñ]a|clave|correo|cuenta|credenciales|recibo|"
    r"matr[ií]cula|pago|fecha|plazo|valor|costo|requisito|permiso|"
    r"tel[eé]fono|contacto|direcci[oó]n|equipo|computador|red|wifi|vpn|"
    r"error|solicitud|soporte|canal|documento)\b",
    flags=re.IGNORECASE,
)
_COVER_METADATA = re.compile(
    r"\b(manual(?:\s+de\s+usuario)?|instructivo|gu[ií]a)\b.*"
    r"\b(derechos reservados|confidencial|copyright)\b|©",
    flags=re.IGNORECASE | re.DOTALL,
)


def _iter_citation_refs(text: str):
    """Yield citation spans and all page/slide numbers in ranges or lists."""
    for match in _CITATION.finditer(text):
        label = match.group("label").casefold()
        if "diapositiva" in label:
            kind = "DIAPOSITIVA"
        elif "secci" in label or "section" in label:
            kind = "SECCIÓN"
        else:
            kind = "PÁGINA"
        numbers: set[int] = set()
        sequence = match.group("sequence")
        for item in re.split(r"\s*(?:,|;|\by\b)\s*", sequence, flags=re.IGNORECASE):
            item = item.strip()
            range_match = re.fullmatch(r"(\d+)\s*[-–—]\s*(\d+)", item)
            if range_match:
                first, last = map(int, range_match.groups())
                if last >= first and last - first <= 100:
                    numbers.update(range(first, last + 1))
            elif item.isdigit():
                numbers.add(int(item))
        if numbers:
            yield match.start(), match.end(), kind, numbers


def load_document_prompt(path: Path) -> str:
    """Read the model prompt from the fenced block in the maintained prompt doc."""
    document = path.read_text(encoding="utf-8")
    match = _PROMPT_BLOCK.search(document)
    if not match:
        raise ValueError(f"No se encontró el bloque de prompt de transformación en {path}")
    prompt = match.group(1).strip()
    if "[CONTENIDO EXTRAÍDO]" not in prompt:
        raise ValueError("El prompt no contiene el marcador [CONTENIDO EXTRAÍDO]")
    return prompt


def expected_source_markers(documents: Sequence[Document]) -> list[tuple[str, int]]:
    """Return required citation markers, excluding short title-only dividers."""
    markers: list[tuple[str, int]] = []
    for document in documents:
        if "slide_number" in document.metadata:
            kind = "DIAPOSITIVA"
            number = document.metadata["slide_number"]
        elif "page_number" in document.metadata:
            kind = "PÁGINA"
            number = document.metadata["page_number"]
        elif "section_number" in document.metadata:
            kind = "SECCIÓN"
            number = document.metadata["section_number"]
        else:
            continue
        if _is_title_only_unit(document.page_content or ""):
            continue
        markers.append((kind, int(number)))
    return sorted(set(markers), key=lambda item: (item[0], item[1]))


def _is_title_only_unit(content: str) -> bool:
    """Identify blank, cover, heading-only units without hiding actionable material."""
    raw = content or ""
    image_descriptions = _IMAGE_DESCRIPTION.findall(raw)
    text = _IMAGE_DESCRIPTION.sub("", raw).strip()
    if not text:
        # Every image description is source content and must be traceable, even
        # when the model says the image contains no readable procedure.
        return not bool(image_descriptions)
    if _COVER_METADATA.search(text) and not _PROCEDURAL_VERB.search(text):
        return True
    if len(text) > 160 or re.search(r"\d|https?://|\b\S+@\S+\b", text, re.IGNORECASE):
        return False
    words = re.findall(r"[\wÁÉÍÓÚÜÑáéíóúüñ]+", text)
    if not words or len(words) > 8 or _PROCEDURAL_VERB.search(text):
        return False
    if _FACTUAL_CUE.search(text) or re.search(r"[.!?;:]", text):
        return False
    letters = [character for character in text if character.isalpha()]
    if not letters:
        return True
    uppercase_ratio = sum(character.isupper() for character in letters) / len(letters)
    if uppercase_ratio >= 0.75:
        return True
    # A short, punctuation-free noun phrase is a common extracted page title
    # (e.g. "Ingreso a la plataforma"). Factual phrases and action language
    # are protected by the checks above.
    return len(text) <= 90 and text.split()[0][:1].isupper()


def normalize_source_citations(markdown: str, markers: Iterable[tuple[str, int]]) -> str:
    """Normalize only citation labels to match the extracted file type.

    Models sometimes call PDF pages slides (or PPTX slides pages). The numeric
    citations remain intact; body prose is deliberately not rewritten.
    """
    kinds = {kind for kind, _ in markers}
    if len(kinds) != 1:
        return markdown
    kind = next(iter(kinds))
    singular, plural = {
        "PÁGINA": ("página", "páginas"),
        "DIAPOSITIVA": ("diapositiva", "diapositivas"),
        "SECCIÓN": ("sección", "secciones"),
    }[kind]

    def replace(match: re.Match[str]) -> str:
        old_label = match.group("label").casefold().rstrip(".")
        is_plural = old_label in {"páginas", "pages", "diapositivas", "secciones", "sections", "pp"}
        return match.group("prefix") + (plural if is_plural else singular)

    return _SOURCE_CITATION_LABEL.sub(replace, markdown)


def format_extracted_source(source_name: str, documents: Sequence[Document]) -> str:
    """Add explicit page/slide boundaries and label local vision descriptions as uncertain."""
    ordered = sorted(
        documents,
        key=lambda document: int(
            document.metadata.get(
                "page_number",
                document.metadata.get("slide_number", document.metadata.get("section_number", 0)),
            )
        ),
    )
    sections = [f"Archivo fuente: {source_name}"]
    for document in ordered:
        if "slide_number" in document.metadata:
            marker = f"[DIAPOSITIVA {int(document.metadata['slide_number'])}]"
        elif "page_number" in document.metadata:
            marker = f"[PÁGINA {int(document.metadata['page_number'])}]"
        elif "section_number" in document.metadata:
            heading = str(document.metadata.get("heading") or "").strip()
            suffix = f": {heading}" if heading else ""
            marker = f"[SECCIÓN {int(document.metadata['section_number'])}{suffix}]"
        else:
            marker = "[SECCIÓN SIN PÁGINA IDENTIFICADA]"

        content = (document.page_content or "").strip()
        content = _IMAGE_DESCRIPTION.sub(
            r"[Descripción automática de imagen, no verificada: \1]", content
        )
        sections.append(f"{marker}\n{content}" if content else marker)
    return "\n\n".join(sections).strip()


def validate_sanitized_markdown(
    markdown: str,
    markers: Iterable[tuple[str, int]],
) -> list[str]:
    """Catch empty output, missing Markdown headings, and omitted page/slide citations."""
    output = (markdown or "").strip()
    if not output:
        return ["La transformación devolvió contenido vacío."]

    errors: list[str] = []
    if not re.search(r"(?m)^#\s+\S", output):
        errors.append("Falta un título Markdown de nivel principal.")

    cited: dict[str, set[int]] = {"PÁGINA": set(), "DIAPOSITIVA": set(), "SECCIÓN": set()}
    for _, _, kind, numbers in _iter_citation_refs(output):
        cited[kind].update(numbers)

    missing = [
        f"{kind.lower()} {number}"
        for kind, number in markers
        if number not in cited.get(kind, set())
    ]
    if missing:
        errors.append("No se encontraron citas para: " + ", ".join(missing[:30]))
    return errors


def split_markdown_for_rag(
    markdown: str,
    metadata: dict,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[Document]:
    """Split generated Markdown with the current RAG size and attach source/page metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    chunks = splitter.create_documents([markdown], metadatas=[dict(metadata)])
    citations = list(_iter_citation_refs(markdown))

    for index, chunk in enumerate(chunks):
        start_index = int(chunk.metadata.get("start_index", 0))
        end_index = start_index + len(chunk.page_content)
        nearby = [citation for citation in citations if citation[0] < end_index and citation[1] > start_index]
        if not nearby and citations:
            previous = [citation for citation in citations if citation[1] <= start_index]
            nearby = [previous[-1] if previous else citations[0]]

        for kind in ("PÁGINA", "DIAPOSITIVA", "SECCIÓN"):
            numbers = sorted({number for _, _, citation_kind, values in nearby if citation_kind == kind for number in values})
            if not numbers:
                continue
            if kind == "PÁGINA":
                chunk.metadata["page_number"] = numbers[0]
                chunk.metadata["source_pages"] = ",".join(map(str, numbers))
            elif kind == "DIAPOSITIVA":
                chunk.metadata["slide_number"] = numbers[0]
                chunk.metadata["source_slides"] = ",".join(map(str, numbers))
            else:
                chunk.metadata["section_number"] = numbers[0]
                chunk.metadata["source_sections"] = ",".join(map(str, numbers))
        chunk.metadata["chunk_index"] = index
    return chunks
