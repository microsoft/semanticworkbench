import time
import uuid

from semantic_workbench_service.assistant_api_key import ApiKeyStore, cached


class MockApiKeyStore(ApiKeyStore):

    def __init__(self) -> None:
        self._api_keys: dict[str, str] = {}

    def override_api_key(self, key_name: str, api_key: str):
        self._api_keys[key_name] = api_key

    def generate_key_name(self, identifier: str) -> str:
        return identifier

    async def get(self, key_name: str) -> str | None:
        return self._api_keys.get(key_name)

    async def reset(self, key_name: str) -> str:
        new_key = uuid.uuid4().hex
        self._api_keys[key_name] = new_key
        return new_key

    async def delete(self, key_name: str) -> None:
        self._api_keys.pop(key_name, None)


async def test_cached_api_key_store():
    ttl_seconds = 0.5
    mock_store = MockApiKeyStore()
    cached_store = cached(api_key_store=mock_store, max_cache_size=200, ttl_seconds=ttl_seconds)

    key_name = "key"

    # set and get initial api key
    api_key = uuid.uuid4().hex
    mock_store.override_api_key(key_name=key_name, api_key=api_key)

    assert (await cached_store.get(key_name=key_name)) == api_key

    # update key on the "backend"
    updated_api_key = uuid.uuid4().hex
    mock_store.override_api_key(key_name=key_name, api_key=updated_api_key)

    # ensure that the old value is still returned
    assert (await cached_store.get(key_name=key_name)) == api_key

    # ensure that reset returns the new value
    reset_api_key = await cached_store.reset(key_name=key_name)
    assert reset_api_key != updated_api_key
    assert (await cached_store.get(key_name=key_name)) == reset_api_key

    # ensure that delete removes the item from the cache
    await cached_store.delete(key_name=key_name)
    assert (await cached_store.get(key_name=key_name)) is None

    # delete again, this time updating the value on the "backend" before getting
    await cached_store.delete(key_name=key_name)
    mock_store.override_api_key(key_name=key_name, api_key=updated_api_key)
    assert (await cached_store.get(key_name=key_name)) == updated_api_key

    # ensure that the cache is cleared after the TTL
    another_updated_api_key = uuid.uuid4().hex
    mock_store.override_api_key(key_name=key_name, api_key=another_updated_api_key)
    assert (await cached_store.get(key_name=key_name)) == updated_api_key
    time.sleep(ttl_seconds)

    assert (await cached_store.get(key_name=key_name)) == another_updated_api_key

    # ensure that a different key has an isolated cache
    second_key_name = "second_key"
    second_api_key = await cached_store.reset(key_name=second_key_name)
    assert await cached_store.get(key_name=second_key_name) == second_api_key
    mock_store.override_api_key(key_name=second_key_name, api_key=uuid.uuid4().hex)
    assert await cached_store.get(key_name=second_key_name) == second_api_key

    assert await cached_store.get(key_name=key_name) == another_updated_api_key