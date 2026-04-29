import nonebot
import httpx

from ..config import UmaConfig

_global_config = nonebot.get_plugin_config(UmaConfig)

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    ),
}


def get_proxy() -> str | None:
    if _global_config.uma_use_proxy:
        return _global_config.uma_proxy_url
    return None


async def async_get(
    url: str,
    headers: dict | None = None,
    timeout: float = 15,
    use_proxy: bool = True,
) -> httpx.Response:
    h = {**DEFAULT_HEADERS, **(headers or {})}
    proxy = get_proxy() if use_proxy else None
    async with httpx.AsyncClient(
        headers=h, proxy=proxy, timeout=timeout, follow_redirects=True
    ) as client:
        return await client.get(url)


async def async_post(
    url: str,
    headers: dict | None = None,
    data=None,
    json_data=None,
    timeout: float = 15,
    use_proxy: bool = True,
) -> httpx.Response:
    h = {**DEFAULT_HEADERS, **(headers or {})}
    proxy = get_proxy() if use_proxy else None
    async with httpx.AsyncClient(
        headers=h, proxy=proxy, timeout=timeout, follow_redirects=True
    ) as client:
        return await client.post(url, data=data, json=json_data)
