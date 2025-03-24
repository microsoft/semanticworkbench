from typing import Annotated

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .files import StorageSettings
from .logging_config import LoggingSettings


class DBSettings(BaseSettings):
    url: str = "sqlite:///.data/workbench.db"
    echosql: bool = False
    postgresql_ssl_mode: str = "require"
    postgresql_pool_size: int = 10
    alembic_config_path: str = "./alembic.ini"


class ApiKeySettings(BaseSettings):
    key_vault_url: HttpUrl | None = None

    @property
    def is_secured(self) -> bool:
        return self.key_vault_url is not None


class AuthSettings(BaseSettings):
    allowed_jwt_algorithms: set[str] = {"RS256"}
    allowed_app_id: str = "22cb77c3-ca98-4a26-b4db-ac4dcecba690"


class AssistantIdentifiers(BaseSettings):
    assistant_service_id: str
    template_id: str
    name: str


class WebServiceSettings(BaseSettings):
    protocol: str = "http"
    host: str = "127.0.0.1"
    port: int = 3000

    assistant_api_key: ApiKeySettings = ApiKeySettings()

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    assistant_service_online_check_interval_seconds: float = 10.0

    azure_openai_endpoint: Annotated[str, Field(validation_alias="azure_openai_endpoint")] = ""
    azure_openai_deployment: Annotated[str, Field(validation_alias="azure_openai_deployment")] = "gpt-4o-mini"
    azure_openai_model: Annotated[str, Field(validation_alias="azure_openai_model")] = "gpt-4o-mini"
    azure_openai_api_version: Annotated[str, Field(validation_alias="azure_openai_api_version")] = "2025-02-01-preview"

    default_assistants: list[AssistantIdentifiers] = []


class AzureSpeechSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="azure_speech__", env_nested_delimiter="_", env_file=".env", extra="allow"
    )

    resource_id: str = ""
    region: str = ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="workbench__", env_nested_delimiter="__", env_file=".env", extra="allow"
    )

    db: DBSettings = DBSettings()
    storage: StorageSettings = StorageSettings()
    logging: LoggingSettings = LoggingSettings()
    service: WebServiceSettings = WebServiceSettings()
    azure_speech: AzureSpeechSettings = AzureSpeechSettings()
    auth: AuthSettings = AuthSettings()


if __name__ == "__main__":
    # for verifying environment variables are having the expected effect
    settings = Settings()
    print(settings.model_dump())
