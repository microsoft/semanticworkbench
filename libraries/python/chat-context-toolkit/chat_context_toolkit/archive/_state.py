import pathlib

from ._types import ArchivesState, StorageProvider

ARCHIVE_STATE_FILE = pathlib.PurePath("archive_state.json")


class StateStorage:
    def __init__(self, storage_provider: StorageProvider) -> None:
        self._storage_provider = storage_provider

    async def read_state(self) -> ArchivesState:
        """
        Reads the current state of the message history archive.

        Returns:
            ArchiveState: The current state of the archive.
        """
        state_content = await self._storage_provider.read_text_file(ARCHIVE_STATE_FILE)

        if state_content is None:
            return ArchivesState()

        return ArchivesState.model_validate_json(state_content)

    async def write_state(self, state: ArchivesState) -> None:
        """
        Writes the current state of the message history archive.

        Args:
            state (ArchiveState): The state to write to the archive.
        """
        await self._storage_provider.write_text_file(ARCHIVE_STATE_FILE, state.model_dump_json())
