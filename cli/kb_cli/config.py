"""Configuration management for kb-cli."""
import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "kb-cli"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "api_base_url": "http://localhost:3000",
    "timeout": 30,
    "output_format": "auto",  # json | human | auto
}

ENV_MAP = {
    "KB_API_URL": "api_base_url",
    "KB_TIMEOUT": "timeout",
}


def load_config() -> dict[str, Any]:
    """Load config from file, apply env var overrides."""
    config = dict(DEFAULTS)

    # Load from file if exists
    if DEFAULT_CONFIG_FILE.exists():
        try:
            with open(DEFAULT_CONFIG_FILE) as f:
                file_config = yaml.safe_load(f) or {}
            config.update(file_config)
        except Exception:
            pass

    # Apply env var overrides
    for env_key, config_key in ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            if config_key == "timeout":
                try:
                    config[config_key] = int(val)
                except ValueError:
                    pass
            else:
                config[config_key] = val

    return config


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_config(config: dict[str, Any]):
    """Save config to file."""
    ensure_config_dir()
    with open(DEFAULT_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
