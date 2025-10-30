# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# Contributions by graduate student Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

"""
Parent classes and a small DeviceRegistry for concrete device instances.

Design notes (synchronous API):
- Device is an abstract base class (ABC) with sync lifecycle hooks:
  connect(), close(), stop().
- Specific device interfaces live in sibling modules (e.g. `devices/pumps.py`,
  `devices/liquid_handlers.py`). Concrete drivers live under `devices/*_devices/`
  and implement these interfaces.
"""

from __future__ import annotations

import abc
from typing import Dict, Optional, List, Literal

Category = Literal["pumps", "liquid_handlers", "temperature_controllers", "valves", "light_beds", "uv_detectors"]


class Device(abc.ABC):
    """Abstract base for all devices (synchronous).

    Subclasses must implement the lifecycle methods and set `self._connected`
    appropriately in connect()/close().
    """

    def __init__(self, name: str):
        self.name = name
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @abc.abstractmethod
    def connect(self) -> None:
        """Establish a connection to the individual device."""

    @abc.abstractmethod
    def close(self) -> None:
        """Tear down the connection and mark the device as closed."""

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop device operation (short-running command)."""


class DeviceRegistry:
    """Registry / container for categorized devices.

    Usage:

        registry = DeviceRegistry()
        registry.register("pumps", "pump1", pump_obj)
        pump = registry.get("pumps", "pump1")
    """

    def __init__(self):
        self.pumps: Dict[str, Device] = {}
        self.liquid_handlers: Dict[str, Device] = {}
        self.temperature_controllers: Dict[str, Device] = {}
        self.valves: Dict[str, Device] = {}
        self.light_beds: Dict[str, Device] = {}
        self.uv_detectors: Dict[str, Device] = {}

    def register(self, category: Category, name: str, device: Device) -> None:
        """Register a device into a category. Raises KeyError on duplicate.

        Also validate that the object is a `Device` instance to catch errors
        early.
        """
        if not isinstance(device, Device):
            raise TypeError("device must be an instance of Device")
        mapping = self._mapping_for(category)
        if name in mapping:
            raise KeyError(f"Device '{name}' already registered in '{category}'.")
        mapping[name] = device

    def unregister(self, category: Category, name: str) -> None:
        self._mapping_for(category).pop(name, None)

    def get(self, category: Category, name: str) -> Optional[Device]:
        return self._mapping_for(category).get(name)

    def list_names(self, category: Category) -> List[str]:
        return list(self._mapping_for(category).keys())

    def _mapping_for(self, category: Category) -> Dict[str, Device]:
        if category == "pumps":
            return self.pumps
        if category == "liquid_handlers":
            return self.liquid_handlers
        if category == "temperature_controllers":
            return self.temperature_controllers
        if category == "valves":
            return self.valves
        if category == "light_beds":
            return self.light_beds
        if category == "uv_detectors":
            return self.uv_detectors
        raise KeyError(f"Unknown device category: {category}")
