from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from services.query_service import search, submit_feedback

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    query: str
    limit: int = 10


class FeedbackRequest(BaseModel):
    query_text: str
    card_id: str
    feedback: str
    route_used: str


@router.post("")
async def query(req: QueryRequest):
    if not req.query or len(req.query) > 500:
        raise HTTPException(400, detail="INVALID_QUERY")
    result = search(req.query, limit=req.limit)
    return result


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    if req.feedback not in ("positive", "negative"):
        raise HTTPException(400, detail="INVALID_FEEDBACK")
    submit_feedback(req.query_text, req.card_id, req.feedback, req.route_used)
    return {"status": "ok"}
