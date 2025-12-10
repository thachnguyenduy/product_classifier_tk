"""
Configuration File - Coca-Cola Sorting System
Điều chỉnh các tham số ở đây
"""

# ============================================
# AI MODEL SETTINGS
# ============================================

# Confidence threshold (0.0 - 1.0)
# - Giảm xuống (0.2-0.3): Detect nhiều hơn, có thể bị false positive
# - Tăng lên (0.5-0.7): Chỉ detect chắc chắn, có thể bị miss
CONFIDENCE_THRESHOLD = 0.3  # Mặc định: 0.3

# Model path
# - Dùng NCNN: "model/best_ncnn_model"
# - Dùng YOLOv8: "model/best.pt"
MODEL_PATH = "model/best_ncnn_model"

# ============================================
# SORTING LOGIC SETTINGS
# ============================================

# Yêu cầu phải có đủ các components này
REQUIRE_CAP = True      # Phải có nắp
REQUIRE_FILLED = True   # Phải đổ đầy
REQUIRE_LABEL = True    # Phải có nhãn

# Nếu muốn "lỏng" hơn, có thể set False cho một số components
# VD: REQUIRE_LABEL = False  # Không bắt buộc phải có nhãn

# ============================================
# CAPTURE SETTINGS
# ============================================

# Số ảnh chụp khi detect chai
NUM_CAPTURE_FRAMES = 5

# Delay giữa các ảnh (seconds)
FRAME_DELAY = 0.1  # 100ms

# ============================================
# CAMERA SETTINGS
# ============================================

CAMERA_ID = 0  # 0 = camera mặc định
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# ============================================
# ARDUINO SETTINGS
# ============================================

ARDUINO_PORT = '/dev/ttyUSB0'  # Linux
# ARDUINO_PORT = 'COM3'  # Windows
ARDUINO_BAUDRATE = 9600

# ============================================
# TESTING MODE
# ============================================

# Bật dummy mode để test không cần hardware
USE_DUMMY_CAMERA = False
USE_DUMMY_HARDWARE = False

# ============================================
# DEBUG SETTINGS
# ============================================

# Hiển thị debug info trong terminal
DEBUG_MODE = True

# Lưu ảnh debug
SAVE_DEBUG_IMAGES = True

