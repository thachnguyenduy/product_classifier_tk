import cv2
import time
import serial
import threading
from ultralytics import YOLO
from collections import Counter

# =============================================================================
# --- PHẦN 1: CẤU HÌNH NGƯỜI DÙNG (USER CONFIGURATION) ---
# Hãy chỉnh sửa các thông số dưới đây cho phù hợp với phần cứng thực tế
# =============================================================================

# --- A. CẤU HÌNH KẾT NỐI (CONNECTION) ---
SERIAL_PORT = '/dev/ttyACM0'    # Cổng USB kết nối Arduino (check lệnh ls /dev/tty*)
BAUD_RATE   = 115200            # Tốc độ truyền (phải khớp với code Arduino)

# --- B. CẤU HÌNH CAMERA (CAMERA SETTINGS) ---
CAM_WIDTH    = 640              # Chiều rộng khung hình
CAM_HEIGHT   = 480              # Chiều cao khung hình
CAM_EXPOSURE = 100              # Độ phơi sáng (Thấp = tối nhưng bắt chuyển động tốt, Cao = sáng nhưng nhòe)
                                # Lưu ý: Bạn cần chỉnh tay số này sao cho ảnh không bị vệt mờ

# --- C. CẤU HÌNH THỜI GIAN & VẬT LÝ (TIMING & PHYSICS) - QUAN TRỌNG! ---
# 1. Độ trễ từ lúc cảm biến thấy chai -> Đến lúc Camera chụp
#    - Tăng số này nếu cảm biến đặt quá xa camera.
#    - Để 0.0 nếu cảm biến đặt ngay sát mép khung hình camera.
DELAY_SENSOR_TO_CAPTURE = 0.05  # (Giây)

# 2. Độ trễ từ lúc Camera chụp xong -> Đến lúc Servo gạt
#    - Đây là biến quan trọng nhất để gạt trúng chai.
#    - Công thức ước tính: Khoảng cách (m) / Tốc độ băng chuyền (m/s)
DELAY_CAMERA_TO_SERVO   = 1.5   # (Giây)

# 3. Thời gian "nghỉ" của cảm biến (Cooldown)
#    - Sau khi phát hiện 1 chai, hệ thống sẽ phớt lờ cảm biến trong khoảng thời gian này
#    - Mục đích: Tránh việc 1 chai dài bị đếm thành 2-3 lần.
SENSOR_COOLDOWN         = 0.8   # (Giây)

# --- D. CẤU HÌNH TRÍ TUỆ NHÂN TẠO (AI PARAMETERS) ---
MODEL_PATH        = 'E:\ĐỒ ÁN TỐT NGHIỆP CUSOR\product_classifier_tk\model\my_model.pt' # Đường dẫn model (khuyên dùng NCNN hoặc TFLite trên Pi)
CONF_THRESHOLD    = 0.6     # Độ tin cậy tối thiểu (0.6 = 60%)
BURST_FRAME_COUNT = 5       # Số lượng ảnh chụp liên tiếp để bỏ phiếu
VOTE_THRESHOLD    = 3       # Số phiếu tối thiểu để kết luận là LỖI (3/5)

# =============================================================================
# --- PHẦN 2: LOGIC HỆ THỐNG (SYSTEM LOGIC) ---
# Không cần sửa phần dưới này trừ khi muốn thay đổi thuật toán
# =============================================================================

# Kết nối Arduino
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2) # Chờ Arduino reset
    print(f"[SYSTEM] Đã kết nối Arduino tại {SERIAL_PORT}")
except Exception as e:
    print(f"[ERROR] Không kết nối được Arduino: {e}")
    exit()

# Load Model
print(f"[SYSTEM] Đang tải model {MODEL_PATH}...")
model = YOLO(MODEL_PATH)

# Setup Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
# Cố gắng set Exposure thủ công (có thể không hoạt động trên một số webcam rẻ tiền)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # 1 = Manual
cap.set(cv2.CAP_PROP_EXPOSURE, CAM_EXPOSURE)

def send_reject_command():
    """Gửi lệnh gạt sau thời gian trễ đã cài đặt"""
    # Chờ chai đi từ Camera đến Servo
    time.sleep(DELAY_CAMERA_TO_SERVO)
    
    # Gửi lệnh
    arduino.write(b"REJECT\n")
    print(f"[ACTION] >>> Đã gửi lệnh GẠT (Delay: {DELAY_CAMERA_TO_SERVO}s)")

def process_burst_images(frames):
    """Xử lý bỏ phiếu 5 hình"""
    results_list = []
    for img in frames:
        results = model(img, verbose=False, conf=CONF_THRESHOLD)
        error_name = "normal"
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls]
                if label in ['no_cap', 'low_level', 'no_label', 'not_coke']:
                    error_name = label
                    break 
        results_list.append(error_name)

    # Đếm phiếu
    counts = Counter(results_list)
    final_verdict, qty = counts.most_common(1)[0]
    
    print(f"[AI] Kết quả Burst: {results_list} -> Chốt: {final_verdict} ({qty}/{BURST_FRAME_COUNT})")
    
    # Logic bỏ phiếu
    if final_verdict != "normal" and qty >= VOTE_THRESHOLD:
        return True, final_verdict
    return False, "normal"

# Vòng lặp chính
try:
    print("[SYSTEM] Hệ thống sẵn sàng! Băng chuyền bắt đầu chạy...")
    arduino.write(b"START_CONVEYOR\n")
    
    last_trigger_time = 0

    while True:
        ret, frame = cap.read()
        if not ret: 
            print("[ERROR] Mất tín hiệu Camera"); break

        # Kiểm tra dữ liệu từ Arduino (Cảm biến)
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            
            # Chỉ xử lý nếu cảm biến kích hoạt VÀ đã hết thời gian Cooldown
            current_time = time.time()
            if line == "DETECTED" and (current_time - last_trigger_time > SENSOR_COOLDOWN):
                last_trigger_time = current_time
                print(f"\n[SENSOR] Phát hiện chai! (Chờ {DELAY_SENSOR_TO_CAPTURE}s để chụp)")

                # Chờ chai vào giữa khung hình (nếu cần)
                if DELAY_SENSOR_TO_CAPTURE > 0:
                    time.sleep(DELAY_SENSOR_TO_CAPTURE)

                # Chụp Burst (Chụp cực nhanh)
                captured_frames = []
                for _ in range(BURST_FRAME_COUNT):
                    r, img = cap.read()
                    if r: captured_frames.append(img)
                
                # Xử lý AI
                if len(captured_frames) == BURST_FRAME_COUNT:
                    is_defect, error_type = process_burst_images(captured_frames)
                    
                    if is_defect:
                        print(f"[DECISION] PHÁT HIỆN LỖI: {error_type} -> Lên lịch gạt.")
                        # Tạo luồng đếm giờ gạt
                        t = threading.Thread(target=send_reject_command)
                        t.start()
                    else:
                        print("[DECISION] Chai Đạt chuẩn.")

        # Hiển thị
        cv2.imshow("Monitor", frame)
        if cv2.waitKey(1) == ord('q'):
            break

except KeyboardInterrupt:
    print("[SYSTEM] Đang dừng hệ thống...")
finally:
    arduino.write(b"STOP_CONVEYOR\n")
    cap.release()
    cv2.destroyAllWindows()