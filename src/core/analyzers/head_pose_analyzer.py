"""
Head Pose Analyzer - Detect nodding off behavior
"""
import numpy as np
import time
from collections import deque
from typing import Tuple
from .thresholds import DrowsinessThresholds


class HeadPoseAnalyzer:
    """
    Analyze head pose to detect nodding off behavior.
    
    Uses facial landmarks to estimate:
    - Pitch (head tilting forward/backward)
    - Roll (head tilting sideways)
    - Yaw (head turning left/right)
    
    Drowsiness signs:
    - Head drooping forward (negative pitch)
    - Head tilting to side (high roll)
    - Head turning away (high yaw)
    - "Nodding" pattern (quick up-down movements)
    """
    
    def __init__(self):
        self.pitch_history = deque(maxlen=90)  # 3 seconds at 30fps
        self.roll_history = deque(maxlen=90)
        self.yaw_history = deque(maxlen=90)
        
        self.head_down_start = None
        self.head_tilt_start = None
        self.head_turn_start = None
        
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
            nose_tip = np.array([lm[1].x, lm[1].y, lm[1].z])
            left_eye = np.array([lm[33].x, lm[33].y, lm[33].z])
            right_eye = np.array([lm[263].x, lm[263].y, lm[263].z])
            chin = np.array([lm[152].x, lm[152].y, lm[152].z])
            forehead = np.array([lm[10].x, lm[10].y, lm[10].z])
            
            # Calculate pitch (forward/backward tilt)
            forehead_to_nose = np.linalg.norm(forehead[:2] - nose_tip[:2])
            nose_to_chin = np.linalg.norm(nose_tip[:2] - chin[:2])
            
            if nose_to_chin > 0:
                pitch_ratio = forehead_to_nose / nose_to_chin
                pitch = (pitch_ratio - 0.9) * 50
            else:
                pitch = 0.0
            
            # Calculate roll (sideways tilt)
            eye_vector = right_eye[:2] - left_eye[:2]
            roll = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
            
            return float(pitch), float(roll)
            
        except Exception:
            return 0.0, 0.0
    
    def _extract_yaw_from_landmarks(self, landmarks) -> float:
        """
        Extract YAW (góc quay trái/phải) từ MediaPipe landmarks
        
        Returns:
            yaw: Góc quay đầu (độ). Positive = quay phải, Negative = quay trái
        """
        if landmarks is None:
            return 0.0
        
        try:
            if hasattr(landmarks, 'landmark'):
                lm = landmarks.landmark
            else:
                return 0.0
            
            if len(lm) < 468:
                return 0.0
            
            nose_tip = lm[1]
            left_eye_outer = lm[33]
            right_eye_outer = lm[263]
            
            eye_center_x = (left_eye_outer.x + right_eye_outer.x) / 2
            nose_offset = nose_tip.x - eye_center_x
            eye_distance = abs(right_eye_outer.x - left_eye_outer.x)
            
            if eye_distance > 0:
                normalized_offset = nose_offset / eye_distance
                yaw = normalized_offset * 150
                yaw = max(-60, min(60, yaw))
                return float(yaw)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def update(self, landmarks, current_time: float) -> dict:
        """Update head pose analysis with YAW detection"""
        pitch, roll = self.estimate_pose(landmarks)
        yaw = self._extract_yaw_from_landmarks(landmarks)
        
        self.pitch_history.append(pitch)
        self.roll_history.append(roll)
        self.yaw_history.append(yaw)
        
        result = {
            'pitch': pitch,
            'roll': roll,
            'yaw': yaw,
            'head_down': False,
            'head_tilt': False,
            'head_turn': False,
            'head_down_duration': 0.0,
            'head_tilt_duration': 0.0,
            'head_turn_duration': 0.0,
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
        
        # Check for head turning (yaw)
        if abs(yaw) > DrowsinessThresholds.HEAD_YAW_WARNING:
            if self.head_turn_start is None:
                self.head_turn_start = current_time
            
            duration = current_time - self.head_turn_start
            result['head_turn'] = True
            result['head_turn_duration'] = duration
            
            if duration >= DrowsinessThresholds.HEAD_POSE_DURATION:
                result['warning'] = True
                if abs(yaw) > DrowsinessThresholds.HEAD_YAW_DANGER:
                    result['warning_type'] = 'head_turn_danger'
                else:
                    result['warning_type'] = 'head_turn'
        else:
            self.head_turn_start = None
        
        # Detect nodding pattern
        if len(self.pitch_history) >= 30:
            recent_pitch = list(self.pitch_history)[-30:]
            pitch_range = max(recent_pitch) - min(recent_pitch)
            
            if pitch_range > 15:
                new_direction = 1 if pitch > self.last_pitch else -1
                
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
        
        recent_nods = len([t for t in self.nod_timestamps if time.time() - t < 60])
        score += min(15, recent_nods * 5)
        
        if self.head_down_start:
            duration = time.time() - self.head_down_start
            score += min(15, duration * 3)
        
        return score
    
    def reset(self):
        self.pitch_history.clear()
        self.roll_history.clear()
        self.yaw_history.clear()
        self.head_down_start = None
        self.head_tilt_start = None
        self.head_turn_start = None
        self.nod_count = 0
        self.nod_timestamps.clear()
        self.last_pitch = 0
        self.pitch_direction = 0
