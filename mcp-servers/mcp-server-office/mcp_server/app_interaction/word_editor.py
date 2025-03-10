# Copyright (c) Microsoft. All rights reserved.

import win32com.client as win32

from mcp_server.types import WordCommentData


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


def get_markdown_representation(doc, include_comments: bool = False) -> str:
    """
    Get the markdown representation of the document.
    Supports Headings, plaintext, bulleted/numbered lists, bold, italic, and code blocks.
    """
    markdown_text = []
    in_code_block = False
    for i in range(1, doc.Paragraphs.Count + 1):
        paragraph = doc.Paragraphs(i)
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

    if include_comments:
        comment_section = get_comments_markdown_representation(doc)
        if comment_section:
            markdown_text.append(comment_section)

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


def write_markdown_to_document(doc, markdown_text: str) -> None:
    """Writes markdown text to a Word document with appropriate formatting.

    Converts markdown syntax to Word formatting, including:
    - Headings (# to Heading styles)
    - Lists (bulleted and numbered)
    - Text formatting (bold, italic)
    - Code blocks (``` to Code style)
    """
    comments = get_document_comments(doc)

    doc.Content.Delete()

    word_app = doc.Application
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
    doc.Range(0, 0).Select()

    # Ensure we start with normal style
    selection.Style = word_app.ActiveDocument.Styles("Normal")

    lines = markdown_text.split("\n")
    i = 0
    in_code_block = False
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            selection.TypeParagraph()
            continue

        if line.startswith("```"):
            in_code_block = True
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
            in_code_block = False

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
    doc.Range(0, 0).Select()

    # Reapply comments. Note this implicitly will remove any comments that have locations not in the new text.
    for comment in comments:
        add_document_comment(doc, comment)


def add_document_comment(
    doc,
    comment_data: WordCommentData,
) -> bool:
    """
    Add a comment to specific text within a Word document.

    Returns:
        bool: True if comment was added successfully, False otherwise
    """
    try:
        content_range = doc.Content
        found_range = None

        # Find the specified occurrence of the text
        found_count = 0

        # Use FindText to locate the text
        content_range.Find.ClearFormatting()
        found = content_range.Find.Execute(FindText=comment_data.location_text, MatchCase=True, MatchWholeWord=False)

        while found:
            found_count += 1
            if found_count == comment_data.occurrence:
                found_range = content_range.Duplicate
                break

            # Continue searching from the end of the current match
            content_range.Collapse(Direction=0)  # Collapse to end
            found = content_range.Find.Execute(
                FindText=comment_data.location_text, MatchCase=True, MatchWholeWord=False
            )

        if not found_range:
            return False

        # Add a comment to the found range
        comment = doc.Comments.Add(Range=found_range, Text=comment_data.comment_text)
        if comment_data.author:
            comment.Author = comment_data.author
        return True
    except Exception:
        return False


def get_document_comments(doc) -> list[WordCommentData]:
    """
    Retrieve all comments from a Word document.
    """
    comments: list[WordCommentData] = []

    try:
        if doc.Comments.Count == 0:
            return comments

        for i in range(1, doc.Comments.Count + 1):
            try:
                comment = doc.Comments(i)

                comment_text = ""
                try:
                    comment_text = comment.Range.Text
                except Exception:
                    pass

                author = "Unknown"
                try:
                    author = comment.Author
                except Exception:
                    pass

                date = ""
                try:
                    date = str(comment.Date)
                except Exception:
                    pass

                reference_text = ""
                try:
                    if hasattr(comment, "Scope"):
                        reference_text = comment.Scope.Text
                except Exception:
                    pass

                comment_info = WordCommentData(
                    id=str(i),
                    comment_text=comment_text,
                    location_text=reference_text,
                    date=date,
                    author=author,
                )
                comments.append(comment_info)
            except Exception:
                continue

        return comments
    except Exception as e:
        print(f"Error retrieving comments: {e}")
        return comments


def get_comments_markdown_representation(doc) -> str:
    comments = get_document_comments(doc)

    if not comments:
        return ""

    comment_section = "\n\n<comments>\n"
    for i, comment in enumerate(comments, 1):
        comment_section += f'<comment id={i} author="{comment.author}">\n'
        comment_section += f"  <location_text>{comment.location_text}</location_text>\n"
        comment_section += f"  <comment_text>{comment.comment_text}</comment_text>\n"
        comment_section += "</comment>\n"
    comment_section.rstrip()
    comment_section += "</comments>"
    return comment_section


def delete_comments_containing_text(doc, search_text: str, case_sensitive: bool = False) -> int:
    """
    Delete comments containing specific text.

    Args:
        doc: Word document object
        search_text: Text to search for in comments
        case_sensitive: Whether the search should be case-sensitive

    Returns:
        int: Number of comments deleted
    """
    deleted_count = 0
    try:
        if not case_sensitive:
            search_text = search_text.lower()

        # Work backwards to avoid index shifting issues when deleting
        for i in range(doc.Comments.Count, 0, -1):
            comment = doc.Comments(i)
            comment_text = comment.Range.Text

            if not case_sensitive:
                comment_text = comment_text.lower()

            if search_text in comment_text:
                comment.Delete()
                deleted_count += 1
        return deleted_count
    except Exception:
        return deleted_count
