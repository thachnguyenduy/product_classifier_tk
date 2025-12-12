# ============================================
# COCA-COLA SORTING SYSTEM - CONFIGURATION
# ============================================
"""
Configuration for Coca-Cola Bottle Sorting System

IMPORTANT:
- Conveyor direction: RIGHT → LEFT
- Line crossing: bottle moves from right to left
- Classification finalizes at line crossing
- Model: YOLO best.pt (NCNN will replace later)
"""

# ============================================
# AI MODEL SETTINGS
# ============================================
# Current model: YOLO (for testing and integration)
# Future: NCNN (will replace without changing logic)
MODEL_PATH_YOLO = "model/best.pt"

# Detection Thresholds
CONFIDENCE_THRESHOLD = 0.25  # Confidence threshold for detection
NMS_THRESHOLD = 0.45         # Non-max suppression threshold

# Class Names (STRICT ORDER - DO NOT CHANGE)
# These are the EXACT class names output by the AI model
CLASS_NAMES = [
    'Cap-Defect',      # 0 - Defect
    'Filling-Defect',  # 1 - Defect
    'Label-Defect',    # 2 - Defect
    'Wrong-Product',   # 3 - Defect
    'cap',             # 4 - Good component
    'coca',            # 5 - Identity (NOT used for OK/NG classification)
    'filled',          # 6 - Good component
    'label'            # 7 - Good component
]

# ============================================
# CLASSIFICATION LOGIC (CRITICAL)
# ============================================
"""
Classification Rules (STRICT):

1. DEFECT CLASSES (indices 0-3):
   - Cap-Defect
   - Filling-Defect
   - Label-Defect
   - Wrong-Product
   
   → If ANY defect detected → Result = NG

2. GOOD CLASSES (indices 4, 6, 7):
   - cap
   - filled
   - label
   
   → If ALL three present AND NO defects → Result = OK
   → If ANY missing → Result = NG

3. IDENTITY CLASS (index 5):
   - coca
   
   → Used ONLY to confirm product identity
   → MUST NOT be used alone for OK/NG classification

4. IMPORTANT:
   - DO NOT use confidence score for classification
   - Classification based ONLY on detected labels
   - Classification finalizes ONLY when bottle crosses line
"""

DEFECT_CLASS_IDS = [0, 1, 2, 3]
GOOD_CLASS_IDS = [4, 6, 7]
IDENTITY_CLASS_ID = 5

# ============================================
# LINE CROSSING (SOFTWARE SENSOR)
# ============================================
"""
Virtual Line Detection:

- Virtual vertical line at x = VIRTUAL_LINE_X
- Bottles move from RIGHT → LEFT
- Crossing condition:
  - Previous x > VIRTUAL_LINE_X
  - Current x <= VIRTUAL_LINE_X
  
- When crossing:
  1. Finalize classification (OK / NG)
  2. Lock result (no further changes)
  3. Send to Arduino: 'O' = OK, 'N' = NG
"""

VIRTUAL_LINE_X = 320  # X coordinate of virtual line (center of 640px frame)
CROSSING_TOLERANCE = 10  # Tolerance in pixels

# ============================================
# CAMERA SETTINGS
# ============================================
CAMERA_ID = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Exposure settings (reduce motion blur)
CAMERA_AUTO_EXPOSURE = False
CAMERA_EXPOSURE = -6

# ============================================
# ARDUINO COMMUNICATION
# ============================================
"""
Serial Protocol:

Raspberry Pi → Arduino:
- 'O' = OK product (allow to pass)
- 'N' = NG product (block with servo)
- 'S' = Start conveyor
- 'P' = Pause/Stop conveyor

Arduino → Raspberry Pi:
- 'T' = IR sensor triggered (bottle detected)
"""

ARDUINO_PORT = '/dev/ttyUSB0'  # Change as needed
# Common: /dev/ttyACM0, /dev/ttyUSB0, /dev/ttyUSB1
ARDUINO_BAUDRATE = 9600
ARDUINO_TIMEOUT = 1.0

# Serial Commands
CMD_OK = 'O'       # OK product
CMD_NG = 'N'       # NG product
CMD_START = 'S'    # Start conveyor
CMD_STOP = 'P'     # Stop conveyor
CMD_TRIGGER = 'T'  # IR trigger (from Arduino)

# ============================================
# HARDWARE PINS (Arduino)
# ============================================
"""
Arduino Pin Configuration:

Digital Pins:
- Pin 2: IR Sensor (INPUT_PULLUP)
- Pin 4: Relay (OUTPUT) - Conveyor control
- Pin 9: Servo (OUTPUT) - Bottle blocking

Relay Logic:
- LOW = Relay ON = Conveyor Running
- HIGH = Relay OFF = Conveyor Stopped
"""

PIN_IR_SENSOR = 2
PIN_RELAY = 4
PIN_SERVO = 9

# Servo positions
SERVO_IDLE = 0     # Allow bottle to pass
SERVO_BLOCK = 100  # Block NG bottle

# ============================================
# UI SETTINGS (TKINTER)
# ============================================
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800

# Virtual Line Visualization
LINE_COLOR = (0, 255, 255)  # Cyan
LINE_THICKNESS = 3

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
# SYSTEM SETTINGS
# ============================================
# Detection cooldown (prevent multiple detections of same bottle)
DETECTION_COOLDOWN = 1.0  # seconds

# Object tracking
MAX_TRACKING_DISTANCE = 100  # pixels
OBJECT_TIMEOUT = 3.0  # seconds

# ============================================
# DEBUG SETTINGS
# ============================================
DEBUG_MODE = True
VERBOSE_LOGGING = True

# ============================================
# TESTING MODE
# ============================================
"""
Dummy Mode for Testing:

- USE_DUMMY_CAMERA: Test UI without physical camera
- USE_DUMMY_HARDWARE: Test without Arduino

For PRODUCTION: Set both to False
"""

USE_DUMMY_CAMERA = False
USE_DUMMY_HARDWARE = False

# ============================================
# SYSTEM INFORMATION
# ============================================
SYSTEM_NAME = "Coca-Cola Bottle Sorting System"
VERSION = "1.0.0"
MODE = "Line Crossing with YOLO"

print(f"[Config] {SYSTEM_NAME} v{VERSION}")
print(f"[Config] Mode: {MODE}")
print(f"[Config] Model: {MODEL_PATH_YOLO}")
print(f"[Config] Classes: {len(CLASS_NAMES)}")
print(f"[Config] Virtual Line: x={VIRTUAL_LINE_X}")
print(f"[Config] Conveyor Direction: RIGHT → LEFT")
