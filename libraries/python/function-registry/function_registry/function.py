import inspect
from dataclasses import dataclass
from typing import Any, Callable

from context.context import ContextProtocol
from pydantic import create_model
from pydantic.fields import FieldInfo


@dataclass
class Parameter:
    name: str
    type: Any
    description: str | None
    default_value: Any | None = None


class Function:
    def __init__(
        self, name: str, description: str | None, parameters: list[Parameter], fn: Callable, strict_schema: bool = False
    ) -> None:
        self.name = name
        self.description = description or name.replace("_", " ").title()
        self.parameters = parameters
        self.fn = fn
        self.schema: dict[str, Any] = self._generate_schema(strict=strict_schema)
        self.usage: str = self._generate_usage()

    async def execute(self, context: ContextProtocol, *args, **kwargs) -> Any:
        result = self.fn(context, *args, **kwargs)
        if inspect.iscoroutine(result):
            return await result
        return result

    def _generate_usage(self) -> str:
        """A usage string for this function."""
        name = self.name
        param_usages = []
        for param in self.parameters:
            param_type = param.type
            try:
                param_type = param.type.__name__
            except AttributeError:
                param_type = param.type
            usage = f"{param.name}: {param_type}"
            if param.default_value is not inspect.Parameter.empty:
                if isinstance(param.default_value, str):
                    usage += f' = "{param.default_value}"'
                else:
                    usage += f" = {param.default_value}"
            param_usages.append(usage)

        description = self.description
        return f"{name}({', '.join(param_usages)}): {description}"

    def _generate_schema(self, strict: bool = True) -> dict[str, Any]:
        """
        Generate a JSON schema for a function based on its signature.
        """

        # Create the Pydantic model using create_model.

        model_name = self.fn.__name__.title().replace("_", "")
        fields = {}
        for parameter in self.parameters:
            field_info = FieldInfo(description=parameter.description)
            if parameter.default_value is not inspect.Parameter.empty:
                field_info.default = parameter.default_value
            fields[parameter.name] = (
                parameter.type,
                field_info,
            )
        pydantic_model = create_model(model_name, **fields)
        # pydantic_model.model_config = {"field_title_generator": lambda _, _: None}

        # Generate the JSON schema from the Pydantic model.
        parameters_schema = pydantic_model.model_json_schema(mode="serialization")

        # Remove title attribute from all properties.
        properties = parameters_schema["properties"]
        for property_key in properties.keys():
            if "title" in properties[property_key]:
                del properties[property_key]["title"]

        # And from the top-level object.
        if "title" in parameters_schema:
            del parameters_schema["title"]

        name = self.fn.__name__
        description = inspect.getdoc(self.fn) or name.replace("_", " ").title()

        # Output a schema that matches OpenAI's "tool" format.
        # e.g., https://platform.openai.com/docs/guides/function-calling
        # We use this because they trained GPT on it.
        schema = {
            # "$schema": "http://json-schema.org/draft-07/schema#",
            # "$id": f"urn:jsonschema:{name}",
            "name": name,
            "description": description,
            "strict": strict,
            "parameters": {
                "type": "object",
                "properties": parameters_schema["properties"],
            },
        }

        # If this is a strict schema requirement, OpenAI requires
        # additionalProperties to be False.
        # if strict:
        schema["parameters"]["additionalProperties"] = False

        # Add required fields.
        if "required" in parameters_schema:
            schema["parameters"]["required"] = parameters_schema["required"]

        # Add definitions.
        if "$defs" in parameters_schema:
            schema["parameters"]["$defs"] = parameters_schema["$defs"]
            for key in schema["parameters"]["$defs"]:
                schema["parameters"]["$defs"][key]["additionalProperties"] = False

        return schema
