import pathlib
import shutil
import uuid
from typing import Iterator

import pytest
from semantic_workbench_assistant import settings, storage


def test_file_path(request: pytest.FixtureRequest, *args) -> str:
    return str(pathlib.Path(request.config.rootpath, *args))


@pytest.fixture()
def file_storage(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> Iterator[storage.FileStorage]:
    path = test_file_path(request, ".data", f"test-{uuid.uuid4().hex}")
    monkeypatch.setattr(settings.storage, "root", path)
    test_storage = storage.FileStorage(settings.storage)
    try:
        yield test_storage
    finally:
        shutil.rmtree(path, ignore_errors=True)
