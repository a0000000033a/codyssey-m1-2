from fastapi import APIRouter, Depends, Query, Response
from ..core.auth import require_owner
from ..core.dependencies import get_services
from ..schemas.stocks import StockInput, Symbol

router = APIRouter(prefix="/api", tags=["종목"], dependencies=[Depends(require_owner)])


@router.get("/stocks")
def search(q: str = Query(default="", max_length=80), cursor: str | None = Query(None, max_length=512), limit: int = Query(30, ge=1, le=100), services=Depends(get_services)):
    return services.stocks.search(q.strip(), cursor, limit)


@router.post("/stocks/{symbol}/refresh")
def refresh(symbol: Symbol, services=Depends(get_services)):
    return services.stocks.refresh(symbol, force=True)


@router.get("/watchlist")
def watchlist(uid=Depends(require_owner), services=Depends(get_services)):
    return services.stocks.watchlist(uid)


@router.post("/watchlist", status_code=201)
def register(payload: StockInput, uid=Depends(require_owner), services=Depends(get_services)):
    return services.stocks.register(uid, payload.symbol)


@router.delete("/watchlist/{id}", status_code=204)
def remove(id: str, uid=Depends(require_owner), services=Depends(get_services)):
    services.stocks.remove(uid, id)
    return Response(status_code=204)
