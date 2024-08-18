import hashlib
import logging
import re
import secrets as python_secrets
from typing import Protocol

import cachetools
import cachetools.keys
from azure.core.credentials_async import AsyncTokenCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient

from . import settings

logger = logging.getLogger(__name__)


class ApiKeyStore(Protocol):

    def generate_key_name(self, identifier: str) -> str: ...

    async def get(self, key_name: str) -> str | None: ...

    async def reset(self, key_name: str) -> str: ...

    async def delete(self, key_name: str) -> None: ...


class KeyVaultApiKeyStore(ApiKeyStore):
    """
    Stores API keys in Azure Key Vault.
    """

    def __init__(
        self,
        key_vault_url: str,
        identity: AsyncTokenCredential,
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

    async def get(self, key_name: str) -> str | None:
        try:
            secret = await self._secret_client.get_secret(name=key_name)
            return secret.value
        except ResourceNotFoundError:
            return None

    async def reset(self, key_name: str) -> str:
        new_api_key = generate_api_key()
        await self._secret_client.set_secret(name=key_name, value=new_api_key)
        return new_api_key

    async def delete(self, key_name: str) -> None:
        try:
            await self._secret_client.delete_secret(name=key_name)
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

    async def get(self, key_name: str) -> str | None:
        return self._api_key

    async def reset(self, key_name: str) -> str:
        return self._api_key

    async def delete(self, key_name: str) -> None:
        pass


def cached(api_key_store: ApiKeyStore, max_cache_size: int, ttl_seconds: float) -> ApiKeyStore:
    hash_key = cachetools.keys.hashkey
    cache = cachetools.TTLCache(maxsize=max_cache_size, ttl=ttl_seconds)

    original_get = api_key_store.get
    original_reset = api_key_store.reset
    original_delete = api_key_store.delete

    async def get(key_name: str) -> str | None:
        cache_key = hash_key(key_name)
        if secret := cache.get(cache_key):
            return secret

        secret = await original_get(key_name)
        if secret is not None:
            cache[cache_key] = secret
        return secret

    async def reset(key_name: str) -> str:
        secret = await original_reset(key_name)
        cache_key = hash_key(key_name)
        cache[cache_key] = secret
        return secret

    async def delete(key_name: str) -> None:
        cache_key = hash_key(key_name)
        cache.pop(cache_key, None)
        return await original_delete(key_name)

    api_key_store.get = get
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

        return cached(api_key_store=key_vault_store, max_cache_size=200, ttl_seconds=10 * 60)

    logger.info("creating FixedApiKeyStore for local development and testing")
    return FixedApiKeyStore(api_key="")


def generate_api_key(length: int = 32) -> str:
    return python_secrets.token_urlsafe(length)
