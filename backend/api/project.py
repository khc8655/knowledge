"""Project CRUD API endpoints."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db.models import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


# ------------------------------------------------------------------
# Helper functions (callable by other services)
# ------------------------------------------------------------------
def create_project(data: dict, conn) -> dict:
    """Insert a new presales project. Returns the created row as dict."""
    now = datetime.now(timezone.utc).isoformat()
    project_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO presales_projects
           (id, customer_name, industry, stage, deployment_type, description, owner,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            project_id,
            data["customer_name"],
            data.get("industry"),
            data.get("stage", "draft"),
            data.get("deployment_type"),
            data.get("description"),
            data.get("owner"),
            now,
            now,
        ),
    )
    conn.commit()
    return {
        "id": project_id,
        "customer_name": data["customer_name"],
        "industry": data.get("industry"),
        "stage": data.get("stage", "draft"),
        "deployment_type": data.get("deployment_type"),
        "description": data.get("description"),
        "owner": data.get("owner"),
        "created_at": now,
        "updated_at": now,
        "archived_at": None,
    }


def get_project(project_id: str, conn) -> Optional[dict]:
    """Return a single project by id, or None."""
    row = conn.execute(
        "SELECT * FROM presales_projects WHERE id = ?", (project_id,)
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_projects(
    page: int = 1, page_size: int = 20, stage: Optional[str] = None, conn=None
) -> dict:
    """List non-archived projects with pagination and optional stage filter."""
    where = "WHERE archived_at IS NULL"
    params: list = []
    if stage:
        where += " AND stage = ?"
        params.append(stage)

    total = conn.execute(
        f"SELECT COUNT(*) FROM presales_projects {where}", params
    ).fetchone()[0]

    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT * FROM presales_projects {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(r) for r in rows],
    }


_MUTABLE_FIELDS = {
    "customer_name",
    "industry",
    "stage",
    "deployment_type",
    "description",
    "owner",
}


def update_project(project_id: str, data: dict, conn) -> Optional[dict]:
    """Update mutable fields of a project. Returns updated row or None."""
    existing = get_project(project_id, conn)
    if existing is None:
        return None

    sets = []
    params: list = []
    for key in _MUTABLE_FIELDS:
        if key in data:
            sets.append(f"{key} = ?")
            params.append(data[key])

    if not sets:
        return existing

    now = datetime.now(timezone.utc).isoformat()
    sets.append("updated_at = ?")
    params.append(now)
    params.append(project_id)

    conn.execute(
        f"UPDATE presales_projects SET {', '.join(sets)} WHERE id = ?", params
    )
    conn.commit()
    return get_project(project_id, conn)


def archive_project(project_id: str, conn) -> bool:
    """Set archived_at on a project. Returns True if found."""
    existing = get_project(project_id, conn)
    if existing is None:
        return False
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE presales_projects SET archived_at = ?, updated_at = ? WHERE id = ?",
        (now, now, project_id),
    )
    conn.commit()
    return True


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class CreateProjectBody(BaseModel):
    customer_name: str
    industry: Optional[str] = None
    stage: str = "draft"
    deployment_type: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None


class UpdateProjectBody(BaseModel):
    customer_name: Optional[str] = None
    industry: Optional[str] = None
    stage: Optional[str] = None
    deployment_type: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("", status_code=201)
async def api_create_project(body: CreateProjectBody):
    conn = get_db()
    try:
        return create_project(body.model_dump(), conn)
    finally:
        conn.close()


@router.get("")
async def api_list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = Query(None),
):
    conn = get_db()
    try:
        return list_projects(page=page, page_size=page_size, stage=stage, conn=conn)
    finally:
        conn.close()


@router.get("/{project_id}")
async def api_get_project(project_id: str):
    conn = get_db()
    try:
        proj = get_project(project_id, conn)
        if proj is None:
            raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
        return proj
    finally:
        conn.close()


@router.put("/{project_id}")
async def api_update_project(project_id: str, body: UpdateProjectBody):
    conn = get_db()
    try:
        proj = update_project(project_id, body.model_dump(exclude_none=True), conn)
        if proj is None:
            raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
        return proj
    finally:
        conn.close()


@router.post("/{project_id}/archive")
async def api_archive_project(project_id: str):
    conn = get_db()
    try:
        ok = archive_project(project_id, conn)
        if not ok:
            raise HTTPException(status_code=404, detail="PROJECT_NOT_FOUND")
        return {"status": "archived", "id": project_id}
    finally:
        conn.close()
