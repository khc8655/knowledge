import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_export_proposal_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from services.export_service import ExportService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '测试方案',
            content_md='# 测试方案\n## 第一章\n内容',
            content_json={'chapters': [{'title': '第一章', 'evidence_ids': ['ev-001']}]})
        exp = ExportService(conn, data_dir=tmpdir)
        result = exp.export(output['id'], fmt='markdown')
        assert result['export_path'] is not None
        assert result['version'] == 1
        assert os.path.exists(result['export_path'])
        with open(result['export_path'], 'r') as f:
            content = f.read()
        assert '证据索引' in content
        conn.close()

def test_export_version_increment():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from services.export_service import ExportService
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'bom', 'BOM清单',
            content_md='# BOM\n产品列表')
        exp = ExportService(conn, data_dir=tmpdir)
        r1 = exp.export(output['id'], fmt='markdown')
        assert r1['version'] == 1
        r2 = exp.export(output['id'], fmt='markdown')
        assert r2['version'] == 2
        conn.close()
