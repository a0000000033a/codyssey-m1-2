"""TEST-ONLY browser fixture. Never deploy this module."""
from datetime import date, timedelta
from types import SimpleNamespace
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import create_app
from app.core.config import Settings
from app.services.stocks import StockService
from app.services.data import DataService
from app.services.summary import SummaryService
from app.services.conversations import ConversationService
from app.services.chat import ChatService
from fakes import MemoryRepository, FakeMarket, FakeAI


class PreviewMarket(FakeMarket):
    def history(self, symbol, start, end):
        return [{"date": (end-timedelta(days=120-i)).isoformat(), "close": 50000+i*100, "volume": 1000+i*5} for i in range(120)]


repo = MemoryRepository()
stocks = StockService(repo, PreviewMarket())
settings = Settings(allowed_user_uid="browser-test")
services = SimpleNamespace(repo=repo, stocks=stocks, data=DataService(repo, stocks), summary=SummaryService(repo, stocks), conversations=ConversationService(repo, stocks), ai=FakeAI())
services.chat = ChatService(repo, services.summary, services.conversations, services.ai, settings)
app = create_app(settings, services, lambda token: {"uid": token})
