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
