# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2024 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty and David Polefrone are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

import ctypes
import re
from typing import Optional

from ..liquid_handlers import LiquidHandler


# You can reuse the immediate() and buffered() functions from Approach 1.
def immediate(unitid: int, command: str) -> str:
    try:
        lib = ctypes.windll.gsioc32
        icmd = getattr(lib, "ICmd")

        rsp = ctypes.create_string_buffer(256)
        rsplen = ctypes.c_int(256)

        icmd(unitid, command.encode('utf-8'), rsp, rsplen)
        return rsp.value
    except OSError as ex:
        print("WARNING:", ex)
        return f"Error: {ex}"


def buffered(unitid: int, command: str) -> str:
    try:
        lib = ctypes.windll.gsioc32
        bcmd = getattr(lib, "BCmd")

        rsp = ctypes.create_string_buffer(256)
        rsplen = ctypes.c_int(256)

        bcmd(unitid, command.encode("utf-8"), rsp, ctypes.byref(rsplen))
        return rsp.value.decode("ascii", "ignore").strip("\x00\r\n ")
    except OSError as ex:
        print("WARNING:", ex)
        return f"Error: {ex}"


# Replace the gsioc_cmd() with a function call that uses the correct direct function

class GX281(LiquidHandler):
    def __init__(self, name: str, uid=25):
        super().__init__(name)
        self.uid = uid
        self.XMIN, self.XMAX = 0, 700
        self.YMIN, self.YMAX = 0, 380
        self.ZMIN, self.ZMAX = 0, 125
        self.SAFE_Z = 125

        # Default racks
        self.rack1 = 204
        self.rack2 = 204
        self.rack3 = 204
        self.rack4 = 204
        self.rack5 = 204
        self.rack6 = 204

        self._lib_ok: Optional[bool] = None  # lazy-checked in connect()

    # ---- Device lifecycle ----------------------------------------------------

    def connect(self) -> None:
        """Load DLL and handshake the device."""
        if self._connected:
            return
        try:
            # Verify DLL present
            _ = ctypes.windll.gsioc32
            self._lib_ok = True
        except OSError as ex:
            self._lib_ok = False
            raise RuntimeError(f"gsioc32.dll not available: {ex}") from ex

        # Lightweight handshake: '%' = device present
        rsp = immediate(self.uid, "%").decode("ascii", "ignore").strip("\x00\r\n ")
        if rsp.lower().startswith("error") or rsp == "":
            raise RuntimeError(f"GX281 (uid {self.uid}) not responding to '%': {rsp!r}")
        self._connected = True
        print(f"Connected GX281 uid={self.uid}")

    def close(self) -> None:
        """No persistent handle to close; mark disconnected."""
        self._connected = False
        print(f"Disconnected GX281 uid={self.uid}")

    def stop(self) -> None:
        """Safe stop: park Z at SAFE_Z and leave connected."""
        try:
            if self.get_z() != self.SAFE_Z:
                self.move_z(self.SAFE_Z)
        except Exception as e:
            print(f"Stop: failed to park Z: {e}")

    ######################################################################
    ### Core movement functions - using direct function calls

    def home(self):
        self._ensure_conn()
        print("-" * 50)
        print("Moving GX281 home")
        print("-" * 50)
        return buffered(self.uid, 'SH')

    def get_xy(self):
        self._ensure_conn()
        print("-" * 50)
        print("Locating X and Y")
        print("-" * 50)
        rsp = immediate(self.uid, 'X')
        nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+", rsp)
        if len(nums) >= 2:
            return float(nums[0]), float(nums[1])
        return rsp

    def move_xy(self, x: float, y: float):
        self._ensure_conn()
        print("-" * 50)
        print(f"Moving GX281 X and Y location {x} and {y}")
        print("-" * 50)
        if x < self.XMIN:
            x = self.XMIN
        if x > self.XMAX:
            x = self.XMAX
        if y < self.YMIN:
            y = self.YMIN
        if y > self.YMAX:
            y = self.YMAX

        try:
            z = self.get_z()
            # get_z may return a raw string or a number depending on device; attempt numeric compare
            if isinstance(z, (int, float)):
                current_z = z
            else:
                nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+", str(z))
                current_z = float(nums[0]) if nums else None
            if current_z is not None and current_z != self.SAFE_Z:
                self.move_z(self.SAFE_Z)
        except Exception as e:
            print(f"Warning: could not verify/park Z before XY move: {e}")

        print(f"Moving to X: {x}, Y: {y}")
        return buffered(self.uid, f'SX{x}/{y}')

    def get_z(self):
        self._ensure_conn()
        print("-" * 50)
        print("Get Z axis of needle")
        print("-" * 50)
        rsp = immediate(self.uid, 'Z')
        nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+", rsp)
        if nums:
            return float(nums[0])
        return rsp

    def move_z(self, z):
        self._ensure_conn()
        print("-" * 50)
        print(f"Moving to Z: {z}")
        print("-" * 50)
        if z < self.ZMIN: z = self.ZMIN
        if z > self.ZMAX: z = self.ZMAX
        return buffered(self.uid, f'SZ{z}')

    ######################################################################
    ### Base-level commands; use with caution.

    def reset_handler(self):
        return immediate(self.uid, '$')

    def read_current_nvram(self):
        # return "AA=xxxx"; see NVMM for more info.
        return immediate(self.uid, '@')

    def set_nvram(self, addr, val):
        return immediate(self.uid, 'S@AA=' + str(val))

    def reset_nvram(self):
        # Omitting other test modes [0, 1, 2, 7].
        return buffered( self.uid, 'S~9')

    def read_id_strings(self):
        # 1 XY, 2 Z, 3 GX Prep, 4 GX Z IM, 5/6 GX Dir IM [L/R]
        return immediate(self.uid, '~')

    def enable_xyz_motors(self):
        return buffered(self.uid, 'SE111')

    def read_diverter_state(self):
        return immediate(self.uid, 'F')

    def set_diverter_state(self, s=0):
        return buffered(self.uid, 'SF' + str(s))

    def read_input_contacts(self):
        return immediate(self.uid, 'I')

    def read_output_contacts(self):
        return immediate(self.uid, 'J')

    ######################################################################
    ### Fun commands.

    def beep(self, t=0.1):
        return buffered(self.uid, 'SA' + str(t))

    def write_display(self, msg, line=2):
        # or line=1
        return buffered(self.uid, 'SW' + str(line) + '=' + msg)
    
    ######################################################################
    ### Core device commands.

    def get_device(self):
        print("-" * 50)
        print("Getting GX281 Device is available")
        print("-" * 50)
        return immediate(self.uid, '%')

    def read_motor_status(self):
        print("-" * 50)
        print("Reading Motor Status")
        print("-" * 50)
        # xyzp. P parked, R running, E error, I not initialized, X no pump.
        # RRRR while commands pending in buffered S command FIFO.
        return immediate(self.uid, 'M')

    def read_travel_ranges(self):
        # 0/700, 0/380, 0/125.
        return immediate(self.uid, 'Q')

    def read_buffer(self):
        # Buffer holds up to 21 commands.
        return immediate(self.uid, 'S')

    def read_error(self):
        print("-" * 50)
        print("Reading Errors")
        print("-" * 50)
        return immediate(self.uid, 'e')

    def clear_error(self):
        print("-" * 50)
        print("Clearing Errors")
        print("-" * 50)
        # Optional n to raise error for testing.
        return buffered(self.uid, 'Se')
    
    
    ######################################################################
    ### Helper functions
    def _ensure_conn(self) -> None:
        if not getattr(self, "_lib_ok", False) or not getattr(self, "_connected", False):
            raise RuntimeError("GX281 not connected. Call connect() first.")