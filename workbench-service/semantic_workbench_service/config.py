import os

import dotenv
from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .files import StorageSettings
from .logging_config import LoggingSettings


def first_env_var(*env_vars: str, include_upper_and_lower: bool = True, include_dot_env: bool = True) -> str | None:
    """
    Get the first environment variable that is set.

    Args:
        include_upper_and_lower: if True, then the UPPER and lower case versions of the env vars will be checked.
        include_dot_env: if True, then the .env file will be checked for the env vars after the os.
    """
    if include_upper_and_lower:
        env_vars = (*env_vars, *[env_var.upper() for env_var in env_vars], *[env_var.lower() for env_var in env_vars])

    for env_var in env_vars:
        if env_var in os.environ:
            return os.environ[env_var]

    if not include_dot_env:
        return None

    dotenv_path = dotenv.find_dotenv(usecwd=True)
    if not dotenv_path:
        return None

    dot_env_values = dotenv.dotenv_values(dotenv_path)
    for env_var in env_vars:
        if env_var in dot_env_values:
            return dot_env_values[env_var]

    return None


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
    allowed_app_ids: set[str] = {"22cb77c3-ca98-4a26-b4db-ac4dcecba690"}


class WebServiceSettings(BaseSettings):
    protocol: str = "http"
    host: str = "127.0.0.1"
    port: int = 3000

    assistant_api_key: ApiKeySettings = ApiKeySettings()

    anonymous_paths: list[str] = ["/", "/docs", "/openapi.json"]

    assistant_service_online_check_interval_seconds: float = 10.0


class WorkflowSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="workflow__", env_nested_delimiter="_", env_file=".env", extra="allow")

    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4-turbo"
    azure_openai_api_version: str = "2023-05-15"


class AzureSpeechSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="azure_speech__", env_nested_delimiter="_", env_file=".env", extra="allow"
    )

    resource_id: str = ""
    region: str = "westus2"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="workbench__", env_nested_delimiter="__", env_file=".env", extra="allow"
    )

    db: DBSettings = DBSettings()
    storage: StorageSettings = StorageSettings()
    logging: LoggingSettings = LoggingSettings()
    service: WebServiceSettings = WebServiceSettings()
    workflow: WorkflowSettings = WorkflowSettings()
    azure_speech: AzureSpeechSettings = AzureSpeechSettings()
    auth: AuthSettings = AuthSettings()


if __name__ == "__main__":
    # for verifying environment variables are having the expected effect
    settings = Settings()
    print(settings.model_dump())
