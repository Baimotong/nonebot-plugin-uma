import json
import platform
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ..utils.http import async_get

RAW_BASE_URL = "https://raw.githubusercontent.com/azmiao/uma_info_data/main"

if platform.system() == "Windows":
    DATE_FORMAT = "%#m月%#d日"
else:
    DATE_FORMAT = "%-m月%-d日"


async def ensure_data(data_dir: Path) -> bool:
    try:
        resp = await async_get(f"{RAW_BASE_URL}/config_v2.json", use_proxy=False)
        resp.raise_for_status()
        (data_dir / "config_v2.json").write_text(resp.text, encoding="utf-8")
        return True
    except Exception:
        return False


def load_uma_data(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_replace_dict(data_dir: Path) -> dict:
    path = data_dir / "replace_dict.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_uma(raw: dict) -> dict:
    return {
        "id": raw.get("id", ""),
        "name": raw.get("name", ""),
        "cn_name": raw.get("cn_name", ""),
        "en": raw.get("en", ""),
        "birthday": raw.get("birthday", ""),
        "category": raw.get("category", []),
    }


def get_display_name(uma: dict, replace_data: dict) -> str:
    if uma["cn_name"]:
        return uma["cn_name"]
    aliases = replace_data.get(uma["id"], [])
    return aliases[0] if aliases else uma["name"]


def query_by_name(name: str, f_data: dict, replace_data: dict) -> dict | None:
    for raw in f_data.values():
        uma = parse_uma(raw)
        if name in (uma["name"], uma["cn_name"], uma["en"]):
            return uma
        if name in replace_data.get(uma["id"], []):
            return uma
    return None


def get_today_str() -> str:
    return datetime.now().strftime(DATE_FORMAT)


def group_by_birthday(f_data: dict) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for raw in f_data.values():
        uma = parse_uma(raw)
        if uma["birthday"] and "ウマ娘" in uma.get("category", []):
            grouped[uma["birthday"]].append(uma)
    return grouped
