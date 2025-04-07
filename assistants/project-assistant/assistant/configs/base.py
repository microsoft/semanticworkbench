from typing import Annotated

import openai_client
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

from ..utils import load_text_include
from .project_config import ProjectConfig, ReceiverConfig, RequestConfig, SenderConfig


# Base Assistant Configuration
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
        "You are an AI project assistant that helps teams collaborate. You can facilitate file sharing between "
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
    ] = "Welcome to the Project Assistant! I can help your team collaborate across conversations. You can:\n\n- Upload files that will be shared with your collaborators\n- Invite team members with the /invite command\n- Work together on documents with real-time file synchronization\n\nHow can I help your project today?"

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

    project_config: Annotated[
        ProjectConfig,
        Field(
            title="Project Configuration",
            description="Configuration settings specific to the project assistant functionality.",
        ),
    ] = ProjectConfig()