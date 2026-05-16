import sqlite3
import tempfile
import os
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.models import init_db, get_db
from job.scheduler import JobScheduler
from job.executor import JobExecutor

@pytest.fixture
def db_conn():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        os.environ['KB_DATA_DIR'] = tmpdir
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        yield conn
        conn.close()

def test_create_job(db_conn):
    scheduler = JobScheduler(db_conn)
    job_id = scheduler.create_job(
        job_type='pipeline_word',
        target_id=1,
        payload='{"file": "test.docx"}'
    )
    assert job_id is not None
    assert job_id > 0
    row = db_conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    assert row is not None
    assert row['status'] == 'pending'
    assert row['job_type'] == 'pipeline_word'

def test_create_cascade_jobs(db_conn):
    scheduler = JobScheduler(db_conn)
    job_ids = scheduler.create_cascade_jobs(file_type='word', target_id=1)
    assert len(job_ids) == 5
    types = []
    for jid in job_ids:
        row = db_conn.execute("SELECT job_type FROM jobs WHERE id = ?", (jid,)).fetchone()
        types.append(row['job_type'])
    assert types[0] == 'pipeline_word'
    assert 'annotate' in types
    assert 'index_bm25' in types

def test_fetch_pending_job(db_conn):
    scheduler = JobScheduler(db_conn)
    scheduler.create_job(job_type='pipeline_word', target_id=1)
    job = scheduler.fetch_pending()
    assert job is not None
    assert job['status'] == 'pending'
    row = db_conn.execute("SELECT status FROM jobs WHERE id = ?", (job['id'],)).fetchone()
    assert row['status'] == 'running'

def test_idempotency(db_conn):
    scheduler = JobScheduler(db_conn)
    id1 = scheduler.create_job(job_type='pipeline_word', target_id=1, idempotency_key='pipeline_word:1:abc123')
    id2 = scheduler.create_job(job_type='pipeline_word', target_id=1, idempotency_key='pipeline_word:1:abc123')
    assert id2 is None

def test_concurrency_control(db_conn):
    scheduler = JobScheduler(db_conn)
    j1 = scheduler.create_job(job_type='pipeline_word', target_id=1)
    j2 = scheduler.create_job(job_type='pipeline_word', target_id=2)
    job = scheduler.fetch_pending()
    assert job['id'] == j1
    job2 = scheduler.fetch_pending()
    assert job2 is None
