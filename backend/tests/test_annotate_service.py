"""Tests for annotate_service with HTTP stubs."""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import responses
from services.annotate_service import annotate_card, annotate_batch, _fallback_annotation


ANNOTATION_RESPONSE = json.dumps({
    "intent_tags": ["性能参数", "报价价格"],
    "concept_tags": ["4K", "H.265", "SVC"],
    "scenario_tags": ["视频会议"],
    "card_type": "parameter",
    "summary": "AE800 4K视频会议终端，支持H.265SVC编码",
    "brand": "小鱼易连",
    "models": ["AE800"],
    "keywords": ["4K", "视频终端", "AE800"],
    "negative_concepts": [],
    "quality_tier": "high",
})


@responses.activate
def test_annotate_card_success():
    """Normal annotation: LLM returns valid JSON -> parsed and validated."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"choices": [{"message": {"content": ANNOTATION_RESPONSE}}]},
    )

    card = {
        "id": "test-001",
        "title": "AE800产品参数",
        "body": "4K视频会议终端，支持H.265SVC编码，8路视频输入",
        "doc_file": "AE800产品手册.docx",
        "path": "产品参数",
    }

    result = annotate_card(card, llm_call=None)

    assert result["card_type"] == "parameter"
    assert "性能参数" in result["intent_tags"]
    assert "4K" in result["concept_tags"]
    assert result["brand"] == "小鱼易连"
    assert "AE800" in result["models"]
    assert result["quality_tier"] == "high"
    assert result["content_hash"]  # auto-generated


@responses.activate
def test_annotate_card_llm_error_fallback():
    """LLM returns 500 -> fallback annotation used."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"error": "internal server error"},
        status=500,
    )

    card = {
        "id": "test-002",
        "title": "测试卡片",
        "body": "测试内容",
        "doc_file": "test.docx",
        "path": "test",
    }

    result = annotate_card(card, llm_call=None)

    assert result["card_type"] == "capability"
    assert result["quality_tier"] == "placeholder"
    assert result["summary"] == "测试卡片"


@responses.activate
def test_annotate_card_llm_invalid_json():
    """LLM returns non-JSON -> fallback annotation used."""
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"choices": [{"message": {"content": "这不是JSON"}}]},
    )

    card = {
        "id": "test-003",
        "title": "无效响应",
        "body": "内容",
    }

    result = annotate_card(card, llm_call=None)

    assert result["card_type"] == "capability"
    assert result["quality_tier"] == "placeholder"


def test_annotate_card_with_custom_llm_call():
    """Custom llm_call function is used when provided."""
    def mock_llm(system, user):
        return json.dumps({
            "intent_tags": ["安全保障"],
            "concept_tags": ["SM2"],
            "card_type": "capability",
            "summary": "安全加密功能",
            "brand": "",
            "models": [],
            "keywords": ["SM2"],
            "quality_tier": "medium",
        })

    card = {"id": "test-004", "title": "安全", "body": "SM2加密"}
    result = annotate_card(card, llm_call=mock_llm)

    assert "安全保障" in result["intent_tags"]
    assert result["quality_tier"] == "medium"


@responses.activate
def test_validate_annotation_clamps_values():
    """Validation clamps invalid tags and types."""
    # LLM returns too many tags and invalid card_type
    bad_response = json.dumps({
        "intent_tags": ["安全保障", "功能更新", "架构设计", "部署运维", "场景方案"],  # 5 tags, max 3
        "concept_tags": ["a", "b", "c", "d", "e", "f"],  # 6, max 5
        "card_type": "invalid_type",
        "summary": "x" * 100,  # too long, max 50
        "brand": "test",
        "models": [],
        "keywords": [],
        "quality_tier": "invalid_tier",
    })
    responses.post(
        "https://api.siliconflow.cn/v1/chat/completions",
        json={"choices": [{"message": {"content": bad_response}}]},
    )

    card = {"id": "test-005", "title": "t", "body": "b"}
    result = annotate_card(card, llm_call=None)

    assert len(result["intent_tags"]) <= 3
    assert len(result["concept_tags"]) <= 5
    assert result["card_type"] == "capability"  # invalid -> fallback
    assert len(result["summary"]) <= 50
    assert result["quality_tier"] == "placeholder"  # invalid -> fallback


def test_fallback_annotation():
    """Fallback annotation has expected structure."""
    card = {"title": "测试标题", "body": "测试内容"}
    result = _fallback_annotation(card, "abc123")

    assert result["intent_tags"] == []
    assert result["card_type"] == "capability"
    assert result["summary"] == "测试标题"
    assert result["quality_tier"] == "placeholder"
    assert result["content_hash"] == "abc123"
