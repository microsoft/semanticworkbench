import json
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel, create_model

from .logging import logger
from .message import ConversationMessageType, Message

UNANSWERED = "Unanswered"

TUnanswered = Literal["Unanswered"]


def modify_model_fields_to_allow_unanswered(
    model: type[BaseModel],
) -> type[BaseModel]:
    """
    Create a new artifact model with 'Unanswered' as a default and valid
    value for all fields.
    """
    field_definitions = {}
    for name, field_info in model.model_fields.items():
        annotation = Union[field_info.annotation, TUnanswered]
        default = UNANSWERED

        # Add UNANSWERED as a possible value to any regex patterns.
        metadata = field_info.metadata
        for m in metadata:
            if hasattr(m, "pattern"):
                m.pattern += f"|{UNANSWERED}"

        field_definitions[name] = (annotation, default, *metadata)

    return create_model(model.__name__, __base__=BaseModel, **field_definitions)


def is_pydantic_model(type_hint):
    """Check if a type hint refers to a subclass of Pydantic's BaseModel."""
    # Handle generic types like list[str]
    origin = get_origin(type_hint)
    if origin is not None:
        # If it's a generic type, its origin might not be BaseModel
        return issubclass(origin, BaseModel) if isinstance(origin, type) else False

    # Handle non-generic types
    return isinstance(type_hint, type) and issubclass(type_hint, BaseModel)


def make_modified_pydantic_field_classes(artifact_class: type[BaseModel]) -> dict[str, type[BaseModel]]:
    """
    Find all pydantic basemodel classes used as type hints in the first level of
    fields of the artifact, and capture modified versions of them that set
    'Unanswered' as a default and valid value for all their fields.
    """
    modified_classes = {}
    # Find any instances of BaseModel in the artifact class in the first "level" of type hints.
    for field_name, field_type in get_type_hints(artifact_class).items():
        if is_pydantic_model(field_type):
            modified_classes[field_name] = modify_model_fields_to_allow_unanswered(field_type)

    return modified_classes


def replace_type_annotations(field_annotation: type[Any] | None, replacements: dict[str, type[BaseModel]]) -> type:
    """
    Recursively replace type annotations with replacement type args where
    applicable.
    """
    if not replacements:
        return field_annotation or object

    # Get the origin of the field annotation, which is the base type for
    # generic types (e.g., List[str] -> list, Dict[str, int] -> dict, int -> None)
    origin = get_origin(field_annotation)

    # Get the type arguments of the generic type (e.g., List[str] -> str,
    # Dict[str, int] -> str, int)
    args = get_args(field_annotation)

    if origin:
        # The base type is generic; recursively replace the type annotations of the arguments
        new_args = tuple(replace_type_annotations(arg, replacements) for arg in args)
        return origin[new_args]

    # Check if the field annotation is a subclass that needs to be replaced.
    # We only replace the annotation if it is a pydantic BaseModel.
    if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModel):
        return replacements.get(field_annotation.__name__, field_annotation)

    return field_annotation or object


def artifact_from_schema(schema: type[BaseModel]) -> type[BaseModel]:
    """
    Create a new artifact model with 'Unanswered' as a default and valid
    value for all fields.
    """

    # Make modified versions of all pydantic classes used as type hints in the
    # artifact class. This is necessary because we need to set 'Unanswered' as a
    # default and valid value for all these subfields, too.
    modified_classes = make_modified_pydantic_field_classes(schema)

    field_definitions = {}
    for name, field_info in schema.model_fields.items():
        # Replace all references to the original pydantic classes with modified versions.
        field_info.annotation = replace_type_annotations(field_info.annotation, modified_classes)

        # Modify field definition to allow unanswered fields.
        annotation = Union[field_info.annotation, TUnanswered]
        default = UNANSWERED
        metadata = field_info.metadata
        for m in metadata:
            if hasattr(m, "pattern"):
                m.pattern += f"|{UNANSWERED}"

        # Update the field definition.
        field_definitions[name] = (annotation, default, *metadata)

    return create_model("Artifact", __base__=BaseModel, **field_definitions)


def get_artifact_for_prompt(artifact: BaseModel | None, failed_fields: list[str] = []) -> str:
    """
    Returns a formatted JSON-like representation of the current state of the
    artifact. Any fields that were failed are completely omitted.
    """
    if not artifact:
        return "{}"
    return json.dumps({k: v for k, v in artifact.model_dump().items() if k not in failed_fields})


def is_valid_field(artifact: BaseModel, field_name: str) -> tuple[bool, Message | None]:
    """
    Check if the field_name is a valid field in the artifact. Returns True
    if it is, False and an error message otherwise.
    """
    if field_name not in artifact.model_fields:
        error_message = f'Field "{field_name}" is not a valid field in the artifact.'
        msg = Message(
            param={"role": "assistant", "content": error_message},
            type=ConversationMessageType.ARTIFACT_UPDATE,
            turn=None,
        )
        return False, msg
    return True, None


def get_schema_for_prompt(
    original_schema: dict[str, Any],
    filter_one_field: str | None = None,
    failed_fields: list[str] = [],
) -> str:
    """Gets a clean version of the original artifact schema, optimized for use in an LLM prompt.

    Args:
        filter_one_field (str | None): If this is provided, only the schema for this one field will be returned.

    Returns:
        str: The cleaned schema
    """

    def _clean_properties(schema: dict, failed_fields: list[str]) -> str:
        """
        Clean the properties of the schema by removing unnecessary fields and
        replacing $ref with type.
        """
        properties = schema.get("properties", {})
        clean_properties = {}
        for name, property_dict in properties.items():
            if name not in failed_fields:
                cleaned_property = {}
                for k, v in property_dict.items():
                    if k in ["title", "default"]:
                        continue
                    cleaned_property[k] = v
                clean_properties[name] = cleaned_property

        clean_properties_str = str(clean_properties)
        clean_properties_str = clean_properties_str.replace("$ref", "type")
        clean_properties_str = clean_properties_str.replace("#/$defs/", "")
        return clean_properties_str

    # If filter_one_field is provided, only get the schema for that one field
    if filter_one_field:
        if filter_one_field not in original_schema["properties"]:
            logger.error(f'Field "{filter_one_field}" is not a valid field in the artifact.')
            raise ValueError(f'Field "{filter_one_field}" is not a valid field in the artifact.')
        filtered_schema = {"properties": {filter_one_field: original_schema["properties"][filter_one_field]}}
        filtered_schema.update((k, v) for k, v in original_schema.items() if k != "properties")
        schema = filtered_schema
    else:
        schema = original_schema

    properties = _clean_properties(schema, failed_fields)
    if not properties:
        logger.error("No properties found in the schema.")
        raise ValueError("No properties found in the schema.")

    types_schema = schema.get("$defs", {})
    custom_types = []
    type_name = None
    for type_name, type_info in types_schema.items():
        if f"'type': '{type_name}'" in properties:
            clean_schema = _clean_properties(type_info, [])
            if clean_schema != "{}":
                custom_types.append(f"{type_name} = {clean_schema}")

    if custom_types:
        explanation = (
            f"If you wanted to create a {type_name} object, for example, you "
            "would make a JSON object with the following keys: "
            "{', '.join(types_schema[type_name]['properties'].keys())}."
        )
        custom_types_str = "\n".join(custom_types)
        return (
            f"{properties}\n\n"
            "Here are the definitions for the custom types referenced in the artifact schema:\n"
            f"{custom_types_str}\n\n"
            f"{explanation}\n"
            "Remember that when updating the artifact, the field will be the original "
            "field name in the artifact and the JSON object(s) will be the value."
        )
    else:
        return properties
