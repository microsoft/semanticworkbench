import os
from pydantic_settings import BaseSettings

log_level = os.environ.get("LOG_LEVEL", "INFO")

class Settings(BaseSettings):
    log_level: str = log_level
