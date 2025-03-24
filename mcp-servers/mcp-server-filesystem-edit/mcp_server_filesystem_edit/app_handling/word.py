import sys
from pathlib import Path


def open_document_in_word(file_path: Path) -> tuple[object, object]:
    """
    Opens a document at the specified path in Word, creating and saving it it doesn't exist
    """

    if sys.platform != "win32":
        raise EnvironmentError("This function only works on Windows.")

    import win32com.client as win32

    # Ensure path is a Path object and resolve to absolute path
    doc_path = file_path.resolve()

    # Create parent directories if they don't exist
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    # First try to get an existing Word instance
    try:
        word = win32.GetActiveObject("Word.Application")
        # Check if the document is already open in this instance
        for i in range(1, word.Documents.Count + 1):
            if word.Documents(i).FullName.lower() == str(doc_path).lower():
                # Document is already open, just return it and its parent app
                return word, word.Documents(i)
    except Exception:
        # No running Word instance found, create a new one
        word = win32.Dispatch("Word.Application")

    # Make Word visible
    word.Visible = True

    # If the file exists, open it, otherwise create a new document and save it
    if doc_path.exists():
        doc = word.Documents.Open(str(doc_path))
    else:
        doc = word.Documents.Add()
        # Save the new document with the specified path
        doc.SaveAs(str(doc_path))

    return word, doc


def get_markdown_representation(document) -> str:
    """
    Get the markdown representation of the document.
    Supports Headings, plaintext, bulleted/numbered lists, bold, italic, code blocks, and comments.
    """

    markdown_text = []
    in_code_block = False
    for i in range(1, document.Paragraphs.Count + 1):
        paragraph = document.Paragraphs(i)
        style_name = paragraph.Style.NameLocal

        # Handle Code style for code blocks
        if style_name == "Code":
            if not in_code_block:
                markdown_text.append("```")
                in_code_block = True
            markdown_text.append(paragraph.Range.Text.rstrip())
            continue
        elif in_code_block:
            # Close code block when style changes
            markdown_text.append("```")
            in_code_block = False

        # Process paragraph style first
        prefix = ""
        if "Heading" in style_name:
            try:
                level = int(style_name.split("Heading")[1].strip())
                prefix = "#" * level + " "
            except (ValueError, IndexError):
                pass

        para_text = ""
        para_range = paragraph.Range
        # For performance, check if there's any formatting at all
        if para_range.Text.strip():
            if para_range.Font.Bold or para_range.Font.Italic:
                # Process words instead of characters for better performance
                current_run = {"text": "", "bold": False, "italic": False}

                # Get all words in this paragraph
                for w in range(1, para_range.Words.Count + 1):
                    word_range = para_range.Words(w)
                    word_text = word_range.Text  # Keep original with potential spaces

                    # Skip if empty
                    if not word_text.strip():
                        continue

                    # Get formatting for this word
                    is_bold = word_range.Font.Bold
                    is_italic = word_range.Font.Italic

                    # If formatting changed, start a new run
                    if is_bold != current_run["bold"] or is_italic != current_run["italic"]:
                        # Finish the previous run if it exists
                        if current_run["text"]:
                            if current_run["bold"] and current_run["italic"]:
                                para_text += f"***{current_run['text'].rstrip()}***"
                            elif current_run["bold"]:
                                para_text += f"**{current_run['text'].rstrip()}**"
                            elif current_run["italic"]:
                                para_text += f"*{current_run['text'].rstrip()}*"
                            else:
                                para_text += current_run["text"].rstrip()

                            # Add a space if the previous run ended with a space
                            if current_run["text"].endswith(" "):
                                para_text += " "

                        # Start a new run with the current word
                        current_run = {"text": word_text, "bold": is_bold, "italic": is_italic}
                    else:
                        # Continue the current run - but be careful with spaces
                        if current_run["text"]:
                            current_run["text"] += word_text
                        else:
                            current_run["text"] = word_text

                # Process the final run
                if current_run["text"]:
                    if current_run["bold"] and current_run["italic"]:
                        para_text += f"***{current_run['text'].rstrip()}***"
                    elif current_run["bold"]:
                        para_text += f"**{current_run['text'].rstrip()}**"
                    elif current_run["italic"]:
                        para_text += f"*{current_run['text'].rstrip()}*"
                    else:
                        para_text += current_run["text"].rstrip()
            else:
                # No special formatting, just get the text
                para_text = para_range.Text.strip()
        else:
            para_text = para_range.Text.strip()

        if not para_text:
            continue

        # Handle list formatting
        if paragraph.Range.ListFormat.ListType == 2:
            markdown_text.append(f"- {para_text}")
        elif paragraph.Range.ListFormat.ListType == 3:
            markdown_text.append(f"1. {para_text}")
        else:
            markdown_text.append(f"{prefix}{para_text}")

    # Close any open code block at the end of document
    if in_code_block:
        markdown_text.append("```")

    return "\n".join(markdown_text)


def _write_formatted_text(selection, text):
    """
    Helper function to write text with markdown formatting (bold, italic) to the document.
    Processes text in chunks for better performance.

    Args:
        selection: Word selection object where text will be inserted
        text: Markdown-formatted text string to process
    """

    segments = []
    i = 0
    while i < len(text):
        # Bold+Italic (***text***)
        if i + 2 < len(text) and text[i : i + 3] == "***" and "***" in text[i + 3 :]:
            end_pos = text.find("***", i + 3)
            if end_pos != -1:
                segments.append(("bold_italic", text[i + 3 : end_pos]))
                i = end_pos + 3
                continue

        # Bold (**text**)
        elif i + 1 < len(text) and text[i : i + 2] == "**" and "**" in text[i + 2 :]:
            end_pos = text.find("**", i + 2)
            if end_pos != -1:
                segments.append(("bold", text[i + 2 : end_pos]))
                i = end_pos + 2
                continue

        # Italic (*text*)
        elif text[i] == "*" and i + 1 < len(text) and text[i + 1] != "*" and "*" in text[i + 1 :]:
            end_pos = text.find("*", i + 1)
            if end_pos != -1:
                segments.append(("italic", text[i + 1 : end_pos]))
                i = end_pos + 1
                continue

        # Find the next special marker or end of string
        next_marker = float("inf")
        for marker in ["***", "**", "*"]:
            pos = text.find(marker, i)
            if pos != -1 and pos < next_marker:
                next_marker = pos

        # Add plain text segment
        if next_marker == float("inf"):
            segments.append(("plain", text[i:]))
            break
        else:
            segments.append(("plain", text[i:next_marker]))
            i = next_marker

    # Now write all segments with minimal formatting changes
    current_format = None
    for format_type, content in segments:
        if format_type != current_format:
            selection.Font.Bold = False
            selection.Font.Italic = False

            if format_type == "bold" or format_type == "bold_italic":
                selection.Font.Bold = True
            if format_type == "italic" or format_type == "bold_italic":
                selection.Font.Italic = True

            current_format = format_type
        selection.TypeText(content)

    selection.Font.Bold = False
    selection.Font.Italic = False


def write_markdown(document, markdown_text: str) -> None:
    """Writes markdown text to a Word document with appropriate formatting.

    Converts markdown syntax to Word formatting, including:
    - Headings (# to Heading styles)
    - Lists (bulleted and numbered)
    - Text formatting (bold, italic)
    - Code blocks (``` to Code style)
    """
    document.Content.Delete()

    word_app = document.Application
    selection = word_app.Selection

    # Create "Code" style if it doesn't exist
    try:
        # Check if Code style exists
        code_style = word_app.ActiveDocument.Styles("Code")
    except Exception:
        # Create the Code style
        code_style = word_app.ActiveDocument.Styles.Add("Code", 1)
        code_style.Font.Name = "Cascadia Code"
        code_style.Font.Size = 10
        code_style.ParagraphFormat.SpaceAfter = 0
        code_style.QuickStyle = True
        code_style.LinkStyle = True

    # This fixes an issue where if there are comments on a doc, there is no selection
    # which causes insertion to fail
    document.Range(0, 0).Select()

    # Ensure we start with normal style
    selection.Style = word_app.ActiveDocument.Styles("Normal")

    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        if line.startswith("```"):
            i_start = i

            # Find the end of the code block
            while i < len(lines) and not lines[i].strip().startswith("```"):
                i += 1

            # Process all lines in the code block
            for j in range(i_start, i):
                code_line = lines[j]
                selection.TypeText(code_line)
                selection.Style = word_app.ActiveDocument.Styles("Code")
                selection.TypeParagraph()

            # Skip the closing code fence
            if i < len(lines):
                i += 1

            # Restore normal style for next paragraph
            selection.Style = word_app.ActiveDocument.Styles("Normal")
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

            _write_formatted_text(selection, text)

            # Get the current paragraph and set its style
            current_paragraph = selection.Paragraphs.Last
            if 1 <= heading_level <= 9:  # Word supports Heading 1-9
                current_paragraph.Style = f"Heading {heading_level}"

            selection.TypeParagraph()

        # Check if line is a bulleted list item
        elif line.startswith(("- ", "* ")):
            # Extract the text after the bullet marker
            text = line[2:].strip()

            _write_formatted_text(selection, text)

            # Apply bullet formatting
            selection.Range.ListFormat.ApplyBulletDefault()

            selection.TypeParagraph()
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
                _write_formatted_text(selection, text)

                # Apply numbered list formatting
                selection.Range.ListFormat.ApplyNumberDefault()
                selection.TypeParagraph()
                selection.Style = word_app.ActiveDocument.Styles("Normal")
            else:
                # If parsing failed, just add the line as normal text
                _write_formatted_text(selection, line)
                selection.TypeParagraph()

        else:
            # Regular paragraph text with formatting support
            _write_formatted_text(selection, line)
            selection.TypeParagraph()

    # Move cursor to the beginning of the document
    document.Range(0, 0).Select()
