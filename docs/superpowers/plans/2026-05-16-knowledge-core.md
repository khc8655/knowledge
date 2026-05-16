# Knowledge Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the knowledge core: card storage, 5 document pipelines (Word/Markdown/TXT/Excel/PPT), card CRUD API, query service integration, and semantic annotation.

**Architecture:** Cards are stored as individual JSON files in `data/cards/sections/`. Pipelines parse documents into cards. Query service wraps the existing wiki_test engine (`query_unified.py`). Semantic annotation uses LLM to enrich cards with structured metadata.

**Tech Stack:** python-docx, python-pptx, openpyxl, chardet, FastAPI, SQLite, LLM API

**Prerequisites:** Plan 1 (Infrastructure & Job System) must be completed first.

---

## File Structure

```
backend/
├── card/
│   ├── __init__.py
│   └── store.py                  # Create: card read/write/validate
├── pipeline/
│   ├── __init__.py
│   ├── base.py                   # Create: shared pipeline logic
│   ├── word.py                   # Create: Word parser
│   ├── markdown.py               # Create: Markdown parser
│   ├── txt.py                    # Create: TXT parser
│   ├── excel.py                  # Create: Excel profiling + parser
│   └── ppt.py                    # Create: PPT parser
├── services/
│   ├── query_service.py          # Create: query routing + wiki_test integration
│   └── annotate_service.py       # Create: LLM annotation
├── api/
│   ├── card.py                   # Modify: real CRUD implementation
│   └── upload.py                 # Modify: wire to DB + cascade jobs
├── tests/
│   ├── test_card_store.py        # Create
│   ├── test_pipeline_word.py     # Create
│   ├── test_pipeline_md.py       # Create
│   ├── test_pipeline_txt.py      # Create
│   ├── test_pipeline_ppt.py      # Create
│   ├── test_pipeline_excel.py    # Create
│   ├── test_query_service.py     # Create
│   └── test_annotate.py          # Create
```

---

### Task 1: Card Storage Layer

**Files:**
- Create: `backend/card/__init__.py`
- Create: `backend/card/store.py`
- Create: `backend/tests/test_card_store.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_card_store.py
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
        assert loaded["body"] == "old body"  # unchanged fields preserved

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from card.store import CardStore"`
Expected: ImportError

- [ ] **Step 3: Implement CardStore**

```python
# backend/card/store.py
import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


class CardStore:
    def __init__(self, data_dir: str):
        self._sections_dir = os.path.join(data_dir, "cards", "sections")
        os.makedirs(self._sections_dir, exist_ok=True)

    def _card_path(self, card_id: str) -> str:
        return os.path.join(self._sections_dir, f"{card_id}.json")

    def get(self, card_id: str) -> Optional[Dict]:
        path = self._card_path(card_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, card: Dict[str, Any]):
        path = self._card_path(card["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(card, f, ensure_ascii=False, indent=2)

    def update(self, card_id: str, updates: Dict[str, Any]) -> bool:
        card = self.get(card_id)
        if not card:
            return False
        card.update(updates)
        card["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(card)
        return True

    def delete(self, card_id: str) -> bool:
        path = self._card_path(card_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True

    def list_cards(
        self,
        source_type: str = None,
        intent_tag: str = None,
        quality_tier: str = None,
        search: str = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> Dict:
        cards = []
        for fname in os.listdir(self._sections_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._sections_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    card = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            if source_type and card.get("source_type") != source_type:
                continue
            if intent_tag:
                semantic = card.get("semantic") or {}
                tags = semantic.get("intent_tags", [])
                if intent_tag not in tags:
                    continue
            if quality_tier:
                semantic = card.get("semantic") or {}
                if semantic.get("quality_tier") != quality_tier:
                    continue
            if search:
                search_lower = search.lower()
                body = card.get("body", "").lower()
                title = card.get("title", "").lower()
                if search_lower not in body and search_lower not in title:
                    continue

            cards.append(card)

        reverse = sort_order == "desc"
        cards.sort(key=lambda c: c.get(sort_by, ""), reverse=reverse)

        total = len(cards)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": cards[start:end],
        }

    def stats(self) -> Dict:
        by_source = {}
        by_tier = {}
        total = 0
        for fname in os.listdir(self._sections_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self._sections_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    card = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
            total += 1
            st = card.get("source_type", "unknown")
            by_source[st] = by_source.get(st, 0) + 1
            semantic = card.get("semantic") or {}
            tier = semantic.get("quality_tier", "unknown")
            by_tier[tier] = by_tier.get(tier, 0) + 1

        return {
            "total": total,
            "by_source_type": by_source,
            "by_quality_tier": by_tier,
        }

    def save_batch(self, cards: List[Dict[str, Any]]):
        for card in cards:
            self.save(card)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "exec(open('tests/test_card_store.py').read()); test_save_and_load_card(); test_list_cards_with_filter(); test_delete_card(); test_update_card(); test_card_stats(); print('ALL PASS')"`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/card/ backend/tests/test_card_store.py && git commit -m "feat: add card storage layer with CRUD and filtering"
```

---

### Task 2: Card CRUD API

**Files:**
- Modify: `backend/api/card.py`

- [ ] **Step 1: Implement real card API**

```python
# backend/api/card.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from card.store import CardStore
from config import AppConfig
import os

router = APIRouter(prefix="/cards", tags=["cards"])


class CardUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


def _get_store() -> CardStore:
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    return CardStore(data_dir=data_dir)


@router.get("")
async def list_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    source_type: str = Query(None),
    intent_tag: str = Query(None),
    quality_tier: str = Query(None),
    search: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    store = _get_store()
    return store.list_cards(
        source_type=source_type,
        intent_tag=intent_tag,
        quality_tier=quality_tier,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def card_stats():
    store = _get_store()
    return store.stats()


@router.get("/{card_id}")
async def get_card(card_id: str):
    store = _get_store()
    card = store.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")
    return card


@router.put("/{card_id}")
async def update_card(card_id: str, update: CardUpdate):
    store = _get_store()
    existing = store.get(card_id)
    if not existing:
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")

    updates = update.model_dump(exclude_none=True)
    if not updates:
        return {"status": "no_changes", "id": card_id}

    if "body" in updates and updates["body"] != existing.get("body"):
        updates["char_count"] = len(updates["body"])

    store.update(card_id, updates)
    return {"status": "updated", "id": card_id}


@router.delete("/{card_id}")
async def delete_card(card_id: str):
    store = _get_store()
    if not store.delete(card_id):
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")
    return {"status": "deleted", "id": card_id}
```

- [ ] **Step 2: Verify imports work**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from api.card import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/api/card.py && git commit -m "feat: implement real card CRUD API with filtering and stats"
```

---

### Task 3: Pipeline Base Framework

**Files:**
- Create: `backend/pipeline/__init__.py`
- Create: `backend/pipeline/base.py`

- [ ] **Step 1: Create pipeline package and base**

```python
# backend/pipeline/__init__.py
from .base import PipelineBase, PipelineError
```

```python
# backend/pipeline/base.py
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path


class PipelineError(Exception):
    pass


class PipelineBase:
    SOURCE_TYPE: str = ""
    SOURCE_ID: str = ""

    def __init__(self, data_dir: str, doc_index: int = 1):
        self.data_dir = data_dir
        self.doc_index = doc_index
        self.raw_dir = os.path.join(data_dir, "raw")

    def make_card_id(self, doc_slug: str, seq: int) -> str:
        return f"{self.doc_index:02d}-{self.SOURCE_ID}-{doc_slug}-sec-{seq:03d}"

    def make_path(self, doc_name: str, sections: List[str]) -> str:
        parts = [doc_name] + sections
        return " > ".join(parts)

    def body_hash(self, body: str) -> str:
        return hashlib.sha256(body.encode()).hexdigest()[:16]

    def make_card(
        self,
        doc_file: str,
        doc_slug: str,
        title: str,
        level: int,
        path: str,
        line_start: int,
        body: str,
        seq: int,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "id": self.make_card_id(doc_slug, seq),
            "doc_file": doc_file,
            "source_type": self.SOURCE_TYPE,
            "title": title,
            "level": level,
            "path": path,
            "line_start": line_start,
            "char_count": len(body),
            "body": body,
            "tags": [],
            "keywords": [],
            "models": [],
            "related_topics": [],
            "aliases": [],
            "sibling_sections": [],
            "source_weight": 2,
            "report_meta": None,
            "semantic": None,
            "created_at": now,
            "updated_at": now,
        }

    def split_body(self, body: str, max_chars: int = 1200) -> List[str]:
        if len(body) <= max_chars:
            return [body]
        chunks = []
        paragraphs = body.split("\n\n")
        current = ""
        for para in paragraphs:
            if len(current) + len(para) + 2 > max_chars and current:
                chunks.append(current.strip())
                current = para
            else:
                current = current + "\n\n" + para if current else para
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [body[:max_chars]]

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def doc_slug(self, filename: str) -> str:
        stem = Path(filename).stem
        slug = ""
        for ch in stem:
            if ch.isalnum() or ch in "-_":
                slug += ch
            elif ch in " \t":
                slug += "-"
        return slug[:50] or "doc"
```

- [ ] **Step 2: Verify imports work**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from pipeline.base import PipelineBase, PipelineError; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/pipeline/ && git commit -m "feat: add pipeline base framework with shared card creation logic"
```

---

### Task 4: Word Pipeline

**Files:**
- Create: `backend/pipeline/word.py`
- Create: `backend/tests/test_pipeline_word.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pipeline_word.py
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.word import WordPipeline


def test_parse_simple_docx():
    """Test parsing a simple docx with headings and paragraphs."""
    try:
        from docx import Document
    except ImportError:
        return  # skip if python-docx not installed

    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = os.path.join(tmpdir, "test.docx")
        doc = Document()
        doc.add_heading("Introduction", level=1)
        doc.add_paragraph("This is the introduction paragraph with enough content to test.")
        doc.add_heading("Features", level=2)
        doc.add_paragraph("Feature A description here.")
        doc.add_paragraph("Feature B description here.")
        doc.save(doc_path)

        pipeline = WordPipeline(data_dir=tmpdir)
        cards = pipeline.parse(doc_path)

        assert len(cards) >= 2
        assert cards[0]["source_type"] == "word"
        assert "Introduction" in cards[0]["title"] or "Introduction" in cards[0]["body"]
        assert cards[0]["level"] >= 1
```

- [ ] **Step 2: Check if python-docx is installed**

Run: `python3 -c "from docx import Document; print('OK')"`
If not installed: `pip3 install python-docx`

- [ ] **Step 3: Implement WordPipeline**

```python
# backend/pipeline/word.py
from typing import List, Dict, Any, Optional
from .base import PipelineBase, PipelineError

try:
    from docx import Document
    from docx.oxml.ns import qn
except ImportError:
    Document = None


class WordPipeline(PipelineBase):
    SOURCE_TYPE = "word"
    SOURCE_ID = "01"

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        if Document is None:
            raise PipelineError("python-docx not installed")

        try:
            doc = Document(file_path)
        except Exception as e:
            raise PipelineError(f"文件损坏，python-docx 解析失败: {e}")

        doc_file = file_path.split("/")[-1].split("\\")[-1]
        slug = self.doc_slug(doc_file)
        cards = []
        seq = 0

        current_section = {"title": "", "level": 0, "body_parts": [], "line": 0}

        for i, para in enumerate(doc.paragraphs):
            heading = self._detect_heading(para)
            if heading:
                if current_section["body_parts"]:
                    body = "\n\n".join(current_section["body_parts"])
                    chunks = self.split_body(body)
                    for ci, chunk in enumerate(chunks):
                        title = current_section["title"] if ci == 0 else f"{current_section['title']} ({ci+1})"
                        path = self.make_path(doc_file, [current_section["title"]])
                        cards.append(self.make_card(
                            doc_file=doc_file,
                            doc_slug=slug,
                            title=title,
                            level=current_section["level"],
                            path=path,
                            line_start=current_section["line"],
                            body=chunk,
                            seq=seq,
                        ))
                        seq += 1
                current_section = {
                    "title": para.text.strip(),
                    "level": heading,
                    "body_parts": [],
                    "line": i,
                }
            else:
                text = para.text.strip()
                if text:
                    current_section["body_parts"].append(text)

        if current_section["body_parts"]:
            body = "\n\n".join(current_section["body_parts"])
            chunks = self.split_body(body)
            for ci, chunk in enumerate(chunks):
                title = current_section["title"] if ci == 0 else f"{current_section['title']} ({ci+1})"
                path = self.make_path(doc_file, [current_section["title"]])
                cards.append(self.make_card(
                    doc_file=doc_file,
                    doc_slug=slug,
                    title=title,
                    level=current_section["level"],
                    path=path,
                    line_start=current_section["line"],
                    body=chunk,
                    seq=seq,
                ))
                seq += 1

        if not cards:
            raise PipelineError("文档无有效文本内容")

        return cards

    def _detect_heading(self, para) -> Optional[int]:
        style_name = (para.style.name or "").lower() if para.style else ""

        if "heading 1" in style_name or "标题 1" in style_name:
            return 1
        if "heading 2" in style_name or "标题 2" in style_name:
            return 2
        if "heading 3" in style_name or "标题 3" in style_name:
            return 3

        if para.runs and para.runs[0].bold and len(para.text.strip()) < 80:
            text = para.text.strip()
            if "。" not in text and "，" not in text:
                return 2

        return None
```

- [ ] **Step 4: Run test to verify**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "exec(open('tests/test_pipeline_word.py').read()); test_parse_simple_docx(); print('PASS')"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/pipeline/word.py backend/tests/test_pipeline_word.py && git commit -m "feat: implement Word document pipeline"
```

---

### Task 5: Markdown Pipeline

**Files:**
- Create: `backend/pipeline/markdown.py`
- Create: `backend/tests/test_pipeline_md.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pipeline_md.py
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.markdown import MarkdownPipeline


def test_parse_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_content = """# Introduction

This is the introduction paragraph.

## Features

Feature A is great.

Feature B is even better.

### Details

Some detailed information here.
"""
        md_path = os.path.join(tmpdir, "test.md")
        with open(md_path, "w") as f:
            f.write(md_content)

        pipeline = MarkdownPipeline(data_dir=tmpdir)
        cards = pipeline.parse(md_path)

        assert len(cards) >= 2
        assert cards[0]["source_type"] == "markdown"
        titles = [c["title"] for c in cards]
        assert any("Introduction" in t for t in titles)


def test_coarse_doc_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        md_content = """# Release Notes

## v3.0
- Feature A
- Feature B

## v2.9
- Bug fix C
"""
        md_path = os.path.join(tmpdir, "release-note-v3.md")
        with open(md_path, "w") as f:
            f.write(md_content)

        pipeline = MarkdownPipeline(data_dir=tmpdir)
        cards = pipeline.parse(md_path)
        assert len(cards) >= 1
```

- [ ] **Step 2: Implement MarkdownPipeline**

```python
# backend/pipeline/markdown.py
import re
from typing import List, Dict, Any
from .base import PipelineBase, PipelineError


class MarkdownPipeline(PipelineBase):
    SOURCE_TYPE = "markdown"
    SOURCE_ID = "02"

    COARSE_DOC_HINTS = ["release-note", "changelog", "发版", "更新日志"]

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="gbk", errors="replace") as f:
                content = f.read()

        doc_file = file_path.split("/")[-1].split("\\")[-1]
        slug = self.doc_slug(doc_file)
        is_coarse = any(hint in doc_file.lower() for hint in self.COARSE_DOC_HINTS)

        sections = self._parse_sections(content)
        cards = []
        seq = 0

        for section in sections:
            body = section["body"].strip()
            if not body:
                continue

            if is_coarse or len(body) <= 1200:
                chunks = [body]
            else:
                chunks = self.split_body(body)

            for ci, chunk in enumerate(chunks):
                title = section["title"] if ci == 0 else f"{section['title']} ({ci+1})"
                path = self.make_path(doc_file, [section["title"]])
                cards.append(self.make_card(
                    doc_file=doc_file,
                    doc_slug=slug,
                    title=title,
                    level=section["level"],
                    path=path,
                    line_start=section["line"],
                    body=chunk,
                    seq=seq,
                ))
                seq += 1

        if not cards:
            raise PipelineError("文档无有效文本内容")

        return cards

    def _parse_sections(self, content: str) -> List[Dict]:
        lines = content.split("\n")
        sections = []
        current = {"title": "", "level": 0, "body_lines": [], "line": 0}

        for i, line in enumerate(lines):
            heading_match = re.match(r'^(#{1,3})\s+(.+)', line)
            if heading_match:
                if current["body_lines"]:
                    current["body"] = "\n".join(current["body_lines"])
                    sections.append(current)
                level = len(heading_match.group(1))
                current = {
                    "title": heading_match.group(2).strip(),
                    "level": level,
                    "body_lines": [],
                    "line": i,
                }
            else:
                current["body_lines"].append(line)

        if current["body_lines"]:
            current["body"] = "\n".join(current["body_lines"])
            sections.append(current)

        return sections
```

- [ ] **Step 3: Run test to verify**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "exec(open('tests/test_pipeline_md.py').read()); test_parse_markdown(); test_coarse_doc_detection(); print('PASS')"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/pipeline/markdown.py backend/tests/test_pipeline_md.py && git commit -m "feat: implement Markdown pipeline with coarse doc detection"
```

---

### Task 6: TXT + PPT Pipelines

**Files:**
- Create: `backend/pipeline/txt.py`
- Create: `backend/pipeline/ppt.py`
- Create: `backend/tests/test_pipeline_txt.py`
- Create: `backend/tests/test_pipeline_ppt.py`

- [ ] **Step 1: Write TXT test**

```python
# backend/tests/test_pipeline_txt.py
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.txt import TxtPipeline


def test_parse_txt():
    with tempfile.TemporaryDirectory() as tmpdir:
        txt_content = """公安行业应用方案

通过部署云视频平台，实现省-市-县三级巡查督导。

教育行业应用方案

远程互动课堂，实现优质教育资源共享。
"""
        txt_path = os.path.join(tmpdir, "cases.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(txt_content)

        pipeline = TxtPipeline(data_dir=tmpdir)
        cards = pipeline.parse(txt_path)

        assert len(cards) >= 2
        assert cards[0]["source_type"] == "txt"
```

- [ ] **Step 2: Write PPT test**

```python
# backend/tests/test_pipeline_ppt.py
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.ppt import PptPipeline


def test_parse_pptx():
    try:
        from pptx import Presentation
    except ImportError:
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        ppt_path = os.path.join(tmpdir, "test.pptx")
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = "Product Overview"
        slide.placeholders[1].text = "AE800 is a 4K video conference system."
        prs.save(ppt_path)

        pipeline = PptPipeline(data_dir=tmpdir)
        cards = pipeline.parse(ppt_path)

        assert len(cards) >= 1
        assert cards[0]["source_type"] == "ppt"
        assert "AE800" in cards[0]["body"]
```

- [ ] **Step 3: Implement TxtPipeline**

```python
# backend/pipeline/txt.py
from typing import List, Dict, Any
from .base import PipelineBase, PipelineError

try:
    import chardet
except ImportError:
    chardet = None


class TxtPipeline(PipelineBase):
    SOURCE_TYPE = "txt"
    SOURCE_ID = "03"

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        content = self._read_with_encoding(file_path)
        doc_file = file_path.split("/")[-1].split("\\")[-1]
        slug = self.doc_slug(doc_file)

        paragraphs = self._split_paragraphs(content)
        if not paragraphs:
            raise PipelineError("文件无有效文本内容")

        cards = []
        for seq, para in enumerate(paragraphs):
            title = self._infer_title(para, seq)
            chunks = self.split_body(para)
            for ci, chunk in enumerate(chunks):
                t = title if ci == 0 else f"{title} ({ci+1})"
                path = self.make_path(doc_file, [title])
                cards.append(self.make_card(
                    doc_file=doc_file,
                    doc_slug=slug,
                    title=t,
                    level=0,
                    path=path,
                    line_start=0,
                    body=chunk,
                    seq=seq * 10 + ci,
                ))

        return cards

    def _read_with_encoding(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            raw = f.read(4096)

        if raw[:3] == b'\xef\xbb\xbf':
            with open(file_path, "r", encoding="utf-8-sig") as f:
                return f.read()

        if chardet:
            result = chardet.detect(raw)
            if result["confidence"] >= 0.7:
                try:
                    with open(file_path, "r", encoding=result["encoding"]) as f:
                        return f.read()
                except (UnicodeDecodeError, LookupError):
                    pass

        for enc in ["utf-8", "gbk", "gb2312", "utf-16"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise PipelineError("无法识别文件编码")

    def _split_paragraphs(self, content: str) -> List[str]:
        import re
        blocks = re.split(r'\n{2,}', content)
        paragraphs = []
        for block in blocks:
            text = block.strip()
            if text:
                paragraphs.append(text)
        return paragraphs

    def _infer_title(self, text: str, seq: int) -> str:
        first_line = text.split("\n")[0].strip()
        if len(first_line) <= 50 and "，" not in first_line and "。" not in first_line:
            return first_line
        return f"第{seq + 1}段"
```

- [ ] **Step 4: Implement PptPipeline**

```python
# backend/pipeline/ppt.py
from typing import List, Dict, Any
from .base import PipelineBase, PipelineError

try:
    from pptx import Presentation
    from pptx.util import Inches
except ImportError:
    Presentation = None


class PptPipeline(PipelineBase):
    SOURCE_TYPE = "ppt"
    SOURCE_ID = "05"

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        if Presentation is None:
            raise PipelineError("python-pptx not installed")

        try:
            prs = Presentation(file_path)
        except Exception as e:
            raise PipelineError(f"文件损坏，python-pptx 解析失败: {e}")

        doc_file = file_path.split("/")[-1].split("\\")[-1]
        slug = self.doc_slug(doc_file)
        cards = []

        for slide_num, slide in enumerate(prs.slides):
            title = self._extract_title(slide)
            body = self._extract_text(slide)
            if not body.strip():
                continue

            cards.append(self.make_card(
                doc_file=doc_file,
                doc_slug=slug,
                title=title or f"第{slide_num + 1}页",
                level=0,
                path=self.make_path(doc_file, [title or f"第{slide_num + 1}页"]),
                line_start=slide_num,
                body=body,
                seq=slide_num,
            ))

        if not cards:
            raise PipelineError("PPT无有效文本内容")

        return cards

    def _extract_title(self, slide) -> str:
        if slide.shapes.title and slide.shapes.title.text:
            return slide.shapes.title.text.strip()
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text.strip():
                return shape.text.strip()[:80]
        return ""

    def _extract_text(self, slide) -> str:
        parts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        parts.append(text)
            if shape.has_table:
                table = shape.table
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
```

- [ ] **Step 5: Run tests**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "exec(open('tests/test_pipeline_txt.py').read()); test_parse_txt(); print('TXT PASS')"`
Expected: TXT PASS

- [ ] **Step 6: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/pipeline/txt.py backend/pipeline/ppt.py backend/tests/test_pipeline_txt.py backend/tests/test_pipeline_ppt.py && git commit -m "feat: implement TXT and PPT pipelines"
```

---

### Task 7: Excel Pipeline (Profiling + Card Generation)

**Files:**
- Create: `backend/pipeline/excel.py`
- Create: `backend/tests/test_pipeline_excel.py`

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_pipeline_excel.py
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.excel import ExcelPipeline


def test_profile_excel():
    try:
        from openpyxl import Workbook
    except ImportError:
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        xlsx_path = os.path.join(tmpdir, "products.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "报价表"
        ws.append(["型号", "价格", "描述"])
        ws.append(["AE800", 138000, "4K视频会议主机"])
        ws.append(["PE8000", 298000, "高端会议室终端"])
        ws.append(["XE800", 68000, "中型会议室终端"])
        wb.save(xlsx_path)

        pipeline = ExcelPipeline(data_dir=tmpdir)
        profile = pipeline.profile(xlsx_path)

        assert len(profile) >= 1
        assert profile[0]["sheet_name"] == "报价表"
        assert profile[0]["header_row"] is not None


def test_generate_cards_from_excel():
    try:
        from openpyxl import Workbook
    except ImportError:
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        xlsx_path = os.path.join(tmpdir, "products.xlsx")
        wb = Workbook()
        ws = wb.active
        ws.title = "报价表"
        ws.append(["型号", "价格", "描述"])
        ws.append(["AE800", 138000, "4K视频会议主机"])
        ws.append(["PE8000", 298000, "高端会议室终端"])
        wb.save(xlsx_path)

        pipeline = ExcelPipeline(data_dir=tmpdir)
        profile = pipeline.profile(xlsx_path)
        config = pipeline.default_config(profile)
        cards = pipeline.generate_cards(xlsx_path, config)

        assert len(cards) >= 2
        assert cards[0]["source_type"] == "excel"
        assert "AE800" in cards[0]["title"] or "AE800" in cards[0]["body"]
```

- [ ] **Step 2: Check if openpyxl is installed**

Run: `python3 -c "from openpyxl import Workbook; print('OK')"`
If not installed: `pip3 install openpyxl`

- [ ] **Step 3: Implement ExcelPipeline**

```python
# backend/pipeline/excel.py
import re
from typing import List, Dict, Any, Optional
from .base import PipelineBase, PipelineError

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None


class ExcelPipeline(PipelineBase):
    SOURCE_TYPE = "excel"
    SOURCE_ID = "04"

    MODEL_PATTERN = re.compile(r'[A-Z]{2,}\d+(?:\s*[A-Z]+)?(?:\s*V\d+\.?\d*)?')

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        profile = self.profile(file_path)
        config = self.default_config(profile)
        return self.generate_cards(file_path, config)

    def profile(self, file_path: str) -> List[Dict]:
        if load_workbook is None:
            raise PipelineError("openpyxl not installed")

        try:
            wb = load_workbook(file_path, read_only=True, data_only=True)
        except Exception as e:
            raise PipelineError(f"Excel 解析失败: {e}")

        results = []
        for ws in wb.worksheets:
            rows = []
            for row in ws.iter_rows(max_row=20, values_only=True):
                rows.append([str(c) if c is not None else "" for c in row])

            if not rows:
                continue

            header_row = self._detect_header_row(rows)
            cols = rows[header_row] if header_row < len(rows) else []
            num_cols = len(cols)

            model_cols = []
            price_cols = []
            note_cols = []

            for ci, col_name in enumerate(cols):
                col_values = [rows[r][ci] if ci < len(rows[r]) else "" for r in range(header_row + 1, min(len(rows), header_row + 20))]

                if self.MODEL_PATTERN.search(col_name) or sum(1 for v in col_values if self.MODEL_PATTERN.search(v)) >= max(1, len(col_values) * 0.3):
                    model_cols.append(ci)

                if any(kw in col_name for kw in ["价", "金额", "price", "cost", "Price", "Cost"]):
                    price_cols.append(ci)

                if ci >= num_cols - 3:
                    avg_len = sum(len(str(v)) for v in col_values) / max(1, len(col_values))
                    if avg_len > 10:
                        note_cols.append(ci)

            discontinued_cols = []
            for ci in range(num_cols):
                col_values = [rows[r][ci] if ci < len(rows[r]) else "" for r in range(header_row + 1, min(len(rows), header_row + 20))]
                if any(kw in str(v) for v in col_values for kw in ["停产", "替代", "停售", "EOL"]):
                    discontinued_cols.append(ci)

            results.append({
                "sheet_name": ws.title,
                "header_row": header_row,
                "skip_rows": header_row,
                "model_cols": model_cols,
                "price_cols": price_cols,
                "title_cols": model_cols,
                "body_cols": [i for i in range(num_cols) if i not in model_cols],
                "keyword_cols": [],
                "note_cols": note_cols,
                "discontinued_cols": discontinued_cols,
                "comparison_mode": False,
                "num_rows": len(rows) - header_row - 1,
                "num_cols": num_cols,
            })

        wb.close()
        return results

    def default_config(self, profile: List[Dict]) -> List[Dict]:
        configs = []
        for sheet in profile:
            configs.append({
                "sheet_name": sheet["sheet_name"],
                "header_row": sheet["header_row"],
                "skip_rows": sheet["skip_rows"],
                "title_cols": sheet["title_cols"],
                "body_cols": sheet["body_cols"],
                "model_cols": sheet["model_cols"],
                "price_cols": sheet["price_cols"],
                "note_cols": sheet["note_cols"],
                "discontinued_cols": sheet["discontinued_cols"],
                "comparison_mode": sheet["comparison_mode"],
            })
        return configs

    def generate_cards(self, file_path: str, config: List[Dict]) -> List[Dict]:
        if load_workbook is None:
            raise PipelineError("openpyxl not installed")

        try:
            wb = load_workbook(file_path, read_only=True, data_only=True)
        except Exception as e:
            raise PipelineError(f"Excel 解析失败: {e}")

        doc_file = file_path.split("/")[-1].split("\\")[-1]
        slug = self.doc_slug(doc_file)
        cards = []
        seq = 0

        for sheet_cfg in config:
            sheet_name = sheet_cfg["sheet_name"]
            if sheet_name not in wb.sheetnames:
                continue

            ws = wb[sheet_name]
            header_row = sheet_cfg["header_row"]
            title_cols = sheet_cfg["title_cols"]
            body_cols = sheet_cfg["body_cols"]

            rows = list(ws.iter_rows(values_only=True))

            for ri in range(header_row + 1, len(rows)):
                row = rows[ri]
                row_values = [str(c) if c is not None else "" for c in row]

                if all(not v.strip() for v in row_values):
                    continue

                title_parts = []
                for ci in title_cols:
                    if ci < len(row_values) and row_values[ci].strip():
                        title_parts.append(row_values[ci].strip())
                title = " | ".join(title_parts) if title_parts else f"行{ri}"

                body_parts = []
                for ci in body_cols:
                    if ci < len(row_values) and row_values[ci].strip():
                        body_parts.append(row_values[ci].strip())
                body = " | ".join(body_parts) if body_parts else ""

                if not body:
                    continue

                path = f"{doc_file} > {sheet_name}"
                cards.append(self.make_card(
                    doc_file=doc_file,
                    doc_slug=slug,
                    title=title,
                    level=0,
                    path=path,
                    line_start=ri,
                    body=body,
                    seq=seq,
                ))
                seq += 1

        wb.close()
        return cards

    def _detect_header_row(self, rows: List[List[str]]) -> int:
        best_row = 0
        best_score = 0

        for ri in range(min(10, len(rows))):
            row = rows[ri]
            score = 0
            for cell in row:
                cell = str(cell).strip()
                if not cell:
                    continue
                if len(cell) < 20 and not any(c.isdigit() for c in cell):
                    score += 2
                if cell and len(cell) < 30:
                    score += 1
            if score > best_score:
                best_score = score
                best_row = ri

        return best_row
```

- [ ] **Step 4: Run tests**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "exec(open('tests/test_pipeline_excel.py').read()); test_profile_excel(); test_generate_cards_from_excel(); print('PASS')"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/pipeline/excel.py backend/tests/test_pipeline_excel.py && git commit -m "feat: implement Excel pipeline with profiling and card generation"
```

---

### Task 8: Upload API + File Type Routing

**Files:**
- Modify: `backend/api/upload.py`

- [ ] **Step 1: Implement real upload API**

```python
# backend/api/upload.py
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from db.models import get_db
from job.scheduler import JobScheduler
from config import AppConfig

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".docx", ".xlsx", ".txt", ".md", ".pptx"}
FILE_TYPE_MAP = {
    ".docx": "word",
    ".xlsx": "excel",
    ".txt": "txt",
    ".md": "markdown",
    ".pptx": "ppt",
}
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    force_overwrite: bool = False,
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail=f"INVALID_FILE_TYPE: {ext}")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, detail="空文件")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="FILE_TOO_LARGE")

    sha256 = hashlib.sha256(content).hexdigest()
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    upload_dir = os.path.join(data_dir, "uploads")

    today = datetime.now().strftime("%Y-%m-%d")
    stored_name = f"{sha256[:8]}_{file.filename}"
    storage_path = os.path.join(upload_dir, today, stored_name)
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)

    with open(storage_path, "wb") as f:
        f.write(content)

    file_type = FILE_TYPE_MAP[ext]
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM uploaded_files WHERE sha256 = ?", (sha256,)
        ).fetchone()

        if existing and not force_overwrite:
            raise HTTPException(409, detail="DUPLICATE_FILE")

        cursor = conn.execute(
            """INSERT INTO uploaded_files
               (original_name, stored_name, file_type, size_bytes, sha256, storage_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file.filename, stored_name, file_type, len(content), sha256, storage_path)
        )
        conn.commit()
        file_id = cursor.lastrowid

        scheduler = JobScheduler(conn)
        job_ids = scheduler.create_cascade_jobs(file_type=file_type, target_id=file_id)

        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "sha256": sha256,
            "size_bytes": len(content),
            "jobs_created": len(job_ids),
        }
    finally:
        conn.close()


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    file_type: str = Query(None),
    is_current: Optional[bool] = Query(None),
):
    conn = get_db()
    try:
        conditions = []
        params = []
        if file_type:
            conditions.append("file_type = ?")
            params.append(file_type)
        if is_current is not None:
            conditions.append("is_current = ?")
            params.append(1 if is_current else 0)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * page_size

        total = conn.execute(f"SELECT COUNT(*) as cnt FROM uploaded_files{where}", params).fetchone()['cnt']
        rows = conn.execute(
            f"SELECT * FROM uploaded_files{where} ORDER BY uploaded_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset]
        ).fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM uploaded_files WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="DOCUMENT_NOT_FOUND")
        conn.execute("DELETE FROM uploaded_files WHERE id = ?", (doc_id,))
        conn.commit()
        return {"status": "deleted", "id": doc_id}
    finally:
        conn.close()


@router.post("/documents/{doc_id}/reprocess")
async def reprocess_document(doc_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM uploaded_files WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="DOCUMENT_NOT_FOUND")

        scheduler = JobScheduler(conn)
        job_ids = scheduler.create_cascade_jobs(
            file_type=row['file_type'],
            target_id=doc_id,
        )
        return {"status": "job_created", "document_id": doc_id, "jobs_created": len(job_ids)}
    finally:
        conn.close()
```

- [ ] **Step 2: Verify imports**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from api.upload import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/api/upload.py && git commit -m "feat: implement upload API with DB records and cascade job creation"
```

---

### Task 9: Query Service (wiki_test Integration)

**Files:**
- Create: `backend/services/query_service.py`
- Modify: `backend/api/query.py`

- [ ] **Step 1: Implement query service**

```python
# backend/services/query_service.py
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from db.models import get_db


def normalize_query(query: str) -> str:
    q = query.strip()
    q = q.replace("　", " ")
    while "  " in q:
        q = q.replace("  ", " ")
    return q


def query_hash(query: str) -> str:
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def search(query: str, limit: int = 10) -> Dict[str, Any]:
    q = normalize_query(query)
    if not q:
        return {"error": "INVALID_QUERY", "results": []}
    if len(q) > 500:
        return {"error": "INVALID_QUERY", "results": []}

    qhash = query_hash(q)
    conn = get_db()

    try:
        cache = conn.execute(
            "SELECT source_type, models FROM route_cache WHERE query_hash = ?",
            (qhash,)
        ).fetchone()

        route_source = "cache" if cache else "rule"

        mapping = conn.execute(
            "SELECT expected_route, confidence FROM route_mappings WHERE query_hash = ? AND is_active = 1",
            (qhash,)
        ).fetchone()

        if mapping and mapping["confidence"] >= 0.7:
            route_source = "feedback_learned"

    finally:
        conn.close()

    wiki_dir = os.environ.get("WIKI_DIR", "/home/jjb/wiki")
    script = os.path.join(wiki_dir, "query_unified.py")

    try:
        result = subprocess.run(
            ["python3", script, q, "--json", "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=wiki_dir,
        )

        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
        else:
            data = {"results": [], "total": 0}

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        data = {"results": [], "total": 0}

    data["route_source"] = route_source
    data["query_hash"] = qhash

    if data.get("total", 0) > 0 and route_source in ("rule", "feedback_learned"):
        _update_cache(qhash, q, data)

    return data


def _update_cache(qhash: str, query: str, data: Dict):
    conn = get_db()
    try:
        source_type = data.get("results", [{}])[0].get("source_type", "knowledge") if data.get("results") else "knowledge"
        models = json.dumps(data.get("models", []))
        conn.execute(
            """INSERT OR REPLACE INTO route_cache (query_hash, query_text, source_type, models, hit_count, last_hit_at)
               VALUES (?, ?, ?, ?,
                       COALESCE((SELECT hit_count FROM route_cache WHERE query_hash = ?), 0) + 1,
                       datetime('now'))""",
            (qhash, query, source_type, models, qhash)
        )
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def submit_feedback(query_text: str, card_id: str, feedback: str, route_used: str):
    qhash = query_hash(normalize_query(query_text))
    conn = get_db()
    try:
        import uuid
        query_id = str(uuid.uuid4())[:8]
        conn.execute(
            """INSERT INTO query_feedback (query_id, query_text, card_id, feedback, route_used, route_source)
               VALUES (?, ?, ?, ?, ?, 'user')""",
            (query_id, query_text, card_id, feedback, route_used)
        )

        mapping = conn.execute(
            "SELECT * FROM route_mappings WHERE query_hash = ?", (qhash,)
        ).fetchone()

        if not mapping:
            conn.execute(
                """INSERT INTO route_mappings (query_pattern, query_hash, expected_route, confidence,
                   positive_count, negative_count, total_count, source)
                   VALUES (?, ?, ?, 0.5, 0, 0, 0, 'rule')""",
                (query_text, qhash, route_used)
            )
            mapping = conn.execute(
                "SELECT * FROM route_mappings WHERE query_hash = ?", (qhash,)
            ).fetchone()

        pos = mapping["positive_count"]
        neg = mapping["negative_count"]
        if feedback == "positive":
            pos += 1
        else:
            neg += 1

        total = pos + neg
        confidence = pos / total if total > 0 else 0.5

        is_active = 0
        source = mapping["source"]
        if confidence >= 0.7 and total >= 5:
            is_active = 1
            source = "feedback_learned"
        elif confidence < 0.3 and total >= 5:
            is_active = 0
        elif confidence < 0.5 and total >= 10:
            is_active = 0

        conn.execute(
            """UPDATE route_mappings SET
               positive_count=?, negative_count=?, total_count=?,
               confidence=?, is_active=?, source=?, updated_at=datetime('now')
               WHERE query_hash=?""",
            (pos, neg, total, confidence, is_active, source, qhash)
        )
        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 2: Update query API**

```python
# backend/api/query.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.query_service import search, submit_feedback

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str
    limit: int = 10


class FeedbackRequest(BaseModel):
    query_text: str
    card_id: str
    feedback: str
    route_used: str


@router.post("")
async def query(req: QueryRequest):
    if not req.query or len(req.query) > 500:
        raise HTTPException(400, detail="INVALID_QUERY")
    result = search(req.query, limit=req.limit)
    return result


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    if req.feedback not in ("positive", "negative"):
        raise HTTPException(400, detail="INVALID_FEEDBACK")
    submit_feedback(req.query_text, req.card_id, req.feedback, req.route_used)
    return {"status": "ok"}
```

- [ ] **Step 3: Verify imports**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from services.query_service import search; from api.query import router; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/services/query_service.py backend/api/query.py && git commit -m "feat: implement query service with wiki_test integration and route learning"
```

---

### Task 10: Semantic Annotation Service

**Files:**
- Create: `backend/services/annotate_service.py`

- [ ] **Step 1: Implement annotation service**

```python
# backend/services/annotate_service.py
import hashlib
import json
import os
import time
from typing import Dict, Any, Optional, List

from card.store import CardStore


ANNOTATION_PROMPT_SYSTEM = """你是小鱼易连产品知识库的标注助手。你的任务是分析技术文档片段，输出结构化的语义标签。仅输出 JSON，不要输出任何其他文本。"""

ANNOTATION_PROMPT_USER = """请分析以下文档片段，输出 JSON 格式的语义标注。

文档上下文: {doc_file} > {path}
标题: {title}
正文: {body}

输出格式:
{{
  "intent_tags": [从标签库中选择 0-3 个],
  "concept_tags": [提取 0-5 个核心技术概念],
  "scenario_tags": [提取 0-5 个应用场景],
  "card_type": "capability/parameter/price/scenario/architecture/update",
  "summary": "一句话描述本节内容（50字以内）",
  "models": [提取产品型号如 AE800/PE8000],
  "keywords": [提取 0-5 个检索关键词],
  "negative_concepts": [与本节无关但易混淆的概念],
  "quality_tier": "high/medium/low/placeholder",
  "content_hash": "{content_hash}"
}}

标签库 (intent_tags 只能从中选择):
- 安全保障: 加密/认证/权限/审计/合规
- 功能更新: 新功能/版本迭代/发版说明
- 架构设计: 系统拓扑/模块设计/技术选型
- 部署运维: 安装/配置/监控/升级
- 场景方案: 行业方案/客户案例/应用场景
- 报价价格: 产品价格/配件价格/报价体系
- 性能参数: 硬件规格/性能指标/技术参数
- 集成对接: API/SDK/接口/第三方集成"""

VALID_INTENT_TAGS = {
    "安全保障", "功能更新", "架构设计", "部署运维",
    "场景方案", "报价价格", "性能参数", "集成对接",
}

VALID_CARD_TYPES = {"capability", "parameter", "price", "scenario", "architecture", "update"}
VALID_QUALITY_TIERS = {"high", "medium", "low", "placeholder"}


def annotate_card(card: Dict[str, Any], llm_call=None) -> Dict[str, Any]:
    body = card.get("body", "")
    content_hash = hashlib.sha256(body.encode()).hexdigest()[:16]

    if llm_call is None:
        llm_call = _default_llm_call

    prompt = ANNOTATION_PROMPT_USER.format(
        doc_file=card.get("doc_file", ""),
        path=card.get("path", ""),
        title=card.get("title", ""),
        body=body[:1200],
        content_hash=content_hash,
    )

    try:
        result = llm_call(ANNOTATION_PROMPT_SYSTEM, prompt)
        annotation = json.loads(result)
    except (json.JSONDecodeError, Exception):
        annotation = _fallback_annotation(card, content_hash)

    annotation = _validate_annotation(annotation, content_hash)

    from datetime import datetime, timezone
    annotation["annotated_at"] = datetime.now(timezone.utc).isoformat()
    annotation["annotation_version"] = (card.get("semantic") or {}).get("annotation_version", 0) + 1

    return annotation


def _fallback_annotation(card: Dict, content_hash: str) -> Dict:
    return {
        "intent_tags": [],
        "concept_tags": [],
        "scenario_tags": [],
        "card_type": "capability",
        "summary": card.get("title", ""),
        "models": [],
        "keywords": [],
        "negative_concepts": [],
        "quality_tier": "placeholder",
        "content_hash": content_hash,
    }


def _validate_annotation(annotation: Dict, content_hash: str) -> Dict:
    result = {}
    result["intent_tags"] = [t for t in annotation.get("intent_tags", []) if t in VALID_INTENT_TAGS][:3]
    result["concept_tags"] = annotation.get("concept_tags", [])[:5]
    result["scenario_tags"] = annotation.get("scenario_tags", [])[:5]
    result["card_type"] = annotation.get("card_type", "capability")
    if result["card_type"] not in VALID_CARD_TYPES:
        result["card_type"] = "capability"
    result["summary"] = str(annotation.get("summary", ""))[:50]
    result["models"] = annotation.get("models", [])
    result["keywords"] = annotation.get("keywords", [])[:5]
    result["negative_concepts"] = annotation.get("negative_concepts", [])
    result["quality_tier"] = annotation.get("quality_tier", "placeholder")
    if result["quality_tier"] not in VALID_QUALITY_TIERS:
        result["quality_tier"] = "placeholder"
    result["content_hash"] = content_hash
    return result


def _default_llm_call(system: str, user: str) -> str:
    import requests
    cfg_path = os.path.join(os.environ.get("KB_DATA_DIR", "./data"), "config.yaml")
    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    model = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    if os.path.exists(cfg_path):
        import yaml
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f) or {}
        api_key = cfg.get("llm_api_key", api_key)
        base_url = cfg.get("llm_base_url", base_url)
        model = cfg.get("llm_model", model)

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def annotate_batch(store: CardStore, card_ids: List[str] = None, llm_call=None) -> int:
    annotated = 0
    if card_ids is None:
        result = store.list_cards(page_size=10000)
        cards = result["items"]
    else:
        cards = [store.get(cid) for cid in card_ids if store.get(cid)]

    for card in cards:
        semantic = annotate_card(card, llm_call=llm_call)
        semantic["annotator_model"] = os.environ.get("LLM_MODEL", "unknown")
        store.update(card["id"], {"semantic": semantic})
        annotated += 1

    return annotated
```

- [ ] **Step 2: Verify imports**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from services.annotate_service import annotate_card, _fallback_annotation; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/services/annotate_service.py && git commit -m "feat: implement semantic annotation service with LLM integration"
```

---

### Task 11: Index Rebuild + Annotate API

**Files:**
- Modify: `backend/api/index.py`

- [ ] **Step 1: Implement index API**

```python
# backend/api/index.py
from fastapi import APIRouter, HTTPException, Query
from db.models import get_db
from job.scheduler import JobScheduler

router = APIRouter(prefix="/indexes", tags=["indexes"])


@router.get("/status")
async def index_status():
    conn = get_db()
    try:
        counts = {}
        for job_type in ["index_bm25", "index_vector", "index_fts5"]:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE job_type=? AND status='done'",
                (job_type,)
            ).fetchone()
            counts[job_type] = row["c"]

        pending = conn.execute(
            "SELECT COUNT(*) as c FROM jobs WHERE job_type LIKE 'index_%' AND status='pending'"
        ).fetchone()["c"]

        return {
            "index_builds": counts,
            "pending_jobs": pending,
        }
    finally:
        conn.close()


@router.post("/rebuild/{index_type}")
async def rebuild_index(index_type: str):
    valid_types = {"bm25", "vector", "fts5", "topics", "all"}
    if index_type not in valid_types:
        raise HTTPException(400, detail=f"INVALID_INDEX_TYPE: {index_type}")

    conn = get_db()
    try:
        scheduler = JobScheduler(conn)
        if index_type == "all":
            job_ids = []
            for t in ["index_bm25", "index_vector", "index_fts5"]:
                jid = scheduler.create_job(job_type=t, triggered_by="user")
                if jid:
                    job_ids.append(jid)
        else:
            jid = scheduler.create_job(job_type=f"index_{index_type}", triggered_by="user")
            job_ids = [jid] if jid else []

        return {"status": "jobs_created", "index_type": index_type, "job_ids": job_ids}
    finally:
        conn.close()


@router.post("/annotate")
async def trigger_annotation(scope: str = Query("all")):
    if scope not in ("all", "unannotated"):
        raise HTTPException(400, detail="INVALID_SCOPE")

    conn = get_db()
    try:
        scheduler = JobScheduler(conn)
        jid = scheduler.create_job(
            job_type="annotate",
            payload=f'{{"scope": "{scope}"}}',
            triggered_by="user",
        )
        return {"status": "job_created", "job_id": jid}
    finally:
        conn.close()
```

- [ ] **Step 2: Verify imports**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "import sys; sys.path.insert(0,'.'); from api.index import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/api/index.py && git commit -m "feat: implement index rebuild and annotate trigger API"
```

---

### Task 12: Integration Test + Pipeline Dispatch

**Files:**
- Modify: `backend/job/executor.py`
- Create: `backend/tests/test_pipeline_integration.py`

- [ ] **Step 1: Implement pipeline dispatch in executor**

Add pipeline handler registration to executor. Modify `backend/job/executor.py` to add a helper:

```python
# Add to backend/job/executor.py after existing code

def register_default_handlers(executor, data_dir: str):
    """Register all default job handlers."""
    from pipeline.word import WordPipeline
    from pipeline.markdown import MarkdownPipeline
    from pipeline.txt import TxtPipeline
    from pipeline.ppt import PptPipeline
    from card.store import CardStore
    from db.models import get_db

    store = CardStore(data_dir=data_dir)

    def handle_pipeline(job, pipeline_cls):
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM uploaded_files WHERE id = ?", (job["target_id"],)
            ).fetchone()
            if not row:
                raise ValueError(f"File not found: {job['target_id']}")

            pipeline = pipeline_cls(data_dir=data_dir, doc_index=row["id"])
            cards = pipeline.parse(row["storage_path"])
            store.save_batch(cards)

            conn.execute(
                "UPDATE uploaded_files SET cards_count=?, pipeline_status='done', processed_at=datetime('now') WHERE id=?",
                (len(cards), row["id"])
            )
            conn.commit()
        finally:
            conn.close()

    executor.register("pipeline_word", lambda j: handle_pipeline(j, WordPipeline))
    executor.register("pipeline_md", lambda j: handle_pipeline(j, MarkdownPipeline))
    executor.register("pipeline_txt", lambda j: handle_pipeline(j, TxtPipeline))
    executor.register("pipeline_ppt", lambda j: handle_pipeline(j, PptPipeline))

    def handle_annotate(job):
        from services.annotate_service import annotate_batch
        annotate_batch(store)

    executor.register("annotate", handle_annotate)

    def handle_index(job):
        pass  # Placeholder - index building happens in wiki_test

    executor.register("index_bm25", handle_index)
    executor.register("index_vector", handle_index)
    executor.register("index_fts5", handle_index)
```

- [ ] **Step 2: Write integration test**

```python
# backend/tests/test_pipeline_integration.py
import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_word_pipeline_end_to_end():
    try:
        from docx import Document
    except ImportError:
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from pipeline.word import WordPipeline
        from card.store import CardStore
        import sqlite3

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        conn.close()

        doc_path = os.path.join(tmpdir, "test.docx")
        doc = Document()
        doc.add_heading("Overview", level=1)
        doc.add_paragraph("AE800 is a 4K video conference system with advanced features.")
        doc.add_heading("Pricing", level=2)
        doc.add_paragraph("AE800 price: 138000 RMB per unit.")
        doc.save(doc_path)

        pipeline = WordPipeline(data_dir=tmpdir)
        cards = pipeline.parse(doc_path)
        assert len(cards) >= 2

        store = CardStore(data_dir=tmpdir)
        store.save_batch(cards)

        loaded = store.get(cards[0]["id"])
        assert loaded is not None
        assert loaded["source_type"] == "word"

        result = store.list_cards(source_type="word")
        assert result["total"] >= 2
```

- [ ] **Step 3: Run all tests**

Run: `cd /home/jjb/kb-platform/backend && python3 -c "exec(open('tests/test_pipeline_integration.py').read()); test_word_pipeline_end_to_end(); print('PASS')"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
cd /home/jjb/kb-platform && git add backend/job/executor.py backend/tests/test_pipeline_integration.py && git commit -m "feat: add pipeline dispatch and integration tests"
```

---

## Verification Checklist

- [ ] `python3 -c "from card.store import CardStore"` works
- [ ] `python3 -c "from pipeline.word import WordPipeline"` works
- [ ] `python3 -c "from pipeline.markdown import MarkdownPipeline"` works
- [ ] `python3 -c "from pipeline.txt import TxtPipeline"` works
- [ ] `python3 -c "from pipeline.ppt import PptPipeline"` works
- [ ] `python3 -c "from services.query_service import search"` works
- [ ] `python3 -c "from services.annotate_service import annotate_card"` works
- [ ] Card CRUD API responds correctly
- [ ] Upload creates DB record and cascade jobs
- [ ] Query routes to wiki_test engine
- [ ] All tests pass
