from typing import List, Dict, Any, Optional
from .base import PipelineBase, PipelineError

try:
    from docx import Document
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
                            doc_file=doc_file, doc_slug=slug, title=title,
                            level=current_section["level"], path=path,
                            line_start=current_section["line"], body=chunk, seq=seq,
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
                    doc_file=doc_file, doc_slug=slug, title=title,
                    level=current_section["level"], path=path,
                    line_start=current_section["line"], body=chunk, seq=seq,
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
