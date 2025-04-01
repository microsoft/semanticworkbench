import pathlib
from typing import Annotated

import openai_client
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Helpers
#


# helper for loading an include from a text file
def load_text_include(filename) -> str:
    # get directory relative to this module
    directory = pathlib.Path(__file__).parent

    # get the file path for the prompt file
    file_path = directory / "text_includes" / filename

    # read the prompt from the file
    return file_path.read_text()


# endregion


#
# region Assistant Configuration
#


class RequestConfig(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens", "openai_model"],
        },
    )

    max_tokens: Annotated[
        int,
        Field(
            title="Max Tokens",
            description=(
                "The maximum number of tokens to use for both the prompt and response. Current max supported by OpenAI"
                " is 128k tokens, but varies by model (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 50_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by OpenAI is 4096 tokens (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 4_048

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"


# the workbench app builds dynamic forms based on the configuration model and UI schema
class SenderConfig(BaseModel):
    model_config = ConfigDict(
        title="Mission Sender Configuration",
        json_schema_extra={
            "required": ["welcome_message", "prompt_for_files", "context_building_prompt"],
        },
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Sender Welcome Message",
            description="The message to display when a mission owner starts a new conversation.",
        ),
        UISchema(widget="textarea"),
    ] = "Welcome to your mission control! As the mission owner, I'll help you build context by organizing files and information to share with your team. You can upload files, invite team members with the /invite command, and I'll help synchronize everything between conversations."

    prompt_for_files: Annotated[
        str,
        Field(
            title="File Upload Prompt",
            description="The message used to prompt mission owners to upload relevant files.",
        ),
        UISchema(widget="textarea"),
    ] = "To begin building your mission context, would you like to upload any relevant files like documents, images, or data that your team will need? You can drag and drop files directly into this conversation."

    context_building_prompt: Annotated[
        str,
        Field(
            title="Context Building Prompt",
            description="The message used to help mission owners organize their mission context.",
        ),
        UISchema(widget="textarea"),
    ] = "Let's organize your mission context. Here are some ways to structure your information:\n\n- Key documents: What reference materials does your team need?\n- Mission objectives: What are the specific goals and deliverables?\n- Timeline: What are the key milestones and deadlines?\n- Team roles: Who should do what?\n\nWould you like me to help you document any of these aspects?"

    list_participants_command: Annotated[
        str,
        Field(
            title="List Participants Command",
            description="The command mission owners can use to list all participants (without the slash).",
        ),
    ] = "list-participants"

    revoke_access_command: Annotated[
        str,
        Field(
            title="Revoke Access Command",
            description="The command mission owners can use to revoke access for a participant (without the slash).",
        ),
    ] = "revoke"


class ReceiverConfig(BaseModel):
    model_config = ConfigDict(
        title="Mission Receiver Configuration",
        json_schema_extra={
            "required": ["welcome_message", "status_command"],
        },
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Receiver Welcome Message",
            description="The message to display when a user joins a mission via invitation.",
        ),
        UISchema(widget="textarea"),
    ] = "Welcome to the mission! You've been added as a collaborator, and any files shared by the mission owner will appear in this conversation. You can also contribute by uploading your own files, which will be shared with the team."

    status_command: Annotated[
        str,
        Field(
            title="Status Command",
            description="The command mission participants can use to check mission status (without the slash).",
        ),
    ] = "mission-status"

    upload_notification: Annotated[
        str,
        Field(
            title="Upload Notification",
            description="The message displayed when a mission participant uploads a file.",
        ),
        UISchema(widget="textarea"),
    ] = "Your file has been uploaded and shared with the mission team. The mission owner and other participants will be notified."


class MissionConfig(BaseModel):
    model_config = ConfigDict(
        title="Mission Configuration",
        json_schema_extra={
            "required": ["auto_sync_files", "invite_command", "join_command"],
        },
    )

    auto_sync_files: Annotated[
        bool,
        Field(
            title="Auto-sync Files",
            description="Automatically synchronize files between linked conversations.",
        ),
    ] = True

    invite_command: Annotated[
        str,
        Field(
            title="Invite Command",
            description="The command users can type to invite others (without the slash).",
        ),
    ] = "invite"

    join_command: Annotated[
        str,
        Field(
            title="Join Command",
            description="The command users can type to join a mission (without the slash).",
        ),
    ] = "join"

    invitation_message: Annotated[
        str,
        Field(
            title="Invitation Message",
            description="The message sent to users when they are invited to collaborate.",
        ),
        UISchema(widget="textarea"),
    ] = "You've been invited to collaborate on a mission. Type /join to accept the invitation."

    proactive_guidance: Annotated[
        bool,
        Field(
            title="Proactive Guidance",
            description="Proactively guide mission owners through context building.",
        ),
    ] = True

    sender_config: Annotated[
        SenderConfig,
        Field(
            title="Sender Configuration",
            description="Configuration for mission owners (senders).",
        ),
    ] = SenderConfig()

    receiver_config: Annotated[
        ReceiverConfig,
        Field(
            title="Receiver Configuration",
            description="Configuration for mission participants (receivers).",
        ),
    ] = ReceiverConfig()


class AssistantConfigModel(BaseModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include Debug Output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior of the AI assistant.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "You are an AI mission assistant that helps teams collaborate. You can facilitate file sharing between "
        "different conversations, allowing users to collaborate without being in the same conversation. "
        "Users can invite others with the /invite command, and you'll help synchronize files between conversations. "
        "In addition to text, you can also produce markdown, code snippets, and other types of content."
    )

    guardrails_prompt: Annotated[
        str,
        Field(
            title="Guardrails Prompt",
            description=(
                "The prompt used to inform the AI assistant about the guardrails to follow. Default value based upon"
                " recommendations from: [Microsoft OpenAI Service: System message templates]"
                "(https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message"
                "#define-additional-safety-and-behavioral-guardrails)"
            ),
        ),
        UISchema(widget="textarea", enable_markdown_in_description=True),
    ] = load_text_include("guardrails_prompt.txt")

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
        UISchema(widget="textarea"),
    ] = "Welcome to the Mission Assistant! I can help your team collaborate across conversations. You can:\n\n- Upload files that will be shared with your collaborators\n- Invite team members with the /invite command\n- Work together on documents with real-time file synchronization\n\nHow can I help your mission today?"

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig()

    service_config: openai_client.ServiceConfig

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
    ] = CombinedContentSafetyEvaluatorConfig()

    mission_config: Annotated[
        MissionConfig,
        Field(
            title="Mission Configuration",
            description="Configuration settings specific to the mission assistant functionality.",
        ),
    ] = MissionConfig()


# endregion
