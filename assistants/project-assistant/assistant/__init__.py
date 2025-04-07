# Initialize logging
from .logging import logger, setup_file_logging

# Set up file logging
log_file = setup_file_logging()
logger.info(f"Project Assistant initialized with log file: {log_file}")

# Import the app
from .chat import app

__all__ = ["app"]
