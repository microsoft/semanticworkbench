import tempfile
from pathlib import Path
from typing import Iterator

import pytest
from mcp.server.fastmcp import Context
from mcp_server_filesystem import settings
from mcp_server_filesystem.server import (
    create_directory,
    edit_file,
    get_file_info,
    list_directory,
    move_file,
    read_file,
    read_multiple_files,
    search_files,
    write_file,
)


@pytest.fixture(scope="function")
def test_dir(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Fixture to create and clean up a temporary test directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Add test directory to allowed directories
        monkeypatch.setattr(settings, "allowed_directories", [str(Path(temp_dir).resolve())])
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def test_context() -> Context:
    """Fixture to create and provide a mock context for tests."""
    return Context()


async def test_read_file(test_dir, test_context):
    test_file = test_dir / "test.txt"
    content = "Hello, World!"
    with test_file.open("w") as f:
        f.write(content)

    result = await read_file(ctx=test_context, path=str(test_file))
    assert result == content


async def test_write_file(test_dir, test_context):
    test_file = test_dir / "output.txt"
    content = "Sample output."

    await write_file(ctx=test_context, path=str(test_file), content=content)

    assert test_file.exists()
    assert test_file.read_text() == content


async def test_list_directory(test_dir, test_context):
    (test_dir / "file1.txt").write_text("Hello")
    (test_dir / "file2.txt").write_text("World")

    result = await list_directory(ctx=test_context, path=str(test_dir))

    assert len(result) == 2
    assert "[FILE] file1.txt" in result
    assert "[FILE] file2.txt" in result


async def test_create_directory(test_dir, test_context):
    new_dir = test_dir / "subdir"

    await create_directory(ctx=test_context, path=str(new_dir))

    assert new_dir.exists()
    assert new_dir.is_dir()


async def test_edit_file(test_dir, test_context):
    test_file = test_dir / "mutable.txt"
    test_file.write_text("original content")

    edits = [{"oldText": "original", "newText": "updated"}]

    await edit_file(ctx=test_context, path=str(test_file), edits=edits)

    assert test_file.read_text() == "updated content"


async def test_search_files(test_dir, test_context):
    (test_dir / "match1.txt").write_text("1")
    (test_dir / "match2.txt").write_text("2")
    (test_dir / "nomatch.log").write_text("3")

    result = await search_files(ctx=test_context, root_path=str(test_dir), pattern="*.txt")

    assert len(result) == 2
    assert any("match1.txt" in r for r in result)
    assert any("match2.txt" in r for r in result)


async def test_read_multiple_files(test_dir, test_context):
    test_file1 = test_dir / "file1.txt"
    test_file2 = test_dir / "file2.txt"
    content1 = "Hello, File 1!"
    content2 = "Hello, File 2!"

    test_file1.write_text(content1)
    test_file2.write_text(content2)

    result = await read_multiple_files(ctx=test_context, paths=[str(test_file1), str(test_file2)])

    assert result[str(test_file1)] == content1
    assert result[str(test_file2)] == content2


async def test_move_file(test_dir, test_context):
    test_file = test_dir / "test.txt"
    test_file.write_text("Test content")

    target_file = test_dir / "moved_test.txt"
    await move_file(ctx=test_context, source=str(test_file), destination=str(target_file))

    assert not test_file.exists()
    assert target_file.exists()
    assert target_file.read_text() == "Test content"


async def test_operations_fail_for_unauthorized_path(test_dir, test_context):
    """
    Validate all file operations fail when attempting to access unauthorized paths.
    """
    unauthorized_path = "/unauthorized/path"

    with pytest.raises(PermissionError):
        await read_file(test_context, unauthorized_path)

    with pytest.raises(PermissionError):
        await write_file(test_context, unauthorized_path, "Test content")

    with pytest.raises(PermissionError):
        await list_directory(test_context, unauthorized_path)

    with pytest.raises(PermissionError):
        await create_directory(test_context, unauthorized_path)

    with pytest.raises(PermissionError):
        await edit_file(test_context, unauthorized_path, edits=[{"oldText": "foo", "newText": "bar"}])

    with pytest.raises(PermissionError):
        await search_files(test_context, unauthorized_path, pattern="*.txt")

    with pytest.raises(PermissionError):
        await get_file_info(test_context, unauthorized_path)

    with pytest.raises(PermissionError):
        await read_multiple_files(ctx=test_context, paths=[unauthorized_path + "/file.txt"])

    with pytest.raises(PermissionError):
        await move_file(ctx=test_context, source=unauthorized_path, destination="/unauthorized/destination")


async def test_get_file_info(test_dir, test_context):
    test_file = test_dir / "info.txt"
    test_file.write_text("This is metadata.")

    result = await get_file_info(ctx=test_context, path=str(test_file))

    assert isinstance(result, dict)
    assert result["size"] == len("This is metadata.")
    assert result["is_file"] is True
