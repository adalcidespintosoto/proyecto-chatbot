from pathlib import Path

from langchain_core.documents import Document

from app.services.sanitized_documents import (
    expected_source_markers,
    format_extracted_source,
    load_document_prompt,
    normalize_source_citations,
    split_markdown_for_rag,
    validate_sanitized_markdown,
)


def test_format_source_keeps_page_order_and_labels_vision_as_unverified():
    pages = [
        Document(page_content="Paso dos [Imagen: botón Guardar]", metadata={"page_number": 2}),
        Document(page_content="Paso uno", metadata={"page_number": 1}),
    ]

    result = format_extracted_source("manual.pdf", pages)

    assert result.index("[PÁGINA 1]") < result.index("[PÁGINA 2]")
    assert "Descripción automática de imagen, no verificada" in result


def test_validation_requires_heading_and_citation_for_every_extracted_page():
    errors = validate_sanitized_markdown(
        "# Manual\nPaso 1. (Fuente: página 1)",
        [("PÁGINA", 1), ("PÁGINA", 2)],
    )

    assert len(errors) == 1
    assert "página 2" in errors[0]


def test_validation_accepts_citation_ranges_and_slide_citations():
    errors = validate_sanitized_markdown(
        "# Manual\nPasos. (Fuente: páginas 1–2) (Fuente: diapositiva 3)",
        [("PÁGINA", 1), ("PÁGINA", 2), ("DIAPOSITIVA", 3)],
    )

    assert errors == []


def test_validation_accepts_common_page_abbreviations():
    errors = validate_sanitized_markdown(
        "# Manual\nPaso. (Fuente: p. 8) (Fuente: pág. 9)",
        [("PÁGINA", 8), ("PÁGINA", 9)],
    )

    assert errors == []


def test_validation_accepts_page_and_slide_lists_in_one_citation():
    errors = validate_sanitized_markdown(
        "# Manual\nResumen. (Fuente: páginas 2–3, 7, 12, 15 y 20) "
        "(Fuente: diapositivas 1, 4 y 8)",
        [("PÁGINA", number) for number in (2, 3, 7, 12, 15, 20)]
        + [("DIAPOSITIVA", number) for number in (1, 4, 8)],
    )

    assert errors == []


def test_normalizes_wrong_pdf_citation_labels_without_changing_prose():
    result = normalize_source_citations(
        "# Manual\nLa diapositiva 2 contiene el paso. (Fuente: diapositivas 1–3)",
        [("PÁGINA", 1), ("PÁGINA", 2), ("PÁGINA", 3)],
    )

    assert "La diapositiva 2 contiene el paso." in result
    assert "(Fuente: páginas 1–3)" in result


def test_normalizes_wrong_pptx_citation_labels():
    result = normalize_source_citations(
        "# Manual\n(Fuente: páginas 4 y 5)",
        [("DIAPOSITIVA", 4), ("DIAPOSITIVA", 5)],
    )

    assert "(Fuente: diapositivas 4 y 5)" in result


def test_expected_markers_skip_only_title_only_divider_units():
    pages = [
        Document(page_content="ACCESO AL SISTEMA", metadata={"page_number": 1}),
        Document(page_content="INGRESE AL PORTAL Y SELECCIONE EL BOTÓN CONTINUAR", metadata={"page_number": 2}),
        Document(page_content="Contacte a ti@example.edu si falla", metadata={"page_number": 3}),
    ]

    assert expected_source_markers(pages) == [("PÁGINA", 2), ("PÁGINA", 3)]


def test_expected_markers_skip_short_heading_pages_but_keep_short_facts():
    pages = [
        Document(page_content="Ingreso a la plataforma", metadata={"page_number": 1}),
        Document(page_content="Postulación a convocatoria", metadata={"page_number": 2}),
        Document(page_content="Gestión de postulaciones", metadata={"page_number": 3}),
        Document(page_content="Usuario y contraseña al final del recibo", metadata={"page_number": 4}),
    ]

    assert expected_source_markers(pages) == [("PÁGINA", 4)]


def test_expected_markers_skip_non_actionable_image_only_page_but_keep_ui_page():
    pages = [
        Document(
            page_content="[Imagen: La imagen muestra un logotipo institucional y un árbol con tres ramas.]",
            metadata={"page_number": 1},
        ),
        Document(
            page_content="[Imagen: La captura muestra un campo Usuario y el botón Continuar.]",
            metadata={"page_number": 2},
        ),
    ]

    assert expected_source_markers(pages) == [("PÁGINA", 2)]


def test_expected_markers_skip_cover_page_with_copyright_metadata():
    cover = Document(
        page_content=(
            "Manual de Usuario - Administrador de transacciones\n"
            "Generación Link de pago\n"
            "Paymentez SAS 2019© Todos los derechos reservados | Documento confidencial"
        ),
        metadata={"page_number": 1},
    )

    assert expected_source_markers([cover]) == []


def test_split_markdown_preserves_source_identity_and_page_metadata():
    chunks = split_markdown_for_rag(
        "# Manual\n" + ("Contenido de soporte. (Fuente: página 7) " * 20),
        {"source": "manual.pdf", "source_type": "sanitized_markdown"},
        chunk_size=140,
        chunk_overlap=20,
    )

    assert len(chunks) > 1
    assert all(chunk.metadata["source"] == "manual.pdf" for chunk in chunks)
    assert all(chunk.metadata["source_type"] == "sanitized_markdown" for chunk in chunks)
    assert all(chunk.metadata["page_number"] == 7 for chunk in chunks)
    assert [chunk.metadata["chunk_index"] for chunk in chunks] == list(range(len(chunks)))


def test_load_document_prompt_reads_the_fenced_text_block(tmp_path: Path):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Antes\n```text\nReglas\n[CONTENIDO EXTRAÍDO]\n```\nDespués", encoding="utf-8")

    assert load_document_prompt(prompt_file) == "Reglas\n[CONTENIDO EXTRAÍDO]"
