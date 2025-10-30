import sys
import time
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from devices.devices import Device  # Import the base Device class first
from devices.valve import Valve    # Import the Valve ABC
from devices.valves.vici_valves import ViciValve

def test_vici_valve():
    valve = ViciValve(
        name="VICI Test Valve",
        port="COM7",  # Using COM7 (USB-SERIAL CH340)
        valve_type="6-way",
        baudrate=9600,
        timeout=2.0,  # Increased timeout
    )
    
    try:
        print("Connecting to valve...")
        valve.connect()
        print("Connected, waiting for valve initialization...")
        time.sleep(2.0)  # Longer wait for initialization
        
        print("Firmware Version:", valve.check_firmware_version())
        
        print("Moving to home position...")
        valve.move_home()
        time.sleep(5)
        print("Current Position after homing:", valve.check_current_position())
        
        print("Moving to position 5...")
        valve.go_to_position(5)
        time.sleep(5)
        print("Current Position after moving to 5:", valve.check_current_position())
        
        print("Moving clockwise 2 positions...")
        valve.move_clockwise(2)
        time.sleep(5)
        print("Current Position after moving clockwise 2:", valve.check_current_position())
        
        print("Moving counterclockwise 1 position...")
        valve.move_counterclockwise()
        time.sleep(5)
        print("Current Position after moving counterclockwise 1:", valve.check_current_position())
        
    finally:
        print("Closing valve connection...")
        valve.close()

if __name__ == "__main__":
    test_vici_valve()