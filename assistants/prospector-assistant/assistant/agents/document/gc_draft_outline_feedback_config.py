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
    final_response: str = Field(
        description="The final response from the agent to the user. You will update this field."
    )
    conversation_status: str = Field(
        description="The status of the conversation. May be user_initiated, user_returned, or "
        "user_completed. You are only allowed to update this field to user_completed, otherwise you will not update it."
    )
    user_decision: str = Field(
        description="The decision of the user on what should happen next. May be update_outline or "
        "draft_paper. You will update this field."
    )
    filenames: str = Field(
        description="Names of the available files currently uploaded as attachments. Information "
        "from the content of these files was used to help draft the outline under review. You "
        "CANNOT change this field."
    )
    current_outline: str = Field(
        description="The most up-to-date version of the outline under review. You CANNOT change this field."
    )


# Rules - These are the do's and don'ts that the agent should follow during the conversation.
rules = [
    "Do NOT rewrite or update the outline, even if the user asks you to.",
    "Do NOT show the outline, unless the user asks you to.",
    (
        "You are ONLY allowed to help the user decide on any changes to the outline or answer questions "
        "about writing an outline."
    ),
    (
        "You are only allowed to update conversation_status to user_completed. All other values for that field"
        " will be preset."
    ),
    (
        "If the conversation_status is marked as user_completed, the final_response cannot be left as "
        "Unanswered. The final_response must be set based on the conversation flow instructions."
    ),
    "Terminate the conversation immediately if the user asks for harmful or inappropriate content.",
]

# Conversation Flow (optional) - This defines in natural language the steps of the conversation.
conversation_flow = """
1. If there is no prior conversation history to reference, use the conversation_status to determine if the user is initiating a new conversation (user_initiated) or returning to an existing conversation (user_returned).
2. Only greet the user if the user is initiating a new conversation. If the user is NOT initiating a new conversation, you should respond as if you are in the middle of a conversation.  In this scenario, do not say "hello", or "welcome back" or any type of formalized greeting.
3. Start by asking the user to review the outline. The outline will have already been provided to the user. You do not provide the outline yourself unless the user
specifically asks for it from you.
4. Answer any questions about the outline or the drafting process the user inquires about.
5. Use the following logic to fill in the artifact fields:
a. At any time, if the user asks for a change to the outline, the conversation_status must be
marked as user_completed. The user_decision must be marked as update_outline. The final_response
must inform the user that a new outline is being generated based off the request.
b. At any time, if the user has provided new attachments (detected via the filenames in the artifact),
the conversation_status must be marked as user_completed. The user_decision must be marked as
update_outline. The final_response must inform the user that a new outline is being generated based
on the addition of new attachments.
c. At any time, if the user is good with the outline in its current form and ready to move on to
drafting a paper from it, the conversation_status must be marked as user_completed. The
user_decision must be marked as draft_paper. The final_response must inform the user that you will
start drafting the beginning of the document based on this outline.
"""

# Context (optional) - This is any additional information or the circumstances the agent is in that it should be aware of.
# It can also include the high level goal of the conversation if needed.
context = """You are working with a user on drafting an outline. The current drafted outline is
provided, along with any filenames that were used to help draft the outline. You do not have access
to the content within the filenames that were used to help draft the outline. Your purpose here is
to help the user decide on any changes to the outline they might want or answer questions about it.
This may be the first time the user is asking for you help (conversation_status is user_initiated),
or the nth time (conversation_status is user_returned)."""


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


class GCDraftOutlineFeedbackConfigModel(GuidedConversationConfigModel):
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
