import logging
import pathlib
from typing import Any, Generic, TypeVar

from pydantic import (
    BaseModel,
    ValidationError,
)

from ..config import (
    ConfigSecretStrJsonSerializationMode,
    config_secret_str_serialization_context,
    get_ui_schema,
    replace_config_secret_str_masked_values,
)
from ..storage import read_model, write_model
from .context import AssistantContext, storage_directory_for_context
from .error import BadRequestError
from .protocol import (
    AssistantConfigDataModel,
    AssistantConfigProvider,
)

logger = logging.getLogger(__name__)

ConfigModelT = TypeVar("ConfigModelT", bound=BaseModel)


class BaseModelAssistantConfig(Generic[ConfigModelT]):
    """
    Assistant-config implementation that uses a BaseModel for default config.
    """

    def __init__(self, default_cls: type[ConfigModelT], other_templates: dict[str, type[ConfigModelT]] = {}) -> None:
        self._templates = {
            "default": default_cls,
        }

        if not other_templates:
            return

        for template_id, template_cls in other_templates.items():
            if template_id in self._templates:
                raise ValueError(f"Template {template_id} already exists")
            self._templates[template_id] = template_cls

    async def get(self, assistant_context: AssistantContext) -> ConfigModelT:
        path = self._private_path_for(assistant_context)

        if not path.exists():
            # if the config file hasn't been written yet, check the export/import path
            path = self._export_import_path_for(assistant_context)

        config = None
        try:
            config = read_model(path, self._templates[assistant_context._template_id])
        except ValidationError as e:
            logger.warning("exception reading config; path: %s", path, exc_info=e)

        return config or self._templates[assistant_context._template_id].model_construct()

    @property
    def provider(self) -> AssistantConfigProvider:
        class _ConfigProvider:
            def __init__(self, provider: BaseModelAssistantConfig[ConfigModelT]) -> None:
                self._provider = provider

            async def get(self, assistant_context: AssistantContext) -> AssistantConfigDataModel:
                config = await self._provider.get(assistant_context)
                errors = []
                try:
                    self._provider._templates[assistant_context._template_id].model_validate(config.model_dump())
                except ValidationError as e:
                    for error in e.errors(include_url=False):
                        errors.append(str(error))

                return self._provider._config_data_model_for(config, errors)

            async def set(self, assistant_context: AssistantContext, config: dict[str, Any]) -> None:
                try:
                    updated_config = self._provider._templates[assistant_context._template_id].model_validate(config)
                except ValidationError as e:
                    raise BadRequestError(str(e))

                # replace masked secret values with original values
                original_config = await self._provider.get(assistant_context)
                updated_config = replace_config_secret_str_masked_values(updated_config, original_config)

                await self._provider._set(assistant_context, updated_config)

            def default_for(self, template_id: str) -> AssistantConfigDataModel:
                # return the default config for the given assistant type
                config = self._provider._templates[template_id].model_construct()
                return self._provider._config_data_model_for(config)

        return _ConfigProvider(self)

    def _private_path_for(self, assistant_context: AssistantContext) -> pathlib.Path:
        # store assistant config, including secrets, in a separate partition that is never exported
        return storage_directory_for_context(assistant_context, partition="private") / "config.json"

    def _export_import_path_for(self, assistant_context: AssistantContext) -> pathlib.Path:
        # store a copy of the config for export in the standard partition
        return storage_directory_for_context(assistant_context) / "config.json"

    async def _set(self, assistant_context: AssistantContext, config: ConfigModelT) -> None:
        # save the config with secrets serialized with their actual values for the assistant
        write_model(
            self._private_path_for(assistant_context),
            config,
            serialization_context=config_secret_str_serialization_context(
                ConfigSecretStrJsonSerializationMode.serialize_value
            ),
        )
        # save a copy of the config for export, with secret fields set to empty strings
        write_model(
            self._export_import_path_for(assistant_context),
            config,
            serialization_context=config_secret_str_serialization_context(
                ConfigSecretStrJsonSerializationMode.serialize_as_empty
            ),
        )

    @staticmethod
    def _config_data_model_for(config: ConfigModelT, errors: list[str] | None = None) -> AssistantConfigDataModel:
        return AssistantConfigDataModel(
            config=config.model_dump(mode="json"),
            errors=errors,
            json_schema=type(config).model_json_schema(),
            ui_schema=get_ui_schema(type(config)),
        )
