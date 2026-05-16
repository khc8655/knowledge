"""Tests for the EvidencePackBuilder service."""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.models import get_db, init_db
from evidence.pack import EvidencePackBuilder

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_card(
    card_id="card-001",
    card_type="parameter",
    source_type="excel",
    title="Server CPU",
    body="Intel Xeon E-2388G, 8C/16T",
    quality_tier="high",
    report_meta=None,
    is_current=1,
    scan_available=True,
    semantic=None,
    doc_file="specs.xlsx",
    path="specs.xlsx > Server CPU",
):
    if semantic is None:
        semantic = {"quality_tier": quality_tier, "intent_tags": ["hardware"]}
    return {
        "id": card_id,
        "card_type": card_type,
        "source_type": source_type,
        "title": title,
        "body": body,
        "report_meta": report_meta,
        "is_current": is_current,
        "scan_available": scan_available,
        "semantic": semantic,
        "doc_file": doc_file,
        "path": path,
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

def test_build_evidence_from_cards():
    """build() maps card fields to evidence items correctly."""
    builder = EvidencePackBuilder()

    cards = [
        _make_card("c1", card_type="price", quality_tier="high"),
        _make_card("c2", card_type="capability", quality_tier="medium"),
        _make_card("c3", card_type="scenario", quality_tier="low"),
        _make_card("c4", card_type="architecture", quality_tier="placeholder"),
        _make_card("c5", card_type="update"),
        _make_card(
            "c6",
            card_type="parameter",
            report_meta={"valid_to": "2020-01-01T00:00:00Z"},
        ),
    ]

    evidences = builder.build(cards, task_type="proposal", project_id="proj-1")
    assert len(evidences) == 6

    # Type mapping
    assert evidences[0]["evidence_type"] == "price"
    assert evidences[1]["evidence_type"] == "parameter"  # capability->parameter
    assert evidences[2]["evidence_type"] == "scenario"
    assert evidences[3]["evidence_type"] == "architecture"
    assert evidences[4]["evidence_type"] == "update"
    assert evidences[5]["evidence_type"] == "report"  # has report_meta

    # Confidence scores
    assert evidences[0]["confidence"] == 0.95
    assert evidences[1]["confidence"] == 0.75
    assert evidences[2]["confidence"] == 0.4
    assert evidences[3]["confidence"] == 0.1

    # Freshness
    assert evidences[5]["freshness"] == "expired"

    # Risk flags — report_meta with valid_to in the past => expired_certificate
    flags5 = json.loads(evidences[5]["risk_flags"])
    assert "expired_certificate" in flags5

    # All fields present
    for ev in evidences:
        assert ev["project_id"] == "proj-1"
        assert ev["id"]
        assert ev["claim"]
        assert ev["source"]
        assert ev["created_at"]


def test_persist_and_get_evidence():
    """persist() writes to DB and get() retrieves it."""
    builder = EvidencePackBuilder()
    cards = [_make_card("card-p1"), _make_card("card-p2")]
    evidences = builder.build(cards, task_type="tender", project_id="proj-2")

    pack_id = builder.persist(evidences, project_id="proj-2", created_by_task_id="task-abc")
    assert pack_id is not None

    # Retrieve each
    for ev in evidences:
        loaded = builder.get(ev["id"])
        assert loaded is not None
        assert loaded["project_id"] == "proj-2"
        assert loaded["source_card_id"] == ev["source_card_id"]
        assert loaded["created_by_task_id"] == "task-abc"

    # Non-existent returns None
    assert builder.get("does-not-exist") is None


def test_list_by_project():
    """list_by_project() returns active (non-archived) evidence for a project."""
    builder = EvidencePackBuilder()

    # Insert 3 items for proj-A
    cards_a = [_make_card(f"a-{i}", title=f"Card A{i}") for i in range(3)]
    evs_a = builder.build(cards_a, task_type="proposal", project_id="proj-A")
    builder.persist(evs_a, project_id="proj-A")

    # Insert 2 items for proj-B
    cards_b = [_make_card(f"b-{i}", title=f"Card B{i}") for i in range(2)]
    evs_b = builder.build(cards_b, task_type="proposal", project_id="proj-B")
    builder.persist(evs_b, project_id="proj-B")

    # Only proj-A items returned
    result_a = builder.list_by_project("proj-A")
    assert len(result_a) == 3

    result_b = builder.list_by_project("proj-B")
    assert len(result_b) == 2

    # Empty for unknown project
    assert builder.list_by_project("proj-Z") == []


def test_archive_evidence():
    """archive() sets archived_at and item disappears from default listing."""
    builder = EvidencePackBuilder()

    cards = [_make_card("arc-1"), _make_card("arc-2")]
    evidences = builder.build(cards, task_type="proposal", project_id="proj-C")
    builder.persist(evidences, project_id="proj-C")

    # Before archive — both visible
    assert len(builder.list_by_project("proj-C")) == 2

    # Archive the first
    target_id = evidences[0]["id"]
    assert builder.archive(target_id) is True

    # After archive — only one visible by default
    visible = builder.list_by_project("proj-C")
    assert len(visible) == 1
    assert visible[0]["id"] == evidences[1]["id"]

    # include_archived=True shows both
    all_items = builder.list_by_project("proj-C", include_archived=True)
    assert len(all_items) == 2

    # Archived item has archived_at set
    archived = builder.get(target_id)
    assert archived["archived_at"] is not None

    # Archiving again returns False (already archived)
    assert builder.archive(target_id) is False
