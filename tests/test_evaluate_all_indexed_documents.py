import asyncio

import pytest

from scripts.evaluate_all_indexed_documents import generate_group, validate_generated_group


def _document():
    quote = "Para completar el proceso, ingrese al portal institucional y seleccione la opción indicada."
    return {
        "source_order": 1,
        "source": "Guia de prueba.pdf",
        "full_text": f"Introducción. {quote} Información complementaria para contextualizar el trámite.",
        "chunk_count": 2,
        "segments": [{"page": "2", "text": quote}],
    }


def _generated_payload(document, count):
    quote = document["segments"][0]["text"]
    return {
        "documents": [{
            "source": document["source"],
            "questions": [{
                "question": f"Consulta coloquial número {index}: ¿qué hago en este paso?",
                "reference_answer": "Debes ingresar al portal institucional y elegir la opción indicada.",
                "answerable": True,
                "evidence_quote": quote,
                "page": "2",
            } for index in range(1, count + 1)],
        }]
    }


def test_validate_generated_group_accepts_five_unique_grounded_questions():
    document = _document()

    cases = validate_generated_group([document], _generated_payload(document, 5), 5)

    assert len(cases) == 5
    assert [case["question_number_for_source"] for case in cases] == [1, 2, 3, 4, 5]
    assert all(case["evidence_valid"] for case in cases)
    assert all(case["expected_answerable"] for case in cases)


def test_validate_generated_group_rejects_wrong_question_count():
    document = _document()

    with pytest.raises(ValueError, match="Se esperaban 5 preguntas"):
        validate_generated_group([document], _generated_payload(document, 4), 5)


def test_validate_generated_group_rejects_questions_without_document_topic():
    document = _document()
    document["source"] = "1. Estudiantes Nuevos Pregrado.pptx"
    other = _document()
    other["source"] = "2. Estudiantes Antiguos Pregrado.pptx"
    payload = _generated_payload(document, 1)

    with pytest.raises(ValueError, match="no nombra el tema distintivo"):
        validate_generated_group([document, other], payload, 1)


def test_sparse_source_creates_five_distinct_unanswerable_probes():
    document = _document()
    document["segments"] = [{"page": "1", "text": "La guía describe acceso inicial al sistema institucional."}]
    document["full_text"] = document["segments"][0]["text"]

    cases, model = asyncio.run(generate_group([document], llm=None, questions_per_document=5))

    assert model == "unanswerable_indexed_source"
    assert len(cases) == 5
    assert len({case["question"] for case in cases}) == 5
    assert all(case["expected_answerable"] is False for case in cases)
