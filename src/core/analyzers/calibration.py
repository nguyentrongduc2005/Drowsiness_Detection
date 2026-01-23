"""
Calibration Module - Personal calibration and smart threshold learning
"""
import numpy as np
import json
import os
import time
import datetime
from collections import deque
from typing import Tuple
from ..config import Config


class PersonalCalibration:
    """Learn personal EAR/MAR thresholds with improved accuracy"""
    
    CALIBRATION_FILE = "data/calibration.json"
    
    STATE_IDLE = "idle"
    STATE_OPEN_EYES = "open_eyes"
    STATE_CLOSED_EYES = "closed_eyes"
    STATE_YAWNING = "yawning"
    STATE_COMPLETED = "completed"
    
    def __init__(self):
        self.calibration_state = self.STATE_IDLE
        self.samples_needed = 60  # More samples for better accuracy
        
        self.open_eyes_samples = []
        self.closed_eyes_samples = []
        self.yawning_samples = []
        
        self.learned_thresholds = {
            'ear_open': None, 'ear_closed': None, 'ear_threshold': None,
            'ear_open_min': None, 'ear_closed_max': None,
            'mar_normal': None, 'mar_yawn': None, 'mar_threshold': None,
            'calibrated': False, 'calibration_date': None
        }
        
        self._load_calibration()
    
    def _filter_outliers(self, samples: list) -> list:
        """Remove outliers using IQR method for more accurate calibration"""
        if len(samples) < 10:
            return samples
        arr = np.array(samples)
        q1, q3 = np.percentile(arr, [25, 75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        filtered = [x for x in samples if lower <= x <= upper]
        return filtered if len(filtered) >= 10 else samples
    
    def _load_calibration(self):
        try:
            if os.path.exists(self.CALIBRATION_FILE):
                with open(self.CALIBRATION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.learned_thresholds = data
                    if data.get('calibrated', False):
                        self.calibration_state = self.STATE_COMPLETED
                        print(f"[OK] Loaded calibration (EAR: {data['ear_threshold']:.3f})")
        except Exception as e:
            print(f"Cannot load calibration: {e}")
    
    def _save_calibration(self):
        try:
            os.makedirs(os.path.dirname(self.CALIBRATION_FILE), exist_ok=True)
            with open(self.CALIBRATION_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.learned_thresholds, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def start_calibration(self):
        self.calibration_state = self.STATE_OPEN_EYES
        self.open_eyes_samples = []
        self.closed_eyes_samples = []
        self.yawning_samples = []
        print("[CALIB] Step 1: Keep eyes open naturally")
    
    def next_state(self):
        if self.calibration_state == self.STATE_OPEN_EYES:
            self.calibration_state = self.STATE_CLOSED_EYES
            print("[CALIB] Step 2: Close eyes gently")
        elif self.calibration_state == self.STATE_CLOSED_EYES:
            self.calibration_state = self.STATE_YAWNING
            print("[CALIB] Step 3: Yawn/open mouth wide (KEEP EYES OPEN!)")
        elif self.calibration_state == self.STATE_YAWNING:
            self._calculate_thresholds()
            self.calibration_state = self.STATE_COMPLETED
            print("[OK] Calibration completed!")
    
    def add_sample(self, ear: float, mar: float):
        if self.calibration_state == self.STATE_OPEN_EYES:
            if ear > 0.15:
                self.open_eyes_samples.append(ear)
            progress = len(self.open_eyes_samples)
            return progress, self.samples_needed, progress >= self.samples_needed
            
        elif self.calibration_state == self.STATE_CLOSED_EYES:
            if ear < 0.25:
                self.closed_eyes_samples.append(ear)
            progress = len(self.closed_eyes_samples)
            return progress, self.samples_needed, progress >= self.samples_needed
            
        elif self.calibration_state == self.STATE_YAWNING:
            if mar > 0.3 and ear > 0.2:
                self.yawning_samples.append(mar)
            progress = len(self.yawning_samples)
            return progress, self.samples_needed, progress >= self.samples_needed
        
        return 0, self.samples_needed, False
    
    def _calculate_thresholds(self):
        # Filter outliers for more accurate calibration
        open_filtered = self._filter_outliers(self.open_eyes_samples)
        closed_filtered = self._filter_outliers(self.closed_eyes_samples)
        
        if open_filtered:
            self.learned_thresholds['ear_open'] = np.mean(open_filtered)
            self.learned_thresholds['ear_open_min'] = np.min(open_filtered)
        
        if closed_filtered:
            self.learned_thresholds['ear_closed'] = np.mean(closed_filtered)
            self.learned_thresholds['ear_closed_max'] = np.max(closed_filtered)
        
        if self.learned_thresholds['ear_open'] and self.learned_thresholds['ear_closed']:
            ear_open = self.learned_thresholds['ear_open']
            ear_closed = self.learned_thresholds['ear_closed']
            ear_open_min = self.learned_thresholds.get('ear_open_min', ear_open * 0.9)
            ear_closed_max = self.learned_thresholds.get('ear_closed_max', ear_closed * 1.1)
            
            base_threshold = ear_closed + 0.35 * (ear_open - ear_closed)
            safe_threshold = min(base_threshold, ear_open_min * 0.85)
            safe_threshold = max(safe_threshold, ear_closed_max * 1.1)
            
            self.learned_thresholds['ear_threshold'] = safe_threshold
        
        if self.yawning_samples:
            yawn_filtered = self._filter_outliers(self.yawning_samples)
            self.learned_thresholds['mar_yawn'] = np.mean(yawn_filtered)
            self.learned_thresholds['mar_threshold'] = self.learned_thresholds['mar_yawn'] * 0.55
        
        self.learned_thresholds['calibrated'] = True
        self.learned_thresholds['calibration_date'] = datetime.datetime.now().isoformat()
        self._save_calibration()
        
        print(f"  EAR open: {self.learned_thresholds['ear_open']:.3f}")
        print(f"  EAR closed: {self.learned_thresholds['ear_closed']:.3f}")
        print(f"  EAR threshold: {self.learned_thresholds['ear_threshold']:.3f}")
    
    def get_thresholds(self):
        return self.learned_thresholds
    
    def is_calibrated(self):
        return self.learned_thresholds.get('calibrated', False)
    
    def get_state(self):
        return self.calibration_state
    
    def get_state_text(self):
        states = {
            self.STATE_IDLE: "Not calibrated",
            self.STATE_OPEN_EYES: "Keep eyes open...",
            self.STATE_CLOSED_EYES: "Close eyes gently...",
            self.STATE_YAWNING: "Yawn with EYES OPEN...",
            self.STATE_COMPLETED: "Calibrated"
        }
        return states.get(self.calibration_state, "")
    
    def reset(self):
        self.calibration_state = self.STATE_IDLE
        self.open_eyes_samples = []
        self.closed_eyes_samples = []
        self.yawning_samples = []
        self.learned_thresholds = {
            'ear_open': None, 'ear_closed': None, 'ear_threshold': None,
            'mar_normal': None, 'mar_yawn': None, 'mar_threshold': None,
            'calibrated': False, 'calibration_date': None
        }
        if os.path.exists(self.CALIBRATION_FILE):
            os.remove(self.CALIBRATION_FILE)
        print("[OK] Calibration reset")


class SmartThreshold:
    """
    Adaptive threshold with ROBUST learning - Anti Data Poisoning
    
    Improvements:
    1. State-Based Gating: Chỉ học khi trạng thái bình thường
    2. Sanity Check: Giới hạn sinh học con người
    3. Median-based: Chống nhiễu outliers
    
    Ngăn chặn:
    - Học khi đang ngáp (MAR cao)
    - Học khi đang nhắm mắt (EAR thấp)
    - Học giá trị vô lý (ngoài phạm vi sinh học)
    """
    
    # BIOLOGICAL LIMITS - Giới hạn sinh học con người
    EAR_MIN_VALID = 0.20
    EAR_MAX_VALID = 0.45
    EAR_SAFE_ZONE_MIN = 0.23
    
    MAR_SAFE_ZONE_MAX = 0.35
    
    # LEARNING PARAMETERS
    OUTLIER_THRESHOLD = 0.08
    MIN_STABILITY_FRAMES = 30
    
    def __init__(self, config=None, personal_calibration=None):
        if config is None:
            config = Config()
        
        self.config = config
        self.personal_calibration = personal_calibration
        self.window_size = 200
        
        self.ear_history = deque(maxlen=self.window_size)
        
        self.current_state = 'unknown'
        self.stable_frames = 0
        
        self.default_threshold = config.get_ear_default()
        self.min_samples = max(50, config.get_min_samples())
        
        self.cached_threshold = self.default_threshold
        self.last_update_time = time.time()
        
        print("[SmartThreshold] Initialized with ROBUST learning")
        print(f"  - Safe zone: EAR {self.EAR_SAFE_ZONE_MIN:.2f} - {self.EAR_MAX_VALID:.2f}")
        print(f"  - MAR limit: {self.MAR_SAFE_ZONE_MAX:.2f}")
        print(f"  - Outlier rejection: ±{self.OUTLIER_THRESHOLD*100:.0f}%")
    
    def _is_valid_sample(self, ear: float, mar: float = 0.0) -> bool:
        """Kiểm tra xem sample có hợp lệ để học không"""
        if not (self.EAR_MIN_VALID <= ear <= self.EAR_MAX_VALID):
            return False
        
        if mar > self.MAR_SAFE_ZONE_MAX:
            return False
        
        if ear < self.EAR_SAFE_ZONE_MIN:
            return False
        
        if len(self.ear_history) >= self.MIN_STABILITY_FRAMES:
            current_median = np.median(list(self.ear_history))
            deviation = abs(ear - current_median) / current_median
            
            if deviation > self.OUTLIER_THRESHOLD:
                return False
        
        return True
    
    def update_threshold(self, current_ear: float, current_mar: float = 0.0, 
                        is_yawning: bool = False, is_drowsy: bool = False) -> Tuple[float, bool]:
        """Update threshold với ROBUST learning"""
        # PRIORITY 1: Calibrated threshold
        if self.personal_calibration and self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            if thresholds.get('ear_threshold'):
                return thresholds['ear_threshold'], True
        
        # BLOCKING: Đừng học khi đang có sự kiện bất thường
        if is_yawning or is_drowsy:
            return self.cached_threshold, len(self.ear_history) >= self.min_samples
        
        # VALIDATION: Kiểm tra sample có hợp lệ không
        if not self._is_valid_sample(current_ear, current_mar):
            return self.cached_threshold, len(self.ear_history) >= self.min_samples
        
        # ACCEPT: Sample hợp lệ → Thêm vào history
        self.ear_history.append(current_ear)
        self.stable_frames += 1
        
        # Chưa đủ dữ liệu → Dùng default
        if len(self.ear_history) < self.min_samples:
            return self.default_threshold, False
        
        # ROBUST CALCULATION - Dùng MEDIAN thay vì MEAN
        median_ear = np.median(list(self.ear_history))
        
        # Lấy top 60% giá trị cao nhất
        sorted_history = sorted(self.ear_history, reverse=True)
        top_60_percent = sorted_history[:int(len(sorted_history) * 0.6)]
        
        robust_baseline = np.median(top_60_percent)
        
        adaptive_threshold = robust_baseline * 0.70
        
        # Safety bounds
        MIN_THRESHOLD = 0.18
        MAX_THRESHOLD = 0.28
        adaptive_threshold = max(MIN_THRESHOLD, min(MAX_THRESHOLD, adaptive_threshold))
        
        # Update cached threshold (mỗi 2 giây)
        current_time = time.time()
        if current_time - self.last_update_time > 2.0:
            self.cached_threshold = adaptive_threshold
            self.last_update_time = current_time
            
            if self.stable_frames % 100 == 0:
                print(f"[SmartThreshold] Updated: {adaptive_threshold:.3f} "
                      f"(median={median_ear:.3f}, baseline={robust_baseline:.3f}, "
                      f"samples={len(self.ear_history)})")
        
        return adaptive_threshold, True
    
    def get_status_text(self):
        """Get current status text for UI"""
        if self.personal_calibration:
            state = self.personal_calibration.get_state()
            if state == PersonalCalibration.STATE_COMPLETED:
                return "Calibrated"
            elif state != PersonalCalibration.STATE_IDLE:
                return self.personal_calibration.get_state_text()
        
        if len(self.ear_history) < self.min_samples:
            return f"Learning: {len(self.ear_history)}/{self.min_samples}"
        
        return f"Active (robust, {len(self.ear_history)} samples)"
    
    def get_learning_stats(self) -> dict:
        """Get detailed learning statistics"""
        if len(self.ear_history) == 0:
            return {
                'samples': 0,
                'median': 0.0,
                'mean': 0.0,
                'std': 0.0,
                'min': 0.0,
                'max': 0.0
            }
        
        history_array = np.array(list(self.ear_history))
        return {
            'samples': len(self.ear_history),
            'median': float(np.median(history_array)),
            'mean': float(np.mean(history_array)),
            'std': float(np.std(history_array)),
            'min': float(np.min(history_array)),
            'max': float(np.max(history_array)),
            'stable_frames': self.stable_frames
        }
    
    def reset(self):
        """Reset learning history"""
        self.ear_history.clear()
        self.stable_frames = 0
        self.cached_threshold = self.default_threshold
        print("[SmartThreshold] Reset - cleared learning history")
