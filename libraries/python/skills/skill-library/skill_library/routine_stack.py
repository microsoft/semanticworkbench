# skill_library/routine_stack.py

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, List
from uuid import uuid4

from assistant_drive import Drive, IfDriveFileExistsBehavior
from pydantic import BaseModel, Field


class RoutineFrame(BaseModel):
    name: str
    id: str = Field(default_factory=lambda: str(uuid4()))
    state: dict[str, Any] = Field(default_factory=dict)


class RoutineStackData(BaseModel):
    frames: List[RoutineFrame]
    model_config = {
        "arbitrary_types_allowed": True,
    }


STACK_FILENAME = "routine_stack.json"


class RoutineStack:
    """
    Manages state for nested routines.

    The RoutineStack provides routines with isolated state storage as they run,
    allowing nested routines to maintain their own state without interfering
    with each other. Each routine execution gets a frame on the stack that
    contains:

    - The routine's name for tracking
    - A state dictionary that the routine can use to store data between steps

    The stack behaves like a traditional call stack:

    - push() creates a new frame when a routine starts
    - pop() removes the frame when the routine completes
    - peek() allows checking the current frame
    - get/set_current_state provide access to the current routine's state

    State is persisted between messages/steps in the conversation, allowing
    routines to maintain context even when paused waiting for user input. When
    routines call other routines, each gets its own isolated state frame.
    """

    def __init__(self, drive: Drive):
        self.drive = drive

    async def get(self) -> List[RoutineFrame]:
        try:
            stack = self.drive.read_model(RoutineStackData, STACK_FILENAME)
        except FileNotFoundError:
            stack = RoutineStackData(frames=[])
            await self.set(stack.frames)
        return stack.frames

    async def push(self, name: str) -> str:
        stack = await self.get()
        frame = RoutineFrame(name=name)
        stack.append(frame)
        await self.set(stack)
        return frame.id

    async def pop(self) -> RoutineFrame | None:
        stack = await self.get()
        if not stack:
            return None
        frame = stack.pop()
        await self.set(stack)
        return frame

    async def peek(self) -> RoutineFrame | None:
        stack = await self.get()
        if not stack:
            return None
        return stack[-1]

    async def update(self, frame: RoutineFrame) -> None:
        """Updates the top frame in the stack."""
        stack = await self.get()
        stack[-1] = frame
        await self.set(stack)

    async def set(self, frames: List[RoutineFrame]) -> None:
        """Replaces the stack with the given list of frames."""
        self.drive.write_model(
            RoutineStackData(frames=frames),
            STACK_FILENAME,
            if_exists=IfDriveFileExistsBehavior.OVERWRITE,
        )

    async def get_current_state(self) -> dict[str, Any]:
        """Returns the state of the current routine."""
        frame = await self.peek()
        if frame:
            return frame.state
        return {}

    async def set_current_state(self, state: dict[str, Any]) -> None:
        """Updates the state of the current routine."""
        frame = await self.peek()
        if frame:
            frame.state = state
            await self.update(frame)

    async def get_current_state_key(self, key: str) -> Any:
        state = await self.get_current_state()
        return state.get(key)

    async def set_current_state_key(self, key: str, value: Any) -> None:
        state = await self.get_current_state()
        state[key] = value
        await self.set_current_state(state)

    async def clear(self) -> None:
        await self.set([])

    async def length(self) -> int:
        return len(await self.get())

    async def string(self) -> str:
        return str([f"{frame.name}.{frame.id}" for frame in await self.get()])

    @asynccontextmanager
    async def stack_frame_state(self) -> AsyncGenerator[dict[str, Any], None]:
        """
        A context manager that allows you to get and set the state of the
        current routine being run. This is useful for storing and retrieving
        information that is needed across multiple steps of a routine.

        Example:

        ```
        async with context.stack_frame_state() as state:
            state["key"] = "value"
        ```
        """
        state = await self.get_current_state()
        yield state
        await self.set_current_state(state)
