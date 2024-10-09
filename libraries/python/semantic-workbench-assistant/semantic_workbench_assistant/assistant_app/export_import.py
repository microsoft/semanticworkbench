import asyncio
import logging
import pathlib
import shutil
import tempfile
from contextlib import asynccontextmanager
from typing import (
    IO,
    AsyncIterator,
)

from .context import AssistantContext, ConversationContext, storage_directory_for_context
from .error import BadRequestError

logger = logging.getLogger(__name__)


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
        pathlib.Path(f.name).unlink(missing_ok=True)


class FileStorageAssistantDataExporter:
    """
    Supports assistants that store data (state) on the file system, enabling export and import as
    a zip archive of the assistant storage directory.
    """

    @asynccontextmanager
    async def export(self, context: AssistantContext) -> AsyncIterator[IO[bytes]]:
        async with zip_directory(storage_directory_for_context(context)) as stream:
            yield stream

    async def import_(self, context: AssistantContext, stream: IO[bytes]) -> None:
        await unzip_to_directory(stream, storage_directory_for_context(context))


class FileStorageConversationDataExporter:
    """
    Supports assistants that store data (state) on the file system, enabling export and import as
    a zip archive of the conversation storage directory.
    """

    @asynccontextmanager
    async def export(self, context: ConversationContext) -> AsyncIterator[IO[bytes]]:
        async with zip_directory(storage_directory_for_context(context)) as stream:
            yield stream

    async def import_(self, context: ConversationContext, stream: IO[bytes]) -> None:
        await unzip_to_directory(stream, storage_directory_for_context(context))
