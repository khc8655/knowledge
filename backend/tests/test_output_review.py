import sys, os, tempfile, sqlite3
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_review_status_transitions():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from api.output_review import review_output, submit_feedback
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '测试方案')
        assert output['status'] == 'draft'
        review_output(output['id'], {'action': 'mark_evidence_checked'}, conn=conn)
        o = svc.get_output(output['id'])
        assert o['status'] == 'evidence_checked'
        review_output(output['id'], {'action': 'mark_human_reviewed', 'reviewer': '张三'}, conn=conn)
        o = svc.get_output(output['id'])
        assert o['status'] == 'human_reviewed'
        conn.close()

def test_submit_feedback():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from services.output_service import OutputService
        from api.output_review import submit_feedback
        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)
        svc = OutputService(conn)
        output = svc.create_output('proj-001', 'proposal', '测试方案')
        submit_feedback(output['id'], {
            'feedback_type': 'edit',
            'target_path': '第一章',
            'before_text': '旧内容',
            'after_text': '新内容',
        }, conn=conn)
        rows = conn.execute("SELECT * FROM project_feedback WHERE output_id=?", (output['id'],)).fetchall()
        assert len(rows) == 1
        assert rows[0]['feedback_type'] == 'edit'
        conn.close()
