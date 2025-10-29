# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2025 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

import serial
import time

from ..temperature_controller import TemperatureController

class TC720(TemperatureController):
    def __init__(self, name: str, port='COM12', baudrate=230400, timeout=1):
        super().__init__(name)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser: Optional[serial.Serial] = None

    # ---- Device lifecycle ----------------------------------------------------

    def connect(self) -> None:
        if self.ser and self.ser.is_open:
            self._connected = True
            return
        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self._connected = True
        print(f"Connected to TC-720 on {self.port}")

    def close(self):
        """
        Closes the serial connection.
        """
        self.ser.close()
        self._connected = False
        print(f"Disconnected from TC-720 on {self.ser.port}")

    def stop(self):
        """Stop the temperature controller device."""
        set_temp = 25.0  # Default safe temperature
        print(f"Stopping TC-720, setting temperature to {set_temp} °C")
        self.close()

    # ---- TemperatureController interface --------------------------------------

    def calculate_checksum(self, char_list):
        """
        Calculates the checksum based on the TC-720 command protocol.
        """
        first_6_chars = char_list[1:7]
        total_sum = sum(ord(char) for char in first_6_chars)
        hex_sum = hex(total_sum)[2:]
        last_two_digits = hex_sum[-2:].zfill(2)
        result_list = ['*'] + first_6_chars + list(last_two_digits) + ['\r']
        return result_list

    def convert_temp_to_bstc(self, temp_celsius):
        """
        Converts temperature to the bstc command with checksum for the TC-720 controller.
        """
        temp_hundredths = int(temp_celsius * 100)
        hex_temp = format(temp_hundredths, '04x')
        bstc = ['*', '1', 'c'] + list(hex_temp) + ['XX', 'XX', '\r']
        return self.calculate_checksum(bstc)

    def set_temperature(self, temp_celsius):
        """
        Sets the temperature on the TC-720 temperature controller.
        """
        bstc = self.convert_temp_to_bstc(temp_celsius)
        print(f"Setting temperature to {temp_celsius} °C with command: {''.join(bstc)}")

        for char in bstc:
            self.ser.write(char.encode())
            time.sleep(0.01)  # Short delay for proper command transmission

        print("Temperature set successfully!")

    def _build_query(self, cc):  # cc: '01' (INPUT1) or '04' (INPUT2)
        return self.calculate_checksum(['*'] + list(cc) + list('0000') + ['XX', 'XX', '\r'])

    def read_temperature(self, sensor=1):
        cc = '01' if sensor == 1 else '04'
        cmd = self._build_query(cc)
        self.ser.reset_input_buffer()
        for ch in cmd:
            self.ser.write(ch.encode())
            time.sleep(0.005)

        resp = self.ser.read(8)  # expects: * D D D D S S ^
        if len(resp) < 8 or resp[0:1] != b'*':
            raise IOError(f"Unexpected response: {resp!r}")

        dddd = resp[1:5].decode('ascii')   # hex value in hundredths °C (signed 16-bit)
        # optional checksum verify for the 4 data chars:
        if resp[5:7].decode('ascii') != format(sum(ord(c) for c in dddd) & 0xFF, '02x'):
            raise IOError("Checksum mismatch")

        val = int(dddd, 16)
        if val >= 0x8000:  # handle negatives (two's complement, 16-bit)
            val -= 0x10000
        return val / 100.0  # °C
