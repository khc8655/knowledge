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
