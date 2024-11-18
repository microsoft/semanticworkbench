import logging
import secrets
import time
from functools import lru_cache
from typing import Any, Awaitable, Callable

import httpx
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, jwt
from semantic_workbench_api_model import workbench_service_client
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from . import auth, settings

logger = logging.getLogger(__name__)


_unauthorized_assistant_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
)


async def _assistant_service_principal_from_request(
    request: Request,
    api_key_source: Callable[[str], Awaitable[str | None]],
) -> auth.AssistantServicePrincipal | None:
    assistant_service_params = workbench_service_client.AssistantServiceRequestHeaders.from_headers(request.headers)
    if not assistant_service_params.assistant_service_id:
        return None

    assistant_service_id = assistant_service_params.assistant_service_id
    api_key = assistant_service_params.api_key

    assistant_instance_params = workbench_service_client.AssistantInstanceRequestHeaders.from_headers(request.headers)
    assistant_id = assistant_instance_params.assistant_id

    expected_api_key = await api_key_source(assistant_service_id)
    if expected_api_key is None:
        logger.info(
            "assistant service authentication failed; assistant_service_id: %s, error: api key not found in store",
            assistant_service_id,
        )
        raise _unauthorized_assistant_exception

    current_password_bytes = api_key.encode("utf8")
    correct_password_bytes = expected_api_key.encode("utf8")
    is_correct_password = secrets.compare_digest(current_password_bytes, correct_password_bytes)

    if not is_correct_password:
        logger.info(
            "assistant service authentication failed; assistant_service_id: %s, error: api key mismatch",
            assistant_service_id,
        )
        raise _unauthorized_assistant_exception

    if assistant_id:
        return auth.AssistantPrincipal(assistant_service_id=assistant_service_id, assistant_id=assistant_id)

    return auth.AssistantServicePrincipal(assistant_service_id=assistant_service_id)


async def _user_principal_from_request(request: Request) -> auth.UserPrincipal | None:
    token = await OAuth2PasswordBearer(tokenUrl="token", auto_error=False)(request)
    if token is None:
        return None

    allowed_jwt_algorithms = settings.auth.allowed_jwt_algorithms

    try:
        algorithm: str = jwt.get_unverified_header(token).get("alg") or ""

        match algorithm:
            case "RS256":
                keys = _get_rs256_jwks()
            case _:
                keys = ""

        decoded = jwt.decode(
            token,
            algorithms=allowed_jwt_algorithms,
            key=keys,
            options={"verify_signature": False, "verify_aud": False},
        )
        app_id: str = decoded.get("appid", "")
        tid: str = decoded.get("tid", "")
        oid: str = decoded.get("oid", "")
        name: str = decoded.get("name", "")
        user_id = f"{tid}.{oid}"

    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired token")

    except Exception:
        logger.exception("error decoding token", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if algorithm not in allowed_jwt_algorithms:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token algorithm")

    if app_id != settings.auth.allowed_app_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid app")

    return auth.UserPrincipal(user_id=user_id, name=name)


async def principal_from_request(
    request: Request,
    api_key_source: Callable[[str], Awaitable[str | None]],
) -> auth.Principal | None:
    assistant_principal = await _assistant_service_principal_from_request(request, api_key_source=api_key_source)
    if assistant_principal is not None:
        return assistant_principal

    user_principal = await _user_principal_from_request(request)
    if user_principal is not None:
        return user_principal

    return None


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        api_key_source: Callable[[str], Awaitable[str | None]],
        exclude_methods: set[str] = set(),
        exclude_paths: set[str] = set(),
    ) -> None:
        super().__init__(app)
        self.exclude_methods = exclude_methods
        self.exclude_routes = exclude_paths
        self.api_key_source = api_key_source

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in self.exclude_methods:
            return await call_next(request)

        if request.url.path in self.exclude_routes:
            return await call_next(request)

        try:
            principal = await principal_from_request(request, api_key_source=self.api_key_source)

            if principal is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        except HTTPException as exc:
            # if the authorization header is invalid, return the error response
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception:
            logger.exception("error validating authorization header")
            # return a generic error response
            return Response(status_code=500)

        auth.authenticated_principal.set(principal)
        return await call_next(request)


def ttl_lru_cache(seconds_to_live: int, maxsize: int = 128):
    """
    Time aware lru caching
    """

    def wrapper(func):
        @lru_cache(maxsize)
        def inner(__ttl, *args, **kwargs):
            # Note that __ttl is not passed down to func,
            # as it's only used to trigger cache miss after some time
            return func(*args, **kwargs)

        return lambda *args, **kwargs: inner(time.time() // seconds_to_live, *args, **kwargs)

    return wrapper


@ttl_lru_cache(seconds_to_live=60 * 10)
def _get_rs256_jwks() -> dict[str, Any]:
    response = httpx.Client().get("https://login.microsoftonline.com/common/discovery/v2.0/keys")
    return response.json()
