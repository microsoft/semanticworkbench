from io import BytesIO  # Import BytesIO

import pytest
from assistant_drive import Drive, DriveConfig
from context import Context

file_content = BytesIO(b"Hello, World!")  # Convert byte string to BytesIO


@pytest.fixture
def drive():
    context: Context = Context(session_id="test_session")
    config = DriveConfig(context=context)
    drive = Drive(config)
    drive.delete()

    yield drive

    drive.delete()


def test_add_bytes_to_root(drive):
    # Add a file with a directory.
    metadata = drive.add_bytes(file_content, "test.txt")

    assert metadata.filename == "test.txt"
    assert metadata.dir is None
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["test.txt"]


def test_add_bytes_to_directory(drive):
    metadata = drive.add_bytes(file_content, "test.txt", "summaries")

    assert metadata.filename == "test.txt"
    assert metadata.dir == "summaries"
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["summaries"]
    assert list(drive.list(dir="summaries")) == ["test.txt"]


def test_add_bytes_to_nested_directory(drive):
    metadata = drive.add_bytes(file_content, "test.txt", "abc/summaries")

    assert metadata.filename == "test.txt"
    assert metadata.dir == "abc/summaries"
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["abc"]
    assert list(drive.list(dir="abc")) == ["summaries"]
    assert list(drive.list(dir="abc/summaries")) == ["test.txt"]


def test_exists(drive):
    assert not drive.file_exists("test.txt", "summaries")
    drive.add_bytes(file_content, "test.txt", "summaries")
    assert drive.file_exists("test.txt", "summaries")


def test_read(drive):
    drive.add_bytes(file_content, "test.txt", "summaries")
    with drive.read_file("test.txt", "summaries") as f:
        assert f.read() == b"Hello, World!"


def test_list(drive):
    drive.add_bytes(file_content, "test.txt", "summaries")
    assert list(drive.list(dir="summaries")) == ["test.txt"]

    drive.add_bytes(file_content, "test2.txt", "summaries")
    assert sorted(list(drive.list(dir="summaries"))) == ["test.txt", "test2.txt"]


def test_read_non_existent_file(drive):
    with pytest.raises(FileNotFoundError):
        with drive.read_file("test.txt", "summaries") as f:
            f.read()


def test_no_overwrite(drive):
    drive.add_bytes(file_content, "test.txt", "summaries")
    metadata = drive.add_bytes(file_content, "test.txt", "summaries")
    assert metadata.filename == "test(1).txt"
    assert sorted(list(drive.list(dir="summaries"))) == sorted(["test.txt", "test(1).txt"])


def test_overwrite(drive):
    drive.add_bytes(file_content, "test.txt", "summaries")
    metadata = drive.add_bytes(BytesIO(b"XXX"), "test.txt", "summaries", overwrite=True)
    assert metadata.filename == "test.txt"
    with drive.read_file("test.txt", "summaries") as f:
        assert f.read() == b"XXX"
    assert list(drive.list(dir="summaries")) == ["test.txt"]


def test_delete(drive):
    drive.add_bytes(file_content, "test.txt", "summaries")
    drive.delete(dir="summaries", filename="test.txt")
    assert list(drive.list(dir="summaries")) == []

    # Add a file with the same name but overwrite.
    metadata = drive.add_bytes(file_content, "test.txt", "summaries", overwrite=True)
    assert metadata.filename == "test.txt"
    assert sorted(list(drive.list(dir="summaries"))) == sorted(["test.txt"])

    drive.delete()
