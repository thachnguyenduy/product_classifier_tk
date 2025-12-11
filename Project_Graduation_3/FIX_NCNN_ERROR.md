# 🔧 Fix NCNN Loading Error

## 🎯 Vấn Đề

Khi chạy `python3 main.py`, bạn thấy:
```
[0 v3D 7.1.7.0] queueC=0[1] queueT=0[1]
[1 llvmpipe (LLVM 19.1.7, 128 bits)] ...
```

Đây là NCNN đang detect GPU/Vulkan devices nhưng sau đó có thể gặp lỗi.

---

## ✅ Các Fix Đã Áp Dụng

### **1. Force CPU Mode (Tắt Vulkan)**

**Lý do:** Vulkan có thể gây lỗi trên một số hệ thống.

**Code đã fix:**
```python
# core/ai.py - _load_model()
self.net.opt.use_vulkan_compute = False  # CPU mode
self.net.opt.num_threads = 4

# core/ai.py - _run_inference()
ex.set_vulkan_compute(False)  # Force CPU
```

### **2. Thêm Debug Logs Chi Tiết**

Bây giờ sẽ thấy:
```
[AI] Loading model from: model/best_ncnn_model
[AI] Param: model.ncnn.param
[AI] Bin: model.ncnn.bin
[AI] Files found:
  - model/best_ncnn_model/model.ncnn.param (16.3 KB)
  - model/best_ncnn_model/model.ncnn.bin (42.5 MB)
[AI] NCNN configured (CPU mode, 4 threads)
[AI] Loading param file...
[AI] Loading bin file...
[AI] ✅ NCNN model loaded successfully!
```

### **3. Kiểm Tra Return Codes**

```python
ret_input = ex.input("in0", mat_in)
if ret_input != 0:
    print(f"[ERROR] Input failed (code={ret_input})")
    return []
```

---

## 🧪 Test Steps

### **Step 1: Test NCNN Installation**

```bash
cd ~/Project_Graduation_3

python3 test_ncnn_only.py
```

**Nếu thành công, sẽ thấy:**
```
============================================================
  NCNN MODEL LOADING TEST
============================================================

[1/5] Checking NCNN installation...
  ✅ NCNN imported successfully

[2/5] Loading config...
  Model path: model/best_ncnn_model

[3/5] Checking model files...
  ✅ Param file: ... (16.3 KB)
  ✅ Bin file: ... (42.5 MB)

[4/5] Loading NCNN model...
  ✅ Param loaded
  ✅ Bin loaded
  ✅ NCNN model loaded successfully!

[5/5] Testing inference...
  - Creating dummy input...
  - Creating extractor...
  ✅ Input set
  ✅ Extract successful
  - Output shape: (12, 8400)
  ✅ Inference test PASSED!

============================================================
  ✅ ALL TESTS PASSED!
============================================================
```

### **Step 2: Nếu Pass, Run Main**

```bash
python3 main.py
```

---

## 🐛 Troubleshooting

### **Issue 1: "NCNN not found"**

```bash
# On Raspberry Pi
sudo apt-get update
sudo apt-get install python3-ncnn

# Check
python3 -c "import ncnn; print('OK')"
```

### **Issue 2: "Failed to load param (code=X)"**

**Possible causes:**
1. **File corrupted:** Re-export model
2. **Wrong format:** Ensure it's NCNN format (not ONNX, PT, etc.)
3. **Permission:** Check file permissions

**Fix:**
```bash
# Check file integrity
ls -lh model/best_ncnn_model/

# Re-export from YOLOv8
# On your training machine:
yolo export model=best.pt format=ncnn imgsz=640
```

### **Issue 3: "Extract failed (code=X)"**

**Possible causes:**
1. **Wrong blob names:** Ensure "in0" and "out0"
2. **Model architecture mismatch**

**Fix:**
```bash
# Check blob names in param file
head -10 model/best_ncnn_model/model.ncnn.param
# Should see: Input ... in0 ...

tail -5 model/best_ncnn_model/model.ncnn.param
# Should see: ... out0
```

### **Issue 4: Vulkan Errors**

**Symptoms:**
```
[ERROR] vkQueueSubmit failed
[ERROR] vkCreateDevice failed
```

**Fix:** Already applied! CPU mode is now forced.

But if you want to try Vulkan:
```python
# config.py - Add this setting
USE_VULKAN = False  # Set to True to try Vulkan

# core/ai.py
self.net.opt.use_vulkan_compute = config.USE_VULKAN
```

---

## 📊 Performance

**CPU Mode:**
- Raspberry Pi 5: ~150-250ms/frame
- Raspberry Pi 4: ~300-500ms/frame
- Desktop CPU: ~50-100ms/frame

**Vulkan Mode** (if working):
- Raspberry Pi 5: ~50-100ms/frame
- May be unstable on some systems

---

## 🎯 Quick Commands

```bash
# 1. Test NCNN only
python3 test_ncnn_only.py

# 2. Check model files
python3 check_model.py

# 3. Run system
python3 main.py
```

---

## 📝 Expected Output (Success)

When running `python3 main.py`, you should see:

```
============================================================
  COCA-COLA SORTING SYSTEM
  FIFO Queue Mode
============================================================

[Initialization] Starting components...
[1/4] Initializing database...
[Database] Initialized: database/product.db

[2/4] Loading AI model...
[AI] Loading model from: model/best_ncnn_model
[AI] Param: model.ncnn.param
[AI] Bin: model.ncnn.bin
[AI] Files found:
  - model/best_ncnn_model/model.ncnn.param (16.3 KB)
  - model/best_ncnn_model/model.ncnn.bin (42.5 MB)
[AI] NCNN configured (CPU mode, 4 threads)
[AI] Loading param file...
[AI] Loading bin file...
[AI] ✅ NCNN model loaded successfully!
[AI] Input size: 640x640
[AI] Confidence threshold: 0.5
[AI] NMS threshold: 0.45
[AI] Input blob: 'in0', Output blob: 'out0'

[3/4] Opening camera...
[Camera] Opened successfully (ID: 0, 640x480)
[Camera] Capture thread started

[4/4] Connecting to Arduino...
[Hardware] Connected to Arduino on /dev/ttyUSB0

✅ All components initialized successfully!

[UI] Creating interface...
✅ UI ready!

============================================================
🚀 SYSTEM READY!
============================================================
```

---

## ✅ Summary

**Fixed:**
- ✅ Forced CPU mode (disabled Vulkan)
- ✅ Added detailed debug logs
- ✅ Added return code checks
- ✅ Added test script (`test_ncnn_only.py`)

**Test:**
```bash
python3 test_ncnn_only.py  # Should pass
python3 main.py             # Should work now
```

---

**If still having issues, run `test_ncnn_only.py` and send the output!**

