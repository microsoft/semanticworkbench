import json
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Type

from guided_conversation.utils.resources import ResourceConstraint, ResourceConstraintMode, ResourceConstraintUnit
from pydantic import BaseModel, Field, create_model
from semantic_workbench_assistant.config import UISchema

from ... import helpers
from . import config_defaults as config_defaults
from .config import GuidedConversationConfigModel, ResourceConstraintConfigModel

if TYPE_CHECKING:
    pass


# Artifact - The artifact is like a form that the agent must complete throughout the conversation.
# It can also be thought of as a working memory for the agent.
# We allow any valid Pydantic BaseModel class to be used.
class ArtifactModel(BaseModel):
    final_response: str = Field(description="The final response from the agent to the user.")
    conversation_status: str = Field(description="The status of the conversation.")
    filenames: str = Field(
        description="Names of the available files currently uploaded as attachments. May be an empty string if no files are attached."
    )


# Rules - These are the do's and don'ts that the agent should follow during the conversation.
rules = [
    "Terminate the conversation immediately if the user asks for harmful or inappropriate content.",
    "Set the conversation_status to user_completed once you have provided a final_response.",
]

# Conversation Flow (optional) - This defines in natural language the steps of the conversation.
conversation_flow = """1. Start by asking if the user has all their documents attached to the conversation that they
would like to use in drafting their outline. If any filenames are available, list those to the user to demonstrate you
know what they have already attached. If no filenames are available, let the user know no documents have been attached."
2. If the user attaches files, be sure to let them know all the filenames you are aware of that have been attached.
3.You want to reach the point that the user confirms all the docs they want attached have been attached. Once you interpret
the user's response as a confirmation, then go ahead and provide a final response.
4. Your final response should share the list of attachments being used and how they will be used. In this scenario they will be used
to construct a draft outline, which you will be requesting user feedback on. With this final response, the conversation_status must be
marked as user_completed.
"""

# Context (optional) - This is any additional information or the circumstances the agent is in that it should be aware of.
# It can also include the high level goal of the conversation if needed.
context = """The purpose of gathering these attachments is for the future user need to draft an outline.  The purpose of this conversation
is to make sure the user is aware of what documents they have uploaded as attachments and if they need to upload anymore before
the user proceeds to drafting the outline."""


# Resource Constraints (optional) - This defines the constraints on the conversation such as time or turns.
# It can also help with pacing the conversation,
# For example, here we have set an exact time limit of 10 turns which the agent will try to fill.
resource_constraint = ResourceConstraint(
    quantity=5,
    unit=ResourceConstraintUnit.TURNS,
    mode=ResourceConstraintMode.MAXIMUM,
)


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


class GCAttachmentCheckConfigModel(GuidedConversationConfigModel):
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
    ] = json.dumps(ArtifactModel.model_json_schema(), indent=2)

    rules: Annotated[
        list[str],
        Field(title="Rules", description="Do's and don'ts that the agent should attempt to follow"),
        UISchema(schema={"items": {"ui:widget": "textarea", "ui:options": {"rows": 2}}}),
    ] = rules

    conversation_flow: Annotated[
        str,
        Field(
            title="Conversation Flow",
            description="A loose natural language description of the steps of the conversation",
        ),
        UISchema(widget="textarea", schema={"ui:options": {"rows": 10}}, placeholder="[optional]"),
    ] = conversation_flow.strip()

    context: Annotated[
        str,
        Field(
            title="Context",
            description="General background context for the conversation.",
        ),
        UISchema(widget="textarea", placeholder="[optional]"),
    ] = context.strip()

    resource_constraint: Annotated[
        ResourceConstraintConfigModel,
        Field(
            title="Resource Constraint",
        ),
        UISchema(schema={"quantity": {"ui:widget": "updown"}}),
    ] = ResourceConstraintConfigModel(
        unit=resource_constraint.unit,
        quantity=resource_constraint.quantity,
        mode=resource_constraint.mode,
    )

    def get_artifact_model(self) -> Type[BaseModel]:
        schema = json.loads(self.artifact)
        return create_pydantic_model_from_json_schema(schema)


# endregion
