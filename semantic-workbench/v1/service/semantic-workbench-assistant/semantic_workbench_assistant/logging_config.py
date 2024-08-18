import logging
import re

import asgi_correlation_id
from pydantic_settings import BaseSettings
from pythonjsonlogger import jsonlogger
from rich.logging import RichHandler


class LoggingSettings(BaseSettings):
    json_format: bool = False
    # The maximum length of the message field in the JSON log output.
    # Azure app services have a limit of 16,368 characters for the entire log entry.
    # Longer entries will be split into multiple log entries, making it impossible
    # to parse the JSON when reading logs.
    json_format_maximum_message_length: int = 15_000
    log_level: str = "INFO"


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
            f"{message[:self.max_message_length // 2]}... truncated ...{message[-self.max_message_length // 2:]}"
        )
        return log_record


class JSONHandler(logging.StreamHandler):

    def __init__(self, max_message_length: int):
        super().__init__()
        self.setFormatter(
            CustomJSONFormatter(
                "%(name)s %(filename)s %(module)s %(lineno)s %(levelname)s %(correlation_id)s %(message)s",
                timestamp=True,
                max_message_length=max_message_length,
            )
        )


class DebugLevelForNoisyLogFilter(logging.Filter):
    """Lowers log level to DEBUG for logs that match specific logger names and message patterns."""

    def __init__(self, log_level: int, *names_and_patterns: tuple[str, re.Pattern]):
        self._log_level = log_level
        self._names_and_patterns = names_and_patterns

    def filter(self, record: logging.LogRecord) -> bool:
        if not any(
            record.name == name and pattern.search(record.getMessage()) for name, pattern in self._names_and_patterns
        ):
            return True

        record.levelname = logging.getLevelName(logging.DEBUG)
        record.levelno = logging.DEBUG

        return self._log_level <= record.levelno


def config(settings: LoggingSettings):
    log_level = logging.getLevelNamesMapping()[settings.log_level.upper()]

    handler = RichHandler(rich_tracebacks=True)
    if settings.json_format:
        handler = JSONHandler(max_message_length=settings.json_format_maximum_message_length)

    handler.addFilter(asgi_correlation_id.CorrelationIdFilter(uuid_length=8, default_value="-"))
    handler.addFilter(
        DebugLevelForNoisyLogFilter(
            log_level,
            # noisy assistant-service ping requests
            ("httpx", re.compile(r"PUT .+/assistant-service-registrations/[^\s]+ \"HTTP")),
        )
    )

    logging.basicConfig(
        level=log_level,
        format="%(name)35s [%(correlation_id)s] %(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
