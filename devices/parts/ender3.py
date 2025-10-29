# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT (minimal Ender-3 controller)
# Copyright: (C) 2025 by Professor Andrew Zahrt
# Contributions by graduate student Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

'''
The purpose of this code is to feed into our liquid handler ender 3 class
which we can use as a 3D printer to control the xyz coordinates of our 3D printer
'''
from AUTO_ZAHRT.Ender3_liquid_handler.ender3 import ender3

class ender3_liquid_handler(ender3):
    """
    Inherits all movement & comms from `ender3`.
    You can add liquid-handler specific helpers here (plate maps, pipette moves, etc.).
    """

    def __init__(self, port="COM14", baud=115200, timeout=2, verbose=False):
        super().__init__(port=port, baud=baud, timeout=timeout, verbose=verbose)
        self.XMIN = 0
        self.XMAX = 225
        self.YMIN = 0
        self.YMAX = 225
        self.ZMIN = 0
        self.ZMAX = 250

    # Example domain helper (optional)
    def home_and_lift(self, lift_mm=5):
        self.home("XYZ")
        self.absolute()
        self.move(z=lift_mm, feed=300, wait=True)

    def move_xy(self, x, y):
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

    def move_z(self, z):
        print("-" * 50)
        print(f"Moving to Z: {z}")
        print("-" * 50)
        if z < self.ZMIN: z = self.ZMIN
        if z > self.ZMAX: z = self.ZMAX
        return self.move(x=None, y=None, z=z, feed=300)

    def get_z(self):
        return self.location()["Z"]

# ============================== USAGE EXAMPLE ==============================

if __name__ == "__main__":
    # Use the subclass exactly like the parent, plus any helpers you add.
    e = ender3_liquid_handler(port="COM14", baud=115200, timeout=2, verbose=False)
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
