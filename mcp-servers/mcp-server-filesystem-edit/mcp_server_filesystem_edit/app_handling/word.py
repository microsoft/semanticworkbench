import re

from mcp_server_filesystem_edit import settings


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

    # Add comments as a line before the ones they are associated with
    comments = get_document_comments(document)
    for comment_text, location_text in comments:
        # Find the first occurrence of the location text
        for i, line in enumerate(markdown_text):
            if location_text in line:
                # Insert the comment before the line
                markdown_text.insert(i, f"<!-- {comment_text} -->")
                break

    markdown_text = "\n".join(markdown_text)
    return markdown_text


def get_document_comments(doc) -> list[tuple[str, str]]:
    """
    Retrieve all comments from a Word document.
    """
    comments: list[tuple[str, str]] = []

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
                    continue

                reference_text = ""
                try:
                    if hasattr(comment, "Scope"):
                        reference_text = comment.Scope.Text
                except Exception:
                    continue

                comment_info = (comment_text, reference_text)
                comments.append(comment_info)
            except Exception:
                continue

        return comments
    except Exception as e:
        print(f"Error retrieving comments: {e}")
        return comments


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
    markdown_with_comments = markdown_text
    # Strip comments from markdown text
    markdown_text = strip_comments_from_markdown(markdown_with_comments)

    # Strip horizontal rules
    hr_pattern = re.compile(r"(\n|^)\s*([-*_][ \t]*){3,}\s*(\n|$)", re.MULTILINE)
    markdown_text = hr_pattern.sub(r"\1\3", markdown_text)

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

    # Handle inserting comments
    comments = _get_comments_from_markdown(markdown_with_comments)
    for comment_text, location_text in comments:
        add_document_comment(document, comment_text, location_text, settings.comment_author)

    # Move cursor to the beginning of the document
    document.Range(0, 0).Select()


def _get_comments_from_markdown(markdown_text: str) -> list[tuple[str, str]]:
    """
    Extracts comments from markdown text and returns them with location context.

    Returns a list of tuples containing (comment_text, location_text), where
    location_text is up to 30 plaintext characters following the comment,
    with markdown syntax elements removed.

    Only supports comments in "<!-- comment_text -->" format.
    """
    comments = []
    comment_pattern = re.compile(r"<!--(.*?)-->", re.DOTALL)

    # First, collect all comment positions to be able to skip over them
    comment_positions = [(match.start(), match.end()) for match in comment_pattern.finditer(markdown_text)]
    for match in comment_pattern.finditer(markdown_text):
        comment_text = match.group(1).strip()
        end_position = match.end()

        location_text = ""
        pos = end_position
        char_count = 0

        # Skip any immediate whitespace including newlines
        while pos < len(markdown_text) and markdown_text[pos].isspace():
            pos += 1

        while pos < len(markdown_text) and char_count < 30:
            # Only stop at newline if we've collected some text AND it's not just blank space
            if markdown_text[pos] == "\n" and char_count > 0 and location_text.strip():
                break

            # Check for comment boundaries at current or next position
            inside_comment = False
            check_positions = [pos]
            # If we're in whitespace, also check where the whitespace ends
            if markdown_text[pos].isspace():
                next_pos = pos
                while next_pos < len(markdown_text) and markdown_text[next_pos].isspace():
                    next_pos += 1
                check_positions.append(next_pos)

            # Check both current position and potential next position after whitespace
            for check_pos in check_positions:
                for start_pos, end_pos in comment_positions:
                    in_comment_range = (check_pos >= start_pos and check_pos < end_pos) or check_pos == start_pos
                    if in_comment_range:
                        pos = end_pos
                        inside_comment = True
                        break
                if inside_comment:
                    break
            if inside_comment:
                continue

            # Skip list markers (bullet points)
            if pos + 1 < len(markdown_text) and markdown_text[pos : pos + 2] in ("- ", "* "):
                pos += 2
                continue

            # Skip numbered list markers (e.g., "1. ", "42) ")
            if pos + 1 < len(markdown_text):
                list_match = re.match(r"(\d+)(\.|\))\s", markdown_text[pos : pos + 10])
                if list_match:
                    pos += len(list_match.group(0))
                    continue

            # Skip other markdown syntax elements
            if pos + 2 < len(markdown_text) and markdown_text[pos : pos + 3] == "***":
                pos += 3
            elif pos + 1 < len(markdown_text) and markdown_text[pos : pos + 2] == "**":
                pos += 2
            elif markdown_text[pos] == "*" and (pos + 1 >= len(markdown_text) or markdown_text[pos + 1] != "*"):
                pos += 1
            elif pos + 3 < len(markdown_text) and markdown_text[pos : pos + 4] == "```\n":
                pos += 4
            elif pos + 2 < len(markdown_text) and markdown_text[pos : pos + 3] == "```":
                pos += 3
            # Skip heading markers
            elif pos < len(markdown_text) and markdown_text[pos] == "#":
                # Skip all consecutive # characters and the following space
                while pos < len(markdown_text) and markdown_text[pos] == "#":
                    pos += 1
                # Skip space after heading markers
                if pos < len(markdown_text) and markdown_text[pos] == " ":
                    pos += 1
                continue
            else:
                # Regular text character
                location_text += markdown_text[pos]
                char_count += 1
                pos += 1

        location_text = location_text.strip()
        comments.append((comment_text, location_text))
    return comments


def strip_comments_from_markdown(markdown_text: str) -> str:
    """
    Strips comments from the given markdown text and returns the cleaned text.
    Comments are represented as "<!-- comment_text -->".

    For example, there might be inline comments like "Target <!-- comment text--> Audience"
    which will result in "Target Audience" (notice how an extra space between words is not added).

    There can also be comments that are on their own line:
    "Here are the market opportunities:
    <!-- This is a comment -->
    Ok let's get into the details"
    In this case, after removal the text will be:
    "Here are the market opportunities:
    Ok let's get into the details"
    """
    # Remove comments that are on their own line.
    standalone_pattern = re.compile(r"\n\s*<!--.*?-->\s*\n", re.DOTALL)
    cleaned_text = standalone_pattern.sub("\n", markdown_text)

    # Remove inline comments between non-space characters.
    inline_between_pattern = re.compile(r"(?<=\S)(\s*)<!--.*?-->(\s*)(?=\S)", re.DOTALL)
    cleaned_text = inline_between_pattern.sub(
        lambda m: " " if m.group(1) == " " and m.group(2) == " " else m.group(1) + m.group(2),
        cleaned_text,
    )

    # Remove any remaining inline comments.
    inline_pattern = re.compile(r"<!--.*?-->", re.DOTALL)
    cleaned_text = inline_pattern.sub("", cleaned_text)
    return cleaned_text


def add_document_comment(
    doc,
    comment_text: str,
    location_text: str,
    author: str,
) -> bool:
    """
    Add a comment to specific text within a Word document.
    Inserts the comment at the first occurrence of the location text.

    Returns:
        bool: True if comment was added successfully, False otherwise
    """
    try:
        content_range = doc.Content

        # Find the first occurrence of the text
        content_range.Find.ClearFormatting()
        found = content_range.Find.Execute(FindText=location_text, MatchCase=True, MatchWholeWord=False)

        if not found:
            return False

        # Add a comment to the found range
        comment = doc.Comments.Add(Range=content_range.Duplicate, Text=comment_text)
        comment.Author = author
        return True
    except Exception:
        return False
