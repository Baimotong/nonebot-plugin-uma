import datetime
import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from ..utils.http import DEFAULT_HEADERS
from ..utils.constants import SERVER_LIST, get_differ

INIT_DATA = {
    "other_uma": {
        "3": ["特别周", "无声铃鹿", "东海帝皇", "丸善斯基", "小栗帽", "大树快车", "目白麦昆", "鲁道夫象征", "米浴"],
        "2": ["黄金船", "伏特加", "大和赤骥", "草上飞", "神鹰", "气槽", "摩耶重炮", "超级小海湾"],
        "1": ["目白赖恩", "爱丽速子", "胜利奖券", "樱花进王", "春乌拉拉", "待兼福来", "优秀素质", "帝王光辉"],
    },
    "other_chart": {
        "SSR": [
            "【輝く景色の、その先に】サイレンススズカ", "【夢は掲げるものなのだっ！】トウカイテイオー",
            "【Run(my)way】ゴールドシチー", "【はやい！うまい！はやい！】サクラバクシンオー",
            "【まだ小さな蕾でも】ニシノフラワー",
            "【必殺！Wキャロットパンチ！】ビコーペガサス", "【不沈艦の進撃】ゴールドシップ", "【待望の大謀】セイウンスカイ",
            "【天をも切り裂くイナズマ娘！】タマモクロス", "【一粒の安らぎ】スーパークリーク",
            "【千紫万紅にまぎれぬ一凛】グラスワンダー",
            "【飛び出せ、キラメケ】アイネスフウジン", "【B·N·Winner!!】ウイニングチケット",
            "【感謝は指先まで込めて】ファインモーション",
            "【7センチの先へ】エアシャカール", "【ロード·オブ·ウオッカ】ウオッカ", "【ようこそ、トレセン学園へ！】駿川たづな",
            "【パッションチャンピオーナ！】エルコンドルパサー", "【これが私のウマドル道☆】スマートファルコン",
            "【日本一のステージを】スペシャルウィーク",
        ],
        "SR": [
            "【やれやれ、お帰り】フジキセキ", "【努力は裏切らない！】ダイワスカーレット", "【テッペンに立て！】ヒシアマゾン",
            "【副会長の一刺し】エアグルーヴ", "【デジタル充電中+】アグネスデジタル", "【検証、開始】ビワハヤヒデ",
            "【カワイイ＋カワイイは～？】マヤノトップガン", "【雨の独奏、私の独創】マンハッタンカフェ",
            "【鍛えぬくトモ】ミホノブルボン", "【鍛えて、応えて！】メジロライアン", "【シチーガール入門＃】ユキノビジン",
            "【生体Aに関する実験的研究】アグネスタキオン", "【0500·定刻通り】エイシンフラッシュ",
            "【波立つキモチ】ナリタタイシン",
            "【マーベラス☆大作戦】マーベラスサンデー", "【運の行方】マチカネフクキタル",
            "【幸せと背中合わせ】メイショウドトウ",
            "【目線は気にせず】メジロドーベル", "【…ただの水滴ですって】ナイスネイチャ", "【一流プランニング】キングヘイロー",
            "【共に同じ道を！】桐生院葵", "【これがウチらのいか焼きや！】タマモクロス",
        ],
    },
}

TYPE_LIST = ["支援卡卡池", "赛马娘卡池"]


def judge_pool_type(tr) -> str | None:
    tr_a = tr.find("td").get_text().strip()
    if tr_a in TYPE_LIST:
        return tr_a
    tr_b = tr.find("td").find_next_sibling("td").get_text().strip()
    if tr_b in TYPE_LIST:
        return tr_b
    return None


async def add_other_server(server, start_time, end_time, now, pool_data, uma_title, uma_title_img, uma_up,
                           chart_title, chart_title_img, chart_up):
    differ = get_differ(server, "jp")
    start_time_ot = start_time + datetime.timedelta(days=differ + 1)
    start_time_ot_show = datetime.datetime.strftime(start_time_ot, "%Y/%m/%d %H:%M")
    end_time_ot = end_time + datetime.timedelta(days=differ + 1)
    end_time_ot_show = datetime.datetime.strftime(end_time_ot, "%Y/%m/%d %H:%M")
    pool_time_ot = f"{start_time_ot_show}~{end_time_ot_show}"
    pool_id_ot = str(start_time_ot).replace("-", "")[:8]
    if now >= start_time_ot:
        pool_data[server][pool_id_ot] = {
            "pool_time": pool_time_ot,
            "start_time": start_time_ot_show,
            "end_time": end_time_ot_show,
            "uma_title": uma_title,
            "uma_title_img": uma_title_img,
            "uma_up": uma_up,
            "chart_title": chart_title,
            "chart_title_img": chart_title_img,
            "chart_up": chart_up,
        }
    return pool_data


async def UP_modify(pool_data):
    for server in SERVER_LIST:
        for pool_id in list(pool_data[server].keys()):
            cal_pool_id = get_correspond(server, "jp", pool_id)
            if cal_pool_id == "20220729":
                pool_data[server][pool_id]["chart_up"]["R"] = ["【トレセン学園】ツルマルツヨシ"]
            if cal_pool_id == "20220111":
                pool_data[server][pool_id]["chart_up"]["SR"] = ["【これがウチらのいか焼きや！】タマモクロス"]
                pool_data[server][pool_id]["chart_up"]["SSR"] = ["【ブスッといっとく？】安心沢刺々美"]
            if "重炮" in pool_data[server][pool_id]["uma_up"]["2"]:
                pool_data[server][pool_id]["uma_up"]["2"].remove("重炮")
                pool_data[server][pool_id]["uma_up"]["2"].append("摩耶重炮")
            if "重炮" in pool_data[server][pool_id]["other_uma"]["2"]:
                pool_data[server][pool_id]["other_uma"]["2"].remove("重炮")
                pool_data[server][pool_id]["other_uma"]["2"].append("摩耶重炮")
            if "皇帝" in pool_data[server][pool_id]["uma_up"]["3"]:
                pool_data[server][pool_id]["uma_up"]["3"].remove("皇帝")
                pool_data[server][pool_id]["uma_up"]["3"].append("鲁道夫象征")
            if "皇帝" in pool_data[server][pool_id]["other_uma"]["3"]:
                pool_data[server][pool_id]["other_uma"]["3"].remove("皇帝")
                pool_data[server][pool_id]["other_uma"]["3"].append("鲁道夫象征")
    return pool_data


async def get_other_uma(pool_data, server):
    if not pool_data[server]:
        return pool_data
    for gacha_type in ["uma", "chart"]:
        id_list = list(pool_data[server].keys())
        id_list.reverse()
        pool_data[server][id_list[0]][f"other_{gacha_type}"] = INIT_DATA[f"other_{gacha_type}"]
        for i in range(1, len(id_list)):
            last_pool = pool_data[server][id_list[i - 1]][f"other_{gacha_type}"]
            new_pool_data = {}
            for rank in list(last_pool.keys()):
                new_pool_data[rank] = list(
                    set(last_pool[rank] + pool_data[server][id_list[i - 1]][f"{gacha_type}_up"][rank])
                )
            pool_data[server][id_list[i]][f"other_{gacha_type}"] = new_pool_data
            if re.search("全体", pool_data[server][id_list[i]][f"{gacha_type}_title"]):
                high_rank = list(last_pool.keys())[0]
                pool_data[server][id_list[i]][f"{gacha_type}_up"][high_rank] = last_pool[high_rank]
                pool_data[server][id_list[i]][f"other_{gacha_type}"][high_rank] = []
    return pool_data


async def get_R(pool_data, server):
    R_chart = ["【トレセン学園】" + x.split("】", 1)[1] for x in pool_data[server]["00000000"]["other_chart"]["SSR"]]
    R_chart.append("【トレセン学園】テイエムオペラオー")
    R_chart.append("【トレセン学園】メジロマックイーン")
    pool_data[server]["00000000"]["other_chart"]["R"] = list(set(R_chart))
    return pool_data


async def add_init_pool(pool_data):
    for server in SERVER_LIST:
        pool_data[server]["00000000"] = {
            "pool_time": "",
            "start_time": "",
            "end_time": "",
            "uma_title": "开服初始马娘池",
            "uma_title_img": "",
            "uma_up": {"3": [], "2": [], "1": []},
            "chart_title": "开服初始支援卡池",
            "chart_title_img": "",
            "chart_up": {"SSR": [], "SR": [], "R": []},
            "other_uma": INIT_DATA["other_uma"],
            "other_chart": INIT_DATA["other_chart"],
        }
        pool_data = await get_R(pool_data, server)
    return pool_data


async def get_pool_data(gacha_dir: Path):
    pool_url = "https://wiki.biligame.com/umamusume/卡池"
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=15, follow_redirects=True) as client:
        res = await client.get(pool_url)
    soup = BeautifulSoup(res.text, "lxml")
    soup = soup.find("table", {"style": "width:100%;text-align:center"})
    tr_all = [
        tr for tr in soup.find_all("tr")
        if tr.find("div", {"class": "floatnone"}) and judge_pool_type(tr) in TYPE_LIST
    ]

    pool_list = []
    i = 0
    while i < len(tr_all):
        tr_a = tr_all[i]
        if judge_pool_type(tr_a) == "支援卡卡池":
            pool_list.append((None, tr_a))
            i += 1
        elif judge_pool_type(tr_a) == "赛马娘卡池":
            tr_b = tr_all[i + 1] if i + 1 < len(tr_all) else None
            if tr_b and judge_pool_type(tr_b) == "赛马娘卡池":
                pool_list.append((tr_a, None))
                i += 1
            elif tr_b and judge_pool_type(tr_b) == "支援卡卡池":
                pool_list.append((tr_a, tr_b))
                i += 2
            else:
                i += 1
        else:
            i += 1

    pool_data: dict = {}
    now = datetime.datetime.now()
    for server in SERVER_LIST:
        pool_data[server] = {}

    for pool in pool_list:
        if pool[0]:
            pool_time_edge = pool[0].find("td").text.strip().split("~", 1)
        else:
            pool_time_edge = pool[1].find("td").text.strip().split("~", 1)
        start_time = datetime.datetime.strptime(pool_time_edge[1], "%Y/%m/%d %H:%M") - datetime.timedelta(hours=1)
        start_time_show = datetime.datetime.strftime(start_time, "%Y/%m/%d %H:%M")
        end_time = datetime.datetime.strptime(pool_time_edge[0], "%Y/%m/%d %H:%M") - datetime.timedelta(hours=1)
        end_time_show = datetime.datetime.strftime(end_time, "%Y/%m/%d %H:%M")
        pool_time = f"{start_time_show}~{end_time_show}"
        pool_id = str(start_time).replace("-", "")[:8]

        uma_title, uma_title_img, uma_up_list = "", "", []
        if pool[0]:
            pool_find = pool[0].find("div", {"class": "floatnone"})
            uma_title = pool_find.find("a").get("title") if pool_find.find("a") else ""
            uma_title_id = pool_find.find("img").get("alt").replace(" ", "_") if pool_find.find("img") else ""
            uma_title_img = (
                pool_find.find("img").get("src").replace("thumb/", "").replace("/400px-" + uma_title_id, "")
                if pool_find.find("img") else ""
            )
            uma_up_list = [
                span.find("a").get("title")
                for span in pool[0].find_all("span", {"style": "display: table-cell;"})
            ]
        uma_up = {"3": uma_up_list, "2": [], "1": []}

        chart_title, chart_title_img, chart_up_list, chart_up_img_list = "", "", [], []
        if pool[1]:
            pool_find = pool[1].find("div", {"class": "floatnone"})
            chart_title = pool_find.find("a").get("title") if pool_find.find("a") else ""
            chart_title_id = pool_find.find("img").get("alt").replace(" ", "_") if pool_find.find("img") else ""
            chart_title_img = (
                pool_find.find("img").get("src").replace("thumb/", "").replace("/400px-" + chart_title_id, "")
                if pool_find.find("img") else ""
            )
            chart_up_list = [
                span.find("a").get("title")
                for span in pool[1].find_all("span", {"style": "display:inline-block;"})
            ]
            chart_up_img_list = [
                span.find("img").get("alt")
                for span in pool[1].find_all("span", {"style": "display:inline-block;"})
            ]

        SSR_list, SR_list, R_list = [], [], []
        for img_name in chart_up_img_list:
            name = img_name.replace("Support thumb ", "")
            num = chart_up_img_list.index(img_name)
            if name.startswith("1"):
                R_list.append(chart_up_list[num])
            elif name.startswith("2"):
                SR_list.append(chart_up_list[num])
            else:
                SSR_list.append(chart_up_list[num])
        chart_up = {"SSR": SSR_list, "SR": SR_list, "R": R_list}

        pool_data["jp"][pool_id] = {
            "pool_time": pool_time,
            "start_time": start_time_show,
            "end_time": end_time_show,
            "uma_title": uma_title,
            "uma_title_img": uma_title_img,
            "uma_up": uma_up,
            "chart_title": chart_title,
            "chart_title_img": chart_title_img,
            "chart_up": chart_up,
        }

        for server in SERVER_LIST:
            if server == "jp":
                continue
            pool_data = await add_other_server(
                server, start_time, end_time, now, pool_data,
                uma_title, uma_title_img, uma_up,
                chart_title, chart_title_img, chart_up,
            )

    pool_data = await add_init_pool(pool_data)
    for server in SERVER_LIST:
        pool_data = await get_other_uma(pool_data, server)
    pool_data = await UP_modify(pool_data)

    with open(gacha_dir / "uma_pool.json", "w", encoding="utf-8") as f:
        json.dump(pool_data, f, ensure_ascii=False, indent=4)
