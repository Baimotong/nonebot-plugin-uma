import json
import nonebot
from pathlib import Path

from ..config import UmaConfig

_global_config = nonebot.get_plugin_config(UmaConfig)


def get_data_dir() -> Path:
    d = _global_config.uma_data_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_gacha_dir() -> Path:
    d = get_data_dir() / "gacha"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_news_dir() -> Path:
    d = get_data_dir() / "news"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_birthday_dir() -> Path:
    d = get_data_dir() / "birthday"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_default_server() -> str:
    server = _global_config.uma_default_server
    if server not in ("jp", "tw", "ko", "bili"):
        return "jp"
    return server


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
