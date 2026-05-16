# Infrastructure & Job System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational infrastructure layer: database initialization, v7.5 schema migration, Job scheduler with state machine, config persistence, and health checks.

**Architecture:** FastAPI app with SQLite backend. The Job system uses a polling scheduler that picks pending jobs and executes them asynchronously. All v7.5 tables (evidence_packs, presales_projects, etc.) are created at startup. Config is persisted to a YAML file.

**Tech Stack:** Python 3.11+, FastAPI, SQLite (via aiosqlite), PyYAML, pytest

---

## File Structure

```
backend/
├── main.py                    # Modify: wire init_db, scheduler, lifespan
├── config.py                  # Create: config persistence to YAML
├── db/
│   ├── __init__.py            # Create: package init
│   ├── models.py              # Modify: add v7.5 tables
│   └── migrations.py          # Create: schema migration logic
├── job/
│   ├── __init__.py            # Create: package init
│   ├── scheduler.py           # Create: polling scheduler
│   ├── executor.py            # Create: job execution dispatch
│   └── state_machine.py       # Create: job state transitions
├── api/
│   ├── __init__.py            # Create: package init
│   ├── job.py                 # Modify: real implementation
│   ├── config.py              # Modify: use config persistence
│   └── ...                    # Other API files (unchanged in this plan)
├── services/
│   ├── __init__.py            # Create: package init
│   └── health.py              # Create: health check logic
└── tests/
    ├── __init__.py            # Create
    ├── conftest.py            # Create: test fixtures
    ├── test_db_init.py        # Create
    ├── test_job_state_machine.py  # Create
    ├── test_job_scheduler.py  # Create
    ├── test_config.py         # Create
    └── test_health.py         # Create
```

---

### Task 1: Project Structure Setup

**Files:**
- Create: `backend/db/__init__.py`
- Create: `backend/api/__init__.py`
- Create: `backend/job/__init__.py`
- Create: `backend/services/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/.env.example`

- [ ] **Step 1: Create package init files**

```python
# backend/db/__init__.py
from .models import get_db, init_db
```

```python
# backend/api/__init__.py
# API routers package
```

```python
# backend/job/__init__.py
# Job system package
```

```python
# backend/services/__init__.py
# Services package
```

```python
# backend/tests/__init__.py
# Test package
```

- [ ] **Step 2: Create .env.example**

```bash
# backend/.env.example
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
KB_ADMIN_TOKEN=
KB_DATA_DIR=./data
```

- [ ] **Step 3: Verify imports work**

Run: `cd /home/jjb/kb-platform/backend && python -c "from db import get_db, init_db; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/db/__init__.py backend/api/__init__.py backend/job/__init__.py backend/services/__init__.py backend/tests/__init__.py backend/.env.example
git commit -m "feat: add package init files and .env.example"
```

---

### Task 2: Database Initialization & v7.5 Schema

**Files:**
- Modify: `backend/db/models.py`
- Create: `backend/db/migrations.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Write failing test for init_db**

```python
# backend/tests/test_db_init.py
import sqlite3
import tempfile
import os
import pytest

def test_init_db_creates_all_tables():
    """init_db should create all v7.5 tables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Import and run init
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from db.models import init_db
        init_db(conn)

        # Check all tables exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row['name'] for row in cursor.fetchall()}

        expected = {
            'uploaded_files', 'jobs', 'query_feedback',
            'route_mappings', 'route_cache',
            'evidence_packs', 'presales_projects',
            'project_requirements', 'project_outputs',
            'project_evidence_links', 'project_feedback',
            'templates',
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"
        conn.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_db_init.py -v`
Expected: FAIL (tables missing)

- [ ] **Step 3: Add v7.5 tables to models.py**

Add the following DDL to the `init_db()` function in `backend/db/models.py`:

```python
# Add after existing CREATE TABLE statements in init_db()

conn.execute("""
CREATE TABLE IF NOT EXISTS evidence_packs (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    source_card_id TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('excel','word','markdown','txt','ppt','report')),
    evidence_type TEXT NOT NULL,
    claim TEXT NOT NULL,
    body TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0,
    freshness TEXT NOT NULL DEFAULT 'unknown' CHECK(freshness IN ('current','expired','history','unknown')),
    risk_flags TEXT NOT NULL DEFAULT '[]',
    created_by_task_id TEXT,
    created_at TEXT NOT NULL,
    archived_at TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS presales_projects (
    id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    industry TEXT,
    stage TEXT NOT NULL DEFAULT 'draft',
    deployment_type TEXT,
    description TEXT,
    owner TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS project_requirements (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    requirement_type TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    structured_json TEXT NOT NULL DEFAULT '{}',
    source_file_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES presales_projects(id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS project_outputs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    output_type TEXT NOT NULL CHECK(output_type IN ('proposal','tender','bom','reply')),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','evidence_checked','human_reviewed','exported','archived')),
    content_md TEXT,
    content_json TEXT NOT NULL DEFAULT '{}',
    export_path TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT,
    FOREIGN KEY(project_id) REFERENCES presales_projects(id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS project_evidence_links (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    output_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    target_path TEXT NOT NULL,
    link_role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES presales_projects(id),
    FOREIGN KEY(output_id) REFERENCES project_outputs(id),
    FOREIGN KEY(evidence_id) REFERENCES evidence_packs(id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS project_feedback (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    output_id TEXT,
    feedback_type TEXT NOT NULL CHECK(feedback_type IN ('accept','edit','reject','comment')),
    target_path TEXT,
    before_text TEXT,
    after_text TEXT,
    comment TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    template_type TEXT NOT NULL CHECK(template_type IN ('proposal','tender','reply','ppt')),
    name TEXT NOT NULL,
    industry TEXT,
    deployment_type TEXT,
    file_path TEXT NOT NULL,
    schema_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
""")

# Add indexes for new tables
conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_project ON evidence_packs(project_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_card ON evidence_packs(source_card_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence_packs(evidence_type)")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_db_init.py -v`
Expected: PASS

- [ ] **Step 5: Wire init_db to FastAPI startup**

Modify `backend/main.py` to call `init_db` on startup:

```python
# backend/main.py - replace the existing content
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.models import init_db, get_db

DATA_DIR = os.environ.get("KB_DATA_DIR", "./data")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_db()
    init_db(conn)
    conn.close()
    yield
    # Shutdown: cleanup

app = FastAPI(
    title="知识库平台",
    version="7.5",
    description="上传文档 → 自动入库 → 随时查询 → 结果带原文出处",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "version": "7.5"}

# Import and register routers
from api.upload import router as upload_router
from api.query import router as query_router
from api.card import router as card_router
from api.config import router as config_router
from api.index import router as index_router
from api.feedback import router as feedback_router
from api.job import router as job_router

app.include_router(upload_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(card_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(index_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(job_router, prefix="/api/v1")
```

- [ ] **Step 6: Verify app starts**

Run: `cd /home/jjb/kb-platform/backend && timeout 5 python -c "from main import app; print('App created:', app.title)"` or `uvicorn main:app --host 0.0.0.0 --port 8920` (ctrl+C after startup)
Expected: App starts without errors, database file created

- [ ] **Step 7: Commit**

```bash
git add backend/db/models.py backend/main.py backend/tests/test_db_init.py
git commit -m "feat: add v7.5 database schema and wire init_db to startup"
```

---

### Task 3: Job State Machine

**Files:**
- Create: `backend/job/state_machine.py`
- Create: `backend/tests/test_job_state_machine.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_job_state_machine.py
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from job.state_machine import JobStateMachine, InvalidTransition

def test_valid_transitions():
    sm = JobStateMachine()
    # pending -> running
    assert sm.can_transition('pending', 'running') is True
    # running -> done
    assert sm.can_transition('running', 'done') is True
    # running -> failed
    assert sm.can_transition('running', 'failed') is True
    # running -> cancelled
    assert sm.can_transition('running', 'cancelled') is True
    # failed -> pending (retry)
    assert sm.can_transition('failed', 'pending') is True

def test_invalid_transitions():
    sm = JobStateMachine()
    # done -> anything
    assert sm.can_transition('done', 'running') is False
    assert sm.can_transition('done', 'pending') is False
    # cancelled -> anything
    assert sm.can_transition('cancelled', 'running') is False
    # pending -> done (must go through running)
    assert sm.can_transition('pending', 'done') is False

def test_transition_updates_status():
    sm = JobStateMachine()
    new_status = sm.transition('pending', 'running')
    assert new_status == 'running'

def test_invalid_transition_raises():
    sm = JobStateMachine()
    with pytest.raises(InvalidTransition):
        sm.transition('done', 'running')

def test_retry_limit():
    sm = JobStateMachine(max_retries=3)
    assert sm.can_retry(retry_count=2) is True
    assert sm.can_retry(retry_count=3) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_job_state_machine.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement state machine**

```python
# backend/job/state_machine.py

class InvalidTransition(Exception):
    pass

class JobStateMachine:
    VALID_TRANSITIONS = {
        'pending': {'running'},
        'running': {'done', 'failed', 'cancelled'},
        'failed': {'pending'},  # retry
        'done': set(),          # terminal
        'cancelled': set(),     # terminal
    }

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def can_transition(self, from_status: str, to_status: str) -> bool:
        allowed = self.VALID_TRANSITIONS.get(from_status, set())
        return to_status in allowed

    def transition(self, from_status: str, to_status: str) -> str:
        if not self.can_transition(from_status, to_status):
            raise InvalidTransition(
                f"Cannot transition from '{from_status}' to '{to_status}'"
            )
        return to_status

    def can_retry(self, retry_count: int) -> bool:
        return retry_count < self.max_retries
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_job_state_machine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/job/state_machine.py backend/tests/test_job_state_machine.py
git commit -m "feat: add job state machine with transition validation"
```

---

### Task 4: Job Scheduler & Executor

**Files:**
- Create: `backend/job/scheduler.py`
- Create: `backend/job/executor.py`
- Create: `backend/tests/test_job_scheduler.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_job_scheduler.py
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

    # Verify job exists
    row = db_conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    assert row is not None
    assert row['status'] == 'pending'
    assert row['job_type'] == 'pipeline_word'

def test_create_cascade_jobs(db_conn):
    scheduler = JobScheduler(db_conn)
    job_ids = scheduler.create_cascade_jobs(
        file_type='word',
        target_id=1,
    )
    # Should create: pipeline -> annotate -> index_bm25 -> index_vector -> index_fts5
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

    # After fetch, status should be running
    row = db_conn.execute("SELECT status FROM jobs WHERE id = ?", (job['id'],)).fetchone()
    assert row['status'] == 'running'

def test_idempotency(db_conn):
    scheduler = JobScheduler(db_conn)
    id1 = scheduler.create_job(
        job_type='pipeline_word',
        target_id=1,
        idempotency_key='pipeline_word:1:abc123'
    )
    id2 = scheduler.create_job(
        job_type='pipeline_word',
        target_id=1,
        idempotency_key='pipeline_word:1:abc123'
    )
    # Second call should return None (duplicate)
    assert id2 is None

def test_concurrency_control(db_conn):
    scheduler = JobScheduler(db_conn)
    # Create two jobs of same type
    j1 = scheduler.create_job(job_type='pipeline_word', target_id=1)
    j2 = scheduler.create_job(job_type='pipeline_word', target_id=2)

    # Fetch first -> running
    job = scheduler.fetch_pending()
    assert job['id'] == j1

    # Fetch second should be None (same type already running)
    job2 = scheduler.fetch_pending()
    assert job2 is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_job_scheduler.py -v`
Expected: FAIL

- [ ] **Step 3: Implement JobScheduler**

```python
# backend/job/scheduler.py
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict

from .state_machine import JobStateMachine


class JobScheduler:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.sm = JobStateMachine()

    def create_job(
        self,
        job_type: str,
        target_id: int = None,
        payload: str = None,
        idempotency_key: str = None,
        parent_job_id: int = None,
        triggered_by: str = 'user',
    ) -> Optional[int]:
        """Create a new job. Returns job_id or None if idempotent duplicate."""
        now = datetime.now(timezone.utc).isoformat()

        # Check idempotency
        if idempotency_key:
            existing = self.conn.execute(
                "SELECT id FROM jobs WHERE idempotency_key = ? AND status IN ('pending', 'running')",
                (idempotency_key,)
            ).fetchone()
            if existing:
                return None

        cursor = self.conn.execute(
            """INSERT INTO jobs (job_type, status, target_id, payload, idempotency_key,
               parent_job_id, triggered_by, created_at)
               VALUES (?, 'pending', ?, ?, ?, ?, ?, ?)""",
            (job_type, target_id, payload, idempotency_key,
             parent_job_id, triggered_by, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def create_cascade_jobs(
        self,
        file_type: str,
        target_id: int,
        triggered_by: str = 'user',
    ) -> List[int]:
        """Create pipeline -> annotate -> index jobs in cascade."""
        job_ids = []

        # 1. Pipeline job
        pipeline_type = f'pipeline_{file_type}'
        pipeline_id = self.create_job(
            job_type=pipeline_type,
            target_id=target_id,
            idempotency_key=f'{pipeline_type}:{target_id}',
            triggered_by=triggered_by,
        )
        job_ids.append(pipeline_id)

        # 2. Annotate job (child of pipeline)
        annotate_id = self.create_job(
            job_type='annotate',
            target_id=target_id,
            parent_job_id=pipeline_id,
            triggered_by='system',
        )
        job_ids.append(annotate_id)

        # 3. Index jobs (children of pipeline)
        for idx_type in ['index_bm25', 'index_vector', 'index_fts5']:
            idx_id = self.create_job(
                job_type=idx_type,
                target_id=target_id,
                parent_job_id=pipeline_id,
                triggered_by='system',
            )
            job_ids.append(idx_id)

        return job_ids

    def fetch_pending(self) -> Optional[Dict]:
        """Fetch and lock a pending job. Returns None if no jobs available."""
        # Find pending jobs, excluding types that are already running
        running_types = self.conn.execute(
            "SELECT DISTINCT job_type FROM jobs WHERE status = 'running'"
        ).fetchall()
        running_type_set = {row['job_type'] for row in running_types}

        # Get pending jobs
        pending = self.conn.execute(
            """SELECT * FROM jobs WHERE status = 'pending'
               ORDER BY created_at ASC LIMIT 10"""
        ).fetchall()

        for job in pending:
            if job['job_type'] not in running_type_set:
                # Lock this job
                now = datetime.now(timezone.utc).isoformat()
                self.conn.execute(
                    "UPDATE jobs SET status = 'running', started_at = ? WHERE id = ?",
                    (now, job['id'])
                )
                self.conn.commit()
                return dict(job)

        return None

    def complete_job(self, job_id: int):
        """Mark job as done."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE jobs SET status = 'done', completed_at = ?, progress_pct = 100 WHERE id = ?",
            (now, job_id)
        )
        self.conn.commit()

    def fail_job(self, job_id: int, error: str):
        """Mark job as failed, increment retry_count."""
        row = self.conn.execute(
            "SELECT retry_count, max_retries FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if row and self.sm.can_retry(row['retry_count']):
            # Retry: set back to pending
            self.conn.execute(
                """UPDATE jobs SET status = 'pending', retry_count = retry_count + 1,
                   last_error = ?, started_at = NULL WHERE id = ?""",
                (error[:500], job_id)
            )
        else:
            # Max retries reached
            now = datetime.now(timezone.utc).isoformat()
            self.conn.execute(
                """UPDATE jobs SET status = 'failed', last_error = ?,
                   completed_at = ? WHERE id = ?""",
                (error[:500], now, job_id)
            )
        self.conn.commit()

    def cancel_job(self, job_id: int) -> bool:
        """Cancel a pending or running job."""
        row = self.conn.execute(
            "SELECT status FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
        if not row or not self.sm.can_transition(row['status'], 'cancelled'):
            return False

        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE jobs SET status = 'cancelled', completed_at = ? WHERE id = ?",
            (now, job_id)
        )
        self.conn.commit()
        return True

    def update_progress(self, job_id: int, pct: int, detail: str = None):
        """Update job progress."""
        self.conn.execute(
            "UPDATE jobs SET progress_pct = ?, progress_detail = ? WHERE id = ?",
            (pct, detail, job_id)
        )
        self.conn.commit()
```

- [ ] **Step 4: Implement JobExecutor**

```python
# backend/job/executor.py
import traceback
from typing import Dict, Callable

from .scheduler import JobScheduler


class JobExecutor:
    """Dispatches job execution based on job_type."""

    def __init__(self, scheduler: JobScheduler):
        self.scheduler = scheduler
        self._handlers: Dict[str, Callable] = {}

    def register(self, job_type: str, handler: Callable):
        """Register a handler for a job type."""
        self._handlers[job_type] = handler

    def execute_one(self) -> bool:
        """Fetch and execute one pending job. Returns True if a job was executed."""
        job = self.scheduler.fetch_pending()
        if not job:
            return False

        job_id = job['id']
        job_type = job['job_type']

        try:
            handler = self._handlers.get(job_type)
            if not handler:
                raise ValueError(f"No handler registered for job type: {job_type}")

            handler(job)
            self.scheduler.complete_job(job_id)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self.scheduler.fail_job(job_id, error_msg)

        return True
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_job_scheduler.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/job/scheduler.py backend/job/executor.py backend/tests/test_job_scheduler.py
git commit -m "feat: implement job scheduler with cascade jobs and concurrency control"
```

---

### Task 5: Config Persistence

**Files:**
- Create: `backend/config.py`
- Modify: `backend/api/config.py`
- Create: `backend/tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_config.py
import tempfile
import os
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import AppConfig

def test_load_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = AppConfig(config_dir=tmpdir)
        assert cfg.get('llm_model') == 'Qwen/Qwen2.5-7B-Instruct'
        assert cfg.get('max_section_chars') == 1200
        assert cfg.get('route_learning_enabled') is True

def test_save_and_reload():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = AppConfig(config_dir=tmpdir)
        cfg.set('llm_model', 'custom-model')
        cfg.set('max_section_chars', 2000)
        cfg.save()

        # Reload from file
        cfg2 = AppConfig(config_dir=tmpdir)
        assert cfg2.get('llm_model') == 'custom-model'
        assert cfg2.get('max_section_chars') == 2000

def test_env_override():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['LLM_MODEL'] = 'env-model'
        cfg = AppConfig(config_dir=tmpdir)
        assert cfg.get('llm_model') == 'env-model'
        del os.environ['LLM_MODEL']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_config.py -v`
Expected: FAIL

- [ ] **Step 3: Implement AppConfig**

```python
# backend/config.py
import os
import yaml
from pathlib import Path
from typing import Any, Optional

DEFAULTS = {
    'llm_api_key': '',
    'llm_base_url': 'https://api.siliconflow.cn/v1',
    'llm_model': 'Qwen/Qwen2.5-7B-Instruct',
    'embedding_model': 'BAAI/bge-large-zh-v1.5',
    'max_section_chars': 1200,
    'max_file_size_mb': 50,
    'max_files_per_upload': 20,
    'route_learning_enabled': True,
    'cache_evict_days': 7,
    'cache_max_entries': 5000,
    'coarse_doc_detection': True,
}

ENV_MAP = {
    'LLM_API_KEY': 'llm_api_key',
    'LLM_BASE_URL': 'llm_base_url',
    'LLM_MODEL': 'llm_model',
    'EMBEDDING_MODEL': 'embedding_model',
    'KB_DATA_DIR': 'data_dir',
}


class AppConfig:
    def __init__(self, config_dir: str = None):
        self._data = dict(DEFAULTS)
        self._config_dir = config_dir or os.environ.get('KB_DATA_DIR', './data')
        self._config_path = os.path.join(self._config_dir, 'config.yaml')
        self._load()

    def _load(self):
        # 1. Load from file if exists
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r') as f:
                    file_data = yaml.safe_load(f) or {}
                self._data.update(file_data)
            except Exception:
                pass

        # 2. Environment variables override
        for env_key, cfg_key in ENV_MAP.items():
            env_val = os.environ.get(env_key)
            if env_val:
                # Type coercion for known int fields
                if cfg_key in ('max_section_chars', 'max_file_size_mb',
                               'max_files_per_upload', 'cache_evict_days',
                               'cache_max_entries'):
                    try:
                        env_val = int(env_val)
                    except ValueError:
                        pass
                self._data[cfg_key] = env_val

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def save(self):
        os.makedirs(self._config_dir, exist_ok=True)
        with open(self._config_path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> dict:
        return dict(self._data)
```

- [ ] **Step 4: Update api/config.py to use AppConfig**

```python
# backend/api/config.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from config import AppConfig

router = APIRouter(prefix="/config", tags=["config"])

class SystemConfig(BaseModel):
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    max_section_chars: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    route_learning_enabled: Optional[bool] = None
    cache_evict_days: Optional[int] = None
    cache_max_entries: Optional[int] = None

@router.get("")
async def get_config():
    cfg = AppConfig()
    data = cfg.to_dict()
    # Mask API key
    if data.get('llm_api_key'):
        data['llm_api_key'] = data['llm_api_key'][:8] + '...'
    return data

@router.put("")
async def update_config(config: SystemConfig):
    cfg = AppConfig()
    update_data = config.model_dump(exclude_none=True)
    for key, value in update_data.items():
        cfg.set(key, value)
    cfg.save()
    return {"status": "updated", "config": cfg.to_dict()}

@router.get("/excel-card")
async def get_excel_card_config():
    cfg = AppConfig()
    return cfg.get('excel_card_config', {})

@router.put("/excel-card")
async def update_excel_card_config(config: dict):
    cfg = AppConfig()
    cfg.set('excel_card_config', config)
    cfg.save()
    return {"status": "updated"}

@router.post("/excel-card/profile/{file_id}")
async def profile_excel(file_id: int):
    # TODO: Trigger Excel profiling job
    return {"status": "job_created", "file_id": file_id}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/config.py backend/api/config.py backend/tests/test_config.py
git commit -m "feat: implement config persistence with YAML file and env overrides"
```

---

### Task 6: Real Job API Implementation

**Files:**
- Modify: `backend/api/job.py`

- [ ] **Step 1: Implement real job API**

```python
# backend/api/job.py
from fastapi import APIRouter, HTTPException, Query
from db.models import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("")
async def list_jobs(
    status: str = Query(None),
    type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    conn = get_db()
    try:
        conditions = []
        params = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if type:
            conditions.append("job_type = ?")
            params.append(type)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * page_size

        total = conn.execute(f"SELECT COUNT(*) as cnt FROM jobs{where}", params).fetchone()['cnt']
        rows = conn.execute(
            f"SELECT * FROM jobs{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset]
        ).fetchall()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [dict(r) for r in rows],
        }
    finally:
        conn.close()

@router.get("/{job_id}")
async def get_job(job_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
        return dict(row)
    finally:
        conn.close()

@router.post("/{job_id}/retry")
async def retry_job(job_id: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
        if row['status'] not in ('failed',):
            raise HTTPException(status_code=409, detail="JOB_NOT_RETRYABLE")

        conn.execute(
            "UPDATE jobs SET status = 'pending', retry_count = retry_count + 1, started_at = NULL WHERE id = ?",
            (job_id,)
        )
        conn.commit()
        return {"status": "retried", "job_id": job_id}
    finally:
        conn.close()

@router.delete("/{job_id}")
async def delete_job(job_id: int, force: bool = Query(False)):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="JOB_NOT_FOUND")
        if row['status'] not in ('pending', 'failed', 'cancelled') and not force:
            raise HTTPException(status_code=409, detail="JOB_ALREADY_RUNNING")

        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        return {"status": "deleted", "job_id": job_id}
    finally:
        conn.close()
```

- [ ] **Step 2: Test the API manually**

Run: Start the server and test:
```bash
cd /home/jjb/kb-platform/backend
uvicorn main:app --port 8920 &
sleep 2
curl http://localhost:8920/api/v1/jobs
curl http://localhost:8920/api/v1/health
kill %1
```
Expected: JSON responses

- [ ] **Step 3: Commit**

```bash
git add backend/api/job.py
git commit -m "feat: implement real job API with list, get, retry, delete"
```

---

### Task 7: Health Check Service

**Files:**
- Create: `backend/services/health.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Implement health check service**

```python
# backend/services/health.py
import os
import time
from db.models import get_db

def check_health() -> dict:
    """Comprehensive health check."""
    checks = {}
    start = time.time()

    # Database check
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'

    # Job counts
    try:
        conn = get_db()
        pending = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='pending'").fetchone()['c']
        running = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='running'").fetchone()['c']
        failed = conn.execute("SELECT COUNT(*) as c FROM jobs WHERE status='failed'").fetchone()['c']
        conn.close()
        checks['jobs_pending'] = pending
        checks['jobs_running'] = running
        checks['jobs_failed'] = failed
    except Exception:
        pass

    # Card count
    try:
        data_dir = os.environ.get('KB_DATA_DIR', './data')
        cards_dir = os.path.join(data_dir, 'cards', 'sections')
        if os.path.isdir(cards_dir):
            count = len([f for f in os.listdir(cards_dir) if f.endswith('.json')])
            checks['cards_count'] = count
    except Exception:
        pass

    elapsed = int((time.time() - start) * 1000)

    return {
        'status': 'healthy',
        'version': '7.5',
        'checks': checks,
        'latency_ms': elapsed,
    }
```

- [ ] **Step 2: Update health endpoint in main.py**

```python
# In backend/main.py, replace the health endpoint:
from services.health import check_health

@app.get("/api/v1/health")
async def health():
    return check_health()
```

- [ ] **Step 3: Test health endpoint**

Run: Start server and `curl http://localhost:8920/api/v1/health`
Expected: JSON with status, version, checks

- [ ] **Step 4: Commit**

```bash
git add backend/services/health.py backend/main.py
git commit -m "feat: implement comprehensive health check service"
```

---

### Task 8: Integration Test

**Files:**
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/test_integration.py
import tempfile
import os
import sqlite3
import pytest
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_full_job_lifecycle():
    """Test: create job -> fetch -> complete -> verify."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['KB_DATA_DIR'] = tmpdir
        from db.models import init_db, get_db
        from job.scheduler import JobScheduler

        conn = sqlite3.connect(os.path.join(tmpdir, "test.db"))
        conn.row_factory = sqlite3.Row
        init_db(conn)

        scheduler = JobScheduler(conn)

        # Create cascade jobs
        job_ids = scheduler.create_cascade_jobs(file_type='word', target_id=1)
        assert len(job_ids) == 5

        # Fetch and complete first job
        job = scheduler.fetch_pending()
        assert job is not None
        assert job['job_type'] == 'pipeline_word'

        scheduler.complete_job(job['id'])

        # Verify job is done
        row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job['id'],)).fetchone()
        assert row['status'] == 'done'

        # Fetch next job
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
```

- [ ] **Step 2: Run all tests**

Run: `cd /home/jjb/kb-platform/backend && python -m pytest tests/ -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add integration tests for job lifecycle and config"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `uvicorn main:app --port 8920` starts without errors
- [ ] `curl localhost:8920/api/v1/health` returns healthy status with version 7.5
- [ ] `curl localhost:8920/api/v1/jobs` returns empty list
- [ ] `curl localhost:8920/api/v1/config` returns config with defaults
- [ ] `python -m pytest tests/ -v` all pass
- [ ] Database file created with all v7.5 tables
- [ ] Job state machine prevents invalid transitions
- [ ] Config persists to YAML file and reloads correctly
