# Copyright (c) Microsoft. All rights reserved.

import logging
from enum import StrEnum
from typing import Annotated, Literal

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from semantic_workbench_assistant import config
from semantic_workbench_assistant.config import ConfigSecretStr, UISchema

logger = logging.getLogger(__name__)


# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Authentication Configuration
#


# TODO: move auth config to a shared location when we have another lib that uses Azure auth


class AzureAuthConfigType(StrEnum):
    Identity = "azure-identity"
    ServiceKey = "api-key"


class AzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal[AzureAuthConfigType.Identity], UISchema(widget="hidden")] = (
        AzureAuthConfigType.Identity
    )


class AzureServiceKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure service key based authentication",
        json_schema_extra={
            "required": ["azure_service_api_key"],
        },
    )

    auth_method: Annotated[Literal[AzureAuthConfigType.ServiceKey], UISchema(widget="hidden")] = (
        AzureAuthConfigType.ServiceKey
    )

    azure_service_api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            title="Azure Service API Key",
            description="The service API key for your resource instance.",
        ),
    ]


# endregion


#
# region Evaluator Configuration
#

_lazy_initialized_azure_default_credential = None


def get_azure_default_credential() -> DefaultAzureCredential:
    global _lazy_initialized_azure_default_credential
    if _lazy_initialized_azure_default_credential is None:
        _lazy_initialized_azure_default_credential = DefaultAzureCredential()
    return _lazy_initialized_azure_default_credential


class AzureContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure Content Safety Evaluator", json_schema_extra={"required": ["azure_content_safety_endpoint"]}
    )

    service_type: Annotated[Literal["azure-content-safety"], UISchema(widget="hidden")] = "azure-content-safety"

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
    ] = 10_000

    auth_config: Annotated[
        AzureIdentityAuthConfig | AzureServiceKeyAuthConfig,
        Field(
            title="Authentication Config",
            description="The authentication configuration to use for the Azure Content Safety service.",
        ),
        UISchema(hide_title=True, widget="radio"),
    ] = AzureIdentityAuthConfig()

    azure_content_safety_endpoint: Annotated[
        HttpUrl,
        Field(
            title="Azure Content Safety Service Endpoint",
            description="The endpoint to use for the Azure Content Safety service.",
            default=config.first_env_var("azure_content_safety_endpoint", "assistant__azure_content_safety_endpoint")
            or "",
        ),
    ]

    # set on the class to avoid re-authenticating for each request
    _azure_default_credential: DefaultAzureCredential | None = None

    def _get_azure_credentials(self) -> AzureKeyCredential | DefaultAzureCredential:
        match self.auth_config:
            case AzureServiceKeyAuthConfig():
                return AzureKeyCredential(self.auth_config.azure_service_api_key)

            case AzureIdentityAuthConfig():
                return get_azure_default_credential()


# endregion
