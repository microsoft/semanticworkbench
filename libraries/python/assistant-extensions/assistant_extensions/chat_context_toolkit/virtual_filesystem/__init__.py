"""
Provides mounts for file sources for integration with the virtual filesystem in chat context toolkit.
"""

from ._archive_file_source import archive_file_source_mount
from ._attachments_file_source import attachments_file_source_mount

__all__ = [
    "attachments_file_source_mount",
    "archive_file_source_mount",
]
