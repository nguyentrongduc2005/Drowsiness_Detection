"""
Face Detector sử dụng MediaPipe
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple


class FaceDetector:
    """Phát hiện khuôn mặt và landmark bằng MediaPipe"""
    
    # Chỉ số landmark cho mắt và miệng
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    # Outer lip cho MAR: góc trái (61), góc phải (291), trên (0), dưới (17), cạnh
    MOUTH = [61, 291, 0, 17, 39, 84, 269, 314]
    
    def __init__(self, 
                 max_num_faces: int = 1,
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """
        Khởi tạo FaceDetector
        
        Args:
            max_num_faces: Số khuôn mặt tối đa
            min_detection_confidence: Độ tin cậy phát hiện tối thiểu
            min_tracking_confidence: Độ tin cậy tracking tối thiểu
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=max_num_faces,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
    
    def process(self, frame: np.ndarray):
        """
        Xử lý frame và phát hiện landmarks
        
        Args:
            frame: Frame BGR từ camera
            
        Returns:
            MediaPipe results object
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.face_mesh.process(rgb_frame)
        rgb_frame.flags.writeable = True
        return results
    
    def get_landmarks(self, results, frame_shape: Tuple[int, int]) -> Optional[np.ndarray]:
        """
        Trích xuất tọa độ landmarks
        
        Args:
            results: MediaPipe results
            frame_shape: Kích thước frame (height, width)
            
        Returns:
            Array landmarks hoặc None
        """
        if not results.multi_face_landmarks:
            return None
        
        h, w = frame_shape
        face_landmarks = results.multi_face_landmarks[0]
        
        landmarks = []
        for landmark in face_landmarks.landmark:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            landmarks.append([x, y])
        
        return np.array(landmarks)
    
    def get_eye_landmarks(self, landmarks: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Lấy landmarks mắt trái và phải"""
        return landmarks[self.LEFT_EYE], landmarks[self.RIGHT_EYE]
    
    def get_mouth_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """Lấy landmarks miệng"""
        return landmarks[self.MOUTH]
    
    def draw_landmarks(self, frame: np.ndarray, results, 
                      draw_eyes: bool = True,
                      draw_mouth: bool = True,
                      draw_full_mesh: bool = False):
        """
        Vẽ landmarks lên frame
        
        Args:
            frame: Frame để vẽ
            results: MediaPipe results
            draw_eyes: Vẽ mắt
            draw_mouth: Vẽ miệng
            draw_full_mesh: Vẽ toàn bộ lưới
        """
        if not results.multi_face_landmarks:
            return
        
        face_landmarks = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]
        
        if draw_full_mesh:
            # Vẽ tesselation (lưới mesh) - màu xám
            self.mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(100, 100, 100), thickness=1, circle_radius=0)
            )
            
            # Vẽ contours (đường viền) - màu xám đậm
            self.mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(150, 150, 150), thickness=1, circle_radius=0)
            )
            
            # Vẽ irises (mắt)
            self.mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=self.mp_face_mesh.FACEMESH_IRISES,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp.solutions.drawing_utils.DrawingSpec(
                    color=(255, 117, 66), thickness=1, circle_radius=1)
            )
        
        landmarks = self.get_landmarks(results, (h, w))
        
        if landmarks is not None:
            if draw_eyes:
                # Vẽ mắt trái với đường nối
                left_eye_pts = [landmarks[idx] for idx in self.LEFT_EYE]
                cv2.polylines(frame, [np.array(left_eye_pts)], True, (0, 255, 0), 2)
                for idx in self.LEFT_EYE:
                    cv2.circle(frame, tuple(landmarks[idx]), 3, (0, 255, 0), -1)
                
                # Vẽ mắt phải với đường nối
                right_eye_pts = [landmarks[idx] for idx in self.RIGHT_EYE]
                cv2.polylines(frame, [np.array(right_eye_pts)], True, (0, 255, 0), 2)
                for idx in self.RIGHT_EYE:
                    cv2.circle(frame, tuple(landmarks[idx]), 3, (0, 255, 0), -1)
            
            # Đã bỏ vẽ miệng màu đỏ để gọn gàng hơn
            # if draw_mouth:
            #     mouth_pts = [landmarks[idx] for idx in self.MOUTH]
            #     cv2.polylines(frame, [np.array(mouth_pts)], True, (0, 0, 255), 2)
            #     for idx in self.MOUTH:
            #         cv2.circle(frame, tuple(landmarks[idx]), 3, (0, 0, 255), -1)
    
    def release(self):
        """Giải phóng tài nguyên"""
        try:
            if self.face_mesh:
                self.face_mesh.close()
                self.face_mesh = None
        except (ValueError, AttributeError):
            # Đã được close rồi hoặc không tồn tại
            pass
