"""
Blink Analyzer - Detect abnormal blink patterns
"""
import numpy as np
import time
from collections import deque
from .thresholds import DrowsinessThresholds


class BlinkAnalyzer:
    """
    Analyze blink patterns for drowsiness detection
    
    Fatigue signs:
    - Slow blinks (long duration)
    - Low blink rate (staring)
    - High blink rate (fighting sleep)
    """
    
    def __init__(self, fps: int = 30):
        self.fps = fps
        self.blinks = deque(maxlen=200)
        self.blink_durations = deque(maxlen=100)
        
        self.in_blink = False
        self.blink_start = None
        self.last_ear = 0.3
        
        self.total_blinks = 0
        self.slow_blinks = 0
        self.start_time = time.time()
        
    def update(self, ear: float, threshold: float, current_time: float) -> dict:
        """Update blink analysis"""
        is_closed = ear < threshold
        
        result = {
            'blink_detected': False,
            'blink_duration': 0.0,
            'is_slow_blink': False,
            'blink_rate': 0.0,
            'avg_blink_duration': 0.0,
            'blink_pattern': 'normal',
        }
        
        if is_closed and not self.in_blink:
            self.in_blink = True
            self.blink_start = current_time
            
        elif not is_closed and self.in_blink:
            self.in_blink = False
            if self.blink_start:
                duration = current_time - self.blink_start
                
                if 0.05 <= duration <= 0.5:
                    self.total_blinks += 1
                    self.blinks.append(current_time)
                    self.blink_durations.append(duration)
                    
                    result['blink_detected'] = True
                    result['blink_duration'] = duration
                    
                    if duration > 0.3:
                        self.slow_blinks += 1
                        result['is_slow_blink'] = True
        
        recent_blinks = [b for b in self.blinks if current_time - b < 60]
        result['blink_rate'] = len(recent_blinks)
        
        if self.blink_durations:
            result['avg_blink_duration'] = np.mean(list(self.blink_durations))
        
        blink_rate = result['blink_rate']
        avg_duration = result['avg_blink_duration']
        
        if blink_rate < DrowsinessThresholds.BLINK_RATE_LOW:
            result['blink_pattern'] = 'low_rate'
        elif blink_rate > DrowsinessThresholds.BLINK_RATE_HIGH:
            result['blink_pattern'] = 'high_rate'
        elif avg_duration > 0.25:
            result['blink_pattern'] = 'slow_blinks'
        else:
            result['blink_pattern'] = 'normal'
        
        self.last_ear = ear
        return result
    
    def get_fatigue_score(self) -> float:
        """Get fatigue score from blink patterns (0-100)"""
        score = 0.0
        
        if not self.blink_durations:
            return score
        
        avg_duration = np.mean(list(self.blink_durations))
        recent_blinks = len([b for b in self.blinks if time.time() - b < 60])
        
        if avg_duration > 0.35:
            score += 40
        elif avg_duration > 0.25:
            score += 20
        
        if recent_blinks < DrowsinessThresholds.BLINK_RATE_LOW:
            score += 30
        elif recent_blinks > DrowsinessThresholds.BLINK_RATE_HIGH:
            score += 20
        
        return min(100, score)
    
    def reset(self):
        self.blinks.clear()
        self.blink_durations.clear()
        self.in_blink = False
        self.blink_start = None
        self.total_blinks = 0
        self.slow_blinks = 0
        self.start_time = time.time()
