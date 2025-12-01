"""Tkinter UI for the Raspberry Pi product classifier."""
from __future__ import annotations

import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

import cv2
from PIL import Image, ImageTk

from core.ai import AIModel
from core.camera import CameraStreamer
from core.database import ProductDatabase
from core.hardware import HardwareController
from ui.history_window import HistoryWindow


class ProductClassifierApp(tk.Tk):
    """Main Tkinter application."""

    def __init__(self, model_path: Path, database_path: Path) -> None:
        super().__init__()
        self.title("Phân loại sản phẩm - Raspberry Pi 5")
        self.geometry("1100x650")
        self.configure(bg="#1e1e1e")

        self.model_path = model_path
        self.database_path = database_path

        self.camera = CameraStreamer()
        self.ai_model = AIModel(model_path)
        self.database = ProductDatabase(database_path)
        self.hardware = HardwareController()

        self.video_label = ttk.Label(self, text="Camera feed", anchor=tk.CENTER)

        self.detection_enabled = False
        self._detection_in_progress = False
        self._last_result: Optional[dict] = None

        self.fps_var = tk.StringVar(value="FPS: --")
        self.result_var = tk.StringVar(value="Result: --")
        self.confidence_var = tk.StringVar(value="Confidence: --")

        self._build_menu()
        self._build_layout()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(50, self._update_loop)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Hardware test", command=self._hardware_test)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="History", command=self._open_history)
        menubar.add_cascade(label="View", menu=view_menu)

        self.config(menu=menubar)

    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        camera_frame = ttk.Frame(main_frame)
        camera_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.video_label = tk.Label(camera_frame, text="Camera feed", bg="#000000", fg="#ffffff")
        self.video_label.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(main_frame, width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        button_specs = [
            ("Start Camera", self.start_camera),
            ("Stop Camera", self.stop_camera),
            ("Start Detection", self.start_detection),
            ("Stop Detection", self.stop_detection),
            ("Start Conveyor", self.hardware.start_conveyor),
            ("Stop Conveyor", self.hardware.stop_conveyor),
        ]

        for text, command in button_specs:
            btn = ttk.Button(control_frame, text=text, command=command)
            btn.pack(fill=tk.X, pady=5)

        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Button(control_frame, text="History", command=self._open_history).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Hardware test", command=self._hardware_test).pack(fill=tk.X, pady=5)

        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        ttk.Label(status_frame, textvariable=self.fps_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, textvariable=self.result_var).pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, textvariable=self.confidence_var).pack(side=tk.LEFT, padx=5)

    def start_camera(self) -> None:
        if self.camera.start():
            self.result_var.set("Result: --")
        else:
            messagebox.showerror("Camera", "Unable to access camera.")

    def stop_camera(self) -> None:
        self.camera.stop()
        self.stop_detection()
        self.video_label.config(text="Camera stopped", image="")

    def start_detection(self) -> None:
        if not self.camera.running:
            messagebox.showwarning("Detection", "Start the camera first.")
            return
        self.detection_enabled = True
        print("Detection enabled")  # Debug log

    def stop_detection(self) -> None:
        self.detection_enabled = False
        self._detection_in_progress = False
        self._last_result = None
        self.result_var.set("Result: --")
        self.confidence_var.set("Confidence: --")
        print("Detection stopped")  # Debug log

    def _open_history(self) -> None:
        HistoryWindow(self, self.database)

    def _hardware_test(self) -> None:
        threading.Thread(target=self.hardware.hardware_test, daemon=True).start()

    def _update_loop(self) -> None:
        frame, fps = self.camera.get_frame()
        if frame is not None:
            display_frame = frame.copy()
            
            # Draw bounding boxes if we have detection results
            if self._last_result and self._last_result.get("detections"):
                defect_keywords = ["defect", "wrong"]
                
                for det in self._last_result["detections"]:
                    x1, y1, x2, y2 = det["bbox"]
                    label_lower = det["label"].lower()
                    
                    # Red for defects, green for normal parts
                    is_defect = any(kw in label_lower for kw in defect_keywords)
                    color = (0, 0, 255) if is_defect else (0, 255, 0)  # BGR: Red or Green
                    thickness = 3 if is_defect else 2
                    
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)
                    label_text = f"{det['label']} {det['confidence']:.2f}"
                    
                    # Background for text
                    (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(display_frame, (x1, y1 - text_h - 10), (x1 + text_w, y1), color, -1)
                    cv2.putText(display_frame, label_text, (x1, y1 - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=image.resize((640, 480)))
            self.video_label.configure(image=imgtk, text="")
            self.video_label.image = imgtk
            self.fps_var.set(f"FPS: {fps:.1f}")

            if self.detection_enabled and not self._detection_in_progress:
                self._detection_in_progress = True
                frame_copy = frame.copy()
                threading.Thread(target=self._run_detection, args=(frame_copy,), daemon=True).start()

        else:
            self.video_label.configure(text="No frame", image="")

        self.after(50, self._update_loop)

    def _run_detection(self, frame) -> None:
        try:
            print("Running detection...")  # Debug log
            result = self.ai_model.predict(frame)
            print(f"Detection result: {result}")  # Debug log
            timestamp = datetime.now().isoformat(timespec="seconds")
            self.after(0, lambda: self._handle_detection_result(result, timestamp, None))
        except Exception as exc:
            print(f"Detection error: {exc}")  # Debug log
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self._handle_detection_result(None, None, exc))
        finally:
            self.after(0, lambda: setattr(self, "_detection_in_progress", False))

    def _handle_detection_result(self, result: Optional[dict], timestamp: Optional[str], error: Optional[Exception]) -> None:
        if error:
            messagebox.showerror("Detection error", str(error))
            return
        if not result or not timestamp:
            return

        # Store result for drawing bounding boxes
        self._last_result = result
        
        # Save to database
        self.database.insert_result(timestamp, result["result"], float(result["confidence"]))
        
        # Trigger hardware action for bad products
        if result["result"] == "BAD":
            threading.Thread(target=self.hardware.push_bad_product, daemon=True).start()

        # Update status bar
        self.result_var.set(f"Result: {result['result']}")
        self.confidence_var.set(f"Confidence: {result['confidence']:.2f}")
        
        # Show detection info
        if result.get("detections"):
            det_count = len(result["detections"])
            print(f"Found {det_count} detection(s)")  # Debug log

    def on_close(self) -> None:
        self.detection_enabled = False
        self.camera.stop()
        self.hardware.cleanup()
        self.destroy()

