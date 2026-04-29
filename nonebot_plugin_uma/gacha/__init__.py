from typing import Callable, Awaitable

import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler

from ..utils.data import get_gacha_dir
from ..utils.limiter import FreqLimiter, DailyNumberLimiter
from ..utils.constants import SERVER_LIST
from .gacha_engine import Gacha
from .pool_manager import (
    get_pool,
    switch_server,
    switch_pool_id,
    get_pool_detail,
    generate_img,
    random_comment,
    get_img_path,
    update_select_data,
)
from .pool_spider import get_pool_data
from .res_spider import get_res
from .target import (
    set_target_config,
    get_current_up_id_dict,
    reset_target_config,
    query_target_config,
)

logger = nonebot.logger

_gacha_dir = get_gacha_dir()

lmt = FreqLimiter(10)
single_limit = DailyNumberLimiter(30000)
tenjou_limit = DailyNumberLimiter(15)
full_limit = DailyNumberLimiter(10)

SINGLE_EXCEED = f"您今天已经抽过{single_limit.max}颗萝卜了，欢迎明早5点后再来哦！"
TENJOU_EXCEED = f"您今天已经抽过{tenjou_limit.max}张天井券了，欢迎明早5点后再来哦！"
FULL_EXCEED = f"您今天已经抽过{full_limit.max}次支援卡满破了，欢迎明早5点后再来哦！"


async def _ensure_data() -> bool:
    select_file = _gacha_dir / "select_data.json"
    res_file = _gacha_dir / "uma_res.json"
    if not select_file.exists() or not res_file.exists():
        logger.info("马娘卡池信息不存在，正在重新生成...")
        try:
            await get_pool_data(_gacha_dir)
            await get_res(_gacha_dir)
            await update_select_data(_gacha_dir)
            logger.info("马娘抽卡信息更新完成")
        except Exception as e:
            logger.error(f"马娘卡池信息初始化失败: {e}")
            return False
    return True


async def _gacha_wrapper(
    matcher: Matcher,
    event: GroupMessageEvent,
    handler: Callable[[str, str, str, str], Awaitable[Message]],
    limit_obj: DailyNumberLimiter | None = None,
    limit_msg: str = "",
    limit_cost: int = 1,
) -> None:
    """抽卡公共逻辑：频率限制、数据准备、异常处理"""
    uid = str(event.user_id)
    if not lmt.check(uid):
        await matcher.finish(MessageSegment.at(int(uid)) + f"\n马娘抽卡功能冷却中(剩余 {int(lmt.left_time(uid)) + 1}秒)")
    if limit_obj and not limit_obj.check(uid):
        await matcher.finish(MessageSegment.at(int(uid)) + f"\n{limit_msg}")
    lmt.start_cd(uid)
    if limit_obj:
        limit_obj.increase(uid, limit_cost)
    if not await _ensure_data():
        await matcher.finish("卡池数据尚未准备好，请稍后再试")
    gid = str(event.group_id)
    server, pool_id = get_pool(_gacha_dir, gid)
    try:
        msg = await handler(uid, gid, server, pool_id)
    except IndexError:
        msg = "卡池数据还未自动更新完全，请耐心等待几小时后再尝试"
    await matcher.finish(msg)


# === 单抽 ===
gacha_one_uma = on_command("马娘单抽", aliases={"单抽马娘"}, priority=5, block=True)

@gacha_one_uma.handle()
async def handle_one_uma(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        gacha = Gacha(pool_id, "uma", server, _gacha_dir)
        chara, res_type = gacha.gacha_one(gacha.up_prob, gacha.s3_prob, gacha.s2_prob, gacha.s1_prob)
        img_path = get_img_path(_gacha_dir, chara, "uma")
        msg = Message(MessageSegment.image(img_path.read_bytes()))
        msg += MessageSegment.at(int(uid)) + f"\n抽到了 {chara}"
        if res_type == "up":
            msg += "\nPS.兄弟姐妹们，有挂！"
        elif res_type == "s3":
            msg += "\nPS.这就是欧皇附体吗？"
        return msg
    await _gacha_wrapper(gacha_one_uma, event, _do, single_limit, SINGLE_EXCEED, 150)


gacha_one_chart = on_command("育成卡单抽", aliases={"支援卡单抽", "s卡单抽", "S卡单抽"}, priority=5, block=True)

@gacha_one_chart.handle()
async def handle_one_chart(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        gacha = Gacha(pool_id, "chart", server, _gacha_dir)
        chara, res_type = gacha.gacha_one(gacha.up_prob, gacha.s3_prob, gacha.s2_prob, gacha.s1_prob)
        img_path = get_img_path(_gacha_dir, chara, "chart")
        msg = Message(MessageSegment.image(img_path.read_bytes()))
        msg += MessageSegment.at(int(uid)) + f"\n抽到了 {chara}"
        if res_type == "up":
            msg += "\nPS.兄弟姐妹们，有挂！"
        elif res_type == "s3":
            msg += "\nPS.这就是欧皇附体吗？"
        return msg
    await _gacha_wrapper(gacha_one_chart, event, _do, single_limit, SINGLE_EXCEED, 150)


# === 十连 ===
gacha_ten_uma = on_command("马娘十连", aliases={"马十连"}, priority=5, block=True)

@gacha_ten_uma.handle()
async def handle_ten_uma(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        gacha = Gacha(pool_id, "uma", server, _gacha_dir)
        first_up, result = gacha.gacha_ten(gacha.result, gacha.first_up)
        result_list = result["up"] + result["s3"] + result["s2"] + result["s1"]
        img_bytes = await generate_img(_gacha_dir, result_list, "uma")
        msg_com = random_comment(result, "uma", first_up, "十连")
        msg = Message(MessageSegment.image(img_bytes))
        msg += MessageSegment.at(int(uid)) + f"\n{msg_com}"
        return msg
    await _gacha_wrapper(gacha_ten_uma, event, _do, single_limit, SINGLE_EXCEED, 1500)


gacha_ten_chart = on_command("育成卡十连", aliases={"支援卡十连", "s卡十连", "S卡十连"}, priority=5, block=True)

@gacha_ten_chart.handle()
async def handle_ten_chart(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        gacha = Gacha(pool_id, "chart", server, _gacha_dir)
        first_up, result = gacha.gacha_ten(gacha.result, gacha.first_up)
        result_list = result["up"] + result["s3"] + result["s2"] + result["s1"]
        img_bytes = await generate_img(_gacha_dir, result_list, "chart")
        msg_com = random_comment(result, "chart", first_up, "十连")
        msg = Message(MessageSegment.image(img_bytes))
        msg += MessageSegment.at(int(uid)) + f"\n{msg_com}"
        return msg
    await _gacha_wrapper(gacha_ten_chart, event, _do, single_limit, SINGLE_EXCEED, 1500)


# === 天井 ===
gacha_tenjou_uma = on_command("马之井", aliases={"马娘井", "马娘一井"}, priority=5, block=True)

@gacha_tenjou_uma.handle()
async def handle_tenjou_uma(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        gacha = Gacha(pool_id, "uma", server, _gacha_dir)
        first_up, result = gacha.gacha_tenjou(gacha.result, gacha.first_up)
        result_list = result["up"] + result["s3"]
        img_bytes = await generate_img(_gacha_dir, result_list, "uma")
        msg_com = random_comment(result, "uma", first_up, "天井")
        msg = Message(MessageSegment.image(img_bytes))
        msg += MessageSegment.at(int(uid)) + f"\n{msg_com}"
        return msg
    await _gacha_wrapper(gacha_tenjou_uma, event, _do, tenjou_limit, TENJOU_EXCEED)


gacha_tenjou_chart = on_command(
    "育成卡井",
    aliases={"育成卡一井", "支援卡井", "支援卡一井", "s卡井", "s卡一井", "S卡井", "S卡一井"},
    priority=5,
    block=True,
)

@gacha_tenjou_chart.handle()
async def handle_tenjou_chart(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        gacha = Gacha(pool_id, "chart", server, _gacha_dir)
        first_up, result = gacha.gacha_tenjou(gacha.result, gacha.first_up)
        result_list = result["up"] + result["s3"]
        img_bytes = await generate_img(_gacha_dir, result_list, "chart")
        msg_com = random_comment(result, "chart", first_up, "天井")
        msg = Message(MessageSegment.image(img_bytes))
        msg += MessageSegment.at(int(uid)) + f"\n{msg_com}"
        return msg
    await _gacha_wrapper(gacha_tenjou_chart, event, _do, tenjou_limit, TENJOU_EXCEED)


# === 满破 ===
gacha_full_chart = on_command("育成卡抽满破", aliases={"支援卡抽满破"}, priority=5, block=True)

@gacha_full_chart.handle()
async def handle_full_chart(event: GroupMessageEvent):
    async def _do(uid: str, gid: str, server: str, pool_id: str) -> Message:
        if pool_id == "00000000":
            raise ValueError("初始卡池00000000不支持该功能哦")
        gacha = Gacha(pool_id, "chart", server, _gacha_dir)
        chart_name_list = await query_target_config(_gacha_dir, uid)
        need_dict, ten_num, exchange, first_up, result = gacha.gacha_full_singer(
            gacha.result, gacha.first_up, chart_name_list
        )
        up_msg_tmp = [f"✦ 获得{v}张{k}" for k, v in need_dict.items()]
        up_msg = "\n".join(up_msg_tmp)
        result_list = result["up"] + result["s3"]
        img_bytes = await generate_img(_gacha_dir, result_list, "chart")
        msg_com = random_comment(result, "chart", first_up, "抽满破")
        msg = Message(MessageSegment.image(img_bytes))
        msg += MessageSegment.at(int(uid)) + f"\n{msg_com}\n{up_msg}\n✦ 其中兑换了{exchange}张\n总共花费{ten_num * 10}抽"
        return msg
    try:
        await _gacha_wrapper(gacha_full_chart, event, _do, full_limit, FULL_EXCEED)
    except ValueError as e:
        await gacha_full_chart.finish(str(e))


# === 满破目标 ===
gacha_select_target = on_command("育成卡选择满破目标", aliases={"支援卡选择满破目标"}, priority=5, block=True)

@gacha_select_target.handle()
async def handle_select_target(event: GroupMessageEvent, args: Message = CommandArg()):
    uid = str(event.user_id)
    gid = str(event.group_id)
    target_raw = args.extract_plain_text().strip()
    ok = await _ensure_data()
    if not ok:
        await gacha_select_target.finish("卡池数据尚未准备好")
    chart_up_id_dict = await get_current_up_id_dict(_gacha_dir, gid)
    if not target_raw:
        msg = '您未输入目标，请从以下目标选择，输入数字ID即可，多个目标用英文逗号间隔，需要添加全部UP请输入"all"：\n'
        msg += "\n".join([f"> {k}: {v}" for k, v in chart_up_id_dict.items()])
    else:
        if target_raw == "all":
            raw_id_list = list(chart_up_id_dict.keys())
        else:
            raw_id_list = target_raw.split(",")
        await set_target_config(_gacha_dir, uid, raw_id_list)
        chart_name_list = [chart_up_id_dict.get(x, "") for x in raw_id_list]
        chart_name_list = [n for n in chart_name_list if n]
        msg = "已将以下目标设置为您的目标，注意卡池更新后将会重置：\n" + "\n".join(chart_name_list)
    await gacha_select_target.finish(msg, at_sender=True)


gacha_query_target = on_command("育成卡查询满破目标", aliases={"支援卡查询满破目标"}, priority=5, block=True)

@gacha_query_target.handle()
async def handle_query_target(event: GroupMessageEvent):
    uid = str(event.user_id)
    name_list = await query_target_config(_gacha_dir, uid)
    if not name_list:
        msg = "您当前没有任何满破目标呢！"
    else:
        msg = "当前您的目标为下列支援卡：\n" + "\n".join(name_list)
    await gacha_query_target.finish(msg, at_sender=True)


gacha_clear_target = on_command("育成卡清除满破目标", aliases={"支援卡清除满破目标"}, priority=5, block=True)

@gacha_clear_target.handle()
async def handle_clear_target(event: GroupMessageEvent):
    uid = str(event.user_id)
    await reset_target_config(_gacha_dir, uid)
    await gacha_clear_target.finish("已为你清除满破目标选择", at_sender=True)


# === 服务器/卡池切换 ===
gacha_switch_server = on_command("切换马娘服务器", priority=5, block=True)

@gacha_switch_server.handle()
async def handle_switch_server(event: GroupMessageEvent, args: Message = CommandArg()):
    server = args.extract_plain_text().strip()
    if server not in SERVER_LIST:
        await gacha_switch_server.finish(f"切换失败！目前仅支持服务器：{' | '.join(SERVER_LIST)}")
    msg = switch_server(_gacha_dir, str(event.group_id), server)
    await gacha_switch_server.finish(msg)


gacha_switch_pool = on_command("切换马娘卡池", priority=5, block=True)

@gacha_switch_pool.handle()
async def handle_switch_pool(event: GroupMessageEvent, args: Message = CommandArg()):
    pool_id = args.extract_plain_text().strip()
    msg = switch_pool_id(_gacha_dir, str(event.group_id), pool_id)
    await gacha_switch_pool.finish(msg)


gacha_view_pool = on_command("查看马娘卡池", priority=5, block=True)

@gacha_view_pool.handle()
async def handle_view_pool(event: GroupMessageEvent):
    msg = await get_pool_detail(_gacha_dir, str(event.group_id))
    await gacha_view_pool.finish(msg)


gacha_update = on_command("更新马娘卡池", priority=5, block=True, permission=SUPERUSER)

@gacha_update.handle()
async def handle_update(event: GroupMessageEvent):
    try:
        await get_pool_data(_gacha_dir)
        await get_res(_gacha_dir)
        await update_select_data(_gacha_dir)
        msg = "马娘抽卡信息更新完成"
    except Exception as e:
        msg = f"马娘卡池信息更新失败：{e}"
    await gacha_update.finish(msg)


@scheduler.scheduled_job("cron", hour=3, minute=30, id="uma_gacha_update")
async def auto_update_gacha():
    try:
        await get_pool_data(_gacha_dir)
        await get_res(_gacha_dir)
        await update_select_data(_gacha_dir)
        logger.info("马娘卡池定时更新完成")
    except Exception as e:
        logger.error(f"马娘卡池定时更新失败: {e}")
