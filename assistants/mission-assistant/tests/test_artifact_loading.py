"""
Tests for the mission storage functionality with the direct storage approach.
These tests replace the previous artifact-based tests.
"""

import shutil
import pathlib
import unittest
import unittest.mock
import uuid
from typing import Any, TypeVar

from assistant.mission_data import MissionBriefing, MissionGoal, SuccessCriterion
from assistant.mission_manager import MissionManager
from assistant.mission_storage import (
    ConversationMissionManager,
    MissionRole,
    MissionStorageManager,
)
from semantic_workbench_assistant import settings
from semantic_workbench_assistant.storage import read_model, write_model

# Type variable for better type annotations
T = TypeVar('T')


class TestMissionStorage(unittest.IsolatedAsyncioTestCase):
    """Test the mission storage functionality with the new direct storage approach"""
    
    async def asyncSetUp(self):
        # Create a test storage path
        self.test_dir = pathlib.Path(__file__).parent.parent / '.data' / 'test_mission_storage'
        self.test_dir.mkdir(exist_ok=True, parents=True)
        
        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)
        
        # Create test mission and conversation IDs
        self.mission_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        self.user_id = "test-user-id"
        self.user_name = "Test User"
        
        # Create mission directory structure
        self.mission_dir = MissionStorageManager.get_mission_dir(self.mission_id)
        self.shared_dir = MissionStorageManager.get_shared_dir(self.mission_id)
        
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
            "assistant.mission_storage.storage_directory_for_context",
            side_effect=mock_storage_directory_for_context
        )
        self.mock_storage_directory = patch1.start()
        self.patches.append(patch1)
        
        # Patch get_conversation_mission
        async def mock_get_conversation_mission(context):
            return self.mission_id
            
        patch2 = unittest.mock.patch.object(
            ConversationMissionManager, 
            'get_conversation_mission',
            side_effect=mock_get_conversation_mission
        )
        self.mock_get_mission = patch2.start()
        self.patches.append(patch2)
        
        # Patch get_conversation_role
        async def mock_get_conversation_role(context):
            return MissionRole.HQ
            
        patch3 = unittest.mock.patch.object(
            ConversationMissionManager, 
            'get_conversation_role',
            side_effect=mock_get_conversation_role
        )
        self.mock_get_role = patch3.start()
        self.patches.append(patch3)
        
        # Create a test briefing
        self.mission_name = "Test Mission"
        self.create_test_briefing()
        
    async def asyncTearDown(self):
        # Clean up the test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Restore settings
        settings.storage.root = self.original_storage_root
        
        # Stop all patches
        for patch in self.patches:
            patch.stop()
    
    def create_test_briefing(self):
        """Create a test mission briefing in the mission's shared directory"""
        # Create a mission briefing
        test_goal = MissionGoal(
            name="Test Goal",
            description="This is a test goal",
            success_criteria=[
                SuccessCriterion(description="Test criteria")
            ]
        )
        
        briefing = MissionBriefing(
            mission_name=self.mission_name,
            mission_description="Test mission description",
            created_by=self.user_id,
            updated_by=self.user_id,
            conversation_id=self.conversation_id,
            goals=[test_goal]
        )
        
        # Write to the mission's shared directory using the correct path
        briefing_path = MissionStorageManager.get_briefing_path(self.mission_id)
        briefing_path.parent.mkdir(parents=True, exist_ok=True)
        write_model(briefing_path, briefing)
    
    async def test_get_mission_briefing(self) -> None:
        """Test that get_mission_briefing correctly loads the briefing from storage"""
        # Mock the MissionManager to use our test context
        with unittest.mock.patch.object(
            MissionManager, 'get_mission_id', return_value=self.mission_id
        ):
            # Using Any here to satisfy type checker with our mock
            context: Any = self.context
            
            # Get the briefing using the MissionManager
            briefing = await MissionManager.get_mission_briefing(context)
            
            # Verify the briefing was loaded correctly
            self.assertIsNotNone(briefing, "Should load the briefing")
            if briefing:  # Type checking guard
                self.assertEqual(briefing.mission_name, self.mission_name)
                self.assertEqual(briefing.conversation_id, self.conversation_id)
                self.assertEqual(len(briefing.goals), 1, "Should have one goal")
                self.assertEqual(briefing.goals[0].name, "Test Goal")
    
    async def test_direct_storage_access(self) -> None:
        """Test direct access to mission storage"""
        # Test basic storage operations
        briefing_path = MissionStorageManager.get_briefing_path(self.mission_id)
        
        # Read the briefing directly using read_model
        briefing = read_model(briefing_path, MissionBriefing)
        
        # Verify we got the correct briefing
        self.assertIsNotNone(briefing, "Should load the briefing directly")
        if briefing:  # Type checking guard
            self.assertEqual(briefing.mission_name, self.mission_name)
            
            # Test updating the briefing
            briefing.mission_name = "Updated Mission Name"
            write_model(briefing_path, briefing)
            
            # Read it back to verify the update
            updated_briefing = read_model(briefing_path, MissionBriefing)
            if updated_briefing:  # Type checking guard
                self.assertEqual(updated_briefing.mission_name, "Updated Mission Name")


if __name__ == "__main__":
    unittest.main()