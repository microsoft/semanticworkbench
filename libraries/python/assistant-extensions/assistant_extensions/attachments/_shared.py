from assistant_drive import Drive, DriveConfig
from semantic_workbench_assistant.assistant_app import (
    ConversationContext,
    storage_directory_for_context,
)


def attachment_drive_for_context(context: ConversationContext) -> Drive:
    """
    Get the Drive instance for the attachments.
    """
    drive_root = storage_directory_for_context(context) / "attachments"
    return Drive(DriveConfig(root=drive_root))


def summary_drive_for_context(context: ConversationContext) -> Drive:
    """
    Get the path to the summary drive for the attachments.
    """
    return attachment_drive_for_context(context).subdrive("summaries")


def original_to_attachment_filename(filename: str) -> str:
    return filename + ".json"


def attachment_to_original_filename(filename: str) -> str:
    return filename.removesuffix(".json")
