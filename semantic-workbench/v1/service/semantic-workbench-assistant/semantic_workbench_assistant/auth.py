import logging
import secrets

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from semantic_workbench_api_model import assistant_service_client
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from . import settings

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, exclude_methods: set[str] = set(), exclude_paths: set[str] = set()) -> None:
        super().__init__(app)
        self.exclude_methods = exclude_methods
        self.exclude_routes = exclude_paths

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in self.exclude_methods:
            return await call_next(request)

        if request.url.path in self.exclude_routes:
            return await call_next(request)

        try:
            await _require_api_key(request)

        except HTTPException as exc:
            # if the authorization header is invalid, return the error response
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception:
            logger.exception("error validating authorization header")
            # return a generic error response
            return Response(status_code=500)

        return await call_next(request)


async def _require_api_key(request: Request) -> None:
    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

    params = assistant_service_client.AuthParams.from_request_headers(request.headers)
    api_key = params.api_key
    if not api_key:
        if settings.workbench_service_api_key:
            raise invalid_credentials_error
        return

    password_bytes = api_key.encode("utf8")
    correct_password_bytes = settings.workbench_service_api_key.encode("utf8")
    is_correct_password = secrets.compare_digest(password_bytes, correct_password_bytes)

    if not is_correct_password:
        raise invalid_credentials_error
