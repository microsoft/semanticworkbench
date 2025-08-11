"""
Analysis and detection functions for the knowledge transfer assistant.

This module contains functions for analyzing messages and knowledge transfer content
to detect specific conditions, such as information request needs.
"""

import json
from typing import Any

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.config import assistant_config
from assistant.logging import convert_to_serializable, logger


async def detect_information_request_needs(context: ConversationContext, message: str) -> dict[str, Any]:
    """
    Analyze a user message in context of recent chat history to detect potential information request needs.
    Uses an LLM for sophisticated detection.

    Args:
        context: The conversation context
        message: The user message to analyze

    Returns:
        Dict with detection results including is_information_request, confidence, and other metadata
    """
    debug: dict[str, Any] = {
        "message": message,
        "context": convert_to_serializable(context.to_dict()),
    }

    config = await assistant_config.get(context.assistant)

    # Get chat history
    chat_history = []
    try:
        messages_response = await context.get_messages(limit=10)
        if messages_response and messages_response.messages:
            for msg in messages_response.messages:
                sender_name = "Team Member"
                if msg.sender.participant_id == context.assistant.id:
                    sender_name = "Assistant"
                role = "user" if sender_name == "Team Member" else "assistant"
                chat_history.append({"role": role, "content": f"{sender_name}: {msg.content}"})
            chat_history.reverse()
    except Exception as e:
        logger.warning(f"Could not retrieve chat history: {e}")

    try:
        async with openai_client.create_client(config.service_config) as client:
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": config.prompt_config.detect_information_request_needs,
                }
            ]

            if chat_history:
                for history_msg in chat_history:
                    messages.append({"role": history_msg["role"], "content": history_msg["content"]})

            # Add the current message for analysis - explicitly mark as the latest message
            messages.append({
                "role": "user",
                "content": f"Latest message from Team Member: {message}",
            })

            completion_args = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "response_format": {"type": "json_object"},
                "max_tokens": 500,
                "temperature": 0.2,  # Low temperature for more consistent analysis
            }
            debug["completion_args"] = openai_client.serializable(completion_args)

            response = await client.chat.completions.create(
                **completion_args,
            )
            debug["completion_response"] = response.model_dump()

        # Extract and parse the response
        if response and response.choices and response.choices[0].message.content:
            try:
                result = json.loads(response.choices[0].message.content)
                # Add the original message for reference
                result["original_message"] = message
                return result
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from LLM response: {response.choices[0].message.content}")
                return {
                    "is_information_request": False,
                    "reason": "Failed to parse LLM response",
                    "confidence": 0.0,
                    "debug": debug,
                }
        else:
            logger.warning("Empty response from LLM for information request detection")
            return {
                "is_information_request": False,
                "reason": "Empty response from LLM",
                "confidence": 0.0,
                "debug": debug,
            }
    except Exception as e:
        logger.exception(f"Error in LLM-based information request detection: {e}")
        debug["error"] = str(e)
        return {
            "is_information_request": False,
            "reason": f"LLM detection error: {e!s}",
            "confidence": 0.0,
            "debug": debug,
        }
