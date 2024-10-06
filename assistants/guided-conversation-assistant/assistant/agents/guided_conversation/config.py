import json
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
    def get_type_str(py_type: Any) -> str:
        type_mapping = {str: "str", int: "int", float: "float", bool: "bool", list: "list", dict: "dict"}
        return type_mapping.get(py_type, "any")

    json_dict = {}
    for field_name, field in model.model_fields.items():
        field_type = get_type_hints(model)[field_name]
        default_value = field.default if not isinstance(field.default, PydanticUndefinedType) else ""
        json_dict[field_name] = {
            "value": default_value,
            "type": get_type_str(field_type),
            "description": field.description or "",
        }
    return json_dict


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
        UISchema(widget="textarea"),
    ] = json.dumps(pydantic_model_to_json(config_defaults.ArtifactModel), indent=2)  # type: ignore

    rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
        UISchema(schema={"items": {"ui:widget": "textarea"}}),
    ] = config_defaults.rules

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
        UISchema(widget="textarea", placeholder="[optional]"),
    ] = config_defaults.conversation_flow

    context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
        UISchema(widget="textarea", placeholder="[optional]"),
    ] = config_defaults.context

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
        return create_pydantic_model_from_json(self.artifact)


# endregion
