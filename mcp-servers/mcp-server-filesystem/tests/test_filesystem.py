import pytest
from pathlib import Path
from mcp_server.server import read_file, write_file, list_directory, create_directory, edit_file, search_files, get_file_info
import tempfile

@pytest.fixture(scope="function")
def test_dir():
    """Fixture to create and clean up a temporary test directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.mark.asyncio
async def test_read_file(test_dir):
    test_file = test_dir / "test.txt"
    content = "Hello, World!"
    with test_file.open("w") as f:
        f.write(content)

    result = read_file(path=str(test_file))
    assert result == content

@pytest.mark.asyncio
async def test_write_file(test_dir):
    test_file = test_dir / "output.txt"
    content = "Sample output."

    write_file(path=str(test_file), content=content)

    assert test_file.exists()
    assert test_file.read_text() == content

@pytest.mark.asyncio
async def test_list_directory(test_dir):
    (test_dir / "file1.txt").write_text("Hello")
    (test_dir / "file2.txt").write_text("World")

    result = list_directory(path=str(test_dir))

    assert len(result) == 2
    assert "file1.txt" in result
    assert "file2.txt" in result

@pytest.mark.asyncio
async def test_create_directory(test_dir):
    new_dir = test_dir / "subdir"

    create_directory(path=str(new_dir))

    assert new_dir.exists()
    assert new_dir.is_dir()

@pytest.mark.asyncio
async def test_edit_file(test_dir):
    test_file = test_dir / "mutable.txt"
    test_file.write_text("original content")

    edits = [
        {"oldText": "original", "newText": "updated"}
    ]

    edit_file(path=str(test_file), edits=edits, dry_run=False)

    assert test_file.read_text() == "updated content"

@pytest.mark.asyncio
async def test_search_files(test_dir):
    (test_dir / "match1.txt").write_text("1")
    (test_dir / "match2.txt").write_text("2")
    (test_dir / "nomatch.log").write_text("3")

    result = search_files(root_path=str(test_dir), pattern="*.txt")

    assert len(result) == 2
    assert any("match1.txt" in r for r in result)
    assert any("match2.txt" in r for r in result)

@pytest.mark.asyncio
async def test_get_file_info(test_dir):
    test_file = test_dir / "info.txt"
    test_file.write_text("This is metadata.")

    result = get_file_info(path=str(test_file))

    assert isinstance(result, dict)
    assert result["size"] == len("This is metadata.")
    assert result["is_file"] is True
