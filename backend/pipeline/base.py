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
