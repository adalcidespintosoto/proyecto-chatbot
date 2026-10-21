from pathlib import Path

from app.services.bot_instance_service import is_retryable_unindexed_record


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_direct_instance_upload_uses_repairable_fidelity_audit_before_indexing():
    html = (PROJECT_ROOT / "app" / "static" / "admin.html").read_text(encoding="utf-8")
    handler_start = "direct.addEventListener('click', async () => {"
    start = html.index(handler_start)
    handler_end = html.index("\n      });", start)
    handler = html[start:handler_end]

    assert "/documents/audit" in handler
    assert "renderReviewRequired(data)" in handler
    assert "resolveUpload('force')" in handler
    assert "postFile(`/api/admin/chatbot-instances/${encodeURIComponent(botId)}/documents`, state.file)" not in handler


def test_same_source_can_be_retried_only_when_fidelity_blocked_and_not_indexed():
    source_hash = "a" * 64
    failed_record = {
        "source_sha256": source_hash,
        "fidelity_audit": {"status": "revisar"},
        "indexed_chunk_count": 0,
    }
    indexed_record = {
        **failed_record,
        "fidelity_audit": {"status": "coincide"},
        "indexed_sha256": source_hash,
        "indexed_chunk_count": 10,
    }
    retry_after_successful_audit = {
        **failed_record,
        "fidelity_audit": {"status": "coincide"},
    }
    record_with_index_timestamp = {
        **failed_record,
        "indexed_at_utc": "2026-10-21T12:00:00Z",
    }

    assert is_retryable_unindexed_record(failed_record, source_hash)
    assert not is_retryable_unindexed_record(failed_record, "b" * 64)
    assert not is_retryable_unindexed_record(indexed_record, source_hash)
    assert not is_retryable_unindexed_record(retry_after_successful_audit, source_hash)
    assert not is_retryable_unindexed_record(record_with_index_timestamp, source_hash)
