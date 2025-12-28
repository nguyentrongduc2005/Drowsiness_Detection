# Hệ thống Phát hiện Buồn ngủ - Drowsiness Detection System

## Tổng quan

Hệ thống phát hiện buồn ngủ sử dụng Computer Vision và Machine Learning để theo dõi trạng thái mắt của người lái xe, cảnh báo khi phát hiện dấu hiệu buồn ngủ.

## Kiến trúc Hệ thống

### P1: Module AI (core/detector.py)

- **Nhiệm vụ**: Chuyển đổi Frame ảnh thành tọa độ 68 điểm landmarks
- **Class chính**: `FaceDetector`
- **Hàm chính**:
  - `get_landmarks(frame)`: Trả về list 68 cặp (x, y) hoặc None
  - Index quan trọng: Mắt trái [36-41], Mắt phải [42-47], Miệng [48-67]

### P2: Module Logic (core/processor.py)

- **Nhiệm vụ**: Tính toán chỉ số và quản lý Ngưỡng thích nghi
- **Hàm chính**:
  - `calculate_ear(eye_points)`: Tính Eye Aspect Ratio (EAR)
  - `calculate_mar(mouth_points)`: Tính Mouth Aspect Ratio (MAR)
- **Class chính**: `SmartThreshold(window_size=150)`
  - `history`: Dùng collections.deque để lưu EAR
  - `update_threshold(current_ear)`:
    - Nếu current_ear > 0.2: Add vào history
    - Nếu len(history) < 100: Trả về (Ngưỡng mặc định, False)
    - Nếu len(history) >= 100: Tính trung bình 50% giá trị cao nhất → Trả về (Ngưỡng mới, True)

### P3: Module Giao diện (ui/interface.py)

- **Nhiệm vụ**: Thiết kế UI của App
- **Class chính**: `MainWindow(QMainWindow)`
- **Hàm hiển thị**: `update_view(qt_image, ear, threshold, status)`
  - Cập nhật ảnh webcam lên QLabel
  - Cập nhật nhãn trạng thái (Hệ thống đang học / Đang bảo vệ)
  - Đổi màu nền/nhãn thành Đỏ nếu nhận tín hiệu is_drowsy

### P4: Module Dữ liệu (utils/logger.py & config.json)

- **Nhiệm vụ**: Cung cấp thông số và lưu vết
- **File config.json**: Lưu EAR_DEFAULT = 0.25, CONSEC_FRAMES = 20
- **Hàm chính trong logger.py**: `log_event(ear, threshold, status)`
  - Lưu vào CSV: Thời gian | EAR | Ngưỡng | Trạng thái

### P5: Tích hợp (main.py)

- **Nhiệm vụ**: Kết nối các module bằng Đa luồng
- **Class chính**: `CameraWorker(QThread)`
- **Luồng xử lý**:
  ```
  Camera → P1 (Landmarks) → P2 (EAR) → P2 (Update Threshold) → So sánh → Emit Signal
  ```
- **Xử lý cảnh báo**: Nếu ear < threshold kéo dài CONSEC_FRAMES → Phát alarm.wav

## Cài đặt

### Yêu cầu

- Python 3.12
- Webcam

### Các bước cài đặt

1. **Clone repository**

   ```bash
   git clone https://github.com/nguyentrongduc2005/Drowsiness_Detection.git
   cd Drowsiness_Detection
   ```

2. **Cài đặt dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Tải shape predictor model**

   - Tải file `shape_predictor_68_face_landmarks.dat` từ [dlib models](http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2)
   - Giải nén và đặt vào thư mục `data/`

4. **Chuẩn bị file âm thanh cảnh báo**
   - Đặt file `alarm.wav` vào thư mục `data/`

## Sử dụng

### Chạy ứng dụng

```bash
python main.py
```

### Các bước sử dụng

1. **Bắt đầu**: Nhấn nút "Bắt đầu"
2. **Giai đoạn học**: Hệ thống sẽ học trong 100 frame đầu (khoảng 3-5 giây)
   - Giữ mắt mở rõ ràng
   - Nhìn thẳng vào camera
3. **Giai đoạn bảo vệ**: Sau khi học xong, hệ thống bắt đầu giám sát
4. **Học lại**: Nhấn nút "Học lại" nếu muốn reset
5. **Dừng**: Nhấn nút "Dừng" để kết thúc

## Cấu hình

Chỉnh sửa file `data/config.json`:

```json
{
  "eye_thresholds": {
    "ear_default": 0.25,
    "consecutive_frames": 20
  },
  "smart_threshold": {
    "window_size": 150,
    "min_samples_for_learning": 100
  },
  "settings": {
    "camera_id": 0,
    "show_landmarks": true,
    "log_enabled": true
  }
}
```

## Cấu trúc thư mục

```
project/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md              # Tài liệu này
├── data/
│   ├── config.json        # Cấu hình
│   ├── shape_predictor_68_face_landmarks.dat  # Model dlib
│   └── alarm.wav          # Âm thanh cảnh báo
├── lib/
│   └── dlib-*.whl         # dlib wheel file
├── logs/                  # Thư mục log (tự động tạo)
├── src/
│   ├── core/
│   │   ├── detector.py    # P1: AI Module
│   │   ├── processor.py   # P2: Logic Module
│   │   └── config.py      # Config loader
│   ├── ui/
│   │   └── interface.py   # P3: UI Module
│   └── utils/
│       └── logger.py      # P4: Logger Module
```

## Công thức toán học

### Eye Aspect Ratio (EAR)

$$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \times ||p_1 - p_4||}$$

Trong đó:

- $p_1, p_2, ..., p_6$ là các điểm landmarks của mắt
- EAR thông thường: 0.25 - 0.35 (mắt mở)
- EAR < 0.25: Mắt nhắm

### Adaptive Threshold

$$Threshold = 0.75 \times \text{mean}(\text{top 50\% EAR values})$$

## Troubleshooting

### Lỗi không tìm thấy camera

- Kiểm tra camera có hoạt động không
- Thử đổi `camera_id` trong config.json (0, 1, 2, ...)

### Lỗi không tìm thấy model

- Đảm bảo file `shape_predictor_68_face_landmarks.dat` trong thư mục `data/`
- Kiểm tra đường dẫn trong config.json

### Cảnh báo sai (false positive)

- Nhấn nút "Học lại"
- Đảm bảo ánh sáng đủ và nhìn thẳng vào camera khi học

## Tác giả

- **Nguyễn Trọng Đức** - [nguyentrongduc2005](https://github.com/nguyentrongduc2005)

## License

MIT License

## Tài liệu tham khảo

1. Soukupová, T., & Čech, J. (2016). Real-Time Eye Blink Detection using Facial Landmarks. 21st Computer Vision Winter Workshop.
2. dlib C++ Library - [http://dlib.net/](http://dlib.net/)
