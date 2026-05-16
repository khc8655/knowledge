from fastapi import APIRouter, HTTPException, Query
from db.models import get_db
from job.scheduler import JobScheduler

router = APIRouter(prefix="/indexes", tags=["indexes"])


@router.get("/status")
async def index_status():
    conn = get_db()
    try:
        counts = {}
        for job_type in ["index_bm25", "index_vector", "index_fts5"]:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM jobs WHERE job_type=? AND status='done'",
                (job_type,)
            ).fetchone()
            counts[job_type] = row["c"]

        pending = conn.execute(
            "SELECT COUNT(*) as c FROM jobs WHERE job_type LIKE 'index_%' AND status='pending'"
        ).fetchone()["c"]

        return {
            "index_builds": counts,
            "pending_jobs": pending,
        }
    finally:
        conn.close()


@router.post("/rebuild/{index_type}")
async def rebuild_index(index_type: str):
    valid_types = {"bm25", "vector", "fts5", "topics", "all"}
    if index_type not in valid_types:
        raise HTTPException(400, detail=f"INVALID_INDEX_TYPE: {index_type}")

    conn = get_db()
    try:
        scheduler = JobScheduler(conn)
        if index_type == "all":
            job_ids = []
            for t in ["index_bm25", "index_vector", "index_fts5"]:
                jid = scheduler.create_job(job_type=t, triggered_by="user")
                if jid:
                    job_ids.append(jid)
        else:
            jid = scheduler.create_job(job_type=f"index_{index_type}", triggered_by="user")
            job_ids = [jid] if jid else []

        return {"status": "jobs_created", "index_type": index_type, "job_ids": job_ids}
    finally:
        conn.close()


@router.post("/annotate")
async def trigger_annotation(scope: str = Query("all")):
    if scope not in ("all", "unannotated"):
        raise HTTPException(400, detail="INVALID_SCOPE")

    conn = get_db()
    try:
        scheduler = JobScheduler(conn)
        jid = scheduler.create_job(
            job_type="annotate",
            payload=f'{{"scope": "{scope}"}}',
            triggered_by="user",
        )
        return {"status": "job_created", "job_id": jid}
    finally:
        conn.close()
