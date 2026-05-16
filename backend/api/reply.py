"""Reply API — generate customer-facing replies from knowledge evidence."""
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from card.store import CardStore
from config import AppConfig
from db.models import get_db
from api.evidence import build_evidence
from services.reply_service import ReplyService

router = APIRouter(prefix="/reply", tags=["reply"])


def _get_store() -> CardStore:
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    return CardStore(data_dir=data_dir)


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class GenerateReplyBody(BaseModel):
    customer_question: str
    project_id: str = "default"
    keywords: Optional[List[str]] = None
    tone: str = "neutral"
    max_chars: int = 2000
    allowed_evidence_ids: Optional[List[str]] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/generate")
async def generate_reply(body: GenerateReplyBody):
    """Generate a customer reply by searching cards and building evidence.

    Flow:
    1. Search knowledge cards by keywords (from question or explicit keywords).
    2. Build evidence pack from matched cards.
    3. Generate reply via ReplyService.
    """
    if not body.customer_question.strip():
        raise HTTPException(status_code=400, detail="EMPTY_QUESTION")

    # Determine search keywords
    keywords = body.keywords
    if not keywords:
        # Extract simple keywords from the question (split on whitespace/punctuation)
        import re
        keywords = re.findall(r'[\w一-鿿]{2,}', body.customer_question)

    # Search cards
    store = _get_store()
    matched_cards = []
    seen_ids = set()

    for kw in keywords:
        result = store.list_cards(search=kw, page_size=50)
        for card in result.get("items", []):
            cid = card.get("id", "")
            if cid not in seen_ids:
                seen_ids.add(cid)
                matched_cards.append(card)

    # Build evidence from matched cards
    if matched_cards:
        evidence_result = build_evidence(
            matched_cards, task_type="reply", project_id=body.project_id
        )
        evidences = evidence_result.get("evidences", [])
        risk_summary = evidence_result.get("risk_summary", {})
    else:
        evidences = []
        risk_summary = {}

    # Generate reply
    conn = get_db()
    try:
        service = ReplyService(conn)
        result = service.generate(
            customer_question=body.customer_question,
            evidences=evidences,
            project_id=body.project_id,
            tone=body.tone,
            max_chars=body.max_chars,
            allowed_evidence_ids=body.allowed_evidence_ids,
        )
        # Merge risk summary from evidence build
        if risk_summary and not result["risk_summary"]:
            result["risk_summary"] = risk_summary
    finally:
        conn.close()

    return result
