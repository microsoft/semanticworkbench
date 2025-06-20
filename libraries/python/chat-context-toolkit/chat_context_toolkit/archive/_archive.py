import asyncio
import logging
import pathlib
import uuid
from typing import AsyncIterable, Callable, Sequence

from ._state import StateStorage
from ._types import (
    ArchiveContent,
    ArchiveManifest,
    ArchivesState,
    ArchiveTaskConfig,
    MessageProtocol,
    MessageProvider,
    StorageProvider,
    Summarizer,
    TokenCounter,
)

CONTENT_DIR = "content"
MANIFEST_DIR = "manifests"


logger = logging.getLogger(__name__)


class ArchiveTask:
    def __init__(
        self,
        storage_provider: StorageProvider,
        message_provider: MessageProvider,
        token_counter: TokenCounter,
        summarizer: Summarizer,
    ) -> None:
        self._state_storage = StateStorage(storage_provider)
        self._message_provider = message_provider
        self._storage_provider = storage_provider
        self._token_counter = token_counter
        self._summarizer = summarizer

    def start(self, config: ArchiveTaskConfig = ArchiveTaskConfig()) -> tuple[asyncio.Task[None], Callable[[], None]]:
        """
        Runs the archive job to process and archive messages.

        Returns:
            asyncio.Task[None]: An asyncio task that runs the archive job periodically.
            Callable[[], None]: A function to trigger the archive job explicitly, outside of the regular schedule.
        """
        adhoc_trigger_event = asyncio.Event()
        task = asyncio.create_task(self._run_periodically_or_on_event(config=config, trigger_event=adhoc_trigger_event))

        def trigger() -> None:
            if adhoc_trigger_event.is_set():
                return

            logger.info("archive job triggered explicitly")
            adhoc_trigger_event.set()

        return task, trigger

    async def _run_periodically_or_on_event(self, config: ArchiveTaskConfig, trigger_event: asyncio.Event) -> None:
        while True:
            try:
                await self._run(config=config)
            except Exception:
                logger.exception("error during archive task")

            try:
                await asyncio.wait_for(
                    trigger_event.wait(),
                    timeout=config.message_poll_interval_seconds,
                )
            except asyncio.TimeoutError:
                # If the event is not set within the timeout, continue to the next iteration
                pass

            trigger_event.clear()

    async def _run(self, config: ArchiveTaskConfig) -> None:
        """
        The main job logic for archiving messages.
        It retrieves messages from the message provider, looking for chunks of messages that exceed the token
        count threshold, and archives them.
        """

        state = await self._state_storage.read_state()
        messages = await self._message_provider(after_id=state.most_recent_archived_message_id)

        logger.info("running archive job; message count: %d", len(messages))

        start_index = 0

        token_counts = [self._token_counter([message.openai_message]) for message in messages]

        archive_count = 0
        archived_message_count = 0

        for index in range(len(messages)):
            token_count = sum(token_counts[start_index : index + 1])

            if token_count < config.chunk_token_count_threshold:
                continue

            chunk = messages[start_index : index + 1]
            manifest = await self._archive_chunk(chunk)
            archive_count += 1
            archived_message_count += len(chunk)
            start_index = index + 1
            logger.info(
                "archived chunk; filename: %s, message count: %d, total archived: %d",
                manifest.filename,
                len(chunk),
                archived_message_count,
            )

        logger.info(
            "archive job completed; archive count: %d, archived message count: %d",
            archive_count,
            archived_message_count,
        )

    async def _archive_chunk(self, messages: Sequence[MessageProtocol]) -> ArchiveManifest:
        """
        Archives the provided messages, creating a manifest and content file.

        Args:
            messages (list[MessageProtocol]): The messages to archive.
        """
        # Here you would implement the logic to archive the messages,
        # such as writing them to a file or database.
        # For now, we will just log the number of messages archived.
        logger.info("Archiving %d messages.", len(messages))

        if not messages:
            raise ValueError("No messages to archive.")

        min_timestamp = min(msg.timestamp for msg in messages)
        max_timestamp = max(msg.timestamp for msg in messages)

        unique_id = uuid.uuid4().hex
        filename = f"archive_{max_timestamp}_{unique_id}.json"

        summary = await self._summarizer.summarize([msg.openai_message for msg in messages])
        manifest = ArchiveManifest(
            summary=summary,
            message_ids=[msg.id for msg in messages],
            timestamp_oldest=min_timestamp,
            timestamp_most_recent=max_timestamp,
            filename=filename,
        )
        await self._storage_provider.write_text_file(
            pathlib.PurePath(MANIFEST_DIR) / filename, manifest.model_dump_json()
        )

        content = ArchiveContent(messages=[msg.openai_message for msg in messages])
        await self._storage_provider.write_text_file(
            pathlib.PurePath(CONTENT_DIR) / filename, content.model_dump_json()
        )

        # Update the state with the most recent archived message ID
        state = await self._state_storage.read_state()
        most_recent_message = messages[-1]
        state.most_recent_archived_message_id = most_recent_message.id
        await self._state_storage.write_state(state)

        return manifest


class ArchiveReader:
    def __init__(
        self,
        message_provider: MessageProvider,
        storage_provider: StorageProvider,
    ) -> None:
        self._state_storage = StateStorage(storage_provider)
        self._storage_provider = storage_provider
        self._message_provider = message_provider

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

        manifest_paths = await self._storage_provider.list_files(pathlib.PurePath(MANIFEST_DIR))

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
        chunk_path = pathlib.PurePath(CONTENT_DIR) / filename

        content = await self._storage_provider.read_text_file(chunk_path)

        if content is None:
            return None

        return ArchiveContent.model_validate_json(content)
