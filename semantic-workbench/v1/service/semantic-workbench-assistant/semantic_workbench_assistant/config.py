import os
from typing import Annotated, Literal, TypeVar

import dotenv
from pydantic import AliasChoices, BaseModel, Field, HttpUrl
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
    workbench_service_ping_interval_seconds: float = 10.0

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


ModelT = TypeVar("ModelT", bound=BaseModel)


def first_env_var(*env_vars: str, include_dotenv: bool = True, include_upper_and_lower: bool = True) -> str | None:
    """
    Get the first environment variable that is set. If include_dotenv is True, then
    the dotenv values will be checked as well. If include_upper_and_lower is True,
    then the upper and lower case versions of the env vars will also be checked.

    .. warning::
        The dotenv values may be cached in the environment, so if you have loaded
        a .env file into the environment, you may need to 'stop' and then 'start' the
        service to get the new values from the .env file. Using the 'restart' command
        does not seem to work.
    """
    if include_upper_and_lower:
        env_vars = (*env_vars, *[env_var.upper() for env_var in env_vars], *[env_var.lower() for env_var in env_vars])

    dotenv_values = {}
    # load dotenv values if requested
    if include_dotenv:
        dotenv_values = dotenv.dotenv_values()

    # check for the first env var that is set
    # prioritize the environment over dotenv values
    for env_var in env_vars:
        # check for the env var in the environment
        if env_var in os.environ:
            return os.environ[env_var]

        # check for the env var in the dotenv values
        if env_var in dotenv_values:
            return dotenv_values[env_var]

    return None


def overwrite_defaults_from_env(model: ModelT, prefix="", separator="__") -> ModelT:
    """
    Overwrite string fields that currently have their default values. Values are
    overwritten with values from environment variables or .env file. If a field
    is a BaseModel, it will be recursively updated.
    """

    non_defaults = model.model_dump(exclude_defaults=True).keys()

    updates: dict[str, str | BaseModel] = {}

    for field, field_info in model.model_fields.items():
        value = getattr(model, field)
        env_var = f"{prefix}{separator}{field}".upper()

        match value:
            case BaseModel():
                updates[field] = overwrite_defaults_from_env(value, prefix=env_var, separator=separator)
                continue

            case str() | (str() | None):
                if field in non_defaults:
                    continue

                alias_env_vars = []
                match field_info.validation_alias:
                    case None:
                        pass

                    case str():
                        alias_env_vars = [
                            f"{prefix}{separator}{field_info.validation_alias}".upper(),
                            field_info.validation_alias.upper(),
                        ]

                    case _:
                        aliases = field_info.validation_alias.convert_to_aliases()
                        for alias in aliases:
                            if isinstance(alias, list) and isinstance(alias[0], str):
                                alias_env_vars.append(f"{prefix}{separator}{alias[0]}".upper())
                                alias_env_vars.append(str(alias[0]).upper())

                env_value = first_env_var(env_var, *alias_env_vars)
                if env_value is not None:
                    updates[field] = env_value

            case _:
                continue

    return model.model_copy(update=updates, deep=True)