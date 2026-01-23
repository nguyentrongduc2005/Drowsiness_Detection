"""
Sleep Event Detection - Microsleep and sleep episode detection
"""
import numpy as np
import time
from collections import deque
from dataclasses import dataclass
from typing import List, Optional
from .thresholds import DrowsinessThresholds


@dataclass
class SleepEvent:
    """Represents a sleep/drowsiness event"""
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    event_type: str = "microsleep"
    severity: int = 1
    ear_min: float = 0.0
    recovered: bool = False
    
    def finalize(self, end_time: float):
        self.end_time = end_time
        self.duration = end_time - self.start_time
        self.recovered = True
        
        if self.duration < DrowsinessThresholds.MICROSLEEP_MAX:
            self.event_type = "microsleep"
            self.severity = 2
        elif self.duration < DrowsinessThresholds.NEAR_SLEEP_MAX:
            self.event_type = "near_sleep"
            self.severity = 4
        else:
            self.event_type = "sleep_episode"
            self.severity = 5


class SleepDetector:
    """
    Real-time sleep/microsleep detection
    FAST RESPONSE for driving safety
    """
    
    def __init__(self):
        self.events: List[SleepEvent] = []
        self.current_event: Optional[SleepEvent] = None
        
        self.eye_closed_start: Optional[float] = None
        self.eye_closed_duration = 0.0
        self.consecutive_closed_frames = 0
        
        self.is_sleeping = False
        self.alert_active = False
        self.last_alert_time = 0.0
        self.alert_cooldown = 3.0
        
        self.total_sleep_time = 0.0
        self.longest_event = 0.0
        self.event_count = 0
        
        self.low_ear_history = deque(maxlen=90)
        
        print("[OK] SleepDetector initialized (fast response)")
    
    def update(self, ear: float, threshold: float, is_eye_closed: bool, 
               current_time: float) -> dict:
        """Update sleep detection - FAST RESPONSE"""
        result = {
            'is_sleeping': False,
            'event_type': None,
            'duration': 0.0,
            'severity': 0,
            'alert': False,
            'alert_message': '',
            'pre_sleep_warning': False,
            'immediate_danger': False,
        }
        
        self.low_ear_history.append(ear)
        
        if len(self.low_ear_history) >= 60:
            avg_ear = np.mean(list(self.low_ear_history))
            if avg_ear < threshold * 1.2 and avg_ear > threshold * 0.7:
                result['pre_sleep_warning'] = True
        
        if is_eye_closed:
            self.consecutive_closed_frames += 1
            
            if self.eye_closed_start is None:
                self.eye_closed_start = current_time
                self.current_event = SleepEvent(start_time=current_time, ear_min=ear)
            else:
                self.eye_closed_duration = current_time - self.eye_closed_start
                if self.current_event:
                    self.current_event.ear_min = min(self.current_event.ear_min, ear)
            
            # IMMEDIATE RESPONSE
            if self.eye_closed_duration >= DrowsinessThresholds.MICROSLEEP_MIN:
                result['event_type'] = 'microsleep'
                result['duration'] = self.eye_closed_duration
                result['severity'] = 2
                
            if self.eye_closed_duration >= DrowsinessThresholds.MICROSLEEP_MAX:
                self.is_sleeping = True
                result['is_sleeping'] = True
                result['event_type'] = 'near_sleep'
                result['severity'] = 4
                
                if current_time - self.last_alert_time > self.alert_cooldown:
                    result['alert'] = True
                    result['alert_message'] = f"⚠ WAKE UP! ({self.eye_closed_duration:.1f}s)"
                    self.last_alert_time = current_time
            
            if self.eye_closed_duration >= DrowsinessThresholds.SLEEP_CRITICAL:
                result['event_type'] = 'sleep_episode'
                result['severity'] = 5
                result['immediate_danger'] = True
                result['alert'] = True
                result['alert_message'] = f"🚨 SLEEPING {self.eye_closed_duration:.1f}s - STOP!"
                self.last_alert_time = current_time
                
        else:
            if self.current_event and self.eye_closed_start:
                duration = current_time - self.eye_closed_start
                
                if duration >= DrowsinessThresholds.MICROSLEEP_MIN:
                    self.current_event.finalize(current_time)
                    self.events.append(self.current_event)
                    self.total_sleep_time += self.current_event.duration
                    self.longest_event = max(self.longest_event, self.current_event.duration)
                    self.event_count += 1
            
            self.eye_closed_start = None
            self.eye_closed_duration = 0.0
            self.consecutive_closed_frames = 0
            self.current_event = None
            self.is_sleeping = False
        
        return result
    
    def get_statistics(self) -> dict:
        """Get sleep statistics"""
        return {
            'total_events': len(self.events),
            'total_sleep_time': self.total_sleep_time,
            'longest_event': self.longest_event,
            'avg_duration': self.total_sleep_time / max(1, len(self.events)),
            'microsleep_count': len([e for e in self.events if e.event_type == 'microsleep']),
            'near_sleep_count': len([e for e in self.events if e.event_type == 'near_sleep']),
            'sleep_episode_count': len([e for e in self.events if e.event_type == 'sleep_episode']),
        }
    
    def get_risk_level(self) -> tuple:
        """Get risk level and trend"""
        recent_5min = [e for e in self.events if time.time() - e.start_time < 300]
        older_5min = [e for e in self.events if 300 <= time.time() - e.start_time < 600]
        
        risk_score = len(recent_5min) * 15 + sum(e.severity for e in recent_5min) * 5
        
        if risk_score >= 60:
            risk = 'critical'
        elif risk_score >= 35:
            risk = 'high'
        elif risk_score >= 15:
            risk = 'moderate'
        else:
            risk = 'low'
        
        if len(recent_5min) > len(older_5min) * 1.5:
            trend = 'worsening'
        elif len(recent_5min) < len(older_5min) * 0.5:
            trend = 'improving'
        else:
            trend = 'stable'
        
        return risk, trend
    
    def reset(self):
        self.events.clear()
        self.current_event = None
        self.eye_closed_start = None
        self.eye_closed_duration = 0.0
        self.consecutive_closed_frames = 0
        self.is_sleeping = False
        self.total_sleep_time = 0.0
        self.longest_event = 0.0
        self.event_count = 0
        self.low_ear_history.clear()
