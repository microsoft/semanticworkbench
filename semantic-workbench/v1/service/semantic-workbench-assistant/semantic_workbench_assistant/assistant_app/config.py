import logging
import pathlib
from typing import Annotated, Any, Generic, TypeVar

import deepmerge
from pydantic import (
    BaseModel,
    ValidationError,
    create_model,
)

from ..config import ENABLE_SECRET_MASKING_CONTEXT_KEY, UISchema, get_ui_schema
from ..storage import read_model, write_model
from .context import AssistantContext, FileStorageContext
from .error import BadRequestError
from .protocol import (
    AssistantConfigDataModel,
    AssistantConfigProvider,
)

logger = logging.getLogger(__name__)

ConfigModelT = TypeVar("ConfigModelT", bound=BaseModel)
ConfigSecretsModelT = TypeVar("ConfigSecretsModelT", bound=BaseModel)


class BaseModelAssistantConfig(Generic[ConfigModelT]):
    """
    Assistant-config implementation that uses a BaseModel for default config.
    """

    def __init__(self, default: ConfigModelT | type[ConfigModelT], ui_schema: dict[str, Any] = {}) -> None:
        default = default() if isinstance(default, type) else default
        self._default = default
        self._ui_schema = deepmerge.always_merger.merge(get_ui_schema(default.__class__), ui_schema)

    def _path_for(self, assistant_context: AssistantContext) -> pathlib.Path:
        return FileStorageContext.get(assistant_context).directory / "config.bin"

    async def get(self, assistant_context: AssistantContext) -> ConfigModelT:
        path = self._path_for(assistant_context)
        try:
            config = read_model(path, self._default.__class__)
        except ValidationError as e:
            logger.warning("exception reading config; path: %s", path, exc_info=e)

        return config or self._default

    async def _set(self, assistant_context: AssistantContext, config: ConfigModelT) -> None:
        write_model(self._path_for(assistant_context), config)

    @property
    def provider(self) -> AssistantConfigProvider:
        class _ConfigProvider:
            def __init__(self, provider: BaseModelAssistantConfig) -> None:
                self._provider = provider

            async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel:
                config = await self._provider.get(assistant_context)
                return AssistantConfigDataModel(
                    config=config.model_dump(mode="json"),
                    json_schema=config.model_json_schema(),
                    ui_schema=self._provider._ui_schema,
                )

            async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None:
                try:
                    updated_config = self._provider._default.model_validate(config)
                except ValidationError as e:
                    raise BadRequestError(str(e))

                await self._provider._set(assistant_context, updated_config)

        return _ConfigProvider(self)


class BaseModelAssistantConfigWithSecrets(Generic[ConfigModelT, ConfigSecretsModelT]):
    """
    Assistant-config implementation that uses a BaseModel for default config.
    """

    def __init__(
        self,
        default: ConfigModelT | type[ConfigModelT],
        default_secrets: ConfigSecretsModelT | type[ConfigSecretsModelT],
        ui_schema: dict[str, Any] = {},
        ui_schema_secrets: dict[str, Any] = {},
    ) -> None:
        default = default() if isinstance(default, type) else default
        self._default = default
        default_secrets = default_secrets() if isinstance(default_secrets, type) else default_secrets
        self._default_secrets = default_secrets
        self._ui_schema = deepmerge.always_merger.merge(get_ui_schema(default.__class__), ui_schema)
        self._ui_schema_secrets = deepmerge.always_merger.merge(
            get_ui_schema(default_secrets.__class__), ui_schema_secrets
        )

    def _path_for(self, assistant_context: AssistantContext) -> pathlib.Path:
        return FileStorageContext.get(assistant_context).directory / "config.bin"

    def _path_for_secrets(self, assistant_context: AssistantContext) -> pathlib.Path:
        return FileStorageContext.get(assistant_context, partition="secret").directory / "config.bin"

    async def get(self, assistant_context: AssistantContext) -> ConfigModelT:
        path = self._path_for(assistant_context)
        try:
            config = read_model(path, self._default.__class__)
        except ValidationError as e:
            logger.warning("exception reading config; path: %s", path, exc_info=e)

        return config or self._default

    async def get_secrets(self, assistant_context: AssistantContext) -> ConfigSecretsModelT:
        path = self._path_for_secrets(assistant_context)
        try:
            config_secrets = read_model(path, self._default_secrets.__class__)
        except ValidationError as e:
            logger.warning("exception reading config; path: %s", path, exc_info=e)

        return config_secrets or self._default_secrets

    async def _set(self, assistant_context: AssistantContext, config: ConfigModelT) -> None:
        write_model(self._path_for(assistant_context), config)

    async def _set_secrets(self, assistant_context: AssistantContext, config: ConfigSecretsModelT) -> None:
        write_model(
            self._path_for_secrets(assistant_context),
            config,
            serialization_context={ENABLE_SECRET_MASKING_CONTEXT_KEY: False},
        )

    @property
    def provider(self) -> AssistantConfigProvider:
        class _ConfigProvider:
            def __init__(
                self,
                provider: BaseModelAssistantConfigWithSecrets[ConfigModelT, ConfigSecretsModelT],
                config_type: type[ConfigModelT],
                config_secrets_type: type[ConfigSecretsModelT],
            ) -> None:
                self._provider = provider
                self._config_type = config_type
                self._config_secrets_type = config_secrets_type

            async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel:
                config = await self._provider.get(assistant_context)
                config_secrets = await self._provider.get_secrets(assistant_context)

                combined_config_model = create_model(
                    "CombinedConfigModel",
                    config=(
                        Annotated[self._config_type, UISchema(hide_title=not config.model_config.get("title"))],
                        ...,
                    ),
                    config_secrets=(
                        Annotated[
                            self._config_secrets_type, UISchema(hide_title=not config_secrets.model_config.get("title"))
                        ],
                        ...,
                    ),
                )

                combined_config = combined_config_model(config=config, config_secrets=config_secrets)
                combined_ui_schema = get_ui_schema(combined_config_model)

                return AssistantConfigDataModel(
                    config=combined_config.model_dump(mode="json"),
                    json_schema=combined_config.model_json_schema(),
                    ui_schema=combined_ui_schema,
                )

            async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None:
                try:
                    updated_config = self._provider._default.model_validate(config.get("config", {}))
                except ValidationError as e:
                    raise BadRequestError(str(e))
                await self._provider._set(assistant_context, updated_config)

                try:
                    updated_config_secrets = self._provider._default_secrets.model_validate(
                        config.get("config_secrets", {})
                    )
                except ValidationError as e:
                    raise BadRequestError(str(e))
                await self._provider._set_secrets(assistant_context, updated_config_secrets)

        return _ConfigProvider(self, self._default.__class__, self._default_secrets.__class__)
