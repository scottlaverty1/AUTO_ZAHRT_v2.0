"""Liquid handler device interface for AutoZahrt.

Concrete liquid handler drivers should live in `devices/liquid_handler_devices/`.
This module defines the async interface expected of all liquid handler drivers.
"""

from .devices import Device
import abc
from typing import Mapping, Any


class LiquidHandler(Device, abc.ABC):
    """Abstract high-level interface for liquid handler robots.

    Notes:
    - Coordinates are assumed to be in millimeters (mm).
    - Volumes are assumed to be in microliters (µL) unless otherwise stated.
    - Implementations must implement the Device lifecycle methods and set
      `self._connected = True` on successful `connect()`.
    """

    @abc.abstractmethod
    async def move_xy(self, x: float, y: float) -> None:
        """Move the toolhead to X/Y coordinates (mm)."""

    @abc.abstractmethod
    async def move_z(self, z: float) -> None:
        """Move the toolhead to Z coordinate (mm)."""

    @abc.abstractmethod
    async def get_z(self) -> float:
        """Return the current Z position (mm)."""

    @abc.abstractmethod
    async def set_bedlayout(self, bed_layout: Mapping[str, Any]) -> None:
        """Configure bed/plate layout.

        `bed_layout` is an implementation-defined mapping describing the
        locations and types of plates/racks. Concrete drivers should document
        the expected shape for their hardware.
        """

