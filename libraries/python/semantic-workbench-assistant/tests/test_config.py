import uuid
from typing import Annotated, Literal

import pytest
from pydantic import BaseModel
from semantic_workbench_assistant.config import (
    ConfigSecretStr,
    ConfigSecretStrJsonSerializationMode,
    UISchema,
    config_secret_str_serialization_context,
    get_ui_schema,
    replace_config_secret_str_masked_values,
)


@pytest.mark.parametrize(
    ("model_dump_mode", "serialization_mode", "secret_value", "expected_value"),
    [
        # python serialization should always return the actual value
        ("dict_python", None, "super-secret", "super-secret"),
        ("dict_python", None, "", ""),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "super-secret", "super-secret"),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "", ""),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "super-secret", "super-secret"),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "", ""),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_value, "super-secret", "super-secret"),
        ("dict_python", ConfigSecretStrJsonSerializationMode.serialize_value, "", ""),
        # json serialization should return the expected value based on the serialization mode
        ("dict_json", None, "super-secret", "************"),
        ("dict_json", None, "", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "super-secret", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "super-secret", "************"),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "", ""),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_value, "super-secret", "super-secret"),
        ("dict_json", ConfigSecretStrJsonSerializationMode.serialize_value, "", ""),
        ("str_json", None, "super-secret", "************"),
        ("str_json", None, "", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "super-secret", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_as_empty, "", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "super-secret", "************"),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_masked_value, "", ""),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_value, "super-secret", "super-secret"),
        ("str_json", ConfigSecretStrJsonSerializationMode.serialize_value, "", ""),
    ],
)
def test_config_secret_str_serialization(
    model_dump_mode: Literal["dict_python", "dict_json", "str_json"],
    serialization_mode: ConfigSecretStrJsonSerializationMode | None,
    secret_value: str,
    expected_value: str,
) -> None:
    class TestModel(BaseModel):
        secret: ConfigSecretStr

    model = TestModel(secret=secret_value)
    assert model.secret == secret_value

    match serialization_mode:
        case None:
            context = None
        case _:
            context = config_secret_str_serialization_context(serialization_mode)

    match model_dump_mode:
        case "dict_python":
            dump = model.model_dump(mode="python", context=context)
            assert dump["secret"] == expected_value
        case "dict_json":
            dump = model.model_dump(mode="json", context=context)
            assert dump["secret"] == expected_value
        case "str_json":
            dump = model.model_dump_json(context=context)
            assert dump == f'{{"secret":"{expected_value}"}}'


def test_config_secret_str_deserialization() -> None:
    class SubModel1(BaseModel):
        submodel1_secret: ConfigSecretStr

    class SubModel2(BaseModel):
        submodel2_secret: ConfigSecretStr

    class TestModel(BaseModel):
        secret: ConfigSecretStr
        sub_model: SubModel1 | SubModel2

    secret_value = uuid.uuid4().hex

    sub_model = SubModel2(submodel2_secret=secret_value)
    model = TestModel(secret=secret_value, sub_model=sub_model)
    assert model.secret == secret_value

    serialized_config = model.model_dump(mode="json")

    assert serialized_config["secret"] == "*" * len(secret_value)
    assert serialized_config["sub_model"]["submodel2_secret"] == "*" * len(secret_value)

    deserialized_config = TestModel.model_validate(serialized_config)

    masked_reverted = replace_config_secret_str_masked_values(deserialized_config, model)
    assert masked_reverted.secret == model.secret
    assert isinstance(masked_reverted.sub_model, SubModel2)
    assert masked_reverted.sub_model.submodel2_secret == sub_model.submodel2_secret

    deserialized_model = TestModel.model_validate(masked_reverted)

    assert deserialized_model.secret == secret_value


def test_config_secret_str_ui_schema() -> None:
    class TestModel(BaseModel):
        secret: ConfigSecretStr

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
