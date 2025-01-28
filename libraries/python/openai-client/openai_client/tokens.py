import base64
import logging
import math
import re
from fractions import Fraction
from io import BytesIO
from typing import Iterable, Sequence

import tiktoken
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from PIL import Image

logger = logging.getLogger(__name__)


def num_tokens_from_message(message: ChatCompletionMessageParam, model: str) -> int:
    """
    Return the number of tokens used by a single message.

    Note that the exact way that tokens are counted from messages may change from model to model.
    Consider the counts from this function an estimate, not a timeless guarantee.

    Reference: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken#6-counting-tokens-for-chat-completions-api-calls
    """

    # First, set the default number of tokens per message and per name and convert generic model names to specific ones
    if model in {
        "gpt-3.5-turbo-0125",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
        # TODO: determine correct handling of reasoning models
        "o1-2024-12-17",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif "gpt-3.5-turbo" in model:
        logger.debug("gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0125.")
        return num_tokens_from_message(message, model="gpt-3.5-turbo-0125")
    elif "gpt-4o-mini" in model:
        logger.debug("gpt-4o-mini may update over time. Returning num tokens assuming gpt-4o-mini-2024-07-18.")
        return num_tokens_from_message(message, model="gpt-4o-mini-2024-07-18")
    elif "gpt-4o" in model:
        logger.debug("gpt-4o may update over time. Returning num tokens assuming gpt-4o-2024-08-06.")
        return num_tokens_from_message(message, model="gpt-4o-2024-08-06")
    elif "gpt-4" in model:
        logger.debug("gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_message(message, model="gpt-4-0613")
    elif model.startswith("o1"):
        logger.debug("o1-* may update over time. Returning num tokens assuming o1-2024-12-17.")
        return num_tokens_from_message(message, model="o1-2024-12-17")
    else:
        raise NotImplementedError(f"num_tokens_from_messages() is not implemented for model {model}.")

    # Then, calculate the number of tokens for the message now that we have the correct specific model name
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("model %s not found. Using cl100k_base encoding.", model)
        encoding = tiktoken.get_encoding("cl100k_base")

    num_tokens = tokens_per_message
    for key, value in message.items():
        if isinstance(value, list):
            # For GPT-4-vision support, based on https://github.com/openai/openai-cookbook/pull/881/files
            for item in value:
                # Note: item[type] does not seem to be counted in the token count
                if item["type"] == "text":
                    num_tokens += len(encoding.encode(item["text"]))
                elif item["type"] == "image_url":
                    num_tokens += count_tokens_for_image(
                        item["image_url"]["url"], model=model, detail=item["image_url"].get("detail", "auto")
                    )
        elif isinstance(value, str):
            num_tokens += len(encoding.encode(value))
        elif value is None:
            # Null values do not consume tokens
            pass
        else:
            raise ValueError(f"Could not encode unsupported message value type: {type(value)}")
        if key == "name":
            num_tokens += tokens_per_name

    return num_tokens


def num_tokens_from_messages(messages: Iterable[ChatCompletionMessageParam], model: str) -> int:
    """
    Return the number of tokens used by a list of messages.

    Note that the exact way that tokens are counted from messages may change from model to model.
    Consider the counts from this function an estimate, not a timeless guarantee.

    In particular, requests that use the optional functions input will consume extra tokens on
    top of the estimates calculated by this function.

    Reference: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken#6-counting-tokens-for-chat-completions-api-calls
    """

    num_tokens = sum((num_tokens_from_message(message, model) for message in messages))
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>

    return num_tokens


def num_tokens_from_tools_and_messages(
    tools: Sequence[ChatCompletionToolParam],
    messages: Iterable[ChatCompletionMessageParam],
    model: str,
):
    """
    Return the number of tokens used by a list of functions and messages.

    Reference: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken#6-counting-tokens-for-chat-completions-api-calls
    """
    # Initialize function settings to 0
    func_init = 0
    prop_init = 0
    prop_key = 0
    enum_init = 0
    enum_item = 0
    func_end = 0

    if model in ["gpt-4o", "gpt-4o-mini"]:
        # Set function settings for the above models
        func_init = 7
        prop_init = 3
        prop_key = 3
        enum_init = -3
        enum_item = 3
        func_end = 12
    elif model in ["gpt-3.5-turbo", "gpt-4"]:
        # Set function settings for the above models
        func_init = 10
        prop_init = 3
        prop_key = 3
        enum_init = -3
        enum_item = 3
        func_end = 12
    else:
        raise NotImplementedError(f"num_tokens_from_tools_and_messages() is not implemented for model {model}.")

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("model %s not found. Using o200k_base encoding.", model)
        encoding = tiktoken.get_encoding("o200k_base")

    func_token_count = 0
    for f in tools:
        func_token_count += func_init  # Add tokens for start of each function
        function = f["function"]
        f_name = function["name"]
        f_desc = function.get("description", "")
        if f_desc.endswith("."):
            f_desc = f_desc[:-1]
        line = f_name + ":" + f_desc
        func_token_count += len(encoding.encode(line))  # Add tokens for set name and description
        if (
            "parameters" in function
            and "properties" in function["parameters"]
            and isinstance(function["parameters"]["properties"], dict)
            and len(function["parameters"]["properties"]) > 0
        ):
            func_token_count += prop_init  # Add tokens for start of each property
            for key in list(function["parameters"]["properties"].keys()):
                func_token_count += prop_key  # Add tokens for each set property
                p_name = key
                p_type = function["parameters"]["properties"][key]["type"]
                p_desc = function["parameters"]["properties"][key]["description"]
                if "enum" in function["parameters"]["properties"][key].keys():
                    func_token_count += enum_init  # Add tokens if property has enum list
                    for item in function["parameters"]["properties"][key]["enum"]:
                        func_token_count += enum_item
                        func_token_count += len(encoding.encode(item))
                if p_desc.endswith("."):
                    p_desc = p_desc[:-1]
                line = f"{p_name}:{p_type}:{p_desc}"
                func_token_count += len(encoding.encode(line))
    if len(tools) > 0:
        func_token_count += func_end

    messages_token_count = num_tokens_from_messages(messages, model)
    total_tokens = messages_token_count + func_token_count

    return total_tokens


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
