# skill_library/types.py

from datetime import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol
from uuid import uuid4

from assistant_drive import Drive
from events import EventProtocol
from openai import AsyncAzureOpenAI, AsyncOpenAI
from semantic_workbench_api_model.workbench_model import ConversationMessageList

if TYPE_CHECKING:
    from .skill import Skill

Metadata = dict[str, Any]


class RunContext:
    """
    "Run context" is passed to parts of the system (skill routines and
    actions, and chat driver functions) that need to be able to run routines or
    actions, set assistant state, or emit messages from the assistant.
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
        self.metadata_log: list[tuple[str, Metadata]] = []

    def log(self, metadata: Metadata) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        self.metadata_log.append((ts, metadata))


class RunContextProvider(Protocol):
    """
    A provider of a run context must have this method. When called, it will
    return a run context. This is used by skill routines and actions to have
    access to all the things they need for running.
    """

    def create_run_context(self) -> RunContext: ...


AskUserFn = Callable[[str], Awaitable[str]]
ActionFn = Callable[[RunContext], Awaitable[Any]]
EmitFn = Callable[[EventProtocol], None]


class RunRoutineFn(Protocol):
    async def __call__(self, designation: str, *args: Any, **kwargs: Any) -> Any: ...


LanguageModel = AsyncOpenAI | AsyncAzureOpenAI
