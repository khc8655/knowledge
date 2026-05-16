"""
卡片 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(tags=["cards"])

class CardUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None

@router.get("/cards")
async def list_cards(
    page: int = 1,
    page_size: int = 50,
    source_type: Optional[str] = None,
    intent_tag: Optional[str] = None,
    quality_tier: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """列出卡片"""
    # TODO: 从文件系统读取卡片
    return {"cards": [], "total": 0, "page": page}

@router.get("/cards/{id}")
async def get_card(id: str):
    """获取卡片详情"""
    # TODO: 读取卡片 JSON
    raise HTTPException(404, detail="卡片不存在")

@router.put("/cards/{id}")
async def update_card(id: str, update: CardUpdate):
    """更新卡片"""
    # TODO: 更新卡片并触发增量索引
    return {"status": "updated", "id": id}

@router.delete("/cards/{id}")
async def delete_card(id: str):
    """删除卡片"""
    # TODO: 删除卡片 JSON
    return {"status": "deleted", "id": id}

@router.get("/cards/stats")
async def card_stats():
    """卡片统计"""
    # TODO: 统计各类型卡片数量
    return {
        "total": 0,
        "by_source_type": {},
        "by_quality_tier": {}
    }
