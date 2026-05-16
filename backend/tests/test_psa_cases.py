import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_psa01_proposal_chapter_coverage():
    """PSA01: 方案生成每章证据覆盖率检查 — 无证据章节标待确认"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.proposal_service import ProposalService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ProposalService(conn)
        result = svc.generate(project_id='p1', title='方案', evidences=[])
        for ch in result.get('risk_summary', []):
            assert '待补' in ch or '待确认' in ch
        assert len(result['risk_summary']) > 0
        conn.close()

def test_psa07_reply_strips_internal_notes():
    """PSA07: 客户答复存在内部备注 — 不输出给客户"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.reply_service import ReplyService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = ReplyService(conn)
        reply = svc.generate(
            customer_question='产品参数？',
            evidences=[{
                'id': 'ev-1',
                'claim': '支持4K',
                'body': '支持4K [内部备注:仅限特定型号]',
                'confidence': 0.9,
                'risk_flags': '[]',
            }],
        )
        assert '内部备注' not in reply['reply_text']
        assert '4K' in reply['reply_text']
        conn.close()

def test_psa08_export_with_evidence_index():
    """PSA08: 导出包含证据索引和版本号"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from services.export_service import ExportService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '公安方案',
            content_md='# 公安方案\n## 架构\n内容')
        exp = ExportService(conn, data_dir=tmpdir)
        result = exp.export(output['id'])
        assert result['version'] == 1
        with open(result['export_path'], 'r') as f:
            content = f.read()
        assert '证据索引' in content
        assert 'v1' in content
        conn.close()
