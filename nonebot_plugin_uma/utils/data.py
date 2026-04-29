import json
from pathlib import Path
from typing import Optional

from nonebot import require

require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

from ..config import UmaConfig

import nonebot

_global_config = nonebot.get_plugin_config(UmaConfig)


def _get_legacy_data_dir() -> Path | None:
    """检查是否存在旧版默认数据目录，用于兼容迁移"""
    legacy = Path("data/uma")
    if legacy.exists() and any(legacy.iterdir()):
        return legacy
    return None


def get_data_dir() -> Path:
    """
    获取数据目录，优先级：
    1. 用户自定义配置路径（兼容旧配置）
    2. 旧版默认路径 data/uma（有数据时兼容）
    3. nonebot-plugin-localstore 标准路径
    """
    # 1. 用户配置了自定义路径
    custom_dir: Optional[Path] = _global_config.uma_data_dir
    if custom_dir is not None and custom_dir.exists():
        return custom_dir

    # 2. 旧版默认路径存在且有数据
    legacy = _get_legacy_data_dir()
    if legacy:
        return legacy

    # 3. 新用户使用 localstore 标准路径
    return store.get_plugin_data_dir()


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
