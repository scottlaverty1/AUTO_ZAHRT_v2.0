import sys
import time
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from devices.pump import Pump
from devices.pump_devices.vici_m6_pumps import VICI_M6_Pumps

def test_vici_m6_long_dispense():
    # Initialize the pump with appropriate COM port
    pump = VICI_M6_Pumps(
        port='COM22',  # Using COM22 for VICI M6 pump
        baud_rate=9600,
        timeout=1
    )
    
    try:
        # Test 1: Connection
        print("\n=== Test 1: Establishing Connection ===")
        pump.start()
        
        # Test 2: Long Dispensing Cycles
        print("\n=== Test 2: Long Dispensing Cycles ===")
        
        # Test various volumes and flow rates
        test_configs = [
            # (volume_ul, flow_rate_ul_min, description)
            (1000, 500, "Medium volume, moderate speed"),
            (2000, 1000, "Large volume, high speed"),
            (3000, 200, "Large volume, slow speed"),
        ]
        
        for volume, flow_rate, description in test_configs:
            print(f"\n--- Starting: {description} ---")
            print(f"Volume: {volume} µL at {flow_rate} µL/min")
            
            # Start dispensing
            pump.set_flow_rate(flow_rate, "dispensing")
            start_time = time.time()
            
            try:
                pump.pump_solution(volume)
            except KeyboardInterrupt:
                print("\nDispensing interrupted by user!")
                pump.stop()
                continue
                
            print(f"Cycle completed. Waiting 5 seconds before next cycle...")
            time.sleep(5)
        
        # Test 3: Continuous Dispensing Cycle
        print("\n=== Test 3: Continuous Dispensing Cycle ===")
        print("Running 3 continuous dispense cycles of 1500 µL each...")
        
        for cycle in range(3):
            print(f"\nCycle {cycle + 1}/3:")
            pump.set_flow_rate(1000, "dispensing")
            pump.pump_solution(1500)
            print("Waiting 3 seconds between cycles...")
            time.sleep(3)
            
    finally:
        # Clean shutdown
        print("\n=== Cleaning Up ===")
        print("Stopping pump operations...")
        pump.stop()
        print("Closing connection...")
        pump.stop_connection()
        print("✓ Cleanup successful")

if __name__ == "__main__":
    print("Starting VICI M6 Pump Long Dispensing Tests")
    print("==========================================")
    try:
        test_vici_m6_long_dispense()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
    print("\nTest sequence complete")