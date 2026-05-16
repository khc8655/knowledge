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
    return {"status": "job_created", "file_id": file_id}
