import os
from fastapi import APIRouter, HTTPException
from db.models import get_db
from services.proposal_service import ProposalService
from evidence.pack import EvidencePackBuilder
from card.store import CardStore

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("/generate")
async def generate_proposal(body: dict):
    project_id = body.get('project_id')
    title = body.get('title')
    if not project_id or not title:
        raise HTTPException(status_code=400, detail="PROJECT_ID_AND_TITLE_REQUIRED")

    conn = get_db()
    try:
        evidences = []
        required_models = body.get('required_models', [])
        if required_models:
            data_dir = os.environ.get('KB_DATA_DIR', './data')
            store = CardStore(data_dir=data_dir)
            all_cards = store.list_cards(page_size=500).get('items', [])
            matching = [c for c in all_cards if any(m in c.get('body', '') for m in required_models)]
            builder = EvidencePackBuilder()
            evidences = builder.build(matching, task_type='proposal', project_id=project_id)

        svc = ProposalService(conn)
        result = svc.generate(
            project_id=project_id,
            title=title,
            customer_context=body.get('customer_context', ''),
            industry=body.get('industry'),
            deployment_type=body.get('deployment_type'),
            outline=body.get('outline'),
            template_id=body.get('template_id'),
            required_models=required_models,
            forbidden_models=body.get('forbidden_models', []),
            output_format=body.get('output_format', 'markdown'),
            evidences=evidences,
        )
        return result
    finally:
        conn.close()


@router.post("/{output_id}/regenerate-section")
async def regenerate_section(output_id: str, body: dict):
    conn = get_db()
    try:
        svc = ProposalService(conn)
        result = svc.regenerate_section(output_id, body.get('chapter_title', ''), body.get('evidences'))
        if not result:
            raise HTTPException(status_code=404, detail="OUTPUT_NOT_FOUND")
        return result
    finally:
        conn.close()
