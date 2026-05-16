"""BOM (Bill of Materials) API endpoints."""
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from card.store import CardStore
from config import AppConfig
from db.models import get_db
from services.bom_service import BomService

router = APIRouter(prefix="/bom", tags=["bom"])


def _get_store() -> CardStore:
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    return CardStore(data_dir=data_dir)


# ------------------------------------------------------------------
# Request model
# ------------------------------------------------------------------
class BomGenerateBody(BaseModel):
    project_id: str
    scenario: str = ""
    room_count: int = 1
    deployment_type: str = "on-prem"
    required_models: Optional[List[str]] = None
    budget_limit: Optional[float] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/generate")
async def generate_bom(body: BomGenerateBody):
    """Generate a BOM from required models.

    Looks up evidence cards whose body/title mentions each required model,
    then delegates to BomService.generate().
    """
    store = _get_store()
    required = body.required_models or []

    # Collect evidence cards that mention any required model
    evidences = []
    seen_ids = set()

    if required:
        all_cards = store.list_cards(page_size=10000).get("items", [])
        for card in all_cards:
            card_id = card.get("id", "")
            if card_id in seen_ids:
                continue
            combined = (card.get("body", "") + " " + card.get("title", "")).upper()
            for model in required:
                if model.upper() in combined:
                    seen_ids.add(card_id)
                    evidences.append(card)
                    break

    if not evidences:
        raise HTTPException(
            status_code=404,
            detail="NO_EVIDENCE_FOUND",
        )

    conn = get_db()
    try:
        svc = BomService(conn)
        result = svc.generate(
            project_id=body.project_id,
            scenario=body.scenario,
            room_count=body.room_count,
            deployment_type=body.deployment_type,
            required_models=required,
            budget_limit=body.budget_limit or 0,
            evidences=evidences,
        )
        return result
    finally:
        conn.close()
