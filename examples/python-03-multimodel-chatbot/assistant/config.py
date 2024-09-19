import pathlib
from typing import Annotated, Literal

import google.generativeai as genai
import openai
from anthropic import AsyncAnthropic
from assistant.responsible_ai.openai_evaluator import \
    OpenAIContentSafetyEvaluatorConfigModel
from azure.identity.aio import (DefaultAzureCredential,
                                get_bearer_token_provider)
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant import config
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

from .responsible_ai.azure_evaluator import (
    AzureContentSafetyEvaluatorConfigModel,
    AzureContentSafetyServiceConfigModel)

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


# helper for loading the guardrails prompt from a text file
def load_guardrails_prompt_from_text_file() -> str:
    # get directory relative to this module
    directory = pathlib.Path(__file__).parent

    # get the file path for the guardrails prompt
    file_path = directory / "responsible_ai" / "guardrails_prompt.txt"

    # read the guardrails prompt from the file
    with open(file_path, "r") as file:
        return file.read()


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
    ] = load_guardrails_prompt_from_text_file()

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
    ] = "Hello! How can I help you today?"

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig()

    # add any additional configuration fields


# endregion

#
# region Azure OpenAI Service Configuration
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
            title="Azure Content Safety Configuration",
            description="The configuration for the Azure Content Safety API.",
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

    def new_client(self, api_version: str) -> openai.AsyncOpenAI:
        match self.auth_config.auth_method:
            case "api-key":
                return openai.AsyncAzureOpenAI(
                    api_key=self.auth_config.azure_openai_api_key,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )

            case "azure-identity":
                return openai.AsyncAzureOpenAI(
                    azure_ad_token_provider=AzureOpenAIServiceConfig._azure_bearer_token_provider,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )


# endregion

#
# region OpenAI Service Configuration
#


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key", "openai_model"],
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

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"

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

# endregion

#
# region Anthropic Service Configuration
#

class AnthropicServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Anthropic",
        json_schema_extra={
            "required": ["anthropic_api_key", "anthropic_model"],
        },
    )

    service_type: Annotated[Literal["Anthropic"], UISchema(widget="hidden")] = "Anthropic"

    anthropic_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Anthropic API Key",
            description="The API key to use for the Anthropic API.",
        ),
    ] = ""

    anthropic_model: Annotated[
        str,
        Field(title="Anthropic Model", description="The Anthropic model to use for generating responses."),
    ] = "claude-3-5-sonnet-20240620"

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

    def new_client(self, **kwargs) -> AsyncAnthropic:
        return AsyncAnthropic(api_key=self.anthropic_api_key)

# endregion

#
# region Gemini Service Configuration
#

class GeminiServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Gemini",
        json_schema_extra={
            "required": ["gemini_api_key", "gemini_model"],
        },
    )

    service_type: Annotated[Literal["Gemini"], UISchema(widget="hidden")] = "Gemini"

    gemini_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Gemini API Key",
            description="The API key to use for the Gemini API.",
        ),
    ] = ""

    gemini_model: Annotated[
        str,
        Field(title="Gemini Model", description="The Gemini model to use for generating responses."),
    ] = "gemini-1.5-pro"

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

    def new_client(self, **kwargs) -> genai.GenerativeModel:
        genai.configure(api_key=self.gemini_api_key)
        return genai.GenerativeModel(self.gemini_model)

# endregion

#
# region Assistant Services Configuration selection
#

# configuration with secrets, such as connection strings or API keys, should be in a separate model
class AssistantServiceConfigModel(BaseModel):
    service_config: Annotated[
        AzureOpenAIServiceConfig | OpenAIServiceConfig | AnthropicServiceConfig | GeminiServiceConfig,
        Field(
            title="Service Configuration",
            discriminator="service_type",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureOpenAIServiceConfig()


# endregion
