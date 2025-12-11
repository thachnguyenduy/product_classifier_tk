# ============================================
# MAIN WINDOW - FIFO Queue with Virtual Line
# ============================================

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import time
import os
from datetime import datetime
import threading
import config


class MainWindow:
    """
    Main UI window with:
    - Live video with Virtual Line
    - FIFO Queue visualization
    - Control buttons
    """
    
    def __init__(self, root, camera, ai_engine, hardware, database):
        self.root = root
        self.camera = camera
        self.ai = ai_engine
        self.hardware = hardware
        self.database = database
        
        # State
        self.system_running = False
        self.product_queue = []  # FIFO Queue: [(result, reason, timestamp, image), ...]
        self.last_detection_time = 0  # For cooldown
        self.last_bottle_x = None  # Track bottle position
        
        # Statistics
        self.total_count = 0
        self.ok_count = 0
        self.ng_count = 0
        
        # UI elements
        self.video_label = None
        self.queue_text = None
        
        self._build_ui()
        self._update_video_loop()
    
    def _build_ui(self):
        """Build the user interface"""
        self.root.title("Coca-Cola Sorting System - FIFO Queue Mode")
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # === LEFT: VIDEO + DETECTION ===
        left_container = ttk.Frame(main_frame)
        left_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Live camera
        video_frame = ttk.LabelFrame(left_container, text="📹 Live Camera (Virtual Line)", padding="5")
        video_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.video_label = ttk.Label(video_frame, text="Camera Feed", background="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Last AI Detection Result
        detection_frame = ttk.LabelFrame(left_container, text="🤖 Last AI Detection", padding="5")
        detection_frame.pack(fill=tk.BOTH, expand=True)
        
        self.detection_label = ttk.Label(detection_frame, text="Waiting for detection...", background="gray")
        self.detection_label.pack(fill=tk.BOTH, expand=True)
        
        # === RIGHT: CONTROLS & QUEUE ===
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.LabelFrame(right_frame, text="🎮 Control", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(control_frame, text="▶ START SYSTEM", command=self.start_system)
        self.start_btn.pack(fill=tk.X, pady=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹ STOP SYSTEM", command=self.stop_system, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        history_btn = ttk.Button(control_frame, text="📊 View History", command=self.show_history)
        history_btn.pack(fill=tk.X, pady=5)
        
        exit_btn = ttk.Button(control_frame, text="🚪 Exit", command=self.on_closing)
        exit_btn.pack(fill=tk.X, pady=5)
        
        # Statistics
        stats_frame = ttk.LabelFrame(right_frame, text="📈 Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_label = ttk.Label(stats_frame, text="Total: 0\nOK: 0\nNG: 0", font=("Arial", 12))
        self.stats_label.pack()
        
        # Queue Display
        queue_frame = ttk.LabelFrame(right_frame, text="📦 FIFO Queue", padding="10")
        queue_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrolled text for queue
        queue_scroll = ttk.Scrollbar(queue_frame)
        queue_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.queue_text = tk.Text(queue_frame, height=15, width=30, 
                                   yscrollcommand=queue_scroll.set, 
                                   font=("Consolas", 10))
        self.queue_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        queue_scroll.config(command=self.queue_text.yview)
        
        # Status bar
        self.status_label = ttk.Label(self.root, text="System Idle", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_system(self):
        """Start the sorting system"""
        if self.system_running:
            return
        
        # Check hardware
        if not self.hardware.is_connected():
            messagebox.showerror("Error", "Arduino not connected!")
            return
        
        # Start hardware listening with callback
        self.hardware.start_listening(self.on_trigger_received)
        
        # Start conveyor belt
        self.hardware.start_conveyor()
        
        self.system_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="✅ System Running (Conveyor ON)")
        
        print("[UI] System STARTED - Conveyor running")
    
    def stop_system(self):
        """Stop the sorting system"""
        if not self.system_running:
            return
        
        # Stop conveyor belt
        self.hardware.stop_conveyor()
        
        self.system_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹ System Stopped (Conveyor OFF)")
        
        print("[UI] System STOPPED - Conveyor stopped")
    
    def _update_video_loop(self):
        """Continuous video update loop"""
        frame = self.camera.get_frame()
        
        if frame is not None:
            # Draw virtual line
            self._draw_virtual_line(frame)
            
            # Check for bottle crossing (only if system running)
            if self.system_running:
                self._check_crossing(frame)
            
            # Convert to Tkinter format
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((800, 600), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        
        # Schedule next update
        self.root.after(30, self._update_video_loop)
    
    def _draw_virtual_line(self, frame):
        """Draw cyan virtual line on frame"""
        h, w = frame.shape[:2]
        line_x = config.VIRTUAL_LINE_X
        
        # Draw line
        cv2.line(frame, (line_x, 0), (line_x, h), config.LINE_COLOR, config.LINE_THICKNESS)
        
        # Draw label
        cv2.putText(frame, "DETECTION LINE", (line_x + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.LINE_COLOR, 2)
    
    def _check_crossing(self, frame):
        """
        Check if bottle crosses virtual line
        
        Improved logic:
        - Better blob detection with size and shape validation
        - Draw bounding box on detected bottle
        - Only trigger when valid bottle crosses line
        """
        current_time = time.time()
        
        # Cooldown check
        if current_time - self.last_detection_time < config.DETECTION_COOLDOWN:
            return
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use adaptive threshold for better detection
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return
        
        # Find valid bottle contours
        valid_bottles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by minimum area (increased for better accuracy)
            if area < 8000:  # Increased from 5000
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio (bottle should be taller than wide)
            aspect_ratio = float(h) / float(w) if w > 0 else 0
            
            # Valid bottle: aspect ratio between 1.5 and 4.0
            if aspect_ratio < 1.2 or aspect_ratio > 5.0:
                continue
            
            # Calculate center
            M = cv2.moments(contour)
            if M["m00"] == 0:
                continue
            
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            
            valid_bottles.append({
                'contour': contour,
                'bbox': (x, y, w, h),
                'center': (cx, cy),
                'area': area,
                'aspect_ratio': aspect_ratio
            })
        
        if len(valid_bottles) == 0:
            return
        
        # Find bottle closest to virtual line
        line_x = config.VIRTUAL_LINE_X
        tolerance = config.CROSSING_TOLERANCE
        
        for bottle in valid_bottles:
            cx, cy = bottle['center']
            x, y, w, h = bottle['bbox']
            
            # Draw bounding box (GREEN = detected bottle)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
            
            # Show info
            info_text = f"Area: {bottle['area']:.0f}, AR: {bottle['aspect_ratio']:.2f}"
            cv2.putText(frame, info_text, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            
            # Check if crossing line
            if abs(cx - line_x) < tolerance:
                # Draw RED box when crossing (trigger detection)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                cv2.putText(frame, "CROSSING!", (x, y - 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Bottle is crossing! Trigger detection
                self._on_bottle_detected(frame, cx, cy)
                self.last_detection_time = current_time
                return  # Only process one bottle at a time
    
    def _on_bottle_detected(self, frame, cx, cy):
        """
        Called when bottle crosses virtual line
        
        Actions:
        1. Run AI prediction
        2. Add result to FIFO queue
        3. Save snapshot
        """
        print(f"[UI] Bottle detected at ({cx}, {cy})")
        
        # Run AI prediction in separate thread to avoid blocking UI
        threading.Thread(target=self._process_detection, args=(frame.copy(),), daemon=True).start()
    
    def _process_detection(self, frame):
        """Process detection in background thread"""
        try:
            # Run AI
            result_dict = self.ai.predict(frame)
            
            result = result_dict['result']
            reason = result_dict['reason']
            timestamp = datetime.now().strftime("%H:%M:%S")
            annotated_image = result_dict['annotated_image']
            
            # Save snapshot
            image_path = self._save_snapshot(annotated_image, result)
            
            # Add to queue
            queue_item = {
                'result': result,
                'reason': reason,
                'timestamp': timestamp,
                'image_path': image_path,
                'annotated_image': annotated_image  # Store for display
            }
            
            self.product_queue.append(queue_item)
            
            # Update UI (queue + detection display)
            self.root.after(0, lambda: self._update_detection_display(annotated_image, result, reason))
            self.root.after(0, self._update_queue_display)
            
            # Log to database
            result_dict['image_path'] = image_path
            self.database.add_inspection(result_dict)
            
            print(f"[UI] Added to queue: {result} | Queue size: {len(self.product_queue)}")
            
        except Exception as e:
            print(f"[ERROR] Detection processing failed: {e}")
            import traceback
            traceback.print_exc()
            self.processing = False
    
    def on_trigger_received(self):
        """
        Called when IR sensor sends 'T'
        
        Actions:
        1. Pop oldest item from queue
        2. If NG -> Send 'K' to Arduino
        3. Update statistics
        """
        if len(self.product_queue) == 0:
            print("[WARNING] Trigger received but queue is empty!")
            return
        
        # Pop oldest (FIFO)
        item = self.product_queue.pop(0)
        
        result = item['result']
        reason = item['reason']
        timestamp = item['timestamp']
        
        print(f"[UI] Trigger! Processing: {result} (from {timestamp})")
        
        # Send command to Arduino
        if result == 'N':
            self.hardware.send_kick()
            print("[UI] Sent KICK command")
        else:
            self.hardware.send_ok()
            print("[UI] Sent OK command")
        
        # Update statistics
        self.total_count += 1
        if result == 'O':
            self.ok_count += 1
        else:
            self.ng_count += 1
        
        self.root.after(0, self._update_statistics_display)
        self.root.after(0, self._update_queue_display)
    
    def _update_queue_display(self):
        """Update queue text widget"""
        self.queue_text.delete('1.0', tk.END)
        
        if len(self.product_queue) == 0:
            self.queue_text.insert(tk.END, "Queue is empty\n")
        else:
            self.queue_text.insert(tk.END, f"Queue Size: {len(self.product_queue)}\n")
            self.queue_text.insert(tk.END, "=" * 30 + "\n\n")
            
            # Show items (newest at top)
            for i, item in enumerate(reversed(self.product_queue[-config.MAX_QUEUE_DISPLAY:])):
                result_icon = "✅" if item['result'] == 'O' else "❌"
                self.queue_text.insert(tk.END, f"{result_icon} {item['timestamp']}\n")
                self.queue_text.insert(tk.END, f"   Result: {item['result']}\n")
                self.queue_text.insert(tk.END, f"   Reason: {item['reason']}\n\n")
    
    def _update_statistics_display(self):
        """Update statistics label"""
        stats_text = f"Total: {self.total_count}\n"
        stats_text += f"✅ OK: {self.ok_count}\n"
        stats_text += f"❌ NG: {self.ng_count}"
        
        self.stats_label.config(text=stats_text)
    
    def _update_detection_display(self, annotated_image, result, reason):
        """Update detection display with AI annotated image"""
        try:
            # Convert OpenCV image to Tkinter format
            img_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
            
            # Resize to fit display (adjust as needed)
            display_width = 400
            h, w = img_rgb.shape[:2]
            aspect_ratio = h / w
            display_height = int(display_width * aspect_ratio)
            
            img_resized = cv2.resize(img_rgb, (display_width, display_height))
            img_pil = Image.fromarray(img_resized)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            
            # Update label
            self.detection_label.imgtk = img_tk
            self.detection_label.configure(image=img_tk)
            
            # Update frame title with result
            detection_frame = self.detection_label.master
            result_color = "green" if result == 'O' else "red"
            result_text = "✅ OK" if result == 'O' else "❌ NG"
            detection_frame.config(text=f"🤖 Last AI Detection - {result_text} ({reason})")
            
        except Exception as e:
            print(f"[ERROR] Update detection display failed: {e}")
    
    def _save_snapshot(self, image, result):
        """Save annotated snapshot"""
        if not config.SAVE_SNAPSHOTS:
            return ""
        
        try:
            # Choose directory
            if result == 'O':
                save_dir = config.CAPTURE_OK_PATH
            else:
                save_dir = config.CAPTURE_NG_PATH
            
            os.makedirs(save_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{result}_{timestamp}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # Save
            cv2.imwrite(filepath, image)
            
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Save snapshot failed: {e}")
            return ""
    
    def show_history(self):
        """Show history window"""
        from ui.history_window import HistoryWindow
        HistoryWindow(self.root, self.database)
    
    def on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.stop_system()
            self.camera.stop()
            self.hardware.stop()
            self.root.destroy()

