"""Main Window - Giao diện phân loại sản phẩm."""
import threading
import time
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk
import cv2

from core.ai import AIModel
from core.camera import CameraStreamer
from core.database import ProductDatabase
from core.hardware import HardwareController


class MainWindow(tk.Tk):
    """Giao diện chính - Phân loại sản phẩm Coca-Cola."""

    def __init__(self, model_path: Path, database_path: Path):
        super().__init__()

        self.title("MainWindow")
        self.geometry("1400x800")
        self.configure(bg="#f0f0f0")

        # Initialize components
        self.camera = CameraStreamer(camera_index=0, width=640, height=480)
        self.ai_model = AIModel(model_path)
        self.database = ProductDatabase(database_path)
        self.hardware = HardwareController()

        # State variables
        self.detection_running = False
        self.conveyor_running = False
        self.last_result = None
        self.processing_time_ms = 0
        
        # Image references (prevent garbage collection)
        self.raw_photo = None
        self.result_photo = None

        # Build UI
        self._build_ui()

        # Start update loop
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._update_loop)

    def _build_ui(self):
        """Xây dựng giao diện."""
        # === LEFT PANEL: Raw Camera ===
        self.frame_left = tk.Frame(self, bg="#d0d0d0", width=540, height=720)
        self.frame_left.place(x=10, y=40)
        self.frame_left.pack_propagate(False)
        
        self.lbl_raw = tk.Label(self.frame_left, bg="#d0d0d0", text="Camera gốc")
        self.lbl_raw.pack(fill=tk.BOTH, expand=True)

        # === MIDDLE PANEL: Detection Result ===
        self.frame_middle = tk.Frame(self, bg="#d0d0d0", width=540, height=720)
        self.frame_middle.place(x=560, y=40)
        self.frame_middle.pack_propagate(False)
        
        self.lbl_result_img = tk.Label(self.frame_middle, bg="#d0d0d0", text="Kết quả detection")
        self.lbl_result_img.pack(fill=tk.BOTH, expand=True)

        # === RIGHT PANEL: Controls ===
        self.frame_right = tk.Frame(self, bg="#e8f4f8", width=220, height=720)
        self.frame_right.place(x=1110, y=40)

        # MỞ CAMERA button
        self.btn_camera = tk.Button(
            self.frame_right,
            text="MỞ CAMERA",
            font=("Arial", 11),
            width=16,
            height=2,
            bg="white",
            relief="solid",
            command=self._toggle_camera
        )
        self.btn_camera.place(x=20, y=20)

        # CHẠY BĂNG TẢI button  
        self.btn_conveyor = tk.Button(
            self.frame_right,
            text="CHẠY BĂNG TẢI",
            font=("Arial", 11),
            width=16,
            height=2,
            bg="white",
            relief="solid",
            command=self._toggle_conveyor
        )
        self.btn_conveyor.place(x=20, y=90)

        # KẾT QUẢ label
        tk.Label(
            self.frame_right,
            text="KẾT QUẢ",
            font=("Arial", 11, "bold"),
            width=16,
            height=2,
            bg="white",
            relief="solid"
        ).place(x=20, y=200)

        # Result value
        self.lbl_result = tk.Label(
            self.frame_right,
            text="---",
            font=("Arial", 11, "bold"),
            width=16,
            height=2,
            bg="white",
            relief="solid"
        )
        self.lbl_result.place(x=20, y=270)

        # THỜI GIAN XỬ LÝ label
        tk.Label(
            self.frame_right,
            text="THỜI GIAN XỬ LÝ",
            font=("Arial", 11, "bold"),
            width=16,
            height=2,
            bg="white",
            relief="solid"
        ).place(x=20, y=380)

        # Processing time value
        self.lbl_time = tk.Label(
            self.frame_right,
            text="0.00",
            font=("Arial", 11, "bold"),
            width=16,
            height=2,
            bg="white",
            relief="solid"
        )
        self.lbl_time.place(x=20, y=450)

    def _toggle_camera(self):
        """Bật/tắt camera."""
        if not self.camera.running:
            if self.camera.start():
                self.btn_camera.config(text="TẮT CAMERA", bg="#ffcccc")
                self.detection_running = True
                print("[UI] Camera ON")
            else:
                messagebox.showerror("Lỗi", "Không thể mở camera!")
        else:
            self.detection_running = False
            self.camera.stop()
            self.btn_camera.config(text="MỞ CAMERA", bg="white")
            self.lbl_raw.config(image="", text="Camera gốc")
            self.lbl_result_img.config(image="", text="Kết quả detection")
            print("[UI] Camera OFF")

    def _toggle_conveyor(self):
        """Bật/tắt băng tải."""
        if not self.conveyor_running:
            self.hardware.start_conveyor()
            self.conveyor_running = True
            self.btn_conveyor.config(text="DỪNG BĂNG TẢI", bg="#90EE90")
        else:
            self.hardware.stop_conveyor()
            self.conveyor_running = False
            self.btn_conveyor.config(text="CHẠY BĂNG TẢI", bg="white")

    def _update_loop(self):
        """Vòng lặp cập nhật."""
        if self.camera.running:
            frame, fps = self.camera.get_frame()

            if frame is not None:
                # Display raw frame (video realtime)
                self._show_image(frame, self.lbl_raw, "raw")

                # Run detection khi enabled
                if self.detection_running and not hasattr(self, '_detecting'):
                    self._detecting = True
                    threading.Thread(
                        target=self._run_detection, 
                        args=(frame.copy(),), 
                        daemon=True
                    ).start()

        self.after(30, self._update_loop)

    def _run_detection(self, frame):
        """Chạy detection và hiển thị kết quả."""
        try:
            start = time.time()
            result = self.ai_model.predict(frame)
            self.processing_time_ms = (time.time() - start) * 1000

            if result and result.get("detections"):
                # Có detection → vẽ bounding boxes
                result_frame = frame.copy()
                
                for det in result["detections"]:
                    x1, y1, x2, y2 = det["bbox"]
                    label = det["label"]
                    conf = det["confidence"]
                    
                    # Màu cam cho tất cả boxes
                    color = (0, 165, 255)  # BGR: Orange
                    cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Vẽ label
                    text = f"{label} {conf:.2f}"
                    cv2.putText(result_frame, text, (x1, y1-5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Hiển thị ảnh kết quả (ảnh tĩnh, không update liên tục)
                self.after(0, lambda: self._show_image(result_frame, self.lbl_result_img, "result"))

                # Update labels
                res = result.get("result", "---")
                reason = result.get("reason", "")
                
                if res == "BAD":
                    self.after(0, lambda: self.lbl_result.config(text="HÀNG BỊ LỖI", bg="#ffcccc"))
                    # Trigger hardware
                    if self.conveyor_running:
                        threading.Thread(target=self.hardware.eject_bad_product, daemon=True).start()
                else:
                    self.after(0, lambda: self.lbl_result.config(text="HÀNG TỐT", bg="#90EE90"))

                # Save to DB
                self.database.insert_result(
                    datetime.now().isoformat(timespec="seconds"),
                    res,
                    result.get("confidence", 0)
                )
                
                # Update time
                self.after(0, lambda: self.lbl_time.config(text=f"{self.processing_time_ms:.2f}"))
                
                print(f"[Result] {res} - {reason}")

        except Exception as e:
            print(f"[Detection] Error: {e}")
        finally:
            self._detecting = False

    def _show_image(self, frame, label, img_type):
        """Hiển thị ảnh."""
        try:
            # Resize
            h, w = frame.shape[:2]
            scale = min(530 / w, 710 / h)
            new_size = (int(w * scale), int(h * scale))
            resized = cv2.resize(frame, new_size)

            # BGR to RGB
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            photo = ImageTk.PhotoImage(img)

            # Update
            label.config(image=photo, text="")
            
            # Keep reference
            if img_type == "raw":
                self.raw_photo = photo
            else:
                self.result_photo = photo

        except Exception as e:
            print(f"[Display] Error: {e}")

    def _on_close(self):
        """Đóng ứng dụng."""
        self.detection_running = False
        if self.conveyor_running:
            self.hardware.stop_conveyor()
        self.camera.stop()
        self.hardware.cleanup()
        self.destroy()
