#!/usr/bin/env python3
# ============================================
# COCA-COLA BOTTLE SORTING SYSTEM
# Main Entry Point
# ============================================
"""
Coca-Cola Bottle Sorting System using AI, Line Crossing, and Tkinter UI

Project: Graduation Project
System: Raspberry Pi 5 (8GB) + Arduino Uno + USB Camera
Model: YOLO best.pt (NCNN will replace later without changing logic)

Hardware:
- Raspberry Pi 5: AI inference, tracking, line crossing, database, UI
- Arduino Uno: IR sensor, servo control, relay control
- USB Camera: Real-time video capture
- IR Sensor: Physical bottle detection at servo position
- Servo 9g: NG bottle blocking
- Relay 5V: Conveyor belt control

Conveyor Direction: RIGHT → LEFT

Classification Logic:
1. Continuously track bottles and accumulate detected classes
2. When bottle crosses virtual line (RIGHT → LEFT):
   - Finalize classification
   - Send result to Arduino ('O' = OK, 'N' = NG)
3. When IR sensor triggers:
   - Arduino actuates servo based on last received classification

Class Names (EXACT ORDER):
1. Cap-Defect (NG)
2. Filling-Defect (NG)
3. Label-Defect (NG)
4. Wrong-Product (NG)
5. cap (required for OK)
6. coca (identity only, not for classification)
7. filled (required for OK)
8. label (required for OK)

Classification Rules:
- NG if ANY defect detected
- OK if ALL good classes (cap + label + filled) present AND NO defects
- Otherwise NG
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from core.camera import Camera, DummyCamera
from core.ai import AIEngine
from core.hardware import HardwareController, DummyHardwareController
from core.database import Database
from ui.main_window import MainWindow


class SortingSystemApp:
    """
    Main application class
    
    Initializes all components and runs the Tkinter UI
    """
    
    def __init__(self):
        print("\n" + "="*70)
        print(" " * 10 + "COCA-COLA BOTTLE SORTING SYSTEM")
        print(" " * 20 + "Graduation Project")
        print("="*70)
        print(f"Version: {config.VERSION}")
        print(f"Mode: {config.MODE}")
        print(f"Model: {config.MODEL_PATH_YOLO}")
        print("="*70 + "\n")
        
        self.root = None
        self.camera = None
        self.ai = None
        self.hardware = None
        self.database = None
        self.main_window = None
        
        self._initialize_components()
        self._create_ui()
    
    def _initialize_components(self):
        """Initialize all system components"""
        print("[Initialization] Starting components...\n")
        
        # 1. Database
        print("[1/4] Initializing database...")
        try:
            self.database = Database()
            print("✅ Database initialized\n")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}\n")
            raise
        
        # 2. AI Engine
        print("[2/4] Loading AI model...")
        try:
            self.ai = AIEngine()
            print("✅ AI engine loaded\n")
        except Exception as e:
            print(f"❌ AI engine failed: {e}\n")
            raise
        
        # 3. Camera
        print("[3/4] Opening camera...")
        try:
            if config.USE_DUMMY_CAMERA:
                self.camera = DummyCamera()
                print("⚠️ Using DUMMY camera (testing mode)")
            else:
                self.camera = Camera()
                if not self.camera.is_opened():
                    print("❌ Camera failed to open")
                    raise RuntimeError("Camera not available")
            
            self.camera.start()
            print("✅ Camera started\n")
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}\n")
            raise
        
        # 4. Hardware (Arduino)
        print("[4/4] Connecting to Arduino...")
        try:
            if config.USE_DUMMY_HARDWARE:
                self.hardware = DummyHardwareController()
                print("⚠️ Using DUMMY hardware (testing mode)")
            else:
                self.hardware = HardwareController()
                if not self.hardware.is_connected():
                    print("⚠️ Arduino not connected")
                    print(f"   Port: {config.ARDUINO_PORT}")
                    print(f"   Baudrate: {config.ARDUINO_BAUDRATE}")
                    print("\nYou can:")
                    print("  1. Check Arduino connection and port")
                    print("  2. Continue in DUMMY mode (set USE_DUMMY_HARDWARE = True)")
                    print("  3. Exit and fix hardware\n")
                    
                    response = input("Continue anyway? (y/n): ")
                    if response.lower() != 'y':
                        raise RuntimeError("Arduino not connected")
            
            print("✅ Hardware initialized\n")
        except Exception as e:
            print(f"❌ Hardware initialization failed: {e}\n")
            raise
        
        print("="*70)
        print("✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY!")
        print("="*70 + "\n")
    
    def _create_ui(self):
        """Create Tkinter UI"""
        print("[UI] Creating interface...\n")
        
        try:
            self.root = tk.Tk()
            self.main_window = MainWindow(
                self.root,
                self.camera,
                self.ai,
                self.hardware,
                self.database
            )
            
            print("✅ UI ready!\n")
        except Exception as e:
            print(f"❌ UI creation failed: {e}\n")
            raise
    
    def run(self):
        """Run the application"""
        print("="*70)
        print("🚀 SYSTEM READY TO START")
        print("="*70)
        print("\nInstructions:")
        print("1. Click 'START SYSTEM' button in the UI")
        print("2. Place bottles on conveyor (moving RIGHT → LEFT)")
        print("3. Bottles will be detected when crossing the cyan line")
        print("4. Classification result sent to Arduino immediately")
        print("5. IR sensor triggers servo action at physical position")
        print("\nClassification Rules:")
        print("  ✅ OK: All good classes (cap + label + filled) present, no defects")
        print("  ❌ NG: Any defect OR missing good classes")
        print("\n" + "="*70 + "\n")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n[Info] Interrupted by user")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources"""
        print("\n[Cleanup] Shutting down components...\n")
        
        if self.camera:
            self.camera.stop()
            print("✅ Camera stopped")
        
        if self.hardware:
            self.hardware.stop()
            print("✅ Hardware disconnected")
        
        print("\n" + "="*70)
        print("✅ CLEANUP COMPLETE - GOODBYE!")
        print("="*70 + "\n")


def main():
    """Main function"""
    try:
        app = SortingSystemApp()
        app.run()
    except KeyboardInterrupt:
        print("\n\n[Info] Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        print("\n" + "="*70)
        print("❌ FATAL ERROR")
        print("="*70)
        print(f"Error: {e}\n")
        import traceback
        traceback.print_exc()
        print("\n" + "="*70)
        sys.exit(1)


if __name__ == "__main__":
    main()
