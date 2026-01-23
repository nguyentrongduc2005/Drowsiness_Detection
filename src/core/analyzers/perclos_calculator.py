"""
PERCLOS Calculator - Key drowsiness metric
"""
import numpy as np
from collections import deque
from .thresholds import DrowsinessThresholds


class PERCLOSCalculator:
    """
    PERCLOS (Percentage of Eye Closure) Calculator
    
    PERCLOS is the percentage of time eyes are closed over a 1-minute window.
    It's one of the most reliable drowsiness indicators in driving research.
    """
    
    def __init__(self, fps: int = 30, window_seconds: int = 60):
        self.fps = fps
        self.window_size = fps * window_seconds
        self.eye_states = deque(maxlen=self.window_size)
        self.ear_values = deque(maxlen=self.window_size)
        
    def update(self, ear: float, threshold: float) -> dict:
        """Update PERCLOS with new EAR reading"""
        # Calculate closure percentage
        if ear < threshold * 0.7:
            closure = 1.0
        elif ear < threshold:
            closure = 1.0 - (ear / threshold)
        else:
            closure = 0.0
        
        self.eye_states.append(closure)
        self.ear_values.append(ear)
        
        if len(self.eye_states) < self.fps * 10:
            return {'perclos': 0.0, 'perclos_level': 'insufficient_data'}
        
        perclos = sum(1 for s in self.eye_states if s >= 0.7) / len(self.eye_states)
        
        if perclos < DrowsinessThresholds.PERCLOS_NORMAL:
            level = 'alert'
        elif perclos < DrowsinessThresholds.PERCLOS_TIRED:
            level = 'normal'
        elif perclos < DrowsinessThresholds.PERCLOS_DROWSY:
            level = 'tired'
        elif perclos < DrowsinessThresholds.PERCLOS_CRITICAL:
            level = 'drowsy'
        else:
            level = 'critical'
        
        return {
            'perclos': perclos,
            'perclos_level': level,
            'perclos_percentage': perclos * 100,
            'avg_ear': np.mean(list(self.ear_values)) if self.ear_values else 0,
        }
    
    def reset(self):
        self.eye_states.clear()
        self.ear_values.clear()
