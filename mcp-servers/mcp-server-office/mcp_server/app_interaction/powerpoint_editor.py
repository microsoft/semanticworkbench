# Copyright (c) Microsoft. All rights reserved.

import pythoncom
import win32com.client as win32


def get_powerpoint_app():
    """Connect to PowerPoint if it is running, or start a new instance."""
    try:
        # Try connecting to an existing instance of PowerPoint
        powerpoint = win32.GetActiveObject("PowerPoint.Application")
    except Exception:
        # If not running, create a new instance
        powerpoint = win32.Dispatch("PowerPoint.Application")
    # Make PowerPoint visible
    powerpoint.Visible = True
    return powerpoint


def get_active_presentation(powerpoint):
    """Return an active PowerPoint presentation, or create one if none is open."""
    if powerpoint.Presentations.Count == 0:
        # If there are no presentations, add a new one
        return powerpoint.Presentations.Add()
    else:
        return powerpoint.ActivePresentation


def get_slide_content(presentation, slide_number):
    """Return the text content of a slide."""
    content = []
    slide = presentation.Slides(slide_number)
    for shape in slide.Shapes:
        if shape.HasTextFrame:
            if shape.TextFrame.HasText:
                content.append(shape.TextFrame.TextRange.Text)
    return "\n".join(content)


def get_presentation_content(presentation):
    """Return the content of all slides in the presentation."""
    content = []
    for i in range(1, presentation.Slides.Count + 1):
        slide_content = get_slide_content(presentation, i)
        content.append(f"Slide {i}:\n{slide_content}")
    return "\n\n".join(content)


def add_text_to_slide(presentation, slide_number, text):
    """Add text to a new textbox on the slide."""
    slide = presentation.Slides(slide_number)
    # Add a larger text box that takes up most of the slide
    text_box = slide.Shapes.AddTextbox(
        Orientation=1,  # msoTextOrientationHorizontal
        Left=50,  # Moved more left
        Top=50,  # Moved more up
        Width=800,  # Much wider
        Height=500,  # Much taller
    )
    text_range = text_box.TextFrame.TextRange
    text_range.Text = text
    text_range.Font.Size = 36  # Larger font size
    text_box.TextFrame.AutoSize = 1  # Auto-size text to fit in shape


def remove_slide(presentation, slide_number):
    """Remove a slide at the specified position.

    Args:
        presentation: The PowerPoint presentation object
        slide_number: The position of the slide to remove

    Returns:
        bool: True if successful, False if slide number is invalid
    """
    try:
        if slide_number <= 0 or slide_number > presentation.Slides.Count:
            return False

        presentation.Slides(slide_number).Delete()
        return True
    except Exception:
        return False


def main():
    # Initialize COM
    pythoncom.CoInitialize()

    # Connect to PowerPoint application and get the active presentation
    powerpoint = get_powerpoint_app()
    presentation = get_active_presentation(powerpoint)

    print("Connected to PowerPoint.")

    # Clear all slides from the presentation
    while presentation.Slides.Count >= 1:
        presentation.Slides(1).Delete()

    # Add two blank slides
    presentation.Slides.Add(1, 11)  # First slide, blank layout
    presentation.Slides.Add(2, 11)  # Second slide, blank layout
    print("Added two blank slides.")

    # Add some initial text to the slides
    add_text_to_slide(presentation, 1, "First Slide")
    add_text_to_slide(presentation, 2, "Second Slide")

    # 1. Read the content of the presentation
    content = get_presentation_content(presentation)
    print(content)

    # 2. Add a new slide with the content
    new_slide_number = presentation.Slides.Count + 1
    presentation.Slides.Add(
        new_slide_number,  # Add at the end
        11,  # Layout: blank slide
    )
    add_text_to_slide(presentation, new_slide_number, content)

    print("Added new slide with content.")


if __name__ == "__main__":
    main()
