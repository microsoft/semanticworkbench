import base64
import datetime
import pathlib
import uuid
from contextlib import asynccontextmanager
from tempfile import TemporaryDirectory
from typing import Any, AsyncGenerator, AsyncIterator, Callable, Iterable
from unittest import mock

import httpx
import pytest
from assistant_extensions.attachments import AttachmentsConfigModel, AttachmentsExtension
from llm_client.model import (
    CompletionMessage,
    CompletionMessageImageContent,
    CompletionMessageTextContent,
)
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_api_model.workbench_model import Conversation, File, FileList, ParticipantRole
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.assistant_app import AssistantAppProtocol, AssistantContext, ConversationContext


@pytest.fixture(scope="function", autouse=True)
def temporary_storage_directory(monkeypatch: pytest.MonkeyPatch) -> Iterable[pathlib.Path]:
    with TemporaryDirectory() as tempdir:
        monkeypatch.setattr(settings.storage, "root", tempdir)
        yield pathlib.Path(tempdir)


@pytest.mark.parametrize(
    ("filenames_with_bytes", "expected_messages"),
    [
        ({}, []),
        (
            {
                "file1.txt": lambda: b"file 1",
                "file2.txt": lambda: b"file 2",
            },
            [
                CompletionMessage(
                    role="system",
                    content=AttachmentsConfigModel().context_description,
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file1.txt</FILENAME><CONTENT>file 1</CONTENT></ATTACHMENT>",
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file2.txt</FILENAME><CONTENT>file 2</CONTENT></ATTACHMENT>",
                ),
            ],
        ),
        (
            {
                "file1.txt": lambda: (_ for _ in ()).throw(RuntimeError("file 1 error")),
                "file2.txt": lambda: b"file 2",
            },
            [
                CompletionMessage(
                    role="system",
                    content=AttachmentsConfigModel().context_description,
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file1.txt</FILENAME><ERROR>error processing file: file 1 error</ERROR><CONTENT></CONTENT></ATTACHMENT>",
                ),
                CompletionMessage(
                    role="system",
                    content="<ATTACHMENT><FILENAME>file2.txt</FILENAME><CONTENT>file 2</CONTENT></ATTACHMENT>",
                ),
            ],
        ),
        (
            {
                "img.png": lambda: base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                ),
            },
            [
                CompletionMessage(
                    role="system",
                    content=AttachmentsConfigModel().context_description,
                ),
                CompletionMessage(
                    role="user",
                    content=[
                        CompletionMessageTextContent(
                            type="text",
                            text="<ATTACHMENT><FILENAME>img.png</FILENAME><IMAGE>",
                        ),
                        CompletionMessageImageContent(
                            type="image",
                            media_type="image/png",
                            data="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                        ),
                        CompletionMessageTextContent(
                            type="text",
                            text="</IMAGE></ATTACHMENT>",
                        ),
                    ],
                ),
            ],
        ),
    ],
)
async def test_get_completion_messages_for_attachments(
    filenames_with_bytes: dict[str, Callable[[], bytes]],
    expected_messages: list[ChatCompletionMessageParam],
) -> None:
    mock_assistant_app = mock.MagicMock(spec=AssistantAppProtocol)

    assistant_id = uuid.uuid4()

    mock_conversation_context = mock.MagicMock(
        spec=ConversationContext(
            id="conversation_id",
            title="conversation_title",
            assistant=AssistantContext(
                id=str(assistant_id),
                name="assistant_name",
                _assistant_service_id="assistant_id",
                _template_id="",
            ),
            httpx_client=httpx.AsyncClient(),
        )
    )
    mock_conversation_context.id = "conversation_id"
    mock_conversation_context.assistant.id = str(assistant_id)

    mock_conversation_context.list_files.return_value = FileList(
        files=[
            File(
                conversation_id=uuid.uuid4(),
                created_datetime=datetime.datetime.now(datetime.UTC),
                updated_datetime=datetime.datetime.now(datetime.UTC),
                filename=filename,
                current_version=1,
                content_type="text/plain",
                file_size=1,
                participant_id="participant_id",
                participant_role=ParticipantRole.user,
                metadata={},
            )
            for filename in filenames_with_bytes.keys()
        ]
    )

    async def mock_get_conversation() -> Conversation:
        mock_conversation = mock.MagicMock(spec=Conversation)
        mock_conversation.metadata = {}
        return mock_conversation

    mock_conversation_context.get_conversation.side_effect = mock_get_conversation

    class MockFileIterator:
        def __init__(self, file_bytes_func: Callable[[], bytes]) -> None:
            self.file_bytes_func = file_bytes_func

        async def __aiter__(self) -> AsyncIterator[bytes]:
            yield self.file_bytes_func()

        async def __anext__(self) -> bytes:
            return self.file_bytes_func()

    @asynccontextmanager
    async def read_file_side_effect(
        filename: str, chunk_size: int | None = None
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        yield MockFileIterator(filenames_with_bytes[filename])

    mock_conversation_context.read_file.side_effect = read_file_side_effect

    extension = AttachmentsExtension(assistant=mock_assistant_app)

    actual_messages = await extension.get_completion_messages_for_attachments(
        context=mock_conversation_context,
        config=AttachmentsConfigModel(),
    )

    assert actual_messages == expected_messages
