#!/usr/bin/env python3
"""
Slow Arduino Test - With longer delays to catch startup messages
"""

import serial
import time
import sys

PORT = "/dev/ttyACM0"
BAUD = 115200

print("="*80)
print("🐌 SLOW ARDUINO TEST (with longer delays)")
print("="*80)
print(f"Port: {PORT}")
print(f"Baud: {BAUD}")
print()

try:
    print("Step 1: Opening serial port...")
    ser = serial.Serial(PORT, BAUD, timeout=2)
    print("✅ Port opened")
    
    print("\nStep 2: Waiting for Arduino reset...")
    print("  (Arduino resets when serial port opens)")
    print("  Waiting 5 seconds to be safe...")
    time.sleep(5)
    print("✅ Wait complete")
    
    print("\nStep 3: Listening for startup messages (15 seconds)...")
    print("  Any data will be shown below:")
    print("  " + "-"*70)
    
    data_received = False
    start_time = time.time()
    
    while (time.time() - start_time) < 15:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"  📨 {line}")
                    data_received = True
            except:
                pass
        time.sleep(0.05)
    
    print("  " + "-"*70)
    
    if data_received:
        print("\n✅ STARTUP MESSAGES RECEIVED!")
        print("   Firmware is working correctly.")
    else:
        print("\n❌ NO STARTUP MESSAGES")
        print("   Firmware might not be uploaded.")
        print("\n🔧 Try:")
        print("   1. Open Arduino IDE Serial Monitor")
        print("   2. Press RESET button on Arduino")
        print("   3. Check if messages appear there")
    
    print("\nStep 4: Manual PING test...")
    print("  Sending: PING")
    ser.write(b"PING\n")
    time.sleep(2)
    
    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"  Response: {response}")
        if response == "PONG":
            print("  ✅ PING successful!")
        else:
            print(f"  ⚠️  Got: '{response}' (expected: 'PONG')")
    else:
        print("  ❌ No response to PING")
        print("\n  This means:")
        print("    - Arduino receives commands (hardware works)")
        print("    - But doesn't send responses back")
        print("    - Firmware issue or wrong firmware uploaded")
    
    print("\nStep 5: Manual STATUS test...")
    print("  Sending: STATUS")
    ser.write(b"STATUS\n")
    time.sleep(2)
    
    print("  Response:")
    if ser.in_waiting > 0:
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"    {line}")
    else:
        print("    (no response)")
    
    ser.close()
    
    print("\n" + "="*80)
    print("🏁 TEST COMPLETE")
    print("="*80)
    print("\nIf you see startup messages and PONG:")
    print("  → ✅ Everything works! Run: python3 main_continuous_flow_tkinter.py")
    print("\nIf no startup messages:")
    print("  → ❌ Firmware not uploaded correctly")
    print("  → Check Arduino IDE Serial Monitor first!")
    print("="*80)

except FileNotFoundError:
    print(f"❌ ERROR: Port {PORT} not found")
    sys.exit(1)
except PermissionError:
    print(f"❌ ERROR: Permission denied for {PORT}")
    print("Run: sudo usermod -a -G dialout $USER")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

