# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Literal

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel, ConfigDict, Field
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


class AzureIdentityAuthConfig(BaseModel):
    model_config = ConfigDict(title="Azure identity based authentication")

    auth_method: Annotated[Literal["azure-identity"], UISchema(widget="hidden")] = "azure-identity"


class AzureServiceKeyAuthConfig(BaseModel):
    model_config = ConfigDict(
        title="Azure service key based authentication",
        json_schema_extra={
            "required": ["api_key"],
        },
    )

    auth_method: Annotated[Literal["api-key"], UISchema(widget="hidden")] = "api-key"

    api_key: Annotated[
        # ConfigSecretStr is a custom type that should be used for any secrets.
        # It will hide the value in the UI.
        ConfigSecretStr,
        Field(
            default="",
            title="Azure Service API Key",
            description="The service API key for your resource instance.",
        ),
        UISchema(placeholder="[optional]"),
    ]


# endregion


#
# region Evaluator Configuration
#


class AzureContentSafetyEvaluatorConfig(BaseModel):
    warn_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            default=2,
            title="Warn at Severity",
            description="The severity level (0, 2, 4, 6) at which to warn about content safety.",
        ),
    ]

    fail_at_severity: Annotated[
        Literal[0, 2, 4, 6],
        Field(
            default=4,
            title="Fail at Severity",
            description="The severity level (0, 2, 4, 6) at which to fail content safety.",
        ),
    ]

    max_request_length: Annotated[
        int,
        Field(
            default=10_000,
            title="Maximum Request Length",
            description=(
                "The maximum length of content to send to the Azure Content Safety service per request, this must less"
                " or equal to the service's maximum (10,000 characters at the time of writing). The evaluator will"
                " split and send the content in batches if it exceeds this length."
            ),
        ),
    ]

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
