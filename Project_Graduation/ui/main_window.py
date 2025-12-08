"""
Main Window for Coca-Cola Sorting System
Provides real-time monitoring and control interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import time
import os
from datetime import datetime


class MainWindow:
    """
    Main application window with live video feed and control panel
    """
    
    def __init__(self, root, camera, ai_engine, hardware, database):
        """
        Initialize main window
        
        Args:
            root: Tkinter root window
            camera: Camera instance
            ai_engine: AIEngine instance
            hardware: HardwareController instance
            database: Database instance
        """
        self.root = root
        self.camera = camera
        self.ai = ai_engine
        self.hardware = hardware
        self.database = database
        
        self.root.title("Coca-Cola Sorting System - Control Panel")
        self.root.geometry("1280x720")
        self.root.resizable(True, True)
        
        # System state
        self.system_running = False
        self.processing = False
        
        # Latest results
        self.latest_frame = None
        self.latest_result = None
        self.latest_snapshot = None
        
        # Statistics
        self.session_total = 0
        self.session_ok = 0
        self.session_ng = 0
        
        # Build UI
        self._build_ui()
        
        # Start video update loop
        self._update_video()
        
        print("[UI] Main window initialized")
    
    def _build_ui(self):
        """Build the user interface"""
        # Configure style
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Status.TLabel", font=("Arial", 12))
        style.configure("Result.TLabel", font=("Arial", 24, "bold"))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # === TOP BAR ===
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(top_frame, text="🥤 COCA-COLA SORTING SYSTEM", style="Title.TLabel")
        title_label.pack(side=tk.LEFT, padx=10)
        
        self.status_label = ttk.Label(top_frame, text="● STOPPED", style="Status.TLabel", foreground="red")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # === LEFT PANEL - Live Video ===
        left_frame = ttk.LabelFrame(main_frame, text="Live Camera Feed", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        self.video_label = ttk.Label(left_frame)
        self.video_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Video info
        self.video_info_label = ttk.Label(left_frame, text="FPS: 0", font=("Arial", 9))
        self.video_info_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # === RIGHT PANEL - Results & Controls ===
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=0)  # Snapshot
        right_frame.rowconfigure(1, weight=0)  # Result
        right_frame.rowconfigure(2, weight=0)  # Details
        right_frame.rowconfigure(3, weight=0)  # Stats
        right_frame.rowconfigure(4, weight=1)  # Control (fill remaining space)
        
        # Snapshot display
        snapshot_frame = ttk.LabelFrame(right_frame, text="Last Inspection", padding="10")
        snapshot_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        snapshot_frame.columnconfigure(0, weight=1)
        
        self.snapshot_label = ttk.Label(snapshot_frame, text="No inspection yet", anchor=tk.CENTER)
        self.snapshot_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Result display
        result_frame = ttk.LabelFrame(right_frame, text="Inspection Result", padding="10")
        result_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        
        self.result_label = ttk.Label(result_frame, text="--", style="Result.TLabel", anchor=tk.CENTER)
        self.result_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.reason_label = ttk.Label(result_frame, text="Waiting for bottle...", 
                                     font=("Arial", 10), anchor=tk.CENTER, wraplength=350)
        self.reason_label.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Details
        details_frame = ttk.LabelFrame(right_frame, text="Detection Details", padding="10")
        details_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.details_text = tk.Text(details_frame, height=6, width=40, font=("Courier", 9))
        self.details_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.details_text.config(state=tk.DISABLED)
        
        # Statistics
        stats_frame = ttk.LabelFrame(right_frame, text="Session Statistics", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text=self._format_stats(), 
                                     font=("Arial", 10), justify=tk.LEFT)
        self.stats_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Control buttons - FIX: Always visible
        control_frame = ttk.LabelFrame(right_frame, text="System Control", padding="10")
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N))  # Changed to tk.N instead of tk.S
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        
        self.start_button = ttk.Button(control_frame, text="▶ START SYSTEM", 
                                       command=self.start_system)
        self.start_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5), pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏹ STOP SYSTEM", 
                                     command=self.stop_system, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=5)
        
        self.history_button = ttk.Button(control_frame, text="📊 View History", 
                                   command=self.open_history)
        self.history_button.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.exit_button = ttk.Button(control_frame, text="🚪 Exit", command=self.on_closing)
        self.exit_button.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def _format_stats(self):
        """Format statistics string"""
        ok_rate = (self.session_ok / self.session_total * 100) if self.session_total > 0 else 0
        ng_rate = (self.session_ng / self.session_total * 100) if self.session_total > 0 else 0
        
        return f"""Total Inspected: {self.session_total}
✓ OK: {self.session_ok} ({ok_rate:.1f}%)
✗ NG: {self.session_ng} ({ng_rate:.1f}%)"""
    
    def _update_video(self):
        """Update video feed"""
        if self.camera and self.camera.is_opened():
            frame = self.camera.read()
            
            if frame is not None:
                # Update FPS
                fps = self.camera.get_fps()
                self.video_info_label.config(text=f"FPS: {fps:.1f}")
                
                # Convert for display
                display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display_frame = cv2.resize(display_frame, (640, 480))
                
                # Add processing indicator
                if self.processing:
                    cv2.putText(display_frame, "PROCESSING...", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                
                # Convert to PhotoImage
                img = Image.fromarray(display_frame)
                photo = ImageTk.PhotoImage(image=img)
                
                self.video_label.config(image=photo)
                self.video_label.image = photo
        
        # Schedule next update
        self.root.after(33, self._update_video)  # ~30 FPS
    
    def start_system(self):
        """Start the sorting system"""
        if not self.hardware.is_connected():
            messagebox.showerror("Error", "Arduino not connected!\n\nPlease connect Arduino and restart.")
            return
        
        # Start listening for detections
        self.hardware.start_listening(self.on_bottle_detected)
        
        self.system_running = True
        self.status_label.config(text="● RUNNING", foreground="green")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        # FIX: Keep other buttons enabled
        self.history_button.config(state=tk.NORMAL)
        self.exit_button.config(state=tk.NORMAL)
        
        print("[UI] System started")
    
    def stop_system(self):
        """Stop the sorting system"""
        self.hardware.stop_listening()
        
        self.system_running = False
        self.status_label.config(text="● STOPPED", foreground="red")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        print("[UI] System stopped")
    
    def on_bottle_detected(self):
        """Handle bottle detection from Arduino - CHỤP NHIỀU ẢNH"""
        if not self.system_running or self.processing:
            return
        
        print("[UI] Bottle detected! Starting multi-frame inspection...")
        self.processing = True
        
        try:
            start_time = time.time()
            
            # CHỤP NHIỀU ẢNH (3-5 ảnh)
            num_frames = 5
            frames = []
            
            print(f"[UI] Capturing {num_frames} frames...")
            for i in range(num_frames):
                snapshot = self.camera.capture_snapshot()
                if snapshot is not None:
                    frames.append(snapshot)
                    print(f"[UI] Frame {i+1}/{num_frames} captured")
                time.sleep(0.1)  # 100ms giữa mỗi ảnh
            
            if not frames:
                print("[ERROR] Failed to capture any frames")
                self.processing = False
                return
            
            print(f"[UI] Running AI on {len(frames)} frames...")
            
            # Run AI prediction trên nhiều ảnh
            result = self.ai.predict_multiple(frames)
            processing_time = time.time() - start_time
            
            # Lấy ảnh có bounding boxes
            if 'annotated_image' in result:
                annotated_image = result['annotated_image']
            else:
                annotated_image = frames[0]  # Fallback
            
            # Save annotated image
            save_dir = "captures/ok" if result['result'] == 'OK' else "captures/ng"
            image_path = self.camera.save_image(annotated_image, save_dir, result['result'])
            
            # Add to database
            result['image_path'] = image_path
            result['processing_time'] = processing_time
            self.database.add_inspection(result)
            
            # Update statistics
            self.session_total += 1
            if result['result'] == 'OK':
                self.session_ok += 1
            else:
                self.session_ng += 1
            
            # Update UI - HIỂN THỊ ẢNH CÓ BOUNDING BOXES
            self._display_result(annotated_image, result)
            
            # Send result to Arduino
            if result['result'] == 'OK':
                self.hardware.send_ok()
            else:
                self.hardware.send_ng()
            
            print(f"[UI] Inspection complete: {result['result']} ({processing_time:.2f}s, {len(frames)} frames)")
            
        except Exception as e:
            print(f"[ERROR] Inspection error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.processing = False
    
    def _display_result(self, snapshot, result):
        """Display inspection result on UI - with bounding boxes"""
        # Display snapshot WITH BOUNDING BOXES
        display_snapshot = cv2.cvtColor(snapshot, cv2.COLOR_BGR2RGB)
        display_snapshot = cv2.resize(display_snapshot, (350, 260))
        
        img = Image.fromarray(display_snapshot)
        photo = ImageTk.PhotoImage(image=img)
        
        self.snapshot_label.config(image=photo, text="")
        self.snapshot_label.image = photo
        
        # Display result
        if result['result'] == 'OK':
            self.result_label.config(text="✓ OK", foreground="green")
        else:
            self.result_label.config(text="✗ NG", foreground="red")
        
        self.reason_label.config(text=result['reason'])
        
        # Display details
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        details = f"Components:\n"
        details += f"  ✓ Cap: {'Yes' if result['has_cap'] else 'No'}\n"
        details += f"  ✓ Filled: {'Yes' if result['has_filled'] else 'No'}\n"
        details += f"  ✓ Label: {'Yes' if result['has_label'] else 'No'}\n\n"
        
        if result['defects_found']:
            details += f"Defects Found:\n"
            for defect in result['defects_found']:
                details += f"  ✗ {defect}\n"
        else:
            details += "No defects detected\n"
        
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)
        
        # Update statistics
        self.stats_label.config(text=self._format_stats())
    
    def open_history(self):
        """Open history window"""
        from ui.history_window import HistoryWindow
        HistoryWindow(self.root, self.database)
    
    def on_closing(self):
        """Handle window closing"""
        if self.system_running:
            if not messagebox.askokcancel("Quit", "System is running. Are you sure you want to quit?"):
                return
        
        print("[UI] Closing application...")
        
        # Stop system
        if self.system_running:
            self.stop_system()
        
        # Cleanup
        if self.camera:
            self.camera.stop()
        
        if self.hardware:
            self.hardware.disconnect()
        
        self.root.quit()
        self.root.destroy()
