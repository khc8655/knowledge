import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from db.models import get_db
from job.scheduler import JobScheduler
from config import AppConfig

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {".docx", ".xlsx", ".txt", ".md", ".pptx"}
FILE_TYPE_MAP = {
    ".docx": "word",
    ".xlsx": "excel",
    ".txt": "txt",
    ".md": "markdown",
    ".pptx": "ppt",
}
MAX_FILE_SIZE = 50 * 1024 * 1024


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    force_overwrite: bool = False,
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail=f"INVALID_FILE_TYPE: {ext}")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(400, detail="空文件")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, detail="FILE_TOO_LARGE")

    sha256 = hashlib.sha256(content).hexdigest()
    cfg = AppConfig()
    data_dir = cfg.get("data_dir", os.environ.get("KB_DATA_DIR", "./data"))
    upload_dir = os.path.join(data_dir, "uploads")

    today = datetime.now().strftime("%Y-%m-%d")
    stored_name = f"{sha256[:8]}_{file.filename}"
    storage_path = os.path.join(upload_dir, today, stored_name)
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)

    with open(storage_path, "wb") as f:
        f.write(content)

    file_type = FILE_TYPE_MAP[ext]
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM uploaded_files WHERE sha256 = ?", (sha256,)
        ).fetchone()

        if existing and not force_overwrite:
            raise HTTPException(409, detail="DUPLICATE_FILE")

        cursor = conn.execute(
            """INSERT INTO uploaded_files
               (original_name, stored_name, file_type, size_bytes, sha256, storage_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file.filename, stored_name, file_type, len(content), sha256, storage_path)
        )
        conn.commit()
        file_id = cursor.lastrowid

        scheduler = JobScheduler(conn)
        job_ids = scheduler.create_cascade_jobs(file_type=file_type, target_id=file_id)

        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "sha256": sha256,
            "size_bytes": len(content),
            "jobs_created": len(job_ids),
        }
    finally:
        conn.close()


@router.get("/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    file_type: str = Query(None),
    is_current: Optional[bool] = Query(None),
):
    conn = get_db()
    try:
        conditions = []
        params = []
        if file_type:
            conditions.append("file_type = ?")
            params.append(file_type)
        if is_current is not None:
            conditions.append("is_current = ?")
            params.append(1 if is_current else 0)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * page_size

        total = conn.execute(f"SELECT COUNT(*) as cnt FROM uploaded_files{where}", params).fetchone()['cnt']
        rows = conn.execute(
            f"SELECT * FROM uploaded_files{where} ORDER BY uploaded_at DESC LIMIT ? OFFSET ?",
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


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM uploaded_files WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="DOCUMENT_NOT_FOUND")
        conn.execute("DELETE FROM uploaded_files WHERE id = ?", (doc_id,))
        conn.commit()
        return {"status": "deleted", "id": doc_id}
    finally:
        conn.close()


@router.post("/documents/{doc_id}/reprocess")
async def reprocess_document(doc_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM uploaded_files WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            raise HTTPException(404, detail="DOCUMENT_NOT_FOUND")

        scheduler = JobScheduler(conn)
        job_ids = scheduler.create_cascade_jobs(
            file_type=row['file_type'],
            target_id=doc_id,
        )
        return {"status": "job_created", "document_id": doc_id, "jobs_created": len(job_ids)}
    finally:
        conn.close()
