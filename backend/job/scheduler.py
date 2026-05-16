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

        pipeline_type = f'pipeline_{file_type}'
        pipeline_id = self.create_job(
            job_type=pipeline_type,
            target_id=target_id,
            idempotency_key=f'{pipeline_type}:{target_id}',
            triggered_by=triggered_by,
        )
        job_ids.append(pipeline_id)

        annotate_id = self.create_job(
            job_type='annotate',
            target_id=target_id,
            parent_job_id=pipeline_id,
            triggered_by='system',
        )
        job_ids.append(annotate_id)

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
        running_types = self.conn.execute(
            "SELECT DISTINCT job_type FROM jobs WHERE status = 'running'"
        ).fetchall()
        running_type_set = {row['job_type'] for row in running_types}

        pending = self.conn.execute(
            """SELECT * FROM jobs WHERE status = 'pending'
               ORDER BY created_at ASC LIMIT 10"""
        ).fetchall()

        for job in pending:
            if job['job_type'] not in running_type_set:
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
            self.conn.execute(
                """UPDATE jobs SET status = 'pending', retry_count = retry_count + 1,
                   last_error = ?, started_at = NULL WHERE id = ?""",
                (error[:500], job_id)
            )
        else:
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
