"""
Inspector modules for the Knowledge Transfer Assistant.

This package contains the tabbed inspector implementations that provide
different views of the knowledge transfer state in the workbench UI.
"""

from .brief import BriefInspector
from .learning import LearningInspector
from .sharing import SharingInspector
from .debug import DebugInspector

__all__ = ["BriefInspector", "LearningInspector", "SharingInspector", "DebugInspector"]
