import os
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


def register_default_handlers(executor, data_dir: str):
    """Register all default job handlers."""
    from pipeline.word import WordPipeline
    from pipeline.markdown import MarkdownPipeline
    from pipeline.txt import TxtPipeline
    from pipeline.ppt import PptPipeline
    from pipeline.excel import ExcelPipeline
    from card.store import CardStore
    from db.models import get_db

    store = CardStore(data_dir=data_dir)

    def handle_pipeline(job, pipeline_cls):
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM uploaded_files WHERE id = ?", (job["target_id"],)
            ).fetchone()
            if not row:
                raise ValueError(f"File not found: {job['target_id']}")

            pipeline = pipeline_cls(data_dir=data_dir, doc_index=row["id"])
            cards = pipeline.parse(row["storage_path"])
            store.save_batch(cards)

            conn.execute(
                "UPDATE uploaded_files SET cards_count=?, pipeline_status='done', processed_at=datetime('now') WHERE id=?",
                (len(cards), row["id"])
            )
            conn.commit()
        finally:
            conn.close()

    executor.register("pipeline_word", lambda j: handle_pipeline(j, WordPipeline))
    executor.register("pipeline_md", lambda j: handle_pipeline(j, MarkdownPipeline))
    executor.register("pipeline_txt", lambda j: handle_pipeline(j, TxtPipeline))
    executor.register("pipeline_ppt", lambda j: handle_pipeline(j, PptPipeline))
    executor.register("pipeline_excel", lambda j: handle_pipeline(j, ExcelPipeline))

    def handle_pipeline_report(job):
        from pipeline.report import ReportPipeline
        import json, os
        pipeline = ReportPipeline()
        payload = json.loads(job.get('payload', '{}') or '{}')
        file_path = payload.get('file_path')
        doc_file = payload.get('doc_file', os.path.basename(file_path) if file_path else 'unknown')
        if not file_path:
            raise ValueError("pipeline_report requires file_path in payload")
        cards = pipeline.parse(file_path, doc_file=doc_file)
        store.save_batch(cards)
        return {'cards_generated': len(cards)}

    executor.register("pipeline_report", handle_pipeline_report)

    def handle_annotate(job):
        from services.annotate_service import annotate_batch
        annotate_batch(store)

    executor.register("annotate", handle_annotate)

    def handle_index_fts5(job):
        from index.fts5 import FTS5Index
        cards_dir = os.path.join(data_dir, "cards", "sections")
        fts5 = FTS5Index()
        count = fts5.build(cards_dir)
        print(f"[Index] FTS5 built: {count} cards")

    def handle_index_bm25(job):
        from index.bm25 import BM25Index
        cards_dir = os.path.join(data_dir, "cards", "sections")
        index_dir = os.path.join(data_dir, "indexes")
        bm25 = BM25Index()
        count = bm25.build(cards_dir, persist_path=os.path.join(index_dir, "bm25.pkl"))
        print(f"[Index] BM25 built: {count} cards")

    def handle_index_vector(job):
        from index.vector import VectorIndex
        from config import AppConfig
        cfg = AppConfig()
        cards_dir = os.path.join(data_dir, "cards", "sections")
        index_dir = os.path.join(data_dir, "indexes")
        vector = VectorIndex()
        count = vector.build(
            cards_dir,
            persist_dir=os.path.join(index_dir, "vector"),
            api_key=cfg.get("llm_api_key"),
            model=cfg.get("embedding_model", "Pro/BAAI/bge-m3"),
        )
        print(f"[Index] Vector built: {count} cards")

    executor.register("index_fts5", handle_index_fts5)
    executor.register("index_bm25", handle_index_bm25)
    executor.register("index_vector", handle_index_vector)
