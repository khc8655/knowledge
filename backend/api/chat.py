"""
对话式 API — 会话管理 + SSE 流式消息
"""
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from db.models import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Request/Response Models ──────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    mode: str = "auto"

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid = {"auto", "search", "proposal", "tender", "bom", "reply"}
        if v not in valid:
            raise ValueError(f"mode must be one of {valid}")
        return v


class UpdateSessionRequest(BaseModel):
    title: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None


class SendMessageRequest(BaseModel):
    content: str
    mode_override: Optional[str] = None


# ── Session CRUD ─────────────────────────────────────────────────────

@router.post("/sessions")
async def create_session(req: CreateSessionRequest):
    sid = uuid.uuid4().hex[:16]
    now = datetime.utcnow().isoformat()
    title = req.title or "新对话"
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO chat_sessions (id, title, mode, created_at, updated_at) VALUES (?,?,?,?,?)",
            (sid, title, req.mode, now, now),
        )
        conn.commit()
        return {"id": sid, "title": title, "mode": req.mode, "status": "active",
                "created_at": now, "updated_at": now}
    finally:
        conn.close()


@router.get("/sessions")
async def list_sessions(
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    conn = get_db()
    try:
        offset = (page - 1) * page_size
        rows = conn.execute(
            "SELECT * FROM chat_sessions WHERE status=? ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (status, page_size, offset),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM chat_sessions WHERE status=?", (status,)
        ).fetchone()[0]
        return {"items": [dict(r) for r in rows], "total": total}
    finally:
        conn.close()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id=?", (session_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, detail="SESSION_NOT_FOUND")
        messages = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id=? ORDER BY created_at",
            (session_id,),
        ).fetchall()
        result = dict(row)
        result["messages"] = []
        for m in messages:
            msg = dict(m)
            if msg.get("cards_json"):
                try:
                    msg["cards"] = json.loads(msg["cards_json"])
                except Exception:
                    msg["cards"] = []
            else:
                msg["cards"] = []
            result["messages"].append(msg)
        return result
    finally:
        conn.close()


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM chat_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="SESSION_NOT_FOUND")
        updates = []
        params = []
        if req.title is not None:
            updates.append("title=?")
            params.append(req.title)
        if req.mode is not None:
            updates.append("mode=?")
            params.append(req.mode)
        if req.status is not None:
            updates.append("status=?")
            params.append(req.status)
        if not updates:
            return {"status": "ok"}
        updates.append("updated_at=?")
        params.append(datetime.utcnow().isoformat())
        params.append(session_id)
        conn.execute(f"UPDATE chat_sessions SET {','.join(updates)} WHERE id=?", params)
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM chat_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="SESSION_NOT_FOUND")
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE chat_sessions SET status='deleted', updated_at=? WHERE id=?",
            (now, session_id),
        )
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@router.post("/sessions/{session_id}/archive")
async def archive_session(session_id: str):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM chat_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="SESSION_NOT_FOUND")
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE chat_sessions SET status='archived', updated_at=? WHERE id=?",
            (now, session_id),
        )
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


# ── Messages ─────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/messages")
async def list_messages(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    conn = get_db()
    try:
        row = conn.execute("SELECT id FROM chat_sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="SESSION_NOT_FOUND")
        offset = (page - 1) * page_size
        messages = conn.execute(
            "SELECT * FROM chat_messages WHERE session_id=? ORDER BY created_at LIMIT ? OFFSET ?",
            (session_id, page_size, offset),
        ).fetchall()
        result = []
        for m in messages:
            msg = dict(m)
            if msg.get("cards_json"):
                try:
                    msg["cards"] = json.loads(msg["cards_json"])
                except Exception:
                    msg["cards"] = []
            else:
                msg["cards"] = []
            result.append(msg)
        return {"items": result}
    finally:
        conn.close()


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, req: SendMessageRequest):
    """发送消息，返回 SSE 流式响应。"""
    conn = get_db()
    try:
        session = conn.execute(
            "SELECT * FROM chat_sessions WHERE id=? AND status='active'", (session_id,)
        ).fetchone()
        if not session:
            raise HTTPException(404, detail="SESSION_NOT_FOUND")
    finally:
        conn.close()

    if not req.content.strip():
        raise HTTPException(400, detail="EMPTY_MESSAGE")

    from services.chat_service import stream_chat_response

    return StreamingResponse(
        stream_chat_response(session_id, req.content, req.mode_override),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
