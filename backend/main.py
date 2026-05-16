"""
知识库平台 - FastAPI 后端
"""
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
