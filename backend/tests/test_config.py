import tempfile
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import AppConfig

def test_load_defaults():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = AppConfig(config_dir=tmpdir)
        assert cfg.get('llm_model') == 'Qwen/Qwen2.5-7B-Instruct'
        assert cfg.get('max_section_chars') == 1200
        assert cfg.get('route_learning_enabled') is True

def test_save_and_reload():
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = AppConfig(config_dir=tmpdir)
        cfg.set('llm_model', 'custom-model')
        cfg.set('max_section_chars', 2000)
        cfg.save()
        cfg2 = AppConfig(config_dir=tmpdir)
        assert cfg2.get('llm_model') == 'custom-model'
        assert cfg2.get('max_section_chars') == 2000

def test_env_override():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['LLM_MODEL'] = 'env-model'
        cfg = AppConfig(config_dir=tmpdir)
        assert cfg.get('llm_model') == 'env-model'
        del os.environ['LLM_MODEL']
