from typing import Annotated, Self
from pydantic import Field
from semantic_workbench_assistant import config, assistant_base

# The semantic workbench app uses react-jsonschema-form for rendering
# dyanmic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(assistant_base.AssistantConfigModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include Debug Output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

    def overwrite_defaults_from_env(self) -> Self:
        """
        Overwrite string fields that currently have their default values. Values are
        overwritten with values from environment variables or .env file. If a field
        is a BaseModel, it will be recursively updated.
        """
        updated = config.overwrite_defaults_from_env(self, prefix="assistant", separator="__")

        # Custom: add any additional handling for nested models

        return updated

    # add any additional configuration fields


ui_schema = {
    # add UI schema for the additional configuration fields
    # see: https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
}
