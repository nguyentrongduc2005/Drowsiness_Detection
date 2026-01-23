"""
Signal Stabilizer - Handle lost tracking gracefully
"""


class SignalStabilizer:
    """
    Stabilizes EAR/MAR signals when face tracking is temporarily lost
    
    Problem: When driver turns head quickly or rubs eyes, tracking fails
             and EAR/MAR jumps to 0, causing graph spikes and false alerts
             
    Solution: Hold last valid value for short period (0.3s = ~10 frames)
              This smooths the signal without hiding real drowsiness
    """
    
    def __init__(self, hold_frames: int = 10):
        """
        Args:
            hold_frames: Number of frames to hold last valid value (default: 10 @ 30fps = 0.33s)
        """
        self.last_valid_ear = 0.3  # Safe default (eyes open)
        self.last_valid_mar = 0.2  # Safe default (mouth closed)
        self.lost_frames = 0
        self.max_hold_frames = hold_frames
        
    def update_ear(self, current_ear: float, is_face_detected: bool) -> float:
        """
        Update EAR with stabilization
        
        Args:
            current_ear: Current EAR value (0.0 if face lost)
            is_face_detected: Whether face is currently detected
            
        Returns:
            Stabilized EAR value
        """
        if is_face_detected and current_ear > 0:
            # Face detected, update last valid value
            self.lost_frames = 0
            self.last_valid_ear = current_ear
            return current_ear
        else:
            # Face lost
            self.lost_frames += 1
            
            if self.lost_frames < self.max_hold_frames:
                # Hold last valid value (short-term loss)
                return self.last_valid_ear
            else:
                # Lost too long, return 0 (real problem)
                return 0.0
    
    def update_mar(self, current_mar: float, is_face_detected: bool) -> float:
        """
        Update MAR with stabilization
        
        Args:
            current_mar: Current MAR value (0.0 if face lost)
            is_face_detected: Whether face is currently detected
            
        Returns:
            Stabilized MAR value
        """
        if is_face_detected and current_mar >= 0:
            # Face detected, update last valid value
            self.lost_frames = 0
            self.last_valid_mar = current_mar
            return current_mar
        else:
            # Face lost
            self.lost_frames += 1
            
            if self.lost_frames < self.max_hold_frames:
                # Hold last valid value
                return self.last_valid_mar
            else:
                # Lost too long
                return 0.0
    
    def reset(self):
        """Reset stabilizer state"""
        self.lost_frames = 0
        
    def is_tracking_lost(self) -> bool:
        """Check if tracking is currently lost"""
        return self.lost_frames > 0
    
    def get_hold_duration(self) -> int:
        """Get current hold duration in frames"""
        return self.lost_frames
