# Initialize logging first
from .logging import logger, setup_file_logging

# Import the app
from .chat import app

# Set up file logging
log_file = setup_file_logging()
logger.info(f"Project Assistant initialized with log file: {log_file}")

__all__ = ["app"]
