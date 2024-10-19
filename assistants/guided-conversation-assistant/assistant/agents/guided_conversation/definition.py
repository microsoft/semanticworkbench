import json
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional, Type, Union

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field, create_model
from semantic_workbench_assistant.config import UISchema

if TYPE_CHECKING:
    pass


#
# region Helpers
#

# take a full json schema and return a pydantic model, including support for
# nested objects and typed arrays


def parse_json_schema_type(schema_type: Union[str, List[str]]) -> Any:
    """Map JSON schema types to Python (Pydantic) types."""
    if isinstance(schema_type, list):
        if "null" in schema_type:
            schema_type = [t for t in schema_type if t != "null"]
            return Optional[parse_json_schema_type(schema_type[0])]

    if schema_type == "string":
        return str
    elif schema_type == "integer":
        return int
    elif schema_type == "number":
        return float
    elif schema_type == "boolean":
        return bool
    elif schema_type == "array":
        return List[Any]
    elif schema_type == "object":
        return Dict[str, Any]

    return Any


def resolve_ref(ref: str, schema: Dict[str, Any], definitions: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Resolves a $ref to the corresponding definition in the schema or definitions.
    """
    if definitions is None:
        raise ValueError("Definitions must be provided to resolve $ref")

    ref_path = ref.split("/")  # Ref paths are typically '#/$defs/SomeType'
    if ref_path[0] == "#":  # Local reference
        ref_path = ref_path[1:]  # Strip the '#'

    current = schema  # Start from the root schema
    for part in ref_path:
        if part == "$defs" and part in definitions:
            current = definitions  # Switch to definitions when we hit $defs
        else:
            current = current[part]  # Walk down the path

    return current


def create_pydantic_model_from_json_schema(
    schema: Dict[str, Any], model_name: str = "GeneratedModel", definitions: Dict[str, Any] | None = None
) -> Type[BaseModel]:
    """
    Recursively converts a JSON schema to a Pydantic BaseModel.
    Handles $defs for local definitions and $ref for references.
    """
    if definitions is None:
        definitions = schema.get("$defs", {})  # Gather $defs if they exist

    fields = {}

    if "properties" in schema:
        for field_name, field_schema in schema["properties"].items():
            if "$ref" in field_schema:  # Resolve $ref
                ref_schema = resolve_ref(field_schema["$ref"], schema, definitions)
                field_type = create_pydantic_model_from_json_schema(
                    ref_schema, model_name=field_name.capitalize(), definitions=definitions
                )

            else:
                field_type = parse_json_schema_type(field_schema.get("type", "any"))

                if "items" in field_schema:  # If array, handle item type
                    item_type = parse_json_schema_type(field_schema["items"].get("type", "any"))
                    field_type = List[item_type]

                if "properties" in field_schema:  # If object, generate sub-model
                    sub_model = create_pydantic_model_from_json_schema(
                        field_schema, model_name=field_name.capitalize(), definitions=definitions
                    )
                    field_type = sub_model

            # Check if field is required
            is_required = field_name in schema.get("required", [])
            if is_required:
                fields[field_name] = (field_type, ...)
            else:
                fields[field_name] = (Optional[field_type], None)

    # Dynamically create the Pydantic model
    return create_model(model_name, **fields)


# endregion


#
# region Models
#


class GuidedConversationDefinition(BaseModel):
    artifact: Annotated[
        str,
        Field(
            title="Artifact",
            description="The artifact that the agent will manage.",
        ),
        UISchema(widget="baseModelEditor"),
    ]

    rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
        UISchema(schema={"items": {"ui:widget": "textarea", "ui:options": {"rows": 2}}}),
    ] = []

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
        UISchema(widget="textarea", schema={"ui:options": {"rows": 10}}, placeholder="[optional]"),
    ] = ""

    context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
        UISchema(widget="textarea", placeholder="[optional]"),
    ] = ""

    # override the default resource constraint to add annotations
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
        ]

        unit: Annotated[
            ResourceConstraintUnit,
            Field(
                title="Resource Unit",
                description="The unit for the resource constraint.",
            ),
        ]

        quantity: Annotated[
            float,
            Field(
                title="Resource Quantity",
                description="The quantity for the resource constraint. If <=0, the resource constraint is disabled.",
            ),
        ]

    resource_constraint: Annotated[
        ResourceConstraint,
        Field(
            title="Resource Constraint",
        ),
        UISchema(schema={"quantity": {"ui:widget": "updown"}}),
    ]

    def get_artifact_model(self) -> Type[BaseModel]:
        schema = json.loads(self.artifact)
        return create_pydantic_model_from_json_schema(schema)


# endregion
