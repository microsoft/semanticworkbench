import json
import logging
from typing import Any

from context import ContextProtocol


class Logger:
    def __init__(self, name: str, context: ContextProtocol) -> None:
        self.logger = logging.getLogger(name)
        self.context = context

    def _extra(self, data: Any) -> dict[str, Any]:
        extra = {"session_id": self.context.session_id, "run_id": self.context.run_id}

        # Ensure data is a JSON-serializable object.
        try:
            data = json.loads(json.dumps(data))
        except Exception:
            data = None

        if data:
            extra["data"] = data

        return extra

    def info(self, message: str, data: Any = None) -> None:
        self.logger.info(message, extra=self._extra(data))

    def warning(self, message: str, data: Any = None) -> None:
        self.logger.warning(message, extra=self._extra(data))

    def error(self, message: str, data: Any = None) -> None:
        self.logger.error(message, extra=self._extra(data))

    def debug(self, message: str, data: Any = None) -> None:
        self.logger.debug(message, extra=self._extra(data))

    def critical(self, message: str, data: Any = None) -> None:
        self.logger.critical(message, extra=self._extra(data))

    def exception(self, message: str, data: Any = None) -> None:
        self.logger.exception(message, extra=self._extra(data))
