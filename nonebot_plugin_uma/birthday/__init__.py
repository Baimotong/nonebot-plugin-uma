from datetime import datetime

import nonebot
from nonebot import on_command, get_bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot_plugin_apscheduler import scheduler

from ..utils.data import get_birthday_dir, load_json, save_json
from .data_manager import (
    ensure_data,
    load_uma_data,
    query_by_name,
    get_display_name,
    get_today_str,
    group_by_birthday,
    DATE_FORMAT,
)

logger = nonebot.logger

_birthday_dir = get_birthday_dir()
_config_path = _birthday_dir / "config_v2.json"
_replace_dict_path = _birthday_dir / "replace_dict.json"
_push_config_path = _birthday_dir / "push_groups.json"


async def _ensure_data():
    if not _config_path.exists():
        success = await ensure_data(_birthday_dir)
        if not success:
            logger.error("马娘生日数据初始化失败")
            return False
    return True


def _load_data():
    f_data = load_uma_data(_config_path)
    replace_data = load_json(_replace_dict_path) if _replace_dict_path.exists() else {}
    return f_data, replace_data


def _get_push_groups() -> set[int]:
    data = load_json(_push_config_path)
    return set(data.get("groups", []))


def _save_push_groups(groups: set[int]):
    save_json(_push_config_path, {"groups": list(groups)})


bir_today = on_command("查今天生日马娘", aliases={"今天生日马娘"}, priority=5, block=True)
bir_query = on_command("查马娘生日", priority=5, block=True)
bir_search = on_command("查生日马娘", priority=5, block=True)
bir_push_on = on_command("开启马娘生日推送", priority=5, block=True)
bir_push_off = on_command("关闭马娘生日推送", priority=5, block=True)


@bir_today.handle()
async def handle_bir_today():
    ok = await _ensure_data()
    if not ok:
        await bir_today.finish("马娘数据尚未准备好，请稍后再试")
    f_data, replace_data = _load_data()
    today = get_today_str()
    grouped = group_by_birthday(f_data)
    names = grouped.get(today, [])
    if not names:
        await bir_today.finish("今天没有马娘生日哟")
    name_list = [get_display_name(uma, replace_data) for uma in names]
    await bir_today.finish("今天生日的马娘有：\n" + " | ".join(name_list))


@bir_query.handle()
async def handle_bir_query(args: Message = CommandArg()):
    name_raw = args.extract_plain_text().strip()
    if not name_raw:
        await bir_query.finish("请输入马娘名字，如：查马娘生日 特别周")
    ok = await _ensure_data()
    if not ok:
        await bir_query.finish("马娘数据尚未准备好，请稍后再试")
    f_data, replace_data = _load_data()
    uma = query_by_name(name_raw, f_data, replace_data)
    if not uma:
        await bir_query.finish(f"马娘 [{name_raw}] 不存在哦")
    if not uma["birthday"]:
        await bir_query.finish(f"{get_display_name(uma, replace_data)} 还没有生日数据哦！")
    await bir_query.finish(f"{get_display_name(uma, replace_data)} 的生日是：{uma['birthday']}")


@bir_search.handle()
async def handle_bir_search(args: Message = CommandArg()):
    date_str = args.extract_plain_text().strip()
    if not date_str:
        await bir_search.finish("请输入日期，如：查生日马娘 1-4")
    try:
        date = datetime.strptime(date_str, "%m-%d")
        formatted = date.strftime(DATE_FORMAT)
    except ValueError:
        await bir_search.finish(f"日期解析失败，请检查输入：{date_str}")
    ok = await _ensure_data()
    if not ok:
        await bir_search.finish("马娘数据尚未准备好，请稍后再试")
    f_data, replace_data = _load_data()
    grouped = group_by_birthday(f_data)
    uma_list = grouped.get(formatted, [])
    if not uma_list:
        await bir_search.finish(f"{formatted} 没有马娘生日哟")
    name_list = [get_display_name(uma, replace_data) for uma in uma_list]
    await bir_search.finish(f"{formatted} 生日的马娘有：\n" + " | ".join(name_list))


@bir_push_on.handle()
async def handle_push_on(event: GroupMessageEvent):
    groups = _get_push_groups()
    groups.add(event.group_id)
    _save_push_groups(groups)
    await bir_push_on.finish("已开启本群马娘生日推送")


@bir_push_off.handle()
async def handle_push_off(event: GroupMessageEvent):
    groups = _get_push_groups()
    groups.discard(event.group_id)
    _save_push_groups(groups)
    await bir_push_off.finish("已关闭本群马娘生日推送")


@scheduler.scheduled_job("cron", hour=8, minute=31, id="uma_birthday_push")
async def push_birthday():
    groups = _get_push_groups()
    if not groups:
        return
    ok = await _ensure_data()
    if not ok:
        return
    f_data, replace_data = _load_data()
    today = get_today_str()
    grouped = group_by_birthday(f_data)
    uma_list = grouped.get(today, [])
    if not uma_list:
        logger.info("今天没有马娘生日")
        return
    name_list = [get_display_name(uma, replace_data) for uma in uma_list]
    msg = "今天生日的马娘有：\n" + " | ".join(name_list)
    try:
        bot = get_bot()
        for gid in groups:
            try:
                await bot.send_group_msg(group_id=gid, message=msg)
            except Exception as e:
                logger.warning(f"马娘生日推送到群 {gid} 失败: {e}")
    except Exception as e:
        logger.error(f"马娘生日推送失败: {e}")
