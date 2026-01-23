# Analyzers Module

Thư mục này chứa các module phân tích cho hệ thống phát hiện buồn ngủ.

## Cấu trúc

```
analyzers/
├── __init__.py              # Export tất cả các class
├── thresholds.py            # DrowsinessThresholds - Các ngưỡng phát hiện
├── signal_stabilizer.py     # SignalStabilizer - Ổn định tín hiệu
├── metrics.py               # Các hàm tính toán EAR, MAR
├── perclos_calculator.py    # PERCLOSCalculator - Tính PERCLOS
├── blink_analyzer.py        # BlinkAnalyzer - Phân tích nháy mắt
├── yawn_analyzer.py         # YawnAnalyzer - Phân tích ngáp
├── head_pose_analyzer.py    # HeadPoseAnalyzer - Phân tích tư thế đầu
├── sleep_detector.py        # SleepDetector & SleepEvent - Phát hiện ngủ gật
├── fatigue_state.py         # FatigueState - Trạng thái mệt mỏi
└── calibration.py           # PersonalCalibration & SmartThreshold - Hiệu chuẩn
```

## Sử dụng

```python
from src.core.analyzers import (
    DrowsinessThresholds,
    SignalStabilizer,
    PERCLOSCalculator,
    BlinkAnalyzer,
    YawnAnalyzer,
    HeadPoseAnalyzer,
    SleepDetector,
    FatigueState,
    PersonalCalibration,
    SmartThreshold,
    calculate_ear,
    calculate_mar,
)
```

## Mục đích

Tách code thành các module nhỏ giúp:

- ✅ Dễ quản lý và bảo trì
- ✅ Dễ test từng phần
- ✅ Code rõ ràng hơn
- ✅ Tránh file quá dài (processor.py trước đây 2100+ dòng)
