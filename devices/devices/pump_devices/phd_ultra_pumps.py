# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

import asyncio
import serial
import time
from typing import Optional

from ..pump import Pump


class PhdUltraPump(Pump):
    """PHD-Ultra syringe pump driver (µL units).

    Minimal synchronous driver with small async wrappers so it satisfies the
    repository's `Pump` abstract interface. The driver speaks the simple PHD
    command set over serial.
    """

    # Air-Tite syringe catalogue (total-volume mL : I.D. mm)
    AIR_TITE_SYRINGES = {1: 4.69, 2.5: 9.65, 5: 12.45, 10: 15.90, 20: 20.05, 30: 22.90}

    def __init__(self, port: str = "COM19", baudrate: int = 9600,
                 timeout: float = 1.0, address: int = 0, pause: float = 0.10):
        super().__init__(f"PHD Ultra Pump (port={port})")
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.address = address
        self.pause = pause
        self.ser: Optional[serial.Serial] = None
        self.syringe_size_ml: Optional[float] = None  # record current syringe
        
    def connect(self) -> None:
        """Establish connection to the pump."""
        if self._connected:
            return
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=self.timeout,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False
        )
        self._connected = True
        print(f"Connected to PHD Ultra pump on {self.port}")

    # ---------- low-level ----------
    def _build(self, body: str) -> bytes:
        prefix = f"{self.address}" if self.address else ""
        return f"{prefix}{body}\r".encode()

    def send(self, body: str) -> str:
        if not getattr(self, "ser", None):
            raise RuntimeError("Serial connection not configured")
        self.ser.reset_input_buffer()
        self.ser.write(self._build(body))
        time.sleep(self.pause)
        return self.ser.read_all().decode(errors="ignore").strip()

    # ---------- setup / mode ----------
    def quick_start_infuse(self) -> str:
        mode = self.send("mode").lower()
        if ("infuse only" in mode) or ("qs i" in mode):
            return mode                    # already correct
        if "satellite" in mode:
            self.send("unlock")
            time.sleep(self.pause)
        return self.send("load qs i")

    # ---------- syringe convenience ----------
    def select_syringe(self, volume_ml: float) -> str:
        diameter = self.AIR_TITE_SYRINGES.get(volume_ml)
        if diameter is None:
            raise ValueError(f"Unsupported syringe size {volume_ml} mL. "
                             f"Choose from {list(self.AIR_TITE_SYRINGES.keys())}")
        self.syringe_size_ml = volume_ml
        # informational only
        self.set_syringe_volume(volume_ml * 1000, "ul")
        return self.set_diameter(diameter)

    def set_diameter(self, mm: float) -> str:
        return self.send(f"diameter {mm:.3f}")

    def set_syringe_volume(self, vol_ul: float, unit: str = "ul") -> str:
        return self.send(f"svolume {vol_ul} {unit}")

    # ---------- run control ----------
    def _set_rate_sync(self, rate_ul_min: float, unit: str = "ul/min") -> str:
        return self.send(f"irate {rate_ul_min:.4g} {unit}")

    def clear_volume_counter(self) -> str:
        return self.send("cvolume")

    def set_target_volume(self, vol_ul: float, unit: str = "ul") -> str:
        return self.send(f"tvolume {vol_ul} {unit}")

    def run(self) -> str:
        return self.send("irun")

    def _dispense_sync(self, vol_ul: float, rate_ul_min: float) -> None:
        """Blocking dispense helper (synchronous).

        This keeps the original behavior: start the run and sleep until the
        estimated duration has passed. Higher-level async callers should use
        the async wrapper `dispense` which runs this in a thread.
        """
        if rate_ul_min <= 0:
            raise ValueError("rate_ul_min must be > 0")
        if not getattr(self, "ser", None):
            raise RuntimeError("Serial connection not configured")

        self._set_rate_sync(rate_ul_min, "ul/min")
        self.clear_volume_counter()
        self.set_target_volume(vol_ul, "ul")
        self.run()  # pump stops when target reached
        duration_sec = vol_ul / rate_ul_min * 60  # seconds
        duration_sec = duration_sec + 2  # small padding
        time.sleep(duration_sec)

    def withdraw(self) -> str:
        if "withdraw" not in self.send("mode").lower():
            raise RuntimeError("Current mode does not allow withdraw")
        return self.send("wrun")

    def stop(self) -> str:
        return self.send("stop")

    # ---------- diagnostics ----------
    def get_status(self) -> str:
        return self.send("status")

    def get_version(self) -> str:
        return self.send("ver")

    # ---------- housekeeping ----------
    def close(self) -> None:
        try:
            if getattr(self, "ser", None) and getattr(self.ser, "is_open", False):
                self.ser.close()
        except Exception:
            pass

    # ---------------- Async wrappers to satisfy Pump ABC ----------------
    async def dispense(self, vol_ul: float, rate_ul_min: float) -> None:  # type: ignore[override]
        return await asyncio.to_thread(self._dispense_sync, vol_ul, rate_ul_min)

    async def set_rate(self, rate_ul_min: float) -> None:  # type: ignore[override]
        return await asyncio.to_thread(self._set_rate_sync, rate_ul_min)

    async def stop_flow(self) -> None:  # type: ignore[override]
        return await asyncio.to_thread(self.stop)

    async def aspirate(self, flow_rate_ul_min: float, volume_ul: float) -> None:  # type: ignore[override]
        raise NotImplementedError("Aspirate/withdraw async helper not implemented; use withdraw() sync helper")


# ----------------------------------------------------------------------
# Self-test harness (executes if you `python phd_ultra_pumps.py`)
# ----------------------------------------------------------------------
'''
PORT, BAUD, PAUSE = "COM18", 9600, 0.25


def _run_selftest():
    pump = None
    try:
        pump = PhdUltraPump(port=PORT, baudrate=BAUD)
        tests = [
            ("mode", lambda: pump.send("mode")),
            ("quick_start_infuse", pump.quick_start_infuse),
            ("select_syringe 10 mL", lambda: pump.select_syringe(10)),
            ("set_rate 3000 µL/min", lambda: pump._set_rate_sync(3000)),
            ("infuse 3000 µL", lambda: pump._dispense_sync(3000, 3000)),
            ("get_version", pump.get_version),
        ]

        print(f"\n===== PHD-Ultra self-test on {PORT} @ {BAUD} baud =====")
        for name, fn in tests:
            try:
                reply = fn()
                print(f"[PASS] {name:30s} → {repr(reply)}")
            except Exception as exc:
                print(f"[FAIL] {name:30s} → {exc}")
            time.sleep(PAUSE)
    finally:
        if pump:
            pump.close()
        print("===== Test complete — port closed =====")
'''