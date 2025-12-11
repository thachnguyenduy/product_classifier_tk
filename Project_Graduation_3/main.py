#!/usr/bin/env python3
# ============================================
# MAIN ENTRY POINT
# Coca-Cola Sorting System - FIFO Queue Mode
# ============================================

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
    """
    
    def __init__(self):
        print("=" * 60)
        print("COCA-COLA SORTING SYSTEM - FIFO QUEUE MODE")
        print("=" * 60)
        
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
        print("\n[Initialization] Starting components...")
        
        # 1. Database
        print("[1/4] Initializing database...")
        self.database = Database()
        
        # 2. AI Engine
        print("[2/4] Loading AI model...")
        self.ai = AIEngine()
        
        # 3. Camera
        print("[3/4] Opening camera...")
        if config.USE_DUMMY_CAMERA:
            self.camera = DummyCamera()
        else:
            self.camera = Camera()
        
        if not self.camera.is_opened():
            print("[ERROR] Camera failed to open!")
            sys.exit(1)
        
        self.camera.start()
        
        # 4. Hardware (Arduino)
        print("[4/4] Connecting to Arduino...")
        if config.USE_DUMMY_HARDWARE:
            self.hardware = DummyHardwareController()
        else:
            self.hardware = HardwareController()
        
        if not self.hardware.is_connected():
            print("[WARNING] Arduino not connected. System will run without hardware.")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(1)
        
        print("\n✅ All components initialized successfully!")
    
    def _create_ui(self):
        """Create Tkinter UI"""
        print("\n[UI] Creating interface...")
        
        self.root = tk.Tk()
        self.main_window = MainWindow(
            self.root,
            self.camera,
            self.ai,
            self.hardware,
            self.database
        )
        
        print("✅ UI ready!")
    
    def run(self):
        """Run the application"""
        print("\n" + "=" * 60)
        print("🚀 SYSTEM READY!")
        print("=" * 60)
        print("\nInstructions:")
        print("1. Click 'START SYSTEM' to begin")
        print("2. Bottles crossing the cyan line will be detected")
        print("3. Results are added to FIFO queue")
        print("4. When IR sensor triggers, oldest result is processed")
        print("\n" + "=" * 60 + "\n")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n[Info] Interrupted by user")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources"""
        print("\n[Cleanup] Shutting down...")
        
        if self.camera:
            self.camera.stop()
        
        if self.hardware:
            self.hardware.stop()
        
        print("✅ Cleanup complete. Goodbye!")


def main():
    """Main function"""
    try:
        app = SortingSystemApp()
        app.run()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

