from typing import Annotated, Literal, Self
from pydantic import BaseModel, Field, ConfigDict, AliasChoices
import openai
from semantic_workbench_assistant import config, assistant_base

# The semantic workbench app uses react-jsonschema-form for rendering
# dyanmic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/


class AzureOpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure OpenAI",
        json_schema_extra={
            "required": ["azure_openai_deployment", "azure_openai_api_version"],
        },
    )

    service_type: Literal["Azure OpenAI"] = "Azure OpenAI"

    azure_openai_api_key: Annotated[
        str,
        Field(
            title="Azure OpenAI API Key",
            description=(
                "The Azure OpenAI API key for your resource instance.  If not provided, the service default will be"
                " used."
            ),
            validation_alias=AliasChoices("azure_openai_api_key", "assistant__azure_openai_api_key"),
        ),
    ] = ""

    azure_openai_endpoint: Annotated[
        str,
        Field(
            title="Azure OpenAI Endpoint",
            description=(
                "The Azure OpenAI endpoint for your resource instance. If not provided, the service default will"
                " be used."
            ),
            validation_alias=AliasChoices("azure_openai_api_key", "assistant__azure_openai_endpoint"),
        ),
    ] = ""

    azure_openai_deployment: Annotated[
        str,
        Field(
            title="Azure OpenAI Deployment",
            description="The Azure OpenAI deployment to use.",
        ),
    ] = "gpt-4o"

    openai_model: Annotated[
        str,
        Field(
            title="OpenAI Model",
            description="The OpenAI model to use.",
        ),
    ] = "gpt-4o"

    azure_openai_api_version: Annotated[
        str,
        Field(
            title="Azure OpenAI API Version",
            description="The Azure OpenAI API version.",
        ),
    ] = "2023-05-15"

    def validate_required_fields(self) -> tuple[bool, str]:
        if (
            self.azure_openai_endpoint
            and self.azure_openai_api_version
            and self.azure_openai_api_key
            and self.azure_openai_deployment
        ):
            return (True, "")

        return (False, "Please set the Azure OpenAI endpoint, API version, API key and deployment in the config.")

    def new_client(self) -> openai.AsyncOpenAI:
        return openai.AsyncAzureOpenAI(
            api_key=self.azure_openai_api_key,
            azure_deployment=self.azure_openai_deployment,
            api_version=self.azure_openai_api_version,
            azure_endpoint=self.azure_openai_endpoint,
        )


class OpenAIServiceConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI",
        json_schema_extra={
            "required": ["openai_api_key", "openai_model"],
        },
    )

    service_type: Literal["OpenAI"] = "OpenAI"

    openai_api_key: Annotated[
        str,
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
    ] = ""

    def validate_required_fields(self) -> tuple[bool, str]:
        if self.openai_api_key and self.openai_model:
            return (True, "")

        return (False, "Please set the OpenAI API key and model in the config.")

    def new_client(self) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.openai_api_key,
            organization=self.openai_organization_id or None,
        )


class RequestConfig(BaseModel):
    model_config = ConfigDict(
        title="Response Generation",
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
class AssistantConfigModel(assistant_base.AssistantConfigModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include Debug Output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

    persona_prompt: Annotated[
        str,
        Field(
            title="Persona Prompt",
            description="The prompt used to define the persona of the AI assistant.",
        ),
    ] = "You are an AI assistant that helps people with their work."

    request_config: Annotated[
        RequestConfig,
        Field(
            title="Request Configuration",
        ),
    ] = RequestConfig()

    service_config: Annotated[
        AzureOpenAIServiceConfig | OpenAIServiceConfig,
        Field(
            title="Service Configuration",
            discriminator="service_type",
        ),
    ] = AzureOpenAIServiceConfig()

    def overwrite_defaults_from_env(self) -> Self:
        """
        Overwrite string fields that currently have their default values. Values are
        overwritten with values from environment variables or .env file. If a field
        is a BaseModel, it will be recursively updated.
        """
        updated = config.overwrite_defaults_from_env(self, prefix="assistant", separator="__")
        updated.service_config = config.overwrite_defaults_from_env(
            updated.service_config, prefix="assistant", separator="__"
        )
        return updated

    # add any additional configuration fields


ui_schema = {
    "persona_prompt": {
        "ui:widget": "textarea",
    },
    "service_config": {
        "ui:widget": "radio",
        "ui:options": {
            "hide_title": True,
        },
        "service_type": {
            "ui:widget": "hidden",
        },
        "openai_api_key": {
            "ui:widget": "password",
        },
        "openai_organization_id": {
            "ui:placeholder": "[optional]",
        },
        "azure_openai_api_key": {
            "ui:widget": "password",
            "ui:placeholder": "[optional]",
        },
        "azure_openai_endpoint": {
            "ui:placeholder": "[optional]",
        },
    },
    # add UI schema for the additional configuration fields
    # see: https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
}
