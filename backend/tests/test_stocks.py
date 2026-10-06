from datetime import datetime, timedelta, timezone
import pytest
from fakes import FakeMarket, MemoryRepository


def stock_service():
    from app.services.stocks import StockService
    repo, provider = MemoryRepository(), FakeMarket()
    return StockService(repo, provider), repo, provider


def test_watchlist_is_idempotent_and_symbol_keeps_zero():
    service, repo, _ = stock_service()
    first = service.register("owner", "005930")
    second = service.register("owner", "005930")
    assert first["id"] == second["id"]
    assert first["symbol"] == "005930"
    assert len(repo.list("watchlist")) == 1


def test_fresh_cache_and_failed_refresh_keep_saved_points():
    service, repo, provider = stock_service()
    service.refresh("005930")
    service.refresh("005930")
    assert provider.calls == 1
    assert repo.list("market_data")[0]["volume"] == 0
    state = repo.get("sync_state", "KR_005930")
    state["last_success_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    repo.put("sync_state", "KR_005930", state)
    provider.fail = True
    result = service.refresh("005930")
    assert result["stale"] is True
    assert len(repo.list("market_data")) == 2


def test_clean_points_drop_invalid_and_deduplicate():
    from app.providers.market import clean_points
    points, excluded = clean_points([
        {"date": "2026-09-01", "close": 100, "volume": 0},
        {"date": "2026-09-01", "close": 200, "volume": 3},
        {"date": "2026-09-02", "close": float("nan"), "volume": 1},
        {"date": "2026-09-03", "close": float("inf"), "volume": 1},
        {"date": "2026-09-04", "close": 100, "volume": -1},
    ])
    assert points[0]["close"] == 200
    assert len(points) == 1
    assert excluded == 4


def test_search_cursor_rejects_different_filter_and_invalid_cursor():
    from app.core.errors import ApiError
    service, _, _ = stock_service()
    page = service.search("", None, 1)
    assert page["next_cursor"]
    with pytest.raises(ApiError):
        service.search("삼성", page["next_cursor"], 1)
    with pytest.raises(ApiError):
        service.search("", "not-a-cursor", 1)


def test_listing_excludes_other_markets_and_products():
    from app.providers.market import clean_listing
    rows = [{"Code": "005930", "Name": "삼성전자", "Market": "KOSPI", "Sector": "반도체"},
            {"Code": "123456", "Name": "ETF", "Market": "KOSPI", "Sector": None},
            {"Code": "123457", "Name": "코넥스", "Market": "KONEX", "Sector": "제조"}]
    assert [r["symbol"] for r in clean_listing(rows)] == ["005930"]


def test_naver_euc_kr_xml_can_be_read(monkeypatch):
    import httpx
    from datetime import date
    from app.providers.market import MarketProvider
    body = '<?xml version="1.0" encoding="EUC-KR"?><protocol><chartdata name="삼성전자"><item data="20260901|1|2|1|100|0" /></chartdata></protocol>'
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, content=body.encode("euc-kr"), request=httpx.Request("GET", "https://test")))
    points = MarketProvider().history("005930", date(2026, 9, 1), date(2026, 9, 1))
    assert points[0]["close"] == "100"


def test_invalid_refresh_retains_quality_reason_and_exclusion_count():
    from app.core.errors import ApiError
    service, repo, provider = stock_service()
    provider.history = lambda *args: [{"date": "2026-09-01", "close": float("nan"), "volume": 1}]
    with pytest.raises(ApiError) as failure:
        service.refresh("005930")
    assert failure.value.code == "market_invalid_data"
    state = repo.get("sync_state", "KR_005930")
    assert state["error_kind"] == "validation"
    assert state["excluded_count"] == 1
    repo.put("market_data", "saved", {"symbol": "005930", "market": "KR", "date": "2026-09-01", "close": 100, "volume": 0})
    result = service.refresh("005930")
    assert result["stale"] is True
    assert result["error_kind"] == "validation"
    assert result["excluded_count"] == 1
    assert repo.get("market_data", "saved")["close"] == 100


def test_repeated_search_and_validation_do_not_reread_catalog():
    service, repo, _ = stock_service()
    service.catalog()
    reads = []
    original_get, original_list = repo.get, repo.list
    repo.get = lambda *args: (reads.append(args[0]), original_get(*args))[1]
    repo.list = lambda *args, **kwargs: (reads.append(args[0]), original_list(*args, **kwargs))[1]
    for _ in range(50):
        assert service.search('삼성')['items'][0]['symbol'] == '005930'
        service.require_stock('000660')
    assert reads == []


def test_warm_search_does_not_wait_for_price_refresh():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    service, _, provider = stock_service()
    service.catalog()
    started, release = Event(), Event()
    history = provider.history
    def slow_history(*args):
        started.set()
        assert release.wait(3)
        return history(*args)
    provider.history = slow_history
    with ThreadPoolExecutor(max_workers=2) as pool:
        refresh = pool.submit(service.refresh, '005930')
        assert started.wait(1)
        search = pool.submit(service.search, '삼성')
        try:
            assert search.result(timeout=.5)['items'][0]['symbol'] == '005930'
        finally:
            release.set()
        refresh.result(timeout=2)


def test_expired_catalog_refreshes_and_cached_rows_cannot_be_mutated(monkeypatch):
    import app.services.stocks as module
    clock = [0]
    monkeypatch.setattr(module, 'monotonic', lambda: clock[0])
    service, repo, provider = stock_service()
    rows = service.catalog()
    rows[0]['name'] = 'tampered'
    assert service.require_stock('005930')['name'] == '삼성전자'
    clock[0] = 86401
    repo.put('sync_state', 'catalog', {'last_success_at': (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()})
    provider.list_stocks = lambda: [{'market': 'KR', 'symbol': '005930', 'name': '갱신된 이름', 'exchange': 'KOSPI'}]
    assert service.require_stock('005930')['name'] == '갱신된 이름'
