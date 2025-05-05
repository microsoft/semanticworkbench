"""
Analysis and detection functions for the project assistant.

This module contains functions for analyzing messages and project content
to detect specific conditions, such as information request needs.
"""

import json
from typing import Any, Dict, List

import openai_client
from openai.types.chat import ChatCompletionMessageParam
from semantic_workbench_assistant.assistant_app import ConversationContext

from .config import assistant_config
from .logging import logger


async def detect_information_request_needs(context: ConversationContext, message: str) -> Dict[str, Any]:
    """
    Analyze a user message in context of recent chat history to detect potential information request needs.
    Uses an LLM for sophisticated detection.

    Args:
        context: The conversation context
        message: The user message to analyze

    Returns:
        Dict with detection results including is_information_request, confidence, and other metadata
    """
    debug: Dict[str, Any] = {
        "message": message,
        "context": context,
    }

    # Get config via assistant config
    config = await assistant_config.get(context.assistant)

    # Check if we're in a test environment (Missing parts of context)
    if not hasattr(context, "assistant") or context.assistant is None:
        return {
            "is_information_request": False,
            "reason": "Unable to perform detection in test environment - missing context",
            "confidence": 0.0,
            "debug": debug,
        }

    # Get the config
    config = await assistant_config.get(context.assistant)

    # Verify service_config is available
    if not config.service_config:
        logger.warning("No service_config available for LLM-based detection")
        return {
            "is_information_request": False,
            "reason": "LLM detection unavailable - missing service configuration",
            "confidence": 0.0,
            "debug": debug,
        }

    # Get recent conversation history (up to 10 messages)
    chat_history = []
    try:
        # Get recent messages to provide context
        messages_response = await context.get_messages(limit=10)
        if messages_response and messages_response.messages:
            # Format messages for the LLM
            for msg in messages_response.messages:
                # Format the sender name
                sender_name = "Team Member"
                if msg.sender.participant_id == context.assistant.id:
                    sender_name = "Assistant"

                # Add to chat history
                role = "user" if sender_name == "Team Member" else "assistant"
                chat_history.append({"role": role, "content": f"{sender_name}: {msg.content}"})

            # Reverse to get chronological order
            chat_history.reverse()
    except Exception as e:
        logger.warning(f"Could not retrieve chat history: {e}")
        # Continue without history if we can't get it

    try:
        # Create chat completion with history context
        async with openai_client.create_client(config.service_config) as client:
            # Prepare messages array with system prompt and chat history
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": config.prompt_config.project_information_request_detection}
            ]

            # Add chat history if available
            if chat_history:
                for history_msg in chat_history:
                    messages.append({"role": history_msg["role"], "content": history_msg["content"]})

            # Add the current message for analysis - explicitly mark as the latest message
            messages.append({"role": "user", "content": f"Latest message from Team Member: {message}"})

            completion_args = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "response_format": {"type": "json_object"},
                "max_tokens": 500,
                "temperature": 0.2,  # Low temperature for more consistent analysis
            }
            debug["completion_args"] = openai_client.make_completion_args_serializable(completion_args)

            # Make the API call
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
            "reason": f"LLM detection error: {str(e)}",
            "confidence": 0.0,
            "debug": debug,
        }
