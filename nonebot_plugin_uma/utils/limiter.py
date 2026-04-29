import time
from datetime import datetime, timedelta


class FreqLimiter:
    def __init__(self, default_cd_seconds: int = 10):
        self._cd = default_cd_seconds
        self._last_call: dict[str, float] = {}

    def check(self, key: str) -> bool:
        now = time.time()
        last = self._last_call.get(key, 0)
        return now - last >= self._cd

    def start_cd(self, key: str):
        self._last_call[key] = time.time()

    def left_time(self, key: str) -> float:
        now = time.time()
        last = self._last_call.get(key, 0)
        return max(0.0, self._cd - (now - last))


class DailyNumberLimiter:
    def __init__(self, max_num: int = 30000, reset_hour: int = 5):
        self.max = max_num
        self._reset_hour = reset_hour
        self._data: dict[str, tuple[int, datetime]] = {}

    def _get_reset_time(self) -> datetime:
        now = datetime.now()
        reset = now.replace(hour=self._reset_hour, minute=0, second=0, microsecond=0)
        if now < reset:
            reset -= timedelta(days=1)
        return reset

    def check(self, key: str) -> bool:
        if key not in self._data:
            return True
        count, ts = self._data[key]
        if datetime.now() >= self._get_reset_time() + timedelta(days=1):
            return True
        if ts < self._get_reset_time():
            return True
        return count < self.max

    def increase(self, key: str, num: int = 1):
        now = datetime.now()
        if key not in self._data:
            self._data[key] = (num, now)
        else:
            count, ts = self._data[key]
            if ts < self._get_reset_time():
                self._data[key] = (num, now)
            else:
                self._data[key] = (count + num, now)
