"""Liquid handler device interface for AutoZahrt.

Concrete liquid handler drivers should live in `devices/liquid_handler_devices/`.
This module defines the async interface expected of all liquid handler drivers.
"""

from .devices import Device
import abc


class Pump(Device, abc.ABC):
    """Abstract high-level interface for pumps used within the lab space.

    Units:
    - flow_rate: microliters per minute (µL/min)
    - volume: microliters (µL)

    Implementations must implement the Device lifecycle methods and set
    `self._connected = True` on successful `connect()`.
    """

    @abc.abstractmethod
    async def aspirate(self, flow_rate_ul_min: float, volume_ul: float) -> None:
        """Aspirate `volume_ul` (µL) at `flow_rate_ul_min` (µL/min)."""

    @abc.abstractmethod
    async def dispense(self, flow_rate_ul_min: float, volume_ul: float) -> None:
        """Dispense `volume_ul` (µL) at `flow_rate_ul_min` (µL/min)."""

    @abc.abstractmethod
    async def set_rate(self, flow_rate_ul_min: float) -> None:
        """Set a default flow rate (µL/min) for subsequent operations."""

    @abc.abstractmethod
    async def stop_flow(self) -> None:
        """Stop any ongoing aspiration/dispense operation promptly."""

    async def close(self) -> None:
        """Convenience: shutdown the pump (default: call `disconnect()`)."""
        await self.disconnect()