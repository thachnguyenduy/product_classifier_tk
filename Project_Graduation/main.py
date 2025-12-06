#!/usr/bin/env python3
"""
Coca-Cola Sorting System - Main Entry Point
Stop-and-Go workflow with AI-based quality inspection
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


class SortingSystemApp:
    """
    Main application class for Coca-Cola Sorting System
    """
    
    def __init__(self):
        """Initialize the application"""
        print("=" * 60)
        print("🥤 COCA-COLA SORTING SYSTEM")
        print("=" * 60)
        print()
        
        self.root = None
        self.camera = None
        self.ai = None
        self.hardware = None
        self.database = None
        self.main_window = None
        
        # Configuration
        self.config = {
            'camera_id': 0,  # Change to video file path if using recorded video
            'camera_width': 640,
            'camera_height': 480,
            'arduino_port': '/dev/ttyUSB0',  # Change to 'COM3' on Windows
            'arduino_baudrate': 9600,
            'model_path': 'model/best_ncnn_model',
            'use_dummy_camera': False,  # Set True for testing without camera
            'use_dummy_hardware': False  # Set True for testing without Arduino
        }
    
    def initialize_components(self):
        """Initialize all system components"""
        print("[System] Initializing components...")
        
        try:
            # 1. Initialize Database
            print("\n[1/4] Initializing database...")
            self.database = Database(db_path="database/product.db")
            
            # 2. Initialize AI Engine
            print("\n[2/4] Initializing AI engine...")
            self.ai = AIEngine(model_path=self.config['model_path'])
            
            # 3. Initialize Camera
            print("\n[3/4] Initializing camera...")
            if self.config['use_dummy_camera']:
                self.camera = DummyCamera(
                    width=self.config['camera_width'],
                    height=self.config['camera_height']
                )
            else:
                self.camera = Camera(
                    camera_id=self.config['camera_id'],
                    width=self.config['camera_width'],
                    height=self.config['camera_height']
                )
            
            if not self.camera.start():
                print("[WARNING] Failed to start camera. Switching to dummy mode...")
                self.camera = DummyCamera(
                    width=self.config['camera_width'],
                    height=self.config['camera_height']
                )
                self.camera.start()
            
            # 4. Initialize Hardware Controller
            print("\n[4/4] Initializing hardware controller...")
            if self.config['use_dummy_hardware']:
                self.hardware = DummyHardwareController()
            else:
                self.hardware = HardwareController(
                    port=self.config['arduino_port'],
                    baudrate=self.config['arduino_baudrate']
                )
            
            if not self.hardware.connect():
                print("[WARNING] Failed to connect to Arduino. Switching to dummy mode...")
                self.hardware = DummyHardwareController()
                self.hardware.connect()
            
            print("\n" + "=" * 60)
            print("✓ All components initialized successfully")
            print("=" * 60)
            print()
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Failed to initialize components: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            'captures/ok',
            'captures/ng',
            'database'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def run(self):
        """Run the application"""
        # Create necessary directories
        self.create_directories()
        
        # Initialize components
        if not self.initialize_components():
            print("[ERROR] Failed to initialize system. Exiting...")
            sys.exit(1)
        
        # Create Tkinter root window
        self.root = tk.Tk()
        
        # Create main window
        print("[System] Starting user interface...")
        self.main_window = MainWindow(
            root=self.root,
            camera=self.camera,
            ai_engine=self.ai,
            hardware=self.hardware,
            database=self.database
        )
        
        # Set closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.main_window.on_closing)
        
        print("[System] System ready! 🚀")
        print()
        print("INSTRUCTIONS:")
        print("1. Click 'START SYSTEM' to begin sorting")
        print("2. Place bottles on the conveyor")
        print("3. System will automatically detect, inspect, and sort")
        print("4. Click 'STOP SYSTEM' to pause")
        print("5. View history and statistics in the History window")
        print()
        
        # Run Tkinter main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n[System] Shutting down...")
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        print("[System] Cleaning up...")
        
        if self.camera:
            self.camera.stop()
        
        if self.hardware:
            self.hardware.disconnect()
        
        if self.database:
            self.database.close()
        
        print("[System] Shutdown complete. Goodbye! 👋")


def main():
    """Main entry point"""
    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required")
        sys.exit(1)
    
    # Create and run application
    app = SortingSystemApp()
    app.run()


if __name__ == "__main__":
    main()

