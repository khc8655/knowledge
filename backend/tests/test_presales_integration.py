import sys, os, tempfile, sqlite3
from unittest.mock import MagicMock

# Mock fastapi and pydantic before importing anything that depends on them
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if 'fastapi' not in sys.modules:
    sys.modules['fastapi'] = MagicMock()
    sys.modules['pydantic'] = MagicMock()

def test_full_presales_workflow():
    """End-to-end: create project -> generate proposal -> review -> generate BOM -> reply."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from api.project import create_project
        from services.proposal_service import ProposalService
        from services.bom_service import BomService
        from services.reply_service import ReplyService
        from services.output_service import OutputService
        from api.output_review import review_output

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # 1. Create project
        proj = create_project({'customer_name': '测试客户', 'industry': '公安'}, conn=conn)
        assert proj['id'] is not None

        # 2. Generate proposal
        proposal_svc = ProposalService(conn)
        proposal = proposal_svc.generate(
            project_id=proj['id'],
            title='公安视频方案',
            customer_context='公安行业',
            evidences=[],
        )
        assert proposal['output_id'] is not None
        assert len(proposal['risk_summary']) > 0  # No evidence = risk

        # 3. Review proposal
        review_output(proposal['output_id'], {'action': 'mark_evidence_checked'}, conn=conn)
        output_svc = OutputService(conn)
        o = output_svc.get_output(proposal['output_id'])
        assert o['status'] == 'evidence_checked'

        # 4. Generate BOM
        bom_svc = BomService(conn)
        bom = bom_svc.generate(
            project_id=proj['id'],
            scenario='视频会议',
            room_count=1,
            deployment_type='cloud',
            required_models=[],
            budget_limit=0,
            evidences=[{
                'id': 'ev-001',
                'evidence_type': 'price',
                'claim': 'AE800',
                'title': 'AE800',
                'body': 'AE800 价格:138000',
                'source': '报价.xlsx:Sheet1:5',
                'confidence': 0.95,
                'risk_flags': [],
            }],
        )
        assert bom['output_id'] is not None
        assert len(bom['lines']) >= 1

        # 5. Generate reply
        reply_svc = ReplyService(conn)
        reply = reply_svc.generate(
            customer_question='AE800支持4K吗？',
            evidences=[{
                'id': 'ev-002',
                'evidence_type': 'parameter',
                'claim': '4K支持',
                'body': 'AE800支持4K超高清',
                'source': '白皮书.docx',
                'confidence': 0.9,
                'risk_flags': [],
            }],
            project_id=proj['id'],
        )
        assert reply['output_id'] is not None
        assert '4K' in reply['reply_text']

        # 6. Verify all outputs linked to project
        outputs = output_svc.list_outputs(proj['id'])
        assert len(outputs) == 3  # proposal + bom + reply

        conn.close()
        print("ALL INTEGRATION TESTS PASSED")


if __name__ == '__main__':
    test_full_presales_workflow()
