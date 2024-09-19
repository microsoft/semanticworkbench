from typing import Annotated

from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

# The semantic workbench app uses react-jsonschema-form for rendering
# dyanmic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


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
        UISchema(
            widget="textarea",
        ),
    ] = "Hello! I am an echo example, I will repeat what you say."

    # add any additional configuration fields
