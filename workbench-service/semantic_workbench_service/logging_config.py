import logging
import re

import asgi_correlation_id
from pydantic_settings import BaseSettings
from pythonjsonlogger import jsonlogger
from rich.logging import RichHandler


class LoggingSettings(BaseSettings):
    json_format: bool = False
    log_level: str = "INFO"


class JSONHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.setFormatter(
            jsonlogger.JsonFormatter(
                "%(filename)s %(name)s %(lineno)s %(levelname)s %(correlation_id)s %(message)s %(taskName)s"
                " %(process)d",
                timestamp=True,
            )
        )


class DebugLevelForNoisyLogFilter(logging.Filter):
    """Lowers logs for specific routes to DEBUG level."""

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
        handler = JSONHandler()

    handler.addFilter(
        DebugLevelForNoisyLogFilter(
            log_level,
            # noisy assistant-service pings
            ("uvicorn.access", re.compile(r"PUT /assistant-service-registrations/[^\s]+ HTTP")),
        )
    )
    handler.addFilter(asgi_correlation_id.CorrelationIdFilter(uuid_length=8, default_value="-"))

    logging.basicConfig(
        level=log_level,
        format="%(name)35s [%(correlation_id)s] %(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
