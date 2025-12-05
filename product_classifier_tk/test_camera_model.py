import cv2

# camera_index = 0 / 1 tuỳ máy
cap = cv2.VideoCapture(0)

# set độ phân giải (tuỳ camera hỗ trợ)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Không đọc được frame từ camera")
        break

    # Lấy kích thước khung hình
    h, w = frame.shape[:2]

    # ====== ĐỊNH NGHĨA VÙNG CẦN SOI (ROI) ======
    roi_w, roi_h = 400, 300  # kích thước vùng cần soi (mày chỉnh theo ý)
    x1 = w//2 - roi_w//2     # bắt đầu từ giữa
    y1 = h//2 - roi_h//2
    x2 = x1 + roi_w
    y2 = y1 + roi_h

    # Cắt vùng ROI
    roi = frame[y1:y2, x1:x2]

    # ====== ĐƯA ROI VÀO MODEL NHẬN DIỆN CỦA MÀY ======
    # ví dụ:
    # results = model.detect(roi)
    # rồi vẽ bounding box lên roi nếu cần

    # Vẽ khung ROI lên full frame cho dễ thấy
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Hiển thị
    cv2.imshow("Full Frame", frame)  # full camera + khung xanh
    cv2.imshow("ROI (vung dang detect)", roi)  # chỉ vùng đang xử lý

    # Nhấn q để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
