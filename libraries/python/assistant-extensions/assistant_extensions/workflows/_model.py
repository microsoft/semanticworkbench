from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field
from semantic_workbench_assistant.config import UISchema


class UserMessage(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["status_label", "message"],
        }
    )

    status_label: Annotated[
        str,
        Field(
            description="The status label to be displayed when the message is sent to the assistant.",
        ),
    ] = ""

    message: Annotated[
        str,
        Field(
            description="The message to be sent to the assistant.",
        ),
        UISchema(widget="textarea"),
    ] = ""


class UserProxyWorkflowDefinition(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["command", "name", "description", "user_messages"],
        }
    )

    workflow_type: Annotated[
        Literal["user_proxy"],
        Field(
            description="The type of workflow.",
        ),
        UISchema(widget="hidden"),
    ] = "user_proxy"
    command: Annotated[
        str,
        Field(
            description="The command that will trigger the workflow. The command should be unique and not conflict with other commands and should only include alphanumeric characters and underscores.",
        ),
    ] = ""
    name: Annotated[
        str,
        Field(
            description="The name of the workflow, to be displayed in the help, logs, and status messages.",
        ),
    ] = ""
    description: Annotated[
        str,
        Field(
            description="A description of the workflow that will be displayed in the help.",
        ),
        UISchema(widget="textarea"),
    ] = ""
    user_messages: Annotated[
        list[UserMessage],
        Field(
            description="A list of user messages that will be sequentially sent to the assistant during the workflow.",
        ),
    ] = []


WorkflowDefinition = Union[UserProxyWorkflowDefinition]


class WorkflowsConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(
            description="Enable the workflows feature.",
        ),
    ] = False

    workflow_definitions: Annotated[
        list[WorkflowDefinition],
        Field(
            description="A list of workflow definitions.",
        ),
    ] = []
