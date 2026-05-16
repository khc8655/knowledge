from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from card.store import CardStore
from config import AppConfig
import os

router = APIRouter(prefix="/cards", tags=["cards"])


class CardUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


def _get_store() -> CardStore:
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    return CardStore(data_dir=data_dir)


@router.get("")
async def list_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    source_type: str = Query(None),
    intent_tag: str = Query(None),
    quality_tier: str = Query(None),
    search: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    store = _get_store()
    return store.list_cards(
        source_type=source_type,
        intent_tag=intent_tag,
        quality_tier=quality_tier,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


@router.get("/stats")
async def card_stats():
    store = _get_store()
    return store.stats()


@router.get("/{card_id}")
async def get_card(card_id: str):
    store = _get_store()
    card = store.get(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")
    return card


@router.put("/{card_id}")
async def update_card(card_id: str, update: CardUpdate):
    store = _get_store()
    existing = store.get(card_id)
    if not existing:
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")

    updates = update.model_dump(exclude_none=True)
    if not updates:
        return {"status": "no_changes", "id": card_id}

    if "body" in updates and updates["body"] != existing.get("body"):
        updates["char_count"] = len(updates["body"])

    store.update(card_id, updates)
    return {"status": "updated", "id": card_id}


@router.delete("/{card_id}")
async def delete_card(card_id: str):
    store = _get_store()
    if not store.delete(card_id):
        raise HTTPException(status_code=404, detail="CARD_NOT_FOUND")
    return {"status": "deleted", "id": card_id}
