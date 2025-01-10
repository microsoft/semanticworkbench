from typing import Any

from liquid import Template

from ..utilities import find_template_vars, parse_command_string, parse_template
from .routine import Routine


def format_with_liquid(template: str, vars: dict[str, Any]) -> str:
    """
    Format a string with the given variables using the Liquid template engine.
    """
    if not vars:
        return template
    liquid_template = Template(template)
    return liquid_template.render(**vars)


class ActionListRoutine(Routine):
    def __init__(
        self,
        name: str,
        skill_name: str,
        description: str,
        routine: str,
    ) -> None:
        super().__init__(
            name=name,
            skill_name=skill_name,
            description=description,
        )
        self.routine = routine

    def template_vars(self) -> list[str]:
        return find_template_vars(self.routine)

    def validate(self, vars: dict[str, Any]):
        """
        Validate the routine. In the case of an Action routine this means that:
        - Each line should have an output variable name defined (the string
        before the first colon). - For each line:
            - Any template variables should have already been defined in either
              vars, or in previous lines.
            - The remaining line (after the colon), with replacements, should be
              parseable as a command.
        """
        # First, clean out any template variables that have been set.
        parsed_routine = parse_template(self.routine, vars)

        # Gather up defined output variables as we go.
        output_variables = {}

        for line in parsed_routine.split("\n"):
            # Skip empty lines.
            line = line.strip()
            if not line:
                continue

            # Check the line format (output_variable: command).
            if ":" not in line:
                raise ValueError(f"Invalid line in routine: {line}")
            output_variable_name, command = line.split(":", 1)
            output_variable_name = output_variable_name.strip()
            command = command.strip()
            if not command:
                raise ValueError(f"Empty command in routine: {line}")

            # Check that no undefined variables are used.
            if not all(variable in output_variables for variable in find_template_vars(command)):
                raise ValueError(f"Unbound template variable in routine: {line}")

            # Check that the command string is valid.
            try:
                command = parse_template(command, dict(output_variables))
                parse_command_string(command)
            except ValueError as e:
                raise ValueError(f"Unparsable command in routine. {e} {command}")

            # Add this line's output variable for checking next line.
            output_variables[output_variable_name] = None

    def __str__(self) -> str:
        template_vars = find_template_vars(self.routine)
        return f"{self.fullname}(vars: {template_vars}): {self.description}"
