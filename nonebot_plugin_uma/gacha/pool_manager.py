import json
from pathlib import Path

from PIL import Image
from io import BytesIO

from ..utils.data import get_default_server, load_json, save_json
from ..utils.constants import SERVER_LIST


def get_new_pool_id(gacha_dir: Path, server: str) -> str:
    with open(gacha_dir / "uma_pool.json", "r", encoding="utf-8") as f:
        pool_data = json.load(f)
    pool_list = list(pool_data[server].keys())
    return pool_list[0]


def get_select_data_path(gacha_dir: Path) -> Path:
    return gacha_dir / "select_data.json"


async def update_select_data(gacha_dir: Path):
    select_path = get_select_data_path(gacha_dir)
    default_server = get_default_server()
    pool_id_default = get_new_pool_id(gacha_dir, default_server)

    if select_path.exists():
        select_data = load_json(select_path)
        old_pool_id = select_data["default"]["pool_id"]
        server_default = select_data["default"]["server"]
        pool_id_default = get_new_pool_id(gacha_dir, server_default)
        if old_pool_id != pool_id_default:
            await reset_all_target(gacha_dir)
        select_data["default"]["pool_id"] = pool_id_default
        for gid in list(select_data.get("group", {}).keys()):
            server = select_data["group"][gid]["server"]
            select_data["group"][gid]["pool_id"] = get_new_pool_id(gacha_dir, server)
    else:
        select_data = {
            "default": {"server": default_server, "pool_id": pool_id_default},
            "group": {},
        }
        await reset_all_target(gacha_dir)

    save_json(select_path, select_data)


async def reset_all_target(gacha_dir: Path):
    target_path = gacha_dir / "gacha_target.json"
    save_json(target_path, {})


def get_pool(gacha_dir: Path, group_id: str) -> tuple[str, str]:
    select_path = get_select_data_path(gacha_dir)
    select_data = load_json(select_path)
    group_data = select_data.get("group", {}).get(group_id, None)
    if group_data:
        return group_data["server"], group_data["pool_id"]
    return select_data["default"]["server"], select_data["default"]["pool_id"]


def switch_server(gacha_dir: Path, group_id: str, server: str) -> str:
    now_server, _ = get_pool(gacha_dir, group_id)
    if server == now_server:
        return f"本群已选择服务器{server}了，无需再次切换"
    select_path = get_select_data_path(gacha_dir)
    select_data = load_json(select_path)
    group_data = select_data.get("group", {}).get(group_id, {})
    group_data["server"] = server
    group_data["pool_id"] = get_new_pool_id(gacha_dir, server)
    select_data["group"][group_id] = group_data
    save_json(select_path, select_data)
    return f"本群已成功切换到服务器{server}，并默认选取该服务器最新卡池"


def switch_pool_id(gacha_dir: Path, group_id: str, pool_id: str) -> str:
    now_server, now_pool_id = get_pool(gacha_dir, group_id)
    if pool_id == now_pool_id:
        return f"本群已选择{now_server}服的卡池{pool_id}了，无需再次切换"
    with open(gacha_dir / "uma_pool.json", "r", encoding="utf-8") as f:
        pool_data = json.load(f)
    pool_list = list(pool_data[now_server].keys())
    if pool_id not in pool_list:
        msg = f"{now_server}中未找到该卡池！\n由于卡池ID过多，您可以去bwiki上查找需要的卡池\n"
        msg += "注：卡池命名方式为卡池开始日期的前8位数字\n例如20220729"
        msg += "\n另附bwiki的卡池链接：https://wiki.biligame.com/umamusume/卡池"
        return msg
    select_path = get_select_data_path(gacha_dir)
    select_data = load_json(select_path)
    group_data = select_data.get("group", {}).get(group_id, {})
    group_data["server"] = now_server
    group_data["pool_id"] = pool_id
    select_data["group"][group_id] = group_data
    save_json(select_path, select_data)
    return f"本群已成功切换到{now_server}服的卡池{pool_id}"


async def get_pool_detail(gacha_dir: Path, group_id: str):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment
    from ..utils.http import async_get

    server, pool_id = get_pool(gacha_dir, group_id)
    with open(gacha_dir / "uma_pool.json", "r", encoding="utf-8") as f:
        pool_data = json.load(f)
    pool_detail = pool_data[server][pool_id]

    msg = Message(f"本群已选{server}服卡池: {pool_id}\n时间: {pool_detail['pool_time']}\n")

    uma_img_url = pool_detail.get("uma_title_img", "")
    if uma_img_url:
        try:
            resp = await async_get(uma_img_url)
            msg += Message(MessageSegment.image(resp.content))
        except Exception:
            pass

    up_msg_uma = "\n".join(pool_detail["uma_up"]["3"])
    msg += Message(f"马娘池: {pool_detail['uma_title']}\n3星UP:\n{up_msg_uma}\n")

    chart_img_url = pool_detail.get("chart_title_img", "")
    if chart_img_url:
        try:
            resp = await async_get(chart_img_url)
            msg += Message(MessageSegment.image(resp.content))
        except Exception:
            pass

    up_msg_chart = "\n".join(pool_detail["chart_up"]["SSR"])
    msg += Message(f"支援卡池: {pool_detail['chart_title']}\nSSR UP:\n{up_msg_chart}")
    return msg


def get_img_path(gacha_dir: Path, chara: str, gacha_type: str) -> Path:
    with open(gacha_dir / "uma_res.json", "r", encoding="utf-8") as f:
        res_data = json.load(f)
    filename = res_data[f"{gacha_type}_res"][chara]["filename"]
    return (gacha_dir / f"{gacha_type}_res" / filename).resolve()


def get_chart_name_dict(gacha_dir: Path) -> tuple[dict, dict]:
    with open(gacha_dir / "uma_res.json", "r", encoding="utf-8") as f:
        res_data = json.load(f)
    res_dict = res_data.get("chart_res", {})
    chart_name_dict = {
        key: value.get("filename", "").replace("Support_thumb_", "").replace(".png", "")
        for key, value in res_dict.items()
    }
    chart_id_dict = {v: k for k, v in chart_name_dict.items()}
    return chart_name_dict, chart_id_dict


async def generate_img(gacha_dir: Path, result_list: list[str], gacha_type: str) -> bytes:
    zoom = 2
    height_count = max((len(result_list) - 1) // 5 + 1, 2)
    w = 256 // zoom if gacha_type == "uma" else 384 // zoom
    h = 280 // zoom if gacha_type == "uma" else 512 // zoom
    full_wh = (w * 5, h * height_count)
    background = Image.new("RGBA", full_wh, "white")
    for i in range(1, len(result_list) + 1):
        column = i % 5 - 1
        if column == -1:
            column = 4
        row = (i - 1) // 5
        pos = (column * w, row * h)
        chara = result_list[i - 1]
        img_path = get_img_path(gacha_dir, chara, gacha_type)
        avatar = Image.open(img_path).convert("RGBA")
        avatar = avatar.resize((w, h))
        background.paste(avatar, pos)
    buf = BytesIO()
    background.save(buf, format="PNG")
    return buf.getvalue()


def random_comment(result: dict, gacha_type: str, first_up: int, gacha_select: str) -> str:
    s3_rank = "3★ × " if gacha_type == "uma" else "SSR × "
    s2_rank = "2★ × " if gacha_type == "uma" else "SR × "
    s1_rank = "1★ × " if gacha_type == "uma" else "R × "
    msg = f"\n本次{gacha_select}抽卡获得:\n"
    msg += f"UP卡 × {len(result['up'])}\n{s3_rank}{len(result['s3'])} (UP外)\n"
    msg += f"{s2_rank}{len(result['s2'])}\n{s1_rank}{len(result['s1'])}"
    if gacha_select == "十连":
        if result["up"]:
            msg += f"\nPS.十连出{len(result['up'])}张UP，兄弟姐妹们，有挂！"
        elif result["s3"]:
            msg += f"\nPS.十连歪到{len(result['s3'])}张彩，这就是欧皇吗？"
    else:
        msg += f"\n其中第{first_up}抽首次出UP卡"
    return msg
