import inspect
import os
import types
from typing import Annotated, Any, Literal, Type, TypeVar, get_args, get_origin

import deepmerge
import dotenv
import typing_extensions
from pydantic import (
    BaseModel,
    PlainSerializer,
    SerializationInfo,
    WithJsonSchema,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


def first_env_var(*env_vars: str, include_upper_and_lower: bool = True, include_dot_env: bool = True) -> str | None:
    """
    Get the first environment variable that is set. If include_upper_and_lower is True,
    then the upper and lower case versions of the env vars will also be checked.

    .. warning::
        When running from VSCode, the .env values are not reloaded on a 'restart'. You
        need to 'stop' and then 'start' the service to get the new values from the .env
        file.
    """
    if include_upper_and_lower:
        env_vars = (*env_vars, *[env_var.upper() for env_var in env_vars], *[env_var.lower() for env_var in env_vars])

    dot_env_values = {}
    if include_dot_env:
        dotenv_path = dotenv.find_dotenv(usecwd=True)
        if dotenv_path:
            dot_env_values = dotenv.dotenv_values(dotenv_path)

    for env_var in env_vars:
        if env_var in os.environ:
            return os.environ[env_var]

        if env_var in dot_env_values:
            return dot_env_values[env_var]

    return None


def overwrite_defaults_from_env(model: ModelT, prefix="", separator="__") -> ModelT:
    """
    Overwrite string fields that currently have their default values. Values are
    overwritten with values from environment variables or .env file. If a field
    is a BaseModel, it will be recursively updated.
    """

    non_defaults = model.model_dump(exclude_defaults=True).keys()

    updates: dict[str, str | BaseModel] = {}

    for field, field_info in model.model_fields.items():
        value = getattr(model, field)
        env_var = f"{prefix}{separator}{field}".upper()

        match value:
            case BaseModel():
                updates[field] = overwrite_defaults_from_env(value, prefix=env_var, separator=separator)
                continue

            case str() | (str() | None):
                if field in non_defaults:
                    continue

                alias_env_vars = []
                match field_info.validation_alias:
                    case None:
                        pass

                    case str():
                        alias_env_vars = [
                            f"{prefix}{separator}{field_info.validation_alias}".upper(),
                            field_info.validation_alias.upper(),
                        ]

                    case _:
                        aliases = field_info.validation_alias.convert_to_aliases()
                        for alias in aliases:
                            if isinstance(alias, list) and isinstance(alias[0], str):
                                alias_env_vars.append(f"{prefix}{separator}{alias[0]}".upper())
                                alias_env_vars.append(str(alias[0]).upper())

                env_value = first_env_var(env_var, *alias_env_vars)
                if env_value is not None:
                    updates[field] = env_value

            case _:
                continue

    return model.model_copy(update=updates, deep=True)


class UISchema:
    """
    UISchema defines the uiSchema for a field on a Pydantic config model. The uiSchema
    directs the workbench app on how to render the field in the UI.
    This class is intended to be used as a type annotation. See the example.
    The full uiSchema for a model can be extracted by passing the model type to `get_ui_schema`.

    The schema parameter provides full control over the schema. The additional parameters are
    shortcuts for common options.

    uiSchema reference:
    https://rjsf-team.github.io/react-jsonschema-form/docs/api-reference/uiSchema/

    Parameters:
    - schema: An optional uiSchema dictionary. If the schema is provided, and any of the other
        parameters are also provided, they will be merged into the schema.
    - widget: The widget to use for the field in the UI. Useful if you want to use a different
        widget than the default for the field type.
    - placeholder: The placeholder text to display in the field.
    - hide_title: Whether to hide the title of the field in the UI.
    - enable_markdown_in_description: Whether to enable markdown when rendering the field
        description.

    Example:
    ```
    class MyConfig(BaseModel):
        description: Annotated[str, UISchema(widget="textarea")]
        option: Annotated[Union[Literal["yes"], Literal["no"]], UISchema(widget="radio")]


    ui_schema = get_ui_schema(MyConfig)
    ```
    """

    def __init__(
        self,
        schema: dict[str, Any] | None = None,
        help: str | None = None,
        widget: Literal["textarea", "radio", "checkbox", "hidden"] | str | None = None,
        placeholder: str | None = None,
        hide_title: bool | None = None,
        enable_markdown_in_description: bool | None = None,
    ) -> None:
        self.schema = schema or {}
        ui_options: dict[str, Any] = self.schema.get("ui:options", {})
        if help:
            ui_options.update({"help": help})
        if widget:
            ui_options.update({"widget": widget})
        if hide_title is not None:
            ui_options.update({"hide_title": hide_title})
        if enable_markdown_in_description is not None:
            ui_options.update({"enableMarkdownInDescription": enable_markdown_in_description})
        if placeholder is not None:
            ui_options.update({"placeholder": placeholder})
        if ui_options:
            self.schema.update({"ui:options": ui_options})


ENABLE_SECRET_MASKING_CONTEXT_KEY = "enable_secret_masking"


def config_secret_str_json_serializer(value: str, info: SerializationInfo) -> str:
    """JSON serializer for secret strings that masks the value unless explicitly requested."""
    if not value:
        return value

    if info.context and info.context.get(ENABLE_SECRET_MASKING_CONTEXT_KEY, True) is False:
        return value

    return "*" * 10


"""
    Type alias for string fields that contain secrets in Pydantic models used for assistant-app
    configuration. Fields with this type will be serialized as masked values in JSON, for example
    when returning the configuration to the client.
    Additionally, the JSON schema for the field is updated to indicate that the field is write-only
    and should be displayed as a password field in the UI.
"""
ConfigSecretStr = typing_extensions.TypeAliasType(
    "ConfigSecretStr",
    Annotated[
        str,
        PlainSerializer(
            func=config_secret_str_json_serializer,
            return_type=str,
            when_used="json-unless-none",
        ),
        WithJsonSchema({
            "type": "string",
            "writeOnly": True,
            "format": "password",
        }),
        UISchema(
            widget="password",
        ),
    ],
)


_AnnotationTypeT = TypeVar("_AnnotationTypeT")


def _get_annotations_of_type(
    type_: Type, annotation_type: type[_AnnotationTypeT]
) -> dict[str, tuple[Type, list[_AnnotationTypeT]]]:
    annotations = inspect.get_annotations(type_)

    result = {}
    for ann_name, ann_type in annotations.items():
        if isinstance(ann_type, typing_extensions.TypeAliasType):
            # Unwrap the type alias
            ann_type = ann_type.__value__

        if get_origin(ann_type) is not Annotated:
            result[ann_name] = (ann_type, [])
            continue

        first_arg, *extra_args = get_args(ann_type)
        matching_annotations = [a for a in extra_args if isinstance(a, annotation_type)]
        result[ann_name] = (first_arg, matching_annotations)

    return result


def get_ui_schema(type_: Type[BaseModel]) -> dict[str, Any]:
    """Gets the unified UI schema for a Pydantic model, built from the UISchema type annotations."""
    try:
        annotations = _get_annotations_of_type(type_, UISchema)
    except TypeError:
        return {}

    ui_schema = {}
    for field_name, v in annotations.items():
        field_type, annotations = v

        field_ui_schema = {}
        for annotation in annotations:
            field_ui_schema.update(annotation.schema)

        field_types = [field_type]
        if isinstance(field_type, types.UnionType):
            field_types = field_type.__args__

        for field_type in field_types:
            type_ui_schema = get_ui_schema(field_type)
            field_ui_schema = deepmerge.always_merger.merge(field_ui_schema, type_ui_schema)

        if field_ui_schema:
            ui_schema[field_name] = field_ui_schema

    return ui_schema
