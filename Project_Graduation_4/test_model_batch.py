import argparse
import glob
import os
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2

import config
from core.ai import AIEngine


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch test NCNN YOLO model on a folder of images.")
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

    img_paths = collect_images(args.images)
    if not img_paths:
        print(f"[TEST] No images found under: {args.images}")
        return 2

    if args.limit and args.limit > 0:
        img_paths = img_paths[: args.limit]

    if args.save_annotated:
        os.makedirs(args.save_annotated, exist_ok=True)

    ai = AIEngine(model_path=config.MODEL_PATH, config=config)

    # Warmup (use first image)
    warm_img = cv2.imread(img_paths[0])
    if warm_img is None:
        print("[TEST] Failed to read first image for warmup.")
        return 2
    for _ in range(max(0, args.warmup)):
        _ = ai.predict(warm_img)

    rows: List[Row] = []
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
        has_cap = bool(r.get("has_cap", False))
        has_filled = bool(r.get("has_filled", False))
        has_label = bool(r.get("has_label", False))

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

        rows.append(
            Row(
                path=p,
                expected=expected,
                result=result,
                reason=reason,
                ms=ms,
                has_cap=has_cap,
                has_filled=has_filled,
                has_label=has_label,
            )
        )
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


