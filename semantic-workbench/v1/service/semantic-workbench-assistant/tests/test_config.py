import pytest
from pydantic import BaseModel
from semantic_workbench_assistant import config


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

    updated = config.overwrite_defaults_from_env(model, prefix="config", separator="__")

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

    updated = config.overwrite_defaults_from_env(model, prefix="config", separator="__")

    # ensure original was not mutated
    assert model == model_copy
    assert updated == model
