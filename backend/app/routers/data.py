from fastapi import APIRouter, Depends, Query, Response
from ..core.auth import require_owner
from ..core.dependencies import get_services
from ..schemas.data import RecordInput
from ..schemas.stocks import Symbol

router = APIRouter(prefix="/api/data", tags=["데이터"])


@router.get("/summary")
def summary(symbol: Symbol, uid=Depends(require_owner), services=Depends(get_services)):
    return services.summary.get(uid, symbol)


@router.get("")
def list_records(symbol: Symbol, cursor: str | None = Query(None, max_length=512), limit: int = Query(30, ge=1, le=100), uid=Depends(require_owner), services=Depends(get_services)):
    return services.data.list(uid, symbol, cursor, limit)


@router.post("", status_code=201)
def create(payload: RecordInput, uid=Depends(require_owner), services=Depends(get_services)):
    return services.data.create(uid, payload)


@router.put("/{id}")
def update(id: str, payload: RecordInput, uid=Depends(require_owner), services=Depends(get_services)):
    return services.data.update(uid, id, payload)


@router.delete("/{id}", status_code=204)
def delete(id: str, uid=Depends(require_owner), services=Depends(get_services)):
    services.data.delete(uid, id)
    return Response(status_code=204)
