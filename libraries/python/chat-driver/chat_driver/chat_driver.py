from dataclasses import dataclass, field
from typing import Any, Callable, Union

from context import Context, ContextProtocol
from events import BaseEvent, ErrorEvent, MessageEvent
from function_registry.function_registry import FunctionRegistry
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.completion_create_params import ResponseFormat
from openai_client.completion import TEXT_RESPONSE_FORMAT, completion_message_string
from openai_client.errors import CompletionError
from openai_client.messages import MessageFormatter, format_message
from openai_client.tools import complete_with_tool_calls, function_registry_to_tools, tool_choice
from pydantic import BaseModel

from .local_message_history_provider import (
    LocalMessageHistoryProvider,
    LocalMessageHistoryProviderConfig,
)
from .message_history_provider import MessageHistoryProviderProtocol


@dataclass
class ChatDriverConfig:
    openai_client: AsyncOpenAI
    model: str
    instructions: str | list[str] = "You are a helpful assistant."
    instruction_formatter: MessageFormatter | None = None
    context: ContextProtocol | None = None
    message_provider: MessageHistoryProviderProtocol | None = None
    commands: list[Callable] = field(default_factory=list)
    functions: list[Callable] = field(default_factory=list)


class ChatDriver:
    """
    A ChatDriver is a class that manages a conversation with a user. It provides
    methods to add messages to the conversation, and to generate responses to
    user messages. The ChatDriver uses the OpenAI API to generate responses, and
    can call functions registered with the ChatDriver to generate parts of the
    response. The ChatDriver also provides a way to register commands that can
    be called by the user to execute functions directly.

    Instructions are messages that are sent to the OpenAI model before any other
    messages. These instructions are used to guide the model in generating a
    response. The ChatDriver allows you to set instructions that can be
    formatted with variables.

    If you want to just generate responses using the OpenAI API, you should use
    the client directly (but we do have some helpers in the openai_helpers
    module) to make this simpler.
    """

    def __init__(self, config: ChatDriverConfig) -> None:
        # A context object holds information about the current session, such as
        # the session ID, the user ID, and the conversation ID. It also provides
        # a method to emit events. If you do not supply one, one will be created
        # for you with a random session ID.
        self.context: ContextProtocol = config.context or Context()

        # Set up a default message provider. This provider stores messages in a
        # local file. You can replace this with your own message provider that
        # implements the MessageHistoryProviderProtocol.
        self.message_provider: MessageHistoryProviderProtocol = config.message_provider or LocalMessageHistoryProvider(
            LocalMessageHistoryProviderConfig(context=self.context)
        )

        self.instructions: list[str] = (
            config.instructions if isinstance(config.instructions, list) else [config.instructions]
        )
        self.instruction_formatter = config.instruction_formatter or format_message

        # Now set up the OpenAI client and model.
        self.client = config.openai_client
        self.model = config.model

        # Functions that you register with the chat driver will be available to
        # for GPT to call while generating a response. If the model generates a
        # call to a function, the function will be executed, the result passed
        # back to the model, and the model will continue generating the
        # response.
        self.function_registry = FunctionRegistry(self.context, config.functions)
        self.functions = self.function_registry.functions

        # Commands are functions that can be called by the user by typing a
        # command in the chat. When a command is received, the chat driver will
        # execute the corresponding function and return the result to the user
        # directly.
        self.command_registry = FunctionRegistry(self.context, config.commands)
        self.commands = self.command_registry.functions

    def _formatted_instructions(self, vars: dict[str, Any] | None) -> list[ChatCompletionSystemMessageParam]:
        return ChatDriver.format_instructions(self.instructions, vars, self.instruction_formatter)

    async def add_message(self, message: ChatCompletionMessageParam) -> None:
        await self.message_provider.append(message)

    # Commands are available to be run by the user message.
    def register_command(self, function: Callable) -> None:
        self.command_registry.register_function(function)

    def register_commands(self, functions: list[Callable]) -> None:
        self.command_registry.register_functions(functions)

    # Functions are available to be called by the model during response
    # generation.
    def register_function(self, function: Callable) -> None:
        self.function_registry.register_function(function)

    def register_functions(self, functions: list[Callable]) -> None:
        self.function_registry.register_functions(functions)

    # Sometimes we want to register a function to be used by both the user and
    # the model.
    def register_function_and_command(self, function: Callable) -> None:
        self.register_command(function)
        self.register_function(function)

    def register_functions_and_commands(self, functions: list[Callable]) -> None:
        self.register_commands(functions)
        self.register_functions(functions)

    def get_functions(self) -> list[Callable]:
        return [function.fn for function in self.function_registry.get_functions()]

    def get_commands(self) -> list[Callable]:
        commands = [function.fn for function in self.command_registry.get_functions()]
        return commands

    async def respond(
        self,
        message: str | None = None,
        response_format: Union[ResponseFormat, type[BaseModel]] = TEXT_RESPONSE_FORMAT,
        function_choice: list[str] | None = None,
        instruction_parameters: dict[str, Any] | None = None,
    ) -> BaseEvent:
        """
        Respond to a user message.

        If the user message is a command, the command will be executed and the
        result returned.

        All generated messages are added to the chat driver's message history.

        Otherwise, the message will be passed to the chat completion API and the
        response returned in the specified request_format.

        The API response might be a request to call functions registered with
        the chat driver. If so, we execute the functions and give the results
        back to the model for the final response generation.
        """

        # If the message contains a command, execute it.
        if message and message.startswith("/"):
            command_string = message[1:]
            try:
                results = await self.command_registry.execute_function_string_with_string_response(command_string)
                return MessageEvent(message=results)
            except Exception as e:
                return ErrorEvent(message=f"Error! {e}", metadata={"error": str(e)})

        # If not a command, add the message to the history.
        if message is not None:
            user_message: ChatCompletionUserMessageParam = {
                "role": "user",
                "content": message,
            }
            await self.add_message(user_message)

        # Generate a response.
        metadata = {}

        completion_args = {
            "model": self.model,
            "messages": [*self._formatted_instructions(instruction_parameters), *(await self.message_provider.get())],
            "tools": function_registry_to_tools(self.function_registry),
            "tool_choice": tool_choice(function_choice),
            "response_format": response_format,
        }
        try:
            completion, new_messages = await complete_with_tool_calls(
                self.client,
                self.function_registry,
                completion_args,
                metadata=metadata,
            )
        except CompletionError as e:
            return ErrorEvent(message=f"Error: {e.message}", metadata=metadata)

        # Add the new messages to the history.
        for new_message in new_messages:
            await self.add_message(new_message)

        # Return the response.

        return MessageEvent(
            message=completion_message_string(completion) or None,
            metadata=metadata,
        )

    @staticmethod
    def format_instructions(
        instructions: list[str],
        vars: dict[str, Any] | None = None,
        formatter: MessageFormatter | None = None,
    ) -> list[ChatCompletionSystemMessageParam]:
        """
        Chat Driver instructions are system messages given to the OpenAI model
        before any other messages. These instructions are used to guide the model in
        generating a response. We oftentimes need inject variables into the
        instructions, so we provide a formatter function to format the instructions
        with the variables. This method returns a list of system messages formatted
        with the variables.
        """
        formatter = formatter or format_message
        instruction_messages: list[ChatCompletionSystemMessageParam] = []
        for instruction in instructions:
            if vars:
                formatted_instruction = formatter(instruction, vars)
            else:
                formatted_instruction = instruction
            instruction_messages.append({"role": "system", "content": formatted_instruction})
        return instruction_messages
