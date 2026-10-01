import base64
import hashlib
import json
from ..core.errors import ApiError


def page(rows, cursor, limit, scope, key="id"):
    fingerprint = hashlib.sha256(scope.encode()).hexdigest()[:16]
    if cursor:
        try:
            decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if decoded["scope"] != fingerprint or not isinstance(decoded["last"], str):
                raise ValueError()
            position = next(i for i, row in enumerate(rows) if row[key] == decoded["last"])
            rows = rows[position+1:]
        except (ValueError, KeyError, StopIteration, TypeError, UnicodeError):
            raise ApiError(400, "invalid_cursor", "목록을 새로 불러와주세요.") from None
    result = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        next_cursor = base64.urlsafe_b64encode(json.dumps({"scope": fingerprint, "last": result[-1][key]}).encode()).decode()
    return {"items": result, "next_cursor": next_cursor}
