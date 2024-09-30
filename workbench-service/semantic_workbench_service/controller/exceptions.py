from typing import Annotated, Any

from fastapi import HTTPException
from typing_extensions import Doc


class Error(HTTPException):
    pass


class RuntimeError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=500, detail=detail)


class NotFoundError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=404, detail=detail)


class ConflictError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=409, detail=detail)


class InvalidArgumentError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=400, detail=detail)


class ForbiddenError(Error):
    def __init__(
        self,
        detail: Annotated[
            Any,
            Doc("""
                Any data to be sent to the client in the `detail` key of the JSON
                response.
                """),
        ] = None,
    ) -> None:
        super().__init__(status_code=403, detail=detail)
