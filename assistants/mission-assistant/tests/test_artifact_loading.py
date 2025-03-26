import shutil
import pathlib
import unittest
import unittest.mock
import uuid
from typing import Any, TypeVar, cast

from assistant.artifacts import MissionBriefing, ArtifactType
from assistant.artifact_messaging import ArtifactMessenger
from assistant.mission_storage import (
    ConversationMissionManager,
    MissionRole,
    MissionStorageManager,
    MissionStorageWriter,
)
from semantic_workbench_assistant import settings

# Type variable for better type annotations
T = TypeVar('T')


class TestArtifactLoading(unittest.IsolatedAsyncioTestCase):
    """Test the artifact loading functionality with the new storage architecture"""
    
    async def asyncSetUp(self):
        # Create a test storage path
        self.test_dir = pathlib.Path(__file__).parent.parent / '.data' / 'test_artifact_loading'
        self.test_dir.mkdir(exist_ok=True, parents=True)
        
        # Mock settings to use our test directory
        self.original_storage_root = settings.storage.root
        settings.storage.root = str(self.test_dir)
        
        # Create test mission and conversation IDs
        self.mission_id = str(uuid.uuid4())
        self.conversation_id = str(uuid.uuid4())
        
        # Create a test briefing artifact
        self.briefing_artifact_id = str(uuid.uuid4())
        self.mission_name = "Test Mission"
        
        # Create mission directory structure
        self.mission_dir = MissionStorageManager.get_mission_dir(self.mission_id)
        self.shared_dir = MissionStorageManager.get_shared_dir(self.mission_id)
        self.briefing_dir = MissionStorageManager.get_artifact_dir(self.mission_id, ArtifactType.MISSION_BRIEFING.value)
        
        # Create the test artifact
        self.create_test_artifact()
        
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
        
    async def asyncTearDown(self):
        # Clean up the test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Restore settings
        settings.storage.root = self.original_storage_root
        
        # Stop all patches
        for patch in self.patches:
            patch.stop()
    
    def create_test_artifact(self):
        """Create a test artifact in the mission's shared directory"""
        # Create the mission briefing
        briefing = MissionBriefing(
            artifact_id=self.briefing_artifact_id,
            mission_name=self.mission_name,
            mission_description="Test mission description",
            created_by="test-user",
            updated_by="test-user",
            conversation_id=self.conversation_id,
        )
        
        # Write to the mission's shared briefing directory
        MissionStorageWriter.write_artifact(
            self.mission_id,
            ArtifactType.MISSION_BRIEFING.value,
            self.briefing_artifact_id,
            briefing
        )
    
    async def test_get_artifacts_by_type(self) -> None:
        """Test that get_artifacts_by_type correctly loads artifacts from the mission storage"""
        # Using Any here to satisfy type checker with our mock
        context: Any = self.context
        
        briefings = await ArtifactMessenger.get_artifacts_by_type(context, MissionBriefing)
        
        self.assertEqual(len(briefings), 1, "Should find exactly one briefing")
        
        # Type assertion to help type checker
        self.assertIsInstance(briefings[0], MissionBriefing)
        
        # Now safe to access attributes
        first_briefing = cast(MissionBriefing, briefings[0])
        self.assertEqual(first_briefing.artifact_id, self.briefing_artifact_id)
        self.assertEqual(first_briefing.mission_name, self.mission_name)
    
    async def test_load_artifact(self) -> None:
        """Test that load_artifact correctly loads an artifact from the mission storage"""
        # Using Any here to satisfy type checker with our mock
        context: Any = self.context
        
        briefing_result = await ArtifactMessenger.load_artifact(context, self.briefing_artifact_id, MissionBriefing)
        
        self.assertIsNotNone(briefing_result, "Should load the briefing")
        
        if briefing_result:  # Type guard for static analysis
            # Safe access with cast
            briefing = cast(MissionBriefing, briefing_result)
            self.assertEqual(briefing.artifact_id, self.briefing_artifact_id)
            self.assertEqual(briefing.mission_name, self.mission_name)


if __name__ == "__main__":
    unittest.main()