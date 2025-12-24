#!/usr/bin/env python3
"""
Coca-Cola Sorting System - Main Entry Point (CONTINUOUS MODE)
Continuous conveyor operation with circular buffer queue for rejection timing
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.camera import Camera, DummyCamera
from core.ai import AIEngine
from core.hardware import HardwareController, DummyHardwareController
from core.database import Database
from ui.main_window import MainWindow
import config


class ContinuousSortingSystem:
    """
    Main application class for Continuous Coca-Cola Sorting System
    """
    
    def __init__(self):
        """Initialize the application"""
        print("=" * 70)
        print("🥤 COCA-COLA SORTING SYSTEM - CONTINUOUS MODE")
        print("=" * 70)
        print()
        
        self.root = None
        self.camera = None
        self.ai = None
        self.hardware = None
        self.database = None
        self.main_window = None
    
    def initialize_components(self):
        """Initialize all system components"""
        print("[System] Initializing components...")
        
        try:
            # 1. Initialize Database
            print("\n[1/4] Initializing database...")
            self.database = Database(db_path=config.DATABASE_PATH)
            print("      ✓ Database ready")
            
            # 2. Initialize AI Engine
            print("\n[2/4] Initializing AI engine...")
            self.ai = AIEngine(model_path=config.MODEL_PATH, config=config)
            print("      ✓ AI engine ready")
            
            # 3. Initialize Camera
            print("\n[3/4] Initializing camera...")
            if config.USE_DUMMY_CAMERA:
                print("      Using DUMMY camera (testing mode)")
                self.camera = DummyCamera(
                    width=config.CAMERA_WIDTH,
                    height=config.CAMERA_HEIGHT
                )
            else:
                self.camera = Camera(
                    camera_id=config.CAMERA_ID,
                    width=config.CAMERA_WIDTH,
                    height=config.CAMERA_HEIGHT,
                    fps=config.CAMERA_FPS,
                    exposure=config.CAMERA_EXPOSURE,
                    auto_exposure=config.CAMERA_AUTO_EXPOSURE
                )
            
            if not self.camera.start():
                print("      [WARNING] Failed to start camera. Switching to dummy mode...")
                self.camera = DummyCamera(
                    width=config.CAMERA_WIDTH,
                    height=config.CAMERA_HEIGHT
                )
                self.camera.start()
            
            print("      ✓ Camera ready")
            
            # 4. Initialize Hardware Controller
            print("\n[4/4] Initializing hardware controller...")
            if config.USE_DUMMY_HARDWARE:
                print("      Using DUMMY hardware (testing mode)")
                self.hardware = DummyHardwareController(
                    port=config.ARDUINO_PORT,
                    baudrate=config.ARDUINO_BAUDRATE,
                    timeout=config.ARDUINO_TIMEOUT
                )
            else:
                self.hardware = HardwareController(
                    port=config.ARDUINO_PORT,
                    baudrate=config.ARDUINO_BAUDRATE,
                    timeout=config.ARDUINO_TIMEOUT
                )
            
            if not self.hardware.connect():
                print("      [WARNING] Failed to connect to Arduino. Switching to dummy mode...")
                self.hardware = DummyHardwareController(
                    port=config.ARDUINO_PORT,
                    baudrate=config.ARDUINO_BAUDRATE,
                    timeout=config.ARDUINO_TIMEOUT
                )
                self.hardware.connect()
            
            print("      ✓ Hardware ready")
            
            print("\n" + "=" * 70)
            print("✓ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
            print("=" * 70)
            print()
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Component initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """Run the application"""
        print("[System] Starting application...")
        
        # Initialize components
        if not self.initialize_components():
            print("[ERROR] Failed to initialize components. Exiting...")
            return
        
        # Create Tkinter root
        self.root = tk.Tk()
        
        # Create main window
        self.main_window = MainWindow(
            self.root,
            self.camera,
            self.ai,
            self.hardware,
            self.database
        )
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Print system info
        self._print_system_info()
        
        # Start Tkinter main loop
        print("[System] UI ready. Starting main loop...")
        print()
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window close event"""
        print("\n[System] Shutting down...")
        
        try:
            # Stop camera
            if self.camera:
                self.camera.stop()
            
            # Disconnect hardware
            if self.hardware:
                self.hardware.disconnect()
            
            # Destroy window
            if self.root:
                self.root.destroy()
            
            print("[System] Shutdown complete")
            
        except Exception as e:
            print(f"[ERROR] Shutdown error: {e}")
    
    def _print_system_info(self):
        """Print system configuration information"""
        print("\n" + "=" * 70)
        print("SYSTEM CONFIGURATION")
        print("=" * 70)
        print(f"Mode:              CONTINUOUS (No conveyor stopping)")
        print(f"Travel Time:       {config.TRAVEL_TIME_MS} ms")
        print(f"Camera:            {config.CAMERA_ID} ({config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT})")
        print(f"Camera Exposure:   {config.CAMERA_EXPOSURE}")
        print(f"Arduino Port:      {config.ARDUINO_PORT}")
        print(f"Model:             {config.MODEL_PATH}")
        print(f"Confidence:        {config.CONFIDENCE_THRESHOLD}")
        print(f"NMS Threshold:     {config.NMS_THRESHOLD}")
        print(f"Debug Mode:        {config.DEBUG_MODE}")
        print("=" * 70)
        print()


def main():
    """Main entry point"""
    try:
        app = ContinuousSortingSystem()
        app.run()
    except KeyboardInterrupt:
        print("\n[System] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
