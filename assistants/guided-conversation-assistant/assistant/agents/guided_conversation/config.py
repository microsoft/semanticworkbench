from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Type

from pydantic import BaseModel, Field, create_model
from semantic_workbench_assistant.config import UISchema

from .definition import GuidedConversationDefinition
from .definitions.patient_intake import patient_intake
from .definitions.poem_feedback import poem_feedback

if TYPE_CHECKING:
    pass


#
# region Helpers
#

# take a full json schema and return a pydantic model, including support for
# nested objects and typed arrays


def json_type_to_python_type(json_type: str) -> Type:
    # Mapping JSON types to Python types
    type_mapping = {"integer": int, "string": str, "number": float, "boolean": bool, "object": dict, "array": list}
    return type_mapping.get(json_type, Any)


def create_pydantic_model_from_json_schema(schema: Dict[str, Any], model_name="DynamicModel") -> Type[BaseModel]:
    # Nested function to parse properties from the schema
    def parse_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
        fields = {}
        for prop_name, prop_attrs in properties.items():
            prop_type = prop_attrs.get("type")
            description = prop_attrs.get("description", None)

            if prop_type == "object":
                nested_model = create_pydantic_model_from_json_schema(prop_attrs, model_name=prop_name.capitalize())
                fields[prop_name] = (nested_model, Field(..., description=description))
            elif prop_type == "array":
                items = prop_attrs.get("items", {})
                if items.get("type") == "object":
                    nested_model = create_pydantic_model_from_json_schema(items)
                    fields[prop_name] = (List[nested_model], Field(..., description=description))
                else:
                    nested_type = json_type_to_python_type(items.get("type"))
                    fields[prop_name] = (List[nested_type], Field(..., description=description))
            else:
                python_type = json_type_to_python_type(prop_type)
                fields[prop_name] = (python_type, Field(..., description=description))
        return fields

    properties = schema.get("properties", {})
    fields = parse_properties(properties)
    return create_model(model_name, **fields)


# endregion


#
# region Models
#


class GuidedConversationAgentConfigModel(BaseModel):
    definition: Annotated[
        GuidedConversationDefinition,
        Field(
            title="Definition",
            description="The definition of the guided conversation agent.",
        ),
        UISchema(
            schema={
                "ui:options": {
                    "configurations": {
                        "Poem Feedback": poem_feedback.model_dump(mode="json"),
                        "Patient Intake": patient_intake.model_dump(mode="json"),
                    },
                },
            },
        ),
    ] = poem_feedback


# endregion
