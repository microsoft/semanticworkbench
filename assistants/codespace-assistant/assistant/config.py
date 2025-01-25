from typing import Annotated

from assistant_extensions.ai_clients.config import (
    AzureOpenAIClientConfigModel,
    OpenAIClientConfigModel,
)
from assistant_extensions.attachments import AttachmentsConfigModel
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from openai_client import AzureOpenAIServiceConfig, OpenAIRequestConfig
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

from . import helpers
from .extensions.tools import ToolsConfigModel

# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Assistant Configuration
#


class ExtensionsConfigModel(BaseModel):
    tools: Annotated[
        ToolsConfigModel,
        Field(
            title="Tools Configuration",
            description="Configuration for the tools.",
        ),
    ] = ToolsConfigModel()

    attachments: Annotated[
        AttachmentsConfigModel,
        Field(
            title="Attachments Extension Configuration",
            description="Configuration for the attachments extension.",
        ),
    ] = AttachmentsConfigModel()


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(BaseModel):
    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior of the AI assistant.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "You are an AI assistant that helps people with their work. In addition to text, you can also produce markdown,"
        " code snippets, and other types of content. If you wrap your response in triple backticks, you can specify the"
        " language for syntax highlighting. For example, ```python print('Hello, World!')``` will produce a code"
        " snippet in Python. Mermaid markdown is supported if you wrap the content in triple backticks and specify"
        ' \'mermaid\' as the language. For example, ```mermaid graph TD; A["A"]-->B["B"];``` will render a flowchart for the'
        " user.ABC markdown is supported if you wrap the content in triple backticks and specify 'abc' as the"
        " language.For example, ```abc C4 G4 A4 F4 E4 G4``` will render a music score and an inline player with a link"
        " to download the midi file."
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
    ] = helpers.load_text_include("guardrails_prompt.txt")

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "Hello! I am an assistant that can help you with coding projects within the context of the Semantic Workbench."
        "Let's get started by having a conversation about your project. You can ask me questions, request code"
        " snippets, or ask for help with debugging. I can also help you with markdown, code snippets, and other types"
        " of content. You can also attach .docx, text, and image files to your chat messages to help me better"
        " understand the context of our conversation. Where would you like to start?"
    )

    only_respond_to_mentions: Annotated[
        bool,
        Field(
            title="Only Respond to @Mentions",
            description="Only respond to messages that @mention the assistant.",
        ),
    ] = False

    generative_ai_client_config: Annotated[
        AzureOpenAIClientConfigModel | OpenAIClientConfigModel,
        Field(
            title="OpenAI Generative Model Configuration",
            description="Configuration for the generative model, such as gpt-4o.",
            discriminator="ai_service_type",
            default=AzureOpenAIClientConfigModel.model_construct(),
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIClientConfigModel(
        service_config=AzureOpenAIServiceConfig.model_construct(),
        request_config=OpenAIRequestConfig(
            max_tokens=128_000,
            response_tokens=16_384,
            model="gpt-4o",
            is_reasoning_model=False,
        ),
    )

    reasoning_ai_client_config: Annotated[
        AzureOpenAIClientConfigModel | OpenAIClientConfigModel,
        Field(
            title="OpenAI Reasoning Model Configuration",
            description="Configuration for the reasoning model, such as o1-preview, o1-mini, etc.",
            discriminator="ai_service_type",
            default=AzureOpenAIClientConfigModel.model_construct(),
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIClientConfigModel(
        service_config=AzureOpenAIServiceConfig.model_construct(),
        request_config=OpenAIRequestConfig(
            max_tokens=128_000, response_tokens=65_536, model="o1-mini", is_reasoning_model=True
        ),
    )

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    extensions_config: Annotated[
        ExtensionsConfigModel,
        Field(
            title="Extensions Configuration",
            description="Configuration for the assistant extensions.",
        ),
    ] = ExtensionsConfigModel()

    # add any additional configuration fields


# endregion