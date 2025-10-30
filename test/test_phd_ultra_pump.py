import sys
import time
import asyncio
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from devices.pump import Pump
from devices.pump_devices.phd_ultra_pumps import PhdUltraPump

def parse_status(status: str) -> dict:
    """Parse the pump status string to extract volume and rate information."""
    try:
        parts = status.split()
        if len(parts) >= 3:
            # The second value in status string represents dispensed volume in nL
            volume_nl = float(parts[1])
            return {
                "volume_ul": volume_nl / 1000,  # Convert nL to µL
                "status": "running" if "I" in parts[-1] else "stopped"
            }
    except (ValueError, IndexError):
        pass
    return {"volume_ul": 0.0, "status": "unknown"}

async def test_phd_ultra_pump():
    # Initialize the pump with appropriate COM port
    pump = PhdUltraPump(
        port="COM19",  # Update this to match your setup
        baudrate=9600,
        timeout=1.0,
        address=0,
        pause=0.25  # Increased pause for reliability
    )
    
    try:
        # Test 1: Basic Connection and Version Check
        print("\n=== Test 1: Connection and Version Check ===")
        print("Connecting to pump...")
        pump.connect()
        version = pump.get_version()
        print(f"Pump Version: {version}")
        status = pump.get_status()
        print(f"Initial Status: {status}")
        
        # Test 2: Syringe Configuration
        print("\n=== Test 2: Syringe Configuration ===")
        print("Available syringe sizes (mL):", list(pump.AIR_TITE_SYRINGES.keys()))
        print("Configuring for 10mL Air-Tite syringe...")
        response = pump.select_syringe(10.0)
        print(f"Syringe configuration response: {response}")
        
        # Test 3: Mode Configuration
        print("\n=== Test 3: Mode Configuration ===")
        print("Setting Quick Start Infuse mode...")
        mode = pump.quick_start_infuse()
        print(f"Current mode: {mode}")
        
        # Test 4: Multiple Syringe Sizes and Flow Rates
        print("\n=== Test 4: Syringe Sizes and Flow Rates ===")
        test_configs = [
            (5.0, [100.0, 250.0]),    # 5mL syringe at different rates
            (10.0, [200.0, 500.0]),   # 10mL syringe at different rates
            (20.0, [400.0, 1000.0]),  # 20mL syringe at different rates
        ]
        
        for syringe_size, rates in test_configs:
            print(f"\nConfiguring {syringe_size}mL syringe...")
            response = pump.select_syringe(syringe_size)
            print(f"Syringe configuration response: {response}")
            
            for rate in rates:
                print(f"\nTesting {rate} μL/min flow rate...")
                response = pump._set_rate_sync(rate)
                print(f"Rate setting response: {response}")
                time.sleep(1)
        
        # Test 5: Volume Dispensing with Progress Tracking
        print("\n=== Test 5: Volume Dispensing Test with Progress ===")
        
        # Configure for longer dispensing test
        print("\nConfiguring 10mL syringe for dispensing test...")
        pump.select_syringe(10.0)
        
        test_volumes = [
            (500.0, 1000.0),    # 500µL at 1000µL/min (30 sec)
            (1000.0, 500.0),    # 1000µL at 500µL/min (2 min)
            (2000.0, 2000.0),   # 2000µL at 2000µL/min (1 min)
        ]
        
        for target_vol, rate in test_volumes:
            print(f"\nDispensing {target_vol} μL at {rate} μL/min")
            pump.clear_volume_counter()
            print("Volume counter cleared")
            
            # Set up the dispense
            pump._set_rate_sync(rate)
            pump.set_target_volume(target_vol)
            print(f"Starting dispense...")
            
            # Run and monitor with volume tracking
            pump.run()
            estimated_time = (target_vol / rate) * 60  # seconds
            print(f"Estimated time: {estimated_time:.1f} seconds")
            
            # Wait and check status periodically with volume tracking
            start_time = time.time()
            last_volume = 0.0
            
            while time.time() - start_time < estimated_time + 2:
                status = pump.get_status()
                parsed_status = parse_status(status)
                current_volume = parsed_status["volume_ul"]
                
                # Calculate flow rate and progress
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    current_rate = current_volume / (elapsed_time / 60)  # µL/min
                    progress = (current_volume / target_vol) * 100 if target_vol > 0 else 0
                    
                    print(f"Progress: {progress:.1f}% | "
                          f"Dispensed: {current_volume:.1f}µL | "
                          f"Target: {target_vol}µL | "
                          f"Rate: {current_rate:.1f}µL/min")
                
                # Calculate instantaneous flow rate
                volume_change = current_volume - last_volume
                if volume_change > 0:
                    inst_rate = volume_change * 60  # µL/min
                    print(f"Instantaneous rate: {inst_rate:.1f}µL/min")
                
                last_volume = current_volume
                time.sleep(1)
            
            pump.stop()
            
            # Final volume check
            status = pump.get_status()
            parsed_status = parse_status(status)
            final_volume = parsed_status["volume_ul"]
            print(f"Dispense complete - Total volume dispensed: {final_volume:.1f}µL")
        
        # Test 6: Error Handling
        print("\n=== Test 6: Error Handling Test ===")
        try:
            print("Testing invalid syringe size...")
            pump.select_syringe(7.5)  # This should raise an error
        except ValueError as e:
            print(f"✓ Successfully caught invalid syringe size: {e}")
        
        try:
            print("\nTesting invalid rate...")
            await pump.set_rate(-100)  # This should raise an error
        except ValueError as e:
            print(f"✓ Successfully caught invalid rate: {e}")
            
    finally:
        # Clean shutdown
        print("\n=== Cleaning Up ===")
        print("Stopping pump...")
        pump.stop()
        print("Closing connection...")
        pump.close()
        print("✓ Cleanup successful")

if __name__ == "__main__":
    print("Starting PHD Ultra Pump Tests")
    print("============================")
    try:
        asyncio.run(test_phd_ultra_pump())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
    print("\nTest sequence complete")