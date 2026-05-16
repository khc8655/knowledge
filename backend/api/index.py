"""
索引 API
"""
from fastapi import APIRouter
from typing import Optional

router = APIRouter(tags=["indexes"])

@router.get("/indexes/status")
async def index_status():
    """索引状态"""
    return {
        "bm25": {"status": "ok", "cards_count": 0},
        "vector": {"status": "ok", "embeddings": 0},
        "fts5": {"status": "ok"}
    }

@router.post("/indexes/rebuild/{type}")
async def rebuild_index(type: str):
    """重建索引"""
    valid_types = ["bm25", "vector", "fts5", "topics", "all"]
    if type not in valid_types:
        return {"error": f"无效类型，可选: {valid_types}"}
    # TODO: 创建重建 Job
    return {"status": "job_created", "type": type}

@router.post("/indexes/annotate")
async def annotate_cards(scope: str = "all"):
    """触发标注"""
    # TODO: 创建标注 Job
    return {"status": "job_created", "scope": scope}
