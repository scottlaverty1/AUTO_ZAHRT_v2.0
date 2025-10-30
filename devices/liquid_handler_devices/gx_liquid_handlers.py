# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2024 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty and David Polefrone are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------
#TODO this file doesn't include any usage examples for the GX271 liquid handler, 
# add those in later.

import ctypes
import re
from typing import Optional

from ..liquid_handler import LiquidHandler


# You can reuse the immediate() and buffered() functions from Approach 1.
def immediate(unitid: int, command:str)-> bytes:
    try:
        lib = ctypes.windll.gsioc32
        icmd = lib.ICmd

        rsp = ctypes.create_string_buffer(256)
        rsplen = ctypes.c_int(256)

        icmd(unitid, command.encode('utf-8'), rsp, rsplen)
        return rsp.value
    except OSError as ex:
        print("WARNING:", ex)
        return b"Error"


def buffered(unitid: int, command: str) -> bytes:
    try:
        lib = ctypes.windll.gsioc32
        bcmd = lib.BCmd

        rsp = ctypes.create_string_buffer(256)
        rsplen = ctypes.c_int(256)

        bcmd(unitid, command.encode('utf-8'), rsp, rsplen)
        return rsp.value
    except OSError as ex:
        print("WARNING:", ex)
        return "Error"


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

    def status(self) -> dict:
        try:
            x, y = self.get_xy()
            z = self.get_z()
            return {"ok": True, "code": "ok", "msg": f"X={x:.2f} Y={y:.2f} Z={z:.2f}"}
        except Exception as e:
            return {"ok": False, "code": "no_response", "msg": str(e)}
        
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

    ### Core movement functions - using direct function calls


    def home(self) -> str:
        _ensure_conn(self)
        return buffered(self.uid, 'SH')

    def get_xy(self) -> str:
        _ensure_conn(self)
        return immediate(self.uid, 'X')

    def move_xy(self, x: float, y: float) -> str:
        _ensure_conn(self)
        if x < self.XMIN: x = self.XMIN
        if x > self.XMAX: x = self.XMAX
        if y < self.YMIN: y = self.YMIN
        if y > self.YMAX: y = self.YMAX

        current_z: float | int | str = self.get_z()  # if get_z remains stringy, keep it loose
        if current_z != self.SAFE_Z: 
            self.move_z(self.SAFE_Z)

        return buffered(self.uid, f'SX{x}/{y}')

    def get_z(self) -> str:
        return immediate(self.uid, 'Z')

    def move_z(self, z: float) -> str:
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
        if not self._connected:
            raise RuntimeError("GX281 not connected. Call connect() first.")
        
# ============================== USAGE EXAMPLE ==============================
gx = GX281(name="gx281", uid=25)
gx.connect()
gx.home()
gx.move_xy(120, 50)
gx.move_z(80)
print(gx.status())   # {'ok': True, 'code': 'ok', 'msg': 'X=120.00 Y=50.00 Z=80.00'}
gx.stop()
gx.close()
