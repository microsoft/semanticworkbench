import tempfile
from pathlib import Path
from typing import Annotated

import pydantic
import pytest
from pydantic import AliasChoices, BaseModel, Field
from semantic_workbench_assistant import storage


def test_read_non_existing():
    class TestModel(BaseModel):
        pass

    result = storage.read_model("./x", TestModel)

    assert result is None


def test_write_read_model():
    class SubModel(BaseModel):
        sub_name: str

    class TestModel(BaseModel):
        name: str
        sub: SubModel

    with tempfile.TemporaryDirectory() as temp_dir:
        value = TestModel(name="test", sub=SubModel(sub_name="sub"))

        value_path = Path(temp_dir) / "model.json"
        storage.write_model(file_path=value_path, value=value)

        assert storage.read_model(value_path, TestModel) == value


def test_write_read_updated_model():
    class TestModel(BaseModel):
        name: str

    class TestModelBreaking(BaseModel):
        name_new: str

    class TestModelSupportsOldName(BaseModel):
        name_new: Annotated[
            str,
            Field(validation_alias=AliasChoices("name", "name_new")),
        ]

    with tempfile.TemporaryDirectory() as temp_dir:
        value = TestModel(name="test")

        value_path = Path(temp_dir) / "model.json"
        storage.write_model(file_path=value_path, value=value)

        with pytest.raises(pydantic.ValidationError):
            storage.read_model(value_path, TestModelBreaking)

        assert storage.read_model(value_path, TestModelSupportsOldName) == TestModelSupportsOldName(name_new="test")
