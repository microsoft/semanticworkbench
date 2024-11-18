from typing import Any, List
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
