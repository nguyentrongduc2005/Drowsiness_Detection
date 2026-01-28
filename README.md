# Driver Drowsiness Detection System

A real-time drowsiness and fatigue detection system for drivers using computer vision with MediaPipe and PyQt5.

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Detection Flow & Logic](#detection-flow--logic)
4. [Detection Algorithms](#detection-algorithms)
5. [Project Structure](#project-structure)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [System Flow Diagram](#system-flow-diagram)

---

## Overview

This system monitors a driver's facial features in real-time through a webcam to detect signs of drowsiness and fatigue. It uses **MediaPipe Face Mesh** for facial landmark detection and calculates various metrics to determine the driver's alertness level.

### Key Features

- **Real-time face detection** with 468 facial landmarks
- **Drowsiness detection** using Eye Aspect Ratio (EAR)
- **Yawn detection** using Mouth Aspect Ratio (MAR)
- **Fatigue detection** based on blink and yawn patterns over time
- **Audio alerts** for critical drowsiness states
- **Visual alerts** with color-coded status (Green/Yellow/Red)
- **Continuous learning** to adapt to individual users
- **Multi-threaded processing** for smooth performance

### Alert Levels

| Level       | Color     | Condition                                  | Alert Type     |
| ----------- | --------- | ------------------------------------------ | -------------- |
| **NONE**    | 🟢 Green  | Normal state                               | None           |
| **FATIGUE** | 🟡 Yellow | Tired (multiple yawns + abnormal blinking) | Visual only    |
| **DROWSY**  | 🔴 Red    | Drowsy (eyes closed for extended period)   | Visual + Audio |

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Main Window (GUI)                     │
│                          (PyQt5)                             │
└───────────────────────┬─────────────────────────────────────┘
                        │ Signals/Slots
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Detection Engine (QThread)                 │
│  ┌────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │   Camera   │→ │ Face        │→ │ Metrics            │  │
│  │   Input    │  │ Detector    │  │ Processor          │  │
│  └────────────┘  └─────────────┘  └────────────────────┘  │
│                          ↓                                   │
│  ┌────────────┐  ┌─────────────┐  ┌────────────────────┐  │
│  │  Learning  │  │   Alert     │  │   Config           │  │
│  │  Engine    │  │   System    │  │   Manager          │  │
│  └────────────┘  └─────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **MainWindow** (`interface/main_window.py`)
   - PyQt5 GUI with control panel and video display
   - Receives signals from DetectionEngine
   - Displays metrics and status

2. **DetectionEngine** (`core/detection_engine.py`)
   - Runs in separate QThread
   - Captures and processes video frames
   - Orchestrates all detection logic
   - Emits signals to GUI

3. **FaceDetector** (`detection/face_detector.py`)
   - Uses MediaPipe Face Mesh
   - Detects 468 facial landmarks
   - Extracts eye and mouth coordinates

4. **MetricsProcessor** (`detection/metrics_processor.py`)
   - Calculates EAR (Eye Aspect Ratio)
   - Calculates MAR (Mouth Aspect Ratio)
   - Tracks blinks, yawns, and time patterns
   - Determines drowsiness and fatigue states

5. **AlertSystem** (`alert/alert_system.py`)
   - Manages audio alerts (pygame)
   - Determines alert level
   - Controls alert color coding

6. **LearningEngine** (`learning/learning_engine.py`)
   - Continuous learning to adapt thresholds
   - Collects samples during normal operation
   - Adjusts EAR/MAR thresholds for individual users

---

## Detection Flow & Logic

### Main Processing Loop

```
START
  ↓
[1] Capture Frame from Camera
  ↓
[2] Detect Face with MediaPipe
  ↓
  Face Detected? ──No──→ Display "No face detected"
  ↓ Yes                         ↑
[3] Extract Landmarks            │
  ↓                              │
[4] Calculate Metrics            │
    - EAR (Eyes)                 │
    - MAR (Mouth)                │
  ↓                              │
[5] Detect States                │
    - Blinks                     │
    - Yawns                      │
    - Drowsiness                 │
    - Fatigue                    │
  ↓                              │
[6] Determine Alert Level        │
    - Fatigue > Drowsy > Normal  │
  ↓                              │
[7] Update GUI & Alerts          │
  ↓                              │
  Loop ─────────────────────────┘
```

### Detection Priority

The system follows this priority order:

1. **Fatigue Detection** (Highest Priority)
   - If fatigue detected → YELLOW alert
2. **Drowsiness Detection**
   - If not fatigued but drowsy → RED alert
3. **Normal State**
   - If neither fatigued nor drowsy → GREEN (normal)

---

## Detection Algorithms

### 1. Eye Aspect Ratio (EAR)

**Purpose**: Detect when eyes are closed (drowsiness)

**Formula**:

```
EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)

Where p1-p6 are the 6 landmarks of each eye:
  p2 --------- p3
p1                p4
  p6 --------- p5
```

**Detection Logic**:

```python
if EAR < threshold (default: 0.26):
    eye_closed_counter += 1
    if eye_closed_counter >= 20 frames:
        → DROWSY detected
else:
    eye_closed_counter = 0
```

**Characteristics**:

- **Open eyes**: EAR ≈ 0.3 - 0.4
- **Closed eyes**: EAR < 0.25
- **Drowsy state**: EAR < 0.26 for 20+ consecutive frames

### 2. Mouth Aspect Ratio (MAR)

**Purpose**: Detect yawning

**Formula**:

```
MAR = (||p3 - p9|| + ||p4 - p8|| + ||p5 - p7||) / (3 * ||p1 - p2||)

Where:
- p1, p2 = left and right mouth corners
- p3-p9 = vertical measurements at 3 positions
```

**Detection Logic**:

```python
if MAR > threshold (default: 0.6):
    yawn_counter += 1
    if yawn_counter >= 20 frames:
        yawn_detected = True
        record_yawn_timestamp()
else:
    yawn_counter = 0
```

**Characteristics**:

- **Closed mouth**: MAR ≈ 0.1 - 0.3
- **Open mouth**: MAR ≈ 0.4 - 0.5
- **Yawning**: MAR > 0.6 for 20+ frames

### 3. Blink Detection

**Purpose**: Track blink rate for fatigue detection

**Algorithm**:

```python
# State machine approach
if current_EAR < threshold and previous_EAR >= threshold:
    # Eye closing detected
    is_blinking = True

elif current_EAR >= threshold and is_blinking:
    # Eye opening detected - complete blink
    is_blinking = False
    blink_count += 1
    record_blink_timestamp()
```

**Normal Blink Rate**: 10-20 blinks per minute

### 4. Fatigue Detection

**Purpose**: Detect tiredness over time based on yawns and abnormal blinking

**Algorithm** (60-second monitoring):

```python
# Count yawns and blinks in last 60 seconds
recent_yawns = count_yawns_in_last_60_seconds()
recent_blinks = count_blinks_in_last_60_seconds()

# Conditions
has_multiple_yawns = recent_yawns >= 2
abnormal_blink = (recent_blinks < 10) OR (recent_blinks >= 20)
is_fatigue = has_multiple_yawns AND abnormal_blink

# Monitoring state machine
if NOT monitoring AND is_fatigue:
    start_monitoring()
    start_time = current_time

if monitoring:
    elapsed = current_time - start_time

    if elapsed < 60:
        continue_monitoring()  # Keep tracking

    elif elapsed >= 60 AND is_fatigue:
        → FATIGUE ALERT (YELLOW)
    else:
        reset_monitoring()
```

**Fatigue Conditions**:

1. **Yawns**: ≥ 2 times in 60 seconds
2. **Abnormal Blinks**: Either
   - Too few: < 10 blinks/min (sign of drowsiness)
   - Too many: ≥ 20 blinks/min (sign of eye strain/fatigue)
3. **Duration**: Both conditions must persist for 60 seconds

**Why 60 seconds?**

- Prevents false positives from temporary yawns or eye movements
- Confirms persistent fatigue pattern
- Gives driver time to recover naturally

### 5. Drowsiness Detection

**Purpose**: Detect immediate drowsiness (eyes closing)

**Algorithm**:

```python
# Only check if NOT yawning and NOT fatigued
if NOT mouth_wide_open AND NOT is_fatigued:
    if EAR < ear_threshold:
        ear_counter += 1
        if ear_counter >= 20:
            → DROWSY ALERT (RED) + AUDIO
    else:
        ear_counter = 0
```

**Why exclude yawning?**

- Eyes naturally close during yawning
- Prevents false drowsy alerts when yawning

---

## Project Structure

```
project1/
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
│
├── config/
│   └── settings.json                # Configuration (auto-generated)
│
├── data/
│   └── alarm.wav                    # Alert sound file
│
└── src/
    ├── __init__.py
    │
    ├── config/
    │   ├── __init__.py
    │   └── config_manager.py        # JSON config manager
    │
    ├── detection/
    │   ├── __init__.py
    │   ├── face_detector.py         # MediaPipe face detection
    │   └── metrics_processor.py     # EAR/MAR calculations
    │
    ├── alert/
    │   ├── __init__.py
    │   └── alert_system.py          # Audio/visual alerts
    │
    ├── core/
    │   ├── __init__.py
    │   └── detection_engine.py      # Main processing engine
    │
    ├── learning/
    │   ├── __init__.py
    │   └── learning_engine.py       # Adaptive learning
    │
    └── interface/
        ├── __init__.py
        └── main_window.py           # PyQt5 GUI
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Webcam
- Windows/Linux/MacOS

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages**:

- opencv-python
- mediapipe
- numpy
- PyQt5
- pygame

---

## Configuration

Default configuration in `config/settings.json`:

```json
{
  "thresholds": {
    "ear": 0.262, // Eye Aspect Ratio threshold
    "mar": 0.594, // Mouth Aspect Ratio threshold
    "blink": 0.25, // Blink detection threshold
    "yawn": 0.6 // Yawn detection threshold
  },
  "consecutive_frames": {
    "drowsiness": 20, // Frames for drowsy detection
    "yawn": 15, // Frames for yawn detection
    "blink": 3 // Frames for blink detection
  },
  "fatigue_detection": {
    "blink_per_minute": 15, // Normal blink rate
    "yawn_per_minute": 3 // Fatigue yawn threshold
  },
  "learning": {
    "samples": 100, // Samples for learning
    "weight": 0.3 // Learning weight
  },
  "camera": {
    "index": 0, // Camera device index
    "width": 640, // Frame width
    "height": 480, // Frame height
    "fps": 30 // Target FPS
  }
}
```

---

## Usage

### Run the Application

```bash
python main.py
```

### GUI Controls

1. **START**: Begin detection
2. **STOP**: Stop detection
3. **RESET & RELEARN**: Clear learned data and restart learning
4. **HIDE/SHOW LANDMARKS**: Toggle facial mesh visualization

### Metrics Display

- **EAR**: Current Eye Aspect Ratio
- **MAR**: Current Mouth Aspect Ratio
- **Blinks/min**: Blink rate
- **Yawns/min**: Yawn count
- **Thresholds**: Current detection thresholds

---

## System Flow Diagram

### Complete Detection Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                    Camera Input (30 FPS)                      │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│              Face Detection (MediaPipe)                       │
│  • 468 facial landmarks                                       │
│  • Extract eyes (12 points) and mouth (8 points)             │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                  Metrics Calculation                          │
│  ┌─────────────────┐           ┌─────────────────┐          │
│  │  Calculate EAR  │           │  Calculate MAR  │          │
│  │  (Eyes)         │           │  (Mouth)        │          │
│  └────────┬────────┘           └────────┬────────┘          │
│           │                              │                    │
│           ├──→ Smoothing (5 frames) ←───┤                   │
│           │                              │                    │
│           ↓                              ↓                    │
│  ┌─────────────────┐           ┌─────────────────┐          │
│  │  Blink          │           │  Yawn           │          │
│  │  Detection      │           │  Detection      │          │
│  └────────┬────────┘           └────────┬────────┘          │
└───────────┼─────────────────────────────┼───────────────────┘
            │                              │
            ↓                              ↓
┌──────────────────────────────────────────────────────────────┐
│              State Detection & Time Tracking                  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Drowsiness Check                                       │ │
│  │  • EAR < 0.26 for 20 frames?                           │ │
│  │  • Mouth NOT wide open?                                │ │
│  │  • NOT in fatigue state?                               │ │
│  │  → YES: DROWSY STATE (RED + AUDIO)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Fatigue Check (60-second window)                      │ │
│  │  • Count yawns in last 60s                             │ │
│  │  • Count blinks in last 60s                            │ │
│  │  • Yawns >= 2 AND (blinks < 10 OR blinks >= 20)?      │ │
│  │                                                         │ │
│  │  NOT monitoring AND conditions met:                    │ │
│  │    → Start 60s countdown                               │ │
│  │                                                         │ │
│  │  Monitoring AND elapsed >= 60s AND still fatigued:     │ │
│  │    → FATIGUE STATE (YELLOW)                            │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                    Alert Priority Logic                       │
│                                                               │
│  IF Fatigue Detected:                                        │
│    → Set FATIGUE level (Yellow, no audio)                   │
│  ELIF Drowsy Detected:                                       │
│    → Set DROWSY level (Red + audio alarm)                   │
│  ELSE:                                                        │
│    → Set NONE level (Green, normal)                         │
└────────────────────────┬─────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                     GUI Update                                │
│  • Display video with landmarks                              │
│  • Update status label with color                            │
│  • Show metrics (EAR, MAR, blinks, yawns)                   │
│  • Draw alert box on frame                                   │
└──────────────────────────────────────────────────────────────┘
```

### State Machine Diagram

```
                    ┌──────────┐
                    │  NORMAL  │ (Green)
                    │  (NONE)  │
                    └────┬─────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ↓               ↓               ↓
  Yawns ≥ 2    Eyes closed      Both conditions
  + abnormal   for 20 frames     met together
  blinking
         │               │               │
         ↓               ↓               │
    ┌─────────┐    ┌──────────┐        │
    │ Start   │    │  DROWSY  │←───────┘
    │ 60s     │    │  (RED)   │  (Priority: Fatigue > Drowsy)
    │ Monitor │    │ + Audio  │
    └────┬────┘    └──────────┘
         │               ↑
         │ Wait 60s      │ Eyes open
         ↓               │
    ┌─────────┐         │
    │ FATIGUE │─────────┘
    │ (YELLOW)│  Recover
    └─────────┘
         ↑
         │ Conditions persist
         └────────────────┐
                          │
           Yawns < 2 OR   │
           blinks normal  │
                  └───────┘
```

### Learning Engine Flow

```
┌──────────────────────────────────────────┐
│     Continuous Learning Process          │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Sample Collection (during operation)    │
│  • Collect when eyes open (0.20 < EAR)  │
│  • Good detection quality (>75%)         │
│  • Not too high (EAR < threshold + 0.08) │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Calculate Statistics                    │
│  • Mean EAR                              │
│  • Mean MAR                              │
│  • Standard deviation                    │
└────────────────┬─────────────────────────┘
                 ↓
┌──────────────────────────────────────────┐
│  Adaptive Threshold Update               │
│  • New = Old * (1-w) + Learned * w       │
│  • Weight w = 0.3                        │
│  • Prevents drastic changes              │
└──────────────────────────────────────────┘
```

---

## Troubleshooting

### No Face Detected

- Ensure good lighting
- Position face clearly in camera view
- Check camera permissions

### High False Positive Rate

- Run RESET & RELEARN for 2-3 minutes
- Adjust thresholds in settings.json
- Ensure stable camera position

### Audio Not Working

- Check alarm.wav exists in data/ folder
- Verify audio device is working
- Check volume settings

---

## Technical Details

### Performance

- **Processing Speed**: ~30 FPS on modern hardware
- **Latency**: < 50ms per frame
- **CPU Usage**: 15-25% (Intel i5 or equivalent)
- **Memory**: ~200-300 MB

### Thread Architecture

- **Main Thread**: GUI rendering and user interaction
- **Worker Thread** (QThread): Video processing and detection
- **Communication**: Qt Signals/Slots (thread-safe)

---

## Future Enhancements

- [ ] Head pose estimation for distraction detection
- [ ] Integration with vehicle systems (CAN bus)
- [ ] Mobile app support
- [ ] Cloud-based analytics dashboard
- [ ] Multiple camera support
- [ ] Personalized alerting profiles

---

## License

This project is for educational and research purposes.

---

## Credits

- **MediaPipe**: Google's face mesh solution
- **OpenCV**: Computer vision library
- **PyQt5**: GUI framework
- **Pygame**: Audio playback

---

## Contact & Support

For questions or issues, please refer to the project documentation or create an issue in the repository.

- **Phát hiện nhấp mắt**: Đếm số lần nhấp mắt để đánh giá mức độ mệt mỏi
- **Phát hiện mệt mỏi**: Theo dõi tần suất nhấp mắt và ngáp

### Cảnh báo

- **Cảnh báo đỏ (Ngủ gật)**:
  - Phát âm thanh cảnh báo liên tục
  - Hiển thị viền đỏ và text cảnh báo lớn
  - Tự động tắt khi mở mắt trở lại

- **Cảnh báo vàng (Mệt mỏi)**:
  - Hiển thị viền vàng khi phát hiện mệt mỏi
  - Không phát âm thanh
  - Dựa trên tần suất nhấp mắt và ngáp

### Học ngưỡng

- Cơ chế học ngưỡng tự động để cá nhân hóa
- Sử dụng cấu hình mặc định khi khởi động lần đầu
- Người dùng có thể chủ động học ngưỡng mới
- Tự động cập nhật và lưu cấu hình

### Giao diện

- **Khung camera**: Hiển thị video từ webcam với các chỉ số
- **Sidebar điều khiển**:
  - Hiển thị trạng thái hệ thống
  - Nút Bắt đầu/Dừng lại
  - Nút Học ngưỡng
  - Nút Bật/Tắt lưới landmark
  - Hiển thị các chỉ số EAR, MAR, nhấp mắt, ngáp

- **Chỉ số hiển thị**:
  - FPS (Frames Per Second)
  - EAR và MAR hiện tại
  - Ngưỡng EAR và MAR
  - Tần suất nhấp mắt và ngáp

## Cài đặt

### Yêu cầu

- Python 3.8 hoặc cao hơn
- Webcam

### Các bước cài đặt

1. Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
```

2. Tạo thư mục `data` và thêm file âm thanh cảnh báo:

```bash
mkdir data
```

Đặt file âm thanh có tên `alert.wav` vào thư mục `data/`

## Sử dụng

### Chạy ứng dụng

```bash
python main.py
```

### Hướng dẫn sử dụng

1. **Khởi động hệ thống**:
   - Nhấn nút "BẮT ĐẦU" để bật camera và bắt đầu phát hiện
   - Hệ thống sẽ sử dụng ngưỡng mặc định hoặc ngưỡng đã học

2. **Học ngưỡng cá nhân**:
   - Nhấn nút "HỌC NGƯỠNG" khi hệ thống đang chạy
   - Giữ trạng thái bình thường (mắt mở, miệng đóng) trong khoảng 10-20 giây
   - Hệ thống sẽ thu thập mẫu và tính toán ngưỡng phù hợp
   - Nhấn lại nút để hoàn thành học
   - Ngưỡng mới sẽ được lưu tự động

3. **Bật/Tắt lưới landmark**:
   - Nhấn nút "ẨN/HIỆN LƯỚI LANDMARK" để bật/tắt hiển thị các điểm landmark trên mặt

4. **Theo dõi trạng thái**:
   - Quan sát màn hình sidebar để xem trạng thái hiện tại
   - Kiểm tra các chỉ số EAR, MAR, nhấp mắt, ngáp
   - Màu xanh: Bình thường
   - Màu vàng: Mệt mỏi
   - Màu đỏ: Ngủ gật (có cảnh báo âm thanh)

5. **Dừng hệ thống**:
   - Nhấn nút "DỪNG LẠI" để tắt camera và dừng phát hiện

## Kiến trúc Module và Giao tiếp

### 1. **Config Module** (`src/config/`)

- `ConfigManager`: Quản lý cấu hình từ file JSON
- Load/Save cấu hình tự động
- Hỗ trợ học ngưỡng và cập nhật

### 2. **Detection Module** (`src/detection/`)

- `FaceDetector`: Phát hiện khuôn mặt và landmarks (MediaPipe)
- `MetricsProcessor`: Tính toán EAR, MAR, phát hiện blink/yawn

### 3. **Alert Module** (`src/alert/`)

- `AlertSystem`: Quản lý cảnh báo âm thanh và hình ảnh
- Hỗ trợ 3 mức: NONE, FATIGUE, DROWSY

### 4. **Core Module** (`src/core/`)

- `DetectionEngine`: QThread xử lý video loop
- Chạy độc lập với GUI thread
- Emit PyQt signals để giao tiếp với interface

### 5. **Interface Module** (`src/interface/`)

- `MainWindow`: Giao diện PyQt5
- Nhận signals từ DetectionEngine
- Cập nhật UI real-time

### Luồng Giao tiếp (Signals)

```
DetectionEngine (QThread)          MainWindow (GUI)
        │                                │
        ├─ frame_processed ────────────→ │ Hiển thị frame
        ├─ metrics_updated ─────────────→ │ Cập nhật metrics
        ├─ status_changed ──────────────→ │ Cập nhật trạng thái
        ├─ alert_changed ───────────────→ │ Xử lý alert
        ├─ learning_progress ───────────→ │ Hiển thị tiến độ
        └─ error_occurred ──────────────→ │ Hiển thị lỗi
```

## Cấu hình (config/settings.json)

File JSON được tự động tạo với cấu trúc:

```json
{
  "thresholds": {
    "ear": 0.25,
    "mar": 0.6,
    "blink": 0.25,
    "yawn": 0.6
  },
  "consecutive_frames": {
    "drowsiness": 20,
    "yawn": 15,
    "blink": 3
  },
  "fatigue_detection": {
    "blink_per_minute": 15,
    "yawn_per_minute": 3
  },
  "learning": {
    "samples": 100,
    "weight": 0.3
  },
  "camera": {
    "index": 0,
    "width": 640,
    "height": 480,
    "fps": 30
  },
  "alert": {
    "sound_file": "data/alert.wav"
  },
  "display": {
    "show_landmarks": true,
    "show_fps": true
  }
}
```

## Công nghệ sử dụng

- **OpenCV**: Xử lý video và hình ảnh
- **MediaPipe**: Phát hiện khuôn mặt và landmark
- **PyQt5**: Giao diện đồ họa
- **Pygame**: Phát âm thanh cảnh báo
- **NumPy**: Tính toán số học
