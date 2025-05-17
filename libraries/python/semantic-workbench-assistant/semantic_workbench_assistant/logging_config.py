import logging
import logging.config
from time import perf_counter
from typing import Awaitable, Callable

import asgi_correlation_id
from fastapi import Request, Response
from pydantic_settings import BaseSettings
from pythonjsonlogger import json as jsonlogger


class LoggingSettings(BaseSettings):
    json_format: bool = False
    # The maximum length of the message field in the JSON log output.
    # Azure app services have a limit of 16,368 characters for the entire log entry.
    # Longer entries will be split into multiple log entries, making it impossible
    # to parse the JSON when reading logs.
    json_format_maximum_message_length: int = 15_000
    log_level: str = "INFO"


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # The default formatter format (configured below) includes a "data"
        # field, which is not always present in the record. We add it here to
        # avoid a KeyError. If you want to add data to be printed out in the
        # logs, add it to the `extra`` dict in the `data`` parameter.
        #
        # For example: logger.info("This is a log message", extra={"data": {"key": "value"}})
        #
        # Note: The JSON Formatter automatically adds anything in the extra dict
        # to its formatted output.
        if "data" not in record.__dict__["args"]:
            record.data = ""
        else:
            record.data = record.__dict__["args"]["data"]
        return super().format(record)


class CustomJSONFormatter(jsonlogger.JsonFormatter):
    def __init__(self, *args, **kwargs):
        self.max_message_length = kwargs.pop("max_message_length", 15_000)
        super().__init__(*args, **kwargs)

    def process_log_record(self, log_record):
        """
        Truncate the message if it is too long to ensure that the downstream processors, such as log shipping
        and/or logging storage, do not chop it into multiple log entries.
        """
        if "message" not in log_record:
            return log_record

        message = log_record["message"]
        if len(message) <= self.max_message_length:
            return log_record

        log_record["message"] = (
            f"{message[: self.max_message_length // 2]}... truncated ...{message[-self.max_message_length // 2 :]}"
        )
        return log_record


def config(settings: LoggingSettings):
    log_level = settings.log_level.upper()
    # log_level_int = logging.getLevelNamesMapping()[log_level]

    handler = "rich"
    if settings.json_format:
        handler = "json"

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": CustomFormatter,
                "format": "%(name)35s [%(correlation_id)s] %(message)s %(data)s",
                "datefmt": "[%X]",
            },
            "json": {
                "()": CustomJSONFormatter,
                "format": "%(name)s %(filename)s %(module)s %(lineno)s %(levelname)s %(correlation_id)s %(message)s",
                "timestamp": True,
                "max_message_length": settings.json_format_maximum_message_length,
            },
        },
        "handlers": {
            "rich": {
                "class": "rich.logging.RichHandler",
                "rich_tracebacks": True,
                "formatter": "default",
                "filters": ["asgi_correlation_id"],
            },
            "json": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["asgi_correlation_id"],
            },
        },
        "loggers": {
            "azure.core.pipeline.policies.http_logging_policy": {
                "level": "WARNING",
            },
            "azure.identity": {
                "level": "WARNING",
            },
            "semantic_workbench_assistant": {
                "level": log_level,
            },
        },
        "root": {
            "handlers": [handler],
            "level": log_level,
        },
        "filters": {
            "asgi_correlation_id": {
                "()": asgi_correlation_id.CorrelationIdFilter,
                "uuid_length": 8,
                "default_value": "-",
            },
        },
    })


def log_request_middleware(
    logger: logging.Logger | None = None,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    access_logger = logger or logging.getLogger("access_log")

    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        This middleware will log all requests and their processing time.
        E.g. log:
        0.0.0.0:1234 - "GET /ping HTTP/1.1" 200 OK 1.00ms 0b
        """
        url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
        start_time = perf_counter()
        response = await call_next(request)
        process_time = (perf_counter() - start_time) * 1000
        formatted_process_time = "{0:.2f}".format(process_time)
        host = getattr(getattr(request, "client", None), "host", None)
        port = getattr(getattr(request, "client", None), "port", None)
        http_version = f"HTTP/{request.scope.get('http_version', '1.1')}"
        content_length = response.headers.get("content-length", 0)
        access_logger.info(
            f'{host}:{port} - "{request.method} {url} {http_version}" {response.status_code} {formatted_process_time}ms {content_length}b',
        )
        return response

    return middleware
