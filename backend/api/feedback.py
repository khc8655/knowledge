"""
反馈 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["feedback"])

class FeedbackRequest(BaseModel):
    query_id: str
    query_text: str
    card_id: str
    feedback: str  # positive | negative
    route_used: Optional[str] = None
    hit_rate: Optional[float] = None

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """提交反馈"""
    # TODO: 写入数据库，更新路由映射
    return {"status": "recorded"}

@router.get("/feedback/stats")
async def feedback_stats():
    """反馈统计"""
    return {
        "total": 0,
        "positive": 0,
        "negative": 0,
        "active_routes": 0
    }

@router.post("/feedback/optimize")
async def optimize_routes():
    """优化路由权重"""
    # TODO: 基于反馈优化
    return {"status": "optimized"}

@router.post("/feedback/optimize/apply")
async def apply_optimization():
    """应用优化结果"""
    # TODO: 应用优化
    return {"status": "applied"}

@router.post("/feedback/sync-route-mappings")
async def sync_route_mappings():
    """同步路由映射"""
    # TODO: 同步
    return {"status": "synced"}
