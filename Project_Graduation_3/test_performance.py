#!/usr/bin/env python3
# ============================================
# PERFORMANCE TEST SCRIPT
# Test NCNN model speed on Raspberry Pi 5
# ============================================

import cv2
import time
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import ncnn
    NCNN_AVAILABLE = True
except ImportError:
    print("[ERROR] NCNN not installed!")
    print("Install: pip3 install ncnn")
    sys.exit(1)

import config


def test_ncnn_speed():
    """Test NCNN inference speed"""
    print("="*60)
    print("NCNN PERFORMANCE TEST")
    print("="*60)
    
    # Load model
    print("\n[1/4] Loading NCNN model...")
    param_file = os.path.join(config.MODEL_PATH_NCNN, config.MODEL_PARAM)
    bin_file = os.path.join(config.MODEL_PATH_NCNN, config.MODEL_BIN)
    
    if not os.path.exists(param_file):
        print(f"[ERROR] Param file not found: {param_file}")
        return
    
    if not os.path.exists(bin_file):
        print(f"[ERROR] Bin file not found: {bin_file}")
        return
    
    net = ncnn.Net()
    net.opt.use_vulkan_compute = False
    net.opt.num_threads = 4
    
    ret_param = net.load_param(param_file)
    ret_bin = net.load_model(bin_file)
    
    if ret_param != 0 or ret_bin != 0:
        print(f"[ERROR] Failed to load model")
        return
    
    print("✅ Model loaded successfully")
    
    # Create dummy input
    print("\n[2/4] Creating test input...")
    input_size = config.INPUT_SIZE
    dummy_frame = np.random.randint(0, 255, (input_size, input_size, 3), dtype=np.uint8)
    
    # Preprocess
    mat_in = ncnn.Mat.from_pixels(
        dummy_frame,
        ncnn.Mat.PixelType.PIXEL_BGR,
        input_size,
        input_size
    )
    mean_vals = [0, 0, 0]
    norm_vals = [1.0/255.0, 1.0/255.0, 1.0/255.0]
    mat_in.substract_mean_normalize(mean_vals, norm_vals)
    
    print("✅ Test input created")
    
    # Warm up (first inference is always slower)
    print("\n[3/4] Warming up...")
    ex = net.create_extractor()
    ex.input("in0", mat_in)
    _, _ = ex.extract("out0")
    print("✅ Warm up complete")
    
    # Benchmark
    print("\n[4/4] Running benchmark (100 iterations)...")
    num_iterations = 100
    times = []
    
    for i in range(num_iterations):
        start = time.time()
        
        ex = net.create_extractor()
        ex.input("in0", mat_in)
        _, mat_out = ex.extract("out0")
        
        elapsed = (time.time() - start) * 1000  # ms
        times.append(elapsed)
        
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{num_iterations}")
    
    # Results
    times = np.array(times)
    avg_time = np.mean(times)
    min_time = np.min(times)
    max_time = np.max(times)
    std_time = np.std(times)
    fps = 1000.0 / avg_time
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"Average inference time: {avg_time:.2f} ms")
    print(f"Min inference time:     {min_time:.2f} ms")
    print(f"Max inference time:     {max_time:.2f} ms")
    print(f"Std deviation:          {std_time:.2f} ms")
    print(f"Estimated FPS:          {fps:.1f}")
    print("="*60)
    
    # Performance rating
    print("\nPERFORMANCE RATING:")
    if avg_time < 40:
        print("🏆 EXCELLENT (>25 FPS) - Perfect for real-time!")
    elif avg_time < 60:
        print("✅ GOOD (16-25 FPS) - Smooth operation")
    elif avg_time < 100:
        print("⚠️  ACCEPTABLE (10-16 FPS) - May need optimization")
    else:
        print("❌ SLOW (<10 FPS) - Need optimization!")
        print("\nOptimization suggestions:")
        print("  1. Reduce resolution in config.py")
        print("  2. Enable SKIP_FRAMES in config.py")
        print("  3. Increase CONFIDENCE_THRESHOLD")
        print("  4. Ensure DEBUG_MODE = False")
        print("  5. Close other applications")
    
    print("\n" + "="*60)


def test_camera_fps():
    """Test camera capture FPS"""
    print("\n" + "="*60)
    print("CAMERA FPS TEST")
    print("="*60)
    
    print("\n[1/3] Opening camera...")
    cap = cv2.VideoCapture(config.CAMERA_ID, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print("[WARNING] V4L2 failed, trying default")
        cap = cv2.VideoCapture(config.CAMERA_ID)
    
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
    print("✅ Camera opened")
    
    # Warm up
    print("\n[2/3] Warming up camera...")
    for _ in range(30):
        cap.read()
    
    # Test
    print("\n[3/3] Testing FPS (5 seconds)...")
    frame_count = 0
    start_time = time.time()
    
    while time.time() - start_time < 5.0:
        ret, frame = cap.read()
        if ret:
            frame_count += 1
    
    elapsed = time.time() - start_time
    fps = frame_count / elapsed
    
    cap.release()
    
    print("\n" + "="*60)
    print("CAMERA RESULTS")
    print("="*60)
    print(f"Frames captured: {frame_count}")
    print(f"Time elapsed:    {elapsed:.2f} s")
    print(f"Camera FPS:      {fps:.1f}")
    print("="*60)
    
    if fps >= 25:
        print("\n✅ Camera FPS is GOOD")
    elif fps >= 15:
        print("\n⚠️  Camera FPS is ACCEPTABLE")
    else:
        print("\n❌ Camera FPS is LOW")
        print("\nTry:")
        print("  - Use MJPEG format (already configured)")
        print("  - Reduce resolution")
        print("  - Check camera quality")
    
    print()


def main():
    """Main test"""
    print("\n" + "="*60)
    print("RASPBERRY PI 5 PERFORMANCE TEST")
    print("Coca-Cola Sorting System v2.0")
    print("="*60)
    
    # System info
    print("\nSYSTEM INFO:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  OpenCV: {cv2.__version__}")
    print(f"  NCNN: Available")
    print(f"  Config: {config.MODEL_PATH_NCNN}")
    
    # Run tests
    try:
        test_ncnn_speed()
    except Exception as e:
        print(f"\n[ERROR] NCNN test failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_camera_fps()
    except Exception as e:
        print(f"\n[ERROR] Camera test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nIf performance is good, you're ready to run:")
    print("  python3 main.py")
    print("\n")


if __name__ == "__main__":
    main()

