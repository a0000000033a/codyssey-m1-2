"""Public-data probe, no private credentials required."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.providers.market import MarketProvider, clean_points

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", required=True)
args = parser.parse_args()
provider = MarketProvider()
end = datetime.now(ZoneInfo("Asia/Seoul")).date()
points, excluded = clean_points(provider.history(args.symbol, end - timedelta(days=365), end))
stocks = provider.list_stocks()
print(json.dumps({"symbol": args.symbol, "count": len(points), "start": points[0]["date"], "end": points[-1]["date"], "excluded": excluded, "catalog_count": len(stocks), "listed": any(s["symbol"] == args.symbol for s in stocks)}, ensure_ascii=False))
if len(points) < 100:
    raise SystemExit(1)
