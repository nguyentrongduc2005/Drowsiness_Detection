"""
Drowsiness Detection Logic Module
Optimized for real-time driver monitoring with high accuracy and fast response
Uses multi-signal fusion: EAR, MAR, PERCLOS, Blink patterns
"""
import numpy as np
import json
import os
import time
import datetime
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Tuple
from scipy.spatial import distance as dist
from .config import Config


# ============================================================================
# CONSTANTS - Optimized for driving safety
# ============================================================================
class DrowsinessThresholds:
    """Thresholds based on driving safety research"""
    # Eye closure thresholds (seconds) - TIME-BASED instead of frame-based
    BLINK_MAX = 0.4           # Normal blink < 0.4s
    MICROSLEEP_MIN = 0.5      # Microsleep starts at 0.5s
    MICROSLEEP_MAX = 2.0      # Microsleep ends at 2s
    NEAR_SLEEP_MAX = 4.0      # Near-sleep: 2-4s
    SLEEP_CRITICAL = 4.0      # Sleep episode: > 4s (DANGER)
    
    # TIME-BASED thresholds (FPS-independent)
    EYE_CLOSED_WARNING = 1.5  # 1.5 seconds eye closed = warning
    EYE_CLOSED_DANGER = 2.0   # 2.0 seconds = danger
    EYE_CLOSED_CRITICAL = 4.0 # 4.0 seconds = critical
    
    # PERCLOS thresholds (% eyes closed in 1 minute)
    PERCLOS_NORMAL = 0.08     # < 8% = alert
    PERCLOS_TIRED = 0.15      # 8-15% = tired
    PERCLOS_DROWSY = 0.25     # 15-25% = drowsy
    PERCLOS_CRITICAL = 0.40   # > 40% = critical
    
    # Yawn detection (with variance check to distinguish from talking)
    YAWN_DURATION_MIN = 1.5   # Minimum yawn duration (seconds)
    YAWN_REMINDER_THRESHOLD = 2  # 2+ yawns = reminder
    YAWN_MAR_VARIANCE_MAX = 0.05  # Low variance = real yawn (not talking)
    YAWN_EAR_DROP_THRESHOLD = 0.03  # Eyes tend to close slightly during yawn
    
    # Head Pose thresholds (degrees)
    HEAD_PITCH_WARNING = -15  # Head tilted down 15 degrees
    HEAD_PITCH_DANGER = -25   # Head tilted down 25 degrees (nodding off)
    HEAD_ROLL_WARNING = 20    # Head tilted sideways 20 degrees
    HEAD_POSE_DURATION = 2.0  # Duration before warning (seconds)
    
    # Fatigue monitoring window (minutes)
    FATIGUE_WINDOW_MINUTES = 3     # Monitor over 3 minutes
    FATIGUE_YAWN_THRESHOLD = 3     # 3+ yawns in window = fatigue sign
    FATIGUE_DROWSY_COUNT = 5       # 5+ drowsy episodes in window = fatigue warning
    
    # Blink rate (per minute) - LOW blink rate is PRE-WARNING
    BLINK_RATE_LOW = 8        # < 8 = staring (pre-drowsiness sign)
    BLINK_RATE_NORMAL_MIN = 12
    BLINK_RATE_NORMAL_MAX = 20
    BLINK_RATE_HIGH = 25      # > 25 = trying to stay awake
    BLINK_RATE_LOW_DURATION = 30  # Seconds of low blink rate before warning
    
    # Dynamic calibration
    EAR_THRESHOLD_RATIO = 0.70  # threshold = baseline_ear * 0.70


# ============================================================================
# PERCLOS CALCULATOR - Key drowsiness metric
# ============================================================================
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


# ============================================================================
# BLINK ANALYZER - Detect abnormal blink patterns
# ============================================================================
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


# ============================================================================
# YAWN ANALYZER - Distinguish yawn from talking/singing
# ============================================================================
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
            self.yawn_start_time = current_time
            self.yawn_start_ear = ear
            
        elif mouth_open and self.is_yawning:
            # Continue yawning
            duration = current_time - self.yawn_start_time
            result['yawn_duration'] = duration
            
            # Check if it's a real yawn
            if duration >= DrowsinessThresholds.YAWN_DURATION_MIN:
                mar_var = result['mar_variance']
                ear_drop = self.yawn_start_ear - ear if self.yawn_start_ear else 0
                result['ear_drop'] = ear_drop
                
                # Real yawn: low variance + slight eye closure
                is_low_variance = mar_var < DrowsinessThresholds.YAWN_MAR_VARIANCE_MAX
                has_ear_drop = ear_drop > DrowsinessThresholds.YAWN_EAR_DROP_THRESHOLD
                
                # Calculate confidence
                confidence = 0.0
                if is_low_variance:
                    confidence += 0.5
                if has_ear_drop:
                    confidence += 0.3
                if duration >= 2.0:  # Long duration = likely yawn
                    confidence += 0.2
                
                result['confidence'] = confidence
                result['is_yawning'] = True
                
                if confidence >= 0.5:
                    result['is_real_yawn'] = True
                    
        elif not mouth_open and self.is_yawning:
            # End of yawn
            duration = current_time - self.yawn_start_time if self.yawn_start_time else 0
            
            if duration >= DrowsinessThresholds.YAWN_DURATION_MIN:
                # Check if it was a real yawn before counting
                mar_var = np.var(list(self.mar_history)) if len(self.mar_history) >= 5 else 1.0
                ear_drop = self.yawn_start_ear - np.mean(list(self.ear_history)) if self.yawn_start_ear else 0
                
                is_real = mar_var < DrowsinessThresholds.YAWN_MAR_VARIANCE_MAX or ear_drop > 0
                
                if is_real and current_time - self.last_yawn_time > 5:
                    self.yawn_count += 1
                    self.yawn_timestamps.append(current_time)
                    self.last_yawn_time = current_time
            
            self.is_yawning = False
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
        self.yawn_count = 0
        self.yawn_timestamps.clear()
        self.last_yawn_time = 0


# ============================================================================
# HEAD POSE ANALYZER - Detect nodding off
# ============================================================================
class HeadPoseAnalyzer:
    """
    Analyze head pose to detect nodding off behavior.
    
    Uses facial landmarks to estimate:
    - Pitch (head tilting forward/backward)
    - Roll (head tilting sideways)
    
    Drowsiness signs:
    - Head drooping forward (negative pitch)
    - Head tilting to side (high roll)
    - "Nodding" pattern (quick up-down movements)
    """
    
    def __init__(self):
        self.pitch_history = deque(maxlen=90)  # 3 seconds at 30fps
        self.roll_history = deque(maxlen=90)
        
        self.head_down_start = None
        self.head_tilt_start = None
        
        self.nod_count = 0
        self.nod_timestamps = deque(maxlen=50)
        self.last_pitch = 0
        self.pitch_direction = 0  # 1 = up, -1 = down
    
    def estimate_pose(self, landmarks) -> Tuple[float, float]:
        """
        Estimate head pitch and roll from landmarks.
        
        Uses nose tip, chin, and eye positions for estimation.
        Returns (pitch, roll) in degrees.
        
        Args:
            landmarks: MediaPipe NormalizedLandmarkList object
        """
        if landmarks is None:
            return 0.0, 0.0
        
        try:
            # Get landmark list from MediaPipe object
            if hasattr(landmarks, 'landmark'):
                lm = landmarks.landmark
            else:
                return 0.0, 0.0
            
            if len(lm) < 468:
                return 0.0, 0.0
            
            # Key landmarks for MediaPipe Face Mesh
            # Each landmark has x, y, z normalized coordinates (0-1)
            # Nose tip: 1, Nose bridge: 6
            # Left eye outer: 33, Right eye outer: 263
            # Chin: 152, Forehead: 10
            
            nose_tip = np.array([lm[1].x, lm[1].y, lm[1].z])
            left_eye = np.array([lm[33].x, lm[33].y, lm[33].z])
            right_eye = np.array([lm[263].x, lm[263].y, lm[263].z])
            chin = np.array([lm[152].x, lm[152].y, lm[152].z])
            forehead = np.array([lm[10].x, lm[10].y, lm[10].z])
            
            # Calculate pitch (forward/backward tilt)
            # Using vertical distance ratio between forehead-nose and nose-chin
            forehead_to_nose = np.linalg.norm(forehead[:2] - nose_tip[:2])
            nose_to_chin = np.linalg.norm(nose_tip[:2] - chin[:2])
            
            if nose_to_chin > 0:
                pitch_ratio = forehead_to_nose / nose_to_chin
                # Convert ratio to approximate degrees
                # Normal ratio ~0.8-1.0, head down increases ratio
                pitch = (pitch_ratio - 0.9) * 50  # Approximate degrees
            else:
                pitch = 0.0
            
            # Calculate roll (sideways tilt)
            eye_vector = right_eye[:2] - left_eye[:2]
            roll = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
            
            return float(pitch), float(roll)
            
        except Exception:
            return 0.0, 0.0
    
    def update(self, landmarks, current_time: float) -> dict:
        """Update head pose analysis"""
        pitch, roll = self.estimate_pose(landmarks)
        
        self.pitch_history.append(pitch)
        self.roll_history.append(roll)
        
        result = {
            'pitch': pitch,
            'roll': roll,
            'head_down': False,
            'head_tilt': False,
            'head_down_duration': 0.0,
            'head_tilt_duration': 0.0,
            'nodding_detected': False,
            'nod_count': self.nod_count,
            'warning': False,
            'warning_type': None,
        }
        
        # Check for head drooping (pitch)
        if pitch < DrowsinessThresholds.HEAD_PITCH_WARNING:
            if self.head_down_start is None:
                self.head_down_start = current_time
            
            duration = current_time - self.head_down_start
            result['head_down'] = True
            result['head_down_duration'] = duration
            
            if duration >= DrowsinessThresholds.HEAD_POSE_DURATION:
                result['warning'] = True
                if pitch < DrowsinessThresholds.HEAD_PITCH_DANGER:
                    result['warning_type'] = 'head_danger'
                else:
                    result['warning_type'] = 'head_warning'
        else:
            self.head_down_start = None
        
        # Check for head tilting (roll)
        if abs(roll) > DrowsinessThresholds.HEAD_ROLL_WARNING:
            if self.head_tilt_start is None:
                self.head_tilt_start = current_time
            
            duration = current_time - self.head_tilt_start
            result['head_tilt'] = True
            result['head_tilt_duration'] = duration
            
            if duration >= DrowsinessThresholds.HEAD_POSE_DURATION:
                result['warning'] = True
                result['warning_type'] = 'head_tilt'
        else:
            self.head_tilt_start = None
        
        # Detect nodding pattern (quick up-down-up movements)
        if len(self.pitch_history) >= 30:
            recent_pitch = list(self.pitch_history)[-30:]
            pitch_range = max(recent_pitch) - min(recent_pitch)
            
            # Significant pitch change in short time = nod
            if pitch_range > 15:  # 15 degrees change
                new_direction = 1 if pitch > self.last_pitch else -1
                
                # Direction changed = potential nod
                if new_direction != self.pitch_direction and self.pitch_direction != 0:
                    if current_time - (self.nod_timestamps[-1] if self.nod_timestamps else 0) > 1:
                        self.nod_count += 1
                        self.nod_timestamps.append(current_time)
                        result['nodding_detected'] = True
                
                self.pitch_direction = new_direction
        
        self.last_pitch = pitch
        result['nod_count'] = self.nod_count
        
        return result
    
    def get_fatigue_contribution(self) -> float:
        """Get fatigue score contribution from head pose (0-30)"""
        score = 0.0
        
        # Recent nods increase score
        recent_nods = len([t for t in self.nod_timestamps if time.time() - t < 60])
        score += min(15, recent_nods * 5)
        
        # Prolonged head down increases score
        if self.head_down_start:
            duration = time.time() - self.head_down_start
            score += min(15, duration * 3)
        
        return score
    
    def reset(self):
        self.pitch_history.clear()
        self.roll_history.clear()
        self.head_down_start = None
        self.head_tilt_start = None
        self.nod_count = 0
        self.nod_timestamps.clear()
        self.last_pitch = 0
        self.pitch_direction = 0


# ============================================================================
# SLEEP EVENT DETECTION
# ============================================================================
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
    
    def get_risk_level(self) -> Tuple[str, str]:
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


# ============================================================================
# FATIGUE STATE SYSTEM
# ============================================================================
class FatigueState:
    """5-level fatigue classification"""
    ALERT = "ALERT"
    NORMAL = "NORMAL"
    TIRED = "TIRED"
    DROWSY = "DROWSY"
    CRITICAL = "CRITICAL"
    
    @staticmethod
    def get_color(state):
        colors = {
            FatigueState.ALERT: (0, 255, 0),
            FatigueState.NORMAL: (0, 200, 100),
            FatigueState.TIRED: (0, 200, 255),
            FatigueState.DROWSY: (0, 100, 255),
            FatigueState.CRITICAL: (0, 0, 255),
        }
        return colors.get(state, (255, 255, 255))
    
    @staticmethod
    def get_level(state):
        levels = {
            FatigueState.ALERT: 0,
            FatigueState.NORMAL: 1,
            FatigueState.TIRED: 2,
            FatigueState.DROWSY: 3,
            FatigueState.CRITICAL: 4,
        }
        return levels.get(state, 1)
    
    @staticmethod
    def get_description(state):
        descriptions = {
            FatigueState.ALERT: "Fully alert",
            FatigueState.NORMAL: "Normal state",
            FatigueState.TIRED: "Early fatigue signs",
            FatigueState.DROWSY: "Drowsy - need break",
            FatigueState.CRITICAL: "DANGER - stop now!",
        }
        return descriptions.get(state, "")


# ============================================================================
# EAR / MAR CALCULATION
# ============================================================================
def calculate_ear(eye_points) -> float:
    """Calculate Eye Aspect Ratio (EAR)"""
    if eye_points is None or len(eye_points) != 6:
        return 0.0
    
    A = dist.euclidean(eye_points[1], eye_points[5])
    B = dist.euclidean(eye_points[2], eye_points[4])
    C = dist.euclidean(eye_points[0], eye_points[3])
    
    if C == 0:
        return 0.0
    
    return (A + B) / (2.0 * C)


def calculate_mar(mouth_points) -> float:
    """Calculate Mouth Aspect Ratio (MAR)"""
    if mouth_points is None or len(mouth_points) < 20:
        return 0.0
    
    A = dist.euclidean(mouth_points[2], mouth_points[10])
    B = dist.euclidean(mouth_points[4], mouth_points[8])
    C = dist.euclidean(mouth_points[0], mouth_points[6])
    
    if C == 0:
        return 0.0
    
    return (A + B) / (2.0 * C)


# ============================================================================
# PERSONAL CALIBRATION
# ============================================================================
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
            print("[CALIB] Step 3: Yawn/open mouth wide")
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
            if mar > 0.3:
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
            # Store min open EAR as safety reference
            self.learned_thresholds['ear_open_min'] = np.min(open_filtered)
        
        if closed_filtered:
            self.learned_thresholds['ear_closed'] = np.mean(closed_filtered)
            # Store max closed EAR as safety reference
            self.learned_thresholds['ear_closed_max'] = np.max(closed_filtered)
        
        if self.learned_thresholds['ear_open'] and self.learned_thresholds['ear_closed']:
            ear_open = self.learned_thresholds['ear_open']
            ear_closed = self.learned_thresholds['ear_closed']
            ear_open_min = self.learned_thresholds.get('ear_open_min', ear_open * 0.9)
            ear_closed_max = self.learned_thresholds.get('ear_closed_max', ear_closed * 1.1)
            
            # Calculate threshold with safety margin
            # Use 35% from closed to open - more conservative to reduce false positives
            base_threshold = ear_closed + 0.35 * (ear_open - ear_closed)
            
            # Ensure threshold is below minimum open EAR (safety margin)
            safe_threshold = min(base_threshold, ear_open_min * 0.85)
            
            # Ensure threshold is above maximum closed EAR
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
            self.STATE_YAWNING: "Yawn/Open mouth...",
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


# ============================================================================
# SMART THRESHOLD
# ============================================================================
class SmartThreshold:
    """Adaptive threshold with personal calibration priority"""
    
    def __init__(self, config=None, personal_calibration=None):
        if config is None:
            config = Config()
        
        self.config = config
        self.personal_calibration = personal_calibration
        self.window_size = config.get_window_size()
        self.history = deque(maxlen=self.window_size)
        self.default_threshold = config.get_ear_default()
        self.min_samples = config.get_min_samples()
        self.min_threshold = 0.18
        self.max_threshold = 0.28
        
    def update_threshold(self, current_ear: float) -> Tuple[float, bool]:
        if self.personal_calibration and self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            if thresholds.get('ear_threshold'):
                return thresholds['ear_threshold'], True
        
        if current_ear > 0.2:
            self.history.append(current_ear)
        
        if len(self.history) < self.min_samples:
            return self.default_threshold, False
        
        sorted_history = sorted(self.history, reverse=True)
        top_60_percent = sorted_history[:int(len(sorted_history) * 0.6)]
        avg_ear = np.mean(top_60_percent)
        
        adaptive_threshold = avg_ear * 0.72
        adaptive_threshold = max(self.min_threshold, min(self.max_threshold, adaptive_threshold))
        
        return adaptive_threshold, True
    
    def get_status_text(self):
        if self.personal_calibration:
            state = self.personal_calibration.get_state()
            if state == PersonalCalibration.STATE_COMPLETED:
                return "Calibrated"
            elif state != PersonalCalibration.STATE_IDLE:
                return self.personal_calibration.get_state_text()
        
        if len(self.history) < self.min_samples:
            return f"Learning: {len(self.history)}/{self.min_samples}"
        return "Active"
    
    def reset(self):
        self.history.clear()


# ============================================================================
# MAIN DROWSINESS DETECTOR
# ============================================================================
class DrowsinessDetector:
    """
    Main drowsiness detection system with improvements:
    - TIME-BASED detection (FPS-independent)
    - Yawn vs Talking distinction
    - Head Pose detection
    - Dynamic calibration
    - Veto logic for critical events
    """
    
    def __init__(self, config=None):
        if config is None:
            config = Config()
        
        self.config = config
        self.fps = 30
        
        # MAR threshold for yawn detection
        self.mar_threshold = config.get('mouth_thresholds.mar_limit', 0.6)
        
        # TIME-BASED tracking (FPS-independent)
        self.eye_closed_start_time = None
        self.eye_closed_duration = 0.0
        self.is_drowsy = False
        self.is_yawning = False
        
        # Fatigue tracking
        self.drowsy_episodes = deque(maxlen=100)
        self.fatigue_window = DrowsinessThresholds.FATIGUE_WINDOW_MINUTES * 60
        self.combined_fatigue_warning = False
        
        # Low blink rate tracking (pre-warning)
        self.low_blink_start_time = None
        self.low_blink_warning = False
        
        # Calibration
        self.personal_calibration = PersonalCalibration()
        self.smart_threshold = SmartThreshold(config, self.personal_calibration)
        
        if self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            if thresholds.get('mar_threshold'):
                self.mar_threshold = thresholds['mar_threshold']
        
        # Analyzers
        self.sleep_detector = SleepDetector()
        self.blink_analyzer = BlinkAnalyzer(self.fps)
        self.perclos_calc = PERCLOSCalculator(self.fps)
        self.yawn_analyzer = YawnAnalyzer()
        self.head_pose_analyzer = HeadPoseAnalyzer()
        
        self.fatigue_state = FatigueState.NORMAL
        self.fatigue_score = 0.0
        
        self.start_time = time.time()
        self.frame_count = 0
        
        # Smoothing buffers
        self.ear_buffer = deque(maxlen=9)
        self.mar_buffer = deque(maxlen=7)
        
        # Hysteresis for eye state
        self.eye_state = 'open'
        self.hysteresis_margin = 0.03
        
        # Stability tracking
        self.stable_closed_count = 0
        self.stability_threshold = 5
        
        # Store landmarks for head pose
        self.current_landmarks = None
        
        print("[OK] DrowsinessDetector initialized (v2.0 - Time-based + Head Pose)")
        self.hysteresis_margin = 0.03  # 3% margin
        
        # Stability tracking - need consistent readings
        self.stable_closed_count = 0
        self.stability_threshold = 5  # Need 5 consecutive closed readings
        
        print("[OK] DrowsinessDetector initialized (v2.0 - Time-based + Head Pose)")
    
    def set_landmarks(self, landmarks):
        """Store landmarks for head pose analysis"""
        self.current_landmarks = landmarks
    
    def process(self, left_eye, right_eye, mouth=None) -> dict:
        """
        Process frame and detect drowsiness.
        Uses TIME-BASED detection (FPS-independent).
        """
        current_time = time.time()
        self.frame_count += 1
        
        # === CALCULATE EAR/MAR ===
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        raw_ear = (left_ear + right_ear) / 2.0
        
        self.ear_buffer.append(raw_ear)
        ear = np.mean(list(self.ear_buffer))
        
        mar = 0.0
        if mouth is not None:
            raw_mar = calculate_mar(mouth)
            self.mar_buffer.append(raw_mar)
            mar = np.mean(list(self.mar_buffer))
        
        # === GET THRESHOLD (Dynamic Calibration) ===
        threshold, is_calibrated = self.smart_threshold.update_threshold(ear)
        
        # Hysteresis for stable state detection
        if self.eye_state == 'open':
            close_threshold = threshold - self.hysteresis_margin
            is_eye_closed = ear < close_threshold
        else:
            open_threshold = threshold + self.hysteresis_margin
            is_eye_closed = ear < open_threshold
        
        # Stability check
        if is_eye_closed:
            self.stable_closed_count += 1
            if self.stable_closed_count >= self.stability_threshold:
                self.eye_state = 'closed'
        else:
            self.stable_closed_count = 0
            self.eye_state = 'open'
        
        # === TIME-BASED EYE CLOSURE DETECTION (FPS-independent) ===
        if is_eye_closed:
            if self.eye_closed_start_time is None:
                self.eye_closed_start_time = current_time
            self.eye_closed_duration = current_time - self.eye_closed_start_time
            
            # Check against TIME thresholds, not frame counts
            if self.eye_closed_duration >= DrowsinessThresholds.EYE_CLOSED_WARNING:
                self.is_drowsy = True
        else:
            self.eye_closed_start_time = None
            self.eye_closed_duration = 0.0
            self.is_drowsy = False
        
        # === ANALYZERS ===
        
        # 1. Sleep detection
        sleep_result = self.sleep_detector.update(ear, threshold, is_eye_closed, current_time)
        
        # 2. PERCLOS
        perclos_result = self.perclos_calc.update(ear, threshold)
        
        # 3. Blink analysis + Low blink rate pre-warning
        blink_result = self.blink_analyzer.update(ear, threshold, current_time)
        
        # Track low blink rate as pre-warning (staring = pre-drowsiness)
        if blink_result['blink_rate'] < DrowsinessThresholds.BLINK_RATE_LOW:
            if self.low_blink_start_time is None:
                self.low_blink_start_time = current_time
            elif current_time - self.low_blink_start_time >= DrowsinessThresholds.BLINK_RATE_LOW_DURATION:
                self.low_blink_warning = True
        else:
            self.low_blink_start_time = None
            self.low_blink_warning = False
        
        # 4. Yawn detection with Talking/Singing distinction
        yawn_result = self.yawn_analyzer.update(mar, ear, self.mar_threshold, current_time)
        self.is_yawning = yawn_result['is_real_yawn']
        recent_yawns = self.yawn_analyzer.get_recent_yawns(300)  # 5 minutes
        
        # 5. Head Pose detection
        head_result = self.head_pose_analyzer.update(self.current_landmarks, current_time)
        
        # === FATIGUE CALCULATION (with improved weights) ===
        self.fatigue_score = self._calculate_fatigue_score_v2(
            perclos_result, blink_result, sleep_result, 
            recent_yawns, head_result
        )
        
        # === VETO LOGIC: Immediate CRITICAL for severe events ===
        veto_critical = False
        veto_reason = ""
        
        # Sleep Critical Override
        if sleep_result.get('immediate_danger'):
            veto_critical = True
            veto_reason = sleep_result.get('alert_message', 'SLEEPING!')
        elif self.eye_closed_duration >= DrowsinessThresholds.EYE_CLOSED_CRITICAL:
            veto_critical = True
            veto_reason = f"EYES CLOSED {self.eye_closed_duration:.1f}s!"
        elif head_result.get('warning_type') == 'head_danger':
            veto_critical = True
            veto_reason = "HEAD DROOPING - DANGER!"
        
        # Determine fatigue state with VETO
        if veto_critical:
            self.fatigue_state = FatigueState.CRITICAL
        else:
            self.fatigue_state = self._determine_fatigue_state_v2(
                sleep_result, perclos_result, recent_yawns, 
                blink_result, head_result
            )
        
        # === COMBINED FATIGUE TRACKING ===
        if self.is_drowsy and (not self.drowsy_episodes or 
                                current_time - self.drowsy_episodes[-1] > 2):
            self.drowsy_episodes.append(current_time)
        
        recent_drowsy = len([t for t in self.drowsy_episodes 
                            if current_time - t < self.fatigue_window])
        recent_yawns_window = self.yawn_analyzer.get_recent_yawns(self.fatigue_window)
        
        self.combined_fatigue_warning = (
            recent_yawns_window >= DrowsinessThresholds.FATIGUE_YAWN_THRESHOLD and
            recent_drowsy >= DrowsinessThresholds.FATIGUE_DROWSY_COUNT
        )
        
        # === WARNING LOGIC ===
        warning = False
        warning_reason = ""
        is_reminder = False
        
        if veto_critical:
            warning = True
            warning_reason = veto_reason
        elif sleep_result.get('alert'):
            warning = True
            warning_reason = sleep_result.get('alert_message', 'Wake up!')
        elif self.fatigue_state == FatigueState.CRITICAL:
            warning = True
            warning_reason = "CRITICAL: Stop driving!"
        elif head_result.get('warning'):
            warning = True
            warning_reason = f"Head drooping ({head_result['head_down_duration']:.1f}s)"
        elif self.combined_fatigue_warning:
            warning = True
            warning_reason = f"FATIGUE: {recent_yawns_window} yawns + {recent_drowsy} drowsy"
        elif self.is_drowsy:
            warning = True
            warning_reason = f"Eyes closing ({self.eye_closed_duration:.1f}s)!"
        elif self.low_blink_warning:
            warning = True
            warning_reason = "Staring detected - stay alert!"
        elif self.fatigue_state == FatigueState.DROWSY:
            warning = True
            warning_reason = "Drowsiness detected"
        elif self.is_yawning:
            is_reminder = True
            warning_reason = "Reminder: Yawning detected"
        elif sleep_result.get('pre_sleep_warning'):
            is_reminder = True
            warning_reason = "Eyes getting heavy"
        
        # === BUILD RESULT ===
        sleep_stats = self.sleep_detector.get_statistics()
        risk_level, trend = self.sleep_detector.get_risk_level()
        session_duration = current_time - self.start_time
        
        return {
            'ear': ear,
            'mar': mar,
            'threshold': threshold,
            'is_calibrated': is_calibrated,
            'is_drowsy': self.is_drowsy,
            'is_yawning': self.is_yawning,
            'warning': warning,
            'warning_reason': warning_reason,
            'is_reminder': is_reminder,
            'combined_fatigue_warning': self.combined_fatigue_warning,
            'recent_drowsy_count': recent_drowsy,
            'fatigue_state': self.fatigue_state,
            'fatigue_score': self.fatigue_score,
            'fatigue_level': FatigueState.get_level(self.fatigue_state),
            'fatigue_color': FatigueState.get_color(self.fatigue_state),
            'perclos': perclos_result['perclos'],
            'perclos_percentage': perclos_result.get('perclos_percentage', 0),
            'perclos_level': perclos_result['perclos_level'],
            'blink_rate': blink_result['blink_rate'],
            'blink_pattern': blink_result['blink_pattern'],
            'avg_blink_duration': blink_result['avg_blink_duration'],
            'low_blink_warning': self.low_blink_warning,
            'is_sleeping': sleep_result.get('is_sleeping', False),
            'sleep_event_type': sleep_result.get('event_type'),
            'sleep_duration': sleep_result.get('duration', 0.0),
            'eye_closed_duration': self.eye_closed_duration,
            'pre_sleep_warning': sleep_result.get('pre_sleep_warning', False),
            'sleep_alert': sleep_result.get('alert', False),
            'sleep_alert_message': sleep_result.get('alert_message', ''),
            'immediate_danger': sleep_result.get('immediate_danger', False) or veto_critical,
            'sleep_stats': sleep_stats,
            'sleep_risk': risk_level,
            'sleep_trend': trend,
            'yawn_count': recent_yawns,
            'yawn_confidence': yawn_result.get('confidence', 0),
            'yawn_counter': 0,  # Deprecated, use yawn_count
            'head_pitch': head_result.get('pitch', 0),
            'head_roll': head_result.get('roll', 0),
            'head_warning': head_result.get('warning', False),
            'nod_count': head_result.get('nod_count', 0),
            'session_duration': session_duration,
            'status': self.smart_threshold.get_status_text(),
            'counter': int(self.eye_closed_duration * self.fps),  # Backward compatibility
        }
    
    def _calculate_fatigue_score_v2(self, perclos, blink, sleep, yawn_count, head) -> float:
        """
        Calculate fatigue score with improved weights.
        
        Weights:
        - PERCLOS: 35%
        - Sleep events: 30% (increased for severity)
        - Blink patterns: 15%
        - Yawns: 10%
        - Head pose: 10%
        """
        score = 0.0
        
        # PERCLOS (35%)
        perclos_value = perclos.get('perclos', 0)
        score += min(35, perclos_value * 90)
        
        # Sleep events (30%) - Increased weight for severity
        if sleep.get('is_sleeping'):
            duration = sleep.get('duration', 0)
            score += min(30, duration * 15)  # Faster score increase
        
        # Blink patterns (15%)
        blink_score = self.blink_analyzer.get_fatigue_score()
        score += blink_score * 0.15
        
        # Low blink rate bonus (pre-drowsiness indicator)
        if blink.get('blink_rate', 15) < DrowsinessThresholds.BLINK_RATE_LOW:
            score += 10
        
        # Yawns (10%)
        score += min(10, yawn_count * 3)
        
        # Head pose (10%)
        score += self.head_pose_analyzer.get_fatigue_contribution() * 0.33
        
        # Eye closure bonus
        if self.is_drowsy:
            score += 15
        
        return min(100, max(0, score))
    
    def _determine_fatigue_state_v2(self, sleep, perclos, yawn_count, blink, head) -> str:
        """Determine fatigue state with VETO logic for critical events."""
        
        # CRITICAL conditions (any of these = immediate CRITICAL)
        if sleep.get('immediate_danger'):
            return FatigueState.CRITICAL
        if perclos.get('perclos_level') == 'critical':
            return FatigueState.CRITICAL
        if sleep.get('is_sleeping') and sleep.get('duration', 0) > 3.0:
            return FatigueState.CRITICAL
        if head.get('warning_type') == 'head_danger':
            return FatigueState.CRITICAL
        if self.fatigue_score >= 75:
            return FatigueState.CRITICAL
        
        # DROWSY conditions
        if sleep.get('is_sleeping'):
            return FatigueState.DROWSY
        if perclos.get('perclos_level') == 'drowsy':
            return FatigueState.DROWSY
        if head.get('warning'):
            return FatigueState.DROWSY
        if self.fatigue_score >= 45:
            return FatigueState.DROWSY
        
        # TIRED conditions
        if perclos.get('perclos_level') == 'tired':
            return FatigueState.TIRED
        if yawn_count >= DrowsinessThresholds.FATIGUE_YAWN_THRESHOLD:
            return FatigueState.TIRED
        if blink.get('blink_rate', 15) < DrowsinessThresholds.BLINK_RATE_LOW:
            return FatigueState.TIRED  # Staring = early fatigue sign
        if self.fatigue_score >= 20:
            return FatigueState.TIRED
        
        # ALERT
        if self.fatigue_score < 10 and perclos.get('perclos_level') == 'alert':
            return FatigueState.ALERT
        
        return FatigueState.NORMAL
    
    def reset(self):
        """Reset all detection state"""
        # Legacy counters (for backward compatibility)
        self.counter = 0
        self.yawn_counter = 0
        
        # State flags
        self.is_drowsy = False
        self.is_yawning = False
        self.yawn_count = 0
        self.yawn_history.clear()
        self.drowsy_episodes.clear()
        self.combined_fatigue_warning = False
        self.fatigue_state = FatigueState.NORMAL
        self.fatigue_score = 0.0
        self.start_time = time.time()
        self.frame_count = 0
        self.ear_buffer.clear()
        self.mar_buffer.clear()
        
        # Reset hysteresis and stability
        self.eye_state = 'open'
        self.stable_closed_count = 0
        
        # Reset TIME-BASED tracking
        self.eye_closed_start_time = None
        self.eye_closed_duration = 0.0
        self.low_blink_start_time = None
        self.low_blink_warning = False
        self.current_landmarks = None
        
        # Reset all analyzers
        self.sleep_detector.reset()
        self.blink_analyzer.reset()
        self.perclos_calc.reset()
        self.smart_threshold.reset()
        self.yawn_analyzer.reset()
        self.head_pose_analyzer.reset()
    
    # === CALIBRATION ===
    
    def start_calibration(self):
        self.personal_calibration.start_calibration()
    
    def is_calibrating(self):
        state = self.personal_calibration.get_state()
        return state not in [PersonalCalibration.STATE_IDLE, PersonalCalibration.STATE_COMPLETED]
    
    def process_calibration(self, left_eye, right_eye, mouth=None) -> dict:
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        mar = 0.0
        if mouth is not None:
            mar = calculate_mar(mouth)
        
        progress, total, should_advance = self.personal_calibration.add_sample(ear, mar)
        
        if should_advance:
            self.personal_calibration.next_state()
        
        if self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            if thresholds.get('mar_threshold'):
                self.mar_threshold = thresholds['mar_threshold']
        
        return {
            'ear': ear,
            'mar': mar,
            'calibration_state': self.personal_calibration.get_state(),
            'calibration_text': self.personal_calibration.get_state_text(),
            'progress': progress,
            'total': total,
            'is_completed': self.personal_calibration.get_state() == PersonalCalibration.STATE_COMPLETED
        }
    
    def reset_calibration(self):
        self.personal_calibration.reset()
    
    def get_calibration_info(self) -> dict:
        if self.personal_calibration.is_calibrated():
            thresholds = self.personal_calibration.get_thresholds()
            return {
                'calibrated': True,
                'ear_threshold': thresholds.get('ear_threshold'),
                'mar_threshold': thresholds.get('mar_threshold'),
                'ear_open': thresholds.get('ear_open'),
                'ear_closed': thresholds.get('ear_closed'),
                'calibration_date': thresholds.get('calibration_date')
            }
        return {'calibrated': False}
