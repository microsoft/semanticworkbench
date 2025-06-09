from typing import Annotated

import openai_client
from assistant_extensions.attachments import AttachmentsConfigModel
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.assistant_app import (
    BaseModelAssistantConfig,
)
from semantic_workbench_assistant.config import UISchema

from .utils import load_text_include


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

    coordinator_conversation_token_limit: Annotated[
        int,
        Field(
            title="Coordinator Conversation Token Limit",
            description="The maximum number of tokens to use for the coordinator conversation history.",
        ),
    ] = 4000

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"


class PromptConfig(BaseModel):
    model_config = ConfigDict(
        title="Prompt Templates",
        json_schema_extra={
            "required": [
                "coordinator_role",
                "coordinator_instructions",
                "team_role",
                "team_instructions",
                "whiteboard_prompt",
                "project_information_request_detection",
            ],
        },
    )

    coordinator_role: Annotated[
        str,
        Field(
            title="Coordinator Role",
            description="The role of the coordinator assistant. This is added to the prompt when in coordinator mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("coordinator_role.txt")

    coordinator_instructions: Annotated[
        str,
        Field(
            title="Coordinator Instructions",
            description="The instructions to give the coordinator assistant. This is added to the prompt when in coordinator mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("coordinator_instructions.txt")

    team_role: Annotated[
        str,
        Field(
            title="Team Role",
            description="The role of the team assistant. This is added to the prompt when in team member mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("team_role.txt")

    team_instructions: Annotated[
        str,
        Field(
            title="Team Instructions",
            description="The instructions to give the team assistant. This is added to the prompt when in team member mode.",
        ),
        UISchema(widget="textarea"),
    ] = load_text_include("team_instructions.txt")

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
    ] = """# Welcome to Knowledge Transfer

Welcome! I'm here to help you capture and share complex information in a way that others can easily explore and understand. Think of me as your personal knowledge bridge - I'll help you:

- 📚 Organize your thoughts - whether from documents, code, research papers, or brainstorming sessions
- 🔄 Establish shared understanding - I'll ask questions to ensure we're aligned on what matters most
- 🔍 Make your knowledge interactive - so others can explore the "why" behind decisions, alternatives considered, and deeper context
- 🔗 Create shareable experiences - I'll capture what knowledge you give me so it can be shared with your team members for them to explore at their own pace using this [Knowledge Transfer link]({share_url})

Simply share your content or ideas, tell me who needs to understand them, and what aspects you want to highlight. I'll capture what knowledge you give me so it can be shared with your team members for them to explore at their own pace.

In the side panel, you can see your "knowledge brief". This brief will be shared with your team members and will help them understand the content of your knowledge transfer. You can ask me to update it at any time.

What knowledge would you like to transfer today?"""


class TeamConfig(BaseModel):
    model_config = ConfigDict(
        title="Team Member Configuration",
        json_schema_extra={
            "required": ["default_welcome_message"],
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
            description="Proactively guide knowledge organizers through knowledge structuring.",
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


assistant_config = BaseModelAssistantConfig(AssistantConfigModel)
