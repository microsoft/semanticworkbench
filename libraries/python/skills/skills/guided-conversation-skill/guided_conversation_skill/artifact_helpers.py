import json
from typing import TYPE_CHECKING, Any

# from datamodel_code_generator import DataModelType, PythonVersion
# from datamodel_code_generator.format import DatetimeClassType
# from datamodel_code_generator.model import get_data_model_types
# from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
# from pydantic import BaseModel
import jsonschema
from pydantic import BaseModel

if TYPE_CHECKING:
    pass


from .logging import add_serializable_data, logger


class UpdateAttempt(BaseModel):
    field_value: str
    error: str


# UNANSWERED = "Unanswered"

# TUnanswered = Literal["Unanswered"]


# def get_artifact_from_schema_and_data(schema: dict[str, Any], data: dict[str, Any]) -> BaseModel:
#     """
#     Create a Pydantic model from a dict representing a JSON Schema and fill it with data.
#     """
#     model = get_model_from_schema(schema)
#     return model(**data)


# def get_model_from_schema(schema: dict[str, Any]) -> type[BaseModel]:
#     """
#     Create a Pydantic model from a dict representing a JSON Schema.
#     """
#     data_model_types = get_data_model_types(
#         DataModelType.PydanticV2BaseModel,
#         target_python_version=PythonVersion.PY_311,
#         target_datetime_class=DatetimeClassType.Datetime,
#     )

#     parser = JsonSchemaParser(
#         str(schema),
#         data_model_type=data_model_types.data_model,
#         data_model_root_type=data_model_types.root_model,
#         data_model_field_type=data_model_types.field_model,
#         data_type_manager_type=data_model_types.data_type_manager,
#         dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
#     )
#     namespace = {}
#     code = parser.parse()
#     exec(code, namespace)


#     className = schema.get("title", "Model")
#     return namespace[className]


def validate_artifact_data(
    schema: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    """
    Validate a dict representing a JSON Schema against a dict.
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Validation failed for data {data}.", add_serializable_data({"schema": schema}))
        raise e
    return data


class InvalidArtifactFieldError(Exception):
    pass


def validate_field_presence_in_schema(
    schema: dict[str, Any],
    field_name: str,
) -> None:
    """
    Validate the presence of a field in the schema.
    """
    if field_name not in schema.get("properties", {}):
        logger.warning(f"Field {field_name} not found in the schema.", add_serializable_data({"schema": schema}))
        raise InvalidArtifactFieldError(f"Field {field_name} not found in the schema.")


def validate_field_value(
    schema: dict[str, Any],
    field_name: str,
    field_value: Any,
) -> Any:
    """
    Validate a field value against a JSON schema.
    """
    # TODO: This may not handle optionals.
    schema = {**schema}
    if "required" in schema:
        del schema["required"]
    try:
        jsonschema.validate(instance={field_name: field_value}, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Validation failed for field {field_name} with value {field_value}.")
        raise e
    return field_value


def get_field_schema_string(
    artifact_schema: dict[str, Any],
    field_name: str,
) -> str:
    """
    Get the schema for a field in the artifact schema.
    """
    field_schema = {**artifact_schema["properties"][field_name]}
    if "description" in field_schema:
        del field_schema["description"]
    if "default" in field_schema:
        del field_schema["default"]
    if "title" in field_schema:
        del field_schema["title"]

    return json.dumps(field_schema)


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


def get_artifact_for_prompt(artifact: dict[str, Any] | None, failed_fields: list[str] = []) -> str:
    """
    Returns a formatted JSON-like representation of the current state of the
    artifact. Any fields that were failed are completely omitted.
    """
    if not artifact:
        return "{}"
    return json.dumps({k: v for k, v in artifact.items() if k not in failed_fields})
