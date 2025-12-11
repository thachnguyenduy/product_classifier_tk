# ============================================
# COCA-COLA SORTING SYSTEM - CONFIGURATION
# FIFO Queue Logic with Virtual Line Detection
# ============================================

# ============================================
# AI MODEL SETTINGS (NCNN)
# ============================================
MODEL_PATH = "model/best_ncnn_model"  # Updated to match actual folder
MODEL_PARAM = "model.ncnn.param"       # Actual filename
MODEL_BIN = "model.ncnn.bin"           # Actual filename
INPUT_SIZE = 640

# Detection Thresholds
CONFIDENCE_THRESHOLD = 0.5
NMS_THRESHOLD = 0.45

# Class Names (8 classes)
CLASS_NAMES = [
    'Cap-Defect',      # 0
    'Filling-Defect',  # 1
    'Label-Defect',    # 2
    'Wrong-Product',   # 3
    'cap',             # 4
    'coca',            # 5
    'filled',          # 6
    'label'            # 7
]

# ============================================
# SORTING LOGIC
# ============================================
# Defect classes (0-3)
DEFECT_CLASSES = [0, 1, 2, 3]

# Required good components
REQUIRED_COMPONENTS = {
    'cap': 4,
    'filled': 6,
    'label': 7
}

# ============================================
# VIRTUAL LINE DETECTION
# ============================================
VIRTUAL_LINE_X = 320  # Pixel position (center of 640px frame)
CROSSING_TOLERANCE = 20  # Pixels tolerance for crossing detection
DETECTION_COOLDOWN = 1.0  # Seconds between detections

# ============================================
# CAMERA SETTINGS
# ============================================
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Manual exposure (reduce motion blur)
CAMERA_AUTO_EXPOSURE = False
CAMERA_EXPOSURE = -6

# ============================================
# ARDUINO COMMUNICATION
# ============================================
ARDUINO_PORT = '/dev/ttyUSB0'  # Arduino Uno CH340 (chip dán) - Change if needed
# Common alternatives: /dev/ttyACM0, /dev/ttyUSB1
# Check with: ls /dev/ttyUSB* or ls /dev/ttyACM*
ARDUINO_BAUDRATE = 9600
ARDUINO_TIMEOUT = 1

# Serial Commands
CMD_TRIGGER = 'T'  # IR Sensor detected bottle
CMD_KICK = 'K'     # Command to kick NG bottle
CMD_OK = 'O'       # OK bottle (optional, for logging)

# ============================================
# UI SETTINGS
# ============================================
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700

# Virtual Line Color (Cyan)
LINE_COLOR = (0, 255, 255)
LINE_THICKNESS = 3

# Queue Display
MAX_QUEUE_DISPLAY = 10  # Show last N items in queue

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
# DEBUG SETTINGS
# ============================================
DEBUG_MODE = True
SAVE_DEBUG_IMAGES = True

# Print verbose logs
VERBOSE_LOGGING = True

# ============================================
# TESTING MODE (Dummy Hardware)
# ============================================
USE_DUMMY_CAMERA = False
USE_DUMMY_HARDWARE = False

