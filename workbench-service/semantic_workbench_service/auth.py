import uuid
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status


@dataclass
class AssistantServicePrincipal:
    assistant_service_id: str


@dataclass
class UserPrincipal:
    user_id: str
    name: str


@dataclass
class AssistantPrincipal(AssistantServicePrincipal):
    assistant_id: uuid.UUID


class ServiceUserPrincipal(UserPrincipal):
    pass


Principal = UserPrincipal | AssistantServicePrincipal

authenticated_principal: ContextVar[Principal | None] = ContextVar("request_principal", default=None)


def _request_principal() -> Principal:
    # the principal is stored in the request state by middle-ware
    principal = authenticated_principal.get()
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return principal


DependsPrincipal = Annotated[Principal, Depends(_request_principal)]


ActorPrincipal = UserPrincipal | AssistantPrincipal


def _actor_principal(principal: DependsPrincipal) -> ActorPrincipal:
    if not isinstance(principal, ActorPrincipal):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return principal


DependsActorPrincipal = Annotated[ActorPrincipal, Depends(_actor_principal)]


def _user_principal(principal: DependsPrincipal) -> UserPrincipal:
    if isinstance(principal, UserPrincipal):
        return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def _assistant_service_principal(principal: DependsPrincipal) -> AssistantServicePrincipal:
    if isinstance(principal, AssistantServicePrincipal):
        return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


def _assistant_principal(principal: DependsPrincipal) -> AssistantPrincipal:
    if isinstance(principal, AssistantPrincipal):
        return principal
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


DependsAssistantServicePrincipal = Annotated[AssistantServicePrincipal, Depends(_assistant_service_principal)]
DependsAssistantPrincipal = Annotated[AssistantPrincipal, Depends(_assistant_principal)]
DependsUserPrincipal = Annotated[UserPrincipal, Depends(_user_principal)]
