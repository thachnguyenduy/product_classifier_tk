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
        self.last_queue_time = 0  # For queue cooldown (when crossing line)
        self.tracked_bottles = {}  # Track bottles: {id: {'cx': x, 'cy': y, 'last_seen': time}}
        self.next_bottle_id = 0
        
        # Continuous detection state
        self.last_ai_result = None  # Last AI detection result (for display)
        self.processing_ai = False  # Flag to prevent concurrent AI processing
        
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
            
            if self.system_running:
                # LINE CROSSING CHECK - Blob detection và line crossing logic
                self._check_crossing(frame)
                
                # CONTINUOUS AI DETECTION - Hiển thị AI bounding boxes (sau blob detection)
                self._run_continuous_ai_detection(frame)
            
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
        Check if bottle crosses virtual line from RIGHT to LEFT
        
        Logic:
        - Bottle starts at RIGHT (cx > line_x)
        - Moves LEFT (cx decreases)
        - Crosses line (cx passes line_x)
        - Only trigger once when crossing from right to left
        """
        current_time = time.time()
        
        # Cooldown check
        if current_time - self.last_detection_time < config.DETECTION_COOLDOWN:
            return
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Try multiple threshold methods
        thresh1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY_INV, 11, 2)
        _, thresh2 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        contours1, _ = cv2.findContours(thresh1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours2, _ = cv2.findContours(thresh2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        contours = contours1 if len(contours1) > len(contours2) else contours2
        
        if len(contours) == 0:
            if config.DEBUG_MODE:
                print("[Blob] No contours found")
            return
        
        # Find valid bottle contours
        valid_bottles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Reduced threshold for better detection
            if area < 5000:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(h) / float(w) if w > 0 else 0
            
            # More lenient aspect ratio
            if aspect_ratio < 1.0 or aspect_ratio > 6.0:
                continue
            
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
            if config.DEBUG_MODE:
                print("[Blob] No valid bottles found")
            return
        
        # Clean old tracked bottles (not seen for 2 seconds)
        current_time = time.time()
        self.tracked_bottles = {
            bid: data for bid, data in self.tracked_bottles.items()
            if current_time - data['last_seen'] < 2.0
        }
        
        # Match bottles to tracked ones or create new
        line_x = config.VIRTUAL_LINE_X
        tolerance = config.CROSSING_TOLERANCE
        
        for bottle in valid_bottles:
            cx, cy = bottle['center']
            x, y, w, h = bottle['bbox']
            
            # Find closest tracked bottle
            matched_id = None
            min_dist = float('inf')
            
            for bid, tracked in self.tracked_bottles.items():
                dist = abs(cx - tracked['cx']) + abs(cy - tracked['cy'])
                if dist < min_dist and dist < 100:  # Max 100 pixels movement
                    min_dist = dist
                    matched_id = bid
            
            # Create new tracking if no match
            if matched_id is None:
                matched_id = self.next_bottle_id
                self.next_bottle_id += 1
                self.tracked_bottles[matched_id] = {
                    'cx': cx,
                    'cy': cy,
                    'last_seen': current_time,
                    'crossed': False
                }
            
            # Update tracking
            tracked = self.tracked_bottles[matched_id]
            prev_cx = tracked['cx']
            tracked['cx'] = cx
            tracked['cy'] = cy
            tracked['last_seen'] = current_time
            
            # Draw bounding box
            color = (0, 255, 0) if not tracked.get('crossed', False) else (128, 128, 128)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.circle(frame, (cx, cy), 5, color, -1)
            
            # Show direction arrow and position info
            if prev_cx != cx:
                direction = "←" if cx < prev_cx else "→"
                cv2.putText(frame, direction, (cx + 10, cy), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Show position relative to line
            if config.DEBUG_MODE:
                pos_text = f"x={cx}"
                if cx > line_x:
                    pos_text += " (RIGHT)"
                elif cx < line_x:
                    pos_text += " (LEFT)"
                else:
                    pos_text += " (LINE)"
                
                cv2.putText(frame, pos_text, (x, y + h + 15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
            
            # Check crossing from RIGHT to LEFT
            # Previous position was RIGHT of line, current is at or LEFT of line
            if not tracked.get('crossed', False):
                # Check if bottle moved from right side to left side of line
                was_right = prev_cx > line_x
                is_at_or_left = cx <= line_x + tolerance
                moved_left = cx < prev_cx  # Moving left direction
                
                if was_right and is_at_or_left and moved_left:
                    # Bottle crossed from right to left!
                    tracked['crossed'] = True
                    
                    # Draw RED box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 3)
                    cv2.putText(frame, "CROSSING!", (x, y - 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    if config.DEBUG_MODE:
                        print(f"[Blob] ✅ Bottle #{matched_id} CROSSED LINE!")
                        print(f"  From: {prev_cx} (RIGHT) → To: {cx} (LEFT)")
                        print(f"  Line: {line_x}, Tolerance: {tolerance}")
                        print(f"  Conditions: was_right={was_right}, is_at_or_left={is_at_or_left}, moved_left={moved_left}")
                    
                    # Trigger detection
                    self._on_bottle_detected(frame, cx, cy)
                    self.last_detection_time = current_time
                    return
    
    def _run_continuous_ai_detection(self, frame):
        """
        Run AI detection continuously to show bounding boxes
        
        This runs every frame but does NOT add to queue
        Only for visual display
        """
        current_time = time.time()
        
        # Throttle: Run AI every 0.3 seconds (~3 FPS) to avoid overload
        if current_time - getattr(self, '_last_ai_time', 0) < 0.3:
            # Draw last result on current frame
            if self.last_ai_result is not None:
                self._draw_ai_results_on_frame(frame, self.last_ai_result)
            return
        
        # Run AI in background if not already processing
        if not self.processing_ai:
            self.processing_ai = True
            self._last_ai_time = current_time
            threading.Thread(target=self._process_continuous_ai, args=(frame.copy(),), daemon=True).start()
        elif self.last_ai_result is not None:
            # Draw cached result while processing
            self._draw_ai_results_on_frame(frame, self.last_ai_result)
    
    def _draw_ai_results_on_frame(self, frame, result_dict):
        """
        Draw AI detection results on frame
        """
        if result_dict is None or 'detections' not in result_dict:
            return
        
        for det in result_dict['detections']:
            x1, y1, x2, y2 = det['box']
            class_id = det['cls']
            confidence = det['conf']
            class_name = self.ai.class_names[class_id]
            
            # Choose color
            if class_id < 4:  # Defects
                color = (0, 0, 255)  # Red
            else:  # Good parts
                color = (0, 255, 0)  # Green
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 4), (x1 + tw, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _process_continuous_ai(self, frame):
        """
        Process AI detection for continuous display (NOT for queue)
        """
        try:
            result_dict = self.ai.predict(frame)
            
            # Cache result for display
            self.last_ai_result = result_dict
            
            # Update detection display panel
            self.root.after(0, lambda: self._update_detection_display(
                result_dict['annotated_image'],
                result_dict['result'],
                result_dict.get('reason', '')
            ))
            
            if config.DEBUG_MODE:
                num_detections = len(result_dict['detections'])
                if num_detections > 0:
                    print(f"[AI] Continuous detection: {num_detections} objects")
                    for det in result_dict['detections'][:3]:  # Show first 3
                        print(f"  - {self.ai.class_names[det['cls']]}: {det['conf']:.2f}")
                else:
                    print(f"[AI] Continuous detection: No objects found")
            
        except Exception as e:
            print(f"[ERROR] Continuous AI detection failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.processing_ai = False
    
    def _on_bottle_detected(self, frame, cx, cy):
        """
        Called when bottle crosses virtual line
        
        Actions:
        1. Run AI prediction
        2. Add result to FIFO queue (ONLY when crossing line)
        3. Save snapshot
        """
        current_time = time.time()
        
        # Queue cooldown (prevent multiple adds)
        if current_time - self.last_queue_time < config.DETECTION_COOLDOWN:
            if config.DEBUG_MODE:
                print(f"[UI] Queue cooldown active, skipping...")
            return
        
        print(f"[UI] Bottle crossed line at ({cx}, {cy}) - Adding to queue")
        
        # Run AI prediction in separate thread to avoid blocking UI
        threading.Thread(target=self._process_detection_for_queue, args=(frame.copy(),), daemon=True).start()
    
    def _process_detection_for_queue(self, frame):
        """
        Process detection when bottle crosses line - ADD TO QUEUE
        
        This is called ONLY when bottle crosses the virtual line
        """
        try:
            # Run AI
            result_dict = self.ai.predict(frame)
            
            result = result_dict['result']
            reason = result_dict['reason']
            timestamp = datetime.now().strftime("%H:%M:%S")
            annotated_image = result_dict['annotated_image']
            
            # Save snapshot
            image_path = self._save_snapshot(annotated_image, result)
            
            # Add to queue (ONLY when crossing line)
            queue_item = {
                'result': result,
                'reason': reason,
                'timestamp': timestamp,
                'image_path': image_path,
                'annotated_image': annotated_image
            }
            
            self.product_queue.append(queue_item)
            self.last_queue_time = time.time()
            
            # Update UI (queue + detection display)
            self.root.after(0, lambda: self._update_detection_display(annotated_image, result, reason))
            self.root.after(0, self._update_queue_display)
            
            # Log to database
            result_dict['image_path'] = image_path
            self.database.add_inspection(result_dict)
            
            print(f"[UI] ✅ Added to queue: {result} | Reason: {reason} | Queue size: {len(self.product_queue)}")
            
        except Exception as e:
            print(f"[ERROR] Queue detection processing failed: {e}")
            import traceback
            traceback.print_exc()
    
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

