# Copyright (c) Microsoft. All rights reserved.

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


def get_markdown_representation(doc):
    """
    Get the markdown representation of the document.
    Supports Headings, plaintext, and bulleted/numbered lists.
    """
    markdown_text = []

    for i in range(1, doc.Paragraphs.Count + 1):
        paragraph = doc.Paragraphs(i)
        style_name = paragraph.Style.NameLocal
        text = paragraph.Range.Text.strip()

        if not text:
            continue

        prefix = ""
        if "Heading" in style_name:
            try:
                level = int(style_name.split("Heading")[1].strip())
                prefix = "#" * level + " "
            except (ValueError, IndexError):
                pass
            markdown_text.append(f"{prefix}{text}")
        # Handle bulleted lists
        elif paragraph.Range.ListFormat.ListType == 2:
            markdown_text.append(f"- {text}")
        # Handle numbered lists
        elif paragraph.Range.ListFormat.ListType == 3:
            markdown_text.append(f"1. {text}")
        else:
            markdown_text.append(text)

    # Join all lines with newlines
    return "\n".join(markdown_text)


def write_markdown_to_document(doc, markdown_text):
    """
    Write the markdown text to the document.
    Supports headings, plaintext, and bulleted/numbered lists.
    """
    # Clear the document content and formatting
    doc.Content.Delete()

    word_app = doc.Application
    selection = word_app.Selection

    # Ensure we start with normal style
    selection.Style = word_app.ActiveDocument.Styles("Normal")

    lines = markdown_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if the line is a heading
        if line.startswith("#"):
            heading_level = 0
            for char in line:
                if char == "#":
                    heading_level += 1
                else:
                    break

            # Remove the # characters and any leading space
            text = line[heading_level:].strip()

            # Insert the text at the end of the document
            selection.TypeText(text)

            # Get the current paragraph and set its style
            current_paragraph = selection.Paragraphs.Last
            if 1 <= heading_level <= 9:  # Word supports Heading 1-9
                current_paragraph.Style = f"Heading {heading_level}"

            # Add a new line for the next paragraph
            selection.TypeParagraph()

        # Check if line is a bulleted list item
        elif line.startswith(("- ", "* ")):
            # Extract the text after the bullet marker
            text = line[2:].strip()

            # Type the text
            selection.TypeText(text)

            # Apply bullet formatting
            selection.Range.ListFormat.ApplyBulletDefault()

            # Add a new line
            selection.TypeParagraph()

            # Reset formatting to normal to prevent carrying over to next paragraph
            selection.Style = word_app.ActiveDocument.Styles("Normal")

        # Check if line is a numbered list item
        elif line.strip().startswith(tuple(f"{i}. " for i in range(1, 100)) + tuple(f"{i})" for i in range(1, 100))):
            # Extract the text after the number and period/parenthesis
            text = ""
            if ". " in line:
                parts = line.strip().split(". ", 1)
                if len(parts) > 1:
                    text = parts[1]
            elif ") " in line:
                parts = line.strip().split(") ", 1)
                if len(parts) > 1:
                    text = parts[1]

            if text:
                selection.TypeText(text)

                # Apply numbered list formatting
                selection.Range.ListFormat.ApplyNumberDefault()

                # Add a new line
                selection.TypeParagraph()

                # Reset formatting to normal to prevent carrying over to next paragraph
                selection.Style = word_app.ActiveDocument.Styles("Normal")
            else:
                # If parsing failed, just add the line as normal text
                selection.TypeText(line)
                selection.TypeParagraph()

        else:
            # Regular paragraph text
            selection.TypeText(line)
            selection.TypeParagraph()

    # Move cursor to the beginning of the document
    doc.Range(0, 0).Select()
