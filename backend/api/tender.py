"""Tender API endpoints — analyze tender text and match requirements against evidence."""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from card.store import CardStore
from config import AppConfig
from db.models import get_db
from services.tender_service import TenderService

router = APIRouter(prefix="/tender", tags=["tender"])


def _get_store() -> CardStore:
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    return CardStore(data_dir=data_dir)


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class AnalyzeBody(BaseModel):
    tender_text: str
    project_id: Optional[str] = None


class MatchBody(BaseModel):
    project_id: Optional[str] = None
    requirement_ids: Optional[List[str]] = None
    candidate_models: Optional[List[str]] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/analyze")
async def analyze_tender(body: AnalyzeBody):
    """Analyze tender text and extract structured requirements.

    Extracts requirements using TenderService.extract_requirements().
    If project_id is provided, persists requirements to project_requirements table.

    Returns: { total, requirements }
    """
    conn = get_db()
    try:
        service = TenderService(conn)
        requirements = service.extract_requirements(body.tender_text)

        # Persist to project_requirements if project_id provided
        if body.project_id:
            cur = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            for req in requirements:
                structured = json.dumps({
                    "requirement_type": req["requirement_type"],
                    "target_models": req["target_models"],
                    "required_capabilities": req["required_capabilities"],
                    "required_evidence": req["required_evidence"],
                }, ensure_ascii=False)
                cur.execute(
                    """
                    INSERT INTO project_requirements
                        (id, project_id, requirement_type, raw_text, structured_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        req["id"],
                        body.project_id,
                        req["requirement_type"],
                        req["raw_text"],
                        structured,
                        now,
                    ),
                )
            conn.commit()

        return {
            "total": len(requirements),
            "requirements": requirements,
        }
    finally:
        conn.close()


@router.post("/match")
async def match_tender(body: MatchBody):
    """Match tender requirements against knowledge base evidence.

    Loads requirements from DB (by IDs or project_id), then searches cards
    for matching evidence by capability keywords in body/title text.

    Returns: { total, results }
    """
    conn = get_db()
    try:
        # Load requirements from DB
        cur = conn.cursor()
        if body.requirement_ids:
            placeholders = ",".join("?" for _ in body.requirement_ids)
            cur.execute(
                f"SELECT * FROM project_requirements WHERE id IN ({placeholders})",
                body.requirement_ids,
            )
        elif body.project_id:
            cur.execute(
                "SELECT * FROM project_requirements WHERE project_id = ?",
                (body.project_id,),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_id or requirement_ids must be provided",
            )

        rows = cur.fetchall()
        requirements = []
        for row in rows:
            row_dict = dict(row)
            structured = json.loads(row_dict.get("structured_json", "{}"))
            requirements.append({
                "id": row_dict["id"],
                "raw_text": row_dict["raw_text"],
                "requirement_type": row_dict.get("requirement_type", structured.get("requirement_type", "general")),
                "target_models": structured.get("target_models", []),
                "required_capabilities": structured.get("required_capabilities", []),
                "required_evidence": structured.get("required_evidence", []),
            })

        if not requirements:
            return {"total": 0, "results": []}

        # Build capability -> keywords map for card search
        from services.tender_service import CAPABILITY_KEYWORDS

        # Collect all capability keywords for searching cards
        all_keywords = set()
        for req in requirements:
            for cap in req.get("required_capabilities", []):
                keywords = CAPABILITY_KEYWORDS.get(cap, [])
                all_keywords.update(keywords)
            # Also add target models as search terms
            for model in req.get("target_models", []):
                all_keywords.add(model)

        # Search cards by capability keywords
        store = _get_store()
        product_evidence = []
        report_evidence = []
        seen_card_ids = set()

        # Get all cards (paginated scan)
        all_cards_result = store.list_cards(page_size=10000)
        all_cards = all_cards_result.get("items", [])

        for card in all_cards:
            card_id = card.get("id", "")
            if card_id in seen_card_ids:
                continue

            body_text = card.get("body", "").lower()
            title_text = card.get("title", "").lower()
            combined = body_text + " " + title_text

            # Check if any capability keyword matches
            matched = False
            for keyword in all_keywords:
                if keyword.lower() in combined:
                    matched = True
                    break

            if matched:
                seen_card_ids.add(card_id)
                source_type = card.get("source_type", "")
                if source_type == "report":
                    report_evidence.append(card)
                else:
                    product_evidence.append(card)

        # Match each requirement
        service = TenderService(conn)
        results = []
        for req in requirements:
            result = service.match_single(req, product_evidence, report_evidence)
            results.append(result)

        return {
            "total": len(results),
            "results": results,
        }
    finally:
        conn.close()


@router.get("/{output_id}")
async def get_tender_result(output_id: str):
    """Get tender analysis result from project_outputs."""
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM project_outputs WHERE id = ? AND output_type = 'tender'",
            (output_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="TENDER_NOT_FOUND")
        return dict(row)
    finally:
        conn.close()
