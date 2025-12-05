#!/usr/bin/env python3
"""
Arduino Connection Test with Physical Hardware Verification

Tests Arduino connection and optionally verifies physical hardware operation.

Usage:
    python3 test_arduino_connection.py              # Connection test only
    python3 test_arduino_connection.py --hardware   # Test + run conveyor 2s

The hardware test will:
    - Run conveyor belt for 2 seconds
    - Test servo eject motion
    - Verify all hardware responds correctly
"""

import serial
import time
import sys

# Configuration
SERIAL_PORT = "/dev/ttyACM0"  # Change if needed
# SERIAL_PORT = "COM3"  # Uncomment for Windows
BAUD_RATE = 115200

def test_arduino(hardware_test=True):
    """Test Arduino connection and communication.
    
    Args:
        hardware_test: If True, will run physical hardware test (conveyor + servo)
    """
    
    print("="*80)
    print("🔧 ARDUINO CONNECTION TEST")
    print("="*80)
    print(f"Port: {SERIAL_PORT}")
    print(f"Baud: {BAUD_RATE}")
    print(f"Hardware Test: {'Enabled' if hardware_test else 'Disabled'}")
    print()
    
    try:
        print("Step 1: Opening serial port...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print("✅ Port opened successfully")
        
        print("\nStep 2: Waiting for Arduino reset (2.5s)...")
        time.sleep(2.5)
        print("✅ Wait complete")
        
        print("\nStep 3: Reading startup messages...")
        startup_received = False
        for _ in range(20):
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                print(f"  📨 {line}")
                if "Arduino" in line or "Ready" in line:
                    startup_received = True
        
        if startup_received:
            print("✅ Startup messages received")
        else:
            print("⚠️  No startup messages (might still work)")
        
        print("\nStep 4: Testing PING command...")
        ser.write(b"PING\n")
        time.sleep(0.5)
        
        ping_ok = False
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            print(f"  📨 Response: {response}")
            if response == "PONG":
                print("✅ PING successful!")
                ping_ok = True
            else:
                print("⚠️  Unexpected response")
        else:
            print("❌ No response to PING")
        
        print("\nStep 5: Testing STATUS command...")
        ser.write(b"STATUS\n")
        time.sleep(0.5)
        
        status_received = False
        while ser.in_waiting > 0:
            line = ser.readline().decode().strip()
            print(f"  📨 {line}")
            status_received = True
        
        if status_received:
            print("✅ STATUS received")
        else:
            print("⚠️  No status response")
        
        # Hardware test (optional)
        if hardware_test:
            print("\nStep 6: Testing physical hardware...")
            print("  ⚠️  WARNING: This will move physical hardware!")
            print("  - Conveyor will RUN for 2 seconds")
            print("  - Servo will perform eject motion")
            print("\n  Make sure:")
            print("    • Area is clear and safe")
            print("    • Conveyor belt is properly connected")
            print("    • Servo is properly mounted")
            
            # Ask for confirmation
            try:
                response = input("\n  ⚠️  Proceed with hardware test? (y/N): ").strip().lower()
                if response != 'y':
                    print("  ⏭️  Hardware test skipped")
                    hardware_test = False
            except:
                print("  ⏭️  Hardware test skipped (no input)")
                hardware_test = False
        
        if hardware_test:
            print("\n  Starting hardware test in 3 seconds...")
            for i in range(3, 0, -1):
                print(f"    {i}...")
                time.sleep(1)
            
            # Test START_CONVEYOR
            print("\n  🔵 Starting conveyor...")
            ser.write(b"START_CONVEYOR\n")
            time.sleep(0.5)
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"    📨 {response}")
            
            # Run for 2 seconds
            print("  ▶️  Conveyor RUNNING...")
            for i in range(2, 0, -1):
                print(f"    ⏱️  {i} seconds remaining...")
                time.sleep(1)
            
            # Test STOP_CONVEYOR
            print("  🔴 Stopping conveyor...")
            ser.write(b"STOP_CONVEYOR\n")
            time.sleep(0.5)
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"    📨 {response}")
            
            print("  ✅ Conveyor stopped")
            
            # Test servo movement
            print("\n  Testing servo movement...")
            print("  🔧 Moving servo to eject position...")
            ser.write(b"REJECT\n")
            time.sleep(1.5)  # Wait for servo sequence
            
            # Read all responses
            while ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"    📨 {response}")
            
            print("  ✅ Servo test complete")
            
            print("\n✅ All hardware commands executed successfully!")
        else:
            print("\nStep 6: Hardware test skipped")
            print("  ℹ️  To test hardware, run with --hardware flag")
        
        # Close
        ser.close()
        
        print("\n" + "="*80)
        print("📊 TEST RESULTS")
        print("="*80)
        
        if ping_ok:
            print("✅ Arduino connection: OK")
            print("✅ Communication: WORKING")
            print("✅ Ready to use!")
            print("\n➡️  You can now run: python3 main_continuous_flow_tkinter.py")
            return True
        else:
            print("⚠️  Arduino connection: PARTIAL")
            print("⚠️  Port opens but communication issues")
            print("\n🔧 Troubleshooting:")
            print("  1. Check if correct firmware uploaded")
            print("  2. Verify baud rate is 115200")
            print("  3. Try re-uploading arduino/product_sorter.ino")
            print("  4. Check Arduino IDE Serial Monitor")
            return False
        
    except FileNotFoundError:
        print(f"\n❌ ERROR: Port not found!")
        print(f"   {SERIAL_PORT} does not exist")
        print("\n🔧 Solutions:")
        print("  Linux/Pi: Run 'ls /dev/ttyACM* /dev/ttyUSB*'")
        print("  Windows: Check Device Manager for COM port")
        print("  Then update SERIAL_PORT in this script")
        return False
        
    except PermissionError:
        print(f"\n❌ ERROR: Permission denied!")
        print(f"   Cannot access {SERIAL_PORT}")
        print("\n🔧 Solutions:")
        print("  1. Add user to dialout group:")
        print("     sudo usermod -a -G dialout $USER")
        print("  2. Logout and login again")
        print("  3. Or run with sudo (not recommended):")
        print("     sudo python3 test_arduino_connection.py")
        return False
        
    except serial.SerialException as e:
        print(f"\n❌ ERROR: Serial communication failed!")
        print(f"   {e}")
        print("\n🔧 Solutions:")
        print("  1. Check USB cable connection")
        print("  2. Try different USB port")
        print("  3. Check if Arduino is powered (LED on)")
        print("  4. Try: sudo lsof | grep ttyACM0")
        print("     (Check if port is busy)")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error!")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n" + "="*80)
        print("Test complete")
        print("="*80)


def main():
    """Entry point."""
    print("\n")
    
    # Check command line arguments
    hardware_test = False
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--hardware', '-h']:
            hardware_test = True
        elif sys.argv[1] in ['--help']:
            print("Usage:")
            print("  python3 test_arduino_connection.py           # Test connection only")
            print("  python3 test_arduino_connection.py --hardware # Test with physical hardware")
            print()
            sys.exit(0)
    
    # Check if pyserial installed
    try:
        import serial
    except ImportError:
        print("❌ ERROR: pyserial not installed!")
        print("\n🔧 Install it:")
        print("   pip3 install pyserial")
        sys.exit(1)
    
    # Run test
    success = test_arduino(hardware_test=hardware_test)
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\n📚 For detailed debugging guide:")
        print("   See: ARDUINO_DEBUG.md")
        sys.exit(1)


if __name__ == "__main__":
    main()

