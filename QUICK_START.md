# 🚀 Quick Start Guide - Drowsiness Detection

## Cài đặt nhanh (5 phút)

### 1. Cài đặt Python packages

```bash
pip install -r requirements.txt
```

### 2. Chạy ứng dụng

```bash
python main.py
```

### 3. Hiệu chỉnh (Calibration) - QUAN TRỌNG!

1. Nhấn nút **"Start Calibration"**
2. Làm theo hướng dẫn trên màn hình:
   - **Bước 1**: Nhìn thẳng camera (mắt mở bình thường) - 90 frames
   - **Bước 2**: Nhắm mắt (mô phỏng ngủ gật) - 60 frames
   - **Bước 3**: Ngáp 2-3 lần - 60 frames
3. Calibration hoàn tất → Hệ thống tự động lưu

### 4. Bắt đầu phát hiện

1. Nhấn **"Start"**
2. Ngồi cách camera 50-100cm
3. Đảm bảo ánh sáng đủ

---

## ⚙️ Cấu hình cơ bản

### Bật hiển thị landmarks (468 điểm MediaPipe)

1. Mở **Settings**
2. Tích **"Show Landmarks"**
3. Bạn sẽ thấy mesh đầy đủ khuôn mặt!

### Thay đổi camera

1. **Settings** → **Camera ID**
2. Thử: `0`, `1`, `2` (thường 0 là webcam mặc định)

### Tắt âm thanh

1. **Settings** → **Enable Sound**
2. Bỏ tích (nếu muốn test im lặng)

---

## 🎯 Các loại cảnh báo

| Loại                | Điều kiện               | Hiển thị           | Âm thanh     |
| ------------------- | ----------------------- | ------------------ | ------------ |
| 😴 **Ngủ gật**      | Mắt nhắm > 1.5s         | ⚠ CẢNH BÁO NGỦ GẬT | ✅ Có        |
| 🚨 **Ngủ vi giây**  | Mắt nhắm > 2s           | 🚨 DỪNG XE NGAY!   | ✅ Có (mạnh) |
| 👀 **Đầu quay**     | Đầu quay > 20°          | ⚠ MẤT TẬP TRUNG    | ✅ Có        |
| 💤 **Mệt mỏi**      | Ngáp ≥3 + chớp mắt chậm | ⚠ MỆT MỎI          | ✅ Có        |
| ℹ️ **Cảnh báo sớm** | Mắt nặng, staring       | ℹ CẢNH BÁO SỚM     | ❌ Không     |

---

## 🐛 Xử lý lỗi thường gặp

### ❌ "Cannot open camera"

**Nguyên nhân**: Camera đang được dùng bởi app khác
**Giải pháp**:

```bash
# Windows
# Đóng tất cả ứng dụng camera (Teams, Zoom, ...)
# Hoặc thử camera khác (Settings → Camera ID = 1)

# Kiểm tra camera có hoạt động:
python -c "import cv2; print('Camera OK' if cv2.VideoCapture(0).read()[0] else 'Camera Error')"
```

### ❌ "No face detected"

**Nguyên nhân**: Ánh sáng yếu hoặc góc camera sai
**Giải pháp**:

1. Bật đèn
2. Nhìn thẳng vào camera
3. Khoảng cách 50-100cm
4. Không đeo kính râm

### ❌ False alerts (cảnh báo sai)

**Nguyên nhân**: Threshold chưa phù hợp
**Giải pháp**:

1. Chạy lại **Calibration**
2. Đảm bảo làm đúng hướng dẫn
3. Nếu vẫn sai → Chỉnh `ear_default` trong `data/config.json`

### ❌ FPS thấp (<20)

**Nguyên nhân**: CPU yếu
**Giải pháp**:

1. Tắt **Show Landmarks** (Settings)
2. Giảm resolution camera
3. Đóng các ứng dụng nặng khác

---

## 📊 Hiểu các chỉ số

### EAR (Eye Aspect Ratio)

- **> 0.25**: Mắt mở
- **0.20-0.25**: Mắt hơi nhắm
- **< 0.20**: Mắt nhắm (nguy hiểm!)

### MAR (Mouth Aspect Ratio)

- **< 0.4**: Miệng đóng
- **0.4-0.6**: Miệng hơi mở
- **> 0.6**: Ngáp (lưu ý!)

### PERCLOS (Percent Eye Closure)

- **< 8%**: Tỉnh táo
- **8-15%**: Bình thường
- **15-25%**: Mệt mỏi
- **> 25%**: Nguy hiểm!

### Blink Rate (tần suất chớp mắt/phút)

- **< 10**: Staring (dấu hiệu tiền buồn ngủ)
- **12-20**: Bình thường
- **> 25**: Cố gắng tỉnh táo

### Head Pose

- **Pitch**: Góc gật đầu (+ = ngước, - = cúi)
- **Yaw**: Góc quay đầu (+ = phải, - = trái)
- **Roll**: Góc nghiêng đầu

---

## 🎓 Tips sử dụng hiệu quả

### ✅ Làm

1. ✅ Chạy Calibration trước khi sử dụng
2. ✅ Ngồi trong môi trường ánh sáng ổn định
3. ✅ Kiểm tra FPS (nên > 25 fps)
4. ✅ Nghỉ ngơi khi có cảnh báo mệt mỏi

### ❌ Không làm

1. ❌ Không đeo kính râm
2. ❌ Không ngồi quá gần/xa camera
3. ❌ Không dùng trong ánh sáng yếu
4. ❌ Không bỏ qua cảnh báo nguy hiểm

---

## 📝 File quan trọng

- **`data/config.json`**: Cấu hình hệ thống
- **`data/calibration.json`**: Threshold cá nhân (sau khi calibration)
- **`logs/*.csv`**: Log sự kiện (để phân tích sau)

---

## 🆘 Cần trợ giúp?

- 📖 Đọc [README.md](README.md) đầy đủ
- 🐛 Báo lỗi: [GitHub Issues](https://github.com/nguyentrongduc2005/Drowsiness_Detection/issues)
- 💬 Liên hệ: [Email/GitHub]

---

**Chúc bạn sử dụng an toàn! 🚗💨**
