import pathlib
from typing import Annotated

import openai_client
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from openai_client import AzureOpenAIServiceConfig
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema, first_env_var

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


class ChatDriverConfig(BaseModel):
    instructions: Annotated[
        str,
        Field(
            title="Instructions",
            description="The prompt used to instruct the behavior of the AI assistant.",
        ),
        UISchema(widget="textarea"),
    ] = "You are a helpful assistant."

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for chat driver."),
    ] = "gpt-4o"


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


# The workbench app builds dynamic forms based on the configuration model and UI
# schema.
class AssistantConfigModel(BaseModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include Debug Output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

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
    ] = "Hi."

    high_token_usage_warning: Annotated[
        HighTokenUsageWarning,
        Field(
            title="High Token Usage Warning",
            description="Configuration for the high token usage warning.",
        ),
    ] = HighTokenUsageWarning()

    general_model_service_config: Annotated[
        openai_client.ServiceConfig,
        Field(
            title="General Model Service Configuration",
            description="The configuration for the general model service.",
        ),
    ] = AzureOpenAIServiceConfig.model_construct(
        azure_openai_deployment=first_env_var("general_model_deployment"),
        azure_openai_endpoint=first_env_var("general_model_endpoint"),
    )

    reasoning_model_service_config: Annotated[
        openai_client.ServiceConfig,
        Field(
            title="Reasoning Model Service Configuration",
            description="The configuration for the reasoning model service.",
        ),
    ] = AzureOpenAIServiceConfig.model_construct(
        azure_openai_deployment=first_env_var("reasoning_model_deployment"),
        azure_openai_endpoint=first_env_var("reasoning_model_endpoint"),
    )

    # openai_service_config: Annotated[
    #     openai_client.ServiceConfig,
    #     Field(
    #         title="OpenAI Service Configuration",
    #     ),
    # ] = OpenAIServiceConfig.model_construct(openai_api_key=first_env_var("openai_api_key"))

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    # add any additional configuration fields

    chat_driver_config: Annotated[
        ChatDriverConfig,
        Field(
            title="Chat Driver Configuration",
            description="The configuration for the chat driver.",
        ),
    ] = ChatDriverConfig()

    metadata_path: Annotated[
        str,
        Field(
            title="Metadata Path",
            description="The path for assistant metadata.",
        ),
    ] = ".data"

    bing_subscription_key: Annotated[
        str,
        Field(
            title="Bing Subscription Key",
            description="The Bing subscription key to use for the Bing search API.",
        ),
    ] = first_env_var("bing_subscription_key", "assistant__bing_subscription_key") or ""

    bing_search_url: Annotated[
        str,
        Field(
            title="Bing Search URL",
            description="The Bing search URL to use for the Bing search API.",
        ),
    ] = first_env_var("bing_search_url", "assistant__bing_search_url") or "https://api.bing.microsoft.com/v7.0/search"


# endregion
