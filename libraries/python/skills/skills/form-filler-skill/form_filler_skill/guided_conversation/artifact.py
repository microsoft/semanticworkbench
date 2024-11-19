# Copyright (c) Microsoft. All rights reserved.


import json
import logging
from typing import Any, Literal, TypeVar, Union, get_args, get_origin, get_type_hints

from pydantic import BaseModel, create_model

from form_filler_skill.guided_conversation.chat_drivers.unneeded.base_model_llm import BaseModelLLM

from .message import ConversationMessageType, Message

logger = logging.getLogger(__name__)


class Artifact:
    """The Artifact plugin takes in a Pydantic base model, and robustly handles updating the fields of the model
    A typical use case is as a form an agent must complete throughout a conversation.
    Another use case is as a working memory for the agent.

    The primary interface is update_artifact, which takes in the field_name to update and its new value.
    Additionally, the chat_history is passed in to help the agent make informed decisions in case an error occurs.

    The Artifact also exposes several functions to access internal state:
    get_artifact_for_prompt, get_schema_for_prompt, and get_failed_fields.
    """

    def __init__(
        self,
        input_artifact: BaseModel,
        max_artifact_field_retries: int = 2,
    ) -> None:
        """
        Initialize the Artifact plugin with the given Pydantic base model.

        Args:
            input_artifact (BaseModel): The Pydantic base model to use as the artifact
            max_artifact_field_retries (int): The maximum number of times to retry updating a field in the artifact
        """

        self.max_artifact_field_retries = max_artifact_field_retries

        self.original_schema = input_artifact.model_json_schema()

        # Create a new artifact model based on the one provided by the user with
        # "Unanswered" set for all fields.
        modified_classes = self._modify_classes(input_artifact)
        self.artifact = self._modify_base_artifact(input_artifact, modified_classes)()

        # failed_artifact_fields maps a field name to a list of the history of
        # the failed attempts to update it.
        # dict: key = field, value = list of tuple[attempt, error message]
        self.failed_artifact_fields: dict[str, list[tuple[str, str]]] = {}

    def get_artifact_for_prompt(self) -> str:
        """
        Returns a formatted JSON-like representation of the current state of the
        fields artifact. Any fields that were failed are completely omitted.
        """
        failed_fields = self.get_failed_fields()
        return json.dumps({k: v for k, v in self.artifact.model_dump().items() if k not in failed_fields})

    def get_schema_for_prompt(self, filter_one_field: str | None = None) -> str:
        """Gets a clean version of the original artifact schema, optimized for use in an LLM prompt.

        Args:
            filter_one_field (str | None): If this is provided, only the schema for this one field will be returned.

        Returns:
            str: The cleaned schema
        """

        def _clean_properties(schema: dict, failed_fields: list[str]) -> str:
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
            if not self._is_valid_field(filter_one_field):
                logger.error(f'Field "{filter_one_field}" is not a valid field in the artifact.')
                raise ValueError(f'Field "{filter_one_field}" is not a valid field in the artifact.')
            filtered_schema = {"properties": {filter_one_field: self.original_schema["properties"][filter_one_field]}}
            filtered_schema.update((k, v) for k, v in self.original_schema.items() if k != "properties")
            schema = filtered_schema
        else:
            schema = self.original_schema

        failed_fields = self.get_failed_fields()
        properties = _clean_properties(schema, failed_fields)
        if not properties:
            logger.error("No properties found in the schema.")
            raise ValueError("No properties found in the schema.")

        types_schema = schema.get("$defs", {})
        custom_types = []
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

    def get_failed_fields(self) -> list[str]:
        """Get a list of fields that have failed all attempts to update.

        Returns:
            list[str]: A list of field names that have failed all attempts to update.
        """
        fields = []
        for field, attempts in self.failed_artifact_fields.items():
            if len(attempts) >= self.max_artifact_field_retries:
                fields.append(field)
        return fields

    T = TypeVar("T")

    def _get_type_if_subtype(self, target_type: type[T], base_type: type[Any]) -> type[T] | None:
        """
        Recursively checks the target_type to see if it is a subclass of
        base_type or a generic including base_type.

        Args:
            target_type: The type to check.
            base_type: The type to check against.

        Returns:
            The class type if target_type is base_type, a subclass of base_type,
            or a generic including base_type; otherwise, None.
        """
        origin = get_origin(target_type)
        if origin is None:
            if issubclass(target_type, base_type):
                return target_type
        else:
            # Recursively check if any of the arguments are the target type.
            for arg in get_args(target_type):
                result = self._get_type_if_subtype(arg, base_type)
                if result is not None:
                    return result
        return None

    def _modify_classes(self, artifact_class: BaseModel) -> dict[str, type[BaseModelLLM]]:
        """Find all classes used as type hints in the artifact, and modify them to set 'Unanswered' as a default and valid value for all fields."""
        modified_classes = {}
        # Find any instances of BaseModel in the artifact class in the first "level" of type hints
        for field_name, field_type in get_type_hints(artifact_class).items():
            is_base_model = self._get_type_if_subtype(field_type, BaseModel)
            if is_base_model is not None:
                modified_classes[field_name] = self._modify_base_artifact(is_base_model)

        return modified_classes

    def _replace_type_annotations(
        self, field_annotation: type[Any] | None, modified_classes: dict[str, type[BaseModelLLM]]
    ) -> type:
        """
        Recursively replace type annotations with modified classes where
        applicable.
        """
        # Get the origin of the field annotation, which is the base type for
        # generic types (e.g., List[str] -> list, Dict[str, int] -> dict)
        origin = get_origin(field_annotation)

        # Get the type arguments of the generic type (e.g., List[str] -> str,
        # Dict[str, int] -> str, int)
        args = get_args(field_annotation)

        if origin is None:
            # The type is not generic; check if it's a subclass that needs to be replaced
            if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModelLLM):
                return modified_classes.get(field_annotation.__name__, field_annotation)
            return field_annotation if field_annotation is not None else object
        else:
            # The type is generic; recursively replace the type annotations of the arguments
            new_args = tuple(self._replace_type_annotations(arg, modified_classes) for arg in args)
            return origin[new_args]

    def _modify_base_artifact(
        self,
        artifact_model: BaseModel,
        modified_classes: dict[str, type[BaseModelLLM]] | None = None,
    ) -> type[BaseModelLLM]:
        """
        Create a new artifact model with 'Unanswered' as a default and valid
        value for all fields.
        """
        field_definitions = {}
        for name, field_info in artifact_model.model_fields.items():
            # Replace original classes with modified version.
            if modified_classes is not None:
                field_info.annotation = self._replace_type_annotations(field_info.annotation, modified_classes)

            # This makes it possible to always set a field to "Unanswered".
            annotation = Union[field_info.annotation, Literal["Unanswered"]]

            # This sets the default value to "Unanswered".
            default = "Unanswered"

            # This adds "Unanswered" as a possible value to any regex patterns.
            metadata = field_info.metadata
            for m in metadata:
                if hasattr(m, "pattern"):
                    m.pattern += "|Unanswered"

            field_definitions[name] = (annotation, default, *metadata)

        return create_model("Artifact", __base__=BaseModelLLM, **field_definitions)

    def _is_valid_field(self, field_name: str) -> tuple[bool, Message | None]:
        """
        Check if the field_name is a valid field in the artifact. Returns True
        if it is, False and an error message otherwise.
        """
        if field_name not in self.artifact.model_fields:
            error_message = f'Field "{field_name}" is not a valid field in the artifact.'
            msg = Message(
                {"role": "assistant", "content": error_message},
                type=ConversationMessageType.ARTIFACT_UPDATE,
                turn=None,
            )
            return False, msg
        return True, None

    def to_json(self) -> dict:
        artifact_fields = self.artifact.model_dump()
        return {
            "artifact": artifact_fields,
            "failed_fields": self.failed_artifact_fields,
        }

    @classmethod
    def from_json(
        cls,
        json_data: dict,
        input_artifact: BaseModel,
        max_artifact_field_retries: int = 2,
    ) -> "Artifact":
        artifact = cls(input_artifact, max_artifact_field_retries)

        artifact.failed_artifact_fields = json_data["failed_fields"]

        # Iterate over artifact fields and set them to the values in the json data
        # Skip any fields that are set as "Unanswered"
        for field_name, field_value in json_data["artifact"].items():
            if field_value != "Unanswered":
                setattr(artifact.artifact, field_name, field_value)
        return artifact
