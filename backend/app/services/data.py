from uuid import uuid4
from ..core.errors import ApiError
from .stocks import now
from .paging import page


def owned(repo, collection, uid, id):
    row = repo.get(collection, id)
    if not row or row.get("owner_uid") != uid:
        raise ApiError(404, "not_found", "항목을 찾을 수 없습니다.")
    return dict(row, id=id)


class DataService:
    def __init__(self, repo, stocks):
        self.repo, self.stocks = repo, stocks

    def create(self, uid, payload):
        self.stocks.require_stock(payload.symbol)
        id = uuid4().hex
        stamp = now()
        row = dict(payload.model_dump(mode="json"), owner_uid=uid, market="KR", created_at=stamp, updated_at=stamp)
        self.repo.put("data", id, row)
        return dict(row, id=id)

    def list(self, uid, symbol, cursor=None, limit=30):
        rows = self.repo.list("data", {"owner_uid": uid, "symbol": symbol})
        rows.sort(key=lambda x: (x["date"], x["created_at"], x["id"]), reverse=True)
        return page(rows, cursor, limit, f"data:{uid}:{symbol}")

    def update(self, uid, id, payload):
        row = owned(self.repo, "data", uid, id)
        if row["symbol"] != payload.symbol:
            raise ApiError(400, "symbol_mismatch", "기록의 종목을 변경할 수 없습니다.")
        row.update(payload.model_dump(mode="json"), updated_at=now())
        row.pop("id")
        self.repo.put("data", id, row)
        return dict(row, id=id)

    def delete(self, uid, id):
        owned(self.repo, "data", uid, id)
        self.repo.delete("data", id)
