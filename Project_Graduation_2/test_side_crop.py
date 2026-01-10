import time

import cv2

import config


def apply_roi_crop(frame):
    """Apply the same ROI-crop logic as Camera.read_frame(), but for raw frames."""
    if frame is None:
        return None

    if not getattr(config, "ENABLE_ROI_CROP", False):
        return cv2.resize(frame, (config.CAMERA_WIDTH, config.CAMERA_HEIGHT))

    left = max(0, int(getattr(config, "ROI_CROP_LEFT_PX", 0) or 0))
    right = max(0, int(getattr(config, "ROI_CROP_RIGHT_PX", 0) or 0))
    top = max(0, int(getattr(config, "ROI_CROP_TOP_PX", 0) or 0))
    bottom = max(0, int(getattr(config, "ROI_CROP_BOTTOM_PX", 0) or 0))

    h, w = frame.shape[:2]
    if (left + right) >= (w - 1) or (top + bottom) >= (h - 1):
        return cv2.resize(frame, (config.CAMERA_WIDTH, config.CAMERA_HEIGHT))

    cropped = frame[top:h - bottom, left:w - right]
    if cropped is None or cropped.shape[0] <= 0 or cropped.shape[1] <= 0:
        return cv2.resize(frame, (config.CAMERA_WIDTH, config.CAMERA_HEIGHT))

    return cv2.resize(cropped, (config.CAMERA_WIDTH, config.CAMERA_HEIGHT))


def main():
    cap = cv2.VideoCapture(config.CAMERA_ID)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera id={config.CAMERA_ID}")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)

    print(
        "[TEST] ROI crop:",
        f"ENABLE_ROI_CROP={getattr(config, 'ENABLE_ROI_CROP', False)}",
        f"L={getattr(config, 'ROI_CROP_LEFT_PX', 0)}",
        f"R={getattr(config, 'ROI_CROP_RIGHT_PX', 0)}",
        f"T={getattr(config, 'ROI_CROP_TOP_PX', 0)}",
        f"B={getattr(config, 'ROI_CROP_BOTTOM_PX', 0)}",
    )
    print("[TEST] Press 'q' to quit.")

    last = time.time()
    frames = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue

        frames += 1
        now = time.time()
        if now - last >= 1.0:
            print(f"[TEST] FPS: {frames / (now - last):.1f}")
            frames = 0
            last = now

        cropped = apply_roi_crop(frame)

        # Visualize ROI on ORIGINAL (yellow rectangle = kept center)
        h, w = frame.shape[:2]
        left = max(0, int(getattr(config, "ROI_CROP_LEFT_PX", 0) or 0))
        right = max(0, int(getattr(config, "ROI_CROP_RIGHT_PX", 0) or 0))
        top = max(0, int(getattr(config, "ROI_CROP_TOP_PX", 0) or 0))
        bottom = max(0, int(getattr(config, "ROI_CROP_BOTTOM_PX", 0) or 0))

        x1 = min(w - 1, left)
        y1 = min(h - 1, top)
        x2 = max(0, (w - 1) - right)
        y2 = max(0, (h - 1) - bottom)
        vis = frame.copy()
        cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 255), 2)

        cv2.imshow("ORIGINAL (yellow rect = kept ROI)", vis)
        cv2.imshow("CROPPED+RESIZED (ROI applied)", cropped)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()


