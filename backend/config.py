import os
import yaml
from typing import Any, Dict, Optional

DEFAULTS = {
    'llm_api_key': '',
    'llm_base_url': 'https://api.siliconflow.cn/v1',
    'llm_model': 'Qwen/Qwen2.5-7B-Instruct',
    'embedding_model': 'Pro/BAAI/bge-m3',
    'reranker_model': 'BAAI/bge-reranker-v2-m3',
    'max_section_chars': 1200,
    'max_file_size_mb': 50,
    'max_files_per_upload': 20,
    'route_learning_enabled': True,
    'cache_evict_days': 7,
    'cache_max_entries': 5000,
    'coarse_doc_detection': True,
    'max_cards_per_response': 5,
    'chat_history_limit': 10,
    'auto_detect_intent': True,
}

DEFAULT_LLM_PROFILES = {
    'default': {
        'base_url': '',
        'api_key': '',
        'model': 'DeepSeek-V4-Flash',
    },
    'annotation': {
        'base_url': 'https://api.siliconflow.cn/v1',
        'api_key': '',
        'model': 'Qwen/Qwen2.5-7B-Instruct',
    },
    'generation': {
        'base_url': '',
        'api_key': '',
        'model': 'DeepSeek-V4-Flash',
    },
    'reply': {
        'base_url': '',
        'api_key': '',
        'model': 'DeepSeek-V4-Flash',
    },
    'vision': {
        'base_url': 'https://api.siliconflow.cn/v1',
        'api_key': '',
        'model': 'Qwen/Qwen3-VL-8B-Instruct',
    },
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

    def get_llm_profile(self, profile_name: str = 'default') -> Dict[str, str]:
        """获取指定任务的 LLM 配置。

        优先级: llm_profiles.{profile_name} > llm_profiles.default > 旧平铺字段 > 环境变量
        """
        profiles = self._data.get('llm_profiles', {})

        # 构建 default profile（兼容旧平铺配置）
        default_profile = {
            'base_url': self._data.get('llm_base_url', DEFAULTS['llm_base_url']),
            'api_key': self._data.get('llm_api_key', DEFAULTS['llm_api_key']),
            'model': self._data.get('llm_model', DEFAULTS['llm_model']),
        }
        # 用 llm_profiles.default 覆盖
        if 'default' in profiles:
            default_profile.update({k: v for k, v in profiles['default'].items() if v})

        # 环境变量覆盖 default
        env_key = os.environ.get('LLM_API_KEY')
        if env_key:
            default_profile['api_key'] = env_key
        env_url = os.environ.get('LLM_BASE_URL')
        if env_url:
            default_profile['base_url'] = env_url
        env_model = os.environ.get('LLM_MODEL')
        if env_model:
            default_profile['model'] = env_model

        if profile_name == 'default':
            return default_profile

        # 非 default profile: 继承 default，用指定 profile 覆盖
        result = dict(default_profile)
        # 先从 DEFAULT_LLM_PROFILES 取默认值，再用用户配置覆盖
        if profile_name in DEFAULT_LLM_PROFILES:
            result.update({k: v for k, v in DEFAULT_LLM_PROFILES[profile_name].items() if v})
        if profile_name in profiles:
            result.update({k: v for k, v in profiles[profile_name].items() if v})

        return result

    def get_llm_profiles(self) -> Dict[str, Dict[str, str]]:
        """获取所有 LLM profiles，用于前端展示。"""
        profiles = self._data.get('llm_profiles', {})
        result = {}
        for name in list(DEFAULT_LLM_PROFILES.keys()) + [k for k in profiles if k not in DEFAULT_LLM_PROFILES]:
            result[name] = self.get_llm_profile(name)
        return result

    def set_llm_profiles(self, profiles: Dict[str, Dict[str, str]]):
        """设置 LLM profiles。"""
        self._data['llm_profiles'] = profiles
