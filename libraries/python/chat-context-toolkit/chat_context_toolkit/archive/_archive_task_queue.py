import asyncio
import uuid
from typing import Sequence

from ._state import StateStorage
from ._types import (
    ArchiveContent,
    ArchiveManifest,
    ArchiveTaskConfig,
    MessageProtocol,
    MessageProvider,
    StorageProvider,
    Summarizer,
    TokenCounter,
    CONTENT_SUB_DIR_PATH,
    MANIFEST_SUB_DIR_PATH,
    logger,
)


class ArchiveTaskQueue:
    """
    A task queue for archiving messages. It processes messages in chunks based on a token count threshold.
    It uses a message provider to retrieve messages and a storage provider to store the archived content.

    Developers should keep a reference to this class and call `enqueue_run()` to trigger the archiving process.
    """

    def __init__(
        self,
        storage_provider: StorageProvider,
        message_provider: MessageProvider,
        token_counter: TokenCounter,
        summarizer: Summarizer,
        config: ArchiveTaskConfig = ArchiveTaskConfig(),
    ) -> None:
        self._state_storage = StateStorage(storage_provider)
        self._message_provider = message_provider
        self._storage_provider = storage_provider
        self._token_counter = token_counter
        self._summarizer = summarizer
        self._queue = asyncio.Queue[None]()
        self._task = asyncio.create_task(self._run_for_every_queue_item())
        self._config = config

    async def enqueue_run(self) -> None:
        await self._queue.put(None)

    async def _run_for_every_queue_item(self) -> None:
        while True:
            # wait for the queue to have an item before proceeding
            await self._queue.get()

            try:
                await self._run()
            except Exception:
                logger.exception("error during archive task")

    async def _run(self) -> None:
        """
        The main job logic for archiving messages.
        It retrieves messages from the message provider, looking for chunks of messages that exceed the token
        count threshold, and archives them.
        """

        config = self._config
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

        unique_id = uuid.uuid4().hex[:8]
        filename = f"archive_{max_timestamp.isoformat()}_{unique_id}.json"

        content = ArchiveContent(messages=[msg.openai_message for msg in messages])
        content_json = content.model_dump_json()
        await self._storage_provider.write_text_file(CONTENT_SUB_DIR_PATH / filename, content_json)
        filesize = len(content_json.encode("utf-8"))

        summary = await self._summarizer.summarize([msg.openai_message for msg in messages])
        manifest = ArchiveManifest(
            summary=summary,
            message_ids=[msg.id for msg in messages],
            timestamp_oldest=min_timestamp,
            timestamp_most_recent=max_timestamp,
            filename=filename,
            content_size_bytes=filesize,
        )
        await self._storage_provider.write_text_file(MANIFEST_SUB_DIR_PATH / filename, manifest.model_dump_json())

        # Update the state with the most recent archived message ID
        most_recent_message = messages[-1]
        async with self._state_storage.update_state() as state:
            state.most_recent_archived_message_id = most_recent_message.id

        return manifest
