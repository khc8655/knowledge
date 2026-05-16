"""
配置 API
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["config"])

class SystemConfig(BaseModel):
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_model: Optional[str] = None
    max_section_chars: int = 1200
    route_learning_enabled: bool = True

@router.get("/config")
async def get_config():
    """获取系统配置"""
    import os
    return {
        "llm_model": os.getenv("LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "embedding_model": os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5"),
        "max_section_chars": 1200,
        "route_learning_enabled": True
    }

@router.put("/config")
async def update_config(config: SystemConfig):
    """更新系统配置"""
    # TODO: 保存到数据库或环境变量
    return {"status": "updated"}

@router.get("/config/excel-card")
async def get_excel_card_config():
    """获取 Excel 卡片配置"""
    # TODO: 读取 excel_card_config.yaml
    return {"config": {}}

@router.put("/config/excel-card")
async def update_excel_card_config(config: dict):
    """更新 Excel 卡片配置"""
    # TODO: 保存到 yaml
    return {"status": "updated"}

@router.post("/config/excel-card/profile/{file_id}")
async def profile_excel(file_id: int):
    """触发 Excel profiling"""
    # TODO: 创建 profiling Job
    return {"status": "job_created", "file_id": file_id}
