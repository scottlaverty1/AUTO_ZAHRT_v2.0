import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devices.pump_devices.vici_m6_pumps import VICI_M6_Pumps

def test_vici_m6_progress():
    # Initialize pump (adjust COM port as needed)
    pump = VICI_M6_Pumps(port='COM21')
    pump.start()
    
    # Test aspirating with different flow rates and volumes
    test_conditions = [
        (200, 100),    # Slow aspiration: 200 µL/min for 100 µL
        (1000, 500),   # Medium speed: 1000 µL/min for 500 µL
        (2000, 1000),  # Fast aspiration: 2000 µL/min for 1000 µL
    ]
    
    for flow_rate, volume in test_conditions:
        print(f"\nTesting aspirating at {flow_rate} µL/min for {volume} µL:")
        pump.set_flow_rate(flow_rate, "aspirating")
        pump.pump_solution(volume)
        time.sleep(2)  # Brief pause between tests
    
    pump.stop_connection()

if __name__ == "__main__":
    test_vici_m6_progress()