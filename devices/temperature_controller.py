# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

from .devices import Device
import abc


class TemperatureController(Device):
    """Abstract interface for temperature controllers.

    Implementations should allow setting temperature setpoints and reading
    current temperature.
    """

    @abc.abstractmethod
    def set_temperature(self, temp_c: float) -> None:
        """Set a temperature setpoint in Celsius."""

    @abc.abstractmethod
    def read_temperature(self) -> float:
        """Return current temperature in Celsius."""
