from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from db.models import get_db
from services.export_service import ExportService
import io

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/{output_id}")
async def export_output(output_id: str, body: dict = None):
    body = body or {}
    fmt = body.get('format', 'markdown')
    if fmt not in ('markdown', 'json'):
        raise HTTPException(status_code=400, detail="FORMAT must be 'markdown' or 'json'")

    conn = get_db()
    try:
        svc = ExportService(conn)
        try:
            result = svc.export(output_id, fmt=fmt)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return result
    finally:
        conn.close()


@router.get("/{output_id}/download")
async def download_export(output_id: str, format: str = "markdown"):
    """Download exported output as a file."""
    if format not in ('markdown', 'json'):
        raise HTTPException(status_code=400, detail="FORMAT must be 'markdown' or 'json'")

    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM project_outputs WHERE id = ?", (output_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, detail="OUTPUT_NOT_FOUND")

        if format == "markdown":
            content = row["content_md"] or ""
            media_type = "text/markdown"
            ext = "md"
        else:
            content = row["content_json"] or "{}"
            media_type = "application/json"
            ext = "json"

        title = row["title"] or "export"
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)
        filename = f"{safe_title}.{ext}"

        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    finally:
        conn.close()
