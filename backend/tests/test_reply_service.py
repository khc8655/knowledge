"""Tests for ReplyService."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.models import get_db, init_db
from services.reply_service import ReplyService, _sanitize_internal_notes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_evidence(
    evidence_id="ev-001",
    claim="SM2 encryption supported",
    body="The terminal supports SM2 encryption algorithm.",
    confidence=0.9,
    risk_flags=None,
    project_id="proj-1",
):
    if risk_flags is None:
        risk_flags = json.dumps([])
    return {
        "id": evidence_id,
        "project_id": project_id,
        "source_card_id": "card-001",
        "source_type": "excel",
        "evidence_type": "parameter",
        "claim": claim,
        "body": body,
        "source": "specs.xlsx > SM2",
        "confidence": confidence,
        "freshness": "current",
        "risk_flags": risk_flags,
        "created_at": "2026-01-01T00:00:00Z",
        "archived_at": None,
    }


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    """Point DB at a temporary file so tests don't touch production data."""
    db_file = tmp_path / "platform.db"
    monkeypatch.setattr("db.models.DB_PATH", db_file)
    conn = get_db()
    init_db(conn)
    conn.close()
    yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_with_evidence():
    """Reply is built from evidence claims and persisted to DB."""
    conn = get_db()
    svc = ReplyService(conn)

    evidences = [
        _make_evidence("ev-1", claim="支持SM2加密", body="终端支持国密SM2算法", confidence=0.95),
        _make_evidence("ev-2", claim="支持SIP协议", body="支持SIP和H.323双协议栈", confidence=0.8),
    ]

    result = svc.generate(
        customer_question="你们的终端支持哪些加密算法？",
        evidences=evidences,
        project_id="proj-1",
        tone="neutral",
    )

    assert result["output_id"] is not None
    assert "SM2" in result["reply_text"]
    assert "SIP" in result["reply_text"]
    assert result["risk_summary"]["total_evidence"] == 2
    assert result["risk_summary"]["avg_confidence"] == 0.88
    assert result["internal_evidence"] == []

    # Verify persisted in DB
    cur = conn.cursor()
    cur.execute("SELECT * FROM project_outputs WHERE id = ?", (result["output_id"],))
    row = cur.fetchone()
    assert row is not None
    assert dict(row)["output_type"] == "reply"
    conn.close()


def test_no_evidence_returns_uncertain():
    """No evidence -> reply with uncertain/disclaimer text."""
    conn = get_db()
    svc = ReplyService(conn)

    result = svc.generate(
        customer_question="你们支持什么协议？",
        evidences=[],
        project_id="proj-1",
        tone="neutral",
    )

    assert result["output_id"] is not None
    assert "暂无" in result["reply_text"] or "待确认" in result["reply_text"]
    assert result["internal_evidence"] == []
    assert result["risk_summary"] == {}
    conn.close()


def test_filters_internal_notes():
    """Internal/confidential notes are stripped from reply text."""
    conn = get_db()
    svc = ReplyService(conn)

    evidences = [
        _make_evidence(
            "ev-10",
            claim="支持4K分辨率",
            body="终端支持4K分辨率。[内部备注:竞品对比已过时]最高可达60fps。[confidential:内部定价信息]性能优异。",
            confidence=0.9,
        ),
    ]

    result = svc.generate(
        customer_question="终端分辨率多少？",
        evidences=evidences,
        project_id="proj-1",
    )

    # Internal notes must not appear in the reply
    reply = result["reply_text"]
    assert "[内部备注:" not in reply
    assert "[confidential:" not in reply
    # But the useful content should remain
    assert "4K" in reply
    # Internal evidence should record the sanitization
    assert len(result["internal_evidence"]) == 1
    conn.close()
