"""
Main Window for Coca-Cola Sorting System (CONTINUOUS MODE)
"Control First" Strategy: Send decision to Arduino IMMEDIATELY after AI,
then update UI/Database
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import time
import threading


class MainWindow:
    """
    Main UI window with "Control First" strategy
    Priority: Hardware control > UI updates
    """
    
    def __init__(self, root, camera, ai, hardware, database):
        """
        Initialize main window
        
        Args:
            root: Tkinter root window
            camera: Camera object
            ai: AIEngine object
            hardware: HardwareController object
            database: Database object
        """
        self.root = root
        self.camera = camera
        self.ai = ai
        self.hardware = hardware
        self.database = database
        
        self.system_running = False
        self.processing = False
        
        # UI elements
        self.live_label = None
        self.snapshot_label = None
        self.result_label = None
        self.stats_label = None
        
        # Latest frames
        self.latest_live_frame = None
        self.latest_snapshot = None
        
        # Statistics
        self.total_count = 0
        self.ok_count = 0
        self.ng_count = 0
        
        # Setup UI
        self._setup_ui()
        
        # Start video update loop
        self._update_video()
    
    def _setup_ui(self):
        """Setup UI layout"""
        self.root.title("Coca-Cola Sorting System - CONTINUOUS MODE")
        self.root.geometry("1400x700")
        self.root.configure(bg='#2c3e50')
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ====================================================================
        # LEFT: Live Video
        # ====================================================================
        left_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(left_frame, text="LIVE VIDEO", 
                font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.live_label = tk.Label(left_frame, bg='black')
        self.live_label.pack(padx=10, pady=10)
        
        # FPS display
        self.fps_label = tk.Label(left_frame, text="FPS: 0", 
                                  font=('Arial', 10), bg='#34495e', fg='#3498db')
        self.fps_label.pack()
        
        # ====================================================================
        # MIDDLE: Last Inspection Result
        # ====================================================================
        middle_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tk.Label(middle_frame, text="LAST INSPECTION", 
                font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.snapshot_label = tk.Label(middle_frame, bg='black')
        self.snapshot_label.pack(padx=10, pady=10)
        
        # Result display
        self.result_label = tk.Label(middle_frame, text="WAITING...", 
                                     font=('Arial', 20, 'bold'),
                                     bg='#34495e', fg='#95a5a6',
                                     width=20, height=2)
        self.result_label.pack(pady=10)
        
        # Reason display
        self.reason_label = tk.Label(middle_frame, text="", 
                                     font=('Arial', 12),
                                     bg='#34495e', fg='white',
                                     wraplength=400)
        self.reason_label.pack(pady=5)
        
        # Processing time
        self.time_label = tk.Label(middle_frame, text="", 
                                   font=('Arial', 10),
                                   bg='#34495e', fg='#95a5a6')
        self.time_label.pack()
        
        # ====================================================================
        # RIGHT: Control Panel
        # ====================================================================
        right_frame = tk.Frame(main_frame, bg='#34495e', relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0))
        
        tk.Label(right_frame, text="CONTROL PANEL", 
                font=('Arial', 14, 'bold'), bg='#34495e', fg='white').pack(pady=10)
        
        # System status
        self.status_label = tk.Label(right_frame, text="● STOPPED", 
                                     font=('Arial', 12, 'bold'),
                                     bg='#34495e', fg='#e74c3c')
        self.status_label.pack(pady=10)
        
        # Start button
        self.start_btn = tk.Button(right_frame, text="START SYSTEM",
                                   font=('Arial', 12, 'bold'),
                                   bg='#27ae60', fg='white',
                                   width=18, height=2,
                                   command=self.start_system)
        self.start_btn.pack(pady=5)
        
        # Stop button
        self.stop_btn = tk.Button(right_frame, text="STOP SYSTEM",
                                  font=('Arial', 12, 'bold'),
                                  bg='#e74c3c', fg='white',
                                  width=18, height=2,
                                  command=self.stop_system,
                                  state=tk.DISABLED)
        self.stop_btn.pack(pady=5)
        
        # Separator
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # Statistics
        tk.Label(right_frame, text="TODAY'S STATISTICS", 
                font=('Arial', 12, 'bold'), bg='#34495e', fg='white').pack(pady=5)
        
        self.stats_label = tk.Label(right_frame, 
                                    text="Total: 0\nOK: 0\nNG: 0\nPass Rate: 0%",
                                    font=('Arial', 11),
                                    bg='#34495e', fg='white',
                                    justify=tk.LEFT)
        self.stats_label.pack(pady=10)
        
        # Separator
        ttk.Separator(right_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        # View History button
        self.history_btn = tk.Button(right_frame, text="VIEW HISTORY",
                                     font=('Arial', 11),
                                     bg='#3498db', fg='white',
                                     width=18, height=2,
                                     command=self.view_history)
        self.history_btn.pack(pady=5)
        
        # Exit button
        self.exit_btn = tk.Button(right_frame, text="EXIT",
                                  font=('Arial', 11),
                                  bg='#95a5a6', fg='white',
                                  width=18, height=2,
                                  command=self.exit_app)
        self.exit_btn.pack(pady=5)
        
        # Mode indicator
        tk.Label(right_frame, text="CONTINUOUS MODE", 
                font=('Arial', 9, 'italic'), 
                bg='#34495e', fg='#f39c12').pack(side=tk.BOTTOM, pady=10)
    
    def _update_video(self):
        """Update live video display (runs continuously)"""
        if self.camera and self.camera.is_running():
            frame = self.camera.read_frame()
            
            if frame is not None:
                self.latest_live_frame = frame
                
                # Convert to PhotoImage
                display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display_frame = cv2.resize(display_frame, (640, 480))
                img = Image.fromarray(display_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Update label
                self.live_label.imgtk = imgtk
                self.live_label.configure(image=imgtk)
                
                # Update FPS
                fps = self.camera.get_fps()
                self.fps_label.configure(text=f"FPS: {fps:.1f}")
        
        # Schedule next update (30 FPS)
        self.root.after(33, self._update_video)
    
    def start_system(self):
        """Start automatic sorting system"""
        if self.system_running:
            return
        
        print("[UI] Starting system...")
        
        # Start conveyor belt (relay ON)
        self.hardware.start_conveyor()
        
        # Update UI
        self.system_running = True
        self.status_label.configure(text="● RUNNING", fg='#27ae60')
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        
        # Start listening for detections from Arduino
        self.hardware.start_listening(self.on_bottle_detected)
        
        print("[UI] System started - Conveyor running, waiting for detections...")
    
    def stop_system(self):
        """Stop automatic sorting system"""
        if not self.system_running:
            return
        
        print("[UI] Stopping system...")
        
        # Stop listening
        self.hardware.stop_listening()
        
        # Stop conveyor belt (relay OFF)
        self.hardware.stop_conveyor()
        
        # Update UI
        self.system_running = False
        self.status_label.configure(text="● STOPPED", fg='#e74c3c')
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        
        print("[UI] System stopped - Conveyor stopped, detection paused")
    
    def on_bottle_detected(self, timestamp):
        """
        Handle bottle detection from Arduino
        CONTROL FIRST STRATEGY: Capture -> AI -> Send Decision -> Update UI
        
        Args:
            timestamp: Detection timestamp from Arduino (or None)
        """
        if not self.system_running or self.processing:
            return
        
        print(f"[UI] Bottle detected! (timestamp: {timestamp})")
        
        # Process in separate thread to avoid blocking
        thread = threading.Thread(target=self._process_bottle, daemon=True)
        thread.start()
    
    def _process_bottle(self):
        """
        Process bottle detection (runs in separate thread)
        CRITICAL: Send decision to Arduino IMMEDIATELY after AI
        """
        self.processing = True
        
        try:
            start_time = time.time()
            
            # STEP 1: Capture frame
            frame = self.camera.capture_snapshot()
            if frame is None:
                print("[ERROR] Failed to capture frame")
                self.processing = False
                return
            
            # STEP 2: Run AI prediction
            result = self.ai.predict(frame)
            
            # STEP 3: SEND DECISION TO ARDUINO IMMEDIATELY (Control First!)
            decision = result['result']
            if decision == 'OK':
                self.hardware.send_ok()
            else:
                self.hardware.send_ng()
            
            print(f"[UI] Decision sent to Arduino: {decision}")
            
            # STEP 4: Now update UI (after hardware control is done)
            self.root.after(0, self._display_result, result)
            
            # STEP 5: Save to database (lowest priority)
            self._save_result(result)
            
            # STEP 6: Update statistics
            self._update_statistics()
            
        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.processing = False
    
    def _display_result(self, result):
        """
        Display result in UI (called from main thread)
        
        Args:
            result: Result dict from AI
        """
        # Display annotated image
        if 'annotated_image' in result:
            img = result['annotated_image']
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_rgb = cv2.resize(img_rgb, (640, 480))
            img_pil = Image.fromarray(img_rgb)
            imgtk = ImageTk.PhotoImage(image=img_pil)
            
            self.snapshot_label.imgtk = imgtk
            self.snapshot_label.configure(image=imgtk)
        
        # Display result
        decision = result['result']
        if decision == 'OK':
            self.result_label.configure(text="✓ OK", fg='#27ae60', bg='#d5f4e6')
        else:
            self.result_label.configure(text="✗ NG", fg='#e74c3c', bg='#fadbd8')
        
        # Display reason
        reason = result.get('reason', '')
        self.reason_label.configure(text=reason)
        
        # Display processing time
        proc_time = result.get('processing_time', 0)
        self.time_label.configure(text=f"Processing: {proc_time*1000:.1f} ms")
    
    def _save_result(self, result):
        """
        Save result to database
        
        Args:
            result: Result dict from AI
        """
        # Chia nhỏ: luôn cố gắng ghi DB, kể cả khi lưu ảnh bị lỗi
        image_path = ""

        # 1. Lưu ảnh (nếu có), không để lỗi ảnh chặn việc ghi DB
        try:
            decision = result.get('result', 'UNKNOWN')
            save_dir = "captures/ok" if decision == 'OK' else "captures/ng"
            image = result.get('annotated_image')

            if image is not None:
                image_path = self.camera.save_image(image, save_dir, decision)
        except Exception as e:
            print(f"[ERROR] Failed to save image for result: {e}")

        # 2. Ghi đường dẫn ảnh (nếu thành công) vào result và luôn cố gắng ghi DB
        if image_path:
            result['image_path'] = image_path

        try:
            self.database.add_inspection(result)
        except Exception as e:
            print(f"[ERROR] Failed to add inspection to database: {e}")
    
    def _update_statistics(self):
        """Update statistics display"""
        try:
            stats = self.database.get_today_statistics()
            
            self.total_count = stats['total']
            self.ok_count = stats['ok']
            self.ng_count = stats['ng']
            pass_rate = stats['pass_rate']
            
            # Update label
            stats_text = f"Total: {self.total_count}\n"
            stats_text += f"OK: {self.ok_count}\n"
            stats_text += f"NG: {self.ng_count}\n"
            stats_text += f"Pass Rate: {pass_rate:.1f}%"
            
            self.root.after(0, self.stats_label.configure, {'text': stats_text})
            
        except Exception as e:
            print(f"[ERROR] Failed to update statistics: {e}")
    
    def view_history(self):
        """Open history window"""
        from ui.history_window import HistoryWindow
        HistoryWindow(self.root, self.database)
    
    def exit_app(self):
        """Exit application"""
        print("[UI] Exiting application...")
        
        # Stop system if running
        if self.system_running:
            self.stop_system()
        
        # Close window
        self.root.quit()
        self.root.destroy()
