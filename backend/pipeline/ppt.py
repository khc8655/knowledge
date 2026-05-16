from typing import List, Dict, Any
from .base import PipelineBase, PipelineError

try:
    from pptx import Presentation
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
                doc_file=doc_file, doc_slug=slug,
                title=title or f"第{slide_num + 1}页",
                level=0,
                path=self.make_path(doc_file, [title or f"第{slide_num + 1}页"]),
                line_start=slide_num, body=body, seq=slide_num,
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
