from copy import deepcopy
from threading import RLock


class MemoryRepository:
    """Only external persistence is replaced; service logic stays real."""
    def __init__(self):
        self.documents = {}
        self.lock = RLock()

    def get(self, collection, id):
        return deepcopy(self.documents.get((collection, id)))

    def put(self, collection, id, value):
        self.documents[collection, id] = deepcopy(value)

    def delete(self, collection, id):
        self.documents.pop((collection, id), None)

    def list(self, collection, filters=None):
        return [dict(deepcopy(v), id=id) for (c, id), v in self.documents.items() if c == collection and all(v.get(k) == x for k, x in (filters or {}).items())]

    def batch_put(self, collection, rows):
        for id, row in rows:
            self.put(collection, id, row)

    def atomic(self, callback):
        with self.lock:
            before = deepcopy(self.documents)
            try:
                return callback(self)
            except Exception:
                self.documents = before
                raise


class FakeMarket:
    def __init__(self):
        self.calls = 0
        self.fail = False

    def list_stocks(self):
        return [{"market": "KR", "symbol": "005930", "name": "삼성전자", "exchange": "KOSPI"}, {"market": "KR", "symbol": "000660", "name": "SK하이닉스", "exchange": "KOSPI"}]

    def history(self, symbol, start, end):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider unavailable")
        return [{"date": "2026-09-28", "close": 100, "volume": 0}, {"date": "2026-09-29", "close": 200, "volume": 10}]


class FakeAI:
    def __init__(self):
        self.calls, self.fail, self.on_answer = 0, False, None

    def answer(self, context):
        self.calls += 1
        if self.fail:
            raise TimeoutError()
        if self.on_answer:
            self.on_answer()
        return "저장된 데이터의 평균 종가는 150원입니다. 표본이 부족합니다."
