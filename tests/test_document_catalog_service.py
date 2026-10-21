from __future__ import annotations

import json
from pathlib import Path

from app.services.document_catalog_service import (
    build_document_catalog,
    relevant_document_cards,
    write_document_catalog,
)


def test_catalog_covers_all_markdown_and_does_not_copy_document_body(tmp_path: Path):
    markdown_root = tmp_path / "markdown"
    markdown_root.mkdir()
    for index in range(45):
        (markdown_root / f"guia_{index:02}.md").write_text(
            f"# Guía de trámite {index}\n\n"
            "## Información del documento\n"
            f"- Fuente original: guia_{index:02}.pdf\n"
            "- Temas incluidos: matrícula, pagos y certificados.\n\n"
            "## Palabras y formas de búsqueda\n"
            "- cómo pagar la matrícula; descargar el recibo\n\n"
            "## Procedimiento\n"
            "Este párrafo completo pertenece al documento y no debe ir al catálogo.\n",
            encoding="utf-8",
        )

    entries = build_document_catalog(markdown_root)

    assert len(entries) == 45
    assert entries[-1]["title"] == "Guía de trámite 44"
    assert "matrícula, pagos y certificados" in entries[-1]["description"]
    assert "párrafo completo" not in json.dumps(entries, ensure_ascii=False)


def test_written_catalog_is_searchable_by_document_topics_and_query_variants(tmp_path: Path):
    markdown_root = tmp_path / "markdown"
    markdown_root.mkdir()
    (markdown_root / "icetex.md").write_text(
        "# Renovación de crédito ICETEX\n\n"
        "- Temas incluidos: actualización de datos y renovación de financiación educativa.\n\n"
        "## Palabras y formas de búsqueda\n"
        "- renovar el crédito; seguir financiando mis estudios\n",
        encoding="utf-8",
    )
    (markdown_root / "teams.md").write_text(
        "# Acceso a Microsoft Teams\n\n"
        "- Temas incluidos: inicio de sesión y cuenta institucional.\n",
        encoding="utf-8",
    )
    json_path = tmp_path / "specialization.json"
    markdown_path = tmp_path / "specialization.md"

    write_document_catalog(
        markdown_root,
        json_path,
        markdown_path,
        bot_id="casa-blanca",
        display_name="Casa Blanca",
        dependency_name="Admisiones",
        scope_description="Matrícula, pagos y financiación.",
    )

    matches = relevant_document_cards(json_path, "quiero seguir financiando mis estudios", limit=2)

    assert matches[0]["title"] == "Renovación de crédito ICETEX"
    assert all(item["title"] != "Acceso a Microsoft Teams" for item in matches)
    assert "Este párrafo completo" not in markdown_path.read_text(encoding="utf-8")


def test_catalog_manifest_excludes_failed_or_unindexed_markdown(tmp_path: Path):
    markdown_root = tmp_path / "markdown"
    markdown_root.mkdir()
    (markdown_root / "good.md").write_text("# Guía vigente\n- Temas incluidos: matrícula y pagos.", encoding="utf-8")
    (markdown_root / "failed.md").write_text("# Documento fallido\n- Temas incluidos: datos incompletos.", encoding="utf-8")
    (markdown_root / "pending.md").write_text("# Documento pendiente\n- Temas incluidos: pagos pendientes.", encoding="utf-8")
    web_root = markdown_root / "public_web"
    web_root.mkdir()
    (web_root / "fragment.md").write_text("# Portal de estudiantes\n- Temas incluidos: acceso a portales institucionales.", encoding="utf-8")
    (web_root / "fragment_2.md").write_text("# Portal de estudiantes\n- Temas incluidos: acceso a servicios académicos.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"records": {
        "good.pdf": {"status": "success", "source_sha256": "abc", "indexed_sha256": "abc", "markdown_relative_path": "markdown/good.md", "source_filename": "good.pdf"},
        "failed.pdf": {"status": "failed", "markdown_relative_path": "markdown/failed.md", "source_filename": "failed.pdf"},
        "pending.pdf": {"status": "success", "source_sha256": "def", "markdown_relative_path": "markdown/pending.md", "source_filename": "pending.pdf"},
        "web::portal": {"status": "success", "source_sha256": "web", "indexed_sha256": "web", "source_filename": "portal.md", "source_type": "public_web_ui", "source_title": "Portal institucional", "markdown_parts": [
            {"markdown_relative_path": "markdown/public_web/fragment.md", "source_metadata": {"section": "Portales"}},
            {"markdown_relative_path": "markdown/public_web/fragment_2.md", "source_metadata": {"section": "Portales"}},
        ]},
    }}), encoding="utf-8")

    entries = build_document_catalog(markdown_root, manifest_path)

    assert {item["title"] for item in entries} == {"Guía vigente", "Portal institucional — Portales"}
    assert len(entries) == 2
