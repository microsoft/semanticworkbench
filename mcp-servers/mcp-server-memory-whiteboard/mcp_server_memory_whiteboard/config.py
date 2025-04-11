from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: Annotated[str, Field(validation_alias="LOG_LEVEL")] = "INFO"


settings = Settings()
