import pathlib
from datetime import datetime, timezone

import pytest
from chat_context_toolkit.archive import ArchiveReader, HistoryMessageParam
from chat_context_toolkit.archive._types import (
    ArchiveContent,
    ArchiveManifest,
    ArchivesState,
    MessageProtocol,
)
from openai.types.chat import ChatCompletionUserMessageParam


class MockMessage:
    def __init__(self, id: str, path_id: str, content: str):
        self.id = id
        self.path_id = path_id
        self.openai_message = ChatCompletionUserMessageParam(role="user", content=content)


class MockStorageProvider:
    def __init__(self):
        self.files = {}
        self.directories = {}

    async def read_text_file(self, relative_file_path: pathlib.PurePath) -> str | None:
        return self.files.get(str(relative_file_path))

    async def write_text_file(self, relative_file_path: pathlib.PurePath, content: str) -> None:
        self.files[str(relative_file_path)] = content

    async def list_files(self, relative_directory_path: pathlib.PurePath) -> list[pathlib.PurePath]:
        directory_str = str(relative_directory_path)
        if directory_str not in self.directories:
            return []
        return [pathlib.PurePath(file_path) for file_path in self.directories[directory_str]]


class MockMessageProvider:
    def __init__(self, messages: list[MessageProtocol]):
        self.messages = messages

    async def __call__(self, after_id: str | None) -> list[MessageProtocol]:
        return self.messages


async def test_get_state_returns_existing_state():
    """Test that get_state returns existing state from storage."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    # Setup existing state
    existing_state = ArchivesState(most_recent_archived_message_id="msg123")
    storage_provider.files["archive_state.json"] = existing_state.model_dump_json()

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    state = await reader.get_state()

    assert state.most_recent_archived_message_id == "msg123"


async def test_list_chunks_empty_directory():
    """Test list_chunks when manifest directory is empty."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()
    storage_provider.directories["manifests"] = []

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    chunks = []
    async for chunk in reader.list():
        chunks.append(chunk)

    assert len(chunks) == 0


async def test_list_chunks_with_manifests():
    """Test list_chunks returns ArchiveChunkManifest objects."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    # Setup manifest files
    manifest1 = ArchiveManifest(
        summary="First chunk summary",
        message_ids=["msg1", "msg2"],
        filename="chunk1.json",
        timestamp_oldest=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        timestamp_most_recent=datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
    )
    manifest2 = ArchiveManifest(
        summary="Second chunk summary",
        message_ids=["msg3", "msg4"],
        filename="chunk2.json",
        timestamp_oldest=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        timestamp_most_recent=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
    )

    storage_provider.directories["manifests"] = [
        "manifests/chunk1.json",
        "manifests/chunk2.json",
        "manifests/not_json.txt",  # Should be ignored
    ]
    storage_provider.files["manifests/chunk1.json"] = manifest1.model_dump_json()
    storage_provider.files["manifests/chunk2.json"] = manifest2.model_dump_json()
    storage_provider.files["manifests/not_json.txt"] = "not json content"

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    chunks: list[ArchiveManifest] = []
    async for chunk in reader.list():
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0].summary == "First chunk summary"
    assert chunks[0].message_ids == ["msg1", "msg2"]
    assert chunks[0].filename == "chunk1.json"
    assert chunks[1].summary == "Second chunk summary"
    assert chunks[1].message_ids == ["msg3", "msg4"]
    assert chunks[1].filename == "chunk2.json"


async def test_list_chunks_skips_non_json_files():
    """Test that list_chunks skips non-JSON files."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    storage_provider.directories["manifests"] = [
        "manifests/manifest.json",
        "manifests/readme.txt",
        "manifests/config.yaml",
    ]

    manifest = ArchiveManifest(
        summary="Test summary",
        message_ids=["msg1"],
        filename="content.json",
        timestamp_oldest=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        timestamp_most_recent=datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
    )
    storage_provider.files["manifests/manifest.json"] = manifest.model_dump_json()
    storage_provider.files["manifests/readme.txt"] = "This is a readme"
    storage_provider.files["manifests/config.yaml"] = "config: value"

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    chunks = []
    async for chunk in reader.list():
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].summary == "Test summary"


async def test_list_chunks_skips_files_with_no_content():
    """Test that list_chunks skips files that return None content."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    storage_provider.directories["manifests"] = ["manifests/valid.json", "manifests/missing.json"]

    manifest = ArchiveManifest(
        summary="Valid manifest",
        message_ids=["msg1"],
        filename="content.json",
        timestamp_oldest=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        timestamp_most_recent=datetime(2024, 1, 1, 10, 30, 0, tzinfo=timezone.utc),
    )
    storage_provider.files["manifests/valid.json"] = manifest.model_dump_json()
    # missing.json is not in storage_provider.files, so read_text_file returns None

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    chunks = []
    async for chunk in reader.list():
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0].summary == "Valid manifest"


async def test_read_chunk_existing_file():
    """Test read_chunk returns ArchiveChunkContent for existing file."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    # Setup content file
    messages: list[HistoryMessageParam] = [
        ChatCompletionUserMessageParam(role="user", content="Hello"),
        ChatCompletionUserMessageParam(role="user", content="World"),
    ]
    content = ArchiveContent(messages=messages)
    storage_provider.files["content/chunk1.json"] = content.model_dump_json()

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    result = await reader.read("chunk1.json")

    assert result is not None
    assert isinstance(result, ArchiveContent)
    assert len(result.messages) == 2
    assert result.messages[0].get("content") == "Hello"
    assert result.messages[1].get("content") == "World"


async def test_read_chunk_nonexistent_file():
    """Test read_chunk returns None for nonexistent file."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    result = await reader.read("nonexistent.json")

    assert result is None


async def test_read_chunk_constructs_correct_path():
    """Test that read_chunk constructs the correct content file path."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    # Setup content in nested directory structure
    content = ArchiveContent(messages=[])
    storage_provider.files["content/subfolder/chunk.json"] = content.model_dump_json()

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    # Test that it correctly constructs the path with CONTENT_DIR prefix
    result = await reader.read("subfolder/chunk.json")

    assert result is not None
    assert isinstance(result, ArchiveContent)


async def test_read_chunk_invalid_json():
    """Test read_chunk handles invalid JSON gracefully."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    # Setup invalid JSON content
    storage_provider.files["content/invalid.json"] = "{ invalid json content"

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    # This should raise a validation error
    with pytest.raises(Exception):  # Could be ValidationError or JSONDecodeError
        await reader.read("invalid.json")


async def test_integration_full_workflow():
    """Integration test showing full workflow of reading archive data."""
    message_provider = MockMessageProvider([])
    storage_provider = MockStorageProvider()

    # Setup complete archive structure
    state = ArchivesState(most_recent_archived_message_id="msg100")
    storage_provider.files["archive_state.json"] = state.model_dump_json()

    # Setup manifests
    manifest1 = ArchiveManifest(
        summary="Chat about weather",
        message_ids=["msg1", "msg2"],
        filename="weather.json",
        timestamp_oldest=datetime(2024, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        timestamp_most_recent=datetime(2024, 1, 1, 9, 30, 0, tzinfo=timezone.utc),
    )
    manifest2 = ArchiveManifest(
        summary="Technical discussion",
        message_ids=["msg3", "msg4"],
        filename="tech.json",
        timestamp_oldest=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
        timestamp_most_recent=datetime(2024, 1, 1, 14, 45, 0, tzinfo=timezone.utc),
    )

    storage_provider.directories["manifests"] = ["manifests/weather.json", "manifests/tech.json"]
    storage_provider.files["manifests/weather.json"] = manifest1.model_dump_json()
    storage_provider.files["manifests/tech.json"] = manifest2.model_dump_json()

    # Setup content files
    content1 = ArchiveContent(
        messages=[
            ChatCompletionUserMessageParam(role="user", content="How's the weather?"),
            ChatCompletionUserMessageParam(role="user", content="It's sunny today!"),
        ]
    )
    content2 = ArchiveContent(
        messages=[
            ChatCompletionUserMessageParam(role="user", content="What's Python?"),
            ChatCompletionUserMessageParam(role="user", content="It's a programming language."),
        ]
    )

    storage_provider.files["content/weather.json"] = content1.model_dump_json()
    storage_provider.files["content/tech.json"] = content2.model_dump_json()

    reader = ArchiveReader(
        message_provider=message_provider,
        storage_provider=storage_provider,
    )

    # Test get_state
    state_result = await reader.get_state()
    assert state_result.most_recent_archived_message_id == "msg100"

    # Test list_chunks
    chunks: list[ArchiveManifest] = []
    async for chunk in reader.list():
        chunks.append(chunk)

    assert len(chunks) == 2
    weather_chunk = next(c for c in chunks if c.summary == "Chat about weather")
    tech_chunk = next(c for c in chunks if c.summary == "Technical discussion")

    # Test read_chunk
    weather_content = await reader.read(weather_chunk.filename)
    tech_content = await reader.read(tech_chunk.filename)

    assert weather_content is not None
    assert len(weather_content.messages) == 2
    assert weather_content.messages[0].get("content") == "How's the weather?"

    assert tech_content is not None
    assert len(tech_content.messages) == 2
    assert tech_content.messages[0].get("content") == "What's Python?"
