import os
import yaml
from typing import Any

DEFAULTS = {
    'llm_api_key': '',
    'llm_base_url': 'https://api.siliconflow.cn/v1',
    'llm_model': 'Qwen/Qwen2.5-7B-Instruct',
    'embedding_model': 'BAAI/bge-large-zh-v1.5',
    'max_section_chars': 1200,
    'max_file_size_mb': 50,
    'max_files_per_upload': 20,
    'route_learning_enabled': True,
    'cache_evict_days': 7,
    'cache_max_entries': 5000,
    'coarse_doc_detection': True,
}

ENV_MAP = {
    'LLM_API_KEY': 'llm_api_key',
    'LLM_BASE_URL': 'llm_base_url',
    'LLM_MODEL': 'llm_model',
    'EMBEDDING_MODEL': 'embedding_model',
    'KB_DATA_DIR': 'data_dir',
}


class AppConfig:
    def __init__(self, config_dir: str = None):
        self._data = dict(DEFAULTS)
        self._config_dir = config_dir or os.environ.get('KB_DATA_DIR', './data')
        self._config_path = os.path.join(self._config_dir, 'config.yaml')
        self._load()

    def _load(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r') as f:
                    file_data = yaml.safe_load(f) or {}
                self._data.update(file_data)
            except Exception:
                pass
        for env_key, cfg_key in ENV_MAP.items():
            env_val = os.environ.get(env_key)
            if env_val:
                if cfg_key in ('max_section_chars', 'max_file_size_mb',
                               'max_files_per_upload', 'cache_evict_days',
                               'cache_max_entries'):
                    try:
                        env_val = int(env_val)
                    except ValueError:
                        pass
                self._data[cfg_key] = env_val

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value

    def save(self):
        os.makedirs(self._config_dir, exist_ok=True)
        with open(self._config_path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    def to_dict(self) -> dict:
        return dict(self._data)
