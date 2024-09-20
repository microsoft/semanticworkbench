import pathlib
from typing import Annotated, Literal

import openai
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant import config
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

from .agents.artifact_agent import ArtifactAgentConfigModel
from .agents.attachment_agent import AttachmentAgentConfigModel
from .responsible_ai.azure_evaluator import AzureContentSafetyEvaluatorConfigModel, AzureContentSafetyServiceConfigModel
from .responsible_ai.openai_evaluator import OpenAIContentSafetyEvaluatorConfigModel

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


# helper for loading a prompt from a text file
def _load_prompt_from_text_file(filename) -> str:
    # get directory relative to this module
    directory = pathlib.Path(__file__).parent

    # get the file path for the prompt file
    file_path = directory / "prompts" / filename

    # read the prompt from the file
    return file_path.read_text()


# endregion


#
# region Assistant Configuration
#


class AgentsConfigModel(BaseModel):
    artifact_agent: Annotated[
        ArtifactAgentConfigModel,
        Field(
            title="Artifact Agent Configuration",
            description="Configuration for the artifact agent.",
        ),
    ] = ArtifactAgentConfigModel()
    attachment_agent: Annotated[
        AttachmentAgentConfigModel,
        Field(
            title="Attachment Agent Configuration",
            description="Configuration for the attachment agent.",
        ),
    ] = AttachmentAgentConfigModel()


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
    ] = 128_000

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
        " 'mermaid' as the language. For example, ```mermaid graph TD; A-->B;``` will render a flowchart for the"
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
    ] = _load_prompt_from_text_file("guardrails_prompt.txt")

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

    high_token_usage_warning: Annotated[
        HighTokenUsageWarning,
        Field(
            title="High Token Usage Warning",
            description="Configuration for the high token usage warning.",
        ),
    ] = HighTokenUsageWarning()

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig()

    agents_config: Annotated[
        AgentsConfigModel,
        Field(
            title="Agents Configuration",
            description="Configuration for the assistant agents.",
        ),
    ] = AgentsConfigModel()

    # add any additional configuration fields


# endregion


#
# region Service Configuration
#


class AzureOpenAIAzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal["azure-identity"], UISchema(widget="hidden")] = "azure-identity"


class AzureOpenAIApiKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_openai_api_key"],
        },
    )

    auth_method: Annotated[Literal["api-key"], UISchema(widget="hidden")] = "api-key"

    azure_openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure OpenAI API Key",
            description=(
                "The Azure OpenAI API key for your resource instance.  If not provided, the service default will be"
                " used."
            ),
        ),
    ] = ""


class AzureOpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_endpoint"],
        },
    )

    service_type: Annotated[Literal["Azure OpenAI"], UISchema(widget="hidden")] = "Azure OpenAI"

    auth_config: Annotated[
        AzureOpenAIAzureIdentityAuthConfig | AzureOpenAIApiKeyAuthConfig,
        Field(
            title="Authentication Config",
            discriminator="auth_method",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureOpenAIAzureIdentityAuthConfig()

    azure_openai_endpoint: Annotated[
        str,
        Field(
            title="Azure OpenAI Endpoint",
            description=(
                "The Azure OpenAI endpoint for your resource instance. If not provided, the service default will"
                " be used."
            ),
        ),
    ] = config.first_env_var("azure_openai_endpoint", "assistant__azure_openai_endpoint") or ""

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = "gpt-4o"

    azure_content_safety_config: Annotated[
        AzureContentSafetyEvaluatorConfigModel,
        Field(
            title="Azure Content Safety Evaluator Configuration",
            description="The configuration for the Azure Content Safety evaluator.",
        ),
    ] = AzureContentSafetyEvaluatorConfigModel()

    azure_content_safety_service_config: Annotated[
        AzureContentSafetyServiceConfigModel,
        Field(
            title="Azure Content Safety Service Configuration",
            description="The configuration for the Azure Content Safety service.",
        ),
    ] = AzureContentSafetyServiceConfigModel()

    # set on the class to avoid re-creating the token provider for each client, which allows
    # the token provider to cache and re-use tokens
    _azure_bearer_token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )

    def new_client(self, api_version: str) -> openai.AsyncAzureOpenAI:
        match self.auth_config:
            case AzureOpenAIApiKeyAuthConfig():
                return openai.AsyncAzureOpenAI(
                    api_key=self.auth_config.azure_openai_api_key,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )

            case AzureOpenAIAzureIdentityAuthConfig():
                return openai.AsyncAzureOpenAI(
                    azure_ad_token_provider=AzureOpenAIServiceConfig._azure_bearer_token_provider,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key"],
        },
    )

    service_type: Annotated[Literal["OpenAI"], UISchema(widget="hidden")] = "OpenAI"

    openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ] = ""

    openai_organization_id: Annotated[
        str,
        Field(
            title="Organization ID [Optional]",
            description=(
                "The ID of the organization to use for the OpenAI API.  NOTE, this is not the same as the organization"
                " name. If you do not specify an organization ID, the default organization will be used."
            ),
        ),
        UISchema(placeholder="[optional]"),
    ] = ""

    openai_content_safety_config: Annotated[
        OpenAIContentSafetyEvaluatorConfigModel,
        Field(
            title="OpenAI Content Safety Evaluator Configuration",
            description="The configuration for the OpenAI Content Safety evaluator.",
        ),
    ] = OpenAIContentSafetyEvaluatorConfigModel()

    def new_client(self, **kwargs) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.openai_api_key,
            organization=self.openai_organization_id or None,
        )


# configuration with secrets, such as connection strings or API keys, should be in a separate model
class AssistantServiceConfigModel(BaseModel):
    service_config: Annotated[
        AzureOpenAIServiceConfig | OpenAIServiceConfig,
        Field(
            title="Service Configuration",
            discriminator="service_type",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureOpenAIServiceConfig()


# endregion
