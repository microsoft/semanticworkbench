import hashlib
import logging
import re
import secrets as python_secrets
import uuid
from typing import Protocol

import cachetools
import cachetools.keys
from azure.core.credentials import TokenCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from . import settings

logger = logging.getLogger(__name__)


class ApiKeyStore(Protocol):

    def generate_key_name(self, identifier: str) -> str: ...

    def get(self, key_name: str) -> str | None: ...

    def reset(self, key_name: str) -> str: ...

    def delete(self, key_name: str) -> None: ...


class KeyVaultApiKeyStore(ApiKeyStore):
    """
    Stores API keys in Azure Key Vault.
    """

    def __init__(
        self,
        key_vault_url: str,
        identity: TokenCredential,
    ) -> None:
        self._secret_client = SecretClient(vault_url=key_vault_url, credential=identity)

    def generate_key_name(self, identifier: str) -> str:
        """
        Generates unique secret name, derived from the identifier, that matches requirements for KeyVault.
        https://azure.github.io/PSRule.Rules.Azure/en/rules/Azure.KeyVault.SecretName/
        - Between 1 and 127 characters long.
        - Alphanumerics and hyphens (dash).
        """
        prefix = "api-key-"
        service_id_hash = hashlib.sha256(identifier.encode()).hexdigest()
        suffix = f"-{service_id_hash}"
        identifier_label_max_length = 127 - len(prefix) - len(suffix)
        identifier_label = re.sub(r"[^a-z0-9-]", "-", identifier)[:identifier_label_max_length]
        secret_name = f"{prefix}{identifier_label}{suffix}"
        assert re.match(r"^[a-z0-9-]{1,127}$", secret_name)
        return secret_name

    def get(self, key_name: str) -> str | None:
        try:
            return self._secret_client.get_secret(name=key_name).value
        except ResourceNotFoundError:
            return None

    def reset(self, key_name: str, tags: dict[str, str] = {}) -> str:
        new_api_key = generate_api_key()
        self._secret_client.set_secret(name=key_name, value=new_api_key, tags=tags)
        return new_api_key

    def delete(self, key_name: str) -> None:
        try:
            self._secret_client.begin_delete_secret(name=key_name).wait()
        except ResourceNotFoundError:
            pass


class FixedApiKeyStore(ApiKeyStore):
    """
    API key store for local development and testing that always returns the same key. Not suitable for production.
    """

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def generate_key_name(self, identifier: str) -> str:
        return identifier

    def get(self, key_name: str) -> str | None:
        return self._api_key

    def reset(self, key_name: str) -> str:
        return self._api_key

    def delete(self, key_name: str) -> None:
        pass


def cached(api_key_store: ApiKeyStore, max_cache_size: int, ttl_seconds: float) -> ApiKeyStore:
    cache_key = cachetools.keys.hashkey
    cache = cachetools.TTLCache(maxsize=max_cache_size, ttl=ttl_seconds)

    api_key_store.get = cachetools.cached(cache=cache, key=cache_key)(api_key_store.get)

    original_reset = api_key_store.reset
    original_delete = api_key_store.delete

    def reset(*args, **kwargs) -> str:
        cache.pop(cache_key(*args, **kwargs), None)
        return original_reset(*args, **kwargs)

    def delete(*args, **kwargs) -> None:
        cache.pop(cache_key(*args, **kwargs), None)
        return original_delete(*args, **kwargs)

    api_key_store.reset = reset
    api_key_store.delete = delete

    return api_key_store


def get_store() -> ApiKeyStore:
    if settings.service.assistant_api_key.is_secured:
        logger.info("creating KeyVaultApiKeyStore; key vault url: %s", settings.service.assistant_api_key.key_vault_url)
        key_vault_store = KeyVaultApiKeyStore(
            key_vault_url=str(settings.service.assistant_api_key.key_vault_url),
            identity=DefaultAzureCredential(),
        )

        # ensure that the key vault is accessible
        assert key_vault_store.get(f"non-existing-key-{uuid.uuid4().hex}") is None

        return cached(api_key_store=key_vault_store, max_cache_size=200, ttl_seconds=10 * 60)

    logger.info("creating FixedApiKeyStore for local development and testing")
    return FixedApiKeyStore(api_key="")


def generate_api_key(length: int = 32) -> str:
    return python_secrets.token_urlsafe(length)
