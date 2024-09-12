from typing import Annotated
from pydantic import Field, BaseModel

# The semantic workbench app uses react-jsonschema-form for rendering
# dyanmic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(BaseModel):
    enable_debug_output: Annotated[
        bool,
        Field(
            title="Include Debug Output",
            description="Include debug output on conversation messages.",
        ),
    ] = False

    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
    ] = "Hello! I am an echo example, I will repeat what you say."

    # add any additional configuration fields


ui_schema = {
    # add UI schema for the additional configuration fields
    # see: https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema
}
