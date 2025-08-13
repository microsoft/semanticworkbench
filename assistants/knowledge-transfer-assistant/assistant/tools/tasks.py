from assistant.data import InspectorTab, NewTaskInfo, TaskInfo, TaskPriority, TaskStatus
from assistant.domain.tasks_manager import TasksManager
from assistant.logging import logger
from assistant.notifications import Notifications

from .base import ToolsBase


class TaskTools(ToolsBase):
    async def add_task(self, status: str, priority: str, content: str) -> str:
        """
        Add a new task to the task list.

        Args:
            status (str): The new status of the task. pending, in_progress, completed, or cancelled.
            priority (TaskPriority): The new priority of the task. low, medium, or high.
            content (str): The content of the task to update.

        Returns:
            Message indicating success or failure
        """
        try:
            task_info = NewTaskInfo(
                status=TaskStatus(status),
                priority=TaskPriority(priority),
                content=content,
            )
            await TasksManager.add_tasks(self.context, [task_info])
            await Notifications.notify(
                self.context,
                "Task added.",
                debug_data={"task_info": task_info},
            )
            await Notifications.notify_state_update(self.context, [InspectorTab.DEBUG])
            return "Task added successfully."
        except Exception as e:
            logger.exception(f"Failed to add task: {e}")
            return f"Failed to add task: {e!s}"

    async def update_task(self, task_id: str, status: str, priority: str, content: str) -> str:
        """
        Update a task's status, priority, or content. Use this for managing the task list. This should be called every time work has been done on a task or when the task needs to be updated.

        Args:
            status (str): The new status of the task. pending, in_progress, completed, or cancelled.
            priority (TaskPriority): The new priority of the task. low, medium, or high.
            content (str): The content of the task to update.

        Returns:
            Message indicating success or failure
        """  # noqa: E501
        try:
            task_info = TaskInfo(
                task_id=task_id,
                status=TaskStatus(status),
                priority=TaskPriority(priority),
                content=content,
            )
            await TasksManager.update_task(self.context, task_info)
            await Notifications.notify(
                self.context,
                "Task updated.",
                debug_data={"task_info": task_info},
            )
            await Notifications.notify_state_update(self.context, [InspectorTab.DEBUG])
            return f"Task {task_info.task_id} updated successfully."
        except Exception as e:
            logger.exception(f"Failed to update task: {e}")
            return f"Failed to update task: {e!s}"

    async def delete_task(self, task_id: str) -> str:
        """
        Mark a task completed. This should be called EVERY TIME a task has been completed.
        Args:
            task (str): The task UUID to mark completed.
        Returns:
            Message indicating success or failure
        """
        try:
            await TasksManager.remove_task(self.context, task_id)
            await Notifications.notify(self.context, "Task marked completed.", debug_data={"task": task_id})
            await Notifications.notify_state_update(self.context, [InspectorTab.DEBUG])
            message = f"Task marked completed: {task_id}"
            logger.info(message)
            return "Marked completed."
        except Exception as e:
            message = f"Failed to mark task completed: {e!s}"
            logger.exception(message)
            return message
