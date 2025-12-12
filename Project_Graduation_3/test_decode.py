#!/usr/bin/env python3
# ============================================
# TEST DECODE FUNCTION
# Kiểm tra hàm decode NCNN có hoạt động đúng không
# ============================================

import cv2
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import ncnn
except ImportError:
    print("[ERROR] NCNN not installed!")
    sys.exit(1)

import config

print("="*60)
print("TEST DECODE FUNCTION - NCNN MODEL")
print("="*60)

# Load model
print("\n[1/3] Loading NCNN model...")
param_file = os.path.join(config.MODEL_PATH_NCNN, config.MODEL_PARAM)
bin_file = os.path.join(config.MODEL_PATH_NCNN, config.MODEL_BIN)

net = ncnn.Net()
net.opt.use_vulkan_compute = False
net.opt.num_threads = 4

ret_param = net.load_param(param_file)
ret_bin = net.load_model(bin_file)

if ret_param != 0 or ret_bin != 0:
    print("[ERROR] Failed to load model")
    sys.exit(1)

print("✅ Model loaded")

# Create test image
print("\n[2/3] Creating test image (solid color)...")
test_img = np.ones((640, 640, 3), dtype=np.uint8) * 128  # Gray image

# Preprocess
mat_in = ncnn.Mat.from_pixels(test_img, ncnn.Mat.PixelType.PIXEL_BGR, 640, 640)
mean_vals = [0, 0, 0]
norm_vals = [1/255.0, 1/255.0, 1/255.0]
mat_in.substract_mean_normalize(mean_vals, norm_vals)

# Run inference
print("\n[3/3] Running inference...")
ex = net.create_extractor()
ex.input("in0", mat_in)
ret, mat_out = ex.extract("out0")

if ret != 0:
    print("[ERROR] Inference failed")
    sys.exit(1)

# Convert output
out_np = np.array(mat_out)

print("\n" + "="*60)
print("OUTPUT ANALYSIS")
print("="*60)
print(f"Raw shape: {out_np.shape}")
print(f"Data type: {out_np.dtype}")

# Handle shape
if len(out_np.shape) == 3:
    out_np = out_np.squeeze(0)
    print(f"After squeeze: {out_np.shape}")

if len(out_np.shape) == 2:
    if out_np.shape[0] == 12 and out_np.shape[1] > 1000:
        out_np = out_np.T
        print(f"After transpose: {out_np.shape}")

print(f"Final shape: {out_np.shape}")

if len(out_np.shape) == 2:
    num_anchors, num_features = out_np.shape
    print(f"\nAnchors: {num_anchors}")
    print(f"Features: {num_features}")
    print(f"Expected features: {4 + len(config.CLASS_NAMES)} (4 bbox + {len(config.CLASS_NAMES)} classes)")
    
    if num_features == 4 + len(config.CLASS_NAMES):
        print("✅ Feature count CORRECT!")
    else:
        print("❌ Feature count MISMATCH!")
    
    # Analyze bbox
    bbox = out_np[:, 0:4]
    print(f"\nBbox coords range:")
    print(f"  X center: [{np.min(bbox[:, 0]):.1f}, {np.max(bbox[:, 0]):.1f}]")
    print(f"  Y center: [{np.min(bbox[:, 1]):.1f}, {np.max(bbox[:, 1]):.1f}]")
    print(f"  Width:    [{np.min(bbox[:, 2]):.1f}, {np.max(bbox[:, 2]):.1f}]")
    print(f"  Height:   [{np.min(bbox[:, 3]):.1f}, {np.max(bbox[:, 3]):.1f}]")
    
    # Analyze scores
    scores = out_np[:, 4:]
    print(f"\nClass scores range:")
    print(f"  Min: {np.min(scores):.3f}")
    print(f"  Max: {np.max(scores):.3f}")
    print(f"  Mean: {np.mean(scores):.3f}")
    
    if np.max(scores) <= 1.0 and np.min(scores) >= 0.0:
        print("  ✅ Scores are normalized (sigmoid applied)")
    else:
        print("  ⚠️  Scores may need sigmoid")
    
    # Count high-confidence detections
    max_scores = np.max(scores, axis=1)
    high_conf = np.sum(max_scores > config.CONFIDENCE_THRESHOLD)
    print(f"\nDetections > {config.CONFIDENCE_THRESHOLD}: {high_conf}")
    
    if high_conf > 0:
        print("✅ Model is detecting objects!")
        top_indices = np.argsort(max_scores)[-5:][::-1]
        print("\nTop 5 detections:")
        for idx in top_indices:
            class_id = np.argmax(scores[idx])
            conf = max_scores[idx]
            print(f"  - {config.CLASS_NAMES[class_id]}: {conf:.3f}")
    else:
        print("⚠️  No detections (normal for blank image)")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nIf output looks good, try with real camera:")
print("  python3 main.py")
print()

