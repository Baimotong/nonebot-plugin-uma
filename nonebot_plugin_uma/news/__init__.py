import nonebot
from nonebot import on_command, on_regex, get_bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot_plugin_apscheduler import scheduler

from ..utils.data import get_news_dir, load_json, save_json
from .news_spider import get_news, sort_news, judge, news_broadcast

logger = nonebot.logger

_news_dir = get_news_dir()
_push_config_path = _news_dir / "push_groups.json"


def _get_push_groups() -> set[int]:
    data = load_json(_push_config_path)
    return set(data.get("groups", []))


def _save_push_groups(groups: set[int]):
    save_json(_push_config_path, {"groups": list(groups)})


news_cmd = on_regex(r"^(\S?服)?马娘新闻$", priority=5, block=True)
news_push_on = on_command("开启马娘新闻推送", priority=5, block=True)
news_push_off = on_command("关闭马娘新闻推送", priority=5, block=True)


@news_cmd.handle()
async def handle_news(event: GroupMessageEvent):
    text = event.message.extract_plain_text().strip()
    import re
    m = re.match(r"^(\S?服)?马娘新闻$", text)
    if not m:
        return
    prefix = m.group(1)
    if prefix and prefix not in ("日服",):
        await news_cmd.finish(f"暂不支持 {prefix} 新闻，仅支持日服")

    try:
        msg = await get_news("jp", _news_dir)
    except Exception as e:
        logger.warning(f"获取马娘新闻失败: {e}")
        await news_cmd.finish("获取新闻失败，请稍后再试")
    await news_cmd.finish(msg)


@news_push_on.handle()
async def handle_push_on(event: GroupMessageEvent):
    groups = _get_push_groups()
    groups.add(event.group_id)
    _save_push_groups(groups)
    await news_push_on.finish("已开启本群日服马娘新闻推送")


@news_push_off.handle()
async def handle_push_off(event: GroupMessageEvent):
    groups = _get_push_groups()
    groups.discard(event.group_id)
    _save_push_groups(groups)
    await news_push_off.finish("已关闭本群日服马娘新闻推送")


@scheduler.scheduled_job("cron", minute="*/5", id="uma_news_poller_jp")
async def poll_news_jp():
    groups = _get_push_groups()
    if not groups:
        return
    logger.info("正在检查日服马娘新闻更新...")
    try:
        news_list = await sort_news("jp")
    except Exception as e:
        logger.warning(f"日服马娘新闻获取失败: {type(e).__name__}: {e}")
        return
    try:
        flag = await judge("jp", news_list, _news_dir)
    except Exception as e:
        logger.warning(f"日服马娘新闻判断失败: {type(e).__name__}: {e}")
        return
    if not flag:
        return
    logger.info("检测到日服马娘新闻更新！")
    try:
        msg = await news_broadcast("jp", news_list, _news_dir)
    except Exception as e:
        logger.warning(f"日服马娘新闻广播生成失败: {type(e).__name__}: {e}")
        return
    try:
        bot = get_bot()
        for gid in groups:
            try:
                await bot.send_group_msg(group_id=gid, message=msg)
            except Exception as e:
                logger.warning(f"马娘新闻推送到群 {gid} 失败: {e}")
    except Exception as e:
        logger.error(f"日服马娘新闻推送失败: {e}")
