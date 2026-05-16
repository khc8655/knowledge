import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.output_service import OutputService

router = APIRouter(prefix="/outputs", tags=["outputs"])

VALID_TRANSITIONS = {
    'draft': ['evidence_checked'],
    'evidence_checked': ['human_reviewed'],
    'human_reviewed': ['exported'],
    'exported': ['archived'],
}


@router.post("/{output_id}/review")
async def api_review_output(output_id: str, body: dict):
    action = body.get('action')
    if not action:
        raise HTTPException(status_code=400, detail="ACTION_REQUIRED")

    conn = get_db()
    try:
        svc = OutputService(conn)
        output = svc.get_output(output_id)
        if not output:
            raise HTTPException(status_code=404, detail="OUTPUT_NOT_FOUND")

        target_status = action.replace('mark_', '')
        current = output['status']
        allowed = VALID_TRANSITIONS.get(current, [])
        if target_status not in allowed:
            raise HTTPException(status_code=409, detail=f"INVALID_TRANSITION: {current} → {target_status}")

        svc.update_status(output_id, target_status)

        if body.get('reviewer'):
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE project_outputs SET reviewed_by=?, reviewed_at=? WHERE id=?",
                (body['reviewer'], now, output_id)
            )
            conn.commit()

        return {"status": target_status, "output_id": output_id}
    finally:
        conn.close()


@router.post("/{output_id}/feedback")
async def api_submit_feedback(output_id: str, body: dict):
    feedback_type = body.get('feedback_type')
    if not feedback_type:
        raise HTTPException(status_code=400, detail="FEEDBACK_TYPE_REQUIRED")

    conn = get_db()
    try:
        svc = OutputService(conn)
        output = svc.get_output(output_id)
        if not output:
            raise HTTPException(status_code=404, detail="OUTPUT_NOT_FOUND")

        feedback_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO project_feedback (id, project_id, output_id, feedback_type, target_path, before_text, after_text, comment, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (feedback_id, output['project_id'], output_id, feedback_type,
             body.get('target_path'), body.get('before_text'),
             body.get('after_text'), body.get('comment'),
             body.get('created_by'), now)
        )
        conn.commit()
        return {"status": "recorded", "feedback_id": feedback_id}
    finally:
        conn.close()


# Helper functions for use by tests and integration code
def review_output(output_id, body, conn=None):
    """Helper for tests — not an HTTP endpoint."""
    svc = OutputService(conn)
    output = svc.get_output(output_id)
    if not output:
        return None
    target_status = body.get('action', '').replace('mark_', '')
    svc.update_status(output_id, target_status)
    if body.get('reviewer'):
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "UPDATE project_outputs SET reviewed_by=?, reviewed_at=? WHERE id=?",
            (body['reviewer'], now, output_id)
        )
        conn.commit()
    return svc.get_output(output_id)


def submit_feedback(output_id, body, conn=None):
    """Helper for tests — not an HTTP endpoint."""
    svc = OutputService(conn)
    output = svc.get_output(output_id)
    if not output:
        return None
    feedback_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO project_feedback (id, project_id, output_id, feedback_type, target_path, before_text, after_text, comment, created_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (feedback_id, output['project_id'], output_id, body.get('feedback_type'),
         body.get('target_path'), body.get('before_text'),
         body.get('after_text'), body.get('comment'),
         body.get('created_by'), now)
    )
    conn.commit()
    return {"status": "recorded", "feedback_id": feedback_id}
