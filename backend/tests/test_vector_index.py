"""Tests for VectorIndex with HTTP stubs."""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import responses
from index.vector import VectorIndex


EMBEDDING_URL = "https://api.siliconflow.cn/v1/embeddings"


def _make_embedding_response(vectors: list) -> dict:
    return {
        "data": [
            {"embedding": vec, "index": i} for i, vec in enumerate(vectors)
        ],
    }


@responses.activate
def test_embed_batch_success():
    """Normal embedding: API returns vectors."""
    vec1 = [0.1, 0.2, 0.3]
    vec2 = [0.4, 0.5, 0.6]
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec1, vec2]))

    idx = VectorIndex()
    result = idx._embed_batch(["hello", "world"], api_key="test-key")

    assert result is not None
    assert len(result) == 2
    assert result[0] == vec1
    assert result[1] == vec2


@responses.activate
def test_embed_batch_retry_on_429():
    """429 rate limit -> retry after wait, then succeed."""
    vec = [0.1, 0.2, 0.3]

    # First call: 429, second call: success
    responses.post(EMBEDDING_URL, json={"retry_after": 0.01}, status=429)
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec]))

    idx = VectorIndex()
    result = idx._embed_batch(["test"], api_key="test-key")

    assert result is not None
    assert len(result) == 1
    assert len(responses.calls) == 2


@responses.activate
def test_embed_batch_retry_on_error():
    """500 error -> retry, then succeed."""
    vec = [0.1, 0.2, 0.3]

    responses.post(EMBEDDING_URL, json={"message": "error"}, status=500)
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec]))

    idx = VectorIndex()
    result = idx._embed_batch(["test"], api_key="test-key")

    assert result is not None
    assert len(responses.calls) == 2


@responses.activate
def test_embed_batch_all_retries_fail():
    """All 3 retries fail -> returns None."""
    responses.post(EMBEDDING_URL, json={"message": "error"}, status=500)
    responses.post(EMBEDDING_URL, json={"message": "error"}, status=500)
    responses.post(EMBEDDING_URL, json={"message": "error"}, status=500)

    idx = VectorIndex()
    result = idx._embed_batch(["test"], api_key="test-key")

    assert result is None
    assert len(responses.calls) == 3


@responses.activate
def test_embed_batch_timeout_retry():
    """Timeout -> retry, then succeed."""
    import requests as req
    vec = [0.1, 0.2, 0.3]

    responses.post(EMBEDDING_URL, body=req.Timeout("timeout"))
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec]))

    idx = VectorIndex()
    result = idx._embed_batch(["test"], api_key="test-key")

    assert result is not None
    assert len(responses.calls) == 2


@responses.activate
def test_embed_batch_preserves_order():
    """Embeddings are returned sorted by index field."""
    vec1 = [0.1] * 3
    vec2 = [0.2] * 3
    vec3 = [0.3] * 3

    # API returns in order (index 0, 1, 2)
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec1, vec2, vec3]))

    idx = VectorIndex()
    result = idx._embed_batch(["a", "b", "c"], api_key="test-key", batch_size=10)

    assert len(result) == 3
    assert result[0] == vec1
    assert result[1] == vec2
    assert result[2] == vec3


@responses.activate
def test_embed_batch_splits_large_input():
    """Large input is split into batches."""
    vec = [0.1] * 3

    # batch_size=2, 5 items -> 3 batches
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec, vec]))
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec, vec]))
    responses.post(EMBEDDING_URL, json=_make_embedding_response([vec]))

    idx = VectorIndex()
    result = idx._embed_batch(["a", "b", "c", "d", "e"], api_key="test-key", batch_size=2)

    assert result is not None
    assert len(result) == 5
    assert len(responses.calls) == 3
