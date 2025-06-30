"""
Provides the ArchiveTaskQueues class, for integrating with the chat context toolkit's archiving functionality.
"""

from ._archive import ArchiveTaskQueues, construct_archive_summarizer

__all__ = [
    "ArchiveTaskQueues",
    "construct_archive_summarizer",
]
