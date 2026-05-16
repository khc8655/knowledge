"""Template CRUD API endpoints."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.models import get_db

router = APIRouter(prefix="/templates", tags=["templates"])


# ------------------------------------------------------------------
# Helper functions (callable by other services)
# ------------------------------------------------------------------
def create_template(data: dict, conn) -> dict:
    """Create a new template and return it as a dict."""
    now = datetime.now(timezone.utc).isoformat()
    template_id = data.get("id") or str(uuid.uuid4())
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO templates (id, template_type, name, industry, deployment_type,
                               file_path, schema_json, enabled, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            template_id,
            data["template_type"],
            data["name"],
            data.get("industry"),
            data.get("deployment_type"),
            data["file_path"],
            data.get("schema_json", "{}"),
            data.get("enabled", 1),
            now,
            now,
        ),
    )
    conn.commit()
    return get_template(template_id, conn)


def get_template(template_id: str, conn) -> Optional[dict]:
    """Get a template by ID. Returns dict or None."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)


def list_templates(
    template_type: Optional[str] = None,
    industry: Optional[str] = None,
    conn=None,
) -> list[dict]:
    """List enabled templates, optionally filtered by type and industry."""
    cur = conn.cursor()
    conditions = ["enabled = 1"]
    params: list = []
    if template_type:
        conditions.append("template_type = ?")
        params.append(template_type)
    if industry:
        conditions.append("industry = ?")
        params.append(industry)
    where = " AND ".join(conditions)
    cur.execute(f"SELECT * FROM templates WHERE {where} ORDER BY created_at DESC", params)
    return [dict(row) for row in cur.fetchall()]


def update_template(template_id: str, data: dict, conn) -> Optional[dict]:
    """Update mutable fields of a template. Returns updated dict or None."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM templates WHERE id = ?", (template_id,))
    if cur.fetchone() is None:
        return None

    mutable_fields = [
        "template_type", "name", "industry", "deployment_type",
        "file_path", "schema_json", "enabled",
    ]
    sets = []
    params: list = []
    for field in mutable_fields:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])
    if not sets:
        return get_template(template_id, conn)

    now = datetime.now(timezone.utc).isoformat()
    sets.append("updated_at = ?")
    params.append(now)
    params.append(template_id)

    cur.execute(
        f"UPDATE templates SET {', '.join(sets)} WHERE id = ?",
        params,
    )
    conn.commit()
    return get_template(template_id, conn)


def delete_template(template_id: str, conn) -> bool:
    """Delete a template. Returns True if deleted, False if not found."""
    cur = conn.cursor()
    cur.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    return cur.rowcount > 0


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class CreateTemplateBody(BaseModel):
    template_type: str
    name: str
    industry: Optional[str] = None
    deployment_type: Optional[str] = None
    file_path: str
    schema_json: Optional[str] = "{}"
    enabled: Optional[int] = 1


class UpdateTemplateBody(BaseModel):
    template_type: Optional[str] = None
    name: Optional[str] = None
    industry: Optional[str] = None
    deployment_type: Optional[str] = None
    file_path: Optional[str] = None
    schema_json: Optional[str] = None
    enabled: Optional[int] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("")
async def api_create_template(body: CreateTemplateBody):
    """Create a new template."""
    conn = get_db()
    try:
        tmpl = create_template(body.model_dump(), conn)
        return tmpl
    finally:
        conn.close()


@router.get("")
async def api_list_templates(
    template_type: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
):
    """List templates, optionally filtered by type and industry."""
    conn = get_db()
    try:
        return list_templates(template_type, industry, conn)
    finally:
        conn.close()


@router.get("/{template_id}")
async def api_get_template(template_id: str):
    """Get a template by ID."""
    conn = get_db()
    try:
        tmpl = get_template(template_id, conn)
        if tmpl is None:
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        return tmpl
    finally:
        conn.close()


@router.put("/{template_id}")
async def api_update_template(template_id: str, body: UpdateTemplateBody):
    """Update a template."""
    conn = get_db()
    try:
        data = {k: v for k, v in body.model_dump().items() if v is not None}
        tmpl = update_template(template_id, data, conn)
        if tmpl is None:
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        return tmpl
    finally:
        conn.close()


@router.delete("/{template_id}")
async def api_delete_template(template_id: str):
    """Delete a template."""
    conn = get_db()
    try:
        deleted = delete_template(template_id, conn)
        if not deleted:
            raise HTTPException(status_code=404, detail="TEMPLATE_NOT_FOUND")
        return {"status": "deleted", "id": template_id}
    finally:
        conn.close()
