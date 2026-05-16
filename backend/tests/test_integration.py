import tempfile
import os
import sqlite3
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_full_job_lifecycle():
    """Test: create job -> fetch -> complete -> verify."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db
        from job.scheduler import JobScheduler

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        scheduler = JobScheduler(conn)

        job_ids = scheduler.create_cascade_jobs(file_type='word', target_id=1)
        assert len(job_ids) == 5

        job = scheduler.fetch_pending()
        assert job is not None
        assert job['job_type'] == 'pipeline_word'

        scheduler.complete_job(job['id'])

        row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job['id'],)).fetchone()
        assert row['status'] == 'done'

        job2 = scheduler.fetch_pending()
        assert job2 is not None
        assert job2['job_type'] == 'annotate'

        conn.close()


def test_config_roundtrip():
    """Test: set config -> save -> reload -> verify."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from config import AppConfig

        cfg = AppConfig(config_dir=tmpdir)
        cfg.set('llm_model', 'test-model')
        cfg.set('max_section_chars', 999)
        cfg.save()

        cfg2 = AppConfig(config_dir=tmpdir)
        assert cfg2.get('llm_model') == 'test-model'
        assert cfg2.get('max_section_chars') == 999
