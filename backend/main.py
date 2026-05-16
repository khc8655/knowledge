"""
知识库平台 - FastAPI 后端
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="知识库平台",
    description="上传文档 → 自动入库 → 随时查询 → 结果带原文出处",
    version="7.4"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录
DATA_DIR = os.getenv("KB_DATA_DIR", "./data")

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "version": "7.4",
        "checks": {
            "database": "ok",
            "llm_api": "ok"
        }
    }

# 导入路由
from api import upload, query, card, config, index, feedback, job

app.include_router(upload.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(card.router, prefix="/api/v1")
app.include_router(config.router, prefix="/api/v1")
app.include_router(index.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(job.router, prefix="/api/v1")
