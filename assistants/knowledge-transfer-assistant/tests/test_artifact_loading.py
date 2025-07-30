"""
Tests for the project storage functionality with the direct storage approach.
These tests replace the previous artifact-based tests.
"""

import pathlib
import shutil
import unittest
import unittest.mock
import uuid
from typing import Any, TypeVar

from assistant.data import (
    ConversationRole,
    KnowledgeBrief,
    KnowledgePackage,
    LearningObjective,
    LearningOutcome,
)
from assistant.domain import KnowledgeBriefManager, ShareManager
from assistant.storage import ShareStorage, ShareStorageManager
from semantic_workbench_assistant import settings

# Type variable for better type annotations
T = TypeVar("T")


class TestShareStorage(unittest.IsolatedAsyncioTestCase):
    """Test the project storage functionality with the new direct storage approach"""

    async def asyncSetUp(self):
        # Create a test storage path
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_project_storage"
        self.test_dir.mkdir(exist_ok=True, parents=True)

        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)

        # Create test project and conversation IDs
        self.share_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"
        self.user_name = "Test User"

        # Create project directory structure
        self.project_dir = ShareStorageManager.get_share_dir(self.share_id)

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
            "semantic_workbench_assistant.assistant_app.context.storage_directory_for_context",
            side_effect=mock_storage_directory_for_context,
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)

        # Patch get_share_id
        async def mock_get_share_id(context):
            return self.share_id

        patch2 = unittest.mock.patch.object(ShareManager, "get_share_id", side_effect=mock_get_share_id)
        self.mock_get_project = patch2.start()
        self.patches.append(patch2)

        # Patch get_conversation_role
        async def mock_get_conversation_role(context):
            return ConversationRole.COORDINATOR

        patch3 = unittest.mock.patch.object(
            ShareManager,
            "get_conversation_role",
            side_effect=mock_get_conversation_role,
        )
        self.mock_get_role = patch3.start()
        self.patches.append(patch3)

        # Create a test brief
        self.title = "Test KnowledgePackage"
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
        test_goal = LearningObjective(
            name="Test Goal",
            description="This is a test goal",
            learning_outcomes=[LearningOutcome(description="Test criteria")],
        )

        brief = KnowledgeBrief(
            title=self.title,
            content="Test project description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Create a project with the goal
        project = KnowledgePackage(
            share_id="test-share-id",
            brief=brief,
            learning_objectives=[test_goal],
            digest=None,
        )

        # Write the project to storage using ShareStorage to ensure proper consolidated format
        ShareStorage.write_share(self.share_id, project)

    async def test_get_project_brief(self) -> None:
        """Test that get_project_brief correctly loads the brief from storage"""
        # Mock the KnowledgeTransferManager to use our test context
        with unittest.mock.patch.object(ShareManager, "get_share_id", return_value=self.share_id):
            # Using Any here to satisfy type checker with our mock
            context: Any = self.context

            brief = await KnowledgeBriefManager.get_knowledge_brief(context)
            project = ShareStorage.read_share(self.share_id)

            assert brief is not None, "Should load the brief"
            if brief:  # Type checking guard
                assert brief.title == self.title
                assert brief.conversation_id == self.conversation_id

            # Verify the project goals were loaded correctly
            assert project is not None, "Should load the project"
            if project:  # Type checking guard
                assert len(project.learning_objectives) == 1, "Should have one goal"
                assert project.learning_objectives[0].name == "Test Goal"

    async def test_direct_storage_access(self) -> None:
        """Test direct access to project storage"""
        # Test basic storage operations with consolidated storage
        brief = ShareStorage.read_knowledge_brief(self.share_id)

        # Verify we got the correct brief
        assert brief is not None, "Should load the brief directly"
        if brief:  # Type checking guard
            assert brief.title == self.title

            # Test updating the brief using consolidated storage
            brief.title = "Updated KnowledgePackageTitle"
            ShareStorage.write_knowledge_brief(self.share_id, brief)

            # Read it back to verify the update
            updated_brief = ShareStorage.read_knowledge_brief(self.share_id)
            if updated_brief:  # Type checking guard
                assert updated_brief.title == "Updated KnowledgePackageTitle"


if __name__ == "__main__":
    unittest.main()
