# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

from ..devices import Device
import abc


class Valve(Device, abc.ABC):
    """Abstract interface for valves (on/off or positionable)."""

    @abc.abstractmethod
    def move_home(self) -> None:
        """Moves a valve to the home position."""

    @abc.abstractmethod
    def go_to_position(self, pos: int) -> None:
        """Moves a valve to the specified position."""

    @abc.abstractmethod
    def check_current_position(self) -> int:
        """Returns the current valve position as an integer."""

    @abc.abstractmethod
    def check_firmware_version(self) -> str:
        """Returns the firmware version string of the valve controller."""

#TODO : Add the multiple valve controller class
