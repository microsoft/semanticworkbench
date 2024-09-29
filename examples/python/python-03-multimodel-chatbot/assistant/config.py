import pathlib
from abc import abstractmethod
from enum import StrEnum
from typing import Annotated, Any, Literal

import google.generativeai as genai
import openai
from anthropic import AsyncAnthropic
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant import config
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

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


# mapping service types to an enum to use as keys in the configuration model
# to prevent errors if the service type is changed where string values were used
class ServiceType(StrEnum):
    AzureOpenAI = "azure_openai"
    OpenAI = "openai"
    Anthropic = "anthropic"
    Gemini = "gemini"
    Ollama = "ollama"


class ServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Service Configuration",
        json_schema_extra={
            "required": ["service_type"],
        },
    )

    service_type: Annotated[str, UISchema(widget="hidden")] = ""

    @property
    def service_type_display_name(self) -> str:
        # get from the class title
        return self.model_config.get("title") or self.service_type

    @abstractmethod
    def new_client(self, **kwargs) -> Any:
        pass


# endregion


#
# region Azure OpenAI Service Configuration
#


class AzureAuthConfigType(StrEnum):
    Identity = "azure-identity"
    ServiceKey = "api-key"


class AzureOpenAIAzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal[AzureAuthConfigType.Identity], UISchema(widget="hidden")] = (
        AzureAuthConfigType.Identity
    )


class AzureOpenAIApiKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_openai_api_key"],
        },
    )

    auth_method: Annotated[Literal[AzureAuthConfigType.ServiceKey], UISchema(widget="hidden")] = (
        AzureAuthConfigType.ServiceKey
    )

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


class AzureOpenAIServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_endpoint"],
        },
    )

    service_type: Annotated[Literal[ServiceType.AzureOpenAI], UISchema(widget="hidden")] = ServiceType.AzureOpenAI

    auth_config: Annotated[
        AzureOpenAIAzureIdentityAuthConfig | AzureOpenAIApiKeyAuthConfig,
        Field(
            title="Authentication Configuration",
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

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = "gpt-4o"

    # set on the class to avoid re-creating the token provider for each client, which allows
    # the token provider to cache and re-use tokens
    _azure_bearer_token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )

    def new_client(self, **kwargs) -> openai.AsyncOpenAI:
        api_version = kwargs.get("api_version", "2024-06-01")

        match self.auth_config.auth_method:
            case AzureAuthConfigType.ServiceKey:
                return openai.AsyncAzureOpenAI(
                    api_key=self.auth_config.azure_openai_api_key,
                    azure_deployment=self.azure_openai_deployment,
                    azure_endpoint=self.azure_openai_endpoint,
                    api_version=api_version,
                )

            case AzureAuthConfigType.Identity:
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


class OpenAIServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key", "openai_model"],
        },
    )

    service_type: Annotated[Literal[ServiceType.OpenAI], UISchema(widget="hidden")] = ServiceType.OpenAI

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

    def new_client(self, **kwargs) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.openai_api_key,
            organization=self.openai_organization_id or None,
        )


# endregion

#
# region Anthropic Service Configuration
#


class AnthropicServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="Anthropic",
        json_schema_extra={
            "required": ["anthropic_api_key", "anthropic_model"],
        },
    )

    service_type: Annotated[Literal[ServiceType.Anthropic], UISchema(widget="hidden")] = ServiceType.Anthropic

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

    def new_client(self, **kwargs) -> AsyncAnthropic:
        return AsyncAnthropic(api_key=self.anthropic_api_key)


# endregion

#
# region Gemini Service Configuration
#


class GeminiServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="Gemini",
        json_schema_extra={
            "required": ["gemini_api_key", "gemini_model"],
        },
    )

    service_type: Annotated[Literal[ServiceType.Gemini], UISchema(widget="hidden")] = ServiceType.Gemini

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

    def new_client(self, **kwargs) -> genai.GenerativeModel:
        genai.configure(api_key=self.gemini_api_key)
        return genai.GenerativeModel(self.gemini_model)


# endregion

#
# region Ollama Service Configuration
#


class OllamaServiceConfig(ServiceConfig):
    model_config = ConfigDict(
        title="Ollama",
        json_schema_extra={
            "required": ["ollama_endpoint", "ollama_model"],
        },
    )

    service_type: Annotated[Literal[ServiceType.Ollama], UISchema(widget="hidden")] = ServiceType.Ollama

    ollama_endpoint: Annotated[
        str,
        Field(
            title="Ollama Endpoint",
            description="The endpoint for the Ollama API.",
        ),
    ] = "http://127.0.0.1:11434/v1/"

    ollama_model: Annotated[
        str,
        Field(title="Ollama Model", description="The Ollama model to use for generating responses."),
    ] = "llama3.1"

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="Same as Ollama model, used in later calls to OpenAI API."),
        UISchema(widget="hidden"),
    ] = ollama_model

    openai_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title=" API Key",
            description="Required by OpenAI API but ignored by Ollama",
        ),
        UISchema(placeholder="[optional]"),
    ] = "ollama"

    def new_client(self, **kwargs) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            base_url=f"{self.ollama_endpoint}/v1",
        )


# endregion


#
# region Assistant Configuration
#


class RequestConfig(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
        json_schema_extra={
            "required": ["max_tokens", "response_tokens"],
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
        UISchema(widget="textarea"),
    ] = load_text_include("guardrails_prompt.txt")

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
        UISchema(widget="textarea"),
    ] = "Hello! How can I help you today?"

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig()

    service_config: Annotated[
        AzureOpenAIServiceConfig
        | OpenAIServiceConfig
        | AnthropicServiceConfig
        | GeminiServiceConfig
        | OllamaServiceConfig,
        Field(
            title="Service Configuration",
            discriminator="service_type",
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIServiceConfig()

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    # add any additional configuration fields


# endregion
