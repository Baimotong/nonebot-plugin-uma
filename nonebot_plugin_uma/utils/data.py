import json
from pathlib import Path
from typing import Optional

from nonebot import require

require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store

from ..config import UmaConfig

import nonebot

_global_config = nonebot.get_plugin_config(UmaConfig)


def _resolve_data_dir() -> Path:
    """
    解析数据目录，优先级：
    1. 用户自定义配置路径（兼容旧配置）
    2. 旧版默认路径 data/uma（有数据时兼容）
    3. nonebot-plugin-localstore 标准路径
    """
    # 1. 用户配置了自定义路径
    custom_dir: Optional[Path] = _global_config.uma_data_dir
    if custom_dir is not None and custom_dir.exists():
        return custom_dir

    # 2. 旧版默认路径存在且有数据
    legacy = Path("data/uma")
    if legacy.exists() and any(legacy.iterdir()):
        return legacy

    # 3. 新用户使用 localstore 标准路径
    return store.get_plugin_data_dir()


# 模块导入时只计算一次数据目录路径
_data_dir: Path = _resolve_data_dir()
_gacha_dir: Path = _data_dir / "gacha"
_news_dir: Path = _data_dir / "news"
_birthday_dir: Path = _data_dir / "birthday"


def get_data_dir() -> Path:
    return _data_dir


def get_gacha_dir() -> Path:
    _gacha_dir.mkdir(parents=True, exist_ok=True)
    return _gacha_dir


def get_news_dir() -> Path:
    _news_dir.mkdir(parents=True, exist_ok=True)
    return _news_dir


def get_birthday_dir() -> Path:
    _birthday_dir.mkdir(parents=True, exist_ok=True)
    return _birthday_dir


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
