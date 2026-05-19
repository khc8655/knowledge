"""Tests for chat_service with HTTP stubs."""
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import responses
from unittest.mock import AsyncMock, MagicMock, patch

from services.chat_service import (
    _detect_intent_fallback,
    _build_card_context,
    _build_messages,
    _llm_stream_sync,
    _sse_event,
)


# ── Pure function tests (no HTTP) ──

def test_detect_intent_fallback_search():
    assert _detect_intent_fallback("AE800价格是多少")["intent"] == "search"
    assert _detect_intent_fallback("PE8000停产了吗")["intent"] == "search"


def test_detect_intent_fallback_proposal():
    assert _detect_intent_fallback("帮我做个方案")["intent"] == "proposal"


def test_detect_intent_fallback_tender():
    assert _detect_intent_fallback("分析这个招标文件")["intent"] == "tender"


def test_detect_intent_fallback_bom():
    assert _detect_intent_fallback("生成BOM清单")["intent"] == "bom"


def test_detect_intent_fallback_reply():
    assert _detect_intent_fallback("帮我回复客户")["intent"] == "reply"


def test_detect_intent_fallback_default_search():
    """Unknown input defaults to search."""
    assert _detect_intent_fallback("随便问个问题")["intent"] == "search"


def test_build_card_context():
    cards = [
        {"title": "AE800", "body": "4K终端", "doc_file": "a.docx", "brand": "小鱼", "hit_rate": 0.9},
        {"title": "GE600", "body": "8K终端", "doc_file": "b.docx", "brand": "", "hit_rate": 0.7},
    ]
    ctx = _build_card_context(cards)
    assert "AE800" in ctx
    assert "4K终端" in ctx
    assert "90%" in ctx
    assert "小鱼" in ctx


def test_build_card_context_truncates():
    """Context is truncated at max_chars."""
    cards = [{"title": f"card{i}", "body": "x" * 2000, "doc_file": "a.docx", "brand": "", "hit_rate": 0.5} for i in range(10)]
    ctx = _build_card_context(cards, max_chars=1000)
    assert len(ctx) <= 1500  # some overhead from headers


def test_build_messages():
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！"},
    ]
    msgs = _build_messages(history, "系统提示", "用户问题", context="知识库内容", history_limit=10)
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "系统提示"
    assert msgs[-1]["role"] == "user"
    assert "知识库内容" in msgs[-1]["content"]
    assert "用户问题" in msgs[-1]["content"]


def test_build_messages_no_context():
    msgs = _build_messages([], "系统", "问题", context=None)
    assert len(msgs) == 2
    assert msgs[-1]["content"] == "问题"


def test_sse_event():
    event = _sse_event("thinking", {"stage": "test"})
    assert event.startswith("event: thinking\n")
    assert "data:" in event
    assert event.endswith("\n\n")


# ── HTTP stub tests ──

def _run_stream_test(profile, messages, sse_body=None, post_status=200, post_json=None):
    """Helper to run _llm_stream_sync with a running event loop."""
    if sse_body:
        responses.post(
            "https://test-llm.example.com/v1/chat/completions",
            body=sse_body,
            content_type="text/event-stream",
        )
    elif post_json:
        responses.post(
            "https://test-llm.example.com/v1/chat/completions",
            json=post_json,
            status=post_status,
        )

    queue = asyncio.Queue()
    loop = asyncio.new_event_loop()

    async def collect():
        # Give the executor thread time to complete
        await asyncio.sleep(0.3)
        tokens = []
        while not queue.empty():
            token = queue.get_nowait()
            if token is None:
                break
            tokens.append(token)
        return tokens

    # Run the sync function in executor, collect results
    async def run():
        loop.run_in_executor(None, _llm_stream_sync, profile, messages, queue, loop)
        return await collect()

    tokens = loop.run_until_complete(run())
    loop.close()
    return tokens


@responses.activate
def test_llm_stream_sync_yields_tokens():
    """Streaming LLM call yields tokens via queue."""
    sse_body = b'\n'.join([
        b'data: {"choices":[{"delta":{"content":"hello"}}]}',
        b'data: {"choices":[{"delta":{"content":" world"}}]}',
        b'data: [DONE]',
    ])

    profile = {
        "base_url": "https://test-llm.example.com/v1",
        "api_key": "test-key",
        "model": "test-model",
    }

    tokens = _run_stream_test(profile, [{"role": "user", "content": "test"}], sse_body=sse_body)
    assert tokens == ["hello", " world"]


@responses.activate
def test_llm_stream_sync_error_puts_error_in_queue():
    """LLM call error -> error message in queue + None sentinel."""
    profile = {
        "base_url": "https://test-llm.example.com/v1",
        "api_key": "test-key",
        "model": "test-model",
    }

    tokens = _run_stream_test(profile, [], post_status=500, post_json={"error": "server error"})
    assert len(tokens) == 1
    assert "LLM 调用失败" in tokens[0]


@responses.activate
def test_llm_stream_sync_malformed_lines_skipped():
    """Malformed SSE lines are skipped gracefully."""
    sse_body = b'\n'.join([
        b'',
        b'data: [DONE]',
    ])

    profile = {
        "base_url": "https://test-llm.example.com/v1",
        "api_key": "test-key",
        "model": "test-model",
    }

    tokens = _run_stream_test(profile, [], sse_body=sse_body)
    assert tokens == []
