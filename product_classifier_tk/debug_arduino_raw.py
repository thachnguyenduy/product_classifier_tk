#!/usr/bin/env python3
"""
Raw Arduino Serial Debug
Tests raw serial communication without any assumptions.
"""

import serial
import time
import sys

PORT = "/dev/ttyACM0"
BAUD = 115200

print("="*80)
print("🔍 RAW ARDUINO SERIAL DEBUG")
print("="*80)
print(f"Port: {PORT}")
print(f"Baud: {BAUD}")
print()

try:
    print("Opening port...")
    ser = serial.Serial(PORT, BAUD, timeout=2)
    print("✅ Port opened")
    
    print("\nWaiting 3 seconds for Arduino reset...")
    time.sleep(3)
    
    print("\n" + "="*80)
    print("LISTENING FOR ANY DATA (10 seconds)...")
    print("="*80)
    print("(Press Ctrl+C to stop early)")
    print()
    
    start_time = time.time()
    data_received = False
    
    try:
        while (time.time() - start_time) < 10:
            if ser.in_waiting > 0:
                try:
                    # Try to read as text
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"📨 TEXT: {line}")
                        data_received = True
                except:
                    # Read as raw bytes
                    raw = ser.read(ser.in_waiting)
                    print(f"📨 RAW: {raw}")
                    data_received = True
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    print("\n" + "="*80)
    
    if data_received:
        print("✅ DATA RECEIVED FROM ARDUINO")
        print("\nArduino is sending data, but might not be the correct firmware.")
        print("\n🔧 Next steps:")
        print("  1. Check what data was received above")
        print("  2. If it's not the startup message, re-upload firmware")
        print("  3. Use Arduino IDE Serial Monitor to verify")
    else:
        print("❌ NO DATA RECEIVED FROM ARDUINO")
        print("\nArduino is not sending ANY data!")
        print("\n🔧 This means:")
        print("  1. Firmware is NOT uploaded, OR")
        print("  2. Arduino is stuck/frozen, OR")
        print("  3. Baud rate is wrong")
        print("\n📝 Actions:")
        print("  1. Open Arduino IDE")
        print("  2. Upload arduino/product_sorter.ino")
        print("  3. Open Serial Monitor (115200 baud)")
        print("  4. Press RESET on Arduino")
        print("  5. Should see startup messages")
    
    print("\n" + "="*80)
    print("\nNow testing manual commands...")
    print("="*80)
    
    # Clear buffer
    ser.reset_input_buffer()
    
    # Test PING
    print("\nSending: PING")
    ser.write(b"PING\n")
    time.sleep(1)
    
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"Response: {response}")
        if response == "PONG":
            print("✅ PING/PONG works!")
        else:
            print(f"⚠️  Unexpected response: {response}")
    else:
        print("❌ No response to PING")
    
    # Test STATUS
    print("\nSending: STATUS")
    ser.write(b"STATUS\n")
    time.sleep(1)
    
    if ser.in_waiting > 0:
        print("Response:")
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"  {line}")
    else:
        print("❌ No response to STATUS")
    
    ser.close()
    print("\n✅ Test complete")
    
except FileNotFoundError:
    print(f"❌ ERROR: Port {PORT} not found!")
    print("\nCheck:")
    print("  ls /dev/ttyACM* /dev/ttyUSB*")
    sys.exit(1)
    
except PermissionError:
    print(f"❌ ERROR: Permission denied for {PORT}")
    print("\nFix:")
    print("  sudo usermod -a -G dialout $USER")
    print("  Then logout/login")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

