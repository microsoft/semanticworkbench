from typing import AsyncIterable

from ._state import StateStorage
from ._types import (
    CONTENT_SUB_DIR_PATH,
    MANIFEST_SUB_DIR_PATH,
    ArchiveContent,
    ArchiveManifest,
    ArchivesState,
    StorageProvider,
)


class ArchiveReader:
    def __init__(
        self,
        storage_provider: StorageProvider,
    ) -> None:
        self._state_storage = StateStorage(storage_provider)
        self._storage_provider = storage_provider

    async def get_state(self) -> ArchivesState:
        """
        Retrieves the current state of the message history archive.

        Returns:
            ArchiveState: The current state of the archive.
        """
        return await self._state_storage.read_state()

    async def list(self) -> AsyncIterable[ArchiveManifest]:
        """
        Lists all archive chunks stored in the archive directory.

        Returns:
            AsyncIterable[ArchiveManifest]: A list of archive manifests.
        """

        manifest_paths = await self._storage_provider.list_files(MANIFEST_SUB_DIR_PATH)

        for manifest_path in manifest_paths:
            if manifest_path.suffix != ".json":
                continue

            content = await self._storage_provider.read_text_file(manifest_path)
            if content is None:
                continue

            manifest = ArchiveManifest.model_validate_json(content)
            yield manifest

    async def read(self, filename: str) -> ArchiveContent | None:
        """
        Reads an archive from the storage.

        Args:
            chunk_path (pathlib.PurePath): The path to the archive chunk file.

        Returns:
            ArchiveContent: The deserialized archive content.
        """
        chunk_path = CONTENT_SUB_DIR_PATH / filename

        content = await self._storage_provider.read_text_file(chunk_path)

        if content is None:
            return None

        return ArchiveContent.model_validate_json(content)
