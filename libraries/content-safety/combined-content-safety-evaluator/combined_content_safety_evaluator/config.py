# Copyright (c) Microsoft. All rights reserved.

import logging
from enum import Enum
from typing import Annotated, Literal

from attr import dataclass
from azure_content_safety_evaluator import AzureContentSafetyType

logger = logging.getLogger(__name__)


# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Evaluator Configuration
#


@dataclass
class ContentSafetyTypeDefinition:
    key: str
    display_name: str


class ContentSafetyType(Enum):
    AzureContentSafety = AzureContentSafetyType
    OpenAIModerationsEndpoint = ("openai_moderations_endpoint", "OpenAI Moderations Endpoint")

    def __init__(self, key: str, display_name: str):
        self.key = key
        self.display_name = display_name


def _content_safety_type_display_name(content_safety_type: ContentSafetyType) -> str:
    content_safety_type_friendly_names = {
        ContentSafetyType.AzureContentSafety: "Azure Content Safety",
        ContentSafetyType.OpenAIModerationsEndpoint: "OpenAI Moderations Endpoint",
    }

    return content_safety_type_friendly_names[content_safety_type]


class CombinedContentSafetyEvaluatorConfigModel(BaseModel):
    model_config = ConfigDict(
        title="Content Safety Configuration",
        json_schema_extra={
            "required": ["content_safety_type"],
        },
    )

    content_safety_type: Annotated[ContentSafetyType, UISchema(widget="hidden")] = ContentSafetyType.AzureContentSafety

    @property
    def display_name(self) -> str:
        # get from the class title
        return self.model_config.get("title") or self.content_safety_type.value


class AzureContentSafetyEvaluatorConfigModel(BaseModel):
    service_type: Annotated[Literal["Azure OpenAI"], UISchema(widget="hidden")] = "Azure OpenAI"

    warn_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            title="Warn at Severity",
            description="The severity level (0, 2, 4, 6) at which to warn about content safety.",
        ),
    ] = 2

    fail_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            title="Fail at Severity",
            description="The severity level (0, 2, 4, 6) at which to fail content safety.",
        ),
    ] = 4

    max_request_length: Annotated[
        int,
        Field(
            title="Maximum Request Length",
            description=(
                "The maximum length of content to send to the Azure Content Safety service per request, this must less"
                " or equal to the service's maximum (10,000 characters at the time of writing). The evaluator will"
                " split and send the content in batches if it exceeds this length."
            ),
        ),
    ] = 10000


# endregion


#
# region Azure Content Safety Service Configuration
#


class AzureContentSafetyServiceIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal["azure-identity"], UISchema(widget="hidden")] = "azure-identity"


class AzureContentSafetyServiceKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="API key based authentication",
        json_schema_extra={
            "required": ["azure_content_safety_service_key"],
        },
    )

    auth_method: Annotated[Literal["api-key"], UISchema(widget="hidden")] = "api-key"

    azure_content_safety_service_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure Content Safety Service Key",
            description="The Azure Content Safety service key for your resource instance.",
        ),
        UISchema(placeholder="[optional]"),
    ] = ""


class AzureContentSafetyServiceConfigModel(BaseModel):
    auth_config: Annotated[
        AzureContentSafetyServiceIdentityAuthConfig | AzureContentSafetyServiceKeyAuthConfig,
        Field(
            title="Authentication Config",
            description="The authentication configuration to use for the Azure Content Safety service.",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureContentSafetyServiceIdentityAuthConfig()

    azure_content_safety_endpoint: Annotated[
        str,
        Field(
            title="Azure Content Safety Service Endpoint",
            description="The endpoint to use for the Azure Content Safety service.",
        ),
    ] = config.first_env_var("azure_content_safety_endpoint", "assistant__azure_content_safety_endpoint") or ""

    # set on the class to avoid re-authenticating for each request
    def _get_azure_credentials(self) -> AzureKeyCredential | DefaultAzureCredential:
        match self.auth_config.auth_method:
            case "api-key":
                return AzureKeyCredential(self.auth_config.azure_content_safety_service_key)

            case "azure-identity":
                return DefaultAzureCredential()


# endregion
