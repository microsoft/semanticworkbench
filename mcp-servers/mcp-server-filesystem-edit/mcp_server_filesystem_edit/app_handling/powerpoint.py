import re


def get_markdown_representation(document) -> str:
    """
    Return the content of the PowerPoint presentation formatted as a combination of XML and markdown.
    """
    markdown_text = []

    # Get layout mappings (reverse of the write_markdown layout dictionary)
    layout_types = {
        1: "title",  # Title Slide
        2: "title_and_content",  # Title and Content
        3: "two_content",  # Section Header
        33: "section_header",  # Section Header
    }

    # Process each slide
    for slide_index in range(1, document.Slides.Count + 1):
        slide = document.Slides(slide_index)

        # Get layout type - slide.Layout is already an integer
        layout_type = slide.Layout
        layout_name = layout_types.get(layout_type, "title_and_content")  # Default if not recognized

        # Start slide tag
        markdown_text.append(f'<slide num=<{slide_index}> layout="{layout_name}">')

        # Extract title if slide has one
        if slide.Shapes.HasTitle:
            title_text = slide.Shapes.Title.TextFrame.TextRange.Text
            markdown_text.append(f"<title>{title_text}</title>")
        else:
            markdown_text.append("<title></title>")

        # Process content based on layout type
        if layout_name == "title":
            # Title slides typically have a subtitle as the second shape
            if slide.Shapes.Count >= 2:
                subtitle_shape = slide.Shapes(2)  # PowerPoint indexing is 1-based
                if hasattr(subtitle_shape, "TextFrame"):
                    subtitle_text = subtitle_shape.TextFrame.TextRange.Text
                    markdown_text.append(f"<content>{subtitle_text}</content>")
                else:
                    markdown_text.append("<content></content>")
            else:
                markdown_text.append("<content></content>")

        elif layout_name == "section_header":
            # Section headers typically have description text as the second shape
            if slide.Shapes.Count >= 2:
                description_shape = slide.Shapes(2)
                if hasattr(description_shape, "TextFrame"):
                    description_text = description_shape.TextFrame.TextRange.Text
                    markdown_text.append(f"<content>{description_text}</content>")
                else:
                    markdown_text.append("<content></content>")
            else:
                markdown_text.append("<content></content>")

        elif layout_name == "title_and_content":
            # Title and content slides have content in the second shape
            if slide.Shapes.Count >= 2:
                content_shape = slide.Shapes(2)
                if hasattr(content_shape, "TextFrame"):
                    content_text = extract_formatted_content(content_shape.TextFrame)
                    markdown_text.append(f"<content>\n{content_text}\n</content>")
                else:
                    markdown_text.append("<content></content>")
            else:
                markdown_text.append("<content></content>")

        elif layout_name == "two_content":
            # Two content slides have content in second and third shapes
            # First content
            if slide.Shapes.Count >= 2:
                left_content_shape = slide.Shapes(2)
                if hasattr(left_content_shape, "TextFrame"):
                    left_content_text = extract_formatted_content(left_content_shape.TextFrame)
                    markdown_text.append(f"<content>\n{left_content_text}\n</content>")
                else:
                    markdown_text.append("<content></content>")
            else:
                markdown_text.append("<content></content>")

            # Second content
            if slide.Shapes.Count >= 3:
                right_content_shape = slide.Shapes(3)
                if hasattr(right_content_shape, "TextFrame"):
                    right_content_text = extract_formatted_content(right_content_shape.TextFrame)
                    markdown_text.append(f"<content>\n{right_content_text}\n</content>")
                else:
                    markdown_text.append("<content></content>")
            else:
                markdown_text.append("<content></content>")

        # Close slide tag
        markdown_text.append("</slide>\n")

    return "\n".join(markdown_text)


def extract_formatted_content(text_frame) -> str:
    markdown_lines = []
    for para_index in range(1, text_frame.TextRange.Paragraphs().Count + 1):
        para = text_frame.TextRange.Paragraphs(para_index)

        # Skip empty paragraphs
        if not para.Text.strip():
            markdown_lines.append("")
            continue

        # Check if paragraph is a heading based on font size
        font_size = para.Font.Size
        is_bold = para.Font.Bold
        line = ""

        # Handle bulleted lists
        if para.ParagraphFormat.Bullet.Type == 1:  # Bullet
            line = "- "
        # Handle numbered lists
        elif para.ParagraphFormat.Bullet.Type == 2:  # Numbered
            line = "1. "  # We'll use 1. for all items since PowerPoint maintains the actual numbering

        # Handle headers (larger font with bold)
        elif font_size >= 20 and is_bold:
            # Inverse of font size calculation in add_formatted_content
            heading_level = int((30 - font_size) // 2)
            line = "#" * heading_level + " "

        # Process text with formatting
        line += extract_text_with_formatting(para)
        markdown_lines.append(line)

    return "\n".join(markdown_lines)


def extract_text_with_formatting(text_range) -> str:
    # For simple cases where there's no mixed formatting
    if text_range.Characters().Count <= 1:
        return text_range.Text

    # For performance, first check if there's any formatting at all
    has_formatting = False
    for i in range(1, text_range.Characters().Count + 1):
        char = text_range.Characters(i)
        if char.Font.Bold or char.Font.Italic:
            has_formatting = True
            break

    # If no formatting, return the plain text
    if not has_formatting:
        return text_range.Text

    formatted_text = []
    current_run = {"text": "", "bold": False, "italic": False}
    for i in range(1, text_range.Characters().Count + 1):
        char = text_range.Characters(i)
        char_text = char.Text

        # Skip null characters or carriage returns
        if not char_text or ord(char_text) == 13:
            continue

        is_bold = char.Font.Bold
        is_italic = char.Font.Italic
        # If formatting changed, start a new run
        if is_bold != current_run["bold"] or is_italic != current_run["italic"]:
            # Finish the previous run if it exists
            if current_run["text"]:
                if current_run["bold"] and current_run["italic"]:
                    formatted_text.append(f"***{current_run['text']}***")
                elif current_run["bold"]:
                    formatted_text.append(f"**{current_run['text']}**")
                elif current_run["italic"]:
                    formatted_text.append(f"*{current_run['text']}*")
                else:
                    formatted_text.append(current_run["text"])

            current_run = {"text": char_text, "bold": is_bold, "italic": is_italic}
        else:
            current_run["text"] += char_text

    # Process the final run
    if current_run["text"]:
        if current_run["bold"] and current_run["italic"]:
            formatted_text.append(f"***{current_run['text']}***")
        elif current_run["bold"]:
            formatted_text.append(f"**{current_run['text']}**")
        elif current_run["italic"]:
            formatted_text.append(f"*{current_run['text']}*")
        else:
            formatted_text.append(current_run["text"])

    return "".join(formatted_text)


def write_markdown(document, markdown_text: str) -> None:
    """
    Converts markdown text to PowerPoint slides with themes.
    Uses a structured format with <slide> tags to define slides.

    Format:
    <slide num=<1> layout=<"title"|"section header"|"two content"|"title and content">
    <title>Title text</title>
    <content>Markdown content</content>
    <content>Second Markdown content - use only if two content is chosen </content>
    </slide>
    <slide num=<2> layout=<"title"|"section header"|"two content"|"title and content">
    ...
    </slide>
    ...

    Other syntax and settings:
    - Heading has no Markdown formatting applied
    - Content is treated as Markdown, with paragraphs, H2, H3, bold, italics, numbered lists, and bullet points supported.
    - Second content is only used if layout is "two content" and ignored otherwise.
    """
    # Clear all slides and sections
    try:
        document.Slides.Range().Delete()
        if document.SectionProperties.Count > 0:
            for i in range(document.SectionProperties.Count, 0, -1):
                document.SectionProperties.Delete(i, True)
    except Exception as e:
        print(f"Error deleting slides: {e}")

    # Create mappings to PowerPoint slide layouts types
    layouts = {
        "title": 1,  # Title Slide
        "title_and_content": 2,  # Title and Content
        "two_content": 3,  # Two Content
        "section_header": 33,  # Section Header
    }

    slide_pattern = re.compile(r'<slide\s+num=<\d+>\s+layout="([^"]+)">(.*?)</slide>', re.DOTALL)
    title_pattern = re.compile(r"<title>(.*?)</title>", re.DOTALL)
    content_pattern = re.compile(r"<content>(.*?)</content>", re.DOTALL)

    slides = slide_pattern.findall(markdown_text)
    for layout_name, slide_content in slides:
        layout_name_typed = layout_name.lower()
        # Use default layout if not recognized
        if layout_name_typed not in layouts:
            layout_name_typed = "title_and_content"

        # Extract title and content
        title_match = title_pattern.search(slide_content)
        title_text = title_match.group(1).strip() if title_match else ""

        # Extract content sections
        content_matches = content_pattern.findall(slide_content)
        content_text = content_matches[0].strip() if content_matches else ""
        second_content_text = content_matches[1].strip() if len(content_matches) > 1 else ""

        # Create a new slide with the specified layout
        slide_layout_index = layouts[layout_name_typed]
        slide = document.Slides.Add(document.Slides.Count + 1, slide_layout_index)

        # Add title if it exists
        if title_text and slide.Shapes.HasTitle:
            slide.Shapes.Title.TextFrame.TextRange.Text = title_text

        # Process content based on layout type
        if layout_name_typed == "title":
            if content_text and slide.Shapes.Count >= 2:
                subtitle_shape = slide.Shapes[1]
                if hasattr(subtitle_shape, "TextFrame"):
                    add_formatted_content(subtitle_shape.TextFrame, content_text)

        elif layout_name_typed == "section_header":
            if content_text and slide.Shapes.Count >= 2:
                description_shape = slide.Shapes[1]
                if hasattr(description_shape, "TextFrame"):
                    add_formatted_content(description_shape.TextFrame, content_text)

        elif layout_name_typed == "title_and_content":
            if content_text and slide.Shapes.Count >= 2:
                content_shape = slide.Shapes[1]
                if hasattr(content_shape, "TextFrame"):
                    add_formatted_content(content_shape.TextFrame, content_text)

        elif layout_name_typed == "two_content":
            if content_text and slide.Shapes.Count >= 2:
                left_content_shape = slide.Shapes[1]
                if hasattr(left_content_shape, "TextFrame"):
                    add_formatted_content(left_content_shape.TextFrame, content_text)

            if second_content_text and slide.Shapes.Count >= 3:
                right_content_shape = slide.Shapes[2]
                if hasattr(right_content_shape, "TextFrame"):
                    add_formatted_content(right_content_shape.TextFrame, second_content_text)


def add_formatted_content(text_frame, content: str) -> None:
    """
    Adds formatted content to a PowerPoint text frame.
    Supports Markdown formatting including headers, lists, bold, and italic.

    Args:
        text_frame: PowerPoint TextFrame object
        content: Markdown-formatted text to add
    """
    # Clear existing text
    text_frame.TextRange.Text = ""
    text_range = text_frame.TextRange
    text_range.ParagraphFormat.Bullet.Type = 0

    # Split content into paragraphs
    paragraphs = content.split("\n")

    # Track if we're in a list and what type
    in_bulleted_list = False
    in_numbered_list = False
    for i, paragraph in enumerate(paragraphs):
        # Skip empty paragraphs and clear formatting
        if not paragraph.strip():
            if i < len(paragraphs) - 1:
                text_range.InsertAfter("\r")
            continue

        # Insert paragraph break for non-first paragraphs
        if i > 0:
            # Use newline for paragraph break in PowerPoint
            text_range.InsertAfter("\r")

            # Access the end of what was just inserted
            text_length = len(text_frame.TextRange.Text)
            text_range = text_frame.TextRange.Characters(text_length + 1)

        # Check for headers (## Header)
        if paragraph.strip().startswith("#"):
            # Clear any previous formatting for headers
            text_range.ParagraphFormat.Bullet.Type = 0
            in_bulleted_list = False
            in_numbered_list = False

            # Calculate header level
            header_level = 0
            for char in paragraph:
                if char == "#":
                    header_level += 1
                else:
                    break

            header_text = paragraph[header_level:].strip()

            # Set header formatting before inserting text
            text_range.Font.Bold = True
            text_range.Font.Size = 30 - (header_level * 2) if header_level > 1 else 30

            format_and_insert_text(text_range, header_text)
            continue

        # Check for bullet points
        if paragraph.strip().startswith(("- ", "* ")):
            # Extract content after bullet
            bullet_text = paragraph.strip()[2:].strip()

            # Apply bullet formatting to the paragraph
            text_range.ParagraphFormat.Bullet.Type = 1

            # Reset text formatting for bullet content
            text_range.Font.Size = 18
            text_range.Font.Bold = False
            text_range.Font.Italic = False

            in_bulleted_list = True
            in_numbered_list = False

            format_and_insert_text(text_range, bullet_text)
            continue

        # Check for numbered lists
        numbered_match = re.match(r"^\s*(\d+)[\.\)]\s+(.*)", paragraph.strip())
        if numbered_match:
            # Extract content after number
            number_text = numbered_match.group(2).strip()

            # Apply numbered list formatting to the paragraph
            text_range.ParagraphFormat.Bullet.Type = 2

            # Reset text formatting for numbered content
            text_range.Font.Size = 18
            text_range.Font.Bold = False
            text_range.Font.Italic = False

            in_numbered_list = True
            in_bulleted_list = False

            format_and_insert_text(text_range, number_text)
            continue

        # For regular paragraphs (not headers or list items)
        if in_bulleted_list or in_numbered_list:
            text_range.ParagraphFormat.Bullet.Type = 0
            in_bulleted_list = False
            in_numbered_list = False

        text_range.Font.Size = 18
        text_range.Font.Bold = False
        text_range.Font.Italic = False

        format_and_insert_text(text_range, paragraph)


def format_and_insert_text(text_range, text: str) -> None:
    """
    Formats and inserts text with markdown-style formatting.
    Supports bold, italic, and bold+italic.
    """
    # First parse the text into formatted segments
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
        next_marker = len(text)
        for marker in ["***", "**", "*"]:
            pos = text.find(marker, i)
            if pos != -1 and pos < next_marker:
                next_marker = pos

        # Add plain text segment
        if next_marker == len(text):
            segments.append(("plain", text[i:]))
            break
        else:
            segments.append(("plain", text[i:next_marker]))
            i = next_marker

    # If no formatting needed, just insert the whole text
    if all(segment[0] == "plain" for segment in segments):
        text_range.InsertAfter("".join(segment[1] for segment in segments))
        return

    # Insert all text first as plain text
    full_text = "".join(segment[1] for segment in segments)
    start_pos = len(text_range.Text)
    text_range.InsertAfter(full_text)

    # Now apply formatting to specific parts
    current_pos = start_pos
    for format_type, content in segments:
        if not content or format_type == "plain":
            current_pos += len(content)
            continue

        # Select the range to format
        format_range = text_range.Characters(
            current_pos + 1,  # Start (1-indexed)
            len(content),  # Length
        )

        # Apply formatting
        if format_type in ("bold", "bold_italic"):
            format_range.Font.Bold = True

        if format_type in ("italic", "bold_italic"):
            format_range.Font.Italic = True

        current_pos += len(content)

    # Reset the text_range to point to the end for future insertions
    text_length = len(text_range.Text)
    text_range = text_range.Characters(text_length)
