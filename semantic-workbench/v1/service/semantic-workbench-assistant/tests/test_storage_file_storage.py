import io
import uuid

import pytest
from semantic_workbench_assistant import storage


def test_read_file_not_found(file_storage: storage.FileStorage) -> None:
    with pytest.raises(FileNotFoundError):
        with file_storage.read_file(dir="conversation_id", filename="filename") as f:
            f.read()


def test_write_file(file_storage: storage.FileStorage) -> None:
    file_storage.write_file(dir="conversation_id", filename="filename", content=io.BytesIO(b"content"))


def test_write_read_delete_file(file_storage: storage.FileStorage) -> None:
    conversation_id = uuid.uuid4().hex
    filename = "myfile.txt"
    file_content = b"""
    this is a text file.
    """
    file_storage.write_file(dir=conversation_id, filename=filename, content=io.BytesIO(file_content))

    with file_storage.read_file(dir=conversation_id, filename=filename) as f:
        assert f.read() == file_content

    file_storage.delete_file(dir=conversation_id, filename=filename)

    with pytest.raises(FileNotFoundError):
        with file_storage.read_file(dir=conversation_id, filename=filename) as f:
            pass
