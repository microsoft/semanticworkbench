from typing import Any

from chat_driver.chat_driver import ChatDriver
from liquid import Template


def format_message(message: str, vars: dict[str, Any]) -> str:
    """
    Format a message with the given variables.
    """
    out = message
    if not message:
        return message
    template = Template(message)
    out = template.render(**vars)
    return out


def test_formatted_instructions() -> None:
    # Set instructions.
    instructions = [
        (
            "Generate an outline for the document, including title. The outline should include the key points that will"
            " be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the"
            " conversation that has taken place. The outline should be a hierarchical structure with multiple levels of"
            " detail, and it should be clear and easy to understand. The outline should be generated in a way that is"
            " consistent with the document that will be generated from it."
        ),
        "<CHAT_HISTORY>{{chat_history}}</CHAT_HISTORY>",
        "<ATTACHMENTS>{% for attachment in attachments %}<ATTACHMENT><FILENAME>{{attachment.filename}}</FILENAME><CONTENT>{{attachment.content}}</CONTENT></ATTACHMENT>{% endfor %}</ATTACHMENTS>",
        "<EXISTING_OUTLINE>{{outline_versions.last}}</EXISTING_OUTLINE>",
        "<USER_FEEDBACK>{{user_feedback}}</USER_FEEDBACK>",
    ]

    # Set vars.
    attachments = [
        {"filename": "filename1", "content": "content1"},
        {"filename": "filename2", "content": "content2"},
    ]
    outline_versions = ["outline1", "outline2"]
    user_feedback = "feedback"
    chat_history = "history"
    formatted_instructions = ChatDriver.format_instructions(
        instructions=instructions,
        vars={
            "attachments": attachments,
            "outline_versions": outline_versions,
            "user_feedback": user_feedback,
            "chat_history": chat_history,
        },
        formatter=format_message,
    )

    expected = [
        {
            "role": "system",
            "content": "Generate an outline for the document, including title. The outline should include the key points that will be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the conversation that has taken place. The outline should be a hierarchical structure with multiple levels of detail, and it should be clear and easy to understand. The outline should be generated in a way that is consistent with the document that will be generated from it.",
        },
        {"role": "system", "content": "<CHAT_HISTORY>history</CHAT_HISTORY>"},
        # {
        #     "role": "system",
        #     "content": "<ATTACHMENT><FILENAME>filename1</FILENAME><CONTENT>content1</CONTENT></ATTACHMENT>",
        # },
        # {
        #     "role": "system",
        #     "content": "<ATTACHMENT><FILENAME>filename2</FILENAME><CONTENT>content2</CONTENT></ATTACHMENT>",
        # },
        {
            "role": "system",
            "content": "<ATTACHMENTS><ATTACHMENT><FILENAME>filename1</FILENAME><CONTENT>content1</CONTENT></ATTACHMENT><ATTACHMENT><FILENAME>filename2</FILENAME><CONTENT>content2</CONTENT></ATTACHMENT></ATTACHMENTS>",
        },
        {"role": "system", "content": "<EXISTING_OUTLINE>outline2</EXISTING_OUTLINE>"},
        {"role": "system", "content": "<USER_FEEDBACK>feedback</USER_FEEDBACK>"},
    ]

    assert formatted_instructions == expected
