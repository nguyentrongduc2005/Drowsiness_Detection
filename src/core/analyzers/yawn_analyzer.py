"""
Yawn Analyzer - Distinguish yawn from talking/singing
"""
import numpy as np
import time
from collections import deque
from .thresholds import DrowsinessThresholds


class YawnAnalyzer:
    """
    Analyze yawning with variance check to distinguish from talking/singing.
    
    Real yawn characteristics:
    - MAR increases, stays high, then decreases slowly
    - Low MAR variance during the yawn
    - EAR often decreases slightly (eyes squint during yawn)
    
    Talking/singing characteristics:
    - MAR changes rapidly and frequently
    - High MAR variance
    - EAR stays normal
    """
    
    def __init__(self, window_size: int = 30):
        self.mar_history = deque(maxlen=window_size)
        self.ear_history = deque(maxlen=window_size)
        self.yawn_start_time = None
        self.yawn_start_ear = None
        self.is_yawning = False
        self.current_yawn_is_real = False  # Track nếu yawn hiện tại đã được confirm là real
        self.yawn_count = 0
        self.yawn_timestamps = deque(maxlen=100)
        self.last_yawn_time = 0
    
    def update(self, mar: float, ear: float, mar_threshold: float, 
               current_time: float) -> dict:
        """Update yawn detection with variance analysis"""
        self.mar_history.append(mar)
        self.ear_history.append(ear)
        
        result = {
            'is_yawning': False,
            'is_real_yawn': False,
            'yawn_duration': 0.0,
            'mar_variance': 0.0,
            'ear_drop': 0.0,
            'confidence': 0.0,
        }
        
        # Calculate MAR variance
        if len(self.mar_history) >= 10:
            result['mar_variance'] = np.var(list(self.mar_history))
        
        mouth_open = mar > mar_threshold
        
        if mouth_open and not self.is_yawning:
            # Start potential yawn
            self.is_yawning = True
            self.current_yawn_is_real = False  # Reset flag
            self.yawn_start_time = current_time
            self.yawn_start_ear = ear
            
        elif mouth_open and self.is_yawning:
            # Continue yawning
            duration = current_time - self.yawn_start_time
            result['yawn_duration'] = duration
            
            # Check if it's a real yawn - KẾT HỢP điều kiện MAR và EAR
            if duration >= DrowsinessThresholds.YAWN_DURATION_MIN:
                mar_var = result['mar_variance']
                ear_drop = self.yawn_start_ear - ear if self.yawn_start_ear else 0
                result['ear_drop'] = ear_drop
                
                # Real yawn: low variance (không phải nói) HOẶC mắt híp (EAR drop)
                is_low_variance = mar_var < DrowsinessThresholds.YAWN_MAR_VARIANCE_MAX
                has_ear_drop = ear_drop > DrowsinessThresholds.YAWN_EAR_DROP_THRESHOLD
                
                # Calculate confidence
                confidence = 0.0
                if is_low_variance:
                    confidence += 0.5
                if has_ear_drop:
                    confidence += 0.5  # Tăng từ 0.3 -> 0.5 để EAR drop quan trọng hơn
                if duration >= 2.0:  # Long duration = likely yawn
                    confidence += 0.2
                
                result['confidence'] = confidence
                result['is_yawning'] = True
                
                # Yawn thật: Cần ít nhất 1 trong 2 điều kiện (variance thấp HOẶC mắt híp)
                if is_low_variance or has_ear_drop:
                    result['is_real_yawn'] = True
                    if not self.current_yawn_is_real:
                        self.current_yawn_is_real = True
                else:
                    result['is_real_yawn'] = False
                    
        elif not mouth_open and self.is_yawning:
            # End of yawn
            duration = current_time - self.yawn_start_time if self.yawn_start_time else 0
            
            # Nếu yawn này đã được confirm là real (text YAWNING đã hiện) VÀ đủ thời gian
            if self.current_yawn_is_real and duration >= DrowsinessThresholds.YAWN_DURATION_MIN:
                # Đếm vào counter nếu cách lần trước > 3 giây
                time_since_last = current_time - self.last_yawn_time
                if time_since_last > 3:
                    self.yawn_count += 1
                    self.yawn_timestamps.append(current_time)
                    self.last_yawn_time = current_time
            
            # Reset state
            self.is_yawning = False
            self.current_yawn_is_real = False
            self.yawn_start_time = None
            self.yawn_start_ear = None
        
        return result
    
    def get_recent_yawns(self, window_seconds: float = 300) -> int:
        """Get yawn count in recent window"""
        current_time = time.time()
        return len([t for t in self.yawn_timestamps if current_time - t < window_seconds])
    
    def reset(self):
        self.mar_history.clear()
        self.ear_history.clear()
        self.yawn_start_time = None
        self.yawn_start_ear = None
        self.is_yawning = False
        self.current_yawn_is_real = False
        self.yawn_count = 0
        self.yawn_timestamps.clear()
        self.last_yawn_time = 0
