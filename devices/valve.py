"""Valve device interface for AutoZahrt."""

from .devices import Device
import abc


class Valve(Device, abc.ABC):
    """Abstract interface for valves (on/off or positionable)."""

    @abc.abstractmethod
    async def open(self) -> None:
        """Open the valve."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the valve."""

    async def is_open(self) -> bool:
        """Optional: return whether valve is open. Implement if available."""
        raise NotImplementedError
