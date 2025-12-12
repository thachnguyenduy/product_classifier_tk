#!/usr/bin/env python3
# ============================================
# TEST DECODE FIX
# Kiểm tra decode function sau khi fix
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
print("TEST DECODE FUNCTION - AFTER FIX")
print("="*60)

# Load model
print("\n[1/4] Loading NCNN model...")
param_file = os.path.join(config.MODEL_PATH_NCNN, config.MODEL_PARAM)
bin_file = os.path.join(config.MODEL_PATH_NCNN, config.MODEL_BIN)

net = ncnn.Net()
net.opt.use_vulkan_compute = False
net.opt.num_threads = 4

ret_param = net.load_param(param_file)
ret_bin = net.load_model(bin_file)

if ret_param != 0 or ret_bin != 0:
    print(f"[ERROR] Failed to load model (param={ret_param}, bin={ret_bin})")
    sys.exit(1)

print("✅ Model loaded")

# Create test image
print("\n[2/4] Creating test image...")
test_img = np.ones((640, 640, 3), dtype=np.uint8) * 128

# Preprocess
mat_in = ncnn.Mat.from_pixels(test_img, ncnn.Mat.PixelType.PIXEL_BGR, 640, 640)
mat_in.substract_mean_normalize([0,0,0], [1/255.0, 1/255.0, 1/255.0])

# Run inference
print("\n[3/4] Running inference...")
ex = net.create_extractor()

print("  - Input blob: 'in0'")
ret_input = ex.input("in0", mat_in)
if ret_input != 0:
    print(f"  ❌ Input failed (code={ret_input})")
    sys.exit(1)
print(f"  ✅ Input OK")

print("  - Output blob: 'out0'")
ret_output, mat_out = ex.extract("out0")
if ret_output != 0:
    print(f"  ❌ Output failed (code={ret_output})")
    sys.exit(1)
print(f"  ✅ Output OK")

# Convert and analyze
out_np = np.array(mat_out)
print(f"\n[4/4] Analyzing output...")
print(f"  Raw shape: {out_np.shape}")

# Handle shape
if len(out_np.shape) == 3:
    out_np = out_np[0]
    print(f"  After squeeze: {out_np.shape}")

if out_np.shape[0] < out_np.shape[1]:
    out_np = out_np.T
    print(f"  After transpose: {out_np.shape}")

print(f"  Final shape: {out_np.shape}")

if len(out_np.shape) == 2:
    num_detections, num_features = out_np.shape
    print(f"\n  Detections: {num_detections}")
    print(f"  Features: {num_features}")
    print(f"  Expected: 12 (4 bbox + 8 classes)")
    
    if num_features == 12:
        print("  ✅ Feature count CORRECT!")
        
        # Analyze scores
        scores = out_np[:, 4:]
        max_scores = np.max(scores, axis=1)
        
        high_conf = np.sum(max_scores > 0.3)
        print(f"\n  High confidence detections (>0.3): {high_conf}")
        
        if high_conf > 0:
            print("  ✅ Model can detect!")
        else:
            print("  ⚠️  No high-conf detections (normal for blank image)")
    else:
        print("  ❌ Feature count WRONG!")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
print("\nIf all OK, run:")
print("  python3 main.py")
print()

