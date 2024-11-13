from textwrap import dedent

from openai_client.messages import format_with_liquid


def test_formatted_messages() -> None:
    # Set instructions.
    instructions = [
        dedent("""
        Generate an outline for the document, including title. The outline should include the key points that will be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the conversation that has taken place. The outline should be a hierarchical structure with multiple levels of detail, and it should be clear and easy to understand. The outline should be generated in a way that is consistent with the document that will be generated from it.
        """).strip(),
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

    actual = [
        format_with_liquid(
            template=instruction,
            vars={
                "attachments": attachments,
                "outline_versions": outline_versions,
                "user_feedback": user_feedback,
                "chat_history": chat_history,
            },
        )
        for instruction in instructions
    ]

    expected = [
        "Generate an outline for the document, including title. The outline should include the key points that will be covered in the document. Consider the attachments, the rationale for why they were uploaded, and the conversation that has taken place. The outline should be a hierarchical structure with multiple levels of detail, and it should be clear and easy to understand. The outline should be generated in a way that is consistent with the document that will be generated from it.",
        "<CHAT_HISTORY>history</CHAT_HISTORY>",
        "<ATTACHMENTS><ATTACHMENT><FILENAME>filename1</FILENAME><CONTENT>content1</CONTENT></ATTACHMENT><ATTACHMENT><FILENAME>filename2</FILENAME><CONTENT>content2</CONTENT></ATTACHMENT></ATTACHMENTS>",
        "<EXISTING_OUTLINE>outline2</EXISTING_OUTLINE>",
        "<USER_FEEDBACK>feedback</USER_FEEDBACK>",
    ]

    assert actual == expected
