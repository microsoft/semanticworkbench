import sys
from enum import Enum, auto
from pathlib import Path


class OfficeAppType(Enum):
    """Enum representing Microsoft Office application types."""

    WORD = auto()
    EXCEL = auto()
    POWERPOINT = auto()


def open_document_in_office(file_path: Path, app_type: OfficeAppType):
    """
    Opens a document at the specified path in Word, Excel, or PowerPoint.
    Creates and saves the document if it doesn't exist.

    Args:
        file_path: Path to the document
        app_type: The type of Office application to use

    Returns:
        A tuple containing (app_instance, document_instance)

    Raises:
        EnvironmentError: If not running on Windows
        ValueError: If an invalid app_type is provided
    """
    if sys.platform != "win32":
        raise EnvironmentError("This function only works on Windows.")

    import win32com.client as win32

    # Map app types to their COM identifiers and document properties
    app_config = {
        OfficeAppType.WORD: {"app_name": "Word.Application", "collection_name": "Documents", "file_ext": ".docx"},
        OfficeAppType.EXCEL: {"app_name": "Excel.Application", "collection_name": "Workbooks", "file_ext": ".xlsx"},
        OfficeAppType.POWERPOINT: {
            "app_name": "PowerPoint.Application",
            "collection_name": "Presentations",
            "file_ext": ".pptx",
        },
    }

    if app_type not in app_config:
        raise ValueError(f"Unsupported app type: {app_type}")

    config = app_config[app_type]
    app_name = config["app_name"]
    collection_name = config["collection_name"]

    # Ensure path is a Path object and resolve to absolute path
    doc_path = file_path.resolve()

    # Add default extension if no extension is present
    if not doc_path.suffix:
        doc_path = doc_path.with_suffix(config["file_ext"])

    # Create parent directories if they don't exist
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    # First try to get an existing app instance
    try:
        app = win32.GetActiveObject(app_name)
        # Check if the document is already open in this instance
        collection = getattr(app, collection_name)

        # Handle different collection indexing methods for different Office apps
        if app_type == OfficeAppType.WORD or app_type == OfficeAppType.EXCEL:
            for i in range(1, collection.Count + 1):
                open_doc = collection(i)
                if open_doc.FullName.lower() == str(doc_path).lower():
                    # Document is already open, just return it and its parent app
                    return app, open_doc
        elif app_type == OfficeAppType.POWERPOINT:
            # PowerPoint uses a different approach for accessing presentations
            for open_doc in collection:
                if hasattr(open_doc, "FullName") and open_doc.FullName.lower() == str(doc_path).lower():
                    return app, open_doc
    except Exception:
        # No running app instance found, create a new one
        app = win32.Dispatch(app_name)

    # Make app visible
    app.Visible = True

    # If the file exists, open it, otherwise create a new document and save it
    collection = getattr(app, collection_name)

    if doc_path.exists():
        doc = collection.Open(str(doc_path))
    else:
        doc = collection.Add()
        doc.SaveAs(str(doc_path))

    return app, doc
