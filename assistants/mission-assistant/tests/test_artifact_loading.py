import asyncio
import json
import os
import shutil
import pathlib
import unittest
import unittest.mock
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING, TypeVar, cast

# Import only the type
if TYPE_CHECKING:
    from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.artifacts import MissionBriefing, ArtifactType
from assistant.artifact_messaging import ArtifactMessenger

# Type variable for better type annotations
T = TypeVar('T')


class TestArtifactLoading(unittest.IsolatedAsyncioTestCase):
    """Test the artifact loading functionality"""
    
    async def asyncSetUp(self):
        # Create a test storage path
        self.test_dir = pathlib.Path(__file__).parent.parent / '.data' / 'test_dir'
        self.test_dir.mkdir(exist_ok=True, parents=True)
        
        # Create artifacts directory
        self.artifacts_dir = self.test_dir / 'artifacts'
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Create a test briefing artifact
        self.briefing_artifact_id = str(uuid.uuid4())
        self.mission_name = "Test Mission"
        
        # Create the mission briefing in both formats
        self.enum_value_dir = self.artifacts_dir / ArtifactType.MISSION_BRIEFING.value
        self.enum_value_dir.mkdir(exist_ok=True)
        
        self.class_name_dir = self.artifacts_dir / str(MissionBriefing)
        self.class_name_dir.mkdir(exist_ok=True)
        
        # Create the test artifact
        self.create_test_artifact()
        
        # Set up patching
        self.patches = []
        
        # Patch MissionStateManager.get_state_file_path
        from assistant.mission import MissionStateManager
        patch1 = unittest.mock.patch.object(
            MissionStateManager, 
            'get_state_file_path',
            return_value=self.test_dir / "mission_links.json"
        )
        self.mock_get_state_file_path = patch1.start()
        self.patches.append(patch1)
        
        # Create a mock context that will be recognized as ConversationContext
        self.context = unittest.mock.MagicMock()
        self.context.id = "test-conversation-id"
        
        # Mock assistant
        mock_assistant = unittest.mock.MagicMock()
        mock_assistant.id = "test-assistant-id"
        self.context.assistant = mock_assistant
        
    async def asyncTearDown(self):
        # Clean up the test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        
        # Stop all patches
        for patch in self.patches:
            patch.stop()
    
    def create_test_artifact(self):
        """Create a test artifact in both directory formats"""
        artifact_data = {
            "artifact_id": self.briefing_artifact_id,
            "artifact_type": ArtifactType.MISSION_BRIEFING.value,
            "version": 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": "test-user",
            "updated_by": "test-user",
            "conversation_id": "test-conversation-id",
            "mission_name": self.mission_name,
            "mission_description": "Test mission description",
            "goals": []
        }
        
        # Write to enum value directory
        with open(self.enum_value_dir / f"{self.briefing_artifact_id}.json", "w") as f:
            json.dump(artifact_data, f, indent=2)
    
    async def test_get_artifacts_by_type(self) -> None:
        """Test that get_artifacts_by_type correctly loads artifacts from the enum value directory"""
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
        """Test that load_artifact correctly loads an artifact from the enum value directory"""
        # Using Any here to satisfy type checker with our mock
        context: Any = self.context
        
        briefing_result = await ArtifactMessenger.load_artifact(context, self.briefing_artifact_id, MissionBriefing)
        
        self.assertIsNotNone(briefing_result, "Should load the briefing")
        
        # Safe access with cast
        briefing = cast(MissionBriefing, briefing_result)
        self.assertEqual(briefing.artifact_id, self.briefing_artifact_id)
        self.assertEqual(briefing.mission_name, self.mission_name)


if __name__ == "__main__":
    unittest.main()