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


if __name__ == "__main__":
    test_parse_txt()
    print("TXT PASS")
