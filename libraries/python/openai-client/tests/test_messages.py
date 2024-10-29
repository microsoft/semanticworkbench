from openai_client import truncate_messages_for_logging
from openai_client.messages import truncate_string


def test_truncate_messages():
    actual = truncate_messages_for_logging(
        [
            {
                "role": "user",
                "content": "This is a test message that should be truncated",
            },
            {
                "role": "assistant",
                "content": "This is a test message that should be truncated",
            },
            {
                "role": "system",
                "content": "This is a test message that should be truncated",
            },
        ],
        maximum_content_length=20,
    )

    assert actual == [
        {"role": "user", "content": "T ...truncated... d"},
        {"role": "assistant", "content": "T ...truncated... d"},
        {"role": "system", "content": "T ...truncated... d"},
    ]


def test_truncate_string():
    assert truncate_string("A" * 50, 20, "...") == "AAAAAAAA...AAAAAAAA"
