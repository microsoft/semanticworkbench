import pathlib
from abc import abstractmethod
from enum import StrEnum
from typing import Annotated, Any

import openai_client
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema

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


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(BaseModel):
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
    ] = "Hello! How can I help you today?"

    chat_driver_config: Annotated[
        ChatDriverConfig,
        Field(
            title="Chat Driver Configuration",
            description="The configuration for the chat driver.",
        ),
    ] = ChatDriverConfig()

    service_config: openai_client.ServiceConfig = openai_client.AzureOpenAIServiceConfig()

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety Configuration",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    # add any additional configuration fields


# endregion
