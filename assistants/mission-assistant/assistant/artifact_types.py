"""
Type definitions for the Mission Assistant artifacts.

This module provides TypeVars and Union types for the various artifact classes
to help with type checking and ensure proper attribute access.
"""

from typing import Any, Dict, List, TypeVar, Union, cast

from .artifacts import (
    ArtifactType,
    BaseArtifact,
    FieldRequest,
    KBSection, 
    LogEntry,
    MissionBriefing,
    MissionGoal,
    MissionKB,
    MissionLog,
    MissionStatus,
)

# Create TypeVar for BaseArtifact and its subclasses
T_BaseArtifact = TypeVar('T_BaseArtifact', bound=BaseArtifact)

# Define Union types for artifact classes
ArtifactUnion = Union[
    MissionBriefing,
    MissionKB,
    MissionStatus,
    FieldRequest,
    MissionLog,
]

# Type casting functions
def cast_to_mission_briefing(artifact: BaseArtifact) -> MissionBriefing:
    """Cast BaseArtifact to MissionBriefing with type checking."""
    if artifact.artifact_type != ArtifactType.MISSION_BRIEFING:
        raise TypeError(f"Cannot cast {artifact.artifact_type} to MissionBriefing")
    return cast(MissionBriefing, artifact)

def cast_to_mission_kb(artifact: BaseArtifact) -> MissionKB:
    """Cast BaseArtifact to MissionKB with type checking."""
    if artifact.artifact_type != ArtifactType.MISSION_KB:
        raise TypeError(f"Cannot cast {artifact.artifact_type} to MissionKB")
    return cast(MissionKB, artifact)

def cast_to_mission_status(artifact: BaseArtifact) -> MissionStatus:
    """Cast BaseArtifact to MissionStatus with type checking."""
    if artifact.artifact_type != ArtifactType.MISSION_STATUS:
        raise TypeError(f"Cannot cast {artifact.artifact_type} to MissionStatus")
    return cast(MissionStatus, artifact)

def cast_to_field_request(artifact: BaseArtifact) -> FieldRequest:
    """Cast BaseArtifact to FieldRequest with type checking."""
    if artifact.artifact_type != ArtifactType.FIELD_REQUEST:
        raise TypeError(f"Cannot cast {artifact.artifact_type} to FieldRequest")
    return cast(FieldRequest, artifact)

def cast_to_mission_log(artifact: BaseArtifact) -> MissionLog:
    """Cast BaseArtifact to MissionLog with type checking."""
    if artifact.artifact_type != ArtifactType.MISSION_LOG:
        raise TypeError(f"Cannot cast {artifact.artifact_type} to MissionLog")
    return cast(MissionLog, artifact)

def cast_artifact(artifact: BaseArtifact) -> ArtifactUnion:
    """Cast BaseArtifact to appropriate subclass based on artifact_type."""
    if artifact.artifact_type == ArtifactType.MISSION_BRIEFING:
        return cast_to_mission_briefing(artifact)
    elif artifact.artifact_type == ArtifactType.MISSION_KB:
        return cast_to_mission_kb(artifact)
    elif artifact.artifact_type == ArtifactType.MISSION_STATUS:
        return cast_to_mission_status(artifact)
    elif artifact.artifact_type == ArtifactType.FIELD_REQUEST:
        return cast_to_field_request(artifact)
    elif artifact.artifact_type == ArtifactType.MISSION_LOG:
        return cast_to_mission_log(artifact)
    else:
        raise TypeError(f"Unknown artifact type: {artifact.artifact_type}")

# Helper functions to access specific attributes from BaseArtifact

def get_entries(artifact: BaseArtifact) -> List[LogEntry]:
    """Safely access the entries attribute from a MissionLog."""
    if artifact.artifact_type == ArtifactType.MISSION_LOG:
        return cast_to_mission_log(artifact).entries
    raise AttributeError(f"Artifact of type {artifact.artifact_type} has no 'entries' attribute")

def get_sections(artifact: BaseArtifact) -> Dict[str, KBSection]:
    """Safely access the sections attribute from a MissionKB."""
    if artifact.artifact_type == ArtifactType.MISSION_KB:
        return cast_to_mission_kb(artifact).sections
    raise AttributeError(f"Artifact of type {artifact.artifact_type} has no 'sections' attribute")

def get_goals(artifact: BaseArtifact) -> List[MissionGoal]:
    """Safely access the goals attribute from a MissionBriefing or MissionStatus."""
    if artifact.artifact_type == ArtifactType.MISSION_BRIEFING:
        return cast_to_mission_briefing(artifact).goals
    elif artifact.artifact_type == ArtifactType.MISSION_STATUS:
        return cast_to_mission_status(artifact).goals
    raise AttributeError(f"Artifact of type {artifact.artifact_type} has no 'goals' attribute")

def get_lifecycle(artifact: BaseArtifact) -> Dict[str, Any]:
    """Safely access the lifecycle attribute from a MissionStatus."""
    if artifact.artifact_type == ArtifactType.MISSION_STATUS:
        return cast_to_mission_status(artifact).lifecycle
    raise AttributeError(f"Artifact of type {artifact.artifact_type} has no 'lifecycle' attribute")

def get_status(artifact: BaseArtifact) -> str:
    """Safely access the status attribute from a MissionStatus or FieldRequest."""
    if artifact.artifact_type == ArtifactType.MISSION_STATUS:
        return cast_to_mission_status(artifact).state.value
    elif artifact.artifact_type == ArtifactType.FIELD_REQUEST:
        return cast_to_field_request(artifact).status.value
    raise AttributeError(f"Artifact of type {artifact.artifact_type} has no 'status' attribute")