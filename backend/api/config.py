from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict
from config import AppConfig

router = APIRouter(prefix="/config", tags=["config"])


class LLMProfileConfig(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class SystemConfig(BaseModel):
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    llm_profiles: Optional[Dict[str, LLMProfileConfig]] = None
    embedding_model: Optional[str] = None
    max_section_chars: Optional[int] = None
    max_file_size_mb: Optional[int] = None
    route_learning_enabled: Optional[bool] = None
    cache_evict_days: Optional[int] = None
    cache_max_entries: Optional[int] = None


def _mask_profiles(profiles: dict) -> dict:
    """Mask API keys in profiles for display."""
    masked = {}
    for name, profile in profiles.items():
        p = dict(profile)
        if p.get('api_key'):
            p['api_key'] = p['api_key'][:8] + '...'
        masked[name] = p
    return masked


@router.get("")
async def get_config():
    cfg = AppConfig()
    data = cfg.to_dict()
    if data.get('llm_api_key'):
        data['llm_api_key'] = data['llm_api_key'][:8] + '...'
    data['llm_profiles'] = _mask_profiles(cfg.get_llm_profiles())
    return data


@router.put("")
async def update_config(config: SystemConfig):
    cfg = AppConfig()
    update_data = config.model_dump(exclude_none=True)

    # Handle llm_profiles separately
    profiles = update_data.pop('llm_profiles', None)
    if profiles is not None:
        # Convert LLMProfileConfig dicts, strip '...' masked keys
        clean_profiles = {}
        for name, profile in profiles.items():
            p = {k: v for k, v in profile.items() if v and not v.endswith('...')}
            clean_profiles[name] = p
        cfg.set_llm_profiles(clean_profiles)

    for key, value in update_data.items():
        cfg.set(key, value)
    cfg.save()
    return {"status": "updated", "config": cfg.to_dict()}


@router.get("/llm-profiles")
async def get_llm_profiles():
    cfg = AppConfig()
    return _mask_profiles(cfg.get_llm_profiles())


@router.put("/llm-profiles")
async def update_llm_profiles(profiles: Dict[str, LLMProfileConfig]):
    cfg = AppConfig()
    clean = {}
    for name, profile in profiles.items():
        p = {k: v for k, v in profile.model_dump(exclude_none=True).items() if v and not v.endswith('...')}
        clean[name] = p
    cfg.set_llm_profiles(clean)
    cfg.save()
    return {"status": "updated", "profiles": _mask_profiles(cfg.get_llm_profiles())}

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
