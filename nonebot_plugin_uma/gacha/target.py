import json
from pathlib import Path

from .gacha_engine import Gacha
from .pool_manager import get_pool, get_chart_name_dict

from ..utils.data import load_json, save_json


def _target_path(gacha_dir: Path) -> Path:
    return gacha_dir / "gacha_target.json"


async def set_target_config(gacha_dir: Path, user_id: str, target_id_list: list[str]):
    path = _target_path(gacha_dir)
    data = load_json(path)
    data[user_id] = target_id_list
    save_json(path, data)


async def reset_target_config(gacha_dir: Path, user_id: str):
    path = _target_path(gacha_dir)
    data = load_json(path)
    data[user_id] = []
    save_json(path, data)


async def query_target_config(gacha_dir: Path, user_id: str) -> list[str]:
    path = _target_path(gacha_dir)
    data = load_json(path)
    _, chart_id_dict = get_chart_name_dict(gacha_dir)
    chart_name_list = [chart_id_dict.get(key, "") for key in data.get(user_id, [])]
    return [n for n in chart_name_list if n]


async def get_current_up_name(gacha_dir: Path, group_id: str) -> list[str]:
    server, pool_id = get_pool(gacha_dir, group_id)
    pool = Gacha.get_pool(pool_id, server, gacha_dir)
    return pool.get("chart_up", {}).get("SSR", [])


async def get_current_up_id_dict(gacha_dir: Path, group_id: str) -> dict[str, str]:
    current_up_name = await get_current_up_name(gacha_dir, group_id)
    chart_name_dict, _ = get_chart_name_dict(gacha_dir)
    return {chart_name_dict.get(v, ""): v for v in current_up_name}
