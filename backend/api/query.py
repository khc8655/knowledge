"""
查询 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
sys.path.append("/home/jjb/wiki")

router = APIRouter(tags=["query"])

class QueryRequest(BaseModel):
    query: str
    limit: int = 10
    source_type: Optional[str] = None
    include_low_quality: bool = False
    include_history: bool = False

class QueryResult(BaseModel):
    card_id: str
    title: str
    body: str
    source_type: str
    doc_file: str
    path: str
    hit_rate: float
    quality_tier: str
    route_source: str

@router.post("/query")
async def query_knowledge(request: QueryRequest):
    """查询知识库"""
    if not request.query or len(request.query) > 500:
        raise HTTPException(400, detail="查询为空或超长")
    
    # 调用 wiki_test 检索引擎
    import subprocess
    result = subprocess.run(
        ["python3", "/home/jjb/wiki/query_unified.py", request.query, "--json"],
        capture_output=True,
        text=True,
        timeout=15
    )
    
    if result.returncode != 0:
        raise HTTPException(500, detail="查询引擎错误")
    
    # 解析结果（后续实现 JSON 解析）
    return {
        "query": request.query,
        "results": [],
        "total": 0,
        "elapsed_ms": 0,
        "route_source": "rule"
    }

@router.get("/query/history")
async def query_history(
    page: int = 1,
    page_size: int = 20,
    since: Optional[str] = None
):
    """查询历史"""
    # TODO: 从数据库查询
    return {"history": [], "total": 0}

@router.get("/query/route_cache")
async def route_cache(status: Optional[str] = None):
    """路由缓存"""
    # TODO: 实现
    return {"cache": [], "total": 0}
