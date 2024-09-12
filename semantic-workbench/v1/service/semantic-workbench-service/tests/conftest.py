import asyncio
import os
import pathlib
import shutil
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
from semantic_workbench_service import files, middleware
from semantic_workbench_service import service as workbenchservice
from semantic_workbench_service.api import FastAPILifespan
from tests.types import MockUser


@pytest.fixture(scope="session")
def service_dir(request: pytest.FixtureRequest) -> str:
    if "service" not in os.path.split(request.config.rootpath):
        pytest.fail("service tests must be run from the service directory or a child directory of service")
    path = request.config.rootpath
    while path.name != "service":
        path = path.parent
    return str(path)


def create_test_user(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    id = str(uuid.uuid4())
    name = f"test user {id}"
    test_user = MockUser(tenant_id=id, object_id=id, name=name)
    # monkeypatch the allowed_algorithms and app_ids for tests
    monkeypatch.setattr(middleware, "allowed_algorithms", {test_user.token_algo})
    monkeypatch.setattr(middleware, "allowed_app_ids", {test_user.app_id})
    return test_user


@pytest.fixture()
def test_user(monkeypatch: pytest.MonkeyPatch) -> MockUser:
    return create_test_user(monkeypatch)


@pytest.fixture()
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
def docker_compose_file(service_dir) -> str:
    return os.path.join(service_dir, "semantic-workbench-service", "tests", "docker-compose.yaml")


@pytest.fixture()
async def db_url(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, service_dir
) -> AsyncGenerator[str, None]:

    echo = request.config.option.echosql
    monkeypatch.setattr(semantic_workbench_service.settings.db, "echosql", echo)

    match request.config.option.dbtype:
        case "sqlite":
            path = os.path.join(service_dir, ".data", f"{uuid.uuid4().hex}.db")
            db_url = f"sqlite:///{path}"
            monkeypatch.setattr(semantic_workbench_service.settings.db, "url", db_url)

            try:
                yield db_url
            finally:
                pathlib.Path(path).unlink(missing_ok=True)
                pathlib.Path(f"{path}-shm").unlink(missing_ok=True)
                pathlib.Path(f"{path}-wal").unlink(missing_ok=True)

        case "postgresql":
            # start docker container with postgres
            docker_services = request.getfixturevalue("docker_services")
            docker_ip = request.getfixturevalue("docker_ip")
            db_name = f"workbench_test_{uuid.uuid4().hex}"
            postgresql_port = docker_services.port_for("postgres", 5432)
            postgresql_url = f"postgresql://{docker_ip}:{postgresql_port}"
            admin_db_url = f"{postgresql_url}/postgres"

            db_url = f"{postgresql_url}/{db_name}"
            monkeypatch.setattr(semantic_workbench_service.settings.db, "url", db_url)
            monkeypatch.setattr(semantic_workbench_service.settings.db, "postgresql_ssl_mode", "disable")
            monkeypatch.setattr(semantic_workbench_service.settings.db, "postgresql_pool_size", 1)
            # disable migrations on startup for tests
            monkeypatch.setattr(semantic_workbench_service.settings.db, "migrate_on_startup", False)

            async def db_is_up() -> bool:
                try:
                    conn = await asyncpg.connect(dsn=admin_db_url)
                    await conn.close()
                    return True
                except Exception:
                    return False

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
                    yield db_url
                finally:
                    await admin_connection.execute(
                        "select pg_terminate_backend(pid) from pg_stat_activity where datname=$1", db_name
                    )
                    await admin_connection.execute(f"DROP DATABASE {db_name}")

            finally:
                await admin_connection.close()


@pytest.fixture()
def file_storage(monkeypatch: pytest.MonkeyPatch, service_dir) -> Iterator[files.Storage]:
    path = os.path.join(service_dir, ".data", f"test-{uuid.uuid4().hex}")
    monkeypatch.setattr(semantic_workbench_service.settings.storage, "root", path)
    storage = files.Storage(semantic_workbench_service.settings.storage)
    try:
        yield storage
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def workbench_service(db_url, file_storage, monkeypatch: pytest.MonkeyPatch) -> FastAPI:

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
    monkeypatch.setattr(workbench_service_client, "httpx_transport", httpx.ASGITransport(app=app))

    return app


@pytest.fixture()
def assistant_file_storage(
    request: pytest.FixtureRequest,
    service_dir,
) -> Iterator[semantic_workbench_assistant.storage.FileStorage]:
    path = os.path.join(service_dir, ".data", f"test-assistant-{uuid.uuid4().hex}")
    storage = semantic_workbench_assistant.storage.FileStorage(
        semantic_workbench_assistant.storage.FileStorageSettings(root=path)
    )
    try:
        yield storage
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def canonical_assistant_service(
    assistant_file_storage: semantic_workbench_assistant.storage.FileStorage,
    monkeypatch: pytest.MonkeyPatch,
) -> FastAPI:

    assistant_app = semantic_workbench_assistant.canonical.app

    # configure assistant client to use a specific transport that directs requests to the assistant app
    monkeypatch.setattr(assistant_service_client, "httpx_transport", httpx.ASGITransport(app=assistant_app))

    return assistant_app
