from contextlib import contextmanager
from contextvars import ContextVar
from typing import BinaryIO, Iterator

from semantic_workbench_assistant import settings
from semantic_workbench_assistant.storage import FileStorage


class ConversationFileStorage:
    def __init__(self, conversation_id: str):
        self._dir = f"conversation-{conversation_id}"

        # use a copy of the storage settings to disable safe filenames; ie. keep original filenames for easier debugging
        storage_settings = settings.storage.model_copy()
        storage_settings.ensure_safe_filenames = False

        self._file_storage = FileStorage(settings=storage_settings)

    def write_file(self, filename: str, content: BinaryIO) -> None:
        self._file_storage.write_file(self._dir, filename, content)

    def delete_file(self, filename: str) -> None:
        self._file_storage.delete_file(self._dir, filename)

    @contextmanager
    def read_file(self, filename: str) -> Iterator[BinaryIO]:
        with self._file_storage.read_file(self._dir, filename) as f:
            yield f


# This sets up a context-local variable that can be used to store and retrieve
# instances of ConversationFileStorage in a way that is safe and isolated across
# different asynchronous tasks or threads. This ensures that each task or thread
# can have its own independent instance of ConversationFileStorage without
# interfering with others.
current = ContextVar[ConversationFileStorage]("conversation_file_storage")
