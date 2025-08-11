from assistant.data import InspectorTab
from assistant.domain.tasks_manager import TasksManager
from assistant.logging import logger
from assistant.notifications import Notifications

from .base import ToolsBase


class TaskTools(ToolsBase):
    async def delete_task(self, task: str) -> str:
        """
        Mark a task completed. This should be called EVERY TIME a task has been completed.
        Args:
            task (str): The task to mark completed. Must be the full text of the task as it appears in the task list.
        Returns:
            Message indicating success or failure
        """
        try:
            await TasksManager.remove_task(self.context, task)
            await Notifications.notify(self.context, "Task marked completed.", debug_data={"task": task})
            await Notifications.notify_all_state_update(self.context, [InspectorTab.DEBUG])
            message = f"Task marked completed: {task}"
            logger.info(message)
            return "Marked completed."
        except Exception as e:
            message = f"Failed to mark task completed: {e!s}"
            logger.exception(message)
            return message
