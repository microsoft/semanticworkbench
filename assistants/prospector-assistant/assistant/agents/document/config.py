import json
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Type

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field, create_model
from semantic_workbench_assistant.config import UISchema

from ... import helpers
from . import config_defaults as config_defaults

if TYPE_CHECKING:
    pass


#
# region Helpers
#

# take a full json schema and return a pydantic model, including support for
# nested objects and typed arrays


def json_type_to_python_type(json_type: str) -> Type:
    # Mapping JSON types to Python types
    type_mapping = {"integer": int, "string": str, "number": float, "boolean": bool, "object": dict, "array": list}
    return type_mapping.get(json_type, Any)


def create_pydantic_model_from_json_schema(schema: Dict[str, Any], model_name="DynamicModel") -> Type[BaseModel]:
    # Nested function to parse properties from the schema
    def parse_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        fields = {}
        for prop_name, prop_attrs in properties.items():
            prop_type = prop_attrs.get("type")
            description = prop_attrs.get("description", None)

            if prop_type == "object":
                nested_model = create_pydantic_model_from_json_schema(prop_attrs, model_name=prop_name.capitalize())
                fields[prop_name] = (nested_model, Field(..., description=description))
            elif prop_type == "array":
                items = prop_attrs.get("items", {})
                if items.get("type") == "object":
                    nested_model = create_pydantic_model_from_json_schema(items)
                    fields[prop_name] = (List[nested_model], Field(..., description=description))
                else:
                    nested_type = json_type_to_python_type(items.get("type"))
                    fields[prop_name] = (List[nested_type], Field(..., description=description))
            else:
                python_type = json_type_to_python_type(prop_type)
                fields[prop_name] = (python_type, Field(..., description=description))
        return fields

    properties = schema.get("properties", {})
    fields = parse_properties(properties)
    return create_model(model_name, **fields)


# endregion


#
# region Models
#


class ResourceConstraintConfigModel(ResourceConstraint):
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


class GuidedConversationConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(description=helpers.load_text_include("guided_conversation_agent_enabled.md")),
        UISchema(enable_markdown_in_description=True),
    ] = False

    artifact: Annotated[
        str,
        Field(
            title="Artifact",
            description="The artifact that the agent will manage.",
        ),
        UISchema(widget="baseModelEditor"),
    ] = json.dumps(config_defaults.ArtifactModel.model_json_schema(), indent=2)

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

    resource_constraint: Annotated[
        ResourceConstraintConfigModel,
        Field(
            title="Resource Constraint",
        ),
        UISchema(schema={"quantity": {"ui:widget": "updown"}}),
    ] = ResourceConstraintConfigModel()

    def get_artifact_model(self) -> Type[BaseModel]:
        schema = json.loads(self.artifact)
        return create_pydantic_model_from_json_schema(schema)


# endregion
