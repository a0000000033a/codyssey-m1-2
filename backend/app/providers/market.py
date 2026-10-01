"""Bounded HTTPS access to KIND company listings and NAVER daily history."""
from datetime import date, datetime, timezone
from io import StringIO
import math
import re
import xml.etree.ElementTree as ET

import httpx


def clean_listing(rows):
    result = {}
    for row in rows:
        code = str(row.get("Code", "")).zfill(6)
        sector = row.get("Sector")
        if row.get("Market") not in {"KOSPI", "KOSDAQ"} or not re.fullmatch(r"\d{6}", code):
            continue
        if not isinstance(sector, str) or not sector.strip():
            continue  # Corporate-list metadata excludes exchange-traded products.
        result[code] = {"market": "KR", "symbol": code, "name": str(row["Name"]), "exchange": row["Market"]}
    return list(result.values())


def clean_points(rows):
    result, excluded = {}, 0
    for row in rows:
        try:
            day = date.fromisoformat(str(row["date"])[:10]).isoformat()
            close, volume = float(row["close"]), float(row["volume"])
            if not math.isfinite(close) or close <= 0 or not math.isfinite(volume) or volume < 0:
                raise ValueError()
            if day in result:
                excluded += 1
            result[day] = dict(row, date=day, close=close, volume=volume)
        except (ValueError, TypeError, KeyError):
            excluded += 1
    return [result[key] for key in sorted(result)], excluded


class MarketProvider:
    def list_stocks(self):
        import pandas as pd
        result = []
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            for market, kind in [("KOSPI", "stockMkt"), ("KOSDAQ", "kosdaqMkt")]:
                response = client.get("https://kind.krx.co.kr/corpgeneral/corpList.do", params={"method": "download", "searchType": "13", "marketType": kind})
                response.raise_for_status()
                response.encoding = "euc-kr"
                frame = pd.read_html(StringIO(response.text), converters={"종목코드": str})[0]
                for row in frame.to_dict("records"):
                    result.append({"Code": row["종목코드"], "Name": row["회사명"], "Sector": row.get("업종"), "Market": market})
        stocks = clean_listing(result)
        if not stocks:
            raise ValueError("Empty company catalog")
        return stocks

    def history(self, symbol, start, end):
        response = httpx.get("https://fchart.stock.naver.com/sise.nhn", params={"timeframe": "day", "count": "600", "requestType": "0", "symbol": symbol}, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.content.decode("euc-kr"))
        rows = []
        for item in root.iter("item"):
            fields = item.attrib["data"].split("|")
            day = datetime.strptime(fields[0], "%Y%m%d").date()
            if start <= day <= end:
                rows.append({"date": day.isoformat(), "close": fields[4], "volume": fields[5]})
        if not rows:
            raise ValueError("No daily history")
        return rows
