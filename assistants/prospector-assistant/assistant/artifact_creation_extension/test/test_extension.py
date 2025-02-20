import datetime
import json
import logging
import uuid
from textwrap import dedent
from unittest.mock import Mock, _CallList

import pytest
from assistant.artifact_creation_extension import store
from assistant.artifact_creation_extension.extension import LLMs, ToolCall, build_plan_for_turn
from assistant.artifact_creation_extension.test import evaluation
from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageSender,
    MessageType,
    NewConversationMessage,
    ParticipantRole,
)


async def test_create_simple_document(
    mock_conversation_context: Mock, llms: LLMs, document_store: store.DocumentStore
) -> None:
    from assistant.artifact_creation_extension.extension import respond_to_message

    conversation_history = [
        user_message(
            content="can you create a new software project plan document? and populate all sections as you see fit?"
        )
    ]

    await respond_to_message(llms=llms, conversation_history=conversation_history)

    assert mock_conversation_context.send_messages.call_count > 0

    calls: _CallList = mock_conversation_context.send_messages.call_args_list
    for call in calls:
        message = call.args[0]
        assert isinstance(message, NewConversationMessage)
        if message.message_type != MessageType.chat:
            continue

        logging.info("message type: %s, content: %s", message.message_type, message.content)

    headers = document_store.list_documents()
    assert len(headers) == 1

    document = document_store.read(headers[0].document_id)
    logging.info("document: %s", document.title)
    assert document.title == "Software Project Plan"

    assert len(document.sections) > 0
    for section in document.sections:
        logging.info("section: %s", section.title)


@pytest.mark.repeat(3)
async def test_create_us_constitution(
    mock_conversation_context: Mock, llms: LLMs, document_store: store.DocumentStore
) -> None:
    from assistant.artifact_creation_extension.extension import respond_to_message

    conversation_history = [
        user_message(
            content=dedent("""
            please create a new document for the United States Constitution.
            populate it with the preamble, all articles (I through VII), and all amendments (I through XXVII).
            the preamble, each article, and each amendment, should be in a separate section.
            ensure that all content matches that of the actual constitution.
            """).strip()
        )
    ]

    await respond_to_message(llms=llms, conversation_history=conversation_history)

    assert mock_conversation_context.send_messages.call_count > 0

    calls: _CallList = mock_conversation_context.send_messages.call_args_list
    assert len(calls) > 0

    for call in reversed(calls):
        message = call.args[0]
        assert isinstance(message, NewConversationMessage)

        if message.message_type != MessageType.chat:
            continue

        conversation_history.append(assistant_message(content=message.content))
        logging.info("message type: %s, content: %s", message.message_type, message.content)

    headers = document_store.list_documents()
    assert len(headers) == 1

    document = document_store.read(headers[0].document_id)
    logging.info("document: %s", document.title)
    assert "united states constitution" in document.title.lower()

    assert len(document.sections) > 0

    markdown_document = store.project_document_to_markdown(document)
    logging.info("markdown document:\n%s", markdown_document)

    preamble = document.sections[0]
    assert preamble.title == "Preamble"
    assert (
        evaluation.sentence_cosine_similarity(
            preamble.content,
            """
        We the People of the United States, in Order to form a more perfect Union, establish Justice, insure domestic Tranquility,
        provide for the common defence, promote the general Welfare, and secure the Blessings of Liberty to ourselves and our Posterity,
        do ordain and establish this Constitution for the United States of America.
    """,
        )
        > 0.99
    )

    titles = [section.title for section in document.sections]
    assert titles == [
        "Preamble",
        "Article I",
        "Article II",
        "Article III",
        "Article IV",
        "Article V",
        "Article VI",
        "Article VII",
        "Amendment I",
        "Amendment II",
        "Amendment III",
        "Amendment IV",
        "Amendment V",
        "Amendment VI",
        "Amendment VII",
        "Amendment VIII",
        "Amendment IX",
        "Amendment X",
        "Amendment XI",
        "Amendment XII",
        "Amendment XIII",
        "Amendment XIV",
        "Amendment XV",
        "Amendment XVI",
        "Amendment XVII",
        "Amendment XVIII",
        "Amendment XIX",
        "Amendment XX",
        "Amendment XXI",
        "Amendment XXII",
        "Amendment XXIII",
        "Amendment XXIV",
        "Amendment XXV",
        "Amendment XXVI",
        "Amendment XXVII",
    ]


@pytest.mark.repeat(10)
async def test_build_plan_for_us_constitution(llms: LLMs) -> None:
    conversation_history = [
        user_message(
            content=dedent("""
            please create a new document for the United States Constitution.
            populate it with the preamble, all articles (I through VII), and all amendments (I through XXVII).
            the preamble, each article, and each amendment, should be in a separate section.
            ensure that all content matches that of the actual constitution.
            """).strip()
        )
    ]
    plan = await build_plan_for_turn(llms, conversation_history)

    assert plan.recommended_next_action == "make_document_changes"
    assert plan.document_changes_tool_calls is not None, (
        "document_changes_tool_calls is not set, even though recommended_next_action is set to make_document_changes"
    )

    def tool_name(call: ToolCall) -> str:
        return call.call.split("(")[0]

    def tool_args(call: ToolCall) -> dict:
        args_json = call.call.strip(tool_name(call) + "(").strip(")")
        args = json.loads(args_json)
        # the completion sometimes returns the arguments nested in a "properties" field
        if "properties" in args:
            args = args["properties"]
        return args

    assert len(plan.document_changes_tool_calls) > 0, (
        "document_changes_tool_calls is empty, expected at least one element"
    )
    possible_create_document_call = plan.document_changes_tool_calls.pop(0)
    assert tool_name(possible_create_document_call) == "create_document"
    assert tool_args(possible_create_document_call).get("title") == "United States Constitution"

    create_document_section_calls = []
    while (
        len(plan.document_changes_tool_calls) > 0
        and tool_name(plan.document_changes_tool_calls[0]) == "create_document_section"
    ):
        create_document_section_calls.append(plan.document_changes_tool_calls.pop(0))

    # collect these for including in assertion messages
    create_document_section_titles = [tool_args(call).get("section_title") for call in create_document_section_calls]

    assert len(plan.document_changes_tool_calls) == 0, (
        f"Remaining tool calls are unexpected: {plan.document_changes_tool_calls}"
    )

    assert len(create_document_section_calls) > 0, (
        "create_document_section_calls is empty, expected at least one element"
    )
    possible_preamble_call = create_document_section_calls.pop(0)
    assert tool_args(possible_preamble_call).get("section_title") == "Preamble"

    # collect calls for articles based on title prefix
    create_article_calls = []
    while len(create_document_section_calls) > 0 and (
        tool_args(create_document_section_calls[0]).get("section_title") or ""
    ).startswith("Article"):
        create_article_calls.append(create_document_section_calls.pop(0))

    # collect calls for amendments based on title prefix
    create_amendment_calls = []
    while len(create_document_section_calls) > 0 and (
        tool_args(create_document_section_calls[0]).get("section_title") or ""
    ).startswith("Amendment"):
        create_amendment_calls.append(create_document_section_calls.pop(0))

    assert len(create_document_section_calls) == 0, (
        f"Remaining tool calls have unexpected titles: {create_document_section_calls}"
    )

    article_titles = [tool_args(call).get("section_title") for call in create_article_calls]

    assert article_titles == [
        "Article I",
        "Article II",
        "Article III",
        "Article IV",
        "Article V",
        "Article VI",
        "Article VII",
    ] or article_titles == [
        "Article I - The Legislative Branch",
        "Article II - The Executive Branch",
        "Article III - The Judicial Branch",
        "Article IV - States' Powers and Limits",
        "Article V - Amendment Process",
        "Article VI - Federal Powers",
        "Article VII - Ratification",
    ], f"Unexpected article titles. Titles for all sections: {create_document_section_titles}"

    amendment_titles = [tool_args(call).get("section_title") for call in create_amendment_calls]

    # allow for Amendments separator section to be included
    if len(amendment_titles) and amendment_titles[0] == "Amendments":
        amendment_titles.pop(0)

    assert amendment_titles == [
        "Amendment I",
        "Amendment II",
        "Amendment III",
        "Amendment IV",
        "Amendment V",
        "Amendment VI",
        "Amendment VII",
        "Amendment VIII",
        "Amendment IX",
        "Amendment X",
        "Amendment XI",
        "Amendment XII",
        "Amendment XIII",
        "Amendment XIV",
        "Amendment XV",
        "Amendment XVI",
        "Amendment XVII",
        "Amendment XVIII",
        "Amendment XIX",
        "Amendment XX",
        "Amendment XXI",
        "Amendment XXII",
        "Amendment XXIII",
        "Amendment XXIV",
        "Amendment XXV",
        "Amendment XXVI",
        "Amendment XXVII",
    ], f"Unexpected amendment titles. Titles for all sections: {create_document_section_titles}"


def assistant_message(content: str, message_type: MessageType = MessageType.chat) -> ConversationMessage:
    return ConversationMessage(
        id=uuid.uuid4(),
        sender=MessageSender(
            participant_id="assistant",
            participant_role=ParticipantRole.assistant,
        ),
        content=content,
        timestamp=datetime.datetime.now(datetime.UTC),
        content_type="text/plain",
        message_type=message_type,
        filenames=[],
        metadata={},
        has_debug_data=False,
    )


def user_message(content: str, message_type: MessageType = MessageType.chat) -> ConversationMessage:
    return ConversationMessage(
        id=uuid.uuid4(),
        sender=MessageSender(
            participant_id="user",
            participant_role=ParticipantRole.user,
        ),
        content=content,
        timestamp=datetime.datetime.now(datetime.UTC),
        content_type="text/plain",
        message_type=message_type,
        filenames=[],
        metadata={},
        has_debug_data=False,
    )
