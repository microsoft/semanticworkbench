# Copyright (c) Microsoft. All rights reserved.

import pythoncom
import win32com.client as win32


def get_word_app():
    """Connect to Word if it is running, or start a new instance."""
    try:
        # Try connecting to an existing instance of Word
        word = win32.GetActiveObject("Word.Application")
    except Exception:
        # If not running, create a new instance
        word = win32.Dispatch("Word.Application")
    # Make sure Word is visible so you can see your edits
    word.Visible = True
    return word


def get_active_document(word):
    """Return an active Word document, or create one if none is open."""
    if word.Documents.Count == 0:
        # If there are no documents, add a new one
        return word.Documents.Add()
    else:
        return word.ActiveDocument


def get_document_content(doc):
    """Return the content of the document."""
    return doc.Content.Text


def replace_document_content(doc, content):
    """Replace the content of the document with the given content."""
    doc.Content.Text = content


def main():
    # Initialize COM (especially useful if you later run in a multi-threaded context)
    pythoncom.CoInitialize()

    # Connect to Word application and get the active document
    word = get_word_app()
    doc = get_active_document(word)

    print("Connected to Word.")

    # 1. Read the entire content of the document
    content = doc.Content.Text
    print(content)

    # 2. Insert new content (by reinserting it all for now)
    doubled_content = content + content
    doc.Content.Text = doubled_content

    # 3. Restore original content by again reinserting it all
    doc.Content.Text = content


if __name__ == "__main__":
    main()
