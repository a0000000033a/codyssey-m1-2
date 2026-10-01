from datetime import datetime, timedelta
from decimal import Decimal
from statistics import mean
from zoneinfo import ZoneInfo


def calculate_summary(points, records, sync):
    points = sorted(points, key=lambda x: x["date"])
    prices = [float(p["close"]) for p in points]
    volumes = [float(p["volume"]) for p in points]
    change, direction = None, "insufficient"
    if len(prices) >= 40:
        previous = sum(Decimal(str(p)) for p in prices[-40:-20]) / 20
        recent = sum(Decimal(str(p)) for p in prices[-20:]) / 20
        ratio = (recent - previous) / previous * 100
        direction = "up" if ratio > 1 else "down" if ratio < -1 else "stable"
        change = round(float(ratio), 4)
    market = {"count": len(prices), "start": points[0]["date"] if points else None,
              "end": points[-1]["date"] if points else None, "average_close": mean(prices) if prices else None,
              "max_close": max(prices) if prices else None, "min_close": min(prices) if prices else None,
              "last_close": prices[-1] if prices else None, "average_volume": mean(volumes) if volumes else None,
              "last_volume": volumes[-1] if volumes else None,
              "trend": {"direction": direction, "change_percent": change, "method": "최근 20거래일과 직전 20거래일 평균 종가 비교"}}
    recent_records = sorted(records, key=lambda x: (x["date"], x.get("created_at", "")), reverse=True)[:20]
    return {"market_data": market, "personal_records": {"count": len(records), "recent": [{k: r[k] for k in ("date", "value", "memo")} for r in recent_records]},
            "quality": {"insufficient_sample": len(prices) < 100, "stale": bool(sync.get("last_error")),
                        "message": sync.get("last_error"), "source": sync.get("source", "NAVER"),
                        "fetched_at": sync.get("last_success_at"), "excluded_count": sync.get("excluded_count", 0),
                        "adjustment": sync.get("adjustment", "가격 조정 여부를 확인하지 못했습니다.")}}


class SummaryService:
    def __init__(self, repo, stocks):
        self.repo, self.stocks = repo, stocks

    def get(self, uid, symbol):
        stock = self.stocks.require_stock(symbol)
        sync = self.stocks.refresh(symbol)
        end = datetime.now(ZoneInfo("Asia/Seoul")).date()
        start = (end - timedelta(days=365)).isoformat()
        points = [p for p in self.repo.list("market_data", {"market": "KR", "symbol": symbol}) if start <= p["date"] <= end.isoformat()]
        records = self.repo.list("data", {"owner_uid": uid, "symbol": symbol})
        result = calculate_summary(points, records, sync)
        result["stock"] = {k: stock[k] for k in ("market", "symbol", "name", "exchange")}
        return result
