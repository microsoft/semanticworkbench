import tempfile
from typing import Iterator

import pytest
from semantic_workbench_assistant import settings, storage


@pytest.fixture
def storage_settings(request: pytest.FixtureRequest) -> Iterator[storage.FileStorageSettings]:
    storage_settings = settings.storage.model_copy()

    with tempfile.TemporaryDirectory() as temp_dir:
        storage_settings.root = temp_dir
        yield storage_settings


@pytest.fixture
def file_storage(monkeypatch: pytest.MonkeyPatch, storage_settings: storage.FileStorageSettings) -> storage.FileStorage:
    monkeypatch.setattr(settings, "storage", storage_settings)

    return storage.FileStorage(settings.storage)
