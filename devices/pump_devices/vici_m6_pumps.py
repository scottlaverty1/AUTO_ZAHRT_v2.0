# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2024 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty and David Polefrone are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

import time
import serial

from ..pumps import Pump

'''
The purpose of this code is to control the VICI M6 pumps
'''

class VICI_M6_Pumps(Pump):

    def __init__(self,  port='COM16', baud_rate=9600, timeout=1):

        try:
            self.ser = serial.Serial(port, baud_rate, timeout=timeout)
            print(f"Successfully initialized serial connection with VICI M6 pump.")
        except serial.SerialException as e:
            print(f"Failed to initialize serial connection with VICI M6 pump: {e}")
            self.ser = None
        self.direction = "aspirating"
        self.direction_multiplier = -1  # Default to aspirating
        self._initialize_parameters()

    def _initialize_parameters(self):
        """Initialize all pump parameters and math constants."""
        # Communication and motor control parameters
        self.MS = 256  # Microsteps per step
        self.P = 0  # Motor position
        self.VI = 1000  # Initial velocity (steps/sec)
        self.VM = 76800  # Maximum velocity (steps/sec)
        self.A = 1000000  # Acceleration (steps/sec^2)
        self.D = 1000000  # Deceleration (steps/sec^2)
        self.MA = None  # Absolute movement (steps/sec)
        self.MR = None  # Relative movement (step/sec)
        self.SL = None  # Speed override (steps/sec)
        self.SL_units = "steps/sec"

        # Math and volume calculations
        self.volume = 1000  # Total volume (uL)
        self.volume_units = "uL"
        self.flow_rate_min = 100  # Default flow rate (uL/min)
        self.flow_rate_sec = self.flow_rate_min / 60  # Convert to uL/sec
        self.flow_rate_units_min = "uL/min"
        self.flow_rate_units_sec = "uL/sec"

        # Motor and pump specifics
        self.micro_steps = 256
        self.motor_steps = 200
        self.gearbox_ratio = 9.87
        self.micro_steps_per_rev = self.micro_steps * self.motor_steps * self.gearbox_ratio
        self.pump_head_volume = 99.771  # Pump head volume (uL/rev)
        self.steps_per_ul = self.micro_steps_per_rev / self.pump_head_volume  # Steps per uL
        self.steps_per_ul_units = "steps/uL"

    def set_flow_rate(self, flow_rate_min, direction):
        try:
            self.flow_rate_min = float(flow_rate_min)
            self.flow_rate_sec = self.flow_rate_min / 60.0

            if direction not in ["aspirating", "dispensing"]:
                print("Invalid direction. Must be 'aspirating' or 'dispensing'.")
                return

            self.direction = direction
            self.direction_multiplier = 1 if direction == "dispensing" else -1
            #TODO These calibration steps were manually calculated at each value, here to ensure accuracy
            # Need a cleaner way to set these values
            calibration_values = {
                "dispensing": {
                    1000: 2494.720, 1500: 2584.774, 200: 2426.062, 2000: 2440.881, 41.33: 2426.062
                },
                "aspirating": {
                    1000: 2606.371104, 1500: 3166.612, 200: 2451.378376, 2000: 2955.059, 41.33: 2451.378376
                }
            }

            self.steps_per_ul = calibration_values[self.direction].get(self.flow_rate_min)
            if not self.steps_per_ul:
                print(f"No calibration data for flow rate {self.flow_rate_min} uL/min in {self.direction} mode.")
                self.steps_per_ul = 2606.371104

            self.VM = abs(int(self.steps_per_ul * self.flow_rate_sec))

            print(f"{direction.capitalize()} at {self.flow_rate_min} uL/min")
            print(f"Steps per uL: {self.steps_per_ul}, VM: {self.VM} steps/sec")

        except ValueError:
            print('Invalid rate or volume.')

    # Initiates the pump
    def start(self):
        # Initiates serial connection
        try:
            if not self.ser:
                print('No serial connection configured for VICI M6 pump.')
                return
            if not self.ser.is_open:
                self.ser.open()
                print('Serial connection opened.')
                self.reset_parameters()
        except Exception as e:
            print(f'Error opening serial connection: {e}')

    def send_command(self, command):
        if not self.ser or not self.ser.is_open:
            print("Serial connection for VICI M6 Pumps is not open.")
            return
        """Send a command to the pump and wait for a response"""
        print(f"Command {command}")
        self.ser.write((command + '\r').encode())
        time.sleep(0.1)
        response = self.ser.read(self.ser.in_waiting)
        print(f"Command sent to the pump \"{response.decode()}\"")

    def get_pump_parameters(self):
        print("Pump parameters:\n"
              f"The flow rate per minute is {self.flow_rate_min} {self.flow_rate_units_min}\n"
              f"The flow rate per second is {round(self.flow_rate_sec,2)} {self.flow_rate_units_sec}\n"
              f"The # of micro steps is  {self.micro_steps}\n"
              f"The # of motor steps is  {self.motor_steps}\n"
              f"The gear box ratio is  {self.gearbox_ratio}\n"
              f"The number of microsteps per revolution is {round(self.micro_steps_per_rev,2)}\n"
              f"The Pump Head Volume is  {self.pump_head_volume}\n"
              f"The Velocity Max is {round(self.steps_per_ul,2)} {self.steps_per_ul_units}"
              )

    #Turns off serial connection and turned it off
    def stop(self):
        if not self.ser or not self.ser.is_open:
            print("Serial connection for VICI M6 Pumps is not open.")
            return
        print("Closing pumps.\n")
        #Sets the flow rate to 0 overriding all previous commands
        self.send_command("SL 0")

    def stop_connection(self):
        if not self.ser:
            print("No serial connection to close.")
            return
        try:
            self.send_command("P=0")
            self.send_command("E")
            self.reset_parameters()
            self.ser.close()
            print('Serial connection closed.\n Pumps are closed.')
        except Exception as e:
            print(f"Error while stopping connection: {e}")

    def pump_solution(self, volume):
        try:
            if not self.ser or not getattr(self.ser, 'is_open', False):
                raise RuntimeError("Serial connection is not open")

            total_microsteps = int(self.steps_per_ul * volume)
            if self.flow_rate_sec == 0:
                raise ValueError("Flow rate cannot be zero.")

            pump_time = abs(volume / self.flow_rate_sec)
            start_time = time.time()

            # Set pump parameters
            commands = [
                f"A={self.A}", f"D={self.D}", f"VI={self.VI}", f"VM={self.VM}", f"P={self.P}", "PR P"
            ]
            for cmd in commands:
                self.send_command(cmd)

            self.send_command(f"MA={self.direction_multiplier * total_microsteps}")
            self.send_command("PR AL")
            time.sleep(pump_time + 2)

            self.stop()
            print("Number of microsteps the pump moved:")
            self.send_command("PR P")
            elapsed = time.time() - start_time
            print(f"Actual pump time: {elapsed:.2f} seconds")
        except Exception as e:
            print(f"Error during pump operation: {e}")

    def aspirating(self, flow_rate_ul_min: float, volume_ul: float):
        # Synchronous aspirate helper (keeps existing blocking behavior)
        self.start()
        # driver expects absolute flow rate and a direction string
        self.set_flow_rate(abs(flow_rate_ul_min), "aspirating")
        self.pump_solution(volume_ul)
        self.stop()

    def dispensing(self, flow_rate_ul_min: float, volume_ul: float):
        # Synchronous dispense helper (keeps existing blocking behavior)
        self.start()
        self.set_flow_rate(abs(flow_rate_ul_min), "dispensing")
        self.pump_solution(volume_ul)
        self.stop()

    def reset_parameters(self):
        self.send_command("FD")
        self.send_command("IP")

    def close(self) -> None:
        """Closes the serial connection."""
        try:
            if self.ser and getattr(self.ser, 'is_open', False):
                self.ser.close()
        except Exception:
            pass


'''
pump = VICI_M6_Pumps(port='COM21')

pump.start()

pump.set_flow_rate(1000, "aspirating")
#pump.set_flow_rate(1000, "dispensing")
pump.pump_solution(500)

pump.stop_connection()
'''