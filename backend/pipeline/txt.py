import re
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
                    doc_file=doc_file, doc_slug=slug, title=t,
                    level=0, path=path, line_start=0, body=chunk,
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
        blocks = re.split(r'\n{2,}', content)
        return [b.strip() for b in blocks if b.strip()]

    def _infer_title(self, text: str, seq: int) -> str:
        first_line = text.split("\n")[0].strip()
        if len(first_line) <= 50 and "，" not in first_line and "。" not in first_line:
            return first_line
        return f"第{seq + 1}段"
