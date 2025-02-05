import pickle
from typing import Any, Dict


class FunctionCache:
    """Cache for function results based on arguments."""

    def __init__(self):
        self.cache: Dict[str, Dict[tuple, Any]] = {}

    @classmethod
    def make_hashable(cls, obj: Any) -> Any:
        """Convert a potentially unhashable object into a hashable one."""
        if isinstance(obj, dict):
            return tuple((cls.make_hashable(k), cls.make_hashable(v)) for k, v in sorted(obj.items()))
        elif isinstance(obj, (list, set)):
            return tuple(cls.make_hashable(x) for x in obj)
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # For other types, we'll use their string representation
            # This is a fallback and might not be perfect for all cases
            return str(obj)

    @classmethod
    def get_cache_key(cls, args: tuple, kwargs: Dict[str, Any]) -> tuple:
        """Create a cache key from args and kwargs."""
        hashable_args = tuple(cls.make_hashable(arg) for arg in args)
        hashable_kwargs = tuple((k, cls.make_hashable(v)) for k, v in sorted(kwargs.items()))
        return hashable_args + hashable_kwargs

    def get(self, func_name: str, args: tuple, kwargs: Dict[str, Any]) -> Any:
        """Get cached result for function call if it exists."""
        if func_name not in self.cache:
            raise KeyError(f"No cache for function {func_name}")

        cache_key = self.get_cache_key(args, kwargs)
        if cache_key not in self.cache[func_name]:
            raise KeyError(f"No cached result for {func_name} with args {args}, kwargs {kwargs}")

        return self.cache[func_name][cache_key]

    def set(self, func_name: str, args: tuple, kwargs: Dict[str, Any], result: Any) -> None:
        """Cache result for function call."""
        if func_name not in self.cache:
            self.cache[func_name] = {}

        cache_key = self.get_cache_key(args, kwargs)
        self.cache[func_name][cache_key] = result

    def set_with_cache_key(self, func_name: str, cache_key: tuple, result: Any) -> None:
        """Cache result for function call with a precomputed cache key."""
        if func_name not in self.cache:
            self.cache[func_name] = {}

        self.cache[func_name][cache_key] = result

    def serialize(self) -> bytes:
        """Serialize the cache to bytes."""
        return pickle.dumps(self.cache)

    @classmethod
    def deserialize(cls, data: bytes) -> "FunctionCache":
        """Create a new FunctionCache from serialized data."""
        instance = cls()
        instance.cache = pickle.loads(data)
        return instance
