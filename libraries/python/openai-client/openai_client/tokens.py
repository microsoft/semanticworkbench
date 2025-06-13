import base64
import logging
import math
import re
from fractions import Fraction
from functools import lru_cache
from io import BytesIO
from typing import Any, Iterable, Sequence

import tiktoken
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from PIL import Image

logger = logging.getLogger(__name__)


def resolve_model_name(model: str) -> str:
    """
    Given a possibly generic model name, return the specific model name
    that should be used for token counting.

    This function encapsulates the logic that was previously inline in num_tokens_from_message.
    """

    if model in {
        "gpt-3.5-turbo-0125",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
        "o1-2024-12-17",
    }:
        return model
    elif "gpt-3.5-turbo" in model:
        logger.debug("gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0125.")
        return "gpt-3.5-turbo-0125"
    elif "gpt-4o-mini" in model:
        logger.debug("gpt-4o-mini may update over time. Returning num tokens assuming gpt-4o-mini-2024-07-18.")
        return "gpt-4o-mini-2024-07-18"
    elif "gpt-4o" in model:
        logger.debug("gpt-4o may update over time. Returning num tokens assuming gpt-4o-2024-08-06.")
        return "gpt-4o-2024-08-06"
    elif "gpt-4" in model:
        logger.debug("gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return "gpt-4-0613"
    elif model.startswith("o"):
        logger.debug("o series models may update over time. Returning num tokens assuming o1-2024-12-17.")
        return "o1-2024-12-17"
    else:
        raise NotImplementedError(f"num_tokens_from_messages() is not implemented for model {model}.")


@lru_cache(maxsize=16)
def _get_cached_encoding(resolved_model: str) -> tiktoken.Encoding:
    """Cache tiktoken encodings to avoid slow initialization on repeated calls."""
    try:
        return tiktoken.encoding_for_model(resolved_model)
    except KeyError:
        if resolved_model.startswith(("gpt-4o", "o")):
            logger.warning(f"model {resolved_model} not found. Using o200k_base encoding.")
            return tiktoken.get_encoding("o200k_base")
        else:
            logger.warning(f"model {resolved_model} not found. Using cl100k_base encoding.")
            return tiktoken.get_encoding("cl100k_base")


def get_encoding_for_model(model: str) -> tiktoken.Encoding:
    """Get tiktoken encoding for a model, with caching for performance."""
    return _get_cached_encoding(resolve_model_name(model))


def num_tokens_from_message(message: ChatCompletionMessageParam, model: str) -> int:
    """
    Return the number of tokens used by a single message.

    This function is simply a wrapper around num_tokens_from_messages.
    """
    return num_tokens_from_messages([message], model)


def num_tokens_from_string(string: str, model: str) -> int:
    """
    Return the number of tokens used by a string.
    """
    encoding = get_encoding_for_model(model)
    return len(encoding.encode(string))


def num_tokens_from_messages(messages: Iterable[ChatCompletionMessageParam], model: str) -> int:
    """
    Return the number of tokens used by a list of messages.

    Note that the exact way that tokens are counted from messages may change from model to model.
    Consider the counts from this function an estimate, not a timeless guarantee.

    In particular, requests that use the optional functions input will consume extra tokens on
    top of the estimates calculated by this function.

    Reference: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken#6-counting-tokens-for-chat-completions-api-calls
    """

    total_tokens = 0
    # Resolve the specific model name using the helper function.
    specific_model = resolve_model_name(model)

    # Use extra token counts determined experimentally.
    tokens_per_message = 3
    tokens_per_name = 1

    # Get the encoding for the specific model
    encoding = get_encoding_for_model(model)

    # Calculate the total tokens for all messages
    for message in messages:
        # Start with the tokens added per message
        num_tokens = tokens_per_message

        # Add tokens for each key-value pair in the message
        for key, value in message.items():
            # Calculate the tokens for the value
            if isinstance(value, list):
                # For GPT-4-vision support, based on the OpenAI cookbook
                for item in value:
                    # Note: item["type"] does not seem to be counted in the token count
                    if item["type"] == "text":
                        num_tokens += len(encoding.encode(item["text"]))
                    elif item["type"] == "image_url":
                        num_tokens += count_tokens_for_image(
                            item["image_url"]["url"],
                            model=specific_model,
                            detail=item["image_url"].get("detail", "auto"),
                        )
            elif isinstance(value, str):
                num_tokens += len(encoding.encode(value))
            elif value is None:
                # Null values do not consume tokens
                pass
            else:
                raise ValueError(f"Could not encode unsupported message value type: {type(value)}")

            # Add tokens for the name key
            if key == "name":
                num_tokens += tokens_per_name

        # Add the total tokens for this message to the running total
        total_tokens += num_tokens

    # Return the total token count for all messages
    return total_tokens


def count_jsonschema_tokens(schema, encoding, prop_key, enum_item, enum_init) -> Any | int:
    """
    Recursively count tokens in any JSON-serializable object (i.e. a JSON Schema)
    using the provided encoding. Applies a special cost for keys and enum lists.
    """
    tokens = 0
    if isinstance(schema, dict):
        for key, value in schema.items():
            # Special handling for "enum" keys
            if key == "enum" and isinstance(value, list):
                tokens += enum_init  # one-time cost for the enum list
                for item in value:
                    tokens += enum_item
                    if isinstance(item, str):
                        tokens += len(encoding.encode(item))
                    else:
                        tokens += count_jsonschema_tokens(item, encoding, prop_key, enum_item, enum_init)
            else:
                # Count tokens for the key name
                tokens += prop_key
                tokens += len(encoding.encode(str(key)))
                # Recursively count tokens for the value
                tokens += count_jsonschema_tokens(value, encoding, prop_key, enum_item, enum_init)
    elif isinstance(schema, list):
        # For lists not specifically marked as enum, just count tokens for each element.
        for item in schema:
            tokens += count_jsonschema_tokens(item, encoding, prop_key, enum_item, enum_init)
    elif isinstance(schema, str):
        tokens += len(encoding.encode(schema))
    elif isinstance(schema, (int, float, bool)) or schema is None:
        tokens += len(encoding.encode(str(schema)))
    return tokens


def num_tokens_from_tools(
    tools: Sequence[ChatCompletionToolParam],
    model: str,
) -> int:
    """
    Return the number of tokens used by a list of functions and messages.
    This version has been updated to traverse any valid JSON Schema in the
    function parameters.
    """
    # Initialize function-specific token settings
    func_init = 0
    prop_key = 0
    enum_init = 0
    enum_item = 0
    func_end = 0

    specific_model = resolve_model_name(model)

    if specific_model.startswith("gpt-4o") or specific_model.startswith("o"):
        func_init = 7
        # prop_init could be used for object-start if desired (e.g. add once per object)
        prop_key = 3
        enum_init = -3
        enum_item = 3
        func_end = 12
    elif specific_model.startswith("gpt-3.5-turbo") or specific_model.startswith("gpt-4"):
        func_init = 10
        prop_key = 3
        enum_init = -3
        enum_item = 3
        func_end = 12
    else:
        raise NotImplementedError(
            f"num_tokens_from_tools_and_messages() is not implemented for model {specific_model}."
        )

    encoding = _get_cached_encoding(specific_model)

    token_count = 0
    for f in tools:
        token_count += func_init  # Add tokens for start of each function
        function = f["function"]
        f_name = function["name"]
        f_desc = function.get("description", "")
        if f_desc.endswith("."):
            f_desc = f_desc[:-1]
        line = f_name + ":" + f_desc
        token_count += len(encoding.encode(line))  # Add tokens for set name and description
        if "parameters" in function:  # Process any JSON Schema in parameters
            token_count += count_jsonschema_tokens(function["parameters"], encoding, prop_key, enum_item, enum_init)
    if len(tools) > 0:
        token_count += func_end

    return token_count


def num_tokens_from_tools_and_messages(
    tools: Sequence[ChatCompletionToolParam],
    messages: Iterable[ChatCompletionMessageParam],
    model: str,
) -> int:
    """
    Return the number of tokens used by a list of functions and messages.
    """
    # Calculate the total token count for the messages and tools
    messages_token_count = num_tokens_from_messages(messages, model)
    tools_token_count = num_tokens_from_tools(tools, model)
    return messages_token_count + tools_token_count


def get_image_dims(image_uri: str) -> tuple[int, int]:
    # From https://github.com/openai/openai-cookbook/pull/881/files
    if re.match(r"data:image\/\w+;base64", image_uri):
        image_uri = re.sub(r"data:image\/\w+;base64,", "", image_uri)
        with Image.open(BytesIO(base64.b64decode(image_uri))) as image:
            return image.size
    else:
        raise ValueError("Image must be a base64 string.")


def count_tokens_for_image(image_uri: str, detail: str, model: str) -> int:
    # From https://github.com/openai/openai-cookbook/pull/881/files
    # Based on https://platform.openai.com/docs/guides/vision
    multiplier = Fraction(1, 1)
    if model.startswith("gpt-4o-mini"):
        multiplier = Fraction(100, 3)
    COST_PER_TILE = 85 * multiplier
    LOW_DETAIL_COST = COST_PER_TILE
    HIGH_DETAIL_COST_PER_TILE = COST_PER_TILE * 2

    if detail == "auto":
        # assume high detail for now
        detail = "high"

    if detail == "low":
        # Low detail images have a fixed cost
        return int(LOW_DETAIL_COST)
    elif detail == "high":
        # Calculate token cost for high detail images
        width, height = get_image_dims(image_uri)
        # Check if resizing is needed to fit within a 2048 x 2048 square
        if max(width, height) > 2048:
            # Resize dimensions to fit within a 2048 x 2048 square
            ratio = 2048 / max(width, height)
            width = int(width * ratio)
            height = int(height * ratio)
        # Further scale down to 768px on the shortest side
        if min(width, height) > 768:
            ratio = 768 / min(width, height)
            width = int(width * ratio)
            height = int(height * ratio)
        # Calculate the number of 512px squares
        num_squares = math.ceil(width / 512) * math.ceil(height / 512)
        # Calculate the total token cost
        total_cost = num_squares * HIGH_DETAIL_COST_PER_TILE + COST_PER_TILE
        return math.ceil(total_cost)
    else:
        # Invalid detail_option
        raise ValueError(f"Invalid value for detail parameter: '{detail}'. Use 'low' or 'high'.")
