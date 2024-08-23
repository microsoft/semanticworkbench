import uuid

import fastapi
from fastapi.testclient import TestClient
from jose import jwt
from semantic_workbench_service import assistant_api_key, middleware
from tests.types import MockUser


def api_key_source(initial_api_key: str = ""):
    async def source(assistant_service_id: str) -> str | None:
        return await assistant_api_key.FixedApiKeyStore(initial_api_key).get(assistant_service_id)

    return source


async def test_auth_middleware_rejects_disallowed_algo():
    tid = str(uuid.uuid4())
    token = jwt.encode(
        claims={
            "tid": tid,
        },
        key="",
        algorithm="HS256",
    )

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/", headers={"Authorization": f"Bearer {token}"})

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "invalid token algorithm"


def test_auth_middleware_rejects_disallowed_app_id(monkeypatch):
    algo = "HS256"

    monkeypatch.setattr(middleware, "allowed_app_ids", {})
    monkeypatch.setattr(middleware, "allowed_algorithms", {algo})

    token = jwt.encode(
        claims={
            "appid": "not allowed",
        },
        key="",
        algorithm=algo,
    )

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/", headers={"Authorization": f"Bearer {token}"})

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "invalid app"


def test_auth_middleware_rejects_missing_authorization_header():
    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/")

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "not authenticated"


def test_auth_middleware_accepts_valid_user(test_user: MockUser):
    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source())

    with TestClient(app) as client:
        http_response = client.get("/", headers=test_user.authorization_headers)

        assert http_response.status_code == 404


def test_auth_middleware_accepts_valid_assistant_service():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source(test_api_key))

    valid_assistant_service_id = uuid.uuid4().hex
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": valid_assistant_service_id,
                "X-API-Key": test_api_key,
            },
        )

        assert http_response.status_code == 404


def test_auth_middleware_rejects_invalid_assistant_api_key():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source(test_api_key))

    valid_assistant_service_id = uuid.uuid4().hex
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": valid_assistant_service_id,
                "X-API-Key": "incorrect key",
            },
        )

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "invalid credentials"


def test_auth_middleware_rejects_invalid_assistant_service_id():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source(test_api_key))

    invalid_assistant_service_id = ""
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": invalid_assistant_service_id,
                "X-API-Key": test_api_key,
            },
        )

        assert http_response.status_code == 401
        assert http_response.json()["detail"].lower() == "not authenticated"


def test_auth_middleware_accepts_valid_assistant():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_middleware(middleware.AuthMiddleware, api_key_source=api_key_source(test_api_key))

    valid_assistant_service_id = uuid.uuid4().hex
    valid_assistant_id = uuid.uuid4()
    with TestClient(app) as client:
        http_response = client.get(
            "/",
            headers={
                "X-Assistant-Service-ID": valid_assistant_service_id,
                "X-Assistant-ID": str(valid_assistant_id),
                "X-API-Key": test_api_key,
            },
        )

        assert http_response.status_code == 404


def test_auth_middleware_allows_anonymous_excluded_paths():
    test_api_key = uuid.uuid4().hex

    app = fastapi.FastAPI()
    app.add_route("/", route=lambda r: fastapi.Response(status_code=200))
    app.add_middleware(
        middleware.AuthMiddleware,
        api_key_source=api_key_source(test_api_key),
        exclude_paths={"/"},
    )

    with TestClient(app) as client:
        http_response = client.get("/")

        assert http_response.status_code == 200
