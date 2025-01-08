from skill_library.utilities import make_arg_set


def test_make_arg_set():
    expected_variables = ["a", "b", "c"]
    args = (1, 2)
    kwargs = {"c": 3}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {"a": 1, "b": 2, "c": 3}


def test_make_arg_set_no_args():
    expected_variables = ["a", "b", "c"]
    args = ()
    kwargs = {"a": 1, "b": 2, "c": 3}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {"a": 1, "b": 2, "c": 3}


def test_make_arg_set_no_kwargs():
    expected_variables = ["a", "b", "c"]
    args = (1, 2, 3)
    kwargs = {}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {"a": 1, "b": 2, "c": 3}


def test_make_arg_set_no_args_or_kwargs():
    expected_variables = ["a", "b", "c"]
    args = ()
    kwargs = {}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {}


def test_make_arg_set_extra_args():
    expected_variables = ["a", "b", "c"]
    args = (1, 2, 3, 4)
    kwargs = {}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {"a": 1, "b": 2, "c": 3}


def test_make_arg_set_extra_kwargs():
    expected_variables = ["a", "b", "c"]
    args = ()
    kwargs = {"a": 1, "b": 2, "c": 3, "d": 4}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {"a": 1, "b": 2, "c": 3}


def test_make_arg_set_extra_args_and_kwargs():
    expected_variables = ["a", "b", "c"]
    args = (1, 2, 3, 4)
    kwargs = {"a": "m", "b": "n", "c": "o", "d": "p"}

    arg_set = make_arg_set(expected_variables, args, kwargs)
    assert arg_set == {"a": "m", "b": "n", "c": "o"}
