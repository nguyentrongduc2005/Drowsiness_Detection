# Configuration Guide

## Tổng quan

Dự án Drowsiness Detection sử dụng các file config để quản lý thông số thay vì hardcode trong code. Điều này giúp dễ dàng điều chỉnh và tùy chỉnh hệ thống mà không cần sửa code.

## Các file config trong dự án

### 1. `data/config.json` ✅ **ĐANG SỬ DỤNG**

File cấu hình chính của hệ thống chứa tất cả thông số phát hiện buồn ngủ.

#### Cấu trúc:

```json
{
  "eye_thresholds": {
    "ear_default": 0.25, // Ngưỡng EAR mặc định
    "consecutive_frames": 20, // Số frame liên tiếp để cảnh báo
    "min_ear_threshold": 0.18, // EAR tối thiểu
    "max_ear_threshold": 0.3, // EAR tối đa
    "blink_max": 0.4, // Thời gian chớp mắt tối đa (giây)
    "microsleep_min": 0.5, // Thời gian vi giấc ngủ tối thiểu
    "microsleep_max": 2.0, // Thời gian vi giấc ngủ tối đa
    "near_sleep_max": 4.0, // Gần ngủ tối đa
    "sleep_critical": 4.0, // Ngưỡng nguy hiểm
    "eye_closed_warning": 1.5, // Cảnh báo mắt nhắm (giây)
    "eye_closed_danger": 2.0, // Nguy hiểm mắt nhắm
    "eye_closed_critical": 4.0 // Cực kỳ nguy hiểm
  },

  "mouth_thresholds": {
    "mar_limit": 0.6, // Ngưỡng MAR để phát hiện ngáp
    "yawn_frames": 30, // Số frame tối thiểu cho ngáp
    "yawn_duration_min": 1.5, // Thời gian ngáp tối thiểu (giây)
    "yawn_reminder_threshold": 2, // Số lần ngáp để nhắc nhở
    "yawn_mar_variance_max": 0.05, // Phương sai MAR tối đa (phân biệt ngáp/nói)
    "yawn_ear_drop_threshold": 0.03 // Ngưỡng giảm EAR khi ngáp
  },

  "perclos_thresholds": {
    "normal": 0.08, // < 8% = Tỉnh táo
    "tired": 0.15, // 8-15% = Mệt
    "drowsy": 0.25, // 15-25% = Buồn ngủ
    "critical": 0.4 // > 40% = Nguy hiểm
  },

  "head_pose_thresholds": {
    "pitch_warning": -15, // Đầu cúi xuống 15 độ (cảnh báo)
    "pitch_danger": -25, // Đầu cúi xuống 25 độ (nguy hiểm)
    "roll_warning": 20, // Đầu nghiêng ngang 20 độ
    "yaw_warning": 25, // Đầu quay trái/phải 25 độ
    "yaw_danger": 40, // Đầu quay trái/phải 40 độ (nguy hiểm)
    "duration": 0.5 // Thời gian trước khi cảnh báo (giây)
  },

  "blink_rate_thresholds": {
    "low": 8, // < 8 lần/phút = Nhìn chằm chằm
    "normal_min": 12, // Tốc độ chớp mắt bình thường tối thiểu
    "normal_max": 20, // Tốc độ chớp mắt bình thường tối đa
    "high": 25, // > 25 = Cố gắng tỉnh táo
    "low_duration": 30 // Thời gian nhìn chằm chằm trước cảnh báo (giây)
  },

  "fatigue_thresholds": {
    "window_minutes": 3, // Cửa sổ giám sát (phút)
    "yawn_threshold": 3, // Số lần ngáp tối thiểu
    "drowsy_count": 5 // Số lần buồn ngủ tối thiểu
  },

  "smart_threshold": {
    "window_size": 150, // Kích thước cửa sổ học
    "min_samples_for_learning": 100, // Số mẫu tối thiểu để học
    "threshold_multiplier": 0.75 // Hệ số nhân ngưỡng
  },

  "detection_settings": {
    "min_detection_confidence": 0.6, // Độ tin cậy phát hiện khuôn mặt
    "min_tracking_confidence": 0.6, // Độ tin cậy theo dõi khuôn mặt
    "smoothing_window": 3, // Số frame làm mịn
    "max_frames_without_face": 10 // Số frame tối đa không có khuôn mặt
  },

  "paths": {
    "model_path": "data/shape_predictor_68_face_landmarks.dat",
    "alarm_sound": "data/alarm.wav"
  },

  "settings": {
    "camera_id": 0, // ID camera (0, 1, 2,...)
    "show_landmarks": true, // Hiển thị điểm landmark
    "fps_display": true, // Hiển thị FPS
    "log_enabled": true // Bật logging
  }
}
```

#### Cách sử dụng trong code:

```python
from src.core.config import Config

config = Config()

# Lấy giá trị
ear_default = config.get('eye_thresholds.ear_default', 0.25)
camera_id = config.get_camera_id()

# Hoặc sử dụng qua DrowsinessThresholds
from src.core.analyzers import DrowsinessThresholds

if duration > DrowsinessThresholds.EYE_CLOSED_WARNING:
    print("Cảnh báo!")
```

---

### 2. `data/calibration.json` ✅ **ĐANG SỬ DỤNG**

File lưu ngưỡng cá nhân hóa sau khi người dùng thực hiện calibration.

#### Cấu trúc:

```json
{
  "ear_open": 0.2998, // EAR khi mở mắt
  "ear_closed": 0.1999, // EAR khi nhắm mắt
  "ear_threshold": 0.2741, // Ngưỡng EAR cá nhân
  "ear_open_min": 0.2691, // EAR mở mắt tối thiểu
  "ear_closed_max": 0.2492, // EAR nhắm mắt tối đa
  "mar_normal": null, // MAR bình thường
  "mar_yawn": 0.5446, // MAR khi ngáp
  "mar_threshold": 0.2995, // Ngưỡng MAR cá nhân
  "calibrated": true, // Đã calibration?
  "calibration_date": "2026-01-23T17:55:15.731489"
}
```

#### Được sử dụng trong:

- `src/core/analyzers/calibration.py` - Class `PersonalCalibration`
- Tự động load khi khởi động nếu đã calibration
- Được tạo/cập nhật khi user chạy calibration

---

### 3. `pyrightconfig.json` ✅ **ĐANG SỬ DỤNG**

File cấu hình cho Pyright (Python type checker) trong VS Code.

#### Cấu trúc:

```json
{
  "reportMissingModuleSource": false,
  "reportGeneralTypeIssues": false,
  "reportOptionalMemberAccess": false,
  "reportUnusedVariable": "warning",
  "reportUnusedImport": "warning",
  "reportMissingImports": false,
  "reportAttributeAccessIssue": false,
  "pythonVersion": "3.12",
  "typeCheckingMode": "off"
}
```

#### Mục đích:

- Tắt một số cảnh báo type checking không cần thiết
- Cấu hình Python version
- Chỉ ảnh hưởng đến VS Code editor, không ảnh hưởng runtime

---

## Lợi ích của việc sử dụng Config

### ✅ Trước khi refactor:

```python
# Hardcoded trong code
BLINK_MAX = 0.4
MICROSLEEP_MIN = 0.5
EYE_CLOSED_WARNING = 1.5
```

**Vấn đề:**

- Khó điều chỉnh
- Phải sửa code và restart
- Không thể tùy chỉnh cho từng user

### ✅ Sau khi refactor:

```python
# Load từ config
class DrowsinessThresholds:
    # Tự động load từ config.json
    BLINK_MAX = None  # Sẽ load từ eye_thresholds.blink_max
```

**Lợi ích:**

- ✅ Dễ điều chỉnh: Chỉ sửa file JSON
- ✅ Không cần restart: Có thể reload config
- ✅ Tùy chỉnh linh hoạt cho từng môi trường
- ✅ Dễ backup/restore settings
- ✅ Có thể tạo nhiều profile khác nhau

---

## Hướng dẫn tùy chỉnh

### 1. Điều chỉnh độ nhạy phát hiện:

**Muốn hệ thống nhạy hơn (cảnh báo sớm hơn):**

```json
{
  "eye_thresholds": {
    "eye_closed_warning": 1.0, // Giảm từ 1.5 xuống 1.0
    "ear_default": 0.27 // Tăng từ 0.25 lên 0.27
  }
}
```

**Muốn hệ thống ít cảnh báo hơn:**

```json
{
  "eye_thresholds": {
    "eye_closed_warning": 2.0, // Tăng từ 1.5 lên 2.0
    "ear_default": 0.23 // Giảm từ 0.25 xuống 0.23
  }
}
```

### 2. Thay đổi camera:

```json
{
  "settings": {
    "camera_id": 1 // Đổi từ 0 sang 1 (camera khác)
  }
}
```

### 3. Tăng độ chính xác:

```json
{
  "detection_settings": {
    "min_detection_confidence": 0.7, // Tăng từ 0.6
    "min_tracking_confidence": 0.7 // Tăng từ 0.6
  }
}
```

---

## File config KHÔNG SỬ DỤNG

❌ **Không có file config nào bị thừa** - Tất cả 3 file config đều đang được sử dụng:

1. ✅ `data/config.json` - Cấu hình hệ thống
2. ✅ `data/calibration.json` - Threshold cá nhân
3. ✅ `pyrightconfig.json` - Type checking config

---

## Kết luận

Dự án đã được refactor để:

✅ **Tất cả thông số đều load từ config**

- Không còn hardcode values trong code
- Dễ dàng tùy chỉnh qua file JSON
- Hỗ trợ multiple profiles

✅ **Cấu trúc config rõ ràng**

- Chia thành các nhóm logic (eye, mouth, head_pose, etc.)
- Comments đầy đủ
- Default values hợp lý

✅ **Không có file config thừa**

- 3 file config đều có mục đích rõ ràng
- Tất cả đều được sử dụng trong dự án

---

## Troubleshooting

### Lỗi: "Config file not found"

**Nguyên nhân:** File `data/config.json` bị xóa hoặc đường dẫn sai

**Giải pháp:** Hệ thống tự động sử dụng default config trong `src/core/config.py`

### Lỗi: "Cannot load calibration"

**Nguyên nhân:** File `data/calibration.json` bị corrupt

**Giải pháp:** Xóa file và chạy lại calibration

### Thay đổi config không có tác dụng

**Nguyên nhân:** DrowsinessThresholds đã cache giá trị

**Giải pháp:** Restart ứng dụng hoặc reload config

---

**Cập nhật:** 23/01/2026
**Phiên bản:** 3.1
