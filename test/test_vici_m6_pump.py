import sys
import time
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from devices.pump import Pump
from devices.pump_devices.vici_m6_pumps import VICI_M6_Pumps

def test_vici_m6_pump():
    # Initialize the pump with appropriate COM port
    pump = VICI_M6_Pumps(
        port='COM22',  # Using COM22 for VICI M6 pump
        baud_rate=9600,
        timeout=1
    )
    
    try:
        # Test 1: Connection and Parameter Initialization
        print("\n=== Test 1: Connection and Parameters ===")
        pump.start()
        print("Initial pump parameters:")
        pump.get_pump_parameters()
        
        # Test 2: Flow Rate Configuration
        print("\n=== Test 2: Flow Rate Configuration ===")
        test_rates = [200, 1000, 1500, 2000]  # Test different calibrated flow rates
        for rate in test_rates:
            print(f"\nTesting flow rate: {rate} µL/min")
            print("Aspirating mode:")
            pump.set_flow_rate(rate, "aspirating")
            time.sleep(1)
            print("\nDispensing mode:")
            pump.set_flow_rate(rate, "dispensing")
            time.sleep(1)
            
        # Test 3: Volume Dispensing
        print("\n=== Test 3: Volume Dispensing Test ===")
        test_volumes = [
            (200, 100),    # 100µL at 200µL/min
            (1000, 500),   # 500µL at 1000µL/min
            (1500, 750),   # 750µL at 1500µL/min
        ]
        
        for rate, volume in test_volumes:
            print(f"\nDispensing {volume}µL at {rate}µL/min")
            pump.set_flow_rate(rate, "dispensing")
            start_time = time.time()
            pump.pump_solution(volume)
            elapsed_time = time.time() - start_time
            print(f"Operation completed in {elapsed_time:.2f} seconds")
            time.sleep(2)  # Wait between operations
            
        # Test 4: Aspirate Operations
        print("\n=== Test 4: Aspirate Operations ===")
        test_volumes = [
            (200, 100),    # 100µL at 200µL/min
            (1000, 500),   # 500µL at 1000µL/min
        ]
        
        for rate, volume in test_volumes:
            print(f"\nAspirating {volume}µL at {rate}µL/min")
            pump.set_flow_rate(rate, "aspirating")
            start_time = time.time()
            pump.pump_solution(volume)
            elapsed_time = time.time() - start_time
            print(f"Operation completed in {elapsed_time:.2f} seconds")
            time.sleep(2)  # Wait between operations
            
        # Test 5: Continuous Operation Test
        print("\n=== Test 5: Continuous Operation Test ===")
        print("Performing alternating dispense/aspirate cycle...")
        
        for i in range(3):  # 3 cycles
            print(f"\nCycle {i+1}:")
            # Dispense phase
            print("Dispensing...")
            pump.set_flow_rate(1000, "dispensing")
            pump.pump_solution(200)
            time.sleep(1)
            
            # Aspirate phase
            print("Aspirating...")
            pump.set_flow_rate(1000, "aspirating")
            pump.pump_solution(200)
            time.sleep(1)
        
    finally:
        # Clean shutdown
        print("\n=== Cleaning Up ===")
        print("Stopping pump operations...")
        pump.stop()
        print("Closing connection...")
        pump.stop_connection()
        print("✓ Cleanup successful")

if __name__ == "__main__":
    print("Starting VICI M6 Pump Tests")
    print("===========================")
    try:
        test_vici_m6_pump()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
    print("\nTest sequence complete")