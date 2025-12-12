#!/usr/bin/env python3
# ============================================
# TEST NCNN MODEL LOADING ONLY
# ============================================

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  NCNN MODEL LOADING TEST")
print("=" * 60)

# Try to import ncnn
print("\n[1/5] Checking NCNN installation...")
try:
    import ncnn
    print("  ✅ NCNN imported successfully")
    print(f"  NCNN version: {ncnn.__version__ if hasattr(ncnn, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"  ❌ NCNN not found: {e}")
    print("\n  To install NCNN:")
    print("    - On Raspberry Pi: sudo apt-get install python3-ncnn")
    print("    - Or build from source: https://github.com/Tencent/ncnn")
    sys.exit(1)

# Import config
print("\n[2/5] Loading config...")
import config
print(f"  Model path: {config.MODEL_PATH}")
print(f"  Param file: {config.MODEL_PARAM}")
print(f"  Bin file: {config.MODEL_BIN}")

# Check files exist
print("\n[3/5] Checking model files...")
param_path = os.path.join(config.MODEL_PATH, config.MODEL_PARAM)
bin_path = os.path.join(config.MODEL_PATH, config.MODEL_BIN)

if not os.path.exists(param_path):
    print(f"  ❌ Param file not found: {param_path}")
    sys.exit(1)
else:
    size_kb = os.path.getsize(param_path) / 1024
    print(f"  ✅ Param file: {param_path} ({size_kb:.1f} KB)")

if not os.path.exists(bin_path):
    print(f"  ❌ Bin file not found: {bin_path}")
    sys.exit(1)
else:
    size_mb = os.path.getsize(bin_path) / 1024 / 1024
    print(f"  ✅ Bin file: {bin_path} ({size_mb:.1f} MB)")

# Try to load model
print("\n[4/5] Loading NCNN model...")
try:
    net = ncnn.Net()
    
    # Configure
    net.opt.use_vulkan_compute = False  # CPU mode
    net.opt.num_threads = 4
    print("  - Configured: CPU mode, 4 threads")
    
    # Load param
    print(f"  - Loading param...")
    ret_param = net.load_param(param_path)
    if ret_param != 0:
        print(f"  ❌ Failed to load param (code={ret_param})")
        sys.exit(1)
    print(f"  ✅ Param loaded (code={ret_param})")
    
    # Load model
    print(f"  - Loading bin...")
    ret_bin = net.load_model(bin_path)
    if ret_bin != 0:
        print(f"  ❌ Failed to load bin (code={ret_bin})")
        sys.exit(1)
    print(f"  ✅ Bin loaded (code={ret_bin})")
    
    print("\n  ✅ NCNN model loaded successfully!")
    
except Exception as e:
    print(f"  ❌ Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to create extractor
print("\n[5/5] Testing inference...")
try:
    import numpy as np
    
    # Create dummy input (640x640x3)
    print("  - Creating dummy input (640x640x3)...")
    dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # Convert to ncnn.Mat
    mat_in = ncnn.Mat.from_pixels(dummy_img, ncnn.Mat.PixelType.PIXEL_BGR, 640, 640)
    
    # Normalize
    mean_vals = [0, 0, 0]
    norm_vals = [1/255.0, 1/255.0, 1/255.0]
    mat_in.substract_mean_normalize(mean_vals, norm_vals)
    
    print("  - Creating extractor...")
    ex = net.create_extractor()
    # Vulkan is already disabled at network level
    
    print("  - Setting input 'in0'...")
    ret_input = ex.input("in0", mat_in)
    if ret_input != 0:
        print(f"  ❌ Input failed (code={ret_input})")
        sys.exit(1)
    print(f"  ✅ Input set (code={ret_input})")
    
    print("  - Extracting output 'out0'...")
    ret, mat_out = ex.extract("out0")
    if ret != 0:
        print(f"  ❌ Extract failed (code={ret})")
        sys.exit(1)
    print(f"  ✅ Extract successful (code={ret})")
    
    # Convert to numpy
    out_np = np.array(mat_out)
    print(f"  - Output shape: {out_np.shape}")
    
    print("\n  ✅ Inference test PASSED!")
    
except Exception as e:
    print(f"  ❌ Exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("  ✅ ALL TESTS PASSED!")
print("=" * 60)
print("\n✅ NCNN model is working correctly!")
print("✅ You can now run the full system:")
print("   python3 main.py")
print("\n" + "=" * 60)

