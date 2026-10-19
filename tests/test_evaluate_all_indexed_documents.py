import asyncio

import pytest

from scripts.evaluate_all_indexed_documents import (
    generate_group,
    judge_group,
    repair_duplicate_questions,
    validate_generated_group,
)


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


def test_validate_generated_group_accepts_exact_quote_of_twenty_characters():
    document = _document()
    payload = _generated_payload(document, 1)
    payload["documents"][0]["questions"][0]["evidence_quote"] = document["segments"][0]["text"][:20]

    cases = validate_generated_group([document], payload, 1)

    assert len(cases[0]["evidence_quote"]) == 20
    assert cases[0]["evidence_valid"] is True


def test_validate_generated_group_flags_questions_without_document_topic():
    document = _document()
    document["source"] = "1. Estudiantes Nuevos Pregrado.pptx"
    other = _document()
    other["source"] = "2. Estudiantes Antiguos Pregrado.pptx"
    payload = _generated_payload(document, 1)
    payload["documents"].append(_generated_payload(other, 1)["documents"][0])

    cases = validate_generated_group([document, other], payload, 1)

    assert len(cases) == 2
    assert all(case["topic_anchor_valid"] is False for case in cases)


def test_sparse_source_creates_five_distinct_unanswerable_probes():
    document = _document()
    document["segments"] = [{"page": "1", "text": "La guía describe acceso inicial al sistema institucional."}]
    document["full_text"] = document["segments"][0]["text"]

    cases, model = asyncio.run(generate_group([document], llm=None, questions_per_document=5))

    assert model == "unanswerable_indexed_source"
    assert len(cases) == 5
    assert len({case["question"] for case in cases}) == 5
    assert all(case["expected_answerable"] is False for case in cases)


def test_repair_duplicate_questions_keeps_the_answer_key_and_makes_question_unique():
    class FakeLLM:
        async def chat_completion(self, messages, max_tokens=500):
            return {"content": '{"question":"¿Qué opciones debo elegir en SIAAF WEB para generar el consolidado?"}', "model": "fake"}

    cases = [
        {
            "case_id": "doc1-q1",
            "source": "Reporte - Asignacion Academica.pdf",
            "question": "¿Cómo genero el consolidado de asignación académica general en SIAAF WEB?",
            "reference_answer": "Selecciona General y presiona Buscar.",
            "evidence_quote": "Seleccione General y presione Buscar.",
            "topic_anchor_valid": True,
        },
        {
            "case_id": "doc2-q1",
            "source": "Reporte - Asignacion Academica.pptx",
            "question": "¿Cómo genero el Consolidado de Asignación Académica General en SIAAF WEB?",
            "reference_answer": "Selecciona General y presiona Buscar.",
            "evidence_quote": "Seleccione General y presione Buscar.",
            "topic_anchor_valid": True,
        },
    ]
    original_answer = cases[1]["reference_answer"]

    repairs = asyncio.run(repair_duplicate_questions(cases, FakeLLM()))

    assert len(repairs) == 1
    assert cases[0]["question"].casefold() != cases[1]["question"].casefold()
    assert cases[1]["reference_answer"] == original_answer


def test_judge_retries_malformed_json_and_scores_all_cases():
    class FakeLLM:
        def __init__(self):
            self.responses = [
                {"content": "not json"},
                {"content": '{"items":[{"id":"case-1","verdict":"correct","confidence":0.99,"reason":"La respuesta coincide con la fuente."}]}'}
            ]

        async def chat_completion(self, messages, max_tokens=1800):
            return self.responses.pop(0)

    quote = "Para completar el proceso, seleccione la opción indicada en el portal."
    row = {
        "case_id": "case-1",
        "question": "¿Cómo completo este trámite en el portal?",
        "source": "Guia de prueba.pdf",
        "expected_source_found": True,
        "evidence_quote": quote,
        "evidence_valid": True,
        "expected_answerable": True,
        "reference_answer": "Selecciona la opción indicada en el portal.",
        "sources": ["Guia de prueba.pdf"],
        "answer": "Selecciona la opción indicada en el portal.",
        "http_status": 200,
    }

    reviewed = asyncio.run(judge_group([row], FakeLLM(), {"Guia de prueba.pdf": {"full_text": quote}}))

    assert reviewed[0]["quality_review"]["verdict"] == "correct"
