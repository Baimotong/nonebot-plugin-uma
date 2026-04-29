import asyncio
import operator
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.http import async_get
from .news_model import NewsItem

QUERY_DICT = {
    "jp": {
        "origin": "https://umamusume.jp",
        "url": "https://umamusume.jp/api/ajax/pr_info_index?format=json",
        "server_name": "日服",
    },
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36",
]


async def get_item(server: str) -> dict:
    params = QUERY_DICT.get(server, {})
    headers = {
        "User-Agent": USER_AGENTS[0],
        "origin": params.get("origin", ""),
        "referer": params.get("origin", ""),
    }
    await asyncio.sleep(0.5)
    url = params.get("url", "")
    resp = await async_get(url=url, headers=headers, timeout=15, use_proxy=True)
    return resp.json()


async def sort_news(server: str) -> list[NewsItem]:
    res_dict = await get_item(server)
    news_list = []
    for n in range(5):
        item = res_dict["information_list"][n]
        news_time = item.get("update_at") or item.get("post_at")
        news_id = item["announce_id"]
        news_url = f"https://umamusume.jp/news/detail.php?id={news_id}"
        news_title = item["title"]
        news_list.append(NewsItem(server, news_id, news_time, news_url, news_title))
    news_list.sort(key=operator.attrgetter("news_time"), reverse=True)
    return news_list


async def get_news(server: str, news_dir: Path) -> str:
    news_list = await sort_news(server)
    server_name = QUERY_DICT.get(server, {}).get("server_name", "")
    msg = f"◎◎ {server_name}马娘官网新闻 ◎◎\n"
    for news in news_list:
        news_time = datetime.strptime(news.news_time, "%Y-%m-%d %H:%M:%S")
        if server == "jp":
            news_time = news_time - timedelta(hours=1)
        msg += f"\n{news_time}\n{news.news_title}\n{news.show_url}\n"

    prev_time_file = news_dir / f"prev_time_{server}.yml"
    prev_time_file.write_text(str(news_list[0].news_time), encoding="utf-8")
    return msg


async def news_broadcast(server: str, news_list: list[NewsItem], news_dir: Path) -> str:
    prev_time_file = news_dir / f"prev_time_{server}.yml"
    if not prev_time_file.exists():
        prev_time_file.write_text("2022-01-01 00:00:00", encoding="utf-8")
    init_time = datetime.strptime(prev_time_file.read_text(encoding="utf-8").strip(), "%Y-%m-%d %H:%M:%S")

    server_name = QUERY_DICT.get(server, {}).get("server_name", "")
    msg = f"◎◎ {server_name}马娘官网新闻更新 ◎◎\n"
    for news in news_list:
        prev_time = datetime.strptime(news.news_time, "%Y-%m-%d %H:%M:%S")
        if init_time >= prev_time:
            break
        news_time = prev_time - timedelta(hours=1) if server == "jp" else prev_time
        msg += f"\n{news_time}\n{news.news_title}\n{news.show_url}\n"

    if news_list:
        prev_time_file.write_text(str(news_list[0].news_time), encoding="utf-8")
    return msg


async def judge(server: str, news_list: list[NewsItem], news_dir: Path) -> bool:
    prev_time_file = news_dir / f"prev_time_{server}.yml"
    if not prev_time_file.exists():
        prev_time_file.write_text("2022-01-01 00:00:00", encoding="utf-8")
        return True
    init_time = prev_time_file.read_text(encoding="utf-8").strip()
    if not news_list:
        return False
    return init_time != news_list[0].news_time
