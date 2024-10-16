import pathlib
from abc import abstractmethod
from enum import StrEnum
from typing import Annotated, Any

import openai_client
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

from .agents.guided_conversation_agent import GuidedConversationAgentConfigModel

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
# region Assistant Configuration
#

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
                " is 128k tokens, but varies by model [https://platform.openai.com/docs/models]"
                "(https://platform.openai.com/docs/models)."
            ),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = 128_000

    response_tokens: Annotated[
        int,
        Field(
            title="Response Tokens",
            description=(
                "The number of tokens to use for the response, will reduce the number of tokens available for the"
                " prompt. Current max supported by OpenAI is 4096 tokens [https://platform.openai.com/docs/models]"
                "(https://platform.openai.com/docs/models)."
            ),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = 4_048

    openai_model: Annotated[
        str,
        Field(title="OpenAI Model", description="The OpenAI model to use for generating responses."),
    ] = "gpt-4o"


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(BaseModel):
    guided_conversation_agent: Annotated[
        GuidedConversationAgentConfigModel,
        Field(
            title="Guided Conversation Agent Configuration",
            description="Configuration for the guided conversation agent.",
        ),
    ] = GuidedConversationAgentConfigModel()

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
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    # add any additional configuration fields


# endregion
