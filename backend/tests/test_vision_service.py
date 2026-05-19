"""Tests for vision_service with HTTP stubs."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import responses
from services.vision_service import describe_image, summarize_slide


@responses.activate
def test_describe_image_success():
    """Vision model returns image description."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"choices": [{"message": {"content": "这是一张AE800终端的产品图片，展示了设备前面板"}}]},
    )

    # 1x1 red PNG
    image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
    result = describe_image(image_bytes, content_type="image/png")

    assert "AE800" in result
    assert len(result) > 0

    # Verify request was made
    assert len(responses.calls) == 1
    req_body = responses.calls[0].request.body
    assert b"image_url" in req_body


@responses.activate
def test_describe_image_api_error():
    """Vision API returns 500 -> raise_for_status raises."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"error": "server error"},
        status=500,
    )

    image_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

    with pytest.raises(Exception):
        describe_image(image_bytes)


@responses.activate
def test_summarize_slide_success():
    """Slide summarization returns text summary."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"choices": [{"message": {"content": "本页介绍了AE800终端的4K视频会议能力和H.265SVC编码支持"}}]},
    )

    result = summarize_slide(
        title="AE800产品介绍",
        text_content="4K视频会议终端\n支持H.265SVC",
        image_descriptions=["终端前面板图片"],
        doc_file="AE800.pptx",
    )

    assert "AE800" in result
    assert len(result) > 0


@responses.activate
def test_summarize_slide_no_images():
    """Slide with text only, no image descriptions."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"choices": [{"message": {"content": "本页为纯文本内容摘要"}}]},
    )

    result = summarize_slide(
        title="概述",
        text_content="项目背景和需求分析",
        image_descriptions=[],
    )

    assert "摘要" in result


@responses.activate
def test_summarize_slide_api_error():
    """API error -> raise_for_status raises."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"error": "rate limited"},
        status=429,
    )

    with pytest.raises(Exception):
        summarize_slide(title="test", text_content="test", image_descriptions=[])
