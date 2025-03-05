import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class SkillLogger:
    """Logger for skill routine execution that supports both stderr and JSON file output."""

    def __init__(self, skills_home_dir: Path, run_id: str, interactive: bool, quiet: bool = False):
        """
        Initialize the logger.

        Args:
            skills_home_dir: Path to the skills home directory
            run_id: Unique identifier for this run
            interactive: Whether we're in interactive mode
            quiet: Whether to suppress stderr output in interactive mode
        """
        self.skills_home_dir = skills_home_dir
        self.run_id = run_id
        self.interactive = interactive
        self.quiet = quiet
        self.log_entries = []

        # Create a runs directory if it doesn't exist
        self.runs_dir = skills_home_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        # Set up log file path - now using .jsonl extension
        self.log_file = self.runs_dir / f"{run_id}.jsonl"

        # Write header entry with run metadata
        header_entry = {
            "type": "header",
            "run_id": run_id,
            "start_time": datetime.datetime.now().isoformat(),
        }
        self._write_entry_to_file(header_entry)

        # Configure Python's built-in logger for potential reuse
        self.logger = logging.getLogger("skill_routine")
        self.logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Add a handler for stderr if in interactive mode and not quiet
        if interactive and not quiet:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%H:%M:%S")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log(self, level: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a message with the specified level.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: The message to log
            metadata: Optional additional metadata to include in JSON logs
        """
        # Create log entry with timestamp
        timestamp = datetime.datetime.now().isoformat()
        entry: dict[str, Any] = {
            "type": "log",
            "timestamp": timestamp,
            "level": level,
            "message": message,
        }

        if metadata:
            entry["metadata"] = metadata

        # Add to in-memory log entries for potential later reference
        self.log_entries.append(entry)

        # Write to file immediately
        self._write_entry_to_file(entry)

        # Log using Python's logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)

    def debug(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        self.log("debug", message, metadata)

    def info(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        self.log("info", message, metadata)

    def warning(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        self.log("warning", message, metadata)

    def error(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        self.log("error", message, metadata)

    def critical(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a critical message."""
        self.log("critical", message, metadata)

    def prompt_user(self, message: str) -> None:
        """
        Display a user prompt that bypasses quiet mode.

        This ensures user prompts are always shown in interactive mode,
        even if general logging is suppressed.
        """
        if self.interactive:
            print(f"\n❓ {message}", file=sys.stderr)
            print("Enter your response (or type ':q' to quit, ':h' for help): ", file=sys.stderr, end="", flush=True)

    def _write_entry_to_file(self, entry: Dict[str, Any]) -> None:
        """Write a single log entry to the jsonl file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # If we can't write to the file, try to output to stderr as a fallback
            print(f"Error writing to log file: {e}", file=sys.stderr)

    def finalize(self) -> None:
        """Finalize logging by writing a footer entry."""
        footer_entry = {
            "type": "footer",
            "run_id": self.run_id,
            "end_time": datetime.datetime.now().isoformat(),
            "log_count": len(self.log_entries),
        }
        self._write_entry_to_file(footer_entry)
