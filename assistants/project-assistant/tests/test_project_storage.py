"""
Tests for the direct project storage functionality.
"""

import pathlib
import shutil
import unittest
import unittest.mock
import uuid
from datetime import datetime

from assistant.project_data import (
    InformationRequest,
    LogEntry,
    LogEntryType,
    ProjectBrief,
    ProjectGoal,
    ProjectLog,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from assistant.project_storage import (
    ProjectRole,
    ProjectStorage,
    ProjectStorageManager,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.storage import write_model


class TestProjectStorage(unittest.IsolatedAsyncioTestCase):
    """Test the direct project storage functionality."""

    async def asyncSetUp(self):
        """Set up test environment."""
        # Create a test directory
        self.test_dir = pathlib.Path(__file__).parent.parent / ".data" / "test_project_storage"
        self.test_dir.mkdir(parents=True, exist_ok=True)

        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)

        # Create test IDs
        self.project_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"

        # Create project directory structure
        self.project_dir = ProjectStorageManager.get_project_dir(self.project_id)

        # Set up directories for different conversation roles
        self.coordinator_dir = self.project_dir / ProjectRole.COORDINATOR.value
        self.coordinator_dir.mkdir(exist_ok=True)

        self.team_dir = self.project_dir / f"team_{self.conversation_id}"
        self.team_dir.mkdir(exist_ok=True)

        # Set up patching
        self.patches = []

        # Create a mock context
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
            "assistant.project_storage.storage_directory_for_context", side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)

        # Create initial test data
        self.create_test_project_data()

    async def asyncTearDown(self):
        """Clean up test environment."""
        # Clean up the test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Restore settings
        settings.storage.root = self.original_storage_root

        # Stop all patches
        for patch in self.patches:
            patch.stop()

    def create_test_project_data(self):
        """Create test project data."""
        # Create a project brief
        test_goal = ProjectGoal(
            name="Test Goal",
            description="This is a test goal",
            success_criteria=[SuccessCriterion(description="Test criterion")],
        )

        brief = ProjectBrief(
            project_name="Test Project",
            project_description="Test project description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
            goals=[test_goal],
        )

        # Write brief to the proper path using ProjectStorage
        brief_path = ProjectStorageManager.get_brief_path(self.project_id)
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(brief_path, brief)

        # Create an information request
        request = InformationRequest(
            request_id=str(uuid.uuid4()),
            title="Test Request",
            description="This is a test request",
            priority=RequestPriority.HIGH,
            status=RequestStatus.NEW,  # Use enum value
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write request to the proper path using ProjectStorage
        request_path = ProjectStorageManager.get_information_request_path(self.project_id, request.request_id)
        request_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(request_path, request)

        # Create context directories
        context_dir = self.test_dir / f"context_{self.conversation_id}"
        context_dir.mkdir(exist_ok=True, parents=True)

    async def test_read_project_brief(self):
        """Test reading a project brief."""
        # Read the brief using ProjectStorage
        brief = ProjectStorage.read_project_brief(self.project_id)

        # Verify the brief was loaded correctly
        self.assertIsNotNone(brief, "Should load the brief")
        if brief:  # Type checking guard
            self.assertEqual(brief.project_name, "Test Project")
            self.assertEqual(brief.project_description, "Test project description")
            self.assertEqual(len(brief.goals), 1)
            self.assertEqual(brief.goals[0].name, "Test Goal")

    async def test_read_information_request(self):
        """Test reading an information request."""
        # First get all requests to find the request ID
        requests = ProjectStorage.get_all_information_requests(self.project_id)
        self.assertEqual(len(requests), 1, "Should find one request")
        request_id = requests[0].request_id

        # Read the request using ProjectStorage
        request = ProjectStorage.read_information_request(self.project_id, request_id)

        # Verify the request was loaded correctly
        self.assertIsNotNone(request, "Should load the request")
        if request:  # Type checking guard
            self.assertEqual(request.title, "Test Request")
            self.assertEqual(request.description, "This is a test request")
            self.assertEqual(request.priority, RequestPriority.HIGH)

    async def test_write_project_log(self):
        """Test writing a project log."""
        # Create a log entry and proper LogEntry objects
        log_entry = ProjectLog(
            entries=[
                LogEntry(
                    id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow(),
                    entry_type=LogEntryType.INFORMATION_UPDATE,
                    message="Test log entry",
                    user_id=self.user_id,
                    user_name="Test User",
                )
            ],
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
        )

        # Write the log
        ProjectStorage.write_project_log(self.project_id, log_entry)

        # Read the log back
        log = ProjectStorage.read_project_log(self.project_id)

        # Verify the log was saved and loaded correctly
        self.assertIsNotNone(log, "Should load the log")
        if log:  # Type checking guard
            self.assertEqual(len(log.entries), 1)
            self.assertEqual(log.entries[0].entry_type, LogEntryType.INFORMATION_UPDATE)
            self.assertEqual(log.entries[0].message, "Test log entry")

    async def test_project_directory_structure(self):
        """Test the project directory structure."""
        # Verify project directory exists
        self.assertTrue(self.project_dir.exists(), "Project directory should exist")

        # Verify Coordinator directory exists
        self.assertTrue(self.coordinator_dir.exists(), "Coordinator directory should exist")

        # Verify team directory exists
        self.assertTrue(self.team_dir.exists(), "Team directory should exist")


if __name__ == "__main__":
    unittest.main()
