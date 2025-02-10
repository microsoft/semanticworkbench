from skill_library.utilities import parse_command_string


def test_parse_command_string():
    command, args, kwargs = parse_command_string(
        'command(arg1, arg2, key1="val1", key2=True, key3=3, key4 = 3+2, key5=[1,2], key6=(1,2), key7={"a": 1, "b": 2})'
    )
    assert command == "command"
    assert args == ("arg1", "arg2")
    assert kwargs == {
        "key1": "val1",
        "key2": True,
        "key3": 3,
        "key4": 5,
        "key5": [1, 2],
        "key6": (1, 2),
        "key7": {"a": 1, "b": 2},
    }


def test_parse_command_string_no_args():
    command, args, kwargs = parse_command_string('command(key1="val1", key2="val2")')
    assert command == "command"
    assert args == ()
    assert kwargs == {"key1": "val1", "key2": "val2"}


def test_parse_command_string_no_kwargs():
    command, args, kwargs = parse_command_string("command(arg1, arg2)")
    assert command == "command"
    assert args == ("arg1", "arg2")
    assert kwargs == {}


def test_parse_command_string_no_args_or_kwargs():
    command, args, kwargs = parse_command_string("command()")
    assert command == "command"
    assert args == ()
    assert kwargs == {}


def test_parse_command_string_no_parens():
    command, args, kwargs = parse_command_string("command")
    assert command == "command"
    assert args == ()
    assert kwargs == {}
