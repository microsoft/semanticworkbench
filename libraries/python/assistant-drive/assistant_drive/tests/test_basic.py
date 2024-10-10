from io import BytesIO

import pytest
from assistant_drive import Drive
from assistant_drive.drive import DriveConfig, IfDriveFileExistsBehavior

# from context import Context
from pydantic import BaseModel

file_content = BytesIO(b"Hello, World!")  # Convert byte string to BytesIO


@pytest.fixture
def drive():
    drive = Drive(DriveConfig(root="./data/drive/test"))
    drive.delete()

    yield drive

    drive.delete()


def test_write_to_root(drive):
    # Add a file with a directory.
    metadata = drive.write(file_content, "test.txt")

    assert metadata.filename == "test.txt"
    assert metadata.dir is None
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["test.txt"]


def test_write_to_directory(drive):
    metadata = drive.write(file_content, "test.txt", "summaries")

    assert metadata.filename == "test.txt"
    assert metadata.dir == "summaries"
    assert metadata.content_type == "text/plain"
    assert metadata.size == 13
    assert metadata.created_at is not None
    assert metadata.updated_at is not None

    assert list(drive.list()) == ["summaries"]
    assert list(drive.list(dir="summaries")) == ["test.txt"]


def test_write_to_nested_directory(drive):
    metadata = drive.write(file_content, "test.txt", "abc/summaries")

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
    drive.write(file_content, "test.txt", "summaries")
    assert drive.file_exists("test.txt", "summaries")


def test_open(drive):
    drive.write(file_content, "test.txt", "summaries")
    with drive.open_file("test.txt", "summaries") as f:
        assert f.read() == b"Hello, World!"


def test_list(drive):
    drive.write(file_content, "test.txt", "summaries")
    assert list(drive.list(dir="summaries")) == ["test.txt"]

    drive.write(file_content, "test2.txt", "summaries")
    assert sorted(list(drive.list(dir="summaries"))) == ["test.txt", "test2.txt"]


def test_open_non_existent_file(drive):
    with pytest.raises(FileNotFoundError):
        with drive.open_file("test.txt", "summaries") as f:
            f.read()


def test_auto_rename(drive, if_exists=IfDriveFileExistsBehavior.AUTO_RENAME):
    drive.write(file_content, "test.txt", "summaries")
    metadata = drive.write(file_content, "test.txt", "summaries")
    assert metadata.filename == "test(1).txt"
    assert sorted(list(drive.list(dir="summaries"))) == sorted(["test.txt", "test(1).txt"])


def test_overwrite(drive):
    drive.write(file_content, "test.txt", "summaries")
    metadata = drive.write(BytesIO(b"XXX"), "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.OVERWRITE)
    assert metadata.filename == "test.txt"
    with drive.open_file("test.txt", "summaries") as f:
        assert f.read() == b"XXX"
    assert list(drive.list(dir="summaries")) == ["test.txt"]


def test_fail(drive):
    drive.write(file_content, "test.txt", "summaries")
    with pytest.raises(FileExistsError):
        drive.write(file_content, "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.FAIL)


def test_delete(drive):
    drive.write(file_content, "test.txt", "summaries")
    drive.delete(dir="summaries", filename="test.txt")
    assert list(drive.list(dir="summaries")) == []

    # Add a file with the same name but overwrite.
    metadata = drive.write(file_content, "test.txt", "summaries", if_exists=IfDriveFileExistsBehavior.OVERWRITE)
    assert metadata.filename == "test.txt"
    assert sorted(list(drive.list(dir="summaries"))) == sorted(["test.txt"])

    drive.delete()


def test_open_files_multiple_files(drive) -> None:
    drive.write(file_content, "test.txt", "summaries")
    drive.write(file_content, "test2.txt", "summaries")

    files = list(drive.open_files("summaries"))
    assert len(files) == 2

    for file_context in files:
        with file_context as file:
            assert file.read() == b"Hello, World!"


def test_open_files_empty_dir(drive) -> None:
    files = list(drive.open_files("summaries"))
    assert len(files) == 0


def test_write_model(drive) -> None:
    class TestModel(BaseModel):
        name: str

    model = TestModel(name="test")
    drive.write_model(model, "test.json", "summaries")

    with drive.open_file("test.json", "summaries") as f:
        assert f.read() == b'{"name":"test"}'

    drive.delete()


def test_read_model(drive) -> None:
    class TestModel(BaseModel):
        name: str

    model = TestModel(name="test")
    drive.write_model(model, "test.json", "summaries")

    model = drive.read_model(TestModel, "test.json", "summaries")
    assert model.name == "test"

    drive.delete()


def test_read_models(drive) -> None:
    class TestModel(BaseModel):
        name: str

    model_1 = TestModel(name="test1")
    drive.write_model(model_1, "test1.json", "summaries")

    model_2 = TestModel(name="test2")
    drive.write_model(model_2, "test2.json", "summaries")

    models = list(drive.read_models(TestModel, "summaries"))
    assert len(models) == 2

    assert models[0].name == "test1"
    assert models[1].name == "test2"


def test_read_model_non_existent_file(drive) -> None:
    class TestModel(BaseModel):
        name: str

    with pytest.raises(FileNotFoundError):
        drive.read_model(TestModel, "test.json", "summaries")

    drive.delete()
