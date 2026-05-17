"""
反馈 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from db.models import get_db
from services.query_service import submit_feedback

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    query_id: Optional[str] = None
    query_text: Optional[str] = ""
    card_id: str
    feedback: str  # positive | negative
    route_used: Optional[str] = None
    hit_rate: Optional[float] = None


@router.post("/feedback")
async def submit_feedback_api(feedback: FeedbackRequest):
    """提交反馈"""
    try:
        submit_feedback(
            query_text=feedback.query_text or feedback.card_id,
            card_id=feedback.card_id,
            feedback=feedback.feedback,
            route_used=feedback.route_used or "direct",
        )
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(500, detail=f"FEEDBACK_ERROR: {e}")


@router.get("/feedback/stats")
async def feedback_stats():
    """反馈统计"""
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM query_feedback").fetchone()["c"]
        positive = conn.execute(
            "SELECT COUNT(*) as c FROM query_feedback WHERE feedback='positive'"
        ).fetchone()["c"]
        negative = conn.execute(
            "SELECT COUNT(*) as c FROM query_feedback WHERE feedback='negative'"
        ).fetchone()["c"]
        active_routes = conn.execute(
            "SELECT COUNT(*) as c FROM route_mappings WHERE is_active=1"
        ).fetchone()["c"]

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "active_routes": active_routes,
        }
    finally:
        conn.close()


@router.post("/feedback/optimize")
async def optimize_routes():
    """优化路由权重 — 重新计算所有 route_mappings 的 confidence"""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM route_mappings").fetchall()
        updated = 0
        for row in rows:
            pos = row["positive_count"]
            neg = row["negative_count"]
            total = pos + neg
            if total == 0:
                continue

            confidence = pos / total
            is_active = 0
            source = row["source"]

            if confidence >= 0.7 and total >= 5:
                is_active = 1
                source = "feedback_learned"
            elif confidence < 0.3 and total >= 5:
                is_active = 0
                source = "feedback_learned"
            elif confidence < 0.5 and total >= 10:
                is_active = 0

            conn.execute(
                """UPDATE route_mappings SET confidence=?, is_active=?, source=?,
                   updated_at=datetime('now') WHERE id=?""",
                (confidence, is_active, source, row["id"]),
            )
            updated += 1

        conn.commit()
        return {"status": "optimized", "updated": updated}
    finally:
        conn.close()


@router.post("/feedback/optimize/apply")
async def apply_optimization():
    """应用优化结果 — 激活高置信度路由，停用低置信度路由"""
    conn = get_db()
    try:
        # Activate routes with confidence >= 0.7 and enough data
        activated = conn.execute(
            """UPDATE route_mappings SET is_active=1, source='feedback_learned',
               updated_at=datetime('now')
               WHERE confidence >= 0.7 AND total_count >= 5 AND is_active=0"""
        ).rowcount

        # Deactivate routes with low confidence
        deactivated = conn.execute(
            """UPDATE route_mappings SET is_active=0, updated_at=datetime('now')
               WHERE confidence < 0.3 AND total_count >= 5 AND is_active=1"""
        ).rowcount

        conn.commit()
        return {
            "status": "applied",
            "activated": activated,
            "deactivated": deactivated,
        }
    finally:
        conn.close()


@router.post("/feedback/sync-route-mappings")
async def sync_route_mappings():
    """同步路由映射 — 清理过期缓存，刷新活跃路由"""
    conn = get_db()
    try:
        # Clear stale cache entries (no hits in 30 days)
        cleared = conn.execute(
            """DELETE FROM route_cache
               WHERE last_hit_at < datetime('now', '-30 days')"""
        ).rowcount

        # Count active mappings
        active = conn.execute(
            "SELECT COUNT(*) as c FROM route_mappings WHERE is_active=1"
        ).fetchone()["c"]

        conn.commit()
        return {
            "status": "synced",
            "cache_cleared": cleared,
            "active_mappings": active,
        }
    finally:
        conn.close()
