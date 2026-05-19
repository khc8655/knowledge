"""
知识库平台 - FastAPI 后端
"""
import os
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from db.models import init_db, get_db

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

DATA_DIR = os.environ.get("KB_DATA_DIR", "./data")

_stop_event = threading.Event()


def _job_runner_loop():
    """Background thread: continuously fetch and execute pending jobs."""
    from job.scheduler import JobScheduler
    from job.executor import JobExecutor, register_default_handlers

    conn = get_db()
    init_db(conn)
    conn.close()

    while not _stop_event.is_set():
        conn = get_db()
        try:
            scheduler = JobScheduler(conn)
            executor = JobExecutor(scheduler)
            register_default_handlers(executor, DATA_DIR)
            executed = executor.execute_one()
        except Exception as e:
            print(f"[JobRunner] Error: {e}")
            executed = False
        finally:
            conn.close()

        if not executed:
            _stop_event.wait(timeout=2.0)
        else:
            _stop_event.wait(timeout=0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and start job runner
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_db()
    init_db(conn)
    conn.close()

    runner_thread = threading.Thread(target=_job_runner_loop, daemon=True, name="job-runner")
    runner_thread.start()

    yield

    # Shutdown: stop job runner
    _stop_event.set()


app = FastAPI(
    title="知识库平台",
    version="8.0",
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
    from services.health import check_health
    return check_health()


# Import and register routers
from api.upload import router as upload_router
from api.query import router as query_router
from api.card import router as card_router
from api.config import router as config_router
from api.index import router as index_router
from api.feedback import router as feedback_router
from api.job import router as job_router
from api.evidence import router as evidence_router
from api.tender import router as tender_router
from api.project import router as project_router
from api.template import router as template_router
from api.reply import router as reply_router
from api.bom import router as bom_router
from api.output_review import router as review_router
from api.proposal import router as proposal_router
from api.export import router as export_router
from api.thumbnail import router as thumbnail_router
from api.chat import router as chat_router

app.include_router(upload_router, prefix="/api/v1")
app.include_router(query_router, prefix="/api/v1")
app.include_router(card_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(index_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(job_router, prefix="/api/v1")
app.include_router(evidence_router, prefix="/api/v1")
app.include_router(tender_router, prefix="/api/v1")
app.include_router(project_router, prefix="/api/v1")
app.include_router(template_router, prefix="/api/v1")
app.include_router(reply_router, prefix="/api/v1")
app.include_router(bom_router, prefix="/api/v1")
app.include_router(review_router, prefix="/api/v1")
app.include_router(proposal_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(thumbnail_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

# Serve frontend static files
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Serve static file if it exists, otherwise fallback to index.html
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
