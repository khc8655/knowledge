from fastapi import APIRouter, HTTPException, Query
from db.models import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    status: str = Query(None),
    type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    conn = get_db()
    try:
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if type:
            conditions.append("job_type = ?")
            params.append(type)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * page_size

        total = conn.execute(f"SELECT COUNT(*) as cnt FROM jobs{where}", params).fetchone()['cnt']
        rows = conn.execute(
            f"SELECT * FROM jobs{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset]
        ).fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }
    finally:
        conn.close()


@router.get("/{job_id}")
async def get_job(job_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
        return dict(row)
    finally:
        conn.close()


@router.post("/{job_id}/retry")
async def retry_job(job_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
        if row['status'] not in ('failed',):
            raise HTTPException(status_code=409, detail="JOB_NOT_RETRYABLE")

        conn.execute(
            "UPDATE jobs SET status = 'pending', retry_count = retry_count + 1, started_at = NULL WHERE id = ?",
            (job_id,)
        )
        conn.commit()
        return {"status": "retried", "job_id": job_id}
    finally:
        conn.close()


@router.delete("/{job_id}")
async def delete_job(job_id: int, force: bool = Query(False)):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
        if row['status'] not in ('pending', 'failed', 'cancelled') and not force:
            raise HTTPException(status_code=409, detail="JOB_ALREADY_RUNNING")

        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        return {"status": "deleted", "job_id": job_id}
    finally:
        conn.close()
