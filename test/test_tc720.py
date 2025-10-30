import sys
import time
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from devices.devices import Device
from devices.temperature_controller import TemperatureController
from devices.temperature_controller_devices.TC720 import TC720

def test_tc720():
    # Initialize the controller with appropriate COM port
    # Note: Update the port if needed based on your system
    controller = TC720(
        name="TC-720 Test Controller",
        port='COM12',  # Update this to match your setup
        baudrate=230400,
        timeout=1
    )
    
    try:
        # Test 1: Connection
        print("\n=== Test 1: Testing Connection ===")
        print("Connecting to TC720...")
        controller.connect()
        assert controller.connected, "Controller should be connected"
        print("✓ Connection successful")
        
        # Test 2: Initial Status Check
        print("\n=== Test 2: Initial Status Check ===")
        status = controller.status()
        print(f"Initial status: {status}")
        assert status['ok'], f"Controller status should be ok, got: {status['msg']}"
        print("✓ Initial status check passed")
        
        # Test 3: Temperature Reading (Both Sensors)
        print("\n=== Test 3: Temperature Reading Test ===")
        try:
            temp1 = controller.read_temperature(sensor=1)
            print(f"Temperature Sensor 1: {temp1:.2f}°C")
            temp2 = controller.read_temperature(sensor=2)
            print(f"Temperature Sensor 2: {temp2:.2f}°C")
            print("✓ Temperature reading test passed")
        except Exception as e:
            print(f"! Temperature reading test failed: {e}")
            raise
        
        # Test 4: Temperature Setting
        print("\n=== Test 4: Temperature Setting Test ===")
        test_temps = [25.0, 30.0, 35.0]  # Safe test temperatures
        for target_temp in test_temps:
            try:
                print(f"\nSetting temperature to {target_temp}°C")
                controller.set_temperature(target_temp)
                time.sleep(2)  # Wait for the command to process
                
                # Read current temperature
                current_temp = controller.read_temperature(sensor=1)
                print(f"Current temperature: {current_temp:.2f}°C")
                
                # Check status
                status = controller.status()
                print(f"Status after setting {target_temp}°C: {status}")
                assert status['ok'], f"Controller status should be ok, got: {status['msg']}"
                
            except Exception as e:
                print(f"! Temperature setting test failed at {target_temp}°C: {e}")
                raise
        print("✓ Temperature setting test passed")
        
        # Test 5: Error Handling
        print("\n=== Test 5: Error Handling Test ===")
        try:
            # Test invalid temperature
            print("Testing invalid temperature handling...")
            invalid_temps = [-273.16, 1000.0]  # Temperatures outside normal range
            for temp in invalid_temps:
                try:
                    controller.set_temperature(temp)
                except Exception as e:
                    print(f"✓ Successfully caught invalid temperature {temp}°C: {e}")
        except Exception as e:
            print(f"! Error handling test failed: {e}")
            raise
        
    finally:
        # Clean shutdown
        print("\n=== Cleaning Up ===")
        print("Setting safe temperature before shutdown...")
        try:
            controller.set_temperature(25.0)  # Set to room temperature
            time.sleep(1)
            print("Stopping controller...")
            controller.stop()
            print("✓ Cleanup successful")
        except Exception as e:
            print(f"! Cleanup failed: {e}")
            raise

if __name__ == "__main__":
    print("Starting TC720 Temperature Controller Tests")
    print("=========================================")
    test_tc720()