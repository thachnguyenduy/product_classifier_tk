import argparse
import os
import statistics
import time
from typing import List, Optional

import cv2

import config
from core.ai import AIEngine
from core.camera import Camera, DummyCamera


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * p
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[f]
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return d0 + d1


def main() -> int:
    parser = argparse.ArgumentParser(description="Live camera NCNN YOLO test (no captures folder).")
    parser.add_argument("--camera-id", type=int, default=getattr(config, "CAMERA_ID", 0))
    parser.add_argument("--every", type=int, default=1, help="Infer every N frames (default 1).")
    parser.add_argument("--print-each", action="store_true", help="Print one line per inference.")
    parser.add_argument("--dummy", action="store_true", help="Force DummyCamera.")
    parser.add_argument("--no-roi", action="store_true", help="Disable ROI crop for this run (temporary).")
    parser.add_argument("--save-dir", default="", help="If set, press 's' to save annotated frames here.")
    args = parser.parse_args()

    if args.no_roi:
        setattr(config, "ENABLE_ROI_CROP", False)

    if args.save_dir:
        os.makedirs(args.save_dir, exist_ok=True)

    print("=" * 70)
    print("[LIVE TEST] Project_Graduation_2")
    print("=" * 70)
    print(f"Model path:            {config.MODEL_PATH}")
    print(f"Confidence threshold:  {config.CONFIDENCE_THRESHOLD}")
    print(f"NMS threshold:         {config.NMS_THRESHOLD}")
    print(f"ROI enabled:           {getattr(config, 'ENABLE_ROI_CROP', False)}")
    print(f"Camera:                id={args.camera_id} ({config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT})")
    print("Keys: q=quit, s=save frame")
    print()

    ai = AIEngine(model_path=config.MODEL_PATH, config=config)

    if getattr(config, "USE_DUMMY_CAMERA", False) or args.dummy:
        cam = DummyCamera(width=config.CAMERA_WIDTH, height=config.CAMERA_HEIGHT)
    else:
        cam = Camera(
            camera_id=args.camera_id,
            width=config.CAMERA_WIDTH,
            height=config.CAMERA_HEIGHT,
            fps=config.CAMERA_FPS,
            exposure=getattr(config, "CAMERA_EXPOSURE", -4),
            auto_exposure=getattr(config, "CAMERA_AUTO_EXPOSURE", False),
        )

    if not cam.start():
        print("[LIVE TEST] Failed to start real camera, falling back to DummyCamera.")
        cam = DummyCamera(width=config.CAMERA_WIDTH, height=config.CAMERA_HEIGHT)
        cam.start()

    times: List[float] = []
    frame_idx = 0
    last_result: Optional[dict] = None

    try:
        while True:
            frame = cam.read_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            frame_idx += 1
            do_infer = (args.every <= 1) or (frame_idx % args.every == 0)

            if do_infer:
                start = time.time()
                last_result = ai.predict(frame)
                ms = (time.time() - start) * 1000.0
                last_result["__ms"] = ms
                times.append(ms)

                if args.print_each:
                    print(
                        f"[LIVE] {frame_idx} | {last_result.get('result')} | "
                        f"{last_result.get('reason')} | {ms:.1f}ms"
                    )

            if last_result and last_result.get("annotated_image") is not None:
                view = last_result["annotated_image"].copy()
            else:
                view = frame.copy()

            if last_result:
                ms = float(last_result.get("__ms", 0.0))
                txt = f"{last_result.get('result')} | {ms:.1f}ms"
                cv2.putText(view, txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            cv2.imshow("LIVE YOLO (q=quit, s=save)", view)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("s") and args.save_dir:
                ts = int(time.time() * 1000)
                out_path = os.path.join(args.save_dir, f"live_{ts}.jpg")
                cv2.imwrite(out_path, view)
                print(f"[LIVE TEST] Saved: {out_path}")

        if times:
            print("\n[LIVE TEST] Timing summary (ms):")
            print(f"  mean:   {statistics.mean(times):.1f}")
            print(f"  median: {statistics.median(times):.1f}")
            print(f"  p95:    {percentile(times, 0.95):.1f}")

        return 0
    finally:
        try:
            cam.stop()
        except Exception:
            pass
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())


