import json
import random
from pathlib import Path


MAX_GACHA = 200
INIT_FIRST_UP = 999999
UP_PROB_DEFAULT = 15
S3_PROB_DEFAULT = 30
S2_PROB_DEFAULT = 180
S1_PROB_DEFAULT = 790


class Gacha:
    def __init__(self, pool_id: str, gacha_type: str, server: str = "jp", gacha_dir: Path | None = None):
        self.server = server
        self.gacha_dir = gacha_dir
        self.pool = self.get_pool(pool_id, server, gacha_dir)
        self.result: dict[str, list] = {"up": [], "s3": [], "s2": [], "s1": []}
        self.first_up: int = INIT_FIRST_UP
        self.up_prob = UP_PROB_DEFAULT
        self.s3_prob = S3_PROB_DEFAULT
        self.s2_prob = S2_PROB_DEFAULT
        self.s1_prob = S1_PROB_DEFAULT

        high_rank = "3" if gacha_type == "uma" else "SSR"
        mid_rank = "2" if gacha_type == "uma" else "SR"
        low_rank = "1" if gacha_type == "uma" else "R"

        self.up = self.pool[f"{gacha_type}_up"][high_rank]
        self.star3 = self.pool[f"other_{gacha_type}"][high_rank]
        self.star2 = self.pool[f"other_{gacha_type}"][mid_rank]
        self.star1 = self.pool[f"other_{gacha_type}"][low_rank]

    @staticmethod
    def get_pool(pool_id: str, server: str, gacha_dir: Path | None = None) -> dict:
        pool_path = gacha_dir / "uma_pool.json"
        with open(pool_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        server_pool = config[server]
        if not pool_id:
            pool_id = list(server_pool.keys())[0]
        return server_pool[pool_id]

    def sort_result(self, i: int, first_up: int, result: dict, select: list[str] | None = None):
        select_chara = None
        if i % 10:
            chara, res_type = self.gacha_one(UP_PROB_DEFAULT, S3_PROB_DEFAULT, S2_PROB_DEFAULT, S1_PROB_DEFAULT)
        else:
            chara, res_type = self.gacha_one(UP_PROB_DEFAULT, S3_PROB_DEFAULT, S2_PROB_DEFAULT + S1_PROB_DEFAULT, 0)
        if res_type == "up":
            result["up"].append(chara)
            first_up = min(i, first_up)
            if select and chara in select:
                select_chara = chara
        else:
            result[res_type].append(chara)
        return first_up, result, select_chara

    def gacha_one(self, up_prob: int, s3_prob: int, s2_prob: int, s1_prob: int = 0) -> tuple[str, str]:
        pick = random.randint(1, s3_prob + s2_prob + s1_prob)
        if pick <= up_prob:
            return random.choice(self.up), "up"
        elif pick <= s3_prob:
            return random.choice(self.star3), "s3"
        elif pick <= s2_prob + s3_prob:
            return random.choice(self.star2), "s2"
        else:
            return random.choice(self.star1), "s1"

    def gacha_ten(self, result: dict, first_up: int) -> tuple[int, dict]:
        for i in range(1, 11):
            first_up, result, _ = self.sort_result(i, first_up, result)
        first_up = 0 if first_up == INIT_FIRST_UP else first_up
        return first_up, result

    def gacha_tenjou(self, result: dict, first_up: int) -> tuple[int, dict]:
        ten_gacha = MAX_GACHA // 10
        for j in range(ten_gacha):
            for i in range(1, 11):
                k = j * 10 + i
                first_up, result, _ = self.sort_result(k, first_up, result)
        first_up = 0 if first_up == INIT_FIRST_UP else first_up
        return first_up, result

    def gacha_full_singer(self, result: dict, first_up: int, chart_name_list: list[str]) -> tuple[dict, int, int, int, dict]:
        select_chart_list = chart_name_list if chart_name_list else [random.choice(self.up)]
        need_dict = {name: 0 for name in select_chart_list}
        ten_num, exchange = -1, 0
        while True:
            if all(v >= 5 for v in need_dict.values()):
                break
            ten_num += 1
            for i in range(1, 11):
                k = ten_num * 10 + i
                first_up, result, select_chara = self.sort_result(k, first_up, result, select_chart_list)
                if select_chara:
                    need_dict[select_chara] += 1
            if ten_num and not ten_num % (MAX_GACHA // 10):
                exchange += 1
                min_key = min(need_dict, key=need_dict.get)
                need_dict[min_key] += 1
        return need_dict, ten_num, exchange, first_up, result
