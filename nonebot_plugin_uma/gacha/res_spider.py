import json
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from ..utils.http import DEFAULT_HEADERS


async def download_img(gacha_dir: Path, res_type_f: str, filename: str, img_url: str):
    img_dir = gacha_dir / res_type_f
    img_dir.mkdir(parents=True, exist_ok=True)
    target = img_dir / filename
    if target.exists():
        return
    try:
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=10, follow_redirects=True) as client:
            resp = await client.get(img_url)
            target.write_bytes(resp.content)
    except Exception:
        pass


async def get_res(gacha_dir: Path):
    res_data: dict[str, dict] = {}

    # 赛马娘 - 新页面结构：img alt含Chr，父级a标签title为角色名
    res_data["uma_res"] = {}
    url = "https://wiki.biligame.com/umamusume/赛马娘一览"
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    imgs = soup.find_all("img")
    for img in imgs:
        alt = img.get("alt", "")
        if "Chr" not in alt:
            continue
        parent = img.parent
        if not parent or parent.name != "a":
            continue
        title = parent.get("title", "")
        if not title:
            continue
        src = img.get("src", "")
        if not src:
            continue
        filename = alt.replace(" ", "_")
        # 去掉缩略图后缀，获取原图URL
        img_url = src
        if "/thumb/" in img_url:
            parts = img_url.split("/thumb/")
            if len(parts) == 2:
                thumb_path = parts[1]
                # 去掉最后的 /100px-xxx 部分
                idx = thumb_path.rfind("/")
                if idx > 0:
                    img_url = parts[0] + "/" + thumb_path[:idx]
        res_data["uma_res"][title] = {"filename": filename, "img_url": img_url}
        await download_img(gacha_dir, "uma_res", filename, img_url)

    # 支援卡 - 旧页面结构popup
    res_data["chart_res"] = {}
    url = "https://wiki.biligame.com/umamusume/支援卡一览"
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=15, follow_redirects=True) as client:
        resp = await client.get(url)
    soup = BeautifulSoup(resp.text, "lxml")
    span_list = soup.find_all("span", {"class": "popup"})
    for span in span_list:
        a_tag = span.find("a")
        img_tag = span.find("img")
        if not a_tag or not img_tag:
            continue
        title = a_tag.get("title", "")
        filename = img_tag.get("alt", "").replace(" ", "_")
        src = img_tag.get("src", "")
        img_url = src.replace("thumb/", "").replace("/100px-" + filename, "") if src else ""
        if title and filename:
            res_data["chart_res"][title] = {"filename": filename, "img_url": img_url}
            await download_img(gacha_dir, "chart_res", filename, img_url)

    with open(gacha_dir / "uma_res.json", "w", encoding="utf-8") as f:
        json.dump(res_data, f, ensure_ascii=False, indent=4)
