import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipeline.report import ReportPipeline


def test_report_pipeline_generates_cards_with_report_meta():
    """Cards should have report_meta dict with expected keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_content = """# 检测报告概述

检测机构: 国家信息中心
证书编号: CMA-2024-00123
产品型号: VPRO5000
报告类型: CMA检测报告
有效期从: 2024-01-01
有效期至: 2026-12-31

本报告包含扫描件。

# 功能测试结果

支持AVC、SVC视频编码。
支持H.323、SIP协议。
支持SM2、SM3、SM4国密算法。
"""
        txt_path = os.path.join(tmpdir, "report.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        pipeline = ReportPipeline(data_dir=tmpdir)
        cards = pipeline.parse(txt_path)

        assert len(cards) >= 1
        card = cards[0]

        # report_meta must exist and be a dict
        assert "report_meta" in card
        assert isinstance(card["report_meta"], dict)

        meta = card["report_meta"]
        # Check all expected keys exist
        for key in [
            "report_type", "issuing_org", "certificate_no",
            "product_models", "tested_capabilities",
            "valid_from", "valid_to", "scan_available",
        ]:
            assert key in meta, f"Missing key: {key}"

        # Verify extracted values
        assert meta["report_type"] == "CMA"
        assert meta["issuing_org"] == "国家信息中心"
        assert meta["certificate_no"] == "CMA-2024-00123"
        assert "VPRO5000" in meta["product_models"]
        assert meta["valid_from"] == "2024-01-01"
        assert meta["valid_to"] == "2026-12-31"
        assert meta["scan_available"] is True
        assert "AVC" in meta["tested_capabilities"]
        assert "SVC" in meta["tested_capabilities"]
        assert "H.323" in meta["tested_capabilities"]
        assert "SIP" in meta["tested_capabilities"]

        # source_type should be report
        assert card["source_type"] == "report"


def test_report_pipeline_extracts_product_models():
    r"""Product models matching [A-Z]{2,}\d{3,} should be extracted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_content = """# 产品信息

检测机构: 某检测中心
产品型号包括: ABC1234、XYZ5678和DEF9012。

# 测试结论

各项指标合格。
"""
        txt_path = os.path.join(tmpdir, "models_report.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        pipeline = ReportPipeline(data_dir=tmpdir)
        cards = pipeline.parse(txt_path)

        assert len(cards) >= 1
        meta = cards[0]["report_meta"]
        models = meta["product_models"]
        assert "ABC1234" in models
        assert "XYZ5678" in models
        assert "DEF9012" in models


def test_report_pipeline_default_meta_when_extraction_fails():
    """When text has no extractable metadata, defaults should be used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_content = "这是一份普通的文档内容，没有任何结构化信息。"
        txt_path = os.path.join(tmpdir, "plain.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        pipeline = ReportPipeline(data_dir=tmpdir)
        cards = pipeline.parse(txt_path)

        assert len(cards) >= 1
        meta = cards[0]["report_meta"]

        assert meta["report_type"] == "其他"
        assert meta["product_models"] == []
        assert meta["tested_capabilities"] == []
        assert meta["issuing_org"] == ""
        assert meta["certificate_no"] == ""
        assert meta["valid_from"] == ""
        assert meta["valid_to"] == ""
        assert meta["scan_available"] is False


if __name__ == "__main__":
    test_report_pipeline_generates_cards_with_report_meta()
    test_report_pipeline_extracts_product_models()
    test_report_pipeline_default_meta_when_extraction_fails()
    print("ALL REPORT PIPELINE TESTS PASSED")
