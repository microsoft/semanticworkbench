# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated

from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import ConfigSecretStr

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
    max_item_size: Annotated[
        int,
        Field(
            default=2_000,
            title="Maximum Item Size",
            description=(
                "The maximum size of an item to send to the OpenAI moderations endpoint, this must be less than or"
                " equal to the service's maximum (2,000 characters at the time of writing)."
            ),
        ),
    ]

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
            default="",
            title="OpenAI API Key",
            description="The API key to use for the OpenAI API.",
        ),
    ]


# endregion
