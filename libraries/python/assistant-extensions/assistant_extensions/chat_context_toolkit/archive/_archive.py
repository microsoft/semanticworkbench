from pathlib import PurePath

from chat_context_toolkit.archive import ArchiveReader, ArchiveTaskConfig, ArchiveTaskQueue, StorageProvider
from chat_context_toolkit.archive import MessageProvider as ArchiveMessageProvider
from chat_context_toolkit.archive.summarization import LLMArchiveSummarizer, LLMArchiveSummarizerConfig
from chat_context_toolkit.history.tool_abbreviations import ToolAbbreviations
from openai_client import OpenAIRequestConfig, ServiceConfig, create_client
from openai_client.tokens import num_tokens_from_messages
from semantic_workbench_assistant.assistant_app import ConversationContext, storage_directory_for_context

from ..message_history import chat_context_toolkit_message_provider_for


class ArchiveStorageProvider(StorageProvider):
    """
    Storage provider implementation for archiving messages in workbench assistants.
    This provider reads and writes text files in a specified sub-directory of the storage directory for a conversation context.
    """

    def __init__(self, context: ConversationContext, sub_directory: str):
        self.root_path = storage_directory_for_context(context) / sub_directory

    async def read_text_file(self, relative_file_path: PurePath) -> str | None:
        """
        Read a text file from the archive storage.
        :param relative_file_path: The path to the file relative to the archive root.
        :return: The content of the file as a string, or None if the file does not exist.
        """
        path = self.root_path / relative_file_path
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # If the file does not exist, we return None
            return None

    async def write_text_file(self, relative_file_path: PurePath, content: str) -> None:
        path = self.root_path / relative_file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    async def list_files(self, relative_directory_path: PurePath) -> list[PurePath]:
        path = self.root_path / relative_directory_path
        if not path.exists() or not path.is_dir():
            return []
        return [file.relative_to(self.root_path) for file in path.iterdir()]


def archive_message_provider_for(
    context: ConversationContext, service_config: ServiceConfig, request_config: OpenAIRequestConfig
) -> ArchiveMessageProvider:
    """Create an archive message provider for the provided context."""
    return chat_context_toolkit_message_provider_for(
        context=context,
        tool_abbreviations=ToolAbbreviations(),
        service_config=service_config,
        request_config=request_config,
    )


def _archive_task_queue_for(
    context: ConversationContext,
    service_config: ServiceConfig,
    request_config: OpenAIRequestConfig,
    archive_task_config: ArchiveTaskConfig = ArchiveTaskConfig(),
    token_counting_model: str = "gpt-4o",
    archive_storage_sub_directory: str = "archives",
) -> ArchiveTaskQueue:
    """
    Create an archive task queue for the conversation context.
    """
    return ArchiveTaskQueue(
        storage_provider=ArchiveStorageProvider(context=context, sub_directory=archive_storage_sub_directory),
        message_provider=archive_message_provider_for(
            context=context, service_config=service_config, request_config=request_config
        ),
        token_counter=lambda messages: num_tokens_from_messages(messages=messages, model=token_counting_model),
        summarizer=LLMArchiveSummarizer(
            client_factory=lambda: create_client(service_config),
            llm_config=LLMArchiveSummarizerConfig(model=request_config.model),
        ),
        config=archive_task_config,
    )


class ArchiveTaskQueues:
    """
    ArchiveTaskQueues manages multiple ArchiveTaskQueue instances, one for each conversation context.
    """

    def __init__(self) -> None:
        self._queues: dict[str, ArchiveTaskQueue] = {}

    async def enqueue_run(
        self,
        context: ConversationContext,
        service_config: ServiceConfig,
        request_config: OpenAIRequestConfig,
        archive_task_config: ArchiveTaskConfig = ArchiveTaskConfig(),
    ) -> None:
        """Get the archive task queue for the given context, creating it if it does not exist."""
        context_id = context.id
        if context_id not in self._queues:
            self._queues[context_id] = _archive_task_queue_for(
                context=context,
                service_config=service_config,
                request_config=request_config,
                archive_task_config=archive_task_config,
            )
        await self._queues[context_id].enqueue_run()


def archive_reader_for(context: ConversationContext, archive_storage_sub_directory: str = "archives") -> ArchiveReader:
    """
    Create an ArchiveReader for the provided conversation context.
    """
    return ArchiveReader(
        storage_provider=ArchiveStorageProvider(context=context, sub_directory=archive_storage_sub_directory),
    )
