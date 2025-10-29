# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

"""
Liquid handler device interface for AutoZahrt.

Concrete liquid handler drivers should live in `devices/liquid_handler_devices/`.
This module defines the async interface expected of all liquid handler drivers.
"""

from .devices import Device
import abc

class LiquidHandler(Device, abc.ABC):
    """Abstract high-level interface for liquid handler robots.

    Notes:
    - Coordinates are assumed to be in millimeters (mm).
    - Volumes are assumed to be in microliters (µL) unless otherwise stated.
    - Implementations must implement the Device lifecycle methods and set
      `self._connected = True` on successful `connect()`.
    """

    @abc.abstractmethod
    def move_xy(self, x: float, y: float) -> None:
        """Move the toolhead to X/Y coordinates (mm)."""

    @abc.abstractmethod
    def get_xy(self) -> tuple[float, float]:
        """Return (X, Y) current coordinates in mm."""

    @abc.abstractmethod
    def move_z(self, z: float) -> None:
        """Move the toolhead to Z coordinate (mm)."""

    @abc.abstractmethod
    def get_z(self) -> float:
        """Return the current Z position (mm)."""

