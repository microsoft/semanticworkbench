from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import NewTaskInfo, TaskInfo
from assistant.domain.share_manager import ShareManager
from assistant.storage import ShareStorage


class TasksManager:
    @staticmethod
    async def get_tasks(
        context: ConversationContext,
    ) -> list[TaskInfo]:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return []
        return ShareStorage.read_tasks(share_id)

    @staticmethod
    async def add_tasks(
        context: ConversationContext,
        tasks: list[NewTaskInfo],
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.add_tasks(share_id, tasks)

    @staticmethod
    async def update_task(
        context: ConversationContext,
        task: TaskInfo,
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.update_task(share_id, task)

    @staticmethod
    async def remove_task(
        context: ConversationContext,
        task_id: str,
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.remove_task(share_id, task_id)

    @staticmethod
    async def set_task_list(
        context: ConversationContext,
        tasks: list[TaskInfo],
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.set_all_tasks(share_id, tasks)
