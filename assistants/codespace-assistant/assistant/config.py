from typing import Annotated

from assistant_extensions.ai_clients.config import AIClientConfig
from assistant_extensions.artifacts import ArtifactsConfigModel
from assistant_extensions.attachments import AttachmentsConfigModel
from assistant_extensions.workflows import WorkflowsConfigModel
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
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
    workflows: Annotated[
        WorkflowsConfigModel,
        Field(
            title="Workflows Extension Configuration",
            description="Configuration for the workflows extension.",
        ),
    ] = WorkflowsConfigModel()

    attachments: Annotated[
        AttachmentsConfigModel,
        Field(
            title="Attachments Extension Configuration",
            description="Configuration for the attachments extension.",
        ),
    ] = AttachmentsConfigModel()

    artifacts: Annotated[
        ArtifactsConfigModel,
        Field(
            title="Artifacts Extension Configuration",
            description="Configuration for the artifacts extension.",
        ),
    ] = ArtifactsConfigModel()

    tools: Annotated[
        ToolsConfigModel,
        Field(
            title="Tools Configuration",
            description="Configuration for the tools.",
        ),
    ] = ToolsConfigModel()


class HighTokenUsageWarning(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            title="Enabled",
            description="Whether to warn when the assistant's token usage is high.",
        ),
    ] = True

    message: Annotated[
        str,
        Field(
            title="Message",
            description="The message to display when the assistant's token usage is high.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "The assistant's token usage is high. If there are attachments that are no longer needed, you can delete them"
        " to free up tokens."
    )

    threshold: Annotated[
        int,
        Field(
            title="Threshold",
            description="The threshold percentage at which to warn about high token usage.",
        ),
    ] = 90


# the workbench app builds dynamic forms based on the configuration model and UI schema
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
        "You are an AI assistant that helps people with their work. In addition to text, you can also produce markdown,"
        " code snippets, and other types of content. If you wrap your response in triple backticks, you can specify the"
        " language for syntax highlighting. For example, ```python print('Hello, World!')``` will produce a code"
        " snippet in Python. Mermaid markdown is supported if you wrap the content in triple backticks and specify"
        ' \'mermaid\' as the language. For example, ```mermaid graph TD; A["A"]-->B["B"];``` will render a flowchart for the'
        " user.ABC markdown is supported if you wrap the content in triple backticks and specify 'abc' as the"
        " language.For example, ```abc C4 G4 A4 F4 E4 G4``` will render a music score and an inline player with a link"
        " to download the midi file."
    )

    # "You are an AI assistant that helps teams synthesize information from conversations and documents to create"
    #     " a shared understanding of complex topics. As you do so, there are tools observing the conversation and"
    #     " they will automatically create an outline and a document based on the conversation, you don't need to do"
    #     " anything special to trigger this, just have a conversation with the user. Focus on assisting the user and"
    #     " drawing out the info needed in order to bring clarity to the topic at hand."

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
        'Hello! I am a "co-intelligence" assistant that can help you synthesize information from conversations and'
        " documents to create a shared understanding of complex topics. Let's get started by having a conversation!"
        " You can also attach .docx, text, and image files to your chat messages to help me better understand the"
        " context of our conversation. Where would you like to start?"
    )

    only_respond_to_mentions: Annotated[
        bool,
        Field(
            title="Only Respond to @Mentions",
            description="Only respond to messages that @mention the assistant.",
        ),
    ] = False

    high_token_usage_warning: Annotated[
        HighTokenUsageWarning,
        Field(
            title="High Token Usage Warning",
            description="Configuration for the high token usage warning.",
        ),
    ] = HighTokenUsageWarning()

    ai_client_config: AIClientConfig

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    use_inline_attachments: Annotated[
        bool,
        Field(
            title="Use Inline Attachments",
            description="Experimental: place attachment content where it was uploaded in the conversation history.",
        ),
    ] = False

    extensions_config: Annotated[
        ExtensionsConfigModel,
        Field(
            title="Extensions Configuration",
            description="Configuration for the assistant extensions.",
        ),
    ] = ExtensionsConfigModel()

    # add any additional configuration fields


# endregion
