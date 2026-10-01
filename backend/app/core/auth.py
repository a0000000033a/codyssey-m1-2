import json
from threading import Lock

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .errors import ApiError

bearer = HTTPBearer(auto_error=False)
_init_lock = Lock()


def firebase_app(settings):
    import firebase_admin
    from firebase_admin import credentials
    with _init_lock:
        try:
            return firebase_admin.get_app()
        except ValueError:
            raw = settings.firebase_service_account_json.get_secret_value()
            path = settings.google_application_credentials
            if not raw and not path:
                raise ApiError(503, "configuration_required", "Firebase 서버 설정이 필요합니다.")
            try:
                credential = credentials.Certificate(json.loads(raw) if raw else path)
                return firebase_admin.initialize_app(credential)
            except (ValueError, OSError, TypeError):
                raise ApiError(503, "configuration_required", "Firebase 서버 설정을 확인해주세요.") from None


def verify_firebase_token(token, settings):
    from firebase_admin import auth
    return auth.verify_id_token(token, app=firebase_app(settings), check_revoked=True)


def require_owner(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if not credentials:
        raise ApiError(401, "authentication_required", "로그인이 필요합니다.")
    settings = request.app.state.settings
    if not settings.allowed_user_uid:
        raise ApiError(503, "configuration_required", "허용 계정 설정이 필요합니다.")
    verifier = request.app.state.token_verifier
    try:
        claims = verifier(credentials.credentials) if verifier else verify_firebase_token(credentials.credentials, settings)
    except ApiError:
        raise
    except Exception:
        raise ApiError(401, "invalid_token", "로그인을 다시 진행해주세요.") from None
    if claims.get("uid") != settings.allowed_user_uid:
        raise ApiError(403, "access_denied", "허용된 계정만 사용할 수 있습니다.")
    return claims["uid"]
