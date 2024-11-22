from pydantic import Field, HttpUrl
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

    workbench_service_url: HttpUrl = Url("http://127.0.0.1:3000")
    workbench_service_api_key: str = ""
    workbench_service_ping_interval_seconds: float = 20.0

    assistant_service_id: str | None = None
    assistant_service_name: str | None = None
    assistant_service_description: str | None = None

    assistant_service_url: HttpUrl | None = None

    host: str = "127.0.0.1"
    port: int = 0

    website_protocol: str = Field(alias="WEBSITE_PROTOCOL", default="https")
    website_port: int | None = Field(alias="WEBSITE_PORT", default=None)
    # this env var is set by the Azure App Service
    website_hostname: str = Field(alias="WEBSITE_HOSTNAME", default="")

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    @property
    def callback_url(self) -> str:
        # use the configured assistant service url if available
        if self.assistant_service_url:
            return str(self.assistant_service_url)

        # use config from Azure App Service if available
        if self.website_hostname:
            url = f"{self.website_protocol}://{self.website_hostname}"
            if self.website_port is None:
                return url
            return f"{url}:{self.website_port}"

        # finally, fallback to the host name/ip and port the app is running on
        url = f"http://{self.host}"
        if self.port is None:
            return url
        return f"{url}:{self.port}"
