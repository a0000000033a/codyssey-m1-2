from datetime import date, timedelta
import pytest


def points(prices):
    return [{"date": (date(2026, 1, 1)+timedelta(days=i)).isoformat(), "close": v, "volume": i} for i, v in enumerate(prices)]


def test_personal_price_is_not_market_price():
    from app.services.summary import calculate_summary
    result = calculate_summary(points([100, 200]), [{"date": "2026-01-01", "value": 999, "memo": "개인 가격"}], {})
    assert result["market_data"]["average_close"] == 150
    assert result["personal_records"]["count"] == 1


@pytest.mark.parametrize("prices,want", [([], "insufficient"), ([100]*39, "insufficient"), ([100]*20+[101]*20, "stable"), ([100]*20+[99]*20, "stable"), ([100]*20+[102]*20, "up"), ([100]*20+[98]*20, "down")])
def test_trend_boundaries(prices, want):
    from app.services.summary import calculate_summary
    summary = calculate_summary(points(prices), [], {})
    assert summary["market_data"]["trend"]["direction"] == want
    assert summary["quality"]["insufficient_sample"] is True
    if not prices:
        assert summary["market_data"]["average_close"] is None


def test_summary_limits_recent_records_and_checks_sample():
    from app.services.summary import calculate_summary
    records = [{"date": "2026-09-01", "value": i+1, "memo": str(i), "created_at": str(i).zfill(2)} for i in range(25)]
    summary = calculate_summary(points([100]*100), records, {"last_error": "갱신 실패", "excluded_count": 2})
    assert summary["quality"]["insufficient_sample"] is False
    assert summary["quality"]["stale"] is True
    assert summary["quality"]["excluded_count"] == 2
    assert len(summary["personal_records"]["recent"]) == 20
    assert summary["personal_records"]["recent"][0]["value"] == 25
