# 📊 Tài Liệu Công Thức Metrics & Phân Phối Xác Suất

> **Hệ Thống Phát Hiện Buồn Ngủ (Drowsiness Detection)**  
> Tài liệu kỹ thuật chi tiết về các công thức tính toán metrics và phân tích thống kê

---

## 📑 Mục Lục

1. [Tổng Quan Hệ Thống](#1-tổng-quan-hệ-thống)
2. [Công Thức Metrics Cơ Bản](#2-công-thức-metrics-cơ-bản)
3. [Phân Phối Xác Suất](#3-phân-phối-xác-suất)
4. [Thuật Toán Học Tự Động](#4-thuật-toán-học-tự-động)
5. [Phát Hiện Trạng Thái](#5-phát-hiện-trạng-thái)
6. [Các Tham Số Cấu Hình](#6-các-tham-số-cấu-hình)

---

## 1. Tổng Quan Hệ Thống

### 1.1 Kiến Trúc Metrics

```
Camera Feed
    ↓
Face Detection (MediaPipe)
    ↓
Facial Landmarks (468 điểm)
    ↓
┌─────────────────────────────────┐
│  Metrics Extraction             │
│  - EAR (Eye Aspect Ratio)       │
│  - MAR (Mouth Aspect Ratio)     │
│  - Quality Score                │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  State Detection                │
│  - Drowsiness                   │
│  - Blink                        │
│  - Yawn                         │
│  - Fatigue                      │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│  Learning Engine                │
│  - Auto Threshold Update        │
│  - Statistical Analysis         │
│  - Personalization              │
└─────────────────────────────────┘
```

---

## 2. Công Thức Metrics Cơ Bản

### 2.1 EAR (Eye Aspect Ratio)

**Định nghĩa:** Đo tỷ lệ giữa chiều cao và chiều rộng của mắt.

#### 📐 Công Thức

```
         ||P2 - P6|| + ||P3 - P5||
EAR = ───────────────────────────────
              2 × ||P1 - P4||
```

**Trong đó:**

- `P1, P2, P3, P4, P5, P6`: 6 điểm landmarks của mắt (đánh số từ 0-5)
- `||·||`: Khoảng cách Euclidean (L2 norm)

#### 💻 Implementation

```python
def calculate_ear(self, eye_landmarks: np.ndarray) -> float:
    """
    Tính Eye Aspect Ratio

    Landmarks layout:
        P2    P3
    P1          P4
        P6    P5
    """
    # Khoảng cách dọc (vertical)
    v1 = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])  # P2-P6
    v2 = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])  # P3-P5

    # Khoảng cách ngang (horizontal)
    h = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])   # P1-P4

    # EAR = (v1 + v2) / (2 × h)
    ear = (v1 + v2) / (2.0 * h)
    return ear
```

#### 📊 Giải Thích Chi Tiết

1. **Tử số:** `v1 + v2`
   - Tổng 2 khoảng cách dọc (chiều cao mắt)
   - Khi mắt mở: v1, v2 lớn
   - Khi mắt nhắm: v1, v2 → 0

2. **Mẫu số:** `2 × h`
   - 2 lần khoảng cách ngang (chiều rộng mắt)
   - Hệ số 2 để chuẩn hóa (trung bình 2 khoảng cách dọc)
   - h ổn định, không đổi khi chớp mắt

3. **Tỷ lệ:**
   - Mắt mở bình thường: **EAR ≈ 0.25 - 0.35**
   - Mắt nửa nhắm: **EAR ≈ 0.15 - 0.25**
   - Mắt nhắm kín: **EAR < 0.15**

#### 🎯 Ví Dụ Tính Toán

```
Giả sử:
- v1 = 8 pixels (khoảng cách P2-P6)
- v2 = 7 pixels (khoảng cách P3-P5)
- h = 30 pixels (khoảng cách P1-P4)

EAR = (8 + 7) / (2 × 30)
    = 15 / 60
    = 0.25  ← Mắt mở bình thường

Khi nhắm mắt:
- v1 = 2 pixels
- v2 = 2 pixels
- h = 30 pixels (không đổi)

EAR = (2 + 2) / (2 × 30)
    = 4 / 60
    = 0.067  ← Mắt nhắm!
```

---

### 2.2 MAR (Mouth Aspect Ratio)

**Định nghĩa:** Đo tỷ lệ giữa chiều cao và chiều rộng của miệng.

#### 📐 Công Thức

```
         ||M1 - M4|| + ||M2 - M5|| + ||M3 - M6||
MAR = ─────────────────────────────────────────────
                   3 × ||M0 - M7||
```

**Trong đó:**

- `M0`: Góc trái miệng (landmark 61)
- `M7`: Góc phải miệng (landmark 291)
- `M1-M6`: 6 điểm dọc tại 3 vị trí (giữa, trái, phải)

#### 💻 Implementation

```python
def calculate_mar(self, mouth_landmarks: np.ndarray) -> float:
    """
    Tính Mouth Aspect Ratio

    Landmarks layout (8 điểm):
    [0]=61 góc trái        [1]=291 góc phải
    [2]=0 trên giữa       [3]=17 dưới giữa
    [4]=39 trên trái      [5]=84 dưới trái
    [6]=269 trên phải     [7]=314 dưới phải
    """
    # 3 khoảng cách dọc tại 3 vị trí
    v1 = np.linalg.norm(mouth_landmarks[2] - mouth_landmarks[3])  # Giữa
    v2 = np.linalg.norm(mouth_landmarks[4] - mouth_landmarks[5])  # Trái
    v3 = np.linalg.norm(mouth_landmarks[6] - mouth_landmarks[7])  # Phải

    # Khoảng cách ngang
    h = np.linalg.norm(mouth_landmarks[0] - mouth_landmarks[1])   # Rộng

    if h == 0:
        return 0.0

    # MAR = trung bình 3 chiều cao / chiều rộng
    mar = (v1 + v2 + v3) / (3.0 * h)
    return mar
```

#### 📊 Giải Thích Chi Tiết

1. **Tử số:** `v1 + v2 + v3`
   - Tổng 3 khoảng cách dọc (chiều cao miệng)
   - Đo ở 3 vị trí: giữa, trái, phải
   - Chính xác hơn chỉ đo 1 điểm

2. **Mẫu số:** `3 × h`
   - 3 lần chiều rộng miệng
   - Hệ số 3 để chuẩn hóa (trung bình 3 khoảng cách)

3. **Tỷ lệ:**
   - Miệng đóng: **MAR ≈ 0.1 - 0.3**
   - Miệng mở vừa: **MAR ≈ 0.3 - 0.5**
   - Ngáp (miệng rộng): **MAR > 0.6**

---

### 2.3 Quality Score

**Định nghĩa:** Đánh giá chất lượng phát hiện khuôn mặt.

#### 📐 Công Thức

```
                 eye_width
Quality = min(1.0, ──────────)
                     30
```

**Trong đó:**

- `eye_width`: Chiều rộng mắt (pixels) = `||P1 - P4||`
- `30`: Ngưỡng tham chiếu (mắt ≥30px là tốt)

#### 💻 Implementation

```python
# Tính chất lượng phát hiện
eye_width = np.linalg.norm(left_eye[0] - left_eye[3])
quality = min(1.0, eye_width / 30.0)

# Chỉ học từ mẫu chất lượng cao
if quality >= 0.75:
    learning_engine.add_sample(ear, mar, quality)
```

#### 📊 Phân Loại Chất Lượng

| Eye Width | Quality   | Đánh Giá | Quyết Định          |
| --------- | --------- | -------- | ------------------- |
| ≥30 px    | 1.0       | Xuất sắc | ✅ Học mẫu          |
| 25-29 px  | 0.83-0.97 | Tốt      | ✅ Học mẫu          |
| 22-24 px  | 0.73-0.80 | Khá      | ✅ Học mẫu (ngưỡng) |
| < 22 px   | < 0.73    | Kém      | ❌ Bỏ qua           |

**Lý do:**

- Mắt lớn → landmarks chính xác
- Mắt nhỏ → sai số cao (xa camera, góc nghiêng)

---

## 3. Phân Phối Xác Suất

### 3.1 Phân Phối Chuẩn (Normal Distribution)

**Giả định:** EAR và MAR tuân theo **phân phối chuẩn** khi người ở trạng thái tỉnh táo.

#### 📐 Hàm Mật Độ Xác Suất

```
                    1              -(x - μ)²
f(x) = ───────────────── × exp( ───────────── )
       σ × √(2π)                   2σ²
```

**Trong đó:**

- `μ` (mu): Trung bình (mean)
- `σ` (sigma): Độ lệch chuẩn (standard deviation)
- `x`: Giá trị metric (EAR hoặc MAR)

#### 💻 Implementation (NumPy)

```python
import numpy as np

# Thu thập samples
ear_samples = [0.28, 0.27, 0.29, 0.26, ...]  # n samples

# Tính statistics
ear_mean = np.mean(ear_samples)      # μ
ear_std = np.std(ear_samples)        # σ

# Phân phối chuẩn: N(μ, σ²)
# EAR ~ N(0.28, 0.04²) ví dụ
```

---

### 3.2 Ngưỡng Dựa Trên Z-Score

#### 📐 Công Thức Z-Score

```
       x - μ
Z = ─────────
        σ
```

**Giải thích:**

- `Z`: Số độ lệch chuẩn từ trung bình
- `Z < 0`: Giá trị thấp hơn trung bình
- `Z > 0`: Giá trị cao hơn trung bình

#### 📊 Bảng Xác Suất (Z-Score)

| Z-Score  | Xác Suất P(X < Z) | Phần Trăm | Ý Nghĩa               |
| -------- | ----------------- | --------- | --------------------- |
| -3.0     | 0.13%             | 0.13%     | Cực kỳ hiếm           |
| -2.0     | 2.28%             | 2.28%     | Rất hiếm              |
| **-1.5** | **6.68%**         | **6.68%** | **Hiếm (Ngưỡng EAR)** |
| -1.0     | 15.87%            | 15.87%    | Khá hiếm              |
| 0.0      | 50.00%            | 50.00%    | Trung bình            |
| +1.0     | 84.13%            | 84.13%    | Bình thường           |

#### 🎯 Áp Dụng Cho EAR

```python
# Ngưỡng phát hiện mắt nhắm
threshold_ear = μ - 1.5 × σ
```

**Giải thích:**

- Chọn `Z = -1.5` (bảo thủ vừa phải)
- Chỉ **6.68%** giá trị EAR nằm dưới ngưỡng này
- Khi EAR < threshold → Khả năng cao đang nhắm mắt

**Ví dụ:**

```
Giả sử: μ = 0.28, σ = 0.04

threshold_ear = 0.28 - 1.5 × 0.04
              = 0.28 - 0.06
              = 0.22

→ EAR < 0.22 được coi là "mắt nhắm" (xảy ra 6.68% thời gian)
```

---

### 3.3 Tại Sao Chọn -1.5 σ?

#### So Sánh Các Ngưỡng

| Hệ Số     | Threshold (μ-kσ) | P(X < T)  | Đặc Điểm     | Đánh Giá          |
| --------- | ---------------- | --------- | ------------ | ----------------- |
| k=1.0     | μ - 1.0σ         | 15.87%    | Quá nhạy     | ❌ Báo động nhiều |
| **k=1.5** | **μ - 1.5σ**     | **6.68%** | **Cân bằng** | ✅ **Tốt nhất**   |
| k=2.0     | μ - 2.0σ         | 2.28%     | Quá chậm     | ⚠️ Bỏ lỡ dấu hiệu |
| k=2.5     | μ - 2.5σ         | 0.62%     | Rất chậm     | ❌ Nguy hiểm      |

**Kết luận:** `-1.5σ` là lựa chọn **tối ưu** giữa độ nhạy và độ chính xác.

---

### 3.4 Phân Phối MAR

#### 🎯 Đặc Điểm Khác Biệt

MAR **không tuân theo phân phối chuẩn** hoàn hảo vì:

1. **Asymmetric:** Miệng không mở âm (MAR ≥ 0)
2. **Bimodal:** Có 2 chế độ (đóng vs. ngáp)

#### 📐 Ngưỡng MAR (Kinh Nghiệm)

```python
# Ngưỡng ngáp = 1.5 lần MAR trung bình
threshold_mar = μ_mar × 1.5
```

**Giải thích:**

- Khi ngáp, miệng mở gấp ~1.5 lần bình thường
- Đây là **heuristic** (kinh nghiệm), không dựa Z-score

**Ví dụ:**

```
Giả sử: μ_mar = 0.40 (miệng đóng)

threshold_mar = 0.40 × 1.5
              = 0.60

→ MAR > 0.60 được coi là "ngáp"
```

---

## 4. Thuật Toán Học Tự Động

### 4.1 Mục Tiêu

**Personalization:** Điều chỉnh ngưỡng phù hợp với từng người dùng.

**Lý do:**

- Mỗi người có khuôn mặt khác nhau
- EAR/MAR bình thường khác nhau
- Ngưỡng cố định không phù hợp mọi người

---

### 4.2 Quy Trình Học

```
Step 1: Thu thập samples (EAR, MAR, quality)
         ↓ (mỗi frame)
Step 2: Lọc chất lượng (quality ≥ 0.75)
         ↓
Step 3: Lọc trạng thái (0.20 < EAR < threshold + 0.08)
         ↓
Step 4: Lưu vào buffer (50-100 samples)
         ↓
Step 5: Tính statistics (μ, σ)
         ↓
Step 6: Cập nhật ngưỡng (Weighted Average)
         ↓
Step 7: Giới hạn ngưỡng (0.17 ≤ EAR ≤ 0.30)
         ↓
Step 8: Lưu vào config
```

---

### 4.3 Công Thức Cập Nhật Ngưỡng

#### 📐 Bước 1: Tính Ngưỡng Mới

```python
# Từ samples gần nhất (n=100)
new_ear = μ - 1.5 × σ
new_mar = μ_mar × 1.5
```

#### 📐 Bước 2: Weighted Average

```python
# Kết hợp ngưỡng cũ và mới
updated_ear = (1 - w) × current_ear + w × new_ear
updated_mar = (1 - w) × current_mar + w × new_mar
```

**Trong đó:**

- `w`: Trọng số (weight) = 0.3 (mặc định)
- `current_ear`: Ngưỡng hiện tại
- `new_ear`: Ngưỡng mới từ samples

#### 📊 Giải Thích Trọng Số

```
w = 0.3 ⇒ 70% cũ + 30% mới

Ví dụ:
- current_ear = 0.25
- new_ear = 0.22

updated_ear = 0.7 × 0.25 + 0.3 × 0.22
            = 0.175 + 0.066
            = 0.241  ← Thay đổi từ từ!
```

**Lợi ích:**

- **Smooth transition:** Tránh thay đổi đột ngột
- **Stability:** Không bị dao động mạnh
- **Adaptability:** Vẫn điều chỉnh theo thời gian

---

### 4.4 Giới Hạn An Toàn

```python
# Đảm bảo ngưỡng trong phạm vi hợp lý
updated_ear = max(0.17, min(0.30, updated_ear))
updated_mar = max(0.50, min(0.80, updated_mar))
```

#### 📊 Bảng Giới Hạn

| Metric | Min  | Max  | Lý Do                    |
| ------ | ---- | ---- | ------------------------ |
| EAR    | 0.17 | 0.30 | Tránh quá nhạy / quá trễ |
| MAR    | 0.50 | 0.80 | Phạm vi thực tế ngáp     |

---

### 4.5 Điều Kiện Học

#### 🎯 Lọc Chất Lượng

```python
if quality < 0.75:
    return False  # Bỏ qua mẫu kém chất lượng
```

#### 🎯 Lọc Trạng Thái

```python
# CHỈ học khi mắt mở gần ngưỡng
ear_threshold = config.get("thresholds.ear", 0.25)
is_valid = 0.20 < ear < (ear_threshold + 0.08)

if not is_valid:
    return False  # Bỏ qua
```

**Lý do:**

- `EAR < 0.20`: Đang ngủ → Không học
- `EAR > threshold + 0.08`: Quá cao → Tránh tăng ngưỡng

---

## 5. Phát Hiện Trạng Thái

### 5.1 Drowsiness (Buồn Ngủ)

#### 📐 Công Thức

```
IF (EAR < threshold_ear) FOR consec_frames ≥ 20
THEN alert = DROWSY
```

**Parameters:**

- `threshold_ear`: 0.17 - 0.30 (tự động học)
- `consec_frames`: 20 frames (≈0.67 giây @ 30fps)

#### 💻 Implementation

```python
def detect_drowsiness(self, ear: float) -> bool:
    threshold = self.config.get("thresholds.ear", 0.25)
    consec_frames = self.config.get("consecutive_frames.drowsiness", 20)

    if ear < threshold:
        self.ear_counter += 1
        if self.ear_counter >= consec_frames:
            return True  # DROWSY!
    else:
        self.ear_counter = 0  # Reset

    return False
```

---

### 5.2 Blink (Chớp Mắt)

#### 📐 Công Thức

```
IF (prev_ear ≥ threshold_blink) AND (ear < threshold_blink)
THEN state = CLOSING

IF (state == CLOSING) AND (ear ≥ threshold_blink)
THEN blink_count += 1
```

**Logic:** Phát hiện quá trình **đóng → mở** hoàn chỉnh.

#### 💻 Implementation

```python
def detect_blink(self, ear: float) -> bool:
    threshold = self.config.get("thresholds.blink", 0.25)

    if self.prev_ear is not None:
        # Mắt đóng
        if ear < threshold and self.prev_ear >= threshold:
            self.is_blinking = True

        # Mắt mở (blink hoàn chỉnh)
        elif ear >= threshold and self.is_blinking:
            self.is_blinking = False
            self.blink_counter += 1
            return True  # BLINK!

    self.prev_ear = ear
    return False
```

#### 📊 Blink Rate

```python
# Đếm blinks trong 60 giây
blink_rate = count(blinks where time > now - 60s)
```

**Tiêu chuẩn:**

- Bình thường: **10-20 blinks/phút**
- Mệt mỏi: **< 10** hoặc **> 25 blinks/phút**

---

### 5.3 Yawn (Ngáp)

#### 📐 Công Thức

```
IF (MAR > threshold_mar) FOR consec_frames ≥ 20
THEN state = YAWNING
```

**Parameters:**

- `threshold_mar`: 0.50 - 0.80 (tự động học)
- `consec_frames`: 20 frames (≈0.67 giây)

#### 💻 Implementation

```python
def detect_yawn(self, mar: float) -> bool:
    threshold = self.config.get("thresholds.yawn", 0.65)
    consec_frames = self.config.get("consecutive_frames.yawn", 20)

    if mar > threshold:
        self.mar_counter += 1
        if self.mar_counter >= consec_frames:
            if not self.is_yawning:
                self.is_yawning = True
                self.yawn_times.append(time.time())
            return True  # YAWNING!
    else:
        self.mar_counter = 0
        self.is_yawning = False

    return False
```

---

### 5.4 Fatigue (Mệt Mỏi)

#### 📐 Công Thức

```
condition = (yawns_60s ≥ 2) AND (blinks_60s < 10 OR blinks_60s ≥ 20)

IF condition FOR 60 seconds
THEN alert = FATIGUE
```

**Logic:**

1. Phát hiện dấu hiệu → Bắt đầu đếm 60s
2. Sau 60s, nếu vẫn còn → Báo cảnh báo
3. Nếu hết → Reset

#### 💻 Implementation

```python
def check_fatigue(self) -> bool:
    current_time = time.time()

    # Đếm trong 60s
    recent_blinks = count(blinks where t > current_time - 60)
    recent_yawns = count(yawns where t > current_time - 60)

    # Điều kiện mệt mỏi
    has_yawns = recent_yawns >= 2
    abnormal_blink = recent_blinks < 10 or recent_blinks >= 20
    is_fatigue = has_yawns and abnormal_blink

    # Bắt đầu theo dõi
    if not self.monitoring and is_fatigue:
        self.monitoring = True
        self.start_time = current_time
        return False  # Chưa báo

    # Đang theo dõi
    if self.monitoring:
        elapsed = current_time - self.start_time

        # Chưa đủ 60s
        if elapsed < 60:
            return False

        # Đủ 60s và vẫn còn dấu hiệu
        if is_fatigue:
            return True  # FATIGUE!
        else:
            self.monitoring = False  # Reset

    return False
```

---

## 6. Các Tham Số Cấu Hình

### 6.1 Ngưỡng Mặc Định

| Tham Số            | Giá Trị | Đơn Vị | Mô Tả                         |
| ------------------ | ------- | ------ | ----------------------------- |
| `thresholds.ear`   | 0.21    | -      | Ngưỡng EAR phát hiện mắt nhắm |
| `thresholds.mar`   | 0.60    | -      | Ngưỡng MAR phát hiện ngáp     |
| `thresholds.blink` | 0.25    | -      | Ngưỡng phát hiện chớp mắt     |

### 6.2 Consecutive Frames

| Tham Số                         | Giá Trị | Frames | Giây (@30fps) |
| ------------------------------- | ------- | ------ | ------------- |
| `consecutive_frames.drowsiness` | 20      | 20     | 0.67s         |
| `consecutive_frames.yawn`       | 20      | 20     | 0.67s         |

**Lý do:** Tránh báo động giả do nhiễu ngắn hạn.

### 6.3 Learning Parameters

| Tham Số                | Giá Trị | Mô Tả                               |
| ---------------------- | ------- | ----------------------------------- |
| `learning.weight`      | 0.3     | Trọng số cập nhật (30% mới, 70% cũ) |
| `learning.samples`     | 50      | Số samples trước khi cập nhật       |
| `learning.buffer`      | 100     | Số samples giữ lại để tính toán     |
| `learning.min_samples` | 10      | Số samples tối thiểu                |

### 6.4 Quality Thresholds

| Tham Số             | Giá Trị | Mô Tả                          |
| ------------------- | ------- | ------------------------------ |
| `quality.min`       | 0.75    | Chỉ học từ mẫu ≥75% chất lượng |
| `quality.eye_width` | 30      | Chiều rộng mắt tham chiếu (px) |

---

## 7. Smoothing & Filtering

### 7.1 Moving Average Filter

#### 📐 Công Thức

```
                  1   n
smoothed_value = ─── ∑ x[i]
                  n  i=1
```

**Trong đó:**

- `n`: Kích thước window (n=5 mặc định)
- `x[i]`: Giá trị tại thời điểm i

#### 💻 Implementation

```python
from collections import deque

# Buffers
self.ear_history = deque(maxlen=5)
self.mar_history = deque(maxlen=5)

# Thêm giá trị mới
self.ear_history.append(current_ear)

# Tính trung bình
smoothed_ear = sum(self.ear_history) / len(self.ear_history)
```

**Lợi ích:**

- Giảm nhiễu cao tần
- Ổn định giá trị metrics
- Tránh dao động

---

## 8. Ví Dụ Thực Tế

### 8.1 Kịch Bản: Người Dùng Mới

```
Frame 1-50: Thu thập samples
- EAR samples: [0.28, 0.27, 0.29, 0.26, ...]
- MAR samples: [0.38, 0.40, 0.37, 0.39, ...]

Frame 50: Cập nhật lần 1
- ear_mean = 0.278, ear_std = 0.042
- new_ear_threshold = 0.278 - 1.5 × 0.042 = 0.215
- updated_ear = 0.7 × 0.21 + 0.3 × 0.215 = 0.212

Frame 100: Cập nhật lần 2
- ear_mean = 0.282, ear_std = 0.038
- new_ear_threshold = 0.282 - 1.5 × 0.038 = 0.225
- updated_ear = 0.7 × 0.212 + 0.3 × 0.225 = 0.216

→ Ngưỡng dần ổn định theo đặc điểm cá nhân!
```

### 8.2 Kịch Bản: Phát Hiện Buồn Ngủ

```
Frame 1000:
- EAR = 0.18 < threshold (0.22)
- Counter = 1

Frame 1001-1019:
- EAR vẫn < 0.22
- Counter tăng: 2, 3, ..., 20

Frame 1020:
- EAR = 0.17 < 0.22
- Counter = 20 ≥ 20
- ⚠️ DROWSINESS DETECTED!
- Alert Level = HIGH
- Play sound warning
```

---

## 9. Tham Khảo Khoa Học

### 9.1 Papers

1. **Soukupová, T., & Čech, J. (2016)**
   - "Real-Time Eye Blink Detection using Facial Landmarks"
   - Conference: CVWW 2016
   - Định nghĩa công thức EAR

2. **Deng, W., & Wu, R. (2019)**
   - "Real-Time Driver Drowsiness Estimation by Multi-Source Information Fusion"
   - Journal: IEEE Access
   - Kết hợp nhiều metrics

### 9.2 Datasets

- **UTA-RLDD:** Real-Life Drowsiness Dataset
- **DROZY:** Drowsiness detection dataset
- **YawDD:** Yawn Detection Dataset

---

## 10. Glossary (Thuật Ngữ)

| Thuật Ngữ     | Tiếng Việt            | Định Nghĩa                     |
| ------------- | --------------------- | ------------------------------ |
| EAR           | Tỷ lệ khía cạnh mắt   | Đo độ mở của mắt               |
| MAR           | Tỷ lệ khía cạnh miệng | Đo độ mở của miệng             |
| Landmark      | Điểm đặc trưng        | Điểm quan trọng trên khuôn mặt |
| Threshold     | Ngưỡng                | Giá trị ranh giới để phân loại |
| Z-Score       | Điểm chuẩn            | Số độ lệch chuẩn từ trung bình |
| Smoothing     | Làm mịn               | Giảm nhiễu trong tín hiệu      |
| Quality Score | Điểm chất lượng       | Đánh giá độ tin cậy phát hiện  |

---

## 📞 Liên Hệ & Đóng Góp

- **Repository:** github.com/nguyentrongduc2005/DrowsinessDetection
- **Issues:** Báo lỗi hoặc đề xuất cải tiến
- **Pull Requests:** Đóng góp code

---

**© 2026 Drowsiness Detection System**  
_Tài liệu kỹ thuật chi tiết - Phiên bản 1.0_
