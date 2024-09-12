import asyncio
import logging
import os
import pathlib
import shutil
import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import IO, Any, AsyncIterator, Generic, Mapping, Sequence, TypeVar

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, ValidationError

from .. import settings
from ..assistant_service import create_app
from ..storage import model_read, model_write
from .content_safety import AlwaysWarnContentSafetyEvaluator, ContentSafety
from .context import AssistantContext, ConversationContext
from .error import BadRequestError
from .protocol import (
    AssistantConfigDataModel,
    AssistantConfigProvider,
    AssistantContextExtender,
    AssistantConversationInspector,
    AssistantDataExporter,
    ContentInterceptor,
    ConversationContextExtender,
    ConversationDataExporter,
    Events,
)
from .service import AssistantService

logger = logging.getLogger(__name__)


ConfigModelT = TypeVar("ConfigModelT", bound=BaseModel)


class BaseModelAssistantConfig(Generic[ConfigModelT]):
    """
    Assistant-config implementation that uses a BaseModel for default config.
    """

    def __init__(self, default: ConfigModelT | type[ConfigModelT], ui_schema: dict[str, Any] = {}) -> None:
        default = default() if isinstance(default, type) else default
        self._default = default
        self._ui_schema = ui_schema

    async def get_typed(self, assistant_context: AssistantContext) -> ConfigModelT:
        config = model_read(
            FileStorageContext.get(assistant_context).directory / "config.json", self._default.__class__
        )
        return config or self._default

    async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel:
        config = await self.get_typed(assistant_context)
        return AssistantConfigDataModel(
            config=config.model_dump(mode="json"),
            json_schema=config.model_json_schema(),
            ui_schema=self._ui_schema,
        )

    async def set_typed(self, assistant_context: AssistantContext, config: ConfigModelT) -> None:
        model_write(FileStorageContext.get(assistant_context).directory / "config.json", config)

    async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None:
        try:
            updated_config = self._default.model_validate(config)
        except ValidationError as e:
            raise BadRequestError(str(e))

        await self.set_typed(assistant_context, updated_config)


class EmptyConfigModel(BaseModel):
    model_config = ConfigDict(title="This assistant has no configuration")


@asynccontextmanager
async def zip_directory(directory: pathlib.Path) -> AsyncIterator[IO[bytes]]:
    # if the directory does not exist, create an empty temporary directory to zip
    empty_temp_dir = ""
    if not directory.exists():
        empty_temp_dir = tempfile.mkdtemp()
        directory = pathlib.Path(empty_temp_dir)

    try:
        # create a zip archive of the directory in a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = await asyncio.to_thread(
                shutil.make_archive,
                base_name=str(pathlib.Path(temp_dir) / "export"),
                format="zip",
                root_dir=directory,
                base_dir="",
                logger=logger,
                verbose=True,
            )

            with open(file_path, "rb") as f:
                yield f
    finally:
        if empty_temp_dir:
            await asyncio.to_thread(shutil.rmtree, empty_temp_dir, ignore_errors=True)


async def unzip_to_directory(stream: IO[bytes], directory: pathlib.Path) -> None:
    if directory.exists():
        await asyncio.to_thread(shutil.rmtree, directory)

    # write stream to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        for chunk in stream:
            f.write(chunk)
        f.flush()

    # extract zip archive to directory
    try:
        await asyncio.to_thread(shutil.unpack_archive, filename=f.name, extract_dir=directory, format="zip")
    except shutil.ReadError as e:
        raise BadRequestError(str(e))
    finally:
        try:
            os.unlink(f.name)
        except FileNotFoundError:
            pass


class FileStorageAssistantDataExporter:
    """
    Supports assistants that store data (state) on the file system, enabling export and import as
    a zip archive of the assistant storage directory.
    """

    @asynccontextmanager
    async def export(self, context: AssistantContext) -> AsyncIterator[IO[bytes]]:
        async with zip_directory(FileStorageContext.get(context).directory) as stream:
            yield stream

    async def import_(self, context: AssistantContext, stream: IO[bytes]) -> None:
        await unzip_to_directory(stream, FileStorageContext.get(context).directory)


@dataclass
class FileStorageContext:
    directory: pathlib.Path

    @staticmethod
    def get(context: AssistantContext | ConversationContext) -> "FileStorageContext":
        try:
            return context._extra[FileStorageContextExtender.__name__]
        except KeyError:
            raise ValueError(
                "FileStorageContext not found in context - ensure FileStorageContextExtender is configured as a"
                " ContextExtender"
            )


class FileStorageContextExtender(AssistantContextExtender, ConversationContextExtender):

    def extend(self, context: AssistantContext | ConversationContext) -> Any:
        match context:
            case AssistantContext():
                return FileStorageContext(directory=pathlib.Path(settings.storage.root) / context.id)

            case ConversationContext():
                return FileStorageContext(
                    directory=pathlib.Path(settings.storage.root) / f"{context.assistant.id}-{context.id}"
                )


class FileStorageConversationDataExporter:
    """
    Supports assistants that store data (state) on the file system, enabling export and import as
    a zip archive of the conversation storage directory.
    """

    @asynccontextmanager
    async def export(self, context: ConversationContext) -> AsyncIterator[IO[bytes]]:
        async with zip_directory(FileStorageContext.get(context).directory) as stream:
            yield stream

    async def import_(self, context: ConversationContext, stream: IO[bytes]) -> None:
        await unzip_to_directory(stream, FileStorageContext.get(context).directory)


class AssistantApp:

    def __init__(
        self,
        assistant_service_id: str,
        assistant_service_name: str,
        assistant_service_description: str,
        context_extenders: Sequence[AssistantContextExtender] = [FileStorageContextExtender()],
        conversation_context_extenders: Sequence[ConversationContextExtender] = [FileStorageContextExtender()],
        config_provider: AssistantConfigProvider = BaseModelAssistantConfig(EmptyConfigModel()),
        data_exporter: AssistantDataExporter = FileStorageAssistantDataExporter(),
        conversation_data_exporter: ConversationDataExporter = FileStorageConversationDataExporter(),
        inspectors: Mapping[str, AssistantConversationInspector] | None = None,
        content_interceptor: ContentInterceptor | None = None,
    ) -> None:
        self._assistant_service_id = assistant_service_id
        self._assistant_service_name = assistant_service_name
        self._assistant_service_description = assistant_service_description

        self._config_provider = config_provider
        self._data_exporter = data_exporter
        self._conversation_data_exporter = conversation_data_exporter

        self.context_extenders = context_extenders
        self.conversation_context_extenders = conversation_context_extenders
        self.events = Events()
        self.inspectors = inspectors or {}
        self.content_interceptor = content_interceptor or ContentSafety(AlwaysWarnContentSafetyEvaluator.factory)

    def fastapi_app(self) -> FastAPI:
        return create_app(
            lambda lifespan: AssistantService(
                assistant_app=self,
                register_lifespan_handler=lifespan.register_handler,
            )
        )
