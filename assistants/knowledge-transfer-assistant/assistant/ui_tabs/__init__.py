"""
Inspector modules for the Knowledge Transfer Assistant. Provide different views
of the knowledge transfer state in the workbench UI.
"""

from .brief import BriefInspector
from .debug import DebugInspector
from .learning import LearningInspector
from .sharing import SharingInspector

__all__ = ["BriefInspector", "DebugInspector", "LearningInspector", "SharingInspector"]
