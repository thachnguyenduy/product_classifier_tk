# ============================================
# MAIN WINDOW - Tkinter UI with Line Crossing
# ============================================
"""
Main UI Window for Coca-Cola Sorting System

Features:
- Live camera feed with virtual line visualization
- Real-time AI detection with tracking
- Object tracking and line crossing detection
- Classification results display
- System controls (START/STOP)
- Statistics display

IMPORTANT:
- Conveyor direction: RIGHT → LEFT
- Line crossing triggers classification
- Classification is sent to Arduino immediately
- IR sensor trigger happens later (physical position)
"""

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
    Main UI window with live video, tracking, and controls
    """
    
    def __init__(self, root, camera, ai_engine, hardware, database):
        self.root = root
        self.camera = camera
        self.ai = ai_engine
        self.hardware = hardware
        self.database = database
        
        # System state
        self.system_running = False
        self.classification_queue = []  # Queue of (result, reason, timestamp, object_id)
        
        # Statistics
        self.total_count = 0
        self.ok_count = 0
        self.ng_count = 0
        
        # UI elements (will be created in _build_ui)
        self.video_label = None
        self.status_label = None
        self.stats_label = None
        self.queue_text = None
        self.start_btn = None
        self.stop_btn = None
        
        # Build UI
        self._build_ui()
        
        # Start video update loop
        self._update_video_loop()
    
    def _build_ui(self):
        """Build the Tkinter user interface"""
        self.root.title(config.SYSTEM_NAME)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)  # Video takes more space
        main_frame.columnconfigure(1, weight=1)  # Controls on right
        main_frame.rowconfigure(0, weight=1)
        
        # === LEFT PANEL: VIDEO ===
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Video frame
        video_frame = ttk.LabelFrame(left_frame, text="📹 Live Camera (Virtual Line)", padding="5")
        video_frame.pack(fill=tk.BOTH, expand=True)
        
        self.video_label = ttk.Label(video_frame, text="Camera initializing...", background="black")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # === RIGHT PANEL: CONTROLS & INFO ===
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.LabelFrame(right_frame, text="🎮 System Control", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(
            control_frame,
            text="▶ START SYSTEM",
            command=self.start_system,
            style="Accent.TButton"
        )
        self.start_btn.pack(fill=tk.X, pady=5)
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="⏹ STOP SYSTEM",
            command=self.stop_system,
            state=tk.DISABLED
        )
        self.stop_btn.pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        history_btn = ttk.Button(
            control_frame,
            text="📊 View History",
            command=self.show_history
        )
        history_btn.pack(fill=tk.X, pady=5)
        
        exit_btn = ttk.Button(
            control_frame,
            text="🚪 Exit",
            command=self.on_closing
        )
        exit_btn.pack(fill=tk.X, pady=5)
        
        # Statistics
        stats_frame = ttk.LabelFrame(right_frame, text="📈 Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_label = ttk.Label(
            stats_frame,
            text="Total: 0\n✅ OK: 0\n❌ NG: 0",
            font=("Arial", 14, "bold")
        )
        self.stats_label.pack()
        
        # Classification Queue
        queue_frame = ttk.LabelFrame(right_frame, text="📦 Classification Queue", padding="10")
        queue_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        queue_scroll = ttk.Scrollbar(queue_frame)
        queue_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.queue_text = tk.Text(
            queue_frame,
            height=20,
            width=30,
            yscrollcommand=queue_scroll.set,
            font=("Consolas", 9)
        )
        self.queue_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        queue_scroll.config(command=self.queue_text.yview)
        
        # Status bar
        self.status_label = ttk.Label(
            self.root,
            text="System Idle - Ready to Start",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_system(self):
        """Start the sorting system"""
        if self.system_running:
            return
        
        # Check hardware connection
        if not self.hardware.is_connected():
            messagebox.showerror("Error", "Arduino not connected!\nCheck hardware connection.")
            return
        
        # Start hardware listening
        self.hardware.start_listening(self.on_ir_trigger)
        
        # Start conveyor
        self.hardware.start_conveyor()
        
        # Update state
        self.system_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="✅ SYSTEM RUNNING - Conveyor ON - Monitoring for bottles...")
        
        print("\n" + "="*60)
        print("🚀 SYSTEM STARTED")
        print("="*60)
        print("Conveyor: RUNNING")
        print("Monitoring: ACTIVE")
        print("Waiting for bottles to cross line...")
        print("="*60 + "\n")
    
    def stop_system(self):
        """Stop the sorting system"""
        if not self.system_running:
            return
        
        # Stop conveyor
        self.hardware.stop_conveyor()
        
        # Update state
        self.system_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹ SYSTEM STOPPED - Conveyor OFF")
        
        print("\n" + "="*60)
        print("⏹ SYSTEM STOPPED")
        print("="*60 + "\n")
    
    def _update_video_loop(self):
        """Continuous video update loop"""
        try:
            frame = self.camera.get_frame()
            
            if frame is not None:
                # Draw virtual line
                self._draw_virtual_line(frame)
                
                if self.system_running:
                    # Run AI detection and tracking
                    result = self.ai.predict_and_track(frame)
                    
                    # Draw tracking visualization
                    frame = self.ai.draw_tracking(frame, result['tracked_objects'])
                    
                    # Handle crossed objects
                    for crossed_obj in result['crossed_objects']:
                        self._on_bottle_crossed_line(crossed_obj, frame)
                
                # Convert to Tkinter format
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                
                # Resize to fit window
                display_width = 900
                h, w = frame_rgb.shape[:2]
                aspect_ratio = h / w
                display_height = int(display_width * aspect_ratio)
                img = img.resize((display_width, display_height), Image.LANCZOS)
                
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            
            # Schedule next update (30 FPS = ~33ms)
            self.root.after(33, self._update_video_loop)
            
        except Exception as e:
            print(f"[ERROR] Video update loop failed: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(100, self._update_video_loop)
    
    def _draw_virtual_line(self, frame):
        """Draw virtual line on frame"""
        h, w = frame.shape[:2]
        line_x = config.VIRTUAL_LINE_X
        
        # Draw vertical line
        cv2.line(
            frame,
            (line_x, 0),
            (line_x, h),
            config.LINE_COLOR,
            config.LINE_THICKNESS
        )
        
        # Draw label
        cv2.putText(
            frame,
            "DETECTION LINE",
            (line_x + 10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            config.LINE_COLOR,
            2
        )
        
        # Draw direction arrow
        cv2.arrowedLine(
            frame,
            (line_x + 100, 70),
            (line_x - 50, 70),
            config.LINE_COLOR,
            2,
            tipLength=0.3
        )
        cv2.putText(
            frame,
            "RIGHT → LEFT",
            (line_x - 50, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            config.LINE_COLOR,
            1
        )
    
    def _on_bottle_crossed_line(self, tracked_obj, frame):
        """
        Called when a bottle crosses the virtual line
        
        Actions:
        1. Add classification to queue
        2. Send classification to Arduino immediately
        3. Save snapshot
        4. Log to database
        5. Update UI
        """
        result = tracked_obj.classification_result
        reason = tracked_obj.classification_reason
        object_id = tracked_obj.object_id
        detected_classes = tracked_obj.detected_classes
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{'='*60}")
        print(f"🎯 BOTTLE CROSSED LINE!")
        print(f"{'='*60}")
        print(f"Object ID: {object_id}")
        print(f"Detected Classes: {detected_classes}")
        print(f"Classification: {result}")
        print(f"Reason: {reason}")
        print(f"{'='*60}\n")
        
        # Add to queue
        self.classification_queue.append({
            'result': result,
            'reason': reason,
            'timestamp': timestamp,
            'object_id': object_id,
            'detected_classes': detected_classes
        })
        
        # Send classification to Arduino immediately
        self.hardware.send_classification(result)
        
        # Save snapshot (in separate thread to avoid blocking)
        threading.Thread(
            target=self._save_and_log,
            args=(frame.copy(), result, reason, object_id, detected_classes),
            daemon=True
        ).start()
        
        # Update UI
        self.root.after(0, self._update_queue_display)
    
    def _save_and_log(self, frame, result, reason, object_id, detected_classes):
        """Save snapshot and log to database (runs in separate thread)"""
        try:
            # Save snapshot
            image_path = self._save_snapshot(frame, result, object_id)
            
            # Log to database
            self.database.add_inspection({
                'object_id': object_id,
                'detected_labels': detected_classes,
                'result': result,
                'reason': reason,
                'image_path': image_path,
                'processing_time': 0
            })
            
            if config.VERBOSE_LOGGING:
                print(f"[UI] Saved and logged: {result} | {image_path}")
        
        except Exception as e:
            print(f"[ERROR] Save and log failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_snapshot(self, frame, result, object_id):
        """Save annotated snapshot"""
        if not config.SAVE_SNAPSHOTS:
            return ""
        
        try:
            # Choose directory
            if result == 'OK':
                save_dir = config.CAPTURE_OK_PATH
            else:
                save_dir = config.CAPTURE_NG_PATH
            
            os.makedirs(save_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{result}_{object_id}_{timestamp}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # Save
            cv2.imwrite(filepath, frame)
            
            return filepath
            
        except Exception as e:
            print(f"[ERROR] Save snapshot failed: {e}")
            return ""
    
    def on_ir_trigger(self):
        """
        Called when Arduino sends 'T' (IR sensor triggered)
        
        Actions:
        1. Pop oldest classification from queue
        2. Update statistics
        3. Update UI
        
        Note: Classification was already sent to Arduino when bottle crossed line
        This is just for bookkeeping and statistics
        """
        print("\n" + "="*60)
        print("🔔 IR SENSOR TRIGGERED!")
        print("="*60)
        
        if len(self.classification_queue) == 0:
            print("⚠️ WARNING: IR triggered but queue is EMPTY!")
            print("Possible causes:")
            print("  - Bottle passed without crossing virtual line")
            print("  - System just started")
            print("  - Queue/timing mismatch")
            print("="*60 + "\n")
            return
        
        # Pop oldest from queue (FIFO)
        item = self.classification_queue.pop(0)
        
        result = item['result']
        reason = item['reason']
        timestamp = item['timestamp']
        object_id = item['object_id']
        
        print(f"Processing queued classification:")
        print(f"  Object ID: {object_id}")
        print(f"  Result: {result}")
        print(f"  Reason: {reason}")
        print(f"  Time: {timestamp}")
        print(f"  Queue remaining: {len(self.classification_queue)}")
        print("="*60 + "\n")
        
        # Update statistics
        self.total_count += 1
        if result == 'OK':
            self.ok_count += 1
        else:
            self.ng_count += 1
        
        # Update UI
        self.root.after(0, self._update_statistics_display)
        self.root.after(0, self._update_queue_display)
    
    def _update_queue_display(self):
        """Update queue text widget"""
        self.queue_text.delete('1.0', tk.END)
        
        if len(self.classification_queue) == 0:
            self.queue_text.insert(tk.END, "Queue is empty\n\n")
            self.queue_text.insert(tk.END, "Waiting for bottles to cross line...")
        else:
            self.queue_text.insert(tk.END, f"Queue Size: {len(self.classification_queue)}\n")
            self.queue_text.insert(tk.END, "="*40 + "\n\n")
            
            # Show items (most recent at top)
            for i, item in enumerate(reversed(self.classification_queue[-10:])):
                result_icon = "✅" if item['result'] == 'OK' else "❌"
                self.queue_text.insert(tk.END, f"{result_icon} Object #{item['object_id']}\n")
                self.queue_text.insert(tk.END, f"   Time: {item['timestamp']}\n")
                self.queue_text.insert(tk.END, f"   Result: {item['result']}\n")
                self.queue_text.insert(tk.END, f"   {item['reason']}\n\n")
    
    def _update_statistics_display(self):
        """Update statistics label"""
        stats_text = f"Total: {self.total_count}\n"
        stats_text += f"✅ OK: {self.ok_count}\n"
        stats_text += f"❌ NG: {self.ng_count}"
        
        if self.total_count > 0:
            ok_percent = (self.ok_count / self.total_count) * 100
            stats_text += f"\n\nYield: {ok_percent:.1f}%"
        
        self.stats_label.config(text=stats_text)
    
    def show_history(self):
        """Show history window"""
        from ui.history_window import HistoryWindow
        HistoryWindow(self.root, self.database)
    
    def on_closing(self):
        """Handle window close"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            print("\n[UI] Closing application...")
            
            if self.system_running:
                self.stop_system()
            
            self.camera.stop()
            self.hardware.stop()
            self.root.destroy()
