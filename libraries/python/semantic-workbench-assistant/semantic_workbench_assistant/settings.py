from typing import Annotated, Literal
from pydantic import AliasChoices, Field, HttpUrl
from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict

from semantic_workbench_assistant.logging_config import LoggingSettings

from .storage import FileStorageSettings


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="assistant__", env_nested_delimiter="__", env_file=".env", extra="allow"
    )

    storage: FileStorageSettings = FileStorageSettings(root=".data/assistants")
    logging: LoggingSettings = LoggingSettings()

    workbench_service_url: Annotated[
        HttpUrl,
        Field(
            # alias for backwards compatibility with older env vars
            validation_alias=AliasChoices(
                "assistant__workbench_service_url",
                "ASSISTANT__WORKBENCH_SERVICE_URL",
                "assistant__workbench_service_base_url",
                "ASSISTANT__WORKBENCH_SERVICE_BASE_URL",
            )
        ),
    ] = Url("http://127.0.0.1:3000")
    workbench_service_api_key: Annotated[
        str,
        Field(
            # alias for backwards compatibility with older env vars
            validation_alias=AliasChoices(
                "assistant__api_key",
                "ASSISTANT__API_KEY",
                "assistant__workbench_service_api_key",
                "ASSISTANT__WORKBENCH_SERVICE_API_KEY",
            )
        ),
    ] = ""
    workbench_service_ping_interval_seconds: float = 20.0

    assistant_service_id: str | None = None
    assistant_service_name: str | None = None
    assistant_service_description: str | None = None

    assistant_service_url: HttpUrl | None = None

    protocol: Literal["http", "https"] = "http"
    host: str = "127.0.0.1"
    port: int = 3001

    website_protocol: str = Field(alias="WEBSITE_PROTOCOL", default="https")
    website_port: int | None = Field(alias="WEBSITE_PORT", default=None)
    # this env var is set by the Azure App Service
    website_hostname: str = Field(alias="WEBSITE_HOSTNAME", default="")

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    @property
    def callback_url(self) -> str:
        # use config from Azure App Service if available
        if self.website_hostname:
            # small hack to always use the non-staging hostname in the callback url
            hostname = self.website_hostname.replace("-staging", "")
            url = f"{self.website_protocol}://{hostname}"
            if self.website_port is None:
                return url
            return f"{url}:{self.website_port}"

        # fallback to the configured assistant service url if available
        if self.assistant_service_url:
            return str(self.assistant_service_url)

        # finally, fallback to the local service name
        url = f"{self.protocol}://{self.host}"
        if self.port is None:
            return url
        return f"{url}:{self.port}"
