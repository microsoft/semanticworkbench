# Define an Exception class for no share found
class NoShareFoundError(Exception):
    """Exception raised when no active knowledge package is found."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


NoShareException = NoShareFoundError("No active share found.")


class NoUserFoundError(Exception):
    """Exception raised when no user is found in the context."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


NoUserException = NoUserFoundError("No user found in the context.")
