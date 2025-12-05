# 🚀 BẮT ĐẦU TẠI ĐÂY

## 👋 Chào Mừng!

Bạn đang ở đúng nơi! Đây là hệ thống kiểm tra lỗi chai Coca-Cola tự động.

---

## 📖 Đọc File Nào Trước?

### 1️⃣ Người Việt Nam → Đọc Đầu Tiên

**[README_VI.md](README_VI.md)** 🇻🇳
- Hướng dẫn đầy đủ bằng tiếng Việt
- Giải thích chi tiết mọi thứ
- **BẮT ĐẦU TỪ ĐÂY!**

### 2️⃣ Muốn Setup Nhanh

**[QUICK_START.md](QUICK_START.md)** ⚡
- 5 bước setup
- 5 phút hoàn thành
- Chạy ngay được

### 3️⃣ Cần Tìm Thông Tin Cụ Thể

**[INDEX.md](INDEX.md)** 📚
- Chỉ mục tất cả tài liệu
- Tìm nhanh theo chủ đề

---

## 🎯 File Chính Để Chạy

```bash
# FILE NÀY ĐỂ CHẠY HỆ THỐNG:
python3 main_continuous_flow_tkinter.py
```

**Đừng nhầm với các file khác!**

---

## ✅ Checklist Nhanh

- [ ] **Đã đọc [README_VI.md](README_VI.md)?**
- [ ] **Đã cài dependencies?** (`pip3 install -r requirements.txt`)
- [ ] **Đã upload Arduino firmware?** (`arduino/product_sorter.ino`)
- [ ] **Đã test components?** (`python3 test_system_components.py`)
- [ ] **Đã hiệu chỉnh PHYSICAL_DELAY?** (Xem CALIBRATION_GUIDE.md)

→ Nếu tất cả ✅ → **Chạy hệ thống:**

```bash
python3 main_continuous_flow_tkinter.py
```

---

## 🗂️ Cấu Trúc Thư Mục

```
product_classifier_tk/
│
├── START_HERE.md                      ← BẠN ĐANG Ở ĐÂY
│
├── 🇻🇳 ĐỌC ĐẦU TIÊN
│   └── README_VI.md                   Hướng dẫn tiếng Việt
│
├── ⚡ SETUP NHANH
│   ├── QUICK_START.md                 5 phút setup
│   └── INDEX.md                       Chỉ mục tài liệu
│
├── ⭐ FILE CHÍNH
│   ├── main_continuous_flow_tkinter.py  ← CHẠY FILE NÀY
│   └── run_tkinter.sh                   Script chạy nhanh
│
├── 📚 TÀI LIỆU CHI TIẾT
│   ├── CONTINUOUS_FLOW_README.md      Manual đầy đủ
│   ├── CALIBRATION_GUIDE.md           Hướng dẫn hiệu chỉnh
│   ├── TKINTER_VERSION.md             Thông tin GUI
│   ├── REFACTORING_COMPARISON.md      So sánh old/new
│   └── REFACTOR_SUMMARY.md            Tổng kết dự án
│
├── 🧪 TESTING
│   ├── test_system_components.py      Test từng phần
│   └── demo_voting_mechanism.py       Demo voting
│
├── 🔧 ARDUINO
│   └── arduino/product_sorter.ino     Firmware Arduino
│
├── 🤖 AI MODEL
│   └── model/my_model.pt              YOLOv8 model
│
└── 📦 DEPENDENCIES
    └── requirements.txt                Python packages
```

---

## 🆘 Gặp Vấn Đề?

### Không Biết Bắt Đầu Từ Đâu
→ Đọc [README_VI.md](README_VI.md) 🇻🇳

### Muốn Setup Nhanh
→ Đọc [QUICK_START.md](QUICK_START.md) ⚡

### Lỗi Kỹ Thuật
→ Xem [CONTINUOUS_FLOW_README.md](CONTINUOUS_FLOW_README.md) → Troubleshooting

### Không Hiệu Chỉnh
→ Xem [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) 🎯

### Tìm Thông Tin Cụ Thể
→ Xem [INDEX.md](INDEX.md) 📚

---

## 🎓 Learning Path

### Đường 1: Người Mới (Production)
```
1. START_HERE.md           ← Bạn đang ở đây
2. README_VI.md           ← Đọc tiếp
3. QUICK_START.md          ← Setup
4. CALIBRATION_GUIDE.md    ← Hiệu chỉnh
5. RUN: main_continuous_flow_tkinter.py
```

### Đường 2: Developer (Hiểu Code)
```
1. README_VI.md
2. REFACTORING_COMPARISON.md  ← Hiểu architecture
3. CONTINUOUS_FLOW_README.md  ← Technical details
4. main_continuous_flow_tkinter.py ← Study code
```

### Đường 3: Đã Dùng Hệ Thống Cũ
```
1. REFACTORING_COMPARISON.md  ← What changed?
2. TKINTER_VERSION.md          ← New GUI info
3. QUICK_START.md              ← Re-setup
4. RUN: main_continuous_flow_tkinter.py
```

---

## 💡 Tip Quan Trọng

### ⚠️ PHẢI HIỆU CHỈNH PHYSICAL_DELAY!

Đây là thông số **QUAN TRỌNG NHẤT**:

```python
# Trong main_continuous_flow_tkinter.py
PHYSICAL_DELAY = 2.0  # ← PHẢI SỬA GIÁ TRỊ NÀY
```

**Cách tính:**
```
Khoảng cách camera → servo: ___ cm
Tốc độ băng chuyền: ___ cm/s
→ PHYSICAL_DELAY = khoảng_cách / tốc_độ
```

**Chi tiết:** [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md)

---

## 🎯 Hành Động Ngay

### Bước 1: Đọc Hướng Dẫn
```bash
# Mở file này trong trình đọc
cat README_VI.md
# Hoặc mở trong text editor
```

### Bước 2: Cài Đặt
```bash
pip3 install -r requirements.txt
```

### Bước 3: Test
```bash
python3 test_system_components.py
```

### Bước 4: Chạy!
```bash
python3 main_continuous_flow_tkinter.py
```

---

## 📞 Cần Giúp Đỡ?

### Tất Cả Câu Trả Lời Có Trong:

| Câu Hỏi | File |
|---------|------|
| Hướng dẫn tổng quan? | [README_VI.md](README_VI.md) |
| Setup nhanh? | [QUICK_START.md](QUICK_START.md) |
| Cách hiệu chỉnh? | [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) |
| Lỗi kỹ thuật? | [CONTINUOUS_FLOW_README.md](CONTINUOUS_FLOW_README.md) |
| Tìm thông tin? | [INDEX.md](INDEX.md) |

---

## ✨ Bắt Đầu Ngay!

```bash
# 1. Đọc hướng dẫn tiếng Việt
cat README_VI.md

# 2. Setup nhanh
pip3 install -r requirements.txt

# 3. Test
python3 test_system_components.py

# 4. Chạy hệ thống
python3 main_continuous_flow_tkinter.py
```

---

**Chúc bạn thành công! 🍾🤖**

**Next:** [README_VI.md](README_VI.md) 🇻🇳

