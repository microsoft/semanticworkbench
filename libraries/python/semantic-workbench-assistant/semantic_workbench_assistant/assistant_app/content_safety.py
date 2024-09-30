# Copyright (c) Microsoft. All rights reserved.
import json
import logging
from enum import StrEnum
from typing import Any, Awaitable, Callable, Protocol

import deepmerge
from pydantic import BaseModel
from semantic_workbench_api_model.workbench_model import (
    ConversationEvent,
    ConversationEventType,
    MessageType,
    NewConversationMessage,
)

from semantic_workbench_assistant.assistant_app.context import ConversationContext
from semantic_workbench_assistant.assistant_app.protocol import ContentInterceptor

logger = logging.getLogger(__name__)


class ContentSafetyEvaluationResult(StrEnum):
    """
    An enumeration of content safety evaluation results.

    **Properties**
    - **Pass**: The content is safe.
    - **Warn**: The content is potentially unsafe.
    - **Fail**: The content is unsafe.
    """

    Pass = "pass"
    Warn = "warn"
    Fail = "fail"


class ContentSafetyEvaluation(BaseModel):
    """
    A model for content safety evaluation results.

    **Properties**
    - **result (ContentSafetyEvaluationResult)**
        - The result of the evaluation, one of the ContentSafetyEvaluationResult enum values.
    - **note (str | None)**
        - Commentary on the evaluation result, written in human-readable form to be used in UI.
    - **metadata (dict[str, Any] | None)**
        - Additional information about the evaluation, frequently passed along as debug information.
    """

    result: ContentSafetyEvaluationResult = ContentSafetyEvaluationResult.Fail
    note: str | None = None
    metadata: dict[str, Any] = {}


class ContentSafetyEvaluator(Protocol):
    """
    A protocol for content safety evaluators.

    These will be passed to a content safety interceptor to evaluate the safety of content or
    may be used directly by the assistant logic to evaluate content safety.

    **Methods:**
        - **evaluate(content: str | list[str]) -> ContentSafetyEvaluation**
            - Evaluate the content safety of a string or list of strings and return the result.
    """

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation: ...


ContentEvaluatorFactory = Callable[[ConversationContext], Awaitable[ContentSafetyEvaluator]]


class AlwaysWarnContentSafetyEvaluator:
    """
    A content safety evaluator that always returns a warning

    Notes:
    - This is a placeholder evaluator that should be replaced with a real implementation.

    Methods:
        - evaluate(content: str | list[str]) -> ContentSafetyEvaluation:
            Evaluate the content safety of a string or list of strings and return a warning.
    """

    @staticmethod
    async def factory(context: ConversationContext) -> ContentSafetyEvaluator:
        """
        Factory method to create an instance of a ContentSafetyEvaluator.
        """
        return AlwaysWarnContentSafetyEvaluator()

    async def evaluate(self, content: str | list[str]) -> ContentSafetyEvaluation:
        """
        Evaluate the content safety of a string or list of strings.
        """
        return ContentSafetyEvaluation(
            result=ContentSafetyEvaluationResult.Warn,
            note="Content safety evaluation not implemented.",
            metadata={"note": "This is a placeholder evaluator that should be replaced with a real implementation."},
        )


class ContentSafety(ContentInterceptor):
    """
    A content safety interceptor that evaluates the safety of content. It is opinionated in that it
    will:

    - **Incoming conversation events**
        - Fail any event that contains unsafe content.
        - Add the evaluation result to the event data for easy access by other interceptors or the assistant logic.
        - Add interceptor data to the event data to avoid infinite loops.
    - **Outgoing conversation messages**
        - Replace all messages with a notice if any message contains unsafe content.
        - Add a warning to all messages that contain generated content.
        - Add the evaluation result to the debug metadata for visibility in the workbench UI debug views.
        - Add interceptor data to the message metadata to avoid infinite loops.

    **Notes**
    - Use this interceptor as an example or template for implementing content safety evaluation in an
        assistant if you want to introduce your own content safety evaluation logic or handling of
        evaluation results.
    """

    # use the class name to identify the metadata key
    @property
    def metadata_key(self) -> str:
        return "content_safety"

    def __init__(self, content_evaluator_factory: ContentEvaluatorFactory) -> None:
        self.content_evaluator_factory = content_evaluator_factory

    #
    # interceptor methods
    #

    async def intercept_incoming_event(
        self, context: ConversationContext, event: ConversationEvent
    ) -> ConversationEvent | None:
        """
        Evaluate the content safety of an incoming conversation event and return a
        new event with the evaluation result added to the data if the content is safe.

        If the content is not safe, the event will be removed and a notice message will
        be sent back to the conversation.
        """

        # avoid infinite loops by checking if the event was sent by the assistant
        if self._check_event_tag(event, context.assistant.id):
            # return the event without further processing
            return event

        # list of event types that should be evaluated
        if event.event not in [
            ConversationEventType.message_created,
            ConversationEventType.file_created,
            ConversationEventType.file_updated,
        ]:
            # skip evaluation for other event types
            return event

        # evaluate the content safety of the event data
        try:
            evaluator = await self.content_evaluator_factory(context)
            evaluation = await evaluator.evaluate(json.dumps(event.data))
        except Exception as e:
            # if there is an error, return a fail result with the error message
            logger.exception("Content safety evaluation failed.")
            evaluation = ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"Content safety evaluation failed: {e}",
            )

        # create an evaluated event to return
        evaluated_event: ConversationEvent | None = None

        match evaluation.result:
            case ContentSafetyEvaluationResult.Pass | ContentSafetyEvaluationResult.Warn:
                # return the original event
                evaluated_event = event

            case ContentSafetyEvaluationResult.Fail:
                # send a notice back to the conversation that the content safety evaluation failed
                await context.send_messages([
                    self._tag_message(
                        NewConversationMessage(
                            content=evaluation.note or "Content safety evaluation failed.",
                            message_type=MessageType.notice,
                            metadata={
                                "generated_content": False,
                                "debug": {
                                    f"{self.metadata_key}": {
                                        "intercept_incoming_event": {
                                            "evaluation": evaluation.model_dump(),
                                            "event": event.model_dump(),
                                        },
                                    },
                                },
                            },
                        ),
                        context.assistant.id,
                    )
                ])

                # do not assign the updated event to prevent the event from being returned

        # update the results with the data from this interceptor
        if evaluated_event is not None:
            # tag the event with the assistant id to avoid infinite loops
            evaluated_event = self._tag_event(evaluated_event, context.assistant.id)

            # add the evaluation result to the event data so that it can be easily accessed
            # by the assistant logic as desired, such as attaching the evaluation result as
            # debug information on response messages
            deepmerge.always_merger.merge(
                evaluated_event.data,
                {
                    f"{self.metadata_key}": {
                        "intercept_incoming_event": {
                            "evaluation": evaluation.model_dump(),
                        },
                    },
                },
            )

        return evaluated_event

    async def intercept_outgoing_messages(
        self, context: ConversationContext, messages: list[NewConversationMessage]
    ) -> list[NewConversationMessage]:
        """
        Evaluate the content safety of outgoing conversation messages and return a list of
        new messages with warnings added to messages that contain generated content.

        If any message contains unsafe content, all messages will be replaced with a notice.
        """

        # check if any of the messages contain generated content
        if not any(
            message.metadata is not None and message.metadata.get("generated_content", True) for message in messages
        ):
            # skip evaluation if no generated content is found
            return messages

        # evaluate the content safety of the messages
        try:
            evaluator = await self.content_evaluator_factory(context)
            evaluation = await evaluator.evaluate([message.content for message in messages])
        except Exception as e:
            # if there is an error, return a fail result with the error message
            logger.exception("Content safety evaluation failed.")
            evaluation = ContentSafetyEvaluation(
                result=ContentSafetyEvaluationResult.Fail,
                note=f"Content safety evaluation failed: {e}",
            )

        # create a list of evaluated messages to return
        evaluated_messages: list[NewConversationMessage] = []

        match evaluation.result:
            case ContentSafetyEvaluationResult.Pass:
                # return the original messages
                evaluated_messages = messages

            case ContentSafetyEvaluationResult.Warn:
                # add a warning to each message
                evaluated_messages = [
                    NewConversationMessage(
                        **message.model_dump(exclude={"content"}),
                        content=f"{message.content}\n\n[Content safety evaluation warning: {evaluation.note}]",
                    )
                    for message in messages
                ]

            case ContentSafetyEvaluationResult.Fail:
                # replace messages with a single notice that the evaluation failed
                evaluated_messages = [
                    self._tag_message(
                        NewConversationMessage(
                            content=evaluation.note or "Content safety evaluation failed.",
                            message_type=MessageType.notice,
                            metadata={
                                "generated_content": False,
                            },
                        ),
                        context.assistant.id,
                    )
                ]

        # update the results with the data from this interceptor
        for message in evaluated_messages:
            # tag the message with the assistant id to avoid infinite loops
            message = self._tag_message(message, context.assistant.id)

            # add the evaluation result to the debug metadata so that it will
            # be visible in the workbench UI debug views
            deepmerge.always_merger.merge(
                message.metadata,
                {
                    "debug": {
                        f"{self.metadata_key}": {
                            "intercept_outgoing_messages": {
                                "evaluation": evaluation.model_dump(),
                            }
                        }
                    }
                },
            )

        return evaluated_messages

    #
    # helper methods
    #

    def _tag_event(self, event: ConversationEvent, assistant_id: str) -> ConversationEvent:
        """
        Tag an event with the assistant ID to avoid infinite loops.
        """
        deepmerge.always_merger.merge(
            event.data,
            {
                f"{self.metadata_key}": {
                    "assistant_id": assistant_id,
                },
            },
        )
        return event

    def _tag_message(self, message: NewConversationMessage, assistant_id: str) -> NewConversationMessage:
        """
        Tag a message with the assistant id to avoid infinite loops.
        """

        # add the metadata key to the message if it does not exist
        if message.metadata is None:
            message.metadata = {}

        # merge the interceptor key with source assistant id into the message metadata
        deepmerge.always_merger.merge(
            message.metadata,
            {
                f"{self.metadata_key}": {
                    "assistant_id": assistant_id,
                },
            },
        )
        return message

    def _check_event_tag(self, event: ConversationEvent, assistant_id: str) -> bool:
        """
        Check if the event is tagged with the assistant id.
        """

        # if event is a message_created event, check the message metadata
        if event.event == ConversationEventType.message_created:
            if (
                event.data.get("message", {})
                .get("metadata", {})
                .get(f"{self.metadata_key}", {})
                .get("assistant_id", None)
                == assistant_id
            ):
                # return True if the message is tagged with the assistant id
                # otherwise fall through to check the event data
                return True

        return event.data.get(f"{self.metadata_key}", {}).get("assistant_id", None) == assistant_id
