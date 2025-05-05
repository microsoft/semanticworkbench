from typing import Annotated

import openai_client
from assistant_extensions.attachments import AttachmentsConfigModel
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

from ..utils import load_text_include


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
    ] = 64_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by OpenAI is 4096 tokens (https://platform.openai.com/docs/models)"
            ),
        ),
    ] = 8_000

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"


class PromptConfig(BaseModel):
    model_config = ConfigDict(
        title="Prompt Templates",
        json_schema_extra={
            "required": [
                "instruction_prompt",
                "coordinator_prompt",
                "team_prompt",
                "whiteboard_prompt",
                "project_information_request_detection",
            ],
        },
    )

    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior of the AI assistant. This is prepended to every response prompt.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "You are an AI project assistant that helps teams collaborate. You can facilitate file sharing between "
        "different conversations, allowing users to collaborate without being in the same conversation. "
        "Users can invite others with the /invite command, and you'll help synchronize files between conversations. "
        "In addition to text, you can also produce markdown, code snippets, and other types of content."
    )

    coordinator_prompt: Annotated[
        str,
        Field(
            title="Coordinator Prompt",
            description="The prompt used to instruct the behavior of the coordinator assistant. This is added to the instruction prompt when in coordinator mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("coordinator_prompt.txt")

    team_prompt: Annotated[
        str,
        Field(
            title="Team Prompt",
            description="The prompt used to instruct the behavior of the team member assistant. This is added to the instruction prompt when in team member mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("team_prompt.txt")

    project_information_request_detection: Annotated[
        str,
        Field(
            title="Information Request Detection Prompt",
            description="The prompt used to detect information requests in project assistant mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("project_information_request_detection.txt")

    whiteboard_prompt: Annotated[
        str,
        Field(title="Whiteboard Prompt", description="The prompt used to generate whiteboard content."),
        UISchema(widget="textarea"),
    ] = load_text_include("whiteboard_prompt.txt")

    welcome_message_generation: Annotated[
        str,
        Field(
            title="Welcome Message generation prompt",
            description="The prompt used to generate a welcome message for new team conversations.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("welcome_message_generation.txt")


class CoordinatorConfig(BaseModel):
    model_config = ConfigDict(
        title="Coordinator Configuration",
        json_schema_extra={
            "required": ["welcome_message", "prompt_for_files"],
        },
    )

    welcome_message: Annotated[
        str,
        Field(
            title="Coordinator Welcome Message",
            description="The message to display when a coordinator starts a new project. {share_url} will be replaced with the actual URL.",
        ),
        UISchema(widget="textarea"),
    ] = """# Welcome to the Project Assistant

This conversation is your personal conversation as the project coordinator.

**To invite team members to your project, copy and share this link with them:**
[Join Team Conversation]({share_url})

I've created a brief for your project. Let's start by updating it with your project goals and details."""

    prompt_for_files: Annotated[
        str,
        Field(
            title="File Upload Prompt",
            description="The message used to prompt project coordinators to upload relevant files.",
        ),
        UISchema(widget="textarea"),
    ] = "To begin building your project context, would you like to upload any relevant files like documents, images, or data that your team will need? You can drag and drop files directly into this conversation."

    list_participants_command: Annotated[
        str,
        Field(
            title="List Participants Command",
            description="The command project coordinators can use to list all participants (without the slash).",
        ),
    ] = "list-participants"


class TeamConfig(BaseModel):
    model_config = ConfigDict(
        title="Team Member Configuration",
        json_schema_extra={
            "required": ["welcome_message", "status_command"],
        },
    )

    default_welcome_message: Annotated[
        str,
        Field(
            title="Team Welcome Message",
            description="The message to display when a user joins a project as a Team member. Shown after successfully joining a project.",
        ),
        UISchema(widget="textarea"),
    ] = "# Welcome to Your Team Conversation\n\nYou've joined this project as a team member. This is your personal conversation for working on the project. You can communicate with the assistant, make information requests, and track your progress here."

    status_command: Annotated[
        str,
        Field(
            title="Status Command",
            description="The command project participants can use to check project status (without the slash).",
        ),
    ] = "project-status"


# ProjectConfig class has been removed - fields are now directly in AssistantConfigModel


# Base Assistant Configuration - shared by all templates
class AssistantConfigModel(BaseModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include Debug Output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

    prompt_config: Annotated[
        PromptConfig,
        Field(
            title="Prompt Configuration",
            description="Configuration for prompt templates used throughout the assistant.",
        ),
    ] = PromptConfig()

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

    attachments_config: Annotated[
        AttachmentsConfigModel,
        Field(
            title="Attachments Configuration",
            description="Configuration for handling file attachments in messages.",
        ),
    ] = AttachmentsConfigModel()

    # Project configuration fields moved directly into AssistantConfigModel
    auto_sync_files: Annotated[
        bool,
        Field(
            title="Auto-sync Files",
            description="Automatically synchronize files between linked conversations.",
        ),
    ] = True

    track_progress: Annotated[
        bool,
        Field(
            title="Track Progress",
            description="Track project progress with goals, criteria completion, and overall project state.",
        ),
    ] = True

    proactive_guidance: Annotated[
        bool,
        Field(
            title="Proactive Guidance",
            description="Proactively guide project coordinators through context building.",
        ),
    ] = True

    coordinator_config: Annotated[
        CoordinatorConfig,
        Field(
            title="Coordinator Configuration",
            description="Configuration for project coordinators.",
        ),
    ] = CoordinatorConfig()

    team_config: Annotated[
        TeamConfig,
        Field(
            title="Team Configuration",
            description="Configuration for project team members.",
        ),
    ] = TeamConfig()
