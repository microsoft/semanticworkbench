import functools
import inspect
from typing import Callable

from .types import ActionFn, RunContextProvider


class ChatDriverFunctions:
    """
    Functions used for chat drivers (tool functions) can be created from skill
    actions functions by removing their run_context parameter and making the
    run_context available through a RunContextProvider. Additionally, we need to
    remove any default values for all parameters as OpenAI doesn't allow default
    parameters in their tool functions.

    Initialize this class with a run context provider and a list of action
    functions and it will generate wrapper methods for each action that can be
    used in a chat driver.

    This is helpful for maing chat driver setup in a skill simpler.
    """

    def __init__(self, actions: list[ActionFn], run_context_provider: RunContextProvider) -> None:
        self.actions = {action.__name__: action for action in actions}
        self.run_context_provider = run_context_provider
        self._generate_wrappers()

    def _generate_wrappers(self) -> None:
        """
        Dynamically create wrapper methods for all actions.
        """
        for name, action in self.actions.items():
            # Throw an error if the action does not have a run_context parameter.
            if "run_context" not in inspect.signature(action).parameters:
                raise ValueError(f"Invalid action function. '{name}' must have a 'run_context' parameter.")

            # Remove default values from the parameters
            original_signature = inspect.signature(action)
            parameters = [
                param.replace(default=inspect.Parameter.empty) for param in original_signature.parameters.values()
            ]
            parameters = [param for param in parameters if param.name != "run_context"]
            new_signature = original_signature.replace(parameters=parameters)

            def make_wrapper(action):
                @functools.wraps(action)
                def wrapper(*args, **kwargs):
                    run_context = self.run_context_provider.create_run_context()
                    return action(run_context, *args, **kwargs)

                # Update the wrapper function's signature to match the modified signature
                wrapper.__signature__ = new_signature  # type: ignore
                return wrapper

            # Set the wrapper as an attribute of the instance.
            setattr(self, name, make_wrapper(action))

    def all(self) -> list[Callable]:
        """
        Return a list of all dynamically created wrapper methods.
        """
        return [getattr(self, name) for name in self.actions.keys()]
