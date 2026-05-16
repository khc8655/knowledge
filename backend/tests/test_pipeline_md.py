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


if __name__ == "__main__":
    test_parse_markdown()
    test_coarse_doc_detection()
    print("PASS")
