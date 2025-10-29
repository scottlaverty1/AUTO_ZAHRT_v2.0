# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

from __future__ import annotations

import re
import serial
from typing import Optional, Union

from ..valves import Valve  # your Valve ABC (inherits Device)


class ViciValve(Valve):
    """
    Driver for VICI selector valves (2–40 even positions).

    Lifecycle:
      - call connect() to open the serial link and program #positions
      - call close() to close the link
      - stop() is a no-op by default (override if you have a safe halt)

    Notes:
      - `valve_type` can be '6-way', '10-way', '24-way', or an even int (2–40).
      - Responses are ASCII lines terminated by CR.
    """

    VALVES_PRESETS = {
        "6-way":  {"positions": 6},
        "10-way": {"positions": 10},
        "24-way": {"positions": 24},
    }

    def __init__(
        self,
        name: str,
        *,
        port: str,
        valve_type: Union[str, int],
        baudrate: int = 9600,
        timeout: float = 1.0,
    ):
        super().__init__(name)
        # keep params, defer opening serial until connect()
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._ser: Optional[serial.Serial] = None

        # Normalize number of positions
        if isinstance(valve_type, str):
            key = valve_type.lower().replace(" ", "").replace("-", "")
            preset = next(
                (v for k, v in self.VALVES_PRESETS.items() if k.replace("-", "") == key),
                None,
            )
            if preset is None:
                raise ValueError(f"Unknown valve_type '{valve_type}'")
            self.positions = preset["positions"]
        else:
            self.positions = int(valve_type)
            if self.positions % 2 or not (2 <= self.positions <= 40):
                raise ValueError("positions must be an even number between 2 and 40")

        self.device_id: Optional[str] = None  # optional address/id if you use one

    # -------------------------
    # Device lifecycle (sync)
    # -------------------------
    def connect(self) -> None:
        if self._connected:
            return
        self._ser = serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=self._timeout,
        )
        # program stator size on connect (mirrors your original init behavior)
        self.set_number_of_positions(self.positions)
        self._connected = True

    def stop(self) -> None:
        """No-op; override if your controller supports a pause/stop command."""
        pass

    def close(self) -> None:
        ser = self._ser
        self._ser = None
        if ser is not None:
            ser.close()
        self._connected = False

    # -------------------------
    # Valve interface (sync)
    # -------------------------
    def move_home(self) -> None:
        self._send("HM")

    def go_to_position(self, pos: int) -> None:
        if not 1 <= pos <= self.positions:
            raise ValueError(f"Position must be between 1 and {self.positions}")
        self._send(f"GO{pos:02}")

    def check_current_position(self) -> int:
        resp = self._send("CP")
        # try to parse the first integer in the response
        m = re.search(r"(\d+)", resp)
        if not m:
            raise RuntimeError(f"Unexpected CP response: {resp!r}")
        return int(m.group(1))

    def check_firmware_version(self) -> str:
        return self._send("VR")

    # -------------------------
    # Extra convenience methods
    # -------------------------
    def move_clockwise(self, pos: Optional[int] = None) -> None:
        cmd = f"CW{pos:02}" if pos is not None else "CW"
        self._send(cmd)

    def move_counterclockwise(self, pos: Optional[int] = None) -> None:
        cmd = f"CC{pos:02}" if pos is not None else "CC"
        self._send(cmd)

    def toggle_position(self) -> None:
        """Two-position mode only."""
        self._send("TO")

    def timed_toggle(self) -> None:
        self._send("TT")

    def set_number_of_positions(self, n: int) -> None:
        if n % 2 or not (2 <= n <= 40):
            raise ValueError("Number of positions must be an even number between 2 and 40")
        self._send(f"NP{n:02}")

    def set_delay_time(self, ms: int) -> None:
        if not (0 <= ms <= 65535):
            raise ValueError("Delay must be 0–65535 ms")
        self._send(f"DT{ms:05}")

    def set_actuator_mode(self, mode: int) -> None:
        if mode not in (1, 2, 3):
            raise ValueError("mode must be 1, 2 or 3")
        self._send(f"AM{mode}")

    def learn_stops(self) -> None:
        self._send("LRN")

    def set_device_id(self, new_id: str) -> None:
        if len(new_id) != 1 or not (new_id.isdigit() or new_id.isalpha()):
            raise ValueError("device_id must be a single digit (0-9) or letter (A-Z)")
        self._send(f"ID{new_id}")
        self.device_id = new_id

    def reset_device_id(self) -> None:
        self._send("*ID*")
        self.device_id = None

    # -------------------------
    # Low-level I/O
    # -------------------------
    def _ensure_connected(self) -> None:
        if not (self._connected and self._ser and self._ser.is_open):
            raise RuntimeError("ViciValve is not connected. Call connect() first.")

    def _send(self, command: str) -> str:
        """Send ASCII command and return single-line ASCII response without CR."""
        self._ensure_connected()
        ser = self._ser  # type: ignore[assignment]
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write((command + "\r").encode("ascii"))
        line = ser.readline()  # reads until '\r' or timeout
        return line.decode("ascii", errors="replace").strip()

#TODO : Add the multiple valve controller class
'''
class Multi_VICIValveController:
    """Helper to broadcast the same command to multiple valves."""

    def __init__(self, *valves: ViciValve):
        if not valves:
            raise ValueError('At least one ViciValve required')
        self.valves = valves

    def _broadcast(self, method: str, *args, **kwargs):
        return [getattr(v, method)(*args, **kwargs) for v in self.valves]

    def go_to_position(self, pos: int):
        return self._broadcast('go_to_position', pos)

    def move_home(self):
        return self._broadcast('move_home')

    def move_clockwise(self, pos: Optional[int] = None):
        return self._broadcast('move_clockwise', pos)

    def move_counterclockwise(self, pos: Optional[int] = None):
        return self._broadcast('move_counterclockwise', pos)

    def check_current_position(self):
        return self._broadcast('check_current_position')

    def close(self):
        return self._broadcast('close')
'''
