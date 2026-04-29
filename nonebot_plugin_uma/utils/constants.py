import datetime

SERVER_DATA = {
    "jp": "2021-02-24",
    "tw": "2022-06-29",
    "ko": "2022-06-20",
    "bili": "2023-08-29",
}

SERVER_LIST = list(SERVER_DATA.keys())


def get_differ(server_a: str, server_b: str) -> int:
    a_time = datetime.datetime.strptime(SERVER_DATA[server_a], "%Y-%m-%d")
    b_time = datetime.datetime.strptime(SERVER_DATA[server_b], "%Y-%m-%d")
    return (a_time - b_time).days


def get_correspond(server_a: str, server_b: str, pool_id: str) -> str:
    if pool_id == "00000000":
        return pool_id
    differ = get_differ(server_a, server_b)
    year, month, day = pool_id[:4], pool_id[4:6], pool_id[6:8]
    a_time = datetime.datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
    b_time = a_time - datetime.timedelta(days=differ)
    return str(b_time).replace("-", "")[:8]
