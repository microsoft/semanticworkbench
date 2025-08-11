from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.domain.share_manager import ShareManager
from assistant.storage import ShareStorage


class TasksManager:
    @staticmethod
    async def get_tasks(
        context: ConversationContext,
    ) -> list[str]:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return []
        return ShareStorage.read_tasks(share_id)

    @staticmethod
    async def add_tasks(
        context: ConversationContext,
        tasks: list[str],
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.add_tasks(share_id, tasks)

    @staticmethod
    async def remove_task(
        context: ConversationContext,
        task: str,
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.remove_task(share_id, task)

    @staticmethod
    async def set_task_list(
        context: ConversationContext,
        tasks: list[str],
    ) -> None:
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return
        ShareStorage.set_all_tasks(share_id, tasks)
