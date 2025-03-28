from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: Annotated[str, Field(validation_alias="log_level")] = "INFO"
    enable_client_roots: Annotated[bool, Field(validation_alias="enable_client_roots")] = False


settings = Settings()
