import argparse
import glob
import os
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import cv2

import config
from core.ai import AIEngine
from core.camera import Camera, DummyCamera


@dataclass
class Row:
    path: str
    expected: Optional[str]  # "OK" | "NG" | None
    result: str
    reason: str
    ms: float
    has_cap: bool
    has_filled: bool
    has_label: bool


def infer_expected_from_path(p: str) -> Optional[str]:
    norm = p.replace("\\", "/").lower()
    if "/ok/" in norm:
        return "OK"
    if "/ng/" in norm:
        return "NG"
    return None


def collect_images(images_dir: str) -> List[str]:
    patterns = ["**/*.jpg", "**/*.jpeg", "**/*.png", "**/*.bmp", "**/*.webp"]
    out: List[str] = []
    for pat in patterns:
        out.extend(glob.glob(os.path.join(images_dir, pat), recursive=True))
    out = [p for p in out if os.path.isfile(p)]
    out.sort()
    return out


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


def run_live(ai: AIEngine, args: argparse.Namespace) -> int:
    # Start camera (prefer project Camera so ROI/exposure settings match app)
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
        print("[TEST] Failed to start real camera, falling back to DummyCamera.")
        cam = DummyCamera(width=config.CAMERA_WIDTH, height=config.CAMERA_HEIGHT)
        cam.start()

    print("[TEST] Live mode started. Keys: q=quit, s=save current annotated frame")
    if args.save_annotated:
        os.makedirs(args.save_annotated, exist_ok=True)

    last = None
    last_result: Optional[dict] = None
    times: List[float] = []
    frame_idx = 0

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
                last = last_result["annotated_image"]
            else:
                last = frame

            # Overlay quick stats
            if last_result:
                ms = float(last_result.get("__ms", 0.0))
                txt = f"{last_result.get('result')} | {ms:.1f}ms"
                cv2.putText(last, txt, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            cv2.imshow("LIVE (press q to quit)", last)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("s") and args.save_annotated:
                ts = int(time.time() * 1000)
                out_path = os.path.join(args.save_annotated, f"live_{ts}.jpg")
                cv2.imwrite(out_path, last)
                print(f"[TEST] Saved: {out_path}")

        if times:
            print("\n[LIVE] Timing summary (ms):")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch test NCNN YOLO model on a folder of images.")
    parser.add_argument("--live", action="store_true", help="Run live camera inference instead of folder batch.")
    parser.add_argument("--camera-id", type=int, default=getattr(config, "CAMERA_ID", 0), help="Camera ID for live mode.")
    parser.add_argument("--every", type=int, default=1, help="Infer every N frames in live mode (default 1).")
    parser.add_argument("--print-each", action="store_true", help="Print one line per inference in live mode.")
    parser.add_argument("--dummy", action="store_true", help="Force DummyCamera in live mode.")
    parser.add_argument(
        "--images",
        default="captures",
        help="Folder containing images (supports nested folders). Default: captures",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of images (0 = no limit).")
    parser.add_argument("--warmup", type=int, default=5, help="Warmup iterations before measuring.")
    parser.add_argument("--save-annotated", default="", help="Output folder to save annotated images (optional).")
    parser.add_argument("--no-roi", action="store_true", help="Disable ROI crop for this run (temporary).")
    args = parser.parse_args()

    if args.no_roi:
        setattr(config, "ENABLE_ROI_CROP", False)

    ai = AIEngine(model_path=config.MODEL_PATH, config=config)

    if args.live:
        return run_live(ai, args)

    img_paths = collect_images(args.images)
    if not img_paths:
        print(f"[TEST] No images found under: {args.images}")
        return 2

    if args.limit and args.limit > 0:
        img_paths = img_paths[: args.limit]

    if args.save_annotated:
        os.makedirs(args.save_annotated, exist_ok=True)

    # Warmup (use first image)
    warm_img = cv2.imread(img_paths[0])
    if warm_img is None:
        print("[TEST] Failed to read first image for warmup.")
        return 2
    for _ in range(max(0, args.warmup)):
        _ = ai.predict(warm_img)

    times: List[float] = []

    counts: Dict[str, int] = {
        "total": 0,
        "expected_ok": 0,
        "expected_ng": 0,
        "pred_ok": 0,
        "pred_ng": 0,
        "tp_ok": 0,
        "tp_ng": 0,
        "fp_ok": 0,  # predicted OK but expected NG
        "fp_ng": 0,  # predicted NG but expected OK
        "missing_cap": 0,
        "missing_filled": 0,
        "missing_label": 0,
        "defect": 0,
    }

    t0 = time.time()
    for idx, p in enumerate(img_paths):
        img = cv2.imread(p)
        if img is None:
            continue

        start = time.time()
        r = ai.predict(img)
        ms = (time.time() - start) * 1000.0
        times.append(ms)

        expected = infer_expected_from_path(p)
        if expected == "OK":
            counts["expected_ok"] += 1
        elif expected == "NG":
            counts["expected_ng"] += 1

        result = r.get("result", "UNKNOWN")
        reason = r.get("reason", "")

        if result == "OK":
            counts["pred_ok"] += 1
        elif result == "NG":
            counts["pred_ng"] += 1

        # Simple reason breakdown
        reason_l = (reason or "").lower()
        if reason_l.startswith("missing:"):
            if "cap" in reason_l:
                counts["missing_cap"] += 1
            if "filled" in reason_l:
                counts["missing_filled"] += 1
            if "label" in reason_l:
                counts["missing_label"] += 1
        if reason_l.startswith("defect:"):
            counts["defect"] += 1

        # Confusion (if expected is known)
        if expected in ("OK", "NG") and result in ("OK", "NG"):
            if expected == result == "OK":
                counts["tp_ok"] += 1
            elif expected == result == "NG":
                counts["tp_ng"] += 1
            elif expected == "NG" and result == "OK":
                counts["fp_ok"] += 1
            elif expected == "OK" and result == "NG":
                counts["fp_ng"] += 1

        counts["total"] += 1

        if args.save_annotated:
            out_img = r.get("annotated_image", None)
            if out_img is None:
                out_img = img
            base = os.path.basename(p)
            out_path = os.path.join(args.save_annotated, f"{idx:05d}_{result}_{base}")
            cv2.imwrite(out_path, out_img)

    dt = time.time() - t0
    if not times:
        print("[TEST] No images processed.")
        return 2

    print("\n" + "=" * 70)
    print("[TEST] Batch results")
    print("=" * 70)
    print(f"Images dir:            {args.images}")
    print(f"Images processed:      {counts['total']}")
    print(f"Model path:            {config.MODEL_PATH}")
    print(f"Confidence threshold:  {config.CONFIDENCE_THRESHOLD}")
    print(f"NMS threshold:         {config.NMS_THRESHOLD}")
    print(f"ROI enabled:           {getattr(config, 'ENABLE_ROI_CROP', False)}")
    print(f"Elapsed:               {dt:.2f}s")
    print()

    print("Timing (ms):")
    print(f"  mean:   {statistics.mean(times):.1f}")
    print(f"  median: {statistics.median(times):.1f}")
    print(f"  p95:    {percentile(times, 0.95):.1f}")
    print(f"  min/max:{min(times):.1f}/{max(times):.1f}")
    print()

    print("Predictions:")
    print(f"  OK: {counts['pred_ok']}")
    print(f"  NG: {counts['pred_ng']}")
    print()

    if counts["expected_ok"] + counts["expected_ng"] > 0:
        print("Confusion (based on folder name /ok/ and /ng/):")
        print(f"  expected OK: {counts['expected_ok']}")
        print(f"  expected NG: {counts['expected_ng']}")
        print(f"  OK->OK:      {counts['tp_ok']}")
        print(f"  NG->NG:      {counts['tp_ng']}")
        print(f"  NG->OK:      {counts['fp_ok']}  (false pass)")
        print(f"  OK->NG:      {counts['fp_ng']}  (false reject)")
        print()

    print("Reasons breakdown:")
    print(f"  Missing cap:    {counts['missing_cap']}")
    print(f"  Missing filled: {counts['missing_filled']}")
    print(f"  Missing label:  {counts['missing_label']}")
    print(f"  Defect:*        {counts['defect']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


