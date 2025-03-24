from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AssistantPutRequestModel(BaseModel):
    assistant_name: str
    template_id: str


class AssistantResponseModel(BaseModel):
    id: str


class StateDescriptionResponseModel(BaseModel):
    id: str
    display_name: str
    description: str


class StateDescriptionListResponseModel(BaseModel):
    states: list[StateDescriptionResponseModel]


class StateResponseModel(BaseModel):
    """
    This model is used by the Workbench to render the state in the UI.
    See: https://github.com/rjsf-team/react-jsonschema-form for
    the use of data, json_schema, and ui_schema.
    """

    id: str
    data: dict[str, Any]
    json_schema: dict[str, Any] | None
    ui_schema: dict[str, Any] | None


class StatePutRequestModel(BaseModel):
    data: dict[str, Any]


class ConfigResponseModel(BaseModel):
    config: dict[str, Any]
    errors: list[str] | None = None
    json_schema: dict[str, Any] | None
    ui_schema: dict[str, Any] | None


class ConfigPutRequestModel(BaseModel):
    config: dict[str, Any]


class AssistantTemplateModel(BaseModel):
    id: str
    name: str
    description: str
    config: ConfigResponseModel


class ServiceInfoModel(BaseModel):
    assistant_service_id: str
    name: str
    templates: list[AssistantTemplateModel]
    metadata: dict[str, Any] = {}


class ConversationPutRequestModel(BaseModel):
    id: str
    title: str


class ConversationResponseModel(BaseModel):
    id: str


class ConversationListResponseModel(BaseModel):
    conversations: list[ConversationResponseModel]
