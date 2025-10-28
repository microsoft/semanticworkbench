import os

import openai_client
import pytest
from openai import AuthenticationError, OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


@pytest.fixture
def client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    # Test if the API key is valid by making a minimal request
    try:
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1,
        )
    except AuthenticationError as e:
        pytest.skip(f"OPENAI_API_KEY is invalid or deactivated: {e}")

    return client


@pytest.mark.parametrize(
    ("model", "include_image"),
    [("gpt-3.5-turbo", False), ("gpt-4-0613", False), ("gpt-4", False), ("gpt-4o", True), ("gpt-4o-mini", True)],
)
def test_num_tokens_for_messages(model: str, include_image: bool, client: OpenAI) -> None:
    example_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "New synergies will help drive top-line growth.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Things working well together will increase revenue.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Let's talk later when we're less busy about how to do better.",
        },
        {
            "role": "user",
            "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
        },
    ]

    if include_image:
        example_messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
                            "detail": "auto",
                        },
                    },
                ],
            },
        )

    response = client.chat.completions.create(model=model, messages=example_messages, temperature=0, max_tokens=1)

    assert response.usage is not None, "No usage data returned by the OpenAI API."

    actual_num_tokens = openai_client.num_tokens_from_messages(messages=example_messages, model=model)
    expected_num_tokens = response.usage.prompt_tokens

    assert actual_num_tokens == expected_num_tokens, (
        f"num_tokens_from_messages() does not match the OpenAI API response for model {model}."
    )


@pytest.mark.parametrize("model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini"])
def test_num_tokens_for_tools_and_messages(model: str, client: OpenAI) -> None:
    tools: list[ChatCompletionToolParam] = [
        {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {
                            "type": "string",
                            "description": "The unit of temperature to return",
                            "enum": ["celsius", "fahrenheit"],
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    example_messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "New synergies will help drive top-line growth.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Things working well together will increase revenue.",
        },
        {
            "role": "system",
            "name": "example_user",
            "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
        },
        {
            "role": "system",
            "name": "example_assistant",
            "content": "Let's talk later when we're less busy about how to do better.",
        },
        {
            "role": "user",
            "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
        },
    ]

    response = client.chat.completions.create(
        model=model, messages=example_messages, tools=tools, temperature=0, max_tokens=1
    )

    assert response.usage is not None, "No usage data returned by the OpenAI API."

    actual_num_tokens = openai_client.num_tokens_from_tools_and_messages(
        tools=tools, messages=example_messages, model=model
    )
    expected_num_tokens = response.usage.prompt_tokens

    assert actual_num_tokens == expected_num_tokens, (
        f"num_tokens_from_tools_and_messages() does not match the OpenAI API response for model {model}."
    )
