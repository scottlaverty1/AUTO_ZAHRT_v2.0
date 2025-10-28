# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

'''
The purpose of this code is to feed into our liquid handler ender 3 class
which we can use as a 3D printer to control the xyz coordinates of our 3D printer
'''
from ..parts.Ender3_liquid_handler.ender3 import ender3
from ..liquid_handlers import LiquidHandler

class Ender3LiquidHandler(ender3, LiquidHandler):
    """
    Inherits all movement & comms from `ender3`.
    You can add liquid-handler specific helpers here (plate maps, pipette moves, etc.).
    """

    def __init__(self, port: str = "COM14", baud: int = 115200, timeout: int = 2, verbose: bool = False, name: str = "ender3"):
        """Initialize the Ender3-based liquid handler.

        This calls the underlying Ender3 (serial) initialization and then
        ensures the `Device` base state is initialized so higher-level code
        (DeviceRegistry, background tasks) can rely on attributes like
        `self._connected` and `self._task`.
        """
        super().__init__(port=port, baud=baud, timeout=timeout, verbose=verbose)
        # ensure Device base initializer runs (ender3.__init__ is not cooperative)
        # import locally to avoid circular imports at module import time
        from ..devices import Device
        Device.__init__(self, name)
        self.XMIN = 0
        self.XMAX = 225
        self.YMIN = 0
        self.YMAX = 225
        self.ZMIN = 0
        self.ZMAX = 250

    def home_and_lift(self, lift_mm: float = 10.0) -> None:
        """Home the axes and lift the toolhead by lift_mm (mm)."""
        # call parent home implementation
        super().home("XYZ")
        self.absolute()
        self.move(z=lift_mm, feed=300, wait=True)

    def move_xy(self, x: float, y: float) -> None:
        print("-" * 50)
        print(f"Moving ender3 liquid handler X and Y location {x} and {y}")
        print("-" * 50)
        if x < self.XMIN: x = self.XMIN
        if x > self.XMAX: x = self.XMAX
        if y < self.YMIN: y = self.YMIN
        if y > self.YMAX: y = self.YMAX

        current_z = self.get_z()
        if current_z != 80:
            self.move_z(80)

        print(f"Moving to X: {x}, Y: {y}")
        return self.move(x=x, y=y, z=None, feed=9000)
    
    def get_xy(self) -> tuple[float, float]:
        """Return (X, Y) current coordinates in mm."""
        loc = self.location()
        return loc["X"], loc["Y"]

    def move_z(self, z: float) -> None:
        print("-" * 50)
        print(f"Moving to Z: {z}")
        print("-" * 50)
        if z < self.ZMIN: z = self.ZMIN
        if z > self.ZMAX: z = self.ZMAX
        return self.move(x=None, y=None, z=z, feed=300)

    def get_z(self) -> float:
        """Return current Z coordinate in mm."""
        return self.location()["Z"]

'''
# ============================== USAGE EXAMPLE ==============================

if __name__ == "__main__":
    # Use the subclass exactly like the parent, plus any helpers you add.
    e = Ender3LiquidHandler(port="COM14", baud=115200, timeout=2, verbose=False)
    try:
        e.home_and_lift(lift_mm=60)
        e.move_xy(x=41.5, y=41.4)
        e.move_z(z=10)
        e.move_z(z=60)
        e.move_xy(x=41.5, y=83)
        e.move_z(z=10)
        e.move_z(z=60)
        e.home_and_lift(lift_mm=60)
        e.location()
    finally:
        e.close()
'''