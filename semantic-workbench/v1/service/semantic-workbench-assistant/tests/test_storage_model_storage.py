from typing import Annotated

import pydantic
import pytest
from pydantic import AliasChoices, BaseModel, Field
from semantic_workbench_assistant import storage


def test_read_non_existing(file_storage: storage.FileStorage):
    class TestModel(BaseModel):
        pass

    model_storage = storage.ModelStorage(cls=TestModel, file_storage=file_storage, namespace="test")

    assert model_storage.get(key="test") is None


def test_write_read_model(file_storage: storage.FileStorage):
    class SubModel(BaseModel):
        sub_name: str

    class TestModel(BaseModel):
        name: str
        sub: SubModel

    model_storage = storage.ModelStorage[TestModel](cls=TestModel, file_storage=file_storage, namespace="test")

    value = TestModel(name="test", sub=SubModel(sub_name="sub"))

    model_storage.set(key="test", value=value)

    assert model_storage.get(key="test") == value


def test_write_read_updated_model(file_storage: storage.FileStorage):
    class TestModel(BaseModel):
        name: str

    class TestModelBreaking(BaseModel):
        name_new: str

    class TestModelSupportsOldName(BaseModel):
        name_new: Annotated[
            str,
            Field(validation_alias=AliasChoices("name", "name_new")),
        ]

    model_storage = storage.ModelStorage[TestModel](cls=TestModel, file_storage=file_storage, namespace="test")

    value = TestModel(name="test")

    model_storage.set(key="test", value=value)

    model_storage = storage.ModelStorage[TestModelBreaking](
        cls=TestModelBreaking, file_storage=file_storage, namespace="test"
    )

    with pytest.raises(pydantic.ValidationError):
        model_storage.get(key="test")

    model_storage = storage.ModelStorage[TestModelSupportsOldName](
        cls=TestModelSupportsOldName, file_storage=file_storage, namespace="test"
    )

    assert model_storage.get(key="test") == TestModelSupportsOldName(name_new="test")


def test_write_delete_model(file_storage: storage.FileStorage):
    class TestModel(BaseModel):
        name: str

    model_storage = storage.ModelStorage[TestModel](cls=TestModel, file_storage=file_storage, namespace="test")

    value = TestModel(name="test")

    model_storage.set(key="test", value=value)

    model_storage.delete(key="test")

    assert model_storage.get(key="test") is None
