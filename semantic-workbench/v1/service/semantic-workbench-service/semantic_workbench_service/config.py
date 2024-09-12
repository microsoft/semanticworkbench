from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .files import StorageSettings
from .logging_config import LoggingSettings


class DBSettings(BaseSettings):
    url: str = "sqlite:///.data/workbench.db"
    echosql: bool = False
    postgresql_ssl_mode: str = "require"
    postgresql_pool_size: int = 10
    migrate_on_startup: bool = True
    alembic_root_path: str = "./"


class ApiKeySettings(BaseSettings):
    key_vault_url: HttpUrl | None = None

    @property
    def is_secured(self) -> bool:
        return self.key_vault_url is not None


class WebServiceSettings(BaseSettings):
    protocol: str = "http"
    hostname: str = "127.0.0.1"
    port: int | None = 3000

    assistant_api_key: ApiKeySettings = ApiKeySettings()

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    assistant_service_online_check_interval_seconds: float = 10.0


class WorkflowSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="workflow__", env_nested_delimiter="_", env_file=".env", extra="allow")

    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4-turbo"
    azure_openai_api_version: str = "2023-05-15"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="workbench__", env_nested_delimiter="__", env_file=".env", extra="allow"
    )

    db: DBSettings = DBSettings()
    storage: StorageSettings = StorageSettings()
    logging: LoggingSettings = LoggingSettings()
    service: WebServiceSettings = WebServiceSettings()
    workflow: WorkflowSettings = WorkflowSettings()


if __name__ == "__main__":
    # for verifying environment variables are having the expected effect
    settings = Settings()
    print(settings.model_dump())
