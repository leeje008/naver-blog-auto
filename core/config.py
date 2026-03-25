"""설정 영속화 모듈 — data/config.json 기반."""

import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"

DEFAULT_CONFIG: dict = {
    "llm_model": "qwen3.5:27b",
    "keyword_model": "llama3.1:8b",
    "seo_profile": "balanced",
}


def load_config() -> dict:
    """설정 파일 로드. 파일이 없거나 손상되면 빈 dict 반환."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    """설정 파일 원자적 저장 (.tmp → rename)."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = CONFIG_PATH.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(str(tmp_path), str(CONFIG_PATH))


def get_config(key: str, default=None):
    """설정값 단일 조회."""
    return load_config().get(key, default)


def set_config(key: str, value) -> None:
    """설정값 단일 저장."""
    config = load_config()
    config[key] = value
    save_config(config)
