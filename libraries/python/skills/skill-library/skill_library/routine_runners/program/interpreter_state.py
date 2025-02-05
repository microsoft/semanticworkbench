import pickle


class InterpreterState:
    """Container for serializable interpreter state."""

    def __init__(self, cache_data: bytes, transformed_code: str):
        self.cache_data = cache_data
        self.transformed_code = transformed_code

    def serialize(self) -> bytes:
        """Serialize the entire state to bytes."""
        return pickle.dumps({
            "cache_data": self.cache_data,
            "transformed_code": self.transformed_code,
        })

    @classmethod
    def deserialize(cls, data: bytes) -> "InterpreterState":
        """Create new InterpreterState from serialized data."""
        state_dict = pickle.loads(data)
        return cls(cache_data=state_dict["cache_data"], transformed_code=state_dict["transformed_code"])
