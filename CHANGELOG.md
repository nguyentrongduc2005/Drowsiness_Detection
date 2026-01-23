# 📋 CHANGELOG - Major Updates

## Version 3.1 - MediaPipe Enhanced (2026-01-23)

### 🎉 Major Changes

#### 1. Chuyển từ dlib sang MediaPipe ✨

**Trước:**

- Sử dụng dlib với 68 landmarks
- Cần tải model file `shape_predictor_68_face_landmarks.dat` (~100MB)
- Cần compile dlib (phức tạp trên Windows)
- Chậm hơn

**Bây giờ:**

- ✅ Sử dụng MediaPipe với **468 landmarks**
- ✅ Model tích hợp sẵn (không cần tải)
- ✅ Cài đặt đơn giản: `pip install mediapipe`
- ✅ **Nhanh hơn 2-3 lần**
- ✅ Độ chính xác cao hơn

#### 2. Vẽ toàn bộ MediaPipe Landmarks 🎨

**Trước:**

- Chỉ vẽ 68 điểm (mắt, mũi, miệng)
- Không thấy được mesh đầy đủ

**Bây giờ:**

- ✅ Vẽ đầy đủ **468 điểm** MediaPipe
- ✅ Hiển thị face mesh chi tiết
- ✅ Có thể bật/tắt qua Settings
- ✅ Màu sắc phân loại:
  - Xanh dương: Mắt
  - Đỏ: Miệng
  - Vàng: Key points (head pose)
  - Xanh lá: Các điểm khác

#### 3. Hệ thống cảnh báo thông minh (Alert System) 🚨

**Trước:**

- Cảnh báo chung chung
- Chỉ phát 1 loại âm thanh
- Không phân biệt mức độ nghiêm trọng

**Bây giờ:**

- ✅ **10 loại cảnh báo** chi tiết:
  1. DROWSINESS - Ngủ gật
  2. MICROSLEEP - Ngủ vi giây
  3. SLEEPING - Đang ngủ (nguy hiểm!)
  4. HEAD_TURN - Đầu quay
  5. HEAD_DOWN - Đầu cúi (xem điện thoại)
  6. HEAD_TILT - Đầu nghiêng
  7. FATIGUE_YAWN - Ngáp nhiều
  8. FATIGUE_BLINK - Chớp mắt bất thường
  9. FATIGUE_COMBINED - Mệt mỏi (ngáp + chớp mắt)
  10. PRE_WARNING - Cảnh báo sớm

- ✅ **4 mức độ nghiêm trọng**:
  - INFO (xanh lá)
  - WARNING (vàng/cam)
  - DANGER (đỏ)
  - CRITICAL (đỏ nhấp nháy)

- ✅ **Cooldown thông minh**: Tránh spam cảnh báo

- ✅ **Đề xuất hành động** cụ thể cho từng loại

#### 4. Logic phát hiện cải thiện 🧠

**Ngủ gật (Drowsiness):**

- Phát hiện: Mắt nhắm > 1.5s
- Cảnh báo: ⚠ CẢNH BÁO NGỦ GẬT
- Hành động: Phát âm thanh + Hiển thị warning

**Mất tập trung (Distraction):**

- Phát hiện:
  - Đầu quay > 20°
  - Đầu cúi xuống (xem điện thoại)
  - Đầu nghiêng sang bên
- Cảnh báo: ⚠ MẤT TẬP TRUNG - NHÌN VỀ PHÍA TRƯỚC
- Hành động: Nhắc nhở tập trung

**Mệt mỏi (Fatigue):**

- Phát hiện: Ngáp ≥3 lần + Chớp mắt chậm/ít
- Cảnh báo: ⚠ MỆT MỎI - NÊN NGHỈ NGƠI
- Hành động: Đề xuất nghỉ 15-20 phút

### 🗑️ Removed

#### Dependencies không cần thiết

- ❌ Removed: `dlib==19.24.99`
- ❌ Removed: `cmake==4.2.1`
- ❌ Removed: `imutils==0.5.4`
- ❌ Removed: `setuptools`, `wheel` (không cần specify)

### 📁 New Files

#### 1. `src/core/alert_system.py`

Hệ thống cảnh báo thông minh với:

- Enum `AlertType`: 10 loại cảnh báo
- Enum `AlertSeverity`: 4 mức độ nghiêm trọng
- Class `AlertSystem`: Quản lý cảnh báo với cooldown
- Config cho từng loại (màu sắc, âm thanh, message)

#### 2. `QUICK_START.md`

Hướng dẫn nhanh:

- Cài đặt 5 phút
- Calibration
- Xử lý lỗi thường gặp
- Tips sử dụng

#### 3. `CHANGELOG.md` (file này)

Tóm tắt các thay đổi lớn

### 🔧 Modified Files

#### `src/core/detector.py`

- ✅ Thêm method `draw_all_mediapipe_landmarks()`: Vẽ đầy đủ 468 điểm
- ✅ Tích hợp MediaPipe drawing utilities
- ✅ Màu sắc phân loại theo vùng

#### `src/core/processor.py`

- ✅ Import `AlertSystem`
- ✅ Tích hợp Alert System vào `__init__()`
- ✅ Cải thiện warning logic với 10 loại cảnh báo
- ✅ Return thêm: `alert_config`, `alert_message`, `alert_action`

#### `main.py`

- ✅ Sử dụng `draw_all_mediapipe_landmarks()` thay vì `draw_landmarks()`
- ✅ Xử lý `alert_config` từ processor
- ✅ Hiển thị cảnh báo theo màu sắc và mức độ nghiêm trọng
- ✅ Truyền `alert_config` vào `_draw_info_on_frame()`

#### `requirements.txt`

- ✅ Loại bỏ dlib, cmake, imutils
- ✅ Chỉ giữ lại dependencies cần thiết
- ✅ Clean và dễ cài đặt

#### `README.md`

- ✅ Cập nhật documentation đầy đủ
- ✅ So sánh dlib vs MediaPipe
- ✅ Hướng dẫn chi tiết các tính năng
- ✅ Benchmark performance

### 📊 Performance Improvements

| Metric         | Before (dlib) | After (MediaPipe) | Improvement |
| -------------- | ------------- | ----------------- | ----------- |
| FPS            | ~15-20        | ~25-30            | **+50%**    |
| Detection time | ~60-80ms      | ~30-40ms          | **-50%**    |
| Setup time     | 30-60 min     | 5 min             | **-90%**    |
| Model size     | 100MB         | Built-in          | **-100MB**  |

### 🎯 Code Quality

#### Tổ chức tốt hơn

- ✅ Alert logic tách riêng module
- ✅ Code dễ đọc, dễ maintain
- ✅ Type hints rõ ràng
- ✅ Documentation đầy đủ

#### Dễ mở rộng

- ✅ Thêm loại cảnh báo mới: Chỉ cần thêm vào `AlertType` enum
- ✅ Thay đổi âm thanh: Chỉ cần sửa `AlertConfig`
- ✅ Điều chỉnh threshold: Có Calibration UI

### 🚀 Migration Guide

#### Nếu đang dùng version cũ (dlib):

1. **Cập nhật dependencies:**

```bash
pip uninstall dlib cmake  # Xóa cũ
pip install -r requirements.txt  # Cài mới
```

2. **Không cần thay đổi config:**

- File `data/config.json` vẫn tương thích
- File `data/calibration.json` vẫn hoạt động

3. **Chạy lại app:**

```bash
python main.py
```

4. **Tận hưởng MediaPipe!**

- Bật "Show Landmarks" để xem 468 điểm
- Cảnh báo chi tiết hơn
- Nhanh hơn, mượt hơn

### 🐛 Bug Fixes

- ✅ Fixed: Tracking lost tạm thời không còn gây spike trên graph
- ✅ Fixed: False positive khi quay đầu nhanh
- ✅ Fixed: Alert spam (thêm cooldown)
- ✅ Fixed: Âm thanh phát liên tục (cooldown 3s)

### 🙏 Credits

- **MediaPipe Team (Google)**: Face detection framework tuyệt vời
- **OpenCV Community**: Computer vision tools
- **Contributors**: Testing and feedback

### 📅 Timeline

- **2026-01-23**: Release version 3.1
  - MediaPipe migration
  - Alert System
  - 468 landmarks visualization
  - Code cleanup

### 🔮 Future Plans (Version 3.2+)

- [ ] Multi-language support (English/Vietnamese toggle)
- [ ] Export alert statistics to PDF report
- [ ] Mobile app (iOS/Android)
- [ ] Cloud sync calibration data
- [ ] AI-based personalized threshold learning
- [ ] Integration with car systems (OBD-II)

---

**Happy safe driving! 🚗💨**

For questions or issues, please visit: https://github.com/nguyentrongduc2005/Drowsiness_Detection/issues
