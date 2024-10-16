import json
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Type, get_type_hints

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field, create_model
from pydantic_core import PydanticUndefinedType
from semantic_workbench_assistant.config import UISchema

from . import config_defaults as config_defaults

if TYPE_CHECKING:
    pass


#
# region Helpers
#
class ArtifactFieldType(str, Enum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    LIST = "list"
    DICT = "dict"


def validate_field_type(type_: str) -> ArtifactFieldType:
    return ArtifactFieldType(type_)


class ArtifactModelChild(BaseModel):
    name: str = ""
    type: Annotated[
        ArtifactFieldType,
        Field(
            title="Type",
            description="The type of the field",
        ),
    ] = ArtifactFieldType.STR
    value: Annotated[
        Any,
        Field(
            title="Value",
            description="The default value of the field",
        ),
    ] = ""
    description: str = ""


ArtifactModel = List[ArtifactModelChild]


def determine_type(type_str: str) -> Type:
    type_mapping = {"str": str, "int": int, "float": float, "bool": bool, "list": List[Any], "dict": Dict[str, Any]}
    return type_mapping.get(type_str, Any)


def create_pydantic_model_from_json(json_data: str) -> Type[BaseModel]:
    data = json.loads(json_data)

    def create_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        fields = {}
        for key, value in data.items():
            if value["type"] == "dict":
                nested_model = create_pydantic_model_from_json(json.dumps(value["value"]))
                fields[key] = (nested_model, Field(description=value["description"]))
            else:
                fields[key] = (
                    determine_type(value["type"]),
                    Field(default=value["value"], description=value["description"]),
                )
        return fields

    fields = create_fields(data)
    return create_model("DynamicModel", **fields)


def pydantic_model_to_json(model: BaseModel) -> Dict[str, Any]:
    json_dict = {}
    for field_name, field in model.model_fields.items():
        field_type = get_type_hints(model)[field_name]
        if field_type is PydanticUndefinedType:
            raise ValueError(f"Field {field_name} has an undefined type")
        default_value = field.default if not isinstance(field.default, PydanticUndefinedType) else ""
        json_dict[field_name] = {
            "value": default_value,
            "type": field_type.__name__,
            "description": field.description or "",
        }
    return json_dict


def create_pydantic_model_from_artifact_model(artifact_model: ArtifactModel) -> Type[BaseModel]:
    def create_fields(artifact_model: ArtifactModel) -> Dict[str, Any]:
        fields = {}
        for child in artifact_model:
            if child.type == "dict":
                nested_model = create_pydantic_model_from_json(child.value)
                fields[child.name] = (nested_model, Field(description=child.description))
            else:
                fields[child.name] = (determine_type(child.type), Field(description=child.description))
        return fields

    fields = create_fields(artifact_model)
    return create_model("DynamicModel", **fields)


def pydantic_model_to_artifact_model(model: BaseModel) -> ArtifactModel:
    children: ArtifactModel = []

    for field_name, field in model.model_fields.items():
        field_type = get_type_hints(model)[field_name]
        if field_type is PydanticUndefinedType:
            raise ValueError(f"Field {field_name} has an undefined type")
        default_value = field.default if not isinstance(field.default, PydanticUndefinedType) else ""
        children.append(
            ArtifactModelChild(
                name=field_name,
                type=validate_field_type(field_type.__name__),
                value=default_value,
                description=field.description or "",
            )
        )

    return children


# endregion


#
# region Models
#


class GuidedConversationAgentConfigModel(BaseModel):
    artifact: Annotated[
        str,
        Field(
            title="Artifact",
            description="The artifact that the agent will manage.",
        ),
        UISchema(widget="baseModelEditor"),
    ] = json.dumps(config_defaults.ArtifactModel.model_json_schema(), indent=2)
    # UISchema(schema={"items": {"ui:options": {"title_field": "name"}}}),
    # ] = pydantic_model_to_artifact_model(config_defaults.ArtifactModel)  # type: ignore
    # ] = json.dumps(pydantic_model_to_json(config_defaults.ArtifactModel), indent=2)  # type: ignore

    rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
        UISchema(schema={"items": {"ui:widget": "textarea", "ui:options": {"rows": 2}}}),
    ] = config_defaults.rules

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
        UISchema(widget="textarea", schema={"ui:options": {"rows": 10}}, placeholder="[optional]"),
    ] = config_defaults.conversation_flow.strip()

    context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
        UISchema(widget="textarea", placeholder="[optional]"),
    ] = config_defaults.context.strip()

    class ResourceConstraint(ResourceConstraint):
        mode: Annotated[
            ResourceConstraintMode,
            Field(
                title="Resource Mode",
                description=(
                    'If "exact", the agents will try to pace the conversation to use exactly the resource quantity. If'
                    ' "maximum", the agents will try to pace the conversation to use at most the resource quantity.'
                ),
            ),
        ] = config_defaults.resource_constraint.mode

        unit: Annotated[
            ResourceConstraintUnit,
            Field(
                title="Resource Unit",
                description="The unit for the resource constraint.",
            ),
        ] = config_defaults.resource_constraint.unit

        quantity: Annotated[
            float,
            Field(
                title="Resource Quantity",
                description="The quantity for the resource constraint. If <=0, the resource constraint is disabled.",
            ),
        ] = config_defaults.resource_constraint.quantity

    resource_constraint: Annotated[
        ResourceConstraint,
        Field(
            title="Resource Constraint",
        ),
        UISchema(schema={"quantity": {"ui:widget": "updown"}}),
    ] = ResourceConstraint()

    def get_artifact_model(self) -> Type[BaseModel]:
        return self.artifact  # type: ignore
        # return create_pydantic_model_from_artifact_model(self.artifact)
        # return create_pydantic_model_from_json(self.artifact)


# endregion
