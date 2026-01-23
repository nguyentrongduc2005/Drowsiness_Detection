# Config Files Overview

```
Drowsiness_Detection/
│
├── 📁 data/
│   ├── 📄 config.json ✅ ĐANG DÙNG
│   │   ├── eye_thresholds (13 settings)
│   │   ├── mouth_thresholds (6 settings)
│   │   ├── perclos_thresholds (4 settings)
│   │   ├── head_pose_thresholds (6 settings)
│   │   ├── blink_rate_thresholds (5 settings)
│   │   ├── fatigue_thresholds (3 settings)
│   │   ├── smart_threshold (3 settings)
│   │   ├── detection_settings (6 settings)
│   │   ├── paths (2 settings)
│   │   └── settings (4 settings)
│   │   → TOTAL: 52 configurable parameters
│   │
│   └── 📄 calibration.json ✅ ĐANG DÙNG
│       └── Personal thresholds (auto-generated)
│
├── 📄 pyrightconfig.json ✅ ĐANG DÙNG
│   └── Python type checker config (VS Code)
│
└── 📁 src/core/
    ├── config.py (Load config.json)
    ├── processor.py (Use config)
    ├── detector.py (Use config)
    └── analyzers/
        ├── thresholds.py (Load from config)
        └── calibration.py (Use calibration.json)
```

## Config Usage Flow

```
┌─────────────────────┐
│  data/config.json   │
│  (52 parameters)    │
└──────────┬──────────┘
           │ loads
           ↓
┌─────────────────────┐
│  src/core/config.py │
│  (Config class)     │
└──────────┬──────────┘
           │ used by
           ├─────────────────────┐
           ↓                     ↓
┌─────────────────────┐  ┌──────────────────────┐
│  DrowsinessThresholds│  │  FaceDetector       │
│  (43 thresholds)    │  │  (6 settings)       │
└──────────┬──────────┘  └──────────┬───────────┘
           │                        │
           └────────┬───────────────┘
                    ↓
         ┌─────────────────────┐
         │ DrowsinessDetector  │
         │ (Main logic)        │
         └─────────────────────┘
```

## Before vs After Refactoring

### ❌ Before (Hardcoded)

```python
# thresholds.py
class DrowsinessThresholds:
    BLINK_MAX = 0.4           # ← Hardcoded
    MICROSLEEP_MIN = 0.5      # ← Hardcoded
    EYE_CLOSED_WARNING = 1.5  # ← Hardcoded
    # ... 40+ more hardcoded values

# detector.py
self.smoothing_window = 3     # ← Hardcoded
self.target_brightness = 130  # ← Hardcoded

# Problems:
# - Must edit Python code to change
# - Need to restart app
# - Hard to customize per user
```

### ✅ After (Config-driven)

```python
# thresholds.py
class DrowsinessThresholds:
    BLINK_MAX = None  # ← Load from config
    # Auto-loads from config.json on first access

# detector.py
config = Config()
self.smoothing_window = config.get(
    'detection_settings.smoothing_window', 3
)

# Benefits:
# ✓ Edit JSON file to change
# ✓ Can reload without restart
# ✓ Easy to customize
# ✓ Multiple profiles possible
```

## Configuration Hierarchy

```
1. config.json (Default values)
        ↓
2. Config class (Loads + validates)
        ↓
3. DrowsinessThresholds (Lazy load on access)
        ↓
4. Application code (Uses thresholds)
```

## Example: Changing Eye Closed Warning

### Method 1: Edit config.json

```json
{
  "eye_thresholds": {
    "eye_closed_warning": 2.0 // Change from 1.5 to 2.0
  }
}
```

Then restart app.

### Method 2: Different profiles

```bash
# config_sensitive.json (Early warning)
"eye_closed_warning": 1.0

# config_normal.json (Default)
"eye_closed_warning": 1.5

# config_relaxed.json (Late warning)
"eye_closed_warning": 2.5
```

Load different configs for different users!

## Summary

| Config File             | Purpose             | Status   | Parameters |
| ----------------------- | ------------------- | -------- | ---------- |
| `data/config.json`      | System settings     | ✅ Using | 52         |
| `data/calibration.json` | Personal thresholds | ✅ Using | 10         |
| `pyrightconfig.json`    | Type checker        | ✅ Using | 8          |
| **TOTAL**               |                     |          | **70**     |

**Result:**

- ✅ All config files are in use
- ✅ No unused config files to delete
- ✅ 43 hardcoded values moved to config
- ✅ System is now fully configurable

**Documentation:**

- 📖 [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - Detailed guide
- 📊 [CONFIG_REFACTORING_SUMMARY.md](CONFIG_REFACTORING_SUMMARY.md) - Changes summary
