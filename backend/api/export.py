from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.export_service import ExportService

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
