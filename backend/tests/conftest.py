"""
Shared test fixtures for HTTP stub testing.
Uses `responses` library to mock external HTTP calls.
"""
import json
import pytest
import responses


# ── Default test LLM profile ──
TEST_LLM_PROFILE = {
    "base_url": "https://test-llm.example.com/v1",
    "api_key": "test-key-12345",
    "model": "test-model",
}

TEST_EMBEDDING_URL = "https://api.siliconflow.cn/v1/embeddings"


def _make_llm_response(content: str) -> dict:
    """Build a standard OpenAI-compatible chat completion response."""
    return {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


def _make_embedding_response(vectors: list) -> dict:
    """Build a standard embedding API response."""
    return {
        "data": [
            {"embedding": vec, "index": i} for i, vec in enumerate(vectors)
        ],
        "usage": {"prompt_tokens": 10, "total_tokens": 10},
    }


@pytest.fixture
def mock_llm():
    """Stub all LLM /chat/completions calls.

    Usage:
        def test_something(mock_llm):
            mock_llm.set_response('{"intent":"search","params":{"query":"AE800"}}')
            # or
            mock_llm.set_responses(["response1", "response2"])  # sequential calls
    """
    class LLMStub:
        def __init__(self):
            self._responses = []
            self._calls = []

        def set_response(self, content: str):
            self._responses = [_make_llm_response(content)]

        def set_responses(self, contents: list):
            self._responses = [_make_llm_response(c) for c in contents]

        def set_error(self, status_code: int = 500):
            self._responses = [{"error": "server error"}]
            self._error_code = status_code

        @property
        def calls(self):
            return self._calls

    stub = LLMStub()

    def request_callback(request):
        body = json.loads(request.body)
        stub._calls.append(body)
        if stub._responses:
            resp = stub._responses.pop(0)
            if isinstance(resp, dict) and "error" in resp:
                return (500, {}, json.dumps(resp))
            return (200, {}, json.dumps(resp))
        return (200, {}, json.dumps(_make_llm_response("{}")))

    # Match any /chat/completions endpoint
    responses.post(
        re.compile(r"https://.+/chat/completions"),
        callback=request_callback,
        content_type="application/json",
    )

    return stub


@pytest.fixture
def mock_embedding():
    """Stub the embedding API call.

    Usage:
        def test_something(mock_embedding):
            mock_embedding.set_vectors([[0.1, 0.2], [0.3, 0.4]])
    """
    class EmbeddingStub:
        def __init__(self):
            self._vectors = None
            self._calls = []
            self._error_code = None

        def set_vectors(self, vectors: list):
            self._vectors = vectors

        def set_error(self, status_code: int = 500):
            self._error_code = status_code

        @property
        def calls(self):
            return self._calls

    stub = EmbeddingStub()

    def request_callback(request):
        body = json.loads(request.body)
        stub._calls.append(body)

        if stub._error_code:
            return (stub._error_code, {}, json.dumps({"message": "error"}))

        vectors = stub._vectors or [[0.1] * 10 for _ in body.get("input", [])]
        return (200, {}, json.dumps(_make_embedding_response(vectors)))

    responses.post(
        TEST_EMBEDDING_URL,
        callback=request_callback,
        content_type="application/json",
    )

    return stub


@pytest.fixture
def mock_all_http(mock_llm, mock_embedding):
    """Combination fixture: stubs both LLM and embedding calls."""
    return mock_llm, mock_embedding


import re  # needed for re.compile in mock_llm
