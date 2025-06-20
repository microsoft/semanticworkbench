import datetime
import logging
from functools import wraps
from inspect import iscoroutinefunction
from time import perf_counter

timing_logger = logging.getLogger("history.timing")


def log_timing(func):
    if iscoroutinefunction(func):
        # If the function is a coroutine, we need to use an async wrapper
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = perf_counter()
            result = await func(*args, **kwargs)
            end_time = perf_counter()
            timing_logger.info(
                "function timing; name: %s, duration: %s",
                func.__name__,
                datetime.timedelta(seconds=end_time - start_time),
            )
            return result

        return async_wrapper

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        result = func(*args, **kwargs)
        end_time = perf_counter()
        timing_logger.info(
            "function timing; name: %s, duration: %s", func.__name__, datetime.timedelta(seconds=end_time - start_time)
        )
        return result

    return wrapper
