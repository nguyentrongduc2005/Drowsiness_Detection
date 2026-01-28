# 🔧 Mã Giả (Pseudocode) - Logic Cốt Lõi

> **Hệ Thống Phát Hiện Buồn Ngủ (Drowsiness Detection)**  
> Mô tả thuật toán và logic xử lý chính dưới dạng mã giả

---

## 📑 Mục Lục

1. [Tính Toán Metrics](#1-tính-toán-metrics)
2. [Phát Hiện Trạng Thái](#2-phát-hiện-trạng-thái)
3. [Học Tự Động](#3-học-tự-động)
4. [Làm Mịn Dữ Liệu](#4-làm-mịn-dữ-liệu)
5. [Vòng Lặp Chính](#5-vòng-lặp-chính)

---

## 1. Tính Toán Metrics

### 1.1 Tính EAR (Eye Aspect Ratio)

```pseudocode
FUNCTION calculate_ear(eye_landmarks):
    INPUT:
        eye_landmarks = array of 6 points [P1, P2, P3, P4, P5, P6]

    // Tính khoảng cách dọc (vertical distances)
    v1 = euclidean_distance(P2, P6)
    v2 = euclidean_distance(P3, P5)

    // Tính khoảng cách ngang (horizontal distance)
    h = euclidean_distance(P1, P4)

    // Công thức EAR
    ear = (v1 + v2) / (2.0 * h)

    OUTPUT: ear
END FUNCTION
```

**Giải thích:**

- **v1, v2:** Chiều cao mắt tại 2 vị trí → Tổng lên để đo độ mở
- **h:** Chiều rộng mắt → Ổn định, dùng làm chuẩn
- **EAR:** Tỷ lệ cao/rộng → Giảm khi mắt nhắm

---

### 1.2 Tính MAR (Mouth Aspect Ratio)

```pseudocode
FUNCTION calculate_mar(mouth_landmarks):
    INPUT:
        mouth_landmarks = array of 8 points
        [M0=left, M1=right, M2-M7=vertical pairs]

    // Tính 3 khoảng cách dọc
    v1 = euclidean_distance(M2, M3)  // Giữa
    v2 = euclidean_distance(M4, M5)  // Trái
    v3 = euclidean_distance(M6, M7)  // Phải

    // Tính khoảng cách ngang
    h = euclidean_distance(M0, M1)

    IF h == 0:
        RETURN 0.0  // Tránh chia cho 0

    // Công thức MAR
    mar = (v1 + v2 + v3) / (3.0 * h)

    OUTPUT: mar
END FUNCTION
```

**Giải thích:**

- **v1, v2, v3:** Chiều cao miệng ở 3 vị trí → Chính xác hơn 1 điểm
- **h:** Chiều rộng miệng
- **MAR:** Tăng khi miệng mở (ngáp)

---

### 1.3 Tính Quality Score

```pseudocode
FUNCTION calculate_quality(left_eye_landmarks):
    INPUT:
        left_eye_landmarks = array of 6 points

    // Đo chiều rộng mắt
    eye_width = euclidean_distance(left_eye[0], left_eye[3])

    // Chuẩn hóa theo ngưỡng 30 pixels
    quality = MIN(1.0, eye_width / 30.0)

    OUTPUT: quality
END FUNCTION
```

**Giải thích:**

- **eye_width ≥ 30px:** Quality = 1.0 (tốt nhất)
- **eye_width < 30px:** Quality giảm (phát hiện kém)

---

## 2. Phát Hiện Trạng Thái

### 2.1 Phát Hiện Buồn Ngủ (Drowsiness)

```pseudocode
FUNCTION detect_drowsiness(ear):
    INPUT:
        ear = current Eye Aspect Ratio

    GLOBAL:
        ear_counter = 0
        ear_threshold = 0.22
        consec_frames = 20
        is_drowsy = False

    IF ear < ear_threshold:
        // Mắt đang nhắm
        ear_counter = ear_counter + 1

        IF ear_counter >= consec_frames:
            // Nhắm đủ lâu → BUỒN NGỦ
            IF NOT is_drowsy:
                is_drowsy = True
                EMIT alert(DROWSY)
            RETURN True
    ELSE:
        // Mắt mở → Reset
        IF is_drowsy:
            is_drowsy = False
            EMIT alert(NORMAL)
        ear_counter = 0

    OUTPUT: False
END FUNCTION
```

**Giải thích:**

- **Counter:** Đếm số frames liên tiếp EAR < ngưỡng
- **consec_frames = 20:** Phải nhắm ≥0.67s mới báo (tránh nhiễu)
- **Reset:** Mắt mở → Counter về 0

---

### 2.2 Phát Hiện Chớp Mắt (Blink)

```pseudocode
FUNCTION detect_blink(ear):
    INPUT:
        ear = current Eye Aspect Ratio

    GLOBAL:
        prev_ear = None
        is_blinking = False
        blink_counter = 0
        blink_threshold = 0.25
        blink_times = deque()

    IF prev_ear IS NOT None:
        // Phát hiện chuyển trạng thái ĐÓNG
        IF ear < blink_threshold AND prev_ear >= blink_threshold:
            is_blinking = True

        // Phát hiện chuyển trạng thái MỞ (blink hoàn chỉnh)
        ELSE IF ear >= blink_threshold AND is_blinking:
            is_blinking = False
            blink_counter = blink_counter + 1
            blink_times.append(current_time())
            prev_ear = ear
            RETURN True  // BLINK DETECTED!

    prev_ear = ear
    OUTPUT: False
END FUNCTION
```

**Giải thích:**

- **State Machine:** Theo dõi chuyển trạng thái mở→đóng→mở
- **Blink hoàn chỉnh:** Chỉ đếm khi có cycle đầy đủ
- **blink_times:** Lưu thời điểm để tính blink rate

---

### 2.3 Phát Hiện Ngáp (Yawn)

```pseudocode
FUNCTION detect_yawn(mar):
    INPUT:
        mar = current Mouth Aspect Ratio

    GLOBAL:
        mar_counter = 0
        mar_threshold = 0.65
        consec_frames = 20
        is_yawning = False
        yawn_times = deque()

    IF mar > mar_threshold:
        // Miệng há rộng
        mar_counter = mar_counter + 1

        IF mar_counter >= consec_frames:
            // Há đủ lâu → NGÁP
            IF NOT is_yawning:
                is_yawning = True
                yawn_times.append(current_time())
            RETURN True
    ELSE:
        // Miệng đóng → Reset
        mar_counter = 0
        is_yawning = False

    OUTPUT: False
END FUNCTION
```

**Giải thích:**

- Tương tự drowsiness nhưng theo dõi MAR (ngưỡng cao)
- Phải há miệng ≥0.67s mới xác định là ngáp

---

### 2.4 Phát Hiện Mệt Mỏi (Fatigue)

```pseudocode
FUNCTION check_fatigue():
    GLOBAL:
        blink_times = deque()
        yawn_times = deque()
        fatigue_monitoring = False
        fatigue_start_time = None

    current_time = get_current_time()

    // Đếm trong 60 giây gần nhất
    recent_blinks = COUNT(blink_times WHERE time > current_time - 60s)
    recent_yawns = COUNT(yawn_times WHERE time > current_time - 60s)

    // Điều kiện mệt mỏi
    has_yawns = (recent_yawns >= 2)
    abnormal_blink = (recent_blinks < 10) OR (recent_blinks >= 20)
    is_fatigue_condition = has_yawns AND abnormal_blink

    // Bắt đầu theo dõi
    IF NOT fatigue_monitoring AND is_fatigue_condition:
        fatigue_monitoring = True
        fatigue_start_time = current_time
        LOG("Bắt đầu theo dõi mệt mỏi")
        RETURN False  // Chưa báo

    // Đang theo dõi
    IF fatigue_monitoring:
        elapsed = current_time - fatigue_start_time

        // Chưa đủ 60 giây
        IF elapsed < 60:
            RETURN False  // Tiếp tục đếm

        // Đã đủ 60 giây → Kiểm tra lại
        IF is_fatigue_condition:
            EMIT alert(FATIGUE)
            RETURN True  // BÁO CẢNH BÁO MỆT MỎI!
        ELSE:
            // Hết dấu hiệu → Reset
            fatigue_monitoring = False
            fatigue_start_time = None
            LOG("Hết mệt mỏi")
            RETURN False

    OUTPUT: False
END FUNCTION
```

**Giải thích:**

- **2-phase detection:** Phát hiện → Theo dõi 60s → Xác nhận
- **Điều kiện:** Ngáp nhiều (≥2) + Blink bất thường
- **Tránh false alarm:** Phải duy trì 60s mới báo

---

## 3. Học Tự Động

### 3.1 Thêm Sample

```pseudocode
FUNCTION add_sample(ear, mar, quality):
    INPUT:
        ear = Eye Aspect Ratio
        mar = Mouth Aspect Ratio
        quality = Quality score (0-1)

    GLOBAL:
        continuous_learning = True
        ear_samples = list()
        mar_samples = list()
        learning_counter = 0

    // Bước 1: Kiểm tra chất lượng
    IF NOT continuous_learning OR quality < 0.75:
        RETURN False  // Bỏ qua mẫu kém

    // Bước 2: Kiểm tra trạng thái (chỉ học khi mắt mở bình thường)
    ear_threshold = config.get("thresholds.ear")
    is_valid = (0.20 < ear < (ear_threshold + 0.08))

    IF NOT is_valid:
        RETURN False  // Bỏ qua

    // Bước 3: Lưu sample
    ear_samples.append(ear)
    mar_samples.append(mar)
    learning_counter = learning_counter + 1

    // Bước 4: Cập nhật sau mỗi 50 samples
    IF learning_counter >= 50:
        update_thresholds()
        learning_counter = 0
        RETURN True

    OUTPUT: False
END FUNCTION
```

**Giải thích:**

- **Lọc kép:** Quality + State → Chỉ học từ dữ liệu tốt
- **Batch update:** Mỗi 50 samples → Cập nhật 1 lần

---

### 3.2 Cập Nhật Ngưỡng

```pseudocode
FUNCTION update_thresholds():
    GLOBAL:
        ear_samples = list()
        mar_samples = list()
        weight = 0.3

    // Kiểm tra đủ samples
    IF length(ear_samples) < 10:
        LOG("Chưa đủ samples")
        RETURN None

    // Lấy 100 samples gần nhất
    recent_ear = ear_samples[-100:]
    recent_mar = mar_samples[-100:]

    // Tính statistics
    ear_mean = MEAN(recent_ear)
    mar_mean = MEAN(recent_mar)
    ear_std = STD_DEV(recent_ear)

    // Tính ngưỡng mới
    new_ear_threshold = ear_mean - 1.5 * ear_std
    new_mar_threshold = mar_mean * 1.5

    // Lấy ngưỡng hiện tại
    current_ear = config.get("thresholds.ear")
    current_mar = config.get("thresholds.mar")

    // Weighted Average (70% cũ + 30% mới)
    updated_ear = current_ear * (1 - weight) + new_ear_threshold * weight
    updated_mar = current_mar * (1 - weight) + new_mar_threshold * weight

    // Giới hạn an toàn
    updated_ear = CLAMP(updated_ear, 0.17, 0.30)
    updated_mar = CLAMP(updated_mar, 0.50, 0.80)

    // Lưu vào config
    config.set("thresholds.ear", updated_ear)
    config.set("thresholds.mar", updated_mar)
    config.save()

    LOG("Cập nhật: EAR={}, MAR={}", updated_ear, updated_mar)

    OUTPUT: (updated_ear, updated_mar)
END FUNCTION
```

**Giải thích:**

- **Statistical analysis:** μ, σ từ samples
- **Weighted update:** Smooth transition
- **Clamping:** Giới hạn trong phạm vi an toàn

---

## 4. Làm Mịn Dữ Liệu

### 4.1 Moving Average Filter

```pseudocode
FUNCTION smooth_metrics(left_eye, right_eye, mouth):
    GLOBAL:
        ear_history = deque(maxlen=5)
        mar_history = deque(maxlen=5)

    // Tính EAR cho 2 mắt
    left_ear = calculate_ear(left_eye)
    right_ear = calculate_ear(right_eye)
    avg_ear = (left_ear + right_ear) / 2.0

    // Tính MAR
    mar = calculate_mar(mouth)

    // Thêm vào history buffer
    ear_history.append(avg_ear)
    mar_history.append(mar)

    // Tính trung bình trượt
    smoothed_ear = SUM(ear_history) / LENGTH(ear_history)
    smoothed_mar = SUM(mar_history) / LENGTH(mar_history)

    OUTPUT: (smoothed_ear, smoothed_mar)
END FUNCTION
```

**Giải thích:**

- **Window size = 5:** Lấy trung bình 5 frames gần nhất
- **Lợi ích:** Giảm nhiễu, ổn định metrics
- **Deque:** Tự động loại bỏ giá trị cũ nhất

---

## 5. Vòng Lặp Chính

### 5.1 Main Detection Loop

```pseudocode
FUNCTION main_detection_loop():
    // Khởi tạo
    camera = open_camera(index=0)
    face_detector = FaceDetector()
    metrics_processor = MetricsProcessor()
    learning_engine = LearningEngine()
    alert_system = AlertSystem()

    WHILE running:
        // Đọc frame
        frame = camera.read()
        IF frame IS None:
            CONTINUE

        // Phát hiện khuôn mặt
        face_landmarks = face_detector.detect(frame)

        IF face_landmarks IS None:
            EMIT face_detected(False)
            CONTINUE
        ELSE:
            EMIT face_detected(True)

        // Trích xuất landmarks
        left_eye = extract_eye_landmarks(face_landmarks, EYE_LEFT)
        right_eye = extract_eye_landmarks(face_landmarks, EYE_RIGHT)
        mouth = extract_mouth_landmarks(face_landmarks)

        // Tính metrics & smoothing
        ear, mar = metrics_processor.process_metrics(left_eye, right_eye, mouth)

        // Tính quality
        quality = calculate_quality(left_eye)

        // Học tự động
        IF learning_engine.is_enabled():
            // Kiểm tra điều kiện học
            ear_threshold = config.get("thresholds.ear")
            is_learning_range = (0.20 < ear < (ear_threshold + 0.08))

            IF is_learning_range AND quality >= 0.75:
                learning_engine.add_sample(ear, mar, quality)
                progress = learning_engine.get_progress()
                EMIT learning_progress(progress)

        // Phát hiện các trạng thái
        is_drowsy = metrics_processor.detect_drowsiness(ear)
        is_blinking = metrics_processor.detect_blink(ear)
        is_yawning = metrics_processor.detect_yawn(mar)
        is_fatigue = metrics_processor.check_fatigue()

        // Xác định mức độ cảnh báo
        alert_level = NORMAL

        IF is_fatigue:
            alert_level = CRITICAL
        ELSE IF is_drowsy:
            alert_level = HIGH
        ELSE IF is_yawning:
            alert_level = MEDIUM

        // Kích hoạt cảnh báo
        IF alert_level != NORMAL:
            alert_system.trigger(alert_level)

        // Emit metrics để UI hiển thị
        EMIT metrics_updated({
            "ear": ear,
            "mar": mar,
            "quality": quality,
            "blink_rate": metrics_processor.get_blink_rate(),
            "yawn_count": metrics_processor.get_yawn_count()
        })

        // Emit alert level
        EMIT alert_changed(alert_level)

        // Vẽ visualization
        IF show_landmarks:
            draw_landmarks(frame, face_landmarks)
            draw_metrics(frame, ear, mar)

        // Emit frame đã xử lý
        EMIT frame_processed(frame, fps)

        // FPS limiting
        SLEEP(1/30)  // 30 FPS

    // Cleanup
    camera.release()
END FUNCTION
```

**Giải thích:**

- **Pipeline:** Camera → Detection → Metrics → State Detection → Alert
- **Parallel tasks:** Learning, Detection, Visualization
- **Event-driven:** Emit signals cho UI thread

---

### 5.2 Alert System

```pseudocode
FUNCTION trigger_alert(alert_level):
    INPUT:
        alert_level = NORMAL | MEDIUM | HIGH | CRITICAL

    GLOBAL:
        current_level = NORMAL
        last_alert_time = 0
        cooldown = 5  // seconds

    current_time = get_current_time()

    // Kiểm tra cooldown (tránh spam)
    IF (current_time - last_alert_time) < cooldown:
        IF alert_level <= current_level:
            RETURN  // Không alert lại

    // Cập nhật state
    current_level = alert_level
    last_alert_time = current_time

    // Thực thi alert theo mức độ
    SWITCH alert_level:
        CASE NORMAL:
            stop_all_sounds()
            status_message = "Bình thường"
            status_color = "green"

        CASE MEDIUM:
            play_sound("warning.wav", volume=0.5)
            status_message = "Ngáp"
            status_color = "yellow"

        CASE HIGH:
            play_sound("alert.wav", volume=0.8, loop=True)
            status_message = "⚠️ BUỒN NGỦ!"
            status_color = "orange"

        CASE CRITICAL:
            play_sound("critical.wav", volume=1.0, loop=True)
            vibrate_device()  // Nếu có
            status_message = "🚨 MỆT MỎI - NGHỈ NGAY!"
            status_color = "red"

    // Emit status cho UI
    EMIT status_changed(status_message, status_color)

    // Log
    LOG("Alert triggered: level={}, time={}", alert_level, current_time)
END FUNCTION
```

**Giải thích:**

- **Cooldown:** Tránh báo động liên tục (spam)
- **Escalation:** Mức độ tăng dần theo mức nghiêm trọng
- **Multi-modal:** Âm thanh + Màu sắc + Rung (nếu có)

---

## 6. Hàm Tiện Ích

### 6.1 Euclidean Distance

```pseudocode
FUNCTION euclidean_distance(point1, point2):
    INPUT:
        point1 = (x1, y1)
        point2 = (x2, y2)

    dx = x2 - x1
    dy = y2 - y1
    distance = SQRT(dx² + dy²)

    OUTPUT: distance
END FUNCTION
```

---

### 6.2 Clamp (Giới Hạn Giá Trị)

```pseudocode
FUNCTION clamp(value, min_value, max_value):
    INPUT:
        value = giá trị cần giới hạn
        min_value = giá trị nhỏ nhất
        max_value = giá trị lớn nhất

    IF value < min_value:
        RETURN min_value
    ELSE IF value > max_value:
        RETURN max_value
    ELSE:
        RETURN value
END FUNCTION
```

---

### 6.3 Get Blink Rate

```pseudocode
FUNCTION get_blink_rate():
    GLOBAL:
        blink_times = deque()

    current_time = get_current_time()
    cutoff_time = current_time - 60  // 60 giây trước

    // Đếm số blink trong 60s gần nhất
    count = 0
    FOR each timestamp IN blink_times:
        IF timestamp > cutoff_time:
            count = count + 1

    OUTPUT: count  // blinks per minute
END FUNCTION
```

---

## 7. Sơ Đồ Tổng Quan

```
┌─────────────────────────────────────────────────────────┐
│                    CAMERA INPUT                         │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FACE DETECTION (MediaPipe)                 │
│  - 468 facial landmarks                                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FEATURE EXTRACTION                         │
│  ┌─────────────┬──────────────┬──────────────┐        │
│  │   EYE       │    MOUTH     │   QUALITY    │        │
│  │ Landmarks   │  Landmarks   │    Score     │        │
│  └──────┬──────┴──────┬───────┴──────┬───────┘        │
└─────────┼─────────────┼──────────────┼─────────────────┘
          │             │              │
          ▼             ▼              ▼
┌─────────────────────────────────────────────────────────┐
│              METRICS CALCULATION                        │
│  calculate_ear()  calculate_mar()  calculate_quality() │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                SMOOTHING (Moving Average)               │
│  - EAR history (5 frames)                              │
│  - MAR history (5 frames)                              │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ DROWSINESS  │ │    BLINK    │ │    YAWN     │
│  DETECTION  │ │  DETECTION  │ │  DETECTION  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       └───────────────┼───────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FATIGUE DETECTION                          │
│  - Yawns in 60s + Abnormal blinks                      │
│  - 60s monitoring period                                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              ALERT SYSTEM                               │
│  NORMAL → MEDIUM → HIGH → CRITICAL                     │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   SOUND     │ │  DISPLAY    │ │  LOGGING    │
│   ALERT     │ │   UPDATE    │ │             │
└─────────────┘ └─────────────┘ └─────────────┘

┌─────────────────────────────────────────────────────────┐
│         LEARNING ENGINE (Background)                    │
│  - Collect samples                                      │
│  - Update thresholds every 50 samples                   │
│  - Personalization                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Complexity Analysis

### 8.1 Time Complexity

| Operation             | Complexity | Notes                                |
| --------------------- | ---------- | ------------------------------------ |
| `calculate_ear()`     | O(1)       | 6 điểm cố định                       |
| `calculate_mar()`     | O(1)       | 8 điểm cố định                       |
| `detect_drowsiness()` | O(1)       | So sánh đơn giản                     |
| `detect_blink()`      | O(1)       | State machine                        |
| `detect_yawn()`       | O(1)       | So sánh đơn giản                     |
| `check_fatigue()`     | O(n)       | n = số blinks/yawns trong 60s (≤100) |
| `smooth_metrics()`    | O(1)       | Buffer size cố định (5)              |
| `update_thresholds()` | O(n)       | n = số samples (100)                 |
| **Per Frame**         | **O(1)**   | **~O(150)** nếu tính fatigue         |

### 8.2 Space Complexity

| Data Structure | Space    | Notes                     |
| -------------- | -------- | ------------------------- |
| `ear_history`  | O(5)     | Deque maxlen=5            |
| `mar_history`  | O(5)     | Deque maxlen=5            |
| `ear_samples`  | O(n)     | Unbounded, n~1000s        |
| `mar_samples`  | O(n)     | Unbounded, n~1000s        |
| `blink_times`  | O(100)   | Deque maxlen=100          |
| `yawn_times`   | O(100)   | Deque maxlen=100          |
| **Total**      | **O(n)** | **n = samples collected** |

---

## 9. Edge Cases & Error Handling

### 9.1 Xử Lý Lỗi

```pseudocode
TRY:
    frame = camera.read()
CATCH CameraError:
    LOG_ERROR("Camera disconnected")
    SHOW_ERROR_DIALOG("Mất kết nối camera")
    RETRY or EXIT

TRY:
    face_landmarks = face_detector.detect(frame)
CATCH DetectionError:
    // Không phát hiện được khuôn mặt
    face_detected_counter = face_detected_counter - 1
    IF face_detected_counter < -30:  // 1 giây không thấy
        EMIT face_detected(False)
        STOP alert sounds
    CONTINUE  // Bỏ qua frame này

TRY:
    ear = calculate_ear(eye_landmarks)
CATCH DivisionByZero:
    LOG_WARNING("Invalid landmarks")
    ear = 0.0  // Safe default
```

---

## 10. Optimization Techniques

### 10.1 Giảm Tính Toán

```pseudocode
// Chỉ tính MAR khi cần (không phải mỗi frame)
IF frame_count % 2 == 0:  // Mỗi 2 frames
    mar = calculate_mar(mouth_landmarks)
    detect_yawn(mar)

// Skip learning khi không cần
IF learning_engine.get_total_samples() > 1000:
    learning_engine.disable()
```

### 10.2 Parallel Processing

```pseudocode
// Xử lý song song
PARALLEL:
    TASK 1: ear_left = calculate_ear(left_eye)
    TASK 2: ear_right = calculate_ear(right_eye)
    TASK 3: mar = calculate_mar(mouth)

avg_ear = (ear_left + ear_right) / 2.0
```

---

## 📚 Tham Khảo

- **File liên quan:**
  - [METRICS_FORMULAS.md](METRICS_FORMULAS.md) - Công thức toán học chi tiết
  - [README.md](../README.md) - Hướng dẫn sử dụng
- **Source code:**
  - [detection_engine.py](../src/core/detection_engine.py)
  - [metrics_processor.py](../src/detection/metrics_processor.py)
  - [learning_engine.py](../src/learning/learning_engine.py)

---

**© 2026 Drowsiness Detection System**  
_Pseudocode Documentation - Version 1.0_
