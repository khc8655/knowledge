import tempfile
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from card.store import CardStore

def test_save_and_load_card():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CardStore(data_dir=tmpdir)
        card = {
            "id": "01-01-test-sec-001",
            "doc_file": "test.docx",
            "source_type": "word",
            "title": "Test Section",
            "level": 1,
            "path": "test.docx > Test Section",
            "line_start": 0,
            "char_count": 100,
            "body": "Hello world",
            "tags": [],
            "keywords": [],
            "models": [],
            "related_topics": [],
            "aliases": [],
            "sibling_sections": [],
            "source_weight": 2,
            "report_meta": None,
            "semantic": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        store.save(card)
        loaded = store.get("01-01-test-sec-001")
        assert loaded is not None
        assert loaded["title"] == "Test Section"
        assert loaded["body"] == "Hello world"

def test_list_cards_with_filter():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CardStore(data_dir=tmpdir)
        for i in range(3):
            store.save({
                "id": f"01-0{i+1}-test-sec-001",
                "doc_file": "test.docx",
                "source_type": "word" if i < 2 else "excel",
                "title": f"Section {i}",
                "level": 1,
                "path": f"test.docx > Section {i}",
                "line_start": i * 10,
                "char_count": 50,
                "body": f"Content {i}",
                "tags": [],
                "keywords": [],
                "models": [],
                "related_topics": [],
                "aliases": [],
                "sibling_sections": [],
                "source_weight": 2,
                "report_meta": None,
                "semantic": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            })
        result = store.list_cards(source_type="word")
        assert result["total"] == 2
        result2 = store.list_cards(source_type="excel")
        assert result2["total"] == 1

def test_delete_card():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CardStore(data_dir=tmpdir)
        store.save({
            "id": "01-01-test-sec-001",
            "doc_file": "test.docx",
            "source_type": "word",
            "title": "X",
            "level": 1,
            "path": "test.docx > X",
            "line_start": 0,
            "char_count": 10,
            "body": "body",
            "tags": [],
            "keywords": [],
            "models": [],
            "related_topics": [],
            "aliases": [],
            "sibling_sections": [],
            "source_weight": 2,
            "report_meta": None,
            "semantic": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        assert store.get("01-01-test-sec-001") is not None
        store.delete("01-01-test-sec-001")
        assert store.get("01-01-test-sec-001") is None

def test_update_card():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CardStore(data_dir=tmpdir)
        store.save({
            "id": "01-01-test-sec-001",
            "doc_file": "test.docx",
            "source_type": "word",
            "title": "Old Title",
            "level": 1,
            "path": "test.docx > Old Title",
            "line_start": 0,
            "char_count": 10,
            "body": "old body",
            "tags": [],
            "keywords": [],
            "models": [],
            "related_topics": [],
            "aliases": [],
            "sibling_sections": [],
            "source_weight": 2,
            "report_meta": None,
            "semantic": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
        store.update("01-01-test-sec-001", {"title": "New Title", "tags": ["updated"]})
        loaded = store.get("01-01-test-sec-001")
        assert loaded["title"] == "New Title"
        assert loaded["tags"] == ["updated"]
        assert loaded["body"] == "old body"

def test_card_stats():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CardStore(data_dir=tmpdir)
        for i in range(5):
            store.save({
                "id": f"01-0{i+1}-test-sec-001",
                "doc_file": "test.docx",
                "source_type": "word" if i < 3 else "excel",
                "title": f"S{i}",
                "level": 1,
                "path": f"test.docx > S{i}",
                "line_start": 0,
                "char_count": 10,
                "body": "b",
                "tags": [],
                "keywords": [],
                "models": [],
                "related_topics": [],
                "aliases": [],
                "sibling_sections": [],
                "source_weight": 2,
                "report_meta": None,
                "semantic": {"quality_tier": "high" if i < 2 else "low"},
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            })
        stats = store.stats()
        assert stats["total"] == 5
        assert stats["by_source_type"]["word"] == 3
        assert stats["by_source_type"]["excel"] == 2
