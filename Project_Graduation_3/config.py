# ============================================
# COCA-COLA SORTING SYSTEM - CONFIGURATION
# OPTIMIZED FOR RASPBERRY PI 5
# ============================================
"""
Configuration tối ưu cho Raspberry Pi 5

PERFORMANCE OPTIMIZATIONS:
- NCNN model (5-10x faster than YOLO)
- Reduced resolution for better FPS
- Optimized thread count
- Lower detection threshold for speed
"""

# ============================================
# AI MODEL SETTINGS - NCNN (OPTIMIZED)
# ============================================
# Using NCNN model for better performance on Raspberry Pi 5
MODEL_PATH_NCNN = "model/best_ncnn_model"
MODEL_PARAM = "model.ncnn.param"
MODEL_BIN = "model.ncnn.bin"
INPUT_SIZE = 640

# Detection Thresholds (optimized for speed)
CONFIDENCE_THRESHOLD = 0.25  # Lowered for better detection
NMS_THRESHOLD = 0.45

# Class Names (STRICT ORDER - DO NOT CHANGE)
CLASS_NAMES = [
    'Cap-Defect',      # 0 - Defect
    'Filling-Defect',  # 1 - Defect
    'Label-Defect',    # 2 - Defect
    'Wrong-Product',   # 3 - Defect
    'cap',             # 4 - Good component
    'coca',            # 5 - Identity (NOT for classification)
    'filled',          # 6 - Good component
    'label'            # 7 - Good component
]

# ============================================
# CLASSIFICATION LOGIC (CRITICAL)
# ============================================
"""
Classification Rules (STRICT):

1. DEFECT CLASSES (0-3):
   → If ANY defect detected → Result = NG

2. GOOD CLASSES (4, 6, 7):
   → If ALL three present AND NO defects → Result = OK
   → If ANY missing → Result = NG

3. IDENTITY CLASS (5):
   → "coca" used ONLY for identity
   → MUST NOT be used for OK/NG classification
"""

DEFECT_CLASS_IDS = [0, 1, 2, 3]
GOOD_CLASS_IDS = [4, 6, 7]
IDENTITY_CLASS_ID = 5

# ============================================
# LINE CROSSING (SOFTWARE SENSOR)
# ============================================
VIRTUAL_LINE_X = 320  # X position (center of 640px frame)
CROSSING_TOLERANCE = 10

# ============================================
# CAMERA SETTINGS (OPTIMIZED FOR PI 5)
# ============================================
CAMERA_ID = 0
CAMERA_WIDTH = 640   # Optimal resolution for Pi 5
CAMERA_HEIGHT = 480  # Balanced quality/speed
CAMERA_FPS = 30

# Exposure settings
CAMERA_AUTO_EXPOSURE = False
CAMERA_EXPOSURE = -6

# ============================================
# ARDUINO COMMUNICATION
# ============================================
ARDUINO_PORT = '/dev/ttyUSB0'  # Change if needed
# Alternatives: /dev/ttyACM0, /dev/ttyUSB1
ARDUINO_BAUDRATE = 9600
ARDUINO_TIMEOUT = 1.0

# Serial Commands
CMD_OK = 'O'
CMD_NG = 'N'
CMD_START = 'S'
CMD_STOP = 'P'
CMD_TRIGGER = 'T'

# ============================================
# HARDWARE PINS (Arduino)
# ============================================
PIN_IR_SENSOR = 2
PIN_RELAY = 4
PIN_SERVO = 9

SERVO_IDLE = 0
SERVO_BLOCK = 100

# ============================================
# UI SETTINGS (OPTIMIZED)
# ============================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# Video display size (reduce for better performance)
VIDEO_DISPLAY_WIDTH = 800   # Reduced from 900
VIDEO_DISPLAY_HEIGHT = 600  # Scaled proportionally

# Virtual Line Color
LINE_COLOR = (0, 255, 255)  # Cyan
LINE_THICKNESS = 3

# UI Update Rate (optimized)
UI_UPDATE_INTERVAL = 33  # ms (30 FPS)

# ============================================
# DATABASE SETTINGS
# ============================================
DB_PATH = "database/product.db"

# ============================================
# CAPTURE SETTINGS
# ============================================
CAPTURE_OK_PATH = "captures/ok"
CAPTURE_NG_PATH = "captures/ng"
SAVE_SNAPSHOTS = True

# ============================================
# PERFORMANCE SETTINGS (RASPBERRY PI 5)
# ============================================
# Detection cooldown (prevent overload)
DETECTION_COOLDOWN = 0.8  # seconds

# Object tracking
MAX_TRACKING_DISTANCE = 100  # pixels
OBJECT_TIMEOUT = 3.0  # seconds

# Thread settings (optimized for Pi 5)
NCNN_NUM_THREADS = 4  # Pi 5 has 4 cores
USE_VULKAN = False    # Disable for stability

# Skip frames for performance (process every Nth frame)
SKIP_FRAMES = 0  # 0 = process all frames, 1 = skip every other frame

# ============================================
# DEBUG SETTINGS
# ============================================
DEBUG_MODE = True  # Set True for debugging, False for production
VERBOSE_LOGGING = True  # Set True to see detailed logs

# ============================================
# TESTING MODE
# ============================================
USE_DUMMY_CAMERA = False
USE_DUMMY_HARDWARE = False

# ============================================
# SYSTEM INFORMATION
# ============================================
SYSTEM_NAME = "Coca-Cola Bottle Sorting System"
VERSION = "2.0.0 - NCNN Optimized"
MODE = "Line Crossing with NCNN"

print(f"[Config] {SYSTEM_NAME} v{VERSION}")
print(f"[Config] Mode: {MODE}")
print(f"[Config] Model: NCNN (Optimized for Raspberry Pi 5)")
print(f"[Config] Resolution: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
print(f"[Config] Classes: {len(CLASS_NAMES)}")
print(f"[Config] Virtual Line: x={VIRTUAL_LINE_X}")
print(f"[Config] Performance: Optimized for real-time processing")
