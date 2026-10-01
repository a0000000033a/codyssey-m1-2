from datetime import date, datetime, timedelta, timezone
from threading import Lock
from zoneinfo import ZoneInfo

from ..core.errors import ApiError
from ..providers.market import clean_points
from .paging import page


def now():
    return datetime.now(timezone.utc).isoformat()


def is_fresh(stamp):
    return bool(stamp) and datetime.now(timezone.utc) - datetime.fromisoformat(stamp) < timedelta(hours=24)


class StockService:
    def __init__(self, repo, provider):
        self.repo, self.provider = repo, provider
        self.lock = Lock()

    def catalog(self):
        with self.lock:
            state = self.repo.get("sync_state", "catalog") or {}
            stocks = self.repo.list("stocks")
            if stocks and is_fresh(state.get("last_success_at")):
                return stocks
            try:
                stocks = self.provider.list_stocks()
                self.repo.batch_put("stocks", [(s["symbol"], dict(s, refreshed_at=now())) for s in stocks])
                current = {s["symbol"] for s in stocks}
                for old in self.repo.list("stocks"):
                    if old["symbol"] not in current:
                        self.repo.delete("stocks", old["id"])
                self.repo.put("sync_state", "catalog", {"last_success_at": now()})
                return stocks
            except Exception:
                if stocks:
                    return stocks
                raise ApiError(502, "catalog_unavailable", "종목 목록을 가져오지 못했습니다. 잠시 후 재시도해주세요.") from None

    def search(self, q="", cursor=None, limit=30):
        rows = [s for s in self.catalog() if q.casefold() in s["name"].casefold() or q in s["symbol"]]
        return page(sorted(rows, key=lambda x: x["symbol"]), cursor, limit, f"stocks:{q}", "symbol")

    def require_stock(self, symbol):
        stock = next((s for s in self.catalog() if s["symbol"] == symbol), None)
        if not stock:
            raise ApiError(404, "stock_not_found", "지원하는 국내 종목을 선택해주세요.")
        return stock

    def register(self, uid, symbol):
        stock = self.require_stock(symbol)
        id = f"{uid}_KR_{symbol}"
        old = self.repo.get("watchlist", id)
        if old:
            return dict(old, id=id)
        row = dict(stock, owner_uid=uid, created_at=now())
        row.pop("id", None)
        self.repo.put("watchlist", id, row)
        return dict(row, id=id)

    def watchlist(self, uid):
        return {"items": self.repo.list("watchlist", {"owner_uid": uid}), "next_cursor": None}

    def remove(self, uid, id):
        row = self.repo.get("watchlist", id)
        if not row or row.get("owner_uid") != uid:
            raise ApiError(404, "not_found", "관심 종목을 찾을 수 없습니다.")
        self.repo.delete("watchlist", id)

    def refresh(self, symbol, force=False):
        self.require_stock(symbol)
        with self.lock:
            id = f"KR_{symbol}"
            state = self.repo.get("sync_state", id) or {}
            if not force and is_fresh(state.get("last_success_at")):
                return dict(state, stale=False)
            excluded, error_kind = None, "fetch"
            try:
                end = datetime.now(ZoneInfo("Asia/Seoul")).date()
                start = end - timedelta(days=365)
                points, excluded = clean_points(self.provider.history(symbol, start, end))
                if not points:
                    error_kind = "validation"
                    raise ValueError("Empty validated data")
                stamp = now()
                self.repo.batch_put("market_data", [(f"KR_{symbol}_{p['date']}", dict(p, market="KR", symbol=symbol, source="NAVER", fetched_at=stamp)) for p in points])
                state = {"last_success_at": stamp, "last_error": None, "error_kind": None, "excluded_count": excluded, "source": "NAVER", "adjustment": "출처의 가격 조정 여부를 확인하지 못했습니다."}
                self.repo.put("sync_state", id, state)
                return dict(state, stale=False)
            except Exception:
                state["error_kind"] = error_kind
                if excluded is not None:
                    state["excluded_count"] = excluded
                state["last_error"] = ("수신한 시장 데이터에 유효한 가격이 없습니다. 저장된 데이터를 표시합니다." if error_kind == "validation" else "최근 데이터 조회 또는 저장에 실패했습니다. 저장된 데이터를 표시합니다.")
                self.repo.put("sync_state", id, state)
                if not self.repo.list("market_data", {"symbol": symbol, "market": "KR"}):
                    code = "market_invalid_data" if error_kind == "validation" else "market_unavailable"
                    message = "수신한 시장 데이터에 유효한 가격이 없습니다." if error_kind == "validation" else "시장 데이터를 가져오지 못했습니다. 잠시 후 재시도해주세요."
                    raise ApiError(502, code, message) from None
                return dict(state, stale=True)
