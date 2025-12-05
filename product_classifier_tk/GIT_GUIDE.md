# 📝 Git Guide - Hướng Dẫn Sử Dụng Git

## 🎯 File `.gitignore` Đã Được Tạo

File `.gitignore` đã được cấu hình để loại bỏ:

### ❌ Các File Bị Ignore (Không Commit):

1. **Python Cache:**
   - `__pycache__/`
   - `*.pyc`, `*.pyo`, `*.pyd`
   - `.pytest_cache/`

2. **IDE/Editor:**
   - `.vscode/`
   - `.idea/`
   - `.cursor/`

3. **System Files:**
   - `.DS_Store` (macOS)
   - `Thumbs.db` (Windows)
   - `*~` (Linux)

4. **Captured Images:**
   - `captures/defects/*.jpg`
   - `captures/*.png`
   - (Folder structure được giữ lại với `.gitkeep`)

5. **Database:**
   - `*.db`
   - `*.sqlite`

6. **Model Files** (quá lớn):
   - `*.pt`
   - `*.pth`
   - `*.onnx`

7. **Virtual Environment:**
   - `venv/`
   - `.venv/`

8. **Logs & Temp:**
   - `*.log`
   - `*.tmp`
   - `*.bak`

### ✅ Các File Được Commit:

- ✅ Source code (`.py`)
- ✅ Arduino code (`.ino`)
- ✅ Documentation (`.md`)
- ✅ Configuration (`requirements.txt`)
- ✅ Scripts (`.sh`)

---

## 🚀 Cách Sử Dụng Git

### Lần Đầu Setup Repository

```bash
cd product_classifier_tk

# 1. Initialize git repository
git init

# 2. Add all files (gitignore sẽ tự động lọc)
git add .

# 3. Commit lần đầu
git commit -m "Initial commit: Bottle defect detection system (Tkinter version)"

# 4. Add remote repository (nếu có)
git remote add origin https://github.com/username/repo-name.git

# 5. Push lên GitHub
git push -u origin main
```

### Workflow Thường Ngày

```bash
# 1. Check status (xem file nào thay đổi)
git status

# 2. Add files muốn commit
git add main_continuous_flow_tkinter.py
git add README_VI.md

# Hoặc add tất cả
git add .

# 3. Commit với message
git commit -m "Update: Improve camera capture speed"

# 4. Push lên remote
git push
```

---

## 📋 Common Git Commands

### Kiểm Tra Trạng Thái

```bash
# Xem file nào thay đổi
git status

# Xem chi tiết thay đổi
git diff

# Xem lịch sử commit
git log --oneline
```

### Làm Việc Với Files

```bash
# Add file cụ thể
git add main_continuous_flow_tkinter.py

# Add tất cả files
git add .

# Remove file khỏi staging
git reset HEAD filename

# Undo thay đổi (CẢNH BÁO: mất changes)
git checkout -- filename
```

### Branches

```bash
# Tạo branch mới
git branch feature-new-gui

# Chuyển sang branch
git checkout feature-new-gui

# Tạo và chuyển luôn
git checkout -b feature-new-gui

# Merge branch vào main
git checkout main
git merge feature-new-gui

# Xóa branch
git branch -d feature-new-gui
```

### Remote Repository

```bash
# Xem remote
git remote -v

# Add remote
git remote add origin URL

# Pull từ remote
git pull origin main

# Push lên remote
git push origin main

# Clone repository
git clone URL
```

---

## 🔧 Xử Lý Cache Đã Commit Trước Đó

Nếu bạn đã commit cache trước khi có `.gitignore`:

### Xóa Cache Khỏi Git (Không Xóa File Local)

```bash
# Xóa tất cả __pycache__
git rm -r --cached **/__pycache__

# Xóa tất cả .pyc files
git rm --cached **/*.pyc

# Xóa .vscode
git rm -r --cached .vscode/

# Xóa .idea
git rm -r --cached .idea/

# Commit changes
git commit -m "Remove cache files from git tracking"

# Push
git push
```

### Xóa Toàn Bộ Cache Và Re-add

```bash
# Xóa tất cả files khỏi git index (không xóa local)
git rm -r --cached .

# Add lại tất cả (gitignore sẽ filter)
git add .

# Commit
git commit -m "Clean up: Remove all cache files"

# Push
git push
```

---

## 📦 Xử Lý Model Files (Quá Lớn)

Model files (`.pt`) quá lớn để push lên GitHub (>100MB limit).

### Giải Pháp 1: Git LFS (Large File Storage)

```bash
# Install Git LFS
git lfs install

# Track model files
git lfs track "*.pt"
git lfs track "*.pth"

# Add .gitattributes
git add .gitattributes

# Commit và push như bình thường
git add model/my_model.pt
git commit -m "Add model file with LFS"
git push
```

### Giải Pháp 2: External Storage

```bash
# Upload model lên Google Drive, Dropbox, etc.
# Tạo file README trong model/ folder:

echo "# Model Files

Download model from: [LINK]

Place file at: model/my_model.pt" > model/README.md

git add model/README.md
git commit -m "Add model download instructions"
git push
```

---

## 🎯 Best Practices

### 1. Commit Messages

**Good:**
```bash
git commit -m "Fix: Camera crash when resolution too high"
git commit -m "Add: Voting mechanism for defect detection"
git commit -m "Update: Improve Arduino communication speed"
git commit -m "Docs: Add calibration guide"
```

**Bad:**
```bash
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
```

### 2. Commit Frequency

- ✅ Commit sau mỗi tính năng hoàn thành
- ✅ Commit trước khi thử nghiệm lớn
- ✅ Commit cuối ngày làm việc
- ❌ Đừng commit code lỗi vào main branch

### 3. Branch Strategy

```
main (production-ready code)
  ├── develop (development branch)
  │     ├── feature/new-gui
  │     ├── feature/improve-ai
  │     └── fix/camera-bug
```

### 4. `.gitignore` Tips

```bash
# Xem files nào sẽ bị ignore
git status --ignored

# Test gitignore pattern
git check-ignore -v filename

# Xem files đã tracked
git ls-files
```

---

## 🔍 Troubleshooting

### Problem: File bị ignore nhưng vẫn muốn commit

**Solution:**
```bash
# Force add file cụ thể
git add -f captures/defects/example.jpg

# Hoặc sửa .gitignore
```

### Problem: Commit nhầm file lớn

**Solution:**
```bash
# Undo commit cuối (giữ changes)
git reset --soft HEAD~1

# Remove file
git rm --cached large_file.pt

# Commit lại
git commit -m "Remove large file"
```

### Problem: Conflict khi merge

**Solution:**
```bash
# Xem files conflict
git status

# Edit files, resolve conflicts
# Then:
git add resolved_file.py
git commit -m "Resolve merge conflict"
```

---

## 📚 Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git LFS](https://git-lfs.github.com/)
- [Gitignore Generator](https://www.toptal.com/developers/gitignore)

---

## ✅ Quick Checklist

Before first commit:
- [ ] `.gitignore` đã tạo
- [ ] Đã xóa cache cũ khỏi git
- [ ] Model files handled (LFS hoặc external)
- [ ] Virtual environment ignored
- [ ] Database files ignored

For daily work:
- [ ] `git status` trước khi commit
- [ ] Commit message rõ ràng
- [ ] Test code trước khi push
- [ ] Pull trước khi push (nếu làm team)

---

**Happy coding! 🚀**

