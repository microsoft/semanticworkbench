from typing import Annotated, Literal

import pytest
from pydantic import BaseModel
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema, get_ui_schema, overwrite_defaults_from_env


def test_overwrite_defaults_from_env(monkeypatch: pytest.MonkeyPatch):
    class SubModel(BaseModel):
        sub_field: str = ""

    class TestModel(BaseModel):
        field: str = "default"
        optional_field: str | None = None
        sub_model: SubModel = SubModel()
        flag: bool = False

    model = TestModel()
    model_copy = model.model_copy()

    monkeypatch.setenv("config__field", "field_test")
    monkeypatch.setenv("config__optional_field", "optional_field_test")
    # verify all caps env var
    monkeypatch.setenv("CONFIG__SUB_MODEL__SUB_FIELD", "sub_field_test")
    # booleans (non strs) should not be affected
    monkeypatch.setenv("config__flag", "TRUE")

    updated = overwrite_defaults_from_env(model, prefix="config", separator="__")

    # ensure original was not mutated
    assert model == model_copy
    # ensure expected updates were applied
    assert updated == TestModel(
        field="field_test",
        optional_field="optional_field_test",
        sub_model=SubModel(sub_field="sub_field_test"),
        flag=False,
    )


def test_overwrite_defaults_from_env_no_effect_on_non_default_values(monkeypatch: pytest.MonkeyPatch):
    class SubModel(BaseModel):
        sub_field: str = ""

    class TestModel(BaseModel):
        field: str = ""
        sub_model: SubModel = SubModel()

    model = TestModel(field="test", sub_model=SubModel(sub_field="test"))
    model_copy = model.model_copy()

    monkeypatch.setenv("config__field", "this value should not be applied")
    monkeypatch.setenv("CONFIG__SUB_MODEL__SUB_FIELD", "this value should not be applied")

    updated = overwrite_defaults_from_env(model, prefix="config", separator="__")

    # ensure original was not mutated
    assert model == model_copy
    assert updated == model


def test_config_secret_str() -> None:
    class TestModel(BaseModel):
        name: str = "default-name"
        secret: ConfigSecretStr = ""

    model = TestModel(secret="super-secret")

    assert model.secret == "super-secret"

    json_serialized = model.model_dump(mode="json")
    assert json_serialized["secret"] == "**********"

    python_serialized = model.model_dump(mode="python")
    assert python_serialized["secret"] == "super-secret"

    json_serialized = model.model_dump(mode="json", context={"enable_secret_masking": False})
    assert json_serialized["secret"] == "super-secret"

    python_serialized = model.model_dump(mode="json", context={"enable_secret_masking": False})
    assert python_serialized["secret"] == "super-secret"

    assert get_ui_schema(TestModel) == {"secret": {"ui:options": {"widget": "password"}}}


def test_annotations() -> None:
    class ChildModel(BaseModel):
        child_name: Annotated[str, UISchema({"ui:options": {"child_name": True}})] = "default-child-name"

    class OtherChildModel(BaseModel):
        other_child_name: Annotated[str, UISchema({"ui:options": {"other_child_name": True}})] = (
            "default-other-child-name"
        )

    class TestModel(BaseModel):
        name: Annotated[str, UISchema({"ui:options": {"name": True}})] = "default-name"
        child: Annotated[ChildModel, UISchema({})] = ChildModel()
        union_type: Annotated[ChildModel | OtherChildModel, UISchema({})] = OtherChildModel()
        un_annotated: str = "un_annotated"
        annotated_with_others: Annotated[str, {"foo": "bar"}] = ""
        literal: Literal["literal"]

    ui_schema = get_ui_schema(TestModel)

    assert ui_schema == {
        "name": {"ui:options": {"name": True}},
        "child": {"child_name": {"ui:options": {"child_name": True}}},
        "union_type": {
            "child_name": {"ui:options": {"child_name": True}},
            "other_child_name": {"ui:options": {"other_child_name": True}},
        },
    }
