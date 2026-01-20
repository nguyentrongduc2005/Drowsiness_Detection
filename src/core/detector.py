"""
AI Module: Face detection and landmark extraction using MediaPipe
Optimized version with preprocessing and smoothing
Enhanced with Head Pose Estimation (PnP algorithm)
"""
import cv2
import numpy as np
import mediapipe as mp
from collections import deque


class FaceDetector:
    """Face detection and landmarks class using MediaPipe - Optimized"""
    
    # MediaPipe FaceMesh indices for eyes and mouth
    # Ordered for compatibility with dlib 68 points
    
    # Right eye (from camera view) - indices 36-41 in dlib
    RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    
    # Left eye (from camera view) - indices 42-47 in dlib  
    LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
    
    def __init__(self, predictor_path=None):
        """
        Initialize detector with MediaPipe FaceMesh - Optimized
        Args:
            predictor_path: Not used (kept for API compatibility)
        """
        print("Initializing face detector with MediaPipe (Optimized)...")
        
        # Initialize MediaPipe FaceMesh with optimized configuration
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # Enable iris landmarks for better accuracy
            min_detection_confidence=0.6,  # Increase detection threshold
            min_tracking_confidence=0.6   # Increase tracking threshold
        )
        
        # Landmark smoothing - reduce noise between frames
        self.smoothing_enabled = True
        self.smoothing_window = 3  # Number of frames for smoothing
        self.landmark_history = deque(maxlen=self.smoothing_window)
        
        # Preprocessing settings
        self.preprocessing_enabled = True
        self.target_brightness = 130  # Target brightness (0-255)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        
        # Detection recovery - count frames without face to reset
        self.frames_without_face = 0
        self.max_frames_without_face = 10  # Reset after N frames without face
        
        # Cache last valid landmarks
        self.last_valid_landmarks = None
        self.landmark_timeout = 5  # Number of frames to use cache
        self.frames_using_cache = 0
        
        # Store raw MediaPipe landmarks for head pose estimation
        self.last_raw_landmarks = None
        
        # Head Pose Estimation - 3D model points (standard face model)
        self.model_points_3d = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (0.0, -330.0, -65.0),        # Chin
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left mouth corner
            (150.0, -150.0, -125.0)      # Right mouth corner
        ], dtype=np.float64)
        
        # Indices for head pose key points in MediaPipe 468 landmarks
        self.head_pose_indices = [1, 152, 33, 263, 61, 291]
        
        print("[OK] MediaPipe FaceMesh (Optimized + Head Pose) initialized!")
        print(f"  - Smoothing: {self.smoothing_window} frames")
        print(f"  - Preprocessing: {'Enabled' if self.preprocessing_enabled else 'Disabled'}")
        print("  - Head Pose: Enabled (PnP algorithm)")
    
    def _preprocess_frame(self, frame):
        """
        Preprocess frame to improve detection
        - Histogram equalization (CLAHE)
        - Brightness adjustment
        - Noise reduction
        """
        if not self.preprocessing_enabled:
            return frame
        
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE on L channel (luminance)
            l = self.clahe.apply(l)
            
            # Merge back
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Check brightness and adjust if needed
            gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
            current_brightness = np.mean(gray)
            
            if current_brightness < 80:  # Too dark
                # Increase brightness
                alpha = 1.3  # Contrast
                beta = 30    # Brightness
                enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)
            elif current_brightness > 200:  # Too bright
                # Decrease brightness
                alpha = 0.8
                beta = -20
                enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)
            
            return enhanced
            
        except Exception:
            # If error, return original frame
            return frame
    
    def _smooth_landmarks(self, landmarks):
        """
        Smooth landmarks using moving average
        Reduces jitter between frames
        """
        if not self.smoothing_enabled or landmarks is None:
            return landmarks
        
        # Add to history
        self.landmark_history.append(landmarks)
        
        if len(self.landmark_history) < 2:
            return landmarks
        
        # Calculate weighted average (newer frames are more important)
        weights = np.array([i + 1 for i in range(len(self.landmark_history))])
        weights = weights / weights.sum()
        
        smoothed = []
        for i in range(len(landmarks)):
            x_sum = 0
            y_sum = 0
            for j, hist_landmarks in enumerate(self.landmark_history):
                if i < len(hist_landmarks):
                    x_sum += hist_landmarks[i][0] * weights[j]
                    y_sum += hist_landmarks[i][1] * weights[j]
            smoothed.append((int(x_sum), int(y_sum)))
        
        return smoothed
    
    def get_landmarks(self, frame):
        """
        Extract landmarks from frame using MediaPipe
        
        Args:
            frame: Camera frame (BGR)
            
        Returns:
            list: List of 68 coordinate pairs (x, y) compatible with dlib format
                  or None if no face detected
            
        Important indices (dlib compatible):
            - Left eye: [36, 41]
            - Right eye: [42, 47]
            - Mouth: [48, 67]
        """
        if frame is None or frame.size == 0:
            return None
        
        try:
            h, w = frame.shape[:2]
            
            # Preprocess frame to improve detection
            processed_frame = self._preprocess_frame(frame)
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            # Optimize: Reduce resolution if frame is too large
            scale = 1.0
            if w > 640:
                scale = 640 / w
                rgb_frame = cv2.resize(rgb_frame, None, fx=scale, fy=scale)
            
            # Process with MediaPipe
            results = self.face_mesh.process(rgb_frame)
            
            if not results.multi_face_landmarks:
                # No face detected
                self.frames_without_face += 1
                self.last_raw_landmarks = None
                
                # Use cache if face is temporarily lost
                if self.last_valid_landmarks and self.frames_using_cache < self.landmark_timeout:
                    self.frames_using_cache += 1
                    return self.last_valid_landmarks
                
                # Reset history if face is lost for too long
                if self.frames_without_face > self.max_frames_without_face:
                    self.landmark_history.clear()
                    self.last_valid_landmarks = None
                
                return None
            
            # Reset counter when face is detected
            self.frames_without_face = 0
            self.frames_using_cache = 0
            
            # Get landmarks of the first face
            face_landmarks = results.multi_face_landmarks[0]
            
            # Store raw landmarks for head pose estimation (all 468 points)
            self.last_raw_landmarks = face_landmarks
            
            # Scale factor to convert to original resolution
            scale_x = w
            scale_y = h
            
            # Create list of 68 points compatible with dlib format
            landmarks = []
            
            # Jawline (0-16): 17 points - from right to left of face
            jawline_indices = [234, 93, 132, 58, 172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397]
            for idx in jawline_indices:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Right eyebrow (17-21): 5 points
            right_eyebrow_indices = [46, 53, 52, 65, 55]
            for idx in right_eyebrow_indices:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Left eyebrow (22-26): 5 points
            left_eyebrow_indices = [285, 295, 282, 283, 276]
            for idx in left_eyebrow_indices:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Nose (27-35): 9 points
            nose_indices = [168, 6, 197, 195, 5, 48, 115, 220, 45]
            for idx in nose_indices:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Right eye (36-41): 6 points - dlib order
            right_eye_indices = [33, 160, 158, 133, 153, 144]
            for idx in right_eye_indices:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Left eye (42-47): 6 points - dlib order
            left_eye_indices = [362, 385, 387, 263, 373, 380]
            for idx in left_eye_indices:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Outer mouth (48-59): 12 points - clockwise from right corner
            mouth_outer = [61, 40, 37, 0, 267, 270, 291, 321, 314, 17, 84, 91]
            for idx in mouth_outer:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Inner mouth (60-67): 8 points
            mouth_inner = [78, 82, 13, 312, 308, 317, 14, 87]
            for idx in mouth_inner:
                lm = face_landmarks.landmark[idx]
                landmarks.append((int(lm.x * scale_x), int(lm.y * scale_y)))
            
            # Apply smoothing to reduce noise
            smoothed_landmarks = self._smooth_landmarks(landmarks)
            
            # Cache valid landmarks
            self.last_valid_landmarks = smoothed_landmarks
            
            return smoothed_landmarks
            
        except Exception as e:
            print(f"Error in get_landmarks: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_eye_landmarks(self, landmarks):
        """
        Get eye landmark coordinates
        
        Args:
            landmarks: List of 68 points
            
        Returns:
            tuple: (left_eye_points, right_eye_points)
        """
        if landmarks is None or len(landmarks) < 48:
            return None, None
        
        left_eye = landmarks[36:42]   # Index 36-41
        right_eye = landmarks[42:48]  # Index 42-47
        
        return left_eye, right_eye
    
    def get_raw_landmarks(self):
        """
        Get raw MediaPipe landmarks (all 468 points)
        For head pose estimation
        
        Returns:
            MediaPipe NormalizedLandmarkList or None
        """
        return self.last_raw_landmarks
    
    def get_mouth_landmarks(self, landmarks):
        """
        Get mouth landmark coordinates
        
        Args:
            landmarks: List of 68 points
            
        Returns:
            list: Mouth points (index 48-67)
        """
        if landmarks is None or len(landmarks) < 68:
            return None
        
        mouth = landmarks[48:68]  # Index 48-67
        
        return mouth
    
    def draw_landmarks(self, frame, landmarks):
        """
        Draw landmarks on frame (for debugging)
        
        Args:
            frame: Image frame
            landmarks: List of 68 points
            
        Returns:
            frame: Frame with landmarks drawn
        """
        if landmarks is None:
            return frame
        
        # Draw points
        for (x, y) in landmarks:
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        
        # Draw left eye outline
        if len(landmarks) >= 42:
            left_eye = landmarks[36:42]
            for i in range(len(left_eye)):
                cv2.line(frame, left_eye[i], left_eye[(i + 1) % len(left_eye)], (255, 0, 0), 1)
        
        # Draw right eye outline
        if len(landmarks) >= 48:
            right_eye = landmarks[42:48]
            for i in range(len(right_eye)):
                cv2.line(frame, right_eye[i], right_eye[(i + 1) % len(right_eye)], (255, 0, 0), 1)
        
        # Draw mouth outline
        if len(landmarks) >= 68:
            mouth = landmarks[48:68]
            for i in range(len(mouth)):
                cv2.line(frame, mouth[i], mouth[(i + 1) % len(mouth)], (0, 0, 255), 1)
        
        return frame
    
    def get_head_pose(self, img_w, img_h):
        """
        Calculate head pose angles using PnP algorithm
        
        Args:
            img_w: Image width
            img_h: Image height
            
        Returns:
            dict: {
                'success': bool,
                'pitch': float (gật đầu lên/xuống, degrees),
                'yaw': float (quay trái/phải, degrees),
                'roll': float (nghiêng đầu, degrees),
                'nodding': bool (True nếu đang gục đầu)
            }
        """
        if self.last_raw_landmarks is None:
            return {
                'success': False,
                'pitch': 0.0,
                'yaw': 0.0,
                'roll': 0.0,
                'nodding': False
            }
        
        try:
            # Extract 2D points from MediaPipe landmarks
            face_2d = []
            for idx in self.head_pose_indices:
                lm = self.last_raw_landmarks.landmark[idx]
                x, y = int(lm.x * img_w), int(lm.y * img_h)
                face_2d.append([x, y])
            
            face_2d = np.array(face_2d, dtype=np.float64)
            
            # Camera matrix (assuming standard focal length)
            focal_length = 1.0 * img_w
            cam_matrix = np.array([
                [focal_length, 0, img_w / 2],
                [0, focal_length, img_h / 2],
                [0, 0, 1]
            ], dtype=np.float64)
            
            # Distortion coefficients (assuming no distortion)
            dist_coeffs = np.zeros((4, 1), dtype=np.float64)
            
            # Solve PnP
            success, rot_vec, _ = cv2.solvePnP(
                self.model_points_3d,
                face_2d,
                cam_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
            
            if not success:
                return {
                    'success': False,
                    'pitch': 0.0,
                    'yaw': 0.0,
                    'roll': 0.0,
                    'nodding': False
                }
            
            # Convert rotation vector to rotation matrix
            rmat, _ = cv2.Rodrigues(rot_vec)
            
            # Decompose rotation matrix to Euler angles
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
            
            # Extract angles (convert to degrees)
            pitch = angles[0] * 360  # Gật đầu (negative = down, positive = up)
            yaw = angles[1] * 360    # Quay đầu (negative = left, positive = right)
            roll = angles[2] * 360   # Nghiêng đầu
            
            # Detect nodding (head tilted down significantly)
            # Threshold: -15 degrees for warning, -25 for danger
            is_nodding = pitch < -15
            
            return {
                'success': True,
                'pitch': pitch,
                'yaw': yaw,
                'roll': roll,
                'nodding': is_nodding,
                'nodding_severity': 'danger' if pitch < -25 else 'warning' if is_nodding else 'normal'
            }
            
        except Exception as e:
            return {
                'success': False,
                'pitch': 0.0,
                'yaw': 0.0,
                'roll': 0.0,
                'nodding': False,
                'error': str(e)
            }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()
    
    def set_preprocessing(self, enabled: bool):
        """Enable/disable frame preprocessing"""
        self.preprocessing_enabled = enabled
        print(f"Preprocessing: {'Enabled' if enabled else 'Disabled'}")
    
    def set_smoothing(self, enabled: bool, window: int = 3):
        """
        Enable/disable and adjust smoothing
        Args:
            enabled: Enable/disable smoothing
            window: Number of frames for smoothing (1-5)
        """
        self.smoothing_enabled = enabled
        self.smoothing_window = max(1, min(5, window))
        self.landmark_history = deque(maxlen=self.smoothing_window)
        print(f"Smoothing: {'Enabled' if enabled else 'Disabled'}, window={self.smoothing_window}")
    
    def reset_tracking(self):
        """Reset tracking state - call when starting over"""
        self.landmark_history.clear()
        self.last_valid_landmarks = None
        self.frames_without_face = 0
        self.frames_using_cache = 0
        print("Tracking state has been reset")
    
    def get_detection_stats(self):
        """Get detection statistics"""
        return {
            "frames_without_face": self.frames_without_face,
            "using_cached_landmarks": self.frames_using_cache > 0,
            "cache_frames_used": self.frames_using_cache,
            "smoothing_history_size": len(self.landmark_history)
        }
