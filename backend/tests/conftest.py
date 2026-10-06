from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from fakes import FakeMarket, FakeAI, MemoryRepository


@pytest.fixture
def api():
    from app.core.config import Settings
    from app.main import create_app
    from app.services.stocks import StockService
    from app.services.data import DataService
    from app.services.summary import SummaryService
    from app.services.conversations import ConversationService
    from app.services.chat import ChatService
    repo = MemoryRepository()
    stocks = StockService(repo, FakeMarket())
    services = SimpleNamespace(repo=repo, stocks=stocks, data=DataService(repo, stocks), summary=SummaryService(repo, stocks), conversations=ConversationService(repo, stocks))
    settings = Settings(allowed_user_uid="owner")
    services.ai = FakeAI()
    services.chat = ChatService(repo, services.summary, services.conversations, services.ai, settings)
    app = create_app(settings, services, lambda token: {"uid": token})
    client = TestClient(app)
    client.headers["Authorization"] = "Bearer owner"
    return client, services
