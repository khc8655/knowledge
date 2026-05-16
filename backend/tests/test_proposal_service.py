import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_generate_proposal_creates_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.proposal_service import ProposalService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ProposalService(conn)
        result = svc.generate(
            project_id='proj-001',
            title='测试方案',
            customer_context='公安行业客户',
            industry='公安',
            evidences=[],
        )
        assert result['output_id'] is not None
        assert result['status'] == 'draft'
        assert 'evidence_coverage' in result
        conn.close()

def test_proposal_low_coverage_flagged():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.proposal_service import ProposalService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ProposalService(conn)
        result = svc.generate(
            project_id='proj-001',
            title='测试方案',
            customer_context='客户背景',
            evidences=[],
        )
        assert any('待补证据' in r or '待确认' in r for r in result.get('risk_summary', []))
        conn.close()
