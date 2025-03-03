# skill_library/types.py

from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol
from uuid import uuid4

from assistant_drive import Drive
from events import EventProtocol
from openai import AsyncAzureOpenAI, AsyncOpenAI
from semantic_workbench_api_model.workbench_model import ConversationMessageList

from .usage import routines_usage as usage_routines_usage

if TYPE_CHECKING:
    from .skill import Skill

Metadata = dict[str, Any]


class RunContext:
    """
    Every skill routine is executed with a "Run context". This is how we give
    routines everything they need to interact one another and the "outside
    world".
    """

    def __init__(
        self,
        session_id: str,
        run_drive: Drive,
        conversation_history: Callable[[], Awaitable[ConversationMessageList]],
        skills: dict[str, "Skill"],
    ) -> None:
        # A session id is useful for maintaining consistent session state across all
        # consumers of this context. For example, a session id can be set in an
        # assistant and all functions called by that assistant can should receive
        # this same context object to know which session is being used.
        self.session_id: str = session_id or str(uuid4())

        # A "run" is a particular series of calls within a session. The initial call will
        # set the run id and all subsequent calls will use the same run id. This is useful
        # for logging, metrics, and debugging.
        self.run_id: str | None = str(uuid4())

        # The assistant drive is a drive object that can be used to read and
        # write files to a particular location. The assistant drive should be
        # used for assistant-specific data and not for general data storage.
        self.run_drive: Drive = run_drive

        # The conversation history function is a function that can be called to
        # get the conversation history for the current session. This is useful
        # for routines that need to know what has been said in the conversation
        # so far. Usage: `await run_context.conversation_history()`
        self.conversation_history = conversation_history

        self.skills = skills

        # This is a dictionary that can be used to store meta information about
        # the current run.
        self.metadata_log: list[Metadata] = []

    def log(self, message: str, metadata: Metadata) -> None:
        """
        Log a message with metadata. The metadata will be stored in the
        `metadata_log` list and can be inspected to see all the things that
        happened for a given run.
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if "log_message" not in metadata:
            metadata["log_message"] = message
        if "ts" not in metadata:
            metadata["ts"] = ts
        if "session_id" not in metadata:
            metadata["session_id"] = self.session_id
        if "run_id" not in metadata:
            metadata["run_id"] = self.run_id
        self.metadata_log.append(metadata)

    def flattened_metadata(self) -> dict[str, dict[str, Any]]:
        return {f"🕒{item['ts']} ➡️{item['log_message']}": item for item in self.metadata_log}

    def routine_usage(self) -> str:
        return usage_routines_usage(self.skills)


class RunContextProvider(Protocol):
    """
    A provider of a run context must have this method. When called, it will
    return a run context. This is used by skill routines to have access to all
    the things they need for running.
    """

    def create_run_context(self) -> RunContext: ...


AskUserFn = Callable[[str], Awaitable[str]]
ActionFn = Callable[[RunContext], Awaitable[Any]]
EmitFn = Callable[[EventProtocol], None]


class RunRoutineFn(Protocol):
    async def __call__(self, designation: str, *args: Any, **kwargs: Any) -> Any: ...


LanguageModel = AsyncOpenAI | AsyncAzureOpenAI
