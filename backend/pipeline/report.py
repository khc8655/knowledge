import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import PipelineBase, PipelineError

REPORT_TYPE_KEYWORDS = {
    "CMA": ["CMA", "检验检测机构资质认定"],
    "CNAS": ["CNAS", "中国合格评定国家认可委员会"],
    "原厂证明函": ["原厂证明函", "原厂证明"],
    "信创认证": ["信创", "信息技术应用创新"],
    "兼容性证明": ["兼容性证明", "兼容性测试"],
    "第三方检测": ["第三方检测", "第三方测试"],
}

CAPABILITY_KEYWORDS = [
    "AVC", "SVC", "H.323", "SIP", "SM2", "SM3", "SM4",
    "国密", "加密", "TLS", "SRTP", "H.264", "H.265",
    "4K", "1080P", "720P", "双流", "录播",
]

PRODUCT_MODEL_RE = re.compile(r'[A-Z]{2,}\d{3,}')
DATE_RE = re.compile(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?')


class ReportPipeline(PipelineBase):
    SOURCE_TYPE = "report"
    SOURCE_ID = "06"

    def parse(self, file_path: str, doc_file: Optional[str] = None) -> List[Dict[str, Any]]:
        text = self._read_file(file_path)
        if doc_file is None:
            doc_file = file_path.split("/")[-1].split("\\")[-1]
        slug = self.doc_slug(doc_file)

        report_meta = self._extract_report_meta(text)
        sections = self._split_body(text)
        if not sections:
            sections = [(text[:200] if text else "空文档", text)]

        cards = []
        for seq, (title, body) in enumerate(sections):
            if not body.strip():
                continue
            chunks = self.split_body(body)
            for ci, chunk in enumerate(chunks):
                t = title if ci == 0 else f"{title} ({ci+1})"
                path = self.make_path(doc_file, [title])
                card = self.make_card(
                    doc_file=doc_file, doc_slug=slug, title=t,
                    level=0, path=path, line_start=0, body=chunk,
                    seq=seq * 10 + ci,
                )
                card["report_meta"] = report_meta
                cards.append(card)

        return cards

    def _read_file(self, file_path: str) -> str:
        for enc in ["utf-8", "gbk", "gb2312", "utf-16"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise PipelineError("无法识别文件编码")

    def _extract_report_meta(self, text: str) -> Dict[str, Any]:
        meta: Dict[str, Any] = {
            "report_type": "其他",
            "issuing_org": "",
            "certificate_no": "",
            "product_models": [],
            "tested_capabilities": [],
            "valid_from": "",
            "valid_to": "",
            "scan_available": False,
        }

        if not text:
            return meta

        # report_type
        for rtype, keywords in REPORT_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    meta["report_type"] = rtype
                    break
            if meta["report_type"] != "其他":
                break

        # product_models
        meta["product_models"] = list(set(PRODUCT_MODEL_RE.findall(text)))

        # tested_capabilities
        for kw in CAPABILITY_KEYWORDS:
            if kw.lower() in text.lower():
                meta["tested_capabilities"].append(kw)

        # issuing_org
        org = self._extract_field(text, ["检测机构", "检测单位", "认证机构", "颁发机构"])
        if org:
            meta["issuing_org"] = org

        # certificate_no
        cert = self._extract_field(text, ["证书编号", "报告编号", "编号", "Certificate No"])
        if cert:
            meta["certificate_no"] = cert

        # valid dates
        date_from = self._extract_date(text, ["有效期从", "有效起始", "签发日期", "检测日期"])
        if date_from:
            meta["valid_from"] = date_from

        date_to = self._extract_date(text, ["有效期至", "有效截止", "有效期到"])
        if date_to:
            meta["valid_to"] = date_to

        # scan_available
        scan_keywords = ["扫描件", "扫描", "电子版", "附件", "含二维码"]
        for kw in scan_keywords:
            if kw in text:
                meta["scan_available"] = True
                break

        return meta

    def _split_body(self, text: str) -> List[tuple]:
        sections = []
        parts = re.split(r'^(#{1,3}\s+.+)$', text, flags=re.MULTILINE)

        if len(parts) <= 1:
            first_line = text.split("\n", 1)[0].strip()[:80] if text.strip() else "报告内容"
            return [(first_line, text)]

        current_title = ""
        current_body = ""
        for part in parts:
            part_stripped = part.strip()
            if re.match(r'^#{1,3}\s+', part_stripped):
                if current_title and current_body.strip():
                    sections.append((current_title, current_body.strip()))
                current_title = re.sub(r'^#{1,3}\s+', '', part_stripped)
                current_body = ""
            else:
                current_body += part

        if current_title and current_body.strip():
            sections.append((current_title, current_body.strip()))

        if not sections:
            first_line = text.split("\n", 1)[0].strip()[:80] if text.strip() else "报告内容"
            sections.append((first_line, text))

        return sections

    def _extract_field(self, text: str, keywords: List[str]) -> str:
        for kw in keywords:
            pattern = re.compile(
                re.escape(kw) + r'[:：\s]*([^\n,，。；;]+)',
                re.IGNORECASE,
            )
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_date(self, text: str, keywords: List[str]) -> str:
        for kw in keywords:
            pattern = re.compile(
                re.escape(kw) + r'[:：\s]*' + DATE_RE.pattern,
                re.IGNORECASE,
            )
            match = pattern.search(text)
            if match:
                date_match = DATE_RE.search(match.group())
                if date_match:
                    return date_match.group()
        return ""
