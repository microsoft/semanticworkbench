import asyncio
from os import PathLike
from pathlib import Path
from typing import Awaitable, Callable

from assistant_drive import Drive, DriveConfig
from events import events as skill_events
from semantic_workbench_api_model.workbench_model import ConversationMessageList
from skill_library import Engine
from skill_library.skills.common import CommonSkill, CommonSkillConfig
from skill_library.skills.posix import PosixSkill, PosixSkillConfig
from skill_library.skills.research import ResearchSkill, ResearchSkillConfig
from skill_library.skills.web_research import WebResearchSkill, WebResearchSkillConfig

from .azure_openai import create_azure_openai_client
from .config import settings


# This is a coupling we probably don't want in the skill library. For this web
# research MCP, though, none of these routines use the message history, so just
# give it this stub.
async def message_history_provider() -> ConversationMessageList:
    return ConversationMessageList(messages=[])


def get_engine(engine_id: str, drive_root: PathLike, metadata_drive_root: PathLike) -> Engine:
    drive = Drive(DriveConfig(root=settings.data_folder))

    language_model = create_azure_openai_client(settings.azure_openai_endpoint, settings.azure_openai_deployment)
    reasoning_language_model = create_azure_openai_client(
        settings.azure_openai_endpoint, settings.azure_openai_reasoning_deployment
    )

    engine = Engine(
        engine_id=engine_id,
        message_history_provider=message_history_provider,
        drive_root=drive_root,
        metadata_drive_root=metadata_drive_root,
        skills=[
            (
                CommonSkill,
                CommonSkillConfig(
                    name="common",
                    language_model=language_model,
                    bing_subscription_key=settings.bing_subscription_key,
                    bing_search_url=settings.bing_search_url,
                    drive=drive.subdrive("common"),
                ),
            ),
            (
                PosixSkill,
                PosixSkillConfig(
                    name="posix",
                    sandbox_dir=Path(settings.data_folder) / engine_id,
                    mount_dir="/mnt/data",
                ),
            ),
            (
                ResearchSkill,
                ResearchSkillConfig(
                    name="research",
                    language_model=language_model,
                    drive=drive.subdrive("research"),
                ),
            ),
            (
                WebResearchSkill,
                WebResearchSkillConfig(
                    name="web_research",
                    language_model=language_model,
                    reasoning_language_model=reasoning_language_model,
                    drive=drive.subdrive("web_research"),
                ),
            ),
        ],
    )
    return engine


def event_string(event: skill_events.EventProtocol) -> str:
    metadata = {"debug": event.metadata} if event.metadata else None
    event_type = type(event).__name__.replace("Event", "")
    event_string = f"{event_type}: {event.message}"
    if event.metadata:
        event_string += f" (metadata: {metadata})"
    return event_string


async def perform_web_research(question: str, on_status_update: Callable[[str], Awaitable[None]]) -> str:
    """
    Perform deep research on a question.

    Args:
        model_id: The ID of the model to use.
        question: The research question.
        on_status_update: A callback function for status updates.

    Returns:
        The research results.
    """
    await on_status_update("Starting research...")

    engine = get_engine(
        engine_id="web_research",
        drive_root=Path(settings.data_folder) / "research",
        metadata_drive_root=Path(settings.data_folder) / "metadata",
    )

    async def monitor_events():
        try:
            async for event in engine.events:
                if event.message:
                    await on_status_update(event_string(event))
        except Exception as e:
            print(f"Error monitoring events: {e}")

    monitor_task = asyncio.create_task(monitor_events())

    try:
        designation = "web_research.research"
        args = []
        kwargs = {
            "plan_name": "temp",
            "topic": question,
        }

        result = await engine.run_routine(designation, *args, **kwargs)

        await on_status_update("Research complete.")
        return result
    except Exception as e:
        error_msg = f"Failed to run routine: {str(e)}"
        await on_status_update(error_msg)
        return error_msg
    finally:
        if not monitor_task.done():
            monitor_task.cancel()
            try:
                await asyncio.wait_for(monitor_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
