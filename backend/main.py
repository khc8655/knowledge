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
