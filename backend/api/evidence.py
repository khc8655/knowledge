"""Evidence Pack API endpoints."""
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from card.store import CardStore
from config import AppConfig
from db.models import get_db
from evidence.pack import EvidencePackBuilder

router = APIRouter(prefix="/evidence", tags=["evidence"])

_builder = EvidencePackBuilder()


def _get_store() -> CardStore:
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    return CardStore(data_dir=data_dir)


# ------------------------------------------------------------------
# Helper (callable by other services)
# ------------------------------------------------------------------
def build_evidence(
    cards: list[dict],
    task_type: str,
    project_id: str,
    conn=None,
) -> dict:
    """Build and optionally persist an evidence pack.

    Args:
        cards: List of card dicts (from CardStore).
        task_type: Task context (e.g. 'proposal', 'tender', 'reply').
        project_id: Target presales project ID.
        conn: Unused (kept for API compatibility with callers that pass a DB conn).

    Returns:
        Dict with keys: evidence_pack_id, evidences, risk_summary.
    """
    evidences = _builder.build(cards, task_type, project_id)
    pack_id = _builder.persist(evidences, project_id)
    risk_summary = _summarise_risks(evidences)
    return {
        "evidence_pack_id": pack_id,
        "evidences": evidences,
        "risk_summary": risk_summary,
    }


def _summarise_risks(evidences: list[dict]) -> dict:
    """Aggregate risk flags across a list of evidence dicts."""
    import json

    flag_counts: dict[str, int] = {}
    for ev in evidences:
        raw = ev.get("risk_flags", "[]")
        flags = json.loads(raw) if isinstance(raw, str) else raw
        for f in flags:
            flag_counts[f] = flag_counts.get(f, 0) + 1
    return {
        "total_evidence": len(evidences),
        "flag_counts": flag_counts,
    }


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class BuildEvidenceBody(BaseModel):
    card_ids: List[str]
    task_type: str
    project_id: Optional[str] = None
    persist: bool = True


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/build")
async def api_build_evidence(body: BuildEvidenceBody):
    """Build evidence pack from card IDs."""
    store = _get_store()
    cards = []
    for cid in body.card_ids:
        card = store.get(cid)
        if card is None:
            raise HTTPException(
                status_code=404,
                detail=f"Card not found: {cid}",
            )
        cards.append(card)

    project_id = body.project_id or "default"

    if body.persist:
        return build_evidence(cards, body.task_type, project_id)

    # Build only, do not persist
    evidences = _builder.build(cards, body.task_type, project_id)
    risk_summary = _summarise_risks(evidences)
    return {
        "evidence_pack_id": None,
        "evidences": evidences,
        "risk_summary": risk_summary,
    }


@router.get("/project/{project_id}")
async def list_project_evidence(
    project_id: str,
    include_archived: bool = Query(False),
):
    """List all evidence for a project."""
    return _builder.list_by_project(project_id, include_archived=include_archived)


@router.get("/{evidence_id}")
async def get_evidence(evidence_id: str):
    """Get single evidence by ID."""
    ev = _builder.get(evidence_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="EVIDENCE_NOT_FOUND")
    return ev


@router.post("/{evidence_id}/archive")
async def archive_evidence(evidence_id: str):
    """Soft-delete evidence."""
    ok = _builder.archive(evidence_id)
    if not ok:
        raise HTTPException(status_code=404, detail="EVIDENCE_NOT_FOUND")
    return {"status": "archived", "id": evidence_id}
