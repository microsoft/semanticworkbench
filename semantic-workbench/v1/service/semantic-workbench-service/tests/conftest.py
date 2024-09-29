import asyncio
import pathlib
import tempfile
import uuid
from typing import AsyncGenerator, Iterator

import asyncpg
import dotenv
import httpx
import pytest
import semantic_workbench_assistant.assistant_app
import semantic_workbench_assistant.assistant_service
import semantic_workbench_assistant.canonical
import semantic_workbench_assistant.storage
import semantic_workbench_service
import semantic_workbench_service.assistant_api_key
from fastapi import FastAPI
from semantic_workbench_api_model import (
    assistant_service_client,
    workbench_service_client,
)
from semantic_workbench_service import files, settings
from semantic_workbench_service import service as workbenchservice
from semantic_workbench_service.api import FastAPILifespan
from semantic_workbench_service.config import DBSettings

from tests.types import MockUser


def create_test_user(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    random_id = str(uuid.uuid4())
    name = f"test user {random_id}"
    test_user = MockUser(tenant_id=random_id, object_id=random_id, name=name)

    # monkeypatch the allowed_jwt_algorithms and app_ids for tests
    monkeypatch.setattr(settings.auth, "allowed_jwt_algorithms", {test_user.token_algo})
    monkeypatch.setattr(settings.auth, "allowed_app_ids", {test_user.app_id})

    return test_user


@pytest.fixture
def test_user(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    return create_test_user(monkeypatch)


@pytest.fixture
def test_user_2(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    return create_test_user(monkeypatch)


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--echosql",
        action="store_true",
        help="echo db sql statements",
        default=(dotenv.dotenv_values().get("WORKBENCH_PYTEST_ECHOSQL") or "").lower() in ["true", "1"],
    )
    parser.addoption(
        "--dbtype",
        action="store",
        help="database type",
        choices=["sqlite", "postgresql"],
        default=dotenv.dotenv_values().get("WORKBENCH_PYTEST_DBTYPE") or "sqlite",
    )


@pytest.fixture(scope="session")
def docker_compose_file() -> pathlib.Path:
    return pathlib.Path(__file__).parent / "docker-compose.yaml"


@pytest.fixture
def db_type(request: pytest.FixtureRequest) -> str:
    return request.config.option.dbtype


@pytest.fixture
def echo_sql(request: pytest.FixtureRequest) -> bool:
    return request.config.option.echosql


@pytest.fixture
async def db_settings(db_type: str, echo_sql: bool, request: pytest.FixtureRequest) -> AsyncGenerator[DBSettings, None]:
    db_settings = semantic_workbench_service.settings.db.model_copy()
    db_settings.echosql = echo_sql
    db_settings.alembic_config_path = str(pathlib.Path(__file__).parent.parent / "alembic.ini")

    match db_type:
        case "sqlite":
            # use a sqlite db in an auto-deleted temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                path = pathlib.Path(temp_dir) / f"{uuid.uuid4().hex}.db"
                db_settings.url = f"sqlite:///{path}"

                yield db_settings

        case "postgresql":
            # use a postgresql db in a docker container
            docker_services = request.getfixturevalue("docker_services")
            docker_ip = request.getfixturevalue("docker_ip")
            db_name = f"workbench_test_{uuid.uuid4().hex}"
            postgresql_port = docker_services.port_for("postgres", 5432)
            postgresql_url = f"postgresql://{docker_ip}:{postgresql_port}"

            db_settings.url = f"{postgresql_url}/{db_name}"
            db_settings.postgresql_ssl_mode = "disable"
            db_settings.postgresql_pool_size = 1

            admin_db_url = f"{postgresql_url}/postgres"

            async def db_is_up() -> bool:
                try:
                    conn = await asyncpg.connect(dsn=admin_db_url)
                    await conn.close()
                except (
                    asyncio.TimeoutError,
                    ConnectionResetError,
                    asyncpg.exceptions.CannotConnectNowError,
                    ConnectionError,
                ):
                    return False
                else:
                    return True

            async def wait_until_responsive(timeout: float, pause: float) -> None:
                async with asyncio.timeout(timeout):
                    while True:
                        if await db_is_up():
                            return
                        await asyncio.sleep(pause)

            await wait_until_responsive(timeout=30.0, pause=0.1)

            admin_connection: asyncpg.Connection = await asyncpg.connect(dsn=admin_db_url)
            try:
                await admin_connection.execute(f"CREATE DATABASE {db_name}")

                try:
                    yield db_settings
                finally:
                    await admin_connection.execute(
                        "select pg_terminate_backend(pid) from pg_stat_activity where datname=$1",
                        db_name,
                    )
                    await admin_connection.execute(f"DROP DATABASE {db_name}")

            finally:
                await admin_connection.close()


@pytest.fixture
def storage_settings() -> Iterator[files.StorageSettings]:
    storage_settings = semantic_workbench_service.settings.storage.model_copy()

    with tempfile.TemporaryDirectory() as temp_dir:
        storage_settings.root = temp_dir
        yield storage_settings


@pytest.fixture
def workbench_service(
    db_settings: DBSettings,
    storage_settings: files.StorageSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:
    monkeypatch.setattr(semantic_workbench_service.settings, "db", db_settings)
    monkeypatch.setattr(semantic_workbench_service.settings, "storage", storage_settings)

    api_key = uuid.uuid4().hex

    # monkeypatch the api key store for the workbench service
    monkeypatch.setattr(
        semantic_workbench_service.assistant_api_key,
        "get_store",
        lambda: semantic_workbench_service.assistant_api_key.FixedApiKeyStore(api_key=api_key),
    )

    # monkeypatch the configured api key for the assistant service
    monkeypatch.setattr(semantic_workbench_assistant.assistant_service.settings, "workbench_service_api_key", api_key)

    lifespan = FastAPILifespan()
    app = FastAPI(title="workbench service", lifespan=lifespan.lifespan)
    workbenchservice.init(
        app,
        register_lifespan_handler=lifespan.register_handler,
    )

    # monkeypatch workbench client to use a transport that directs requests to the workbench app
    monkeypatch.setattr(workbench_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=app))

    return app


@pytest.fixture
def canonical_assistant_service(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[FastAPI]:
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr(semantic_workbench_assistant.settings.storage, "root", temp_dir)

        assistant_app = semantic_workbench_assistant.canonical.canonical_app.fastapi_app()

        # configure assistant client to use a specific transport that directs requests to the assistant app
        monkeypatch.setattr(
            assistant_service_client, "httpx_transport_factory", lambda: httpx.ASGITransport(app=assistant_app)
        )

        yield assistant_app
