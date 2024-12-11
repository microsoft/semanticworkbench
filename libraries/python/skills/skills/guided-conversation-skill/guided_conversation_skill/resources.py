# Copyright (c) Microsoft. All rights reserved.


import math
import time
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field

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

    mode: ResourceConstraintMode
    quantity: float | int
    unit: ResourceConstraintUnit

    # class Config:
    #     arbitrary_types_allowed = True


def format_resource(quantity: float, unit: ResourceConstraintUnit) -> str:
    """
    Get formatted string for a given quantity and unit (e.g. 1 second, 20
    seconds)
    """
    if unit != ResourceConstraintUnit.TURNS:
        quantity = round(quantity, 1)
    if quantity == 1:
        return f"{quantity} {unit.value.rstrip('s')}"
    else:
        return f"{quantity} {unit.value}"


class GCResourceData(BaseModel):
    """
    Data class for GCResource. This class is used to store the data of the
    GCResource class.
    """

    resource_constraint: Optional[ResourceConstraint] = Field(default=None)
    turn_number: int = Field(default=0)
    elapsed_units: float = Field(default=0)
    remaining_units: float = Field(default=0.0)
    initial_seconds_per_turn: int = Field(default=120)


class GCResource:
    """
    Resource constraints for the GuidedConversation agent. This class is used to
    keep track of the resource constraints. If resource_constraint is None, then
    the agent can continue indefinitely. This also means that no agenda will be
    created for the conversation.

    Args:
        resource_constraint (ResourceConstraint | None): The resource constraint
        for the conversation.

        initial_seconds_per_turn (int): The initial number of seconds per turn.
        Defaults to 120 seconds.
    """

    def __init__(
        self,
        resource_constraint: ResourceConstraint | None = None,
        turn_number: int = 0,
        elapsed_units: float = 0,
        remaining_units: float | None = None,
        initial_seconds_per_turn: int = 120,
    ):
        self.resource_constraint = resource_constraint
        self.turn_number = turn_number

        # This is only used on the first turn.
        self.initial_seconds_per_turn: int = initial_seconds_per_turn

        if resource_constraint is not None:
            # If a resource constraint is given, then the initial remaining_units
            # should be the quantity of the resource constraint.
            self.elapsed_units = elapsed_units
            if remaining_units is None:
                self.remaining_units = resource_constraint.quantity
            else:
                self.remaining_units = remaining_units
        else:
            # If there is no resource constraint, then these should all be zero.
            self.elapsed_units = elapsed_units
            self.remaining_units = 0

    @classmethod
    def from_data(cls, data: GCResourceData) -> "GCResource":
        return cls(
            resource_constraint=data.resource_constraint,
            turn_number=data.turn_number,
            elapsed_units=data.elapsed_units,
            remaining_units=data.remaining_units,
            initial_seconds_per_turn=data.initial_seconds_per_turn,
        )

    def to_data(self) -> GCResourceData:
        return GCResourceData(
            resource_constraint=self.resource_constraint,
            turn_number=self.turn_number,
            elapsed_units=self.elapsed_units,
            remaining_units=self.remaining_units,
            initial_seconds_per_turn=self.initial_seconds_per_turn,
        )

    def to_json(self) -> dict:
        return {
            "turn_number": self.turn_number,
            "remaining_units": self.remaining_units,
            "elapsed_units": self.elapsed_units,
        }

    @classmethod
    def from_json(
        cls,
        json_data: dict,
    ) -> "GCResource":
        gc_resource = cls(
            resource_constraint=None,
            initial_seconds_per_turn=120,
        )
        gc_resource.turn_number = json_data["turn_number"]
        gc_resource.remaining_units = json_data["remaining_units"]
        gc_resource.elapsed_units = json_data["elapsed_units"]
        return gc_resource

    def start_resource(self) -> None:
        """To be called at the start of a conversation turn"""
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
                case _:
                    raise ValueError("Invalid resource unit provided.")
        self.turn_number += 1

    def get_resource_mode(self) -> ResourceConstraintMode | None:
        """
        Get the mode of the resource constraint.
        """
        if self.resource_constraint is None:
            return None
        return self.resource_constraint.mode

    def get_elapsed_turns(self, formatted_repr: bool = False) -> str | int:
        """
        Get the number of elapsed turns.

        Args:
            formatted_repr (bool): If true, return a formatted string
            representation of the elapsed turns. If false, return an integer.
            Defaults to False.

        Returns:
            str | int: The description/number of elapsed turns.
        """
        if formatted_repr:
            return format_resource(self.turn_number, ResourceConstraintUnit.TURNS)
        else:
            return self.turn_number

    def estimate_remaining_turns_formatted(self) -> str:
        """
        Get the number of remaining turns in a formatted string.
        """
        return format_resource(self.estimate_remaining_turns(), ResourceConstraintUnit.TURNS)

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

    def get_resource_instructions(self) -> str:
        """Get the resource instructions for the conversation.

        Assumes we're always using turns as the resource unit.

        Returns:
            str: the resource instructions
        """
        if self.resource_constraint is None:
            return ""

        formatted_elapsed_resource = format_resource(self.elapsed_units, ResourceConstraintUnit.TURNS)
        formatted_remaining_resource = format_resource(self.remaining_units, ResourceConstraintUnit.TURNS)

        # if the resource quantity is anything other than 1, the resource unit should be plural (e.g. "minutes" instead of "minute")
        is_plural_elapsed = self.elapsed_units != 1
        is_plural_remaining = self.remaining_units != 1

        if self.elapsed_units > 0:
            resource_instructions = f"So far, {formatted_elapsed_resource} {'have' if is_plural_elapsed else 'has'} elapsed since the conversation began. "
        else:
            resource_instructions = ""

        if self.resource_constraint.mode == ResourceConstraintMode.EXACT:
            exact_mode_instructions = (
                f"There {'are' if is_plural_remaining else 'is'} {formatted_remaining_resource} "
                "remaining (including this one) - the conversation will automatically terminate "
                "when 0 turns are left. You should continue the conversation until it is "
                "automatically terminated. This means you should NOT preemptively end the "
                'conversation, either explicitly (by selecting the "End conversation" action) '
                "or implicitly (e.g. by telling the user that you have all required information "
                "and they should wait for the next step). Your goal is not to maximize efficiency "
                "(i.e. complete the artifact as quickly as possible then end the conversation), "
                "but rather to make the best use of ALL remaining turns available to you"
            )

            if is_plural_remaining:
                resource_instructions += f"""{exact_mode_instructions}. This will require you to plan your actions carefully using the agenda: you want to avoid the situation where you have to pack too many topics into the final turns because you didn't account for them earlier, \
or where you've rushed through the conversation and all fields are completed but there are still many turns left."""

            # special instruction for the final turn (i.e. 1 remaining) in exact mode
            else:
                resource_instructions += f"""{exact_mode_instructions}, including this one. Therefore, you should use this turn to ask for any remaining information needed to complete the artifact, \
        or, if the artifact is already completed, continue to broaden/deepen the discussion in a way that's directly relevant to the artifact. Do NOT indicate to the user that the conversation is ending."""

        elif self.resource_constraint.mode == ResourceConstraintMode.MAXIMUM:
            resource_instructions += f"""You have a maximum of {formatted_remaining_resource} (including this one) left to complete the conversation. \
You can decide to terminate the conversation at any point (including now), otherwise the conversation will automatically terminate when 0 turns are left. \
You will need to plan your actions carefully using the agenda: you want to avoid the situation where you have to pack too many topics into the final turns because you didn't account for them earlier."""

        else:
            logger.error("Invalid resource mode provided.")

        return resource_instructions
