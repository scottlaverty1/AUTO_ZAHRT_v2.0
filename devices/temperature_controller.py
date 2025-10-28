"""Temperature controller device interface for AutoZahrt."""

from .devices import Device
import abc


class TemperatureController(Device, abc.ABC):
    """Abstract interface for temperature controllers.

    Implementations should allow setting temperature setpoints and reading
    current temperature.
    """

    @abc.abstractmethod
    async def set_temperature(self, temp_c: float) -> None:
        """Set a temperature setpoint in Celsius."""

    @abc.abstractmethod
    async def read_temperature(self) -> float:
        """Return current temperature in Celsius."""
