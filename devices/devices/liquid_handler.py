# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

# liquid_handler.py
from __future__ import annotations
import abc
from .devices import Device

class LiquidHandler(Device):
    """Abstract high-level interface for liquid handler robots (synchronous)."""

    @abc.abstractmethod
    def home(self) -> None:
        """Home the liquid handler (move axes to known reference)."""

    @abc.abstractmethod
    def move_xy(self, x: float, y: float) -> None:
        """Move the toolhead to X/Y coordinates (mm)."""

    @abc.abstractmethod
    def get_xy(self) -> tuple[float, float]:
        """Return the current X/Y position (mm)."""

    @abc.abstractmethod
    def move_z(self, z: float) -> None:
        """Move the toolhead to Z coordinate (mm)."""

    @abc.abstractmethod
    def get_z(self) -> float:
        """Return the current Z position (mm)."""
