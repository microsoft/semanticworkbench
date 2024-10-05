# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field
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
# region Evaluator Configuration
#


class OpenAIContentSafetyEvaluatorConfig(BaseModel):
    model_config = ConfigDict(
        title="OpenAI Content Safety Evaluator",
        json_schema_extra={
            "required": ["openai_api_key"],
        },
    )

    service_type: Annotated[
        Literal["openai-moderations"],
        UISchema(widget="hidden"),
    ] = "openai-moderations"

    max_item_size: Annotated[
        int,
        Field(
            title="Maximum Item Size",
            description=(
                "The maximum size of an item to send to the OpenAI moderations endpoint, this must be less than or"
                " equal to the service's maximum (2,000 characters at the time of writing)."
            ),
        ),
    ] = 2_000

    max_item_count: Annotated[
        int,
        Field(
            default=32,
            title="Maximum Item Count",
            description=(
                "The maximum number of items to send to the OpenAI moderations endpoint at a time, this must be less or"
                " equal to the service's maximum (32 items at the time of writing)."
            ),
        ),
    ]

    openai_api_key: Annotated[
        ConfigSecretStr,
        Field(
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ]


# endregion
