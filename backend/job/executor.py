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
