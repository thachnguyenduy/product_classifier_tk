"""
Main Window for Coca-Cola Sorting System
Provides real-time monitoring and control interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
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
        
        self.root.title("MainWindow")
        self.root.geometry("1440x810")
        self.root.resizable(True, True)
        self.root.configure(bg='white')
        
        # System state
        self.system_running = False
        self.processing = False
        
        # Latest results
        self.latest_frame = None
        self.latest_result = None
        self.latest_snapshot = None
        self.latest_annotated = None
        
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
        """Build the user interface - THEO THIẾT KẾ MỚI"""
        # Main container
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure columns
        main_frame.columnconfigure(0, weight=1)  # Left image
        main_frame.columnconfigure(1, weight=1)  # Middle image
        main_frame.columnconfigure(2, weight=0)  # Right panel (fixed width)
        
        # === LEFT IMAGE - Ảnh gốc ===
        left_frame = tk.Frame(main_frame, bg='lightgray', relief=tk.SOLID, borderwidth=2)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.left_image_label = tk.Label(left_frame, bg='gray')
        self.left_image_label.pack(fill=tk.BOTH, expand=True)
        
        # === MIDDLE IMAGE - Ảnh có bounding boxes ===
        middle_frame = tk.Frame(main_frame, bg='lightgray', relief=tk.SOLID, borderwidth=2)
        middle_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.middle_image_label = tk.Label(middle_frame, bg='gray')
        self.middle_image_label.pack(fill=tk.BOTH, expand=True)
        
        # === RIGHT PANEL - Controls và Results ===
        right_frame = tk.Frame(main_frame, bg='white', width=350)
        right_frame.grid(row=0, column=2, sticky=(tk.N, tk.S), padx=(5, 0))
        right_frame.grid_propagate(False)  # Prevent shrinking
        
        # MỞ CAMERA / CHẠY BẰNG TAY button
        self.camera_button_frame = tk.Frame(right_frame, bg='white', height=60)
        self.camera_button_frame.pack(fill=tk.X, pady=(10, 20))
        
        tk.Label(right_frame, text="MỞ CAMERA", font=('Arial', 11), 
                bg='white', fg='gray').pack()
        
        self.manual_button = tk.Button(
            right_frame,
            text="CHẠY BẰNG TAY",
            font=('Arial', 14, 'bold'),
            bg='#FFD700',  # Màu vàng
            fg='black',
            relief=tk.RAISED,
            borderwidth=3,
            height=2,
            command=self.manual_process
        )
        self.manual_button.pack(fill=tk.X, padx=20, pady=(5, 30))
        
        # KẾT QUẢ label
        tk.Label(right_frame, text="KẾT QUẢ", font=('Arial', 12), 
                bg='white', fg='black').pack(pady=(0, 10))
        
        # Result display area - Empty frame
        self.result_display_frame = tk.Frame(right_frame, bg='white', 
                                             relief=tk.SOLID, borderwidth=2, 
                                             height=200)
        self.result_display_frame.pack(fill=tk.X, padx=20, pady=(0, 30))
        self.result_display_frame.pack_propagate(False)
        
        # Result button (initially hidden, shown when result comes)
        self.result_button = tk.Button(
            self.result_display_frame,
            text="",
            font=('Arial', 20, 'bold'),
            relief=tk.RAISED,
            borderwidth=3,
            height=3
        )
        # Don't pack yet, will pack when result arrives
        
        # THỜI GIAN XỬ LÝ
        tk.Label(right_frame, text="THỜI GIAN XỬ LÝ", font=('Arial', 12), 
                bg='white', fg='black').pack(pady=(20, 10))
        
        self.time_display_frame = tk.Frame(right_frame, bg='white', 
                                          relief=tk.SOLID, borderwidth=2, 
                                          height=60)
        self.time_display_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        self.time_display_frame.pack_propagate(False)
        
        self.time_label = tk.Label(
            self.time_display_frame,
            text="0",
            font=('Arial', 24, 'bold'),
            bg='white',
            fg='black'
        )
        self.time_label.pack(expand=True)
        
        # Bottom buttons
        button_frame = tk.Frame(right_frame, bg='white')
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20))
        
        self.start_button = tk.Button(
            button_frame,
            text="▶ START SYSTEM",
            font=('Arial', 11, 'bold'),
            bg='#4CAF50',
            fg='white',
            height=2,
            command=self.start_system
        )
        self.start_button.pack(fill=tk.X, pady=(0, 5))
        
        self.stop_button = tk.Button(
            button_frame,
            text="⏹ STOP SYSTEM",
            font=('Arial', 11, 'bold'),
            bg='#f44336',
            fg='white',
            height=2,
            state=tk.DISABLED,
            command=self.stop_system
        )
        self.stop_button.pack(fill=tk.X, pady=(0, 5))
        
        self.history_button = tk.Button(
            button_frame,
            text="📊 View History",
            font=('Arial', 10),
            bg='#2196F3',
            fg='white',
            command=self.open_history
        )
        self.history_button.pack(fill=tk.X, pady=(0, 5))
        
        self.exit_button = tk.Button(
            button_frame,
            text="🚪 Exit",
            font=('Arial', 10),
            bg='#9E9E9E',
            fg='white',
            command=self.on_closing
        )
        self.exit_button.pack(fill=tk.X)
    
    def _update_video(self):
        """Update video feed - chỉ hiển thị ở ảnh trái"""
        if self.camera and self.camera.is_opened():
            frame = self.camera.read()
            
            if frame is not None:
                # Display on LEFT image (ảnh gốc)
                display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display_frame = cv2.resize(display_frame, (540, 760))
                
                img = Image.fromarray(display_frame)
                photo = ImageTk.PhotoImage(image=img)
                
                self.left_image_label.config(image=photo)
                self.left_image_label.image = photo
        
        # Schedule next update
        self.root.after(33, self._update_video)  # ~30 FPS
    
    def manual_process(self):
        """Xử lý thủ công khi bấm nút CHẠY BẰNG TAY"""
        if self.processing:
            messagebox.showwarning("Warning", "Đang xử lý, vui lòng đợi!")
            return
        
        print("[UI] Manual process triggered")
        self.process_bottle()
    
    def start_system(self):
        """Start the sorting system"""
        if not self.hardware.is_connected():
            messagebox.showerror("Error", "Arduino not connected!\n\nPlease connect Arduino and restart.")
            return
        
        # Start listening for detections
        self.hardware.start_listening(self.on_bottle_detected)
        
        self.system_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.manual_button.config(state=tk.DISABLED)  # Disable manual when auto running
        
        print("[UI] System started")
    
    def stop_system(self):
        """Stop the sorting system"""
        self.hardware.stop_listening()
        
        self.system_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.manual_button.config(state=tk.NORMAL)  # Enable manual when stopped
        
        print("[UI] System stopped")
    
    def on_bottle_detected(self):
        """Handle bottle detection from Arduino"""
        if not self.system_running or self.processing:
            return
        
        print("[UI] Bottle detected by Arduino!")
        self.process_bottle()
    
    def process_bottle(self):
        """Process bottle - chụp nhiều ảnh và hiển thị kết quả"""
        self.processing = True
        
        try:
            start_time = time.time()
            
            # CHỤP NHIỀU ẢNH (5 ảnh)
            num_frames = 5
            frames = []
            
            print(f"[UI] Capturing {num_frames} frames...")
            for i in range(num_frames):
                snapshot = self.camera.capture_snapshot()
                if snapshot is not None:
                    frames.append(snapshot)
                time.sleep(0.1)  # 100ms giữa mỗi ảnh
            
            if not frames:
                print("[ERROR] Failed to capture any frames")
                self.processing = False
                return
            
            print(f"[UI] Running AI on {len(frames)} frames...")
            
            # Run AI prediction trên nhiều ảnh
            result = self.ai.predict_multiple(frames)
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Lấy ảnh có bounding boxes
            if 'annotated_image' in result:
                annotated_image = result['annotated_image']
            else:
                annotated_image = frames[0]
            
            # Save images
            save_dir = "captures/ok" if result['result'] == 'OK' else "captures/ng"
            image_path = self.camera.save_image(annotated_image, save_dir, result['result'])
            
            # Add to database
            result['image_path'] = image_path
            result['processing_time'] = processing_time / 1000  # Store in seconds
            self.database.add_inspection(result)
            
            # Update statistics
            self.session_total += 1
            if result['result'] == 'OK':
                self.session_ok += 1
            else:
                self.session_ng += 1
            
            # HIỂN THỊ KẾT QUẢ THEO THIẾT KẾ
            self._display_result(frames[0], annotated_image, result, processing_time)
            
            # Send result to Arduino (if system is running)
            if self.system_running:
                if result['result'] == 'OK':
                    self.hardware.send_ok()
                else:
                    self.hardware.send_ng()
            
            print(f"[UI] Inspection complete: {result['result']} ({processing_time:.2f}ms)")
            
        except Exception as e:
            print(f"[ERROR] Inspection error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.processing = False
    
    def _display_result(self, original_frame, annotated_frame, result, processing_time):
        """Hiển thị kết quả theo thiết kế mới"""
        # LEFT IMAGE - Ảnh gốc (không có bounding box)
        display_left = cv2.cvtColor(original_frame, cv2.COLOR_BGR2RGB)
        display_left = cv2.resize(display_left, (540, 760))
        
        img_left = Image.fromarray(display_left)
        photo_left = ImageTk.PhotoImage(image=img_left)
        
        self.left_image_label.config(image=photo_left)
        self.left_image_label.image = photo_left
        
        # MIDDLE IMAGE - Ảnh có bounding boxes
        display_middle = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        display_middle = cv2.resize(display_middle, (540, 760))
        
        img_middle = Image.fromarray(display_middle)
        photo_middle = ImageTk.PhotoImage(image=img_middle)
        
        self.middle_image_label.config(image=photo_middle)
        self.middle_image_label.image = photo_middle
        
        # RIGHT PANEL - Hiển thị kết quả
        
        # Clear previous result button
        for widget in self.result_display_frame.winfo_children():
            widget.destroy()
        
        # Show result button
        if result['result'] == 'OK':
            result_text = "KẾT QUẢ"
            result_bg = '#4CAF50'  # Green
        else:
            result_text = "HÀNG BỊ LỖI"
            result_bg = '#f44336'  # Red
        
        self.result_button = tk.Button(
            self.result_display_frame,
            text=result_text,
            font=('Arial', 20, 'bold'),
            bg=result_bg,
            fg='white',
            relief=tk.RAISED,
            borderwidth=3,
            height=3
        )
        self.result_button.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Update time display
        self.time_label.config(text=f"{processing_time:.2f}")
    
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
