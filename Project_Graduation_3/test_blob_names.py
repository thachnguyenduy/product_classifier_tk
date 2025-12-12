#!/usr/bin/env python3
# ============================================
# TEST BLOB NAMES
# Tìm đúng tên input/output blobs của NCNN model
# ============================================

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
print("FIND CORRECT BLOB NAMES")
print("="*60)

# Load model
print("\n[1/3] Loading model...")
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

# Parse param file to find blob names
print("\n[2/3] Parsing param file...")
with open(param_file, 'r') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find Input layer
input_blobs = []
for i, line in enumerate(lines):
    if line.startswith('Input'):
        parts = line.strip().split()
        print(f"\nLine {i+1}: {line.strip()}")
        print(f"  Parts: {parts}")
        if len(parts) >= 6:
            layer_type = parts[0]
            layer_name = parts[1]
            input_count = parts[2]
            output_count = parts[3]
            output_blob = parts[4]
            print(f"  → Layer: {layer_type}")
            print(f"  → Name: {layer_name}")
            print(f"  → Output blob: {output_blob}")
            input_blobs.append(output_blob)

# Find output layers (usually last few lines)
print("\n[3/3] Finding output layers...")
output_blobs = []
for i in range(max(0, len(lines)-10), len(lines)):
    line = lines[i].strip()
    if line and not line.startswith('#'):
        parts = line.split()
        if len(parts) >= 5:
            # Last column is usually output blob
            potential_output = parts[-1]
            if 'out' in potential_output.lower():
                print(f"\nLine {i+1}: {line}")
                print(f"  → Potential output: {potential_output}")
                output_blobs.append(potential_output)

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"Input blobs found: {input_blobs}")
print(f"Output blobs found: {output_blobs}")

# Try to use them
if len(input_blobs) > 0 and len(output_blobs) > 0:
    input_name = input_blobs[0]
    output_name = output_blobs[-1]  # Use last one
    
    print(f"\n→ Trying: {input_name} → {output_name}")
    
    import numpy as np
    
    # Create dummy input
    dummy = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    mat_in = ncnn.Mat.from_pixels(dummy, ncnn.Mat.PixelType.PIXEL_BGR, 640, 640)
    mat_in.substract_mean_normalize([0,0,0], [1/255.0, 1/255.0, 1/255.0])
    
    try:
        ex = net.create_extractor()
        
        print(f"\n  Testing input '{input_name}'...")
        ret_input = ex.input(input_name, mat_in)
        if ret_input == 0:
            print(f"  ✅ Input '{input_name}' OK")
        else:
            print(f"  ❌ Input '{input_name}' failed (code={ret_input})")
        
        print(f"\n  Testing output '{output_name}'...")
        ret_output, mat_out = ex.extract(output_name)
        if ret_output == 0:
            print(f"  ✅ Output '{output_name}' OK")
            out_np = np.array(mat_out)
            print(f"  → Output shape: {out_np.shape}")
        else:
            print(f"  ❌ Output '{output_name}' failed (code={ret_output})")
        
        if ret_input == 0 and ret_output == 0:
            print("\n" + "="*60)
            print("SUCCESS!")
            print("="*60)
            print(f"Use these blob names in config:")
            print(f"  INPUT:  '{input_name}'")
            print(f"  OUTPUT: '{output_name}'")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

print("\n")

