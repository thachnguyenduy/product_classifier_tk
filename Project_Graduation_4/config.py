"""
Configuration file for Coca-Cola Sorting System (CONTINUOUS MODE)
Adjust these parameters to tune system performance
"""

# ============================================================================
# AI MODEL CONFIGURATION
# ============================================================================

# Model path (NCNN format)
MODEL_PATH = "model/best_ncnn_model"  # Folder containing .param and .bin files

# Detection confidence threshold (0.0 - 1.0)
# Lower = more detections (may include false positives)
# Higher = fewer detections (may miss some objects)
CONFIDENCE_THRESHOLD = 0.5

# NMS (Non-Maximum Suppression) threshold (0.0 - 1.0)
# Lower = remove more overlapping boxes (strict)
# Higher = keep more overlapping boxes (loose)
NMS_THRESHOLD = 0.45

# Class names (must match model training)
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

# Defect classes (indices)
DEFECT_CLASSES = [0, 1, 2, 3]

# Required component classes (indices)
REQUIRED_COMPONENTS = {
    'cap': 4,
    'filled': 6,
    'label': 7
}

# ============================================================================
# SORTING LOGIC
# ============================================================================

# Require specific components for OK classification
REQUIRE_CAP = True
REQUIRE_FILLED = True
REQUIRE_LABEL = True

# ============================================================================
# CAMERA CONFIGURATION
# ============================================================================

CAMERA_ID = 0  # 0 for /dev/video0, 1 for /dev/video1, etc.
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Manual exposure setting (important for moving conveyor)
# Negative values = shorter exposure = less motion blur
# Range typically -13 to 0 (camera dependent)
CAMERA_EXPOSURE = -4  # Adjust based on lighting conditions

# Auto-exposure (set to False for manual exposure)
CAMERA_AUTO_EXPOSURE = False

# ============================================================================
# CAMERA ROI (CROP) - reduce 4 sides (left/right/top/bottom)
# ============================================================================
# Crop pixels from each edge, then resize back to CAMERA_WIDTH x CAMERA_HEIGHT.
# This effectively reduces the visible area without changing output resolution.
ENABLE_ROI_CROP = True
ROI_CROP_LEFT_PX = 100
ROI_CROP_RIGHT_PX = 100
ROI_CROP_TOP_PX = 0
ROI_CROP_BOTTOM_PX = 0

# ============================================================================
# HARDWARE CONFIGURATION
# ============================================================================

# Arduino serial port
# Linux: '/dev/ttyUSB0' or '/dev/ttyACM0'
# Windows: 'COM3', 'COM4', etc.
ARDUINO_PORT = '/dev/ttyUSB0'
ARDUINO_BAUDRATE = 9600
ARDUINO_TIMEOUT = 0.1  # Short timeout for fast response

# Travel time from sensor to servo (milliseconds)
# CRITICAL: Must match Arduino's TRAVEL_TIME setting
TRAVEL_TIME_MS = 4500

# ============================================================================
# CAPTURE CONFIGURATION
# ============================================================================

# Number of frames to capture per bottle (for voting/averaging)
NUM_CAPTURE_FRAMES = 1  # In continuous mode, we capture quickly (no time for multiple frames)

# Frame delay between captures (seconds)
FRAME_DELAY = 0.05  # 50ms between frames if capturing multiple

# ============================================================================
# DUMMY MODE (For testing without hardware)
# ============================================================================

USE_DUMMY_CAMERA = False  # True = use generated test images
USE_DUMMY_HARDWARE = False  # True = simulate Arduino communication

# ============================================================================
# DEBUG & LOGGING
# ============================================================================

DEBUG_MODE = True  # Print detailed debug information
SAVE_DEBUG_IMAGES = True  # Save annotated images to captures/debug/

# Log file path
LOG_FILE = "system.log"

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# UI update rate (milliseconds)
UI_UPDATE_INTERVAL = 33  # ~30 FPS

# Display settings
DISPLAY_WIDTH = 640
DISPLAY_HEIGHT = 480

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_PATH = "database/product.db"

# ============================================================================
# PERFORMANCE TUNING
# ============================================================================

# Maximum processing time warning threshold (seconds)
MAX_PROCESSING_TIME = 1.0  # Warn if AI takes longer than this

# Serial response timeout (seconds)
SERIAL_RESPONSE_TIMEOUT = 0.05  # How long to wait before sending decision

# ============================================================================
# CALIBRATION
# ============================================================================

# Calibration mode (prints timing information)
CALIBRATION_MODE = False
