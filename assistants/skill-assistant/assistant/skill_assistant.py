# Copyright (c) Microsoft. All rights reserved.

# An assistant for exploring use of the skills library, using the AssistantApp from
# the semantic-workbench-assistant package.

# The code in this module demonstrates the minimal code required to create a chat assistant
# using the AssistantApp class from the semantic-workbench-assistant package and leveraging
# the skills library to create a skill-based assistant.

import asyncio
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable

import openai_client
from assistant_drive import Drive, DriveConfig
from content_safety.evaluators import CombinedContentSafetyEvaluator
from openai_client.chat_driver import ChatDriver, ChatDriverConfig
from openai_client.tools import ToolFunctions
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import (
    AssistantApp,
    BaseModelAssistantConfig,
    ContentSafety,
    ContentSafetyEvaluator,
    ConversationContext,
)
from skill_library import Engine
from skill_library.skills.common import CommonSkill, CommonSkillConfig
from skill_library.skills.eval import EvalSkill, EvalSkillConfig
from skill_library.skills.fabric import FabricSkill, FabricSkillConfig
from skill_library.skills.meta import MetaSkill, MetaSkillConfig
from skill_library.skills.posix import PosixSkill, PosixSkillConfig
from skill_library.skills.research import ResearchSkill, ResearchSkillConfig

from assistant.skill_event_mapper import SkillEventMapper
from assistant.workbench_helpers import WorkbenchMessageProvider

from .config import AssistantConfigModel
from .logging import extra_data, logger
from .skill_engine_registry import SkillEngineRegistry

logger.info("Starting skill assistant service.")

# The service id to be registered in the workbench to identify the assistant.
service_id = "skill-assistant.made-exploration"

# The name of the assistant service, as it will appear in the workbench UI.
service_name = "Skill Assistant"

# A description of the assistant service, as it will appear in the workbench UI.
service_description = "A skills-based assistant using the Semantic Workbench Assistant SDK."

# Create the configuration provider, using the extended configuration model.
assistant_config = BaseModelAssistantConfig(AssistantConfigModel)


# Create the content safety interceptor.
async def content_evaluator_factory(conversation_context: ConversationContext) -> ContentSafetyEvaluator:
    config = await assistant_config.get(conversation_context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)


content_safety = ContentSafety(content_evaluator_factory)


# create the AssistantApp instance
assistant_service = AssistantApp(
    assistant_service_id=service_id,
    assistant_service_name=service_name,
    assistant_service_description=service_description,
    config_provider=assistant_config.provider,
    content_interceptor=content_safety,
)

#
# create the FastAPI app instance
#
app = assistant_service.fastapi_app()


# This engine registry is used to manage the skill engines for this service and
# to register their event subscribers so we can map events to the workbench.
#
# NOTE: Currently, the skill library doesn't have the notion of "conversations"
# so we map a skill library engine to a particular conversation in the
# workbench. This means if you have a different conversation with the same
# "skill assistant" it will appear as a different engine in the skill assistant
# library. We can improve this in the future by adding a conversation ID to the
# skill library and mapping it to a conversation in the workbench.
engine_registry = SkillEngineRegistry()


# Handle the event triggered when the assistant is added to a conversation.
@assistant_service.events.conversation.on_created
async def on_conversation_created(conversation_context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    """

    # Send a welcome message to the conversation.
    config = await assistant_config.get(conversation_context.assistant)
    welcome_message = config.welcome_message
    await conversation_context.send_messages(
        NewConversationMessage(
            content=welcome_message,
            message_type=MessageType.chat,
            metadata={"generated_content": False},
        )
    )


@assistant_service.events.conversation.message.command.on_created
async def on_command_message_created(
    conversation_context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """
    Handle the event triggered when a new command message is created in the
    conversation. Commands in the skill assistant currently are oriented around
    running skills manually. We will update this in the future to add a few more
    commands that we'll register to the chat driver so we can call them
    conversationally.
    """

    config = await assistant_config.get(conversation_context.assistant)
    engine = await get_or_register_skill_engine(conversation_context, config)
    functions = ChatFunctions(engine)

    command_string = event.data["message"]["content"]

    match command_string:
        case "/help":
            help_msg = dedent("""
            ```markdown
            - __/help__: Display this help message.
            - __/list_routines__: List all routines.
            - __/run__("&lt;name&gt;", ...args): Run a routine.
            - __/reset__: Reset the assistant.
            ```
            """).strip()
            await conversation_context.send_messages(
                NewConversationMessage(
                    content=str(help_msg),
                    message_type=MessageType.notice,
                ),
            )
        case _:
            """
            For every other command we receive, we're going to try to map it to
            one of the registered ChatFunctions below and execute the command.
            """
            try:
                function_string, args, kwargs = ToolFunctions.parse_fn_string(command_string)
                if not function_string:
                    await conversation_context.send_messages(
                        NewConversationMessage(
                            content="Invalid command.",
                            message_type=MessageType.notice,
                        ),
                    )
                    return
            except ValueError as e:
                await conversation_context.send_messages(
                    NewConversationMessage(
                        content=f"Invalid command. {e}",
                        message_type=MessageType.notice,
                        metadata={},
                    ),
                )
                return

            # Run the function.
            result = await getattr(functions, function_string)(*args, **kwargs)

            if result:
                await conversation_context.send_messages(
                    NewConversationMessage(
                        content=str(result),
                        message_type=MessageType.note,
                    ),
                )


@assistant_service.events.conversation.message.chat.on_created
async def on_message_created(
    conversation_context: ConversationContext, event: ConversationEvent, message: ConversationMessage
) -> None:
    """Handle new chat messages"""
    logger.debug("Message received", extra_data({"content": message.content}))

    config = await assistant_config.get(conversation_context.assistant)
    engine = await get_or_register_skill_engine(conversation_context, config)

    # Check if routine is running.
    if engine.is_routine_running():
        try:
            logger.debug("Resuming routine with message", extra_data({"message": message.content}))
            resume_task = asyncio.create_task(engine.resume_routine(message.content))
            resume_task.add_done_callback(
                lambda t: logger.debug("Routine resumed", extra_data({"success": not t.exception()}))
            )
        except Exception as e:
            logger.error(f"Failed to resume routine: {e}")
        finally:
            return

    # Use a chat driver to respond.
    async with conversation_context.set_status("thinking..."):
        chat_driver_config = ChatDriverConfig(
            openai_client=openai_client.create_client(config.service_config),
            model=config.chat_driver_config.openai_model,
            instructions=config.chat_driver_config.instructions,
            message_provider=WorkbenchMessageProvider(conversation_context.id, conversation_context),
            functions=ChatFunctions(engine).list_functions(),
        )
        chat_driver = ChatDriver(chat_driver_config)
        chat_functions = ChatFunctions(engine)
        chat_driver_config.functions = [chat_functions.list_routines]

        metadata: dict[str, Any] = {"debug": {"content_safety": event.data.get(content_safety.metadata_key, {})}}
        await chat_driver.respond(message.content, metadata=metadata or {})


async def get_or_register_skill_engine(
    conversation_context: ConversationContext, config: AssistantConfigModel
) -> Engine:
    """
    Get or register a skill engine for the conversation. This is used to manage
    the skill engines for this service and to register their event subscribers
    so we can map events to the workbench.
    """

    # Get an engine from the registry.
    engine_id = conversation_context.id
    engine = engine_registry.get_engine(engine_id)

    # Register an assistant if it's not there.
    if not engine:
        assistant_drive_root = Path(".data") / engine_id / "assistant"
        assistant_metadata_drive_root = Path(".data") / engine_id / ".assistant"
        assistant_drive = Drive(DriveConfig(root=assistant_drive_root))
        language_model = openai_client.create_client(config.service_config)
        message_provider = WorkbenchMessageProvider(engine_id, conversation_context)

        # Create the engine and register it. This is where we configure which
        # skills the engine can use and their configuration.
        engine = Engine(
            engine_id=conversation_context.id,
            message_history_provider=message_provider.get_history,
            drive_root=assistant_drive_root,
            metadata_drive_root=assistant_metadata_drive_root,
            skills=[
                (
                    MetaSkill,
                    MetaSkillConfig(name="meta", language_model=language_model, drive=assistant_drive.subdrive("meta")),
                ),
                (
                    CommonSkill,
                    CommonSkillConfig(
                        name="common",
                        language_model=language_model,
                        drive=assistant_drive.subdrive("common"),
                    ),
                ),
                (
                    EvalSkill,
                    EvalSkillConfig(
                        name="eval",
                        language_model=language_model,
                        drive=assistant_drive.subdrive("eval"),
                    ),
                ),
                (
                    PosixSkill,
                    PosixSkillConfig(
                        name="posix",
                        sandbox_dir=Path(".data") / conversation_context.id,
                        mount_dir="/mnt/data",
                    ),
                ),
                (
                    ResearchSkill,
                    ResearchSkillConfig(
                        name="research",
                        language_model=language_model,
                        drive=assistant_drive.subdrive("research"),
                    ),
                ),
                (
                    FabricSkill,
                    FabricSkillConfig(
                        name="fabric",
                        language_model=language_model,
                        drive=assistant_drive.subdrive("fabric"),
                    ),
                ),
            ],
        )

        await engine_registry.register_engine(engine, SkillEventMapper(conversation_context))

    return engine


class ChatFunctions:
    """
    These are functions that can be run from the chat.
    """

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    async def reset(self) -> str:
        """Resets the skill engine run state. Useful for troubleshooting."""
        await self.engine.clear(include_drives=False)
        return "Assistant stack cleared."

    async def list_routines(self) -> str:
        """Lists all the routines available in the assistant."""

        routines = self.engine.routines_usage()
        if not routines:
            return "No routines available."

        return "```markdown\n" + routines + "\n```"

    async def run(self, designation: str, *args, **kwargs) -> str:
        try:
            task = asyncio.create_task(self.engine.run_routine(designation, *args, **kwargs))
            task.add_done_callback(self._handle_routine_completion)
        except Exception as e:
            logger.error(f"Failed to start routine {designation}: {e}")
            return f"Failed to start routine: {designation}"

        return ""

    def _handle_routine_completion(self, task: asyncio.Task) -> None:
        try:
            result = task.result()
            logger.debug(f"Routine completed with result: {result}")
        except Exception as e:
            logger.error(f"Routine failed with error: {e}")

    def list_functions(self) -> list[Callable]:
        return [
            self.list_routines,
        ]
