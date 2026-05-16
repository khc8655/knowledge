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
                    doc_file=doc_file, doc_slug=slug, title=title,
                    level=section["level"], path=path,
                    line_start=section["line"], body=chunk, seq=seq,
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
