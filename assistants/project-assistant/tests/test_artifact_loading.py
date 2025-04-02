"""
Tests for the project storage functionality with the direct storage approach.
These tests replace the previous artifact-based tests.
"""

import shutil
import pathlib
import unittest
import unittest.mock
import uuid
from typing import Any, TypeVar

from assistant.project_data import ProjectBrief, ProjectGoal, SuccessCriterion
from assistant.project_manager import ProjectManager
from assistant.project import (
    ConversationProjectManager,
    ProjectRole,
    ProjectStorageManager,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.storage import read_model, write_model

# Type variable for better type annotations
T = TypeVar("T")


class TestProjectStorage(unittest.IsolatedAsyncioTestCase):
    """Test the project storage functionality with the new direct storage approach"""

    async def asyncSetUp(self):
        # Create a test storage path
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_project_storage"
        self.test_dir.mkdir(exist_ok=True, parents=True)

        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)

        # Create test project and conversation IDs
        self.project_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"
        self.user_name = "Test User"

        # Create project directory structure
        self.project_dir = ProjectStorageManager.get_project_dir(self.project_id)
        self.shared_dir = ProjectStorageManager.get_shared_dir(self.project_id)

        # Set up patching
        self.patches = []

        # Create a mock context that will be recognized as ConversationContext
        self.context = unittest.mock.MagicMock()
        self.context.id = self.conversation_id

        # Mock assistant
        mock_assistant = unittest.mock.MagicMock()
        mock_assistant.id = "test-assistant-id"
        self.context.assistant = mock_assistant

        # Patch storage_directory_for_context
        def mock_storage_directory_for_context(context, *args, **kwargs):
            return self.test_dir / f"context_{context.id}"

        patch1 = unittest.mock.patch(
            "assistant.project.storage_directory_for_context", side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)

        # Patch get_conversation_project
        async def mock_get_conversation_project(context):
            return self.project_id

        patch2 = unittest.mock.patch.object(
            ConversationProjectManager, "get_conversation_project", side_effect=mock_get_conversation_project
        )
        self.mock_get_project = patch2.start()
        self.patches.append(patch2)

        # Patch get_conversation_role
        async def mock_get_conversation_role(context):
            return ProjectRole.COORDINATOR

        patch3 = unittest.mock.patch.object(
            ConversationProjectManager, "get_conversation_role", side_effect=mock_get_conversation_role
        )
        self.mock_get_role = patch3.start()
        self.patches.append(patch3)

        # Create a test brief
        self.project_name = "Test Project"
        self.create_test_brief()

    async def asyncTearDown(self):
        # Clean up the test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Restore settings
        settings.storage.root = self.original_storage_root

        # Stop all patches
        for patch in self.patches:
            patch.stop()

    def create_test_brief(self):
        """Create a test project brief in the project's shared directory"""
        # Create a project brief
        test_goal = ProjectGoal(
            name="Test Goal",
            description="This is a test goal",
            success_criteria=[SuccessCriterion(description="Test criteria")],
        )

        brief = ProjectBrief(
            project_name=self.project_name,
            project_description="Test project description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
            goals=[test_goal],
        )

        # Write to the project's shared directory using the correct path
        brief_path = ProjectStorageManager.get_brief_path(self.project_id)
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(brief_path, brief)

    async def test_get_project_brief(self) -> None:
        """Test that get_project_brief correctly loads the brief from storage"""
        # Mock the ProjectManager to use our test context
        with unittest.mock.patch.object(ProjectManager, "get_project_id", return_value=self.project_id):
            # Using Any here to satisfy type checker with our mock
            context: Any = self.context

            # Get the brief using the ProjectManager
            brief = await ProjectManager.get_project_brief(context)

            # Verify the brief was loaded correctly
            self.assertIsNotNone(brief, "Should load the brief")
            if brief:  # Type checking guard
                self.assertEqual(brief.project_name, self.project_name)
                self.assertEqual(brief.conversation_id, self.conversation_id)
                self.assertEqual(len(brief.goals), 1, "Should have one goal")
                self.assertEqual(brief.goals[0].name, "Test Goal")

    async def test_direct_storage_access(self) -> None:
        """Test direct access to project storage"""
        # Test basic storage operations
        brief_path = ProjectStorageManager.get_brief_path(self.project_id)

        # Read the brief directly using read_model
        brief = read_model(brief_path, ProjectBrief)

        # Verify we got the correct brief
        self.assertIsNotNone(brief, "Should load the brief directly")
        if brief:  # Type checking guard
            self.assertEqual(brief.project_name, self.project_name)

            # Test updating the brief
            brief.project_name = "Updated Project Name"
            write_model(brief_path, brief)

            # Read it back to verify the update
            updated_brief = read_model(brief_path, ProjectBrief)
            if updated_brief:  # Type checking guard
                self.assertEqual(updated_brief.project_name, "Updated Project Name")


if __name__ == "__main__":
    unittest.main()
