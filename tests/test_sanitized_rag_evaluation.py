from scripts.evaluate_sanitized_rag import parse_sources


def test_parse_sources_preserves_commas_inside_document_names():
    assert parse_sources(
        "Calificaciones.pdf, Proyección (agregar, elimnar, homologar).pptx"
    ) == [
        "Calificaciones.pdf",
        "Proyección (agregar, elimnar, homologar).pptx",
    ]


def test_parse_sources_keeps_json_lists():
    assert parse_sources('["Manual, Parte 1.pdf", "Teams.pptx"]') == [
        "Manual, Parte 1.pdf",
        "Teams.pptx",
    ]


def test_parse_sources_supports_semicolon_delimited_documents():
    assert parse_sources("Manual.pdf; Guía.pptx") == ["Manual.pdf", "Guía.pptx"]
