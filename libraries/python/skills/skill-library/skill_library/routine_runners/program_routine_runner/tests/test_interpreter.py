from textwrap import dedent
from typing import Generator

import pytest
from skill_library.routine_runners.program_routine_runner import (
    FunctionCache,
    Interpreter,
    PausedExecution,
    ReturnValue,
)


class TestInterpreter:
    def test_basic(self):
        code = dedent("""
        def main():
            x = str(123)  # Built-in function call
            y = len([1, 2, 3])  # Built-in function call
            z = unknown_func("test")  # Unknown function (should pause)
            print(x, y, z)
        """)

        # Run with built-in support
        interpreter = Interpreter()
        interpreter.load_code(code)
        gen = interpreter.execute_with_pausing()

        try:
            # Execution runs until it pauses.
            status = next(gen)
            assert isinstance(status, PausedExecution)

            # Simulate getting a return value for `unknown_func`.
            external_result = "external_result"

            # Inject and resume
            cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
            interpreter.add_function_result(status.func_name, cache_key, external_result)
            gen = interpreter.execute_with_pausing()

        except StopIteration:
            print("Execution finished.")

    def test_invalid_syntax(self):
        """Test parsing rejects invalid Python syntax."""
        code = "x = :"
        with pytest.raises(SyntaxError):
            interpreter = Interpreter().load_code(code)
            gen = interpreter.execute_with_pausing()
            next(gen)
            assert False

    def test_basic_function(self):
        """Test parsing of valid Python code."""
        interpreter = Interpreter()

        def main():
            x = 1
            y = 2
            result = x + y
            return result

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()
        assert isinstance(gen, Generator)
        value = next(gen)
        assert value.value == 3  # type: ignore

    def test_external_function_pause(self):
        """Test parsing of valid Python code."""
        interpreter = Interpreter()

        def external_func(x, y):
            return x + y

        def main():
            x = 1
            y = 2
            z = external_func(x, y)
            result = x + y + z
            return result

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        value = None
        while True:
            status = next(gen)
            if isinstance(status, PausedExecution):
                external_result = locals()[status.func_name](*status.args, **status.kwargs)
                cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
                interpreter.add_function_result(status.func_name, cache_key, external_result)
            elif isinstance(status, ReturnValue):
                value = status.value
                break

        assert value == 6

    def test_external_method_pause(self):
        """Test parsing of valid Python code."""
        interpreter = Interpreter()

        class ExternalClass:
            def external_func(self, x, y):
                return x + y

        common = ExternalClass()

        def main():
            x = 1
            y = 2
            z = common.external_func(x, y)
            result = x + y + z
            return result

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        value = None
        while True:
            status = next(gen)
            if isinstance(status, PausedExecution):
                external_result = common.external_func(*status.args, **status.kwargs)
                cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
                interpreter.add_function_result(status.func_name, cache_key, external_result)
            elif isinstance(status, ReturnValue):
                value = status.value
                break

        assert value == 6

    def test_multiple_external_calls(self):
        """Test parsing of valid Python code."""

        def external_func(x, y):
            return x + y

        def main():
            x = 1
            y = 2
            z = external_func(x, x)  # Will pause
            m = external_func(y, y)  # Will pause again since args are different
            result = z + m
            return result

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        value = None
        while True:
            status = next(gen)
            if isinstance(status, PausedExecution):
                # Calculate result with actual args
                external_result = locals()[status.func_name](*status.args, **status.kwargs)
                # Cache the result for these specific args
                cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
                interpreter.add_function_result(status.func_name, cache_key, external_result)
            elif isinstance(status, ReturnValue):
                value = status.value
                break

        assert value == 6

    def test_multiple_processes(self):
        """Test handling external calls across multiple process boundaries."""

        def external_func(x, y):
            return x + y

        def main():
            x = 1
            y = 2
            z = external_func(x, x)
            m = external_func(y, y)
            result = z + m
            return result

        # First "process"
        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        # Handle first external call
        status = next(gen)
        assert isinstance(status, PausedExecution)
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)

        # Serialize state
        state_data = interpreter.get_state()

        # Second "process"
        interpreter = Interpreter.from_state(state_data)
        gen = interpreter.execute_with_pausing()  # Don't transform, use stored AST

        # Handle second external call
        status = next(gen)
        assert isinstance(status, PausedExecution)
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)

        # Get final result
        result = next(gen)
        assert isinstance(result, ReturnValue)
        assert result.value == 6

    def test_conditional_external_call(self):
        """Test external function call inside a conditional block."""

        def external_func(x, y):
            return x + y

        def main():
            x = 1
            y = 2
            if x < y:  # This condition will be True
                result = external_func(x, y)
                return result
            return 0

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        # Handle external call
        status = next(gen)
        assert isinstance(status, PausedExecution)
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)

        # Get final result
        result = next(gen)
        assert isinstance(result, ReturnValue)
        assert result.value == 3

    def test_while_loop_external_call(self):
        """Test external function call inside a while loop, breaking after second call."""

        def external_func(x):
            return x + 1

        def main():
            counter = 0
            while True:
                counter = external_func(counter)  # First call returns 1, second call returns 2
                if counter >= 2:
                    break
            return counter

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        # First iteration - counter goes from 0 to 1
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.args == (0,)  # First call with counter = 0
        external_result = external_func(*status.args)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)

        # Second iteration - counter goes from 1 to 2 and breaks
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.args == (1,)  # Second call with counter = 1
        external_result = external_func(*status.args)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)

        # Get final result
        result = next(gen)
        assert isinstance(result, ReturnValue)
        assert result.value == 2  # Loop breaks when counter reaches 2

    def test_nested_external_calls(self):
        """Test external function call being used as argument to another external function."""

        def add_one(x):
            return x + 1

        def multiply(x, y):
            return x * y

        def main():
            x = 2
            # multiply(add_one(x), x) should compute multiply(3, 2) = 6
            result = multiply(add_one(x), x)
            return result

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        # First we should get the inner add_one call
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.func_name == "add_one"
        assert status.args == (2,)
        inner_result = add_one(*status.args)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, inner_result)

        # Then we should get the outer multiply call
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.func_name == "multiply"
        assert status.args == (3, 2)  # First arg is result of add_one(2), second arg is original x
        outer_result = multiply(*status.args)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, outer_result)

        # Get final result
        result = next(gen)
        assert isinstance(result, ReturnValue)
        assert result.value == 6

    def test_external_function_complex_types(self):
        """Test handling of complex data types in external function calls."""

        def external_func(lst, dct):
            return {"list_sum": sum(lst), "dict_value": dct["key"], "combined": f"{sum(lst)}_{dct['key']}"}

        def main():
            # Create some complex nested data structures
            my_list = [1, 2, 3, 4, 5]
            my_dict = {"key": "value", "nested": {"number": 42}}
            data = external_func(my_list, my_dict)
            return data

        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        # Handle external call
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.func_name == "external_func"

        # Verify the arguments were passed correctly
        assert status.args[0] == [1, 2, 3, 4, 5]
        assert status.args[1] == {"key": "value", "nested": {"number": 42}}

        # Calculate external function result
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)

        # Get final result
        result = next(gen)
        assert isinstance(result, ReturnValue)

        # Verify the complex return value
        expected = {"list_sum": 15, "dict_value": "value", "combined": "15_value"}
        assert result.value == expected

        # Verify the result can be serialized and deserialized
        # by getting interpreter state and restoring it
        state_data = interpreter.get_state()
        new_interpreter = Interpreter.from_state(state_data)

        # Try to use the cached result
        gen = new_interpreter.execute_with_pausing()
        result = next(gen)
        assert isinstance(result, ReturnValue)
        assert result.value == expected

    def test_state_persistence_complex(self):
        """Test state persistence with complex call patterns and state serialization mid-execution."""

        def external_func(x, prev_results=None):
            # Function that depends on both current input and previous results
            if prev_results is None:
                prev_results = []
            return {"value": x + sum(prev_results), "history": prev_results + [x]}

        def main():
            results = []
            # We'll make three calls, each depending on previous results
            for i in range(3):
                response = external_func(i, prev_results=[r["value"] for r in results] if results else None)
                results.append(response)
            return results

        # First "process" - handle first call
        interpreter = Interpreter().load_function(main)
        gen = interpreter.execute_with_pausing()

        # First call (i=0)
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.args == (0,)  # First call with i=0
        assert status.kwargs == {"prev_results": None}  # Default param gets passed as None
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)
        print("Cache state after first call:")
        print(interpreter.function_cache.json())

        # Save state after first call
        state_data = interpreter.get_state()

        # Second "process" - handle second call
        interpreter = Interpreter.from_state(state_data)
        print("Cache state after loading state after first call:")
        print(interpreter.function_cache.json())
        gen = interpreter.execute_with_pausing()

        # Second call (i=1)
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.args == (1,)  # Second call with i=1
        assert status.kwargs == {"prev_results": [0]}  # Previous results passed as kwarg
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)
        print("Cache state after second call:")
        print(interpreter.function_cache.json())

        # Save state after second call
        state_data = interpreter.get_state()

        # Third "process" - handle final call
        interpreter = Interpreter.from_state(state_data)
        print("Cache state after loading state after second call:")
        print(interpreter.function_cache.json())
        gen = interpreter.execute_with_pausing()

        # Third call (i=2)
        status = next(gen)
        assert isinstance(status, PausedExecution)
        assert status.args == (2,)  # Third call with i=2
        assert status.kwargs == {"prev_results": [0, 1]}  # Previous results passed as kwarg
        external_result = external_func(*status.args, **status.kwargs)
        cache_key = FunctionCache.get_cache_key(status.args, status.kwargs)
        interpreter.add_function_result(status.func_name, cache_key, external_result)
        print("Cache state after third call:")
        print(interpreter.function_cache.json())

        # Get final result
        result = next(gen)
        assert isinstance(result, ReturnValue)

        # Verify the complete execution results
        expected = [
            {"value": 0, "history": [0]},  # First call: just 0
            {"value": 1, "history": [0, 1]},  # Second call: 1 + previous (0)
            {"value": 3, "history": [0, 1, 2]},  # Third call: 2 + previous (0 + 1)
        ]
        assert result.value == expected
