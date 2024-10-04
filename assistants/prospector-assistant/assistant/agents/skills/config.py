import pathlib
from typing import Annotated

from pydantic import BaseModel, Field
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
    directory = pathlib.Path(__file__).parent.parent.parent

    # get the file path for the prompt file
    file_path = directory / "text_includes" / filename

    # read the prompt from the file
    return file_path.read_text()


# endregion


#
# region Agent Configuration
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


class SkillsAgentConfigModel(BaseModel):
    enable_skills: Annotated[
        bool,
        Field(
            description=load_text_include("skills_agent_enable_skills.md"),
        ),
        UISchema(enable_markdown_in_description=True),
    ] = False

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

    # add any additional configuration fields


# endregion
