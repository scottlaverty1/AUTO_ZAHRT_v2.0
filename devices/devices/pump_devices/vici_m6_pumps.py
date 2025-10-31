# ------------------------------------------------------------------------------
# Software: AUTO_ZAHRT
# Copyright: (C) 2024 by Professor Andrew Zahrt
# This software is the intellectual property of Professor Andrew Zahrt
# Contributions by graduate students Scott Laverty and David Polefrone are acknowledged.
# All rights reserved.
# ------------------------------------------------------------------------------

import time
import serial

from ..pump import Pump

'''
The purpose of this code is to control the VICI M6 pumps
'''

class VICI_M6_Pumps(Pump):

    def __init__(self,  port='COM22', baud_rate=9600, timeout=1):
        super().__init__(f"VICI M6 Pump (port={port})")  # Initialize base class with name

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

    def send_command(self, command, verbose=False):
        if not self.ser or not self.ser.is_open:
            print("Serial connection for VICI M6 Pumps is not open.")
            return
        """Send a command to the pump and wait for a response"""
        if verbose:
            print(f"Command {command}")
        self.ser.write((command + '\r').encode())
        time.sleep(0.1)
        response = self.ser.read(self.ser.in_waiting)
        if verbose:
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
        self.send_command("SL 0", verbose=False)

    def stop_connection(self):
        if not self.ser:
            print("No serial connection to close.")
            return
        try:
            self.send_command("P=0", verbose=False)
            self.send_command("E", verbose=False)
            self.reset_parameters()
            self.ser.close()
            print('Serial connection closed.\n Pumps are closed.')
        except Exception as e:
            print(f"Error while stopping connection: {e}")

    def get_current_position(self):
        """Get current position in microsteps"""
        # Clear any pending responses
        self.ser.reset_input_buffer()
        
        # Send position request command
        self.ser.write("PR P\r".encode())
        time.sleep(0.2)  # Give more time to respond
        
        response = self.ser.read(self.ser.in_waiting)
        try:
            response_text = response.decode(errors='ignore').strip()
            # Try to find any number in the response
            import re
            numbers = re.findall(r'-?\d+', response_text)
            if numbers:
                return int(numbers[0])
            return 0
        except Exception as e:
            print(f"Error reading position: {e}")
            return 0
            
    def get_progress_info(self, start_position, total_microsteps, start_time, target_volume):
        """Calculate and display progress information"""
        current_position = self.get_current_position()
        
        # Ensure we have valid positions
        if start_position is None or start_position == 0:
            start_position = 0
        if current_position is None or current_position == 0:
            current_position = 0
            
        try:
            steps_moved = abs(current_position - start_position)
            volume_moved = steps_moved / self.steps_per_ul
            percent_complete = min(100, (steps_moved / abs(total_microsteps)) * 100)
            
            elapsed = time.time() - start_time
            if elapsed > 0:
                current_flow_rate = (volume_moved / elapsed) * 60  # Convert to ul/min
            else:
                current_flow_rate = 0
                
            # Create progress bar
            bar_width = 30
            filled = int(bar_width * percent_complete / 100)
            bar = '=' * filled + '-' * (bar_width - filled)
            
            print(f"\r[{bar}] {volume_moved:.1f}/{target_volume:.1f} µL "
                  f"({percent_complete:.1f}%) at {current_flow_rate:.1f} µL/min", end="")
        except Exception as e:
            print(f"\rError calculating progress: {e}", end="")
              
    def pump_solution(self, volume):
        try:
            if not self.ser or not getattr(self.ser, 'is_open', False):
                raise RuntimeError("Serial connection is not open")

            total_microsteps = int(self.steps_per_ul * volume)
            if self.flow_rate_sec == 0:
                raise ValueError("Flow rate cannot be zero.")

            pump_time = abs(volume / self.flow_rate_sec)
            start_time = time.time()
            # Clear any pending commands and get initial position
            self.send_command("SL 0", verbose=False)
            time.sleep(0.5)
            start_position = self.get_current_position()
            print(f"Starting position: {start_position} steps")

            # Set pump parameters
            commands = [
                f"A={self.A}", f"D={self.D}", f"VI={self.VI}", f"VM={self.VM}", f"P={start_position}", "PR P"
            ]
            for cmd in commands:
                self.send_command(cmd, verbose=False)
                time.sleep(0.1)  # Give the pump time to process each command

            self.send_command(f"MA={self.direction_multiplier * total_microsteps}", verbose=False)
            self.send_command("PR AL", verbose=False)
            
            # Monitor progress
            update_interval = 0.5  # Update every 0.5 seconds
            next_update = start_time
            while time.time() - start_time < pump_time + 2:
                if time.time() >= next_update:
                    self.get_progress_info(start_position, total_microsteps, start_time, volume)
                    next_update = time.time() + update_interval
                time.sleep(0.1)

            self.stop()
            print("\nFinal position:")
            final_position = self.get_current_position()
            steps_moved = abs(final_position - start_position)
            actual_volume = steps_moved / self.steps_per_ul
            elapsed = time.time() - start_time
            actual_flow_rate = (actual_volume / elapsed) * 60  # Convert to ul/min
            
            print(f"Completed {actual_volume:.1f} µL in {elapsed:.1f} seconds")
            print(f"Average flow rate: {actual_flow_rate:.1f} µL/min")
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
        self.send_command("FD", verbose=False)
        self.send_command("IP", verbose=False)

    def close(self) -> None:
        """Closes the serial connection."""
        try:
            if self.ser and getattr(self.ser, 'is_open', False):
                self.ser.close()
        except Exception:
            pass
        self._connected = False
        
    def connect(self) -> None:
        """Connect to the pump. Required by Device base class."""
        if self._connected:
            return
        self.start()  # Use existing start method
        self._connected = True
    
    async def aspirate(self, flow_rate_ul_min: float, volume_ul: float) -> None:
        """Async wrapper for aspirating operation."""
        self.aspirating(flow_rate_ul_min, volume_ul)
        
    async def dispense(self, flow_rate_ul_min: float, volume_ul: float) -> None:
        """Async wrapper for dispensing operation."""
        self.dispensing(flow_rate_ul_min, volume_ul)
        
    async def set_rate(self, flow_rate_ul_min: float) -> None:
        """Async wrapper for setting flow rate. Defaults to dispensing direction."""
        self.set_flow_rate(flow_rate_ul_min, "dispensing")
        
    async def stop_flow(self) -> None:
        """Async wrapper for stopping flow."""
        self.stop()



pump = VICI_M6_Pumps(port='COM21')

pump.start()

pump.set_flow_rate(1000, "aspirating")
#pump.set_flow_rate(1000, "dispensing")
pump.pump_solution(500)

pump.stop_connection()
