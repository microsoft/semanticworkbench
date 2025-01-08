# Copyright (c) Microsoft. All rights reserved.


import math
import time
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .logging import logger


class ResourceConstraintUnit(StrEnum):
    """
    Choose the unit of the resource constraint. Seconds and Minutes are
    real-time and will be impacted by the latency of the model.
    """

    SECONDS = "seconds"
    MINUTES = "minutes"
    TURNS = "turns"


class ResourceConstraintMode(StrEnum):
    """
    Choose how the agent should use the resource.

    Maximum: is an upper bound, i.e. the agent can end the conversation before
    the resource is exhausted.

    Exact: The agent should aim to use exactly the given amount of the resource.
    """

    MAXIMUM = "maximum"
    EXACT = "exact"


class ResourceConstraint(BaseModel):
    """
    A structured representation of the resource constraint for the
    GuidedConversation agent.
    """

    mode: ResourceConstraintMode = Field(default=ResourceConstraintMode.MAXIMUM)
    quantity: float | int
    unit: ResourceConstraintUnit = Field(default=ResourceConstraintUnit.TURNS)


class ConversationResource(BaseModel):
    """
    Resource constraints for the GuidedConversation agent. This class is used to
    keep track of the resource constraints. If resource_constraint is None, then
    the agent can continue indefinitely. This also means that no agenda will be
    created for the conversation.
    """

    resource_constraint: Optional[ResourceConstraint] = Field(default=None)
    turn_number: int = Field(default=0)
    elapsed_units: float = Field(default=0.0)
    remaining_units: float = Field(default=None, validate_default=True)
    initial_seconds_per_turn: int = Field(default=120)

    @field_validator("remaining_units", mode="before")
    @classmethod
    def set_remaining_units(
        cls,
        value,
        info,
    ):
        constraint = info.data.get("resource_constraint")
        if constraint is not None:
            if value is not None:
                return value
            else:
                return constraint.quantity
        else:
            return 0.0

    def start_resource(self) -> None:
        """To be called at the start of a conversation turn."""
        if self.resource_constraint is not None and (
            self.resource_constraint.unit == ResourceConstraintUnit.SECONDS
            or self.resource_constraint.unit == ResourceConstraintUnit.MINUTES
        ):
            self.start_time = time.time()

    def increment_resource(self) -> None:
        """Increment the resource counter by one turn."""
        if self.resource_constraint is not None:
            match self.resource_constraint.unit:
                case ResourceConstraintUnit.SECONDS:
                    self.elapsed_units += time.time() - self.start_time
                    self.remaining_units = self.resource_constraint.quantity - self.elapsed_units
                case ResourceConstraintUnit.MINUTES:
                    self.elapsed_units += (time.time() - self.start_time) / 60
                    self.remaining_units = self.resource_constraint.quantity - self.elapsed_units
                case ResourceConstraintUnit.TURNS:
                    self.elapsed_units += 1
                    self.remaining_units -= 1
        self.turn_number += 1

    def get_resource_mode(self) -> ResourceConstraintMode | None:
        """
        Get the mode of the resource constraint.
        """
        return None if self.resource_constraint is None else self.resource_constraint.mode

    def estimate_remaining_turns(self) -> int:
        """
        Estimate the remaining turns based on the resource constraint, thereby
        translating certain resource units (e.g. seconds, minutes) into turns.
        """
        if self.resource_constraint is None:
            logger.error(
                "Resource constraint is not set, so turns cannot be estimated using function estimate_remaining_turns"
            )
            raise ValueError(
                "Resource constraint is not set. Do not try to call this method without a resource constraint."
            )

        match self.resource_constraint.unit:
            case ResourceConstraintUnit.MINUTES:
                if self.turn_number == 0:
                    time_per_turn = self.initial_seconds_per_turn
                else:
                    time_per_turn = (self.elapsed_units * 60) / self.turn_number
                time_per_turn /= 60
                remaining_turns = self.remaining_units / time_per_turn
                if remaining_turns < 1:
                    return math.ceil(remaining_turns)
                else:
                    return math.floor(remaining_turns)

            case ResourceConstraintUnit.SECONDS:
                if self.turn_number == 0:
                    time_per_turn = self.initial_seconds_per_turn
                else:
                    time_per_turn = self.elapsed_units / self.turn_number
                remaining_turns = self.remaining_units / time_per_turn
                if remaining_turns < 1:
                    return math.ceil(remaining_turns)
                else:
                    return math.floor(remaining_turns)

            case ResourceConstraintUnit.TURNS:
                return int(self.resource_constraint.quantity - self.turn_number)

            case _:
                raise ValueError("Invalid resource unit provided.")
